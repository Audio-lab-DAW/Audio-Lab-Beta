#!/usr/bin/env node
// A stand-in for alengine (task NB-R1): speaks the same JSON lines and takes sound on a local socket, so the
// shell's side of the bridge (desktop/native-engine.js, native/bridge/engine-bridge.js) can be tested on any
// machine, with no sound card. It keeps a log of every command it got in FAKE_LOG (one JSON line each).
//   FAKE_DIE_AFTER_READY=1  exits right after saying ready (a crashing engine)
//   FAKE_SILENT=1           never says ready (a hung engine)
'use strict';
const fs = require('fs');
const net = require('net');
const LOG = process.env.FAKE_LOG || '';
const log = o => { if (LOG) fs.appendFileSync(LOG, JSON.stringify(Object.assign({ pid: process.pid }, o)) + '\n'); };
const say = o => process.stdout.write(JSON.stringify(o) + '\n');

let dev = null, volume = 0.5, mute = false, server = null, frames = 0, bytes = 0, sockPath = '';
if (process.env.FAKE_SILENT !== '1') say({ ev: 'ready', pid: process.pid, version: 'fake' });
if (process.env.FAKE_DIE_AFTER_READY === '1') setTimeout(() => process.exit(3), 50);
log({ started: true });

let buf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  buf += chunk; let i;
  while ((i = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, i); buf = buf.slice(i + 1);
    let m; try { m = JSON.parse(line); } catch (e) { say({ re: '?', ok: false, error: 'not a JSON object' }); continue; }
    log({ cmd: m });
    const re = m.cmd;
    switch (m.cmd) {
      case 'devices': say({ re, defaultOutput: 1, devices: [{ id: 1, uid: 'fake-dac', name: 'Fake DAC', rates: [44100, 48000, 96000] }] }); break;
      case 'open': dev = m.uid || 'fake-dac'; say({ re, ok: true, uid: dev, rate: m.rate || 48000, buffer: m.buffer || 256 }); break;
      case 'close': dev = null; say({ re, ok: true }); break;
      case 'volume': volume = +m.value; say({ re, ok: true, value: volume }); break;
      case 'mute': mute = !!m.on; say({ re, ok: true, mute }); break;
      case 'clock': say({ re, ok: m.mode === 'exact' || m.mode === 'follow', mode: m.mode }); break;
      case 'status': say({ re, ok: true, device: dev, volume, mute, socketFrames: frames, socketBytes: bytes }); break;
      case 'source':
        if (server) { server.close(); server = null; }
        if (m.type === 'socket') {
          sockPath = m.path; try { fs.unlinkSync(sockPath); } catch (e) { /* none */ }
          server = net.createServer(c => { c.on('data', d => { bytes += d.length; frames = Math.floor(bytes / 8); }); });
          server.listen(sockPath, () => say({ re, ok: true, type: 'socket', path: sockPath, clock: m.clock }));
        } else say({ re, ok: true, type: m.type });
        break;
      case 'quit': say({ re, ok: true }); setTimeout(() => process.exit(0), 10); break;
      default: say({ re, ok: false, error: 'unknown command' });
    }
  }
});
process.stdin.on('end', () => process.exit(0));
