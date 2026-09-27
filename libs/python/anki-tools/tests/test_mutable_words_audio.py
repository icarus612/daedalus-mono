"""Contract tests for ``anki_tools.mutable_words_audio``, written from the
packet contract text alone. The implementation module is never read by
this file's author.
"""

import os
from pathlib import Path

import pytest
import requests

from anki_tools import elevenlabs_tts
from anki_tools.audio_naming import build_filename, spoken_text_for
from anki_tools.elevenlabs_tts import (
    API_KEY_ENV_VAR,
    VOICES,
    BudgetExceededError,
    RequestBudget,
)
from anki_tools.mutable_words_audio import (
    SHEETS,
    AudioWorkPlan,
    generate,
    load_base_words,
    main,
    pending_pairs,
    plan_requests,
    select_voices,
)
from anki_tools.mutable_words_plan import VOICE_SLOTS

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "anki_tools" / "data" / "russian-vocabulary"

DUMMY_API_KEY = "dummy-not-real"


@pytest.fixture(autouse=True)
def block_real_network(monkeypatch):
    def _boom(*_args, **_kwargs):
        raise AssertionError(
            "a test attempted a REAL HTTP request -- every test must inject "
            "its own fake session instead."
        )

    monkeypatch.setattr(requests, "post", _boom)
    monkeypatch.setattr(requests.Session, "post", _boom)


def test_network_guard_actually_blocks_real_requests():
    with pytest.raises(AssertionError, match="REAL HTTP request"):
        requests.post("https://api.elevenlabs.io/v1/voices")
    with pytest.raises(AssertionError, match="REAL HTTP request"):
        requests.Session().post("https://api.elevenlabs.io/v1/voices")


class FakeResponse:
    def __init__(self, status_code=200, content=b"", headers=None, text=""):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.text = text or ""


def _mock_session(responses):
    from unittest.mock import MagicMock

    session = MagicMock()
    session.post = MagicMock(side_effect=list(responses))
    return session


def _patch_session(monkeypatch, responses):
    session = _mock_session(responses)
    monkeypatch.setattr(
        "anki_tools.mutable_words_audio.requests.Session", lambda: session
    )
    return session


NOUN_TSV_HEADER = "\t".join(
    [
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
    ]
)


