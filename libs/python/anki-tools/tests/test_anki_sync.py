import hashlib
import os
import sqlite3

import pytest

from anki_tools import anki_sync


def _setup(tmp_path, rows, files):
    media = tmp_path / "collection.media"
    media.mkdir()
    for name, data in files.items():
        (media / name).write_bytes(data)
    conn = sqlite3.connect(tmp_path / "collection.media.db2")
    conn.execute("create table media (fname text, csum text, mtime int, dirty int)")
    conn.executemany("insert into media values (?, ?, 0, ?)", rows)
    conn.commit()
    conn.close()
    col = sqlite3.connect(tmp_path / "collection.anki2")
    col.execute("create table col (ls int, mod int)")
    col.execute("insert into col values (5, 5)")
    for table in ("notes", "cards", "notetypes", "revlog", "decks"):
        col.execute(f"create table {table} (usn int)")
    col.commit()
    col.close()
    return str(tmp_path / "collection.anki2")


def _sha(data):
    return hashlib.sha1(data).hexdigest()


def test_uploaded_file_with_current_checksum_counts_as_synced(tmp_path):
    path = _setup(tmp_path, [("a.mp3", _sha(b"new"), 0)], {"a.mp3": b"new"})
    media = os.path.join(tmp_path, "collection.media")
    assert (
        anki_sync.unsynced_media(media, anki_sync.media_db_path(path), ["a.mp3"]) == []
    )


@pytest.mark.parametrize(
    "rows",
    [
        [("a.mp3", _sha(b"old"), 0)],
        [("a.mp3", _sha(b"new"), 1)],
        [],
    ],
    ids=["stale-checksum", "still-dirty", "never-registered"],
)
def test_replaced_file_not_yet_uploaded_is_reported(tmp_path, rows):
    path = _setup(tmp_path, rows, {"a.mp3": b"new"})
    media = os.path.join(tmp_path, "collection.media")
    assert anki_sync.unsynced_media(
        media, anki_sync.media_db_path(path), ["a.mp3"]
    ) == ["a.mp3"]


def test_sync_opens_then_closes_anki_and_passes_when_uploaded(tmp_path):
    path = _setup(tmp_path, [("a.mp3", _sha(b"new"), 0)], {"a.mp3": b"new"})
    calls = []
    anki_sync.sync(
        ["a.mp3"],
        path,
        open_anki=lambda: calls.append("open"),
        close_anki=lambda: calls.append("close"),
        wait=lambda _s: calls.append("wait"),
    )
    assert calls == ["close", "open", "wait", "close"]


def test_sync_fails_loudly_when_the_new_audio_did_not_go_up(tmp_path):
    path = _setup(tmp_path, [("a.mp3", _sha(b"old"), 0)], {"a.mp3": b"new"})
    with pytest.raises(anki_sync.SyncError, match="a.mp3"):
        anki_sync.sync(
            ["a.mp3"],
            path,
            open_anki=lambda: None,
            close_anki=lambda: None,
            wait=lambda _s: None,
        )


def test_sync_fails_when_collection_changes_are_pending(tmp_path):
    path = _setup(tmp_path, [], {})
    col = sqlite3.connect(path)
    col.execute("insert into cards values (-1)")
    col.commit()
    col.close()
    with pytest.raises(anki_sync.SyncError, match="collection"):
        anki_sync.sync(
            [],
            path,
            open_anki=lambda: None,
            close_anki=lambda: None,
            wait=lambda _s: None,
        )
