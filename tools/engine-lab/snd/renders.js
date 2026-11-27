// A/B renders of the shared DSP kit (task SND-0) for listening: tools/engine-lab/snd/renders/*.wav (44.1 kHz, 16-bit, mono).
// node tools/engine-lab/snd/renders.js [index.html]
// No device uses the kit yet; these show what the blocks do and what the later steps build on (B1, B8, B28, N2, N4, N5).
'use strict';
const fs = require('fs'), path = require('path');
const src = fs.readFileSync(process.argv[2] || path.join(__dirname, '..', '..', '..', 'index.html'), 'utf8');
const core = src.slice(src.indexOf('function sndKitCore(){'), src.indexOf('\nfunction sndWL(){'));
const K = new Function(core + '\nreturn sndKitCore();')();
const SR = 44100, OUT = path.join(__dirname, 'renders'); fs.mkdirSync(OUT, { recursive: true });
function wav(name, x) {
  let pk = 0; for (const v of x) pk = Math.max(pk, Math.abs(v)); const g = pk > 0 ? 0.5 / pk : 1; // all files at -6 dBFS peak
  const b = Buffer.alloc(44 + x.length * 2);
  b.write('RIFF', 0); b.writeUInt32LE(36 + x.length * 2, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(x.length * 2, 40);
  for (let i = 0; i < x.length; i++) b.writeInt16LE(Math.max(-32767, Math.min(32767, Math.round(x[i] * g * 32767))), 44 + i * 2);
  fs.writeFileSync(path.join(OUT, name), b); console.log(name);
}
// a polyBLEP saw for the sources (test signal only, not part of the kit)
function saw(freqAt, n, sr) { const y = new Float64Array(n); let ph = 0;
  for (let i = 0; i < n; i++) { const dt = freqAt(i) / sr; let v = 2 * ph - 1;
    if (ph < dt) { const t = ph / dt; v -= t + t - t * t - 1 } else if (ph > 1 - dt) { const t = (ph - 1) / dt; v -= t * t + t + t + 1 }
    y[i] = v; ph += dt; if (ph >= 1) ph -= 1 } return y }
const n3 = SR * 3;
// 1. a 1 to 8 kHz sine sweep into a hard tanh (drive 4): plain at 1x against ADAA at 2x (the Saturate and B28 groundwork)
{ const x = new Float64Array(n3); let ph = 0; for (let i = 0; i < n3; i++) { const f = 1000 * Math.exp(Math.log(8) * i / n3); ph += f / SR; x[i] = 0.5 * Math.sin(2 * Math.PI * ph) }
  for (const [nm, os, ad] of [['sweep_tanh_plain_1x.wav', 1, 0], ['sweep_tanh_adaa_2x.wav', 2, 1]]) { const s = new K.Shaper(0, os, ad); wav(nm, x.map(v => s.tick(4 * v))) } }
// 2. a rolling psy bass (F1, K-B-B-B at 145 BPM, the three 16ths after the kick) through the ladder: linear against driven at 2x
const bpm = 145, six = SR * 60 / bpm / 4, nb = Math.round(six * 16 * 2);
const gate = i => { const s = Math.floor(i / six) % 4; return s === 0 ? 0 : 1 }, inStep = i => (i % six) / six;
{ const src = saw(() => 43.65, nb, SR);
  for (const [nm, nl, drive] of [['bass_ladder_linear.wav', 0, 1], ['bass_ladder_driven_2x.wav', 1, 3]]) {
    const L = new K.Ladder(), os = new K.Os2(), y = new Float64Array(nb);
    L.setDrive(drive, nl);
    for (let i = 0; i < nb; i++) { const t = inStep(i), env = Math.exp(-t * 9), fc = 120 + 2600 * env; L.set(fc, 0.55, SR * 2);
      const amp = gate(i) * (t < 0.02 ? t / 0.02 : 1) * (t > 0.85 ? (1 - t) / 0.15 : 1), o = os.up(src[i] * amp);
      o[0] = L.tick(o[0]); o[1] = L.tick(o[1]); y[i] = os.down(o) }
    wav(nm, y) } }
// 3. an acid line (A1 and A2, slides off) through the diode ladder: linear against driven, resonance 0.9, cutoff sweeping up
{ const steps = [45, 45, 57, 45, 48, 45, 57, 52, 45, 45, 57, 45, 50, 45, 55, 57], st = SR * 60 / 140 / 4, na = Math.round(st * 32);
  const f = i => 440 * Math.exp((steps[Math.floor(i / st) % 16] - 69) * Math.LN2 / 12), src = saw(f, na, SR);
  for (const [nm, nl] of [['acid_diode_linear.wav', 0], ['acid_diode_driven_2x.wav', 1]]) {
    const D = new K.Diode(), os = new K.Os2(), y = new Float64Array(na); D.setDrive(2.5, nl);
    for (let i = 0; i < na; i++) { const t = (i % st) / st, sweep = i / na, fc = 200 + (300 + 2500 * sweep) * Math.exp(-t * 5);
      D.set(fc, 0.9, SR * 2); const o = os.up(src[i] * (t < 0.7 ? 1 : (1 - t) / 0.3)); o[0] = D.tick(o[0]); o[1] = D.tick(o[1]); y[i] = os.down(o) }
    wav(nm, y) } }
// 4. a saw at 110 Hz through the formant filter, morphing a e i o u and back
{ const src = saw(() => 110, n3, SR), F = new K.Formant(), y = new Float64Array(n3);
  for (let i = 0; i < n3; i++) { const t = i / n3; F.set(4 * (t < 0.5 ? 2 * t : 2 - 2 * t), SR, 1); y[i] = F.tick(src[i]) } wav('formant_morph.wav', y) }
// 5. noise bursts through a damped feedback comb tuned to A2, C3, E3, A3 (Comb and Resonator groundwork)
{ const y = new Float64Array(n3), C = new K.Comb(2000), notes = [45, 48, 52, 57]; let s = 1;
  for (let i = 0; i < n3; i++) { const k = Math.floor(i / (n3 / 4)), t = i - k * n3 / 4;
    if (t === 0) { C.set(SR / (440 * Math.exp((notes[k] - 69) * Math.LN2 / 12)), 0.985, 0); C.setDamp(4000, SR) }
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0; y[i] = C.tick(t < 200 ? (s / 4294967296 * 2 - 1) : 0) }
  wav('comb_plucks.wav', y) }
