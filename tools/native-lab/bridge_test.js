// Test of the app's side of the engine (task NB-N1): Node starts alengine through native/bridge/engine-bridge.js,
// opens the loop-back device, and feeds it the web engine's own renders the way the app's main process would.
//   node tools/native-lab/bridge_test.js build/alengine build/alnative outdir
'use strict';
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { EngineBridge } = require('../../native/bridge/engine-bridge');
const [exe, alnative, out] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const wavData = f => { const b = fs.readFileSync(f); const i = b.indexOf('data'); const n = b.readUInt32LE(i + 4); return b.subarray(i + 8, i + 8 + n); };
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const R = {};
  const eng = new EngineBridge(exe);
  const events = [];
  for (const n of ['volume', 'rate', 'devices', 'sound-connected', 'sound-disconnected', 'stopped']) eng.on(n, e => events.push(e));
  R.ready = await eng.start();
  const list = await eng.devices();
  const bh = (list.devices || []).find(d => d.name.includes('BlackHole'));
  if (!bh) { R.error = 'no loop-back device on this machine'; fs.writeFileSync(path.join(out, 'bridge.json'), JSON.stringify(R, null, 1)); console.log(R.error); await eng.stop(); return; }
  const o = await eng.open({ uid: bh.uid, rate: 48000, buffer: 256 });
  R.open = { ok: o.ok, notes: o.notes, tookMilliseconds: o.tookMilliseconds, rate: o.rate, buffer: o.buffer };
  await eng.startSound({ prefillMs: 150, highMs: 1500, pageRate: 48000 });
  const ref = f => wavData(path.join(__dirname, 'ref', f));
  const one = Buffer.concat([ref('crush_plain_web.wav'), ref('crush_filter_web.wav'), ref('crush_dither_web.wav')]);
  const sent = Buffer.concat([one, one]);
  fs.writeFileSync(path.join(out, 'bridge_sent.raw'), sent);
  const rec = spawn(alnative, ['record', '--device', String(bh.id), '--seconds', '5', '--to', path.join(out, 'bridge_loopback.wav')], { stdio: 'ignore' });
  const recDone = new Promise(r => rec.on('exit', r));
  await sleep(600);
  // feed in pieces of 128 frames (the web engine's block), 400 ms ahead of real time
  const piece = 128 * 8, t0 = Date.now();
  let pos = 0;
  await new Promise(resolve => {
    const tick = setInterval(() => {
      const due = ((Date.now() - t0) / 1000 + 0.4) * 48000 * 8;
      while (pos < sent.length && pos < due) {
        const b = sent.subarray(pos, pos + piece);
        eng.feed(new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.length)));
        pos += piece;
      }
      if (pos >= sent.length) { clearInterval(tick); resolve(); }
    }, 4);
  });
  await sleep(700);
  const st = await eng.status();
  R.status = { ring: st.ring, overloads: st.overloads, callbacks: st.callbacks };
  R.fedFrames = eng.fed;
  await recDone;
  const v = await eng.volume(0.6); await sleep(200);
  R.volume = { asked: 0.6, readBack: v.value, eventSeen: events.filter(e => e.ev === 'volume').pop() || null };
  await eng.volume(1.0);
  await eng.close();
  await eng.stop();
  await sleep(300);
  R.events = events.map(e => e.ev);
  fs.writeFileSync(path.join(out, 'bridge.json'), JSON.stringify(R, null, 1));
  console.log(JSON.stringify(R));
  process.exit(0);
})().catch(e => { console.error('bridge test failed:', e); process.exit(1); });
