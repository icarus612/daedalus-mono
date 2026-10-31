import unicodedata

import pytest

from anki_tools import phrase_words as pw

GOVORIT = pw.TaughtWord(
    headword="говорить / сказать",
    note_id=1790557980081,
    forms=("говорить", "сказать"),
)
VSTRECHA = pw.TaughtWord(headword="встреча", note_id=1, forms=("встреча", "встречи"))
KAKOY = pw.TaughtWord(
    headword="какой", note_id=2, forms=("какой", "какая", "какое", "какие")
)
VSE = pw.TaughtWord(headword="всё", note_id=3, forms=("все",))


def index_of(*words):
    return pw.build_index(words)


def test_normalize_lowercases_and_composes():
    assert pw.normalize("Ваше") == "ваше"


def test_normalize_strips_acute_and_grave_stress():
    assert pw.normalize("говори́ть") == "говорить"
    assert pw.normalize("что̀") == "что"


def test_normalize_folds_yo_to_ye():
    assert pw.normalize("ещё") == "еще"


def test_normalize_folds_a_decomposed_yo():
    decomposed = unicodedata.normalize("NFD", "ещё")
    assert "ё" not in decomposed
    assert pw.normalize(decomposed) == "еще"


def test_normalize_folds_a_stressed_yo():
    assert pw.normalize("ё́лка") == "елка"


def test_normalize_is_idempotent():
    once = pw.normalize("Споко́йной")
    assert pw.normalize(once) == once


def test_normalize_output_is_nfc():
    out = pw.normalize(unicodedata.normalize("NFD", "Сего́дня"))
    assert out == unicodedata.normalize("NFC", out)


def test_normalize_without_renormalizing_would_leave_a_combining_mark():
    """Positive control for the second NFC pass: a decomposed ё reaches the
    fold only once it has been composed, and the leftover diaeresis has to
    be gone from the result."""
    out = pw.normalize(unicodedata.normalize("NFD", "ещё"))
    assert "̈" not in out and "ё" not in out


def test_tokenize_splits_a_phrase_into_words():
    assert pw.tokenize("Как дела?") == ["как", "дела"]


def test_tokenize_keeps_a_hyphenated_adverb_whole():
    assert pw.tokenize("Вы говорите по-английски?") == [
        "вы",
        "говорите",
        "по-английски",
    ]


def test_tokenize_keeps_po_russki_whole():
    assert "по-русски" in pw.tokenize("Я немного говорю по-русски")


def test_tokenize_drops_html_markup_and_entities():
    assert pw.tokenize("Доброе <div>утро</div>&#x27;") == ["доброе", "утро"]


def test_tokenize_drops_latin_and_digits():
    assert pw.tokenize("Rank 633 интернет") == ["интернет"]


def test_tokenize_drops_an_em_dash_placeholder():
    assert pw.tokenize("—") == []


def test_tokenize_does_not_keep_a_trailing_hyphen():
    assert pw.tokenize("по- русски") == ["по", "русски"]


def test_tokenize_normalizes_as_it_goes():
    assert pw.tokenize("Споко́йной но́чи") == ["спокойной", "ночи"]


@pytest.mark.parametrize(
    "name",
    [
        "Russian - Immutable Words (Ellis Version)",
        "Russian - Mutable Nouns (Ellis Version)",
        "Russian - Mutable Verbs (Ellis Version)",
        "Russian - Mutable Adverbs (Ellis Version)",
    ],
)
def test_taught_note_types_are_the_mutable_and_immutable_families(name):
    assert pw.is_taught_note_type(name)


@pytest.mark.parametrize(
    "name",
    [
        "Russian - Common Words (Ellis Version) ",
        "Russian - Alphabet",
        "LlamaNote",
        "Japanese - Common Words (Ellis Version)",
    ],
)
def test_the_phrase_type_and_foreign_types_are_not_taught(name):
    assert not pw.is_taught_note_type(name)


def test_taught_word_reads_a_noun_headword_and_its_stored_inflections():
    word = pw.taught_word(
        7,
        ["Russian", "Translation", "Plural", "Genitive Pl", "Examples"],
        ["сторона́", "side", "сто́роны", "сто́рон", "в сторону"],
    )
    assert word.headword == "сторона́"
    assert set(word.forms) == {"сторона", "стороны", "сторон"}


def test_taught_word_joins_both_verb_aspects_as_the_headword():
    word = pw.taught_word(
        8,
        ["Imperfective", "Perfective", "Translation", "я (1sg)"],
        ["мочь", "смочь", "can", "могу́"],
    )
    assert word.headword == "мочь / смочь"
    assert set(word.forms) == {"мочь", "смочь", "могу"}


def test_taught_word_strips_an_immutable_qualifier_from_the_forms():
    word = pw.taught_word(9, ["Russian", "Translation"], ["как (conjunction)", "as"])
    assert word.forms == ("как",)
    assert word.headword == "как (conjunction)"


