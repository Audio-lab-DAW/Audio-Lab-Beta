"""Device layout with side headers (v0.196, task T; from DV-3 a closed device On the picture keeps its preset row visible, floating on the picture): python3 tools/ui-tests/sideheaders.py [index.html] [out dir]
Fractals demo, headless. For every device of several tracks and the master: a strip on the left (on/off or logo at the top, the name, remove at the bottom),
a strip on the right (pin at the top, the show and hide parameters button; since v0.262, task DV-1: the pill with the eye and the pin at the top right of the display), the preset row on top of the parameters, nothing clipped, at two panel heights,
parameters open and shut. Mouse tests: on/off, show and hide parameters, next preset, Change (Escape), pin and unpin (and the layout in the window), remove
and undo, remove on an instrument (asks; Keep it), the panel's own Devices tab (hide, show), the overflow buttons of the track tabs at a narrow width."""
import sys, os, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
FAIL = []
def ok(c, m):
    print(('ok   ' if c else 'FAIL ') + m)
    if not c: FAIL.append(m)

def boot(p, w, h):
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': w, 'height': h}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:400]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404, body=b'')))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html'); pg.wait_for_timeout(7000)
    pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    return b, pg, errs
def run(pg, c): return pg.evaluate("c=>window.AudioLab.run(c)", c)
def sel(pg, name):
    run(pg, "(()=>{const t=S.tracks.find(t=>t.name===%s);selectTrack(t.id);return 1})()" % json.dumps(name)); pg.wait_for_timeout(500)

# every laid-out device in a root: geometry of the strips, the row, and anything outside the device or the visible panel
GEO = r"""(root=>{const out=[];const R0=root.getBoundingClientRect();for(const D of root.querySelectorAll(':scope>.dev[data-d=inst],:scope>.dev[data-d=fx],.pinb>.dev')){if(!D.classList.contains('du'))continue;
 const R=D.getBoundingClientRect(),L=D.querySelector(':scope>.devh'),Rs=D.querySelector(':scope>.dsr')||D.querySelector(':scope>.devb>.dvtr'),l=L&&L.getBoundingClientRect(),r=Rs&&Rs.getBoundingClientRect();
 const first=L&&L.firstElementChild,rm=L&&L.querySelector(':scope>.dsrm'),pin=Rs&&Rs.querySelector(':scope>.pinbtn'),ar=Rs&&Rs.querySelector(':scope>.duar'),row=D.querySelector('.dspr');
 const bad=[];for(const el of D.querySelectorAll('.kn,.vb,.hb,button,select,canvas,label')){const q=el.getBoundingClientRect();if(!q.width||!el.offsetParent)continue;if(el.closest('.kscroll,.gridwrap,.pzscroll,[data-scroll],.gwrap'))continue;if(D.classList.contains('dvshut')&&el.closest('.dfs,.eqside,.dug'))continue;
   if(q.left<R.left-1||q.right>R.right+1||q.top<R.top-1||q.bottom>R.bottom+1)bad.push((el.title||el.textContent||el.className||el.tagName).toString().trim().slice(0,18))}
 const nm=L&&L.querySelector(':scope>span');out.push({d:D.dataset.d,name:nm?(nm.title||nm.textContent).trim():'?',ds:D.classList.contains('ds'),shut:D.classList.contains('dushut')||D.classList.contains('dvshut'),pic:D.classList.contains('dvpic'),
  left:l?Math.round(l.left-R.left):-1,lw:l?Math.round(l.width):0,right:r?Math.round(R.right-r.right):-1,
  top:first?(first.classList.contains('pw')?'onoff':first.tagName.toLowerCase()==='svg'?'logo':first.className):'-',
  rmBottom:rm?Math.round(R.bottom-rm.getBoundingClientRect().bottom):-1,rmLeft:rm?Math.round(rm.getBoundingClientRect().left-R.left):-1,
  pinTop:pin?Math.round(pin.getBoundingClientRect().top-R.top):-1,pinRight:pin?Math.round(R.right-pin.getBoundingClientRect().right):-1,arrow:!!ar,
  row:row?(row.classList.contains('dsfl')?'float':'side'):'none',rowVis:!!(row&&row.offsetParent&&getComputedStyle(row.closest('.dfs,.eqside')||row).opacity!=='0'),
  rowTop:row&&row.offsetParent?Math.round(row.getBoundingClientRect().top-R.top):-1,
  inPanel:root.id!=='fxin'||root.classList.contains('wrap')||(R.top>=R0.top-1&&R.bottom<=R0.bottom+1),bad:bad.slice(0,4),w:Math.round(R.width),h:Math.round(R.height)})}return JSON.stringify(out)})"""
