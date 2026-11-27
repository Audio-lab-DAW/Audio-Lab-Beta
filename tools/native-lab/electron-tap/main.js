// First proof for stage N2 (task NB-N2a), outside the app: the real desktop shell (Electron) sends the sound of a
// page to the native engine. The page's audio runs with no output of its own; an AudioWorklet hands every
// 128-frame block through a message port straight to the main process, which feeds alengine through
// native/bridge/engine-bridge.js. The loop-back device records what reaches the "DAC".
//   electron tools/native-lab/electron-tap/main.js <alengine> <alnative> <outdir> [seconds]
'use strict';
const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { EngineBridge } = require('../../../native/bridge/engine-bridge');

const args = process.argv.slice(process.argv.findIndex(a => a.endsWith('main.js')) + 1);
const [exe, alnative, out] = args;
const SECONDS = Number(args[3] || 20), SR = 48000;
fs.mkdirSync(out, { recursive: true });
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
app.commandLine.appendSwitch('disable-renderer-backgrounding');
app.commandLine.appendSwitch('disable-background-timer-throttling');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const R = { seconds: SECONDS, electron: process.versions.electron, chrome: process.versions.chrome, fills: [] };
const done = code => { fs.writeFileSync(path.join(out, 'tap.json'), JSON.stringify(R, null, 1)); console.log(JSON.stringify(R)); app.exit(code); };

// the same numbers the worklet makes, so the test knows what was sent
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
    const eng = new EngineBridge(exe);
    await eng.start();
    const list = await eng.devices();
    const bh = (list.devices || []).find(d => d.name.includes('BlackHole'));
    if (!bh) { R.error = 'no loop-back device on this machine'; return done(0); }
    const o = await eng.open({ uid: bh.uid, rate: SR, buffer: 256 });
    R.open = { ok: o.ok, rate: o.rate, buffer: o.buffer };
    await eng.startSound({ prefillMs: 100, highMs: 1000 });
    let blocks = 0, frames = 0, firstAt = 0, lastAt = 0, worstGapMs = 0;
    ipcMain.on('tap-port', e => {
      const port = e.ports[0];
      port.on('message', m => {
        const d = m.data; let f;
        if (d instanceof ArrayBuffer) f = new Float32Array(d);
        else if (ArrayBuffer.isView(d)) f = new Float32Array(d.buffer, d.byteOffset, Math.floor(d.byteLength / 4));
        else { R.dataKind = Object.prototype.toString.call(d); return; }
        if (!R.dataKind) R.dataKind = Object.prototype.toString.call(d);
        const now = Date.now(); if (!firstAt) firstAt = now; else if (now - lastAt > worstGapMs) worstGapMs = now - lastAt; lastAt = now;
        eng.feed(f); blocks++; frames += f.length / 2;
      });
      port.start();
    });
    ipcMain.on('tap-info', (e, info) => { R.page = Object.assign(R.page || {}, info); });
    const rec = spawn(alnative, ['record', '--device', String(bh.id), '--seconds', String(SECONDS * 2 + 6), '--to', path.join(out, 'tap_loopback.wav')], { stdio: 'ignore' });
    const recDone = new Promise(r => rec.on('exit', r));
    await sleep(700);
    const win = new BrowserWindow({ width: 500, height: 300, show: true, webPreferences: { preload: path.join(__dirname, 'preload.js'), backgroundThrottling: false } });
    await win.loadFile(path.join(__dirname, 'page.html'), { query: { seconds: String(SECONDS), sr: String(SR) } });
    for (let s = 0; s < SECONDS * 2 + 4 && frames < SECONDS * SR; s++) { await sleep(1000); const st = await eng.status(); R.fills.push(st.ring ? st.ring.fill : -1); R.lastStatus = { ring: st.ring, overloads: st.overloads }; }
    await recDone;
    R.blocks = blocks; R.framesFromPage = frames; R.worstGapBetweenBlocksMs = worstGapMs;
    R.pageSecondsByWallClock = (lastAt - firstAt) / 1000;
    // how far the page's clock and the device's clock moved apart: the ring's fill at the start and the end of steady play
    R.pageSpeedAgainstWallClock = frames / SR / R.pageSecondsByWallClock;
    const mid = R.fills.slice(2, R.fills.length - 2);
    if (mid.length > 4) R.driftFramesPerSecond = (mid[mid.length - 1] - mid[0]) / (mid.length - 1);
    if (R.driftFramesPerSecond !== undefined) R.driftPartsPerMillion = R.driftFramesPerSecond / SR * 1e6;
    const exp = expected(frames);
    fs.writeFileSync(path.join(out, 'tap_sent.raw'), Buffer.from(exp.buffer));
    await eng.close(); await eng.stop();
    done(0);
  } catch (e) { R.error = String(e && e.stack || e); done(1); }
});
