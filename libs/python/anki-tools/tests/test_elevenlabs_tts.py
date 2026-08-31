"""Tests for anki_tools.elevenlabs_tts (Phase 4, subphase 4.1, lane 2).

Every test in this file is fully offline: `requests.Session.post` (and the
bare `requests.post`) are monkeypatched, module-wide, to blow up if actually
called -- a test that forgets to inject its own fake session fails loudly
instead of silently reaching the real ElevenLabs API and spending money.
Nothing here ever imports or touches a real network socket.

THE HARD COST LIMIT (tightened): the default invocation issues exactly ONE
mocked request -- one word, one voice. `--all-voices` and `--all`/`--count`
are two SEPARATE opt-ins that must never imply each other, and the cap is
enforced structurally via `RequestBudget`/`fetch_tts_audio_metered`, not by
trusting a default argument to be threaded through correctly. The tests
below assert real `mock.call_count` values against a `unittest.mock.Mock`
session, not just "it worked" -- per the coordinator's explicit ask.
"""

import json
import os
from unittest.mock import MagicMock

import pytest
import requests

from anki_tools.elevenlabs_tts import (
    API_KEY_ENV_VAR,
    DEFAULT_MODEL_ID,
    DEFAULT_VOICE_LIMIT,
    DEFAULT_VOICES,
    DEFAULT_WORD_LIMIT,
    VOICES,
    BudgetExceededError,
    ElevenLabsAPIError,
    MissingAPIKeyError,
    RateLimitedError,
    RequestBudget,
    TransientServerError,
    Voice,
    build_and_save,
    build_and_save_batch,
    build_filename,
    build_parser,
    get_api_key,
    load_words_from_file,
    main,
    sanitize_word_slug,
)

# ---------------------------------------------------------------------------
# Global network guard -- a positive control that the guard itself works,
# plus the guard applied to every test in this module.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def block_real_network(monkeypatch):
    def _boom(*_args, **_kwargs):
        raise AssertionError(
            "a test attempted a REAL HTTP request -- every test must inject "
            "its own fake session/response instead."
        )

    monkeypatch.setattr(requests, "post", _boom)
    monkeypatch.setattr(requests.Session, "post", _boom)
    # Never actually sleep during a retry test.
    monkeypatch.setattr("anki_tools.elevenlabs_tts.time.sleep", lambda _seconds: None)


def test_network_guard_actually_blocks_real_requests():
    """Positive control: prove the autouse guard could fail if it were absent."""
    with pytest.raises(AssertionError, match="REAL HTTP request"):
        requests.post("https://api.elevenlabs.io/v1/voices")
    with pytest.raises(AssertionError, match="REAL HTTP request"):
        requests.Session().post("https://api.elevenlabs.io/v1/voices")


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeResponse:
    def __init__(self, status_code=200, content=b"", headers=None, text=""):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.text = text or ""


