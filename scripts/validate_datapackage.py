#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "frictionless[json,pandas,parquet]>=5.18.1",  # `pandas` extra: frictionless-py#1773 / #1774
#   "rich>=13",
# ]
# ///

"""
Validate datapackage.json against data/.

Runs two phases in order. Both look at every resource in the descriptor.

Phase 1 — does each file on disk still match what ``datapackage.json``
claims about it?

    For every resource we recompute two facts from disk and compare them
    to the values in the descriptor:

    * file size in bytes (via ``Path.stat().st_size``),
    * git-blob SHA-1 fingerprint (the same hash ``git`` uses for blobs).

    We do these ourselves in pure Python because frictionless-py doesn't
    cover either case reliably: its byte-count check returns ``None`` for
    tabular JSON / arrow / parquet resources (the underlying parsers yield
    values lazily and never drain the byte stream), and its hash check
    only supports md5 and sha256 — our descriptor uses sha1, so
    frictionless warns and skips.

Phase 2 — does each file's content match its declared schema?

    For every resource we construct a frictionless ``Package`` from the
    descriptor dict and call ``validate()`` on it: checks column types,
    flags malformed rows, and so on. Two implementation notes:

    * byte-count and hash-count checks are disabled here because phase 1
      already did them correctly and more completely,
    * resources are validated serially — frictionless's parallel code
      path silently ignores ``Checklist.skip_errors``, which re-surfaces
      every spurious byte-count error we just said to skip.

    Resources whose phase-2 failure is known and non-actionable (e.g.
    ``movies`` for documented pedagogy, ``flights_200k_arrow`` because
    frictionless has no arrow parser) are listed in
    ``_data/validate_datapackage.toml``. They're reported with a ⚠ marker
    but do not trip the exit code; remove an entry from that file to
    re-enable strict checking once the underlying issue is resolved.

    The descriptor is passed as an already-loaded dict so ``basepath``
    applies only to the resource paths, not the descriptor path — a
    workaround for https://github.com/frictionlessdata/framework/issues/1435.

Usage
-----
    uv run scripts/validate_datapackage.py
    uv run scripts/validate_datapackage.py --limit-rows 100000

Exits 0 when no unexpected failures occur, 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
import time
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

from frictionless import Checklist, Package
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from frictionless import Report

FRICTIONLESS_VERSION = importlib.metadata.version("frictionless")
CONFIG_FILE = "_data/validate_datapackage.toml"


def load_expected_failures(repo: Path) -> dict[str, str]:
    """
    Read the expected-failures config.

    Returns a mapping of ``resource name -> reason`` parsed from
    ``_data/validate_datapackage.toml``. Returns an empty dict if the file
    is missing, so the script still runs cleanly in a fresh checkout.
    """
    cfg_path = repo / CONFIG_FILE
    if not cfg_path.exists():
        return {}
    cfg = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    return {
        entry["resource"]: entry["reason"].strip()
        for entry in cfg.get("expected_failures", [])
    }


def git_blob_sha1(path: Path) -> str:
    r"""
    Compute the git-blob SHA-1 of a file.

    Our ``datapackage.json`` stores git blob SHAs (from ``extract_sha()`` in
    ``scripts/build_datapackage.py``), not raw content SHAs. A naive
    ``hashlib.sha1(content)`` would mismatch every resource.

    The blob format is ``sha1(b"blob " + len(content) + b"\\0" + content)``.
    """
    content = path.read_bytes()
    return hashlib.sha1(b"blob %d\0%b" % (len(content), content)).hexdigest()


def check_integrity(descriptor: dict, data_dir: Path) -> list[str]:
    """
    Compare each resource's on-disk stats to the descriptor.

    Returns a list of human-readable drift messages, empty if every resource
    matches.
    """
    errors: list[str] = []
    for r in descriptor["resources"]:
        path = data_dir / r["path"]
        if not path.exists():
            errors.append(f"{r['name']}: file missing ({r['path']})")
            continue
        declared_bytes = r.get("bytes")
        if declared_bytes is not None:
            actual_bytes = path.stat().st_size
            if declared_bytes != actual_bytes:
                errors.append(
                    f"{r['name']}: bytes drift "
                    f"(descriptor={declared_bytes}, disk={actual_bytes})"
                )
        declared_hash = r.get("hash", "")
        if declared_hash.startswith("sha1:"):
            expected = declared_hash.removeprefix("sha1:")
            actual = git_blob_sha1(path)
            if expected != actual:
                errors.append(
                    f"{r['name']}: sha1 drift "
                    f"(descriptor={expected[:10]}..., disk={actual[:10]}...)"
                )
    return errors


PANEL_STYLE = "cyan"
PASS_STYLE = "green"
FAIL_STYLE = "red"
EXPECTED_STYLE = "yellow"
MUTED_STYLE = "bright_black"


def _render_header(console: Console, descriptor: dict, limit_rows: int | None) -> None:
    name = descriptor.get("name", "package")
    version = descriptor.get("version", "")
    resource_count = len(descriptor["resources"])
    mode = f"limit-rows = {limit_rows:_}" if limit_rows else "full read (no row limit)"
    body = Text.assemble(
        (f"{name} ", "bold"),
        (version, MUTED_STYLE),
        "\n",
        (f"{resource_count} resources  ", ""),
        ("·", MUTED_STYLE),
        (f"  frictionless-py {FRICTIONLESS_VERSION}  ", MUTED_STYLE),
        ("·", MUTED_STYLE),
        (f"  {mode}", MUTED_STYLE),
    )
    console.print(
        Panel(
            body,
            title="datapackage validation",
            border_style=PANEL_STYLE,
            padding=(0, 2),
        )
    )


def _run_phase1(
    console: Console, descriptor: dict, data_dir: Path
) -> tuple[list[str], float]:
    console.print()
    console.rule(
        "[bold]Phase 1[/] · file integrity",
        style=MUTED_STYLE,
        align="left",
    )
    console.print(
        f"  [{MUTED_STYLE}]Does each file on disk still match what datapackage.json claims?[/]"
    )
    console.print(
        f"  [{MUTED_STYLE}]We recompute two things ourselves because frictionless-py doesn't:[/]"
    )
    console.print(
        f"  [{MUTED_STYLE}]  • file size — frictionless can't measure this for tabular JSON,[/]"
    )
    console.print(
        f"  [{MUTED_STYLE}]    arrow, or parquet files, so we read it via Python's stat()[/]"
    )
    console.print(
        f"  [{MUTED_STYLE}]  • git-blob SHA-1 fingerprint — frictionless only accepts md5 or[/]"
    )
    console.print(
        f"  [{MUTED_STYLE}]    sha256, and silently skips our sha1 entries[/]"
    )
    console.print()
    t0 = time.perf_counter()
    with console.status("[cyan]hashing files...", spinner="dots"):
        errors = check_integrity(descriptor, data_dir)
    elapsed = time.perf_counter() - t0
    total = len(descriptor["resources"])
    if errors:
        console.print(
            f"  [{FAIL_STYLE}]✗[/] {len(errors)} drift issue(s)   [{MUTED_STYLE}]({elapsed:.2f}s)[/]"
        )
        for msg in errors:
            console.print(f"    [{FAIL_STYLE}]•[/] {msg}")
    else:
        console.print(
            f"  [{PASS_STYLE}]✓[/] {total}/{total} resources match descriptor   [{MUTED_STYLE}]({elapsed:.2f}s)[/]"
        )
    return errors, elapsed


def _run_phase2(
    console: Console,
    descriptor: dict,
    data_dir: Path,
    *,
    limit_rows: int | None,
    expected_failures: dict[str, str],
) -> tuple[list[Report], float]:
    console.print()
    console.rule(
        f"[bold]Phase 2[/] · schema & row content  [dim](via frictionless-py {FRICTIONLESS_VERSION})[/]",
        style=MUTED_STYLE,
        align="left",
    )
    console.print(
        f"  [{MUTED_STYLE}]Does each file's actual content match its declared schema?[/]"
    )
    console.print(
        f"  [{MUTED_STYLE}]Column types, required fields, well-formed rows — handled by[/]"
    )
    console.print(
        f"  [{MUTED_STYLE}]frictionless-py. Two things to know about how we run it:[/]"
    )
    console.print(
        f"  [{MUTED_STYLE}]  • byte-count and hash-count checks are turned off here — phase 1[/]"
    )
    console.print(
        f"  [{MUTED_STYLE}]    already did them correctly and more completely[/]"
    )
    console.print(
        f"  [{MUTED_STYLE}]  • resources are validated one at a time, not in parallel —[/]"
    )
    console.print(
        f"  [{MUTED_STYLE}]    frictionless's parallel mode ignores our 'skip these' setting[/]"
    )
    console.print()
    reports: list[Report] = []
    total = len(descriptor["resources"])
    t0 = time.perf_counter()
    progress = Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style=PASS_STYLE, finished_style=PASS_STYLE),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TextColumn("[{task.fields[current]}]", style=MUTED_STYLE),
        console=console,
        transient=True,
    )
    with progress:
        task_id = progress.add_task("validating", total=total, current="")
        for resource_dict in descriptor["resources"]:
            progress.update(task_id, current=resource_dict["name"])
            checklist = Checklist(skip_errors=["byte-count", "hash-count"])
            single = Package(
                {"resources": [deepcopy(resource_dict)]}, basepath=str(data_dir)
            )
            reports.append(single.validate(checklist=checklist, limit_rows=limit_rows))
            progress.advance(task_id)
    elapsed = time.perf_counter() - t0

    unexpected = [
        r for r in reports if not r.valid and r.tasks[0].name not in expected_failures
    ]
    expected = [
        r for r in reports if not r.valid and r.tasks[0].name in expected_failures
    ]
    valid_count = total - len(unexpected) - len(expected)

    summary_parts = [f"[{PASS_STYLE}]✓[/] {valid_count} valid"]
    if expected:
        summary_parts.append(f"[{EXPECTED_STYLE}]⚠[/] {len(expected)} expected")
    if unexpected:
        summary_parts.append(f"[{FAIL_STYLE}]✗[/] {len(unexpected)} unexpected")
    console.print(f"  {'   '.join(summary_parts)}   [{MUTED_STYLE}]({elapsed:.2f}s)[/]")

    if unexpected:
        console.print()
        for report in unexpected:
            _render_task_errors(console, report.tasks[0], mark_style=FAIL_STYLE)

    if expected:
        console.print()
        console.print(f"  [{MUTED_STYLE}]expected failures (see {CONFIG_FILE})[/]")
        console.print()
        for report in expected:
            task = report.tasks[0]
            _render_task_errors(console, task, mark_style=EXPECTED_STYLE)
            reason = expected_failures[task.name].splitlines()[0]
            console.print(f"      [{MUTED_STYLE}]why expected: {reason}[/]")

    return reports, elapsed


def _render_task_errors(console: Console, task: Any, *, mark_style: str) -> None:
    """Render a single frictionless ReportTask's errors, grouped by (type, field)."""
    name = task.name
    # Group by (error type, field name) so row-level errors in the same field
    # collapse into a single summary with sample cells.
    grouped: dict[tuple[str, str | None], list[Any]] = {}
    for err in task.errors:
        field = getattr(err, "field_name", None)
        grouped.setdefault((err.type, field), []).append(err)

    mark = "⚠" if mark_style == EXPECTED_STYLE else "✗"
    console.print(Text.assemble((f"  {mark} ", mark_style), (name, "bold")))
    for (err_type, field), errs in grouped.items():
        count = len(errs)
        label = f"{err_type} x{count}" if count > 1 else err_type
        if field:
            # Row-level errors: show field + sample cells with row numbers.
            samples = ", ".join(f'"{e.cell}" (row {e.row_number})' for e in errs[:3])
            more = f", +{count - 3} more" if count > 3 else ""
            detail = f"field {field!r}: {samples}{more}"
        else:
            # Resource-level errors (format-error, scheme-error, etc.).
            detail = errs[0].note
            if len(detail) > 80:
                detail = detail[:77] + "..."
        console.print(f"      [{mark_style}]{label}[/]  [{MUTED_STYLE}]{detail}[/]")


