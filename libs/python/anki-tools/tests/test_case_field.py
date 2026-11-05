"""Contract tests for the `Case` field: the cases a word governs, read from
a government TSV and rendered as pills.
"""

import re
from pathlib import Path

import pytest

from anki_tools import case_field, distinction
from anki_tools.immutable_words_plan import FIELD_NAMES, WordRow, parse_word_list

REAL_SOURCE_PATH = Path(__file__).resolve().parent / "data" / "source-word-list.md"


@pytest.fixture(scope="module")
def real_rows():
    with open(REAL_SOURCE_PATH, encoding="utf-8") as fh:
        return parse_word_list(fh.read())


@pytest.mark.parametrize(
    "info,expected",
    [
        ("Genitive", "Genitive"),
        ("Dative", "Dative"),
        ("Prepositional", "Prepositional"),
        ("Instrumental", "Instrumental"),
        ("Accusative", "Accusative"),
        (
            "Accusative for motion in; Prepositional for location",
            "Accusative or Prepositional",
        ),
        (
            'Instrumental for "with"; Genitive for "from / since"',
            "Instrumental or Genitive",
        ),
        ("Genitive — always", "Genitive"),
        ("Static location", ""),
        ("", ""),
    ],
)
def test_case_name_cases(info, expected):
    assert case_field.case_name(info) == expected


def test_dash_commentary_is_not_read_as_a_second_case():
    info = "Dative — one of the few Genitive-looking ones that takes Dative"
    assert case_field.case_name(info) == "Dative"


def test_case_order_follows_the_cell_not_the_table():
    assert case_field.case_name("Genitive; Accusative") == "Genitive or Accusative"
    assert case_field.case_name("Accusative; Genitive") == "Accusative or Genitive"


def test_poznravlyayu_style_row_names_the_governed_case_only_in_raw_info():
    info = "1st-person present of поздравлять; often + с + instrumental"
    assert case_field.case_name(info) == "Instrumental"


def test_every_real_preposition_info_names_a_case(real_rows):
    prepositions = [r for r in real_rows if r.pos == "Prepositions"]
    assert len(prepositions) == 44
    named = {r.russian: case_field.case_name(r.info) for r in prepositions}
    assert [w for w, tag in named.items() if not tag] == []
    assert named["о / об"] == "Prepositional"
    assert named["насчёт"] == "Genitive"
    assert named["в / во"] == "Accusative or Prepositional"
    assert named["вопреки"] == "Dative"


@pytest.mark.parametrize("name", ["case_name_for_row", "add_case_row"])
def test_removed_helpers_are_gone(name):
    assert not hasattr(case_field, name)


def test_the_module_does_not_import_case_pill():
    assert not hasattr(case_field, "case_pill")


def test_case_is_a_field_of_the_note_type():
    assert case_field.CASE_FIELD in FIELD_NAMES


def test_every_row_supplies_a_value_for_every_field(real_rows):
    for row in real_rows:
        assert len(row.fields()) == len(FIELD_NAMES)


HEADER = "guid\tcases\tmeaning→case\tfamily\theadword"


def write_tsv(tmp_path, rows, header=HEADER, name="case-government.tsv"):
    path = tmp_path / name
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


MULTI_LINE_CELL = "in / at (where) => Prepositional || into (where/what) => Accusative"


def test_constants_have_the_pinned_values():
    assert case_field.LINE_CASE_SEPARATOR == " || "
    assert case_field.LINE_CASE_ARROW == " => "
    assert case_field.CASE_GOVERNMENT_PATH == (
        Path(case_field.__file__).parent / "data" / "case-government.tsv"
    )


def test_loader_reads_cases_in_file_order_and_line_cases(tmp_path):
    path = write_tsv(
        tmp_path,
        [
            f"g1\tAccusative, Prepositional\t{MULTI_LINE_CELL}\tx\tв",
            "g2\tGenitive\t\tx\tоколо",
        ],
    )
    government = case_field.load_case_government(path)
    assert set(government) == {"g1", "g2"}
    assert government["g1"].cases == ("Accusative", "Prepositional")
    assert dict(government["g1"].line_cases) == {
        "in / at (where)": "Prepositional",
        "into (where/what)": "Accusative",
    }
    assert government["g2"].cases == ("Genitive",)
    assert dict(government["g2"].line_cases) == {}


def test_loader_accepts_str_path_and_ascii_arrow_header(tmp_path):
    path = write_tsv(
        tmp_path,
        ["g1\tAccusative, Prepositional\tin => Prepositional"],
        header="guid\tcases\tmeaning->case",
    )
    government = case_field.load_case_government(str(path))
    assert dict(government["g1"].line_cases) == {"in": "Prepositional"}


def test_loader_matches_headers_casefolded_stripped_in_any_order(tmp_path):
    path = write_tsv(
        tmp_path,
        ["Genitive\tg1"],
        header=" CASES \t Guid ",
    )
    assert case_field.load_case_government(path)["g1"].cases == ("Genitive",)


