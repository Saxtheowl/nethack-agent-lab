"use strict";

// Palette xterm 16 couleurs (les glyphes NetHack n'utilisent pas plus).
const ANSI = {
  black: "#1a1a1a", red: "#d64545", green: "#4fb04f", brown: "#b58b2a",
  blue: "#4f7fd6", magenta: "#b657c7", cyan: "#3fb0b0", white: "#c7cdd9",
  brightblack: "#5a6072", brightred: "#ff6b6b", brightgreen: "#7bd88f",
  yellow: "#ffcf5a", brightblue: "#6ab7ff", brightmagenta: "#e08fff",
  brightcyan: "#66e0e0", brightwhite: "#ffffff",
};
const DEFAULT_FG = "#c7cdd9";
const DEFAULT_BG = "#000000";

function colorFor(name, bold, isBg) {
  if (name === "default") return isBg ? DEFAULT_BG : DEFAULT_FG;
  if (typeof name === "number") {
    // xterm 256 -> on reste simple, on mappe les 16 premiers.
    const base = ["black","red","green","brown","blue","magenta","cyan","white",
      "brightblack","brightred","brightgreen","yellow","brightblue","brightmagenta","brightcyan","brightwhite"];
    if (name < 16) name = base[name];
    else return isBg ? DEFAULT_BG : DEFAULT_FG;
  }
  if (!isBg && bold) {
    const map = { black:"brightblack", red:"brightred", green:"brightgreen",
      brown:"yellow", blue:"brightblue", magenta:"brightmagenta", cyan:"brightcyan", white:"brightwhite" };
    if (map[name]) name = map[name];
  }
  return ANSI[name] || (isBg ? DEFAULT_BG : DEFAULT_FG);
}

const escapeHtml = (s) => s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

// ---------- état global ----------
const state = {
  index: null,
  activeRun: null,
  kit: "strict", // strict = parties honnêtes uniquement (défaut)
  epFilter: "all",
  epSearch: "",
  epSort: { key: "episode", dir: 1 },
};

function visibleRuns() {
  const runs = state.index.runs;
  if (state.kit === "strict") return runs.filter((r) => r.clean);
  if (state.kit === "cheat") return runs.filter((r) => !r.clean);
  return runs;
}

const $ = (sel, root = document) => root.querySelector(sel);
const el = (tag, cls, html) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (html != null) node.innerHTML = html;
  return node;
};

// ---------- chargement de l'index ----------
async function loadIndex() {
  const res = await fetch("/api/index");
  if (!res.ok) throw new Error("index indisponible");
  state.index = await res.json();
  $("#root-path").textContent = state.index.root;
  renderSidebar();
  const runs = visibleRuns();
  if (!state.activeRun && runs.length) {
    selectRun(runs[runs.length - 1].name);
  } else if (state.activeRun) {
    renderRun(state.activeRun);
  }
}

function rateColor(rate) {
  if (rate == null) return { bg: "#2a3145", fg: "#8592ad" };
  if (rate >= 0.8) return { bg: "rgba(123,216,143,0.16)", fg: "#7bd88f" };
  if (rate >= 0.5) return { bg: "rgba(255,207,90,0.16)", fg: "#ffcf5a" };
  if (rate >= 0.2) return { bg: "rgba(255,180,84,0.16)", fg: "#ffb454" };
  return { bg: "rgba(255,107,122,0.14)", fg: "#ff6b7a" };
}

