"""Tests for anki_tools.elevenlabs_tts (Phase 4, subphase 4.1, lane 2).

Every test in this file is fully offline: `requests.Session.post` (and the
bare `requests.post`) are monkeypatched, module-wide, to blow up if actually
called -- a test that forgets to inject its own fake session fails loudly
instead of silently reaching the real ElevenLabs API and spending money.
Nothing here ever imports or touches a real network socket.
"""

import json
import os

import pytest
import requests

from anki_tools.elevenlabs_tts import (
    API_KEY_ENV_VAR,
    DEFAULT_MODEL_ID,
    DEFAULT_WORD_LIMIT,
    VOICES,
    ElevenLabsAPIError,
    MissingAPIKeyError,
    RateLimitedError,
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
# Voice roster (D5)
# ---------------------------------------------------------------------------


def test_voices_are_exactly_the_three_settled_russian_voices():
    assert [v.voice_id for v in VOICES] == [
        "TPIitICAZ8CqlGZ81AKm",
        "RLRdvNFwJJct2XZOgfzy",
        "pM78bgjPVk0JXtaEnFoj",
    ]
    assert all(isinstance(v, Voice) for v in VOICES)


# ---------------------------------------------------------------------------
# build_and_save: happy path, skip-if-exists, replace
# ---------------------------------------------------------------------------


def test_build_and_save_writes_one_file_per_voice(tmp_path):
    out_dir = str(tmp_path / "audio")
    responses = [
        FakeResponse(status_code=200, content=f"audio-{i}".encode()) for i in range(3)
    ]
    session = FakeSession(responses)

    results = build_and_save("на", dir_name=out_dir, api_key="k", session=session)

    assert len(results) == 3
    assert len(session.calls) == 3
    for result in results:
        assert not result.skipped
        assert os.path.isfile(result.path)
    # Every call hit a distinct voice_id in the fixed roster, in order.
    called_voice_ids = [c["url"].rsplit("/", 1)[-1] for c in session.calls]
    assert called_voice_ids == [v.voice_id for v in VOICES]


def test_build_and_save_skips_existing_file_by_default(tmp_path):
    out_dir = str(tmp_path / "audio")
    session = FakeSession(
        [FakeResponse(200, b"a"), FakeResponse(200, b"b"), FakeResponse(200, b"c")]
    )
    build_and_save("на", dir_name=out_dir, api_key="k", session=session)
    assert len(session.calls) == 3

    # Second run: nothing should be requested again.
    session2 = FakeSession([])
    results = build_and_save("на", dir_name=out_dir, api_key="k", session=session2)
    assert all(r.skipped for r in results)
    assert len(session2.calls) == 0


def test_build_and_save_replace_forces_regeneration(tmp_path):
    out_dir = str(tmp_path / "audio")
    session = FakeSession(
        [FakeResponse(200, b"a"), FakeResponse(200, b"b"), FakeResponse(200, b"c")]
    )
    build_and_save("на", dir_name=out_dir, api_key="k", session=session)

    session2 = FakeSession(
        [FakeResponse(200, b"a2"), FakeResponse(200, b"b2"), FakeResponse(200, b"c2")]
    )
    results = build_and_save(
        "на", dir_name=out_dir, api_key="k", session=session2, replace=True
    )
    assert all(not r.skipped for r in results)
    assert len(session2.calls) == 3
    with open(results[0].path, "rb") as fh:
        assert fh.read() == b"a2"


def test_build_and_save_rejects_missing_api_key_before_any_request(
    tmp_path, monkeypatch
):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    session = FakeSession([])
    with pytest.raises(MissingAPIKeyError):
        build_and_save("на", dir_name=str(tmp_path), session=session)
    assert session.calls == []


def test_build_and_save_batch_covers_every_word_and_voice(tmp_path):
    out_dir = str(tmp_path / "audio")
    words = ["на", "по"]
    responses = [
        FakeResponse(200, f"x{i}".encode()) for i in range(len(words) * len(VOICES))
    ]
    session = FakeSession(responses)
    results = build_and_save_batch(
        words, dir_name=out_dir, api_key="k", session=session
    )
    assert len(results) == len(words) * len(VOICES)
    assert len(session.calls) == len(words) * len(VOICES)


# ---------------------------------------------------------------------------
# Retry / backoff, including 429 handling
# ---------------------------------------------------------------------------


def test_transient_500_is_retried_then_succeeds(tmp_path):
    session = FakeSession(
        [FakeResponse(500, text="boom"), FakeResponse(200, content=b"ok")]
    )
    results = build_and_save(
        "у", dir_name=str(tmp_path), api_key="k", session=session, voices=VOICES[:1]
    )
    assert len(session.calls) == 2
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
        "у", dir_name=str(tmp_path), api_key="k", session=session, voices=VOICES[:1]
    )
    assert len(session.calls) == 2
    assert sleep_calls == [2.5]


