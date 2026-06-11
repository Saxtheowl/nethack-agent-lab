// Replay player: xterm.js renders the bytes; we drive playback frame by frame
// and use the server-built turn index for jumping by turn count.

const params = new URLSearchParams(location.search);
const GAME_ID = params.get("game");
if (!GAME_ID) { document.body.innerHTML = "<p>missing ?game=...</p>"; throw 0; }

const term = new Terminal({
  cols: 80, rows: 24,
  fontFamily: 'ui-monospace, "JetBrains Mono", "Cascadia Code", Menlo, monospace',
  fontSize: 16,
  theme: { background: "#000000", foreground: "#e6edf3" },
  scrollback: 200,
  disableStdin: true,
  convertEol: false,
});
term.open(document.getElementById("term"));

// --- state ----------------------------------------------------------------
let frames = null;        // [{relTs, len}], plus turnAtFrame, turnFirstFrame
let cursor = 0;           // index of last applied frame (exclusive: bytes 0..cursor have been fed)
let allBytes = null;      // Uint8Array of every frame's payload, concatenated
let frameOffsets = null;  // prefix sum: byte offset of frame i (i=0..N)
let playing = false;
let speed = 1;
let skipPauses = false;
let playTimer = null;

// --- DOM ------------------------------------------------------------------
const $ = (id) => document.getElementById(id);
const scrubber = $("scrubber");
const readoutTurn = $("readout-turn");
const readoutFrame = $("readout-frame");
const readoutFrames = $("readout-frames");
const readoutTime = $("readout-time");
const btnPlay = $("btn-play");

// --- helpers --------------------------------------------------------------
function bytesSlice(start, end) { return allBytes.subarray(frameOffsets[start], frameOffsets[end]); }

function resetTerm() {
  // Hard reset: \x1bc clears the screen, scrollback, attributes and cursor
  term.write("\x1bc");
}

function writeUpTo(target) {
  // Apply bytes from current cursor up to (exclusive) target. If target < cursor,
  // we have to rewind — there's no per-frame inverse for a terminal stream, so
  // we reset and replay from 0. This is fast enough up to ~5MB ttyrecs.
  if (target === cursor) return;
  if (target < cursor) {
    resetTerm();
    cursor = 0;
  }
  if (target > frames.frame_count) target = frames.frame_count;
  const slice = bytesSlice(cursor, target);
  if (slice.length) term.write(slice);
  cursor = target;
  updateReadouts();
}

function updateReadouts() {
  readoutFrame.textContent = cursor;
  const t = frames.turn_at_frame[Math.max(0, cursor - 1)];
  readoutTurn.textContent = t != null ? "T:" + t : "T:?";
  readoutTime.textContent = (cursor > 0 ? frames.rel_ts[cursor - 1] : 0).toFixed(1) + "s";
  scrubber.value = cursor;
}

// Cached sorted list of recorded turn numbers (built once frames load).
let sortedTurns = null;

function currentTurn() {
  if (cursor === 0) return 0;
  return frames.turn_at_frame[cursor - 1] || 0;
}

// Index in sortedTurns of the largest turn key <= cur.
function currentTurnIndex(cur) {
  if (!sortedTurns || !sortedTurns.length) return -1;
  let i = sortedTurns.length - 1;
  while (i >= 0 && sortedTurns[i] > cur) i--;
  return i;
}

function gotoTurnKey(turnKey) {
  const fi = frames.turn_first_frame[String(turnKey)];
  if (fi === undefined) return;
  writeUpTo(fi + 1);  // +1: include the frame that introduced this turn
}

// Absolute jump to a target turn number — picks the smallest recorded turn
// that is >= t (so "jump to T:50" lands at 50 or the next recorded turn).
function jumpToTurn(t) {
  if (!sortedTurns || !sortedTurns.length) return;
  if (t <= sortedTurns[0]) return gotoTurnKey(sortedTurns[0]);
  if (t >= sortedTurns[sortedTurns.length - 1]) return gotoTurnKey(sortedTurns[sortedTurns.length - 1]);
  // binary search-ish
  let target = sortedTurns[0];
  for (const k of sortedTurns) { if (k >= t) { target = k; break; } }
  gotoTurnKey(target);
}

// Relative move by `delta` *recorded turns*. Going back N takes you N entries
// earlier in the recorded turn list — predictable even when turns are sparse.
function nudgeTurn(delta) {
  if (!sortedTurns || !sortedTurns.length) return;
  const curIdx = currentTurnIndex(currentTurn());
  const newIdx = Math.max(0, Math.min(sortedTurns.length - 1, curIdx + delta));
  gotoTurnKey(sortedTurns[newIdx]);
}

function nudgeFrame(delta) {
  writeUpTo(Math.max(0, Math.min(frames.frame_count, cursor + delta)));
}

