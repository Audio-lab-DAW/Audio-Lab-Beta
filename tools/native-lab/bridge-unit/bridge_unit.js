// Unit tests of the shell's side of the native engine (task NB-R1, review RN5): desktop/native-engine.js and
// native/bridge/engine-bridge.js, run in plain Node on any machine against a stand-in engine (fake-alengine.js).
// Electron's ipcMain, the page's webContents and the worklet port are faked; the platform is set to macOS so the
// shell does what it does on the Mac.
//   node tools/native-lab/bridge-unit/bridge_unit.js        prints one line per check, exit code 0 when all pass
'use strict';
const path = require('path');
const fs = require('fs');
const os = require('os');
const { EventEmitter } = require('events');

const ROOT = path.join(__dirname, '..', '..', '..');
const FAKE = path.join(__dirname, 'fake-alengine.js');
fs.chmodSync(FAKE, 0o755);
const LOG = path.join(os.tmpdir(), 'al-fake-engine-' + process.pid + '.log');
process.env.AL_ENGINE = FAKE;
process.env.FAKE_LOG = LOG;
Object.defineProperty(process, 'platform', { value: 'darwin' });
const shell = require(path.join(ROOT, 'desktop', 'native-engine.js'));

let pass = 0, fail = 0;
const check = (ok, what, extra) => { if (ok) pass++; else fail++; console.log((ok ? 'ok   ' : 'FAIL ') + what + (extra !== undefined && !ok ? '  (' + JSON.stringify(extra) + ')' : '')); };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const until = async (f, ms = 4000) => { const t = Date.now(); while (Date.now() - t < ms) { if (f()) return true; await sleep(20); } return !!f(); };
const logLines = () => { try { return fs.readFileSync(LOG, 'utf8').trim().split('\n').filter(Boolean).map(l => JSON.parse(l)); } catch (e) { return []; } };
const alive = pid => { try { process.kill(pid, 0); return true; } catch (e) { return false; } };

// task NB-R3: a stand-in for Electron's utilityProcess that runs the real feeder (desktop/native-feeder.js) in this
// process. Messages go both ways on the next turn, as between processes; freeze() stops it answering (a hung feeder).
const { createFeeder } = require(path.join(ROOT, 'desktop', 'native-feeder.js'));
function fakeUtility() {
  const made = [];
  return { made, fork(file) {
    const proc = new EventEmitter(); proc.pid = 0; proc.frozen = false; proc.dead = false; proc.file = file;   // pid 0: no real process, the shell's SIGKILL fallback must not reach anything
    const F = createFeeder(m => setImmediate(() => { if (!proc.dead && !proc.frozen) proc.emit('message', m); }));
    proc.feeder = F;
    proc.postMessage = (m, transfer) => setImmediate(() => { if (!proc.dead && !proc.frozen) F.handle(m, transfer); });
    proc.kill = () => { if (proc.dead) return; proc.dead = true; F.handle({ type: 'disconnect' }); setImmediate(() => proc.emit('exit', 0)); };
    made.push(proc); return proc;
  } };
}

// one fake Electron main process per scenario (the shell keeps its state inside setup())
function makeShell(utilityProcess) {
  const handlers = {}, listeners = {}, quit = [];
  const ipcMain = { handle: (n, f) => { handlers[n] = f; }, on: (n, f) => { listeners[n] = f; } };
  const app = { isPackaged: false, on: (n, f) => { if (n === 'will-quit') quit.push(f); } };
  const events = [];
  const sender = { send: (ch, d) => { if (ch === 'al:native-ev') events.push(d); }, isDestroyed: () => false };
  shell.setup(utilityProcess ? { ipcMain, app, utilityProcess } : { ipcMain, app });
  const call = (n, ...a) => handlers[n]({ sender }, ...a);
  const port = () => { const p = new EventEmitter(); p.start = () => {}; p.close = () => { p.emit('close'); }; listeners['al:native-port']({ ports: [p] }); return p; };
  return { call, events, port, quit: () => quit.forEach(f => f()), handlers };
}

