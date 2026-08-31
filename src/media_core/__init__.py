"""Code the music, film and book tools share because they share a file format.

Three things were duplicated across five repos that talk to each other only
through JSON files in ``~/.music``, ``~/.movies`` and ``~/.books``:

* :mod:`media_core.names` — the normalisation that decides two catalogues are
  describing one release, pinned to a golden corpus.
* :mod:`media_core.paths` — where those files live.
* :mod:`media_core.export` — the versioned envelope they are written in.

Nothing here knows about any account, API or database. That is the whole point:
each tool keeps its own rows and its own credentials, and shares only the part
that has to agree.
"""

from media_core.export import ExportError, build_export, read_export, write_export
from media_core.names import fold, key, normalise, strip_article, strip_edition
from media_core.paths import books_dir, media_dir, movies_dir, music_dir

__version__ = "0.1.1"

__all__ = [
    "ExportError",
    "books_dir",
    "build_export",
    "fold",
    "key",
    "media_dir",
    "movies_dir",
    "music_dir",
    "normalise",
    "read_export",
    "strip_article",
    "strip_edition",
    "write_export",
]
