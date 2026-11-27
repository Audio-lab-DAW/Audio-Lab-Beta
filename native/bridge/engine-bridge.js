// The desktop app's side of the native engine (task NB-N1). Plain Node, nothing from Electron, so the same
// file runs in the app's main process and in a test. It starts alengine as a helper, talks to it in JSON
// lines, and sends sound to it through a local socket.
//
//   const { EngineBridge } = require('./engine-bridge');
//   const eng = new EngineBridge('/path/to/alengine');
//   await eng.start();
//   const list = await eng.devices();
//   await eng.open({ uid, rate: 96000, buffer: 64, exclusive: true });
//   await eng.startSound({ prefillMs: 30, highMs: 120, clock: 'exact' });   // or clock: 'follow' (task NB-N2b)
//   eng.feed(float32StereoInterleaved);            // as it arrives from the page
//   eng.on('volume', e => ...); eng.on('devices', e => ...); eng.on('rate', e => ...);
'use strict';
const { spawn } = require('child_process');
const net = require('net');
const os = require('os');
const path = require('path');
const { EventEmitter } = require('events');

class EngineBridge extends EventEmitter {
  constructor(exe) { super(); this.exe = exe; this.proc = null; this.waiting = []; this.sock = null; this.buf = ''; this.pid = 0; this.fed = 0; }

  start() {
    return new Promise((resolve, reject) => {
      let done = false, timer = null;
      this.proc = spawn(this.exe, [], { stdio: ['pipe', 'pipe', 'ignore'] });
      this.proc.on('error', e => { if (!done) { done = true; clearTimeout(timer); reject(e); } });
      this.proc.on('exit', code => { this.proc = null; for (const w of this.waiting) w.resolve({ ok: false, error: 'the engine stopped' }); this.waiting = []; this.emit('stopped', { code }); });
      this.proc.stdout.setEncoding('utf8');
      this.proc.stdout.on('data', chunk => {
        this.buf += chunk;
        let i;
        while ((i = this.buf.indexOf('\n')) >= 0) {
          const line = this.buf.slice(0, i); this.buf = this.buf.slice(i + 1);
          let m; try { m = JSON.parse(line); } catch (e) { continue; }
          if (m.ev) {
            if (m.ev === 'ready') { this.pid = m.pid; if (!done) { done = true; clearTimeout(timer); resolve(m); } }
            this.emit(m.ev, m);
          } else if (m.re !== undefined) {
            const k = this.waiting.findIndex(w => w.cmd === m.re);
            if (k >= 0) this.waiting.splice(k, 1)[0].resolve(m);
          }
        }
      });
      // a helper that never says ready is killed, not left running behind the app (task NB-R1, found by bridge_unit.js)
      const p = this.proc;
      timer = setTimeout(() => { if (!done) { done = true; try { p.kill('SIGKILL'); } catch (e) { /* gone */ } reject(new Error('the engine did not answer')); } }, 8000);
    });
  }

  send(obj, timeoutMs = 15000) {
    return new Promise(resolve => {
      if (!this.proc) return resolve({ ok: false, error: 'the engine is not running' });
      const w = { cmd: obj.cmd, resolve };
      this.waiting.push(w);
      setTimeout(() => { const k = this.waiting.indexOf(w); if (k >= 0) { this.waiting.splice(k, 1); resolve({ ok: false, error: 'no answer' }); } }, timeoutMs);
      this.proc.stdin.write(JSON.stringify(obj) + '\n');
    });
  }
  devices() { return this.send({ cmd: 'devices' }); }
  formats(o = {}) { return this.send(Object.assign({ cmd: 'formats' }, o)); }
  open(o = {}) { return this.send(Object.assign({ cmd: 'open' }, o)); }
  close() { return this.send({ cmd: 'close' }); }
  volume(value) { return this.send({ cmd: 'volume', value }); }
  mute(on) { return this.send({ cmd: 'mute', on: !!on }); }
  status() { return this.send({ cmd: 'status' }); }
  tone() { return this.send({ cmd: 'source', type: 'tone' }); }
  silence() { return this.send({ cmd: 'source', type: 'silence' }); }
  // task NB-N2b: 'exact' hands every sample over untouched (rare corrections), 'follow' steers smoothly to the sender's clock
  clock(mode) { return this.send({ cmd: 'clock', mode }); }

  // Opens the way for sound: the engine listens on a socket, this side connects.
  async startSound(o = {}) {
    this.stopSound();
    const p = path.join(os.tmpdir(), 'audiolab-engine-' + process.pid + '-' + Date.now() + '.sock');
    const r = await this.send({ cmd: 'source', type: 'socket', path: p, prefillMs: o.prefillMs || 30, highMs: o.highMs || 120, clock: o.clock === 'follow' ? 'follow' : 'exact', limitPpm: +o.limitPpm || 2000 });
    if (!r.ok) return r;
    await new Promise((resolve, reject) => { this.sock = net.connect(p, resolve); this.sock.on('error', reject); });
    this.sock.on('error', () => {});
    this.fed = 0;
    return r;
  }
  // Float32Array, stereo interleaved, at the device's rate. Returns false when the socket asks for a pause.
  feed(f32) {
    if (!this.sock) return false;
    this.fed += f32.length / 2;
    return this.sock.write(Buffer.from(f32.buffer, f32.byteOffset, f32.byteLength));
  }
  stopSound() { if (this.sock) { try { this.sock.destroy(); } catch (e) {} this.sock = null; } }

  async stop() {
    this.stopSound();
    if (!this.proc) return;
    const p = this.proc;
    await this.send({ cmd: 'quit' }, 3000);
    setTimeout(() => { try { p.kill(); } catch (e) {} }, 1500);
  }
}

module.exports = { EngineBridge };
