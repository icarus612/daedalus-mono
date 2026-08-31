#!/usr/bin/env python3
"""Text -> speech via the ElevenLabs API, for Russian Anki-card audio.

Standalone and Anki-agnostic: this module knows nothing about decks, notes,
or `.apkg` packages -- given a Russian string it produces one `.mp3` per
configured voice. Wiring the resulting files onto Anki notes is a later
integration concern, not this module's.

Shape follows `web_crawlers/anki_scrapers/text_to_speech/basic_google_TTS.py`
(a `build_and_save(...)` entry point plus a retry/backoff decorator) and
`anki_tools/rebalance_due.py` for the `argparse` CLI conventions
(`build_parser()` kept separate from `main()` so both are testable).

Voices: the account is on a paid plan and has five verified Russian voices
(`GET /v2/voices`); the other ~21 voices on the account are premade English
and must never be used here. The default ROSTER is four of the five, one
per "slot" -- the slot, not the voice name, is the filename identity:

    f1  Alisa - Natural Russian Female
    f2  Elena Gromova - Podcasts & Conversation
    m1  Mishka Yaponcik - Odessa Rogue Charm
    m2  Nester Surovy - Gravely yet Refined

A fifth voice, Elen Kuragina ("Golden & Dangerous"), is a character voice
displaced from the default roster by the two clearer female voices above;
it stays defined in this module (see `ELEN_KURAGINA`) for explicit,
non-default use, and is never included in `VOICES`/`ALL_VOICES` iteration
by default.

Every synthesis call sends a `voice_settings` object (`stability`,
`similarity_boost`, both 0.0-1.0 per ElevenLabs' API, default 0.85/0.85).
Out-of-range values RAISE rather than clamp -- a typo like `85` instead of
`0.85` must fail loudly, never silently coerce into something that looks
plausible.

THE HARD COST LIMIT -- the strictest reading, not the convenient one: a
default run produces exactly ONE `.mp3`. One word, one voice (the first
slot, `f1`/Alisa), one request. Two independent opt-ins widen it, and
neither implies the other:

  --all-voices   the same word(s), across all four roster voices instead
                 of one.
  --all/--count  more than one word from --file, still one voice unless
                 --all-voices is ALSO given.

This is enforced structurally, not by convention: every actual HTTP call
this module ever makes funnels through `fetch_tts_audio_metered`, which
takes a REQUIRED `RequestBudget` and calls `budget.spend(1)` before issuing
anything. There is no default that lets a caller -- CLI, `build_and_save`,
`build_and_save_batch`, or a bare import -- skip declaring how many requests
it is allowed to make; exceeding the declared budget raises
`BudgetExceededError` instead of silently proceeding, regardless of how the
word/voice lists upstream were constructed.

Filenames are `<word>_<slot>.mp3` (e.g. `около_f1.mp3`) -- readable, no
hash suffix. This is safe ONLY because it has been verified collision-free
against the real 152-row source word list (see
`test_slug_collision_free_across_real_source_word_list`); the one
"collision" that DOES occur ("да", appearing twice with identical text
under two different parts of speech) is a genuine duplicate, not a
collision, and correctly shares one file. If the source list ever grows to
include two genuinely DIFFERENT strings that sanitize to the same slug,
that must be reported and resolved explicitly -- never silently patched by
re-adding a hash to every filename.
"""

import argparse
import functools
import json
import os
import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import requests

API_BASE_URL = "https://api.elevenlabs.io/v1"
API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"

# D2/D3 conventions: no time estimates, no literal secrets. The key is read
# from the environment ONLY -- never a CLI flag (shell history), never
# logged, never interpolated into an error message.

DEFAULT_OUTPUT_DIR = "audio_files"

# eleven_multilingual_v2 is ElevenLabs' documented multilingual model and the
# one they recommend for non-English text (including Russian); their
# English-only models (e.g. eleven_monolingual_v1) are not suitable here.
# Trivially overridable via --model-id.
DEFAULT_MODEL_ID = "eleven_multilingual_v2"

DEFAULT_TIMEOUT = 30  # seconds, per HTTP request

# The hard limit (see module docstring): a default run touches exactly one
# word. Anything beyond this requires an explicit --all/--count opt-in.
DEFAULT_WORD_LIMIT = 1

