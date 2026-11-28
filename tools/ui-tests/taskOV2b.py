#!/usr/bin/env python3
"""Task OV2b (lane F, overlays, pick R2): the project tab menu, the Quick actions (logo) menu and the device menu get command rows;
the restarts fold into one submenu. Every entry still reaches its command; keyboard paths; dark, Light mode, Solid, reduced motion.
   python3 tools/ui-tests/taskOV2b.py [index.html] [shots-dir]
At the user's size (2194 x 1139 CSS px at 1.75x) with Fractals. SwiftShader: open times for comparison only."""
import sys, os, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
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
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    R("pmSetOn(false)"); R("openDemoFractals()"); pg.wait_for_timeout(6000)
    return b, pg, R

ROW = "[...ctxm.querySelectorAll('.ovcrow button')].map(b=>[b.textContent.trim(),b.disabled])"
FOC = "(()=>{const a=document.activeElement;if(!a)return'';if(!ctxm.contains(a))return'OUT:'+(a.className||a.tagName);const l=a.querySelector('.mlab');return(a.getAttribute('aria-label')||(l?l.firstChild.textContent:a.textContent)).trim()})()"
# the menus, opened through their own callers
TAB = "tabMenu(PJ.cur,300,60)"
LOGO = "(()=>{const b=document.getElementById('bLogo'),r=b.getBoundingClientRect();b.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:r.left+5,clientY:r.top+5}))})()"
DEV = "(()=>{const t=S.tracks.find(t=>t.fx&&t.fx.length);selT=t.id;fxMenu(500,400,t,t.fx[0])})()"
# every enabled entry, command row and submenus included, reaches its command through a click (acts stubbed)
ALL = r"""(code=>{let n=0,ran=0,sub=0,bad=[];const go=()=>AudioLab.run(code);go();const top=MENU,L=[];
  top.forEach((it,i)=>{if(it&&it.kids)it.kids.forEach((k,j)=>{if(k&&k!=='-'&&!k.head&&!k.dis&&typeof k.act==='function')L.push([i,j])});else if(it&&it!=='-'&&!it.head&&!it.chips&&!it.swatches&&!it.dis&&typeof it.act==='function')L.push([i,-1])});
  for(const[i,j] of L){go();const t0=MENU;let real=t0[i];if(j>=0){ctxm.querySelector('button[data-i="'+i+'"]').click();if(MENU!==t0[i].kids){bad.push('submenu '+t0[i].label);continue}sub++;real=MENU[j]}
    let hit=0;const a=real.act;real.act=function(){hit=1};const btn=ctxm.querySelector('button[data-i="'+(j>=0?j:i)+'"]');if(btn)btn.click();real.act=a;n++;if(hit)ran++;else bad.push(real.label||i)}
  closeMenu();return{n,ran,sub,bad}})"""
TIME = r"""async (code)=>{const out=[];const CL=()=>AudioLab.run("closeMenu()");for(let i=0;i<15;i++){CL();
 await new Promise(r=>setTimeout(r,120));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const t0=performance.now();AudioLab.run(code);const t1=performance.now();
 await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));out.push([t1-t0,performance.now()-t0])}
 CL();out.sort((a,b)=>a[0]-b[0]);return out[7]}"""

