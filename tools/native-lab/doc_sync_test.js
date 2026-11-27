#!/usr/bin/env node
/* The state and edit protocol, proven (task NB-R7, review RN5 A10).
 *
 * A page simulation (the app's own undo: a JSON snapshot per pushUndo, restore on undo) edits the three built-in
 * songs (Fractals, the Psytrance demo, Shrine Legion, as the app holds them) with random edits of the kinds the
 * app makes, and talks to the engine's document (aldoc) through native/bridge/doc-sync.js. After every step the
 * page's project and the engine's are compared by their structural hash, and now and then as whole JSON.
 *
 *   A  the page owns the project: edits, the app's undo and redo (snapshot restore), commits as diffs
 *   B  the engine owns undo: edits from the page, undo and redo done by the engine and sent back
 *   C  the engine changes the project while the page's edit is on its way: refused, rebased, nothing lost
 *   D  a lost line, an engine restart, a refused edit: the page sends the whole project, the copies agree again
 *   E  saving: atomic, older copies kept, a crash before the rename, a damaged file, minReader
 *
 *   node tools/native-lab/doc_sync_test.js <path to aldoc> [--steps 1000] [--seed 7]
 */
'use strict';
const fs = require('fs'), path = require('path'), zlib = require('zlib'), os = require('os');
const { spawn } = require('child_process');
const D = require('../../native/bridge/doc-sync.js');

const args = process.argv.slice(2);
const ALDOC = args[0];
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? +args[i + 1] : d; };
const STEPS = opt('--steps', 1000), SEED = opt('--seed', 7);
if (!ALDOC || !fs.existsSync(ALDOC)) { console.error('usage: doc_sync_test.js <aldoc> [--steps N] [--seed N]'); process.exit(2); }

let fails = 0;
const check = (ok, what) => { console.log((ok ? 'ok   ' : 'FAIL ') + what); if (!ok) fails++; };

// ---------------------------------------------------------------- the engine, one line in, one line out
class Engine {
  constructor() { this.start(); }
  start() {
    this.p = spawn(ALDOC, [], { stdio: ['pipe', 'pipe', 'inherit'] });
    this.buf = ''; this.lines = []; this.waiters = [];
    this.p.stdout.setEncoding('utf8');
    this.p.stdout.on('data', d => {
      this.buf += d; let i;
      while ((i = this.buf.indexOf('\n')) >= 0) { const l = this.buf.slice(0, i); this.buf = this.buf.slice(i + 1); const w = this.waiters.shift(); if (w) w(l); else this.lines.push(l); }
    });
  }
  write(text) { this.p.stdin.write(text + '\n'); }
  read() { return this.lines.length ? Promise.resolve(this.lines.shift()) : new Promise(r => this.waiters.push(r)); }
  async call(obj) { this.write(typeof obj === 'string' ? obj : JSON.stringify(obj)); return JSON.parse(await this.read()); }
  stop() { this.p.stdin.end(); return new Promise(r => this.p.on('close', r)); }
  kill() { this.p.kill('SIGKILL'); return new Promise(r => this.p.on('close', r)); }
}

// ---------------------------------------------------------------- the page: the app's state, undo and the mirror
const rnd = (() => { let a = SEED >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; })();
const ri = n => Math.floor(rnd() * n), pick = a => a[ri(a.length)];
const rid = () => Math.floor(rnd() * 36 ** 8).toString(36).padStart(8, '0');

