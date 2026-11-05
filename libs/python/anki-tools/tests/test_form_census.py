import os
import sqlite3
from pathlib import Path

import pytest

from anki_tools import form_census as fc
from anki_tools import mutable_words_plan as mwp

SHEET_FILES = {
    "Nouns": "nouns.tsv",
    "Verbs": "verbs.tsv",
    "Adjectives": "adjectives.tsv",
    "Adverbs": "adverbs.tsv",
    "Pronouns": "pronouns.tsv",
    "Numerals": "numerals.tsv",
}
PARSERS = {
    "Nouns": "parse_nouns",
    "Verbs": "parse_verbs",
    "Adjectives": "parse_adjectives",
    "Adverbs": "parse_adverbs",
    "Pronouns": "parse_pronouns",
    "Numerals": "parse_numerals",
}
NOTE_TYPE_NAMES = {
    sheet: f"Russian - Mutable {sheet} (Ellis Version)" for sheet in SHEET_FILES
}


def fields_for(sheet, overrides=None):
    names = mwp.FIELD_NAMES[sheet]
    values = {name: f"{name}-v" for name in names}
    values[names[0]] = "слово"
    if sheet == "Adjectives":
        values["Russian (m)"] = "красный"
    if sheet == "Nouns":
        values["Gender"] = "m"
        values["Additional Info"] = ""
    values.update(overrides or {})
    return values


def all_sheets(**per_sheet):
    return {sheet: dict(per_sheet.get(sheet, {})) for sheet in fc.SHEETS}


def make_collection(path, notes_by_sheet, extra_types=()):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE notetypes (id INTEGER PRIMARY KEY, name TEXT)")
    con.execute("CREATE TABLE fields (ntid INTEGER, ord INTEGER, name TEXT)")
    con.execute(
        "CREATE TABLE notes (id INTEGER PRIMARY KEY, guid TEXT, mid INTEGER, flds TEXT)"
    )
    note_id = 1
    for index, sheet in enumerate(fc.SHEETS, start=1):
        con.execute(
            "INSERT INTO notetypes VALUES (?, ?)", (index, NOTE_TYPE_NAMES[sheet])
        )
        for ordinal, name in enumerate(mwp.FIELD_NAMES[sheet]):
            con.execute("INSERT INTO fields VALUES (?, ?, ?)", (index, ordinal, name))
        for guid, values in notes_by_sheet.get(sheet, {}).items():
            flds = "\x1f".join(values[name] for name in mwp.FIELD_NAMES[sheet])
            con.execute(
                "INSERT INTO notes VALUES (?, ?, ?, ?)", (note_id, guid, index, flds)
            )
            note_id += 1
    for offset, name in enumerate(extra_types, start=100):
        con.execute("INSERT INTO notetypes VALUES (?, ?)", (offset, name))
        con.execute("INSERT INTO fields VALUES (?, 0, 'Front')", (offset,))
        con.execute("INSERT INTO fields VALUES (?, 1, 'Back')", (offset,))
        con.execute(
            "INSERT INTO notes VALUES (?, ?, ?, ?)",
            (note_id, f"x{offset}", offset, "a\x1fb"),
        )
        note_id += 1
    con.commit()
    con.close()
    return path


def cells_by_field(cells):
    return {cell.field: cell for cell in cells}


class TestConstants:
    def test_empty_markers(self):
        assert fc.EMPTY_MARKERS == frozenset({"", "—", "–", "-", "--"})

    def test_sheets(self):
        assert fc.SHEETS == (
            "Nouns",
            "Verbs",
            "Adjectives",
            "Adverbs",
            "Pronouns",
            "Numerals",
        )

    def test_inflection_fields_exact(self):
        assert fc.INFLECTION_FIELDS == {
            "Nouns": ("Plural", "Genitive Sg", "Genitive Pl"),
            "Adjectives": ("Feminine", "Neuter", "Plural", "Short Form", "Comparative"),
            "Adverbs": ("Comparative",),
            "Pronouns": ("Gender Forms", "Oblique Forms"),
            "Numerals": ("Gender Forms", "Genitive"),
            "Verbs": (
                "Perfective",
                "Conjugation",
                "я (1sg)",
                "ты (2sg)",
                "они (3pl)",
                "Past (m / f)",
            ),
        }

    @pytest.mark.parametrize("sheet", sorted(mwp.FIELD_NAMES))
    def test_inflection_fields_exist_in_field_names(self, sheet):
        for name in fc.INFLECTION_FIELDS[sheet]:
            assert name in mwp.FIELD_NAMES[sheet]


