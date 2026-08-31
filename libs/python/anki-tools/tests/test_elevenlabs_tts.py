"""Tests for anki_tools.elevenlabs_tts (Phase 4, subphase 4.1, lane 2).

Every test in this file is fully offline: `requests.Session.post` (and the
bare `requests.post`) are monkeypatched, module-wide, to blow up if actually
called -- a test that forgets to inject its own fake session fails loudly
instead of silently reaching the real ElevenLabs API and spending money.
Nothing here ever imports or touches a real network socket.

THE HARD COST LIMIT: the default invocation issues exactly ONE mocked
request -- one word, one voice (f1/Alisa). `--all-voices` and
`--all`/`--count` are two SEPARATE opt-ins that must never imply each
other, and the cap is enforced structurally via `RequestBudget`/
`fetch_tts_audio_metered`, not by trusting a default argument to be
threaded through correctly.

Voice roster (paid plan, four slots + one retired, non-default voice):
f1 Alisa, f2 Elena Gromova, m1 Mishka Yaponcik, m2 Nester Surovy, plus
f0 Elen Kuragina (defined, never default). Filenames are
`<word-slug>_<slot>.mp3`, readable and hash-free -- verified collision-free
against the real 152-row source word list below, distinguishing the one
legitimate duplicate ("да", same text twice) from a genuine collision
(two DIFFERENT words sanitizing to the same slug, which must never happen
silently).

Every synthesis call sends ElevenLabs' `voice_settings` (`stability`,
`similarity_boost`, both 0.0-1.0, default 0.85/0.85) -- validated to RAISE,
never clamp, on an out-of-range value.
"""

import json
import os
import re
from unittest.mock import MagicMock

import pytest
import requests