class Page {
  constructor(S, engine) {
    this.S = S; this.UNDO = []; this.REDO = []; this.stepId = 0; this.engine = engine; this.out = [];
    this.sizes = [];
    this.m = new D.DocMirror(t => { if (t.startsWith('{"cmd":"doc.edit"')) this.sizes.push(t.length); this.out.push(t); });
    this.m.wantHash = true;
    this.lastHash = null; this.engineHash = null; this.drop = 0;
  }
  // as the app: snapshot before the change, then the change, then changed() -> commit
  pushUndo() { this.UNDO.push(JSON.stringify(this.S)); if (this.UNDO.length > 80) this.UNDO.shift(); this.REDO = []; this.m.beginStep(++this.stepId); }
  undo() { if (!this.UNDO.length) return false; this.REDO.push(JSON.stringify(this.S)); this.S = JSON.parse(this.UNDO.pop()); this.m.beginStep(++this.stepId); return true; }
  redo() { if (!this.REDO.length) return false; this.UNDO.push(JSON.stringify(this.S)); this.S = JSON.parse(this.REDO.pop()); this.m.beginStep(++this.stepId); return true; }
  changed(label) { this.m.commit(this.S, label); }
  // deliver what the mirror wants to send, and the answers back, until nothing is left
  async flush() {
    while (this.out.length) {
      const batch = this.out.splice(0);
      for (const t of batch) {
        if (this.drop > 0) { this.drop--; this.dropped = true; continue; }   // a lost line
        const r = await this.engine.call(t);
        if (r.hash) this.engineHash = r.hash;
        this.deliver(r);
      }
    }
  }
  deliver(r) {
    if (r.ev === 'doc.change') { this.S = this.m.remote(r, this.S); if (r.hash) this.engineHash = r.hash; return; }
    this.m.onReply(r, this.S);
  }
  async verify(what, full) {
    await this.flush();
    const h = D.hashDoc(D.canon(this.S));
    const e = await this.engine.call({ cmd: full ? 'doc.snapshot' : 'doc.hash', rq: 'v' });
    let ok = e.hash === h;
    if (full && ok) ok = D.equal(e.doc, D.canon(this.S)) && JSON.stringify(D.hashDoc(e.doc)) === JSON.stringify(h);
    return ok;
  }
}

// ---------------------------------------------------------------- the random edits, of the kinds the app makes
const NAMES = ['Kick', 'Bass 2', 'Pad (wide)', 'Vox "lead"', 'Back\\slash', 'line\nbreak', 'tab\there', 'ctl\u0001', 'é à ü', 'ビート', 'emoji 🎵🥁', 'lone \ud83c', 'lone \udc00 low', '', ' '.repeat(3)];
const NUMS = [0, -0, 1, -1, 0.1 + 0.2, 1e21, 1e-7, 5e-324, 1.7976931348623157e308, -2.5e-310, 123456789.123456789, 2 ** 53 + 2, Math.PI, NaN, Infinity];
function tracksWith(S, f) { return S.tracks.filter(f); }
function anyClip(S, f) { const cs = []; S.tracks.forEach((t, ti) => (t.clips || []).forEach((c, ci) => { if (!f || f(c)) cs.push([t, c, ti, ci]); })); return cs.length ? pick(cs) : null; }

