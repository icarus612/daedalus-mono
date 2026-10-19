"""Contract tests for ``anki_tools.card_audio.audio_block``.

Written from the contract text alone -- ``audio_block``'s implementation is
never read by this file's author.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

from anki_tools.card_audio import (
    AUDIO_BUTTON_CSS,
    BUTTON_CLASS,
    LINE_CLASS,
    SMALL_BUTTON_CLASS,
    audio_block,
    audio_line_block,
)

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


def test_button_carries_stable_class():
    result = audio_block("Audio", "audio", "__x")
    assert f'button.className = "{BUTTON_CLASS}";' in result


def test_button_text_and_click_handler_unchanged():
    result = audio_block("Audio", "audio", "__x")
    assert 'button.textContent = "▶";' in result
    assert "audio.currentTime = 0;" in result
    assert "audio.play();" in result


def test_button_appended_after_audio_element():
    result = audio_block("Audio", "audio", "__x")
    audio_index = result.index("container.appendChild(audio);")
    button_index = result.index("container.appendChild(button);")
    assert audio_index < button_index


def test_audio_button_css_targets_button_class():
    assert f".{BUTTON_CLASS} {{" in AUDIO_BUTTON_CSS
    assert f".{BUTTON_CLASS}:hover" in AUDIO_BUTTON_CSS
    assert f".{BUTTON_CLASS}:active" in AUDIO_BUTTON_CSS


def test_audio_line_block_references_its_field_exactly_once():
    result = audio_line_block("Audio Perfective", "aspect-audio", "perfective")
    assert result.count("{{Audio Perfective}}") == 1


def test_audio_line_block_never_autoplays():
    result = audio_line_block("Audio Perfective", "aspect-audio", "perfective")
    assert "autoplay" not in result


def test_audio_line_block_button_carries_both_classes():
    result = audio_line_block("Audio Perfective", "aspect-audio", "perfective")
    assert f'"{BUTTON_CLASS} {SMALL_BUTTON_CLASS}"' in result


def test_audio_line_block_makes_the_whole_line_a_click_target():
    result = audio_line_block("Audio Imperfective", "aspect-audio", "imperfective")
    assert 'document.getElementById("imperfective")' in result
    assert f'line.classList.add("{LINE_CLASS}")' in result
    assert 'line.addEventListener("click"' in result


def test_audio_line_block_slot_and_line_ids_are_independent():
    result = audio_line_block("Audio Perfective", "slot-x", "row-y")
    assert 'id="slot-x"' in result
    assert 'document.getElementById("row-y")' in result
    assert "slot-y" not in result and "row-x" not in result


def test_audio_line_block_bails_out_on_an_empty_field():
    result = audio_line_block("Audio Perfective", "aspect-audio", "perfective")
    assert "if (!text) return;" in result


def test_audio_line_block_is_idempotent_per_render():
    result = audio_line_block("Audio Perfective", "aspect-audio", "perfective")
    assert 'slot.querySelector("button")' in result


def test_small_button_and_line_classes_are_styled():
    assert f".{SMALL_BUTTON_CLASS} {{" in AUDIO_BUTTON_CSS
    assert f".{LINE_CLASS} {{" in AUDIO_BUTTON_CSS
    assert "cursor: pointer" in AUDIO_BUTTON_CSS.split(f".{LINE_CLASS} {{")[1]