from anki_tools.elevenlabs_tts import (
    ALL_VOICES,
    API_KEY_ENV_VAR,
    DEFAULT_MODEL_ID,
    DEFAULT_SIMILARITY_BOOST,
    DEFAULT_STABILITY,
    DEFAULT_VOICE_LIMIT,
    DEFAULT_VOICES,
    DEFAULT_WORD_LIMIT,
    ELEN_KURAGINA,
    VOICES,
    BudgetExceededError,
    ElevenLabsAPIError,
    MissingAPIKeyError,
    RateLimitedError,
    RequestBudget,
    TransientServerError,
    Voice,
    _check_unique_slots,
    build_and_save,
    build_and_save_batch,
    build_filename,
    build_parser,
    fetch_tts_audio_metered,
    get_api_key,
    load_words_from_file,
    main,
    sanitize_word_slug,
    validate_voice_setting,
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
# Voice roster and slot uniqueness
# ---------------------------------------------------------------------------


def test_voices_are_exactly_the_four_default_roster_voices():
    assert [v.voice_id for v in VOICES] == [
        "t6lBrEl93uCiLR1Lgm8v",  # Alisa
        "0ArNnoIAWKlT4WweaVMY",  # Elena Gromova
        "RLRdvNFwJJct2XZOgfzy",  # Mishka Yaponcik
        "pM78bgjPVk0JXtaEnFoj",  # Nester Surovy
    ]
    assert [v.slot for v in VOICES] == ["f1", "f2", "m1", "m2"]
    assert all(isinstance(v, Voice) for v in VOICES)


def test_elen_kuragina_is_defined_but_excluded_from_the_default_roster():
    assert ELEN_KURAGINA not in VOICES
    assert ELEN_KURAGINA.voice_id == "TPIitICAZ8CqlGZ81AKm"
    assert ELEN_KURAGINA in ALL_VOICES
    assert ELEN_KURAGINA.slot not in {v.slot for v in VOICES}


def test_default_voice_limit_and_default_voices_is_exactly_one_voice():
    assert DEFAULT_VOICE_LIMIT == 1
    assert DEFAULT_WORD_LIMIT == 1
    assert len(DEFAULT_VOICES) == 1
    assert DEFAULT_VOICES[0] == VOICES[0]  # f1, Alisa


def test_all_voices_have_pairwise_unique_slots():
    slots = [v.slot for v in ALL_VOICES]
    assert len(slots) == len(set(slots)) == 5


def test_check_unique_slots_raises_on_a_duplicate():
    a = Voice(name="A", voice_id="id-a", slug="a", gender="female", slot="f1")
    b = Voice(name="B", voice_id="id-b", slug="b", gender="male", slot="f1")
    with pytest.raises(ValueError, match="duplicate slot"):
        _check_unique_slots((a, b))


def test_check_unique_slots_passes_on_the_real_roster():
    _check_unique_slots(ALL_VOICES)  # must not raise


# ---------------------------------------------------------------------------
# Filename sanitization -- the genuinely awkward rows from the source list
# ---------------------------------------------------------------------------

AWKWARD_WORDS = [
    "в / во",
    "с / со",
    "о / об",
    "ни... ни...",
    "то... то...",
    "-то",
    "-ка",
    "несмотря на то, что",
    "для того, чтобы",
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


def test_sanitize_word_slug_collision_free_across_the_awkward_set():
    slugs = [sanitize_word_slug(w) for w in AWKWARD_WORDS]
    assert len(slugs) == len(set(slugs))


def test_build_filename_is_word_slug_underscore_slot_dot_mp3():
    voice = VOICES[0]  # f1
    path = build_filename("около", voice, dir_name="audio_files")
    assert path == os.path.join("audio_files", "около_f1.mp3")


def test_build_filename_has_no_slash_in_the_basename():
    voice = VOICES[3]  # m2
    path = build_filename("в / во", voice, dir_name="audio_files")
    basename = os.path.basename(path)
    assert "/" not in basename
    assert basename.endswith("_m2.mp3")


def test_build_filename_is_reproducible_across_calls():
    voice = VOICES[1]
    assert build_filename("на", voice) == build_filename("на", voice)


def test_all_four_roster_voices_produce_distinct_filenames_for_the_same_word():
    paths = {build_filename("на", voice) for voice in VOICES}
    assert len(paths) == len(VOICES) == 4


# ---------------------------------------------------------------------------
# THE hazard the coordinator asked to be checked, not assumed: dropping the
# hash suffix must not silently reintroduce collisions across the REAL
# 152-row source word list.
# ---------------------------------------------------------------------------

# Computed relative to this test file, not hardcoded to a home directory:
# .../<run>-l2/libs/python/anki-tools/tests/test_elevenlabs_tts.py
# -> up 4 levels -> the lane's own worktree root (<run>-l2)
# -> its sibling, the PARENT worktree (<run>), holds the gitignored run dir.
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_LANE_WORKTREE_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_TESTS_DIR)))
)
_WORKFLOWS_DIR = os.path.dirname(_LANE_WORKTREE_ROOT)
_LANE_SUFFIX = "-l2"
_lane_name = os.path.basename(_LANE_WORKTREE_ROOT)
_run_name = (
    _lane_name[: -len(_LANE_SUFFIX)]
    if _lane_name.endswith(_LANE_SUFFIX)
    else _lane_name
)
SOURCE_WORD_LIST_PATH = os.path.join(
    _WORKFLOWS_DIR, _run_name, ".artifacts", "source-word-list.md"
)

_SOURCE_LIST_MISSING_REASON = (
    "source-word-list.md lives in the parent worktree's gitignored run dir "
    "(.artifacts/), which is destroyed with that worktree once this run's "
    "lanes merge and closeout runs -- this test verifies against the REAL "
    "word list while the run is in flight and skips once the artifact is "
    "gone, rather than becoming a permanently broken/false-failing test "
    "long after the data it checks stopped existing."
)