// ---------- sidebar : runs groupés par famille ----------
function renderSidebar() {
  const nav = $("#sidebar");
  nav.innerHTML = "";
  const runs = visibleRuns();
  const kitLabel = { strict: "strict", all: "tous", cheat: "triche" }[state.kit];
  nav.appendChild(el("div", "side-section-title", `Runs · ${kitLabel} (${runs.length})`));

  const families = new Map();
  for (const run of runs) {
    if (!families.has(run.family)) families.set(run.family, []);
    families.get(run.family).push(run);
  }
  const famNames = [...families.keys()].sort();

  for (const fam of famNames) {
    const runs = families.get(fam).sort((a, b) => a.name.localeCompare(b.name));
    const totalEps = runs.reduce((s, r) => s + r.episodes, 0);
    const totalWin = runs.reduce((s, r) => s + r.successes, 0);

    const wrap = el("div", "run-family");
    const head = el("div", "run-family-head");
    head.appendChild(el("span", "caret", "▼"));
    head.appendChild(el("span", null, fam));
    const rate = totalEps ? totalWin / totalEps : null;
    const c = rateColor(rate);
    const cnt = el("span", "run-family-count",
      rate == null ? `${runs.length}` : `${(rate * 100).toFixed(0)}% · ${runs.length}`);
    cnt.style.color = c.fg;
    head.appendChild(cnt);
    head.onclick = () => wrap.classList.toggle("collapsed");
    wrap.appendChild(head);

    const list = el("div", "run-list");
    if (runs.length === 1) wrap.classList.add(""); // single run families rester ouvertes
    for (const run of runs) {
      const item = el("div", "run-item");
      item.dataset.run = run.name;
      if (run.name === state.activeRun) item.classList.add("active");
      const nameRow = el("div", "run-name");
      nameRow.textContent = run.name;
      if (!run.clean) nameRow.appendChild(el("span", "cheat-badge", "triche"));
      item.appendChild(nameRow);
      const meta = el("div", "run-meta");
      const rc = rateColor(run.win_rate);
      const badge = el("span", "rate-badge",
        run.win_rate == null ? "—" : `${(run.win_rate * 100).toFixed(0)}%`);
      badge.style.background = rc.bg;
      badge.style.color = rc.fg;
      meta.appendChild(badge);
      meta.appendChild(el("span", "run-eps", `${run.episodes} ép · ${run.replays}▶`));
      item.appendChild(meta);
      item.onclick = () => selectRun(run.name);
      list.appendChild(item);
    }
    wrap.appendChild(list);
    // familles volumineuses repliées par défaut, sauf celle active
    if (runs.length > 6 && !runs.some((r) => r.name === state.activeRun)) {
      wrap.classList.add("collapsed");
    }
    nav.appendChild(wrap);
  }
}

function selectRun(name) {
  state.activeRun = name;
  state.epSearch = "";
  document.querySelectorAll(".run-item").forEach((n) =>
    n.classList.toggle("active", n.dataset.run === name));
  renderRun(name);
}

// ---------- panneau run ----------
function runInfo(name) { return state.index.runs.find((r) => r.name === name); }
function runEpisodes(name) { return state.index.episodes.filter((e) => e.run === name); }

function renderRun(name) {
  const info = runInfo(name);
  const main = $("#main");
  main.innerHTML = "";
  if (!info) { main.appendChild(el("div", "empty", "Run introuvable.")); return; }

  const header = el("div", "run-header");
  const h1 = el("h1", "run-title", escapeHtml(info.name));
  if (!info.clean) h1.appendChild(el("span", "cheat-badge big", "triche · avantages"));
  header.appendChild(h1);
  const bits = [];
  if (info.character) bits.push(`<code>${escapeHtml(info.character)}</code>`);
  if (info.nethack) bits.push(`NetHack ${escapeHtml(info.nethack)}`);
  if (info.max_steps) bits.push(`${info.max_steps} steps max`);
  if (info.wizard != null) bits.push(info.wizard ? "wizard" : "non-wizard");
  if (info.started_at) bits.push(escapeHtml(String(info.started_at).slice(0, 19).replace("T", " ")));
  header.appendChild(el("div", "run-sub", bits.join(" · ")));
  main.appendChild(header);

  // cartes de stats
  const cards = el("div", "stat-cards");
  const rate = info.win_rate;
  const rc = rateColor(rate);
  const winCard = el("div", "stat-card");
  winCard.appendChild(el("div", "k", "Taux Minetown"));
  const v = el("div", "v", rate == null ? "—" : `${(rate * 100).toFixed(1)}%`);
  v.style.color = rc.fg;
  winCard.appendChild(v);
  const bar = el("div", "winbar");
  bar.appendChild(Object.assign(el("i"), { style: `width:${(rate || 0) * 100}%` }));
  winCard.appendChild(bar);
  if (info.wilson_95) {
    winCard.appendChild(el("div", "wilson-note",
      `Wilson 95% : ${(info.wilson_95[0] * 100).toFixed(1)}–${(info.wilson_95[1] * 100).toFixed(1)}%`));
  }
  cards.appendChild(winCard);

  cards.appendChild(statCard("Épisodes", info.episodes));
  cards.appendChild(statCard("Succès", info.successes, "#7bd88f"));
  cards.appendChild(statCard("Échecs", info.episodes - info.successes, "#ff6b7a"));
  cards.appendChild(statCard("Steps médians (succès)",
    info.median_success_steps ?? "—", null, true));
  cards.appendChild(statCard("Replays", info.replays, "#6ab7ff"));
  main.appendChild(cards);

  // causes d'échec
  const causes = info.failure_causes || {};
  const causeEntries = Object.entries(causes).sort((a, b) => b[1] - a[1]);
  if (causeEntries.length) {
    const box = el("div", "causes");
    box.appendChild(el("div", "side-section-title", "Causes d'échec"));
    const max = Math.max(...causeEntries.map((c) => c[1]));
    for (const [cause, count] of causeEntries) {
      const row = el("div", "cause-row");
      row.appendChild(el("div", "cause-label", escapeHtml(cause)));
      const cbar = el("div", "cause-bar");
      cbar.appendChild(Object.assign(el("i"), { style: `width:${(count / max) * 100}%` }));
      row.appendChild(cbar);
      row.appendChild(el("div", "cause-count", String(count)));
      box.appendChild(row);
    }
    main.appendChild(box);
  }

  renderEpisodeTable(main, name);
}

