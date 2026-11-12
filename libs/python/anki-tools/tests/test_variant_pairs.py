from pathlib import Path

from anki_tools import immutable_words_plan, variant_pairs

SOURCE = Path(__file__).parent / "data" / "source-word-list.md"


def test_the_four_pairs():
    pairs = variant_pairs.load_pairs()
    assert [(p.deck_leaf, p.headword) for p in pairs] == [
        ("Particles", "пусть / пускай"),
        ("Conjunctions", "пусть / пускай"),
        ("Conjunctions", "чтобы / чтоб"),
        ("Particles", "мол / дескать"),
    ]


def test_guids_are_unique():
    guids = [p.guid for p in variant_pairs.load_pairs()]
    assert len(set(guids)) == len(guids) == 4


def test_fields_follow_field_names():
    for pair in variant_pairs.load_pairs():
        fields = dict(zip(variant_pairs.FIELD_NAMES, pair.fields(), strict=True))
        assert fields["Russian"] == pair.russian
        assert fields["Variant"] == pair.variant
        assert fields["Part of Speech"] in {"particle", "conjunction"}


def test_audio_reuses_existing_files():
    by_key = {(p.deck_leaf, p.russian): p for p in variant_pairs.load_pairs()}
    fields = dict(
        zip(variant_pairs.FIELD_NAMES, by_key[("Particles", "пусть")].fields())
    )
    assert 'src="пусть-пускай_f1.mp3"' in fields["Audio"]
    assert 'src="пускай_f1.mp3"' in fields["Variant Audio"]
    fields = dict(
        zip(variant_pairs.FIELD_NAMES, by_key[("Conjunctions", "чтобы")].fields())
    )
    assert 'src="чтобы-чтоб_m2.mp3"' in fields["Audio"]
    assert 'src="чтоб_m2.mp3"' in fields["Variant Audio"]


def test_pair_words_left_the_immutable_list():
    words = {
        row.russian
        for row in immutable_words_plan.parse_word_list(
            SOURCE.read_text(encoding="utf-8")
        )
    }
    for gone in ("пусть / пускай", "пускай", "чтобы / чтоб", "мол", "дескать"):
        assert gone not in words


def test_english_card_lists_each_word_on_its_own_line():
    _, back = variant_pairs.TEMPLATES["English"]
    assert back.count('class="pair-line ') == 2
    assert '{{Russian}}</span> <span class="pair-label">(default)' in back
    assert '{{Variant}}</span> <span class="pair-label">({{Register}})' in back
    assert "pair-default-slot-player" in back


def test_templates_reference_only_real_fields():
    import re

    names = set(variant_pairs.FIELD_NAMES) | {"FrontSide", "Deck"}
    for front, back in variant_pairs.TEMPLATES.values():
        for ref in re.findall(r"\{\{[#/]?(?:text:|hint:)?([^}]+)\}\}", front + back):
            assert ref in names, ref


def test_play_button_comes_before_the_word():
    _, back = variant_pairs.TEMPLATES["English"]
    for slug, field in (("default", "Russian"), ("variant", "Variant")):
        assert back.index(f'id="pair-{slug}-slot"') < back.index(
            f"{{{{{field}}}}}</span>"
        )


def test_russian_backs_show_only_the_other_word_under_a_heading():
    for name, shown, other in (
        ("Russian", "{{Russian}}", "{{Variant}}"),
        ("Variant", "{{Variant}}", "{{Russian}}"),
    ):
        back = variant_pairs.TEMPLATES[name][1]
        assert "Alternative Russian:" in back
        assert back.count('class="pair-line ') == 1
        assert f"{other}</span>" in back
        assert f'class="pair-word">{shown}' not in back
        assert "display: none" not in back
    assert "Alternative Russian:" not in variant_pairs.TEMPLATES["English"][1]
