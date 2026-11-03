import importlib.util
import os
import sys
from pathlib import Path

import pytest
from anki.sync_pb2 import SyncCollectionResponse, SyncStatusResponse

_PATH = Path(__file__).resolve().parents[1] / "anki_sync_and_restore.py"
_SPEC = importlib.util.spec_from_file_location("anki_sync_and_restore", _PATH)
sar = importlib.util.module_from_spec(_SPEC)
sys.modules["anki_sync_and_restore"] = sar
_SPEC.loader.exec_module(sar)


def test_due_today_is_the_plain_form_not_the_interval_rewriting_one():
    from anki_tools.phrase_due_cli import DUE_TODAY

    assert DUE_TODAY == "0"
    assert "!" not in DUE_TODAY


def test_packages_are_both_named_and_distinct():
    assert len(sar.PACKAGES) == 2
    assert len(set(sar.PACKAGES)) == 2
    assert all(p.endswith(".apkg") for p in sar.PACKAGES)


def test_credentials_prefer_the_environment(monkeypatch):
    monkeypatch.setenv("ANKI_SYNC_USER", "someone@example.com")
    monkeypatch.setenv("ANKI_SYNC_PASS", "from-env")
    monkeypatch.setattr(
        sar.getpass, "getpass", lambda *a: pytest.fail("prompted despite env")
    )
    assert sar.credentials() == ("someone@example.com", "from-env")


def test_credentials_prompt_without_echoing(monkeypatch):
    monkeypatch.delenv("ANKI_SYNC_USER", raising=False)
    monkeypatch.delenv("ANKI_SYNC_PASS", raising=False)
    monkeypatch.setattr("builtins.input", lambda *a: " someone@example.com ")
    monkeypatch.setattr(sar.getpass, "getpass", lambda *a: "typed")
    assert sar.credentials() == ("someone@example.com", "typed")


@pytest.mark.parametrize("user,password", [("", "p"), ("u", ""), ("", "")])
def test_credentials_refuse_to_proceed_when_blank(monkeypatch, user, password):
    monkeypatch.setenv("ANKI_SYNC_USER", user)
    monkeypatch.setenv("ANKI_SYNC_PASS", password)
    monkeypatch.setattr("builtins.input", lambda *a: user)
    monkeypatch.setattr(sar.getpass, "getpass", lambda *a: password)
    with pytest.raises(SystemExit):
        sar.credentials()


def test_the_secret_is_never_an_argv_entry():
    source = _PATH.read_text(encoding="utf-8")
    assert "--password" not in source
    assert "ANKI_SYNC_PASS" in source
    for marker in ("print(password", 'print(f"{password', "password}"):
        assert marker not in source


def test_anki_is_running_matches_the_process_name_exactly(monkeypatch):
    def fake(cmd, **kwargs):
        class R:
            stdout = "bash\npython3\nanki\n"

        return R()

    monkeypatch.setattr(sar.subprocess, "run", fake)
    assert sar.anki_is_running() is True


def test_anki_is_running_is_not_fooled_by_a_substring(monkeypatch):
    """`pgrep -f anki` once matched this session's own shell. Exact
    comm-name matching is what keeps that from happening."""

    def fake(cmd, **kwargs):
        class R:
            stdout = "bash\nankiconnect-helper\nmy-anki-script\n"

        return R()

    monkeypatch.setattr(sar.subprocess, "run", fake)
    assert sar.anki_is_running() is False


def test_main_refuses_while_anki_is_open(monkeypatch, capsys):
    monkeypatch.setattr(sar, "anki_is_running", lambda: True)
    monkeypatch.setattr(
        sar, "credentials", lambda: pytest.fail("asked for credentials anyway")
    )
    assert sar.main() == 2
    assert "close it first" in capsys.readouterr().err


