#!/usr/bin/env python3
"""On-demand audio generation for individual words, in `single` mode (one
voice per gender) or `double` mode (two).

`mutable_words_audio` only ever fills gaps across a whole sheet and can
never redo a word that already has audio. This driver names its words
explicitly and, under `--replace`, archives the existing media file aside
before the write -- `elevenlabs_tts.build_and_save` never overwrites in the
Anki media directory, and that invariant stays intact.
"""

import argparse
import os
import shutil
import time
from dataclasses import dataclass
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

MODES: tuple[str, ...] = ("single", "double")
GENDERS: tuple[str, ...] = ("female", "male", "both")

# `single` mirrors the Mutable Words deck's f1/m2 pair; `double` mirrors
# Immutable Words' full f1/f2/m1/m2 roster.
_FEMALE_SLOTS = {"single": ("f1",), "double": ("f1", "f2")}
_MALE_SLOTS = {"single": ("m2",), "double": ("m1", "m2")}

DEFAULT_ARCHIVE_ROOT = os.path.expanduser("~/anki-backups/replaced-audio")


def slots_for(mode: str, gender: str) -> tuple[str, ...]:
    """The voice slots one (mode, gender) pair resolves to."""
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode!r}")
    if gender not in GENDERS:
        raise ValueError(f"unknown gender: {gender!r}")
    if gender == "female":
        return _FEMALE_SLOTS[mode]
    if gender == "male":
        return _MALE_SLOTS[mode]
    return _FEMALE_SLOTS[mode] + _MALE_SLOTS[mode]


def select_voices(slots: Sequence[str]) -> list[Voice]:
    by_slot = {voice.slot: voice for voice in VOICES}
    unknown = [slot for slot in slots if slot not in by_slot]
    if unknown:
        raise ValueError(f"unknown voice slot(s): {unknown}")
    return [by_slot[slot] for slot in slots]


@dataclass(frozen=True)
class WordAudioPlan:
    requested: tuple[tuple[str, str], ...]
    pending: tuple[tuple[str, str], ...]
    present: tuple[tuple[str, str], ...]


def plan_requests(
    words: Sequence[str],
    slots: Sequence[str],
    media_dir: str,
    replace: bool = False,
) -> WordAudioPlan:
    """(word, slot) pairs split into those needing a request and those
    already present. Duplicate words collapse to one entry."""
    requested = tuple(
        (word, slot) for word in dict.fromkeys(words) for slot in slots
    )
    pending: list[tuple[str, str]] = []
    present: list[tuple[str, str]] = []
    for word, slot in requested:
        exists = os.path.isfile(build_filename(word, slot, dir_name=media_dir))
        if exists and not replace:
            present.append((word, slot))
        else:
            pending.append((word, slot))
    return WordAudioPlan(requested, tuple(pending), tuple(present))


def archive_existing(
    pairs: Sequence[tuple[str, str]], media_dir: str, archive_dir: str
) -> list[str]:
    """Move each pair's existing media file into `archive_dir` so the
    regenerated file can be written. Returns the archived destinations."""
    moved: list[str] = []
    for word, slot in pairs:
        source = build_filename(word, slot, dir_name=media_dir)
        if not os.path.isfile(source):
            continue
        os.makedirs(archive_dir, exist_ok=True)
        dest = os.path.join(archive_dir, os.path.basename(source))
        shutil.move(source, dest)
        moved.append(dest)
    return moved


def generate(
    pending: Sequence[tuple[str, str]],
    *,
    media_dir: str,
    output_dir: str,
    budget: RequestBudget,
    session=None,
    api_key: str | None = None,
) -> list[SynthesisResult]:
    api_key = api_key or get_api_key()
    session = session if session is not None else requests.Session()

    slots_by_word: dict[str, list[str]] = {}
    for word, slot in pending:
        slots_by_word.setdefault(word, []).append(slot)

    results: list[SynthesisResult] = []
    for word, word_slots in slots_by_word.items():
        results.extend(
            build_and_save_batch(
                [word],
                budget=budget,
                voices=select_voices(word_slots),
                dir_name=output_dir,
                api_key=api_key,
                session=session,
                replace=True,
                anki_media_dir=media_dir,
            )
        )
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anki-word-audio",
        description=(
            "Generate audio for named words. 'single' mode uses one voice "
            "per gender (f1/m2, as the Mutable Words deck does); 'double' "
            "uses two (f1/f2 and m1/m2, as Immutable Words does)."
        ),
    )
    parser.add_argument("words", nargs="+", help="Russian word(s) to voice.")
    parser.add_argument(
        "--mode",
        choices=MODES,
        default="single",
        help="Voices per gender. Default: single.",
    )
    parser.add_argument(
        "--gender",
        choices=GENDERS,
        default="both",
        help="Which gender(s) to generate. Default: both.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        default=False,
        help="Redo words that already have audio, archiving the old file.",
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
        "--archive-dir",
        dest="archive_dir",
        type=str,
        default=None,
        help=f"Where --replace moves old files. Default: {DEFAULT_ARCHIVE_ROOT}/<timestamp>",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Print the plan and exit without generating.",
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
    args = build_parser().parse_args(argv)

    slots = slots_for(args.mode, args.gender)
    media_dir = args.anki_media_dir or get_anki_media_dir()
    work_plan = plan_requests(args.words, slots, media_dir, replace=args.replace)
    voices = select_voices(slots)

    print(f"mode {args.mode} / gender {args.gender} / slots {', '.join(slots)}")
    print(f"voices: {', '.join(voice.name for voice in voices)}")
    print(
        f"total {len(work_plan.requested)} / present {len(work_plan.present)} / "
        f"pending {len(work_plan.pending)}"
    )
    for word, slot in work_plan.present:
        print(f"  skip {word} [{slot}] -- already in media (use --replace to redo)")

    if args.dry_run:
        return 0

    if not work_plan.pending:
        print("Nothing to do.")
        return 0

    request_count = len(work_plan.pending)
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
        return 2

    archive_dir = args.archive_dir or os.path.join(
        DEFAULT_ARCHIVE_ROOT, time.strftime("%Y%m%d-%H%M%S")
    )
    if args.replace:
        archived = archive_existing(work_plan.pending, media_dir, archive_dir)
        if archived:
            print(f"archived {len(archived)} existing file(s) to {archive_dir}")

    results = generate(
        work_plan.pending,
        media_dir=media_dir,
        output_dir=args.output_dir,
        budget=RequestBudget(request_count),
        api_key=api_key,
    )

    written = [r for r in results if not r.skipped]
    collisions = [r for r in results if r.media_collision]
    print(f"generated {len(written)} / {len(results)} requested pair(s)")
    for result in collisions:
        print(f"  media collision (left alone): {result.media_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