def test_taught_word_ignores_prose_fields():
    word = pw.taught_word(
        10,
        ["Russian", "Additional Info", "Examples", "Case / Preposition"],
        ["чек", "счёт в ресторане", "дайте чек", "винительный падеж"],
    )
    assert word.forms == ("чек",)


def test_taught_word_skips_an_em_dash_placeholder_aspect():
    word = pw.taught_word(
        12,
        ["Imperfective", "Perfective", "Translation"],
        ["заблудиться", "\u2014", "get lost"],
    )
    assert word.headword == "заблудиться"


def test_taught_word_is_none_when_every_headword_field_is_a_placeholder():
    assert pw.taught_word(13, ["Russian", "Translation"], ["\u2014", "nothing"]) is None


def test_taught_word_is_none_without_a_headword_field():
    assert pw.taught_word(11, ["Front", "Back"], ["cat", "кошка"]) is None


def test_build_index_keys_every_surface_form():
    index = index_of(VSTRECHA)
    assert set(index) == {"встреча", "встречи"}
    assert index["встречи"] is VSTRECHA


def test_build_index_keeps_the_first_word_to_claim_a_form():
    other = pw.TaughtWord(headword="встречать", note_id=4, forms=("встречи",))
    index = pw.build_index([VSTRECHA, other])
    assert index["встречи"] is VSTRECHA


def test_resolve_matches_an_exact_form():
    got = pw.resolve("встреча", index_of(VSTRECHA))
    assert got.word is VSTRECHA and got.via == pw.VIA_SURFACE


def test_resolve_matches_a_stored_inflection_before_guessing_a_lemma():
    got = pw.resolve("встречи", index_of(VSTRECHA))
    assert got.matched == "встречи" and got.via == pw.VIA_SURFACE


def test_resolve_matches_through_stripped_stress():
    got = pw.resolve("встре́ча", index_of(VSTRECHA))
    assert got.word is VSTRECHA


def test_resolve_matches_through_folded_yo():
    got = pw.resolve("всё", index_of(VSE))
    assert got.word is VSE


def test_resolve_lemmatizes_a_first_person_verb_to_its_infinitive():
    got = pw.resolve("говорю", index_of(GOVORIT))
    assert got.word is GOVORIT
    assert got.matched == "говорить"
    assert got.via == pw.VIA_LEMMA


def test_resolve_lemmatizes_a_second_person_plural_verb():
    assert pw.resolve("говорите", index_of(GOVORIT)).matched == "говорить"


def test_resolve_undoes_the_l_epenthesis_of_a_first_person_form():
    lyubit = pw.TaughtWord(
        headword="любить / полюбить", note_id=5, forms=("любить", "полюбить")
    )
    assert pw.resolve("люблю", index_of(lyubit)).matched == "любить"


def test_resolve_lemmatizes_an_ovat_verb_from_its_present_stem():
    advise = pw.TaughtWord(
        headword="советовать / посоветовать",
        note_id=6,
        forms=("советовать", "посоветовать"),
    )
    assert pw.resolve("посоветуете", index_of(advise)).matched == "посоветовать"


def test_resolve_lemmatizes_a_reflexive_verb_keeping_the_particle():
    found = pw.TaughtWord(
        headword="находиться / найтись",
        note_id=7,
        forms=("находиться", "найтись"),
    )
    assert pw.resolve("находится", index_of(found)).matched == "находиться"


def test_resolve_reaches_a_suppletive_stem_through_a_stored_present_form():
    byt = pw.TaughtWord(
        headword="быть / побыть", note_id=8, forms=("быть", "побыть", "буду")
    )
    assert pw.resolve("будет", index_of(byt)).matched == "буду"


def test_resolve_lemmatizes_an_accusative_noun():
    side = pw.TaughtWord(headword="сторона", note_id=9, forms=("сторона",))
    assert pw.resolve("сторону", index_of(side)).matched == "сторона"


def test_resolve_lemmatizes_a_genitive_plural_with_a_null_ending():
    problem = pw.TaughtWord(headword="проблема", note_id=10, forms=("проблема",))
    assert pw.resolve("проблем", index_of(problem)).matched == "проблема"


def test_resolve_prefers_the_longer_candidate_over_a_shorter_homograph():
    kak = pw.TaughtWord(headword="как (conjunction)", note_id=11, forms=("как",))
    assert pw.resolve("какую", pw.build_index([kak, KAKOY])).word is KAKOY


def test_resolve_prefers_an_adjective_over_its_derived_adverb():
    calm_adj = pw.TaughtWord(headword="спокойный", note_id=12, forms=("спокойный",))
    calm_adv = pw.TaughtWord(headword="спокойно", note_id=13, forms=("спокойно",))
    got = pw.resolve("спокойной", pw.build_index([calm_adj, calm_adv]))
    assert got.word is calm_adj