(async () => {
  // 1. the basics
  {
    const S = makeShell();
    const av = await S.call('al:native-available');
    check(av.mac && av.engine && av.bridge, 'available: Mac, engine found through AL_ENGINE, bridge found', av);
    const before = await S.call('al:native-cmd', 'devices', {});
    check(!before.ok && /not running/.test(before.error), 'a command before start is refused', before);
    const [s1, s2] = await Promise.all([S.call('al:native-start'), S.call('al:native-start')]);
    check(s1.ok && s2.ok && s1.pid === s2.pid, 'two starts at once give one engine', [s1, s2]);
    const s3 = await S.call('al:native-start');
    check(s3.ok && s3.already, 'a third start finds the running engine', s3);
    for (const bad of ['quit', 'source', 'selftest', '__proto__']) {
      const r = await S.call('al:native-cmd', bad, {});
      check(!r.ok && r.error === 'unknown command', 'the page cannot send "' + bad + '"', r);
    }
    const d = await S.call('al:native-cmd', 'devices', null);
    check(d.devices && d.devices[0].uid === 'fake-dac', 'devices answered (options null accepted)', d);
    const o = await S.call('al:native-cmd', 'open', { uid: 'fake-dac', rate: 96000, buffer: 64, cmd: 'quit' });
    check(o.ok && o.rate === 96000, 'open answered; a "cmd" field in the options cannot change the command', o);
    const noRate = await S.call('al:native-sound', { clock: 'follow' });
    check(!noRate.ok, 'sound without the page rate is refused (task NB-R2)', noRate);
    const badRate = await S.call('al:native-sound', { clock: 'follow', pageRate: 16000 });
    check(!badRate.ok && badRate.deviceRate === 96000, 'sound at 16 kHz into a device at 96 kHz is refused (task NB-R2)', badRate);
    const snd = await S.call('al:native-sound', { prefillMs: 'x', clock: 'follow', limitPpm: 1e9, pageRate: 96000 });
    const srcCmd = logLines().filter(l => l.cmd && l.cmd.cmd === 'source').pop();
    check(snd.ok && srcCmd && srcCmd.cmd.prefillMs === 30 && srcCmd.cmd.clock === 'follow' && srcCmd.cmd.limitPpm === 20000, 'sound: bad numbers fall back, the speed limit is capped at 20000 ppm', srcCmd);
    // the worklet port: 100 blocks of 128 stereo frames as Float32Array, ArrayBuffer and a typed view; one non-float message
    const p = S.port();
    for (let i = 0; i < 100; i++) {
      const f = new Float32Array(256).fill(i / 100);
      p.emit('message', { data: i % 3 === 0 ? f : i % 3 === 1 ? f.buffer : new Uint8Array(f.buffer) });
    }
    p.emit('message', { data: 'hello' });
    const st = await (async () => { let r; await until(async () => false, 0); for (let k = 0; k < 100; k++) { r = await S.call('al:native-cmd', 'status', {}); if (r.socketFrames >= 12800) break; await sleep(30); } return r; })();
    check(st.socketFrames === 12800, 'every frame the page sent reached the engine (12,800)', st.socketFrames);
    check(st.tap && st.tap.blocks === 100 && st.tap.frames === 12800 && st.tap.notFloat === 1 && st.tap.fedFrames === 12800, 'the tap counts blocks, frames and the one message that was not sound', st.tap);

    // 2. crash recovery: killed three times, it comes back with the same device and sound settings; the fourth time it gives up
    for (let k = 1; k <= 3; k++) {
      const pid = (await S.call('al:native-cmd', 'status', {})).ok ? logLines().filter(l => l.started).pop().pid : 0;
      process.kill(pid, 'SIGKILL');
      const got = await until(() => S.events.some(e => e.ev === 'restarted' && e.attempt === k));
      const ev = S.events.find(e => e.ev === 'restarted' && e.attempt === k);
      const newPid = logLines().filter(l => l.started).pop().pid;
      const cmds = logLines().filter(l => l.pid === newPid && l.cmd).map(l => l.cmd);
      const open = cmds.find(c => c.cmd === 'open'), src = cmds.find(c => c.cmd === 'source');
      check(got && ev.ok && newPid !== pid && open && open.uid === 'fake-dac' && open.rate === 96000 && src && src.clock === 'follow',
        'killed (' + k + ' of 3): started again, the same device and sound settings sent again', { ev, open, src });
    }
    const lastPid = logLines().filter(l => l.started).pop().pid;
    process.kill(lastPid, 'SIGKILL');
    check(await until(() => S.events.some(e => e.ev === 'gave-up')), 'the fourth stop within a minute: gave-up (the page goes back to the web engine)');
    await sleep(300);
    check(logLines().filter(l => l.started).pop().pid === lastPid, 'after giving up, no further start');
    const after = await S.call('al:native-cmd', 'status', {});
    check(!after.ok, 'after giving up, commands answer "not running"', after);
  }

  // 3. a stop that was asked for is not a crash
  {
    const S = makeShell();
    const s = await S.call('al:native-start');
    await S.call('al:native-stop');
    check(await until(() => !alive(s.pid), 3000), 'stop: the engine quits');
    await sleep(200);
    check(!S.events.some(e => e.ev === 'restarted' || e.ev === 'gave-up'), 'stop: no restart and no gave-up', S.events);
    const again = await S.call('al:native-start');
    check(again.ok && again.pid !== s.pid, 'started again after a stop', again);
    S.quit();
    check(await until(() => !alive(again.pid), 3000), 'quitting the app stops the engine');
  }

  // 4. an engine that dies at once after every start: three tries, then gave-up, no endless loop
  {
    process.env.FAKE_DIE_AFTER_READY = '1';
    const S = makeShell();
    await S.call('al:native-start');
    check(await until(() => S.events.some(e => e.ev === 'gave-up'), 6000), 'an engine that always dies: gave-up');
    const starts = S.events.filter(e => e.ev === 'restarted').length;
    check(starts <= 3, 'an engine that always dies: at most 3 restarts', starts);
    delete process.env.FAKE_DIE_AFTER_READY;
  }

  // 5. an engine that never answers: start fails after the wait, and the hung process does not stay behind
  {
    process.env.FAKE_SILENT = '1';
    const S = makeShell();
    const t = Date.now();
    const r = await S.call('al:native-start');
    const hung = logLines().filter(l => l.started).pop().pid;
    check(!r.ok && /did not answer/.test(r.error) && Date.now() - t < 12000, 'a hung engine: start fails with "did not answer"', r);
    check(await until(() => !alive(hung), 3000), 'a hung engine is killed, not left running', hung);
    delete process.env.FAKE_SILENT;
  }

  // 6. task NB-R3: the sound goes through the feeder, not through the main process
  const block = (v) => { const f = new Float32Array(256); f.fill(v); return f; };
  {
    const U = fakeUtility(), S = makeShell(U);
    const av = await S.call('al:native-available');
    check(av.feeder === true, 'feeder: available says the sound path is the feeder', av);
    await S.call('al:native-start');
    await S.call('al:native-cmd', 'open', { uid: 'fake-dac', rate: 48000 });
    const snd = await S.call('al:native-sound', { pageRate: 48000 });
    check(snd.ok && snd.feeder === true && snd.queueFrames === 12000 && snd.path === undefined, 'feeder: sound opened through the feeder, queue 250 ms (12,000 frames at 48 kHz), the socket path not handed to the page', snd);
    check(U.made.length === 1 && path.basename(U.made[0].file) === 'native-feeder.js', 'feeder: one feeder process, started from desktop/native-feeder.js', U.made.map(p => p.file));
    const p = S.port();
    check(p.listenerCount('message') === 0, 'feeder: the main process does not listen to the page port (it went on to the feeder)');
    // the port went to the feeder as a transfer: send blocks into it as the page would
    const fp = U.made[0].feeder;
    await sleep(20);
    for (let i = 0; i < 100; i++) p.emit('message', { data: i % 2 ? block(0.1) : block(0.2).buffer });
    p.emit('message', { data: 'not sound' });
    let st; for (let k = 0; k < 100; k++) { st = await S.call('al:native-cmd', 'status', {}); if (st.socketFrames >= 12800) break; await sleep(30); }
    check(st.socketFrames === 12800, 'feeder: every frame the page sent reached the engine (12,800)', st.socketFrames);
    check(st.tap && st.tap.path === 'feeder' && st.tap.blocks === 100 && st.tap.fedFrames === 12800 && st.tap.notFloat === 1 && U.made[0].feeder.stats().blocks === 100, 'feeder: the status carries the feeder\'s counts and its process', st.tap);
    // the page gives a new port (after a feeder restart): the feeder keeps its socket
    const p2 = S.port(); await sleep(30);
    for (let i = 0; i < 10; i++) p2.emit('message', { data: block(0.3) });
    for (let k = 0; k < 50; k++) { st = await S.call('al:native-cmd', 'status', {}); if (st.socketFrames >= 14080) break; await sleep(30); }
    check(st.socketFrames === 14080 && st.tap.socket === true, 'feeder: a new page port keeps the engine\'s socket (the old one is dropped)', st);
    // a frozen feeder: the watchdog finds it within about 3 s and starts another; the page is told to give a new port
    U.made[0].frozen = true;
    check(await until(() => S.events.some(e => e.ev === 'feeder-restarted'), 6000), 'feeder: a frozen feeder is found by the watchdog (3 missed pings)');
    const ev = S.events.find(e => e.ev === 'feeder-restarted');
    check(ev.ok && ev.needPort && U.made.length === 2 && U.made[0].dead, 'feeder: the frozen one is killed, a new one is connected to the engine, the page is asked for a new port', ev);
    const p3 = S.port(); await sleep(30);
    for (let i = 0; i < 10; i++) p3.emit('message', { data: block(0.4) });
    for (let k = 0; k < 50; k++) { st = await S.call('al:native-cmd', 'status', {}); if (st.tap && st.tap.fedFrames >= 1280) break; await sleep(30); }
    check(U.made[1].feeder.stats().fedFrames === 1280 && st.tap.fedFrames === 1280 && st.tap.feederRestarts === 1, 'feeder: the new feeder carries the sound', st.tap);
    await S.call('al:native-stop');
    check(U.made.every(p => p.dead), 'feeder: stop ends the feeder too');
  }

  // 7. task NB-R3: an engine that does not read (back-pressure): the feeder's queue stops at its bound and counts the drops
  {
    process.env.FAKE_PAUSE_READ = '1';
    const U = fakeUtility(), S = makeShell(U);
    await S.call('al:native-start');
    await S.call('al:native-cmd', 'open', { uid: 'fake-dac', rate: 48000 });
    await S.call('al:native-sound', { pageRate: 48000, queueMs: 50 });
    const p = S.port(); await sleep(30);
    for (let i = 0; i < 6000; i++) { p.emit('message', { data: block(0.5) }); if (i % 500 === 0) await sleep(5); }   // 768,000 frames, 16 s of sound
    await sleep(100);
    const t = U.made[0].feeder.stats();
    check(t.backPressure >= 1 && t.queuedMaxFrames <= 2400 && t.droppedFrames > 0 && t.blocks === 6000, 'back-pressure: the socket said wait, the queue stayed within 50 ms (' + t.queuedMaxFrames + ' of 2,400 frames), ' + t.droppedBlocks + ' blocks dropped and counted', t);
    check(t.fedFrames + t.queuedFrames + t.droppedFrames === 768000, 'back-pressure: every frame is either written, queued or counted as dropped', t);
    await S.call('al:native-stop');
    delete process.env.FAKE_PAUSE_READ;
  }

  // 8. task NB-R3: an engine that stops answering while it runs: the watchdog kills it, crash recovery starts it again
  {
    process.env.FAKE_HANG_AFTER_MS = '1500';
    const U = fakeUtility(), S = makeShell(U);
    const s = await S.call('al:native-start');
    await S.call('al:native-cmd', 'open', { uid: 'fake-dac', rate: 48000 });
    await S.call('al:native-sound', { pageRate: 48000 });
    check(await until(() => S.events.some(e => e.ev === 'engine-hung'), 8000), 'watchdog: an engine that stopped answering is found (3 missed pings)');
    check(await until(() => S.events.some(e => e.ev === 'restarted'), 4000) && !alive(s.pid), 'watchdog: the hung engine is killed and started again', S.events);
    const r = S.events.find(e => e.ev === 'restarted');
    check(r && r.ok, 'watchdog: the new engine got the device and the sound again (through the feeder)', r);
    delete process.env.FAKE_HANG_AFTER_MS;
    await S.call('al:native-stop');
  }

  // 9. task NB-R4 (review A10, C11): the protocol number, request numbers, a late answer
  {
    const { EngineBridge } = require(path.join(ROOT, 'native', 'bridge', 'engine-bridge.js'));
    process.env.FAKE_PROTOCOL = '2';
    const b = new EngineBridge(FAKE); let err = null;
    try { await b.start(); } catch (e) { err = e; }
    const pid = logLines().filter(l => l.started).pop().pid;
    check(err && /protocol 2, this app speaks 1/.test(err.message), 'an engine that speaks another protocol is refused', err && err.message);
    check(await until(() => !alive(pid), 3000), 'and it is not left running');
    delete process.env.FAKE_PROTOCOL;
    process.env.FAKE_SLOW_FIRST_STATUS_MS = '600';
    const c = new EngineBridge(FAKE); await c.start();
    const first = await c.send({ cmd: 'status' }, 200);
    const second = await c.send({ cmd: 'status' }, 2000);
    await sleep(700);
    const third = await c.send({ cmd: 'status' }, 2000);
    check(first.error === 'no answer' && second.ok && !second.late && third.ok && !third.late, 'a late answer is never taken for the answer to a later command of the same name', [first, second, third]);
    const cmds = logLines().filter(l => l.pid === c.pid && l.cmd).map(l => l.cmd.req);
    check(cmds.length >= 3 && new Set(cmds).size === cmds.length && cmds.every(r => Number.isInteger(r)), 'every command carries its own request number', cmds);
    delete process.env.FAKE_SLOW_FIRST_STATUS_MS;
    await c.stop();
    check(await until(() => !alive(c.pid), 4000), 'stop ends the engine');
  }

  try { fs.unlinkSync(LOG); } catch (e) { /* none */ }
  console.log(JSON.stringify({ re: 'bridge_unit', ok: fail === 0, passed: pass, failed: fail }));
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL exception ' + (e && e.stack || e)); process.exit(1); });
