#!/usr/bin/env python3
"""Task OV1 (lane F, overlays): shared overlay tokens and timing; the right-click menu fades in (90 ms) and out (60 ms).
   python3 tools/ui-tests/taskOV1.py [index.html] [shots-dir]
At the user's size (2194 x 1139 CSS px at 1.75x) with Fractals: Dark (glass), Light mode, the Solid glass level, reduced motion and
Motion 'Signal only'. Keyboard paths, focus, menu entries still running their commands, open times. SwiftShader: correctness only."""
import sys, os, json
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else ''
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)

def load(p, logs, reduced=False):
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': 2194, 'height': 1139}, device_scale_factor=1.75, reduced_motion='reduce' if reduced else 'no-preference'); pg = ctx.new_page()
    pg.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text else None)
    pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    R("pmSetOn(false)"); R("openDemoFractals()"); pg.wait_for_timeout(6000)
    return b, pg, R

TIME = r"""async (code)=>{const out=[];const CL=()=>AudioLab.run("closeMenu()");for(let i=0;i<9;i++){CL();
 await new Promise(r=>setTimeout(r,120));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const t0=performance.now();AudioLab.run(code);const t1=performance.now();
 await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));out.push([t1-t0,performance.now()-t0])}
 CL();out.sort((a,b)=>a[0]-b[0]);return out[4]}"""
TM = "trackMenu(420,300,S.tracks[1],4)"
ST = "(()=>{const m=document.getElementById('ctxm'),c=getComputedStyle(m);return{h:m.hidden,out:m.classList.contains('ovout'),inert:m.inert,disp:c.display,op:+c.opacity,an:c.animationName,ad:c.animationDuration,pe:c.pointerEvents,bf:c.backdropFilter||c.webkitBackdropFilter||'none',shown:glfShown(m),act:document.activeElement&&document.activeElement.closest&&!!document.activeElement.closest('#ctxm')}})()"

