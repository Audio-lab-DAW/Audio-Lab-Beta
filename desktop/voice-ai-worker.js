// AudioLab Pro: AI voices (task Z2). Runs in its own Electron utility process, so a long conversion never blocks the app.
// Model: OpenVoice V2 tone-colour converter (MyShell, MIT), as ONNX graphs (fp16 build by moonbox-dev, MIT, checked against the
// original PyTorch model: 47 dB SNR). Audio in and out is mono at 22050 Hz; the page resamples and does the pitch work.
// Messages: {id, type:'embed'|'convert'|'free', ...} -> {id, ok, r} or {id, err}; progress {id, p}.
'use strict';
const path = require('path');
let ort = null;
function loadOrt() { if (!ort) ort = require('onnxruntime-node'); return ort; }

const SR = 22050, NFFT = 1024, HOP = 256, NB = NFFT / 2 + 1, PAD = (NFFT - HOP) / 2;

/* ---- spectrogram, the same as openvoice.mel_processing.spectrogram_torch(center=False): reflect pad 384, periodic Hann 1024, hop 256,
   sqrt(re^2+im^2+1e-6). Returns {d: Float32Array(NB*T) laid out [NB][T], T} */
const WIN = new Float64Array(NFFT); for (let i = 0; i < NFFT; i++) WIN[i] = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / NFFT);
const REV = new Uint16Array(NFFT); { const b = Math.log2(NFFT); for (let i = 0; i < NFFT; i++) { let r = 0; for (let k = 0; k < b; k++) r |= ((i >> k) & 1) << (b - 1 - k); REV[i] = r; } }
const COS = new Float64Array(NFFT / 2), SIN = new Float64Array(NFFT / 2); for (let i = 0; i < NFFT / 2; i++) { COS[i] = Math.cos(2 * Math.PI * i / NFFT); SIN[i] = -Math.sin(2 * Math.PI * i / NFFT); }
function fft(re, im) {
  for (let i = 0; i < NFFT; i++) { const j = REV[i]; if (j > i) { let t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; } }
  for (let s = 2; s <= NFFT; s <<= 1) { const h = s >> 1, st = NFFT / s;
    for (let a = 0; a < NFFT; a += s) for (let k = 0; k < h; k++) { const c = COS[k * st], sn = SIN[k * st], i = a + k, j = i + h;
      const tr = re[j] * c - im[j] * sn, ti = re[j] * sn + im[j] * c; re[j] = re[i] - tr; im[j] = im[i] - ti; re[i] += tr; im[i] += ti; } }
}
function spectrogram(x) {
  const N = x.length, L = N + 2 * PAD, T = Math.max(1, 1 + Math.floor((L - NFFT) / HOP));
  const at = (i) => { let k = i - PAD; if (N < 2) return 0; while (k < 0 || k >= N) { if (k < 0) k = -k; if (k >= N) k = 2 * (N - 1) - k; } return x[k]; };
  const d = new Float32Array(NB * T), re = new Float64Array(NFFT), im = new Float64Array(NFFT);
  for (let t = 0; t < T; t++) { const o = t * HOP; for (let i = 0; i < NFFT; i++) { re[i] = at(o + i) * WIN[i]; im[i] = 0; } fft(re, im);
    for (let k = 0; k < NB; k++) d[k * T + t] = Math.sqrt(re[k] * re[k] + im[k] * im[k] + 1e-6); }
  return { d, T };
}
/* the posterior encoder's sampling noise: a fixed normal sequence per frame index, so chunks join without a seam */
function noise(t0, T) {
  const n = new Float32Array(192 * T);
  for (let t = 0; t < T; t++) { let s = ((t0 + t) * 2654435761 + 0x9e3779b9) >>> 0;
    const rnd = () => { s = (s + 0x6D2B79F5) >>> 0; let z = s; z = Math.imul(z ^ (z >>> 15), z | 1); z ^= z + Math.imul(z ^ (z >>> 7), z | 61); return (((z ^ (z >>> 14)) >>> 0) + 0.5) / 4294967296; };
    for (let c = 0; c < 192; c += 2) { const u = rnd(), v = rnd(), r = Math.sqrt(-2 * Math.log(u)); n[c * T + t] = r * Math.cos(2 * Math.PI * v); if (c + 1 < 192) n[(c + 1) * T + t] = r * Math.sin(2 * Math.PI * v); } }
  return n;
}

