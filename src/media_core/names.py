"""Name normalisation for matching one release across catalogues.

Extracted verbatim from three copies that had to be kept identical by hand —
one each in the tools that sync a Spotify library, a Discogs collection and a
RateYourMusic account. Those tools share a file format, not a process, so
nothing at import time made them agree; a golden corpus did, duplicated into
each of their test suites. That corpus now lives beside this module
(``tests/fixtures/name_normalisation_corpus.json``) and is the definition of
correct: the functions here reproduce it byte-for-byte.

The rules stay conservative because the two mistakes cost differently. A false
match writes to a real account or hides a record from a queue forever; a missed
match only shows something twice. So only noise that is provably not part of a
title is stripped.
"""

from __future__ import annotations

import re

# Streaming services decorate album titles in ways collection databases do not:
# "(Deluxe Edition)", "- Remastered 2011", "(feat. ...)". These are editions of
# one record, not different records.
_EDITION = re.compile(
    r"\s*[\(\[-]\s*("
    r"deluxe|expanded|remaster|remastered|reissue|anniversary|special|"
    r"bonus|deluxe edition|super deluxe|legacy|collector|mono|stereo|"
    r"explicit|clean|international|japan|uk|us"
    r")\b.*$",
    re.IGNORECASE,
)
_BRACKETS = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]\s*$")
_PUNCT = re.compile(r"[^\w\s]")
_SPACE = re.compile(r"\s+")

_ARTICLES = ("the ", "a ", "an ")

__all__ = ["key", "normalise", "strip_article", "strip_edition"]


def strip_edition(text: str) -> str:
    """Drop edition noise and a trailing bracket, keeping case and punctuation.

    For search queries, where the original spelling still matters:
    ``"In Utero (Deluxe Edition)"`` -> ``"In Utero"``.
    """
    cleaned = _EDITION.sub("", text)
    return _BRACKETS.sub("", cleaned).strip()


def normalise(text: str) -> str:
    """Strip edition noise, punctuation and casing from a title or artist."""
    cleaned = _PUNCT.sub(" ", strip_edition(text))
    return _SPACE.sub(" ", cleaned).strip().casefold()


def strip_article(name: str) -> str:
    """Normalise and drop a leading article.

    Catalogues file "The Beatles" under Beatles about as often as not, so the
    two spellings have to collapse to one act.
    """
    stripped = normalise(name)
    for article in _ARTICLES:
        if stripped.startswith(article):
            return stripped[len(article) :]
    return stripped


def key(artist: str, title: str) -> tuple[str, str]:
    """The identity of a release for matching purposes.

    The artist loses its article (catalogues disagree about it) and the title
    keeps its own (an article can be the whole title — "The The").
    """
    return (strip_article(artist), normalise(title))
