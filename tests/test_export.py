"""The envelope, and the five hand-written documents it has to reproduce.

Each ``test_reproduces_the_*_envelope`` case is the header of a real interchange
file as its own repo wrote it before this package existed. They are the reason
the cosmetic arguments exist: the tools do not agree about indentation,
``ensure_ascii`` or a trailing newline, and a file whose bytes changed under
them would show up as a whole-file diff in a repo that only writes rows.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from media_core.export import (
    ExportError,
    build_export,
    read_export,
    schema_version,
    write_export,
)

GENERATED_AT = "2026-08-26T00:00:00+00:00"


# -- the envelope ---------------------------------------------------------


def test_header_comes_first_and_sections_keep_their_order() -> None:
    doc = build_export("discogs/1", GENERATED_AT, username="u", collection=[1], wantlist=[2])
    assert list(doc) == ["schema", "generated_at", "username", "collection", "wantlist"]


def test_coverage_is_emitted_last() -> None:
    """Every repo that has coverage counts puts them after the rows they count."""
    doc = build_export("rym/1", GENERATED_AT, ratings=[], coverage={"listened": 0})
    assert list(doc) == ["schema", "generated_at", "ratings", "coverage"]


def test_username_is_omitted_when_absent_rather_than_null() -> None:
    """A null username would be a claim about the account; absence is not."""
    assert "username" not in build_export("rym/1", GENERATED_AT, ratings=[])


def test_empty_coverage_is_still_emitted() -> None:
    """0 rated is a measurement. Only `None` means "this export has no coverage"."""
    doc = build_export("goodreads/1", GENERATED_AT, books=[], coverage={})
    assert doc["coverage"] == {}


def test_rejects_a_malformed_schema_string() -> None:
    with pytest.raises(ExportError, match="schema string"):
        build_export("discogs", GENERATED_AT, collection=[])


def test_rejects_an_empty_generated_at() -> None:
    with pytest.raises(ExportError, match="generated_at"):
        build_export("discogs/1", "", collection=[])


@pytest.mark.parametrize(
    ("schema", "version"),
    [("discogs/1", 1), ("rym/1", 1), ("goodreads/1", 1), ("letterboxd/1", 1),
     ("music-library/1", 1), ("music-library/12", 12)],
)
def test_schema_version_reads_the_real_schema_strings(schema: str, version: int) -> None:
    assert schema_version(schema) == version


# -- the five documents this envelope replaces ----------------------------


def test_reproduces_the_discogs_envelope() -> None:
    doc = build_export("discogs/1", GENERATED_AT, username="u", collection=[], wantlist=[])
    assert doc == {
        "schema": "discogs/1", "generated_at": GENERATED_AT, "username": "u",
        "collection": [], "wantlist": [],
    }


def test_reproduces_the_rym_envelope() -> None:
    doc = build_export("rym/1", GENERATED_AT, ratings=[],
                       coverage={"listened": 1, "rated": 0, "queued": 1})
    assert list(doc) == ["schema", "generated_at", "ratings", "coverage"]


def test_reproduces_the_goodreads_envelope() -> None:
    doc = build_export("goodreads/1", GENERATED_AT, books=[],
                       coverage={"read": 0, "rated": 0, "reviewed": 0, "queued": 0})
    assert list(doc) == ["schema", "generated_at", "books", "coverage"]


def test_reproduces_the_letterboxd_envelope() -> None:
    doc = build_export("letterboxd/1", GENERATED_AT, username="u", films=[], watchlist=[],
                       coverage={"watched": 0})
    assert list(doc) == [
        "schema", "generated_at", "username", "films", "watchlist", "coverage",
    ]


def test_reproduces_the_spotify_envelope() -> None:
    """The Spotify export nests its user under `source`, so it passes a section."""
    doc = build_export("music-library/1", GENERATED_AT,
                       source={"platform": "spotify", "user": "u"}, albums=[], discoveries=[])
    assert list(doc) == ["schema", "generated_at", "source", "albums", "discoveries"]
    assert "username" not in doc


# -- writing --------------------------------------------------------------


def test_write_creates_missing_parents(tmp_path: Path) -> None:
    out = write_export({"schema": "discogs/1"}, tmp_path / "deep" / "nested" / "d.json")
    assert out.exists()


def test_write_leaves_no_temp_file_behind(tmp_path: Path) -> None:
    write_export({"schema": "discogs/1"}, tmp_path / "d.json")
    assert list(tmp_path.iterdir()) == [tmp_path / "d.json"]


def test_write_replaces_an_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "d.json"
    write_export({"schema": "discogs/1", "n": 1}, path)
    write_export({"schema": "discogs/1", "n": 2}, path)
    assert json.loads(path.read_text())["n"] == 2


def test_write_returns_the_path_it_wrote(tmp_path: Path) -> None:
    assert write_export({"schema": "discogs/1"}, str(tmp_path / "d.json")) == tmp_path / "d.json"


def test_default_bytes_are_indent_1_utf8_and_newline_terminated(tmp_path: Path) -> None:
    """What rym, goodreads and letterboxd already wrote — the majority default."""
    path = write_export({"schema": "rym/1", "a": ["Sigur Rós"]}, tmp_path / "r.json")
    assert path.read_text(encoding="utf-8") == '{\n "schema": "rym/1",\n "a": [\n  "Sigur Rós"\n ]\n}\n'


def test_ensure_ascii_reproduces_the_discogs_bytes(tmp_path: Path) -> None:
    path = write_export({"a": "Rós"}, tmp_path / "d.json", ensure_ascii=True, newline=False)
    assert path.read_text(encoding="utf-8") == '{\n "a": "R\\u00f3s"\n}'


def test_indent_none_reproduces_the_spotify_bytes(tmp_path: Path) -> None:
    path = write_export({"a": "Rós"}, tmp_path / "s.json", indent=None, ensure_ascii=True,
                        newline=False)
    assert path.read_text(encoding="utf-8") == '{"a": "R\\u00f3s"}'


# -- reading --------------------------------------------------------------


def test_round_trips(tmp_path: Path) -> None:
    doc = build_export("discogs/1", GENERATED_AT, username="u", collection=[{"title": "Kid A"}])
    assert read_export(write_export(doc, tmp_path / "d.json"), "discogs/1") == doc


def test_read_accepts_any_schema_when_none_is_named(tmp_path: Path) -> None:
    write_export({"schema": "rym/1"}, tmp_path / "r.json")
    assert read_export(tmp_path / "r.json")["schema"] == "rym/1"


def test_read_refuses_a_schema_it_was_not_written_for(tmp_path: Path) -> None:
    write_export(build_export("rym/1", GENERATED_AT, ratings=[]), tmp_path / "r.json")
    with pytest.raises(ExportError, match="declares schema 'rym/1'"):
        read_export(tmp_path / "r.json", "discogs/1")


def test_read_names_the_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ExportError, match="No export file at"):
        read_export(tmp_path / "absent.json")


def test_read_refuses_invalid_json(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ExportError, match="not valid JSON"):
        read_export(tmp_path / "bad.json")


def test_read_refuses_a_json_document_that_is_not_an_object(tmp_path: Path) -> None:
    (tmp_path / "list.json").write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ExportError, match="not an object"):
        read_export(tmp_path / "list.json")


def test_read_refuses_a_document_with_no_schema_at_all(tmp_path: Path) -> None:
    (tmp_path / "bare.json").write_text('{"albums": []}', encoding="utf-8")
    with pytest.raises(ExportError, match="declares schema None"):
        read_export(tmp_path / "bare.json", "music-library/1")