def _render_summary(
    console: Console,
    *,
    integrity_errors: list[str],
    reports: list[Report],
    expected_failures: dict[str, str],
    phase1_elapsed: float,
    phase2_elapsed: float,
) -> None:
    unexpected = [
        r for r in reports if not r.valid and r.tasks[0].name not in expected_failures
    ]
    expected = [
        r for r in reports if not r.valid and r.tasks[0].name in expected_failures
    ]

    phase1_style = FAIL_STYLE if integrity_errors else PASS_STYLE
    phase1_mark = "✗" if integrity_errors else "✓"
    phase1_text = f"{len(integrity_errors)} drift" if integrity_errors else "pass"

    if unexpected:
        phase2_style, phase2_mark = FAIL_STYLE, "✗"
        phase2_text = f"{len(unexpected)} unexpected"
    elif expected:
        phase2_style, phase2_mark = EXPECTED_STYLE, "⚠"
        phase2_text = f"{len(expected)} expected"
    else:
        phase2_style, phase2_mark = PASS_STYLE, "✓"
        phase2_text = "pass"

    table = Table(show_header=False, box=None, pad_edge=False, padding=(0, 2))
    table.add_column(justify="left")
    table.add_column(justify="left")
    table.add_column(justify="right")
    table.add_row(
        Text.assemble(
            ("Integrity  ", "bold"),
            (f"{phase1_mark} {phase1_text}", phase1_style),
        ),
        Text.assemble(
            ("Schema/rows  ", "bold"),
            (f"{phase2_mark} {phase2_text}", phase2_style),
        ),
        Text(f"{phase1_elapsed + phase2_elapsed:.2f}s", style=MUTED_STYLE),
    )
    console.print()
    console.rule(style=MUTED_STYLE)
    console.print(table)
    console.rule(style=MUTED_STYLE)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate datapackage.json against data/ (integrity + schema/rows).",
    )
    parser.add_argument(
        "--limit-rows",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Validate only the first N rows of each resource. "
            "Skips deep parquet reads (flights-3m is ~3M rows). "
            "Default: no limit (full read)."
        ),
    )
    args = parser.parse_args()

    console = Console()
    repo = Path(__file__).resolve().parent.parent
    with (repo / "datapackage.json").open(encoding="utf-8") as f:
        descriptor = json.load(f)
    data_dir = repo / "data"
    expected_failures = load_expected_failures(repo)

    _render_header(console, descriptor, args.limit_rows)
    integrity_errors, phase1_elapsed = _run_phase1(console, descriptor, data_dir)
    reports, phase2_elapsed = _run_phase2(
        console,
        descriptor,
        data_dir,
        limit_rows=args.limit_rows,
        expected_failures=expected_failures,
    )
    _render_summary(
        console,
        integrity_errors=integrity_errors,
        reports=reports,
        expected_failures=expected_failures,
        phase1_elapsed=phase1_elapsed,
        phase2_elapsed=phase2_elapsed,
    )

    unexpected_fail = any(
        not r.valid and r.tasks[0].name not in expected_failures for r in reports
    )
    failed = bool(integrity_errors) or unexpected_fail
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