with sync_playwright() as p:
    logs = []
    b, pg, R = load(p, logs)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    print('version', R("VERSION"))
    t = pg.evaluate(TIME, LOGO); t2 = pg.evaluate(TIME, TAB); t3 = pg.evaluate(TIME, DEV)
    print('open times (JS, render to 2nd frame): logo', [round(x, 1) for x in t], 'tab', [round(x, 1) for x in t2], 'device', [round(x, 1) for x in t3])
    ok(min(t[0], t2[0], t3[0]) < 6.9 and max(t[0], t2[0], t3[0]) < 13.8, 'open calls in the range of the track menu limit (6.9 ms; printed, software renderer)', [t[0], t2[0], t3[0]])
    # tab menu
    R(TAB); pg.wait_for_timeout(100); tb = J(ROW)
    ok([x[0] for x in tb] == ['Save', 'Rename', 'Duplicate', 'Close'], 'tab menu: Save, Rename, Duplicate, Close on the command row', tb)
    ok(tb[3][1] == (J("PJ.list.length") < 2), 'Close greyed only with one tab, as before', [tb[3], J("PJ.list.length")])
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov2b_dark_tab.png'))
    R("closeMenu()")
    # Quick actions
    R(LOGO); pg.wait_for_timeout(250)
    lg = J("{row:" + ROW + ",sub:[...ctxm.querySelectorAll('button[aria-haspopup=menu]')].map(b=>b.textContent.trim()),drop:ctxm.classList.contains('dropup'),b:ctxm.getBoundingClientRect().bottom,lt:document.getElementById('bLogo').getBoundingClientRect().top,rows:ctxm.querySelectorAll('button[data-i]:not(.ovcrow button)').length,stop:[...ctxm.querySelectorAll('button[data-i]')].some(b=>/^Stop all sound/.test(b.textContent.trim()))}")
    ok([x[0] for x in lg['row']] == ['Save', 'Open', 'Undo', 'Settings'], 'Quick actions: Save, Open, Undo, Settings on the command row', lg['row'])
    ok(lg['sub'] and lg['sub'][0].startswith('Restart') and lg['stop'], 'the two restarts in one submenu; Stop all sound stays in the list', lg['sub'])
    ok(lg['drop'] and lg['b'] <= lg['lt'] + 1, 'still opens upwards from the logo', lg)
    print('Quick actions list rows:', lg['rows'])
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov2b_dark_logo.png'))
    R("(()=>{const b=ctxm.querySelector('button[aria-haspopup=menu]');b.click()})()"); pg.wait_for_timeout(80)
    rs = J("{rows:[...ctxm.querySelectorAll('button[data-i]')].map(b=>b.textContent.trim()),fit:ctxm.getBoundingClientRect().top>=0}")
    ok(rs['rows'][:2] == ['Restart audio engine', 'Restart AudioLabreload everything, back to the splash'] and rs['fit'], 'the Restart submenu holds both restarts and stays on screen', rs)
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov2b_dark_logo_sub.png'))
    R("closeMenu()")
    # device menu
    R(DEV); pg.wait_for_timeout(100); dv = J(ROW)
    ok([x[0] for x in dv] in (['Turn off', 'Copy', 'Paste', 'Duplicate', 'Delete'], ['Turn on', 'Copy', 'Paste', 'Duplicate', 'Delete']), 'device menu: on/off, Copy, Paste, Duplicate, Delete on the command row', dv)
    ok(J("document.activeElement&&ctxm.contains(document.activeElement)"), 'a menu that is only a command row focuses its first button')
    pg.keyboard.press('ArrowRight'); f1 = J(FOC); pg.keyboard.press('End'); f2 = J(FOC)
    ok(f1 == 'Copy device' and f2 == 'Delete', 'Left/Right and End move along the command row', [f1, f2])
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov2b_dark_device.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(60)
    # every entry still runs its command
    for nm, code in [('tab', TAB), ('logo', LOGO), ('device', DEV)]:
        c = J(ALL + '(' + json.dumps(code) + ')'); pg.wait_for_timeout(120)
        ok(c['n'] >= 3 and c['ran'] == c['n'], nm + ' menu: every enabled entry (row and submenu too) reaches its command', c)
    # the tab menu from the keyboard
    R("(()=>{const b=document.querySelector('#ptl [data-p].on')||document.querySelector('#ptl [data-p]');b.focus()})()"); pg.keyboard.press('Shift+F10'); pg.wait_for_timeout(120)
    k = J("{open:!ctxm.hidden,row:" + ROW + ",f:" + FOC + "}")
    ok(k['open'] and [x[0] for x in k['row']][:1] == ['Save'] and k['f'] == 'Save as…', 'Shift+F10 on a project tab opens its menu, first list entry focused', k)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(60)
    ok(J("!!document.activeElement.closest('#ptl [data-p]')") and J("ctxm.hidden"), 'Esc closes, focus back on the tab')
    # a menu opened during the last one's fade-out takes focus (right-click on another object while a menu is open)
    R(TAB); R("closeMenu()"); R(DEV); pg.wait_for_timeout(30)
    ok(J("!ctxm.inert&&!ctxm.classList.contains('ovout')&&ctxm.contains(document.activeElement)"), 'a menu opened during the previous one\'s fade-out has focus and is not inert')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    hb = J("(()=>{const h=document.querySelectorAll('#hdrin .hdr');const a=h[2].getBoundingClientRect(),c=h[0].getBoundingClientRect();return[a.left+a.width/2,a.top+a.height/2,c.left+c.width/2,c.top+c.height/2]})()")
    pg.mouse.click(hb[0], hb[1], button='right'); pg.wait_for_timeout(700); pg.mouse.click(hb[2], hb[3], button='right'); pg.wait_for_timeout(40)
    ok(J("!ctxm.hidden&&ctxm.contains(document.activeElement)"), 'right-click a second track while a menu is open: the new menu has keyboard focus')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    R(TAB); pg.wait_for_timeout(50); hd = J("(()=>{const r=ctxm.querySelector('.mh').getBoundingClientRect();return[r.left+r.width/2,r.top+r.height/2]})()")
    pg.mouse.click(hd[0], hd[1]); pg.wait_for_timeout(50)
    ok(J("!ctxm.hidden&&ctxm.contains(document.activeElement)"), 'a click on the menu\'s head keeps the menu open with keyboard focus in it')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok(not logs, 'no console errors (dark)', logs[:5])
    # Light mode, Solid
    R("pmSetOn(true)"); pg.wait_for_timeout(1200); R(LOGO); pg.wait_for_timeout(250)
    ok(J("!ctxm.hidden&&!!ctxm.querySelector('.ovcrow')"), 'Light mode: Quick actions with its command row')
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov2b_lite_logo.png'))
    R("closeMenu()"); R(TAB); pg.wait_for_timeout(500)   # Light mode draws few frames; its 0.01 ms transitions land on the next one
    tp = J("(()=>{const r=ctxm.getBoundingClientRect();return[Math.round(r.left),Math.round(r.top)]})()")
    ok(abs(tp[0] - 300) < 3 and abs(tp[1] - 60) < 3, 'Light mode: the tab menu opens where it is asked', tp)
    R("closeMenu()"); R("pmSetOn(false)"); pg.wait_for_timeout(1000)
    R("(()=>{UI.gl={...(UI.gl||{}),lv:'solid'};gleApply()})()"); pg.wait_for_timeout(800); R(DEV); pg.wait_for_timeout(150)
    ok(J("!ctxm.hidden&&!!ctxm.querySelector('.ovcrow')") and J("(getComputedStyle(ctxm).backdropFilter||'none')") == 'none', 'Solid level: the device menu, no backdrop-filter')
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov2b_solid_device.png'))
    R("closeMenu()"); R("(()=>{UI.gl={...(UI.gl||{}),lv:'glass'};gleApply()})()"); pg.wait_for_timeout(500)
    ok(not logs, 'no console errors (Light mode, Solid)', logs[:5])
    b.close()
    logs2 = []
    b, pg, R = load(p, logs2, reduced=True)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    R(LOGO); pg.wait_for_timeout(200)
    ok(J("!ctxm.hidden&&!!ctxm.querySelector('.ovcrow')"), 'reduced motion: Quick actions opens with its row')
    pg.keyboard.press('Escape'); ok(J("ctxm.hidden"), 'reduced motion: Esc closes')
    ok(not logs2, 'no console errors (reduced motion)', logs2[:5])
    b.close()
    print(f'{N[0] - len(FAIL)} of {N[0]} checks passed'); sys.exit(1 if FAIL else 0)
