"""Where the cue lands relative to the word, rendered in headless WebKit."""

import pytest

from anki_tools import prompt_hint

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

MEASURE_JS = """
() => {
  const word = document.getElementById('translation').getBoundingClientRect();
  const hint = document.getElementById('prompt-hint');
  const rect = hint.getBoundingClientRect();
  return {wordTop: word.top, wordBottom: word.bottom, hintTop: rect.top,
          hintBottom: rect.bottom, hintHeight: rect.height,
          hintRects: hint.getClientRects().length};
}
"""


@pytest.fixture(scope="module")
def page():
    try:
        playwright = sync_playwright().start()
    except Exception as error:  # pragma: no cover
        pytest.skip(f"WebKit unavailable: playwright did not start: {error}")
    try:
        browser = playwright.webkit.launch()
    except Exception as error:  # pragma: no cover
        playwright.stop()
        pytest.skip(f"WebKit unavailable: {error}")
    yield browser.new_page()
    browser.close()
    playwright.stop()


def _render(page, word_html, cue, width=390):
    page.set_viewport_size({"width": width, "height": 900})
    page.set_content(
        "<!doctype html><html><head>"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<style>.card {{ font-size: 30px; text-align: center; }}"
        f'{prompt_hint.PROMPT_HINT_CSS}</style></head><body><div class="card">'
        f'<div class="cue-row"><span id="translation">{word_html}</span>\n'
        f'<span id="prompt-hint">{cue}</span></div></div></body></html>'
    )
    return page.evaluate(MEASURE_JS)


def test_single_line_word_keeps_the_cue_beside_it(page):
    m = _render(page, "business", "(an affair)")
    assert m["hintTop"] < m["wordBottom"], m


def test_multi_line_word_puts_the_cue_on_its_own_line_below(page):
    m = _render(page, "up to<br>until", "(a point)")
    assert m["hintTop"] >= m["wordBottom"] - 1, m


def test_a_cue_that_does_not_fit_drops_whole_rather_than_splitting(page):
    m = _render(
        page, "until / before (when)", "(as far as a point; before a time)", width=500
    )
    assert m["hintTop"] >= m["wordBottom"] - 1, m
    assert m["hintRects"] == 1, m


def test_empty_cue_takes_no_space_under_a_multi_line_word(page):
    m = _render(page, "up to<br>until", "")
    assert m["hintHeight"] == 0, m