def test_exhausting_retries_on_persistent_500_raises(tmp_path):
    session = FakeSession([FakeResponse(500, text="down")] * 10)
    with pytest.raises(TransientServerError):
        build_and_save(
            "у", dir_name=str(tmp_path), api_key="k", session=session, voices=VOICES[:1]
        )


def test_non_retryable_4xx_raises_immediately_without_retrying(tmp_path):
    session = FakeSession([FakeResponse(401, text="unauthorized")])
    with pytest.raises(ElevenLabsAPIError):
        build_and_save(
            "у", dir_name=str(tmp_path), api_key="k", session=session, voices=VOICES[:1]
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
        "у", dir_name=str(tmp_path), api_key="k", session=session, voices=VOICES[:1]
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
# CLI: the hard cost limit is the point of this whole file
# ---------------------------------------------------------------------------


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["--word", "на"])
    assert args.model_id == DEFAULT_MODEL_ID
    assert args.all is False
    assert args.count is None


def test_count_and_all_are_mutually_exclusive():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--file", "x.txt", "--all", "--count", "3"])


def _install_fake_session(monkeypatch, n_responses):
    responses = [FakeResponse(200, content=b"a") for _ in range(n_responses)]
    session = FakeSession(responses)
    monkeypatch.setattr("anki_tools.elevenlabs_tts.requests.Session", lambda: session)
    return session


def test_default_run_is_exactly_one_word_times_three_voices(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    # 5 words available; default run must touch only the first one.
    words_file.write_text("\n".join(["в", "на", "с", "по", "к"]), encoding="utf-8")

    session = _install_fake_session(monkeypatch, n_responses=3)

    rc = main(["--file", str(words_file), "--output-dir", "out"])

    assert rc == 0
    assert len(session.calls) == 3  # exactly 1 word x 3 voices, never more
    out = capsys.readouterr().out
    assert "1 of 5" in out
    assert "3 ElevenLabs" in out
    assert DEFAULT_WORD_LIMIT == 1


def test_all_flag_opts_into_the_full_list(tmp_path, monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n".join(["в", "на"]), encoding="utf-8")

    session = _install_fake_session(monkeypatch, n_responses=2 * len(VOICES))
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")

    rc = main(["--file", str(words_file), "--all", "--output-dir", "out"])

    assert rc == 0
    assert len(session.calls) == 2 * len(VOICES)


def test_count_flag_opts_into_an_explicit_number(tmp_path, monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n".join(["в", "на", "с"]), encoding="utf-8")

    session = _install_fake_session(monkeypatch, n_responses=2 * len(VOICES))
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")

    rc = main(["--file", str(words_file), "--count", "2", "--output-dir", "out"])

    assert rc == 0
    assert len(session.calls) == 2 * len(VOICES)


def test_multi_word_run_requires_confirmation_and_aborts_on_no(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n".join(["в", "на"]), encoding="utf-8")

    session = _install_fake_session(monkeypatch, n_responses=0)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")

    rc = main(["--file", str(words_file), "--all", "--output-dir", "out"])

    assert rc == 1
    assert len(session.calls) == 0  # nothing was spent
    assert "Aborted" in capsys.readouterr().out


def test_yes_flag_skips_the_confirmation_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n".join(["в", "на"]), encoding="utf-8")

    session = _install_fake_session(monkeypatch, n_responses=2 * len(VOICES))

    def _boom_input(_prompt=""):
        raise AssertionError("input() must not be called when --yes is given")

    monkeypatch.setattr("builtins.input", _boom_input)

    rc = main(["--file", str(words_file), "--all", "--yes", "--output-dir", "out"])
    assert rc == 0
    assert len(session.calls) == 2 * len(VOICES)


def test_single_word_default_run_never_prompts(tmp_path, monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    monkeypatch.chdir(tmp_path)

    session = _install_fake_session(monkeypatch, n_responses=len(VOICES))

    def _boom_input(_prompt=""):
        raise AssertionError("a single-word default run must never prompt")

    monkeypatch.setattr("builtins.input", _boom_input)

    rc = main(["--word", "на", "--output-dir", "out"])
    assert rc == 0
    assert len(session.calls) == len(VOICES)


def test_missing_api_key_fails_before_touching_the_network(tmp_path, monkeypatch):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    monkeypatch.chdir(tmp_path)
    session = _install_fake_session(monkeypatch, n_responses=0)

    rc = main(["--word", "на", "--output-dir", "out"])

    assert rc == 1
    assert len(session.calls) == 0


def test_word_and_file_are_mutually_exclusive(tmp_path):
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--word", "на", "--file", "x.txt"])


def test_neither_word_nor_file_is_an_error(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "k")
    with pytest.raises(SystemExit):
        main([])
