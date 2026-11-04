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


STATE = (100, 50, 7)


class _Db:
    def all(self, sql):
        return [(1, 1)]

    def scalar(self, sql):
        return 0


class _SummaryCol(_Col):
    db = _Db()


class _Harness:
    def __init__(self, monkeypatch, tmp_path):
        self.calls = []
        self.state = STATE
        self.root = tmp_path / "backups"
        package = tmp_path / "a.apkg"
        package.write_bytes(b"x")
        monkeypatch.setattr(sar, "BACKUP_ROOT", str(self.root))
        monkeypatch.setattr(sar, "PACKAGES", (str(package),))
        monkeypatch.setattr(sar, "anki_is_running", lambda: False)
        monkeypatch.setattr(sar, "review_state", lambda col: self.state)
        _patch_collection(monkeypatch, _SummaryCol(SyncStatusResponse.NO_CHANGES))
        self._patch_path(monkeypatch)
        self._record(monkeypatch, "credentials", ("user", "pw"))
        self._record(monkeypatch, "backup", "made", args=True)
        for name in ("pull", "rebuild", "push", "push_media"):
            self._record(monkeypatch, name, None, args=True)
        original = sar.record_snapshot

        def record_snapshot(path):
            self.calls.append("record_snapshot")
            return original(path)

        monkeypatch.setattr(sar, "record_snapshot", record_snapshot)

    @staticmethod
    def _patch_path(monkeypatch):
        import anki_tools.audio_naming as audio_naming

        monkeypatch.setattr(
            audio_naming, "get_anki_collection_path", lambda: "/fake/collection"
        )
        if hasattr(sar, "get_anki_collection_path"):
            monkeypatch.setattr(
                sar, "get_anki_collection_path", lambda: "/fake/collection"
            )

    def _record(self, monkeypatch, name, result, args=False):
        def fake(*a, **kw):
            self.calls.append((name, a[1]) if name == "backup" else name)
            return result

        monkeypatch.setattr(sar, name, fake)

    def names(self):
        return [c if isinstance(c, str) else f"{c[0]}:{c[1]}" for c in self.calls]


@pytest.fixture
def harness(monkeypatch, tmp_path):
    return _Harness(monkeypatch, tmp_path)


def test_stages_are_the_four_named_ones():
    assert sar.STAGES == ("pull", "rebuild", "push", "all")


@pytest.mark.parametrize(
    "argv,expected",
    [
        ([], "all"),
        (["--stage", "pull"], "pull"),
        (["--stage", "rebuild"], "rebuild"),
        (["--stage", "push"], "push"),
        (["--stage", "all"], "all"),
    ],
)
def test_parse_args_stage(argv, expected):
    assert sar.parse_args(argv).stage == expected


def test_parse_args_rejects_an_unknown_stage():
    with pytest.raises(SystemExit):
        sar.parse_args(["--stage", "sideways"])


