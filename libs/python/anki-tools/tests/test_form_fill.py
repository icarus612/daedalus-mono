import copy
import json
import os
import unicodedata
from pathlib import Path
from urllib.parse import quote

import pytest

from anki_tools import form_census as fc
from anki_tools import form_fill as ff
from anki_tools import mutable_words_plan as mwp

ACUTE = "́"


def fields_for(sheet, overrides=None):
    names = mwp.FIELD_NAMES[sheet]
    values = {name: f"{name}-v" for name in names}
    values.update(overrides or {})
    return values


def all_sheets(**per_sheet):
    return {sheet: dict(per_sheet.get(sheet, {})) for sheet in fc.SHEETS}


def entry(pos, *forms):
    return {"pos": pos, "forms": [[form, list(tags)] for form, tags in forms]}


def noun_fields(**overrides):
    base = {"Russian": "год", "Plural": "", "Genitive Sg": "", "Genitive Pl": ""}
    base.update({"Additional Info": ""})
    base.update(overrides)
    return fields_for("Nouns", base)


def verb_fields(**overrides):
    return fields_for(
        "Verbs", {"Imperfective": "делать", "Perfective": "", **overrides}
    )


EMPTY_GENERATED_VERB = {
    "Conjugation": "",
    "я (1sg)": "",
    "ты (2sg)": "",
    "они (3pl)": "",
    "Past (m / f)": "",
}


def adj_fields(**overrides):
    return fields_for("Adjectives", {"Russian (m)": "новый", **overrides})


def adv_fields(**overrides):
    return fields_for("Adverbs", {"Adverb": "быстро", **overrides})


class TestConstants:
    def test_generated_fields(self):
        assert ff.GENERATED_FIELDS == {
            "Nouns": ("Plural", "Genitive Sg", "Genitive Pl"),
            "Verbs": (
                "Conjugation",
                "я (1sg)",
                "ты (2sg)",
                "они (3pl)",
                "Past (m / f)",
            ),
            "Adjectives": ("Short Form", "Comparative"),
            "Adverbs": ("Comparative",),
        }

    def test_statuses(self):
        assert ff.STATUS_FILLED == "missing-filled"
        assert ff.STATUS_NOT_APPLICABLE == "not-applicable"
        assert ff.STATUS_UNRESOLVED == "unresolved"

    def test_excluded_by_plan(self):
        assert ff.EXCLUDED_BY_PLAN == frozenset(
            {
                ("Numerals", "Gender Forms"),
                ("Numerals", "Genitive"),
                ("Pronouns", "Oblique Forms"),
                ("Adverbs", "Formation"),
            }
        )

    def test_columns(self):
        assert ff.COLUMNS == (
            "note type",
            "headword",
            "guid",
            "field",
            "generated value",
            "reference (source + entry URL)",
            "status",
        )

    def test_errors_are_value_errors(self):
        assert issubclass(ff.OverlapError, ValueError)
        assert issubclass(ff.NonEmptyTargetError, ValueError)


class TestNormalizeLemma:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("просто (adverb)", "просто"),
            ("го́д", "год"),
            ("Год", "год"),
            ("  год  ", "год"),
            ("год", "год"),
            ("е" + "̈", "ё"),
        ],
    )
    def test_cases(self, text, expected):
        assert ff.normalize_lemma(text) == expected

    def test_nfc_output(self):
        result = ff.normalize_lemma("е" + "̈")
        assert unicodedata.is_normalized("NFC", result)


class TestLemmaFor:
    @pytest.mark.parametrize(
        "sheet, fields, expected",
        [
            ("Nouns", {"Russian": "Го́д"}, "год"),
            ("Adjectives", {"Russian (m)": "но́вый"}, "новый"),
            ("Adverbs", {"Adverb": "бы́стро"}, "быстро"),
            ("Verbs", {"Imperfective": "де́лать", "Perfective": "сде́лать"}, "делать"),
            ("Verbs", {"Imperfective": "", "Perfective": "сде́лать"}, "сделать"),
            ("Verbs", {"Imperfective": "—", "Perfective": "сде́лать"}, "сделать"),
            ("Verbs", {"Imperfective": "  ", "Perfective": "сде́лать"}, "сделать"),
        ],
    )
    def test_cases(self, sheet, fields, expected):
        assert ff.lemma_for(sheet, fields) == expected


class TestHouseStress:
    @pytest.mark.parametrize(
        "form, expected",
        [
            ("мо́г", "мог"),
            ("го́д", "год"),
            ("лет", "лет"),
            ("все" + ACUTE + "х", "всех"),
            ("нового́", "нового́"),
            ("но́вый", "но́вый"),
            ("жё" + ACUTE + "сткий", "жёсткий"),
            ("ё" + ACUTE, "ё"),
            ("ё" + ACUTE + "лка", "ёлка"),
            ("Го́д", "Год"),
            ("пло́хо но́вый", "пло́хо но́вый"),
            ("мо́г нового́", "мог нового́"),
        ],
    )
    def test_cases(self, form, expected):
        assert ff.house_stress(form) == expected

    def test_never_mark_after_yo(self):
        assert ACUTE not in ff.house_stress("приё" + ACUTE + "м")

    def test_polysyllable_mark_preserved_control(self):
        assert ACUTE in ff.house_stress("коро́ва")

    def test_output_is_nfc(self):
        assert unicodedata.is_normalized(
            "NFC", ff.house_stress("е" + "̈" + ACUTE + "лка")
        )


class TestStripOptionalPrefix:
    @pytest.mark.parametrize(
        "form, expected",
        [
            ("(по)быстре́е", "быстре́е"),
            ("быстре́е", "быстре́е"),
            ("(по)лучше", "лучше"),
        ],
    )
    def test_cases(self, form, expected):
        assert ff.strip_optional_prefix(form) == expected


class TestStripFootnoteMarks:
    @pytest.mark.parametrize(
        "form, expected",
        [
            ("бра́тьев^*", "бра́тьев"),
            ("*моло́к", "моло́к"),
            ("мо*ло^́к", "моло́к"),
            ("^*", ""),
            ("*", ""),
            ("^", ""),
            ("моло́к", "моло́к"),
            ("", ""),
            ("*(по)быстре́е", "(по)быстре́е"),
        ],
    )
    def test_cases(self, form, expected):
        assert ff.strip_footnote_marks(form) == expected

    def test_leaves_no_marks_control(self):
        result = ff.strip_footnote_marks("a*b^c**d^^")
        assert "*" not in result and "^" not in result


