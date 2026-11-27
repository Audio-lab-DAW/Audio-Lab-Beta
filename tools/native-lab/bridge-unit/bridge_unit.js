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

// one fake Electron main process per scenario (the shell keeps its state inside setup())
function makeShell() {
  const handlers = {}, listeners = {}, quit = [];
  const ipcMain = { handle: (n, f) => { handlers[n] = f; }, on: (n, f) => { listeners[n] = f; } };
  const app = { isPackaged: false, on: (n, f) => { if (n === 'will-quit') quit.push(f); } };
  const events = [];
  const sender = { send: (ch, d) => { if (ch === 'al:native-ev') events.push(d); }, isDestroyed: () => false };
  shell.setup({ ipcMain, app });
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

  try { fs.unlinkSync(LOG); } catch (e) { /* none */ }
  console.log(JSON.stringify({ re: 'bridge_unit', ok: fail === 0, passed: pass, failed: fail }));
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL exception ' + (e && e.stack || e)); process.exit(1); });