const EDITS = [
  ['move clip', 10, (S, pg) => { const x = anyClip(S); if (!x) return; pg.pushUndo(); x[1].start = Math.max(0, x[1].start + pick([-4, -1, 1, 4, 16])); pg.changed('Moved ' + x[1].name); }],
  ['drag clip (several commits)', 4, (S, pg) => { const x = anyClip(S); if (!x) return; pg.pushUndo(); for (let i = 0; i < 4; i++) { x[1].start = Math.max(0, x[1].start + pick([-1, 1, 2])); pg.changed('Moved ' + x[1].name); } }],
  ['resize clip', 6, (S, pg) => { const x = anyClip(S); if (!x) return; pg.pushUndo(); x[1].len = Math.max(0.25, x[1].len + pick([-2, -0.5, 0.25, 8])); if (rnd() < .3) x[1].off = (x[1].off || 0) + 1; pg.changed('Resized'); }],
  ['add note', 8, (S, pg) => { const x = anyClip(S, c => Array.isArray(c.notes)); if (!x) return; pg.pushUndo(); const n = x[1].notes; n.splice(ri(n.length + 1), 0, { p: 36 + ri(48), s: ri(64) / 4, l: pick([0.25, 0.5, 1]), v: Math.round(rnd() * 100) / 100 }); pg.changed('Added note'); }],
  ['remove notes', 5, (S, pg) => { const x = anyClip(S, c => Array.isArray(c.notes) && c.notes.length); if (!x) return; pg.pushUndo(); const n = x[1].notes; const k = 1 + ri(Math.min(8, n.length)); n.splice(ri(n.length - k + 1), k); pg.changed('Removed notes'); }],
  ['move notes and sort', 4, (S, pg) => { const x = anyClip(S, c => Array.isArray(c.notes) && c.notes.length > 3); if (!x) return; pg.pushUndo(); const n = x[1].notes; for (let i = 0; i < 3; i++) { const q = pick(n); q.s = Math.max(0, q.s + pick([-1, 1, 0.25])); q.p += pick([-12, 0, 7]); } n.sort((a, b) => a.s - b.s || a.p - b.p); pg.changed('Edited notes'); }],
  ['velocity', 4, (S, pg) => { const x = anyClip(S, c => Array.isArray(c.notes) && c.notes.length); if (!x) return; pg.pushUndo(); for (const q of x[1].notes) if (rnd() < .3) q.v = Math.round(rnd() * 127) / 127; pg.changed('Velocity'); }],
  ['volume drag', 8, (S, pg) => { const t = pick(S.tracks); pg.pushUndo(); for (let i = 0; i < 1 + ri(6); i++) { t.vol = Math.max(0, Math.min(2, t.vol + (rnd() - .5) * .1)); pg.changed('Volume of ' + t.name); } }],
  ['pan', 4, (S, pg) => { const t = pick(S.tracks); pg.pushUndo(); t.pan = Math.round((rnd() * 2 - 1) * 100) / 100; pg.changed('Pan'); }],
  ['mute solo', 4, (S, pg) => { const t = pick(S.tracks); pg.pushUndo(); if (rnd() < .5) t.mute = !t.mute; else t.solo = !t.solo; pg.changed('Mute'); }],
  ['device setting', 8, (S, pg) => { const t = pick(tracksWith(S, t => t.fx && t.fx.length) || S.tracks); if (!t || !t.fx.length) return; const f = pick(t.fx); const ks = Object.keys(f.p || {}); if (!ks.length) return; pg.pushUndo(); for (let i = 0; i < 1 + ri(4); i++) { const k = pick(ks); f.p[k] = typeof f.p[k] === 'number' ? Math.round((f.p[k] + (rnd() - .5) * 10) * 1000) / 1000 : typeof f.p[k] === 'boolean' ? !f.p[k] : f.p[k]; pg.changed('Changed effect'); } }],
  ['device on off', 3, (S, pg) => { const t = pick(tracksWith(S, t => t.fx && t.fx.length)); if (!t) return; pg.pushUndo(); const f = pick(t.fx); f.on = !f.on; pg.changed('Bypass'); }],
  ['add device', 4, (S, pg) => { const all = S.tracks.flatMap(t => t.fx || []); if (!all.length) return; const t = pick(S.tracks); pg.pushUndo(); const f = JSON.parse(JSON.stringify(pick(all))); f.id = rid(); t.fx.splice(ri(t.fx.length + 1), 0, f); pg.changed('Added effect'); }],
  ['remove device', 3, (S, pg) => { const t = pick(tracksWith(S, t => t.fx && t.fx.length)); if (!t) return; pg.pushUndo(); t.fx.splice(ri(t.fx.length), 1); pg.changed('Removed effect'); }],
  ['reorder devices', 2, (S, pg) => { const t = pick(tracksWith(S, t => t.fx && t.fx.length > 1)); if (!t) return; pg.pushUndo(); const [f] = t.fx.splice(ri(t.fx.length), 1); t.fx.splice(ri(t.fx.length + 1), 0, f); pg.changed('Moved effect'); }],
  ['instrument preset', 3, (S, pg) => { const t = pick(tracksWith(S, t => t.inst)); if (!t) return; pg.pushUndo(); const ks = Object.keys(t.inst).filter(k => typeof t.inst[k] === 'number'); if (ks.length) t.inst[pick(ks)] = Math.round(rnd() * 1000) / 1000; if (rnd() < .3) t.inst.preset = 'custom'; pg.changed('Changed instrument'); }],
  ['add track', 3, (S, pg) => { const src = pick(S.tracks); pg.pushUndo(); const t = JSON.parse(JSON.stringify(src)); t.id = rid(); t.name = src.name + ' copy'; (t.clips || []).forEach(c => c.id = rid()); (t.fx || []).forEach(f => f.id = rid()); S.tracks.splice(ri(S.tracks.length + 1), 0, t); pg.changed('Added track'); }],
  ['delete track', 2, (S, pg) => { if (S.tracks.length < 3) return; pg.pushUndo(); S.tracks.splice(ri(S.tracks.length), 1); pg.changed('Deleted track'); }],
  ['move track', 3, (S, pg) => { pg.pushUndo(); const [t] = S.tracks.splice(ri(S.tracks.length), 1); S.tracks.splice(ri(S.tracks.length + 1), 0, t); pg.changed('Reordered tracks'); }],
  ['rename (any text)', 4, (S, pg) => { pg.pushUndo(); const x = rnd() < .5 ? pick(S.tracks) : (anyClip(S) || [pick(S.tracks)])[1] || pick(S.tracks); x.name = pick(NAMES) + (rnd() < .5 ? ' ' + ri(100) : ''); pg.changed('Renamed'); }],
  ['tempo', 2, (S, pg) => { pg.pushUndo(); S.bpm = pick([120, 128, 138, 145, 147.5, 174]); pg.changed('Tempo'); }],
  ['sections', 3, (S, pg) => { S.sections = S.sections || []; pg.pushUndo(); if (rnd() < .5 || !S.sections.length) S.sections.splice(ri(S.sections.length + 1), 0, { id: rid(), name: pick(NAMES), start: ri(64) * 4, len: 16, color: '#4cc9f0' }); else S.sections.splice(ri(S.sections.length), 1); pg.changed('Sections'); }],
  ['automation points', 4, (S, pg) => { const x = anyClip(S); if (!x) return; const c = x[1]; pg.pushUndo(); c.env = c.env || {}; const k = pick(['cut', 'vol', 'res']); c.env[k] = c.env[k] || []; const e = c.env[k]; if (rnd() < .6 || !e.length) e.splice(ri(e.length + 1), 0, { b: ri(32), v: Math.round(rnd() * 1000) / 1000, c: rnd() < .3 ? Math.round(rnd() * 100) / 100 : undefined }); else e.splice(ri(e.length), 1); if (rnd() < .2) delete c.env[k]; pg.changed('Automation'); }],
  ['parameter automation (keyed object)', 3, (S, pg) => { pg.pushUndo(); S.pauto = S.pauto || {}; const k = pick(S.tracks).id + ':' + pick(['vol', 'pan', 'p.cut']); if (S.pauto[k] && rnd() < .3) delete S.pauto[k]; else S.pauto[k] = [{ b: 0, v: rnd() }, { b: 16, v: rnd() }]; pg.changed('Parameter automation'); }],
  ['integer-like keys', 2, (S, pg) => { pg.pushUndo(); S.work = S.work || {}; S.work[String(ri(20))] = ri(9); if (rnd() < .3) S.work['__proto__'] = { x: 1 }; pg.changed('Work'); }],
  ['new and deleted keys', 3, (S, pg) => { const t = pick(S.tracks); pg.pushUndo(); if (t.sends && rnd() < .5) delete t.sends; else t.sends = [{ to: pick(S.tracks).id, amt: Math.round(rnd() * 100) / 100 }]; pg.changed('Sends'); }],
  ['type changes', 3, (S, pg) => { const x = anyClip(S); if (!x) return; pg.pushUndo(); const c = x[1]; c.envShow = pick([null, 'cut', ['a', 1], { k: true }, 0, false]); pg.changed('View'); }],
  ['awkward numbers', 3, (S, pg) => { const t = pick(S.tracks); pg.pushUndo(); t.vol = pick(NUMS); t.extra = pick(NUMS); pg.changed('Numbers'); }],
  ['undefined fields', 2, (S, pg) => { const t = pick(S.tracks); pg.pushUndo(); t.gone = undefined; t.fn = () => 1; pg.changed('Undefined'); delete t.gone; delete t.fn; }],
  ['master chain', 3, (S, pg) => { if (!S.mfx || !S.mfx.length) return; pg.pushUndo(); const f = pick(S.mfx); const ks = Object.keys(f.p || {}).filter(k => typeof f.p[k] === 'number'); if (ks.length) f.p[pick(ks)] += 1; pg.changed('Master effects'); }],
  ['duplicate and delete clips', 4, (S, pg) => { const t = pick(tracksWith(S, t => t.clips && t.clips.length)); if (!t) return; pg.pushUndo(); if (rnd() < .5) { const c = JSON.parse(JSON.stringify(pick(t.clips))); c.id = rid(); c.start += c.len; t.clips.push(c); } else t.clips.splice(ri(t.clips.length), 1); pg.changed('Clips'); }],
  ['sort clips', 2, (S, pg) => { const t = pick(tracksWith(S, t => t.clips && t.clips.length > 2)); if (!t) return; pg.pushUndo(); t.clips.reverse(); pg.changed('Order'); }],
  ['nothing changed', 3, (S, pg) => { pg.pushUndo(); pg.changed('Nothing'); }],
  ['change and change back', 2, (S, pg) => { const t = pick(S.tracks); pg.pushUndo(); const v = t.vol; t.vol = 0.123; pg.changed('Vol'); t.vol = v; pg.changed('Vol'); }],
];
const WSUM = EDITS.reduce((a, e) => a + e[1], 0);
function randomEdit(pg) { let r = rnd() * WSUM; for (const e of EDITS) { r -= e[1]; if (r < 0) { e[2](pg.S, pg); return e[0]; } } }