@pytest.mark.skipif(
    not os.path.isfile(SOURCE_WORD_LIST_PATH), reason=_SOURCE_LIST_MISSING_REASON
)
def test_slug_collision_free_across_real_source_word_list():
    """Prove, don't assume: run every word in the real 152-row source list
    through `sanitize_word_slug` and assert the results are pairwise
    unique, with exactly one KNOWN, LEGITIMATE exception -- "да" appears
    twice (Conjunctions #20, Particles #20) with IDENTICAL text, so it
    correctly shares one slug/file. Any OTHER repeated slug would mean two
    DIFFERENT words silently overwriting each other's audio, which this
    test must catch and report, never paper over by re-adding a hash.
    """
    row_re = re.compile(r"^\| *\d+ *\| *(.+?) *\| *.+? *\|\s*$")
    words = []
    with open(SOURCE_WORD_LIST_PATH, encoding="utf-8") as fh:
        for line in fh:
            m = row_re.match(line)
            if m:
                words.append(m.group(1))

    # A positive control on the parse itself: a bare zero (or a suspiciously
    # low count from a regex that stopped matching) would make every
    # assertion below trivially true for the wrong reason.
    assert len(words) == 152, (
        f"expected 152 parsed rows from the source word list, got "
        f"{len(words)} -- the parser regex may no longer match the table "
        f"format; investigate before trusting this test's result."
    )

    slugs = [sanitize_word_slug(w) for w in words]
    slug_to_words = {}
    for word, slug in zip(words, slugs):
        slug_to_words.setdefault(slug, []).append(word)
    collisions = {slug: ws for slug, ws in slug_to_words.items() if len(ws) > 1}

    da_slug = sanitize_word_slug("да")
    assert list(collisions.keys()) == [da_slug], (
        f"expected exactly one repeated slug (the legitimate 'да' "
        f"duplicate); found instead: {collisions}"
    )
    da_words = collisions[da_slug]
    assert da_words == ["да", "да"], (
        f"the one expected duplicate slug must come from two IDENTICAL "
        f"occurrences of 'да' (same word, same audio) -- got {da_words}, "
        f"which would mean a GENUINE collision between different words."
    )

    # The headline number, asserted on the actual count -- 152 rows, one
    # legitimate duplicate pair, so 151 distinct slugs.
    assert len(set(slugs)) == 151

    # The specific hazard named in the request: "/" cannot appear in a
    # filename at all, and must never survive sanitization.
    assert all("/" not in s for s in slugs)


# ---------------------------------------------------------------------------
# Voice settings validation -- raise, never clamp
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", [0.0, 0.5, 0.85, 1.0])
def test_validate_voice_setting_accepts_the_full_valid_range(value):
    validate_voice_setting("stability", value)  # must not raise


@pytest.mark.parametrize("value", [-0.01, 1.01, 2.0, 85, 100])
def test_validate_voice_setting_rejects_out_of_range_values(value):
    with pytest.raises(ValueError):
        validate_voice_setting("stability", value)


def test_validate_voice_setting_gives_a_percent_hint_for_a_typo_like_85():
    with pytest.raises(ValueError, match=r"did you mean 0\.85"):
        validate_voice_setting("stability", 85)


def test_validate_voice_setting_never_clamps():
    # A clamp would silently turn 85 into 1.0 and return normally instead
    # of raising -- this is the exact failure mode the coordinator called
    # out by name ("do not silently clamp").
    with pytest.raises(ValueError):
        validate_voice_setting("similarity_boost", 85)


def test_validate_voice_setting_rejects_non_numeric_values():
    with pytest.raises(ValueError):
        validate_voice_setting("stability", "0.85")


def test_validate_voice_setting_rejects_booleans():
    # bool is a subclass of int in Python; True/False must not silently
    # pass as 1/0.
    with pytest.raises(ValueError):
        validate_voice_setting("stability", True)


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
    assert results[0].path.endswith("_f1.mp3")
    assert budget.spent == 1


def test_build_and_save_explicit_all_voices_writes_four_files(tmp_path):
    out_dir = str(tmp_path / "audio")
    responses = [FakeResponse(200, content=f"audio-{i}".encode()) for i in range(4)]
    session = _mock_session(responses)
    budget = RequestBudget(limit=4)

    results = build_and_save(
        "на",
        dir_name=out_dir,
        api_key="k",
        session=session,
        budget=budget,
        voices=VOICES,  # explicit opt-in to all four, direct-import style
    )

    assert len(results) == 4
    assert session.post.call_count == 4
    called_voice_ids = [
        c.args[0].rsplit("/", 1)[-1] for c in session.post.call_args_list
    ]
    assert called_voice_ids == [v.voice_id for v in VOICES]
    assert budget.spent == 4