def test_main_without_args_ignores_sys_argv_and_means_all(harness, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--stage", "pull"])
    assert sar.main() == 0
    assert "rebuild" in harness.calls and "push" in harness.calls


@pytest.mark.parametrize(
    "state",
    [(0, 0, 0), (1, 2, 3), (100, 50, 7)],
)
def test_snapshot_round_trips(monkeypatch, tmp_path, state):
    monkeypatch.setattr(sar, "BACKUP_ROOT", str(tmp_path / "new" / "root"))
    sar.save_snapshot(state)
    assert sar.snapshot_file() == os.path.join(sar.BACKUP_ROOT, "review-state.json")
    assert os.path.exists(sar.snapshot_file())
    assert sar.load_snapshot() == state


@pytest.mark.parametrize(
    "content",
    [
        None,
        "",
        "{not json",
        "[1, 2]",
        "[1, 2, 3, 4]",
        '"abc"',
        "null",
        '["a", "b", "c"]',
        "[1.5, 2, 3]",
        "{}",
    ],
)
def test_load_snapshot_is_none_when_absent_or_malformed(monkeypatch, tmp_path, content):
    monkeypatch.setattr(sar, "BACKUP_ROOT", str(tmp_path))
    if content is not None:
        Path(sar.snapshot_file()).write_text(content, encoding="utf-8")
    assert sar.load_snapshot() is None


def test_snapshot_problem_none_when_matching(harness):
    sar.save_snapshot(STATE)
    assert sar.snapshot_problem(object()) is None


def test_snapshot_problem_on_absent_snapshot_names_snapshot_and_rebuild(harness):
    message = sar.snapshot_problem(object())
    assert "snapshot" in message and "rebuild" in message


def test_snapshot_problem_on_malformed_snapshot_names_snapshot_and_rebuild(harness):
    harness.root.mkdir()
    Path(sar.snapshot_file()).write_text("{oops", encoding="utf-8")
    message = sar.snapshot_problem(object())
    assert "snapshot" in message and "rebuild" in message


def test_snapshot_problem_on_mismatch_shows_both_states(harness):
    sar.save_snapshot(STATE)
    harness.state = (101, 50, 7)
    message = sar.snapshot_problem(object())
    assert "reviewed" in message
    assert "100" in message and "101" in message


def test_record_snapshot_saves_returns_and_closes(monkeypatch, tmp_path):
    col = _Col(SyncStatusResponse.NO_CHANGES)
    _patch_collection(monkeypatch, col)
    monkeypatch.setattr(sar, "BACKUP_ROOT", str(tmp_path))
    monkeypatch.setattr(sar, "review_state", lambda c: STATE)
    assert sar.record_snapshot("ignored") == STATE
    assert sar.load_snapshot() == STATE
    assert col.closed


def test_record_snapshot_closes_the_collection_when_the_state_read_fails(
    monkeypatch, tmp_path
):
    col = _Col(SyncStatusResponse.NO_CHANGES)
    _patch_collection(monkeypatch, col)
    monkeypatch.setattr(sar, "BACKUP_ROOT", str(tmp_path))

    def boom(c):
        raise RuntimeError("db gone")

    monkeypatch.setattr(sar, "review_state", boom)
    with pytest.raises(RuntimeError):
        sar.record_snapshot("ignored")
    assert col.closed
    assert sar.load_snapshot() is None


def test_pull_stage_calls_only_pull_and_backups(harness):
    assert sar.main(["--stage", "pull"]) == 0
    assert harness.names() == [
        "credentials",
        "backup:presync",
        "pull",
        "backup:postpull",
    ]


def test_pull_stage_is_not_blocked_by_a_missing_package(harness, monkeypatch, tmp_path):
    monkeypatch.setattr(sar, "PACKAGES", (str(tmp_path / "nope.apkg"),))
    assert sar.main(["--stage", "pull"]) == 0
    assert "pull" in harness.calls


@pytest.mark.parametrize("stage", ["rebuild", "push", "all"])
def test_other_stages_are_blocked_by_a_missing_package(
    harness, monkeypatch, tmp_path, capsys, stage
):
    monkeypatch.setattr(sar, "PACKAGES", (str(tmp_path / "nope.apkg"),))
    assert sar.main(["--stage", stage]) == 2
    assert "missing package" in capsys.readouterr().err
    assert harness.calls == []


@pytest.mark.parametrize("stage", ["pull", "rebuild", "push", "all"])
def test_every_stage_refuses_while_anki_runs(harness, monkeypatch, capsys, stage):
    monkeypatch.setattr(sar, "anki_is_running", lambda: True)
    assert sar.main(["--stage", stage]) == 2
    assert "close it first" in capsys.readouterr().err
    assert harness.calls == []


def test_push_stage_with_a_matching_snapshot_pushes_then_syncs_media(harness):
    sar.save_snapshot(STATE)
    assert sar.main(["--stage", "push"]) == 0
    assert harness.names() == [
        "credentials",
        "backup:prepush",
        "push",
        "push_media",
    ]


def _refusal_cases():
    return ["running", "package", "absent", "stale", "malformed"]


@pytest.mark.parametrize("case", _refusal_cases())
def test_push_stage_refuses_before_credentials_backup_or_push(
    harness, monkeypatch, tmp_path, capsys, case
):
    if case == "running":
        sar.save_snapshot(STATE)
        monkeypatch.setattr(sar, "anki_is_running", lambda: True)
    elif case == "package":
        sar.save_snapshot(STATE)
        monkeypatch.setattr(sar, "PACKAGES", (str(tmp_path / "nope.apkg"),))
    elif case == "stale":
        sar.save_snapshot(STATE)
        harness.state = (STATE[0] + 1, STATE[1], STATE[2])
    elif case == "malformed":
        harness.root.mkdir()
        Path(sar.snapshot_file()).write_text("[1, 2]", encoding="utf-8")
    assert sar.main(["--stage", "push"]) == 2
    assert capsys.readouterr().err.strip()
    assert harness.calls == []


def test_push_stage_stale_snapshot_message_mentions_reviewed(harness, capsys):
    sar.save_snapshot(STATE)
    harness.state = (STATE[0] + 1, STATE[1], STATE[2])
    sar.main(["--stage", "push"])
    assert "reviewed" in capsys.readouterr().err


def test_push_stage_absent_snapshot_message_points_at_rebuild(harness, capsys):
    sar.main(["--stage", "push"])
    err = capsys.readouterr().err
    assert "snapshot" in err and "rebuild" in err


def test_push_stage_closes_the_collection_it_opened_for_the_check(harness, monkeypatch):
    col = _SummaryCol(SyncStatusResponse.NO_CHANGES)
    _patch_collection(monkeypatch, col)
    sar.save_snapshot(STATE)
    sar.main(["--stage", "push"])
    assert col.closed


def test_rebuild_stage_rebuilds_then_records_and_never_syncs(harness):
    assert sar.main(["--stage", "rebuild"]) == 0
    assert harness.names() == [
        "backup:prerebuild",
        "rebuild",
        "record_snapshot",
    ]
    assert sar.load_snapshot() == STATE


def test_rebuild_stage_prints_the_snapshot_state(harness, capsys):
    sar.main(["--stage", "rebuild"])
    out = capsys.readouterr().out
    assert all(str(n) in out for n in STATE)


def test_rebuild_then_push_is_the_positive_path(harness):
    assert sar.main(["--stage", "rebuild"]) == 0
    harness.calls.clear()
    assert sar.main(["--stage", "push"]) == 0
    assert "push" in harness.calls and "push_media" in harness.calls


def test_all_stage_runs_pull_rebuild_push_in_order(harness):
    assert sar.main(["--stage", "all"]) == 0
    assert _in_order(
        harness.names(),
        ["backup:presync", "pull", "backup:postpull", "rebuild", "record_snapshot"]
        + ["push", "push_media"],
    )
    assert sar.load_snapshot() == STATE


def _in_order(seen, expected):
    positions = [seen.index(item) for item in expected]
    return positions == sorted(positions)


def test_all_stage_equals_the_default(harness):
    sar.main(["--stage", "all"])
    explicit = list(harness.calls)
    harness.calls.clear()
    sar.main()
    assert harness.calls == explicit


def test_all_stage_aborts_before_push_when_state_changes_after_recording(
    harness, monkeypatch, capsys
):
    original = sar.record_snapshot

    def record_then_drift(path):
        result = original(path)
        harness.state = (STATE[0] + 1, STATE[1], STATE[2])
        return result

    monkeypatch.setattr(sar, "record_snapshot", record_then_drift)
    assert sar.main(["--stage", "all"]) == 2
    assert "push" not in harness.calls and "push_media" not in harness.calls
    assert "reviewed" in capsys.readouterr().err


@pytest.mark.parametrize(
    "stage,failing",
    [
        ("pull", "pull"),
        ("all", "pull"),
        ("rebuild", "rebuild"),
        ("all", "rebuild"),
        ("push", "push"),
        ("all", "push"),
        ("push", "push_media"),
        ("all", "push_media"),
    ],
)
def test_anki_errors_return_one(harness, monkeypatch, capsys, stage, failing):
    from anki.errors import AnkiException

    sar.save_snapshot(STATE)

    def boom(*a, **kw):
        raise AnkiException("kaput")

    monkeypatch.setattr(sar, failing, boom)
    assert sar.main(["--stage", stage]) == 1
    assert "anki error" in capsys.readouterr().err