// ---------------------------------------------------------------- the phases
async function phaseA(name, S0, eng) {
  const pg = new Page(D.canon(S0), eng);
  pg.m.load(pg.S); await pg.flush();
  let bad = 0, full = 0, steps = 0, undos = 0, redos = 0, applyOk = 0, applyChecks = 0;
  const t0 = Date.now();
  for (let i = 0; i < STEPS; i++) {
    const r = rnd();
    const before = (i % 10 === 0) ? D.canon(pg.m.shadow) : null, nEdits = pg.m.stats.edits;
    if (r < .10) { if (pg.undo()) { pg.changed('Undo'); undos++; } }
    else if (r < .15) { if (pg.redo()) { pg.changed('Redo'); redos++; } }
    else { randomEdit(pg); steps++; }
    await pg.flush();
    if (pg.engineHash !== D.hashDoc(D.canon(pg.S)) && pg.m.stats.edits > nEdits) bad++;
    if (before && pg.m.stats.edits > nEdits) {             // the page's own apply agrees with diff: before + ops = after
      applyChecks++;
      try { const after = D.applyOps(before, D.diff(before, D.canon(pg.S)), true); if (D.equal(after, D.canon(pg.S))) applyOk++; } catch (e) {}
    }
    if (i % 100 === 99) { if (!(await pg.verify('', true))) bad++; else full++; }
  }
  const ms = Date.now() - t0, st = pg.m.stats;
  check(bad === 0 && (await pg.verify('', true)), `A ${name}: ${STEPS} steps (${steps} edits, ${undos} undos and ${redos} redos by snapshot restore as the app does), the engine's hash equal to the page's after every step, whole JSON equal ${full} times`);
  check(applyOk === applyChecks, `A ${name}: the page's own diff and apply agree (${applyOk} of ${applyChecks})`);
  const sz = pg.sizes.slice().sort((x, y) => x - y), q = f => sz[Math.min(sz.length - 1, Math.floor(f * sz.length))];
  return { name, median: q(.5), p90: q(.9), max: sz[sz.length - 1], edits: st.edits, ops: st.ops, opBytes: st.opBytes, loadBytes: st.loadBytes, diffMs: st.diffMs, ms, steps: STEPS };
}

