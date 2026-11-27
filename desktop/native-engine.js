// The native engine in the desktop shell (task NB-N2b). The shell's side of the bridge between the interface and
// the native AudioLab Engine (`alengine`, native/engine/). Nothing here runs until the page asks: the app keeps
// playing through the web engine exactly as before until a setting turns native output on (that hook in
// index.html is stage N2c).
//
// What the page gets (through preload.js, window.audiolabDesktop.nativeEngine):
//   available()            { mac, engine, bridge }: is there an engine to start
//   start()                starts the helper; events come back through on(cb) as { ev, ... }
//   cmd(name, options)     devices, formats, open, close, volume, mute, status, clock
//   sound(options)         opens the way for sound ({ pageRate, prefillMs, highMs, clock: 'exact' | 'follow' }); pageRate
//                          must be the device's rate (task NB-R2). A 'rate' event with soundPaused: true means the
//                          device changed rate: make the AudioContext again at event.value and call sound() again
//   stop()                 stops the helper
// Events besides the engine's own: 'restarted' { ok, attempt } after a crash, 'gave-up' when the page should
// play through the web engine again, 'engine-hung' { missed } when the watchdog killed an engine that stopped
// answering (a 'restarted' follows), 'feeder-restarted' { ok, why, needPort: true } when the sound feeder was
// started again: the page then gives a new port (tap.reconnect(), native/bridge/page-tap.js).
// The sound itself does not go through these calls: the page moves one end of a MessageChannel into its
// AudioWorklet (native/bridge/page-tap.js) and the other end here. Since task NB-R3 (review RN5 A8) this process
// does not touch the sound: it hands that port to a small utilityProcess, the feeder (desktop/native-feeder.js),
// which writes the 128-frame blocks straight into the engine's local socket with a bounded queue. So a main
// process busy with menus, other handlers or the updater cannot starve the engine. A watchdog pings the feeder
// and the engine once a second while the engine is wanted and starts either again after 3 missed answers.
// Without utilityProcess (plain Node, or AL_FEED_IN_MAIN=1 for a comparison) the blocks go through this process
// as in NB-N2b.
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

const FEEDER = path.join(__dirname, 'native-feeder.js');
// Electron's utilityProcess, or null in plain Node (tests) and when AL_FEED_IN_MAIN=1 asks for the old path
function findUtility(given) {
  if (process.env.AL_FEED_IN_MAIN === '1') return null;
  if (given !== undefined) return given;
  try { const u = require('electron').utilityProcess; return u && typeof u.fork === 'function' ? u : null; } catch (e) { return null; }
}
// the Mac, or any machine when a test asks for it (the engine runs on the null device off the Mac, task NB-R2)
const osOk = () => process.platform === 'darwin' || process.env.AL_ENGINE_TEST === '1';

const EVENTS = ['volume', 'rate', 'buffer', 'exclusive', 'devices', 'default-output', 'format', 'sound-connected', 'sound-disconnected', 'stopped', 'restarted', 'gave-up'];
const COMMANDS = new Set(['devices', 'formats', 'open', 'close', 'volume', 'mute', 'status', 'clock']);

// task NB-R4b (review C6, RN6 1.4): the engine refuses a device volume louder than the device has been unless the
// command says confirm. Only the person at the Mac may give that: the page arrives through an update channel that is
// not signed, so the shell drops a confirm the page sends and asks in its own dialog, then sends confirm itself.
function findDialog(given) {
  if (given !== undefined) return given;
  try { const d = require('electron').dialog; return d && typeof d.showMessageBox === 'function' ? d : null; } catch (e) { return null; }
}
async function askRaise(dialog, from, to, name) {
  if (!dialog) return false;
  const pc = x => Math.round(x * 1000) / 10 + ' %';
  try {
    const a = await dialog.showMessageBox({ type: 'warning', buttons: ['Make it louder', 'Keep it'], defaultId: 1, cancelId: 1, noLink: true,
      message: 'Raise ' + (name || 'the device') + "'s own volume from " + pc(from) + ' to ' + pc(to) + '?',
      detail: 'This is the volume of the DAC itself, before your amplifier, speakers or headphones. It is louder than this device has been, so AudioLab asks first.' });
    return !!a && a.response === 0;
  } catch (e) { return false; }
}

