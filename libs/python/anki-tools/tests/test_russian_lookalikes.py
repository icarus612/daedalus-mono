import unicodedata
from collections import defaultdict
from pathlib import Path

from anki_tools import immutable_words_plan, mutable_words_plan, variant_pairs
from anki_tools.distinction import RUSSIAN_FIELD

VOCAB = Path(mutable_words_plan.__file__).parent / "data" / "russian-vocabulary"
SOURCE = Path(__file__).parent / "data" / "source-word-list.md"
MUTABLE = {
    "Nouns": (mutable_words_plan.parse_nouns, "nouns.tsv", ("Russian",)),
    "Verbs": (
        mutable_words_plan.parse_verbs,
        "verbs.tsv",
        ("Imperfective", "Perfective"),
    ),
    "Adjectives": (
        mutable_words_plan.parse_adjectives,
        "adjectives.tsv",
        ("Russian (m)",),
    ),
    "Adverbs": (mutable_words_plan.parse_adverbs, "adverbs.tsv", ("Adverb",)),
    "Pronouns": (mutable_words_plan.parse_pronouns, "pronouns.tsv", ("Russian",)),
    "Numerals": (mutable_words_plan.parse_numerals, "numerals.tsv", ("Russian",)),
}


def _bare(text: str) -> str:
    text = unicodedata.normalize("NFD", text).replace("́", "")
    return unicodedata.normalize("NFC", text).strip().lower()


def _shown_spellings() -> dict[str, dict[str, str]]:
    """spelling -> {note key: Russian Distinction} for every word a card shows."""
    seen: dict[str, dict[str, str]] = defaultdict(dict)
    immutable_fields = immutable_words_plan.FIELD_NAMES
    for row in immutable_words_plan.parse_word_list(SOURCE.read_text("utf-8")):
        values = dict(zip(immutable_fields, row.fields(), strict=True))
        seen[_bare(values["Russian"])][row.guid] = values[RUSSIAN_FIELD]
    for pair in variant_pairs.load_pairs():
        key = f"pair:{pair.deck_leaf}:{pair.russian}"
        for word in (pair.russian, pair.variant):
            seen[_bare(word)][key] = pair.russian_distinction
    for sheet, (parse, name, prompts) in MUTABLE.items():
        names = mutable_words_plan.FIELD_NAMES[sheet]
        for row in parse(str(VOCAB / name)):
            values = dict(zip(names, row.fields(), strict=True))
            words = [values[f] for f in prompts if values[f].strip() not in ("", "—")]
            if sheet == "Pronouns":
                words += [form.text for form in row.forms()]
            for word in words:
                seen[_bare(word)][row.guid] = values[RUSSIAN_FIELD]
    return seen


def test_shared_russian_spellings_carry_distinct_labels() -> None:
    bad = []
    for word, notes in _shown_spellings().items():
        if len(notes) < 2:
            continue
        labels = list(notes.values())
        unlabelled = labels.count("")
        named = [label for label in labels if label]
        if unlabelled > 1 or len(set(named)) != len(named):
            bad.append((word, sorted(labels)))
    assert not bad, bad


def test_the_check_sees_pronoun_forms_and_pair_variants() -> None:
    seen = _shown_spellings()
    assert len(seen["во"]) == 2
    assert len(seen["самого"]) == 2
    assert len(seen["ним"]) == 3