async function phaseB(name, S0, eng) {
  const pg = new Page(D.canon(S0), eng);
  pg.m.load(pg.S); await pg.flush();
  const hist = [], fut = [];
  let bad = 0, undos = 0, redos = 0, emptyUndo = 0;
  for (let i = 0; i < STEPS; i++) {
    const r = rnd();
    if (r < .2) {                                   // the engine's undo
      const cur = D.hashDoc(D.canon(pg.S));
      const r2 = await eng.call({ cmd: 'doc.undo', rq: 'u' + i });
      if (!r2.ops.length) { emptyUndo++; if (hist.length) { bad++; if (process.env.DBG) console.log('empty undo', i, hist.length); } continue; }
      pg.deliver(r2); await pg.flush(); undos++;
      const want = hist.pop(); fut.push(cur);
      const got = D.hashDoc(D.canon(pg.S));
      if (got !== want || r2.hash !== want) { bad++; if (process.env.DBG) console.log('undo mismatch', i, r2.label, got, want, r2.hash); }
      // the step before it in the engine's history
      const prev = await eng.call({ cmd: 'doc.hash', rq: 'h' }); if (prev.hash !== got) { bad++; if (process.env.DBG) console.log('after undo', i); }
    } else if (r < .3) {
      const r2 = await eng.call({ cmd: 'doc.redo', rq: 'r' + i });
      if (!r2.ops.length) { if (fut.length) { bad++; if (process.env.DBG) console.log('empty redo', i, fut.length); } continue; }
      const before = D.hashDoc(D.canon(pg.S));
      pg.deliver(r2); await pg.flush(); redos++;
      const want = fut.pop(); hist.push(before);
      if (D.hashDoc(D.canon(pg.S)) !== want || r2.hash !== want) { bad++; if (process.env.DBG) console.log('redo mismatch', i); }
    } else {
      const before = D.hashDoc(D.canon(pg.S)), n = pg.m.stats.edits;
      randomEdit(pg); await pg.flush();
      if (pg.m.stats.edits > n) { hist.push(before); fut.length = 0; }
      if (pg.engineHash !== D.hashDoc(D.canon(pg.S))) { bad++; if (process.env.DBG) console.log('edit mismatch', i); }
    }
  }
  const stats = await eng.call({ cmd: 'doc.stats', rq: 's' });
  // undo everything back to the song as loaded
  let back = 0;
  while (true) { const r2 = await eng.call({ cmd: 'doc.undo', rq: 'all' }); if (!r2.ops.length) break; pg.deliver(r2); back++; }
  await pg.flush();
  // the size limit drops whole steps from the oldest end; then undoing everything reaches the state after them
  const target = stats.droppedSteps ? hist[stats.droppedSteps] : D.hashDoc(D.canon(S0));
  const atStart = D.hashDoc(D.canon(pg.S)) === target;
  check(bad === 0 && (await pg.verify('', true)), `B ${name}: ${STEPS} steps with ${undos} undos and ${redos} redos done by the engine and sent to the page: every undo gives exactly the state before its step, page and engine equal throughout`);
  check(atStart, `B ${name}: ${back} undo steps in the engine take the project back to ${stats.droppedSteps ? 'the oldest step still kept (' + stats.droppedSteps + ' oldest dropped by the 64 MB limit, whole steps)' : 'the song as loaded'}, bit for bit (history ${(stats.historyBytes / 1024).toFixed(0)} KB)`);
}