def test_resolve_returns_none_for_a_word_nothing_teaches():
    """Positive control: without this, a report of zero missing words would
    say nothing about whether the resolver can fail at all."""
    assert pw.resolve("пожаловать", index_of(GOVORIT, VSTRECHA, KAKOY)) is None


@pytest.mark.parametrize("absent", ["трансформатор", "бутерброд", "зеленоватый"])
def test_resolve_does_not_invent_a_lemma_for_an_untaught_word(absent):
    assert pw.resolve(absent, index_of(GOVORIT, VSTRECHA, KAKOY, VSE)) is None


def test_resolve_can_be_asked_to_skip_lemmatization():
    assert pw.resolve("говорю", index_of(GOVORIT), use_lemma=False) is None
    assert pw.resolve("говорить", index_of(GOVORIT), use_lemma=False) is not None


@pytest.mark.parametrize(
    "rows,expected",
    [
        ([(0, 0), (0, 0)], pw.ALL_NEW),
        ([(0, 0)], pw.ALL_NEW),
        ([(2, 2), (2, 2)], pw.STUDIED),
        ([(1, 1), (2, 2)], pw.STUDIED),
        ([(3, 2)], pw.STUDIED),
        ([(0, 0), (2, 2)], pw.PART_NEW),
        ([(2, 2), (0, 0), (2, 2)], pw.PART_NEW),
        ([(0, -1), (0, -1)], pw.SUSPENDED),
        ([(2, -1)], pw.SUSPENDED),
        ([(0, -1), (0, 0)], pw.ALL_NEW),
        ([(0, -1), (2, 2)], pw.STUDIED),
        ([(0, -1), (0, 0), (2, 2)], pw.PART_NEW),
        ([], pw.NO_CARDS),
    ],
)
def test_card_state_over_every_type_queue_combination(rows, expected):
    assert pw.card_state(rows) == expected


def test_card_state_counts_a_suspended_new_card_as_out_of_circulation():
    assert pw.card_state([(0, -1), (2, 2)]) == pw.STUDIED


def test_audit_reports_a_single_word_entry_and_a_phrase_through_one_path():
    index = index_of(VSTRECHA, GOVORIT)
    records = pw.audit(
        ["Встреча", "Вы говорите по-английски?"],
        index,
        {VSTRECHA.note_id: [(2, 2)], GOVORIT.note_id: [(2, 2)]},
    )
    by_token = {r.token: r for r in records}
    assert by_token["встреча"].state == pw.STUDIED
    assert by_token["говорите"].state == pw.STUDIED
    assert by_token["по-английски"].state == pw.MISSING


def test_audit_keeps_every_phrase_a_token_came_from():
    records = pw.audit(["Как дела?", "Как Вас зовут?"], index_of(), {})
    kak = next(r for r in records if r.token == "как")
    assert kak.phrases == ("Как дела?", "Как Вас зовут?")


def test_audit_lists_a_token_once_however_often_it_appears():
    records = pw.audit(["Как как как"], index_of(), {})
    assert [r.token for r in records] == ["как"]


def test_audit_orders_records_by_token():
    records = pw.audit(["Яблоко берег"], index_of(), {})
    assert [r.token for r in records] == ["берег", "яблоко"]


def test_audit_marks_a_resolved_word_with_no_cards():
    records = pw.audit(["встреча"], index_of(VSTRECHA), {})
    assert records[0].state == pw.NO_CARDS


def test_audit_records_how_each_word_resolved():
    records = pw.audit(["Я говорю"], index_of(GOVORIT), {GOVORIT.note_id: [(0, 0)]})
    govoryu = next(r for r in records if r.token == "говорю")
    assert govoryu.via == pw.VIA_LEMMA
    assert govoryu.matched == "говорить"
    assert govoryu.headword == "говорить / сказать"
    assert govoryu.state == pw.ALL_NEW


def test_audit_leaves_a_missing_word_without_a_headword():
    records = pw.audit(["пожаловать"], index_of(VSTRECHA), {})
    assert records[0].headword is None and records[0].via == ""


def test_group_by_state_covers_every_state_key():
    records = pw.audit(
        ["встреча пожаловать"], index_of(VSTRECHA), {VSTRECHA.note_id: [(2, 2)]}
    )
    grouped = pw.group_by_state(records)
    assert set(grouped) == set(pw.STATES)
    assert [r.token for r in grouped[pw.STUDIED]] == ["встреча"]
    assert [r.token for r in grouped[pw.MISSING]] == ["пожаловать"]


def test_group_by_state_totals_match_the_record_count():
    records = pw.audit(
        ["Как дела?", "Я говорю по-русски"],
        index_of(GOVORIT, VSTRECHA),
        {GOVORIT.note_id: [(2, 2)]},
    )
    grouped = pw.group_by_state(records)
    assert sum(len(v) for v in grouped.values()) == len(records)
