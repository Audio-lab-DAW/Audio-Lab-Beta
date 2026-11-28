#!/usr/bin/env python3
"""Task OV8 (lane F, overlays, pick K1): the command palette on Cmd/Ctrl+K with the Assistant inside, Recent first, and the ? key sheet.
Keyboard paths, focus return, every command of the palette reaches runCommand, the Assistant row and Cmd+K again, the key sheet,
open and search times; dark, Light mode, Solid, reduced motion; no console errors.
   python3 tools/ui-tests/taskOV8.py [index.html] [shots-dir]
At the user's size (2194 x 1139 CSS px at 1.75x) with Fractals. SwiftShader: times for comparison only."""
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

PAL = "(()=>{const e=document.getElementById('ovPal');return!!e&&!e.hidden})()"
KS = "(()=>{const e=document.getElementById('ovKeys');return!!e&&!e.hidden})()"
ROWS = "[...document.querySelectorAll('#ovPal .ovr')].map(r=>r.querySelector('.ovl').textContent)"
FOCROW = "(document.querySelector('#ovPal .ovr.on .ovl')||{}).textContent"
TIME = r"""async ()=>{const out=[];for(let i=0;i<15;i++){AudioLab.run("ovPalClose(false)");
 await new Promise(r=>setTimeout(r,60));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const t0=performance.now();AudioLab.run("ovPalOpen()");const t1=performance.now();
 await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));out.push([t1-t0,performance.now()-t0])}
 AudioLab.run("ovPalClose(false)");out.sort((a,b)=>a[0]-b[0]);return out[7]}"""
SEARCH = r"""()=>{const inp=document.querySelector('#ovPal input');const T=[];for(const q of['s','sp','spl','split','mixer','zoom in','quantize','xyz']){inp.value=q;const t0=performance.now();ovPalDraw();T.push(performance.now()-t0)}T.sort((a,b)=>a-b);return[T[4],T[7]]}"""