# And, independently, exactly one voice per word by default. Requesting the
# other three is the SEPARATE --all-voices opt-in -- it must never be
# implied by --all/--count, and vice versa.
DEFAULT_VOICE_LIMIT = 1

# Anything above this many total requests (words x voices) requires either
# --yes or an interactive confirmation before a single request is issued.
CONFIRM_ABOVE_REQUESTS = 1

# ElevenLabs' `voice_settings.stability`/`similarity_boost`, both in
# [0.0, 1.0]. 0.85/0.85 is a safely mid-range default per the user's
# direction; NEVER clamped -- see `validate_voice_setting`.
DEFAULT_STABILITY = 0.85
DEFAULT_SIMILARITY_BOOST = 0.85

DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_INITIAL_BACKOFF = 1.0
DEFAULT_MAX_BACKOFF = 40.0


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ElevenLabsTTSError(Exception):
    """Base class for every error this module raises."""


class MissingAPIKeyError(ElevenLabsTTSError):
    """`ELEVENLABS_API_KEY` is unset. Raised before any network call."""


class ElevenLabsAPIError(ElevenLabsTTSError):
    """A non-retryable error response from the ElevenLabs API."""


class BudgetExceededError(ElevenLabsTTSError):
    """Raised when a caller tries to spend past its declared `RequestBudget`.

    This is a structural stop, not a bug report: it fires whenever ANY code
    path -- CLI, batch helper, or direct import -- attempts to issue more
    requests than were explicitly declared allowed, regardless of how the
    word/voice lists that led to the attempt were built.
    """


class _RetryableTTSError(ElevenLabsTTSError):
    """Base for transient failures the retry decorator will retry."""

    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class RateLimitedError(_RetryableTTSError):
    """HTTP 429 from ElevenLabs -- handled specifically, per the contract."""


class TransientServerError(_RetryableTTSError):
    """A 5xx response, or a network-level failure (timeout, connection)."""


# ---------------------------------------------------------------------------
# Voices
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Voice:
    name: str
    voice_id: str
    slug: str
    gender: str
    slot: str  # the filename identity -- f1/f2/m1/m2 (or f0 for the retired
    # non-default Elen Kuragina). Must be unique across any roster this
    # module iterates; see `_check_unique_slots` below.


VOICES: tuple = (
    # f1: Alisa - Natural Russian Female
    Voice(
        name="Alisa - Natural Russian Female",
        voice_id="t6lBrEl93uCiLR1Lgm8v",
        slug="alisa",
        gender="female",
        slot="f1",
    ),
    # f2: Elena Gromova - Podcasts & Conversation
    Voice(
        name="Elena Gromova - Podcasts & Conversation",
        voice_id="0ArNnoIAWKlT4WweaVMY",
        slug="elena-gromova",
        gender="female",
        slot="f2",
    ),
    # m1: Mishka Yaponcik - Odessa Rogue Charm
    Voice(
        name="Mishka Yaponcik - Odessa Rogue Charm",
        voice_id="RLRdvNFwJJct2XZOgfzy",
        slug="mishka-yaponcik",
        gender="male",
        slot="m1",
    ),
    # m2: Nester Surovy - Gravely yet Refined
    Voice(
        name="Nester Surovy - Gravely yet Refined",
        voice_id="pM78bgjPVk0JXtaEnFoj",
        slug="nester-surovy",
        gender="male",
        slot="m2",
    ),
)

# A character voice, displaced from the default roster by the two clearer
# female voices above -- kept defined, never deleted, for explicit,
# non-default use only (never iterated by `VOICES`, `DEFAULT_VOICES`, or
# `--all-voices`). Given its own slot ("f0") so it still composes cleanly
# with the `[word]_[slot].mp3` filename scheme if a caller opts into it
# directly.
ELEN_KURAGINA = Voice(
    name="Elen Kuragina - Golden & Dangerous",
    voice_id="TPIitICAZ8CqlGZ81AKm",
    slug="elen-kuragina",
    gender="female",
    slot="f0",
)

# Every voice this module knows about, default roster plus the retired one.
ALL_VOICES: tuple = VOICES + (ELEN_KURAGINA,)