class TestIsEmpty:
    @pytest.mark.parametrize(
        ("value", "dash_rule", "expected"),
        [
            ("", True, True),
            ("   ", True, True),
            ("—", True, True),
            ("–", True, True),
            ("-", True, True),
            ("--", True, True),
            (" — ", True, True),
            ("\t-\n", True, True),
            ("слова", True, False),
            ("-а", True, False),
            ("---", True, False),
            ("", False, True),
            ("   ", False, True),
            ("—", False, False),
            ("–", False, False),
            ("-", False, False),
            ("--", False, False),
            (" — ", False, False),
            ("слова", False, False),
        ],
    )
    def test_is_empty(self, value, dash_rule, expected):
        assert fc.is_empty(value, dash_rule=dash_rule) is expected

    def test_dash_rule_defaults_to_true(self):
        assert fc.is_empty("—") is True


class TestSheetForNoteTypeName:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Russian - Mutable Nouns (Ellis Version)", "Nouns"),
            ("Russian - Mutable Verbs (Ellis Version)", "Verbs"),
            ("Russian - Mutable Adjectives (Ellis Version)", "Adjectives"),
            ("Russian - Mutable Adverbs (Ellis Version)", "Adverbs"),
            ("Russian - Mutable Pronouns (Ellis Version)", "Pronouns"),
            ("Russian - Mutable Numerals (Ellis Version)", "Numerals"),
            ("Mutable Nouns", "Nouns"),
            ("Russian - Immutable Words (Ellis Version)", None),
            ("Basic", None),
            ("", None),
        ],
    )
    def test_mapping(self, name, expected):
        assert fc.sheet_for_note_type_name(name) == expected


VOCAB_DIR = Path(fc.__file__).parent / "data" / "russian-vocabulary"
PARSE_FUNCS = {
    "Nouns": mwp.parse_nouns,
    "Verbs": mwp.parse_verbs,
    "Adjectives": mwp.parse_adjectives,
    "Adverbs": mwp.parse_adverbs,
    "Pronouns": mwp.parse_pronouns,
    "Numerals": mwp.parse_numerals,
}
ADVERB_PLACEHOLDER = "\t".join(["2", "—", "", "", "", "none", "", "", "", ""])


TSV_HEADERS = {
    "Nouns": [
        "#",
        "Russian",
        "English",
        "Stress",
        "Gender",
        "Plural",
        "Genitive Sg",
        "Genitive Pl",
        "Animate",
        "Category",
        "Additional Info",
        "Examples",
    ],
    "Verbs": [
        "#",
        "Imperfective",
        "Perfective",
        "English",
        "Stress",
        "Conjugation",
        "я (1sg)",
        "ты (2sg)",
        "они (3pl)",
        "Past (m / f)",
        "Case / Preposition",
        "Additional Info",
        "Examples",
    ],
    "Adjectives": [
        "#",
        "Russian (m)",
        "English",
        "Stress",
        "Feminine",
        "Neuter",
        "Plural",
        "Short Form",
        "Comparative",
        "Opposite",
        "Stem Type",
        "Additional Info",
        "Examples",
    ],
    "Adverbs": [
        "#",
        "Adverb",
        "English",
        "Stress",
        "From Adjective",
        "Formation",
        "Comparative",
        "Additional Info",
        "Examples",
        "Status",
    ],
    "Pronouns": [
        "#",
        "Russian",
        "English",
        "Stress",
        "Pronoun Type",
        "Gender Forms",
        "Oblique Forms",
        "Additional Info",
        "Examples",
    ],
    "Numerals": [
        "#",
        "Russian",
        "English",
        "Stress",
        "Numeral Type",
        "Case Governed",
        "Gender Forms",
        "Genitive",
        "Additional Info",
        "Examples",
    ],
}


