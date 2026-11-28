from pathlib import Path

import pytest

from anki_tools import noun_intake as ni
from anki_tools.anki_identity import guid_for_row
from anki_tools.mutable_words_plan import parse_nouns

ACUTE = "́"
DATA = Path(ni.DATA_DIR)
NOUN_HEADER = (
    "#\tRussian\tEnglish\tStress\tGender\tPlural\tGenitive Sg\tGenitive Pl\t"
    "Animate\tCategory\tAdditional Info\tExamples\tStatus"
)


def write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def live_header(name):
    with open(DATA / name, encoding="utf-8") as handle:
        return handle.readline().rstrip("\n")


def noun_line(rank, russian, english="thing", status="Done", category="Time"):
    cells = [
        str(rank),
        russian,
        english,
        russian,
        "m",
        "p",
        "g",
        "gp",
        "No",
        category,
        "",
        "ex",
        status,
    ]
    return "\t".join(cells)


def make_nouns(tmp_path, russians=("год", "время")):
    lines = [NOUN_HEADER]
    lines += [noun_line(i, r) for i, r in enumerate(russians, 1)]
    return write(tmp_path / "nouns.tsv", "\n".join(lines) + "\n")


def fragment_line(russian, ipm="10.0", **overrides):
    cells = {
        "#": "",
        "Russian": russian,
        "English": "thing",
        "Stress": russian,
        "Gender": "m",
        "Plural": "p",
        "Genitive Sg": "g",
        "Genitive Pl": "gp",
        "Animate": "No",
        "Category": "Time",
        "Additional Info": "",
        "Examples": "",
        "Status": "New",
        "Degrees": "1",
        "ipm": ipm,
        "flags": "",
    }
    cells.update(overrides)
    return "\t".join(cells[column] for column in ni.FRAGMENT_COLUMNS)


def make_fragment(tmp_path, name, *lines):
    header = "\t".join(ni.FRAGMENT_COLUMNS)
    return write(tmp_path / name, "\n".join([header, *lines]) + "\n")


def make_degrees(tmp_path, name, pairs):
    lines = ["#\tRussian\tDegrees"] + [f"{r}\t{w}\t{d}" for r, w, d in pairs]
    return write(tmp_path / name, "\n".join(lines) + "\n")


