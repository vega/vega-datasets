"""Source verification tests for the bird migration generator."""

from __future__ import annotations

import csv
import hashlib
import importlib
from typing import TYPE_CHECKING
from unittest.mock import Mock

import niquests
import pytest

if TYPE_CHECKING:
    from pathlib import Path

bird_migration = importlib.import_module("scripts.bird-migration")


@pytest.mark.parametrize("download", [False, True])
def test_rejects_changed_source_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, download: bool
) -> None:
    source = tmp_path / "centroids.txt"
    source.write_bytes(b"unexpected source bytes")
    dest = tmp_path / "birds.csv"
    dest.write_bytes(b"existing dataset")
    response = Mock(content=source.read_bytes())
    monkeypatch.setattr(niquests, "get", Mock(return_value=response))

    with pytest.raises(SystemExit, match="source SHA-256 mismatch"):
        bird_migration.convert(None if download else source, dest)

    assert dest.read_bytes() == b"existing dataset"


def test_download_failure_preserves_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = Mock()
    response.raise_for_status.side_effect = niquests.HTTPError("download failed")
    monkeypatch.setattr(niquests, "get", Mock(return_value=response))
    dest = tmp_path / "birds.csv"
    dest.write_bytes(b"existing dataset")

    with pytest.raises(niquests.HTTPError, match="download failed"):
        bird_migration.convert(None, dest)

    assert dest.read_bytes() == b"existing dataset"


@pytest.mark.parametrize("download", [False, True])
def test_verified_source_preserves_day_gaps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, download: bool
) -> None:
    content = (
        "species\tlon\tlat\n"
        + "Bicknell_s_Thrush\tNA\tNA\n"
        + "Bicknell_s_Thrush\t-70.123456\t40.123456\n" * 364
    ).encode()
    monkeypatch.setattr(
        bird_migration, "SOURCE_SHA256", hashlib.sha256(content).hexdigest()
    )
    source = tmp_path / "centroids.txt"
    source.write_bytes(content)
    response = Mock(content=content)
    get = Mock(return_value=response)
    monkeypatch.setattr(niquests, "get", get)
    dest = tmp_path / "birds.csv"

    bird_migration.convert(None if download else source, dest)

    if download:
        get.assert_called_once_with(bird_migration.SOURCE_URL, timeout=60)
        response.raise_for_status.assert_called_once_with()
    else:
        get.assert_not_called()
    with dest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 364
    assert rows[0] == {
        "species": "Bicknell's Thrush",
        "day": "2",
        "date": "2015-01-02",
        "lon": "-70.1235",
        "lat": "40.1235",
    }
    assert rows[-1]["day"] == "365"
    assert rows[-1]["date"] == "2015-12-31"
