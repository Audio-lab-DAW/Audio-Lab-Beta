"""Task SND-0 (lane L): the shared DSP kit (sndKitCore; SNDK in the worklet module).
Checks in the app: the kit is in the worklet module and loads without errors; the probe processor al-snd-kit gives the
same bits in the worklet as the kit on the main thread for every block (filters, shapers, oversamplers); worklet
instruments still render; nothing of the kit runs at start or while idle; no console errors. Then the unit tests against
the analog responses (tools/engine-lab/snd/kit_test.py) on this index.html. No device uses the kit yet: no sound changes.
  python3 tools/ui-tests/taskSND_0.py [index.html] [out dir]"""
import sys, os, json, subprocess
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
IDX = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
SRC = open(IDX, encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('snd0')){sessionStorage.setItem('snd0','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
BLOCKS = [['svf', [1200, 3, 0]], ['svf', [300, 0.7, 2]], ['svf', [5000, 8, 5]], ['onepole', [800, 0]],
          ['ladder', [900, 0.8, 1, 0]], ['ladder', [900, 1.05, 3, 1]], ['diode', [700, 0.9, 1, 0]], ['diode', [700, 0.95, 4, 1]],
          ['sk', [1500, 0.9, 2, 1]], ['comb', [123.4, 0.9, 5000, 0]], ['comb', [57, -0.6, 1e9, 1]], ['formant', [2.3, 1]],
          ['shaper', [0, 6, 1, 1]], ['shaper', [1, 6, 2, 1]], ['shaper', [2, 3, 4, 1]], ['shaper', [0, 6, 1, 0]], ['os2', []], ['os4', []]]
JS = """window.__sndRes=(async (B) => {
  const sr = 48000, n = 8192, x = new Float32Array(n); let s = 777;
  for (let k = 0; k < n; k++) { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; x[k] = (s / 4294967296 * 2 - 1) * 0.7 } x[0] = 1;
  const K = sndKitCore(), res = [];
  for (const [name, p] of B) {
    const oc = new OfflineAudioContext(1, n, sr); await wlLoad(oc);
    const buf = oc.createBuffer(1, n, sr); buf.copyToChannel(x, 0);
    const src = oc.createBufferSource(); src.buffer = buf;
    const nd = new AudioWorkletNode(oc, 'al-snd-kit', {numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [1], processorOptions: {name, p}});
    src.connect(nd); nd.connect(oc.destination); src.start(0);
    const y = (await oc.startRendering()).getChannelData(0);
    const b = K.make(name, p, sr), z = new Float32Array(n); for (let k = 0; k < n; k++) z[k] = b.tick(x[k]);
    let diff = 0, pk = 0; for (let k = 0; k < n; k++) { if (y[k] !== z[k]) diff++; const a = Math.abs(y[k]); if (a > pk) pk = a }
    res.push({name, p, diff, pk, fin: y.every(Number.isFinite)});
  }
  return res })(%s);0"""
with sync_playwright() as pw:
    b = pw.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.add_init_script(INIT)
    pg.add_init_script("window.__sndNodes=0;const _AWN=window.AudioWorkletNode;if(_AWN)window.AudioWorkletNode=class extends _AWN{constructor(c,n,o){super(c,n,o);if(n==='al-snd-kit')window.__sndNodes++}}")
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body='')))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(2500)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 274), 'version 0.274 or later', R('VERSION'))
    ok(J("typeof sndKitCore==='function'&&typeof sndWL==='function'&&SND_HOOKS.kit===1"), 'the kit, its worklet part and SND_HOOKS are in the page')
    R("openDemoFractals()"); pg.wait_for_timeout(6000); R("toggle()"); pg.wait_for_timeout(2500); R("play.on&&toggle()"); pg.wait_for_timeout(500)
    ok(J("window.__sndNodes") == 0, 'nothing of the kit runs at start, with a song or while playing (no probe node; no device uses the kit yet)')
    R("window.__sndTxt=(async()=>{ensureCtx();await wlLoad(ctx);return await (await fetch(WLU)).text()})();0"); txt = pg.evaluate("() => window.__sndTxt")
    ok('const SNDK=(' in txt and "registerProcessor('al-snd-kit'" in txt, 'the worklet module carries the kit (SNDK) and the probe', len(txt))
    ok(txt.count("registerProcessor('al-snd-kit'") == 1 and txt.rfind('const SNDK=(') > txt.rfind("registerProcessor('al-abx") if "registerProcessor('al-abx" in txt else True, 'the kit is appended once, after the other processors')
    R(JS % json.dumps(BLOCKS)); res = pg.evaluate("() => window.__sndRes")
    same = [r for r in res if r['diff'] == 0 and r['fin'] and r['pk'] > 1e-4]
    ok(len(same) == len(BLOCKS), 'every kit block gives the same bits in the worklet as on the main thread (%d blocks, 8192 samples of noise)' % len(BLOCKS),
       [(r['name'], r['p'], r['diff']) for r in res if r not in same])
    # an existing worklet instrument still renders through the same module
    R("window.__snd0=null;(async()=>{const oc=new OfflineAudioContext(2,48000,48000);await wlLoad(oc);const n=new AudioWorkletNode(oc,'al-psb',{numberOfInputs:0,outputChannelCount:[2]});n.connect(oc.destination);window.__snd0='ok'})().catch(e=>window.__snd0='err '+e)")
    pg.wait_for_timeout(1500)
    ok(J("window.__snd0") == 'ok', 'the other worklet processors still load from the same module (Psy Bass node made)', J("window.__snd0"))
    ok(not errs, 'no console errors', errs[:5])
    b.close()
r = subprocess.run([sys.executable, os.path.join(HERE, '..', 'engine-lab', 'snd', 'kit_test.py'), IDX, os.path.join(OUT, 'snd0_kit.json')], capture_output=True, text=True)
last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:]
ok(r.returncode == 0, 'the kit unit tests against the analog responses pass (kit_test.py)', last)
print(f'{N[1]} of {N[0]} checks passed')
sys.exit(1 if FAIL else 0)