def write_tsvs(data_dir, rows_per_sheet=2):
    for sheet, header in TSV_HEADERS.items():
        lines = ["\t".join(header)]
        for n in range(1, rows_per_sheet + 1):
            cells = [f"{sheet[:2]}{n}-{name}" for name in header]
            cells[0] = str(n)
            if sheet == "Adverbs":
                cells[header.index("Formation")] = "regular"
                cells[header.index("Status")] = "ok"
            lines.append("\t".join(cells))
        (data_dir / SHEET_FILES[sheet]).write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )


class TestTsvCensusNotes:
    @pytest.fixture
    def data_dir(self, tmp_path):
        write_tsvs(tmp_path)
        return tmp_path

    def test_shape_and_values_match_parsers(self, data_dir):
        result = fc.tsv_census_notes(data_dir)
        assert set(result) == set(fc.SHEETS)
        for sheet, parser in PARSERS.items():
            rows = getattr(mwp, parser)(str(data_dir / SHEET_FILES[sheet]))
            assert len(rows) == 2
            expected = {
                row.guid: dict(zip(mwp.FIELD_NAMES[sheet], row.fields(), strict=True))
                for row in rows
            }
            assert result[sheet] == expected

    def test_field_names_are_keys(self, data_dir):
        result = fc.tsv_census_notes(str(data_dir))
        for sheet in fc.SHEETS:
            for values in result[sheet].values():
                assert list(values) == list(mwp.FIELD_NAMES[sheet])

    def test_missing_tsv_raises(self, data_dir):
        (data_dir / "nouns.tsv").unlink()
        with pytest.raises(FileNotFoundError):
            fc.tsv_census_notes(data_dir)


class TestCollectionCensusNotes:
    @pytest.fixture
    def collection(self, tmp_path):
        notes = {
            "Nouns": {
                "n1": fields_for("Nouns", {"Plural": "", "Genitive Sg": "стола"}),
                "n2": fields_for("Nouns", {"Plural": "—"}),
            },
            "Verbs": {"v1": fields_for("Verbs")},
        }
        path = make_collection(
            tmp_path / "collection.anki2",
            notes,
            extra_types=("Russian - Immutable Words",),
        )
        return path, notes

    def test_reads_mutable_notes_by_field_ord(self, collection):
        path, notes = collection
        result = fc.collection_census_notes(path)
        assert result["Nouns"] == notes["Nouns"]
        assert result["Verbs"] == notes["Verbs"]

    def test_all_sheet_keys_present_and_unmapped_types_ignored(self, collection):
        path, _ = collection
        result = fc.collection_census_notes(path)
        assert set(result) == set(fc.SHEETS)
        assert result["Adjectives"] == {}
        guids = {guid for by_guid in result.values() for guid in by_guid}
        assert not any(guid.startswith("x") for guid in guids)
        assert guids == {"n1", "n2", "v1"}

    def test_accepts_str_path(self, collection):
        path, notes = collection
        assert fc.collection_census_notes(str(path))["Nouns"] == notes["Nouns"]

    def test_missing_path_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            fc.collection_census_notes(tmp_path / "nope.anki2")

    def test_source_untouched(self, collection):
        path, _ = collection
        os.utime(path, ns=(1_000_000_000_000_000_000, 1_000_000_000_000_000_000))
        before_bytes = path.read_bytes()
        before_mtime = path.stat().st_mtime_ns
        before_listing = sorted(p.name for p in path.parent.iterdir())
        fc.collection_census_notes(path)
        assert path.read_bytes() == before_bytes
        assert path.stat().st_mtime_ns == before_mtime
        assert sorted(p.name for p in path.parent.iterdir()) == before_listing

    def test_source_change_is_detectable_control(self, collection):
        path, _ = collection
        before = path.read_bytes()
        con = sqlite3.connect(path)
        con.execute("UPDATE notes SET guid = 'changed' WHERE guid = 'v1'")
        con.commit()
        con.close()
        assert path.read_bytes() != before


