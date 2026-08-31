"""Pin `normalise` to the exact expression the three repos ran before this one.

The 41-case corpus says the behaviour is right on the inputs anyone thought of.
This says it is right on the ones nobody did.

Two spellings of the same function were in circulation. One stripped edition
noise, brackets and punctuation in a single run; the other stripped whitespace
in between, because it factored the first two steps into a `strip_edition`
helper it needed on its own for search queries. `media_core.names` keeps the
second shape, because that helper is worth having. That is only safe if the two are the same function, so
the single-run expression is reproduced verbatim here as a reference oracle and
the two are compared over inputs built to hit the seams: brackets, dashes,
edition words, and every whitespace and separator codepoint — the places where
an extra `.strip()` could possibly matter.
"""

from __future__ import annotations

import random
import re

import pytest

from media_core.names import normalise

# The single-run implementation, verbatim as it stood before the extraction.
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


def reference_normalise(text: str) -> str:
    """The pre-extraction implementation, kept here only to be compared against."""
    cleaned = _EDITION.sub("", text)
    cleaned = _BRACKETS.sub("", cleaned)
    cleaned = _PUNCT.sub(" ", cleaned)
    return _SPACE.sub(" ", cleaned).strip().casefold()


ALPHABET = list(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    " \t\n\r\v\f\x1c\x1d\x1e\x1f  ​　"
    "()[]-—–.,'!?#•=†/&+*:;\"@$%^_`~{}|<>\\"
) + list("ÁáÆæÇçÉéÍíÑñÓóÖöÚúÜüßÅåØøÐðÞþ日本語シーナリィ한글Кириллица🎵")
EDITION_WORDS = [
    "deluxe", "Remastered 2011", "Mono", "stereo", "(feat. Frank Ocean)", "Edition",
    "The", "A", "an", "Kid A", "Super Deluxe", "japan", "uk", "us", "clean",
    "explicit", "legacy", "collector", "anniversary", "bonus", "expanded", "reissue",
]


def _inputs(count: int) -> list[str]:
    rng = random.Random(20260831)  # noqa: S311 - generating test inputs, not secrets
    out = []
    for i in range(count):
        if i % 2:
            body = " ".join(rng.choice(EDITION_WORDS) for _ in range(rng.randint(0, 4)))
            out.append(rng.choice(["", "(", "["]) + body + rng.choice(["", ")", "]", " - "]))
        else:
            out.append("".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 24))))
    return out


@pytest.mark.parametrize("text", _inputs(2000), ids=range(2000))
def test_agrees_with_the_pre_extraction_implementation(text: str) -> None:
    assert normalise(text) == reference_normalise(text)


def test_agrees_on_every_whitespace_and_separator_codepoint() -> None:
    """The only place the extra `.strip()` could bite: what counts as whitespace.

    `str.strip()` and the regex `\\s` do not have to agree, and the extracted
    version strips between two substitutions where the original did not.
    """
    suspects = [chr(cp) for cp in range(0x3000) if chr(cp).isspace() or _SPACE.match(chr(cp))]
    assert len(suspects) > 20  # the search would pass vacuously if this narrowed
    for ch in suspects:
        for text in (ch, ch + "x", "x" + ch, ch + "The Beatles" + ch, "(a)" + ch):
            assert normalise(text) == reference_normalise(text), repr(text)
