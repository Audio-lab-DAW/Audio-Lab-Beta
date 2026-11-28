#!/usr/bin/env python3
"""Task SC-A (science look, lane G): the shared drawing module SCI, its one timer and the Science drawings setting.
   python3 tools/ui-tests/taskSC_A.py [index.html] [shots-dir]
No place uses a view yet, so the test makes its own views in a test box and checks the rules: at most 30 pictures a second,
nothing drawn while hidden, still with Motion other than Ambient, nothing in Light mode or with the setting off, no cost without views."""
import sys, json, os
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
SH = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != '-' else None
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)

# a test box with one canvas; the paint function uses every drawing
MK = r"""(o)=>{let b=document.getElementById('sciT');if(!b){b=document.createElement('div');b.id='sciT';b.style.cssText='position:fixed;left:40px;top:120px;width:420px;height:260px;z-index:99999;background:#090b10;border:1px solid #333';document.body.appendChild(b)}
 const c=document.createElement('canvas');c.className='sciv';c.dataset.k=o.name;b.appendChild(c);
 const sp=SCI.D.spec(120,32);for(let i=0;i<120;i++){const m=new Float32Array(32);for(let j=0;j<32;j++)m[j]=Math.max(0,Math.sin(i*.2+j*.3))*.8*(1-j/40);sp.push(m)}
 const D=SCI.D;window.__sci=window.__sci||{};
 window.__sci[o.name]=SCI.view({cv:c,place:o.place,move:o.move,paint:(g,w,h,t,k)=>{D.orbits(g,w*.3,h*.5,60,t,k,{ticks:1,cross:1,names:['4 BARS','8','16'],core:1});D.corner(g,w+4,h+4,180,k,t);D.field(g,w*.72,h*.5,90,Math.PI/2,t,k,{L:[.3,.5,.8,1.2],a:.26});
   D.lissa(g,w*.72,h*.25,40,30,3,2,t*.14,k,{dot:t*.35});D.harm(g,w*.55,h*.8,150,30,t,k);D.comb(g,10,h-50,180,40,110,1400,k,{label:'F0 110.00 HZ = A2'});sp.draw(g,w-130,8,120,32,k,.7);D.lab(g,'TEMPO 145.00 BPM',10,14,k)}});
 return !!window.__sci[o.name]}"""
PX = r"""(n)=>{const c=document.querySelector('#sciT canvas[data-k="'+n+'"]');if(!c||!c.width)return -1;const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let s=0;for(let i=3;i<d.length;i+=4)if(d[i])s++;return s}"""

