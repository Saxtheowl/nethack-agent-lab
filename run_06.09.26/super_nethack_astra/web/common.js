/* Shared code for the alternative dashboards (/ui/a, /ui/b, /ui/c):
   terminal renderer, game loader (frames + events), small helpers. */
'use strict';
const $ = s => document.querySelector(s);
const el = (tag, props = {}, ...kids) => { const e = Object.assign(document.createElement(tag), props); for (const k of kids) if (k != null && k !== '') e.append(k); return e; };
const api = async p => { const r = await fetch(p, {cache: 'no-store'}); if (!r.ok) throw new Error(p + ' ' + r.status); return r.json(); };
const fmtN = n => (n ?? 0).toLocaleString('fr-FR');
const fmtT = t => new Date(t * 1000).toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'});
const STATUS_FR = {live: 'en direct', dead: 'morte', saved: 'sauvegardée', ascended: 'ASCENSION', stopped: 'arrêtée', quit: 'abandonnée'};

/* ---- terminal ---- */
class Term {
  constructor(node, {x1 = 144, y0 = 0, y1 = 36, fitHeight = false} = {}) {
    Object.assign(this, {node, x1, y0, y1, fitHeight});
    node.classList.add('term'); node.textContent = '';
    this.rows = []; this.cache = [];
    for (let y = y0; y < y1; y++) { const r = el('div', {className: 'row'}); node.append(r); this.rows.push(r); this.cache.push(null); }
    this.fit(); new ResizeObserver(() => this.fit()).observe(node);
  }
  fit() {
    const w = this.node.clientWidth - 16; if (w <= 0) return;
    let size = w / (this.x1 * 0.602);
    if (this.fitHeight) { const h = this.node.clientHeight - 12; if (h > 0) size = Math.min(size, h / ((this.y1 - this.y0) * 1.18)); }
    this.node.style.fontSize = Math.max(4, size) + 'px';
  }
  render(rows) {
    for (let y = this.y0; y < this.y1; y++) {
      const row = rows[y] || [], key = JSON.stringify(row), i = y - this.y0;
      if (this.cache[i] === key) continue;
      this.cache[i] = key;
      const frag = document.createDocumentFragment(); let x = 0;
      for (const [text, fg, bg, fl] of row) {
        if (x >= this.x1) break;
        const s = el('span', {textContent: text.slice(0, this.x1 - x).replace(/▒/g, '#')}); x += text.length;
        if (fg) s.style.color = fg; if (bg) s.style.backgroundColor = bg; if (fl) s.className = fl.split('').join(' ');
        frag.append(s);
      }
      this.rows[i].replaceChildren(frag);
    }
  }
}

/* ---- games ---- */
async function activeSlots() {
  const d = await api('/api/games');
  const retired = new Set(d.retired || []);
  const games = Object.fromEntries(d.games.map(g => [g.id, g]));
  const slots = Object.entries(d.slots).filter(([s, v]) => v && !retired.has(s))
    .map(([s, v]) => ({slot: s, info: v, meta: games[v.game_id] || {}}));
  return {slots, games: d.games};
}