def census_pair():
    tsv = all_sheets(
        Nouns={
            "g1": fields_for("Nouns", {"Plural": "—", "Genitive Pl": "столов"}),
            "g2": fields_for("Nouns"),
        },
        Verbs={"v1": fields_for("Verbs", {"Perfective": ""})},
    )
    return tsv


class TestCounts:
    def test_note_counts(self):
        notes = all_sheets(
            Nouns={"a": fields_for("Nouns"), "b": fields_for("Nouns")},
            Verbs={"v": fields_for("Verbs")},
        )
        assert fc.note_counts(notes) == {
            "Nouns": 2,
            "Verbs": 1,
            "Adjectives": 0,
            "Adverbs": 0,
            "Pronouns": 0,
            "Numerals": 0,
        }

    def test_empty_counts_shape_zero_allowed(self):
        counts = fc.empty_counts(all_sheets())
        assert set(counts) == set(fc.INFLECTION_FIELDS)
        for sheet, names in fc.INFLECTION_FIELDS.items():
            assert counts[sheet] == dict.fromkeys(names, 0)

    @pytest.mark.parametrize(
        ("dash_rule", "expected_plural", "expected_gen_pl"),
        [(True, 3, 1), (False, 1, 1)],
    )
    def test_empty_counts_dash_rule(self, dash_rule, expected_plural, expected_gen_pl):
        notes = all_sheets(
            Nouns={
                "a": fields_for("Nouns", {"Plural": "—"}),
                "b": fields_for("Nouns", {"Plural": "-"}),
                "c": fields_for("Nouns", {"Plural": ""}),
                "d": fields_for("Nouns", {"Genitive Pl": "  "}),
            }
        )
        counts = fc.empty_counts(notes, dash_rule=dash_rule)
        assert counts["Nouns"]["Plural"] == expected_plural
        assert counts["Nouns"]["Genitive Pl"] == expected_gen_pl
        assert counts["Nouns"]["Genitive Sg"] == 0

    def test_empty_counts_guid_filter_with_unfiltered_control(self):
        notes = all_sheets(
            Nouns={
                "a": fields_for("Nouns", {"Plural": ""}),
                "b": fields_for("Nouns", {"Plural": ""}),
                "c": fields_for("Nouns", {"Plural": ""}),
            }
        )
        assert fc.empty_counts(notes)["Nouns"]["Plural"] == 3
        filtered = fc.empty_counts(notes, guids={"Nouns": {"a", "c", "zzz"}})
        assert filtered["Nouns"]["Plural"] == 2
        assert set(filtered) == set(fc.INFLECTION_FIELDS)

    def test_empty_counts_guid_filter_excludes_all(self):
        notes = all_sheets(Nouns={"a": fields_for("Nouns", {"Plural": ""})})
        assert fc.empty_counts(notes, guids={"Nouns": set()})["Nouns"]["Plural"] == 0