def test_build_and_save_sends_default_voice_settings_in_the_payload(tmp_path):
    session = _mock_session([FakeResponse(200, content=b"audio")])
    build_and_save(
        "на",
        dir_name=str(tmp_path),
        api_key="k",
        session=session,
        budget=RequestBudget(1),
    )
    sent_json = session.post.call_args.kwargs["json"]
    assert sent_json["voice_settings"] == {
        "stability": DEFAULT_STABILITY,
        "similarity_boost": DEFAULT_SIMILARITY_BOOST,
    }


def test_build_and_save_sends_custom_voice_settings_in_the_payload(tmp_path):
    session = _mock_session([FakeResponse(200, content=b"audio")])
    build_and_save(
        "на",
        dir_name=str(tmp_path),
        api_key="k",
        session=session,
        budget=RequestBudget(1),
        stability=0.9,
        similarity_boost=0.8,
    )
    sent_json = session.post.call_args.kwargs["json"]
    assert sent_json["voice_settings"] == {"stability": 0.9, "similarity_boost": 0.8}


def test_build_and_save_rejects_invalid_stability_before_any_request(tmp_path):
    session = _mock_session([FakeResponse(200, content=b"audio")])
    budget = RequestBudget(limit=1)
    with pytest.raises(ValueError):
        build_and_save(
            "на",
            dir_name=str(tmp_path),
            api_key="k",
            session=session,
            budget=budget,
            stability=85,  # the exact typo the coordinator called out
        )
    assert session.post.call_count == 0
    assert budget.spent == 0


def test_build_and_save_rejects_invalid_similarity_boost_before_any_request(tmp_path):
    session = _mock_session([FakeResponse(200, content=b"audio")])
    budget = RequestBudget(limit=1)
    with pytest.raises(ValueError):
        build_and_save(
            "на",
            dir_name=str(tmp_path),
            api_key="k",
            session=session,
            budget=budget,
            similarity_boost=-1.0,
        )
    assert session.post.call_count == 0
    assert budget.spent == 0


def test_fetch_tts_audio_metered_validates_before_spending_the_budget():
    session = _mock_session([FakeResponse(200, content=b"audio")])
    budget = RequestBudget(limit=1)
    with pytest.raises(ValueError):
        fetch_tts_audio_metered(
            VOICES[0],
            "на",
            DEFAULT_MODEL_ID,
            "k",
            budget,
            session=session,
            stability=2.0,
        )
    assert budget.spent == 0  # validation failed before budget.spend() ran
    assert session.post.call_count == 0


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
    # 4 voices requested for one word, but the budget only allows 1: the
    # first (word, voice) pair must succeed, the second must raise instead
    # of proceeding, and the network must never be touched a second time.
    session = _mock_session(
        [
            FakeResponse(200, b"a"),
            FakeResponse(200, b"b"),
            FakeResponse(200, b"c"),
            FakeResponse(200, b"d"),
        ]
    )
    budget = RequestBudget(limit=1)  # deliberately smaller than the 4 voices below

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
# Retry / backoff, including 429 handling (unaffected by the budget/voice-
# settings changes: a retried request is still only ONE spend against the
# budget, and voice_settings ride along unchanged on every retry)
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
    assert args.stability == DEFAULT_STABILITY
    assert args.similarity_boost == DEFAULT_SIMILARITY_BOOST


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


def test_stability_and_similarity_boost_flags_parse():
    parser = build_parser()
    args = parser.parse_args(
        ["--word", "на", "--stability", "0.9", "--similarity-boost", "0.7"]
    )
    assert args.stability == 0.9
    assert args.similarity_boost == 0.7


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
    assert "Alisa" in out  # the voice involved is printed by name