with sync_playwright() as p:
    logs = []
    b, pg, R = load(p, logs)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    print('version', R("VERSION"))
    st = J("{pal:SCM.has('help.palette')&&scBind(SCM.get('help.palette')),ks:SCM.has('help.keySheet')&&scBind(SCM.get('help.keySheet')),ai:scBind(SCM.get('ai')),reg:XT_CMD.n,el:!!document.getElementById('ovPal')}")
    ok(st['pal'] == 'Mod+K' and st['ks'] == '?' and st['ai'] == '', 'Mod+K is the palette, ? the key sheet; the Assistant row has no default key now', st)
    ok(st['reg'] == -1 and not st['el'], 'nothing is built at start: no registry, no palette element', st)
    # Cmd/Ctrl+K from the arrangement, focus on the Loop button
    R("document.getElementById('bLoop').focus()"); pg.keyboard.press('Control+k'); pg.wait_for_timeout(150)
    o = J("{pal:" + PAL + ",foc:document.activeElement===document.querySelector('#ovPal input'),role:document.activeElement.getAttribute('role'),ad:document.activeElement.getAttribute('aria-activedescendant'),rows:" + ROWS + ",groups:[...document.querySelectorAll('#ovPal .ovpg')].map(g=>g.textContent),ai:!!document.getElementById('aip')&&!document.getElementById('aip').hidden}")
    ncmd = J("ovPalCmds().length")
    ok(o['pal'] and o['foc'] and o['role'] == 'combobox' and o['ad'] == 'ovpo0' and not o['ai'], 'Ctrl+K opens the palette (not the Assistant), the search has focus, combobox with the first row active', {k: o[k] for k in ('pal', 'foc', 'role', 'ad', 'ai')})
    ok(len(o['rows']) == ncmd and ncmd >= 60, 'every runnable command is listed (registry without gestures and without the palette itself)', (len(o['rows']), ncmd))
    ok(o['groups'][:5] == ['Transport', 'Editing', 'Windows & view', 'Project & files', 'Help & tools'], 'grouped like Settings › Keyboard shortcuts', o['groups'])
    pg.wait_for_timeout(600)
    ok(J("GLF.items.some(it=>it.el.id==='ovPal')||document.getElementById('ovPal').classList.contains('glfsol')") and J("getComputedStyle(document.getElementById('ovPal')).backdropFilter") == 'none', 'the glass engine draws it (a menu face), no backdrop-filter')
    pg.wait_for_timeout(600)
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov8_dark_palette.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(80)
    ok(J("!" + PAL + "&&document.activeElement&&document.activeElement.id==='bLoop'"), 'Esc closes, focus back on the Loop button')
    # fuzzy search, highlight, keys, the Assistant row
    pg.keyboard.press('Control+k'); pg.wait_for_timeout(80); pg.keyboard.type('splt'); pg.wait_for_timeout(50)
    s1 = J("{rows:" + ROWS + ",mark:document.querySelectorAll('#ovPal .ovr.on mark').length,key:(document.querySelector('#ovPal .ovr.on kbd')||{}).textContent,last:document.querySelector('#ovPal .ovr:last-child .ovl').textContent}")
    ok(s1['rows'] and s1['rows'][0] == 'Split clip at the playhead' and s1['mark'] == 4 and s1['key'] == '⇧S', 'fuzzy search: "splt" finds Split first, matched letters marked, its key in mono', s1)
    ok(s1['last'] == 'Ask the Assistant: “splt”', 'the last row asks the Assistant with what was typed', s1['last'])
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov8_dark_search.png'))
    pg.keyboard.press('ArrowDown'); f1 = J(FOCROW); pg.keyboard.press('ArrowUp'); pg.keyboard.press('ArrowUp'); f2 = J(FOCROW)
    ok(f1 != s1['rows'][0] and f2 == s1['rows'][-1], 'arrows move through the rows and wrap', [f1, f2])
    pg.keyboard.press('Tab'); ok(J("document.activeElement===document.querySelector('#ovPal input')"), 'Tab stays in the palette')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(60)
    # Enter runs: the metronome through the palette, focus returned, Recent first
    a0 = J("$('#bClick').getAttribute('aria-pressed')")
    R("document.getElementById('bLoop').focus()"); pg.keyboard.press('Control+k'); pg.wait_for_timeout(60); pg.keyboard.type('metronome'); pg.keyboard.press('Enter'); pg.wait_for_timeout(150)
    a1 = J("$('#bClick').getAttribute('aria-pressed')")
    ok(a1 != a0 and J("!" + PAL) and J("document.activeElement.id") == 'bLoop' and J("XT_CMD_LOG[XT_CMD_LOG.length-1].src") == 'palette', 'Enter runs the command through runCommand (metronome toggled), the palette closes, focus goes back', (a0, a1))
    R("runCommand('transport.metronome')")
    pg.keyboard.press('Control+k'); pg.wait_for_timeout(60)
    rc = J("{g:document.querySelector('#ovPal .ovpg').textContent,r:" + FOCROW + ",u:UI.ovRecent}")
    ok(rc['g'] == 'Recent' and rc['r'] == 'Metronome' and rc['u'][0] == 'transport.metronome', 'Recent comes first and holds the command just run (kept in the settings)', rc)
    pg.keyboard.press('Escape')
    # every row reaches its command (runCommand stubbed)
    ev = J(r"""(()=>{const real=runCommand,ran=[];runCommand=(id,src)=>{ran.push(id);return true};const want=ovPalCmds().map(c=>c.id);
      try{for(let i=0;i<want.length;i++){ovPalOpen();const r=document.querySelectorAll('#ovPal .ovr')[i];r.click()}}finally{runCommand=real}
      const miss=want.filter(id=>!ran.includes(id));return{n:want.length,ran:new Set(ran).size,miss}})()""")
    ok(ev['n'] == ev['ran'] and not ev['miss'], 'every palette row (click) reaches runCommand with its own id', ev)
    R("UI.ovRecent=[];saveUI()")
    # the Assistant row and Cmd+K again
    ak = J(r"""(()=>{const real=aiSend,got=[];aiSend=t=>{got.push(t)};try{ovPalOpen();const inp=document.querySelector('#ovPal input');inp.value='add a riser';ovPalDraw();
      const n=document.querySelectorAll('#ovPal .ovr').length;document.querySelectorAll('#ovPal .ovr')[n-1].click()}finally{aiSend=real}
      return{got,open:!document.getElementById('aip').hidden}})()""")
    ok(ak['got'] == ['add a riser'] and ak['open'], 'the Ask the Assistant row opens the Assistant and sends what was typed', ak)
    R("aiOpen(false)"); pg.wait_for_timeout(100)
    R("document.getElementById('bLoop').focus()"); pg.keyboard.press('Control+k'); pg.wait_for_timeout(60); pg.keyboard.type('louder'); pg.keyboard.press('Control+k'); pg.wait_for_timeout(250)
    a2 = J("{pal:" + PAL + ",ai:!document.getElementById('aip').hidden,v:document.querySelector('#aip textarea').value,msgs:AI.msgs.length}")
    ok(not a2['pal'] and a2['ai'] and a2['v'] == 'louder', 'Ctrl+K again in the palette opens the Assistant with what was typed, without sending it', a2)
    R("aiOpen(false)"); pg.wait_for_timeout(80)
    # the ? key sheet
    R("document.getElementById('bLoop').focus()"); pg.keyboard.press('Control+k'); pg.wait_for_timeout(60); pg.keyboard.press('?'); pg.wait_for_timeout(120)
    k1 = J("{ks:" + KS + ",pal:" + PAL + ",foc:document.activeElement===document.querySelector('#ovKeys input'),cnt:document.querySelector('#ovKeys .ovcnt').textContent,rows:document.querySelectorAll('#ovKeys .ovkr').length,want:SCA.filter(a=>scBind(a)).length}")
    ok(k1['ks'] and not k1['pal'] and k1['foc'] and k1['rows'] == k1['want'] and k1['cnt'].startswith(str(k1['want']) + ' KEYS'), '? in the empty palette opens the key sheet: every key, counted, search focused', k1)
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov8_dark_keys.png'))
    pg.keyboard.type('shift'); pg.wait_for_timeout(50)
    k2 = J("[...document.querySelectorAll('#ovKeys .ovkr')].map(k=>[k.querySelector('span').textContent,k.querySelector('kbd').textContent])")
    ok(len(k2) >= 10 and all('⇧' in k or 'Shift' in l for l, k in k2), 'the key sheet search finds keys ("shift" lists the Shift keys)', len(k2))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(60)
    ok(J("!" + KS) and J("document.activeElement.id") == 'bLoop', 'Esc closes the key sheet, focus back where it was')
    R("document.activeElement.blur()"); pg.mouse.click(1100, 600); pg.keyboard.press('Escape'); pg.wait_for_timeout(50); pg.keyboard.press('?'); pg.wait_for_timeout(100)
    ok(J(KS), '? anywhere outside a text field opens the key sheet')
    R("document.querySelector('#ovKeys .ovkset').click()"); pg.wait_for_timeout(500)
    ok(J("!" + KS + "&&!$('#set').hidden&&!!document.querySelector('#setBody section[data-page=keys]:not([hidden])')"), 'Change keys in Settings opens Settings on the shortcuts page')
    nsc = J("document.querySelectorAll('#scBody .scr').length"); ok(nsc == J("SCA.length"), 'the Settings shortcut list shows the two new rows with the others', (nsc, J("SCA.length")))
    R("$('#set').hidden=true"); pg.wait_for_timeout(100)
    # a key the user gave the Assistant is kept; typing in a field does not open the palette
    R("UI.keys=Object.assign({},UI.keys,{ai:'Mod+Shift+K'})"); R("document.activeElement.blur()"); pg.keyboard.press('Control+Shift+K'); pg.wait_for_timeout(200)
    ok(J("!document.getElementById('aip').hidden") and not J(PAL), 'a key the user gave the Assistant still opens it')
    R("aiOpen(false);delete UI.keys.ai"); pg.wait_for_timeout(80)
    R("(()=>{const i=document.createElement('input');i.id='ov8t';document.body.appendChild(i);i.focus()})()"); pg.keyboard.press('?'); pg.wait_for_timeout(60)
    ok(not J(KS) and J("document.getElementById('ov8t').value") == '?', 'in a text field ? is just typed')
    R("document.getElementById('ov8t').remove()")
    # outside click closes without stealing focus
    R("ovPalOpen()"); pg.wait_for_timeout(60); pg.mouse.click(1100, 700); pg.wait_for_timeout(250)
    ok(not J(PAL), 'a click outside closes the palette')
    # times
    t = pg.evaluate(TIME); R("ovPalOpen()"); sv = pg.evaluate(SEARCH); R("ovPalClose(false)")
    print('open (JS, to 2nd frame) ms', [round(x, 2) for x in t], 'search per key median/max ms', [round(x, 2) for x in sv])
    ok(t[0] < 6.9, 'open call under the track menu\'s 6.9 ms (software renderer)', round(t[0], 2))
    ok(sv[0] < 2 and sv[1] < 10, 'search per key a few ms (median under 2, one slow key under 10: a garbage-collection pause on a 2-core software renderer once gave 4.6)', [round(x, 2) for x in sv])
    ok(not logs, 'no console errors (dark)', logs[:5])
    # Light mode, Solid
    R("pmSetOn(true)"); pg.wait_for_timeout(1200); R("document.activeElement.blur()"); pg.keyboard.press('Control+k'); pg.wait_for_timeout(300); pg.keyboard.type('mix'); pg.wait_for_timeout(300)
    ok(J(PAL) and J(ROWS)[0] == 'Mixer window', 'Light mode: the palette opens and searches')
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov8_lite_palette.png'))
    pg.keyboard.press('Escape'); R("pmSetOn(false)"); pg.wait_for_timeout(1000)
    R("(()=>{UI.gl={...(UI.gl||{}),lv:'solid'};gleApply()})()"); pg.wait_for_timeout(800); R("ovKeysOpen()"); pg.wait_for_timeout(500)
    ok(J(KS) and J("getComputedStyle(document.getElementById('ovKeys')).backdropFilter") == 'none' and J("getComputedStyle(document.getElementById('ovKeys')).backgroundColor") != 'rgba(0, 0, 0, 0)', 'Solid level: the key sheet is solid, no backdrop-filter')
    if OUT: pg.screenshot(path=os.path.join(OUT, 'ov8_solid_keys.png'))
    R("ovKeysClose(false)"); R("(()=>{UI.gl={...(UI.gl||{}),lv:'glass'};gleApply()})()"); pg.wait_for_timeout(500)
    ok(not logs, 'no console errors (Light mode, Solid)', logs[:5])
    b.close()
    logs2 = []
    b, pg, R = load(p, logs2, reduced=True)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    pg.keyboard.press('Control+k'); pg.wait_for_timeout(100)
    ok(J(PAL) and J("getComputedStyle(document.getElementById('ovPal')).animationName") == 'none', 'reduced motion: the palette opens without a fade')
    pg.keyboard.press('Escape'); ok(not J(PAL), 'reduced motion: Esc closes')
    ok(not logs2, 'no console errors (reduced motion)', logs2[:5])
    b.close()
    print(f'{N[0] - len(FAIL)} of {N[0]} checks passed'); sys.exit(1 if FAIL else 0)
