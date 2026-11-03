#!/usr/bin/env python3
"""Pull reviews down from AnkiWeb, put the deck changes back, push up.

Credentials come from ANKI_SYNC_USER/ANKI_SYNC_PASS when set, otherwise from
an interactive prompt. Either way they stay in memory: never written to disk,
never echoed, never passed as an argument where `ps` would show them.

Adding fields bumps the collection's schema, so AnkiWeb forces a one-sided
full sync. That is why a download alone loses the fields and an upload alone
loses whatever was reviewed elsewhere -- this runs download, rebuild, upload
in one pass so neither side has to be the loser.

Aborts rather than guessing whenever the server asks for a direction it was
not told to take.
"""

import getpass
import os
import shutil
import subprocess
import sys
import time

from anki.collection import Collection
from anki.errors import AnkiException, DBError
from anki.sync_pb2 import SyncCollectionResponse, SyncStatusResponse

PACKAGES = (
    "/home/icarus64/Desktop/anki-rebuild/mutable-words.apkg",
    "/home/icarus64/Desktop/anki-rebuild/immutable-words.apkg",
)
BACKUP_ROOT = os.path.expanduser("~/anki-backups")

_REQUIRED = {v.number: v.name for v in SyncStatusResponse.Required.DESCRIPTOR.values}
_CHANGES = {
    v.number: v.name for v in SyncCollectionResponse.ChangesRequired.DESCRIPTOR.values
}


def anki_is_running() -> bool:
    out = subprocess.run(
        ["ps", "-eo", "comm"], capture_output=True, text=True, check=False
    ).stdout
    return any(line.strip() == "anki" for line in out.splitlines())


def credentials() -> tuple[str, str]:
    user = os.environ.get("ANKI_SYNC_USER") or input("AnkiWeb email: ").strip()
    password = os.environ.get("ANKI_SYNC_PASS") or getpass.getpass("AnkiWeb password: ")
    if not user or not password:
        raise SystemExit("no credentials given")
    return user, password


