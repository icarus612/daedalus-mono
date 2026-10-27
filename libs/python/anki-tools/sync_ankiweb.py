"""One-off AnkiWeb sync. Credentials come from ANKI_SYNC_USER/ANKI_SYNC_PASS
in the environment only -- never a CLI argument, never read from disk.

Aborts rather than choosing a direction when the server demands a full sync:
that always clobbers one side, and it is not a machine's call to make.
"""

import os
import shutil
import subprocess
import sys
import time

from anki.collection import Collection
from anki.sync_pb2 import SyncCollectionResponse, SyncStatusResponse

COLLECTION = os.path.expanduser("~/.local/share/Anki2/User 1/collection.anki2")
BACKUP_ROOT = os.path.expanduser("~/anki-backups")

_REQUIRED = {v.number: v.name for v in SyncStatusResponse.Required.DESCRIPTOR.values}
_CHANGES = {
    v.number: v.name for v in SyncCollectionResponse.ChangesRequired.DESCRIPTOR.values
}


def anki_is_running() -> bool:
    found = subprocess.run(
        ["pgrep", "-f", "-a", "anki"], capture_output=True, text=True
    ).stdout
    return any(
        "/anki" in line or line.rstrip().endswith("anki") for line in found.splitlines()
    )


def main() -> int:
    username = os.environ.get("ANKI_SYNC_USER")
    password = os.environ.get("ANKI_SYNC_PASS")
    if not username or not password:
        print(
            "set ANKI_SYNC_USER and ANKI_SYNC_PASS in the environment",
            file=sys.stderr,
        )
        return 2

    if anki_is_running():
        print("Anki is running -- close it first", file=sys.stderr)
        return 2

    backup = os.path.join(BACKUP_ROOT, f"presync-{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(backup, exist_ok=True)
    shutil.copy2(COLLECTION, backup)
    print(f"backup: {backup}")

    col = Collection(COLLECTION)
    try:
        auth = col.sync_login(username, password, None)
        status = col.sync_status(auth)
        print(f"status before: {_REQUIRED.get(status.required, status.required)}")

        if status.required == SyncStatusResponse.FULL_SYNC:
            print(
                "server requires a FULL sync -- aborting. One side would be "
                "overwritten; choose the direction yourself in the Anki GUI.",
                file=sys.stderr,
            )
            return 3

        if status.required == SyncStatusResponse.NO_CHANGES:
            print("already up to date; syncing media only")

        out = col.sync_collection(auth, True)
        print(f"result: {_CHANGES.get(out.required, out.required)}")
        if out.server_message:
            print(f"server: {out.server_message}")

        deadline = time.time() + 900
        while time.time() < deadline:
            progress = col.media_sync_status()
            if not progress.active:
                break
            time.sleep(2)
        else:
            print("media sync still running after 15m", file=sys.stderr)
    finally:
        col.close()

    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