@pytest.fixture
def data_dir(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    make_nouns(root, ("год", "время"))
    for name in ("adjectives.tsv", "adverbs.tsv"):
        write(root / name, live_header(name) + "\n")
    return root


def test_constants():
    assert len(ni.NOUN_COLUMNS) == 13
    assert ni.FRAGMENT_COLUMNS == ni.NOUN_COLUMNS + ("Degrees", "ipm", "flags")
    assert ni.NOUN_COLUMNS[0] == "#"
    assert ni.NOUN_COLUMNS[-1] == "Status"


def write_freq(tmp_path, rows):
    lines = ["Lemma\tPoS\tFreq(ipm)\tR\tD\tDoc"]
    lines += [f"{lemma}\t{pos}\t{ipm}\t1\t1\t1" for lemma, pos, ipm in rows]
    return write(tmp_path / "freq.csv", "\n".join(lines) + "\n")


def test_load_frequency_filters_and_sorts(tmp_path):
    path = write_freq(
        tmp_path,
        [
            ("бежать", "v", "900.0"),
            ("год", "s", "100.5"),
            ("москва", "s.PROP", "500.0"),
            ("время", "s", "300.25"),
            ("дом", "s", "100.5"),
        ],
    )
    rows = ni.load_frequency(path)
    assert [r.lemma for r in rows] == ["время", "год", "дом"]
    assert rows[0].ipm == 300.25
    assert isinstance(rows[0], ni.FreqRow)


def test_freqrow_is_frozen():
    row = ni.FreqRow("год", 1.0)
    with pytest.raises(Exception):
        row.lemma = "x"


def test_top_nouns():
    rows = [ni.FreqRow(str(i), float(10 - i)) for i in range(5)]
    assert ni.top_nouns(rows, 3) == rows[:3]
    assert ni.top_nouns(rows, 0) == []


@pytest.mark.parametrize(
    "text,expected",
    [
        ("правда (noun)", "правда"),
        ("ПРАВДА", "правда"),
        ("вода" + ACUTE, "вода"),
        ("ёлка", "елка"),
        ("Ёлка", "елка"),
        ("  дом  ", "дом"),
        ("сло" + ACUTE + "во (x)", "слово"),
    ],
)
def test_match_key(text, expected):
    assert ni.match_key(text) == expected


def test_missing_positive_control_and_order(tmp_path):
    nouns = make_nouns(tmp_path, ("правда (noun)", "год", "елка"))
    rows = parse_nouns(str(nouns))
    top = [
        ni.FreqRow("время", 5.0),
        ni.FreqRow("правда", 4.0),
        ni.FreqRow("ёлка", 3.0),
        ni.FreqRow("дом", 2.0),
        ni.FreqRow("год", 1.0),
    ]
    assert [r.lemma for r in ni.missing(top, rows)] == ["время", "дом"]


def entry(forms, pos="noun"):
    return [{"pos": pos, "forms": forms}]


def classify(candidate, entries=None, other=None, immutable=()):
    return ni.classify(candidate, other or {}, entries or {}, set(immutable))


def test_classify_clean_noun():
    entries = {
        "стол": entry(
            [["столы", ["nominative", "plural"]], ["стол", ["nominative", "singular"]]]
        )
    }
    assert classify("стол", entries) == ()


def test_classify_immutable_present():
    entries = {"стол": entry([["стол", ["singular"]]])}
    result = classify("стол", entries, immutable={"стол"})
    assert result == (ni.FLAG_IMMUTABLE_PRESENT,)


def test_classify_other_sheet_homonym():
    entries = {"стол": entry([["стол", ["singular"]]])}
    other = {"Verbs": set(), "Adjectives": {"стол"}}
    assert classify("стол", entries, other) == (ni.FLAG_OTHER_SHEET,)


def test_classify_adjectival_by_ending():
    for lemma in ("новый", "синий", "большой", "будущая", "ое"):
        entries = {lemma: entry([[lemma, ["singular"]], [lemma + "х", ["plural"]]])}
        assert ni.FLAG_ADJECTIVAL in classify(lemma, entries), lemma


def test_classify_adjectival_by_tag():
    entries = {"учёный": entry([["учёный", ["adjectival", "singular"]]])}
    assert ni.FLAG_ADJECTIVAL in classify("учёный", entries)


def test_classify_plural_only_by_tag():
    entries = {"часы": entry([["часы", ["plural-only"]]])}
    assert classify("часы", entries) == (ni.FLAG_PLURAL_ONLY,)


def test_classify_plural_only_without_singular():
    entries = {"ножницы": entry([["ножницы", ["nominative", "plural"]]])}
    assert classify("ножницы", entries) == (ni.FLAG_PLURAL_ONLY,)


def test_classify_indeclinable():
    entries = {"метро": entry([["метро", ["indeclinable"]]])}
    assert ni.FLAG_INDECLINABLE in classify("метро", entries)


def test_classify_no_wiktionary_noun():
    assert classify("стол", {}) == (ni.FLAG_NO_WIKT_NOUN,)
    verb_only = {"стол": entry([["стол", ["singular"]]], pos="verb")}
    assert classify("стол", verb_only) == (ni.FLAG_NO_WIKT_NOUN,)


def test_classify_flag_order():
    flags = [
        ni.FLAG_IMMUTABLE_PRESENT,
        ni.FLAG_OTHER_SHEET,
        ni.FLAG_ADJECTIVAL,
        ni.FLAG_PLURAL_ONLY,
        ni.FLAG_INDECLINABLE,
        ni.FLAG_NO_WIKT_NOUN,
    ]
    entries = {
        "новое": entry(
            [["новое", ["indeclinable", "plural-only", "adjectival"]]],
        )
    }
    other = {"Adverbs": {"новое"}}
    result = classify("новое", entries, other, {"новое"})
    assert list(result) == flags[:5]
    assert list(classify("новое", {}, other, {"новое"})) == [
        ni.FLAG_IMMUTABLE_PRESENT,
        ni.FLAG_OTHER_SHEET,
        ni.FLAG_ADJECTIVAL,
        ni.FLAG_NO_WIKT_NOUN,
    ]


OR_HEADER = "bare\taccented\tgender\tanimate\tpl_nom\tsg_gen\tpl_gen"


def make_or_index(tmp_path, noun_rows):
    from anki_tools import form_fill as ff

    directory = tmp_path / "or"
    directory.mkdir()
    write(directory / "nouns.csv", "\n".join([OR_HEADER, *noun_rows]) + "\n")
    write(directory / "verbs.csv", "bare\taccented\n")
    write(directory / "adjectives.csv", "bare\taccented\n")
    return ff.load_openrussian(directory)


STOL_FORMS = [
    ["столы", ["nominative", "plural"]],
    ["стола", ["genitive", "singular"]],
    ["столов", ["genitive", "plural"]],
]


def test_skeleton_row_keys_and_fixed_cells(tmp_path):
    index = make_or_index(tmp_path, ["стол\tстол\tm\tinan\tстолы\tстола\tстолов"])
    row = ni.skeleton_row(
        ni.FreqRow("стол", 123.456), {"стол": entry(STOL_FORMS)}, index
    )
    assert set(row) == set(ni.FRAGMENT_COLUMNS)
    assert row["Russian"] == "стол"
    assert row["Status"] == "New"
    assert row["#"] == ""
    assert row["Degrees"] == ""
    assert row["Examples"] == ""
    assert row["English"] == ""
    assert row["Category"] == ""
    assert row["Additional Info"] == ""
    assert "123" in row["ipm"]


def test_skeleton_row_agreeing_forms_kept(tmp_path):
    index = make_or_index(tmp_path, ["стол\tстол\tm\tinan\tстолы\tстола\tстолов"])
    row = ni.skeleton_row(ni.FreqRow("стол", 5.0), {"стол": entry(STOL_FORMS)}, index)
    assert row["Plural"] == "столы"
    assert row["Genitive Sg"] == "стола"
    assert row["Genitive Pl"] == "столов"
    assert "Plural" not in row["flags"]


def test_skeleton_row_differs_left_empty_and_flagged(tmp_path):
    index = make_or_index(tmp_path, ["стол\tстол\tm\tinan\tстола\tстола\tстолов"])
    row = ni.skeleton_row(ni.FreqRow("стол", 5.0), {"стол": entry(STOL_FORMS)}, index)
    assert row["Plural"] == ""
    assert "Plural:differs" in row["flags"].split(";")
    assert row["Genitive Sg"] == "стола"


def test_skeleton_row_no_entry_left_empty_and_flagged(tmp_path):
    index = make_or_index(tmp_path, [])
    row = ni.skeleton_row(ni.FreqRow("стол", 5.0), {"стол": entry(STOL_FORMS)}, index)
    assert row["Plural"] == ""
    assert "Plural:no-entry" in row["flags"].split(";")


def test_skeleton_row_missing_generated_flagged(tmp_path):
    index = make_or_index(tmp_path, ["стол\tстол\tm\tinan\tстолы\tстола\tстолов"])
    row = ni.skeleton_row(ni.FreqRow("стол", 5.0), {}, index)
    assert row["Plural"] == ""
    assert "Plural:missing" in row["flags"].split(";")


def test_skeleton_row_never_invents(tmp_path):
    index = make_or_index(tmp_path, [])
    row = ni.skeleton_row(ni.FreqRow("стол", 5.0), {}, index)
    for column in ("Plural", "Genitive Sg", "Genitive Pl"):
        assert row[column] == ""


def validate(path, sheet, data_dir):
    return ni.validate_fragment(path, sheet, data_dir=data_dir)


def test_validate_clean_noun_fragment(tmp_path, data_dir):
    path = make_fragment(tmp_path, "f.tsv", fragment_line("год"))
    assert validate(path, "Nouns", data_dir) == []


def test_validate_bad_sheet(tmp_path, data_dir):
    path = make_fragment(tmp_path, "f.tsv", fragment_line("год"))
    with pytest.raises(ValueError):
        validate(path, "Verbs", data_dir)


def test_validate_bad_header(tmp_path, data_dir):
    path = write(tmp_path / "f.tsv", NOUN_HEADER + "\n" + fragment_line("год") + "\n")
    violations = validate(path, "Nouns", data_dir)
    assert violations
    assert violations[0].startswith("header:")


@pytest.mark.parametrize(
    "overrides",
    [
        {"Status": "Done"},
        {"Examples": "что-то"},
        {"Category": "Nonexistent"},
        {"Gender": "x"},
        {"Animate": "Maybe"},
        {"Degrees": "4"},
        {"Degrees": ""},
        {"English": ""},
        {"English": "тест"},
        {"English": "a; b"},
        {"English": "a, b"},
        {"Stress": "вода"},
        {"Stress": "нет"},
        {"Plural": ""},
        {"Genitive Sg": ""},
        {"Genitive Pl": ""},
        {"Genitive Pl": "—"},
        {"Genitive Sg": "—", "Gender": "pl-only"},
        {"Plural": "", "Genitive Pl": ""},
        {"flags": "Plural:differs"},
    ],
)
def test_validate_noun_violations(tmp_path, data_dir, overrides):
    path = make_fragment(tmp_path, "f.tsv", fragment_line("год", **overrides))
    violations = validate(path, "Nouns", data_dir)
    assert violations
    assert all(v.startswith("row 1:") for v in violations)


@pytest.mark.parametrize(
    "overrides",
    [
        {"Gender": "n"},
        {"Animate": "Yes"},
        {"Degrees": "0"},
        {"Degrees": "3"},
        {"English": "a / b"},
        {"Plural": "—"},
        {"Plural": "—", "Genitive Pl": ""},
        {"Gender": "pl-only", "Plural": "—", "Genitive Sg": ""},
        {"#": "999"},
    ],
)
def test_validate_noun_accepted(tmp_path, data_dir, overrides):
    path = make_fragment(tmp_path, "f.tsv", fragment_line("год", **overrides))
    assert validate(path, "Nouns", data_dir) == []


def test_validate_noun_stress_marked_and_qualifier(tmp_path, data_dir):
    line = fragment_line("вода", Stress="вода" + ACUTE)
    qualified = fragment_line("правда (noun)", Stress="пра" + ACUTE + "вда")
    path = make_fragment(tmp_path, "f.tsv", line, qualified)
    assert validate(path, "Nouns", data_dir) == []


def test_validate_reports_row_number(tmp_path, data_dir):
    path = make_fragment(
        tmp_path,
        "f.tsv",
        fragment_line("год"),
        fragment_line("дом"),
        fragment_line("лес", Status="Done"),
    )
    violations = validate(path, "Nouns", data_dir)
    assert violations
    assert all(v.startswith("row 3:") for v in violations)


def adj_fragment(tmp_path, name, header_name, **overrides):
    header = live_header(header_name)
    columns = header.split("\t")
    cells = {column: "" for column in columns}
    cells.update({columns[1]: "новый", "English": "new", "Stress": "новый"})
    cells["Status"] = "New"
    cells.update(overrides)
    line = "\t".join(cells[column] for column in columns)
    return write(tmp_path / name, header + "\n" + line + "\n")


@pytest.mark.parametrize(
    "sheet,header_name", [("Adjectives", "adjectives.tsv"), ("Adverbs", "adverbs.tsv")]
)
def test_validate_adj_adverb_clean_and_bad(tmp_path, data_dir, sheet, header_name):
    clean = adj_fragment(tmp_path, "ok.tsv", header_name)
    assert validate(clean, sheet, data_dir) == []
    for overrides in (
        {"Status": "Done"},
        {"Examples": "x"},
        {"English": ""},
        {"English": "тест"},
        {"English": "a; b"},
        {"Stress": "вода"},
    ):
        bad = adj_fragment(tmp_path, "bad.tsv", header_name, **overrides)
        violations = validate(bad, sheet, data_dir)
        assert violations, overrides
        assert all(v.startswith("row 1:") for v in violations)


def test_validate_adj_header_must_match_live(tmp_path, data_dir):
    path = write(tmp_path / "f.tsv", "\t".join(ni.FRAGMENT_COLUMNS) + "\n")
    violations = validate(path, "Adjectives", data_dir)
    assert violations[0].startswith("header:")


def list_tsv(name, rows):
    header = live_header(name).split("\t")
    lines = [live_header(name)]
    for rank, russian in rows:
        cells = [""] * len(header)
        cells[0] = str(rank)
        cells[1] = russian
        cells[2] = "x"
        lines.append("\t".join(cells))
    return "\n".join(lines) + "\n"


def frag_rows(name, russians):
    header = live_header(name).split("\t")
    lines = [live_header(name)]
    for russian in russians:
        cells = [""] * len(header)
        cells[0] = "77"
        cells[1] = russian
        cells[2] = "y"
        lines.append("\t".join(cells))
    return "\n".join(lines) + "\n"


def test_merge_rows_appends_and_continues_rank(tmp_path):
    existing = list_tsv("adjectives.tsv", [(1, "новый"), (2, "старый")])
    tsv = write(tmp_path / "adjectives.tsv", existing)
    f1 = write(tmp_path / "a.tsv", frag_rows("adjectives.tsv", ["добрый"]))
    f2 = write(tmp_path / "b.tsv", frag_rows("adjectives.tsv", ["злой", "умный"]))
    result = ni.merge_rows(tsv, [f1, f2])
    assert result.startswith(existing)
    new_lines = result[len(existing) :].splitlines()
    cells = [line.split("\t") for line in new_lines]
    assert [c[0] for c in cells] == ["3", "4", "5"]
    assert [c[1] for c in cells] == ["добрый", "злой", "умный"]


def test_merge_rows_adverbs(tmp_path):
    existing = list_tsv("adverbs.tsv", [(1, "по-новому")])
    tsv = write(tmp_path / "adverbs.tsv", existing)
    frag = write(tmp_path / "a.tsv", frag_rows("adverbs.tsv", ["быстро"]))
    result = ni.merge_rows(tsv, [frag])
    assert result.startswith(existing)
    assert result.splitlines()[-1].split("\t")[:2] == ["2", "быстро"]


def test_merge_rows_duplicate_against_existing(tmp_path):
    tsv = write(tmp_path / "adjectives.tsv", list_tsv("adjectives.tsv", [(1, "новый")]))
    frag = write(tmp_path / "a.tsv", frag_rows("adjectives.tsv", ["новый"]))
    with pytest.raises(ValueError):
        ni.merge_rows(tsv, [frag])


def test_merge_rows_duplicate_across_fragments(tmp_path):
    tsv = write(tmp_path / "adjectives.tsv", list_tsv("adjectives.tsv", [(1, "новый")]))
    f1 = write(tmp_path / "a.tsv", frag_rows("adjectives.tsv", ["добрый"]))
    f2 = write(tmp_path / "b.tsv", frag_rows("adjectives.tsv", ["добрый"]))
    with pytest.raises(ValueError):
        ni.merge_rows(tsv, [f1, f2])


def test_merge_rows_unknown_file_name(tmp_path):
    tsv = write(tmp_path / "other.tsv", list_tsv("adjectives.tsv", [(1, "новый")]))
    frag = write(tmp_path / "a.tsv", frag_rows("adjectives.tsv", ["добрый"]))
    with pytest.raises(ValueError):
        ni.merge_rows(tsv, [frag])


def test_merge_rows_header_mismatch(tmp_path):
    tsv = write(tmp_path / "adjectives.tsv", list_tsv("adjectives.tsv", [(1, "новый")]))
    frag = write(tmp_path / "a.tsv", frag_rows("adverbs.tsv", ["быстро"]))
    with pytest.raises(ValueError):
        ni.merge_rows(tsv, [frag])


def merge_setup(tmp_path):
    nouns = make_nouns(tmp_path, ("год", "время"))
    degrees = make_degrees(tmp_path, "deg.tsv", [(1, "год", "1"), (2, "время", "2")])
    return nouns, degrees


def test_merge_header_and_existing_rows_bytes(tmp_path):
    nouns, degrees = merge_setup(tmp_path)
    original = nouns.read_text(encoding="utf-8").splitlines()
    batch = make_fragment(tmp_path, "b.tsv", fragment_line("дом", "5.0", Degrees="3"))
    out = ni.merge(nouns, [batch], [degrees]).splitlines()
    assert out[0] == NOUN_HEADER + "\tDegrees"
    assert out[1] == original[1] + "\t1"
    assert out[2] == original[2] + "\t2"


def test_merge_new_rows_sorted_ranked_trimmed(tmp_path):
    nouns, degrees = merge_setup(tmp_path)
    b1 = make_fragment(
        tmp_path,
        "b1.tsv",
        fragment_line("дом", "5.0", Degrees="3"),
        fragment_line("лес", "9.0", Degrees="2"),
    )
    b2 = make_fragment(
        tmp_path,
        "b2.tsv",
        fragment_line("мир", "9.0", Degrees="0"),
        fragment_line("сад", "7.5", Degrees="1"),
    )
    out = ni.merge(nouns, [b1, b2], [degrees]).splitlines()
    new = [line.split("\t") for line in out[3:]]
    assert [c[1] for c in new] == ["лес", "мир", "сад", "дом"]
    assert [c[0] for c in new] == ["3", "4", "5", "6"]
    assert all(len(c) == 14 for c in new)
    assert [c[13] for c in new] == ["2", "0", "1", "3"]
    assert all(c[12] == "New" for c in new)
    assert "9.0" not in "".join(out[3:])


def test_merge_duplicate_guid_rejected(tmp_path):
    nouns, degrees = merge_setup(tmp_path)
    batch = make_fragment(tmp_path, "b.tsv", fragment_line("год", "5.0"))
    with pytest.raises(ValueError):
        ni.merge(nouns, [batch], [degrees])
    assert guid_for_row("год", "Nouns")


def test_merge_row_in_two_batches_rejected(tmp_path):
    nouns, degrees = merge_setup(tmp_path)
    b1 = make_fragment(tmp_path, "b1.tsv", fragment_line("дом", "5.0"))
    b2 = make_fragment(tmp_path, "b2.tsv", fragment_line("дом", "6.0"))
    with pytest.raises(ValueError):
        ni.merge(nouns, [b1, b2], [degrees])


def test_merge_missing_degree_rejected(tmp_path):
    nouns = make_nouns(tmp_path, ("год", "время"))
    degrees = make_degrees(tmp_path, "deg.tsv", [(1, "год", "1")])
    with pytest.raises(ValueError):
        ni.merge(nouns, [], [degrees])


def test_merge_degree_out_of_range_rejected(tmp_path):
    nouns = make_nouns(tmp_path, ("год", "время"))
    degrees = make_degrees(tmp_path, "deg.tsv", [(1, "год", "1"), (2, "время", "7")])
    with pytest.raises(ValueError):
        ni.merge(nouns, [], [degrees])


def test_merge_unknown_rank_rejected(tmp_path):
    nouns, _ = merge_setup(tmp_path)
    degrees = make_degrees(
        tmp_path, "deg.tsv", [(1, "год", "1"), (2, "время", "2"), (9, "дом", "1")]
    )
    with pytest.raises(ValueError):
        ni.merge(nouns, [], [degrees])


def test_merge_russian_mismatch_rejected(tmp_path):
    nouns = make_nouns(tmp_path, ("год", "время"))
    degrees = make_degrees(tmp_path, "deg.tsv", [(1, "год", "1"), (2, "дом", "2")])
    with pytest.raises(ValueError):
        ni.merge(nouns, [], [degrees])


def test_merge_degrees_from_multiple_files(tmp_path):
    nouns = make_nouns(tmp_path, ("год", "время"))
    d1 = make_degrees(tmp_path, "d1.tsv", [(1, "год", "0")])
    d2 = make_degrees(tmp_path, "d2.tsv", [(2, "время", "3")])
    out = ni.merge(nouns, [], [d1, d2]).splitlines()
    assert out[1].endswith("\t0")
    assert out[2].endswith("\t3")


def test_load_immutable_headwords_returns_set(tmp_path):
    source = Path(__file__).parent / "data" / "source-word-list.md"
    if not source.exists():
        pytest.skip("source list absent")
    words = ni.load_immutable_headwords(source)
    assert isinstance(words, set)
    assert words


def sing_entry(lemma, genitive=None):
    forms = [[lemma, ["nominative", "singular"]]]
    if genitive:
        forms.append([genitive, ["genitive", "singular"]])
    return {lemma: entry(forms)}


@pytest.mark.parametrize("lemma", ["развитие", "здание", "новые"])
def test_classify_ie_ye_with_singular_not_adjectival(lemma):
    entries = sing_entry(lemma, lemma + "х")
    assert ni.FLAG_ADJECTIVAL not in classify(lemma, entries)


@pytest.mark.parametrize("lemma", ["близкие", "новые"])
def test_classify_ie_ye_plural_only_is_adjectival(lemma):
    entries = {lemma: entry([[lemma, ["nominative", "plural"]]])}
    result = classify(lemma, entries)
    assert ni.FLAG_ADJECTIVAL in result
    assert ni.FLAG_PLURAL_ONLY in result


def test_classify_ie_with_plural_only_tag_is_adjectival():
    entries = {"близкие": entry([["близкие", ["plural-only"]]])}
    assert ni.FLAG_ADJECTIVAL in classify("близкие", entries)


@pytest.mark.parametrize("lemma", ["будущее", "синяя", "новое", "новая", "синий"])
def test_classify_other_endings_adjectival_with_singular(lemma):
    assert ni.FLAG_ADJECTIVAL in classify(lemma, sing_entry(lemma))


def test_excluded_already_present_content():
    assert isinstance(ni.EXCLUDED_ALREADY_PRESENT, frozenset)
    assert ni.EXCLUDED_ALREADY_PRESENT == frozenset(
        "кино кофе радио метро пальто интервью кафе шоссе такси бюро привет".split()
    )


@pytest.mark.parametrize(
    "noun,adjectives,expected",
    [
        ("новая", {"новый"}, "новый"),
        ("большая", {"большой"}, "большой"),
        ("новое", {"новый"}, "новый"),
        ("синяя", {"синий"}, "синий"),
        ("будущее", {"будущий"}, "будущий"),
        ("новые", {"новый"}, "новый"),
        ("близкие", {"близкий"}, "близкий"),
        ("новая", {"новый", "новой"}, "новый"),
        ("новый", set(), "новый"),
        ("синий", set(), "синий"),
        ("большой", set(), "большой"),
        ("новая", set(), None),
        ("новая", {"синий"}, None),
        ("стол", {"стол", "новый"}, None),
        ("чёрная", {"черный"}, "чёрный"),
    ],
)
def test_adjective_lemma(noun, adjectives, expected):
    assert ni.adjective_lemma(noun, adjectives) == expected


def sheet_tsv(root, name, headwords, perfective=()):
    header = live_header(name)
    width = len(header.split("\t"))
    lines = [header]
    for rank, word in enumerate(headwords, 1):
        cells = [""] * width
        cells[0] = str(rank)
        cells[1] = word
        if perfective:
            cells[2] = perfective[rank - 1]
        lines.append("\t".join(cells))
    return write(root / name, "\n".join(lines) + "\n")


def make_data_dir(tmp_path, **sheets):
    root = tmp_path / "dd"
    root.mkdir()
    for name in (
        "nouns",
        "verbs",
        "adjectives",
        "adverbs",
        "pronouns",
        "numerals",
    ):
        sheet_tsv(root, f"{name}.tsv", sheets.get(name, ()))
    return root


def test_same_spelling_pairs_groups_and_sorts(tmp_path):
    root = make_data_dir(
        tmp_path,
        nouns=["ёлка", "дом", "дом", "лук"],
        pronouns=["елка"],
        adverbs=["выпить", "—"],
        numerals=["один"],
    )
    sheet_tsv(root, "verbs.tsv", ["пить", "один2"], perfective=["выпить", "—"])
    pairs = ni.same_spelling_pairs(root, frozenset({"лук"}))
    assert pairs == [
        ("выпить", ("Adverbs", "Verbs")),
        ("елка", ("Nouns", "Pronouns")),
        ("лук", ("Immutable", "Nouns")),
    ]


def test_same_spelling_pairs_same_sheet_only_is_empty(tmp_path):
    root = make_data_dir(tmp_path, nouns=["дом", "дом"])
    sheet_tsv(root, "verbs.tsv", ["пить"], perfective=["пить"])
    assert ni.same_spelling_pairs(root) == []


def test_same_spelling_pairs_skips_dash_and_empty(tmp_path):
    root = make_data_dir(tmp_path, adverbs=["—"], numerals=["—"])
    sheet_tsv(root, "verbs.tsv", ["пить"], perfective=["—"])
    assert ni.same_spelling_pairs(root) == []


OR_FULL_HEADER = (
    "bare\taccented\ttranslations_en\ttranslations_de\tgender\tpartner\tanimate\t"
    "indeclinable\tsg_only\tpl_only\tsg_nom\tsg_gen\tsg_dat\tsg_acc\tsg_inst\t"
    "sg_prep\tpl_nom\tpl_gen\tpl_dat\tpl_acc\tpl_inst\tpl_prep"
)


def or_noun(bare, accented, gender, sg_gen, pl_nom, pl_gen, animate="0"):
    cells = {
        "bare": bare,
        "accented": accented,
        "gender": gender,
        "animate": animate,
        "sg_nom": bare,
        "sg_gen": sg_gen,
        "pl_nom": pl_nom,
        "pl_gen": pl_gen,
    }
    return "\t".join(cells.get(c, "") for c in OR_FULL_HEADER.split("\t"))


def make_or_dir(tmp_path, noun_rows):
    root = tmp_path / "orx"
    root.mkdir()
    write(root / "nouns.csv", "\n".join([OR_FULL_HEADER, *noun_rows]) + "\n")
    write(root / "verbs.csv", OR_FULL_HEADER + "\n")
    write(root / "adjectives.csv", OR_FULL_HEADER + "\n")
    return root


def kaikki_line(word, forms, extra_tags=()):
    import json

    return json.dumps(
        {
            "word": word,
            "pos": "noun",
            "tags": list(extra_tags),
            "forms": [{"form": f, "tags": t} for f, t in forms],
        },
        ensure_ascii=False,
    )


def noun_forms(sg, gen, pl, gen_pl):
    return [
        (sg, ["nominative", "singular"]),
        (gen, ["genitive", "singular"]),
        (pl, ["nominative", "plural"]),
        (gen_pl, ["genitive", "plural"]),
    ]


IMMUTABLE_MD = """# Words

| Rank | Russian | English | Info | Examples |
|---|---|---|---|---|
| 1 | итого | total | adverb | — |
"""


@pytest.fixture
def skeleton_inputs(tmp_path):
    write_freq(
        tmp_path,
        [
            ("кино", "s", "90.0"),
            ("расчет", "s", "80.0"),
            ("москва", "s.PROP", "75.0"),
            ("добро", "s", "70.0"),
            ("итого", "s", "60.0"),
            ("год", "s", "50.0"),
            ("стол", "s", "40.0"),
            ("бежать", "v", "30.0"),
        ],
    )
    nouns = make_nouns(tmp_path, ("год",))
    kaikki = write(
        tmp_path / "kaikki.jsonl",
        "\n".join(
            [
                kaikki_line(
                    "расчёт",
                    noun_forms("расчёт", "расчёта", "расчёты", "расчётов"),
                ),
                kaikki_line("добро", noun_forms("добро", "добра", "добра", "добр")),
                kaikki_line("итого", noun_forms("итого", "итога", "итоги", "итогов")),
                kaikki_line("стол", noun_forms("стол", "стола", "столы", "столов")),
            ]
        )
        + "\n",
    )
    orx = make_or_dir(
        tmp_path,
        [
            or_noun("расчёт", "расчёт", "m", "расчёта", "расчёты", "расчётов"),
            or_noun("добро", "добро", "n", "добра", "добра", "добр"),
            or_noun("итого", "итого", "n", "итога", "итоги", "итогов"),
            or_noun("стол", "стол", "m", "стола", "столы", "столов"),
        ],
    )
    md = write(tmp_path / "imm.md", IMMUTABLE_MD)
    root = make_data_dir(tmp_path, adverbs=["добро"], nouns=["год"])
    return {
        "freq_path": tmp_path / "freq.csv",
        "nouns_path": nouns,
        "kaikki_jsonl": kaikki,
        "openrussian_dir": orx,
        "immutable_md": md,
        "data_dir": root,
    }


def test_load_immutable_headwords_fixture(tmp_path):
    md = write(tmp_path / "imm.md", IMMUTABLE_MD)
    assert "итого" in ni.load_immutable_headwords(md)


def test_build_skeleton_end_to_end(skeleton_inputs):
    result = ni.build_skeleton(**skeleton_inputs)
    by_russian = {row["Russian"]: row for row in result.rows}
    assert "расчёт" in by_russian
    assert "расчет" not in by_russian
    assert "добро (noun)" in by_russian
    assert "итого (noun)" in by_russian
    assert "стол" in by_russian
    assert len(result.rows) == 4
    assert [r["Russian"] for r in result.rows] == [
        "расчёт",
        "добро (noun)",
        "итого (noun)",
        "стол",
    ]
    assert result.excluded == ["кино"]
    assert all(r["Status"] == "New" for r in result.rows)


def test_build_skeleton_yo_restored_and_resolved(skeleton_inputs):
    result = ni.build_skeleton(**skeleton_inputs)
    row = next(r for r in result.rows if r["Russian"] == "расчёт")
    flags = row["flags"].split(";")
    assert ni.FLAG_NO_WIKT_NOUN not in flags
    assert row["Plural"] == "расчёты"
    assert row["Genitive Sg"] == "расчёта"


def test_build_skeleton_qualified_keeps_stress_unqualified(skeleton_inputs):
    result = ni.build_skeleton(**skeleton_inputs)
    for russian in ("добро (noun)", "итого (noun)"):
        row = next(r for r in result.rows if r["Russian"] == russian)
        assert "(" not in row["Stress"]
        assert row["Stress"].replace(ACUTE, "") == russian.split(" ")[0]
    plain = next(r for r in result.rows if r["Russian"] == "стол")
    assert "(" not in plain["Russian"]


def test_build_skeleton_flags_for_homonyms(skeleton_inputs):
    result = ni.build_skeleton(**skeleton_inputs)
    row = {r["Russian"]: r for r in result.rows}
    assert ni.FLAG_OTHER_SHEET in row["добро (noun)"]["flags"].split(";")
    assert ni.FLAG_IMMUTABLE_PRESENT in row["итого (noun)"]["flags"].split(";")
    classify_flags = {
        ni.FLAG_IMMUTABLE_PRESENT,
        ni.FLAG_OTHER_SHEET,
        ni.FLAG_ADJECTIVAL,
        ni.FLAG_PLURAL_ONLY,
        ni.FLAG_INDECLINABLE,
        ni.FLAG_NO_WIKT_NOUN,
    }
    assert not classify_flags & set(row["стол"]["flags"].split(";"))


def test_build_skeleton_excludes_and_drops_existing(skeleton_inputs):
    result = ni.build_skeleton(**skeleton_inputs)
    lemmas = [r["Russian"] for r in result.rows]
    assert "кино" not in lemmas
    assert "год" not in lemmas
    assert "москва" not in lemmas
    assert "бежать" not in lemmas


def test_build_skeleton_excluded_param_overrides(skeleton_inputs):
    result = ni.build_skeleton(**skeleton_inputs, excluded=frozenset({"стол"}))
    lemmas = [r["Russian"] for r in result.rows]
    assert "стол" not in lemmas
    assert any(r.startswith("кино") for r in lemmas)
    assert result.excluded == ["стол"]


def test_build_skeleton_excluded_matches_by_match_key(skeleton_inputs):
    result = ni.build_skeleton(**skeleton_inputs, excluded=frozenset({"расчет"}))
    assert [ni.match_key(x) for x in result.excluded] == ["расчет"]
    assert all(not r["Russian"].startswith("расч") for r in result.rows)


def test_build_skeleton_histogram_counts_kept_rows_only(skeleton_inputs):
    result = ni.build_skeleton(**skeleton_inputs)
    assert result.histogram[ni.FLAG_OTHER_SHEET] == 1
    assert result.histogram[ni.FLAG_IMMUTABLE_PRESENT] == 1
    assert result.histogram.get(ni.FLAG_NO_WIKT_NOUN, 0) == 0
    for flag, count in result.histogram.items():
        kept = sum(flag in r["flags"].split(";") for r in result.rows)
        assert count == kept, flag


def test_build_skeleton_rows_have_fragment_columns(skeleton_inputs):
    result = ni.build_skeleton(**skeleton_inputs)
    for row in result.rows:
        assert set(row) == set(ni.FRAGMENT_COLUMNS)


def a2_inputs(tmp_path, lemma, kaikki_lines, or_rows):
    write_freq(tmp_path, [(lemma, "s", "50.0")])
    nouns = make_nouns(tmp_path, ("год",))
    kaikki = write(tmp_path / "kaikki.jsonl", "\n".join(kaikki_lines) + "\n")
    orx = make_or_dir(tmp_path, or_rows)
    md = write(tmp_path / "imm.md", IMMUTABLE_MD)
    root = make_data_dir(tmp_path, nouns=["год"])
    return {
        "freq_path": tmp_path / "freq.csv",
        "nouns_path": nouns,
        "kaikki_jsonl": kaikki,
        "openrussian_dir": orx,
        "immutable_md": md,
        "data_dir": root,
    }


@pytest.mark.parametrize("alt_first", [True, False])
@pytest.mark.parametrize("accented", ["пёс", "пё" + ACUTE + "с"])
def test_build_skeleton_or_yo_beats_kaikki_alt_spelling(tmp_path, alt_first, accented):
    alt = kaikki_line("пес", [], extra_tags=["alt-of"])
    real = kaikki_line("пёс", noun_forms("пёс", "пса", "псы", "псов"))
    lines = [alt, real] if alt_first else [real, alt]
    inputs = a2_inputs(
        tmp_path,
        "пес",
        lines,
        [or_noun("пёс", accented, "m", "пса", "псы", "псов")],
    )
    result = ni.build_skeleton(**inputs)
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row["Russian"] == "пёс"
    assert row["Plural"] == "псы"
    assert row["Genitive Sg"] == "пса"
    assert row["Genitive Pl"] == "псов"
    flags = row["flags"].split(";")
    for field in ("Plural", "Genitive Sg", "Genitive Pl", "Stress"):
        assert not any(flag.startswith(f"{field}:") for flag in flags)
    assert not any(flag.endswith(":missing") for flag in flags)
    assert ni.FLAG_NO_WIKT_NOUN not in flags


def test_build_skeleton_exact_spelling_without_or_yo_match(tmp_path):
    inputs = a2_inputs(
        tmp_path,
        "лес",
        [kaikki_line("лес", noun_forms("лес", "леса", "леса", "лесов"))],
        [or_noun("лес", "лес", "m", "леса", "леса", "лесов")],
    )
    result = ni.build_skeleton(**inputs)
    assert [r["Russian"] for r in result.rows] == ["лес"]
    assert result.rows[0]["Plural"] == "леса"


def test_build_skeleton_exact_spelling_kaikki_only(tmp_path):
    inputs = a2_inputs(
        tmp_path,
        "лес",
        [kaikki_line("лес", noun_forms("лес", "леса", "леса", "лесов"))],
        [],
    )
    result = ni.build_skeleton(**inputs)
    assert [r["Russian"] for r in result.rows] == ["лес"]
