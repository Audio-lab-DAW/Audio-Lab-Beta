// Proof for task NB-R3 (review RN5 A8): the page's sound reaches the engine through the shell's feeder process, so
// a busy main process no longer makes gaps. The real Electron shell with the real desktop/native-engine.js,
// desktop/native-feeder.js and desktop/preload.js; the real alengine on the null device (any machine, task NB-R2),
// which records what the "DAC" played (AL_NULL_RECORD). Production settings: prefill 30 ms, high 120 ms, exact clock.
//   AL_ENGINE=build/alengine AL_ENGINE_TEST=1 AL_NULL_RECORD=out/rec.wav \
//     electron tools/native-lab/electron-feeder/main.js <outdir> <seconds> [blockMs=50] [stopFeederAt=0] [busy|wait]
// With AL_FEED_IN_MAIN=1 the blocks go through the main process as before NB-R3 (the comparison).
// blockMs: every second the main process is held for this long (a stand-in for menus, handlers, the updater):
// 'busy' spins (a handler using a core, like hashing a download), 'wait' blocks without using a core (sync I/O).
// stopFeederAt: at that second the feeder process is frozen (SIGSTOP): the watchdog must start a new one and the
// page must hand it a new port.
'use strict';
const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(process.argv.findIndex(a => a.endsWith('main.js')) + 1);
const out = args[0], SECONDS = Number(args[1] || 20), BLOCK_MS = Number(args[2] || 50), STOP_AT = Number(args[3] || 0), KIND = args[4] === 'wait' ? 'wait' : 'busy', SR = 48000;
fs.mkdirSync(out, { recursive: true });
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
app.commandLine.appendSwitch('disable-renderer-backgrounding');
app.commandLine.appendSwitch('disable-background-timer-throttling');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const R = { seconds: SECONDS, blockMs: BLOCK_MS, holdKind: KIND, stopFeederAt: STOP_AT, mode: process.env.AL_FEED_IN_MAIN === '1' ? 'main' : 'feeder',
  electron: process.versions.electron, chrome: process.versions.chrome, statuses: [], blocks: [] };
const done = code => { fs.writeFileSync(path.join(out, 'feeder.json'), JSON.stringify(R, null, 1)); console.log(JSON.stringify(Object.assign({}, R, { statuses: R.statuses.length, blocks: R.blocks.length }))); app.exit(code); };

require('../../../desktop/native-engine.js').setup({ ipcMain, app });

function expected(frames) {
  const f = new Float32Array(frames * 2); let st = 0x2468ace1 >>> 0;
  for (let i = 0; i < frames; i++) {
    st = (Math.imul(st, 1664525) + 1013904223) >>> 0; f[2 * i] = ((st >>> 8) / 16777216 * 2 - 1) * 0.25;
    st = (Math.imul(st, 1664525) + 1013904223) >>> 0; f[2 * i + 1] = ((st >>> 8) / 16777216 * 2 - 1) * 0.25;
  }
  return f;
}
// hold the main process busy, as a long handler would
const WAIT = new Int32Array(new SharedArrayBuffer(4));
function hold(ms) { if (KIND === 'wait') { Atomics.wait(WAIT, 0, 0, ms); return; } const t = Date.now() + ms; while (Date.now() < t) { /* busy */ } }

app.whenReady().then(async () => {
  try {
    const win = new BrowserWindow({ width: 520, height: 320, show: true, webPreferences: { preload: path.join(__dirname, '..', '..', '..', 'desktop', 'preload.js'), backgroundThrottling: false } });
    const js = s => win.webContents.executeJavaScript(s);
    await win.loadFile(path.join(__dirname, 'page.html'), { query: { seconds: String(SECONDS), sr: String(SR) } });
    let st = null;
    for (let i = 0; i < 100; i++) { st = await js('window.__t'); if (st && (st.stage === 'opened' || st.error)) break; await sleep(200); }
    R.page = st;
    if (!st || st.error || st.stage !== 'opened') { R.error = (st && st.error) || 'the page did not open the device'; return done(0); }
    await js('window.__go()');
    // the busy main process: every second, BLOCK_MS of nothing else
    let holds = 0;
    const holder = BLOCK_MS > 0 ? setInterval(() => { const t0 = Date.now(); hold(BLOCK_MS); R.blocks.push(Date.now() - t0); holds++; }, 1000) : null;
    for (let s = 0; s < SECONDS + 6; s++) {
      await sleep(1000);
      const t = await js('window.__t');
      const ring = t.status && t.status.ring || {}, tap = t.status && t.status.tap || {};
      R.statuses.push({ s, fill: ring.fill, ranEmpty: ring.ranEmpty, dropped: ring.droppedTimes, tapPath: tap.path, blocks: tap.blocks, fed: tap.fedFrames, backPressure: tap.backPressure, queuedMax: tap.queuedMaxFrames, droppedFrames: tap.droppedFrames, feederPid: tap.feederPid, worstGapMs: tap.worstGapMs });
      if (STOP_AT && s === STOP_AT && tap.feederPid) { try { process.kill(tap.feederPid, 'SIGSTOP'); R.stopped = { pid: tap.feederPid, atSecond: s }; } catch (e) { R.stopped = { error: String(e) }; } }
      if (t.stage === 'finished') break;
    }
    if (holder) clearInterval(holder);
    R.holds = holds;
    R.page = await js('window.__t');
    fs.writeFileSync(path.join(out, 'sent.raw'), Buffer.from(expected(SECONDS * SR).buffer));
    await js('window.__end()');
    await sleep(800);
    done(0);
  } catch (e) { R.error = String(e && e.stack || e); done(1); }
});