class FakeSession:
    """Records every call and returns queued responses/exceptions in order."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def post(self, url, headers=None, json=None, timeout=None):  # noqa: A002
        self.calls.append(
            {"url": url, "headers": headers, "json": json, "timeout": timeout}
        )
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _mock_session(responses):
    """A `unittest.mock.Mock`-based session whose `.post` has a real,
    directly-assertable `call_count` -- used for the tests the coordinator
    specifically asked to see `mock.call_count` assertions from."""
    session = MagicMock()
    session.post = MagicMock(side_effect=list(responses))
    return session


# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------


def test_get_api_key_missing_names_the_env_var(monkeypatch):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    with pytest.raises(MissingAPIKeyError, match=API_KEY_ENV_VAR):
        get_api_key()


def test_get_api_key_never_leaks_into_the_error_message(monkeypatch):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    try:
        get_api_key()
    except MissingAPIKeyError as exc:
        assert "sk_" not in str(exc)  # nothing resembling a real key literal


def test_get_api_key_reads_from_environment(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "test-key-value")
    assert get_api_key() == "test-key-value"


# ---------------------------------------------------------------------------
# Filename sanitization -- the genuinely awkward rows from the source list
# ---------------------------------------------------------------------------

AWKWARD_WORDS = [
    "в / во",
    "с / со",
    "ни... ни...",
    "несмотря на то, что",
    "-то",
    "чтобы / чтоб",
]


@pytest.mark.parametrize("word", AWKWARD_WORDS)
def test_sanitize_word_slug_has_no_filesystem_hostile_chars(word):
    slug = sanitize_word_slug(word)
    for bad_char in ("/", "\\", "\0"):
        assert bad_char not in slug
    assert slug  # never empty


@pytest.mark.parametrize("word", AWKWARD_WORDS + ["простой", "бра"])
def test_sanitize_word_slug_is_deterministic(word):
    assert sanitize_word_slug(word) == sanitize_word_slug(word)


def test_sanitize_word_slug_collision_free_across_the_whole_awkward_set():
    slugs = [sanitize_word_slug(w) for w in AWKWARD_WORDS]
    assert len(slugs) == len(set(slugs))


def test_sanitize_word_slug_distinguishes_hyphen_stripped_collisions():
    # "-то" simplifies to the same visible text as "то" once its leading
    # hyphen is stripped -- the hash suffix must still keep them apart.
    assert sanitize_word_slug("-то") != sanitize_word_slug("то")


def test_build_filename_encodes_word_and_voice_and_has_no_slash_in_the_slug():
    voice = VOICES[0]
    path = build_filename("в / во", voice, dir_name="audio_files")
    assert path.startswith("audio_files" + os.sep)
    basename = os.path.basename(path)
    assert "/" not in basename
    assert basename.endswith(f"__{voice.slug}.mp3")


def test_build_filename_is_reproducible_across_calls():
    voice = VOICES[1]
    assert build_filename("на", voice) == build_filename("на", voice)


def test_all_three_voices_produce_distinct_filenames_for_the_same_word():
    paths = {build_filename("на", voice) for voice in VOICES}
    assert len(paths) == len(VOICES) == 3


# ---------------------------------------------------------------------------
# Voice roster (D5) and the tightened default (D5 + cost-limit amendment)
# ---------------------------------------------------------------------------


def test_voices_are_exactly_the_three_settled_russian_voices():
    assert [v.voice_id for v in VOICES] == [
        "TPIitICAZ8CqlGZ81AKm",
        "RLRdvNFwJJct2XZOgfzy",
        "pM78bgjPVk0JXtaEnFoj",
    ]
    assert all(isinstance(v, Voice) for v in VOICES)


def test_default_voice_limit_and_default_voices_is_exactly_one_voice():
    assert DEFAULT_VOICE_LIMIT == 1
    assert DEFAULT_WORD_LIMIT == 1
    assert len(DEFAULT_VOICES) == 1
    assert DEFAULT_VOICES[0] == VOICES[0]  # Elen Kuragina, first in the roster


# ---------------------------------------------------------------------------
# RequestBudget -- the structural choke point itself
# ---------------------------------------------------------------------------


def test_request_budget_allows_spend_up_to_its_limit():
    budget = RequestBudget(limit=2)
    budget.spend(1)
    budget.spend(1)
    assert budget.spent == 2
    assert budget.remaining() == 0


def test_request_budget_raises_rather_than_proceeding_when_exceeded():
    budget = RequestBudget(limit=1)
    budget.spend(1)
    with pytest.raises(BudgetExceededError):
        budget.spend(1)
    # The rejected spend must not have been recorded as spent.
    assert budget.spent == 1


def test_request_budget_rejects_a_negative_limit():
    with pytest.raises(ValueError):
        RequestBudget(limit=-1)


def test_request_budget_of_zero_allows_nothing():
    budget = RequestBudget(limit=0)
    with pytest.raises(BudgetExceededError):
        budget.spend(1)


# ---------------------------------------------------------------------------
# build_and_save: the choke point wired into real synthesis calls
# ---------------------------------------------------------------------------


def test_build_and_save_default_voices_writes_exactly_one_file(tmp_path):
    out_dir = str(tmp_path / "audio")
    session = _mock_session([FakeResponse(200, content=b"audio")])
    budget = RequestBudget(limit=1)

    results = build_and_save(
        "на", dir_name=out_dir, api_key="k", session=session, budget=budget
    )

    assert len(results) == 1
    assert session.post.call_count == 1
    assert results[0].voice == DEFAULT_VOICES[0]
    assert not results[0].skipped
    assert os.path.isfile(results[0].path)
    assert budget.spent == 1


def test_build_and_save_explicit_all_voices_writes_three_files(tmp_path):
    out_dir = str(tmp_path / "audio")
    responses = [FakeResponse(200, content=f"audio-{i}".encode()) for i in range(3)]
    session = _mock_session(responses)
    budget = RequestBudget(limit=3)

    results = build_and_save(
        "на",
        dir_name=out_dir,
        api_key="k",
        session=session,
        budget=budget,
        voices=VOICES,  # explicit opt-in to all three, direct-import style
    )

    assert len(results) == 3
    assert session.post.call_count == 3
    called_voice_ids = [
        c.args[0].rsplit("/", 1)[-1] for c in session.post.call_args_list
    ]
    assert called_voice_ids == [v.voice_id for v in VOICES]
    assert budget.spent == 3


def test_build_and_save_skips_existing_file_by_default(tmp_path):
    out_dir = str(tmp_path / "audio")
    session = _mock_session([FakeResponse(200, b"a")])
    build_and_save(
        "на", dir_name=out_dir, api_key="k", session=session, budget=RequestBudget(1)
    )
    assert session.post.call_count == 1

    # Second run: nothing should be requested again -- a budget of ZERO
    # still succeeds, because a skip never touches the budget.
    session2 = _mock_session([])
    zero_budget = RequestBudget(limit=0)
    results = build_and_save(
        "на", dir_name=out_dir, api_key="k", session=session2, budget=zero_budget
    )
    assert all(r.skipped for r in results)
    assert session2.post.call_count == 0
    assert zero_budget.spent == 0


def test_build_and_save_replace_forces_regeneration(tmp_path):
    out_dir = str(tmp_path / "audio")
    session = _mock_session([FakeResponse(200, b"a")])
    build_and_save(
        "на", dir_name=out_dir, api_key="k", session=session, budget=RequestBudget(1)
    )

    session2 = _mock_session([FakeResponse(200, b"a2")])
    results = build_and_save(
        "на",
        dir_name=out_dir,
        api_key="k",
        session=session2,
        budget=RequestBudget(1),
        replace=True,
    )
    assert all(not r.skipped for r in results)
    assert session2.post.call_count == 1
    with open(results[0].path, "rb") as fh:
        assert fh.read() == b"a2"


def test_build_and_save_rejects_missing_api_key_before_any_request(
    tmp_path, monkeypatch
):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    session = _mock_session([])
    with pytest.raises(MissingAPIKeyError):
        build_and_save(
            "на", dir_name=str(tmp_path), session=session, budget=RequestBudget(1)
        )
    assert session.post.call_count == 0


def test_build_and_save_batch_covers_every_word_and_voice(tmp_path):
    out_dir = str(tmp_path / "audio")
    words = ["на", "по"]
    responses = [
        FakeResponse(200, f"x{i}".encode()) for i in range(len(words) * len(VOICES))
    ]
    session = _mock_session(responses)
    budget = RequestBudget(limit=len(words) * len(VOICES))
    results = build_and_save_batch(
        words,
        dir_name=out_dir,
        api_key="k",
        session=session,
        budget=budget,
        voices=VOICES,
    )
    assert len(results) == len(words) * len(VOICES)
    assert session.post.call_count == len(words) * len(VOICES)
    assert budget.spent == len(words) * len(VOICES)


# ---------------------------------------------------------------------------
# THE structural cap: exceeding the budget raises, and stops BEFORE the
# network call that would exceed it -- test #4 from the coordinator's list.
# ---------------------------------------------------------------------------


def test_exceeding_budget_raises_and_over_limit_request_never_reaches_network(tmp_path):
    # 3 voices requested for one word, but the budget only allows 1: the
    # first (word, voice) pair must succeed, the second must raise instead
    # of proceeding, and the network must never be touched a second time.
    session = _mock_session(
        [FakeResponse(200, b"a"), FakeResponse(200, b"b"), FakeResponse(200, b"c")]
    )
    budget = RequestBudget(limit=1)

    with pytest.raises(BudgetExceededError):
        build_and_save(
            "на",
            dir_name=str(tmp_path),
            api_key="k",
            session=session,
            budget=budget,
            voices=VOICES,
        )

    assert session.post.call_count == 1  # the 2nd/3rd voice never reached the network
    assert budget.spent == 1


def test_build_and_save_requires_an_explicit_budget_argument(tmp_path):
    # No default: a caller that forgets to declare a budget gets a TypeError
    # at the call site, not a silent "unlimited" fallback.
    with pytest.raises(TypeError):
        build_and_save(
            "на", dir_name=str(tmp_path), api_key="k", session=_mock_session([])
        )


def test_build_and_save_batch_requires_an_explicit_budget_argument(tmp_path):
    with pytest.raises(TypeError):
        build_and_save_batch(
            ["на"], dir_name=str(tmp_path), api_key="k", session=_mock_session([])
        )


# ---------------------------------------------------------------------------
# Retry / backoff, including 429 handling (unaffected by the budget change:
# a retried request is still only ONE spend against the budget)
# ---------------------------------------------------------------------------


def test_transient_500_is_retried_then_succeeds_and_only_spends_once(tmp_path):
    session = FakeSession(
        [FakeResponse(500, text="boom"), FakeResponse(200, content=b"ok")]
    )
    budget = RequestBudget(limit=1)
    results = build_and_save(
        "у",
        dir_name=str(tmp_path),
        api_key="k",
        session=session,
        budget=budget,
        voices=VOICES[:1],
    )
    assert len(session.calls) == 2  # one logical request, retried once at HTTP level
    assert budget.spent == 1  # but only ONE unit of budget was spent
    assert not results[0].skipped


def test_429_is_retried_and_honors_retry_after_header(tmp_path, monkeypatch):
    sleep_calls = []
    monkeypatch.setattr(
        "anki_tools.elevenlabs_tts.time.sleep",
        lambda seconds: sleep_calls.append(seconds),
    )
    session = FakeSession(
        [
            FakeResponse(429, headers={"Retry-After": "2.5"}, text="slow down"),
            FakeResponse(200, content=b"ok"),
        ]
    )
    build_and_save(
        "у",
        dir_name=str(tmp_path),
        api_key="k",
        session=session,
        budget=RequestBudget(1),
        voices=VOICES[:1],
    )
    assert len(session.calls) == 2
    assert sleep_calls == [2.5]


def test_exhausting_retries_on_persistent_500_raises(tmp_path):
    session = FakeSession([FakeResponse(500, text="down")] * 10)
    with pytest.raises(TransientServerError):
        build_and_save(
            "у",
            dir_name=str(tmp_path),
            api_key="k",
            session=session,
            budget=RequestBudget(1),
            voices=VOICES[:1],
        )


def test_non_retryable_4xx_raises_immediately_without_retrying(tmp_path):
    session = FakeSession([FakeResponse(401, text="unauthorized")])
    with pytest.raises(ElevenLabsAPIError):
        build_and_save(
            "у",
            dir_name=str(tmp_path),
            api_key="k",
            session=session,
            budget=RequestBudget(1),
            voices=VOICES[:1],
        )
    assert len(session.calls) == 1  # no retry for a non-retryable error


def test_network_error_from_requests_is_retried(tmp_path):
    session = FakeSession(
        [
            requests.exceptions.ConnectionError("dns fail"),
            FakeResponse(200, content=b"ok"),
        ]
    )
    build_and_save(
        "у",
        dir_name=str(tmp_path),
        api_key="k",
        session=session,
        budget=RequestBudget(1),
        voices=VOICES[:1],
    )
    assert len(session.calls) == 2


def test_rate_limited_error_is_not_a_subclass_of_transient_server_error():
    # 429 is handled specifically, per the contract, and is distinguishable
    # from a generic transient server error by callers who care to.
    assert not issubclass(RateLimitedError, TransientServerError)
    assert not issubclass(TransientServerError, RateLimitedError)


# ---------------------------------------------------------------------------
# Word-list loading
# ---------------------------------------------------------------------------


def test_load_words_from_file_plain_text_skips_blanks_and_comments(tmp_path):
    file_path = tmp_path / "words.txt"
    file_path.write_text(
        "\n".join(["в / во", "", "# a comment", "  на  ", "ни... ни..."]),
        encoding="utf-8",
    )
    words = load_words_from_file(str(file_path))
    assert words == ["в / во", "на", "ни... ни..."]


def test_load_words_from_file_json_list(tmp_path):
    file_path = tmp_path / "words.json"
    file_path.write_text(json.dumps(["на", "по", " "]), encoding="utf-8")
    words = load_words_from_file(str(file_path))
    assert words == ["на", "по"]


def test_load_words_from_file_json_rejects_non_list(tmp_path):
    file_path = tmp_path / "words.json"
    file_path.write_text(json.dumps({"на": "on"}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_words_from_file(str(file_path))


# ---------------------------------------------------------------------------
# CLI: build_parser
# ---------------------------------------------------------------------------


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["--word", "на"])
    assert args.model_id == DEFAULT_MODEL_ID
    assert args.all is False
    assert args.count is None
    assert args.all_voices is False


def test_count_and_all_are_mutually_exclusive():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--file", "x.txt", "--all", "--count", "3"])


def test_word_and_file_are_mutually_exclusive():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--word", "на", "--file", "x.txt"])


def test_all_voices_composes_with_all_and_with_count():
    parser = build_parser()
    args1 = parser.parse_args(["--file", "x.txt", "--all", "--all-voices"])
    assert args1.all is True
    assert args1.all_voices is True
    args2 = parser.parse_args(["--file", "x.txt", "--count", "5", "--all-voices"])
    assert args2.count == 5
    assert args2.all_voices is True


# ---------------------------------------------------------------------------
# CLI: main() -- the four required tests (assertions on real mock.call_count)
# ---------------------------------------------------------------------------


def _patch_session(monkeypatch, responses):
    session = _mock_session(responses)
    monkeypatch.setattr("anki_tools.elevenlabs_tts.requests.Session", lambda: session)
    return session


def test_1_default_invocation_issues_exactly_one_request(tmp_path, monkeypatch, capsys):
    """Required test #1: default invocation issues exactly ONE mocked
    request -- one word, one voice. Asserts the real call count, not just
    that the run "worked"."""
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    session = _patch_session(monkeypatch, [FakeResponse(200, content=b"audio")])

    rc = main(["--word", "на", "--output-dir", "out"])

    assert rc == 0
    assert session.post.call_count == 1
    out = capsys.readouterr().out
    assert "About to issue 1 ElevenLabs request(s)" in out
    assert "1 word(s)" in out
    assert "1 voice(s)" in out
    assert "Elen Kuragina" in out  # the voice involved is printed by name


def test_2_all_voices_on_one_word_issues_exactly_three_requests(
    tmp_path, monkeypatch, capsys
):
    """Required test #2: --all-voices on one word issues exactly 3."""
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    responses = [FakeResponse(200, content=f"a{i}".encode()) for i in range(3)]
    session = _patch_session(monkeypatch, responses)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")  # 3 > threshold

    rc = main(["--word", "на", "--all-voices", "--output-dir", "out"])

    assert rc == 0
    assert session.post.call_count == 3
    out = capsys.readouterr().out
    assert "About to issue 3 ElevenLabs request(s)" in out
    assert "Mishka Yaponcik" in out and "Nester Surovy" in out