function setup({ ipcMain, app, utilityProcess, dialog }) {
  const DLG = findDialog(dialog);
  let eng = null, owner = null, port = null, starting = null;
  const UP = findUtility(utilityProcess);
  let feeder = null, feederId = 0, dog = null, engMissed = 0, engPinging = false; const feederRestarts = [];
  // crash recovery (research RN1, point 10): if the engine stops without being asked, start it again with the
  // last device and sound settings, at most 3 times a minute; then tell the page to go back to the web engine.
  let wanted = false, lastOpen = null, lastSound = null; const restarts = [];
  const tap = { blocks: 0, frames: 0, firstAt: 0, lastAt: 0, worstGapMs: 0, notFloat: 0 };
  const tell = (ev, d) => { try { if (owner && !owner.isDestroyed()) owner.send('al:native-ev', Object.assign({ ev }, d || {})); } catch (e) { /* window gone */ } };
  const closePort = () => {
    if (port === 'feeder') { port = null; if (feeder) try { feeder.proc.postMessage({ type: 'disconnect' }); } catch (e) { /* gone */ } return; }
    if (port) { try { port.close(); } catch (e) { /* ignore */ } port = null; }
  };

  async function start(sender) {
    owner = sender;
    if (eng) return { ok: true, already: true, pid: eng.pid };
    if (starting) return starting;
    const exe = enginePath(app), Bridge = loadBridge();
    if (!osOk() || !exe || !Bridge) return { ok: false, error: !osOk() ? 'the native engine is Mac only for now' : !exe ? 'the engine is not in this build' : 'the bridge is not in this build' };
    starting = (async () => {
      const e = new Bridge(exe);
      for (const n of EVENTS) e.on(n, m => tell(n, m));
      e.on('stopped', m => { if (eng === e) { eng = null; if (wanted) recover(m); else closePort(); } });
      try { const r = await e.start(); eng = e; engMissed = 0; return Object.assign({ ok: true, feeder: !!UP }, r); }
      catch (x) { return { ok: false, error: String(x && x.message || x) }; }
      finally { starting = null; }
    })();
    return starting;
  }

  async function recover(m) {
    const now = Date.now();
    while (restarts.length && now - restarts[0] > 60000) restarts.shift();
    if (restarts.length >= 3) { wanted = false; stopDog(); closePort(); killFeeder(); tell('gave-up', { reason: 'the engine stopped 3 times in a minute', code: m && m.code }); return; }
    restarts.push(now);
    const r = await start(owner);
    let ok = !!r.ok;
    if (ok && lastOpen) ok = !!(await eng.send(Object.assign({}, lastOpen, { cmd: 'open' }))).ok;
    if (ok && lastSound) ok = !!(await openSound(lastSound)).ok;   // refused if the device came back at another rate: then gave-up below
    tell('restarted', { ok, attempt: restarts.length, code: m && m.code });
    if (!ok) { wanted = false; stopDog(); closePort(); killFeeder(); tell('gave-up', { reason: 'the engine could not be started again' }); }
  }

  // ---- the feeder (task NB-R3) ----
  function feederStart() {
    const proc = UP.fork(FEEDER, [], { serviceName: 'AudioLab sound feeder', stdio: 'ignore' });
    const F = { proc, waiters: new Map(), connectWait: null, missed: 0, stats: null, closed: 0 };
    proc.on('message', m => {
      if (!m) return;
      if (m.type === 'pong') { F.stats = m.stats; const w = F.waiters.get(m.id); if (w) { F.waiters.delete(m.id); w(m.stats); } }
      else if (m.type === 'connected') { const w = F.connectWait; F.connectWait = null; if (w) w(m); }
      else if (m.type === 'closed') F.closed++;
    });
    proc.on('exit', code => {
      for (const w of F.waiters.values()) w(null); F.waiters.clear();
      if (F.connectWait) { F.connectWait({ ok: false, error: 'the feeder stopped' }); F.connectWait = null; }
      if (feeder === F) { feeder = null; if (wanted && !F.killed) restartFeeder('the feeder stopped (code ' + code + ')'); }
    });
    feeder = F;
    return F;
  }
  function pingFeeder(F, ms) {
    return new Promise(res => {
      const id = ++feederId; F.waiters.set(id, res);
      setTimeout(() => { if (F.waiters.delete(id)) res(null); }, ms);
      try { F.proc.postMessage({ type: 'ping', id }); } catch (e) { F.waiters.delete(id); res(null); }
    });
  }
  function feederConnect(F, p, so) {
    return new Promise(res => {
      F.connectWait = res;
      setTimeout(() => { if (F.connectWait === res) { F.connectWait = null; res({ ok: false, error: 'the feeder did not answer' }); } }, 5000);
      F.proc.postMessage({ type: 'connect', path: p, rate: so.pageRate, queueMs: so.queueMs });
    });
  }
  function killFeeder() {
    const F = feeder; feeder = null;
    if (!F) return;
    F.killed = true; const pid = F.proc.pid;
    try { F.proc.kill(); } catch (e) { /* gone */ }
    // a hung (or stopped) process may not act on the polite signal
    if (pid) { const t = setTimeout(() => { try { process.kill(pid, 0); process.kill(pid, 'SIGKILL'); } catch (e) { /* gone */ } }, 500); if (t.unref) t.unref(); }
  }
  async function restartFeeder(why) {
    killFeeder();
    const now = Date.now();
    while (feederRestarts.length && now - feederRestarts[0] > 60000) feederRestarts.shift();
    if (feederRestarts.length >= 3) { wanted = false; closePort(); stopDog(); killFeeder(); tell('gave-up', { reason: 'the sound feeder stopped 3 times in a minute' }); return; }
    feederRestarts.push(now);
    feederStart();
    let ok = true;
    if (eng && lastSound) ok = !!(await openSound(lastSound)).ok;
    tell('feeder-restarted', { ok, why, attempt: feederRestarts.length, needPort: true });
  }
  // opens the engine's sound socket and connects the feeder (or this process) to it
  async function openSound(so) {
    if (!UP) return eng.startSound(so);
    const r = await eng.startSound(so, { connect: false });
    if (!r.ok) return r;
    const F = feeder || feederStart();
    const c = await feederConnect(F, r.path, so);
    if (!c.ok) return { ok: false, error: 'the sound feeder could not connect: ' + c.error };
    const o = Object.assign({}, r, { feeder: true, queueFrames: c.queueFrames }); delete o.path;
    return o;
  }
  // the watchdog: once a second while the engine is wanted
  function startDog() {
    if (dog) return;
    dog = setInterval(async () => {
      const F = feeder;
      if (F && (lastSound || port === 'feeder')) {
        const st = await pingFeeder(F, 900);
        if (feeder === F) { if (st) F.missed = 0; else if (++F.missed >= 3) restartFeeder('no answer for 3 s'); }
      }
      if (eng && !engPinging) {
        const e = eng; engPinging = true;
        const r = await e.send({ cmd: 'status' }, 900);
        engPinging = false;
        if (eng === e) {
          if (r && r.error === 'no answer') {
            if (++engMissed >= 3) { engMissed = 0; tell('engine-hung', { missed: 3 }); try { e.proc.kill('SIGKILL'); } catch (x) { /* gone */ } }
          } else engMissed = 0;
        }
      }
    }, 1000);
    if (dog.unref) dog.unref();
  }
  function stopDog() { if (dog) { clearInterval(dog); dog = null; } }

  ipcMain.handle('al:native-available', () => ({ mac: process.platform === 'darwin', engine: !!enginePath(app), bridge: !!loadBridge(), feeder: !!UP }));
  ipcMain.handle('al:native-start', async e => { const r = await start(e.sender); if (r.ok) { wanted = true; startDog(); } return r; });
  ipcMain.handle('al:native-cmd', async (e, name, o) => {
    if (!COMMANDS.has(name)) return { ok: false, error: 'unknown command' };
    if (!eng) return { ok: false, error: 'the engine is not running' };
    const oo = Object.assign({}, o && typeof o === 'object' ? o : {});
    delete oo.req; delete oo.confirm;   // task NB-R4b: the bridge numbers requests; only the shell's own dialog confirms a louder volume
    let r = await eng.send(Object.assign({}, oo, { cmd: name }));
    if (name === 'volume' && r.needsConfirm && eng) {
      const st = await eng.send({ cmd: 'status' });
      if (await askRaise(DLG, r.value, +oo.value, st && st.device)) r = eng ? await eng.send(Object.assign({}, oo, { cmd: 'volume', confirm: true })) : r;
      else r = Object.assign({}, r, { declined: true });
    }
    if (name === 'open' && r.ok) lastOpen = Object.assign({}, o, r.uid ? { uid: r.uid } : {});
    if (name === 'close') lastOpen = null;
    if (name === 'status') {
      if (UP) { const F = feeder, st = F ? (await pingFeeder(F, 500)) || F.stats : null; r.tap = Object.assign({ path: 'feeder', feederPid: F ? F.proc.pid : 0, feederRestarts: feederRestarts.length }, st || {}); }
      else r.tap = Object.assign({ path: 'main' }, tap, { fedFrames: eng.fed });
    }
    return r;
  });
  ipcMain.handle('al:native-sound', async (e, o) => {
    if (!eng) return { ok: false, error: 'the engine is not running' };
    Object.assign(tap, { blocks: 0, frames: 0, firstAt: 0, lastAt: 0, worstGapMs: 0, notFloat: 0 });
    o = o || {};
    // task NB-R2: pageRate (the page's AudioContext rate) is required; the engine refuses a rate that is not the device's
    const so = { prefillMs: +o.prefillMs || 30, highMs: +o.highMs || 120, clock: o.clock === 'follow' ? 'follow' : 'exact', limitPpm: Math.min(20000, Math.max(100, +o.limitPpm || 2000)), pageRate: +o.pageRate || 0, queueMs: Math.min(2000, Math.max(20, +o.queueMs || 250)) };
    const r = await openSound(so); if (r.ok) lastSound = so;
    return r;
  });
  ipcMain.handle('al:native-silence', async () => { closePort(); lastSound = null; if (eng) { eng.stopSound(); return eng.silence(); } return { ok: true }; });
  ipcMain.handle('al:native-stop', async () => { wanted = false; stopDog(); lastOpen = lastSound = null; closePort(); killFeeder(); const e = eng; eng = null; if (e) await e.stop(); return { ok: true }; });
  // the far end of the page's worklet port
  ipcMain.on('al:native-port', e => {
    const p = e.ports && e.ports[0];
    if (!p) return;
    if (UP) {   // task NB-R3: the port goes on to the feeder (which drops its old port itself, keeping the socket); no block passes through this process
      const F = feeder || feederStart();
      try { F.proc.postMessage({ type: 'port' }, [p]); port = 'feeder'; } catch (x) { try { p.close(); } catch (y) { /* gone */ } }
      return;
    }
    closePort();
    port = p;
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
  app.on('will-quit', () => { wanted = false; stopDog(); closePort(); killFeeder(); if (eng) { const e = eng; eng = null; e.stop().catch(() => {}); } });
}

module.exports = { setup, enginePath };
