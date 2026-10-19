"""Parameterized audio-picker block for the mutable/immutable-words card lanes.

Pure module -- standard library only, no `anki` imports.
"""

# Shared by every caller so the button's class and its CSS never drift apart.
BUTTON_CLASS = "audio-play"

# The counterpart-aspect line's own smaller button, and the class that marks
# the whole line as a click target for it.
SMALL_BUTTON_CLASS = "audio-play-sm"
LINE_CLASS = "audio-line"

AUDIO_BUTTON_CSS = (
    f".{BUTTON_CLASS} {{\n"
    "\tdisplay: inline-flex;\n"
    "\talign-items: center;\n"
    "\tjustify-content: center;\n"
    "\twidth: 3rem;\n"
    "\theight: 3rem;\n"
    "\tpadding: 0;\n"
    "\tborder: none;\n"
    "\tborder-radius: 50%;\n"
    "\tbackground-color: #605C8B;\n"
    "\tcolor: white;\n"
    "\tfont-size: 1.4rem;\n"
    "\tline-height: 1;\n"
    "\tcursor: pointer;\n"
    "}\n\n"
    f".{BUTTON_CLASS}:hover {{\n"
    "\topacity: .85;\n"
    "}\n\n"
    f".{BUTTON_CLASS}:active {{\n"
    "\topacity: .7;\n"
    "}\n\n"
    f".{SMALL_BUTTON_CLASS} {{\n"
    "\twidth: 1.8rem;\n"
    "\theight: 1.8rem;\n"
    "\tfont-size: .8rem;\n"
    "}\n\n"
    f".{LINE_CLASS} {{\n"
    "\tcursor: pointer;\n"
    "}"
)

_TEMPLATE = r"""<!-- Audio field holds a plain-text, comma/newline-separated list of
     bare media filenames -- it is NOT wrapped in Anki's own sound-tag
     syntax. Anki's backend autoplays every sound-tagged reference in
     a field, in order, before any template JS runs, so three tagged
     recordings would play back to back with no way for JS to
     suppress or reorder that queue. Keeping the field as plain text
     lets the script below pick and play just one.

     The pick must survive unchanged from the question render to the
     answer render of the SAME review: `afmt` always re-embeds the
     question's rendered HTML via `{{FrontSide}}`, which re-runs this
     very script a second time whenever a template places this div on
     the question side -- without this logic that second run would
     call Math.random() again and autoplay a DIFFERENT file than the
     one just heard. The script defers its work with setTimeout(fn, 0)
     because it runs at parse time, before the answer side's own
     `#back` element has actually been inserted into the page --
     checking for it synchronously would never see it. Once deferred,
     document.getElementById("back") reliably tells a pure
     question-side render (no #back anywhere yet) apart from any
     answer-side render (#back always exists by then, whether this
     particular audio div started life on the question side and got
     duplicated in via FrontSide, or lives on the answer side alone).
     window.__immutableWordsAudioChoice carries the chosen filename
     across exactly one such question->answer duplication; every fresh
     render -- every question-side render, or an answer-side render
     whose stored choice doesn't belong to THIS note's own file list
     (a template that only ever shows audio on the answer side, or a
     global left over from a different note reviewed a moment ago) --
     overwrites it with a new random pick, so a later review of the
     same card rolls a fresh voice rather than repeating one forever.
     The script also renders a <button> so the native R-key replay
     isn't simply lost, on both sides, always pointing at whichever
     file this render actually chose or reused. -->
<div id="@@DOM_ID@@"><span id="@@DOM_ID@@-data" class="hidden">{{@@FIELD@@}}</span>
<span id="@@DOM_ID@@-controls"></span></div>
<script>
(function () {
  var data = document.getElementById("@@DOM_ID@@-data");
  if (!data) return;
  var text = data.textContent.trim();
  if (!text) return;
  var files = text
    .split(/[,\n]+/)
    .map(function (f) { return f.trim(); })
    .filter(function (f) { return f.length > 0; });
  if (files.length === 0) return;
  setTimeout(function () {
    var container = document.getElementById("@@DOM_ID@@");
    if (!container) return;
    var onAnswerSide = !!document.getElementById("back");
    var previous = window.@@STATE_KEY@@;
    var reusable = onAnswerSide && !!previous && files.indexOf(previous) !== -1;
    var chosen = reusable
      ? previous
      : files[Math.floor(Math.random() * files.length)];
    window.@@STATE_KEY@@ = chosen;
    var audio = document.createElement("audio");
    audio.autoplay = !reusable;
    audio.src = chosen;
    var button = document.createElement("button");
    button.className = "@@BUTTON_CLASS@@";
    button.textContent = "▶";
    button.addEventListener("click", function () {
      audio.currentTime = 0;
      audio.play();
    });
    container.appendChild(audio);
    container.appendChild(button);
  }, 0);
})();
</script>
"""


def audio_block(field: str, dom_id: str, state_key: str) -> str:
    """Render the audio-picker HTML+JS block for one field/container/state key."""
    return (
        _TEMPLATE.replace("@@FIELD@@", field)
        .replace("@@DOM_ID@@", dom_id)
        .replace("@@STATE_KEY@@", state_key)
        .replace("@@BUTTON_CLASS@@", BUTTON_CLASS)
    )


_LINE_TEMPLATE = (
    r"""<span id="@@SLOT_ID@@"><span id="@@SLOT_ID@@-data" class="hidden">"""
    r"""{{@@FIELD@@}}</span></span>"""
    r"""
<script>
(function () {
  var data = document.getElementById("@@SLOT_ID@@-data");
  if (!data) return;
  var text = data.textContent.trim();
  if (!text) return;
  var files = text
    .split(/[,\n]+/)
    .map(function (f) { return f.trim(); })
    .filter(function (f) { return f.length > 0; });
  if (files.length === 0) return;
  setTimeout(function () {
    var slot = document.getElementById("@@SLOT_ID@@");
    var line = document.getElementById("@@LINE_ID@@");
    if (!slot || !line || slot.querySelector("button")) return;
    var audio = document.createElement("audio");
    audio.src = files[Math.floor(Math.random() * files.length)];
    var button = document.createElement("button");
    button.type = "button";
    button.className = "@@BUTTON_CLASS@@ @@SMALL_BUTTON_CLASS@@";
    button.textContent = "▶";
    slot.appendChild(audio);
    slot.appendChild(button);
    line.classList.add("@@LINE_CLASS@@");
    line.addEventListener("click", function () {
      audio.currentTime = 0;
      audio.play();
    });
  }, 0);
})();
</script>
"""
)


def audio_line_block(field: str, slot_id: str, line_id: str) -> str:
    """A counterpart word's play button, and its whole line as a click target.

    Unlike `audio_block` this never autoplays. The line it decorates is
    reference material shown beside an answer -- the card's own recording
    has just played (or is playing) on that same side, and a second
    autoplaying clip would talk over it. The button is the affordance; the
    click handler sits on `line_id` so tapping anywhere on the row plays it.

    One file is picked per render and kept for that render, so the button
    and the row always play the same clip. There is no cross-render state
    key because this block only ever lives on an answer side, never
    duplicated in by `{{FrontSide}}`.
    """
    return (
        _LINE_TEMPLATE.replace("@@FIELD@@", field)
        .replace("@@SLOT_ID@@", slot_id)
        .replace("@@LINE_ID@@", line_id)
        .replace("@@SMALL_BUTTON_CLASS@@", SMALL_BUTTON_CLASS)
        .replace("@@BUTTON_CLASS@@", BUTTON_CLASS)
        .replace("@@LINE_CLASS@@", LINE_CLASS)
    )
