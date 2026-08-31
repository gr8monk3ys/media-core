# media-core

The part several catalogue tools have to agree on: how a release name is
normalised, where the shared files live, and the envelope those files are
written in.

Tools that sync a music, film or book collection end up talking to each other
through one JSON file each in a shared directory. They have nothing else in
common — different APIs, different databases, different credentials — so the
tempting "one big pipeline" is the wrong shape. What they do share is a
handshake, and a handshake only works if every side implements it identically.

This package is that handshake and nothing else. Zero runtime dependencies,
pure functions, no network, no account, no data.

```bash
pip install "media-core @ git+https://github.com/gr8monk3ys/media-core@v0.1.0"
```

## `media_core.names` — deciding two catalogues mean one release

There is no shared identifier between a streaming service and a collection
database: no ISRC in the export, no MBID, no release id. Matching is by name,
which is fuzzy, and the two mistakes cost very differently. A **false** match
writes to a real account or hides a record from a queue forever. A **missed**
match only shows something twice. So the rules strip only noise that is
provably not part of a title.

```python
from media_core.names import key, normalise, strip_article, strip_edition

normalise("In Utero (Deluxe Edition)")     # 'in utero'
normalise("OK Computer - Remastered 2011") # 'ok computer'
strip_article("The Beatles")               # 'beatles'
strip_edition("In Utero (Deluxe Edition)") # 'In Utero'  — for a search query
key("The Beatles", "Revolver")             # ('beatles', 'revolver')
```

`key` drops the artist's article but keeps the title's, because catalogues
disagree about "The Beatles" vs "Beatles" while an article can be the whole
title — The The released *The The*.

### The corpus is the specification

`tests/fixtures/name_normalisation_corpus.json` holds 41 cases with their exact
expected output, and it is the definition of correct here, not an example of it.
It got that status the hard way: three repos each carried a byte-identical copy
of these functions, kept in step only by the same corpus file duplicated into
each test suite, so that a change landing in one repo turned the other two red.
Those copies are gone, the corpus is not. It still says the behaviour did not
change when the code moved.

Changing a case changes what matching means everywhere downstream. Treat the
file as an interface.

## `media_core.paths` — where the shared files live

```python
from media_core.paths import books_dir, movies_dir, music_dir

music_dir()   # $MUSIC_DIR,  default ~/.music
movies_dir()  # $MOVIES_DIR, default ~/.movies
books_dir()   # $BOOKS_DIR,  default ~/.books
```

The variables are deliberately unprefixed. Each tool has a settings prefix the
others know nothing about, so an unprefixed name is the only one they can all
honour. Resolution happens per call, never at import, so pointing `HOME` or the
variable elsewhere in a test works. An empty or whitespace-only value counts as
unset, because `export MUSIC_DIR=` is a shell accident and resolving it to the
current directory would silently write the collection into whatever directory
the tool happened to start in.

## `media_core.export` — the versioned envelope

```python
from media_core.export import build_export, read_export, write_export

doc = build_export(
    "discogs/1",
    generated_at,                    # a string the caller supplies
    username="…",
    collection=[...], wantlist=[...],  # sections, in the order you pass them
)
write_export(doc, music_dir() / "discogs.json")

# in the consuming tool, a process and a repo away:
data = read_export(music_dir() / "discogs.json", "discogs/1")
```

The envelope is `schema`, `generated_at`, an optional `username`, your sections
in order, and an optional `coverage` last.

`schema` is the whole compatibility contract, which is why `read_export`
**asserts** it instead of trusting it. The consumer is a different program than
the writer, and "no rows" is the one answer it must never reach by accident — a
document it was not written to read has to fail loudly rather than parse into
nothing.

Building the rows is not this package's business; that needs a database, an API
cache and an account. `build_export` takes rows already built, which is what
lets it be pure and lets a tool assert its own document's shape in a test
without a network or a clock.

Writes are atomic. A plain write truncates first, so an interruption lands in
exactly the window a reader is walking through; this writes a sibling file and
renames it, and `os.replace` is atomic on POSIX and Windows.

### Why cosmetics are arguments

Five tools wrote this envelope independently and agreed on everything that
matters. They did not agree on indentation, `ensure_ascii`, or a trailing
newline, and each of those splits them at least two against two. Rather than
impose one, each is a keyword argument whose default is what the majority
already wrote:

| | `indent` | `ensure_ascii` | trailing newline |
|---|---|---|---|
| default (rym, goodreads, letterboxd) | `1` | `False` | yes |
| discogs | `1` | `True` | no |
| spotify | `None` | `True` | no |

A tool passing its own values keeps its file byte-identical, so adopting this
package shows up as a diff in the code and no diff at all in the output.

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run mypy
```

MIT.
