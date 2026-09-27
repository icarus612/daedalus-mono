"""Contract tests for anki_tools.renumber_russian_decks, written blind to its
implementation from the CLI/module contract alone."""

import os
import sys

import anki.collection
import pytest
from anki.collection import Collection
from anki.errors import DBError

import anki_tools.renumber_russian_decks as rrd
from anki_tools.renumber_russian_decks import (
    DECK_PREFIX,
    RENAMES,
    PrecheckError,
    apply_plan,
    build_parser,
    build_plan,
    full_deck_name,
    main,
    precheck,
)

MODULE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "anki_tools",
    "renumber_russian_decks.py",
)


def _add_card(col, deck_id, front, back="a"):
    note = col.new_note(col.models.by_name("Basic"))
    note["Front"] = front
    note["Back"] = back
    col.add_note(note, deck_id)
    return note.cards()[0]


def _seed_subtree(col):
    layout = [
        (full_deck_name("1. Alphabet"), 1),
        (full_deck_name("2. Immutable Words"), 2),
        (full_deck_name("2. Immutable Words") + "::a. Listening", 3),
        (full_deck_name("3. Sentences (lingo llama)"), 4),
        (full_deck_name("3. Sentences (lingo llama)") + "::a. Listening", 5),
        (full_deck_name("3. Sentences (lingo llama)") + "::b. Recall", 6),
        (full_deck_name("4. 100 Words & Phrases"), 7),
        (full_deck_name("5. Master Russian 300+"), 8),
    ]
    for name, n_cards in layout:
        did = col.decks.id(name)
        for i in range(n_cards):
            _add_card(col, did, front=f"{name} #{i}")
    return {name: col.decks.id(name) for name, _ in layout}


def _full_snapshot(col):
    return {
        entry.id: (col.decks.name(entry.id), col.decks.card_count([entry.id], False))
        for entry in col.decks.all_names_and_ids()
    }


def _run_cli(argv, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["anki-renumber-russian-decks", *argv])
    try:
        main()
    except SystemExit as exc:
        return exc.code if exc.code is not None else 0
    return 0


@pytest.fixture
def collection(tmp_path):
    col = Collection(os.path.join(str(tmp_path), "test.anki2"))
    try:
        yield col
    finally:
        col.close()


def test_deck_prefix_is_the_russian_subtree_path():
    assert DECK_PREFIX == "Languages::Russian::"


def test_full_deck_name_prefixes_the_short_name():
    assert full_deck_name("3. Sentences (lingo llama)") == (
        DECK_PREFIX + "3. Sentences (lingo llama)"
    )


def test_renames_tuple_matches_the_contracted_pairs_and_order():
    assert RENAMES == (
        ("3. Sentences (lingo llama)", "4. Sentences (lingo llama)"),
        ("4. 100 Words & Phrases", "5. 100 Words & Phrases"),
        ("5. Master Russian 300+", "6. Master Russian 300+"),
    )


def test_build_plan_forward_is_full_names_in_reverse_of_renames_order():
    plan = build_plan(revert=False)
    assert plan == tuple(
        (full_deck_name(old), full_deck_name(new)) for old, new in reversed(RENAMES)
    )


def test_build_plan_revert_is_inverse_pairs_in_reverse_of_renames_order():
    plan = build_plan(revert=True)
    assert plan == tuple(
        (full_deck_name(new), full_deck_name(old)) for old, new in reversed(RENAMES)
    )


def test_precheck_passes_when_every_target_name_is_free(collection):
    _seed_subtree(collection)
    precheck(collection, build_plan(revert=False))


def test_precheck_raises_when_a_target_name_already_exists(collection):
    _seed_subtree(collection)
    collection.decks.id(full_deck_name("6. Master Russian 300+"))
    with pytest.raises(PrecheckError):
        precheck(collection, build_plan(revert=False))


def test_build_parser_prog_name():
    assert build_parser().prog == "anki-renumber-russian-decks"


def test_parser_defaults_have_no_flags_set():
    args = build_parser().parse_args([])
    assert args.collection is None
    assert args.backup_dir is None
    assert args.no_backup is False
    assert args.dry_run is False
    assert args.yes is False
    assert args.revert is False


def test_parser_accepts_short_yes_flag():
    args = build_parser().parse_args(["-y"])
    assert args.yes is True


def test_full_apply_renames_top_and_child_decks_preserves_ids_and_counts(
    tmp_path, monkeypatch
):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    before = _full_snapshot(col)
    col.close()

    exit_code = _run_cli(["--yes", "--collection", col_path], monkeypatch)
    assert exit_code == 0

    col2 = Collection(col_path)
    try:
        after = _full_snapshot(col2)
    finally:
        col2.close()

    assert set(before) == set(after)
    renamed_full = {full_deck_name(old): full_deck_name(new) for old, new in RENAMES}
    for did, (old_name, count) in before.items():
        expected_name = old_name
        for old_prefix, new_prefix in renamed_full.items():
            if old_name == old_prefix or old_name.startswith(old_prefix + "::"):
                expected_name = old_name.replace(old_prefix, new_prefix, 1)
                break
        assert after[did] == (expected_name, count)