function statCard(k, val, color, small) {
  const card = el("div", "stat-card");
  card.appendChild(el("div", "k", k));
  const v = el("div", small ? "v small" : "v", String(val));
  if (color) v.style.color = color;
  card.appendChild(v);
  return card;
}

// ---------- tableau des épisodes ----------
function renderEpisodeTable(main, name) {
  const toolbar = el("div", "ep-toolbar");
  const seg = el("div", "seg");
  for (const [key, lbl] of [["all", "Tous"], ["success", "Succès"], ["failure", "Échecs"]]) {
    const btn = el("button", state.epFilter === key ? "active" : "", lbl);
    btn.onclick = () => { state.epFilter = key; renderRun(name); };
    seg.appendChild(btn);
  }
  toolbar.appendChild(seg);
  const search = el("input", "ep-search");
  search.placeholder = "filtrer (cause, message, ep…)";
  search.value = state.epSearch;
  search.oninput = () => { state.epSearch = search.value; refreshRows(name); };
  toolbar.appendChild(search);
  const count = el("div", "ep-count");
  count.id = "ep-count";
  toolbar.appendChild(count);
  main.appendChild(toolbar);

  const table = el("table", "ep-table");
  const cols = [
    ["episode", "Ep"], ["outcome", "Résultat"], ["steps", "Steps"],
    ["turn", "Turn"], ["depth", "Dlvl"], ["xp", "Xp"],
    ["hp", "HP"], ["cause", "Cause / message"],
  ];
  const thead = el("thead");
  const tr = el("tr");
  for (const [key, lbl] of cols) {
    const th = el("th", null, lbl);
    if (state.epSort.key === key) {
      th.appendChild(el("span", "arrow", state.epSort.dir > 0 ? " ▲" : " ▼"));
    }
    th.onclick = () => {
      if (state.epSort.key === key) state.epSort.dir *= -1;
      else state.epSort = { key, dir: 1 };
      refreshRows(name);
    };
    tr.appendChild(th);
  }
  thead.appendChild(tr);
  table.appendChild(thead);
  const tbody = el("tbody");
  tbody.id = "ep-tbody";
  table.appendChild(tbody);
  main.appendChild(table);

  refreshRows(name);
}

function sortValue(ep, key) {
  switch (key) {
    case "outcome": return ep.success ? 1 : 0;
    case "cause": return ep.failure_cause || ep.last_message || "";
    case "hp": return ep.hp ?? -1;
    default: return ep[key] ?? -1;
  }
}