def backup(path: str, label: str) -> str:
    target = os.path.join(BACKUP_ROOT, f"{label}-{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(target, exist_ok=True)
    shutil.copy2(path, target)
    return os.path.join(target, os.path.basename(path))


def review_state(col) -> tuple[int, int, int]:
    return (
        col.db.scalar("select count(*) from revlog"),
        col.db.scalar("select count(*) from cards where type != 0"),
        col.db.scalar("select count(*) from cards where queue = -1"),
    )


def pull(path: str, login) -> None:
    col = Collection(path)
    try:
        auth = login(col)
        status = col.sync_status(auth)
        print(f"  server says: {_REQUIRED.get(status.required, status.required)}")
        if status.required == SyncStatusResponse.NO_CHANGES:
            print("  nothing to pull")
            return
        if status.required == SyncStatusResponse.NORMAL_SYNC:
            out = col.sync_collection(auth, True)
            print(f"  normal sync -> {_CHANGES.get(out.required, out.required)}")
            if out.required == SyncCollectionResponse.NO_CHANGES:
                return
            if out.required != SyncCollectionResponse.FULL_DOWNLOAD:
                raise SystemExit(
                    f"server asked for {_CHANGES.get(out.required)} while pulling; "
                    "not guessing a direction"
                )
        col.close_for_full_sync()
        col.full_upload_or_download(auth=auth, server_usn=None, upload=False)
        print("  full download done")
    finally:
        try:
            col.close()
        except Exception:
            pass


def rebuild(path: str) -> None:
    from anki import import_export_pb2 as ie

    from anki_tools import phrase_due
    from anki_tools import phrase_words as pw
    from anki_tools.phrase_due_cli import DUE_TODAY
    from anki_tools.phrase_words_cli import collect

    assert DUE_TODAY == "0" and "!" not in DUE_TODAY, DUE_TODAY
    always = (
        ie.ImportAnkiPackageUpdateCondition.IMPORT_ANKI_PACKAGE_UPDATE_CONDITION_ALWAYS
    )

    col = Collection(path)
    try:
        before = review_state(col)
        print(f"  before: revlog={before[0]} studied={before[1]} suspended={before[2]}")

        for package in PACKAGES:
            out = col.import_anki_package(
                ie.ImportAnkiPackageRequest(
                    package_path=package,
                    options=ie.ImportAnkiPackageOptions(
                        merge_notetypes=True,
                        with_scheduling=False,
                        update_notes=always,
                        update_notetypes=always,
                    ),
                )
            )
            name = os.path.basename(package)
            print(
                f"  {name}: {len(out.log.new)} new, {len(out.log.updated)} updated, "
                f"{len(out.log.conflicting)} conflicting"
            )
            if out.log.conflicting:
                raise SystemExit(f"{name} reported conflicts; stopping")

        imported = review_state(col)
        if imported[1:] != before[1:]:
            raise SystemExit(
                f"the import moved scheduling ({before} -> {imported}); "
                "stopping before anything is pushed"
            )

        phrases, index, card_rows, _ = collect(col, pw.PHRASE_NOTE_TYPE, False)
        all_new = pw.group_by_state(pw.audit(phrases, index, card_rows))[pw.ALL_NEW]
        note_ids = set()
        for record in all_new:
            resolution = pw.resolve(record.token, index)
            if resolution is not None:
                note_ids.add(resolution.word.note_id)
        if note_ids:
            listed = "(" + ",".join(str(n) for n in note_ids) + ")"
            rows = col.db.all(
                f"select id, nid, type, queue from cards where nid in {listed}"
            )
            due = phrase_due.find_all_new_cards(rows, note_ids)
            skipped = phrase_due.count_suspended_skipped(rows, note_ids)
            col.sched.set_due_date(due, DUE_TODAY)
            print(
                f"  phrase words: {len(all_new)} word(s), {len(due)} card(s) due, "
                f"{skipped} suspended skipped"
            )
            made_due = len(due)
        else:
            made_due = 0

        after = review_state(col)
        print(f"  after:  revlog={after[0]} studied={after[1]} suspended={after[2]}")
        # Dating a new card turns it into a review card, so `studied` is
        # expected to grow by exactly the cards asked for -- and by no others.
        expected_studied = imported[1] + made_due
        if after[1] != expected_studied or after[2] != imported[2]:
            raise SystemExit(
                f"scheduling moved beyond the {made_due} card(s) asked for "
                f"({imported} -> {after}); stopping before anything is pushed"
            )
    finally:
        col.close()

    result = subprocess.run(
        [sys.executable, "-m", "anki_tools.aspect_due_cli", "--rule", "space", "--fix"],
        check=False,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    if result.returncode:
        raise SystemExit(f"aspect rule failed:\n{result.stderr}")
    for line in result.stdout.splitlines():
        if "Deferred" in line or "still breaking" in line:
            print(f"  aspect rule: {line.strip()}")


def push(path: str, login) -> None:
    col = Collection(path)
    try:
        auth = login(col)
        status = col.sync_status(auth)
        name = _REQUIRED.get(status.required, status.required)
        print(f"  server says: {name}")

        if status.required == SyncStatusResponse.NO_CHANGES:
            print("  nothing to push")
            return

        if status.required == SyncStatusResponse.NORMAL_SYNC:
            out = col.sync_collection(auth, True)
            asked = _CHANGES.get(out.required, out.required)
            print(f"  normal sync -> {asked}")
            if out.required == SyncCollectionResponse.NO_CHANGES:
                return
            if out.required != SyncCollectionResponse.FULL_UPLOAD:
                raise SystemExit(
                    f"server asked for {asked} on the way up; refusing"
                    " -- that direction would discard local work"
                )

        col.close_for_full_sync()
        col.full_upload_or_download(auth=auth, server_usn=None, upload=True)
        print("  full upload done")
    finally:
        try:
            col.close()
        except Exception:
            pass


def push_media(path: str, login) -> None:
    col = Collection(path)
    try:
        col.sync_media(login(col))
        print("  media sync running")
        for _ in range(180):
            if not col.media_sync_status().active:
                break
            time.sleep(1)
        print("  media sync finished")
    finally:
        col.close()


def main() -> int:
    from anki_tools.audio_naming import get_anki_collection_path

    path = get_anki_collection_path()
    if anki_is_running():
        print("Anki is running -- close it first", file=sys.stderr)
        return 2
    missing = [p for p in PACKAGES if not os.path.exists(p)]
    if missing:
        print(f"missing package(s): {', '.join(missing)}", file=sys.stderr)
        return 2

    user, password = credentials()

    def login(col):
        return col.sync_login(user, password, None)

    print(f"\nbackup: {backup(path, 'presync')}")
    try:
        print("\n[1/3] pulling from AnkiWeb")
        pull(path, login)
        print(f"backup after pull: {backup(path, 'postpull')}")
        print("\n[2/3] putting the deck changes back")
        rebuild(path)
        print("\n[3/3] pushing to AnkiWeb")
        push(path, login)
        push_media(path, login)
    except (AnkiException, DBError) as error:
        print(f"\nanki error: {error}", file=sys.stderr)
        return 1

    col = Collection(path)
    try:
        mod, ls = col.db.all("select mod, ls from col")[0]
        revlog, studied, suspended = review_state(col)
        cued = col.db.scalar(
            "select count(*) from notes where mid in "
            "(select ntid from fields where name = 'English Distinction')"
        )
        print(
            f"\nin sync: {mod == ls} | revlog={revlog} studied={studied} "
            f"suspended={suspended} | notes carrying the cue fields: {cued}"
        )
    finally:
        col.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
