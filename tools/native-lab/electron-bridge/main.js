// Proof for stage N2b (task NB-N2b): the app's own pieces, outside the app. The real desktop shell (Electron)
// with the real desktop/native-engine.js and desktop/preload.js, and a page that uses only what the app's page
// will use: window.audiolabDesktop.nativeEngine and native/bridge/page-tap.js. The loop-back device records
// what reaches the "DAC".
//   AL_ENGINE=build/alengine electron tools/native-lab/electron-bridge/main.js <alnative> <outdir> <seconds> <exact|follow> <noise|sine> [kill-at-second]
// With a kill second the engine is killed while it plays, to prove the shell starts it again (crash recovery).
'use strict';
const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const args = process.argv.slice(process.argv.findIndex(a => a.endsWith('main.js')) + 1);
const [alnative, out] = args;
const SECONDS = Number(args[2] || 20), CLOCK = args[3] || 'exact', SIGNAL = args[4] || 'noise', KILL_AT = Number(args[5] || 0), SR = 48000;
fs.mkdirSync(out, { recursive: true });
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
app.commandLine.appendSwitch('disable-renderer-backgrounding');
app.commandLine.appendSwitch('disable-background-timer-throttling');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const R = { seconds: SECONDS, clock: CLOCK, signal: SIGNAL, electron: process.versions.electron, chrome: process.versions.chrome, statuses: [] };
const done = code => { fs.writeFileSync(path.join(out, 'bridge.json'), JSON.stringify(R, null, 1)); console.log(JSON.stringify(Object.assign({}, R, { statuses: R.statuses.length }))); app.exit(code); };

// the shell's side, exactly as the app sets it up
require('../../../desktop/native-engine.js').setup({ ipcMain, app });

// the same numbers the page makes for 'noise', so the test knows what was sent
function expected(frames) {
  const f = new Float32Array(frames * 2); let st = 0x2468ace1 >>> 0;
  for (let i = 0; i < frames; i++) {
    st = (Math.imul(st, 1664525) + 1013904223) >>> 0; f[2 * i] = ((st >>> 8) / 16777216 * 2 - 1) * 0.25;
    st = (Math.imul(st, 1664525) + 1013904223) >>> 0; f[2 * i + 1] = ((st >>> 8) / 16777216 * 2 - 1) * 0.25;
  }
  return f;
}

app.whenReady().then(async () => {
  try {
    const win = new BrowserWindow({ width: 520, height: 320, show: true, webPreferences: { preload: path.join(__dirname, '..', '..', '..', 'desktop', 'preload.js'), backgroundThrottling: false } });
    const js = s => win.webContents.executeJavaScript(s);
    await win.loadFile(path.join(__dirname, 'page.html'), { query: { seconds: String(SECONDS), sr: String(SR), clock: CLOCK, signal: SIGNAL } });
    // the page starts the engine and opens the loop-back device itself; wait for it
    let st = null;
    for (let i = 0; i < 100; i++) { st = await js('window.__t'); if (st && (st.stage === 'opened' || st.error)) break; await sleep(200); }
    R.page = st;
    if (!st || st.error || st.stage !== 'opened') { R.error = (st && st.error) || 'the page did not open the device'; return done(0); }
    const rec = spawn(alnative, ['record', '--device', String(st.deviceId), '--seconds', String(SECONDS + 8), '--to', path.join(out, 'loopback.wav')], { stdio: 'ignore' });
    const recDone = new Promise(r => rec.on('exit', r));
    await sleep(700);
    await js('window.__go()');
    for (let s = 0; s < SECONDS + 6; s++) {
      await sleep(1000);
      const t = await js('window.__t');
      if (t.status) R.statuses.push({ s, fill: t.status.ring && t.status.ring.fill, ppm: t.status.ring && t.status.ring.ppm, ranEmpty: t.status.ring && t.status.ring.ranEmpty, dropped: t.status.ring && t.status.ring.droppedTimes, blocks: t.status.tap && t.status.tap.blocks });
      if (KILL_AT && s === KILL_AT && t.start && t.start.pid) { try { process.kill(t.start.pid, 'SIGKILL'); R.killed = { pid: t.start.pid, atSecond: s }; } catch (e) { R.killed = { error: String(e) }; } }
      if (t.stage === 'finished') break;
    }
    await recDone;
    R.page = await js('window.__t');
    if (SIGNAL === 'noise') fs.writeFileSync(path.join(out, 'sent.raw'), Buffer.from(expected(SECONDS * SR).buffer));
    await js('window.__end()');
    done(0);
  } catch (e) { R.error = String(e && e.stack || e); done(1); }
});