function refreshRows(name) {
  const tbody = $("#ep-tbody");
  if (!tbody) return;
  let eps = runEpisodes(name);
  if (state.epFilter === "success") eps = eps.filter((e) => e.success);
  else if (state.epFilter === "failure") eps = eps.filter((e) => !e.success);
  const q = state.epSearch.trim().toLowerCase();
  if (q) {
    eps = eps.filter((e) => {
      const hay = [e.episode, e.failure_cause, e.failure_hint, e.last_message]
        .map((x) => String(x ?? "").toLowerCase()).join(" ");
      return hay.includes(q);
    });
  }
  const { key, dir } = state.epSort;
  eps = eps.slice().sort((a, b) => {
    const va = sortValue(a, key), vb = sortValue(b, key);
    if (va < vb) return -dir;
    if (va > vb) return dir;
    return a.episode - b.episode;
  });

  tbody.innerHTML = "";
  for (const ep of eps) {
    const tr = el("tr", ep.has_replay ? "playable" : "no-replay");
    const out = ep.success
      ? '<span class="outcome-pill win">MINETOWN</span>'
      : `<span class="outcome-pill loss">${escapeHtml(ep.failure_cause || "échec")}</span>`;
    const causeText = ep.success
      ? (ep.last_message || "")
      : (ep.failure_hint ? `${ep.failure_hint} — ` : "") + (ep.last_message || "");
    const playCell = ep.has_replay ? '<span class="play-icon">▶</span> ' : "";
    tr.innerHTML =
      `<td>${playCell}${ep.episode}</td>` +
      `<td>${out}</td>` +
      `<td>${ep.steps ?? "—"}</td>` +
      `<td>${ep.turn ?? "—"}</td>` +
      `<td>${ep.depth ?? "—"}</td>` +
      `<td>${ep.xp ?? "—"}</td>` +
      `<td>${ep.hp ?? "—"}${ep.hpmax != null ? "/" + ep.hpmax : ""}</td>` +
      `<td class="col-msg" title="${escapeHtml(causeText)}">${escapeHtml(causeText)}</td>`;
    if (ep.has_replay) tr.onclick = () => openPlayer(name, ep);
    tbody.appendChild(tr);
  }
  const cnt = $("#ep-count");
  if (cnt) cnt.textContent = `${eps.length} épisode${eps.length > 1 ? "s" : ""}`;
}

// ---------- lecteur de replay ----------
const player = {
  data: null,
  frame: 0,
  playing: false,
  speed: 4,
  timer: null,
  overlay: null,
  meta: null,
};