def test_3_word_list_path_is_not_reached_without_its_explicit_opt_in(
    tmp_path, monkeypatch, capsys
):
    """Required test #3: the word-list path is NOT reached without its
    explicit opt-in -- a multi-word --file with no --all/--count must still
    issue exactly one request (one word, the default one voice)."""
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n".join(["в", "на", "с", "по", "к"]), encoding="utf-8")
    session = _patch_session(monkeypatch, [FakeResponse(200, content=b"audio")])

    rc = main(["--file", str(words_file), "--output-dir", "out"])

    assert rc == 0
    assert session.post.call_count == 1  # not 5, not 15 -- exactly 1
    out = capsys.readouterr().out
    assert "1 word(s) (of 5 available)" in out


def test_3b_all_voices_alone_does_not_start_walking_the_word_list(
    tmp_path, monkeypatch, capsys
):
    """--all-voices given alone (no --all/--count) must widen the voice
    axis only, never the word axis: 1 word x 3 voices = 3, not 5 x 3 = 15."""
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n".join(["в", "на", "с", "по", "к"]), encoding="utf-8")
    responses = [FakeResponse(200, content=f"a{i}".encode()) for i in range(3)]
    session = _patch_session(monkeypatch, responses)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")

    rc = main(["--file", str(words_file), "--all-voices", "--output-dir", "out"])

    assert rc == 0
    assert session.post.call_count == 3  # 1 word x 3 voices, word list NOT walked
    out = capsys.readouterr().out
    assert "1 word(s) (of 5 available)" in out


