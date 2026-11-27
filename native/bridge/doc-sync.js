/* The page's side of the project document protocol (task NB-R7, review RN5 A10).
 *
 * The app keeps changing its project object S in place, as it does today (327 places call pushUndo). This module
 * turns those changes into numbered edits for the engine without touching any of them: at every changed() the page
 * compares S with the copy it last sent (the shadow) and sends the difference as operations that carry their own
 * inverse. The engine (native/engine/doc/doc.h) applies them whole or refuses them, and both sides compute the same
 * structural hash, so "the page and the engine hold the same project" is one comparison of 16 hex digits.
 * The design and the proofs: docs/native-state-protocol.md.
 *
 * Works in the page (copied in by the hook, as page-tap.js) and in Node (the tests). No dependencies.
 */
(function (root) {
  'use strict';

  // ---------------------------------------------------------------- values
  const canon = v => JSON.parse(JSON.stringify(v));            // what JSON carries: no undefined, NaN to null, -0 to 0
  const isObj = v => v !== null && typeof v === 'object' && !Array.isArray(v);
  const kindOf = v => v === null ? 'n' : Array.isArray(v) ? 'a' : typeof v === 'object' ? 'o' : typeof v;
  const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);

  function equal(a, b) {
    if (a === b) return true;
    const ka = kindOf(a);
    if (ka !== kindOf(b)) return false;
    if (ka === 'a') { if (a.length !== b.length) return false; for (let i = 0; i < a.length; i++) if (!equal(a[i], b[i])) return false; return true; }
    if (ka === 'o') {
      const xa = Object.keys(a), xb = Object.keys(b);
      if (xa.length !== xb.length) return false;
      for (const k of xa) if (!has(b, k) || !equal(a[k], b[k])) return false;
      return true;
    }
    return false;                                                // numbers: a === b above (0 === -0)
  }

  // ---------------------------------------------------------------- the structural hash (same as Hasher in doc.h)
  // WTF-8: UTF-8 in which a lone surrogate keeps its own 3 bytes, so any JS string round-trips through the engine.
  function wtf8(s) {
    const out = [];
    for (let i = 0; i < s.length; i++) {
      let c = s.charCodeAt(i);
      if (c < 0x80) { out.push(c); continue; }
      if (c >= 0xD800 && c < 0xDC00 && i + 1 < s.length) {
        const d = s.charCodeAt(i + 1);
        if (d >= 0xDC00 && d < 0xE000) { c = 0x10000 + ((c - 0xD800) << 10) + (d - 0xDC00); i++; }
      }
      if (c < 0x800) out.push(0xC0 | (c >> 6), 0x80 | (c & 63));
      else if (c < 0x10000) out.push(0xE0 | (c >> 12), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
      else out.push(0xF0 | (c >> 18), 0x80 | ((c >> 12) & 63), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
    }
    return out;
  }
  const ascii = s => { for (let i = 0; i < s.length; i++) if (s.charCodeAt(i) >= 0x80) return false; return true; };
  function cmpBytes(x, y) { const n = Math.min(x.length, y.length); for (let i = 0; i < n; i++) if (x[i] !== y[i]) return x[i] - y[i]; return x.length - y.length; }

  const F64 = new Float64Array(1), U8 = new Uint8Array(F64.buffer);
  const LITTLE = new Uint8Array(new Uint16Array([1]).buffer)[0] === 1;
  function hashDoc(v) {
    let a = 0x811c9dc5, b = 0x6b43a9b5;
    function byte(x) { a = Math.imul(a ^ x, 0x01000193); b = Math.imul(b ^ x, 0x01000193); b ^= b >>> 15; }
    function u32(n) { byte(n & 255); byte((n >>> 8) & 255); byte((n >>> 16) & 255); byte(n >>> 24); }
    function str(s) {
      byte(115);                                                 // 's'
      if (ascii(s)) { u32(s.length); for (let i = 0; i < s.length; i++) byte(s.charCodeAt(i)); }
      else { const w = wtf8(s); u32(w.length); for (let i = 0; i < w.length; i++) byte(w[i]); }
    }
    function val(x) {
      if (x === null) { byte(110); return; }
      switch (typeof x) {
        case 'boolean': byte(x ? 116 : 102); return;
        case 'number':
          F64[0] = x === 0 ? 0 : x; byte(100);
          if (LITTLE) for (let i = 0; i < 8; i++) byte(U8[i]); else for (let i = 7; i >= 0; i--) byte(U8[i]);
          return;
        case 'string': str(x); return;
        case 'object': {
          if (Array.isArray(x)) { byte(97); u32(x.length); for (let i = 0; i < x.length; i++) val(x[i]); return; }
          const ks = [];
          for (const k in x) if (has(x, k) && x[k] !== undefined) ks.push(k);
          byte(111); u32(ks.length);
          let all = true; for (let i = 0; i < ks.length; i++) if (!ascii(ks[i])) { all = false; break; }
          if (all) ks.sort((p, q) => p < q ? -1 : p > q ? 1 : 0);   // for ASCII, code unit order = byte order
          else { const e = new Map(ks.map(k => [k, wtf8(k)])); ks.sort((p, q) => cmpBytes(e.get(p), e.get(q))); }
          for (let i = 0; i < ks.length; i++) { str(ks[i]); val(x[ks[i]]); }
          return;
        }
      }
      throw new Error('not a JSON value: ' + typeof x);
    }
    val(v);
    return (a >>> 0).toString(16).padStart(8, '0') + (b >>> 0).toString(16).padStart(8, '0');
  }

  // ---------------------------------------------------------------- the difference as operations
  // Ops: {o:'set',p,v[,w]} {o:'del',p,w} {o:'ins',p,v} {o:'rm',p,w}; p is an array of keys (strings) and indices (numbers).
  // Arrays: elements that match (equal, or objects with the same id) are kept from both ends and compared inside;
  // what is left in the middle is compared element by element when it has the same length and no ids moved,
  // otherwise removed and inserted. Any result is correct (the tests prove the states agree); these rules keep the
  // usual edits (one clip moved, a note added, a track deleted) to one or two small operations.
  const idOf = x => isObj(x) && (typeof x.id === 'string' || typeof x.id === 'number') ? x.id : undefined;
  const match = (x, y) => { const i = idOf(x); return i !== undefined ? (i === idOf(y) ? 2 : 0) : (equal(x, y) ? 1 : 0); };

  function diff(a, b, path, out) {
    out = out || [];
    diffAt(a, b, path ? path.slice() : [], out);
    return out;
  }
  // path is one shared stack, copied only when an operation is written
  function diffAt(a, b, path, out) {
    if (a === b) return;
    const ka = kindOf(a), kb = kindOf(b);
    if (ka !== kb || (ka !== 'a' && ka !== 'o')) { if (!equal(a, b)) out.push({ o: 'set', p: path.slice(), v: canon(b), w: canon(a) }); return; }
    const d = path.length;
    if (ka === 'o') {
      for (const k in a) if (has(a, k) && !has(b, k)) { path[d] = k; out.push({ o: 'del', p: path.slice(), w: canon(a[k]) }); }
      for (const k in b) {
        if (!has(b, k)) continue;
        path[d] = k;
        if (has(a, k)) diffAt(a[k], b[k], path, out);
        else out.push({ o: 'set', p: path.slice(), v: canon(b[k]) });
      }
      path.length = d;
      return;
    }
    // arrays
    const la = a.length, lb = b.length;
    // matched ends: 1 = equal (nothing to do inside), 2 = the same id (compared inside below)
    const ms = [], me = [];
    let s = 0, m;
    while (s < la && s < lb && (m = match(a[s], b[s]))) { ms.push(m); s++; }
    let e = 0;
    while (e < la - s && e < lb - s && (m = match(a[la - 1 - e], b[lb - 1 - e]))) { me.push(m); e++; }
    const ma = la - s - e, mb = lb - s - e;
    // the middle first, from the end of a's middle so that the indices before it stay valid
    let same = ma === mb && ma > 0 && ma <= 64;
    for (let i = s; same && i < s + ma; i++) if (idOf(a[i]) !== undefined) same = false;
    let ids = ma > 0 && mb > 0;
    for (let i = s; ids && i < s + ma; i++) if (idOf(a[i]) === undefined) ids = false;
    for (let i = s; ids && i < s + mb; i++) if (idOf(b[i]) === undefined) ids = false;
    if (same) {
      for (let i = 0; i < ma; i++) { path[d] = s + i; diffAt(a[s + i], b[s + i], path, out); }
    } else if (ids) {
      // objects with ids (tracks, clips, devices): remove the ones gone, move the ones that moved, insert the new
      // ones, then compare the kept ones inside. A moved track costs its value twice, not the whole list.
      // the ones that stay where they are: the longest run of b's order already in a's order (patience sorting)
      const posA = new Map(); for (let i = s; i < s + ma; i++) if (!posA.has(idOf(a[i]))) posA.set(idOf(a[i]), i - s);
      const seq = []; for (let i = s; i < s + mb; i++) { const q = posA.get(idOf(b[i])); seq.push(q === undefined ? -1 : q); }
      const tails = [], tailAt = [], prev = new Array(seq.length).fill(-1);
      for (let i = 0; i < seq.length; i++) {
        if (seq[i] < 0) continue;
        let lo = 0, hi = tails.length;
        while (lo < hi) { const mid = (lo + hi) >> 1; if (tails[mid] < seq[i]) lo = mid + 1; else hi = mid; }
        tails[lo] = seq[i]; tailAt[lo] = i; prev[i] = lo ? tailAt[lo - 1] : -1;
      }
      const stayB = new Set(), stayA = new Set();
      for (let i = tails.length ? tailAt[tails.length - 1] : -1; i >= 0; i = prev[i]) { stayB.add(i); stayA.add(seq[i]); }
      // remove everything in a's middle that does not stay (gone or moved), from the end
      for (let k = ma - 1; k >= 0; k--) if (!stayA.has(k)) { path[d] = s + k; out.push({ o: 'rm', p: path.slice(), w: canon(a[s + k]) }); }
      // insert in b's order whatever does not stay (new or moved); the ones that stay are already in place
      const work = []; for (let k = 0; k < ma; k++) if (stayA.has(k)) work.push(a[s + k]);
      const kept = [];
      for (let i = 0; i < mb; i++) {
        if (stayB.has(i)) { kept.push(i); continue; }
        path[d] = s + i; out.push({ o: 'ins', p: path.slice(), v: canon(b[s + i]) }); work.splice(i, 0, b[s + i]);
      }
      for (const i of kept) { path[d] = s + i; diffAt(work[i], b[s + i], path, out); }
    } else {
      for (let i = s + ma - 1; i >= s; i--) { path[d] = i; out.push({ o: 'rm', p: path.slice(), w: canon(a[i]) }); }
      for (let i = 0; i < mb; i++) { path[d] = s + i; out.push({ o: 'ins', p: path.slice(), v: canon(b[s + i]) }); }
    }
    // the kept ends, compared inside (their indices in b equal their indices in a after the middle changed)
    for (let i = 0; i < s; i++) if (ms[i] === 2) { path[d] = i; diffAt(a[i], b[i], path, out); }
    for (let i = 0; i < e; i++) if (me[i] === 2) { path[d] = lb - 1 - i; diffAt(a[la - 1 - i], b[lb - 1 - i], path, out); }
    path.length = d;
  }

  // ---------------------------------------------------------------- applying, inverting
  function inverse(op) {
    switch (op.o) {
      case 'set': return 'w' in op ? { o: 'set', p: op.p, v: op.w, w: op.v } : { o: 'del', p: op.p, w: op.v };
      case 'del': return { o: 'set', p: op.p, v: op.w };
      case 'ins': return { o: 'rm', p: op.p, w: op.v };
      case 'rm': return { o: 'ins', p: op.p, v: op.w };
    }
    throw new Error('unknown operation ' + op.o);
  }
  const inverseAll = ops => ops.slice().reverse().map(inverse);

  // apply to a document (in place); returns the new root (only a set at [] replaces it). check: compare old values.
  function applyOp(doc, op, check) {
    const p = op.p;
    if (!p.length) { if (op.o !== 'set') throw new Error('only set may address the root'); if (check && !equal(doc, op.w)) throw new Error('old value differs at the root'); return canon(op.v); }
    let c = doc;
    for (let i = 0; i + 1 < p.length; i++) { c = c[p[i]]; if (c === null || typeof c !== 'object') throw new Error('path not found: ' + JSON.stringify(p)); }
    const k = p[p.length - 1];
    switch (op.o) {
      case 'set':
        if (Array.isArray(c)) { if (typeof k !== 'number' || k >= c.length) throw new Error('index out of range'); }
        else if (typeof k !== 'string') throw new Error('not an array');
        if (check) { if ('w' in op) { if (!has(c, k) || !equal(c[k], op.w)) throw new Error('old value differs at ' + JSON.stringify(p)); } else if (has(c, k)) throw new Error('key exists already'); }
        if (k === '__proto__') Object.defineProperty(c, k, { value: canon(op.v), writable: true, enumerable: true, configurable: true });
        else c[k] = canon(op.v);
        return doc;
      case 'del':
        if (Array.isArray(c) || !has(c, k)) throw new Error('key not found');
        if (check && !equal(c[k], op.w)) throw new Error('old value differs at ' + JSON.stringify(p));
        delete c[k]; return doc;
      case 'ins':
        if (!Array.isArray(c) || k > c.length) throw new Error('index out of range');
        c.splice(k, 0, canon(op.v)); return doc;
      case 'rm':
        if (!Array.isArray(c) || k >= c.length) throw new Error('index out of range');
        if (check && !equal(c[k], op.w)) throw new Error('old value differs at ' + JSON.stringify(p));
        c.splice(k, 1); return doc;
    }
    throw new Error('unknown operation ' + op.o);
  }
  function applyOps(doc, ops, check) { for (const op of ops) doc = applyOp(doc, op, check); return doc; }

  // ---------------------------------------------------------------- the page's mirror of the engine's document
  // send(text) delivers one line to the engine (through the bridge); every answer goes to onReply, every change
  // that started in the engine (its undo or redo, later edits from a control surface) to remote.
  // Rules (docs/native-state-protocol.md): one edit in flight at a time, the ones made meanwhile wait in a queue
  // (one per undo step); an edit names the seq it was made on (base) and the engine refuses it if anything came in
  // between; then the page rolls its waiting edits back, takes the engine's change and puts its own on top again.
  class DocMirror {
    constructor(send) {
      this.send = send;
      this.shadow = null;               // the engine's document as the page last sent or heard it
      this.seq = 0;                     // the engine's seq that the shadow corresponds to, before the edit in flight
      this.rq = 0; this.step = ''; this.label = '';
      this.inflight = null;             // {rq, ops, step, label, base} sent, not answered
      this.queue = [];                  // [{ops, step, label}] made while one was in flight
      this.loading = false;
      this.stats = { edits: 0, ops: 0, opBytes: 0, loads: 0, loadBytes: 0, refused: 0, rebased: 0, conflicts: 0, diffMs: 0 };
    }
    load(S) {
      this.shadow = canon(S); this.queue = []; this.loading = true;
      const text = '{"cmd":"doc.load","rq":' + (++this.rq) + ',"doc":' + JSON.stringify(this.shadow) + '}';
      this.stats.loads++; this.stats.loadBytes += text.length;
      this.inflight = { rq: this.rq, load: true, ops: [] };
      this.send(text);
    }
    beginStep(id) { this.step = String(id); }
    get busy() { return !!this.inflight || this.queue.length > 0; }
    // compare S with what the engine has (or will have) and send or queue the difference
    commit(S, label) {
      const t0 = Date.now();
      const cur = canon(S), ops = diff(this.shadow, cur);
      this.stats.diffMs += Date.now() - t0;
      if (!ops.length) return ops;
      this.shadow = cur;
      const last = this.queue[this.queue.length - 1];
      if (last && last.step === this.step && this.step !== '') { last.ops = last.ops.concat(ops); if (label) last.label = label; }
      else this.queue.push({ ops, step: this.step, label: label || '' });
      this.pump();
      return ops;
    }
    pump() {
      if (this.inflight || !this.queue.length) return;
      const it = this.queue.shift();
      const text = JSON.stringify({ cmd: 'doc.edit', rq: ++this.rq, base: this.seq, step: it.step, label: it.label, ops: it.ops, hash: !!this.wantHash });
      this.stats.edits++; this.stats.ops += it.ops.length; this.stats.opBytes += text.length;
      this.inflight = { rq: this.rq, ops: it.ops, step: it.step, label: it.label, base: this.seq };
      this.send(text);
    }
    // the engine's answer to doc.load or doc.edit. Returns 'resync' when the page had to send the whole project.
    onReply(r, S) {
      const f = this.inflight;
      if (!f || r.rq !== f.rq) return null;                     // an answer to something else (status, undo...)
      this.inflight = null;
      if (!r.error) { this.seq = r.seq; this.loading = false; this.pump(); return null; }
      this.stats.refused++;
      if (r.error === 'stale' && f.rolledBack) { this.pump(); return null; }   // expected after remote(): its ops are already on top again
      this.load(S);                                               // anything else: the copies may differ, start again from S
      return 'resync';
    }
    // a change that started in the engine. Returns the project for the app to use from now on (S = mirror.remote(ev, S)).
    remote(ev, S) {
      if (this.inflight && this.inflight.load) return S;           // the engine takes the whole project next: it wins
      // 1. the engine's document before its change: the shadow without what the engine has not taken yet
      let base = this.shadow;
      const unsent = this.queue.reduce((a, q) => a.concat(q.ops), this.inflight && !this.inflight.load ? this.inflight.ops.slice() : []);
      if (unsent.length) { base = applyOps(canon(base), inverseAll(unsent), true); this.stats.rebased++; }
      if (this.inflight) this.inflight.rolledBack = true;
      this.queue = [];
      // 2. what the page changed on top of it (sent or not), and the engine's change
      const local = diff(base, canon(S));
      const next = applyOps(base === this.shadow ? canon(base) : base, ev.ops, true);
      this.shadow = next; this.seq = ev.seq;
      // 3. the page's changes on top again; if one no longer fits (the same place was changed), the engine's wins
      let out;
      try { out = applyOps(canon(next), local, true); }
      catch (e) { out = canon(next); this.stats.conflicts++; }
      if (local.length && !this.inflight) this.commit(out, 'rebased');   // nothing in flight: send now; else after the refusal
      else if (local.length) { const ops = diff(this.shadow, out); if (ops.length) { this.shadow = canon(out); this.queue.push({ ops, step: this.step, label: 'rebased' }); } }
      return out;
    }
    // no answer in time (a lost line, an engine that restarted): send the whole project again
    timeout(S) { this.inflight = null; this.load(S); }
  }

  const api = { canon, equal, hashDoc, wtf8, diff, inverse, inverseAll, applyOp, applyOps, DocMirror };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.alDocSync = api;
})(typeof window !== 'undefined' ? window : globalThis);
