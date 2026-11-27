// Task AE1: run today's algorithms and the candidates (dsp.js) on test signals, write the signals for lab_anal.py and
// measure the CPU cost. node tools/engine-lab/ae1/lab.js [part ...]   parts: osc acid drive kick filter resample limit dither cpu
const AE = require('./dsp.js'), fs = require('fs'), path = require('path');
const OUT = path.join(__dirname, 'results', 'sig'); fs.mkdirSync(OUT, { recursive: true });
const parts = new Set(process.argv.slice(2)), want = (p) => !parts.size || parts.has(p);
const dump = (name, a) => fs.writeFileSync(path.join(OUT, name + '.f64'), Buffer.from(Float64Array.from(a).buffer));
const sr = 48000, n = 96000, hz = (p) => 440 * Math.pow(2, (p - 69) / 12);

if (want('osc')) { // the al-poly saw through its 18 kHz low-pass (as measured in the app), the table-BLEP saw, a 2x PolyBLEP
  for (const p of [33, 45, 57, 69, 81, 88, 93, 100, 105]) { const f = hz(p);
    dump('osc_today_' + p, AE.rbjLP16(AE.sawPolyBlep(f, sr, n), sr, 18000, 0));
    dump('osc_blep_' + p, AE.rbjLP16(AE.sawBlep(f, sr, n), sr, 18000, 0));
    dump('osc_pb2x_' + p, AE.rbjLP16(AE.down2(AE.sawPolyBlep(f, sr * 2, n * 2), AE.HB47), sr, 18000, 0)); }
  // a sweep 40 Hz -> 6 kHz (exponential, 4 s) for the spectrogram
  const N = sr * 4, fq = (i) => 40 * Math.pow(150, i / N);
  dump('sweep_today', AE.sawPolyBlep(fq, sr, N)); dump('sweep_blep', AE.sawBlep(fq, sr, N)); }

if (want('acid')) { // a held acid note: al-poly acid at 1x against variants
  for (const p of [33, 45, 57, 69]) { const notes = [[0, n, p, .8]], base = { sr, n, notes, cut: 2000, env: 0, dec: 1, res: 12, dist: 55 };
    dump('acid_today_' + p, AE.acidVoice({ ...base }));
    dump('acid_adaa1x_' + p, AE.acidVoice({ ...base, drv: 'adaa' }));
    dump('acid_2x_' + p, AE.acidVoice({ ...base, M: 2 }));
    dump('acid_2xadaa_' + p, AE.acidVoice({ ...base, M: 2, drv: 'adaa' }));
    dump('acid_hq_' + p, AE.acidVoice({ ...base, hq: true }));
    dump('acid_4xadaa_' + p, AE.acidVoice({ ...base, M: 4, drv: 'adaa', osc: 'blep', flt: 'svf' })); } }

if (want('drive')) { // the Drive effect's curve: 1x, 4x (as the WaveShaperNode), 4x + ADAA, 8x
  for (const [f0, lvl, drv] of [[2531, -6, 60], [4057, -6, 60], [5003, 3, 100], [1013, -6, 30]]) { const a = Math.pow(10, lvl / 20), x = new Float64Array(n); for (let i = 0; i < n; i++) x[i] = a * Math.sin(2 * Math.PI * f0 * i / sr);
    const f = AE.driveCurve(drv), F = AE.driveCurveF(drv), tag = f0 + '_' + drv;
    dump('drive_1x_' + tag, AE.shape(x, f));
    dump('drive_4x_' + tag, AE.os(x, 2, (u) => AE.shape(u, f)));
    dump('drive_4xadaa_' + tag, AE.os(x, 2, (u) => AE.shapeADAA(u, f, F)));
    dump('drive_8x_' + tag, AE.os(x, 3, (u) => AE.shape(u, f))); } }

if (want('kick')) { // the demo's kick (psyzap, tune 29, drive 45, click 60, start 2600)
  const K = { len: .24, tune: 29, start: 2600, sweep: .055, bend: 60, tail: 14, click: 60, drive: 45 };
  dump('kick_1x', AE.kick(K, sr, 1)); dump('kick_2x', AE.kick(K, sr, 2)); dump('kick_4x', AE.kick(K, sr, 4)); dump('kick_8x', AE.kick(K, sr, 8));
  dump('kick_ref', AE.kick(K, sr, 32)); }

if (want('filter')) { // a fast acid envelope sweep 9 kHz -> 300 Hz with high resonance: per-16 RBJ against per-sample ZDF SVF
  const N = sr, x = AE.sawPolyBlep(hz(45), sr, N), cut = (i) => 300 + 8700 * Math.exp(-i / sr / .04), res = 21;
  dump('flt_rbj16', AE.rbjLP16(x, sr, cut, res)); dump('flt_rbj1', AE.rbjLP16(x, sr, cut, res, 1)); dump('flt_svf', AE.svfLP(x, sr, cut, res));
  // an extreme case: the cut-off jumping by an LFO at audio rate (FM of the filter), 2 kHz <-> 12 kHz at 300 Hz
  const cut2 = (i) => 7000 + 5000 * Math.sin(2 * Math.PI * 300 * i / sr);
  dump('flt2_rbj16', AE.rbjLP16(x, sr, cut2, 18)); dump('flt2_svf', AE.svfLP(x, sr, cut2, 18)); }

