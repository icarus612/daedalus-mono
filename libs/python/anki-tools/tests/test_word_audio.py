import os

import pytest

from anki_tools import word_audio
from anki_tools.audio_naming import build_filename

EXPECTED_SLOTS = {
    ("single", "female"): ("f1",),
    ("single", "male"): ("m2",),
    ("single", "both"): ("f1", "m2"),
    ("double", "female"): ("f1", "f2"),
    ("double", "male"): ("m1", "m2"),
    ("double", "both"): ("f1", "f2", "m1", "m2"),
}


@pytest.mark.parametrize("key,expected", sorted(EXPECTED_SLOTS.items()))
def test_slots_for_matrix(key, expected):
    mode, gender = key
    assert word_audio.slots_for(mode, gender) == expected


def test_slots_for_rejects_unknown():
    with pytest.raises(ValueError):
        word_audio.slots_for("triple", "both")
    with pytest.raises(ValueError):
        word_audio.slots_for("single", "neuter")


def test_single_mode_matches_mutable_deck_slots():
    from anki_tools.mutable_words_plan import VOICE_SLOTS

    assert word_audio.slots_for("single", "both") == VOICE_SLOTS


def test_double_mode_matches_immutable_deck_slots():
    from anki_tools.audio_naming import SLOTS

    assert sorted(word_audio.slots_for("double", "both")) == sorted(SLOTS)


def test_select_voices_rejects_unknown_slot():
    with pytest.raises(ValueError):
        word_audio.select_voices(["f1", "zz"])


def _touch(media_dir, word, slot):
    path = build_filename(word, slot, dir_name=media_dir)
    os.makedirs(os.path.dirname(path) or media_dir, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(b"old")
    return path


def test_plan_skips_present_pairs(tmp_path):
    media = str(tmp_path)
    _touch(media, "слово", "f1")
    plan = word_audio.plan_requests(["слово"], ("f1", "m2"), media)
    assert plan.present == (("слово", "f1"),)
    assert plan.pending == (("слово", "m2"),)


def test_plan_replace_includes_present_pairs(tmp_path):
    media = str(tmp_path)
    _touch(media, "слово", "f1")
    plan = word_audio.plan_requests(["слово"], ("f1", "m2"), media, replace=True)
    assert plan.present == ()
    assert set(plan.pending) == {("слово", "f1"), ("слово", "m2")}


def test_plan_deduplicates_words(tmp_path):
    plan = word_audio.plan_requests(["дом", "дом"], ("f1",), str(tmp_path))
    assert plan.requested == (("дом", "f1"),)


def test_archive_existing_moves_the_file(tmp_path):
    media = tmp_path / "media"
    media.mkdir()
    archive = tmp_path / "archive"
    source = _touch(str(media), "слово", "f1")

    moved = word_audio.archive_existing([("слово", "f1")], str(media), str(archive))

    assert not os.path.exists(source)
    assert len(moved) == 1
    assert os.path.isfile(moved[0])
    assert open(moved[0], "rb").read() == b"old"


def test_archive_existing_ignores_absent_files(tmp_path):
    archive = tmp_path / "archive"
    assert word_audio.archive_existing([("нет", "f1")], str(tmp_path), str(archive)) == []


def test_generate_requests_replace_and_correct_voices(tmp_path, monkeypatch):
    calls = []

    def fake_batch(words, **kwargs):
        calls.append((list(words), kwargs))
        return []

    monkeypatch.setattr(word_audio, "build_and_save_batch", fake_batch)
    word_audio.generate(
        [("слово", "f1"), ("слово", "m2"), ("дом", "f1")],
        media_dir=str(tmp_path / "media"),
        output_dir=str(tmp_path / "out"),
        budget=word_audio.RequestBudget(3),
        session=object(),
        api_key="k",
    )

    assert [words for words, _ in calls] == [["слово"], ["дом"]]
    for _words, kwargs in calls:
        assert kwargs["replace"] is True
        assert kwargs["anki_media_dir"] == str(tmp_path / "media")
    assert [v.slot for v in calls[0][1]["voices"]] == ["f1", "m2"]
    assert [v.slot for v in calls[1][1]["voices"]] == ["f1"]


def test_dry_run_spends_nothing(tmp_path, monkeypatch, capsys):
    def explode(*args, **kwargs):
        raise AssertionError("dry run must not generate")

    monkeypatch.setattr(word_audio, "build_and_save_batch", explode)
    monkeypatch.setattr(word_audio, "get_api_key", explode)

    code = word_audio.main(
        [
            "слово",
            "--mode",
            "double",
            "--anki-media-dir",
            str(tmp_path),
            "--dry-run",
        ]
    )

    assert code == 0
    assert "pending 4" in capsys.readouterr().out


def test_nothing_to_do_when_all_present(tmp_path, monkeypatch, capsys):
    def explode(*args, **kwargs):
        raise AssertionError("must not generate")

    monkeypatch.setattr(word_audio, "build_and_save_batch", explode)
    _touch(str(tmp_path), "слово", "f1")
    _touch(str(tmp_path), "слово", "m2")

    code = word_audio.main(["слово", "--anki-media-dir", str(tmp_path), "--yes"])

    assert code == 0
    assert "Nothing to do." in capsys.readouterr().out