def test_revert_round_trip_restores_original_names_ids_and_counts(
    tmp_path, monkeypatch
):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    before = _full_snapshot(col)
    col.close()

    assert _run_cli(["--yes", "--collection", col_path], monkeypatch) == 0
    assert _run_cli(["--revert", "--yes", "--collection", col_path], monkeypatch) == 0

    col2 = Collection(col_path)
    try:
        after = _full_snapshot(col2)
    finally:
        col2.close()

    assert after == before


def test_e2e_forward_apply_issues_renames_in_reverse_of_renames_order(
    tmp_path, monkeypatch
):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    deck_manager_cls = type(col.decks)
    col.close()

    calls = []
    original_rename = deck_manager_cls.rename

    def _wrapper(self, deck, new_name):
        calls.append(new_name)
        return original_rename(self, deck, new_name)

    monkeypatch.setattr(deck_manager_cls, "rename", _wrapper)

    assert _run_cli(["--yes", "--collection", col_path], monkeypatch) == 0
    assert calls == [full_deck_name(new) for _, new in reversed(RENAMES)]


def test_e2e_revert_apply_issues_renames_in_reverse_pairs_order(tmp_path, monkeypatch):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    deck_manager_cls = type(col.decks)
    col.close()

    assert _run_cli(["--yes", "--collection", col_path], monkeypatch) == 0

    calls = []
    original_rename = deck_manager_cls.rename

    def _wrapper(self, deck, new_name):
        calls.append(new_name)
        return original_rename(self, deck, new_name)

    monkeypatch.setattr(deck_manager_cls, "rename", _wrapper)

    assert _run_cli(["--revert", "--yes", "--collection", col_path], monkeypatch) == 0
    assert calls == [full_deck_name(old) for old, _ in reversed(RENAMES)]


def test_apply_plan_returns_the_applied_pairs(collection):
    _seed_subtree(collection)
    plan = build_plan(revert=False)
    applied = apply_plan(collection, plan)
    assert list(applied) == list(plan)


def test_e2e_precheck_failure_makes_no_backup_and_no_rename(tmp_path, monkeypatch):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    col.decks.id(full_deck_name("6. Master Russian 300+"))
    before = _full_snapshot(col)
    col.close()

    backup_calls = []
    monkeypatch.setattr(
        Collection,
        "create_backup",
        lambda self, **kwargs: backup_calls.append(kwargs) or True,
    )

    exit_code = _run_cli(["--yes", "--collection", col_path], monkeypatch)
    assert exit_code != 0
    assert backup_calls == []

    col2 = Collection(col_path)
    try:
        after = _full_snapshot(col2)
    finally:
        col2.close()
    assert after == before


def test_collection_is_closed_even_when_precheck_fails(tmp_path, monkeypatch):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    col.decks.id(full_deck_name("6. Master Russian 300+"))
    col.close()

    exit_code = _run_cli(["--yes", "--collection", col_path], monkeypatch)
    assert exit_code != 0

    col2 = Collection(col_path)
    col2.close()


def test_e2e_dry_run_prints_plan_backs_up_but_mutates_nothing(
    tmp_path, monkeypatch, capsys
):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    before = _full_snapshot(col)
    col.close()

    backup_calls = []
    monkeypatch.setattr(
        Collection,
        "create_backup",
        lambda self, **kwargs: backup_calls.append(kwargs) or True,
    )

    mtime_before = os.path.getmtime(col_path)
    exit_code = _run_cli(["--dry-run", "--yes", "--collection", col_path], monkeypatch)
    mtime_after = os.path.getmtime(col_path)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert len(backup_calls) == 1
    assert mtime_before == mtime_after

    for old, new in RENAMES:
        assert full_deck_name(old) in captured.out
        assert full_deck_name(new) in captured.out

    col2 = Collection(col_path)
    try:
        after = _full_snapshot(col2)
    finally:
        col2.close()
    assert after == before


@pytest.mark.parametrize("answer", ["n", "N", "", "no", "maybe"])
def test_confirmation_prompt_declined_variants_abort_without_renaming(
    tmp_path, monkeypatch, answer
):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    before = _full_snapshot(col)
    col.close()

    monkeypatch.setattr("builtins.input", lambda prompt="": answer)
    exit_code = _run_cli(["--collection", col_path], monkeypatch)
    assert exit_code != 0

    col2 = Collection(col_path)
    try:
        after = _full_snapshot(col2)
    finally:
        col2.close()
    assert after == before


