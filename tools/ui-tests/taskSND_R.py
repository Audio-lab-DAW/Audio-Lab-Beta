"""Task SND-R (lane L): one random stream per device (the user's D2, docs/review-native.md A2).
Checks in the app: the worklet module puts the wrapper before every processor; a probe processor (added to the same worklet scope)
reads exactly seedRng('sndr|<seed>|<name>#<n>'); a second device's numbers do not change when the first draws more or fewer; they do
not change with the render block size (where the browser offers renderSizeHint); two Bitcrushers with dither and jitter: the second
one's output is bit-identical whatever the first does; the same seed renders the same twice, another seed differs; with Fixed seed
off two renders differ; a node given processorOptions.sndKey keeps its stream when another node is made before it; the cost of
8 Bitcrushers (offline, 20 s); the Fractals song opens and plays without console errors.
Run on the old file too: the checks that show the old shared stream fail there (that is the before).
  python3 tools/ui-tests/taskSND_R.py [index.html] [out json]"""
# for: task SND-R (lane L)
import sys, os, json
from playwright.sync_api import sync_playwright
IDX = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
SRC = open(IDX, encoding='utf-8').read()
OUTJ = sys.argv[2] if len(sys.argv) > 2 else None
N = [0, 0]; FAIL = []; RES = {}
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('sndr')){sessionStorage.setItem('sndr','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
PROBE = r"""class SndrProbe extends AudioWorkletProcessor{constructor(o){super();this.k=(o.processorOptions&&o.processorOptions.k)||1}
 process(i,o){const a=o[0][0];for(let j=0;j<a.length;j++){let v=0;for(let q=0;q<this.k;q++)v=Math.random();a[j]=v}return true}}
registerProcessor('sndr-probe',SndrProbe);"""
JS = r"""window.__r=(async (PROBE) => {
  const sr = 48000, n = 128 * 40, out = {};
  const PU = URL.createObjectURL(new Blob([PROBE], {type: 'application/javascript'}));
  const ctxOf = async (rq) => { const oc = rq ? new OfflineAudioContext({numberOfChannels: 2, length: n, sampleRate: sr, renderSizeHint: rq}) : new OfflineAudioContext(2, n, sr); await wlLoad(oc); await oc.audioWorklet.addModule(PU); return oc };
  const probes = async (ks, rq, keys) => { const oc = await ctxOf(rq), m = oc.createChannelMerger(2);
    ks.forEach((k, i) => { const po = {k}; if (keys && keys[i] != null) po.sndKey = keys[i]; const nd = new AudioWorkletNode(oc, 'sndr-probe', {numberOfInputs: 0, numberOfOutputs: 1, outputChannelCount: [1], processorOptions: po}); nd.connect(m, 0, Math.min(i, 1)) });
    m.connect(oc.destination); const y = await oc.startRendering(); return [Array.from(y.getChannelData(0)), Array.from(y.getChannelData(1))] };
  const same = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);
  S.seed = 12345; UI.exSeed = true;
  // 1. a lone probe reads seedRng('sndr|12345|sndr-probe#0')
  { const [a] = await probes([1]); const R = seedRng('sndr|12345|sndr-probe#0'); let d = 0; for (let i = 0; i < n; i++) if (a[i] !== Math.fround(R())) d++; out.exact = d; out.first = a.slice(0, 3) }
  // 2. probe B (channel 1) with A drawing once or three times per sample
  { const [a1, b1] = await probes([1, 1]), [a3, b3] = await probes([3, 1]); out.indep = same(b1, b3); out.distinct = !same(a1, b1) }
  // 3. block size
  out.rq = (() => { try { return new OfflineAudioContext({numberOfChannels: 1, length: 1024, sampleRate: sr, renderSizeHint: 256}).renderQuantumSize === 256 } catch (e) { return false } })();
  if (out.rq) { const p128 = await probes([2, 1], 128), p256 = await probes([2, 1], 256), p512 = await probes([2, 1], 512); out.bs = same(p128[1], p256[1]) && same(p128[1], p512[1]) && same(p128[0], p512[0]) }
  // 4. sndKey: a keyed node keeps its stream when another node is made before it
  { const [x] = await probes([1], 0, ['dev-7']), [, y] = await probes([1, 1], 0, [null, 'dev-7']); out.key = same(x, y) }
  // 5. two Bitcrushers with dither and jitter on two channels: the second one's output whatever the first does
  const crush = async (pa, pb, rq) => { const oc = await ctxOf(rq), m = oc.createChannelMerger(2);
    const buf = oc.createBuffer(1, n, sr), d = buf.getChannelData(0); for (let i = 0; i < n; i++) d[i] = 0.4 * Math.sin(i * 0.031);
    const mk = (p, ch) => { const s = oc.createBufferSource(); s.buffer = buf; const x = mkFxNode(oc, 'crush'); const P = Object.assign(mkFx('crush').p, p); x.set(P); s.connect(x.in); x.out.connect(m, 0, ch); s.start(0) };
    mk(pa, 0); mk(pb, 1); m.connect(oc.destination); const y = await oc.startRendering(); return [Array.from(y.getChannelData(0)), Array.from(y.getChannelData(1))] };
  const B = {bits: 6, dith: 60, jit: 30, rate: 3}, A1 = {bits: 5, dith: 80, jit: 50, rate: 2}, A0 = {bits: 8, dith: 0, jit: 0, rate: 1};
  { const [a1, b1] = await crush(A1, B), [a0, b0] = await crush(A0, B); out.crushIndep = same(b1, b0); out.crushMoves = b1.some((v, i) => v !== b1[0]);
    let s = 0; for (const v of b1) s += v * v; out.crushRms = 10 * Math.log10(s / n + 1e-30);
    const [, b1b] = await crush(A1, B); out.repeat = same(b1, b1b);
    if (out.rq) { const [, q512] = await crush(A1, B, 512), [, q128] = await crush(A1, B, 128); out.crushBs = same(q512, q128) }
    S.seed = 777; const [, bs2] = await crush(A1, B); out.seedMatters = !same(b1, bs2); S.seed = 12345;
    UI.exSeed = false; const [, f1] = await crush(A1, B), [, f2] = await crush(A1, B); out.freeDiffers = !same(f1, f2); UI.exSeed = true }
  // 6. cost: 8 Bitcrushers with dither and jitter, 20 s offline, best of 3
  { const L = sr * 20; let best = 1e9;
    for (let r = 0; r < 3; r++) { const oc = new OfflineAudioContext(2, L, sr); await wlLoad(oc); const o = oc.createOscillator(); o.frequency.value = 220;
      for (let k = 0; k < 8; k++) { const x = mkFxNode(oc, 'crush'); x.set(Object.assign(mkFx('crush').p, B)); o.connect(x.in); x.out.connect(oc.destination) }
      o.start(0); const t0 = performance.now(); await oc.startRendering(); best = Math.min(best, performance.now() - t0) }
    out.ms8 = best; out.pctCore = best / 20000 * 100 / 8 }
  return out })(%s);0"""
with sync_playwright() as pw:
    b = pw.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.add_init_script(INIT)
    pg.route('https://app.test/**', lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body=''))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(2500)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    print('version', R('VERSION'))
    new = J("typeof sndRWL==='function'")
    ok(new and J("typeof sndRSeed==='function'&&SND_HOOKS.rseed===sndRSeed&&AudioWorkletNode.__sndR===1"), 'the per-device seed is defined (sndRSeed, SND_HOOKS.rseed) and every new AudioWorkletNode carries it')
    R("window.__t=(async()=>{ensureCtx();await wlLoad(ctx);return await (await fetch(WLU)).text()})();0"); pg.wait_for_function('() => window.__t && window.__t.then', timeout=5000); txt = pg.evaluate("() => window.__t")
    i0 = txt.find('rp.__sndR'); i1 = txt.find('registerProcessor(')
    ok(i0 >= 0 and i0 < txt.find("registerProcessor('al-", i0) and txt.count('rp.__sndR') == 1, 'the worklet module puts the wrapper once, before every processor')
    R(JS % json.dumps(PROBE)); pg.wait_for_function('() => window.__r && window.__r.then', timeout=5000)
    r = pg.evaluate("() => window.__r"); RES.update(r); print(json.dumps({k: v for k, v in r.items() if k != 'first'}))
    ok(r['exact'] == 0, "a device's numbers are exactly seedRng('sndr|<seed>|<processor>#<n>') (5120 samples)", r['exact'])
    ok(r['indep'], "the second device's numbers do not change when the first draws three times as many")
    ok(r['distinct'], 'two devices get different streams')
    ok(not r['rq'] or r.get('bs'), 'the same numbers at render blocks of 128, 256 and 512', 'renderSizeHint %s' % r['rq'])
    ok(r['key'], 'a node given processorOptions.sndKey keeps its stream when another node is made before it')
    ok(r['crushIndep'], "two Bitcrushers with dither and jitter: the second one's output is bit-identical whatever the first does")
    ok(r['crushMoves'] and -40 < r['crushRms'] < 0, 'the Bitcrusher still makes sound (level %.2f dB)' % r['crushRms'])
    ok(r['repeat'], 'the same project and seed render the same twice')
    ok(not r['rq'] or r.get('crushBs'), 'two Bitcrushers: the same output at render blocks of 128 and 512')
    ok(r['seedMatters'], 'another export seed gives another noise pattern')
    ok(r['freeDiffers'], 'Fixed seed off: two renders differ')
    print('cost: 8 Bitcrushers 20 s offline %.0f ms, %.3f %% of a core per device' % (r['ms8'], r['pctCore']))
    R("openDemoFractals()"); pg.wait_for_timeout(6000)
    R("ensureCtx();start()"); pg.wait_for_timeout(3000); R("stop()"); pg.wait_for_timeout(500)
    ok(not errs, 'no console errors (load, the tests, Fractals open and played 3 s)', errs[:4])
    b.close()
print('%d of %d' % (N[1], N[0]))
if OUTJ: json.dump(dict(res=RES, passed=N[1], total=N[0], failed=FAIL), open(OUTJ, 'w'), indent=1)
sys.exit(0 if not FAIL else 1)
