/* Task AE1, sound quality: today's algorithms (ported from index.html v0.263, line references in comments) and the
   candidate improvements, as plain functions on Float64Arrays. Loaded by lab.js (node, measurements and CPU cost) and
   inlined into the pick page (live A/B tests). No Web Audio here: everything is computed into buffers. */
(function (root) {
'use strict';
const TAU = Math.PI * 2;
const AE = {};

/* ---------- helpers */
function sfc32(a, b, c, d) { return () => { a >>>= 0; b >>>= 0; c >>>= 0; d >>>= 0; let t = (a + b) | 0; a = b ^ (b >>> 9); b = (c + (c << 3)) | 0; c = (c << 21) | (c >>> 11); d = (d + 1) | 0; t = (t + d) | 0; c = (c + t) | 0; return (t >>> 0) / 4294967296; }; }
AE.rng = (s) => sfc32(0x9e3779b9 ^ s, 0x243f6a88, 0xb7e15162, 0x7f4a7c15 + s);
function besselI0(x) { let s = 1, t = 1; for (let k = 1; k < 50; k++) { t *= (x / (2 * k)) * (x / (2 * k)); s += t; if (t < 1e-20 * s) break; } return s; }
function kaiserW(n, N, beta) { const r = 2 * n / (N - 1) - 1; return besselI0(beta * Math.sqrt(Math.max(0, 1 - r * r))) / besselI0(beta); }
AE.kaiserW = kaiserW;
const sinc = (x) => x === 0 ? 1 : Math.sin(Math.PI * x) / (Math.PI * x);

/* half-band low-pass (Kaiser windowed sinc, cut at a quarter of the high rate); N odd, (N-1)/2 odd taps are zero except the centre */
AE.halfband = function (N, beta) { const h = new Float64Array(N), c = (N - 1) / 2; let s = 0; for (let i = 0; i < N; i++) { h[i] = .5 * sinc((i - c) / 2) * kaiserW(i, N, beta); s += h[i]; } for (let i = 0; i < N; i++) h[i] /= s; return h; };
/* 2x down: filter at the high rate, keep every second sample (only the non-zero taps are computed) */
AE.down2 = function (x, h) { const N = h.length, c = (N - 1) / 2, n = x.length >> 1, y = new Float64Array(n); const nz = []; for (let k = 0; k < N; k++) if (Math.abs(h[k]) > 1e-12) nz.push(k);
  for (let i = 0; i < n; i++) { const j = 2 * i; let s = 0; for (const k of nz) { const q = j - k + c; if (q >= 0 && q < x.length) s += h[k] * x[q]; } y[i] = s; } return y; };
/* 2x up (zero stuffing, gain 2) */
AE.up2 = function (x, h) { const N = h.length, c = (N - 1) / 2, y = new Float64Array(x.length * 2);
  for (let j = 0; j < y.length; j++) { let s = 0; for (let k = (j - c) & 1 ? 1 : 0; k < N; k += 2) { const q = j - k + c; if (q >= 0 && q < y.length && !(q & 1)) s += h[k] * x[q >> 1]; } y[j] = 2 * s; } return y; };
AE.HB47 = AE.halfband(47, 9);    // ~ -90 dB stop band, pass band flat to ~0.42 of the low rate (20 kHz at 48 kHz)
AE.HB79 = AE.halfband(79, 11);   // ~ -110 dB, the Psy Bass instrument's quality

/* ---------- oscillators */
/* TODAY: al-poly saw, 2-point PolyBLEP at the engine rate (index.html PWL, run(): T===1) */
AE.sawPolyBlep = function (f, sr, n, ph0) { const y = new Float64Array(n); let t = ph0 || 0;
  for (let i = 0; i < n; i++) { const d = (typeof f === 'function' ? f(i) : f) / sr, ad = d < 0 ? -d : d; let s = 2 * t - 1;
    if (t < ad) { const x = t / ad; s -= 2 * x - x * x - 1; } else if (t > 1 - ad) { const x = (t - 1) / ad; s -= x * x + 2 * x + 1; }
    y[i] = s; t += d; if (t >= 1) t -= 1; } return y; };

/* CANDIDATE: table BLEP, a band-limited step (Kaiser windowed sinc, Z zero crossings each side) added at every wrap.
   Linear phase: the output is Z samples late (0.33 ms at 48 kHz for Z=16). Cost is per edge, not per sample. */
function makeBlep(Z, OS, beta, fc) { const L = 2 * Z * OS + 1, blit = new Float64Array(L); let s = 0;
  for (let i = 0; i < L; i++) { const x = (i - Z * OS) / OS; blit[i] = fc * sinc(fc * x) * kaiserW(i, L, beta); s += blit[i]; }
  const res = new Float64Array(L); let acc = 0; for (let i = 0; i < L; i++) { acc += blit[i] / s; res[i] = acc - .5 * blit[i] / s; } return { Z, OS, res }; }   /* res = the band-limited step itself (integral to the sample centre); the ideal step is subtracted where it is used */
AE.BLEP = makeBlep(16, 256, 10, .94);
AE.sawBlep = function (f, sr, n, ph0, B) { B = B || AE.BLEP; const Z = B.Z, OS = B.OS, res = B.res, y = new Float64Array(n + 2 * Z); let t = ph0 || 0;
  for (let i = 0; i < n; i++) { const d = (typeof f === 'function' ? f(i) : f) / sr; y[i + Z] += 2 * t - 1; const tn = t + d;
    if (tn >= 1) { /* the wrap happened at fraction a of the way to the next sample */ const a = (1 - t) / d, h = -2; // step of -2 at time i + a
      for (let k = -Z + 1; k <= Z; k++) { const x = k - a, p = (x + Z) * OS, pi = p | 0; if (pi < 0 || pi >= res.length - 1) continue; const r = res[pi] + (res[pi + 1] - res[pi]) * (p - pi) - (x >= 0 ? 1 : 0); const j = i + k + Z; if (j >= 0 && j < y.length) y[j] += h * r; } }
    t = tn >= 1 ? tn - 1 : tn; }
  return y.subarray(Z, Z + n); };

/* ---------- filters */
/* TODAY: al-poly low-pass, RBJ cookbook biquad in transposed direct form II, Q in dB (G=10^(q/20)), coefficients every 16 samples */
AE.rbjLP16 = function (x, sr, cut, qdb, blk) { blk = blk || 16; const y = new Float64Array(x.length), G = Math.pow(10, qdb / 20); let z1 = 0, z2 = 0, b0 = 0, b1 = 0, b2 = 0, a1 = 0, a2 = 0;
  for (let i = 0; i < x.length; i++) { if (i % blk === 0) { let cu = typeof cut === 'function' ? cut(i) : cut; cu = Math.min(Math.max(cu, 20), sr * .49); const w = TAU * cu / sr, cs = Math.cos(w), sn = Math.sin(w), al = sn / (2 * G), ia = 1 / (1 + al); b1 = (1 - cs) * ia; b0 = b2 = b1 * .5; a1 = -2 * cs * ia; a2 = (1 - al) * ia; }
    const v = x[i], o = b0 * v + z1; z1 = b1 * v - a1 * o + z2; z2 = b2 * v - a2 * o; y[i] = o; } return y; };
/* CANDIDATE: zero-delay-feedback state variable filter (trapezoidal, A. Simper), cut-off prewarped with tan(), updated every sample */
AE.svfLP = function (x, sr, cut, qdb) { const y = new Float64Array(x.length), Q = Math.pow(10, qdb / 20), k = 1 / Q; let ic1 = 0, ic2 = 0;
  for (let i = 0; i < x.length; i++) { let cu = typeof cut === 'function' ? cut(i) : cut; cu = Math.min(Math.max(cu, 20), sr * .49); const g = Math.tan(Math.PI * cu / sr), a1 = 1 / (1 + g * (g + k)), a2 = g * a1, a3 = g * a2;
    const v0 = x[i], v3 = v0 - ic2, v1 = a1 * ic1 + a2 * v3, v2 = ic2 + a2 * ic1 + a3 * v3; ic1 = 2 * v1 - ic1; ic2 = 2 * v2 - ic2; y[i] = v2; } return y; };

/* ---------- drive */
/* TODAY: Acid drive, hard clip to +-1 then tanh, at the engine rate (PWL: yl=Math.tanh(clamp(yl)*dg)*dn) */
AE.acidDrive = function (x, dg) { const dn = 1 / Math.tanh(dg), y = new Float64Array(x.length); for (let i = 0; i < x.length; i++) { const v = x[i] > 1 ? 1 : x[i] < -1 ? -1 : x[i]; y[i] = Math.tanh(v * dg) * dn; } return y; };
/* CANDIDATE: the same curve with first-order antiderivative anti-aliasing (Parker, Zavalishin, Le Bivic 2016); half a sample late */
function lncosh(u) { const a = Math.abs(u); return a + Math.log1p(Math.exp(-2 * a)) - Math.LN2; }
AE.acidDriveADAA = function (x, dg) { const dn = 1 / Math.tanh(dg), td = Math.tanh(dg), F1 = lncosh(dg) / dg;
  const F = (v) => { if (v > 1) return F1 + td * (v - 1); if (v < -1) return F1 - td * (v + 1); return lncosh(v * dg) / dg; };
  const f = (v) => Math.tanh((v > 1 ? 1 : v < -1 ? -1 : v) * dg);
  const y = new Float64Array(x.length); let xp = 0, Fp = F(0);
  for (let i = 0; i < x.length; i++) { const v = x[i], Fv = F(v), d = v - xp; y[i] = (Math.abs(d) > 1e-6 ? (Fv - Fp) / d : f(.5 * (v + xp))) * dn; xp = v; Fp = Fv; } return y; };
/* TODAY: the Drive effect's curve (index.html mkFxNode 'drive'): (1+k)x/(1+k|x|), k = drive*1.5, ends at +-1 (input clamped) */
AE.driveCurve = (drive) => { const k = drive * 1.5; return (v) => { v = v > 1 ? 1 : v < -1 ? -1 : v; return (1 + k) * v / (1 + k * Math.abs(v)); }; };
AE.driveCurveF = (drive) => { const k = drive * 1.5; /* antiderivative of (1+k)v/(1+k|v|) */
  const G = (a) => k > 0 ? (1 + k) * (a / k - Math.log1p(k * a) / (k * k)) : a * a / 2, G1 = G(1), c1 = (1 + k) / (1 + k);
  return (v) => { const a = Math.abs(v); if (a <= 1) return G(a); return G1 + (a - 1) * c1; }; };
AE.shapeADAA = function (x, f, F) { const y = new Float64Array(x.length); let xp = 0, Fp = F(0);
  for (let i = 0; i < x.length; i++) { const v = x[i], Fv = F(v), d = v - xp; y[i] = Math.abs(d) > 1e-7 ? (Fv - Fp) / d : f(.5 * (v + xp)); xp = v; Fp = Fv; } return y; };
AE.shape = function (x, f) { const y = new Float64Array(x.length); for (let i = 0; i < x.length; i++) y[i] = f(x[i]); return y; };
/* oversample any block function g by 2^m with half-bands */
AE.os = function (x, m, g, hb) { hb = hb || AE.HB47; let u = x; for (let k = 0; k < m; k++) u = AE.up2(u, hb); u = g(u, 1 << m); for (let k = 0; k < m; k++) u = AE.down2(u, hb); return u; };

/* ---------- an Acid / psy voice: saw, two filter stages, drive (al-poly 'acid'), at 1x (today) or 2x with ADAA (candidate) */
AE.acidVoice = function (o) { /* o: {sr, notes:[[startSample, lenSamples, midi, vel]], n, cut, env, dec, res, dist, hq | M, osc, flt, drv} */
  const hq = !!o.hq, M = o.M || (hq ? 2 : 1), oscT = o.osc || (hq ? 'blep' : 'polyblep'), fltT = o.flt || (hq ? 'svf' : 'rbj16'), drvT = o.drv || (hq ? 'adaa' : 'plain');
  const sr = o.sr, R = sr * M, n = o.n * M, x = new Float64Array(n), cutA = new Float64Array(n), amp = new Float64Array(n);
  const k = Math.round(o.dist / 100 * 10) / 10, dg = 1 + k * 12;
  for (const [s0, len, p, vel] of o.notes) { const f = 440 * Math.pow(2, (p - 69) / 12), S = s0 * M, L = len * M, rel = Math.round(.018 * R);
    const fe = Math.min(16000, o.cut * Math.pow(2, o.env / 100 * 5)), ftc = o.dec / 3;
    const osc = oscT === 'blep' ? AE.sawBlep(f, R, L + rel, 0) : AE.sawPolyBlep(f, R, L + rel, 0);
    for (let i = 0; i < L + rel && S + i < n; i++) { const t = i / R; let a = Math.min(1, t / .003); if (i >= L) a *= Math.max(0, 1 - (i - L) / rel);
      x[S + i] = osc[i] * .847; amp[S + i] = a * vel; cutA[S + i] = o.cut + (fe - o.cut) * Math.exp(-t / ftc); } }
  for (let i = 1; i < n; i++) if (cutA[i] === 0) cutA[i] = cutA[i - 1] || o.cut;
  if (cutA[0] === 0) cutA[0] = o.cut;
  const cf = (i) => cutA[i], F = fltT === 'svf' ? AE.svfLP : AE.rbjLP16;
  let y = F(x, R, cf, o.res);
  y = F(y, R, cf, .7);   // the second stage: al-poly q2 = 0.7 (dB)
  if (o.dist > 0) y = drvT === 'adaa' ? AE.acidDriveADAA(y, dg) : AE.acidDrive(y, dg);
  for (let i = 0; i < n; i++) y[i] *= amp[i];
  for (let m = M; m > 1; m >>= 1) y = AE.down2(y, AE.HB47);
  return y; };

/* ---------- the kick (kickRender, index.html ~L3985): sine sweep + tick, then tanh at the engine rate (today) or 4x (candidate) */
AE.kick = function (I, sr, os) { os = os || 1; const hz = (p) => 440 * Math.pow(2, (p - 69) / 12), tr = 0;
  const n = Math.ceil(I.len * sr) + 8, d = new Float64Array(n), fE = hz(I.tune + tr), fS = Math.max(fE * 1.02, I.start), lE = Math.log(fE), lS = Math.log(fS);
  const cp = 1 + I.bend / 100 * 5, att = .0005, hold = I.len * (.04 + .22 * I.tail / 100), tp = 2.8 - 2.4 * I.tail / 100, fade = Math.min(.006, I.len * .05); let ph = 0;
  for (let i = 0; i < n; i++) { const t = i / sr, x = Math.min(1, t / I.sweep), f = Math.exp(lE + (lS - lE) * Math.pow(1 - x, cp)); ph += TAU * f / sr; if (ph > TAU) ph -= TAU;
    let a = t < att ? t / att : 1; const y = Math.min(1, Math.max(0, (t - hold) / Math.max(1e-4, I.len - hold))); a *= Math.pow(1 - y, tp); if (t > I.len - fade) a *= Math.max(0, (I.len - t) / fade); d[i] = Math.sin(ph) * a; }
  const cl = I.click / 100 * .9; if (cl > 0) { let xp = 0, yp = 0; const m = Math.min(n, Math.ceil(sr * .06)); let seed = 12345; const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x3fffffff - 1; };
    for (let i = 0; i < m; i++) { const t = i / sr, nz = rnd(); yp = .92 * (yp + nz - xp); xp = nz; d[i] += (Math.sin(TAU * 3400 * t) * Math.exp(-t / .0012) * .9 + yp * Math.exp(-t / .0018) * .6) * cl; } }
  const g = 1 + I.drive / 100 * 14, tg = Math.tanh(g), th = (u) => { for (let i = 0; i < u.length; i++) u[i] = Math.tanh(u[i] * g) / tg; return u; };
  /* today: tanh at the engine rate; candidate: the same signal, tanh at os x (half-band up and down; the kick is rendered once into a buffer, so this costs nothing while playing) */
  let y = os === 1 ? th(d) : AE.os(d, Math.round(Math.log2(os)), th, AE.HB79);
  let pk = 0; for (const v of y) pk = Math.max(pk, Math.abs(v)); const nm = .95 / pk; y = Float64Array.from(y); for (let i = 0; i < y.length; i++) y[i] *= nm; return y; };

/* ---------- resampling */
/* TODAY: AudioBufferSourceNode in Chromium: linear interpolation at any rate other than 1 (buffer rate / context rate, playbackRate) */
AE.resampleLinear = function (x, ratio, n) { /* ratio = input samples per output sample */ const y = new Float64Array(n); for (let i = 0; i < n; i++) { const p = i * ratio, k = Math.floor(p), f = p - k; const a = x[k] || 0, b = x[k + 1] || 0; y[i] = a + (b - a) * f; } return y; };
/* CANDIDATE: windowed-sinc resampler (Kaiser, Z zero crossings, cut-off follows the lower rate), run once when a buffer is loaded */
AE.resampleSinc = function (x, ratio, n, Z, beta) { Z = Z || 32; beta = beta || 10; const fc = Math.min(1, 1 / ratio) * .96, y = new Float64Array(n), OS = 512, L = Z * OS + 1, tab = new Float64Array(L + 1);
  for (let i = 0; i <= L; i++) { const u = i / OS; tab[i] = u >= Z ? 0 : sinc(fc * u) * besselI0(beta * Math.sqrt(1 - (u / Z) * (u / Z))) / besselI0(beta); }
  const W = Math.ceil(Z / fc);
  for (let i = 0; i < n; i++) { const p = i * ratio, k = Math.floor(p); let s = 0;
    for (let j = k - W + 1; j <= k + W; j++) { if (j < 0 || j >= x.length) continue; const u = Math.abs(p - j) * fc * OS, ui = u | 0; if (ui >= L) continue; s += x[j] * (tab[ui] + (tab[ui + 1] - tab[ui]) * (u - ui)); }
    y[i] = s * fc; } return y; };

/* ---------- limiter: al-limit (WLSRC Lim) ported line for line; candidate = BS.1770 4x true-peak detection + 4x oversampled final clip */
const tpk = (s0, s1, s2, s3) => Math.max(Math.abs((-s0 + 9 * s1 + 9 * s2 - s3) / 16), Math.abs((-9 * s0 + 111 * s1 + 29 * s2 - 3 * s3) / 128), Math.abs((-3 * s0 + 29 * s1 + 111 * s2 - 9 * s3) / 128));
AE.TPH = [0.001708984375, 0.010986328125, -0.0196533203125, 0.033203125, -0.0594482421875, 0.1373291015625, 0.97216796875, -0.102294921875, 0.047607421875, -0.026611328125, 0.014892578125, -0.00830078125, -0.0291748046875, 0.029296875, -0.0517578125, 0.089111328125, -0.16650390625, 0.465087890625, 0.77978515625, -0.2003173828125, 0.1015625, -0.0582275390625, 0.0330810546875, -0.0189208984375, -0.0189208984375, 0.0330810546875, -0.0582275390625, 0.1015625, -0.2003173828125, 0.77978515625, 0.465087890625, -0.16650390625, 0.089111328125, -0.0517578125, 0.029296875, -0.0291748046875, -0.00830078125, 0.014892578125, -0.026611328125, 0.047607421875, -0.102294921875, 0.97216796875, 0.1373291015625, -0.0594482421875, 0.033203125, -0.0196533203125, 0.010986328125, 0.001708984375];
AE.limiter = function (L, R, sr, p) { /* p: {ceil, look(ms), rel(ms), style, tp, gain, mode:'today'|'tp4'|'tp4clip'} */
  const n = L.length, oL = new Float64Array(n), oR = new Float64Array(n), mode = p.mode || 'today', dB = (v) => Math.pow(10, v / 20);
  const gi = dB(p.gain || 0), ce = dB(p.ceil ?? -.3), tp = p.tp !== false, st = p.style || 'transparent';
  const D = Math.ceil(sr * .03) + 64, dl0 = new Float64Array(D), dl1 = new Float64Array(D); let look = Math.max(1, Math.round((p.look || 2) * sr / 1000)); if (st === 'aggressive') look = Math.max(1, look >> 2);
  const HL = mode === 'today' ? 0 : 6; /* the 12-tap phases look 6 samples ahead: the lookahead grows by 6 */ const LK = look + HL;
  const W = look + 1, ring = new Float64Array(W).fill(1); let sum = W; const Q = D * 2, dq = new Float64Array(Q), dv = new Float64Array(Q); let qh = 0, qt = 0, cnt = 0, w = 0;
  const rel = Math.max(5, p.rel || 120) / 1000, rc1 = 1 - Math.exp(-1 / (rel * .12 * sr)), rc2 = 1 - Math.exp(-1 / (rel * sr)); let e1 = 1, e2 = 1;
  const h0 = [0, 0, 0, 0], h1 = [0, 0, 0, 0], H0 = new Float64Array(12), H1 = new Float64Array(12);
  const tp4 = (H) => { let m = 0; for (let ph = 1; ph < 4; ph++) { let s = 0; for (let k = 0; k < 12; k++) s += AE.TPH[ph * 12 + k] * H[11 - k]; m = Math.max(m, Math.abs(s)); } return m; };
  for (let i = 0; i < n; i++) { const l = L[i] * gi, r = R[i] * gi; let pk;
    if (mode === 'today') { h0.shift(); h0.push(l); h1.shift(); h1.push(r); pk = Math.max(Math.abs(l), Math.abs(r)); if (tp) pk = Math.max(pk, tpk(h0[0], h0[1], h0[2], h0[3]), tpk(h1[0], h1[1], h1[2], h1[3])); }
    else { H0.copyWithin(0, 1); H0[11] = l; H1.copyWithin(0, 1); H1[11] = r; pk = Math.max(Math.abs(H0[5]), Math.abs(H1[5]), Math.abs(l), Math.abs(r), tp4(H0), tp4(H1)) * 1.0116; /* +0.1 dB: what the 4x filter can still miss */ }
    const need = pk > ce ? ce / pk : 1;
    while (qt !== qh && dv[(qt - 1 + Q) % Q] >= need) qt = (qt - 1 + Q) % Q; dq[qt] = cnt; dv[qt] = need; qt = (qt + 1) % Q;
    while (dq[qh] <= cnt - W) qh = (qh + 1) % Q; const m = dv[qh]; const k = cnt % W; sum += m - ring[k]; ring[k] = m; const ga = sum / W;
    let g; if (st === 'transparent' || st === 'clean') { e1 = ga < e1 ? ga : e1 + (ga - e1) * rc1; e2 = ga < e2 ? ga : e2 + (ga - e2) * rc2; g = (e1 + e2) * .5; } else { e1 = ga < e1 ? ga : e1 + (ga - e1) * rc2 * 1.6; e2 = e1; g = e1; }
    dl0[w] = l; dl1[w] = r; const rp = (w - (mode === 'today' ? look : LK) + D) % D; let yl = dl0[rp] * g, yr = dl1[rp] * g;
    if (mode !== 'tp4clip') { if (yl > ce) yl = ce; else if (yl < -ce) yl = -ce; if (yr > ce) yr = ce; else if (yr < -ce) yr = -ce; }
    oL[i] = yl; oR[i] = yr; w = (w + 1) % D; cnt++; }
  if (mode === 'tp4clip') { /* final safety: 4x up (BS.1770 filter as 4-phase interpolator), clip at the ceiling, 4x down with a long linear-phase filter */
    for (const o of [oL, oR]) { const U = AE.up4(o); for (let i = 0; i < U.length; i++) { if (U[i] > ce) U[i] = ce; else if (U[i] < -ce) U[i] = -ce; } const d = AE.down4(U); o.set(d.subarray(0, n)); } }
  return [oL, oR]; };
AE.up4 = function (x) { const n = x.length, y = new Float64Array(n * 4); for (let i = 0; i < n; i++) for (let ph = 0; ph < 4; ph++) { let s = 0; for (let k = 0; k < 12; k++) { const j = i + 6 - k; if (j >= 0 && j < n) s += AE.TPH[ph * 12 + k] * x[j]; } y[i * 4 + ph] = s; } return y; };
AE.down4 = function (U) { let u = AE.down2(U, AE.HB79); u = AE.down2(u, AE.HB79); /* realign the up4 delay (6 samples) */ return u.subarray(6); };

/* ---------- dither (postProc, index.html L7989): TPDF +-1 LSB; first-order error feedback ('ns'); candidate: 9-tap F-weighted shaping (Wannamaker 1992) */
AE.quantize = function (x, bits, mode, rnd) { const m = Math.pow(2, bits - 1) - 1, q = 1 / m, y = new Float64Array(x.length); let e1 = 0; const E = new Float64Array(9);
  const W9 = [2.412, -3.370, 3.937, -4.174, 3.353, -2.205, 1.281, -0.569, 0.0847];
  for (let i = 0; i < x.length; i++) { let v = x[i];
    if (mode === 'ns') v -= e1; else if (mode === 'ns9') { let s = 0; for (let k = 0; k < 9; k++) s += W9[k] * E[k]; v -= s; }
    const d = mode === 'off' ? 0 : (rnd() - rnd()) * q; let o = Math.round((v + d) * m) / m; o = o > 1 ? 1 : o < -1 ? -1 : o;
    if (mode === 'ns') e1 = o - v; else if (mode === 'ns9') { E.copyWithin(1, 0); E[0] = o - v; } y[i] = o; } return y; };

/* ---------- DC blocker (JOS: R = 0.995 at 44.1 kHz ~ 35 Hz; a 5 Hz one here) */
AE.dcBlock = function (x, sr, fc) { fc = fc || 5; const R = 1 - TAU * fc / sr, y = new Float64Array(x.length); let xp = 0, yp = 0; for (let i = 0; i < x.length; i++) { const v = x[i] - xp + R * yp; xp = x[i]; yp = v; y[i] = v; } return y; };

if (typeof module !== 'undefined' && module.exports) module.exports = AE; else root.AE = AE;
})(typeof globalThis !== 'undefined' ? globalThis : this);