def _write_nouns_tsv(path, words):
    lines = [NOUN_TSV_HEADER]
    for index, word in enumerate(words, start=1):
        lines.append(
            "\t".join(
                [
                    str(index),
                    word,
                    "translation",
                    "-",
                    "m",
                    "-",
                    "-",
                    "-",
                    "no",
                    "misc",
                    "",
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.fixture(scope="session")
def real_words():
    return load_base_words(str(DATA_DIR), SHEETS)


# ---------------------------------------------------------------------------
# 5.1 -- pure half
# ---------------------------------------------------------------------------


def test_load_base_words_matches_the_real_1183_word_set(real_words):
    assert len(real_words) == 1183


def test_plan_requests_total_pairs_over_the_real_word_set(real_words, tmp_path):
    plan = plan_requests(real_words, ("f1", "m2"), media_dir=str(tmp_path))
    assert plan.total_pairs == 2366


def test_plan_requests_pending_excludes_present_pairs(tmp_path):
    words = ["на", "по", "с"]
    slots = ("f1", "m2")
    present_pairs = [("на", "f1"), ("по", "m2")]
    for word, slot in present_pairs:
        Path(build_filename(word, slot, dir_name=str(tmp_path))).touch()

    plan = plan_requests(words, slots, media_dir=str(tmp_path))

    assert len(plan.pending) == len(words) * len(slots) - len(present_pairs)
    for word, slot in plan.pending:
        assert not os.path.isfile(build_filename(word, slot, dir_name=str(tmp_path)))


def test_select_voices_returns_f1_m2_in_order():
    voices = select_voices(("f1", "m2"))
    assert [v.voice_id for v in voices] == [
        "t6lBrEl93uCiLR1Lgm8v",
        "pM78bgjPVk0JXtaEnFoj",
    ]
    assert [v.name for v in voices] == [
        "Alisa - Natural Russian Female",
        "Nester Surovy - Gravely yet Refined",
    ]


def test_select_voices_raises_naming_the_unknown_slot():
    with pytest.raises(ValueError, match="f3"):
        select_voices(("f3",))


def test_importing_mutable_words_audio_does_not_mutate_shared_voice_state():
    assert len(elevenlabs_tts.DEFAULT_VOICES) == 1
    assert elevenlabs_tts.DEFAULT_VOICES == elevenlabs_tts.VOICES[:1]


def test_pure_functions_never_touch_the_network(real_words, tmp_path):
    words = real_words[:5]
    voices = select_voices(("f1", "m2"))
    assert len(voices) == 2

    pairs = pending_pairs(words, ("f1", "m2"), str(tmp_path))
    assert pairs == [(word, slot) for word in words for slot in ("f1", "m2")]

    plan = plan_requests(words, ("f1", "m2"), media_dir=str(tmp_path))
    assert isinstance(plan, AudioWorkPlan)
    assert plan.total_pairs == 10
    assert plan.skipped == 0


# ---------------------------------------------------------------------------
# 5.2 -- driver + CLI
# ---------------------------------------------------------------------------


def test_main_dry_run_prints_the_real_environment_totals(capsys):
    rc = main(["--dry-run"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "total 2366 / present 14 / pending 2352" in out
    assert "voices:" in out


def test_generate_dedupes_a_doubled_word_list_and_spends_exactly_the_pending_count(
    tmp_path,
):
    media_dir = tmp_path / "media"
    output_dir = tmp_path / "output"
    words = ["на", "по", "с"]
    slots = ("f1", "m2")
    doubled = words + words

    session = _mock_session(
        [FakeResponse(200, content=f"a{i}".encode()) for i in range(6)]
    )
    budget = RequestBudget(limit=6)

    generate(
        doubled,
        slots=slots,
        media_dir=str(media_dir),
        output_dir=str(output_dir),
        budget=budget,
        session=session,
        api_key=DUMMY_API_KEY,
    )

    assert session.post.call_count == 6
    assert budget.spent == 6 == budget.limit


def test_generate_over_budget_by_one_raises_before_a_sixth_call(tmp_path):
    media_dir = tmp_path / "media"
    output_dir = tmp_path / "output"
    words = ["на", "по", "с"]
    slots = ("f1", "m2")
    doubled = words + words

    session = _mock_session(
        [FakeResponse(200, content=f"a{i}".encode()) for i in range(6)]
    )
    budget = RequestBudget(limit=5)

    with pytest.raises(BudgetExceededError):
        generate(
            doubled,
            slots=slots,
            media_dir=str(media_dir),
            output_dir=str(output_dir),
            budget=budget,
            session=session,
            api_key=DUMMY_API_KEY,
        )

    assert session.post.call_count == 5


def test_generate_writes_to_both_output_dir_and_media_dir(tmp_path):
    media_dir = tmp_path / "media"
    output_dir = tmp_path / "output"
    words = ["на", "по"]
    slots = ("f1", "m2")

    session = _mock_session(
        [FakeResponse(200, content=f"a{i}".encode()) for i in range(4)]
    )
    generate(
        words,
        slots=slots,
        media_dir=str(media_dir),
        output_dir=str(output_dir),
        budget=RequestBudget(limit=4),
        session=session,
        api_key=DUMMY_API_KEY,
    )

    for word in words:
        for slot in slots:
            assert os.path.isfile(build_filename(word, slot, dir_name=str(media_dir)))
            assert os.path.isfile(build_filename(word, slot, dir_name=str(output_dir)))


def test_generate_second_run_over_the_same_words_issues_zero_requests(tmp_path):
    media_dir = tmp_path / "media"
    output_dir = tmp_path / "output"
    words = ["на", "по"]
    slots = ("f1", "m2")

    first_session = _mock_session(
        [FakeResponse(200, content=f"a{i}".encode()) for i in range(4)]
    )
    generate(
        words,
        slots=slots,
        media_dir=str(media_dir),
        output_dir=str(output_dir),
        budget=RequestBudget(limit=4),
        session=first_session,
        api_key=DUMMY_API_KEY,
    )

    second_session = _mock_session([])
    second_budget = RequestBudget(limit=0)
    generate(
        words,
        slots=slots,
        media_dir=str(media_dir),
        output_dir=str(output_dir),
        budget=second_budget,
        session=second_session,
        api_key=DUMMY_API_KEY,
    )

    assert second_session.post.call_count == 0
    assert second_budget.spent == 0


def test_generate_regression_media_present_output_missing_issues_zero_requests(
    tmp_path,
):
    media_dir = tmp_path / "media"
    output_dir = tmp_path / "output"
    os.makedirs(media_dir)
    word = "на"
    slot = "f1"
    Path(build_filename(word, slot, dir_name=str(media_dir))).touch()

    session = _mock_session([])
    results = generate(
        [word],
        slots=(slot,),
        media_dir=str(media_dir),
        output_dir=str(output_dir),
        budget=RequestBudget(limit=0),
        session=session,
        api_key=DUMMY_API_KEY,
    )

    assert session.post.call_count == 0
    assert not os.path.isfile(build_filename(word, slot, dir_name=str(output_dir)))
    assert results is not None


def test_limit_flag_caps_total_requests_to_limit_times_slot_count(
    tmp_path, monkeypatch, capsys
):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _write_nouns_tsv(source_dir / "nouns.tsv", ["ага", "бег", "вид", "год"])
    media_dir = tmp_path / "media"
    output_dir = tmp_path / "output"
    monkeypatch.setenv(API_KEY_ENV_VAR, DUMMY_API_KEY)
    session = _patch_session(
        monkeypatch, [FakeResponse(200, content=f"a{i}".encode()) for i in range(8)]
    )

    rc = main(
        [
            "--source-dir",
            str(source_dir),
            "--sheet",
            "Nouns",
            "--anki-media-dir",
            str(media_dir),
            "--output-dir",
            str(output_dir),
            "--limit",
            "2",
            "--yes",
        ]
    )

    assert rc == 0
    assert session.post.call_count <= 2 * len(VOICE_SLOTS)
    assert DUMMY_API_KEY not in capsys.readouterr().out


def test_generate_sends_spoken_text_and_only_the_selected_voice_ids(tmp_path):
    media_dir = tmp_path / "media"
    output_dir = tmp_path / "output"
    words = ["в / во", "на"]
    slots = ("f1", "m2")

    session = _mock_session([FakeResponse(200, content=b"audio") for _ in range(4)])
    generate(
        words,
        slots=slots,
        media_dir=str(media_dir),
        output_dir=str(output_dir),
        budget=RequestBudget(limit=4),
        session=session,
        api_key=DUMMY_API_KEY,
    )

    allowed_ids = {v.voice_id for v in select_voices(slots)}
    excluded_ids = {v.voice_id for v in VOICES if v.slot not in slots}
    expected_texts = {spoken_text_for(word) for word in words}

    for call in session.post.call_args_list:
        sent_json = call.kwargs["json"]
        assert sent_json["text"] in expected_texts
        voice_id = call.args[0].rsplit("/", 1)[-1]
        assert voice_id in allowed_ids
        assert voice_id not in excluded_ids


def test_generate_writes_files_matching_build_filename_exactly(tmp_path):
    media_dir = tmp_path / "media"
    output_dir = tmp_path / "output"
    words = ["на"]
    slots = ("f1", "m2")

    session = _mock_session([FakeResponse(200, content=b"audio") for _ in range(2)])
    results = generate(
        words,
        slots=slots,
        media_dir=str(media_dir),
        output_dir=str(output_dir),
        budget=RequestBudget(limit=2),
        session=session,
        api_key=DUMMY_API_KEY,
    )

    expected = {build_filename("на", slot) for slot in slots}
    written = {os.path.basename(r.path) for r in results}
    assert written == expected


def test_main_never_leaks_the_api_key_into_stdout(tmp_path, monkeypatch, capsys):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _write_nouns_tsv(source_dir / "nouns.tsv", ["ага"])
    media_dir = tmp_path / "media"
    output_dir = tmp_path / "output"
    monkeypatch.setenv(API_KEY_ENV_VAR, DUMMY_API_KEY)
    _patch_session(monkeypatch, [FakeResponse(200, content=b"audio") for _ in range(2)])

    rc = main(
        [
            "--source-dir",
            str(source_dir),
            "--sheet",
            "Nouns",
            "--anki-media-dir",
            str(media_dir),
            "--output-dir",
            str(output_dir),
            "--yes",
        ]
    )

    assert rc == 0
    assert DUMMY_API_KEY not in capsys.readouterr().out


def test_main_prompts_above_the_threshold_and_aborts_on_no(
    tmp_path, monkeypatch, capsys
):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _write_nouns_tsv(source_dir / "nouns.tsv", ["ага", "бег"])
    media_dir = tmp_path / "media"
    output_dir = tmp_path / "output"
    monkeypatch.setenv(API_KEY_ENV_VAR, DUMMY_API_KEY)
    session = _patch_session(monkeypatch, [])
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "n")

    rc = main(
        [
            "--source-dir",
            str(source_dir),
            "--sheet",
            "Nouns",
            "--anki-media-dir",
            str(media_dir),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert rc == 1
    assert session.post.call_count == 0
    out = capsys.readouterr().out
    assert "Aborted" in out
    assert DUMMY_API_KEY not in out


def test_main_proceeds_with_yes_flag_or_a_yes_answer(tmp_path, monkeypatch, capsys):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _write_nouns_tsv(source_dir / "nouns.tsv", ["ага", "бег"])
    monkeypatch.setenv(API_KEY_ENV_VAR, DUMMY_API_KEY)

    session = _patch_session(
        monkeypatch, [FakeResponse(200, content=f"a{i}".encode()) for i in range(4)]
    )
    rc = main(
        [
            "--source-dir",
            str(source_dir),
            "--sheet",
            "Nouns",
            "--anki-media-dir",
            str(tmp_path / "media"),
            "--output-dir",
            str(tmp_path / "output"),
            "--yes",
        ]
    )
    assert rc == 0
    assert session.post.call_count == 4

    session2 = _patch_session(
        monkeypatch, [FakeResponse(200, content=f"b{i}".encode()) for i in range(4)]
    )
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "y")
    rc2 = main(
        [
            "--source-dir",
            str(source_dir),
            "--sheet",
            "Nouns",
            "--anki-media-dir",
            str(tmp_path / "media2"),
            "--output-dir",
            str(tmp_path / "output2"),
        ]
    )
    assert rc2 == 0
    assert session2.post.call_count == 4
    assert DUMMY_API_KEY not in capsys.readouterr().out


def test_main_missing_api_key_prints_the_env_var_name_and_returns_1(
    tmp_path, monkeypatch, capsys
):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _write_nouns_tsv(source_dir / "nouns.tsv", ["ага"])
    media_dir = tmp_path / "media"
    output_dir = tmp_path / "output"
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    session = _patch_session(monkeypatch, [])
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "y")

    rc = main(
        [
            "--source-dir",
            str(source_dir),
            "--sheet",
            "Nouns",
            "--anki-media-dir",
            str(media_dir),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert rc == 1
    assert session.post.call_count == 0
    assert API_KEY_ENV_VAR in capsys.readouterr().out