class TestReconcile:
    def dash_pair(self):
        tsv = all_sheets(
            Nouns={
                "g1": fields_for("Nouns", {"Plural": "—"}),
                "g2": fields_for("Nouns"),
            }
        )
        coll = all_sheets(
            Nouns={"g1": fields_for("Nouns", {"Plural": ""}), "g2": fields_for("Nouns")}
        )
        return tsv, coll

    def test_dash_rule_true_reconciles(self):
        tsv, coll = self.dash_pair()
        result = fc.reconcile(tsv, coll, dash_rule=True)
        assert result.reconciles is True
        assert result.mismatches == {}
        assert result.tsv_counts["Nouns"]["Plural"] == 1
        assert result.collection_counts["Nouns"]["Plural"] == 1

    def test_dash_rule_default_is_true(self):
        tsv, coll = self.dash_pair()
        assert fc.reconcile(tsv, coll).reconciles is True

    def test_dash_rule_false_mismatches_positive_control(self):
        tsv, coll = self.dash_pair()
        result = fc.reconcile(tsv, coll, dash_rule=False)
        assert result.reconciles is False
        assert result.mismatches == {("Nouns", "Plural"): (0, 1)}

    def test_real_count_difference_is_mismatch(self):
        tsv = all_sheets(Nouns={"g1": fields_for("Nouns", {"Genitive Pl": ""})})
        coll = all_sheets(Nouns={"g1": fields_for("Nouns", {"Genitive Pl": "столов"})})
        result = fc.reconcile(tsv, coll)
        assert result.reconciles is False
        assert result.mismatches == {("Nouns", "Genitive Pl"): (1, 0)}

    def test_orphans_and_unbuilt_reported_not_failures(self):
        tsv = all_sheets(
            Nouns={
                "b": fields_for("Nouns"),
                "a": fields_for("Nouns", {"Plural": ""}),
                "shared": fields_for("Nouns"),
            }
        )
        coll = all_sheets(
            Nouns={
                "z": fields_for("Nouns", {"Genitive Sg": ""}),
                "y": fields_for("Nouns"),
                "shared": fields_for("Nouns"),
            }
        )
        result = fc.reconcile(tsv, coll)
        assert result.unbuilt["Nouns"] == ("a", "b")
        assert result.orphans["Nouns"] == ("y", "z")
        assert result.mismatches == {}
        assert result.reconciles is True

    def test_one_sided_empties_do_not_mismatch_but_shared_ones_do(self):
        tsv = all_sheets(
            Nouns={
                "only-tsv": fields_for("Nouns", {"Plural": ""}),
                "s": fields_for("Nouns"),
            }
        )
        coll = all_sheets(
            Nouns={
                "only-coll": fields_for("Nouns", {"Plural": ""}),
                "s": fields_for("Nouns", {"Plural": ""}),
            }
        )
        result = fc.reconcile(tsv, coll)
        assert result.mismatches == {("Nouns", "Plural"): (0, 1)}
        assert result.reconciles is False

    def test_collection_counts_exclude_orphans(self):
        tsv = all_sheets(Nouns={"s": fields_for("Nouns")})
        coll = all_sheets(
            Nouns={"s": fields_for("Nouns"), "o": fields_for("Nouns", {"Plural": ""})}
        )
        result = fc.reconcile(tsv, coll)
        assert result.collection_counts["Nouns"]["Plural"] == 0
        assert result.orphans["Nouns"] == ("o",)

    def test_identical_sides(self):
        tsv = census_pair()
        result = fc.reconcile(tsv, census_pair())
        assert result.reconciles is True
        assert all(not v for v in result.orphans.values())
        assert all(not v for v in result.unbuilt.values())

    def test_reconciliation_is_frozen(self):
        result = fc.reconcile(all_sheets(), all_sheets())
        with pytest.raises(AttributeError):
            result.orphans = {}