async function phaseC(name, S0, eng) {
  const pg = new Page(D.canon(S0), eng);
  pg.m.load(pg.S); await pg.flush();
  let bad = 0, rounds = 0, kept = 0, keptChecks = 0;
  for (let i = 0; i < 200; i++) {
    randomEdit(pg); await pg.flush();                  // E1, taken by the engine
    // E2 made by the page, and the engine's undo arriving first (a control surface, a key in another window)
    const sBefore = D.canon(pg.S);
    pg.pushUndo(); const t = pick(pg.S.tracks); t.name = 'rebased ' + i; pg.changed('Renamed');
    const pending = pg.out.splice(0);
    pg.engine.write(JSON.stringify({ cmd: 'doc.undo', rq: 'x' + i }));
    for (const l of pending) pg.engine.write(l);
    const replies = [];
    for (let k = 0; k < 1 + pending.length; k++) replies.push(JSON.parse(await pg.engine.read()));
    for (const r of replies) pg.deliver(r);
    await pg.flush();
    rounds++;
    if (!(await pg.verify())) bad++;
    keptChecks++; if (pg.S.tracks.some(x => x.name === 'rebased ' + i)) kept++;
    void sBefore;
  }
  const st = pg.m.stats;
  check(bad === 0, `C ${name}: ${rounds} times the engine's undo overtook the page's edit: the edit refused as stale (${st.refused}), rebased on the engine's change (${st.rebased}), page and engine equal every time`);
  check(kept + st.conflicts === keptChecks, `C ${name}: the page's edit survived the rebase ${kept} times, ${st.conflicts} times the engine's change won at the same place (the track it renamed was taken away by the undo)`);
}

async function phaseD(name, S0) {
  let eng = new Engine();
  const pg = new Page(D.canon(S0), eng);
  pg.m.load(pg.S); await pg.flush();
  for (let i = 0; i < 50; i++) { randomEdit(pg); await pg.flush(); }
  // a lost line: the page waits for an answer that never comes, then sends the whole project
  pg.drop = 1; randomEdit(pg); pg.pushUndo(); pg.S.bpm = 133; pg.changed('Tempo'); await pg.flush();
  const before = await eng.call({ cmd: 'doc.hash', rq: 'd' });
  const differed = before.hash !== D.hashDoc(D.canon(pg.S));
  pg.m.timeout(pg.S); await pg.flush();
  check(differed && (await pg.verify('', true)), `D ${name}: a lost edit leaves the copies different (found by the hash), the page's timeout sends the whole project, equal again`);
  // a stale base without a change from the engine (a line lost the other way): refused, whole project sent
  const r = await eng.call({ cmd: 'doc.edit', rq: 'z', base: 1, ops: [] });
  check(r.error === 'stale', `D ${name}: an edit on an old seq is refused as stale`);
  pg.m.seq = 1; pg.pushUndo(); pg.S.bpm = 99; pg.changed('Tempo'); await pg.flush();
  check(pg.m.stats.loads >= 3 && (await pg.verify('', true)), `D ${name}: the page whose seq is behind gets a refusal and sends the whole project (${pg.m.stats.loads} loads in all)`);
  // a wrong old value (the page thinks the engine has something it has not)
  pg.m.shadow.bpm = 77; pg.pushUndo(); pg.S.bpm = 101; pg.changed('Tempo'); await pg.flush();
  check(await pg.verify('', true), `D ${name}: an edit whose old value the engine does not have is refused whole and the page sends the whole project`);
  // the engine restarts (crash): an empty document; the page loads again on 'ready'
  await eng.kill(); eng = new Engine(); pg.engine = eng; pg.m.inflight = null;
  pg.m.load(pg.S); await pg.flush();
  for (let i = 0; i < 20; i++) { randomEdit(pg); await pg.flush(); }
  check(await pg.verify('', true), `D ${name}: after an engine restart the page loads the project again and edits go on, equal`);
  await eng.stop();
}

