"""Contract tests for ``anki_tools.card_audio.audio_block``.

Written from the contract text alone -- ``audio_block``'s implementation is
never read by this file's author.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

from anki_tools.card_audio import audio_block

ID_RE = re.compile(r'id="([^"]*)"')
_PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_field_reference_appears_exactly_once():
    result = audio_block("Audio Perfective", "audio-perfective", "__x")
    assert result.count("{{Audio Perfective}}") == 1


def test_container_id_present():
    result = audio_block("Audio", "audio-perfective", "__x")
    assert 'id="audio-perfective"' in result


def test_data_span_id_present_and_referenced_in_script():
    result = audio_block("Audio", "audio-perfective", "__x")
    assert result.count("audio-perfective-data") >= 2
    assert 'id="audio-perfective-data"' in result


def test_controls_span_id_present():
    result = audio_block("Audio", "audio-perfective", "__x")
    assert 'id="audio-perfective-controls"' in result


def test_state_key_assigned_on_window():
    result = audio_block("Audio", "audio-perfective", "__mutableVerbPerfectiveChoice")
    assert "window.__mutableVerbPerfectiveChoice" in result


def test_two_parameterizations_share_no_identifier():
    first = audio_block("Audio Perfective", "audio-perfective", "__perfChoice")
    second = audio_block("Audio Imperfective", "audio-imperfective", "__impChoice")

    first_ids = [
        "audio-perfective",
        "audio-perfective-data",
        "audio-perfective-controls",
        "__perfChoice",
    ]
    second_ids = [
        "audio-imperfective",
        "audio-imperfective-data",
        "audio-imperfective-controls",
        "__impChoice",
    ]

    for identifier in first_ids:
        assert identifier not in second
    for identifier in second_ids:
        assert identifier not in first


def test_two_calls_concatenated_have_no_duplicated_id_attribute_value():
    first = audio_block("Audio Perfective", "audio-perfective", "__perfChoice")
    second = audio_block("Audio Imperfective", "audio-imperfective", "__impChoice")

    ids = ID_RE.findall(first + second)
    assert len(ids) == len(set(ids))
    assert len(ids) > 0


def test_module_imports_only_stdlib():
    script = (
        f"import sys; sys.path.insert(0, {str(_PACKAGE_ROOT)!r}); "
        "before = set(sys.modules); "
        "import anki_tools.card_audio; "
        "after = set(sys.modules) - before; "
        "after.discard('anki_tools'); "
        "print(sorted(m for m in after if not m.startswith('anki_tools.')))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )
    new_modules = eval(proc.stdout.strip())
    stdlib_module_names = set(sys.stdlib_module_names)
    non_stdlib = [m for m in new_modules if m.split(".")[0] not in stdlib_module_names]
    assert non_stdlib == []


@pytest.mark.parametrize(
    "field,dom_id,state_key",
    [
        ("Audio", "audio", "__immutableWordsAudioChoice"),
        (
            "Audio Imperfective",
            "audio-imperfective",
            "__mutableVerbImperfectiveChoice",
        ),
    ],
)
def test_result_is_non_empty_string(field, dom_id, state_key):
    result = audio_block(field, dom_id, state_key)
    assert isinstance(result, str)
    assert result != ""
