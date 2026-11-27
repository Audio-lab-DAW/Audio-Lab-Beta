// The sound path of the native engine, out of the desktop shell's main process (task NB-R3, review RN5 A8).
// Runs as an Electron utilityProcess started by desktop/native-engine.js. It does nothing but take the page's
// 128-frame blocks from the worklet's MessagePort and write them into the engine's local socket, so a busy main
// process (menus, every ipcMain handler, the updater hashing a download, AI voices) can no longer starve the engine.
//
// Messages from the shell (process.parentPort):
//   { type: 'connect', path, rate, queueMs }  connect to the engine's sound socket (path from the engine's 'source')
//   { type: 'port' } + ports[0]              the far end of the page's worklet port (a MessagePortMain)
//   { type: 'ping', id }                     answered at once with { type: 'pong', id, stats } (the shell's watchdog)
//   { type: 'disconnect' }                   close the socket and the port
// Answers: { type: 'connected', ok, error }, { type: 'pong', ... }, { type: 'closed', why } when the engine's side
// went away.
//
// Back-pressure (review A8: feed()'s flag was ignored): while the socket says "wait", blocks go into a bounded queue
// (queueMs of sound, 250 ms by default); when it is full, new blocks are dropped and counted, never piled up without
// limit. The order of the samples is kept: a block is dropped whole, and only when nothing fits.
'use strict';
const net = require('net');

function createFeeder(post, opts = {}) {
  const S = { blocks: 0, frames: 0, fedFrames: 0, firstAt: 0, lastAt: 0, worstGapMs: 0, notFloat: 0, noSink: 0,
    backPressure: 0, queuedFrames: 0, queuedMaxFrames: 0, droppedBlocks: 0, droppedFrames: 0, pings: 0, socket: false, port: false };
  let sock = null, port = null, waiting = false, maxQ = 12000;
  const q = [];
  const now = opts.now || (() => Date.now());

  function write(f) {
    const b = Buffer.from(f.buffer, f.byteOffset, f.byteLength);
    S.fedFrames += f.length / 2;
    return sock.write(b);
  }
  function flush() {
    waiting = false;
    while (q.length && sock) {
      const f = q.shift(); S.queuedFrames -= f.length / 2;
      if (!write(f)) { waiting = true; S.backPressure++; return; }
    }
  }
  function block(d) {
    let f;
    if (d instanceof Float32Array) f = d;
    else if (d instanceof ArrayBuffer) f = new Float32Array(d);
    else if (ArrayBuffer.isView(d)) f = new Float32Array(d.buffer, d.byteOffset, Math.floor(d.byteLength / 4));
    else { S.notFloat++; return; }
    const t = now();
    if (!S.firstAt) S.firstAt = t; else if (t - S.lastAt > S.worstGapMs) S.worstGapMs = t - S.lastAt;
    S.lastAt = t; S.blocks++; S.frames += f.length / 2;
    if (!sock) { S.noSink++; return; }
    if (!waiting && !q.length) { if (!write(f)) { waiting = true; S.backPressure++; } return; }
    const n = f.length / 2;
    if (S.queuedFrames + n > maxQ) { S.droppedBlocks++; S.droppedFrames += n; return; }
    q.push(f); S.queuedFrames += n; if (S.queuedFrames > S.queuedMaxFrames) S.queuedMaxFrames = S.queuedFrames;
  }
  function closeSock(why) {
    if (!sock) return;
    const s = sock; sock = null; S.socket = false; waiting = false; q.length = 0; S.queuedFrames = 0;
    try { s.destroy(); } catch (e) { /* gone */ }
    if (why) post({ type: 'closed', why });
  }
  function closePort() { if (port) { try { port.close(); } catch (e) { /* gone */ } port = null; S.port = false; } }

  function handle(m, ports) {
    m = m || {};
    if (m.type === 'ping') { S.pings++; post({ type: 'pong', id: m.id, stats: Object.assign({}, S) }); return; }
    if (m.type === 'connect') {
      closeSock(null);
      maxQ = Math.max(256, Math.round((Math.min(2000, Math.max(20, +m.queueMs || 250))) * (+m.rate || 48000) / 1000));
      for (const k of ['blocks', 'frames', 'fedFrames', 'firstAt', 'lastAt', 'worstGapMs', 'notFloat', 'noSink', 'backPressure', 'queuedMaxFrames', 'droppedBlocks', 'droppedFrames']) S[k] = 0;
      let answered = false;
      const s = net.connect(String(m.path || ''), () => { sock = s; S.socket = true; answered = true; post({ type: 'connected', ok: true, queueFrames: maxQ }); });
      s.on('error', e => { if (!answered) { answered = true; post({ type: 'connected', ok: false, error: String(e && e.message || e) }); } });
      s.on('drain', () => { if (sock === s) flush(); });
      s.on('close', () => { if (sock === s) closeSock('the engine closed the sound socket'); });
      return;
    }
    if (m.type === 'port') {
      closePort();
      port = ports && ports[0];
      if (!port) return;
      S.port = true;
      port.on('message', e => block(e.data));
      port.on('close', () => { port = null; S.port = false; });
      port.start();
      return;
    }
    if (m.type === 'disconnect') { closePort(); closeSock(null); }
  }
  return { handle, block, stats: () => Object.assign({}, S) };
}

// Inside Electron's utilityProcess: wire it to the shell.
if (process.parentPort) {
  const pp = process.parentPort;
  const F = createFeeder(m => pp.postMessage(m));
  pp.on('message', e => F.handle(e.data, e.ports));
}

module.exports = { createFeeder };
