"""SND-R cost: 8 Bitcrushers with dither and jitter (and 8 plain Bitcrushers, no random), 20 s offline at 48 kHz, best of 5, old and new file alternately.
  python3 tools/engine-lab/snd/sndr_cost.py before.html after.html"""
import sys, json
from playwright.sync_api import sync_playwright
JS = r"""(async()=>{const sr=48000,L=sr*20,res={};for(const [nm,p] of [['rand',{bits:6,dith:60,jit:30,rate:3}],['plain',{bits:6,dith:0,jit:0,rate:3}]]){let best=1e9;
 for(let r=0;r<5;r++){const oc=new OfflineAudioContext(2,L,sr);await wlLoad(oc);const o=oc.createOscillator();o.frequency.value=220;
  for(let k=0;k<8;k++){const x=mkFxNode(oc,'crush');x.set(Object.assign(mkFx('crush').p,p));o.connect(x.in);x.out.connect(oc.destination)}
  o.start(0);const t0=performance.now();await oc.startRendering();best=Math.min(best,performance.now()-t0)}res[nm]=best}return res})()"""
out = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(); P = {}
    for k, f in (('before', sys.argv[1]), ('after', sys.argv[2])):
        src = open(f, encoding='utf-8').read(); pg = b.new_page()
        pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
        pg.route('https://app.test/**', (lambda s: lambda r: r.fulfill(body=s, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body=''))(src))
        pg.goto('https://app.test/', timeout=180000, wait_until='domcontentloaded'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(2000)
        P[k] = pg
    for rnd in range(3):
        for k, pg in P.items():
            r = pg.evaluate(JS)
            for n, v in r.items(): out.setdefault(k, {}).setdefault(n, []).append(v)
            print(k, r, flush=True)
    b.close()
print(json.dumps({k: {n: min(v) for n, v in d.items()} for k, d in out.items()}))
