"""Sync the collection and its media to AnkiWeb through Anki desktop, then
prove the given media files went up.

Anki only rescans the media folder when the folder's own mtime moves, and
only uploads a file its scan marked dirty. So the folder is touched first,
Anki is opened (sync on open) and closed (sync on close), and the run fails
unless every named file is in the media DB with its current checksum and
nothing is left dirty.
"""

import hashlib
import os
import shutil
import sqlite3
import subprocess
import tempfile
import time
from collections.abc import Callable, Iterable

from anki_tools.audio_naming import get_anki_collection_path, get_anki_media_dir

SYNC_SECONDS = 45
EXIT_TIMEOUT = 120


class SyncError(RuntimeError):
    pass


def _sha1(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha1(handle.read()).hexdigest()


def media_db_path(collection_path: str) -> str:
    return os.path.join(os.path.dirname(collection_path), "collection.media.db2")


def unsynced_media(media_dir: str, media_db: str, names: Iterable[str]) -> list[str]:
    """Names whose current file is not recorded as uploaded, plus any dirty row."""
    conn = sqlite3.connect(f"file:{media_db}?mode=ro", uri=True)
    try:
        rows = {
            fname: (csum, dirty)
            for fname, csum, dirty in conn.execute(
                "select fname, csum, dirty from media"
            )
        }
        dirty = [fname for fname, (_csum, flag) in rows.items() if flag and fname]
    finally:
        conn.close()
    missing = []
    for name in names:
        csum, flag = rows.get(name, (None, 1))
        if flag or csum != _sha1(os.path.join(media_dir, name)):
            missing.append(name)
    return sorted(set(missing) | set(dirty))


def collection_pending(collection_path: str) -> int:
    """Unsynced collection changes, read from a copy so a lock never matters."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = os.path.join(tmp, "c.anki2")
        shutil.copy(collection_path, copy)
        conn = sqlite3.connect(copy)
        try:
            behind = conn.execute("select ls < mod from col").fetchone()[0]
            rows = sum(
                conn.execute(f"select count(*) from {table} where usn = -1").fetchone()[
                    0
                ]
                for table in ("notes", "cards", "notetypes", "revlog", "decks")
            )
        finally:
            conn.close()
    return rows + int(behind)


def _anki_running() -> bool:
    return subprocess.run(["pgrep", "-x", "anki"], capture_output=True).returncode == 0


def _close_anki() -> None:
    subprocess.run(["pkill", "-INT", "-x", "anki"], check=False)
    deadline = time.monotonic() + EXIT_TIMEOUT
    while _anki_running():
        if time.monotonic() > deadline:
            raise SyncError("Anki did not exit after its closing sync")
        time.sleep(1)


def _open_anki() -> None:
    subprocess.Popen(
        ["anki"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def sync(
    media_names: Iterable[str] = (),
    collection_path: str | None = None,
    open_anki: Callable[[], None] = _open_anki,
    close_anki: Callable[[], None] = _close_anki,
    wait: Callable[[float], None] = time.sleep,
) -> None:
    """Open and close Anki desktop so it syncs, then verify; raises SyncError."""
    path = collection_path or get_anki_collection_path()
    media_dir = get_anki_media_dir(path)
    names = list(media_names)
    close_anki()
    os.utime(media_dir)
    open_anki()
    wait(SYNC_SECONDS)
    close_anki()
    left = unsynced_media(media_dir, media_db_path(path), names)
    if left:
        raise SyncError(f"media not uploaded: {', '.join(left)}")
    pending = collection_pending(path)
    if pending:
        raise SyncError(f"{pending} collection change(s) not synced")