def test_loader_ignores_extra_columns_and_blank_lines(tmp_path):
    path = tmp_path / "gov.tsv"
    path.write_text(
        "\nguid\tnote type\tcases\tstatus\n\ng1\tImmutable\tDative\tok\n\n",
        encoding="utf-8",
    )
    assert set(case_field.load_case_government(path)) == {"g1"}


def test_loader_does_not_interpret_quotes(tmp_path):
    path = write_tsv(
        tmp_path,
        ['g1\tAccusative, Prepositional\t"in" => Prepositional\tx\tв'],
    )
    government = case_field.load_case_government(path)
    assert dict(government["g1"].line_cases) == {'"in"': "Prepositional"}


def test_blank_cases_row_yields_no_entry(tmp_path):
    path = write_tsv(tmp_path, ["g1\t   \t\tx\tв", "g2\tGenitive\t\tx\tоколо"])
    assert set(case_field.load_case_government(path)) == {"g2"}


def test_line_case_splits_on_the_first_arrow_and_strips(tmp_path):
    path = write_tsv(
        tmp_path,
        ["g1\tDative, Genitive\t  a => b => Dative  ||  c => Genitive \tx\tк"],
    )
    # the value "b => Dative" is not canonical, so the first-arrow split fails
    with pytest.raises(ValueError):
        case_field.load_case_government(path)
    ok = write_tsv(
        tmp_path,
        ["g1\tDative, Genitive\t  a b =>  Dative  ||  c => Genitive \tx\tк"],
        name="ok.tsv",
    )
    assert dict(case_field.load_case_government(ok)["g1"].line_cases) == {
        "a b": "Dative",
        "c": "Genitive",
    }


GOOD_ROW = f"g1\tAccusative, Prepositional\t{MULTI_LINE_CELL}\tx\tв"


@pytest.mark.parametrize(
    "bad_rows,bad_header,message",
    [
        (["g1\tAccusativ\t\tx\tв"], HEADER, "Accusativ"),
        (["g1\tAccusative, Accusative\t\tx\tв"], HEADER, "Accusative"),
        (
            ["g1\tAccusative\t\tx\tв", "g1\tGenitive\t\tx\tв"],
            HEADER,
            "g1",
        ),
        (
            ["g1\tAccusative, Prepositional\tin => Dative\tx\tв"],
            HEADER,
            "Dative",
        ),
        (
            ["g1\tAccusative, Prepositional\tin => Locative\tx\tв"],
            HEADER,
            "Locative",
        ),
        (["g1\tAccusative, Prepositional\tin\tx\tв"], HEADER, "in"),
        (
            ["g1\tAccusative, Prepositional\t => Accusative\tx\tв"],
            HEADER,
            "",
        ),
        (["Accusative\tx\tв"], "cases\tfamily\theadword", "guid"),
        (["g1\tx\tв"], "guid\tfamily\theadword", "cases"),
    ],
    ids=[
        "unknown-case",
        "duplicate-case-in-cell",
        "duplicate-guid",
        "line-case-not-in-cases",
        "line-case-not-canonical",
        "entry-without-arrow",
        "empty-gloss-key",
        "missing-guid-header",
        "missing-cases-header",
    ],
)
def test_loader_rejects_malformed_files_but_loads_the_clean_twin(
    tmp_path, bad_rows, bad_header, message
):
    clean = write_tsv(tmp_path, [GOOD_ROW], name="clean.tsv")
    assert set(case_field.load_case_government(clean)) == {"g1"}
    bad = write_tsv(tmp_path, bad_rows, header=bad_header, name="bad.tsv")
    with pytest.raises(ValueError, match=re.escape(message) if message else None):
        case_field.load_case_government(bad)


def test_missing_explicit_path_raises_but_an_existing_one_loads(tmp_path):
    existing = write_tsv(tmp_path, [GOOD_ROW])
    assert case_field.load_case_government(existing)
    with pytest.raises(FileNotFoundError):
        case_field.load_case_government(tmp_path / "absent.tsv")


def test_default_path_missing_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(case_field, "CASE_GOVERNMENT_PATH", tmp_path / "absent.tsv")
    assert case_field.load_case_government() == {}


def test_default_path_present_is_read(monkeypatch, tmp_path):
    path = write_tsv(tmp_path, [GOOD_ROW])
    monkeypatch.setattr(case_field, "CASE_GOVERNMENT_PATH", path)
    assert set(case_field.load_case_government()) == {"g1"}


@pytest.mark.parametrize(
    "guid,expected",
    [
        ("g1", "Accusative, Prepositional"),
        ("g2", "Genitive"),
        ("unlisted", ""),
        ("", ""),
    ],
)
def test_case_value_joins_cases_and_blanks_unlisted(tmp_path, guid, expected):
    path = write_tsv(tmp_path, [GOOD_ROW, "g2\tGenitive\t\tx\tоколо"])
    government = case_field.load_case_government(path)
    assert case_field.case_value(government, guid) == expected