class TestFootnoteMarksInGenerate:
    @pytest.mark.parametrize(
        "sheet, field, fields, forms, pos, expected",
        [
            (
                "Nouns",
                "Genitive Pl",
                noun_fields(Russian="брат"),
                [("бра́тьев^*", ["genitive", "plural"])],
                "noun",
                "бра́тьев",
            ),
            (
                "Nouns",
                "Genitive Pl",
                noun_fields(Russian="брат"),
                [("*бра́тьев", ["genitive", "plural"])],
                "noun",
                "бра́тьев",
            ),
            (
                "Nouns",
                "Genitive Pl",
                noun_fields(Russian="брат"),
                [("бра́тьев", ["genitive", "plural"])],
                "noun",
                "бра́тьев",
            ),
            (
                "Nouns",
                "Genitive Pl",
                noun_fields(Russian="брат"),
                [("*моло́к^", ["genitive", "plural"])],
                "noun",
                "моло́к",
            ),
            (
                "Nouns",
                "Genitive Pl",
                noun_fields(Russian="брат"),
                [("*ле́т^*", ["genitive", "plural"])],
                "noun",
                "лет",
            ),
            (
                "Verbs",
                "я (1sg)",
                verb_fields(),
                [("де́лаю*", ["present", "first-person", "singular"])],
                "verb",
                "де́лаю",
            ),
            (
                "Verbs",
                "ты (2sg)",
                verb_fields(),
                [("^де́лаешь", ["present", "second-person", "singular"])],
                "verb",
                "де́лаешь",
            ),
            (
                "Verbs",
                "они (3pl)",
                verb_fields(),
                [("де́лают^*", ["present", "third-person", "plural"])],
                "verb",
                "де́лают",
            ),
            (
                "Adjectives",
                "Comparative",
                adj_fields(),
                [("нове́е*", ["comparative"])],
                "adj",
                "нове́е",
            ),
            (
                "Adjectives",
                "Comparative",
                adj_fields(),
                [("*(по)нове́е^", ["comparative"])],
                "adj",
                "нове́е",
            ),
            (
                "Adverbs",
                "Comparative",
                adv_fields(),
                [("быстре́е^*", ["comparative"])],
                "adv",
                "быстре́е",
            ),
        ],
    )
    def test_marks_removed(self, sheet, field, fields, forms, pos, expected):
        lemma = ff.lemma_for(sheet, fields)
        entries = {lemma: [entry(pos, *forms)]}
        assert ff.generate_value(sheet, field, fields, entries) == expected

    def test_marked_noun_conjugation_unaffected_control(self):
        e = entry(
            "verb",
            ("де́лаешь^*", ["present", "second-person", "singular"]),
            ("*де́лают", ["present", "third-person", "plural"]),
        )
        assert (
            ff.generate_value("Verbs", "Conjugation", verb_fields(), {"делать": [e]})
            == "1st (-ешь)"
        )

    def test_marked_short_form_and_past(self):
        e = entry(
            "adj",
            ("нов*", ["short-form", "masculine"]),
            ("*нова́", ["short-form", "feminine"]),
        )
        assert (
            ff.generate_value("Adjectives", "Short Form", adj_fields(), {"новый": [e]})
            == "нов, нова́"
        )
        v = entry(
            "verb",
            ("де́лал^", ["past", "masculine", "singular"]),
            ("*де́лала", ["past", "feminine", "singular"]),
        )
        assert (
            ff.generate_value("Verbs", "Past (m / f)", verb_fields(), {"делать": [v]})
            == "де́лал / де́лала"
        )

    @pytest.mark.parametrize("form", ["^*", "*", "^"])
    def test_empty_after_removal_rejected_without_fallthrough(self, form):
        entries = {
            "год": [
                entry(
                    "noun",
                    (form, ["nominative", "plural"]),
                    ("го́ды", ["nominative", "plural"]),
                )
            ]
        }
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) is None

    @pytest.mark.parametrize("form", ["*бу́дешь делать", "-*", "*-^"])
    def test_whitespace_or_dash_check_runs_after_removal(self, form):
        entries = {"год": [entry("noun", (form, ["nominative", "plural"]))]}
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) is None


class TestWiktionaryUrl:
    @pytest.mark.parametrize("lemma", ["год", "делать", "ёлка"])
    def test_cases(self, lemma):
        assert (
            ff.wiktionary_url(lemma)
            == f"https://en.wiktionary.org/wiki/{quote(lemma)}#Russian"
        )

    def test_is_percent_encoded(self):
        url = ff.wiktionary_url("год")
        assert "%D0%B3%D0%BE%D0%B4" in url
        assert "год" not in url


NOUN_ENTRY = entry(
    "noun",
    ("го́д", ["nominative", "singular"]),
    ("года́", ["genitive", "singular"]),
    ("го́ды", ["nominative", "plural"]),
    ("лет", ["genitive", "plural"]),
)


class TestGenerateNouns:
    @pytest.mark.parametrize(
        "field, expected",
        [("Plural", "го́ды"), ("Genitive Sg", "года́"), ("Genitive Pl", "лет")],
    )
    def test_fields(self, field, expected):
        entries = {"год": [NOUN_ENTRY]}
        assert ff.generate_value("Nouns", field, noun_fields(), entries) == expected

    def test_absent_lemma_is_none(self):
        assert (
            ff.generate_value("Nouns", "Plural", noun_fields(), {"дом": [NOUN_ENTRY]})
            is None
        )

    def test_wrong_pos_ignored(self):
        entries = {"год": [entry("verb", ("го́ды", ["nominative", "plural"]))]}
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) is None

    def test_wrong_pos_skipped_then_right_pos_used(self):
        entries = {
            "год": [entry("verb", ("ложь", ["nominative", "plural"])), NOUN_ENTRY]
        }
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) == "го́ды"

    def test_missing_form_is_none(self):
        entries = {"год": [entry("noun", ("го́д", ["nominative", "singular"]))]}
        assert ff.generate_value("Nouns", "Genitive Pl", noun_fields(), entries) is None

    def test_first_form_in_list_order(self):
        entries = {
            "год": [
                entry(
                    "noun",
                    ("го́ды", ["nominative", "plural"]),
                    ("года́", ["nominative", "plural"]),
                )
            ]
        }
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) == "го́ды"

    def test_first_entry_in_list_order(self):
        entries = {
            "год": [
                entry("noun", ("первый", ["nominative", "plural"])),
                entry("noun", ("второй", ["nominative", "plural"])),
            ]
        }
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) == "первый"

    @pytest.mark.parametrize("tag", ["dated", "obsolete", "archaic", "colloquial"])
    def test_ignored_tags_skipped(self, tag):
        entries = {
            "год": [
                entry(
                    "noun",
                    ("ста́рое", ["nominative", "plural", tag]),
                    ("го́ды", ["nominative", "plural"]),
                )
            ]
        }
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) == "го́ды"

    def test_only_ignored_form_is_none(self):
        entries = {
            "год": [entry("noun", ("ста́рое", ["nominative", "plural", "dated"]))]
        }
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) is None

    def test_other_tags_do_not_block_control(self):
        entries = {"год": [entry("noun", ("го́ды", ["nominative", "plural", "rare"]))]}
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) == "го́ды"

    def test_requires_both_tags(self):
        entries = {"год": [entry("noun", ("x", ["nominative"]), ("y", ["plural"]))]}
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) is None

    def test_optional_prefix_stripped(self):
        entries = {"год": [entry("noun", ("(по)го́ды", ["nominative", "plural"]))]}
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) == "го́ды"

    def test_monosyllable_destressed(self):
        entries = {"год": [entry("noun", ("ле́т", ["genitive", "plural"]))]}
        assert (
            ff.generate_value("Nouns", "Genitive Pl", noun_fields(), entries) == "лет"
        )

    @pytest.mark.parametrize("form", ["бу́дешь делать", "-"])
    def test_compound_or_dash_rejected(self, form):
        entries = {"год": [entry("noun", (form, ["nominative", "plural"]))]}
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) is None

    def test_rejected_form_is_not_replaced_by_later_one(self):
        entries = {
            "год": [
                entry(
                    "noun",
                    ("-", ["nominative", "plural"]),
                    ("го́ды", ["nominative", "plural"]),
                )
            ]
        }
        assert ff.generate_value("Nouns", "Plural", noun_fields(), entries) is None

    @pytest.mark.parametrize(
        "sheet, field",
        [
            ("Nouns", "Translation"),
            ("Pronouns", "Oblique Forms"),
            ("Bogus", "Plural"),
            ("Verbs", "Perfective"),
        ],
    )
    def test_outside_generated_fields_is_none(self, sheet, field):
        entries = {"год": [NOUN_ENTRY]}
        assert ff.generate_value(sheet, field, noun_fields(), entries) is None


