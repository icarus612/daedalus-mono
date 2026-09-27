"""Parameterized audio-picker block for the mutable/immutable-words card lanes.

Pure module -- standard library only, no `anki` imports.
"""

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
    )