def test_4_a_would_exceed_the_cap_path_raises_rather_than_proceeding(tmp_path):
    """Required test #4: a "would exceed the cap" path raises rather than
    proceeding. Exercised directly against the structural choke point
    (RequestBudget/build_and_save), independent of the CLI's own printed
    count and confirmation prompt (covered separately below)."""
    session = _mock_session(
        [FakeResponse(200, b"a"), FakeResponse(200, b"b"), FakeResponse(200, b"c")]
    )
    budget = RequestBudget(limit=1)  # deliberately smaller than the 3 voices below

    with pytest.raises(BudgetExceededError):
        build_and_save(
            "на",
            dir_name=str(tmp_path / "audio"),  # isolated: never a stray cwd dir
            api_key="k",
            session=session,
            budget=budget,
            voices=VOICES,
        )

    assert session.post.call_count == 1  # the would-exceed request never proceeded


def test_4b_cli_prompts_before_a_would_exceed_the_default_cap_run(
    tmp_path, monkeypatch
):
    """The CLI-level counterpart of #4: anything above the default cap must
    prompt, and answering "no" must issue ZERO requests."""
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    session = _patch_session(monkeypatch, [])
    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")

    rc = main(["--word", "на", "--all-voices", "--output-dir", "out"])

    assert rc == 1
    assert session.post.call_count == 0  # nothing was spent