def adj_entry(*extra):
    return entry(
        "adj",
        ("нов", ["short-form", "masculine"]),
        ("нова́", ["short-form", "feminine"]),
        ("но́во", ["short-form", "neuter"]),
        ("но́вы", ["short-form", "plural"]),
        ("нове́е", ["comparative"]),
        *extra,
    )


class TestGenerateAdjectivesAdverbs:
    def test_short_form_full(self):
        entries = {"новый": [adj_entry()]}
        assert (
            ff.generate_value("Adjectives", "Short Form", adj_fields(), entries)
            == "нов, нова́, но́во, но́вы"
        )

    def test_short_form_missing_neuter_omitted(self):
        e = entry(
            "adj",
            ("нов", ["short-form", "masculine"]),
            ("нова́", ["short-form", "feminine"]),
            ("но́вы", ["short-form", "plural"]),
        )
        assert (
            ff.generate_value("Adjectives", "Short Form", adj_fields(), {"новый": [e]})
            == "нов, нова́, но́вы"
        )

    def test_short_form_missing_plural_omitted(self):
        e = entry(
            "adj",
            ("нов", ["short-form", "masculine"]),
            ("нова́", ["short-form", "feminine"]),
            ("но́во", ["short-form", "neuter"]),
        )
        assert (
            ff.generate_value("Adjectives", "Short Form", adj_fields(), {"новый": [e]})
            == "нов, нова́, но́во"
        )

    @pytest.mark.parametrize("missing", ["masculine", "feminine"])
    def test_short_form_missing_core_is_none(self, missing):
        forms = {
            "masculine": ("нов", ["short-form", "masculine"]),
            "feminine": ("нова́", ["short-form", "feminine"]),
        }
        del forms[missing]
        e = entry("adj", *forms.values(), ("но́во", ["short-form", "neuter"]))
        assert (
            ff.generate_value("Adjectives", "Short Form", adj_fields(), {"новый": [e]})
            is None
        )

    def test_short_form_plural_must_not_be_gendered(self):
        e = entry(
            "adj",
            ("нов", ["short-form", "masculine"]),
            ("нова́", ["short-form", "feminine"]),
            ("x", ["short-form", "plural", "masculine"]),
            ("но́вы", ["short-form", "plural"]),
        )
        assert (
            ff.generate_value("Adjectives", "Short Form", adj_fields(), {"новый": [e]})
            == "нов, нова́, но́вы"
        )

    def test_short_form_skips_ignored_tag_form(self):
        e = entry(
            "adj",
            ("стар", ["short-form", "masculine", "dated"]),
            ("нов", ["short-form", "masculine"]),
            ("нова́", ["short-form", "feminine"]),
        )
        assert (
            ff.generate_value("Adjectives", "Short Form", adj_fields(), {"новый": [e]})
            == "нов, нова́"
        )

    def test_short_form_monosyllable_destressed(self):
        e = entry(
            "adj",
            ("но́в", ["short-form", "masculine"]),
            ("нова́", ["short-form", "feminine"]),
        )
        assert (
            ff.generate_value("Adjectives", "Short Form", adj_fields(), {"новый": [e]})
            == "нов, нова́"
        )

    def test_adjective_comparative(self):
        assert (
            ff.generate_value(
                "Adjectives", "Comparative", adj_fields(), {"новый": [adj_entry()]}
            )
            == "нове́е"
        )

    def test_adjective_comparative_absent_is_none(self):
        e = entry("adj", ("нов", ["short-form", "masculine"]))
        assert (
            ff.generate_value("Adjectives", "Comparative", adj_fields(), {"новый": [e]})
            is None
        )

    def test_adjective_wrong_pos_is_none(self):
        assert (
            ff.generate_value(
                "Adjectives",
                "Comparative",
                adj_fields(),
                {"новый": [entry("noun", ("нове́е", ["comparative"]))]},
            )
            is None
        )

    def test_adverb_comparative_with_prefix(self):
        e = entry("adv", ("(по)быстре́е", ["comparative"]))
        assert (
            ff.generate_value("Adverbs", "Comparative", adv_fields(), {"быстро": [e]})
            == "быстре́е"
        )

    def test_adverb_comparative_uses_adverb_lemma(self):
        e = entry("adv", ("быстре́е", ["comparative"]))
        assert (
            ff.generate_value(
                "Adverbs",
                "Comparative",
                adv_fields(Adverb="быстро (adverb)"),
                {"быстро": [e]},
            )
            == "быстре́е"
        )

    def test_adverb_wrong_pos_is_none(self):
        e = entry("adj", ("быстре́е", ["comparative"]))
        assert (
            ff.generate_value("Adverbs", "Comparative", adv_fields(), {"быстро": [e]})
            is None
        )

    def test_adverb_comparative_tag_dated_skipped(self):
        e = entry(
            "adv",
            ("старо", ["comparative", "obsolete"]),
            ("быстре́е", ["comparative"]),
        )
        assert (
            ff.generate_value("Adverbs", "Comparative", adv_fields(), {"быстро": [e]})
            == "быстре́е"
        )


def verb_entry(sg1="де́лаю", sg2="де́лаешь", pl3="де́лают", tense="present"):
    return entry(
        "verb",
        (sg1, [tense, "first-person", "singular"]),
        (sg2, [tense, "second-person", "singular"]),
        (pl3, [tense, "third-person", "plural"]),
        ("де́лал", ["past", "masculine", "singular"]),
        ("де́лала", ["past", "feminine", "singular"]),
    )


