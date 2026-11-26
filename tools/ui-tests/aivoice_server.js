// Test stand-in for the desktop app's AI voice bridge (desktop/voice-ai.js): the same worker code (desktop/voice-ai-worker.js) behind HTTP,
// so a headless Chromium test can use AI voices. Arrays travel as base64 of float32.
//   NODE_PATH=<dir with onnxruntime-node> node tools/ui-tests/aivoice_server.js <model dir> <port>
const http = require('http'), path = require('path');
const W = require(path.join(__dirname, '..', '..', 'desktop', 'voice-ai-worker.js'));
const dir = process.argv[2], port = +process.argv[3] || 8765, voices = new Map(); let seq = 0;
const f32 = (s) => { const b = Buffer.from(s, 'base64'); return new Float32Array(b.buffer, b.byteOffset, b.length / 4).slice(); };
const b64 = (a) => Buffer.from(Float32Array.from(a).buffer).toString('base64');
const T = { embed: 0, convert: 0, convertAudio: 0 };
const api = {
  status: () => ({ ok: true, v: 1, model: { id: 'openvoice-v2-fp16', name: 'OpenVoice V2 (MyShell, MIT licence)', size: 65949021, have: true }, platform: 'test', gpu: 'graphics chip' }),
  download: () => ({ ok: true }),
  embed: async (m) => { const t = Date.now(); const se = await W.embed(dir, f32(m.x), 'cpu', m.sh ? { st: m.sh.st, f0: f32(m.sh.f0) } : null); T.embed += Date.now() - t; return { se: b64(se) }; },
  convert: async (m) => { const t = Date.now(), x = f32(m.x); const y = await W.convert(dir, { x, src: m.src, tgt: m.tgt, ep: 'cpu' }); const ms = Date.now() - t; T.convert += ms; T.convertAudio += x.length / 22050; return { y: b64(y), ms }; },
  voices: () => [...voices.values()].map((v) => ({ id: v.id, name: v.name, from: v.from, made: v.made, hz: v.hz, dur: v.dur })),
  saveVoice: (v) => { const id = 'v' + (++seq); voices.set(id, { id, name: v.name, from: v.from, made: Date.now(), hz: v.hz, dur: f32(v.x).length / 22050, x: v.x, se: v.se, ses: {} }); return { id }; },
  getVoice: (m) => { const v = voices.get(m.id); return Object.assign({}, v); },
  setVoice: (m) => { const v = voices.get(m.id); if (m.p.name) v.name = m.p.name; if (m.p.ses) Object.assign(v.ses, m.p.ses); return true; },
  delVoice: (m) => { voices.delete(m.id); return true; },
  stats: () => Object.assign({ rssMB: Math.round(process.memoryUsage().rss / 1e6) }, T)
};
http.createServer((req, res) => { let body = ''; req.on('data', (d) => (body += d)); req.on('end', async () => {
  const name = req.url.split('/').pop(); try { const r = await api[name](body ? JSON.parse(body) : {}); res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify(r)); }
  catch (e) { res.writeHead(500); res.end(JSON.stringify({ err: String(e && e.message || e) })); } }); }).listen(port, () => console.log('ready ' + port));