with sync_playwright() as p:
    src = open(F, encoding='utf-8').read(); logs = []
    ctx = p.chromium.launch(args=ARGS).new_context(viewport={'width': 1400, 'height': 860}, device_scale_factor=2); pg = ctx.new_page()
    pg.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'icons.json' not in m.text else None)
    pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=src) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    J = lambda c: (lambda v: None if v is None else json.loads(v))(R("JSON.stringify(" + c + ")"))
    E = lambda c, a=None: J('(' + c.strip() + ')(' + json.dumps(a) + ')')
    R("pmSetOn(false)"); R("openDemoFractals()"); pg.wait_for_timeout(5000)
    print('version', R("VERSION"))
    # ---------- the module and the picks ----------
    d = J("SCI.DEF")
    ok(d == {'W1': 'normal', 'W2': 'faint', 'W3': 'off', 'W4': 'faint', 'W5': 'normal', 'W6': 'normal', 'W7': 'normal', 'W8': 'normal', 'W9': 'faint', 'W10': 'faint', 'W11': 'faint', 'W12': 'faint', 'W13': 'faint', 'W14': 'off'}, "the user's picks W1 to W14 (W3 and W14 off)", d)
    ok(J("[SCI.level('W1'),SCI.level('W2'),SCI.level('W3'),SCI.level('W14'),SCI.level('nope')]") == [1, 0.45, 0, 0, 0], 'levels: normal 1, faint 0.45, off and unknown 0')
    ok(J("Object.keys(SCI.D).sort()") == sorted(['dot', 'lab', 'orbits', 'corner', 'field', 'lissa', 'harm', 'comb', 'spec']), 'the drawings: orbits, corner, field, lissa, harm, comb, spec, lab, dot')
    ok(J("typeof window.SCI_HOOKS.view==='function'&&typeof SCI_HOOKS.level==='function'"), 'hooks SCI_HOOKS.view and .level for other lanes')
    # ---------- no cost without views ----------
    f0 = J("[SCI.views(),SCI.running(),SCI.watching(),SCI.frames()]"); pg.wait_for_timeout(1500); f1 = J("[SCI.views(),SCI.running(),SCI.watching(),SCI.frames()]")
    ok(f0 == [0, False, False, 0] and f1 == f0, 'no view: no timer, no observer, no frames', [f0, f1])
    # ---------- the setting ----------
    st = J("(()=>{const c=document.getElementById('scOnChk'),r=STX.get('scOn');return{el:!!c,chk:c&&c.checked,page:c&&c.closest('#setBody section[data-page]')?c.closest('#setBody section[data-page]').dataset.page:null,row:!!r,tip:c&&c.closest('.row').title,cal:!!document.getElementById('mdCalChk')&&document.getElementById('mdCalChk').closest('.row').nextElementSibling===c.closest('.row')}})()")
    ok(st['el'] and st['chk'] and st['row'] and st['cal'], 'Science drawings: a checkbox, on by default, under Caliper while dragging, in the settings table', st)
    ok(st['page'] == 'appearance', 'it sits on the Appearance page (Interface size, Density and motion)', st['page'])
    ok(st['tip'] and '—' not in st['tip'] and 'Light mode' in st['tip'], 'its tooltip in plain language, no em dash', st['tip'])
    # ---------- a moving view ----------
    R("UI.lkMotion='ambient';lkApply()")
    ok(E(MK, {'name': 'mv', 'place': 'W1', 'move': True}), 'a moving view is made')
    pg.wait_for_timeout(400); a = J("SCI.frames()"); pg.wait_for_timeout(2000); b = J("SCI.frames()")
    fps = (b - a) / 2.0
    ok(4 <= fps <= 31.5, 'a moving view is painted at most 30 times a second', '%.1f a second' % fps)
    ok(J("SCI.running()") and J("SCI.watching()"), 'the one timer runs and Light mode and Motion are watched while a view exists')
    px = E(PX, 'mv'); ok(px > 1500, 'the drawing is there (pixels painted)', px)
    sz = J("(()=>{const c=document.querySelector('#sciT canvas'),z=c.getBoundingClientRect().width/c.clientWidth,k=Math.min(2,devicePixelRatio*z);return[c.width,c.height,Math.round(c.clientWidth*k),Math.round(c.clientHeight*k),k]})()")
    ok(sz[0] == sz[2] and sz[1] == sz[3] and sz[4] == 2, 'the canvas is sized in device pixels (up to 2x, with the interface scale)', sz)
    if SH:
        os.makedirs(SH, exist_ok=True); pg.screenshot(path=os.path.join(SH, 'scA_normal.png'), clip={'x': 36, 'y': 116, 'width': 428, 'height': 268})
    # hidden: nothing drawn
    E("()=>{document.getElementById('sciT').style.display='none'}"); pg.wait_for_timeout(300); a = J("SCI.frames()"); pg.wait_for_timeout(1500); b = J("SCI.frames()")
    ok(b == a and not J("SCI.running()"), 'hidden: no picture is drawn and the timer stops', [a, b])
    E("()=>{document.getElementById('sciT').style.display=''}"); R("__sci.mv.wake()"); pg.wait_for_timeout(700)
    ok(J("SCI.frames()") > b and J("SCI.running()"), 'shown again with wake(): it moves again')
    # faint: no labels, weaker lines
    R("UI.scW={W1:'faint'};SCI.refresh()"); pg.wait_for_timeout(300); pf = E(PX, 'mv')
    ok(J("SCI.level('W1')") == 0.45 and 0 < pf, 'UI.scW can set one place to faint', pf)
    if SH: pg.screenshot(path=os.path.join(SH, 'scA_faint.png'), clip={'x': 36, 'y': 116, 'width': 428, 'height': 268})
    R("delete UI.scW;SCI.refresh()")
    # Motion other than Ambient: one still picture
    R("UI.lkMotion='trans';lkApply()"); pg.wait_for_timeout(400); a = J("SCI.frames()"); pg.wait_for_timeout(1500); b = J("SCI.frames()")
    ok(b == a and not J("SCI.running()") and E(PX, 'mv') > 1500, 'Motion not Ambient: one still picture, no frames', [a, b])
    R("UI.lkMotion='ambient';lkApply()"); pg.wait_for_timeout(500)
    ok(J("SCI.running()"), 'Motion Ambient again: it moves again')
    # Light mode: nothing at all (W14 off)
    R("document.body.classList.add('lite')"); pg.wait_for_timeout(400); a = J("SCI.frames()"); pg.wait_for_timeout(1200); b = J("SCI.frames()")
    ok(b == a and not J("SCI.running()") and E(PX, 'mv') <= 0, 'Light mode: nothing drawn, no frames (W14 off)', [a, b, E(PX, 'mv')])
    R("document.body.classList.remove('lite')"); pg.wait_for_timeout(500)
    ok(E(PX, 'mv') > 1500 and J("SCI.running()"), 'out of Light mode: drawn and moving again')
    # the setting off: nothing anywhere
    R("openSettings('appearance')"); pg.wait_for_timeout(300)
    E("()=>{document.getElementById('sciT').style.zIndex='1'}")
    pg.click('#scOnChk'); pg.wait_for_timeout(700)
    ok(J("[UI.scOn,SCI.level('W1'),SCI.running()]") == [False, 0, False] and E(PX, 'mv') <= 0, 'Science drawings off: nothing drawn, no timer')
    if SH:
        r = J("(()=>{const b=document.getElementById('scOnChk').closest('.row').getBoundingClientRect();return[b.x,b.y,b.width,b.height]})()")
        pg.screenshot(path=os.path.join(SH, 'scA_setting.png'), clip={'x': max(0, r[0] - 20), 'y': max(0, r[1] - 120), 'width': 560, 'height': 200})
    pg.wait_for_timeout(500); ok(json.loads(R("localStorage.getItem('audiolab-ui')")).get('scOn') is False, 'the setting is stored')
    pg.click('#scOnChk'); pg.wait_for_timeout(500); R("closeSettings&&closeSettings()") if J("typeof closeSettings==='function'") else None
    ok(J("[UI.scOn,SCI.running()]") == [True, True], 'on again: moving again')
    # ---------- a still view (working surfaces) ----------
    R("__sci.mv.stop()")
    ok(E(MK, {'name': 'st', 'place': 'W4', 'move': False}), 'a still view is made')
    pg.wait_for_timeout(300); a = J("SCI.frames()"); pg.wait_for_timeout(1500); b = J("SCI.frames()")
    ok(b == a and not J("SCI.running()") and E(PX, 'st') > 500, 'a still view is drawn once and costs nothing afterwards', [a, b])
    E("()=>dispatchEvent(new Event('resize'))"); pg.wait_for_timeout(500)
    ok(J("SCI.frames()") == b + 1, 'a resize draws it once more', J("SCI.frames()") - b)
    R("__sci.st.stop()"); pg.wait_for_timeout(200)
    ok(J("[SCI.views(),SCI.running(),SCI.watching()]") == [0, False, False], 'all views stopped: no timer, no observer, no resize listener')
    # ---------- k = 0 draws nothing ----------
    z = J("(()=>{const c=document.createElement('canvas');c.width=200;c.height=200;const g=c.getContext('2d'),D=SCI.D;D.orbits(g,100,100,50,1,0,{ticks:1,cross:1});D.corner(g,0,0,100,0,1);D.field(g,100,100,80,0,1,0);D.lissa(g,100,100,40,40,3,2,0,0);D.harm(g,0,0,200,50,1,0);D.comb(g,0,0,200,50,100,1000,0);D.lab(g,'X',10,10,.45);const d=g.getImageData(0,0,200,200).data;let s=0;for(let i=3;i<d.length;i+=4)if(d[i])s++;return s})()")
    ok(z == 0, 'strength 0 draws nothing, labels only at normal', z)
    # ---------- playing is not touched ----------
    R("pos=0;start()"); pg.wait_for_timeout(1500); a = J("SCI.frames()"); pg.wait_for_timeout(1500)
    ok(J("SCI.frames()") == a and J("play.on"), 'playing: the module draws nothing (no place yet)'); R("stop()")
    ok(not logs, 'no console errors', logs[:5])
print('%d checks, %d failed' % (N[0], len(FAIL)))
sys.exit(1 if FAIL else 0)
