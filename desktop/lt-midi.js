// Fast MIDI notes (task LT-3a, lane J, the user's AE2 pick L5; docs/latency-build.md).
//
// Notes from a MIDI keyboard used to reach the sound through the app page's main thread: Web MIDI event, then the
// controller layer, then noteOn, then a message to the instrument's AudioWorklet. When that thread is busy (drawing,
// a long task, a project loading) the note waits. Here notes are read in a small hidden window of the shell that
// does nothing else, and posted straight into the audio worklet through a MessagePort, with their time stamps:
//
//   page: makes a MessageChannel, moves one end into its AudioWorklet and posts the other to its own window
//         ({ ltMidiPort: true }); preload.js hands it to this process ('al:lt-port').
//   here: makes the listening window on the first port (its own renderer process: a separate session partition)
//         and hands the port on. Nothing else: no MIDI goes through this process.
//   listening window (this same file, run as its preload): Web MIDI inputs, read only (nothing is ever sent, so
//         no feedback loop), only the ports the page names as plain note inputs (the controller layer's generic
//         profile; surfaces such as the Push, Mackie and the IAC "to Cubase" kind of port never), notes and the
//         sustain pedal only; a port that sends a flood (a loop) is left out for a while.
//
// The page's own Web MIDI keeps everything else (controllers, MIDI learn, surfaces) and still sees the notes for
// the piano display and recording; it does not play a note the worklet already played.
// AL_LT_TEST=1: the shell takes injected notes for the tests (inject(bytes) in this process).
'use strict';