// --- play loop ------------------------------------------------------------
function tick() {
  if (!playing || cursor >= frames.frame_count) {
    stop();
    return;
  }
  const next = cursor + 1;
  writeUpTo(next);
  if (next >= frames.frame_count) { stop(); return; }
  const dtSec = (frames.rel_ts[next - 1] - (frames.rel_ts[next - 2] || 0));
  let waitMs;
  if (skipPauses) waitMs = 0;
  else waitMs = Math.max(0, Math.min(2000, dtSec * 1000 / speed));
  playTimer = setTimeout(tick, waitMs);
}
function play() {
  if (cursor >= frames.frame_count) writeUpTo(0);
  playing = true;
  btnPlay.textContent = "❚❚ pause";
  btnPlay.classList.add("active");
  tick();
}
function stop() {
  playing = false;
  if (playTimer) { clearTimeout(playTimer); playTimer = null; }
  btnPlay.textContent = "▶ play";
  btnPlay.classList.remove("active");
}
function toggle() { playing ? stop() : play(); }

// --- bootstrap ------------------------------------------------------------
async function init() {
  // metadata + per-frame index
  const meta = await (await fetch(`/api/games/${GAME_ID}`)).json();
  document.getElementById("title").textContent =
    `${GAME_ID}  —  ${meta.meta?.ascended ? "ASCENDED" : "no ascension"}  —  seed ${meta.meta?.seed ?? "?"}`;
  document.getElementById("meta-bar").textContent =
    `${meta.frame_count} frames · ${meta.duration_sec?.toFixed(1)}s real · final T:${meta.meta?.final_turn ?? "?"}`;

  frames = await (await fetch(`/api/games/${GAME_ID}/frames`)).json();
  sortedTurns = Object.keys(frames.turn_first_frame).map(Number).sort((a, b) => a - b);
  scrubber.max = frames.frame_count;
  readoutFrames.textContent = frames.frame_count;

  // Pre-fetch all bytes in one go. ttyrec sizes are typically a few MB — fine.
  const buf = await (await fetch(`/api/games/${GAME_ID}/bytes`)).arrayBuffer();
  allBytes = new Uint8Array(buf);
  // Reconstruct prefix sums from frame lengths
  frameOffsets = new Uint32Array(frames.frame_count + 1);
  let acc = 0;
  for (let i = 0; i < frames.frame_count; i++) {
    acc += frames.lengths[i];
    frameOffsets[i + 1] = acc;
  }

  updateReadouts();
  // auto-start paused at frame 0
}

// --- event wiring ---------------------------------------------------------
btnPlay.addEventListener("click", toggle);
$("btn-home").addEventListener("click",  () => { stop(); writeUpTo(0); });
$("btn-end").addEventListener("click",   () => { stop(); writeUpTo(frames.frame_count); });
$("btn-t-100").addEventListener("click", () => { stop(); nudgeTurn(-100); });
$("btn-t-10").addEventListener("click",  () => { stop(); nudgeTurn(-10); });
$("btn-t-1").addEventListener("click",   () => { stop(); nudgeTurn(-1); });
$("btn-t1").addEventListener("click",    () => { stop(); nudgeTurn(1); });
$("btn-t10").addEventListener("click",   () => { stop(); nudgeTurn(10); });
$("btn-t100").addEventListener("click",  () => { stop(); nudgeTurn(100); });
$("btn-f-1").addEventListener("click",   () => { stop(); nudgeFrame(-1); });
$("btn-f1").addEventListener("click",    () => { stop(); nudgeFrame(1); });

scrubber.addEventListener("input", (e) => {
  stop();
  writeUpTo(parseInt(e.target.value, 10));
});

document.querySelectorAll(".speeds button[data-speed]").forEach(b => {
  b.addEventListener("click", () => {
    document.querySelectorAll(".speeds button").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    if (b.id === "skip-pauses") { skipPauses = true; speed = 1; }
    else { skipPauses = false; speed = parseFloat(b.dataset.speed); }
  });
});

$("btn-jump").addEventListener("click", () => {
  const t = parseInt($("jump-turn").value, 10);
  if (!isNaN(t)) { stop(); jumpToTurn(t); }
});
$("jump-turn").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("btn-jump").click();
});

document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT") return;
  switch (e.key) {
    case " ":         e.preventDefault(); toggle(); break;
    case "Home":      e.preventDefault(); stop(); writeUpTo(0); break;
    case "End":       e.preventDefault(); stop(); writeUpTo(frames.frame_count); break;
    case "ArrowLeft":  e.preventDefault(); stop();
                       nudgeTurn(e.shiftKey ? -100 : e.ctrlKey ? -10 : -1); break;
    case "ArrowRight": e.preventDefault(); stop();
                       nudgeTurn(e.shiftKey ? 100 : e.ctrlKey ? 10 : 1); break;
    case "[":         e.preventDefault(); stop(); nudgeFrame(-1); break;
    case "]":         e.preventDefault(); stop(); nudgeFrame(1); break;
  }
});

init().catch(err => {
  term.write(`\r\n\x1b[31mload failed: ${err}\x1b[0m\r\n`);
  console.error(err);
});
