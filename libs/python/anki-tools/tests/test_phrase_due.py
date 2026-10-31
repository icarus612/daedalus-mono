"""Tests for the all-cards-new phrase-sourced word sweep."""

import pytest

from anki_tools.phrase_due import (
    SUSPENDED_QUEUE,
    build_taught_index,
    count_suspended_skipped,
    find_all_new_cards,
    headword_variants,
    normalize_form,
    resolve_phrase_note_ids,
    tokenize,
)

NEW = 0
LEARNING = 1
REVIEW = 2
RELEARNING = 3

NEW_QUEUE = 0
LEARN_QUEUE = 1
REVIEW_QUEUE = 2
BURIED_QUEUE = -2

PHRASE_NOTES = {10, 11, 12, 13, 14, 15, 16, 17}


def test_an_all_new_unsuspended_phrase_word_is_selected():
    rows = [(1, 10, NEW, NEW_QUEUE), (2, 10, NEW, NEW_QUEUE)]
    assert find_all_new_cards(rows, PHRASE_NOTES) == [1, 2]


def test_a_note_with_one_studied_card_is_left_to_counterpart_due():
    rows = [(1, 11, REVIEW, REVIEW_QUEUE), (2, 11, NEW, NEW_QUEUE)]
    assert find_all_new_cards(rows, PHRASE_NOTES) == []


def test_a_note_whose_cards_are_all_studied_is_not_a_hit():
    rows = [(1, 12, REVIEW, REVIEW_QUEUE), (2, 12, REVIEW, REVIEW_QUEUE)]
    assert find_all_new_cards(rows, PHRASE_NOTES) == []


def test_a_suspended_card_is_never_selected_and_is_counted():
    rows = [(1, 13, NEW, NEW_QUEUE), (2, 13, NEW, SUSPENDED_QUEUE)]
    assert find_all_new_cards(rows, PHRASE_NOTES) == [1]
    assert count_suspended_skipped(rows, PHRASE_NOTES) == 1


def test_a_fully_suspended_all_new_note_yields_nothing_at_all():
    rows = [(1, 14, NEW, SUSPENDED_QUEUE), (2, 14, NEW, SUSPENDED_QUEUE)]
    assert find_all_new_cards(rows, PHRASE_NOTES) == []
    assert count_suspended_skipped(rows, PHRASE_NOTES) == 2


def test_a_buried_new_card_is_still_selected():
    rows = [(1, 15, NEW, BURIED_QUEUE), (2, 15, NEW, NEW_QUEUE)]
    assert find_all_new_cards(rows, PHRASE_NOTES) == [1, 2]
    assert count_suspended_skipped(rows, PHRASE_NOTES) == 0


def test_a_note_outside_the_phrase_set_is_never_touched():
    rows = [(1, 99, NEW, NEW_QUEUE), (2, 99, NEW, NEW_QUEUE)]
    assert find_all_new_cards(rows, PHRASE_NOTES) == []
    assert count_suspended_skipped(rows, PHRASE_NOTES) == 0


@pytest.mark.parametrize(
    ("card_type", "queue", "selected"),
    [
        (NEW, NEW_QUEUE, True),
        (NEW, BURIED_QUEUE, True),
        (NEW, LEARN_QUEUE, True),
        (NEW, SUSPENDED_QUEUE, False),
        (LEARNING, LEARN_QUEUE, False),
        (REVIEW, REVIEW_QUEUE, False),
        (RELEARNING, LEARN_QUEUE, False),
        (LEARNING, SUSPENDED_QUEUE, False),
        (REVIEW, SUSPENDED_QUEUE, False),
    ],
)
def test_single_card_note_over_every_type_queue_combination(card_type, queue, selected):
    rows = [(1, 16, card_type, queue)]
    assert find_all_new_cards(rows, PHRASE_NOTES) == ([1] if selected else [])