class TestClassifyCells:
    def classify(self, sheet, overrides, guid="g"):
        return fc.classify_cells(sheet, guid, fields_for(sheet, overrides))

    def test_no_empties_returns_empty_list(self):
        assert self.classify("Nouns", {}) == []

    def test_cell_fields_and_order(self):
        cells = self.classify(
            "Nouns", {"Genitive Pl": "", "Plural": " — ", "Genitive Sg": ""}
        )
        assert [c.field for c in cells] == ["Plural", "Genitive Sg", "Genitive Pl"]
        first = cells[0]
        assert (first.sheet, first.guid, first.headword, first.marker) == (
            "Nouns",
            "g",
            "слово",
            "—",
        )
        assert cells[1].marker == "" and cells[2].marker == ""
        assert all(isinstance(c, fc.EmptyCell) for c in cells)
        assert all(c.reason.strip() for c in cells)

    def test_verb_headword_is_imperfective(self):
        cells = self.classify("Verbs", {"Imperfective": "делать", "Perfective": ""})
        assert cells[0].headword == "делать"

    def test_inflection_order_verbs(self):
        overrides = {name: "" for name in fc.INFLECTION_FIELDS["Verbs"]}
        cells = self.classify("Verbs", overrides)
        assert [c.field for c in cells] == list(fc.INFLECTION_FIELDS["Verbs"])

    def test_non_inflection_field_ignored(self):
        assert self.classify("Nouns", {"Additional Info": ""}) == []

    @pytest.mark.parametrize("marker", ["—", "–", "-", "--"])
    @pytest.mark.parametrize(
        "sheet", ["Nouns", "Verbs", "Adjectives", "Adverbs", "Pronouns", "Numerals"]
    )
    def test_explicit_dash_is_not_applicable(self, sheet, marker):
        name = fc.INFLECTION_FIELDS[sheet][0]
        cells = self.classify(sheet, {name: marker})
        assert len(cells) == 1
        assert cells[0].status == fc.NOT_APPLICABLE
        assert cells[0].marker == marker
        assert cells[0].reason.strip()

    @pytest.mark.parametrize(
        "sheet", ["Nouns", "Verbs", "Adjectives", "Adverbs", "Pronouns", "Numerals"]
    )
    def test_blank_with_no_rule_is_missing_control(self, sheet):
        name = fc.INFLECTION_FIELDS[sheet][0]
        cells = self.classify(sheet, {name: ""})
        assert len(cells) == 1
        assert cells[0].status == fc.MISSING
        assert cells[0].marker == ""
        assert cells[0].reason.strip()

    def test_dash_beats_indeclinable(self):
        cells = self.classify(
            "Nouns", {"Plural": "—", "Additional Info": "indeclinable"}
        )
        assert cells[0].status == fc.NOT_APPLICABLE
        assert cells[0].marker == "—"

    def test_status_constants(self):
        assert fc.NOT_APPLICABLE == "not-applicable"
        assert fc.MISSING == "missing"

    @pytest.mark.parametrize(
        ("info", "expected"),
        [
            (
                "indeclinable",
                {"Plural": "na", "Genitive Sg": "na", "Genitive Pl": "na"},
            ),
            (
                "Indeclinable loanword",
                {"Plural": "na", "Genitive Sg": "na", "Genitive Pl": "na"},
            ),
            (
                "INDECLINABLE",
                {"Plural": "na", "Genitive Sg": "na", "Genitive Pl": "na"},
            ),
            (
                "no plural",
                {"Plural": "na", "Genitive Sg": "missing", "Genitive Pl": "na"},
            ),
            (
                "No Plural in use",
                {"Plural": "na", "Genitive Sg": "missing", "Genitive Pl": "na"},
            ),
            (
                "uncountable",
                {"Plural": "na", "Genitive Sg": "missing", "Genitive Pl": "na"},
            ),
            (
                "Uncountable noun",
                {"Plural": "na", "Genitive Sg": "missing", "Genitive Pl": "na"},
            ),
            (
                "singular-only",
                {"Plural": "na", "Genitive Sg": "missing", "Genitive Pl": "na"},
            ),
            (
                "singular only",
                {"Plural": "na", "Genitive Sg": "missing", "Genitive Pl": "na"},
            ),
            (
                "Singular Only; mass",
                {"Plural": "na", "Genitive Sg": "missing", "Genitive Pl": "na"},
            ),
            (
                "irregular stress",
                {
                    "Plural": "missing",
                    "Genitive Sg": "missing",
                    "Genitive Pl": "missing",
                },
            ),
            (
                "",
                {
                    "Plural": "missing",
                    "Genitive Sg": "missing",
                    "Genitive Pl": "missing",
                },
            ),
            (
                "plural form exists",
                {
                    "Plural": "missing",
                    "Genitive Sg": "missing",
                    "Genitive Pl": "missing",
                },
            ),
        ],
    )
    def test_noun_additional_info_rules(self, info, expected):
        overrides = {
            "Plural": "",
            "Genitive Sg": "",
            "Genitive Pl": "",
            "Additional Info": info,
        }
        cells = cells_by_field(self.classify("Nouns", overrides))
        statuses = {
            field: ("na" if cell.status == fc.NOT_APPLICABLE else cell.status)
            for field, cell in cells.items()
        }
        assert statuses == expected

    def test_indeclinable_reason_text(self):
        overrides = {
            "Plural": "",
            "Genitive Sg": "",
            "Genitive Pl": "",
            "Additional Info": "indeclinable",
        }
        for cell in self.classify("Nouns", overrides):
            assert "indeclinable noun" in cell.reason.lower()

    @pytest.mark.parametrize(
        ("gender", "expected_gen_sg"),
        [
            ("pl-only", fc.NOT_APPLICABLE),
            ("m", fc.MISSING),
            ("f", fc.MISSING),
            ("n", fc.MISSING),
        ],
    )
    def test_plural_only_gender(self, gender, expected_gen_sg):
        cells = cells_by_field(
            self.classify(
                "Nouns",
                {"Gender": gender, "Genitive Sg": "", "Plural": "", "Genitive Pl": ""},
            )
        )
        assert cells["Genitive Sg"].status == expected_gen_sg
        assert cells["Plural"].status == fc.MISSING
        assert cells["Genitive Pl"].status == fc.MISSING

    @pytest.mark.parametrize(
        ("russian_m", "relational"),
        [
            ("русский", True),
            ("городской", True),
            ("француский", True),
            ("дружеский", True),
            ("немецкий", True),
            ("царский", True),
            ("кузнецкий", True),
            ("городско́й", True),
            ("ру́сский", True),
            ("  русский  ", True),
            ("красный", False),
            ("большой", False),
            ("синий", False),
            ("скийный", False),
        ],
    )
    def test_relational_adjective(self, russian_m, relational):
        empties = {name: "" for name in fc.INFLECTION_FIELDS["Adjectives"]}
        cells = cells_by_field(
            self.classify("Adjectives", {**empties, "Russian (m)": russian_m})
        )
        for field in ("Short Form", "Comparative"):
            expected = fc.NOT_APPLICABLE if relational else fc.MISSING
            assert cells[field].status == expected, field
        for field in ("Feminine", "Neuter", "Plural"):
            assert cells[field].status == fc.MISSING, field

    @pytest.mark.parametrize("sheet", ["Verbs", "Adverbs", "Pronouns", "Numerals"])
    def test_noun_adjective_rules_do_not_leak(self, sheet):
        overrides = {name: "" for name in fc.INFLECTION_FIELDS[sheet]}
        overrides.update(
            {
                "Additional Info": "indeclinable",
                "Gender": "pl-only",
                "Russian (m)": "русский",
            }
        )
        for cell in self.classify(sheet, overrides):
            assert cell.status == fc.MISSING


