const params = new URLSearchParams(location.search);
const GAME_ID = params.get("game");
if (!GAME_ID) {
  document.body.innerHTML = "<p>missing ?game=...</p>";
  throw new Error("missing game id");
}

const term = new Terminal({
  cols: 80,
  rows: 24,
  fontFamily: 'ui-monospace, "Cascadia Code", Menlo, Consolas, monospace',
  fontSize: 16,
  theme: { background: "#000000", foreground: "#e6edf3" },
  scrollback: 200,
  disableStdin: true,
  convertEol: false,
});
term.open(document.getElementById("term"));

let frames = null;
let cursor = 0;
let allBytes = null;
let frameOffsets = null;
let playing = false;
let speed = 1;
let skipPauses = false;
let playTimer = null;
let sortedTurns = null;

const $ = (id) => document.getElementById(id);
const scrubber = $("scrubber");
const readoutTurn = $("readout-turn");
const readoutFrame = $("readout-frame");
const readoutFrames = $("readout-frames");
const readoutTime = $("readout-time");
const btnPlay = $("btn-play");

function bytesSlice(start, end) {
  return allBytes.subarray(frameOffsets[start], frameOffsets[end]);
}

function resetTerm() {
  term.write("\x1bc");
}

function updateReadouts() {
  readoutFrame.textContent = cursor;
  const t = frames.turn_at_frame[Math.max(0, cursor - 1)];
  readoutTurn.textContent = t != null ? "T:" + t : "T:?";
  readoutTime.textContent = (cursor > 0 ? frames.rel_ts[cursor - 1] : 0).toFixed(1) + "s";
  scrubber.value = cursor;
}

function writeUpTo(target) {
  if (!frames) return;
  if (target === cursor) return;
  if (target < cursor) {
    resetTerm();
    cursor = 0;
  }
  target = Math.max(0, Math.min(frames.frame_count, target));
  const slice = bytesSlice(cursor, target);
  if (slice.length) term.write(slice);
  cursor = target;
  updateReadouts();
}

function currentTurn() {
  if (cursor === 0) return 0;
  return frames.turn_at_frame[cursor - 1] || 0;
}

function currentTurnIndex(cur) {
  if (!sortedTurns || !sortedTurns.length) return -1;
  let i = sortedTurns.length - 1;
  while (i >= 0 && sortedTurns[i] > cur) i--;
  return i;
}

function gotoTurnKey(turnKey) {
  const fi = frames.turn_first_frame[String(turnKey)];
  if (fi === undefined) return;
  writeUpTo(fi + 1);
}

function jumpToTurn(t) {
  if (!sortedTurns || !sortedTurns.length) return;
  if (t <= sortedTurns[0]) return gotoTurnKey(sortedTurns[0]);
  if (t >= sortedTurns[sortedTurns.length - 1]) return gotoTurnKey(sortedTurns[sortedTurns.length - 1]);
  for (const k of sortedTurns) {
    if (k >= t) return gotoTurnKey(k);
  }
}

function nudgeTurn(delta) {
  if (!sortedTurns || !sortedTurns.length) return;
  const curIdx = currentTurnIndex(currentTurn());
  const newIdx = Math.max(0, Math.min(sortedTurns.length - 1, curIdx + delta));
  gotoTurnKey(sortedTurns[newIdx]);
}

function nudgeFrame(delta) {
  writeUpTo(Math.max(0, Math.min(frames.frame_count, cursor + delta)));
}

function tick() {
  if (!playing || cursor >= frames.frame_count) {
    stop();
    return;
  }
  const next = cursor + 1;
  writeUpTo(next);
  if (next >= frames.frame_count) {
    stop();
    return;
  }
  const dtSec = frames.rel_ts[next - 1] - (frames.rel_ts[next - 2] || 0);
  const waitMs = skipPauses ? 0 : Math.max(0, Math.min(2000, dtSec * 1000 / speed));
  playTimer = setTimeout(tick, waitMs);
}

function play() {
  if (cursor >= frames.frame_count) writeUpTo(0);
  playing = true;
  btnPlay.textContent = "pause";
  btnPlay.classList.add("active");
  tick();
}

