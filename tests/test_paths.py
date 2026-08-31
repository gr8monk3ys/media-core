"""The shared directories, resolved the same way by every tool."""

from __future__ import annotations

from pathlib import Path

import pytest

from media_core.paths import books_dir, media_dir, movies_dir, music_dir

CASES = [
    (music_dir, "MUSIC_DIR", ".music"),
    (movies_dir, "MOVIES_DIR", ".movies"),
    (books_dir, "BOOKS_DIR", ".books"),
]


@pytest.mark.parametrize(("fn", "var", "default"), CASES, ids=[c[1] for c in CASES])
def test_defaults_under_home_when_unset(
    fn, var: str, default: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert fn() == tmp_path / default


@pytest.mark.parametrize(("fn", "var", "default"), CASES, ids=[c[1] for c in CASES])
def test_env_var_wins(fn, var: str, default: str, monkeypatch: pytest.MonkeyPatch,
                      tmp_path: Path) -> None:
    monkeypatch.setenv(var, str(tmp_path / "elsewhere"))
    assert fn() == tmp_path / "elsewhere"


@pytest.mark.parametrize(("fn", "var", "default"), CASES, ids=[c[1] for c in CASES])
def test_tilde_in_the_env_var_is_expanded(
    fn, var: str, default: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv(var, "~/somewhere")
    assert fn() == tmp_path / "somewhere"


@pytest.mark.parametrize(("fn", "var", "default"), CASES, ids=[c[1] for c in CASES])
def test_empty_env_var_is_treated_as_unset(
    fn, var: str, default: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`export MUSIC_DIR=` is a shell accident, not a request for the cwd."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv(var, "   ")
    assert fn() == tmp_path / default


def test_resolved_at_call_time_not_import_time(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """This module is imported long before a test points HOME somewhere else."""
    monkeypatch.setenv("HOME", str(tmp_path / "one"))
    first = music_dir()
    monkeypatch.setenv("HOME", str(tmp_path / "two"))
    assert music_dir() != first


def test_media_dir_takes_any_variable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GAMES_DIR", str(tmp_path / "g"))
    assert media_dir("GAMES_DIR", ".games") == tmp_path / "g"


def test_home_relative_default_needs_no_expansion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`Path.home()` is already absolute, so the default branch expands nothing."""
    monkeypatch.delenv("MUSIC_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    resolved = music_dir()
    assert resolved.is_absolute()
    assert resolved == resolved.expanduser()