def _check_unique_slots(voices: Sequence[Voice]) -> None:
    """Make it structurally impossible for two voices to share a slot.

    The slot is the filename identity now (`build_filename` uses
    `voice.slot`, not `voice.slug`), so a duplicate slot would silently
    make two different voices overwrite each other's files. Raises
    `ValueError` -- not a bare `assert`, which `python -O` would strip --
    so this check cannot be silently disabled.
    """
    slots = [v.slot for v in voices]
    if len(slots) != len(set(slots)):
        dupes = sorted({s for s in slots if slots.count(s) > 1})
        raise ValueError(f"Voice roster has duplicate slot(s): {dupes}")


# Runs at import time: a future edit that introduces a duplicate slot
# breaks the whole module immediately, not just whichever code path
# happens to hit it first.
_check_unique_slots(ALL_VOICES)

# The default voice touched when the caller doesn't opt into --all-voices --
# always the first roster slot, f1/Alisa. Trivially widened to the full
# roster by passing `voices=VOICES` explicitly (direct import) or
# `--all-voices` (CLI); never the other way around.
DEFAULT_VOICES: tuple = VOICES[:DEFAULT_VOICE_LIMIT]


@dataclass(frozen=True)
class SynthesisResult:
    word: str
    voice: Voice
    path: str
    skipped: bool


# ---------------------------------------------------------------------------
# Request budget -- THE single choke point for real ElevenLabs spend
# ---------------------------------------------------------------------------


class RequestBudget:
    """The one gate every real ElevenLabs request must pass through.

    Deliberately not a default-argument convention: `limit` has no default
    here either, and `fetch_tts_audio_metered` (the sole function that
    actually calls `_fetch_tts_audio`) requires a `RequestBudget` instance
    with no fallback to "unlimited". A caller -- CLI, `build_and_save`,
    `build_and_save_batch`, or a bare import -- that wants more than one
    request must construct (or receive) a budget sized for that, explicitly.
    Exceeding it raises `BudgetExceededError` immediately, before any
    further network call is attempted, rather than silently proceeding.
    """

    def __init__(self, limit: int):
        if limit < 0:
            raise ValueError(f"RequestBudget limit must be >= 0, got {limit}")
        self.limit = limit
        self.spent = 0

    def spend(self, n: int = 1) -> None:
        if self.spent + n > self.limit:
            raise BudgetExceededError(
                f"request budget exceeded: attempting request "
                f"{self.spent + n} against a cap of {self.limit}. This is a "
                f"deliberate stop, not a bug -- construct a larger "
                f"RequestBudget (or pass --all-voices / --all / --count on "
                f"the CLI) to explicitly allow more spend."
            )
        self.spent += n

    def remaining(self) -> int:
        return self.limit - self.spent


# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------


def get_api_key() -> str:
    """Read the ElevenLabs API key from the environment.

    Never accepts the key as a literal or a CLI flag (it would land in shell
    history) and never logs it. Fails loudly, before any network call, with
    a message naming the variable rather than a traceback.
    """
    api_key = os.environ.get(API_KEY_ENV_VAR)
    if not api_key:
        raise MissingAPIKeyError(
            f"{API_KEY_ENV_VAR} is not set. Export it (it is already staged "
            f"in the gitignored repo-root .env) before running this tool -- "
            f"no ElevenLabs request will be made without it."
        )
    return api_key


