"""Tests for ``scripts/build_datapackage.py``."""

from __future__ import annotations

import subprocess as sp
from typing import TYPE_CHECKING

import pytest

from scripts.build_datapackage import git_blob_sha1, iter_resources

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"a,b\n1,x\n",
        b"a,b\r\n1,x\r\n",
        bytes(range(256)),
    ],
    ids=["empty", "lf", "crlf", "binary"],
)
def test_git_blob_sha1_matches_git(tmp_path: Path, content: bytes) -> None:
    """The hash is git's object name for the file's bytes, whatever they are."""
    fp = tmp_path / "blob"
    fp.write_bytes(content)
    expected = sp.run(
        ["git", "hash-object", "--no-filters", fp],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert git_blob_sha1(fp) == f"sha1:{expected}"


def test_iter_resources_hashes_working_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    A dataset that git has never seen gets a hash of its current contents.

    Regression: hashes used to come from ``git ls-tree``, so building before
    committing crashed on a new file and recorded a stale hash for an edited one.
    """
    fp = tmp_path / "untracked.csv"
    fp.write_bytes(b"a,b\n1,x\n2,y\n")
    monkeypatch.chdir(tmp_path)
    (resource,) = iter_resources(tmp_path, {})
    assert resource.bytes == fp.stat().st_size
    assert resource.hash == git_blob_sha1(fp)