async function fetchReplay(run, episode) {
  const res = await fetch(`/api/replay?run=${encodeURIComponent(run)}&episode=${episode}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

function buildPlayerDom() {
  if (player.overlay) return;
  const overlay = el("div");
  overlay.id = "player-overlay";
  overlay.innerHTML = `
    <div class="player">
      <div class="player-head">
        <span class="player-title" id="pl-title"></span>
        <span class="spacer"></span>
        <a class="dl" id="pl-dl" title="Télécharger le ttyrec">⬇ ttyrec</a>
        <button class="close-btn" id="pl-close">×</button>
      </div>
      <div class="screen-wrap"><div id="screen"></div></div>
      <div class="player-controls">
        <div class="timeline">
          <span class="turn-badge" id="pl-turn"></span>
          <input type="range" id="scrub" min="0" max="0" value="0">
          <span class="frame-count" id="pl-frames"></span>
        </div>
        <div class="buttons-row">
          <button class="pbtn" id="pl-first" title="Début (g)">⏮</button>
          <button class="pbtn" id="pl-prev" title="Frame précédente (←)">◀</button>
          <button class="pbtn play" id="pl-play" title="Play/Pause (espace)">▶</button>
          <button class="pbtn" id="pl-next" title="Frame suivante (→)">▶|</button>
          <button class="pbtn" id="pl-last" title="Fin (G)">⏭</button>
          <div class="speed-group">
            <label>vitesse</label>
            <button class="pbtn" id="pl-slower" title="Moins vite (-)">−</button>
            <span class="speed-val" id="pl-speed"></span>
            <button class="pbtn" id="pl-faster" title="Plus vite (+)">+</button>
          </div>
          <span class="input-badge" id="pl-input" title="Touche envoyée par l'agent"></span>
          <span class="keyhint">espace · ←/→ · g/G · +/− · f frame-input · q</span>
        </div>
      </div>
      <div class="player-foot" id="pl-foot"></div>
    </div>`;
  document.body.appendChild(overlay);
  player.overlay = overlay;

  $("#pl-close").onclick = closePlayer;
  overlay.onclick = (e) => { if (e.target === overlay) closePlayer(); };
  $("#pl-play").onclick = togglePlay;
  $("#pl-first").onclick = () => seekFrame(0);
  $("#pl-last").onclick = () => seekFrame(player.data.t.length - 1);
  $("#pl-prev").onclick = () => { pause(); seekFrame(player.frame - 1); };
  $("#pl-next").onclick = () => { pause(); seekFrame(player.frame + 1); };
  $("#pl-slower").onclick = () => setSpeed(player.speed / 1.5);
  $("#pl-faster").onclick = () => setSpeed(player.speed * 1.5);
  $("#scrub").oninput = (e) => { pause(); seekFrame(+e.target.value); };
}

async function openPlayer(run, ep) {
  buildPlayerDom();
  player.overlay.classList.add("open");
  player.meta = ep;
  $("#pl-title").innerHTML =
    `${escapeHtml(run)} · ep ${ep.episode} ` +
    (ep.success ? '<span class="ep-out outcome-pill win">MINETOWN</span>'
      : `<span class="ep-out outcome-pill loss">${escapeHtml(ep.failure_cause || "échec")}</span>`);
  $("#pl-dl").href = `/api/ttyrec?run=${encodeURIComponent(run)}&episode=${ep.episode}`;
  $("#screen").innerHTML = '<div class="pl-loading">Décodage du ttyrec…</div>';
  $("#pl-foot").textContent = "";
  try {
    player.data = await fetchReplay(run, ep.episode);
  } catch (e) {
    $("#screen").innerHTML = `<div class="pl-loading">Erreur : ${escapeHtml(e.message)}</div>`;
    return;
  }
  player.frame = 0;
  player.playing = false;
  setSpeed(4);
  const n = player.data.t.length;
  $("#scrub").max = String(Math.max(0, n - 1));
  buildInputMap();
  renderFrame(0);
  // démarrage automatique de la lecture
  play();
}

// index frame -> dernière touche agent connue (pour l'affichage)
function buildInputMap() {
  const map = new Array(player.data.t.length).fill(null);
  for (const [frameIdx, key] of player.data.inputs) {
    for (let i = frameIdx; i < map.length; i++) {
      if (map[i] === null) map[i] = key; else break;
    }
  }
  player.inputMap = map;
}

function closePlayer() {
  pause();
  player.overlay.classList.remove("open");
  player.data = null;
}

function setSpeed(s) {
  player.speed = Math.max(0.5, Math.min(60, s));
  $("#pl-speed").textContent = `${player.speed.toFixed(1)}×`;
}

function renderFrame(i) {
  const d = player.data;
  if (!d) return;
  i = Math.max(0, Math.min(d.t.length - 1, i));
  player.frame = i;
  const grid = d.grid[i];
  const [cx, cy] = d.cursor[i];
  const lines = [];
  for (let y = 0; y < grid.length; y++) {
    lines.push(renderRow(d.pool[grid[y]], y === cy ? cx : -1));
  }
  $("#screen").innerHTML = lines.join("\n");

  $("#scrub").value = String(i);
  $("#pl-frames").textContent = `${i + 1} / ${d.t.length}  ·  ${d.t[i].toFixed(1)}s`;
  const turnLine = d.pool[grid[grid.length - 1]];
  const turnText = turnLine.map((s) => s[0]).join("");
  const m = turnText.match(/T:(\d+)/);
  $("#pl-turn").textContent = m ? `T ${m[1]}` : "";
  const key = player.inputMap ? player.inputMap[i] : null;
  $("#pl-input").textContent = key ? `⌨ ${key}` : "";
  if (player.meta) {
    const meta = player.meta;
    $("#pl-foot").textContent =
      `frame ${i + 1}/${d.t.length} · steps ${meta.steps ?? "?"} · ` +
      (meta.failure_hint ? `hint ${meta.failure_hint} · ` : "") +
      (meta.last_message ? `« ${meta.last_message} »` : "");
  }
}

function renderRow(segments, cursorX) {
  // Reconstruit la ligne caractère par caractère seulement si le curseur est dessus,
  // sinon on émet des <span> par segment (bien plus rapide).
  if (cursorX < 0) {
    let html = "";
    for (const [text, fg, bg, flags] of segments) {
      html += styledSpan(text, fg, bg, flags, -1, 0);
    }
    return html || " ";
  }
  let html = "";
  let x = 0;
  for (const [text, fg, bg, flags] of segments) {
    if (cursorX >= x && cursorX < x + text.length) {
      const rel = cursorX - x;
      html += styledSpan(text.slice(0, rel), fg, bg, flags, -1, 0);
      html += `<span class="cursor">${escapeHtml(text[rel])}</span>`;
      html += styledSpan(text.slice(rel + 1), fg, bg, flags, -1, 0);
    } else {
      html += styledSpan(text, fg, bg, flags, -1, 0);
    }
    x += text.length;
  }
  // curseur au-delà du dernier caractère
  if (cursorX >= x) html += '<span class="cursor"> </span>';
  return html || " ";
}

function styledSpan(text, fg, bg, flags, cursorRel) {
  if (!text) return "";
  const bold = flags & 1, reverse = flags & 2, underline = flags & 4;
  let f = colorFor(fg, bold, false);
  let b = colorFor(bg, false, true);
  if (reverse) { const t = f; f = b === DEFAULT_BG ? DEFAULT_FG : b; b = t; }
  const styles = [`color:${f}`];
  if (b !== DEFAULT_BG) styles.push(`background:${b}`);
  if (underline) styles.push("text-decoration:underline");
  return `<span style="${styles.join(";")}">${escapeHtml(text)}</span>`;
}

function seekFrame(i) { renderFrame(i); }

function play() {
  if (!player.data || player.playing) return;
  player.playing = true;
  $("#pl-play").textContent = "⏸";
  scheduleNext();
}
function pause() {
  player.playing = false;
  $("#pl-play").textContent = "▶";
  if (player.timer) { clearTimeout(player.timer); player.timer = null; }
}
function togglePlay() { player.playing ? pause() : play(); }

function scheduleNext() {
  if (!player.playing) return;
  const d = player.data;
  if (player.frame + 1 >= d.t.length) { pause(); return; }
  const dt = Math.max(0, d.t[player.frame + 1] - d.t[player.frame]);
  // délai réel borné, accéléré par la vitesse.
  const delay = Math.min(0.4, dt) / player.speed * 1000;
  player.timer = setTimeout(() => {
    renderFrame(player.frame + 1);
    scheduleNext();
  }, Math.max(8, delay));
}

// ---------- clavier ----------
document.addEventListener("keydown", (e) => {
  if (!player.overlay || !player.overlay.classList.contains("open")) return;
  if (e.target.tagName === "INPUT" && e.target.id !== "scrub") return;
  const d = player.data;
  switch (e.key) {
    case " ": e.preventDefault(); togglePlay(); break;
    case "ArrowRight": e.preventDefault(); pause(); seekFrame(player.frame + 1); break;
    case "ArrowLeft": e.preventDefault(); pause(); seekFrame(player.frame - 1); break;
    case "g": seekFrame(0); break;
    case "G": if (d) seekFrame(d.t.length - 1); break;
    case "+": case "=": setSpeed(player.speed * 1.5); break;
    case "-": case "_": setSpeed(player.speed / 1.5); break;
    case "f": if (d) jumpToNextInput(); break;
    case "q": case "Escape": closePlayer(); break;
  }
});

// saute à la prochaine frame associée à une touche agent
function jumpToNextInput() {
  pause();
  for (const [frameIdx] of player.data.inputs) {
    if (frameIdx > player.frame) { seekFrame(frameIdx); return; }
  }
}

// ---------- toggle kit strict/tous/triche ----------
document.querySelectorAll("#kit-seg button").forEach((btn) => {
  btn.onclick = () => {
    state.kit = btn.dataset.kit;
    document.querySelectorAll("#kit-seg button").forEach((b) =>
      b.classList.toggle("active", b === btn));
    const runs = visibleRuns();
    if (!runs.some((r) => r.name === state.activeRun)) {
      state.activeRun = runs.length ? runs[runs.length - 1].name : null;
    }
    renderSidebar();
    if (state.activeRun) renderRun(state.activeRun);
    else $("#main").innerHTML = '<div class="empty">Aucun run pour ce filtre.</div>';
  };
});

// ---------- démarrage ----------
$("#refresh-btn").onclick = () => loadIndex();
loadIndex().catch((e) => {
  $("#main").innerHTML = `<div class="empty">Erreur de chargement : ${escapeHtml(e.message)}</div>`;
});