@pytest.mark.parametrize("studied_type", [LEARNING, REVIEW, RELEARNING])
def test_any_non_new_sibling_disqualifies_the_whole_note(studied_type):
    rows = [(1, 17, studied_type, REVIEW_QUEUE), (2, 17, NEW, NEW_QUEUE)]
    assert find_all_new_cards(rows, PHRASE_NOTES) == []
    assert count_suspended_skipped(rows, PHRASE_NOTES) == 0


def test_results_are_sorted_regardless_of_input_order():
    rows = [(9, 10, NEW, NEW_QUEUE), (3, 10, NEW, NEW_QUEUE), (5, 10, NEW, NEW_QUEUE)]
    assert find_all_new_cards(rows, PHRASE_NOTES) == [3, 5, 9]


def test_four_card_verb_note_with_all_cards_new_is_selected_whole():
    rows = [(i, 10, NEW, NEW_QUEUE) for i in (1, 2, 3, 4)]
    assert find_all_new_cards(rows, PHRASE_NOTES) == [1, 2, 3, 4]


def test_suspended_count_ignores_notes_that_are_not_all_new():
    rows = [(1, 11, REVIEW, REVIEW_QUEUE), (2, 11, NEW, SUSPENDED_QUEUE)]
    assert count_suspended_skipped(rows, PHRASE_NOTES) == 0


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Чек", "чек"),
        ("ТУАЛЕТ", "туалет"),
        ("  можно  ", "можно"),
        ("ещё", "еще"),
        ("Ещё", "еще"),
        ("хорошо́", "хорошо"),
        ("по-английски", "по-английски"),
    ],
)
def test_normalize_form_folds_case_stress_and_yo(raw, expected):
    assert normalize_form(raw) == expected


def test_normalize_form_is_idempotent():
    once = normalize_form("Ещё́")
    assert normalize_form(once) == once


@pytest.mark.parametrize(
    ("headword", "expected"),
    [
        ("в / во", ["в", "во"]),
        ("как (conjunction)", ["как"]),
        ("чтобы / чтоб", ["чтобы", "чтоб"]),
        ("правда (noun)", ["правда"]),
        ("туалет", ["туалет"]),
        ("<b>чек</b>", ["чек"]),
        ("", []),
    ],
)
def test_headword_variants_splits_pairs_and_drops_qualifiers(headword, expected):
    assert headword_variants(headword) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Можно сфотографировать?", ["можно", "сфотографировать"]),
        ("Говорите по-английски?", ["говорите", "по-английски"]),
        ("Чек, пожалуйста", ["чек", "пожалуйста"]),
        ("<div>Где туалет?</div>", ["где", "туалет"]),
        ("Мне 25 лет", ["мне", "лет"]),
        ("", []),
    ],
)
def test_tokenize_keeps_hyphenated_words_and_drops_punctuation(text, expected):
    assert tokenize(text) == expected


def test_build_taught_index_maps_every_variant_to_its_note():
    index = build_taught_index([(1, ["в / во"]), (2, ["знакомиться", "познакомиться"])])
    assert index["в"] == {1}
    assert index["во"] == {1}
    assert index["познакомиться"] == {2}


def test_build_taught_index_keeps_both_homonym_notes_for_one_spelling():
    index = build_taught_index([(1, ["правда (noun)"]), (2, ["правда (adverb)"])])
    assert index["правда"] == {1, 2}


def test_resolve_phrase_note_ids_matches_tokens_inside_phrases():
    index = build_taught_index([(1, ["можно"]), (2, ["фотографировать"]), (3, ["дом"])])
    assert resolve_phrase_note_ids(["Можно сфотографировать?"], index) == {1}


def test_resolve_phrase_note_ids_resolves_a_stressed_yo_token():
    index = build_taught_index([(7, ["ещё"])])
    assert resolve_phrase_note_ids(["Ещё́ раз"], index) == {7}


def test_resolve_phrase_note_ids_reports_nothing_for_an_untaught_phrase():
    index = build_taught_index([(1, ["дом"])])
    assert resolve_phrase_note_ids(["Спокойной ночи"], index) == set()