@pytest.mark.parametrize("answer", ["y", "Y"])
def test_confirmation_prompt_accepted_variants_apply_renames(
    tmp_path, monkeypatch, answer
):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    col.close()

    monkeypatch.setattr("builtins.input", lambda prompt="": answer)
    exit_code = _run_cli(["--collection", col_path], monkeypatch)
    assert exit_code == 0

    col2 = Collection(col_path)
    try:
        assert col2.decks.by_name(full_deck_name("6. Master Russian 300+")) is not None
        assert col2.decks.by_name(full_deck_name("5. Master Russian 300+")) is None
    finally:
        col2.close()


def test_yes_flag_never_calls_input(tmp_path, monkeypatch):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    col.close()

    def _forbidden(prompt=""):
        raise AssertionError("input must not be called")

    monkeypatch.setattr("builtins.input", _forbidden)
    exit_code = _run_cli(["--yes", "--collection", col_path], monkeypatch)
    assert exit_code == 0


def test_backup_call_precedes_first_rename_call(tmp_path, monkeypatch):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    deck_manager_cls = type(col.decks)
    col.close()

    events = []
    original_backup = Collection.create_backup
    original_rename = deck_manager_cls.rename

    def _backup_wrapper(self, **kwargs):
        events.append("backup")
        return original_backup(self, **kwargs)

    def _rename_wrapper(self, deck, new_name):
        events.append("rename")
        return original_rename(self, deck, new_name)

    monkeypatch.setattr(Collection, "create_backup", _backup_wrapper)
    monkeypatch.setattr(deck_manager_cls, "rename", _rename_wrapper)

    exit_code = _run_cli(["--yes", "--collection", col_path], monkeypatch)
    assert exit_code == 0

    first_rename_index = events.index("rename")
    assert "backup" in events[:first_rename_index]


def test_no_backup_flag_skips_the_backup_call(tmp_path, monkeypatch):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    col.close()

    backup_calls = []
    monkeypatch.setattr(
        Collection,
        "create_backup",
        lambda self, **kwargs: backup_calls.append(kwargs) or True,
    )

    exit_code = _run_cli(
        ["--yes", "--no-backup", "--collection", col_path], monkeypatch
    )
    assert exit_code == 0
    assert backup_calls == []


def test_default_backup_dir_is_collection_dir_slash_backups(tmp_path, monkeypatch):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    col.close()

    seen_dirs = []
    real_backup = Collection.create_backup

    def _wrapper(self, **kwargs):
        seen_dirs.append(kwargs.get("backup_folder"))
        return real_backup(self, **kwargs)

    monkeypatch.setattr(Collection, "create_backup", _wrapper)

    exit_code = _run_cli(["--yes", "--collection", col_path], monkeypatch)
    assert exit_code == 0
    assert seen_dirs == [os.path.join(str(tmp_path), "backups")]


def test_backup_dir_flag_overrides_the_default_backup_folder(tmp_path, monkeypatch):
    col_path = str(tmp_path / "test.anki2")
    col = Collection(col_path)
    _seed_subtree(col)
    col.close()

    custom_dir = str(tmp_path / "custom-backups")
    seen_dirs = []
    real_backup = Collection.create_backup

    def _wrapper(self, **kwargs):
        seen_dirs.append(kwargs.get("backup_folder"))
        return real_backup(self, **kwargs)

    monkeypatch.setattr(Collection, "create_backup", _wrapper)

    exit_code = _run_cli(
        ["--yes", "--backup-dir", custom_dir, "--collection", col_path],
        monkeypatch,
    )
    assert exit_code == 0
    assert seen_dirs == [custom_dir]


def test_dberror_on_open_prints_two_line_message_and_exits_nonzero(
    tmp_path, monkeypatch, capsys
):
    col_path = str(tmp_path / "test.anki2")
    Collection(col_path).close()

    def _raise_dberror(*args, **kwargs):
        raise DBError(
            "Anki already open, or media currently syncing.", None, None, None
        )

    monkeypatch.setattr(anki.collection, "Collection", _raise_dberror)
    if hasattr(rrd, "Collection"):
        monkeypatch.setattr(rrd, "Collection", _raise_dberror)

    exit_code = _run_cli(["--yes", "--collection", col_path], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code != 0
    assert (
        "Could not open the collection: "
        "Anki already open, or media currently syncing." in captured.out
    )
    assert "Make sure Anki is not running when you execute this script." in captured.out


def test_implementation_does_not_hardcode_the_real_collection_path_twice():
    with open(MODULE_PATH, encoding="utf-8") as handle:
        source = handle.read()
    assert source.count("Anki2/User 1/collection.anki2") <= 1
