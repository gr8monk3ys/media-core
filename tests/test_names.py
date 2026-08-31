"""The golden corpus is the definition of correct normalisation.

Before this package existed the corpus lived in three tools at once, duplicated
on purpose, so that a change landing in one turned the other two red. That was
the only thing making three copies of `normalise` agree. The copies are gone;
the corpus is not, because it is what says the *behaviour* did not change when
the code moved. Every case in it was passing in all three on 2026-08-27 and must
still pass here, byte for byte.

A change to this file is a change to what matching means in every consuming
repo. Silent drift makes a false match, and a false match hides a record
forever.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from media_core.names import fold, key, normalise, strip_article, strip_edition

CORPUS_PATH = Path(__file__).parent / "fixtures" / "name_normalisation_corpus.json"
CORPUS = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
IDS = [c["input"] or "<empty>" for c in CORPUS]


@pytest.mark.parametrize("case", CORPUS, ids=IDS)
def test_normalise_matches_corpus(case: dict[str, str]) -> None:
    assert normalise(case["input"]) == case["normalised"]


@pytest.mark.parametrize("case", CORPUS, ids=IDS)
def test_strip_article_matches_corpus(case: dict[str, str]) -> None:
    assert strip_article(case["input"]) == case["stripped_article"]


def test_corpus_is_not_empty() -> None:
    """A corpus that silently emptied would assert nothing at all."""
    assert len(CORPUS) >= 41


def test_corpus_is_the_one_the_repos_pinned() -> None:
    """The md5 the three tools' corpus tests were pinned to on 2026-08-27.

    Checked as bytes, not as parsed cases: a reformat that changed nothing about
    the assertions would still be a change to a file other tools hold a copy of,
    and it should be noticed rather than absorbed.
    """
    import hashlib

    digest = hashlib.md5(CORPUS_PATH.read_bytes()).hexdigest()  # noqa: S324 - not a security use
    assert digest == "f941657d076a09d7e4d1fe7ee2953063"


def test_strip_edition_keeps_case_and_punctuation() -> None:
    """The search-query form: edition noise gone, the original spelling intact."""
    assert strip_edition("In Utero (Deluxe Edition)") == "In Utero"
    assert strip_edition("Sgt. Pepper's Lonely Hearts Club Band") == (
        "Sgt. Pepper's Lonely Hearts Club Band"
    )


def test_key_strips_the_article_from_the_artist_but_not_the_title() -> None:
    """"The The" is an act whose name is an article, and a title that is one."""
    assert key("The Beatles", "The Beatles") == ("beatles", "the beatles")


def test_key_matches_across_the_two_spellings_of_an_act() -> None:
    assert key("The Beatles", "Revolver") == key("Beatles", "Revolver (Remastered)")


def test_fold_is_normalise_without_the_edition_stripping() -> None:
    """The identity that lets a caller ask whether a title carried noise."""
    for text in [c["input"] for c in CORPUS]:
        assert normalise(text) == fold(strip_edition(text))


def test_fold_keeps_the_edition_noise_normalise_removes() -> None:
    assert fold("In Utero (Deluxe Edition)") == "in utero deluxe edition"
    assert normalise("In Utero (Deluxe Edition)") == "in utero"


def test_fold_and_normalise_agree_when_there_is_no_edition_noise() -> None:
    """This equality IS the "is this the plain release?" question a consumer asks."""
    assert fold("In Utero") == normalise("In Utero") == "in utero"
    assert fold("Sgt. Pepper's") == normalise("Sgt. Pepper's") == "sgt pepper s"