async function phaseE(name, S0) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'aldoc-'));
  const f = path.join(dir, 'song.aldoc');
  let eng = new Engine();
  const pg = new Page(D.canon(S0), eng);
  pg.m.load(pg.S); await pg.flush();
  const saves = [];
  for (let i = 0; i < 7; i++) { for (let k = 0; k < 5; k++) { randomEdit(pg); await pg.flush(); } const r = await eng.call({ cmd: 'doc.save', rq: 's' + i, path: f, keep: 5 }); saves.push({ hash: D.hashDoc(D.canon(pg.S)), r }); }
  const t = saves[saves.length - 1].r;
  check(t.ok && fs.existsSync(f + '.5') && !fs.existsSync(f + '.6'), `E ${name}: seven saves, the file and five older copies (${(t.bytes / 1024).toFixed(0)} KB, ${(t.us / 1000).toFixed(1)} ms with the flush to disk)`);
  await eng.stop(); eng = new Engine();
  let o = await eng.call({ cmd: 'doc.open', rq: 'o', path: f });
  check(o.hash === saves[6].hash, `E ${name}: a new engine opens the saved file: the same hash as the page's project`);
  pg.engine = eng; pg.m.seq = o.seq;                 // the page goes on with the engine that opened the file
  // a crash between writing and renaming: the file is the last whole one
  randomEdit(pg); await pg.flush();
  check(await pg.verify(), `E ${name}: edits go on against the engine that opened the file`);
  await eng.call({ cmd: 'doc.save', rq: 'c', path: f, keep: 5, crashBeforeRename: true });
  o = await eng.call({ cmd: 'doc.open', rq: 'o2', path: f });
  check(o.hash === saves[6].hash && o.from === f, `E ${name}: a crash after writing and before the rename leaves the last saved file whole`);
  // a damaged file: the newest older copy that reads whole
  const txt = fs.readFileSync(f, 'utf8'); fs.writeFileSync(f, txt.slice(0, txt.length >> 1));
  o = await eng.call({ cmd: 'doc.open', rq: 'o3', path: f });
  check(o.hash === saves[5].hash && o.from === f + '.1', `E ${name}: a file cut in half is refused (${o.why}) and the copy before it opens`);
  // one changed number inside: the hash finds it
  const t1 = fs.readFileSync(f + '.1', 'utf8'), m = t1.match(/"bpm":(\d+)/);
  fs.writeFileSync(f + '.1', t1.replace(m[0], '"bpm":' + (+m[1] + 1)));
  o = await eng.call({ cmd: 'doc.open', rq: 'o4', path: f });
  check(o.from === f + '.2' && o.hash === saves[4].hash, `E ${name}: a file with one number changed is found by its hash, the copy before it opens`);
  // a file for a newer AudioLab
  fs.writeFileSync(f + '.n', JSON.stringify({ format: 'audiolab-doc', formatVersion: 3, minReader: 2, seq: 1, hash: '0', project: {} }));
  o = await eng.call({ cmd: 'doc.open', rq: 'o5', path: f + '.n' });
  check(o.error === 'needs a newer AudioLab', `E ${name}: a file whose minReader is above this engine's is refused with "${o.error}", not half read`);
  await eng.stop();
  fs.rmSync(dir, { recursive: true, force: true });
}