function stop() {
  playing = false;
  if (playTimer) {
    clearTimeout(playTimer);
    playTimer = null;
  }
  btnPlay.textContent = "play";
  btnPlay.classList.remove("active");
}

function toggle() {
  playing ? stop() : play();
}

function seedText(meta) {
  if (meta.seed !== null && meta.seed !== undefined && meta.seed !== "") return meta.seed;
  return meta.seed_source || "?";
}

async function init() {
  const meta = await (await fetch(`/api/games/${encodeURIComponent(GAME_ID)}`)).json();
  document.getElementById("title").textContent =
    `${GAME_ID} - ${meta.meta?.ascended ? "ASCENDED" : "attempt"} - seed ${seedText(meta.meta || {})}`;
  document.getElementById("meta-bar").textContent =
    `${meta.frame_count} frames · ${meta.duration_sec?.toFixed(1)}s real`;

  frames = await (await fetch(`/api/games/${encodeURIComponent(GAME_ID)}/frames`)).json();
  sortedTurns = Object.keys(frames.turn_first_frame).map(Number).sort((a, b) => a - b);
  scrubber.max = frames.frame_count;
  readoutFrames.textContent = frames.frame_count;

  const buf = await (await fetch(`/api/games/${encodeURIComponent(GAME_ID)}/bytes`)).arrayBuffer();
  allBytes = new Uint8Array(buf);
  frameOffsets = new Uint32Array(frames.frame_count + 1);
  let acc = 0;
  for (let i = 0; i < frames.frame_count; i++) {
    acc += frames.lengths[i];
    frameOffsets[i + 1] = acc;
  }
  updateReadouts();
}

btnPlay.addEventListener("click", toggle);
$("btn-home").addEventListener("click", () => { stop(); writeUpTo(0); });
$("btn-end").addEventListener("click", () => { stop(); writeUpTo(frames.frame_count); });
$("btn-t-100").addEventListener("click", () => { stop(); nudgeTurn(-100); });
$("btn-t-10").addEventListener("click", () => { stop(); nudgeTurn(-10); });
$("btn-t-1").addEventListener("click", () => { stop(); nudgeTurn(-1); });
$("btn-t1").addEventListener("click", () => { stop(); nudgeTurn(1); });
$("btn-t10").addEventListener("click", () => { stop(); nudgeTurn(10); });
$("btn-t100").addEventListener("click", () => { stop(); nudgeTurn(100); });
$("btn-f-1").addEventListener("click", () => { stop(); nudgeFrame(-1); });
$("btn-f1").addEventListener("click", () => { stop(); nudgeFrame(1); });

scrubber.addEventListener("input", (e) => {
  stop();
  writeUpTo(parseInt(e.target.value, 10));
});

document.querySelectorAll(".speeds button[data-speed]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".speeds button").forEach((x) => x.classList.remove("active"));
    button.classList.add("active");
    if (button.id === "skip-pauses") {
      skipPauses = true;
      speed = 1;
    } else {
      skipPauses = false;
      speed = parseFloat(button.dataset.speed);
    }
  });
});

$("btn-jump").addEventListener("click", () => {
  const t = parseInt($("jump-turn").value, 10);
  if (!isNaN(t)) {
    stop();
    jumpToTurn(t);
  }
});
$("jump-turn").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("btn-jump").click();
});

document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT") return;
  switch (e.key) {
    case " ":
      e.preventDefault();
      toggle();
      break;
    case "Home":
      e.preventDefault();
      stop();
      writeUpTo(0);
      break;
    case "End":
      e.preventDefault();
      stop();
      writeUpTo(frames.frame_count);
      break;
    case "ArrowLeft":
      e.preventDefault();
      stop();
      nudgeTurn(e.shiftKey ? -100 : e.ctrlKey ? -10 : -1);
      break;
    case "ArrowRight":
      e.preventDefault();
      stop();
      nudgeTurn(e.shiftKey ? 100 : e.ctrlKey ? 10 : 1);
      break;
    case "[":
      e.preventDefault();
      stop();
      nudgeFrame(-1);
      break;
    case "]":
      e.preventDefault();
      stop();
      nudgeFrame(1);
      break;
  }
});

init().catch((err) => {
  term.write(`\r\n\x1b[31mload failed: ${err}\x1b[0m\r\n`);
  console.error(err);
});
