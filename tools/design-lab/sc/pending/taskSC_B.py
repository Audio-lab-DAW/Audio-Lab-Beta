#!/usr/bin/env python3
"""Task SC-B (science look, lane G): About as the random set Y1: the Earth 3 in 5 (AB1's corner and sheet), the orbit corner 1 in 5,
the field arcs 1 in 5, chosen at each opening; Earth only in Light mode and with Science drawings off.
   python3 tools/ui-tests/taskSC_B.py [index.html] [shots-dir]"""
# for: task SC-B (lane G)
import sys, json, os
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../../../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
SH = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != '-' else None
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)
# pixels of the background canvas that are brighter than the ground, outside the veiled text column (left and right thirds)
LIT = r"""(()=>{const c=document.querySelector('#splash .abBg');if(!c)return -1;const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data,W=c.width;let s=0;for(let i=0;i<d.length;i+=4*7){const x=(i/4)%W;if(x>W*.3&&x<W*.7)continue;if(d[i]+d[i+1]+d[i+2]>110)s++}return s})()"""

with sync_playwright() as p:
    src = open(F, encoding='utf-8').read(); logs = []
    ctx = p.chromium.launch(args=ARGS).new_context(viewport={'width': 1400, 'height': 900}, device_scale_factor=2); pg = ctx.new_page()
    pg.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'icons.json' not in m.text else None)
    pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=src) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    J = lambda c: (lambda v: None if v is None else json.loads(v))(R("JSON.stringify(" + c + ")"))
    R("pmSetOn(false)"); R("UI.lkMotion='ambient';lkApply()"); pg.wait_for_timeout(500)
    print('version', R("VERSION"))
    ok(J("AB1.KINDS") == ['corner', 'sheet', 'orbit', 'arcs'], 'About knows four pictures', J("AB1.KINDS"))
    # ---------- the odds ----------
    c = J("(()=>{const n={corner:0,sheet:0,orbit:0,arcs:0};for(let i=0;i<20000;i++)n[AB1.pick()]++;return n})()")
    e = (c['corner'] + c['sheet']) / 200.0; o = c['orbit'] / 200.0; a = c['arcs'] / 200.0
    ok(58 <= e <= 62 and 18.5 <= o <= 21.5 and 18.5 <= a <= 21.5 and 28 <= c['corner'] / 200.0 <= 32, 'Y1: Earth 3 in 5 (corner and sheet even), orbit corner 1 in 5, field arcs 1 in 5 (20,000 picks)', c)
    seq = []
    for i in range(30):
        R('showAbout()'); pg.wait_for_timeout(40); seq.append(R("document.getElementById('splash').dataset.abp")); R('hideSplash()'); pg.wait_for_timeout(400 if i % 10 == 0 else 40)
    ok(len(set(seq)) >= 3, 'chosen at each opening, no restart needed (30 openings)', {k: seq.count(k) for k in set(seq)})
    pg.wait_for_timeout(800)
    # ---------- each new picture ----------
    for k in ('orbit', 'arcs'):
        R(f'AB1.force("{k}");showAbout()'); pg.wait_for_timeout(1500)
        g = J("(()=>{const s=document.getElementById('splash');return{k:s&&s.dataset.abp,ab2:s&&s.classList.contains('ab2'),atom:!!s.querySelector('.abAtom'),vals:s.querySelectorAll('.abI .v').length}})()")
        ok(g['k'] == k and g['ab2'] and g['atom'] and g['vals'] == 8, f'{k}: shown in the same About window (atom, 8 values)', g)
        lit = R(LIT); ok(lit > 200, f'{k}: the drawing is there beside the text', lit)
        n0 = J("AB1.n.bg"); pg.wait_for_timeout(1000); n1 = J("AB1.n.bg")
        ok(18 <= n1 - n0 <= 32, f'{k}: moving at 30 pictures a second at most while open', n1 - n0)
        if SH: os.makedirs(SH, exist_ok=True); pg.screenshot(path=os.path.join(SH, f'scB_{k}.png'))
        # still with Motion other than Ambient
        R("UI.lkMotion='trans';lkApply()"); pg.wait_for_timeout(400); n0 = J("AB1.n.bg"); pg.wait_for_timeout(900)
        ok(J("AB1.n.bg") == n0 and R(LIT) > 200, f'{k}: one still picture when Motion is not Ambient', J("AB1.n.bg") - n0)
        R("UI.lkMotion='ambient';lkApply()")
        R('hideSplash()'); pg.wait_for_timeout(900); n0 = J("AB1.n.bg"); pg.wait_for_timeout(800)
        ok(J("AB1.n.bg") == n0 and not J("AB1.running()"), f'{k}: closed, nothing is drawn')
    R('AB1.force(null)')
    # ---------- Light mode and the setting: Earth only ----------
    R("document.body.classList.add('lite')")
    c = J("(()=>{const n={corner:0,sheet:0,orbit:0,arcs:0};for(let i=0;i<4000;i++)n[AB1.pick()]++;return n})()")
    ok(c['orbit'] == 0 and c['arcs'] == 0 and 45 <= c['corner'] / 40.0 <= 55, 'Light mode: the Earth only (W14 off), corner and sheet even', c)
    R("document.body.classList.remove('lite')"); R("UI.scOn=false")
    c = J("(()=>{const n={corner:0,sheet:0,orbit:0,arcs:0};for(let i=0;i<4000;i++)n[AB1.pick()]++;return n})()")
    ok(c['orbit'] == 0 and c['arcs'] == 0 and 45 <= c['corner'] / 40.0 <= 55, 'Science drawings off: the Earth only', c)
    R("UI.scOn=true")
    # ---------- the Earth pictures are unchanged ----------
    for k in ('corner', 'sheet'):
        R(f'AB1.force("{k}");showAbout()'); pg.wait_for_timeout(1000)
        ok(R("document.getElementById('splash').dataset.abp") == k and R(LIT) > 200, f'{k}: the Earth as before')
        if SH and k == 'corner': pg.screenshot(path=os.path.join(SH, 'scB_corner.png'))
        R('hideSplash()'); pg.wait_for_timeout(700)
    R('AB1.force(null)')
    ok(J("[AB1.bench('orbit',780,720,20),AB1.bench('arcs',780,720,20)]") is not None, 'bench runs for the new pictures', J("[AB1.bench('orbit',780,720,20),AB1.bench('arcs',780,720,20)].map(v=>v.toFixed(2)+' ms')"))
    ok(not logs, 'no console errors', logs[:5])
print('%d checks, %d failed' % (N[0], len(FAIL)))
sys.exit(1 if FAIL else 0)