const ICONS = {death: '☠', level: '▼', xl: '⬆', danger: '♥', item: '💎', monster: '👹', progress: '🧭', decision: '💬', event: '★', say: '💬'};
class Game {
  constructor(gid) { Object.assign(this, {gid, frames: [], keys: [], status: [], events: [], log: [], screen: null, screenPos: -1, total: 0}); }
  async load() {
    await this.more(true);
    try { this.log = (await api('/api/log?game=' + encodeURIComponent(this.gid))).log; } catch (e) { this.log = []; }
    for (const l of this.log) if (l.kind === 'decision' && l.text) this.events.push({f: this.frameAt(l.t), kind: 'say', label: l.text, imp: false});
    try {
      for (const c of (await api('/api/chronicle?game=' + encodeURIComponent(this.gid))).chronicle)
        this.events.push({f: c.frame, kind: c.kind || 'event', label: c.title, text: c.text, imp: (c.importance || 2) >= 2});
    } catch (e) {}
    try {
      for (const k of (await api('/api/keyevents?game=' + encodeURIComponent(this.gid))).events)
        this.events.push({f: k.f, kind: /Objet|Excalibur|Wish/.test(k.label) ? 'item' : /Monstre/.test(k.label) ? 'monster' : 'danger', label: k.label.replace(/^\S+\s/, ''), imp: true});
    } catch (e) {}
    this.sortEvents();
  }
  sortEvents() {
    const seen = new Set();
    this.events = this.events.filter(e => { const k = e.f + e.label; if (seen.has(k)) return false; seen.add(k); return true; }).sort((a, b) => a.f - b.f);
  }
  async more(all) {
    do {
      const d = await api(`/api/frames?game=${encodeURIComponent(this.gid)}&from=${this.frames.length}&limit=6000`);
      const start = this.frames.length;
      for (const f of d.frames) this.frames.push(f);
      this.total = d.total; this.derive(start);
      if (!d.frames.length) break;
    } while (all && this.frames.length < this.total);
  }
  derive(from) {
    let maxd = this._maxd || 0;
    for (let i = from; i < this.frames.length; i++) {
      const f = this.frames[i];
      if (f.k) this.keys.push(i);
      this.status[i] = f.s || (i ? this.status[i - 1] : null);
      const s = this.status[i], p = i ? this.status[i - 1] : null;
      if (s && p) {
        const d = +s[1] || 0;
        if (s[1] !== p[1] && d > maxd) { maxd = d; this.events.push({f: i, kind: 'level', label: `Dlvl ${s[1]} atteint`, imp: true}); }
        if (s[4] > p[4]) this.events.push({f: i, kind: 'xl', label: `XL ${s[4]}`, imp: false});
        if (s[2] <= s[3] / 4 && p[2] > p[3] / 4) this.events.push({f: i, kind: 'danger', label: `HP ${s[2]}/${s[3]}`, imp: true});
      }
      const r = f.r || {};
      const msg = ['1', '2', '3', '4', '5', '6', '7'].map(y => (r[y] || []).map(x => x[0]).join('')).join(' ');
      if (/You die\.\.\.|Do you want your possessions identified/.test(msg) && !this.events.some(e => e.kind === 'death'))
        this.events.push({f: i, kind: 'death', label: 'Mort', imp: true});
    }
    this._maxd = maxd;
    if (from) this.sortEvents();
  }
  frameAt(t) { let lo = 0, hi = this.frames.length - 1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (this.frames[m].t <= t) lo = m; else hi = m - 1; } return lo; }
  screenAt(j) {
    if (this.screen && j === this.screenPos) return this.screen;
    let start, screen;
    if (this.screen && j > this.screenPos && j - this.screenPos < 400) { start = this.screenPos + 1; screen = this.screen; }
    else { let k = 0; for (const ki of this.keys) { if (ki <= j) k = ki; else break; } screen = Array(36).fill(null).map(() => []); start = k; }
    for (let i = start; i <= j; i++) for (const y in this.frames[i].r) screen[+y] = this.frames[i].r[y];
    this.screen = screen; this.screenPos = j; return screen;
  }
  sayAt(j) { const t = this.frames[j] ? this.frames[j].t : 0; let d = null; for (const l of this.log) { if (l.t > t) break; if (l.kind === 'decision') d = l; } return d; }
}

/* ---- player: play/pause/seek on a Game, rendering into a Term ---- */
class Player {
  constructor(term, onSeek) { Object.assign(this, {term, onSeek, game: null, pos: 0, playing: false, speed: 8, follow: false}); this.tick(); }
  async open(gid, at) {
    this.playing = false;
    this.game = new Game(gid); await this.game.load();
    this.follow = at === 'live';
    this.seek(at === 'live' || at === 'end' ? this.game.frames.length - 1 : (at || 0));
  }
  seek(j) {
    if (!this.game || !this.game.frames.length) return;
    this.pos = Math.max(0, Math.min(this.game.frames.length - 1, j));
    if (this.pos < this.game.frames.length - 1) this.follow = false;
    this.term.render(this.game.screenAt(this.pos));
    this.onSeek && this.onSeek(this);
  }
  async tick() {
    for (;;) {
      await new Promise(r => setTimeout(r, 120));
      if (!this.game) continue;
      if (this.playing) {
        const f = this.game.frames, n = f.length;
        if (this.pos < n - 1) {
          let dt = 0.12 * this.speed, j = this.pos;
          while (j < n - 1 && dt > 0) { dt -= Math.min(f[j + 1].t - f[j].t, 1.0); j++; }
          this.seek(j);
        } else this.playing = false;
      }
      if (this.follow || (this._lastMore || 0) < Date.now() - 2000) {
        if ((this._lastMore || 0) < Date.now() - 2000) { this._lastMore = Date.now(); const n = this.game.frames.length; await this.game.more(false); if (this.follow && this.game.frames.length > n) { this.pos = this.game.frames.length - 1; this.term.render(this.game.screenAt(this.pos)); this.onSeek && this.onSeek(this); } }
      }
    }
  }
}