class TestGenerateVerbs:
    @pytest.mark.parametrize(
        "field, expected",
        [
            ("я (1sg)", "де́лаю"),
            ("ты (2sg)", "де́лаешь"),
            ("они (3pl)", "де́лают"),
            ("Past (m / f)", "де́лал / де́лала"),
            ("Conjugation", "1st (-ешь)"),
        ],
    )
    def test_present_fields(self, field, expected):
        entries = {"делать": [verb_entry()]}
        assert ff.generate_value("Verbs", field, verb_fields(), entries) == expected

    def test_future_used_for_perfective(self):
        entries = {
            "сделать": [verb_entry("сде́лаю", "сде́лаешь", "сде́лают", tense="future")]
        }
        fields = verb_fields(Imperfective="", Perfective="сде́лать")
        assert ff.generate_value("Verbs", "я (1sg)", fields, entries) == "сде́лаю"
        assert ff.generate_value("Verbs", "они (3pl)", fields, entries) == "сде́лают"
        assert (
            ff.generate_value("Verbs", "Conjugation", fields, entries) == "1st (-ешь)"
        )

    def test_present_preferred_over_future(self):
        e = entry(
            "verb",
            ("буду", ["future", "first-person", "singular"]),
            ("пою́", ["present", "first-person", "singular"]),
        )
        assert (
            ff.generate_value("Verbs", "я (1sg)", verb_fields(), {"делать": [e]})
            == "пою́"
        )

    def test_neither_tense_is_none(self):
        e = entry("verb", ("x", ["past", "first-person", "singular"]))
        assert (
            ff.generate_value("Verbs", "я (1sg)", verb_fields(), {"делать": [e]})
            is None
        )

    def test_past_monosyllables_destressed(self):
        e = entry(
            "verb",
            ("мо́г", ["past", "masculine", "singular"]),
            ("могла́", ["past", "feminine", "singular"]),
        )
        assert (
            ff.generate_value("Verbs", "Past (m / f)", verb_fields(), {"делать": [e]})
            == "мог / могла́"
        )

    @pytest.mark.parametrize("drop", ["masculine", "feminine"])
    def test_past_needs_both(self, drop):
        forms = {
            "masculine": ("де́лал", ["past", "masculine", "singular"]),
            "feminine": ("де́лала", ["past", "feminine", "singular"]),
        }
        del forms[drop]
        e = entry("verb", *forms.values())
        assert (
            ff.generate_value("Verbs", "Past (m / f)", verb_fields(), {"делать": [e]})
            is None
        )

    def test_past_requires_singular_past_tags(self):
        e = entry(
            "verb",
            ("де́лали", ["past", "plural"]),
            ("де́лал", ["past", "masculine", "singular"]),
            ("де́лала", ["past", "feminine", "singular"]),
        )
        assert (
            ff.generate_value("Verbs", "Past (m / f)", verb_fields(), {"делать": [e]})
            == "де́лал / де́лала"
        )

    def test_compound_form_rejected(self):
        e = entry("verb", ("бу́дешь де́лать", ["present", "second-person", "singular"]))
        assert (
            ff.generate_value("Verbs", "ты (2sg)", verb_fields(), {"делать": [e]})
            is None
        )

    @pytest.mark.parametrize(
        "sg2, pl3, expected",
        [
            ("де́лаешь", "де́лают", "1st (-ешь)"),
            ("идёшь", "иду́т", "1st (-ешь)"),
            ("говори́шь", "говоря́т", "2nd (-ишь)"),
            ("ви́дишь", "ви́дят", "2nd (-ишь)"),
            ("слы́шишь", "слы́шат", "2nd (-ишь)"),
            ("хо́чешь", "хотя́т", None),
            ("бежи́шь", "бегу́т", None),
            ("дашь", "даду́т", None),
            ("де́лаешь", "говоря́т", None),
            ("говори́шь", "де́лают", None),
        ],
    )
    def test_conjugation_rule(self, sg2, pl3, expected):
        e = entry(
            "verb",
            (sg2, ["present", "second-person", "singular"]),
            (pl3, ["present", "third-person", "plural"]),
        )
        assert (
            ff.generate_value("Verbs", "Conjugation", verb_fields(), {"делать": [e]})
            == expected
        )

    def test_conjugation_reflexive_suffix_removed(self):
        e = entry(
            "verb",
            ("учи́шься", ["present", "second-person", "singular"]),
            ("у́чатся", ["present", "third-person", "plural"]),
        )
        fields = verb_fields(Imperfective="учиться")
        assert (
            ff.generate_value("Verbs", "Conjugation", fields, {"учиться": [e]})
            == "2nd (-ишь)"
        )

    def test_conjugation_missing_form_is_none(self):
        e = entry("verb", ("де́лаешь", ["present", "second-person", "singular"]))
        assert (
            ff.generate_value("Verbs", "Conjugation", verb_fields(), {"делать": [e]})
            is None
        )

    def test_conjugation_future_fallback(self):
        e = verb_entry("сде́лаю", "сде́лаешь", "сде́лают", tense="future")
        fields = verb_fields(Imperfective="", Perfective="сде́лать")
        assert (
            ff.generate_value("Verbs", "Conjugation", fields, {"сделать": [e]})
            == "1st (-ешь)"
        )


class TestOpenRussian:
    HEADER = {
        "nouns.csv": ["bare", "pl_nom", "sg_gen", "pl_gen"],
        "verbs.csv": [
            "bare",
            "presfut_sg1",
            "presfut_sg2",
            "presfut_pl3",
            "past_m",
            "past_f",
        ],
        "adjectives.csv": [
            "bare",
            "comparative",
            "short_m",
            "short_f",
            "short_n",
            "short_pl",
        ],
    }

    def write(self, directory, rows_by_file):
        for name, header in self.HEADER.items():
            lines = ["\t".join(header)]
            for row in rows_by_file.get(name, []):
                lines.append("\t".join(row.get(col, "") for col in header))
            (directory / name).write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_load_keys_and_skip_empty_bare(self, tmp_path):
        self.write(
            tmp_path,
            {
                "nouns.csv": [
                    {"bare": "Го́д", "pl_nom": "го'ды"},
                    {"bare": "", "pl_nom": "zzz"},
                ],
                "verbs.csv": [{"bare": "делать"}],
            },
        )
        index = ff.load_openrussian(tmp_path)
        assert set(index) == {"nouns", "verbs", "adjectives"}
        assert list(index["nouns"]) == ["год"]
        assert index["nouns"]["год"][0]["pl_nom"] == "го'ды"
        assert "делать" in index["verbs"]
        assert index["adjectives"] == {}

    def test_load_duplicate_bare_keeps_rows(self, tmp_path):
        self.write(
            tmp_path,
            {
                "nouns.csv": [
                    {"bare": "год", "pl_nom": "a"},
                    {"bare": "год", "pl_nom": "b"},
                ]
            },
        )
        assert [r["pl_nom"] for r in ff.load_openrussian(tmp_path)["nouns"]["год"]] == [
            "a",
            "b",
        ]

    @pytest.fixture
    def index(self, tmp_path):
        self.write(
            tmp_path,
            {
                "nouns.csv": [
                    {"bare": "год", "pl_nom": "", "sg_gen": "года'", "pl_gen": "ле'т"},
                    {"bare": "год", "pl_nom": "го'ды", "sg_gen": "x", "pl_gen": "y"},
                ],
                "verbs.csv": [
                    {
                        "bare": "делать",
                        "presfut_sg1": "де'лаю",
                        "presfut_sg2": "де'лаешь",
                        "presfut_pl3": "де'лают",
                        "past_m": "де'лал",
                        "past_f": "де'лала",
                    },
                    {
                        "bare": "идти",
                        "presfut_sg2": "идёшь",
                        "presfut_pl3": "иду'т",
                        "past_m": "шёл",
                    },
                ],
                "adjectives.csv": [
                    {
                        "bare": "новый",
                        "comparative": "нове'е",
                        "short_m": "нов",
                        "short_f": "нова'",
                        "short_n": "",
                        "short_pl": "но'вы",
                    }
                ],
            },
        )
        return ff.load_openrussian(tmp_path)

    @pytest.mark.parametrize(
        "field, expected",
        [("Plural", "го́ды"), ("Genitive Sg", "года́"), ("Genitive Pl", "лет")],
    )
    def test_nouns_first_nonempty_row_wins(self, index, field, expected):
        assert ff.openrussian_value("Nouns", field, noun_fields(), index) == expected

    @pytest.mark.parametrize(
        "field, expected",
        [
            ("я (1sg)", "де́лаю"),
            ("ты (2sg)", "де́лаешь"),
            ("они (3pl)", "де́лают"),
            ("Past (m / f)", "де́лал / де́лала"),
            ("Conjugation", "1st (-ешь)"),
        ],
    )
    def test_verbs(self, index, field, expected):
        assert ff.openrussian_value("Verbs", field, verb_fields(), index) == expected

    def test_past_requires_both(self, index):
        fields = verb_fields(Imperfective="идти")
        assert ff.openrussian_value("Verbs", "Past (m / f)", fields, index) is None
        assert ff.openrussian_value("Verbs", "ты (2sg)", fields, index) == "идёшь"

    def test_adjectives(self, index):
        assert (
            ff.openrussian_value("Adjectives", "Comparative", adj_fields(), index)
            == "нове́е"
        )
        assert (
            ff.openrussian_value("Adjectives", "Short Form", adj_fields(), index)
            == "нов, нова́, но́вы"
        )

    def test_adverbs_none(self, index):
        assert (
            ff.openrussian_value("Adverbs", "Comparative", adv_fields(), index) is None
        )

    def test_absent_lemma_none(self, index):
        assert (
            ff.openrussian_value("Nouns", "Plural", noun_fields(Russian="дом"), index)
            is None
        )