class TestCensusCells:
    def test_empty_input(self):
        assert fc.census_cells(all_sheets()) == []

    def test_ordering_sheets_then_notes(self):
        notes = {
            "Numerals": {"u1": fields_for("Numerals", {"Genitive": ""})},
            "Verbs": {"v1": fields_for("Verbs", {"Perfective": ""})},
            "Nouns": {
                "n2": fields_for("Nouns", {"Plural": ""}),
                "n1": fields_for("Nouns", {"Genitive Sg": "", "Genitive Pl": ""}),
            },
            "Adjectives": {},
            "Adverbs": {},
            "Pronouns": {},
        }
        cells = fc.census_cells(notes)
        assert [(c.sheet, c.guid, c.field) for c in cells] == [
            ("Nouns", "n2", "Plural"),
            ("Nouns", "n1", "Genitive Sg"),
            ("Nouns", "n1", "Genitive Pl"),
            ("Verbs", "v1", "Perfective"),
            ("Numerals", "u1", "Genitive"),
        ]

    def test_full_notes_yield_no_cells_control(self):
        notes = all_sheets(
            Nouns={"n": fields_for("Nouns")}, Verbs={"v": fields_for("Verbs")}
        )
        assert fc.census_cells(notes) == []

    def test_cells_match_classify_cells(self):
        values = fields_for("Nouns", {"Plural": "—", "Genitive Pl": ""})
        cells = fc.census_cells(all_sheets(Nouns={"n": values}))
        assert cells == fc.classify_cells("Nouns", "n", values)


REAL_DATA_DIR = Path(fc.__file__).resolve().parent / "data" / "russian-vocabulary"

