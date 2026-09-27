"""Resumable, budget-safe ElevenLabs audio generation for the mutable-words
deck (Nouns, Verbs, Adjectives, Adverbs).

The pure half (`load_base_words`, `select_voices`, `pending_pairs`,
`plan_requests`) only ever plans against the Anki media directory; `generate`
is the sole half that spends real requests, rechecking `media_dir` per word
so a duplicate word -- or a resumed run -- costs nothing the second time.
"""

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import requests

from anki_tools.audio_naming import build_filename, get_anki_media_dir
from anki_tools.elevenlabs_tts import (
    CONFIRM_ABOVE_REQUESTS,
    DEFAULT_OUTPUT_DIR,
    VOICES,
    MissingAPIKeyError,
    RequestBudget,
    SynthesisResult,
    Voice,
    build_and_save_batch,
    get_api_key,
)
from anki_tools.mutable_words_plan import (
    VOICE_SLOTS,
    parse_adjectives,
    parse_adverbs,
    parse_nouns,
    parse_verbs,
)

SHEETS: tuple[str, ...] = ("Nouns", "Verbs", "Adjectives", "Adverbs")

_PARSERS = {
    "Nouns": parse_nouns,
    "Verbs": parse_verbs,
    "Adjectives": parse_adjectives,
    "Adverbs": parse_adverbs,
}

_TSV_FILENAMES = {
    "Nouns": "nouns.tsv",
    "Verbs": "verbs.tsv",
    "Adjectives": "adjectives.tsv",
    "Adverbs": "adverbs.tsv",
}


def load_base_words(source_dir: str, sheets: Sequence[str] = SHEETS) -> list[str]:
    """Flatten every row's `.base_words` across `sheets`' TSVs under
    `source_dir`, in sheet order then row order."""
    words: list[str] = []
    for sheet in sheets:
        tsv_path = os.path.join(source_dir, _TSV_FILENAMES[sheet])
        for row in _PARSERS[sheet](tsv_path):
            words.extend(row.base_words)
    return words


@dataclass(frozen=True)
class AudioWorkPlan:
    total_pairs: int
    pending: list[tuple[str, str]]
    skipped: int


def select_voices(slots: Sequence[str]) -> list[Voice]:
    """Filter `elevenlabs_tts.VOICES` by `.slot`, preserving `slots`' order."""
    by_slot = {voice.slot: voice for voice in VOICES}
    unknown = [slot for slot in slots if slot not in by_slot]
    if unknown:
        raise ValueError(f"unknown voice slot(s): {unknown}")
    return [by_slot[slot] for slot in slots]


def pending_pairs(
    words: Sequence[str], slots: Sequence[str], media_dir: str
) -> list[tuple[str, str]]:
    """(word, slot) pairs whose predicted file is absent from `media_dir`."""
    return [
        (word, slot)
        for word in words
        for slot in slots
        if not os.path.isfile(build_filename(word, slot, dir_name=media_dir))
    ]


def plan_requests(
    words: Sequence[str], slots: Sequence[str], media_dir: str
) -> AudioWorkPlan:
    """Total pairs vs. pending vs. already-present, for `words` x `slots`
    against `media_dir`."""
    total_pairs = len(words) * len(slots)
    pending = pending_pairs(words, slots, media_dir)
    return AudioWorkPlan(
        total_pairs=total_pairs, pending=pending, skipped=total_pairs - len(pending)
    )


def generate(
    words: Sequence[str],
    *,
    slots: Sequence[str],
    media_dir: str,
    output_dir: str,
    budget: RequestBudget,
    session=None,
    api_key: str | None = None,
    replace: bool = False,
) -> list[SynthesisResult]:
    """Resumable driver: for each word, recheck `media_dir` at that point in
    the loop and only request the slots still missing there. A word with no
    missing slots is skipped entirely -- no call into `elevenlabs_tts`."""
    api_key = api_key or get_api_key()
    session = session or requests.Session()
    voices_by_slot = {voice.slot: voice for voice in select_voices(slots)}

    results: list[SynthesisResult] = []
    for word in words:
        word_slots = [
            slot
            for slot in slots
            if not os.path.isfile(build_filename(word, slot, dir_name=media_dir))
        ]
        if not word_slots:
            continue
        results.extend(
            build_and_save_batch(
                [word],
                budget=budget,
                voices=[voices_by_slot[slot] for slot in word_slots],
                dir_name=output_dir,
                api_key=api_key,
                session=session,
                replace=replace,
                anki_media_dir=media_dir,
            )
        )
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anki-mutable-words-audio",
        description=(
            "Generate missing audio for the mutable-words deck (Nouns, "
            "Verbs, Adjectives, Adverbs) across the f1/m2 voice slots, "
            "skipping every pair whose file already exists in the Anki "
            "media directory."
        ),
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default=str(Path(__file__).parent / "data" / "russian-vocabulary"),
        help="Directory holding nouns.tsv/verbs.tsv/adjectives.tsv/adverbs.tsv.",
    )
    parser.add_argument(
        "--sheet",
        action="append",
        choices=SHEETS,
        default=None,
        help="Limit to this sheet (repeatable). Default: all four, in order.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to write .mp3 files into. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--anki-media-dir",
        dest="anki_media_dir",
        type=str,
        default=None,
        help="Override the auto-detected Anki media directory.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N pending words.",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Print the cost table and voices line, then exit without generating.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        default=False,
        help="Skip the confirmation prompt.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    sheets = args.sheet or list(SHEETS)
    words = load_base_words(args.source_dir, sheets)
    slots = VOICE_SLOTS
    media_dir = args.anki_media_dir or get_anki_media_dir()

    work_plan = plan_requests(words, slots, media_dir)
    voices = select_voices(slots)

    print(
        f"total {work_plan.total_pairs} / present {work_plan.skipped} / "
        f"pending {len(work_plan.pending)}"
    )
    print(f"voices: {', '.join(voice.name for voice in voices)}")

    if args.dry_run:
        return 0

    pending_slots_by_word: dict[str, list[str]] = {}
    for word, slot in work_plan.pending:
        pending_slots_by_word.setdefault(word, []).append(slot)

    seen: set[str] = set()
    pending_words: list[str] = []
    for word in words:
        if word in seen:
            continue
        seen.add(word)
        if word in pending_slots_by_word:
            pending_words.append(word)

    if args.limit is not None:
        pending_words = pending_words[: args.limit]

    request_count = sum(len(pending_slots_by_word[word]) for word in pending_words)

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

    budget = RequestBudget(limit=request_count)
    session = requests.Session()
    results = generate(
        pending_words,
        slots=slots,
        media_dir=media_dir,
        output_dir=args.output_dir,
        budget=budget,
        session=session,
        api_key=api_key,
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
