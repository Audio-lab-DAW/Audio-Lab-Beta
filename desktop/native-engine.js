// The native engine in the desktop shell (task NB-N2b). The shell's side of the bridge between the interface and
// the native AudioLab Engine (`alengine`, native/engine/). Nothing here runs until the page asks: the app keeps
// playing through the web engine exactly as before until a setting turns native output on (that hook in
// index.html is stage N2c).
//
// What the page gets (through preload.js, window.audiolabDesktop.nativeEngine):
//   available()            { mac, engine, bridge }: is there an engine to start
//   start()                starts the helper; events come back through on(cb) as { ev, ... }
//   cmd(name, options)     devices, formats, open, close, volume, mute, status, clock
//   sound(options)         opens the way for sound ({ prefillMs, highMs, clock: 'exact' | 'follow' })
//   stop()                 stops the helper
// Events besides the engine's own: 'restarted' { ok, attempt } after a crash, 'gave-up' when the page should
// play through the web engine again.
// The sound itself does not go through these calls: the page moves one end of a MessageChannel into its
// AudioWorklet (native/bridge/page-tap.js) and the other end here, so 128-frame blocks go from the page's
// audio thread straight to this process (proven in task NB-N2a), and from here through a local socket to the
// engine (native/bridge/engine-bridge.js).
'use strict';
const path = require('path');
const fs = require('fs');

const isFile = p => { try { return fs.statSync(p).isFile(); } catch (e) { return false; } };

function enginePath(app) {
  const c = [];
  if (process.env.AL_ENGINE) c.push(process.env.AL_ENGINE);
  if (app && app.isPackaged) c.push(path.join(process.resourcesPath, 'bin', 'alengine'));
  c.push(path.join(__dirname, 'bin', 'alengine'));
  c.push(path.join(__dirname, '..', 'native', 'build', 'alengine'));
  return c.find(isFile) || null;
}
function loadBridge() {
  for (const p of ['./engine-bridge', '../native/bridge/engine-bridge']) { try { return require(p).EngineBridge; } catch (e) { /* next */ } }
  return null;
}

const EVENTS = ['volume', 'rate', 'buffer', 'exclusive', 'devices', 'default-output', 'sound-connected', 'sound-disconnected', 'stopped', 'restarted', 'gave-up'];
const COMMANDS = new Set(['devices', 'formats', 'open', 'close', 'volume', 'mute', 'status', 'clock']);