PLANNED_EMPTY_COUNTS = {
    "Nouns": {"Plural": 134, "Genitive Sg": 622, "Genitive Pl": 623},
    "Adjectives": {"Short Form": 158, "Comparative": 165},
    "Adverbs": {"Comparative": 40},
    "Pronouns": {"Gender Forms": 11},
    "Numerals": {"Gender Forms": 44},
    "Verbs": {
        "Perfective": 4,
        "Conjugation": 160,
        "я (1sg)": 162,
        "ты (2sg)": 162,
        "они (3pl)": 162,
        "Past (m / f)": 177,
    },
}
PENDING_IMPORT_VERB_GUID = "t1#RNs`=(A"
ORPHANED_NOUNS = {"пальто", "кино", "кафе", "метро", "кофе"}


def _live_collection_path():
    from anki_tools.audio_naming import get_anki_collection_path

    path = Path(get_anki_collection_path())
    return path if path.exists() else None


class TestRealData:
    @pytest.fixture(scope="class")
    def tsv_notes(self):
        return fc.tsv_census_notes(REAL_DATA_DIR)

    def test_tsv_note_counts(self, tsv_notes):
        assert fc.note_counts(tsv_notes) == {
            "Nouns": 631,
            "Verbs": 215,
            "Adjectives": 172,
            "Adverbs": 134,
            "Pronouns": 29,
            "Numerals": 55,
        }

    @pytest.mark.parametrize(
        ("sheet", "field", "expected"),
        [
            (sheet, field, count)
            for sheet, fields in PLANNED_EMPTY_COUNTS.items()
            for field, count in fields.items()
        ],
    )
    def test_tsv_empty_counts_match_planning_census(
        self, tsv_notes, sheet, field, expected
    ):
        assert fc.empty_counts(tsv_notes)[sheet][field] == expected

    def test_counting_only_empty_strings_cannot_reproduce_the_planning_counts(
        self, tsv_notes
    ):
        strict = fc.empty_counts(tsv_notes, dash_rule=False)
        differing = [
            (sheet, field)
            for sheet, fields in PLANNED_EMPTY_COUNTS.items()
            for field, count in fields.items()
            if strict[sheet][field] != count
        ]
        assert ("Adjectives", "Short Form") in differing
        assert strict["Adjectives"]["Short Form"] == 151

    def test_every_empty_cell_is_classified_and_totals_match(self, tsv_notes):
        cells = fc.census_cells(tsv_notes)
        planned_total = sum(
            c for f in PLANNED_EMPTY_COUNTS.values() for c in f.values()
        )
        assert len(cells) == planned_total
        assert {c.status for c in cells} == {fc.MISSING, fc.NOT_APPLICABLE}
        assert all(c.reason for c in cells)

    def test_live_collection_reconciles_with_tsv(self, tsv_notes):
        path = _live_collection_path()
        if path is None:
            pytest.skip("no local Anki collection")
        before = (path.stat().st_mtime_ns, path.stat().st_size)
        collection = fc.collection_census_notes(path)
        assert (path.stat().st_mtime_ns, path.stat().st_size) == before
        result = fc.reconcile(tsv_notes, collection)
        assert result.reconciles, result.mismatches
        assert result.unbuilt == {
            **{s: () for s in fc.SHEETS},
            "Verbs": (PENDING_IMPORT_VERB_GUID,),
        }
        orphan_names = {
            collection["Nouns"][g]["Russian"] for g in result.orphans["Nouns"]
        }
        assert orphan_names == ORPHANED_NOUNS
        assert all(not result.orphans[s] for s in fc.SHEETS if s != "Nouns")

    def test_dash_rule_is_load_bearing_for_the_reconciliation_inputs(self, tsv_notes):
        path = _live_collection_path()
        if path is None:
            pytest.skip("no local Anki collection")
        collection = fc.collection_census_notes(path)
        loose = fc.reconcile(tsv_notes, collection, dash_rule=True)
        strict = fc.reconcile(tsv_notes, collection, dash_rule=False)
        assert loose.tsv_counts != strict.tsv_counts
        assert loose.tsv_counts["Adjectives"]["Short Form"] == 158