with sync_playwright() as p:
    logs = []
    b, pg, R = load(p, logs)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    print('version', R("VERSION"))
    # tokens
    tk = J("(()=>{const c=getComputedStyle(document.documentElement),g=k=>c.getPropertyValue(k).trim();return{row:g('--ov-row'),r:g('--ov-r'),tip:g('--ov-r-tip'),card:g('--ov-r-card'),pal:g('--ov-r-pal'),inn:g('--ov-in'),out:g('--ov-out'),sh:g('--ov-sheet'),mo:getComputedStyle(document.body).getPropertyValue('--ov-mo').trim(),amb:g('--ov-amb'),hi:g('--ov-hi'),lab:g('--ov-lab')}})()")
    ok(tk['row'] == '26px' and tk['r'] == '10px' and tk['tip'] == '8px' and tk['card'] == '9px' and tk['pal'] == '12px', 'size tokens: row 26, menu 10, callout 8, card 9, palette 12', tk)
    ok(tk['inn'] == '90ms' and tk['out'] == '60ms' and tk['sh'] == '140ms' and tk['mo'] == '1', 'motion tokens: 90 ms in, 60 ms out, 140 ms sheet, motion on', tk)
    ok('JetBrains Mono' in tk['lab'] and tk['amb'] != '' and tk['hi'] != '', 'label, amber and focus tokens', tk)
    lk = J("{ov:LOOK.ov,same:LOOK.ov===ovLook(),i:ovMs('in'),o:ovMs('out'),s:ovMs('sheet'),td:ovMs('tipDelay'),st:ovStill()}")
    ok(lk['same'] and lk['ov']['row'] == 26 and lk['ov']['cards'] == 3 and lk['i'] == 90 and lk['o'] == 60 and lk['s'] == 140 and lk['td'] == 500 and not lk['st'], 'LOOK.ov holds the same numbers; ovMs gives them', lk)
    # open: the fade in
    R(TM); s = J(ST)
    ok(not s['h'] and s['an'] == 'ovIn' and s['ad'] == '0.09s' and s['bf'] == 'none', 'track menu opens with the 90 ms fade, no backdrop-filter', s)
    ok(s['act'], 'focus is inside the menu (first entry)', s)
    pg.wait_for_timeout(200)
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov1_dark_menu.png'))
    # Escape: closed at once for the code, fades for 60 ms, focus not kept in the menu
    pg.keyboard.press('Escape'); s = J(ST)
    ok(s['h'] and s['out'] and s['inert'] and s['disp'] == 'flex' and s['pe'] == 'none' and not s['act'], 'Esc: hidden at once, focus out, still drawn while it fades (inert, no pointer)', s)
    ok(s['shown'], 'the glass engine keeps the face during the fade-out', s)
    pg.wait_for_timeout(160); s = J(ST)
    ok(s['h'] and not s['out'] and not s['inert'] and s['disp'] == 'none' and not s['shown'], 'after the fade: gone, glass face gone', s)
    # re-open during the fade-out
    R(TM); R("closeMenu()"); s0 = J(ST); R(TM); s = J(ST)
    ok(s0['out'] and not s0['act'], 'closing from code: focus leaves the menu at once', s0)
    ok(not s['h'] and not s['out'] and not s['inert'] and s['pe'] != 'none', 'opening again during the fade-out shows the menu at once, clickable', s)
    R("closeMenu()"); pg.wait_for_timeout(150)
    # a right-click on a track header, keyboard: arrow / Tab and Enter still run the command
    hb = J("(()=>{const h=document.querySelectorAll('#hdrin .hdr')[1]||document.querySelector('.hdr');const r=h.getBoundingClientRect();return{x:r.left+r.width*.5,y:r.top+r.height*.5}})()")
    pg.mouse.click(hb['x'], hb['y'], button='right'); pg.wait_for_timeout(150)
    lab = J("(()=>{const b=document.activeElement;return b&&b.closest('#ctxm')?b.textContent:''})()")
    ok(not J("ctxm.hidden") and lab != '', 'right-click on a track header opens its menu with the first entry focused', lab[:40])
    m0 = J("S.tracks[1].mute")
    R("(()=>{const b=[...ctxm.querySelectorAll('button[data-i]')].find(b=>/^Mute track|^Unmute track/.test(b.textContent.trim()));b.focus()})()")
    pg.keyboard.press('Enter'); pg.wait_for_timeout(150)
    ok(J("S.tracks[1].mute") != m0 and J("ctxm.hidden"), 'Enter on Mute track runs it and closes the menu', [m0, J("S.tracks[1].mute")])
    R("S.tracks[1].mute=%s;dirty=true" % ('true' if m0 else 'false'))
    # every entry of the track and clip menus still runs its command (each act is called once, through a click; state is restored)
    cnt = J(r"""(()=>{const S0=JSON.stringify(S.tracks.map(t=>[t.name,t.clips.length]));let n=0,ran=0,bad=[];
      for(const mk of ['track','clip']){const go=()=>{if(mk==='track')trackMenu(420,300,S.tracks[1],4);else{const t=S.tracks[1];clipMenu(700,320,t,t.clips[0])}};go();
        const L=MENU.map((it,i)=>[it,i]).filter(([it])=>it&&it!=='-'&&!it.head&&!it.chips&&!it.swatches&&!it.dis&&typeof it.act==='function');
        for(const[it,i] of L){go();const real=MENU[i];let hit=0;const a=real.act;real.act=function(){hit=1};const btn=ctxm.querySelector('button[data-i="'+i+'"]');if(btn)btn.click();real.act=a;n++;if(hit)ran++;else bad.push(mk+':'+(real.label||i))}}
      closeMenu();return{n,ran,bad}})()""")
    ok(cnt['n'] > 20 and cnt['ran'] == cnt['n'], 'every enabled track and clip menu entry reaches its command through a click', cnt)
    pg.wait_for_timeout(150)
    # three-column menus close without the fade (their layout changes on close)
    R(TM + ";ctxm.classList.add('mcols')"); R("closeMenu()"); s = J(ST)
    ok(s['h'] and not s['out'] and s['disp'] == 'none', 'a three-column menu closes at once', s)
    # open times (JS of the open call; today 6.9 ms in v0.228 at 1600x1000) and click to second frame
    t = pg.evaluate(TIME, TM); c = pg.evaluate(TIME, "(()=>{const t=S.tracks[1];clipMenu(700,320,t,t.clips[0])})()")
    print('open times: track menu', [round(x, 2) for x in t], 'clip menu', [round(x, 2) for x in c])
    ok(t[0] < 6.9, 'track menu open call under 6.9 ms of JS (today in v0.228); frames printed only (software renderer, load-dependent)', t)
    pg.wait_for_timeout(150)
    # Light mode
    R("pmSetOn(true)"); pg.wait_for_timeout(1200); R(TM); s = J(ST)
    ok(not s['h'] and s['an'] == 'none' and s['op'] == 1, 'Light mode: the menu opens at once, no animation (Light mode has none)', s)
    pg.wait_for_timeout(200)
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov1_light_menu.png'))
    R("closeMenu()"); s = J(ST); ok(s['h'] and not s['out'] and s['disp'] == 'none', 'Light mode: it closes at once', s); pg.wait_for_timeout(150)
    R("pmSetOn(false)"); pg.wait_for_timeout(1000)
    # Solid glass level
    R("(()=>{UI.gl={...(UI.gl||{}),lv:'solid'};gleApply()})()"); pg.wait_for_timeout(800); R(TM); pg.wait_for_timeout(150); s = J(ST)
    ok(not s['h'] and s['bf'] == 'none', 'Solid level: the menu opens, no backdrop-filter', s)
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov1_solid_menu.png'))
    R("closeMenu()"); pg.wait_for_timeout(150); R("(()=>{UI.gl={...(UI.gl||{}),lv:'glass'};gleApply()})()"); pg.wait_for_timeout(600)
    # Motion 'Signal only': no transitions
    R("SETT.set('motion','signal')"); pg.wait_for_timeout(200); R(TM); s = J(ST)
    ok(s['ad'] == '0s' and J("ovStill()") and J("ovMs('in')") == 0, "Motion 'Signal only': no fade in", s)
    R("closeMenu()"); s = J(ST); ok(s['h'] and not s['out'] and s['disp'] == 'none', "Motion 'Signal only': closes at once", s)
    R("SETT.set('motion','ambient')"); pg.wait_for_timeout(200)
    ok(not logs, 'no console errors (normal motion)', logs[:5])
    b.close()
    # reduced motion from the system
    logs2 = []
    b, pg, R = load(p, logs2, reduced=True)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    R(TM); s = J(ST)
    ok(s['ad'] == '0s' and J("ovStill()") and J("ovMs('out')") == 0 and J("ovMs('drain')") == 6000, 'reduced motion: no fade in (times that are not motion stay)', s)
    pg.keyboard.press('Escape'); s = J(ST)
    ok(s['h'] and not s['out'] and s['disp'] == 'none', 'reduced motion: Esc closes at once', s)
    ok(not logs2, 'no console errors (reduced motion)', logs2[:5])
    b.close()
    print(f'{N[0] - len(FAIL)} of {N[0]} checks passed'); sys.exit(1 if FAIL else 0)
