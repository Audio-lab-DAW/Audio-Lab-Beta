"""Task SND-1 (lane L): Filter v2 (new device 'filter2') and the Auto Filter's Clean models (B37, N5).
Checks in the app: the processor al-snd-filter is in the worklet module once; the worklet gives the same bits as the core on the main
thread for every model, at 2x and Off, with parameter jumps, a mono part and a stereo part; values glide (20 ms) instead of jumping;
the processor sleeps after 1 s of silence and wakes on sound; the Filter device opens, its menus have tooltips, a model change reaches
the processor; a new Auto Filter starts in Clean, a saved one (no Quality) stays Classic and a preset keeps it Classic; switching an
old Auto Filter to Clean moves its sound through the processor (LFO and envelope still move the cutoff); dark and Light screenshots;
no console errors. Then the before and after numbers (tools/engine-lab/snd/snd1_measure.py) if given as a third argument.
  python3 tools/ui-tests/taskSND_1.py [index.html] [out dir]"""
import sys, os, json
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
INIT = "if(!sessionStorage.getItem('snd1')){sessionStorage.setItem('snd1','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
# worklet against the main-thread core: 3 blocks of 128 at each value set, freq/res/drive/mix jump at block 24 and 40
CASES = [dict(model=m, mode=md, os=o, freq=f, res=r, drive=d, mix=x, out=ou, vowel=v, det=dt)
         for (m, md, f, r, d, x, ou, v, dt) in [(0, 0, 900, .8, 0, 1, 0, 0, 0), (0, 0, 700, 1.0, .6, 1, 3, 0, 0), (1, 0, 600, .9, .4, 1, 0, 0, 0), (1, 0, 3000, .2, 0, .5, 0, 0, 0),
                                                (2, 0, 1500, .95, .5, 1, 0, 0, 0), (2, 1, 900, .7, 0, 1, 0, 0, 0), (3, 1, 1200, .5, 0, 1, 0, 0, 0), (3, 2, 300, .2, .3, .7, 0, 0, 0),
                                                (4, 0, 2000, 0, 0, 1, 0, 0, 0), (4, 3, 1000, .4, 0, 1, 0, 0, 0), (5, 0, 220, .85, 0, 1, 0, 0, 0), (5, 3, 400, .7, .2, 1, 0, 0, 0),
                                                (6, 0, 1000, 0, 0, 1, -2, 2.3, 0), (7, 0, 1100, .3, 0, 1, 0, 0, 0), (0, 0, 500, .5, 0, 1, 0, 0, 700)]
         for o in (2, 1)]
JS = """window.__s1=(async (C) => {
  const sr = 48000, n = 128 * 64, xl = new Float32Array(n), xr = new Float32Array(n); let s = 4242;
  for (let k = 0; k < n; k++) { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; const a = (s / 4294967296 * 2 - 1) * 0.6; s = (Math.imul(s, 1664525) + 1013904223) >>> 0; const b = (s / 4294967296 * 2 - 1) * 0.6;
    xl[k] = a; xr[k] = k < 128 * 16 ? a : b } xl[0] = 1; xr[0] = 1;
  const K = sndKitCore(), F = sndFltCore(K), res = [], f32 = v => new Float32Array([v]);
  const J = [[24, {freq: 2.5, res: 0.5, drive: 0.5, mix: 1}], [40, {freq: 0.3, res: 1.1, drive: 0, mix: 0.8}]];
  for (const c of C) {
    const oc = new OfflineAudioContext(2, n, sr); await wlLoad(oc);
    const buf = oc.createBuffer(2, n, sr); buf.copyToChannel(xl, 0); buf.copyToChannel(xr, 1);
    const src = oc.createBufferSource(); src.buffer = buf;
    const pd = {freq: c.freq, res: c.res, drive: c.drive, mix: c.mix, out: c.out, vowel: c.vowel, det: c.det};
    const nd = new AudioWorkletNode(oc, 'al-snd-filter', {numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [2], channelCount: 2, channelCountMode: 'explicit', parameterData: pd, processorOptions: {model: c.model, mode: c.mode, os: c.os}});
    const V = [], cur = Object.assign({}, pd);
    for (const [b, m] of J) { const nv = {freq: c.freq * m.freq, res: Math.min(1.2, c.res * m.res + (m.res > 1 ? 0.05 : 0)), drive: c.drive * m.drive + (m.drive ? 0.1 : 0), mix: c.mix * m.mix};
      for (const k in nv) nd.parameters.get(k).setValueAtTime(nv[k], b * 128 / sr); V.push([b, nv]) }
    src.connect(nd); nd.connect(oc.destination); src.start(0);
    const y = await oc.startRendering(), yl = y.getChannelData(0), yr = y.getChannelData(1);
    const e = new F.Engine(sr, {model: c.model, mode: c.mode, os: c.os}), zl = new Float32Array(n), zr = new Float32Array(n);
    for (let b = 0; b < n / 128; b++) { for (const [bb, nv] of V) if (bb === b) Object.assign(cur, nv);
      const P = {freq: f32(cur.freq), res: f32(cur.res), drive: f32(cur.drive), mix: f32(cur.mix), out: f32(cur.out), vowel: f32(cur.vowel), det: f32(cur.det)};
      const ol = new Float32Array(128), or = new Float32Array(128);
      e.block(xl.subarray(b * 128, b * 128 + 128), xr.subarray(b * 128, b * 128 + 128), ol, or, 128, P); zl.set(ol, b * 128); zr.set(or, b * 128) }
    let diff = 0, pk = 0; for (let k = 0; k < n; k++) { if (yl[k] !== zl[k] || yr[k] !== zr[k]) diff++; pk = Math.max(pk, Math.abs(yl[k]), Math.abs(yr[k])) }
    let stereo = 0; for (let k = 128 * 16; k < n; k++) if (yl[k] !== yr[k]) stereo++;
    res.push({m: c.model, md: c.mode, os: c.os, diff, pk, stereo, fin: yl.every(Number.isFinite) && yr.every(Number.isFinite)}) }
  return res })(%s);0"""
