// AudioLab Pro: AI voices for the Voice device (task Z2). Kept in its own file so main.js only needs one line.
// - Downloads the model on first use (Hugging Face, a pinned revision), checks every file's SHA-256, keeps it in userData/voice-ai.
// - Runs the model in a utility process (voice-ai-worker.js) and closes it after 3 minutes without work (frees the memory).
// - Saves voices made from clips (userData/voice-ai/voices), so they can be used in every project.
'use strict';
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

const REV = '1be2e319a10a88ff2d268eb1ec2977740df729f2';
const BASE = 'https://huggingface.co/moonbox-dev/OpenVoiceV2-ONNX/resolve/' + REV + '/fp16/';
const MODEL = {
  id: 'openvoice-v2-fp16',
  name: 'OpenVoice V2 (MyShell, MIT licence)',
  files: [
    { name: 'converter.onnx', size: 64313099, sha256: '22a79ab872d1fd3b9da5853f7725b97fddac1a6eee18f8478ea5d010973fa4c3' },
    { name: 'ref_encoder.onnx', size: 1635922, sha256: '50742432520f98aabe70148674109fbe66a33f3a73fa5cd014edd600830b6321' }
  ]
};

function setup({ ipcMain, app }) {
  const root = () => path.join(app.getPath('userData'), 'voice-ai');
  const mdir = () => path.join(root(), MODEL.id);
  const vdir = () => path.join(root(), 'voices');
  const have = () => MODEL.files.every((f) => { try { return fs.statSync(path.join(mdir(), f.name)).size === f.size; } catch (e) { return false; } });

  /* ---- the utility process ---- */
  let proc = null, seq = 0, idle = null;
  const jobs = new Map();
  function worker() {
    if (proc) return proc;
    const { utilityProcess } = require('electron');
    proc = utilityProcess.fork(path.join(__dirname, 'voice-ai-worker.js'), [], { serviceName: 'AudioLab AI voices' });
    proc.on('message', (r) => { const j = jobs.get(r.id); if (!j) return; if (r.p != null && r.ok == null && !r.err) { j.prog && j.prog(r.p); return; } jobs.delete(r.id); if (r.err) j.rej(new Error(r.err)); else j.res(r); });
    proc.on('exit', () => { proc = null; for (const [, j] of jobs) j.rej(new Error('The AI voice process stopped. Try again.')); jobs.clear(); });
    return proc;
  }
  function job(m, prog) {
    clearTimeout(idle);
    return new Promise((res, rej) => { const id = ++seq; jobs.set(id, { res, rej, prog }); worker().postMessage(Object.assign({ id, dir: mdir() }, m)); })
      .finally(() => { if (!jobs.size) { clearTimeout(idle); idle = setTimeout(() => { if (proc && !jobs.size) { try { proc.kill(); } catch (e) { /* ignore */ } proc = null; } }, 180000); } });
  }

  /* ---- download with progress and checksum ---- */
  let dl = null;
  async function download(sender) {
    if (dl) return dl;
    dl = (async () => {
      const { net } = require('electron');
      fs.mkdirSync(mdir(), { recursive: true });
      const total = MODEL.files.reduce((a, f) => a + f.size, 0); let done = 0;
      for (const f of MODEL.files) {
        const dst = path.join(mdir(), f.name);
        if (fs.existsSync(dst) && fs.statSync(dst).size === f.size) { done += f.size; continue; }
        const tmp = dst + '.part', h = crypto.createHash('sha256'), out = fs.createWriteStream(tmp);
        const ac = new AbortController(); let stall = setTimeout(() => ac.abort(), 60000);
        try {
          const res = await net.fetch(BASE + f.name, { signal: ac.signal });
          if (!res.ok) throw new Error('the server answered ' + res.status);
          const rd = res.body.getReader(); let got = 0, last = 0;
          for (;;) {
            const { value, done: end } = await rd.read(); if (end) break;
            clearTimeout(stall); stall = setTimeout(() => ac.abort(), 60000);
            const b = Buffer.from(value); h.update(b); got += b.length;
            if (!out.write(b)) await new Promise((r) => out.once('drain', r));
            const now = Date.now(); if (now - last > 120) { last = now; try { sender.send('al:vai-progress', { stage: 'download', got: done + got, total }); } catch (e) { /* window gone */ } }
          }
          await new Promise((r, j) => out.end((e) => (e ? j(e) : r())));
          clearTimeout(stall);
          const sum = h.digest('hex');
          if (sum !== f.sha256) { fs.rmSync(tmp, { force: true }); throw new Error('the file ' + f.name + ' did not match its checksum, so it was not used'); }
          fs.renameSync(tmp, dst); done += f.size;
        } catch (e) { clearTimeout(stall); try { out.destroy(); fs.rmSync(tmp, { force: true }); } catch (x) { /* ignore */ } throw new Error(ac.signal.aborted ? 'the download stalled (no data for a minute)' : (e.message || String(e))); }
      }
      try { sender.send('al:vai-progress', { stage: 'download', got: total, total }); } catch (e) { /* ignore */ }
      return { ok: true };
    })().finally(() => { dl = null; });
    return dl;
  }

  /* ---- saved voices: <id>.json (name, source, pitch, embeddings) and <id>.f32 (the example, mono 22050 Hz, at most 60 s) ---- */
  const vjson = (id) => path.join(vdir(), String(id).replace(/[^\w-]/g, '') + '.json');
  const vaudio = (id) => path.join(vdir(), String(id).replace(/[^\w-]/g, '') + '.f32');
  function listVoices() {
    try { return fs.readdirSync(vdir()).filter((n) => n.endsWith('.json')).map((n) => { try { const j = JSON.parse(fs.readFileSync(path.join(vdir(), n), 'utf8')); return { id: j.id, name: j.name, from: j.from, made: j.made, hz: j.hz, dur: j.dur }; } catch (e) { return null; } }).filter(Boolean).sort((a, b) => (b.made || 0) - (a.made || 0)); } catch (e) { return []; }
  }

  const H = (ch, fn) => { try { ipcMain.removeHandler(ch); } catch (e) { /* ignore */ } ipcMain.handle(ch, fn); };
  H('al:vai-status', () => ({ ok: true, v: 1, model: { id: MODEL.id, name: MODEL.name, size: MODEL.files.reduce((a, f) => a + f.size, 0), have: have(), downloading: !!dl }, platform: process.platform, arch: process.arch, gpu: process.platform === 'darwin' ? 'Apple Neural Engine and GPU (Core ML)' : process.platform === 'win32' ? 'graphics card (DirectML)' : '' }));
  H('al:vai-download', (e) => download(e.sender).then(() => ({ ok: true }), (x) => ({ ok: false, err: x.message })));
  H('al:vai-embed', async (e, x, ep, sh) => { if (!have()) throw new Error('The AI voice model is not downloaded yet.'); const r = await job({ type: 'embed', x: Float32Array.from(x), ep: ep || 'cpu', sh: sh && sh.f0 ? { st: +sh.st || 0, f0: Float32Array.from(sh.f0) } : null }); return { se: r.r, fellBack: !!r.fellBack }; });
  H('al:vai-convert', async (e, m) => { if (!have()) throw new Error('The AI voice model is not downloaded yet.');
    const t0 = Date.now(); const r = await job({ type: 'convert', x: Float32Array.from(m.x), src: Array.from(m.src), tgt: Array.from(m.tgt), ep: m.ep || 'cpu' }, (p) => { try { e.sender.send('al:vai-progress', { stage: 'convert', p, tag: m.tag }); } catch (x) { /* ignore */ } });
    return { y: r.r, ms: Date.now() - t0, fellBack: !!r.fellBack }; });
  H('al:vai-voices', () => listVoices());
  H('al:vai-voice-save', (e, v) => {
    fs.mkdirSync(vdir(), { recursive: true });
    const id = 'v' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    const x = Float32Array.from(v.x).subarray(0, 22050 * 60);
    fs.writeFileSync(vaudio(id), Buffer.from(x.buffer, x.byteOffset, x.byteLength));
    const j = { id, name: String(v.name || 'Voice').slice(0, 60), from: String(v.from || '').slice(0, 120), made: Date.now(), hz: +v.hz || 0, dur: x.length / 22050, se: Array.from(v.se || []), ses: {}, model: MODEL.id };
    fs.writeFileSync(vjson(id), JSON.stringify(j)); return { id };
  });
  H('al:vai-voice-get', (e, id) => { const j = JSON.parse(fs.readFileSync(vjson(id), 'utf8')); const b = fs.readFileSync(vaudio(id)); j.x = new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.length)); return j; });
  H('al:vai-voice-set', (e, id, patch) => { const j = JSON.parse(fs.readFileSync(vjson(id), 'utf8')); if (patch.name != null) j.name = String(patch.name).slice(0, 60); if (patch.ses) Object.assign(j.ses = j.ses || {}, patch.ses); fs.writeFileSync(vjson(id), JSON.stringify(j)); return true; });
  H('al:vai-voice-del', (e, id) => { fs.rmSync(vjson(id), { force: true }); fs.rmSync(vaudio(id), { force: true }); return true; });
  H('al:vai-free', () => { if (proc) { try { proc.kill(); } catch (e) { /* ignore */ } proc = null; } return true; });
  app.on('will-quit', () => { if (proc) { try { proc.kill(); } catch (e) { /* ignore */ } } });
}

module.exports = { setup, MODEL };