/* ---- a voice moved to another pitch, for its embedding only: per voiced frame, the harmonic peaks and the valleys between them give
   the spectral envelope (dB, linear between harmonics); new harmonics at the new pitch are drawn with the Hann window's main lobe under
   that envelope, over the valley floor. Unvoiced frames stay. f0: Hz per spectrogram frame (0 = unvoiced). Measured against moving the
   audio with TD-PSOLA: the converted voice lands 2 to 5.5 semitones nearer the wanted pitch (docs/voice-research.md, section 9). */
const BW = SR / NFFT;
const snc = (v) => (v === 0 ? 1 : Math.sin(Math.PI * v) / (Math.PI * v));
const kern = (d) => Math.abs(0.5 * snc(d) + 0.25 * snc(d - 1) + 0.25 * snc(d + 1)) / 0.5;
function interp(q, xs, ys) { const n = xs.length; if (q <= xs[0]) return ys[0]; if (q >= xs[n - 1]) return ys[n - 1]; let lo = 0, hi = n - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (xs[m] <= q) lo = m; else hi = m; } return ys[lo] + (ys[hi] - ys[lo]) * (q - xs[lo]) / (xs[hi] - xs[lo]); }
function shiftSpec(d, T, st, f0) {
  const r = Math.pow(2, st / 12), out = d.slice(), col = new Float64Array(NB), comb = new Float64Array(NB);
  for (let t = 0; t < T; t++) {
    const f = f0[Math.min(t, f0.length - 1)]; if (!(f > 0)) continue;
    const H = Math.floor((SR / 2 - BW) / f); if (H < 2) continue;
    for (let k = 0; k < NB; k++) col[k] = d[k * T + t];
    const hb = [], pk = [], vb = [], vl = [];
    for (let h = 1; h <= H; h++) { const b = h * f / BW, c = Math.round(b), lo = Math.max(0, c - 1), hi = Math.min(NB - 1, c + 1); let m = 0; for (let k = lo; k <= hi; k++) if (col[k] > m) m = col[k]; hb.push(b); pk.push(20 * Math.log10(m + 1e-9)); }
    for (let j = 0; j + 1 < hb.length; j++) { const lo = Math.round(hb[j]) + 1, hi = Math.round(hb[j + 1]) - 1; let m; if (hi >= lo) { m = Infinity; for (let k = lo; k <= hi; k++) if (col[k] < m) m = col[k]; m = 20 * Math.log10(m + 1e-9); } else m = Math.min(pk[j], pk[j + 1]); vb.push((hb[j] + hb[j + 1]) / 2); vl.push(m); }
    comb.fill(0); const nf = f * r;
    for (let b = nf / BW; b * BW < SR / 2 - BW; b += nf / BW) { const e = Math.pow(10, interp(b, hb, pk) / 20), lo = Math.max(0, Math.floor(b) - 3), hi = Math.min(NB - 1, Math.floor(b) + 4); for (let k = lo; k <= hi; k++) { const v = kern(k - b) * e; if (v > comb[k]) comb[k] = v; } }
    for (let k = 0; k < NB; k++) { const ep = interp(k, hb, pk), ev = vl.length ? interp(k, vb, vl) : ep - 30; out[k * T + t] = Math.max(comb[k], Math.pow(10, Math.min(ev, ep) / 20)); }
  }
  return out;
}

/* ---- sessions ---- */
const SES = {};
async function session(dir, name, ep) {
  const key = dir + '|' + name + '|' + ep;
  if (SES[key]) return SES[key];
  const o = loadOrt(), threads = Math.max(1, Math.min(8, require('os').cpus().length - 1));
  const prov = ep === 'gpu' ? (process.platform === 'darwin' ? ['coreml', 'cpu'] : process.platform === 'win32' ? ['dml', 'cpu'] : ['cpu']) : ['cpu'];
  SES[key] = await o.InferenceSession.create(path.join(dir, name + '.onnx'), { executionProviders: prov, intraOpNumThreads: threads, graphOptimizationLevel: 'all', logSeverityLevel: 3 });
  return SES[key];
}
function free() { for (const k of Object.keys(SES)) { try { SES[k].release && SES[k].release(); } catch (e) { /* ignore */ } delete SES[k]; } }