def test_2_all_voices_on_one_word_issues_exactly_four_requests(
    tmp_path, monkeypatch, capsys
):
    """Required test #2 (roster grew from 3 to 4 voices; the property under
    test -- --all-voices widens to the WHOLE roster -- is unchanged):
    --all-voices on one word issues exactly len(VOICES) requests."""
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    responses = [
        FakeResponse(200, content=f"a{i}".encode()) for i in range(len(VOICES))
    ]
    session = _patch_session(monkeypatch, responses)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")  # 4 > threshold

    rc = main(["--word", "на", "--all-voices", "--output-dir", "out"])

    assert rc == 0
    assert session.post.call_count == len(VOICES) == 4
    out = capsys.readouterr().out
    assert f"About to issue {len(VOICES)} ElevenLabs request(s)" in out
    assert (
        "Elena Gromova" in out and "Mishka Yaponcik" in out and "Nester Surovy" in out
    )


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
    assert session.post.call_count == 1  # not 5, not 20 -- exactly 1
    out = capsys.readouterr().out
    assert "1 word(s) (of 5 available)" in out


def test_3b_all_voices_alone_does_not_start_walking_the_word_list(
    tmp_path, monkeypatch, capsys
):
    """--all-voices given alone (no --all/--count) must widen the voice
    axis only, never the word axis: 1 word x 4 voices = 4, not 5 x 4 = 20."""
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n".join(["в", "на", "с", "по", "к"]), encoding="utf-8")
    responses = [
        FakeResponse(200, content=f"a{i}".encode()) for i in range(len(VOICES))
    ]
    session = _patch_session(monkeypatch, responses)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")

    rc = main(["--file", str(words_file), "--all-voices", "--output-dir", "out"])

    assert rc == 0
    assert (
        session.post.call_count == len(VOICES) == 4
    )  # 1 word x 4 voices, word list NOT walked
    out = capsys.readouterr().out
    assert "1 word(s) (of 5 available)" in out


def test_4_a_would_exceed_the_cap_path_raises_rather_than_proceeding(tmp_path):
    """Required test #4: a "would exceed the cap" path raises rather than
    proceeding. Exercised directly against the structural choke point
    (RequestBudget/build_and_save), independent of the CLI's own printed
    count and confirmation prompt (covered separately below)."""
    session = _mock_session(
        [
            FakeResponse(200, b"a"),
            FakeResponse(200, b"b"),
            FakeResponse(200, b"c"),
            FakeResponse(200, b"d"),
        ]
    )
    budget = RequestBudget(limit=1)  # deliberately smaller than the 4 voices below

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
# CLI: main() -- remaining coverage (opt-in composition, --yes, missing key,
# voice_settings flags)
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
    assert session.post.call_count == 2  # 2 words x 1 voice, NOT x 4


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
        monkeypatch,
        [FakeResponse(200, content=f"a{i}".encode()) for i in range(2 * len(VOICES))],
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")

    rc = main(
        ["--file", str(words_file), "--all", "--all-voices", "--output-dir", "out"]
    )

    assert rc == 0
    assert session.post.call_count == 2 * len(VOICES)  # both axes explicitly widened


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


def test_cli_rejects_out_of_range_stability_before_touching_the_network(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    session = _patch_session(monkeypatch, [])

    with pytest.raises(SystemExit):
        main(["--word", "на", "--stability", "85", "--output-dir", "out"])

    assert session.post.call_count == 0  # rejected before any word list load or spend


def test_cli_stability_and_similarity_boost_flags_reach_the_request(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    session = _patch_session(monkeypatch, [FakeResponse(200, content=b"audio")])

    rc = main(
        [
            "--word",
            "на",
            "--stability",
            "0.9",
            "--similarity-boost",
            "0.7",
            "--output-dir",
            "out",
        ]
    )

    assert rc == 0
    sent_json = session.post.call_args.kwargs["json"]
    assert sent_json["voice_settings"] == {"stability": 0.9, "similarity_boost": 0.7}
