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

Voices (D5, settled): the account's three Russian voices, verified live via
`GET /v2/voices`. The other ~21 voices on the account are premade English
and must never be used here.

    Elen Kuragina - Golden & Dangerous   (female)
    Mishka Yaponcik - Odessa Rogue Charm (male)
    Nester Surovy - Gravely yet Refined  (male)

THE HARD COST LIMIT: a default run synthesizes exactly one word across all
three voices (3 requests) and stops. Processing more than one word requires
an explicit `--all` or `--count` opt-in on the CLI, or passing more than one
word to `build_and_save_batch` directly -- there is no code path in `main()`
that spends money on the full word list without that opt-in.
"""

import argparse
import functools
import hashlib
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
# Voices (D5)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Voice:
    name: str
    voice_id: str
    slug: str
    gender: str


VOICES: tuple = (
    # Elen Kuragina - Golden & Dangerous (female)
    Voice(
        name="Elen Kuragina - Golden & Dangerous",
        voice_id="TPIitICAZ8CqlGZ81AKm",
        slug="elen-kuragina",
        gender="female",
    ),
    # Mishka Yaponcik - Odessa Rogue Charm (male)
    Voice(
        name="Mishka Yaponcik - Odessa Rogue Charm",
        voice_id="RLRdvNFwJJct2XZOgfzy",
        slug="mishka-yaponcik",
        gender="male",
    ),
    # Nester Surovy - Gravely yet Refined (male)
    Voice(
        name="Nester Surovy - Gravely yet Refined",
        voice_id="pM78bgjPVk0JXtaEnFoj",
        slug="nester-surovy",
        gender="male",
    ),
)


@dataclass(frozen=True)
class SynthesisResult:
    word: str
    voice: Voice
    path: str
    skipped: bool


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


# ---------------------------------------------------------------------------
# Filename sanitization -- deterministic and collision-free
# ---------------------------------------------------------------------------

# Cyrillic letters, digits, and underscore all count as "word" characters
# under Python's unicode-aware \w, so the source text survives intact; every
# run of anything else (spaces, "/", ",", ".", quotes, ...) collapses to a
# single hyphen. This alone makes "/" -- which cannot appear in a filename
# at all -- disappear along with every other filesystem-hostile character.
_UNSAFE_RUN = re.compile(r"[^\w\-]+", re.UNICODE)
_MULTI_HYPHEN = re.compile(r"-{2,}")


def sanitize_word_slug(word: str) -> str:
    """Turn a Russian word/phrase into a filesystem-safe, reproducible slug.

    Deliberately defensive rather than merely tidy: two different source
    strings that simplify to the same visible slug (e.g. "-то" and "то"
    once leading hyphens are trimmed) still get different filenames, because
    a short hash of the ORIGINAL (NFC-normalized) string is always appended.
    Same input -> same output, every time, which is what lets a rerun target
    the same names and the skip-if-exists check actually skip.
    """
    normalized = unicodedata.normalize("NFC", word.strip())
    slug = _UNSAFE_RUN.sub("-", normalized)
    slug = _MULTI_HYPHEN.sub("-", slug).strip("-")
    if not slug:
        slug = "word"
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:8]
    return f"{slug}-{digest}"


def build_filename(word: str, voice: Voice, dir_name: str = DEFAULT_OUTPUT_DIR) -> str:
    """The deterministic path for one (word, voice) pair's .mp3."""
    word_slug = sanitize_word_slug(word)
    return os.path.join(dir_name, f"{word_slug}__{voice.slug}.mp3")


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
    session=None,
    timeout: int = DEFAULT_TIMEOUT,
) -> bytes:
    """One HTTP call to ElevenLabs. Raises on any non-2xx response.

    `session` is an injected `requests.Session` (or any object exposing a
    `.post` matching its signature) so callers can reuse a connection across
    a batch, and so tests can substitute a mock with zero real HTTP.
    """
    client = session if session is not None else requests
    url = f"{API_BASE_URL}/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    payload = {"text": text, "model_id": model_id}

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


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------


def build_and_save(
    word: str,
    *,
    dir_name: str = DEFAULT_OUTPUT_DIR,
    voices: Sequence[Voice] = VOICES,
    model_id: str = DEFAULT_MODEL_ID,
    replace: bool = False,
    api_key: Optional[str] = None,
    session=None,
) -> list:
    """Synthesize ONE word across every voice in `voices` (default: all 3).

    Skips a (word, voice) pair whose file already exists unless `replace` is
    set, so a resumed run is cheap and idempotent. Returns one
    `SynthesisResult` per voice, generated or skipped.
    """
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

        audio_bytes = _fetch_tts_audio(
            voice.voice_id, word, model_id, api_key, session=session
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
    dir_name: str = DEFAULT_OUTPUT_DIR,
    voices: Sequence[Voice] = VOICES,
    model_id: str = DEFAULT_MODEL_ID,
    replace: bool = False,
    api_key: Optional[str] = None,
    session=None,
) -> list:
    """Synthesize many words, each across every voice in `voices`.

    This is the many-words path -- it exists and is exercised by tests, but
    NOTHING in `main()` reaches it with more than `DEFAULT_WORD_LIMIT` words
    unless the caller opted in via `--all`/`--count`. Callers driving this
    directly (not through the CLI) are themselves responsible for the same
    restraint; this function does not re-enforce the limit.
    """
    api_key = api_key or get_api_key()
    session = session if session is not None else requests.Session()
    results = []
    for word in words:
        results.extend(
            build_and_save(
                word,
                dir_name=dir_name,
                voices=voices,
                model_id=model_id,
                replace=replace,
                api_key=api_key,
                session=session,
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
            "Synthesize Russian text to speech via ElevenLabs, one .mp3 per "
            "configured voice (currently 3: Elen Kuragina, Mishka Yaponcik, "
            "Nester Surovy). The default run costs at most 3 requests -- ONE "
            "word times the three voices -- and stops. Processing more than "
            "one word from --file requires --all or --count."
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
            "Process every word in --file, not just the first one. This "
            "spends real ElevenLabs credits for every word -- see the "
            "request count printed before the confirmation prompt."
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
            "exclusive with --all."
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

    if args.word:
        available_words = [args.word]
    else:
        available_words = load_words_from_file(args.file)

    total_available = len(available_words)
    if args.count is not None:
        limit = args.count
    elif args.all:
        limit = total_available
    else:
        limit = DEFAULT_WORD_LIMIT
    limit = max(0, min(limit, total_available))
    selected_words = available_words[:limit]
    request_count = len(selected_words) * len(VOICES)

    print(
        f"Selected {len(selected_words)} of {total_available} word(s) "
        f"available x {len(VOICES)} voice(s) = {request_count} ElevenLabs "
        f"request(s) at most (files that already exist are skipped unless "
        f"--replace is given)."
    )

    if not selected_words:
        print("Nothing to do.")
        return 0

    if len(selected_words) > DEFAULT_WORD_LIMIT and not args.yes:
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

    session = requests.Session()
    results = build_and_save_batch(
        selected_words,
        dir_name=args.output_dir,
        model_id=args.model_id,
        replace=args.replace,
        api_key=api_key,
        session=session,
    )
    saved = sum(1 for r in results if not r.skipped)
    skipped = sum(1 for r in results if r.skipped)
    print(f"Done: {saved} file(s) generated, {skipped} skipped (already existed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