def test_case_value_on_an_empty_mapping_is_blank():
    assert case_field.case_value({}, "g1") == ""


def test_default_government_is_cached_and_follows_the_default_path(
    monkeypatch, tmp_path
):
    case_field.default_government.cache_clear()
    monkeypatch.setattr(
        case_field, "CASE_GOVERNMENT_PATH", write_tsv(tmp_path, [GOOD_ROW])
    )
    try:
        first = case_field.default_government()
        assert set(first) == {"g1"}
        assert case_field.default_government() is first
    finally:
        case_field.default_government.cache_clear()


def test_row_fields_case_value_comes_from_the_government_not_the_section(tmp_path):
    preposition = WordRow(pos="Prepositions", rank=1, russian="в", english="in")
    particle = WordRow(pos="Particles", rank=1, russian="не", english="not")
    unlisted = WordRow(pos="Prepositions", rank=2, russian="над", english="above")
    path = write_tsv(
        tmp_path,
        [
            f"{preposition.guid}\tAccusative, Prepositional\t\tx\tв",
            f"{particle.guid}\tGenitive\t\tx\tне",
        ],
    )
    government = case_field.load_case_government(path)
    index = FIELD_NAMES.index(case_field.CASE_FIELD)
    assert preposition.fields(government)[index] == "Accusative, Prepositional"
    assert particle.fields(government)[index] == "Genitive"
    assert unlisted.fields(government)[index] == ""


@pytest.mark.parametrize(
    "info,expected",
    [
        ("Prepositional", ""),
        ("Genitive", ""),
        ("Dative", ""),
        ("Genitive — always", "always"),
        ("Dative — always", "always"),
        ("Accusative for motion in; Prepositional for location", ""),
        ('Instrumental for "with"; Genitive for "from / since"', ""),
        ("", ""),
    ],
)
def test_residual_info(info, expected):
    assert case_field.residual_info_for_row("Prepositions", info) == expected


def test_residual_info_only_applies_to_prepositions():
    assert case_field.residual_info_for_row("Prepositions", "Genitive") == ""
    for pos in ("Particles", "Base Adverbs", "Conjunctions", "Indeclinable Nouns"):
        assert case_field.residual_info_for_row(pos, "Genitive") == "Genitive"


def test_no_preposition_states_its_case_twice(real_rows):
    """The whole point: the pill renders the case, so the prose must not."""
    for row in (r for r in real_rows if r.pos == "Prepositions"):
        residual = case_field.residual_info_for_row(row.pos, row.info)
        assert case_field.case_name(row.info), row.russian
        assert not case_field.case_name(residual), (row.russian, residual)


def test_bare_case_cells_collapse_and_commentary_survives(real_rows):
    preps = [r for r in real_rows if r.pos == "Prepositions"]
    residual = {
        r.russian: case_field.residual_info_for_row(r.pos, r.info) for r in preps
    }
    assert residual["о / об"] == ""
    assert residual["из"] == ""
    assert residual["для"] == "always"
    assert residual["в / во"] == ""
    assert sum(1 for v in residual.values() if v) == 2


def test_additional_info_field_carries_the_residual(real_rows):
    index = FIELD_NAMES.index("Additional Info")
    for row in real_rows:
        expected = case_field.residual_info_for_row(row.pos, row.info)
        assert row.fields()[index] == expected


def test_no_two_rows_share_an_identical_english_gloss_and_cue(real_rows):
    """An English prompt must name exactly one Russian word.

    Two rows may share a gloss only when their English Distinction cues differ
    (`because` is `потому что` / `оттого что (less common)`).
    """
    seen: dict[tuple[str, str], str] = {}
    clashes = []
    for row in real_rows:
        gloss = re.sub(r"\s+", " ", row.english.strip().lower())
        key = (gloss, distinction.english_distinction(row.russian))
        if key in seen:
            clashes.append((key, seen[key], row.russian))
        seen[key] = row.russian
    assert clashes == []


def test_the_about_pair_is_told_apart_by_its_english_not_by_its_case(real_rows):
    """Both say "about" and each governs a different case, but the English
    columns already differ -- so the prompt is answerable on its own and the
    `Case` row never has to carry that weight."""
    by_word = {r.russian: r for r in real_rows if r.pos == "Prepositions"}
    o, naschet = by_word["о / об"], by_word["насчёт"]
    assert "about" in o.english and "about" in naschet.english
    assert o.english != naschet.english
    assert case_field.case_name(o.info) == "Prepositional"
    assert case_field.case_name(naschet.info) == "Genitive"


def test_case_is_spelled_out_never_abbreviated(real_rows):
    """`prep.` reads as "preposition", the one thing it does not mean."""
    for row in (r for r in real_rows if r.pos == "Prepositions"):
        name = case_field.case_name(row.info)
        assert name, row.russian
        assert "." not in name, (row.russian, name)
        for word in name.split(" or "):
            assert word in [full for full, _ in case_field.CASE_NAMES], (
                row.russian,
                word,
            )