// ---------------------------------------------------------------- the diff alone, on arrays shuffled every way
function phaseF() {
  let ok = 0, n = 0, moveBytes = 0;
  const mk = k => ({ id: 'i' + k, v: k, big: 'x'.repeat(50) });
  for (let t = 0; t < 3000; t++) {
    const a = Array.from({ length: ri(12) }, (_, k) => rnd() < .15 ? { v: k } : mk(k));
    let b = D.canon(a);
    const kind = ri(6);
    if (kind === 0 && b.length) { const [x] = b.splice(ri(b.length), 1); b.splice(ri(b.length + 1), 0, x); }   // one moved
    else if (kind === 1) b.reverse();
    else if (kind === 2) b.sort(() => rnd() - .5);
    else if (kind === 3) { b = b.filter(() => rnd() < .7); b.splice(ri(b.length + 1), 0, mk(100 + t)); }
    else if (kind === 4) for (const x of b) if (rnd() < .3) x.v = -1;
    else { b.sort(() => rnd() - .5); for (const x of b) if (rnd() < .3) x.v = 7; b.push(mk(200 + t)); }
    const ops = D.diff(a, b);
    n++;
    try { const r = D.applyOps(D.canon(a), ops, true); const back = D.applyOps(D.canon(r), D.inverseAll(ops), true); if (D.equal(r, b) && D.equal(back, a)) ok++; } catch (e) {}
  }
  // one track of 30 moved to the end of Fractals: the edit carries that track twice, not the list
  const S = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(__dirname, 'ref', 'doc', 'fractals.json.gz'))).toString('utf8'));
  const S2 = D.canon(S); S2.tracks.push(S2.tracks.shift());
  moveBytes = JSON.stringify(D.diff(S, S2)).length;
  const trackBytes = JSON.stringify(S.tracks[0]).length;
  check(ok === n, `F: the diff on ${n} arrays (moved, reversed, shuffled, filtered, changed, mixed with and without ids): applying it gives the new array and its inverse the old one, every time`);
  check(moveBytes < 3 * trackBytes + 200, `F: moving one Fractals track to the end is an edit of ${(moveBytes / 1024).toFixed(1)} KB (the track is ${(trackBytes / 1024).toFixed(1)} KB, all tracks ${(JSON.stringify(S.tracks).length / 1024).toFixed(0)} KB)`);
}

// ---------------------------------------------------------------- timing on the biggest song
async function timing(S0) {
  const S = D.canon(S0), N = 50;
  let t = process.hrtime.bigint();
  for (let i = 0; i < N; i++) JSON.stringify(S);
  const stringify = Number(process.hrtime.bigint() - t) / 1e6 / N;
  t = process.hrtime.bigint();
  for (let i = 0; i < N; i++) D.diff(S, D.canon(S));
  const commit = Number(process.hrtime.bigint() - t) / 1e6 / N;
  t = process.hrtime.bigint();
  for (let i = 0; i < N; i++) D.hashDoc(S);
  const hash = Number(process.hrtime.bigint() - t) / 1e6 / N;
  const eng = new Engine();
  await eng.call({ cmd: 'doc.load', rq: 1, doc: S });
  let us = 0; for (let i = 0; i < N; i++) us += (await eng.call({ cmd: 'doc.hash', rq: 2 })).us;
  await eng.stop();
  return { bytes: JSON.stringify(S).length, stringify, commit, hash, engineHashMs: us / N / 1000 };
}

(async () => {
  const songs = ['fractals', 'psytrance', 'shrine'].map(n => [n, JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(__dirname, 'ref', 'doc', n + '.json.gz'))).toString('utf8'))]);
  const results = [];
  phaseF();
  for (const [name, S] of songs) {
    const eng = new Engine();
    results.push(await phaseA(name, S, eng));
    await phaseB(name, S, eng);
    await phaseC(name, S, eng);
    await eng.stop();
    await phaseD(name, S);
    await phaseE(name, S);
  }
  const tm = await timing(songs[0][1]);
  console.log('\nsizes and costs (page side in Node ' + process.version + ')');
  for (const r of results) console.log(`  ${r.name.padEnd(10)} ${r.edits} edits, ${r.ops} operations, on the wire per edit: median ${r.median} bytes, 90 % under ${(r.p90 / 1024).toFixed(1)} KB, mean ${(r.opBytes / r.edits / 1024).toFixed(1)} KB, largest ${(r.max / 1024).toFixed(0)} KB; the whole project ${(r.loadBytes / 1024).toFixed(0)} KB; diff ${(r.diffMs / r.steps).toFixed(2)} ms per step`);
  console.log(`  fractals: JSON.stringify(S) ${tm.stringify.toFixed(2)} ms (the app already does this at every pushUndo), commit (copy and diff, nothing changed) ${tm.commit.toFixed(2)} ms, hash ${tm.hash.toFixed(2)} ms in the page, ${tm.engineHashMs.toFixed(2)} ms in the engine, ${(tm.bytes / 1024).toFixed(0)} KB`);
  console.log(fails ? `FAIL: ${fails} failed` : 'PASS: all checks');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