function setup({ ipcMain, app }) {
  let eng = null, owner = null, port = null, starting = null;
  // crash recovery (research RN1, point 10): if the engine stops without being asked, start it again with the
  // last device and sound settings, at most 3 times a minute; then tell the page to go back to the web engine.
  let wanted = false, lastOpen = null, lastSound = null; const restarts = [];
  const tap = { blocks: 0, frames: 0, firstAt: 0, lastAt: 0, worstGapMs: 0, notFloat: 0 };
  const tell = (ev, d) => { try { if (owner && !owner.isDestroyed()) owner.send('al:native-ev', Object.assign({ ev }, d || {})); } catch (e) { /* window gone */ } };
  const closePort = () => { if (port) { try { port.close(); } catch (e) { /* ignore */ } port = null; } };

  async function start(sender) {
    owner = sender;
    if (eng) return { ok: true, already: true, pid: eng.pid };
    if (starting) return starting;
    const exe = enginePath(app), Bridge = loadBridge();
    if (process.platform !== 'darwin' || !exe || !Bridge) return { ok: false, error: process.platform !== 'darwin' ? 'the native engine is Mac only for now' : !exe ? 'the engine is not in this build' : 'the bridge is not in this build' };
    starting = (async () => {
      const e = new Bridge(exe);
      for (const n of EVENTS) e.on(n, m => tell(n, m));
      e.on('stopped', m => { if (eng === e) { eng = null; if (wanted) recover(m); else closePort(); } });
      try { const r = await e.start(); eng = e; return Object.assign({ ok: true }, r); }
      catch (x) { return { ok: false, error: String(x && x.message || x) }; }
      finally { starting = null; }
    })();
    return starting;
  }

  async function recover(m) {
    const now = Date.now();
    while (restarts.length && now - restarts[0] > 60000) restarts.shift();
    if (restarts.length >= 3) { wanted = false; closePort(); tell('gave-up', { reason: 'the engine stopped 3 times in a minute', code: m && m.code }); return; }
    restarts.push(now);
    const r = await start(owner);
    let ok = !!r.ok;
    if (ok && lastOpen) ok = !!(await eng.send(Object.assign({}, lastOpen, { cmd: 'open' }))).ok;
    if (ok && lastSound) ok = !!(await eng.startSound(lastSound)).ok;
    tell('restarted', { ok, attempt: restarts.length, code: m && m.code });
    if (!ok) { wanted = false; closePort(); tell('gave-up', { reason: 'the engine could not be started again' }); }
  }

  ipcMain.handle('al:native-available', () => ({ mac: process.platform === 'darwin', engine: !!enginePath(app), bridge: !!loadBridge() }));
  ipcMain.handle('al:native-start', async e => { const r = await start(e.sender); if (r.ok) wanted = true; return r; });
  ipcMain.handle('al:native-cmd', async (e, name, o) => {
    if (!COMMANDS.has(name)) return { ok: false, error: 'unknown command' };
    if (!eng) return { ok: false, error: 'the engine is not running' };
    const r = await eng.send(Object.assign({}, o && typeof o === 'object' ? o : {}, { cmd: name }));
    if (name === 'open' && r.ok) lastOpen = Object.assign({}, o, r.uid ? { uid: r.uid } : {});
    if (name === 'close') lastOpen = null;
    if (name === 'status') r.tap = Object.assign({}, tap, { fedFrames: eng.fed });
    return r;
  });
  ipcMain.handle('al:native-sound', async (e, o) => {
    if (!eng) return { ok: false, error: 'the engine is not running' };
    Object.assign(tap, { blocks: 0, frames: 0, firstAt: 0, lastAt: 0, worstGapMs: 0, notFloat: 0 });
    o = o || {};
    const so = { prefillMs: +o.prefillMs || 30, highMs: +o.highMs || 120, clock: o.clock === 'follow' ? 'follow' : 'exact', limitPpm: Math.min(20000, Math.max(100, +o.limitPpm || 2000)) };
    const r = await eng.startSound(so); if (r.ok) lastSound = so;
    return r;
  });
  ipcMain.handle('al:native-silence', async () => { closePort(); lastSound = null; if (eng) { eng.stopSound(); return eng.silence(); } return { ok: true }; });
  ipcMain.handle('al:native-stop', async () => { wanted = false; lastOpen = lastSound = null; closePort(); const e = eng; eng = null; if (e) await e.stop(); return { ok: true }; });
  // the far end of the page's worklet port
  ipcMain.on('al:native-port', e => {
    closePort();
    port = e.ports && e.ports[0];
    if (!port) return;
    port.on('message', m => {
      const d = m.data; let f;
      if (d instanceof Float32Array) f = d;
      else if (d instanceof ArrayBuffer) f = new Float32Array(d);
      else if (ArrayBuffer.isView(d)) f = new Float32Array(d.buffer, d.byteOffset, Math.floor(d.byteLength / 4));
      else { tap.notFloat++; return; }
      const now = Date.now();
      if (!tap.firstAt) tap.firstAt = now; else if (now - tap.lastAt > tap.worstGapMs) tap.worstGapMs = now - tap.lastAt;
      tap.lastAt = now; tap.blocks++; tap.frames += f.length / 2;
      if (eng) eng.feed(f);
    });
    port.on('close', () => { port = null; });
    port.start();
  });
  app.on('will-quit', () => { wanted = false; closePort(); if (eng) { const e = eng; eng = null; e.stop().catch(() => {}); } });
}

module.exports = { setup, enginePath };