def check(pg, tag, root='fxin'):
    rows = json.loads(run(pg, GEO + "(document.getElementById('%s'))" % root if root == 'fxin' else GEO + "(document.querySelector('%s'))" % root))
    for d in rows:
        m = '%s %-18s %4dx%-3d' % (tag, d['name'][:18], d['w'], d['h'])
        good = d['ds'] and 0 <= d['left'] <= 2 and 0 <= d['right'] <= 8 and d['top'] in ('onoff', 'logo') and 0 <= d['rmBottom'] <= 8 and d['rmLeft'] <= 4 \
            and 0 <= d['pinTop'] <= 10 and 0 <= d['pinRight'] <= 8 and not d['bad'] and d['inPanel'] \
            and (d['shut'] and (not d['rowVis'] or d.get('pic')) or not d['shut'] and (d['row'] != 'none' and d['rowVis'] and d['rowTop'] <= 10))
        ok(good, m + ' strips L%d R%d top %s remove %d from bottom, pin %d from top, row %s at %d%s%s' % (d['left'], d['right'], d['top'], d['rmBottom'], d['pinTop'],
            d['row'] if not d['shut'] else 'hidden (shut)', d['rowTop'], '' if d['inPanel'] else ' NOT IN PANEL', (' clipped: ' + ', '.join(d['bad'])) if d['bad'] else ''))
    return rows