class TestCrossCheck:
    @pytest.mark.parametrize(
        "generated, other, expected",
        [
            ("го́ды", None, "no-entry"),
            ("го́ды", "го́ды", "agree"),
            ("го́ды", "годы", "spelling-only"),
            ("Го́ды", "годы", "spelling-only"),
            ("го́ды", "года́", "differs"),
            ("", "", "agree"),
        ],
    )
    def test_cases(self, generated, other, expected):
        assert ff.cross_check(generated, other) == expected

    def test_nfc_equal_agrees(self):
        assert ff.cross_check("ё", "е" + "̈") == "agree"


class TestExclusions:
    HEADER = "Note type\tHeadword\tDestination field\tOther\n"

    def write(self, tmp_path, body):
        path = tmp_path / "case-text-routing.tsv"
        path.write_text(self.HEADER + body, encoding="utf-8")
        return path

    def test_parse(self, tmp_path):
        path = self.write(
            tmp_path,
            "Russian - Mutable Nouns (Ellis Version)\tгод\tPlural\tx\n"
            "Verbs\tделать\t Conjugation \tx\n"
            "Russian - Mutable Nouns (Ellis Version)\tдом\t\tx\n"
            "Russian - Mutable Nouns (Ellis Version)\tдом2\tDelete\tx\n"
            "Russian - Mutable Nouns (Ellis Version)\tдом3\tDELETE\tx\n"
            "Basic\tfoo\tFront\tx\n",
        )
        assert ff.parse_routing_exclusions(path) == frozenset(
            {("Nouns", "год", "Plural"), ("Verbs", "делать", "Conjugation")}
        )

    def test_parse_header_only_empty(self, tmp_path):
        assert ff.parse_routing_exclusions(self.write(tmp_path, "")) == frozenset()

    def test_parse_header_case_and_order(self, tmp_path):
        path = tmp_path / "r.tsv"
        path.write_text(
            "Destination Field (x)\tHEADWORD\tNote Type\nPlural\tгод\tNouns\n",
            encoding="utf-8",
        )
        assert ff.parse_routing_exclusions(path) == frozenset(
            {("Nouns", "год", "Plural")}
        )

    def test_parse_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            ff.parse_routing_exclusions(tmp_path / "nope.tsv")

    def test_plan_exclusions_existing_file(self, tmp_path):
        path = self.write(tmp_path, "Nouns\tгод\tPlural\tx\n")
        excluded, source = ff.plan_exclusions(path)
        assert source == "plan list + case-text-routing.tsv"
        assert ff.EXCLUDED_BY_PLAN <= excluded
        assert ("Nouns", "год", "Plural") in excluded

    @pytest.mark.parametrize("use_none", [True, False])
    def test_plan_exclusions_absent_file(self, tmp_path, use_none):
        path = None if use_none else tmp_path / "case-text-routing.tsv"
        excluded, source = ff.plan_exclusions(path)
        assert source == "plan list (case-text-routing.tsv not yet committed)"
        assert excluded == ff.EXCLUDED_BY_PLAN

    @pytest.mark.parametrize(
        "sheet, headword, field, expected",
        [
            ("Numerals", "один", "Genitive", True),
            ("Nouns", "год", "Plural", True),
            ("Nouns", "дом", "Plural", False),
            ("Nouns", "год", "Genitive Sg", False),
            ("Verbs", "год", "Plural", False),
        ],
    )
    def test_is_excluded(self, sheet, headword, field, expected):
        excluded = frozenset({("Numerals", "Genitive"), ("Nouns", "год", "Plural")})
        assert ff.is_excluded(sheet, headword, field, excluded) is expected


ENTRIES = {
    "год": [NOUN_ENTRY],
    "делать": [verb_entry()],
}