if (want('resample')) { // 44.1 kHz material in a 48 kHz engine, and a sample pitched +7 semitones
  for (const f0 of [1000, 5000, 10000, 15000]) { const n0 = 44100 * 2, x = new Float64Array(n0); for (let i = 0; i < n0; i++) x[i] = .5 * Math.sin(2 * Math.PI * f0 * i / 44100);
    dump('rs_lin_' + f0, AE.resampleLinear(x, 44100 / 48000, n)); dump('rs_sinc_' + f0, AE.resampleSinc(x, 44100 / 48000, n)); }
  const rate = Math.pow(2, 7 / 12);
  for (const f0 of [1000, 5000, 10000]) { const n0 = sr * 3, x = new Float64Array(n0); for (let i = 0; i < n0; i++) x[i] = .5 * Math.sin(2 * Math.PI * f0 * i / sr);
    dump('rp_lin_' + f0, AE.resampleLinear(x, rate, n)); dump('rp_sinc_' + f0, AE.resampleSinc(x, rate, n)); } }

if (want('limit')) { // the demo's Climax (rendered by measure_app.py) through al-limit (port) and the candidates
  const f = path.join(__dirname, 'results', 'demo_climax.f32');
  if (fs.existsSync(f)) { const b = fs.readFileSync(f), a = new Float32Array(b.buffer, b.byteOffset, b.length / 4), m = a.length / 2, L = Float64Array.from(a.subarray(0, m)), R = Float64Array.from(a.subarray(m));
    for (const push of [6, 10]) for (const mode of ['today', 'tp4', 'tp4clip']) { const [oL, oR] = AE.limiter(L, R, sr, { gain: push + 3, ceil: -.3, look: 3, rel: 150, style: 'transparent', tp: true, mode }); dump('lim_' + mode + '_' + push + '_L', oL); dump('lim_' + mode + '_' + push + '_R', oR); } }
  else console.log('no demo_climax.f32: run measure_app.py limit first'); }

if (want('dither')) { const x = new Float64Array(n); for (let i = 0; i < n; i++) x[i] = Math.pow(10, -90 / 20) * Math.sin(2 * Math.PI * 1000 * i / sr);
  for (const m of ['off', 'tpdf', 'ns', 'ns9']) dump('dith_' + m, AE.quantize(x, 16, m, AE.rng(1))); }

if (want('cpu')) { // ns per output sample, best of 5, one voice / one stereo channel pair
  const T = (fn, N) => { let best = 1e9; for (let r = 0; r < 5; r++) { const t0 = process.hrtime.bigint(); fn(); const dt = Number(process.hrtime.bigint() - t0) / N; best = Math.min(best, dt); } return best; };
  const N = sr * 4, R = {};
  const notes = [[0, N, 45, .8]], base = { sr, n: N, notes, cut: 2000, env: 50, dec: .2, res: 12, dist: 55 };
  R.acid_today = T(() => AE.acidVoice({ ...base }), N);
  R.acid_adaa1x = T(() => AE.acidVoice({ ...base, drv: 'adaa' }), N);
  R.acid_2xadaa = T(() => AE.acidVoice({ ...base, M: 2, drv: 'adaa' }), N);
  R.acid_hq = T(() => AE.acidVoice({ ...base, hq: true }), N);
  R.saw_polyblep = T(() => AE.sawPolyBlep(110, sr, N), N);
  R.saw_blep = T(() => AE.sawBlep(110, sr, N), N);
  R.saw_blep_3k = T(() => AE.sawBlep(3000, sr, N), N);
  R.rbj16 = T(() => AE.rbjLP16(new Float64Array(N), sr, 1000, 3), N);
  R.svf = T(() => AE.svfLP(new Float64Array(N), sr, (i) => 1000, 3), N);
  const x = new Float64Array(N).map((_, i) => .5 * Math.sin(i * .1)), f = AE.driveCurve(60), F = AE.driveCurveF(60);
  R.drive_1x = T(() => AE.shape(x, f), N); R.drive_4x = T(() => AE.os(x, 2, (u) => AE.shape(u, f)), N); R.drive_4xadaa = T(() => AE.os(x, 2, (u) => AE.shapeADAA(u, f, F)), N); R.drive_8x = T(() => AE.os(x, 3, (u) => AE.shape(u, f)), N);
  R.lim_today = T(() => AE.limiter(x, x, sr, { mode: 'today' }), N); R.lim_tp4 = T(() => AE.limiter(x, x, sr, { mode: 'tp4' }), N); R.lim_tp4clip = T(() => AE.limiter(x, x, sr, { mode: 'tp4clip' }), N);
  R.rs_lin = T(() => AE.resampleLinear(x, 44100 / 48000, N), N); R.rs_sinc = T(() => AE.resampleSinc(x, 44100 / 48000, N), N);
  R.kick_1x = T(() => AE.kick({ len: .24, tune: 29, start: 2600, sweep: .055, bend: 60, tail: 14, click: 60, drive: 45 }, sr, 1), 11520);
  R.kick_4x = T(() => AE.kick({ len: .24, tune: 29, start: 2600, sweep: .055, bend: 60, tail: 14, click: 60, drive: 45 }, sr, 4), 11520);
  fs.writeFileSync(path.join(__dirname, 'results', 'cpu.json'), JSON.stringify(R, null, 1)); console.log(R); }
console.log('done');
