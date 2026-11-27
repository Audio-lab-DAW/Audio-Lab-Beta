#!/usr/bin/env node
// A stand-in for alengine (task NB-R1): speaks the same JSON lines and takes sound on a local socket, so the
// shell's side of the bridge (desktop/native-engine.js, native/bridge/engine-bridge.js) can be tested on any
// machine, with no sound card. It keeps a log of every command it got in FAKE_LOG (one JSON line each).
//   FAKE_DIE_AFTER_READY=1  exits right after saying ready (a crashing engine)
//   FAKE_SILENT=1           never says ready (a hung engine)
//   FAKE_HANG_AFTER_MS=n    stops answering n ms after it started, but stays alive (task NB-R3: the watchdog's case)
//   FAKE_SLOW_FIRST_STATUS_MS=n  answers the first status n ms late (task NB-R4: a late answer must not be taken for the next one)
//   FAKE_PROTOCOL=n         says protocol n in ready (task NB-R4)
//   FAKE_FORMAT_EVENT_MS=n  says a format event n ms after ready (task NB-R4b: the shell passes it to the page)
//   FAKE_PAUSE_READ=1       takes the sound connection but never reads from it (task NB-R3: back-pressure)
'use strict';
const fs = require('fs');
const net = require('net');
const LOG = process.env.FAKE_LOG || '';
const log = o => { if (LOG) fs.appendFileSync(LOG, JSON.stringify(Object.assign({ pid: process.pid }, o)) + '\n'); };
let curReq, slowDone = false;   // task NB-R4: answers carry the command's request number
const say = o => process.stdout.write(JSON.stringify(o.re !== undefined && curReq !== undefined ? Object.assign({ req: curReq }, o) : o) + '\n');

let ceiling = 0.5;   // task NB-R4b: the volume ceiling, as alengine's
let rate = 48000, dev = null, volume = 0.5, mute = false, server = null, frames = 0, bytes = 0, sockPath = '';
if (process.env.FAKE_SILENT !== '1') say({ ev: 'ready', pid: process.pid, version: 'fake', protocol: process.env.FAKE_PROTOCOL !== undefined ? Number(process.env.FAKE_PROTOCOL) : 1 });
if (process.env.FAKE_FORMAT_EVENT_MS) setTimeout(() => say({ ev: 'format', handedToUs: '24-bit integer, 2 ch, 48000 Hz', restarted: true, error: '' }), Number(process.env.FAKE_FORMAT_EVENT_MS));   // task NB-R4b
if (process.env.FAKE_DIE_AFTER_READY === '1') setTimeout(() => process.exit(3), 50);
log({ started: true });

const HANG_AT = process.env.FAKE_HANG_AFTER_MS ? Date.now() + Number(process.env.FAKE_HANG_AFTER_MS) : 0;
let buf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  buf += chunk; let i;
  while ((i = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, i); buf = buf.slice(i + 1);
    if (HANG_AT && Date.now() >= HANG_AT) continue;
    let m; try { m = JSON.parse(line); } catch (e) { say({ re: '?', ok: false, error: 'not a JSON object' }); continue; }
    log({ cmd: m });
    curReq = m.req;
    const re = m.cmd;
    switch (m.cmd) {
      case 'devices': say({ re, defaultOutput: 1, devices: [{ id: 1, uid: 'fake-dac', name: 'Fake DAC', rates: [44100, 48000, 96000] }] }); break;
      case 'open': dev = m.uid || 'fake-dac'; rate = m.rate || rate; say({ re, ok: true, uid: dev, rate, buffer: m.buffer || 256 }); break;
      case 'close': dev = null; say({ re, ok: true }); break;
      case 'volume': {   // like alengine 0.5: louder than the loudest level the device has had needs confirm (task NB-R4b)
        const v = +m.value;
        if (v > ceiling + 1e-9 && m.confirm !== true) { say({ re, ok: false, needsConfirm: true, ceiling, value: volume, error: 'louder than this device has been' }); break; }
        if (v > ceiling) ceiling = v;
        volume = v; say({ re, ok: true, value: volume, target: v, ceiling }); break;
      }
      case 'mute': mute = !!m.on; say({ re, ok: true, mute }); break;
      case 'clock': say({ re, ok: m.mode === 'exact' || m.mode === 'follow', mode: m.mode }); break;
      case 'status':
        if (process.env.FAKE_SLOW_FIRST_STATUS_MS && !slowDone) { slowDone = true; const rq = m.req, ans = { re, req: rq, ok: true, late: true }; setTimeout(() => process.stdout.write(JSON.stringify(ans) + '\n'), Number(process.env.FAKE_SLOW_FIRST_STATUS_MS)); break; }
        say({ re, ok: true, device: dev, volume, mute, socketFrames: frames, socketBytes: bytes }); break;
      case 'source':
        if (server) { server.close(); server = null; }
        if (m.type === 'socket' && m.pageRate !== rate) { say({ re, ok: false, error: 'pageRate ' + m.pageRate + ' is not the device rate ' + rate, pageRate: m.pageRate, deviceRate: rate }); break; }
        if (m.type === 'socket') {
          sockPath = m.path; try { fs.unlinkSync(sockPath); } catch (e) { /* none */ }
          server = net.createServer(c => { if (process.env.FAKE_PAUSE_READ === '1') { c.pause(); return; } c.on('data', d => { bytes += d.length; frames = Math.floor(bytes / 8); }); });
          const rq = m.req; server.listen(sockPath, () => process.stdout.write(JSON.stringify({ re, req: rq, ok: true, type: 'socket', path: sockPath, clock: m.clock }) + '\n'));
        } else say({ re, ok: true, type: m.type });
        break;
      case 'quit': say({ re, ok: true }); setTimeout(() => process.exit(0), 10); break;
      default: say({ re, ok: false, error: 'unknown command' });
    }
  }
});
process.stdin.on('end', () => process.exit(0));
