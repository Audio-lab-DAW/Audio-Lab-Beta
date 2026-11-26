#!/usr/bin/env python3
"""Headless checks for tools/glass-lab/devices-lab.html (display-first devices on the glass engine, task D4 lab).
Run: python3 tools/glass-lab/devices_lab.py [out dir for screenshots]
The cloud machine has no GPU (SwiftShader), so only behaviour and the engine's counters are checked; frame rates mean nothing."""
import os, sys, json
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = sys.argv[1] if len(sys.argv) > 1 else None
ARGS = ["--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
RES, LOGS = [], []
def ok(name, cond, detail=''):
    RES.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + (('   ' + str(detail)) if detail != '' else ''), flush=True)
def shot(pg, n):
    if OUT: os.makedirs(OUT, exist_ok=True); pg.screenshot(path=os.path.join(OUT, n + '.png'))
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS); pg = b.new_page(viewport={'width': 1640, 'height': 900})
    pg.on('console', lambda m: LOGS.append(m.type + ': ' + m.text) if (m.type == 'error' and 'ERR_FAILED' not in m.text) or (m.type == 'warning' and 'ReadPixels' not in m.text and 'willReadFrequently' not in m.text) else None)
    pg.on('pageerror', lambda e: LOGS.append('pageerror: ' + str(e)))
    pg.route('**/fonts.googleapis.com/**', lambda r: r.abort())
    pg.goto('file://' + os.path.join(HERE, 'devices-lab.html')); pg.wait_for_timeout(2500)
    ev = pg.evaluate
    ok('engine runs in GL mode', ev("LAB.eng&&LAB.eng.mode") == 'gl', ev("LAB.eng&&LAB.eng.reason"))
    st = lambda: ev("LAB.DVS.map(d=>d.dataset.l+'/'+d.dataset.pref).join(' ')")
    ok('devices start as picked', st() == 'DD2/DD4 DD2/DD4 DD3/DD3 DD4/DD4 DD4/DD4 DD2/DD4', st())
    def per_second(ms=1200):
        a = ev("LAB.stat()"); pg.wait_for_timeout(ms); c = ev("LAB.stat()"); return {k: (c[k] - a[k]) * 1000 / ms for k in ('flatUploads', 'flatPyramids', 'draws')}
    pg.mouse.move(5, 5); pg.wait_for_timeout(900)
    r = per_second(); ok('still displays, nothing moving: no uploads, no blur rebuilds, no face redraws', r['flatUploads'] == 0 and r['flatPyramids'] == 0 and r['draws'] == 0, r)
    n = ev("LAB.eng.info&&document.querySelectorAll('#scr .g').length"); shot(pg, 'lab_picked')
    # glass faces are drawn: a pixel in the middle of the Psy Bass rail on the engine canvas is opaque
    px = ev("""(()=>{const g=LAB.eng.gl,e=document.querySelector('#scr .dv .rail').getBoundingClientRect(),R=document.getElementById('panel').getBoundingClientRect(),d=g.drawingBufferWidth/R.width;
      LAB.eng.debug.draw();const b=new Uint8Array(4);g.readPixels(Math.round((e.left-R.left+e.width/2)*d),g.drawingBufferHeight-Math.round((e.top-R.top+e.height/2)*d),1,1,g.RGBA,g.UNSIGNED_BYTE,b);
      const o=new Uint8Array(4);g.readPixels(Math.round((e.left-R.left-60)*d),g.drawingBufferHeight-Math.round((e.top-R.top+e.height/2)*d),1,1,g.RGBA,g.UNSIGNED_BYTE,o);return [[...b],[...o]]})()""")
    ok('the rail is a glass face on the engine canvas, the display beside it is left clear', px[0][3] > 240 and px[1][3] == 0, px)
    css = ev("getComputedStyle(document.querySelector('#scr .rail')).backdropFilter+'|'+getComputedStyle(document.querySelector('#scr .rail')).backgroundColor")
    ok('no backdrop-filter and no CSS fill on glass in GL mode', css == 'none|rgba(0, 0, 0, 0)', css)
    # states
    for name, v in (('Rail open', 'DD2'), ('Hover reveal', 'DD4'), ('On the picture', 'DD3')):
        ev("LAB.set('all','%s')" % v); pg.mouse.move(5, 5); pg.wait_for_timeout(900)
        panels = ev("(()=>{let n=0;for(const e of document.querySelectorAll('#scr .g')){const q=e.getBoundingClientRect();if(q.width&&+getComputedStyle(e).opacity>0)n++}return n})()")
        r = per_second(900); ok('%s on all six, still: no uploads, no rebuilds (%d glass panels shown)' % (name, panels), r['flatUploads'] == 0 and r['flatPyramids'] == 0 and r['draws'] == 0, r); shot(pg, 'lab_' + v)
    # hover reveal: the dock appears under the mouse, and goes again
    ev("LAB.set('all','DD4')"); pg.wait_for_timeout(600)
    box = ev("(()=>{const r=LAB.DVS[0].querySelector('.dp').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()")
    op0 = ev("+getComputedStyle(LAB.DVS[0].querySelector('.ly:not([hidden]) .dock')).opacity"); pg.mouse.move(box[0], box[1]); pg.wait_for_timeout(700)
    op1 = ev("+getComputedStyle(LAB.DVS[0].querySelector('.ly:not([hidden]) .dock')).opacity"); shot(pg, 'lab_hover')
    pxd = ev("""(()=>{const g=LAB.eng.gl,e=LAB.DVS[0].querySelector('.ly:not([hidden]) .dock').getBoundingClientRect(),R=document.getElementById('panel').getBoundingClientRect(),d=g.drawingBufferWidth/R.width;LAB.eng.debug.draw();const b=new Uint8Array(4);
      g.readPixels(Math.round((e.left-R.left+e.width/2)*d),g.drawingBufferHeight-Math.round((e.top-R.top+e.height/2)*d),1,1,g.RGBA,g.UNSIGNED_BYTE,b);return [...b]})()""")
    pg.mouse.move(5, 5); pg.wait_for_timeout(700); op2 = ev("+getComputedStyle(LAB.DVS[0].querySelector('.ly:not([hidden]) .dock')).opacity")
    ok('hover reveal: dock hidden, shown under the mouse as a glass face, hidden again', op0 == 0 and op1 == 1 and op2 == 0 and pxd[3] > 240, [op0, op1, op2, pxd])
    r = per_second(900); ok('after the hover: idle again', r['flatUploads'] == 0 and r['flatPyramids'] == 0 and r['draws'] == 0, r)
    # eye and its right-click menu
    ev("LAB.set('all','mine')"); pg.wait_for_timeout(500)
    eye = "#scr .dv:nth-child(%d) .ly:not([hidden]) [data-eye]"
    pg.click(eye % 1); s1 = st().split()[0]; pg.click(eye % 1, button='right'); pg.wait_for_timeout(300); shot(pg, 'lab_menu')
    menu_panel = ev("!!document.querySelector('#scr .menu')"); pg.click('#scr .menu [data-pref=DD3]'); s2 = st().split()[0]
    pg.click(eye % 1); s3 = st().split()[0]; pg.click(eye % 1); s4 = st().split()[0]
    ok('eye closes the rail to hover reveal; menu switches to on the picture; rail open hides it; closing brings it back', [s1, s2, s3, s4] == ['DD4/DD4', 'DD3/DD3', 'DD2/DD3', 'DD3/DD3'] and menu_panel, [s1, s2, s3, s4])
    # live displays and the refresh cap
    ev("LAB.set('all','DD2')"); ev("LAB.set('live','1')"); pg.mouse.move(5, 5); pg.wait_for_timeout(800)
    vis = ev("LAB.DVS.filter(d=>{const r=d.getBoundingClientRect();return r.right>0&&r.left<innerWidth}).length")
    fr = lambda: ev("new Promise(r=>{let n=0,t=performance.now();const f=()=>{n++;performance.now()-t<1000?requestAnimationFrame(f):r(n)};requestAnimationFrame(f)})")
    hi = per_second(1500); f = fr(); ok('live, high: every visible display uploaded each frame, one blur rebuild per frame', hi['flatPyramids'] > 0 and abs(hi['flatUploads'] / hi['flatPyramids'] - vis) < 0.6, dict(hi, visible=vis, frames=f))
    ev("LAB.set('q','1')"); pg.wait_for_timeout(500); lo = per_second(2000); ok('live, low: blur rebuilds capped at 30 per second', lo['flatPyramids'] <= 31, lo); shot(pg, 'lab_live')
    ev("LAB.set('all','DD4')"); pg.mouse.move(5, 5); pg.wait_for_timeout(800); ev("LAB.set('q','3')"); pg.wait_for_timeout(300)
    # other glass modes
    ev("LAB.set('live','0')"); ev("LAB.set('all','mine')"); ev("LAB.set('glass','css')"); pg.wait_for_timeout(500)
    ok('Browser blur: engine canvas hidden, CSS glass back', ev("getComputedStyle(document.getElementById('eng')).display") == 'none' and 'blur' in ev("getComputedStyle(document.querySelector('#scr .rail')).backdropFilter")); shot(pg, 'lab_css')
    ev("LAB.set('glass','solid')"); pg.wait_for_timeout(300); ok('Solid: no blur', ev("getComputedStyle(document.querySelector('#scr .rail')).backdropFilter") == 'none'); shot(pg, 'lab_solid')
    ev("LAB.set('glass','gl')"); pg.wait_for_timeout(600)
    # scrolling the devices panel keeps glass on its controls
    ev("document.getElementById('scr').scrollLeft=700"); pg.wait_for_timeout(700)
    al = ev("""(()=>{const g=LAB.eng.gl,R=document.getElementById('panel').getBoundingClientRect(),d=g.drawingBufferWidth/R.width;LAB.eng.debug.draw();let okc=0,n=0;
      for(const e of document.querySelectorAll('#scr .g')){const q=e.getBoundingClientRect();if(!q.width||+getComputedStyle(e).opacity===0||q.left<R.left+4||q.right>R.right-4)continue;n++;const b=new Uint8Array(4);
        g.readPixels(Math.round((q.left-R.left+q.width/2)*d),g.drawingBufferHeight-Math.round((q.top-R.top+q.height/2)*d),1,1,g.RGBA,g.UNSIGNED_BYTE,b);if(b[3]>240)okc++}return [okc,n]})()""")
    ok('after scrolling the panel every visible control still has its glass face', al[0] == al[1] and al[1] >= 3, al); shot(pg, 'lab_scrolled')
    ok('no console errors or warnings', not LOGS, LOGS[:4])
    b.close()
print('%d of %d passed' % (sum(RES), len(RES))); sys.exit(0 if all(RES) else 1)