with sync_playwright() as pw:
    b = pw.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.add_init_script(INIT)
    pg.add_init_script("window.__sndF=0;const _AWN=window.AudioWorkletNode;if(_AWN)window.AudioWorkletNode=class extends _AWN{constructor(c,n,o){super(c,n,o);if(n==='al-snd-filter')window.__sndF++}}")
    pg.route('https://app.test/**', lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body=''))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(2500)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 289), 'version 0.289 or later', R('VERSION'))
    ok(J("typeof sndFltCore==='function'&&typeof sndFltNode==='function'&&SND_HOOKS.filterResp===sndFltResp&&!!FXDEF.filter2&&FXDEF.filter2.name==='Filter'"), 'Filter v2 is defined (FXDEF.filter2 "Filter"), with its core and SND_HOOKS.filterResp')
    ok(J("FXCAT.find(x=>x[0]==='EQ & filter')[1].includes('filter2')&&!!FXIC.filter2&&FBG.some(g=>g[2].includes('filter2'))"), 'it is listed with the filters in the device browser, with an icon')
    ok(J("!!FXDEF.filter&&FXDEF.filter.name==='Low-pass filter'"), 'the old Low-pass filter is still there for old projects')
    R("openDemoFractals()"); pg.wait_for_timeout(6000)
    ok(J("window.__sndF") == 0, 'nothing of Filter v2 runs in the Fractals song (no processor made)')
    R("window.__t=(async()=>{ensureCtx();await wlLoad(ctx);return await (await fetch(WLU)).text()})();0"); txt = pg.evaluate("() => window.__t")
    ok(txt.count("registerProcessor('al-snd-filter'") == 1 and txt.index('const SNDF=(') > txt.index('const SNDK=('), 'the worklet module carries the processor once, after the kit')
    R(JS % json.dumps(CASES)); pg.wait_for_function('() => window.__s1 && window.__s1.then', timeout=5000)
    res = pg.evaluate("() => window.__s1")
    bad = [r for r in res if r['diff'] or not r['fin'] or r['pk'] < 1e-3]
    ok(not bad, 'worklet bits equal the main-thread core: %d cases (7 models + Peak, 2x and Off, jumps at blocks 24 and 40, det, a mono part then stereo)' % len(res), bad[:4])
    ok(all(r['stereo'] > 1000 for r in res), 'the stereo part stays stereo after the mono part (channel 1 picks up channel 0)', [r['stereo'] for r in res][:6])
    # smoothing and sleep on the main thread
    sm = J("""(()=>{const K=sndKitCore(),F=sndFltCore(K),e=new F.Engine(48000,{model:3,mode:0,os:2}),z=new Float32Array(128),o=new Float32Array(128),f=v=>new Float32Array([v]);
      const P=(fr)=>({freq:f(fr),res:f(.3),drive:f(0),mix:f(1),out:f(0),vowel:f(0),det:f(0)}),x=new Float32Array(128);for(let k=0;k<128;k++)x[k]=Math.sin(k)*.3;
      e.block(x,x,o,o,128,P(200));const tr=[];for(let b=0;b<120;b++){e.block(x,x,o,o,128,P(5000));tr.push(Math.exp(e.lf.y))}
      const t63=tr.findIndex(v=>Math.log(v/200)>=Math.log(25)*0.632)*128/48,mono=tr.every((v,i)=>!i||v>=tr[i-1]);
      let sl=-1;for(let b=0;b<600;b++){e.block(z,z,o,o,128,P(5000));if(e.sleep&&sl<0)sl=b}
      const zero=o.every(v=>v===0);e.block(x,x,o,o,128,P(5000));return{t63,mono,end:tr[tr.length-1],sl:sl*128/48000,zero,woke:!e.sleep&&o.some(v=>v!==0)}})()""")
    ok(16 <= sm['t63'] <= 24 and sm['mono'] and abs(sm['end'] - 5000) < 1, 'a cutoff jump from 200 Hz to 5 kHz glides (63 %% in %.1f ms, 20 ms set), steadily, and lands' % sm['t63'], sm)
    ok(0.99 < sm['sl'] < 1.3 and sm['zero'] and sm['woke'], 'it sleeps after 1 s of silence in and out (%.2f s), gives zeros, and wakes on sound' % sm['sl'])
    # the device in the app
    R("selT=S.tracks.find(t=>t.name==='Bass').id;window.__t2=curT();window.__f2=mkFx('filter2');__t2.fx.push(__f2);changed(true);renderFx();0"); pg.wait_for_timeout(1500)
    d = J("(()=>{const D=document.querySelector(`#fxin .dev[data-id='${__f2.id}']`);if(!D)return null;const s=k=>D.querySelector(`select[data-x=${k}]`);return{model:s('model')&&s('model').options.length,tm:s('model')&&(s('model').title||s('model').dataset.tip||''),to:s('os')&&(s('os').title||s('os').dataset.tip||''),tmo:s('mode')&&(s('mode').title||s('mode').dataset.tip||''),p:__f2.p,knobs:[...D.querySelectorAll('[data-c]')].filter(e=>/:(freq|res|drive|vowel|mix|out)$/.test(e.dataset.c)).map(e=>(e.title||e.dataset.tip||'').length)}})()")
    ok(d and d['model'] == 7 and d['p']['model'] == 'ladder' and d['p']['os'] == '2x' and d['p']['pre'] == 'init', 'Filter opens on a track: 7 models, Ladder low-pass, 2x', d and {k: d[k] for k in ('model', 'p')})
    ok(d and len(d['tm']) > 40 and len(d['to']) > 40 and len(d['tmo']) > 40 and d['knobs'] and min(d['knobs']) > 20, 'its menus and knobs have tooltips', d and (d['knobs'], len(d['tm'])))
    pg.wait_for_timeout(1000)
    R("(()=>{const D=document.querySelector(`#fxin .dev[data-id='${__f2.id}']`),s=D.querySelector('select[data-x=model]');s.value='diode';s.dispatchEvent(new Event('change',{bubbles:true}))})()"); pg.wait_for_timeout(800)
    x2 = J("(()=>{const N=NODES.get(__t2.id),X=N&&N.fxm.get(__f2.id);return X&&X.snd?{m:X.snd.o.model,node:!!X.snd.node,p:__f2.p.model}:null})()")
    ok(x2 and x2['m'] == 1 and x2['node'] and x2['p'] == 'diode', 'a model change from the menu reaches the processor (Diode)', x2)
    def shot(fid, name):
        try:
            L = pg.locator("#fxin .dev[data-id='%s']" % fid); L.scroll_into_view_if_needed(); pg.wait_for_timeout(700); L.screenshot(path=os.path.join(OUT, name))
        except Exception as e: print('screenshot', name, e)
    fid2 = J("__f2.id"); shot(fid2, 'snd1_filter_dark.png')
    R("toggle()"); pg.wait_for_timeout(2500); R("play.on&&toggle()"); pg.wait_for_timeout(300)
    ok(J("window.__sndF") >= 1, 'playing with the Filter on the Bass makes its processor', J("window.__sndF"))
    # Auto Filter: new is Clean, saved is Classic, presets keep Classic
    a = J("(()=>{const f=mkFx('afilt');return{q:f.p.q,pre:f.p.pre,presetsQ:Object.values(FXPRE.afilt).filter(v=>v[1]&&'q' in v[1]).length,types:AFT.map(a=>a[0])}})()")
    ok(a['q'] == 'clean' and a['presetsQ'] == 0, 'a new Auto Filter starts with Hi-Fi on (q clean); its presets carry no q', a)
    ok(all(t in a['types'] for t in ('ladder', 'diode', 'ms20', 'lp24', 'comb', 'formant')), 'the Auto Filter types gain Ladder, Diode and MS-20', a['types'])
    R("window.__fa={id:rid(),type:'afilt',on:true,p:JSON.parse(JSON.stringify(FXPRE.afilt.wobble[1]))};delete __fa.p.q;__t2.fx.push(__fa);changed(true);renderFx();0"); pg.wait_for_timeout(1200)
    c1 = J("(()=>{const D=document.querySelector(`#fxin .dev[data-id='${__fa.id}']`),s=D&&D.querySelector('select[data-x=q]'),X=NODES.get(__t2.id).fxm.get(__fa.id);return{sel:s&&s.value,tip:s&&(s.title||s.dataset.tip||'').length,snd:!!X.snd,q:__fa.p.q??null}})()")
    ok(c1['sel'] == 'classic' and not c1['snd'] and c1['q'] is None and c1['tip'] > 40, 'a saved Auto Filter (no q) shows Hi-Fi Off and runs its old biquads', c1)
    R("(()=>{const D=document.querySelector(`#fxin .dev[data-id='${__fa.id}']`),s=D.querySelector('select[data-x=pre]');if(s){s.value='acid';s.dispatchEvent(new Event('change',{bubbles:true}))}})()"); pg.wait_for_timeout(500)
    ok(J("__fa.p.q??null") is None and J("__fa.p.pre") == 'acid', 'picking a preset keeps Hi-Fi off')
    R("(()=>{const D=document.querySelector(`#fxin .dev[data-id='${__fa.id}']`),s=D.querySelector('select[data-x=q]');s.value='clean';s.dispatchEvent(new Event('change',{bubbles:true}))})()"); pg.wait_for_timeout(900)
    c2 = J("(()=>{const X=NODES.get(__t2.id).fxm.get(__fa.id);return{q:__fa.p.q,snd:!!(X.snd&&X.snd.node),model:X.snd&&X.snd.o.model,mods:X.snd&&X.snd.mods.length,b1:typeof X.b1.getFrequencyResponse,dry:X._v1.dry.gain.value,wet:X._v1.wet.gain.value}})()")
    ok(c2['q'] == 'clean' and c2['snd'] and c2['model'] == 4 and c2['mods'] == 2 and c2['dry'] == 0 and c2['wet'] == 0, 'switching Hi-Fi on runs it through the processor (the Acid preset: Low-pass 24 as SVF 24), LFO and envelope wired to the cutoff', c2)
    shot(J('__fa.id'), 'snd1_autofilter_clean_dark.png')
    R("(()=>{const D=document.querySelector(`#fxin .dev[data-id='${__fa.id}']`),s=D.querySelector('select[data-x=q]');s.value='classic';s.dispatchEvent(new Event('change',{bubbles:true}))})()"); pg.wait_for_timeout(600)
    c3 = J("(()=>{const X=NODES.get(__t2.id).fxm.get(__fa.id);return{snd:!!X.snd,dry:X._v1.dry.gain.value,wet:X._v1.wet.gain.value}})()")
    ok(not c3['snd'] and c3['wet'] == 1, 'and Hi-Fi off again', c3)
    R("UI.lite=true;UI.liteMan=true;applyLite();renderFx();0"); pg.wait_for_timeout(1200)
    ok(J("document.body.classList.contains('lite')"), 'Light mode on for the last screenshot')
    shot(fid2, 'snd1_filter_light.png')
    ok(not errs, 'no console errors', errs[:5])
    b.close()
print(f'{N[1]} of {N[0]} checks passed')
sys.exit(1 if FAIL else 0)
