// Runs the shared DSP kit (sndKitCore) taken from index.html or kit_src.js on test signals (task SND-0).
// node kit_run.js <source file> < jobs.json > results.json
// job: {id, name, p, sr, n, sig: 'imp'|'sine'|'noise'|'ramp'|'up2'|'down2'|'cpu', a, f}
'use strict';
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
const i0 = src.indexOf('function sndKitCore(){'), i1 = src.indexOf('\nfunction sndWL(){');
if (i0 < 0 || i1 < 0) { console.error('sndKitCore not found'); process.exit(2); }
const core = src.slice(i0, i1);
const K = new Function(core + '\nreturn sndKitCore();')();
const jobs = JSON.parse(fs.readFileSync(0, 'utf8'));
function sig(j, n) {
  const x = new Float64Array(n), a = j.a == null ? 1 : j.a, sr = j.sr || 48000;
  if (j.sig === 'imp') x[0] = a;
  else if (j.sig === 'sine') for (let k = 0; k < n; k++) x[k] = a * Math.sin(2 * Math.PI * j.f * k / sr);
  else if (j.sig === 'noise') { let s = 12345; for (let k = 0; k < n; k++) { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; x[k] = a * (s / 4294967296 * 2 - 1); } }
  else if (j.sig === 'ramp') for (let k = 0; k < n; k++) x[k] = -a + 2 * a * k / (n - 1);
  return x;
}
const enc = a => Buffer.from(new Float64Array(a).buffer).toString('base64');
const out = {};
for (const j of jobs) {
  const sr = j.sr || 48000, n = j.n || 4096;
  if (j.sig === 'up2') { // the 2x (or 4x) up-sampler alone on a sine: the images
    const o = j.name === 'os4' ? new K.Os4() : new K.Os2(), m = j.name === 'os4' ? 4 : 2, x = sig({ ...j, sig: 'sine' }, n), y = new Float64Array(n * m);
    for (let k = 0; k < n; k++) { const v = o.up(x[k]); for (let q = 0; q < m; q++) y[k * m + q] = v[q]; }
    out[j.id] = enc(y); continue;
  }
  if (j.sig === 'down2') { // a sine at the high rate into the down-sampler alone: the aliasing
    const o = j.name === 'os4' ? new K.Os4() : new K.Os2(), m = j.name === 'os4' ? 4 : 2, x = sig({ ...j, sig: 'sine', sr: sr * m }, n * m), y = new Float64Array(n);
    for (let k = 0; k < n; k++) y[k] = o.down(x.subarray(k * m, k * m + m));
    out[j.id] = enc(y); continue;
  }
  if (j.sig === 'smooth') { // Smooth to 1 with a time constant of j.ms; Ramp over j.ms
    const s = new K.Smooth(j.ms, sr, 0), r = new K.Ramp(Math.round(j.ms * sr / 1000), 0), y = new Float64Array(n * 2);
    s.to(1); r.to(1); for (let k = 0; k < n; k++) { y[k] = s.next(); y[n + k] = r.next(); }
    out[j.id] = enc(y); continue;
  }
  const b = K.make(j.name, j.p, sr);
  if (j.sig === 'cpu') { const x = sig({ ...j, sig: 'noise' }, n); let t0 = process.hrtime.bigint(), z = 0; for (let r = 0; r < 20; r++) for (let k = 0; k < n; k++) z += b.tick(x[k]); const ns = Number(process.hrtime.bigint() - t0) / (20 * n); out[j.id] = { ns, z }; continue; }
  const x = sig(j, n), y = new Float64Array(n);
  for (let k = 0; k < n; k++) y[k] = b.tick(x[k]);
  out[j.id] = enc(y);
}
out._src = core.length; out._math = [...new Set(core.match(/Math\.[a-zA-Z0-9]+/g))].sort();
process.stdout.write(JSON.stringify(out));