# ---------------------------------------------------------------------------
# CLI: main() -- remaining coverage (opt-in composition, --yes, missing key)
# ---------------------------------------------------------------------------


def test_all_flag_opts_into_the_full_word_list_at_the_default_one_voice(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n".join(["в", "на"]), encoding="utf-8")

    session = _patch_session(
        monkeypatch, [FakeResponse(200, content=f"a{i}".encode()) for i in range(2)]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")

    rc = main(["--file", str(words_file), "--all", "--output-dir", "out"])

    assert rc == 0
    assert session.post.call_count == 2  # 2 words x 1 voice, NOT x 3


def test_count_flag_opts_into_an_explicit_number_of_words(tmp_path, monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n".join(["в", "на", "с"]), encoding="utf-8")

    session = _patch_session(
        monkeypatch, [FakeResponse(200, content=f"a{i}".encode()) for i in range(2)]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")

    rc = main(["--file", str(words_file), "--count", "2", "--output-dir", "out"])

    assert rc == 0
    assert session.post.call_count == 2


def test_all_and_all_voices_compose_to_widen_both_axes(tmp_path, monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n".join(["в", "на"]), encoding="utf-8")

    session = _patch_session(
        monkeypatch, [FakeResponse(200, content=f"a{i}".encode()) for i in range(2 * 3)]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")

    rc = main(
        ["--file", str(words_file), "--all", "--all-voices", "--output-dir", "out"]
    )

    assert rc == 0
    assert session.post.call_count == 2 * 3  # both axes explicitly widened


def test_multi_request_run_requires_confirmation_and_aborts_on_no(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n".join(["в", "на"]), encoding="utf-8")

    session = _patch_session(monkeypatch, [])
    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")

    rc = main(["--file", str(words_file), "--all", "--output-dir", "out"])

    assert rc == 1
    assert session.post.call_count == 0  # nothing was spent
    assert "Aborted" in capsys.readouterr().out


def test_yes_flag_skips_the_confirmation_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n".join(["в", "на"]), encoding="utf-8")

    session = _patch_session(
        monkeypatch, [FakeResponse(200, content=f"a{i}".encode()) for i in range(2)]
    )

    def _boom_input(_prompt=""):
        raise AssertionError("input() must not be called when --yes is given")

    monkeypatch.setattr("builtins.input", _boom_input)

    rc = main(["--file", str(words_file), "--all", "--yes", "--output-dir", "out"])
    assert rc == 0
    assert session.post.call_count == 2


def test_single_word_default_run_never_prompts(tmp_path, monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)

    session = _patch_session(monkeypatch, [FakeResponse(200, content=b"audio")])

    def _boom_input(_prompt=""):
        raise AssertionError("a single-request default run must never prompt")

    monkeypatch.setattr("builtins.input", _boom_input)

    rc = main(["--word", "на", "--output-dir", "out"])
    assert rc == 0
    assert session.post.call_count == 1


def test_missing_api_key_fails_before_touching_the_network(tmp_path, monkeypatch):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    monkeypatch.chdir(tmp_path)
    session = _patch_session(monkeypatch, [])

    rc = main(["--word", "на", "--output-dir", "out"])

    assert rc == 1
    assert session.post.call_count == 0


def test_neither_word_nor_file_is_an_error(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    with pytest.raises(SystemExit):
        main([])