def validate_voice_setting(name: str, value) -> None:
    """Raise if `value` is outside ElevenLabs' accepted [0.0, 1.0] range for
    `stability`/`similarity_boost`.

    Deliberately RAISES rather than clamps: silently coercing an
    out-of-range value (e.g. clamping `85` to `1.0`) would make a `0.85`-vs-
    `85` typo look like it worked while actually sending the wrong voice
    setting to every request. A typo here must fail loudly, before any
    network call, not get "fixed" into something that looks plausible.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number in [0.0, 1.0], got {value!r}")
    if not (0.0 <= value <= 1.0):
        hint = ""
        if 1.0 < value <= 100.0:
            hint = f" (did you mean {value / 100.0}?)"
        raise ValueError(
            f"{name} must be between 0.0 and 1.0 -- the range ElevenLabs' "
            f"API accepts -- got {value!r}{hint}. This is never clamped: a "
            f"typo like 85 instead of 0.85 must fail loudly."
        )


# ---------------------------------------------------------------------------
# Filename sanitization -- readable, verified collision-free
# ---------------------------------------------------------------------------

# Cyrillic letters, digits, and underscore all count as "word" characters
# under Python's unicode-aware \w, so the source text survives intact; every
# run of anything else (spaces, "/", ",", ".", quotes, ...) collapses to a
# single hyphen. This alone makes "/" -- which cannot appear in a filename
# at all -- disappear along with every other filesystem-hostile character.
_UNSAFE_RUN = re.compile(r"[^\w\-]+", re.UNICODE)
_MULTI_HYPHEN = re.compile(r"-{2,}")


def sanitize_word_slug(word: str) -> str:
    """Turn a Russian word/phrase into a filesystem-safe, readable slug.

    No hash suffix, by design (the user asked for `[word]_[slot].mp3`, not
    an opaque hash) -- but that is safe ONLY because it has been VERIFIED
    collision-free across the real 152-row source word list, including the
    genuinely awkward rows ("в / во", "ни... ни...", "-то", "несмотря на то,
    что", ...): see `test_slug_collision_free_across_real_source_word_list`.
    The one repeated slug that DOES occur ("да", appearing twice with
    identical text under two different parts of speech) is a legitimate
    duplicate -- same word, same audio, correctly sharing one file -- not a
    collision between two different words.

    If a future word list ever produces a genuine collision (two DIFFERENT
    strings sanitizing to the same slug), that must be reported and
    resolved explicitly, never silently patched by re-adding a hash here.
    """
    normalized = unicodedata.normalize("NFC", word.strip())
    slug = _UNSAFE_RUN.sub("-", normalized)
    slug = _MULTI_HYPHEN.sub("-", slug).strip("-")
    if not slug:
        slug = "word"
    return slug


def build_filename(word: str, voice: Voice, dir_name: str = DEFAULT_OUTPUT_DIR) -> str:
    """The path for one (word, voice) pair's .mp3: `<word-slug>_<slot>.mp3`
    (e.g. `около_f1.mp3`). The slot, not the voice's slug/name, is the
    filename identity -- see `Voice.slot` and `_check_unique_slots`."""
    word_slug = sanitize_word_slug(word)
    return os.path.join(dir_name, f"{word_slug}_{voice.slot}.mp3")


# ---------------------------------------------------------------------------
# Retry / backoff
# ---------------------------------------------------------------------------


def _retry_with_backoff(
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    initial_backoff: float = DEFAULT_INITIAL_BACKOFF,
    max_backoff: float = DEFAULT_MAX_BACKOFF,
) -> Callable:
    """Exponential backoff on `_RetryableTTSError`, honoring `Retry-After`.

    Mirrors the shape of `basic_google_TTS.py`'s `@retry(...)` decorator,
    reimplemented locally: `retrying`/`tenacity` are not declared
    dependencies of this package and `requests` alone is preferred per the
    contract, so adding one of those packages just for this would not be
    justified. Uses `time.sleep` directly (monkeypatched in tests) rather
    than a real wait, so retry behavior is tested without slowing the suite.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            backoff = initial_backoff
            last_exc: Optional[_RetryableTTSError] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except _RetryableTTSError as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        break
                    wait_s = exc.retry_after if exc.retry_after else backoff
                    print(
                        f"[elevenlabs_tts] transient error on attempt "
                        f"{attempt}/{max_attempts}: {exc}; retrying in "
                        f"{wait_s:.1f}s"
                    )
                    time.sleep(wait_s)
                    backoff = min(backoff * 2, max_backoff)
            raise last_exc

        return wrapper

    return decorator


@_retry_with_backoff()
def _fetch_tts_audio(
    voice_id: str,
    text: str,
    model_id: str,
    api_key: str,
    stability: float,
    similarity_boost: float,
    session=None,
    timeout: int = DEFAULT_TIMEOUT,
) -> bytes:
    """One HTTP call to ElevenLabs. Raises on any non-2xx response.

    `session` is an injected `requests.Session` (or any object exposing a
    `.post` matching its signature) so callers can reuse a connection across
    a batch, and so tests can substitute a mock with zero real HTTP.

    `stability`/`similarity_boost` are sent as ElevenLabs' `voice_settings`
    object, verbatim -- they are validated by the caller
    (`fetch_tts_audio_metered`) before this function is ever reached, so
    this layer trusts them and only builds the request.
    """
    client = session if session is not None else requests
    url = f"{API_BASE_URL}/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
        },
    }

    try:
        response = client.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.exceptions.RequestException as exc:
        raise TransientServerError(
            f"network error calling ElevenLabs for voice {voice_id!r}: {exc}"
        ) from exc

    if response.status_code == 429:
        retry_after_header = response.headers.get("Retry-After")
        retry_after = None
        if retry_after_header:
            try:
                retry_after = float(retry_after_header)
            except ValueError:
                retry_after = None
        raise RateLimitedError(
            f"ElevenLabs rate-limited the request for voice {voice_id!r} (429).",
            retry_after=retry_after,
        )

    if 500 <= response.status_code < 600:
        raise TransientServerError(
            f"ElevenLabs returned a server error {response.status_code} for "
            f"voice {voice_id!r}."
        )

    if response.status_code != 200:
        raise ElevenLabsAPIError(
            f"ElevenLabs returned {response.status_code} for voice "
            f"{voice_id!r}: {response.text[:200]!r}"
        )

    return response.content