class TestCandidateCells:
    def test_missing_cells_listed(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        cells = ff.candidate_cells(tsv, all_sheets(), frozenset())
        assert [(c.sheet, c.guid, c.field) for c in cells] == [
            ("Nouns", "n1", "Plural"),
            ("Nouns", "n1", "Genitive Sg"),
            ("Nouns", "n1", "Genitive Pl"),
        ]

    def test_full_note_has_no_candidates_control(self):
        tsv = all_sheets(Nouns={"n1": fields_for("Nouns", {"Additional Info": ""})})
        assert ff.candidate_cells(tsv, all_sheets(), frozenset()) == []

    def test_dash_marker_not_candidate(self):
        tsv = all_sheets(Nouns={"n1": noun_fields(Plural="—")})
        fields = {c.field for c in ff.candidate_cells(tsv, all_sheets(), frozenset())}
        assert fields == {"Genitive Sg", "Genitive Pl"}

    def test_not_applicable_not_candidate(self):
        tsv = all_sheets(
            Nouns={"n1": noun_fields(**{"Additional Info": "indeclinable"})}
        )
        assert ff.candidate_cells(tsv, all_sheets(), frozenset()) == []

    def test_excluded_removed_with_control(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        excluded = frozenset({("Nouns", "год", "Plural")})
        fields = [c.field for c in ff.candidate_cells(tsv, all_sheets(), excluded)]
        assert fields == ["Genitive Sg", "Genitive Pl"]

    def test_collection_nonempty_removes_cell_with_control(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        coll = all_sheets(Nouns={"n1": noun_fields(Plural="  го́ды ")})
        fields = [c.field for c in ff.candidate_cells(tsv, coll, frozenset())]
        assert fields == ["Genitive Sg", "Genitive Pl"]

    def test_collection_dash_removes_cell(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        coll = all_sheets(Nouns={"n1": noun_fields(Plural="—")})
        fields = [c.field for c in ff.candidate_cells(tsv, coll, frozenset())]
        assert "Plural" not in fields

    def test_collection_whitespace_is_empty(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        coll = all_sheets(Nouns={"n1": noun_fields(Plural="   ")})
        fields = [c.field for c in ff.candidate_cells(tsv, coll, frozenset())]
        assert "Plural" in fields

    def test_guid_absent_from_collection_counts_empty(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        coll = all_sheets(Nouns={"other": noun_fields(Plural="x")})
        assert len(ff.candidate_cells(tsv, coll, frozenset())) == 3

    def test_sheet_missing_from_collection_dict(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        assert len(ff.candidate_cells(tsv, {}, frozenset())) == 3


class TestBuildRows:
    def rows(
        self, tsv, entries=ENTRIES, coll=None, excluded=frozenset(), openrussian=None
    ):
        return ff.build_rows(
            tsv,
            coll if coll is not None else all_sheets(),
            entries,
            excluded,
            openrussian,
        )

    def test_filled_and_unresolved(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        entries = {"год": [entry("noun", ("го́ды", ["nominative", "plural"]))]}
        rows = self.rows(tsv, entries)
        assert [r.field for r in rows] == ["Plural", "Genitive Sg", "Genitive Pl"]
        plural, gen_sg, gen_pl = rows
        assert plural == ff.FillRow(
            "Nouns",
            "год",
            "n1",
            "Plural",
            "го́ды",
            "kaikki.org Wiktionary extract " + ff.wiktionary_url("год"),
            ff.STATUS_FILLED,
        )
        for row in (gen_sg, gen_pl):
            assert (row.value, row.reference, row.status) == (
                "",
                "",
                ff.STATUS_UNRESOLVED,
            )
            assert (row.note_type, row.headword, row.guid) == ("Nouns", "год", "n1")

    def test_absent_lemma_unresolved(self):
        rows = self.rows(all_sheets(Nouns={"n1": noun_fields(Russian="дом")}))
        assert {r.status for r in rows} == {ff.STATUS_UNRESOLVED}
        assert {(r.value, r.reference) for r in rows} == {("", "")}

    def test_non_generated_field_unresolved(self):
        tsv = all_sheets(Verbs={"v1": verb_fields(**EMPTY_GENERATED_VERB)})
        rows = self.rows(tsv)
        by_field = {r.field: r for r in rows}
        assert by_field["Perfective"].status == ff.STATUS_UNRESOLVED
        assert (by_field["Perfective"].value, by_field["Perfective"].reference) == (
            "",
            "",
        )
        assert by_field["Conjugation"].status == ff.STATUS_FILLED
        assert by_field["Perfective"].note_type == "Verbs"

    def test_reference_uses_normalized_lemma(self):
        tsv = all_sheets(Verbs={"v1": verb_fields(**EMPTY_GENERATED_VERB)})
        row = next(r for r in self.rows(tsv) if r.field == "ты (2sg)")
        assert row.reference.endswith(ff.wiktionary_url("делать"))

    def test_census_order_across_sheets(self):
        tsv = all_sheets(
            Verbs={"v1": verb_fields(Perfective="сделать")},
            Nouns={"n1": noun_fields(Plural="x", **{"Genitive Sg": "y"})},
        )
        rows = self.rows(tsv)
        assert [(r.note_type, r.field) for r in rows] == [("Nouns", "Genitive Pl")]

    def test_excluded_cell_has_no_row(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        excluded = frozenset({("Nouns", "год", "Plural")})
        assert "Plural" not in [r.field for r in self.rows(tsv, excluded=excluded)]

    def test_collection_filled_cell_has_no_row(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        coll = all_sheets(Nouns={"n1": noun_fields(Plural="x")})
        assert "Plural" not in [r.field for r in self.rows(tsv, coll=coll)]

    @pytest.mark.parametrize(
        "other, suffix",
        [
            ("го́ды", "; OpenRussian: agree"),
            ("годы", "; OpenRussian: spelling-only"),
            ("года́", "; OpenRussian: differs (года́)"),
        ],
    )
    def test_openrussian_annotation(self, other, suffix):
        index = {
            "nouns": {"год": [{"pl_nom": other.replace(ACUTE, "'")}]},
            "verbs": {},
            "adjectives": {},
        }
        tsv = all_sheets(
            Nouns={"n1": noun_fields(**{"Genitive Sg": "x", "Genitive Pl": "y"})}
        )
        row = self.rows(tsv, openrussian=index)[0]
        base = "kaikki.org Wiktionary extract " + ff.wiktionary_url("год")
        assert row.reference == base + suffix

    def test_openrussian_no_entry(self):
        index = {"nouns": {}, "verbs": {}, "adjectives": {}}
        tsv = all_sheets(
            Nouns={"n1": noun_fields(**{"Genitive Sg": "x", "Genitive Pl": "y"})}
        )
        row = self.rows(tsv, openrussian=index)[0]
        assert row.reference.endswith("; OpenRussian: no-entry")

    def test_no_openrussian_no_annotation_control(self):
        tsv = all_sheets(
            Nouns={"n1": noun_fields(**{"Genitive Sg": "x", "Genitive Pl": "y"})}
        )
        assert "OpenRussian" not in self.rows(tsv)[0].reference

    def test_unresolved_has_no_openrussian_note(self):
        index = {"nouns": {}, "verbs": {}, "adjectives": {}}
        tsv = all_sheets(Nouns={"n1": noun_fields(Russian="дом")})
        assert {r.reference for r in self.rows(tsv, openrussian=index)} == {""}


def row(**overrides):
    base = dict(
        note_type="Nouns",
        headword="год",
        guid="n1",
        field="Plural",
        value="го́ды",
        reference="ref",
        status=ff.STATUS_FILLED,
    )
    base.update(overrides)
    return ff.FillRow(**base)


class TestValidators:
    def test_overlap_rejected_by_field(self):
        excluded = frozenset({("Nouns", "Plural")})
        with pytest.raises(ff.OverlapError, match="Plural"):
            ff.assert_no_overlap([row()], excluded)

    def test_overlap_rejected_by_headword_triple(self):
        excluded = frozenset({("Nouns", "год", "Plural")})
        with pytest.raises(ff.OverlapError, match="год"):
            ff.assert_no_overlap([row()], excluded)

    def test_overlap_unrelated_cell_passes(self):
        excluded = frozenset({("Nouns", "год", "Plural"), ("Numerals", "Genitive")})
        ff.assert_no_overlap([row(field="Genitive Sg"), row(headword="дом")], excluded)

    def test_overlap_first_offender_raises_among_clean(self):
        excluded = frozenset({("Nouns", "дом", "Plural")})
        with pytest.raises(ff.OverlapError):
            ff.assert_no_overlap([row(), row(headword="дом")], excluded)

    def test_targets_empty_passes(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        coll = all_sheets(Nouns={"n1": noun_fields()})
        ff.assert_targets_empty([row()], tsv, coll)

    @pytest.mark.parametrize("value", ["x", "—", "-", " y "])
    def test_target_nonempty_in_tsv_rejected(self, value):
        tsv = all_sheets(Nouns={"n1": noun_fields(Plural=value)})
        with pytest.raises(ff.NonEmptyTargetError, match="Plural"):
            ff.assert_targets_empty(
                [row()], tsv, all_sheets(Nouns={"n1": noun_fields()})
            )

    @pytest.mark.parametrize("value", ["x", "—", "-"])
    def test_target_nonempty_in_collection_rejected(self, value):
        coll = all_sheets(Nouns={"n1": noun_fields(Plural=value)})
        with pytest.raises(ff.NonEmptyTargetError, match="Plural"):
            ff.assert_targets_empty(
                [row()], all_sheets(Nouns={"n1": noun_fields()}), coll
            )

    def test_target_whitespace_only_passes(self):
        tsv = all_sheets(Nouns={"n1": noun_fields(Plural="  ")})
        ff.assert_targets_empty([row()], tsv, all_sheets())

    def test_target_guid_absent_from_collection_passes(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        ff.assert_targets_empty([row()], tsv, all_sheets())

    def test_other_field_nonempty_does_not_block(self):
        tsv = all_sheets(Nouns={"n1": noun_fields(**{"Genitive Sg": "x"})})
        ff.assert_targets_empty([row()], tsv, all_sheets())

    def test_build_rows_runs_validators_on_clean_input(self):
        tsv = all_sheets(Nouns={"n1": noun_fields()})
        assert len(ff.build_rows(tsv, all_sheets(), ENTRIES, frozenset())) == 3


class TestOracle:
    def tsv(self, **overrides):
        return all_sheets(
            Nouns={
                "n1": fields_for(
                    "Nouns",
                    {
                        "Russian": "год",
                        "Plural": "го́ды",
                        "Genitive Sg": "года́",
                        "Genitive Pl": "лет",
                        **overrides,
                    },
                )
            }
        )

    def test_every_key_present(self):
        result = ff.check_oracle(all_sheets(), {})
        expected = {(s, f) for s, fs in ff.GENERATED_FIELDS.items() for f in fs}
        assert set(result) == expected
        for res in result.values():
            assert (
                res.exact,
                res.spelling_only,
                res.differs,
                res.no_output,
                res.no_entry,
            ) == (0, 0, 0, 0, 0)
            assert res.disagreements == ()

    def test_exact(self):
        res = ff.check_oracle(self.tsv(), ENTRIES)[("Nouns", "Plural")]
        assert (res.exact, res.differs, res.no_entry) == (1, 0, 0)

    def test_exact_all_three(self):
        result = ff.check_oracle(self.tsv(), ENTRIES)
        assert all(
            result[("Nouns", f)].exact == 1 for f in ff.GENERATED_FIELDS["Nouns"]
        )

    def test_spelling_only(self):
        res = ff.check_oracle(self.tsv(Plural="Годы"), ENTRIES)[("Nouns", "Plural")]
        assert (res.spelling_only, res.exact, res.differs) == (1, 0, 0)

    def test_differs_with_disagreement(self):
        res = ff.check_oracle(self.tsv(Plural="лета́"), ENTRIES)[("Nouns", "Plural")]
        assert res.differs == 1
        assert res.disagreements == (("год", "Plural", "лета́", "го́ды"),)

    def test_no_entry_absent_lemma(self):
        res = ff.check_oracle(self.tsv(), {})[("Nouns", "Plural")]
        assert res.no_entry == 1

    def test_no_entry_wrong_pos(self):
        entries = {"год": [entry("verb", ("го́ды", ["nominative", "plural"]))]}
        res = ff.check_oracle(self.tsv(), entries)[("Nouns", "Plural")]
        assert (res.no_entry, res.no_output) == (1, 0)

    def test_no_output(self):
        entries = {"год": [entry("noun", ("го́д", ["nominative", "singular"]))]}
        res = ff.check_oracle(self.tsv(), entries)[("Nouns", "Plural")]
        assert (res.no_output, res.no_entry) == (1, 0)

    @pytest.mark.parametrize("marker", sorted(fc.EMPTY_MARKERS))
    def test_empty_house_values_not_counted(self, marker):
        res = ff.check_oracle(self.tsv(Plural=marker), ENTRIES)[("Nouns", "Plural")]
        assert (
            res.exact,
            res.spelling_only,
            res.differs,
            res.no_output,
            res.no_entry,
        ) == (0, 0, 0, 0, 0)

    def test_other_sheet_counts_independent(self):
        tsv = all_sheets(
            Verbs={
                "v1": verb_fields(**{"Conjugation": "1st (-ешь)", "я (1sg)": "де́лаю"})
            }
        )
        result = ff.check_oracle(tsv, ENTRIES)
        assert result[("Verbs", "Conjugation")].exact == 1
        assert result[("Verbs", "я (1sg)")].exact == 1
        assert result[("Nouns", "Plural")].exact == 0


class TestArtifact:
    ROWS = [
        row(),
        row(field="Genitive Sg", value="", reference="", status=ff.STATUS_UNRESOLVED),
        row(
            note_type="Verbs",
            headword="мочь",
            guid="v1",
            field="Past (m / f)",
            value="мог / могла́",
        ),
    ]

    def test_render_layout(self):
        text = ff.render_artifact(self.ROWS, ["Source: x", "", "Coverage: y"])
        lines = text.split("\n")
        assert lines[:3] == ["# Source: x", "#", "# Coverage: y"]
        assert lines[3] == "\t".join(ff.COLUMNS)
        assert lines[4] == "\t".join(
            ["Nouns", "год", "n1", "Plural", "го́ды", "ref", ff.STATUS_FILLED]
        )
        assert text.endswith("\n") and not text.endswith("\n\n")
        assert len(lines) == 3 + 1 + len(self.ROWS) + 1

    def test_render_no_header_lines(self):
        text = ff.render_artifact([], [])
        assert text == "\t".join(ff.COLUMNS) + "\n"

    def test_round_trip(self):
        text = ff.render_artifact(self.ROWS, ["a", "", "b"])
        assert ff.parse_artifact(text) == self.ROWS

    def test_round_trip_empty(self):
        assert ff.parse_artifact(ff.render_artifact([], ["only header"])) == []

    @pytest.mark.parametrize("bad", ["a\tb", "a\nb"])
    @pytest.mark.parametrize("column", ["headword", "value", "reference"])
    def test_render_rejects_tab_newline(self, bad, column):
        with pytest.raises(ValueError):
            ff.render_artifact([row(**{column: bad})], [])

    def test_render_clean_row_control(self):
        assert ff.render_artifact([row(value="clean value")], [])

    def test_parse_skips_comments_and_blank_lines(self):
        header = "\t".join(ff.COLUMNS)
        body = "Nouns\tгод\tn1\tPlural\tго́ды\tref\tmissing-filled"
        text = f"# c\n\n{header}\n\n# mid\n{body}\n\n"
        assert ff.parse_artifact(text) == [row()]

    def test_parse_requires_header(self):
        with pytest.raises(ValueError):
            ff.parse_artifact("Nouns\tгод\tn1\tPlural\tго́ды\tref\tmissing-filled\n")

    def test_parse_wrong_header(self):
        with pytest.raises(ValueError):
            ff.parse_artifact("a\tb\tc\td\te\tf\tg\n")

    @pytest.mark.parametrize("cells", [6, 8])
    def test_parse_wrong_column_count(self, cells):
        header = "\t".join(ff.COLUMNS)
        body = "\t".join(["x"] * cells)
        with pytest.raises(ValueError):
            ff.parse_artifact(f"{header}\n{body}\n")

    def test_parse_accepts_not_applicable(self):
        header = "\t".join(ff.COLUMNS)
        text = f"{header}\nNouns\tгод\tn1\tPlural\t\t\tnot-applicable\n"
        assert ff.parse_artifact(text)[0].status == ff.STATUS_NOT_APPLICABLE

    def test_parse_preserves_empty_trailing_columns(self):
        header = "\t".join(ff.COLUMNS)
        text = f"{header}\nNouns\tгод\tn1\tPlural\t\t\tunresolved\n"
        parsed = ff.parse_artifact(text)[0]
        assert (parsed.value, parsed.reference) == ("", "")


class TestExtractEntries:
    def write(self, tmp_path, records):
        path = tmp_path / "kaikki.jsonl"
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
            encoding="utf-8",
        )
        return path

    def test_filters_and_cleans(self, tmp_path):
        path = self.write(
            tmp_path,
            [
                {
                    "word": "год",
                    "pos": "noun",
                    "forms": [
                        {"form": "го́ды", "tags": ["nominative", "plural"]},
                        {"form": "year", "tags": ["table-tags"]},
                        {"form": "ru-noun-table", "tags": ["inflection-template"]},
                        {"form": "2a", "tags": ["class"]},
                        {"form": "god", "tags": ["romanization"]},
                        {"form": "ле́т", "tags": ["genitive", "plural", "extra"]},
                    ],
                },
                {
                    "word": "дом",
                    "pos": "noun",
                    "forms": [{"form": "дома́", "tags": ["nominative", "plural"]}],
                },
                {
                    "word": "год",
                    "pos": "name",
                    "forms": [{"form": "x", "tags": ["plural"]}],
                },
                {
                    "word": "год",
                    "pos": "verb",
                    "forms": [{"form": "y", "tags": ["present"]}],
                },
            ],
        )
        result = ff.extract_entries(path, {"год"})
        assert set(result) == {"год"}
        assert result["год"] == [
            {
                "pos": "noun",
                "forms": [
                    ["го́ды", ["nominative", "plural"]],
                    ["ле́т", ["genitive", "plural", "extra"]],
                ],
            },
            {"pos": "verb", "forms": [["y", ["present"]]]},
        ]

    @pytest.mark.parametrize("pos", ["noun", "verb", "adj", "adv"])
    def test_kept_pos(self, tmp_path, pos):
        path = self.write(tmp_path, [{"word": "х", "pos": pos, "forms": []}])
        assert ff.extract_entries(path, {"х"}) == {"х": [{"pos": pos, "forms": []}]}

    @pytest.mark.parametrize("pos", ["name", "prep", "pron", "num"])
    def test_dropped_pos(self, tmp_path, pos):
        path = self.write(tmp_path, [{"word": "х", "pos": pos, "forms": []}])
        assert ff.extract_entries(path, {"х"}) == {}

    def test_word_normalized_for_matching(self, tmp_path):
        path = self.write(tmp_path, [{"word": "Го́д", "pos": "noun", "forms": []}])
        assert set(ff.extract_entries(path, {"год"})) == {"год"}

    def test_file_order_kept(self, tmp_path):
        path = self.write(
            tmp_path,
            [
                {"word": "год", "pos": "noun", "forms": [{"form": "a", "tags": []}]},
                {"word": "год", "pos": "noun", "forms": [{"form": "b", "tags": []}]},
            ],
        )
        forms = [e["forms"][0][0] for e in ff.extract_entries(path, {"год"})["год"]]
        assert forms == ["a", "b"]

    def test_missing_forms_key_tolerated_or_empty(self, tmp_path):
        path = self.write(
            tmp_path,
            [
                {
                    "word": "год",
                    "pos": "noun",
                    "forms": [{"form": "a", "tags": ["table-tags"]}],
                }
            ],
        )
        assert ff.extract_entries(path, {"год"}) == {
            "год": [{"pos": "noun", "forms": []}]
        }

    def test_empty_lemmas(self, tmp_path):
        path = self.write(tmp_path, [{"word": "год", "pos": "noun", "forms": []}])
        assert ff.extract_entries(path, set()) == {}


REAL_DATA_DIR = Path(ff.__file__).resolve().parent / "data" / "russian-vocabulary"
KAIKKI_ENV = "FORM_FILL_KAIKKI_JSONL"
PINNED_ORACLE = {
    ("Nouns", "Plural"): (490, 1, 6, 0, 0),
    ("Nouns", "Genitive Sg"): (9, 0, 0, 0, 0),
    ("Nouns", "Genitive Pl"): (5, 2, 1, 0, 0),
    ("Verbs", "Conjugation"): (36, 0, 14, 4, 0),
    ("Verbs", "я (1sg)"): (50, 0, 2, 0, 0),
    ("Verbs", "ты (2sg)"): (50, 0, 2, 0, 0),
    ("Verbs", "они (3pl)"): (50, 0, 2, 0, 0),
    ("Verbs", "Past (m / f)"): (32, 0, 5, 0, 0),
    ("Adjectives", "Short Form"): (8, 2, 3, 1, 0),
    ("Adjectives", "Comparative"): (3, 2, 0, 2, 0),
    ("Adverbs", "Comparative"): (60, 1, 0, 26, 7),
}


class TestRealArtifact:
    @pytest.fixture(scope="class")
    def tsv_notes(self):
        return fc.tsv_census_notes(REAL_DATA_DIR)

    @pytest.fixture(scope="class")
    def rows(self):
        return ff.parse_artifact(
            (REAL_DATA_DIR / "form-fill.tsv").read_text(encoding="utf-8")
        )

    def test_status_counts(self, rows):
        counts = {
            s: sum(r.status == s for r in rows)
            for s in (ff.STATUS_FILLED, ff.STATUS_UNRESOLVED)
        }
        assert counts == {ff.STATUS_FILLED: 2267, ff.STATUS_UNRESOLVED: 88}
        assert len(rows) == 2355

    def test_unresolved_rows_target_missing_cells_and_filled_rows_are_written(
        self, rows, tsv_notes
    ):
        missing = {
            (c.sheet, c.guid, c.field)
            for c in fc.census_cells(tsv_notes)
            if c.status == fc.MISSING
        }
        unresolved = {
            (r.note_type, r.guid, r.field)
            for r in rows
            if r.status == ff.STATUS_UNRESOLVED
        }
        assert unresolved == missing
        ff.assert_targets_empty(
            [r for r in rows if r.status == ff.STATUS_UNRESOLVED], tsv_notes, {}
        )
        filled = [r for r in rows if r.status == ff.STATUS_FILLED]
        assert all(tsv_notes[r.note_type][r.guid][r.field] == r.value for r in filled)

    def test_no_row_targets_an_excluded_cell(self, rows):
        excluded, _ = ff.plan_exclusions(None)
        ff.assert_no_overlap(rows, excluded)
        assert not [r for r in rows if r.field in {f for _, f in ff.EXCLUDED_BY_PLAN}]

    def test_seeded_overlap_and_non_empty_target_are_rejected(self, rows, tsv_notes):
        sample = rows[0]
        with pytest.raises(ff.OverlapError):
            ff.assert_no_overlap(
                [sample], frozenset({(sample.note_type, sample.field)})
            )
        filled = {sample.note_type: {sample.guid: {sample.field: "x"}}}
        with pytest.raises(ff.NonEmptyTargetError):
            ff.assert_targets_empty([sample], filled, {})

    def test_values_are_clean_and_stressed_like_the_house_format(self, rows):
        filled = [r for r in rows if r.status == ff.STATUS_FILLED]
        assert not [
            r for r in filled if set(r.value) & set("*^()") and r.field != "Conjugation"
        ]
        assert not [
            r for r in filled if "ё" + ACUTE in unicodedata.normalize("NFC", r.value)
        ]
        assert not [r for r in filled if r.value != ff.house_stress(r.value)]
        assert sum(ACUTE in r.value for r in filled) > 1500

    def test_unresolved_rows_are_left_for_hand_citing(self, rows):
        unresolved = [r for r in rows if r.status == ff.STATUS_UNRESOLVED]
        assert {(r.value, r.reference) for r in unresolved} == {("", "")}
        assert all(
            r.reference.startswith(
                "kaikki.org Wiktionary extract https://en.wiktionary.org/wiki/"
            )
            for r in rows
            if r.status == ff.STATUS_FILLED
        )

    @pytest.mark.skipif(KAIKKI_ENV not in os.environ, reason="needs the kaikki dump")
    def test_oracle_against_the_dump_is_pinned(self, tsv_notes):
        committed = ff.parse_artifact(
            (REAL_DATA_DIR / "form-fill.tsv").read_text(encoding="utf-8")
        )
        tsv_notes = copy.deepcopy(tsv_notes)
        for r in committed:
            if r.status == ff.STATUS_FILLED:
                tsv_notes[r.note_type][r.guid][r.field] = ""
        lemmas = {ff.lemma_for(s, f) for s, n in tsv_notes.items() for f in n.values()}
        entries = ff.extract_entries(os.environ[KAIKKI_ENV], lemmas)
        result = ff.check_oracle(tsv_notes, entries)
        got = {
            k: (r.exact, r.spelling_only, r.differs, r.no_output, r.no_entry)
            for k, r in result.items()
        }
        assert got == PINNED_ORACLE
        assert all(len(r.disagreements) == r.differs for r in result.values())
        rebuilt = ff.build_rows(tsv_notes, {}, entries, ff.plan_exclusions(None)[0])
        assert [(r.guid, r.field, r.value, r.status) for r in rebuilt] == [
            (r.guid, r.field, r.value, r.status) for r in committed
        ]
