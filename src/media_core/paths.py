"""Where the interchange files live.

Several tools write one JSON file each into a directory they all agree on, and
read each other's. The agreement is an unprefixed environment variable per
medium with a home-directory default, which every tool has to resolve the same
way — a tool that resolved it differently would read a stale file, or none, and
report an empty library rather than an error.

The variable is deliberately unprefixed. Each tool has its own settings prefix
that the other tools know nothing about, so the shared name is the only one they
can all honour. A tool's own prefixed setting may still override what it passes
in; that is the tool's business, not this module's.
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["BOOKS_DIR_VAR", "MOVIES_DIR_VAR", "MUSIC_DIR_VAR", "books_dir", "media_dir",
           "movies_dir", "music_dir"]

MUSIC_DIR_VAR = "MUSIC_DIR"
MOVIES_DIR_VAR = "MOVIES_DIR"
BOOKS_DIR_VAR = "BOOKS_DIR"


def media_dir(var: str, default: str) -> Path:
    """The directory *var* names, or *default* under the home directory.

    Resolved at call time, never at import: a caller's test that points ``HOME``
    or the variable somewhere else has usually already imported this module.
    An empty or whitespace-only value counts as unset — an exported-but-empty
    variable is a shell accident, and honouring it would resolve every path to
    the current working directory.
    """
    value = os.environ.get(var)
    if value is None or not value.strip():
        return (Path.home() / default).expanduser()
    return Path(value).expanduser()


def music_dir() -> Path:
    """``$MUSIC_DIR``, default ``~/.music``."""
    return media_dir(MUSIC_DIR_VAR, ".music")


def movies_dir() -> Path:
    """``$MOVIES_DIR``, default ``~/.movies``."""
    return media_dir(MOVIES_DIR_VAR, ".movies")


def books_dir() -> Path:
    """``$BOOKS_DIR``, default ``~/.books``."""
    return media_dir(BOOKS_DIR_VAR, ".books")