def fetch_tts_audio_metered(
    voice: Voice,
    text: str,
    model_id: str,
    api_key: str,
    budget: RequestBudget,
    session=None,
    timeout: int = DEFAULT_TIMEOUT,
    stability: float = DEFAULT_STABILITY,
    similarity_boost: float = DEFAULT_SIMILARITY_BOOST,
) -> bytes:
    """THE single choke point: the only function in this module that is
    allowed to actually issue a real ElevenLabs request.

    `budget` is a REQUIRED positional-adjacent argument with no default --
    there is no way to call this function without declaring, up front, how
    many requests are allowed. `stability`/`similarity_boost` are validated
    (raising, never clamping) BEFORE `budget.spend(1)`, so a bad voice
    setting fails before any budget is consumed, let alone any network call
    made. `build_and_save` (and therefore `build_and_save_batch` and
    `main`) is the only other code in this module that calls this function;
    anything that wants to synthesize audio funnels through here.
    """
    validate_voice_setting("stability", stability)
    validate_voice_setting("similarity_boost", similarity_boost)
    budget.spend(1)
    return _fetch_tts_audio(
        voice.voice_id,
        text,
        model_id,
        api_key,
        stability,
        similarity_boost,
        session=session,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------


def build_and_save(
    word: str,
    *,
    budget: RequestBudget,
    dir_name: str = DEFAULT_OUTPUT_DIR,
    voices: Sequence[Voice] = DEFAULT_VOICES,
    model_id: str = DEFAULT_MODEL_ID,
    replace: bool = False,
    api_key: Optional[str] = None,
    session=None,
    stability: float = DEFAULT_STABILITY,
    similarity_boost: float = DEFAULT_SIMILARITY_BOOST,
) -> list:
    """Synthesize ONE word across every voice in `voices`.

    `voices` defaults to `DEFAULT_VOICES` -- exactly ONE voice (the f1 slot,
    Alisa). Passing `voices=VOICES` (all four) is itself the explicit opt-in
    for a direct-import caller; the CLI's `--all-voices` is the equivalent
    opt-in on that surface. `budget` is required (see
    `fetch_tts_audio_metered`) -- there is no way to call this and
    accidentally issue more requests than `budget.limit` allows.

    Skips a (word, voice) pair whose file already exists unless `replace` is
    set, so a resumed run is cheap and idempotent (skipped pairs never touch
    `budget` at all -- nothing is spent on them). Returns one
    `SynthesisResult` per voice, generated or skipped.
    """
    validate_voice_setting("stability", stability)
    validate_voice_setting("similarity_boost", similarity_boost)
    api_key = api_key or get_api_key()
    os.makedirs(dir_name, exist_ok=True)

    results = []
    for voice in voices:
        file_name = build_filename(word, voice, dir_name=dir_name)
        if not replace and os.path.isfile(file_name):
            print(f"Skip (exists): {file_name}")
            results.append(
                SynthesisResult(word=word, voice=voice, path=file_name, skipped=True)
            )
            continue

        audio_bytes = fetch_tts_audio_metered(
            voice,
            word,
            model_id,
            api_key,
            budget,
            session=session,
            stability=stability,
            similarity_boost=similarity_boost,
        )
        with open(file_name, "wb") as fh:
            fh.write(audio_bytes)
        print(f"Saved: {file_name} (voice: {voice.name})")
        results.append(
            SynthesisResult(word=word, voice=voice, path=file_name, skipped=False)
        )
    return results


def build_and_save_batch(
    words: Sequence[str],
    *,
    budget: RequestBudget,
    dir_name: str = DEFAULT_OUTPUT_DIR,
    voices: Sequence[Voice] = DEFAULT_VOICES,
    model_id: str = DEFAULT_MODEL_ID,
    replace: bool = False,
    api_key: Optional[str] = None,
    session=None,
    stability: float = DEFAULT_STABILITY,
    similarity_boost: float = DEFAULT_SIMILARITY_BOOST,
) -> list:
    """Synthesize many words, each across every voice in `voices`.

    `budget` is shared across the WHOLE batch (every word funnels through
    the same `RequestBudget` instance), so it caps total spend across the
    entire call regardless of how many words or voices were passed in --
    including a bug that duplicates an entry in `words` or `voices`. There
    is no default that lets this function -- or `main()`, which is its only
    caller -- issue more requests than `budget.limit` without that having
    been explicitly raised beforehand.
    """
    validate_voice_setting("stability", stability)
    validate_voice_setting("similarity_boost", similarity_boost)
    api_key = api_key or get_api_key()
    session = session if session is not None else requests.Session()
    results = []
    for word in words:
        results.extend(
            build_and_save(
                word,
                budget=budget,
                dir_name=dir_name,
                voices=voices,
                model_id=model_id,
                replace=replace,
                api_key=api_key,
                session=session,
                stability=stability,
                similarity_boost=similarity_boost,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Word-list loading
# ---------------------------------------------------------------------------


def load_words_from_file(file_path: str) -> list:
    """Load words from a plain-text file (one per line, `#`-comments
    allowed) or a `.json` file holding a JSON list of strings."""
    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            raise ValueError(f"{file_path}: JSON word file must be a list of strings.")
        return [str(item).strip() for item in data if str(item).strip()]

    words = []
    with open(file_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            words.append(line)
    return words


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anki-elevenlabs-tts",
        description=(
            "Synthesize Russian text to speech via ElevenLabs. The default "
            "run produces exactly ONE .mp3 -- one word, one voice (f1, "
            "Alisa) -- and stops. --all-voices opts into the same word(s) "
            "across all four roster voices; --all/--count opt into more "
            "than one word from --file. Neither implies the other."
        ),
    )
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--word",
        "-w",
        type=str,
        default=None,
        help="A single Russian word/phrase to synthesize.",
    )
    target_group.add_argument(
        "--file",
        "-f",
        type=str,
        default=None,
        help=(
            "A word list: a plain-text file with one word per line "
            "('#'-comments allowed), or a .json file holding a JSON list "
            "of strings."
        ),
    )
    count_group = parser.add_mutually_exclusive_group()
    count_group.add_argument(
        "--all",
        action="store_true",
        default=False,
        help=(
            "Process every word in --file, not just the first one. "
            "Independent of --all-voices -- combine them explicitly if you "
            "want both axes widened. Spends real ElevenLabs credits for "
            "every word -- see the request count printed before the "
            "confirmation prompt."
        ),
    )
    count_group.add_argument(
        "--count",
        "-n",
        type=int,
        default=None,
        help=(
            "Process exactly this many words from --file (an explicit "
            "opt-in override of the default 1-word limit). Mutually "
            "exclusive with --all; independent of --all-voices."
        ),
    )
    parser.add_argument(
        "--all-voices",
        dest="all_voices",
        action="store_true",
        default=False,
        help=(
            "Synthesize each selected word in all four roster voices "
            "instead of just the default one (f1, Alisa). Independent of "
            "--all/--count -- given alone, it does NOT start walking a "
            "--file word list; it only widens the voice axis for whichever "
            "word(s) --all/--count already selected."
        ),
    )
    parser.add_argument(
        "--stability",
        type=float,
        default=DEFAULT_STABILITY,
        help=(
            f"ElevenLabs voice_settings.stability, 0.0-1.0. Default: "
            f"{DEFAULT_STABILITY}. Never clamped -- an out-of-range value "
            f"(e.g. 85 instead of 0.85) is rejected, not coerced."
        ),
    )
    parser.add_argument(
        "--similarity-boost",
        dest="similarity_boost",
        type=float,
        default=DEFAULT_SIMILARITY_BOOST,
        help=(
            f"ElevenLabs voice_settings.similarity_boost, 0.0-1.0. Default: "
            f"{DEFAULT_SIMILARITY_BOOST}. Never clamped -- an out-of-range "
            f"value is rejected, not coerced."
        ),
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to write .mp3 files into. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default=DEFAULT_MODEL_ID,
        help=(
            "ElevenLabs model id. Default: "
            f"{DEFAULT_MODEL_ID} (ElevenLabs' documented multilingual "
            "model; needed for non-English text such as Russian)."
        ),
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        default=False,
        help="Regenerate and overwrite files that already exist. Default: skip them.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        default=False,
        help="Skip the confirmation prompt before a run of more than one word.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # --word/--file and --all/--count are enforced as argparse mutually
    # exclusive groups above; only the numeric range check needs doing here.
    if args.count is not None and args.count < 1:
        parser.error("--count must be >= 1")

    # Validate the voice settings BEFORE anything else -- a typo like `85`
    # instead of `0.85` must fail immediately, before any word list is even
    # loaded, not deep inside the synthesis loop after other work has run.
    try:
        validate_voice_setting("stability", args.stability)
        validate_voice_setting("similarity_boost", args.similarity_boost)
    except ValueError as exc:
        parser.error(str(exc))

    if args.word:
        available_words = [args.word]
    else:
        available_words = load_words_from_file(args.file)

    # Word axis and voice axis are two SEPARATE opt-ins -- neither implies
    # the other. --all-voices alone must never start walking the word list,
    # and --all/--count alone must never add the other two voices.
    total_available = len(available_words)
    if args.count is not None:
        word_limit = args.count
    elif args.all:
        word_limit = total_available
    else:
        word_limit = DEFAULT_WORD_LIMIT
    word_limit = max(0, min(word_limit, total_available))
    selected_words = available_words[:word_limit]

    selected_voices = list(VOICES) if args.all_voices else list(DEFAULT_VOICES)

    request_count = len(selected_words) * len(selected_voices)
    voice_names = ", ".join(v.name for v in selected_voices)

    print(
        f"About to issue {request_count} ElevenLabs request(s): "
        f"{len(selected_words)} word(s) (of {total_available} available) x "
        f"{len(selected_voices)} voice(s) [{voice_names}] (files that "
        f"already exist are skipped unless --replace is given)."
    )

    if request_count == 0:
        print("Nothing to do.")
        return 0

    if request_count > CONFIRM_ABOVE_REQUESTS and not args.yes:
        answer = input(
            f"This will spend ElevenLabs credits on up to {request_count} "
            f"request(s). Continue? [y/N] "
        )
        if answer.strip().lower() != "y":
            print("Aborted: nothing generated.")
            return 1

    try:
        api_key = get_api_key()
    except MissingAPIKeyError as exc:
        print(str(exc))
        return 1

    # The budget's limit is exactly the count just printed and (if needed)
    # confirmed -- computed once, here, independently of the loops inside
    # build_and_save_batch/build_and_save. If those loops ever tried to
    # issue more than this (a bug in word/voice-list construction, a stray
    # extra iteration, anything), fetch_tts_audio_metered's budget.spend()
    # raises BudgetExceededError before a second unauthorized request could
    # ever reach the network.
    budget = RequestBudget(limit=request_count)
    session = requests.Session()
    results = build_and_save_batch(
        selected_words,
        budget=budget,
        voices=selected_voices,
        dir_name=args.output_dir,
        model_id=args.model_id,
        replace=args.replace,
        api_key=api_key,
        session=session,
        stability=args.stability,
        similarity_boost=args.similarity_boost,
    )
    saved = sum(1 for r in results if not r.skipped)
    skipped = sum(1 for r in results if r.skipped)
    print(
        f"Done: {saved} file(s) generated, {skipped} skipped (already "
        f"existed). Budget spent: {budget.spent}/{budget.limit}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