/* ---- tone-colour embedding of a recording: frames quieter than 45 dB under the loudest are left out (pauses say nothing about the voice) */
async function embed(dir, x, ep, sh) {
  let { d, T } = spectrogram(x); const E = new Float64Array(T); let mx = 0;
  if (sh && sh.st && sh.f0) d = shiftSpec(d, T, sh.st, sh.f0);
  for (let t = 0; t < T; t++) { let s = 0; for (let k = 0; k < NB; k++) { const v = d[k * T + t]; s += v * v; } E[t] = s; if (s > mx) mx = s; }
  /* a moved voice: only its voiced frames (the ones that were moved); measured: lands 1.5 to 3 semitones nearer the wanted pitch */
  const vo = sh && sh.st && sh.f0 ? (t) => sh.f0[Math.min(t, sh.f0.length - 1)] > 0 : () => true;
  let keep = []; for (let t = 0; t < T; t++) if (E[t] > mx * 3.2e-5 && vo(t)) keep.push(t);
  if (keep.length < 40) keep = Array.from({ length: T }, (_, i) => i);
  const n = keep.length, a = new Float32Array(n * NB);
  for (let j = 0; j < n; j++) { const t = keep[j]; for (let k = 0; k < NB; k++) a[j * NB + k] = d[k * T + t]; }
  const o = loadOrt(), s = await session(dir, 'ref_encoder', ep);
  const r = await s.run({ spec: new o.Tensor('float32', a, [1, n, NB]) });
  return Float32Array.from(r[s.outputNames[0]].data);
}

/* ---- conversion in chunks of 4 s with 0.75 s of context on each side (measured: from 0.5 s of context on, chunked = whole file) */
async function convert(dir, m, prog) {
  const o = loadOrt(), s = await session(dir, 'converter', m.ep), x = m.x, N = x.length;
  const { d, T } = spectrogram(x), L = Math.round(4 * SR / HOP), C = Math.round(0.75 * SR / HOP), y = new Float32Array(N);
  const src = new o.Tensor('float32', Float32Array.from(m.src), [1, 256, 1]), tgt = new o.Tensor('float32', Float32Array.from(m.tgt), [1, 256, 1]);
  for (let a = 0; a < T; a += L) {
    const s0 = Math.max(0, a - C), s1 = Math.min(T, a + L + C), n = s1 - s0, sp = new Float32Array(NB * n);
    for (let k = 0; k < NB; k++) sp.set(d.subarray(k * T + s0, k * T + s1), k * n);
    const r = await s.run({ spec: new o.Tensor('float32', sp, [1, NB, n]), noise: new o.Tensor('float32', noise(s0, n), [1, 192, n]), src_se: src, tgt_se: tgt });
    const w = r[s.outputNames[0]].data, b0 = (a - s0) * HOP, b1 = Math.min(w.length, (Math.min(T, a + L) - s0) * HOP);
    for (let i = b0; i < b1; i++) { const j = s0 * HOP + i; if (j < N) { const v = w[i]; y[j] = Number.isFinite(v) ? v : 0; } }
    if (prog) prog(Math.min(1, (a + L) / T));
  }
  return y;
}

async function handle(m, reply) {
  try {
    if (m.type === 'embed') return reply({ id: m.id, ok: 1, r: await embed(m.dir, m.x, m.ep, m.sh) });
    if (m.type === 'convert') return reply({ id: m.id, ok: 1, r: await convert(m.dir, m, (p) => reply({ id: m.id, p })) });
    if (m.type === 'free') { free(); return reply({ id: m.id, ok: 1, r: true }); }
    if (m.type === 'ping') { loadOrt(); return reply({ id: m.id, ok: 1, r: { ort: require('onnxruntime-node/package.json').version } }); }
    reply({ id: m.id, err: 'unknown job ' + m.type });
  } catch (e) {
    if (m.ep === 'gpu' && (m.type === 'embed' || m.type === 'convert')) { free(); m.ep = 'cpu'; m.fellBack = 1; return handle(m, (r) => { if (r.ok) r.fellBack = 1; reply(r); }); }
    reply({ id: m.id, err: String((e && e.message) || e) });
  }
}

if (process.parentPort) process.parentPort.on('message', (e) => handle(e.data, (r) => process.parentPort.postMessage(r)));
module.exports = { spectrogram, shiftSpec, noise, embed, convert, handle, free, SR };