with sync_playwright() as p:
    b, pg, errs = boot(p, 1600, 1000)
    ok(not errs, 'no page errors on load ' + '; '.join(errs))
    tracks = ['Bass', 'Kick', 'Lead', 'Acid', 'Riser', 'Crash', 'Kick & Bass']
    # three heights: the default panel, the smallest panel (piano roll docked above it, border dragged down), and the Devices window made tall
    OPENPR = "(()=>{const t=S.tracks.find(t=>t.clips.some(c=>c.notes&&c.notes.length));openPR(t,t.clips.find(c=>c.notes));UI.fxDH=215;prDockFit();renderFx();return 1})()"
    for H in (262, 215, 430):
        if H == 215: run(pg, OPENPR)
        if H == 430: run(pg, "(()=>{closePR();devPop(true);const w=document.getElementById('devWin');w.style.height='470px';w.style.width='1500px';w.style.left='40px';w.style.top='60px';renderFx();return 1})()")
        pg.wait_for_timeout(600)
        print('panel height', run(pg, "fxin.getBoundingClientRect().height|0"), 'device height', run(pg, "(fxin.querySelector('.dev.du')||{offsetHeight:0}).offsetHeight"))
        for t in tracks:
            sel(pg, t); check(pg, 'h%d %s' % (H, t[:5]))
            pg.screenshot(path=os.path.join(OUT, 'panel_%d_%s.png' % (H, t.replace(' ', '_').replace('&', 'and'))))
        run(pg, "(()=>{selMaster();return 1})()"); pg.wait_for_timeout(400)
        run(pg, "(()=>{if(!S.master)return 0;return 1})()")
        check(pg, 'h%d master' % H); pg.screenshot(path=os.path.join(OUT, 'panel_%d_master.png' % H))
        # every device shut
        sel(pg, 'Bass')
        run(pg, "(()=>{const t=curT();t.inst.kOpen=false;for(const f of t.fx)f.kOpen=false;renderFx();return 1})()"); pg.wait_for_timeout(400)
        check(pg, 'h%d shut' % H); pg.screenshot(path=os.path.join(OUT, 'panel_%d_shut.png' % H))
        run(pg, "(()=>{const t=curT();t.inst.kOpen=true;for(const f of t.fx)f.kOpen=true;renderFx();return 1})()"); pg.wait_for_timeout(400)
    run(pg, "(()=>{devPop(false);devHide(false);renderFx();return 1})()"); pg.wait_for_timeout(600)

    # ---- mouse tests on the Bass track: Plant > EQ > Sidechain > EQ ----
    sel(pg, 'Bass')
    Q = "fxin.querySelector(':scope>.dev[data-d=fx]:nth-of-type(%d)')"
    def fxdev(i): return "[...fxin.querySelectorAll(':scope>.dev[data-d=fx]')][%d]" % i
    def click(css_js, sub):
        r = json.loads(run(pg, "(()=>{const e=%s.querySelector(%s);e.scrollIntoView({block:'nearest',inline:'nearest'});const q=e.getBoundingClientRect();return JSON.stringify([q.left+q.width/2,q.top+Math.min(q.height/2,11)])})()" % (css_js, json.dumps(sub))))
        pg.mouse.click(r[0], r[1]); pg.wait_for_timeout(350)
    on0 = run(pg, "curT().fx[1].on"); click(fxdev(1), '.devh>.pw'); on1 = run(pg, "curT().fx[1].on"); click(fxdev(1), '.devh>.pw'); on2 = run(pg, "curT().fx[1].on")
    ok(on0 != on1 and on2 == on0, 'on/off on the Sidechain by mouse: %s > %s > %s' % (on0, on1, on2))
    click(fxdev(1), ':is(.dsr>.duar,.dvtr>.dveye)'); pg.wait_for_timeout(300); k1 = run(pg, "curT().fx[1].kOpen"); w1 = run(pg, fxdev(1) + ".offsetWidth")
    click(fxdev(1), ':is(.dsr>.duar,.dvtr>.dveye)'); pg.wait_for_timeout(300); k2 = run(pg, "curT().fx[1].kOpen"); w2 = run(pg, fxdev(1) + ".offsetWidth")
    ok(k1 is False and k2 is True and w1 < w2, 'show and hide parameters by mouse on the Sidechain: kOpen %s > %s, width %s > %s' % (k1, k2, w1, w2))
    click("fxin.querySelector(':scope>.dev[data-d=inst]')", ':is(.dsr>.duar,.dvtr>.dveye)'); pg.wait_for_timeout(300); ki = run(pg, "curT().inst.kOpen")
    pg.screenshot(path=os.path.join(OUT, 'mouse_plant_shut.png'))
    click("fxin.querySelector(':scope>.dev[data-d=inst]')", ':is(.dsr>.duar,.dvtr>.dveye)'); pg.wait_for_timeout(300); ki2 = run(pg, "curT().inst.kOpen")
    ok(ki is False and ki2 is not False, 'show and hide parameters by mouse on Plant: %s > %s' % (ki, ki2))
    p0 = run(pg, "curT().inst.ipk||''"); click("fxin.querySelector(':scope>.dev[data-d=inst]')", '.dspr .kpre button:last-of-type'); p1 = run(pg, "curT().inst.ipk||''")
    run(pg, "(()=>{undo();return 1})()"); pg.wait_for_timeout(300)
    ok(p0 != p1, 'next preset on Plant by mouse: %r > %r' % (p0, p1))
    e0 = run(pg, fxdev(0) + ".querySelector('.dspr select').value"); click(fxdev(0), '.dspr .kpre button:last-of-type'); e1 = run(pg, fxdev(0) + ".querySelector('.dspr select').value")
    ok(e0 != e1, 'next preset on the EQ by mouse: %r > %r' % (e0, e1)); run(pg, "(()=>{undo();return 1})()"); pg.wait_for_timeout(300)
    click(fxdev(1), '.dspr .duchg'); pg.wait_for_timeout(500); ibo = run(pg, "!document.getElementById('ib').hidden")
    pg.screenshot(path=os.path.join(OUT, 'mouse_change.png')); pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    ok(ibo and run(pg, "document.getElementById('ib').hidden") and run(pg, "curT().fx[1].type") == 'side', 'Change on the Sidechain opens the browser, Escape keeps the Sidechain')
    click("fxin.querySelector(':scope>.dev[data-d=inst]')", '.dspr .duchg'); pg.wait_for_timeout(500); ibi = run(pg, "!document.getElementById('ib').hidden")
    pg.keyboard.press('Escape'); pg.wait_for_timeout(500); ok(ibi and run(pg, "curT().inst.preset") == 'plant', 'Change on Plant opens the browser, Escape keeps Plant')
    n0 = run(pg, "curT().fx.length"); click(fxdev(2), '.devh>.dsrm'); n1 = run(pg, "curT().fx.length"); run(pg, "(()=>{undo();return 1})()"); pg.wait_for_timeout(400); n2 = run(pg, "curT().fx.length")
    ok(n1 == n0 - 1 and n2 == n0, 'remove the last EQ by mouse: %d > %d effects, undo %d' % (n0, n1, n2))
    t0 = run(pg, "S.tracks.length"); click("fxin.querySelector(':scope>.dev[data-d=inst]')", '.devh>.dsrm'); pg.wait_for_timeout(400)
    dl = run(pg, "!document.getElementById('cdlg').hidden&&document.getElementById('cdT').textContent"); pg.screenshot(path=os.path.join(OUT, 'mouse_remove_inst.png'))
    pg.click('#cdlg button:has-text("Keep it")'); pg.wait_for_timeout(400); t1 = run(pg, "S.tracks.length")
    ok(bool(dl) and t1 == t0, 'remove on the instrument asks (%s), Keep it keeps the track (%d > %d)' % (dl, t0, t1))
    # pin the Sidechain and the instrument; the window has the same layout
    click(fxdev(1), ':is(.dsr,.dvtr)>.pinbtn'); pg.wait_for_timeout(600); click("fxin.querySelector(':scope>.dev[data-d=inst]')", ':is(.dsr,.dvtr)>.pinbtn'); pg.wait_for_timeout(600)
    nw = run(pg, "PIN.wins.size"); ok(nw == 2, 'pinned two devices by mouse: %d windows' % nw)
    sel(pg, 'Kick'); pg.wait_for_timeout(400)
    for i, w in enumerate(json.loads(run(pg, "JSON.stringify([...PIN.wins.keys()])"))):
        rows = check(pg, 'pinned', "[data-pk=\"%s\"] .pinb" % w)
        on = run(pg, "!!document.querySelector('[data-pk=\"%s\"] .dsr>.pinbtn.on')" % w); ok(on, 'pinned window %d: its pin is lit' % i)
    pg.screenshot(path=os.path.join(OUT, 'pinned.png'))
    w0 = run(pg, "[...PIN.wins.keys()].find(k=>!k.endsWith('/inst'))")
    r = json.loads(run(pg, "(()=>{const q=document.querySelector('[data-pk=\"%s\"] .dsr>.duar').getBoundingClientRect();return JSON.stringify([q.left+q.width/2,q.top+12])})()" % w0))
    pg.mouse.click(r[0], r[1]); pg.wait_for_timeout(500); ks = run(pg, "(()=>{const t=S.tracks.find(t=>t.name==='Bass');return t.fx[1].kOpen})()")
    pg.screenshot(path=os.path.join(OUT, 'pinned_shut.png'))
    r = json.loads(run(pg, "(()=>{const q=document.querySelector('[data-pk=\"%s\"] .dsr>.duar').getBoundingClientRect();return JSON.stringify([q.left+q.width/2,q.top+12])})()" % w0))
    pg.mouse.click(r[0], r[1]); pg.wait_for_timeout(500); ko = run(pg, "(()=>{const t=S.tracks.find(t=>t.name==='Bass');return t.fx[1].kOpen})()")
    ok(ks is False and ko is True, 'show and hide parameters inside a pinned window: %s > %s' % (ks, ko))
    for w in json.loads(run(pg, "JSON.stringify([...PIN.wins.keys()])")):
        r = json.loads(run(pg, "(()=>{const q=document.querySelector('[data-pk=\"%s\"] .dsr>.pinbtn').getBoundingClientRect();return JSON.stringify([q.left+q.width/2,q.top+q.height/2])})()" % w))
        pg.mouse.click(r[0], r[1]); pg.wait_for_timeout(500)
    ok(run(pg, "PIN.wins.size") == 0, 'unpinned both with the pin in their windows')
    # the panel's own tab
    pg.click('#fxHide'); pg.wait_for_timeout(500); h1 = run(pg, "UI.fxHide"); pg.screenshot(path=os.path.join(OUT, 'devices_hidden.png'))
    tb = run(pg, "(()=>{const r=document.getElementById('fxHide').getBoundingClientRect();return r.width>60&&r.height>=18&&r.bottom<=innerHeight&&r.top>=0})()")
    pg.click('#fxHide'); pg.wait_for_timeout(500); h2 = run(pg, "UI.fxHide")
    ok(h1 is True and h2 is False and tb, 'the Devices tab hides and shows the panel; it stays on screen while hidden')
    tip = run(pg, "(()=>{const b=document.getElementById('fxHide');return b.title||b.dataset.tip||b.getAttribute('data-title')||b.getAttribute('aria-label')})()"); ok('—' not in tip and len(tip) > 10, 'Devices tab tooltip: ' + tip)
    errs0 = list(errs); b.close()

    # ---- narrow window: the overflow buttons of the track tabs ----
    b, pg, errs = boot(p, 900, 700)
    sel(pg, 'Shaker'); pg.wait_for_timeout(400)
    st = json.loads(run(pg, "(()=>{const b=document.querySelector('#fxTitle .fxsw.fxall'),sc=b.querySelector('.fxsc');const L=b.querySelector('.fxov.l'),R=b.querySelector('.fxov.r');return JSON.stringify({l:getComputedStyle(L).display,r:getComputedStyle(R).display,nl:L.textContent,nr:R.textContent,sl:sc.scrollLeft,tl:L.title,tr:R.title})})()"))
    pg.screenshot(path=os.path.join(OUT, 'tabs_900.png'), clip={'x': 0, 'y': run(pg, "document.getElementById('fx').getBoundingClientRect().top") - 40, 'width': 900, 'height': 90})
    ok(st['l'] == 'flex' and st['r'] == 'flex' and st['nl'] and st['nr'], 'at 900 px both sides show how many tabs are hidden: %s left, %s right' % (st['nl'], st['nr']))
    r = json.loads(run(pg, "(()=>{const q=document.querySelector('#fxTitle .fxov.r').getBoundingClientRect();return JSON.stringify([q.left+q.width/2,q.top+q.height/2])})()"))
    pg.mouse.click(r[0], r[1]); pg.wait_for_timeout(700); sl = run(pg, "document.querySelector('#fxTitle .fxsc').scrollLeft"); hid = run(pg, "UI.fxHide")
    ok(sl > st['sl'] and not hid, 'the right button scrolls the tabs (%d > %d) and does not fold the panel' % (st['sl'], sl))
    run(pg, "(()=>{document.querySelector('#fxTitle .fxsc').scrollLeft=0;return 1})()"); pg.wait_for_timeout(300)
    st2 = json.loads(run(pg, "(()=>{const b=document.querySelector('#fxTitle .fxsw.fxall');return JSON.stringify([getComputedStyle(b.querySelector('.fxov.l')).display,b.querySelector('.fxov.r').textContent])})()"))
    pg.screenshot(path=os.path.join(OUT, 'tabs_900_start.png'), clip={'x': 0, 'y': run(pg, "document.getElementById('fx').getBoundingClientRect().top") - 40, 'width': 900, 'height': 90})
    ok(st2[0] == 'none' and st2[1], 'scrolled to the start: no left button, %s hidden on the right' % st2[1])
    ok(not errs0 and not errs, 'no page errors: ' + '; '.join(errs0 + errs))
    b.close()
print('\n%d failures' % len(FAIL)); [print('  ' + f) for f in FAIL]