def test_main_refuses_when_a_package_is_missing(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(sar, "anki_is_running", lambda: False)
    monkeypatch.setattr(sar, "PACKAGES", (str(tmp_path / "nope.apkg"),))
    monkeypatch.setattr(
        sar, "credentials", lambda: pytest.fail("asked for credentials anyway")
    )
    assert sar.main() == 2
    assert "missing package" in capsys.readouterr().err


class _Col:
    """Minimal stand-in. Records which full-sync direction was taken."""

    def __init__(self, required, after_normal=None):
        self._required = required
        self._after_normal = after_normal
        self.uploaded = None
        self.normal_synced = False
        self.closed_for_full = False
        self.closed = False
        self.media_synced = False

    def sync_login(self, *a):
        return "auth"

    def sync_status(self, auth):
        class S:
            required = self._required

        return S()

    def sync_collection(self, auth, media):
        self.normal_synced = True

        class Out:
            required = self._after_normal

        return Out()

    def close_for_full_sync(self):
        self.closed_for_full = True

    def full_upload_or_download(self, *, auth, server_usn, upload):
        self.uploaded = upload

    def sync_media(self, auth):
        self.media_synced = True

    def media_sync_status(self):
        class M:
            active = False

        return M()

    def close(self):
        self.closed = True


def _patch_collection(monkeypatch, col):
    monkeypatch.setattr(sar, "Collection", lambda path: col)


def test_pull_takes_the_download_direction(monkeypatch):
    col = _Col(SyncStatusResponse.FULL_SYNC)
    _patch_collection(monkeypatch, col)
    sar.pull("ignored", lambda c: "auth")
    assert col.uploaded is False
    assert col.closed_for_full and col.closed


def test_pull_does_nothing_when_the_server_has_nothing(monkeypatch):
    col = _Col(SyncStatusResponse.NO_CHANGES)
    _patch_collection(monkeypatch, col)
    sar.pull("ignored", lambda c: "auth")
    assert col.uploaded is None
    assert not col.closed_for_full


def test_pull_refuses_an_upload_the_server_asks_for_mid_pull(monkeypatch):
    """The direction that would discard the server's reviews. Refusing is the
    whole point: a wrong direction here is what destroyed work three times."""
    col = _Col(
        SyncStatusResponse.NORMAL_SYNC,
        after_normal=SyncCollectionResponse.FULL_UPLOAD,
    )
    _patch_collection(monkeypatch, col)
    with pytest.raises(SystemExit) as exc:
        sar.pull("ignored", lambda c: "auth")
    assert "not guessing" in str(exc.value)
    assert col.uploaded is None


def test_push_takes_the_upload_direction(monkeypatch):
    col = _Col(SyncStatusResponse.FULL_SYNC)
    _patch_collection(monkeypatch, col)
    sar.push("ignored", lambda c: "auth")
    assert col.uploaded is True
    assert col.closed_for_full and col.closed


def test_media_is_pushed_as_its_own_step(monkeypatch):
    col = _Col(SyncStatusResponse.NO_CHANGES)
    _patch_collection(monkeypatch, col)
    sar.push_media("ignored", lambda c: "auth")
    assert col.media_synced and col.closed


def test_push_refuses_a_download_the_server_asks_for_mid_push(monkeypatch):
    """A download here would overwrite the freshly rebuilt fields, which is
    exactly the failure this script exists to prevent."""
    col = _Col(
        SyncStatusResponse.NORMAL_SYNC,
        after_normal=SyncCollectionResponse.FULL_DOWNLOAD,
    )
    _patch_collection(monkeypatch, col)
    with pytest.raises(SystemExit) as exc:
        sar.push("ignored", lambda c: "auth")
    assert "discard local work" in str(exc.value)
    assert col.uploaded is None


def test_the_direction_guards_can_fail(monkeypatch):
    """Positive control: both guards are reachable, so the refusals above are
    not passing by accident."""
    down = _Col(SyncStatusResponse.FULL_SYNC)
    _patch_collection(monkeypatch, down)
    sar.pull("ignored", lambda c: "auth")
    up = _Col(SyncStatusResponse.FULL_SYNC)
    _patch_collection(monkeypatch, up)
    sar.push("ignored", lambda c: "auth")
    assert (down.uploaded, up.uploaded) == (False, True)


def test_backup_lands_under_the_backup_root(monkeypatch, tmp_path):
    source = tmp_path / "collection.anki2"
    source.write_bytes(b"x" * 16)
    monkeypatch.setattr(sar, "BACKUP_ROOT", str(tmp_path / "backups"))
    made = sar.backup(str(source), "presync")
    assert os.path.exists(made)
    assert "presync-" in made
    assert Path(made).read_bytes() == b"x" * 16


def test_the_guard_brackets_the_import_not_the_whole_rebuild():
    """Dating a new card converts it to a review card, so `studied` grows by
    design. The earlier guard compared end-to-end and so aborted on its own
    intended change -- it would have stopped every real run before the upload.
    """
    source = _PATH.read_text(encoding="utf-8")
    assert "the import moved scheduling" in source
    assert "imported = review_state(col)" in source
    assert "expected_studied = imported[1] + made_due" in source
    # the end-to-end comparison that caused the false abort must be gone
    assert "after[1:] != before[1:]" not in source


def test_the_guard_still_fails_on_drift_it_should_catch():
    """Positive control for the arithmetic: the check passes only when the
    growth is exactly the cards asked for, and fails one either side."""

    def passes(imported, after, made_due):
        return after[1] == imported[1] + made_due and after[2] == imported[2]

    imported = (100, 50, 7)
    assert passes(imported, (162, 112, 7), 62)
    assert not passes(imported, (162, 113, 7), 62)  # one card too many
    assert not passes(imported, (162, 111, 7), 62)  # one too few
    assert not passes(imported, (162, 112, 6), 62)  # a suspend was lifted