if (typeof process !== 'undefined' && process.type === 'renderer') {
  /* ---------- the listening window ---------- */
  const { ipcRenderer } = require('electron');
  const pages = new Map();             // sender id -> { port, allow: Set of port names }
  const flood = new Map();             // input name -> { t, n, until }
  let acc = null, asked = false, pend = [];
  const ins = () => (acc ? [...acc.inputs.values()].filter((i) => i.state !== 'disconnected').map((i) => i.name) : []);
  const pong = (p, v) => { try { p.port.postMessage({ pong: v, t: now(), ins: ins() }); } catch (e) { /* ignore */ } };
  const TEST = (process.argv || []).includes('--al-lt-test');
  const now = () => performance.timeOrigin + performance.now();
  const send = (name, data, t) => {
    if (name) {
      const now2 = performance.now(), f = flood.get(name) || { t: now2, n: 0, until: 0 };
      if (now2 < f.until) return;
      if (now2 - f.t > 1000) { f.t = now2; f.n = 0; }
      if (++f.n > 600) { f.until = now2 + 5000; flood.set(name, f); return; }   // a loop or a broken cable: leave it out for 5 s
      flood.set(name, f);
    }
    const s = data[0] & 0xf0;
    if (!(s === 0x90 || s === 0x80 || (s === 0xB0 && data[1] === 64))) return;   // notes and the sustain pedal only
    for (const p of pages.values()) {
      if (name && !p.allow.has(name)) continue;
      try { p.port.postMessage({ m: [data[0], data[1], data[2] || 0], t, n: name || '' }); } catch (e) { /* ignore */ }
    }
  };
  const bind = () => {
    if (!acc) return;
    for (const i of acc.inputs.values()) {
      if (i.__lt) continue;
      i.__lt = 1;
      i.onmidimessage = (ev) => send(i.name, ev.data, performance.timeOrigin + ev.timeStamp);
    }
  };
  const start = () => {
    if (asked || !navigator.requestMIDIAccess) return;
    asked = true;
    const done = () => { const w = pend; pend = []; for (const [p, v] of w) pong(p, v); };
    navigator.requestMIDIAccess({ sysex: false }).then((a) => {
      acc = a; bind(); done();
      a.onstatechange = () => { bind(); for (const p of pages.values()) pong(p, 0); };   // a keyboard plugged in or out: the page learns which ports are read here
    }, () => { asked = false; done(); });
  };
  ipcRenderer.on('al:lt-port', (e, id) => {
    const port = e.ports && e.ports[0];
    if (!port) return;
    const old = pages.get(id);
    if (old) try { old.port.close(); } catch (x) { /* ignore */ }
    const p = { port, allow: new Set() };
    pages.set(id, p);
    port.onmessage = (ev) => {
      const d = ev.data || {};
      if (Array.isArray(d.ports)) { p.allow = new Set(d.ports.map(String)); start(); bind(); }
      if (d.ping) { if (acc || !asked) pong(p, d.ping); else pend.push([p, d.ping]); }
    };
    port.start();
  });
  ipcRenderer.on('al:lt-gone', (e, id) => { const p = pages.get(id); if (p) { try { p.port.close(); } catch (x) { /* ignore */ } pages.delete(id); } });
  if (TEST) ipcRenderer.on('al:lt-inject', (e, bytes) => send('', bytes, now()));
} else {
  /* ---------- the shell's main process ---------- */
  let win = null, waiting = [], made = false;
  const users = new Set();   // the pages that use it: when the last one goes, so does the window (it must never keep the app open, or count as a window)
  const make = ({ BrowserWindow, session, scheme }) => {
    if (made) return;
    made = true;
    const path = require('path');
    const ses = session.fromPartition('al-lt-midi');   // its own process: never shares the app page's renderer
    ses.setPermissionRequestHandler((wc, perm, cb) => cb(perm === 'midi'));
    ses.setPermissionCheckHandler((wc, perm) => perm === 'midi');
    // a page on the app's own (secure) scheme so Web MIDI is allowed; it is empty, the preload does the work
    try { ses.protocol.handle(scheme, () => new Response('<!doctype html><title>AudioLab MIDI notes</title>', { headers: { 'Content-Type': 'text/html' } })); } catch (e) { /* already there */ }
    win = new BrowserWindow({
      show: false, width: 100, height: 100, skipTaskbar: true, focusable: false, paintWhenInitiallyHidden: false,
      webPreferences: {
        preload: __filename, partition: 'al-lt-midi', contextIsolation: true, nodeIntegration: false, sandbox: true,
        backgroundThrottling: false, spellcheck: false,
        additionalArguments: process.env.AL_LT_TEST === '1' ? ['--al-lt-test'] : []
      }
    });
    win.webContents.once('did-finish-load', () => { const w = waiting; waiting = []; for (const f of w) f(); });
    win.on('closed', () => { win = null; made = false; });
    win.loadURL(scheme + '://lt-midi/');
  };
  const ready = (f) => { if (win && !win.webContents.isLoading()) f(); else waiting.push(f); };
  function setup({ ipcMain, BrowserWindow, session, scheme, app }) {
    const deps = { BrowserWindow, session, scheme };
    ipcMain.on('al:lt-port', (e) => {
      const port = e.ports && e.ports[0], id = e.sender.id;
      if (!port) return;
      make(deps);
      ready(() => { if (win) win.webContents.postMessage('al:lt-port', id, [port]); });
      if (!users.has(id)) {
        users.add(id);
        e.sender.once('destroyed', () => {
          users.delete(id);
          if (!win) return;
          if (users.size) win.webContents.send('al:lt-gone', id);
          else { try { win.destroy(); } catch (x) { /* ignore */ } win = null; made = false; waiting = []; }
        });
      }
    });
    if (app) app.on('before-quit', () => { try { if (win) win.destroy(); } catch (x) { /* ignore */ } });
  }
  // tests only (AL_LT_TEST=1): a note as if it came from a MIDI keyboard, read by the listening window
  function inject(bytes) { if (process.env.AL_LT_TEST === '1' && win) win.webContents.send('al:lt-inject', Array.from(bytes)); return !!win; }
  module.exports = { setup, inject };
}
