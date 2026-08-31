"""The versioned envelope every interchange file shares.

Five tools each wrote their own ``build_export`` / ``write_export`` pair, under
those exact names, and agreed by coincidence on the parts that matter: a
``schema`` string as the compatibility contract, a ``generated_at`` timestamp,
then one or more named lists of rows. What they disagreed on was cosmetic —
indentation, ``ensure_ascii``, a trailing newline — and each of those splits the
five at least two-to-two, so each is a keyword argument here rather than a
decision imposed on everyone. The default is what the majority already wrote.

The *rows* are not this module's business. Building them needs a database, an
API cache, an account — everything a tool has that the other four do not. This
module takes rows already built and puts an envelope round them, which is why it
can be pure, dependency-free, and tested without a network.

    doc = build_export("discogs/1", generated_at, username="…",
                       collection=[...], wantlist=[...])
    write_export(doc, path)

``read_export`` is the other half of the contract, and the reason the schema
string exists: a consumer asserts the version rather than trusting it, so a file
it was not written to read fails loudly instead of producing wrong rows.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

__all__ = ["ExportError", "build_export", "read_export", "schema_version", "write_export"]

# "discogs/1", "music-library/1" — a name and an integer version. Asserting the
# shape here catches a typo at write time; without it a bad schema string only
# surfaces in another repo, as an unreadable file.
_SCHEMA_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*/(\d+)$")


class ExportError(Exception):
    """An export file is missing, malformed, or a version we cannot read."""


def schema_version(schema: str) -> int:
    """The integer version out of a ``name/N`` schema string."""
    match = _SCHEMA_RE.match(schema)
    if match is None:
        raise ExportError(f"{schema!r} is not a 'name/version' schema string")
    return int(match.group(1))


def build_export(
    schema: str,
    generated_at: str,
    *,
    username: str | None = None,
    coverage: dict[str, Any] | None = None,
    **sections: Any,
) -> dict[str, Any]:
    """Wrap already-built *sections* in the shared envelope.

    *sections* are emitted in the order they are passed, between the header and
    ``coverage``, which reproduces the field order all five hand-written
    documents happened to use. ``username`` (2 tools) and ``coverage`` (3) are
    named because more than one tool emits them in the same place; anything only
    one tool emits is just another section.

    *generated_at* is a string the caller supplies rather than a clock this
    module reads, so an export is a pure function of its inputs and its shape can
    be asserted in a test without freezing time.
    """
    schema_version(schema)  # raises on a malformed schema string
    if not generated_at:
        raise ExportError("generated_at must be a non-empty timestamp string")
    doc: dict[str, Any] = {"schema": schema, "generated_at": generated_at}
    if username is not None:
        doc["username"] = username
    doc.update(sections)
    if coverage is not None:
        doc["coverage"] = coverage
    return doc


def write_export(
    doc: dict[str, Any],
    path: str | Path,
    *,
    indent: int | None = 1,
    ensure_ascii: bool = False,
    newline: bool = True,
) -> Path:
    """Write *doc* to *path* atomically and return where it landed.

    A plain write truncates first, so an interrupt lands in exactly the window a
    consumer is reading through. Write a sibling and rename — ``os.replace`` is
    atomic on POSIX and Windows, so a reader sees either the old file or the new
    one, never half of either.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, indent=indent, ensure_ascii=ensure_ascii)
    if newline:
        text += "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    return path


def read_export(path: str | Path, schema: str | None = None) -> dict[str, Any]:
    """Parse an export file, refusing anything this build cannot read.

    Every failure is an :class:`ExportError` naming the file, because the caller
    is a different tool than the writer and "no rows" is the one answer it must
    never get by accident. When *schema* is given it is asserted exactly: a
    silently-changed document shape would otherwise surface as wrong output
    rather than as an error.
    """
    target = Path(path)
    if not target.exists():
        raise ExportError(f"No export file at {target}.")
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExportError(f"{target} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ExportError(f"{target} is not an object")
    if schema is not None and data.get("schema") != schema:
        raise ExportError(
            f"{target} declares schema {data.get('schema')!r}; this build reads {schema!r}."
        )
    return data
