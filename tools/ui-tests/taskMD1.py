#!/usr/bin/env python3
"""Task MD1 (measurement details): M1 readouts with units, M2 orbit loader, M3 caliper while dragging.
   python3 tools/ui-tests/taskMD1.py [index.html] [before.html | out-dir] [shots-dir]
At 1600 x 900 CSS px at 2x with Fractals (SwiftShader: correctness only). With before.html, text clipping is compared with the build before."""
import sys, json, os
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
A2 = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != '-' else None
B = A2 if A2 and os.path.isfile(A2) else None   # the release gate passes an output folder here: then no comparison, screenshots go there
SH = sys.argv[3] if len(sys.argv) > 3 else (A2 if A2 and os.path.isdir(A2) else None)
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)

def load(p, f, logs, w=1600, h=900, dsf=2):
    src = open(f, encoding='utf-8').read()
    ctx = p.chromium.launch(args=ARGS).new_context(viewport={'width': w, 'height': h}, device_scale_factor=dsf, accept_downloads=True); pg = ctx.new_page()
    pg.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'icons.json' not in m.text else None)
    pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=src) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    R("pmSetOn(false)"); R("openDemoFractals()"); pg.wait_for_timeout(6000)
    return pg, R

# text cut off by its own box in the transport, the device panel and the mixer (scrollWidth over clientWidth by more than a pixel)
CLIP = r"""(()=>{const out=[];for(const sel of['#tr','#fx','#mixer','#mxw','.mx']){for(const root of document.querySelectorAll(sel))for(const e of root.querySelectorAll('output,b,span,i,small,label')){if(!e.offsetParent||!e.textContent.trim())continue;const cs=getComputedStyle(e);if(cs.overflow==='visible'&&cs.textOverflow!=='ellipsis'&&e.tagName!=='OUTPUT')continue;if(e.scrollWidth>e.clientWidth+1)out.push((e.id||e.className||e.tagName)+':'+e.textContent.trim().slice(0,20))}}return out})()"""
UNITW = r"""(()=>{const r=[];for(const o of document.querySelectorAll('#fx output, #mixer output, .mx output')){if(!o.offsetParent)continue;const b=o.getBoundingClientRect(),p=o.parentElement.getBoundingClientRect();r.push([b.right>p.right+1||b.left<p.left-1?1:0])}return{n:r.length,out:r.filter(x=>x[0]).length}})()"""

def shot(pg, name, sel=None, clip=None):
    if not SH: return
    os.makedirs(SH, exist_ok=True)
    if sel:
        r = pg.evaluate("s=>{const b=document.querySelector(s).getBoundingClientRect();return[b.x,b.y,b.width,b.height]}", sel)
        clip = {'x': max(0, r[0] - 4), 'y': max(0, r[1] - 4), 'width': min(1600, r[2] + 8), 'height': min(900, r[3] + 8)}
    pg.screenshot(path=os.path.join(SH, name + '.png'), clip=clip)

with sync_playwright() as p:
    logs = []
    pg, R = load(p, F, logs)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    print('version', R("VERSION"))
    # ---------- M1 ----------
    t = J("{uc:LOOK.unitCase,lku:getComputedStyle(document.querySelector('#mBtnV .lku')||document.body).fontVariantCaps,labs:[...document.querySelectorAll('#tr .mdu')].map(e=>e.textContent+':'+getComputedStyle(e).fontVariantCaps+':'+getComputedStyle(e).fontSize+':'+getComputedStyle(e).color),pk:document.getElementById('pkNow').innerHTML,cpu:document.getElementById('cpuV').innerHTML,lat:document.getElementById('latV').innerHTML}")
    ok(t['uc'] == 'small caps' and t['lku'] == 'all-small-caps', 'units are small capitals (LOOK.unitCase, .lku)', [t['uc'], t['lku']])
    ok([l.split(':')[0] for l in t['labs']] == ['bpm', 'bar', 't+'] and all(':all-small-caps:11px:rgb(255, 181, 71)' in l for l in t['labs']), 'transport labels BPM, BAR, T+ as amber small capitals at 11 px (on the type scale)', t['labs'])
    ok('lku' in t['pk'] and 'lku' in t['cpu'] and 'lku' in t['lat'], 'peak, CPU and latency show their unit apart (dB, %, ms)', [t['pk'], t['cpu'], t['lat']])
    tk = J("(()=>{const s=getComputedStyle(document.querySelector('#posBars').closest('.lcd'),'::after');return[s.content,s.height,s.backgroundImage.includes('repeating-linear-gradient')]})()")
    ok(tk[0] == '""' and tk[2], 'a fine tick scale under the position read-outs (CSS only)', tk)
    lt = R("document.getElementById('latV').textContent")
    ok(lt.endswith(' ms') and (lt.startswith('–') or '.' in lt), 'latency with one decimal always', lt)
    # digits do not jump: widths of the read-outs and their boxes stay the same while values change (playing)
    WS = r"""(()=>['#posBars','#posTime','#cpuV','#latV','#peakBox','#mBtnV'].map(s=>{const e=document.querySelector(s);return e?Math.round(e.getBoundingClientRect().width*100)/100:null}).concat([...document.querySelectorAll('#tr .lcd')].map(e=>Math.round(e.getBoundingClientRect().width*100)/100)))()"""
    R("pos=0;start()"); pg.wait_for_timeout(500); ws = []; txt = set()
    for i in range(30):
        ws.append(tuple(J(WS))); txt.add(R("document.getElementById('posTime').textContent+'|'+document.getElementById('cpuV').textContent+'|'+document.getElementById('pkNow').textContent")); pg.wait_for_timeout(150)
    R("stop()")
    var = [i for i in range(len(ws[0])) if len(set(w[i] for w in ws)) > 1]
    ok(len(txt) > 10 and not var, 'no read-out or transport box changes width while the values change (30 samples while playing)', {'values': len(txt), 'changing': var, 'sample': sorted(txt)[:3]})
    # master volume set to values with different lengths
    mw = []
    for v in [0, -10, -3.5, 6, -60, -0.1]:
        R("lkOut($('#mBtnV'),SPEC_MASTER.f(%s))" % v); mw.append(J("[document.getElementById('mBtnV').textContent,document.getElementById('mBtn').getBoundingClientRect().width]"))
    R("lkOut($('#mBtnV'),SPEC_MASTER.f(S.master))")
    ok(len(set(m[1] for m in mw)) <= 2, 'master button width with different volumes', mw)
    # canvas units: lkVU draws the unit in small capitals
    cv = J("(()=>{const c=document.createElement('canvas'),g=c.getContext('2d');g.font='11px Inter';const w1=lkVU(g,'-3.0 dB',0,10);g.fontVariantCaps='all-small-caps';const ws=g.measureText('dB').width;g.fontVariantCaps='normal';return{w1,ws,wn:g.measureText('-3.0 ').width,caps:'fontVariantCaps' in g}})()")
    ok(cv['caps'] and abs(cv['w1'] - cv['wn'] - cv['ws']) < .5, 'canvas units (clip gain) in small capitals', cv)
    shot(pg, 'transport_dark', '#tr')
    # ---------- clipping ----------
    R("selectTrack(S.tracks[0].id)"); pg.wait_for_timeout(800)
    c1 = J(CLIP); u1 = J(UNITW)
    shot(pg, 'devices_dark', '#fx')
    R("$('#mBtn').click()"); pg.wait_for_timeout(1500); c2 = J(CLIP); u2 = J(UNITW); shot(pg, 'mixer_dark', clip={'x': 0, 'y': 300, 'width': 1600, 'height': 600}); R("$('#mBtn').click()"); pg.wait_for_timeout(500)
    if B:
        logsb = []; pgb, RB = load(p, B, logsb); JB = lambda c: json.loads(RB("JSON.stringify(" + c + ")"))
        RB("selectTrack(S.tracks[0].id)"); pgb.wait_for_timeout(800); b1 = JB(CLIP); bu1 = JB(UNITW)
        RB("$('#mBtn').click()"); pgb.wait_for_timeout(1500); b2 = JB(CLIP); bu2 = JB(UNITW)
        new = sorted(set(c1 + c2) - set(b1 + b2))
        ok(not new, 'no text newly cut off in the transport, device panel and mixer (compared with the build before)', {'new': new, 'before': len(b1 + b2), 'after': len(c1 + c2)})
        ok(u1['out'] + u2['out'] <= bu1['out'] + bu2['out'], 'no knob or fader value newly wider than its control', [u1, u2, bu1, bu2])
        pgb.context.close()
    else:
        ok(True, 'clipping (no build to compare with)', [len(c1), len(c2)])
    # ---------- M2 ----------
    o = J("(()=>{const d=document.createElement('div');document.body.appendChild(d);d.innerHTML=mdOrb(16)+mdOrb(24)+mdOrb(40)+mdOrb(24,.3);const s=[...d.querySelectorAll('.mdorb')].map(e=>{const r=e.getBoundingClientRect();return[r.width,r.height,e.getAnimations({subtree:true}).length,e.getAttribute('role')]});const pr=d.querySelectorAll('.mdorb')[3],v0=pr.getAttribute('aria-valuenow');mdOrbSet(pr,.75);const v1=pr.getAttribute('aria-valuenow'),da=pr.querySelector('.o1').style.strokeDasharray;mdOrbSet(d.querySelector('.mdorb'),.5);const sw=[d.querySelector('.mdorb').classList.contains('mdp'),d.querySelector('.mdorb').getAnimations({subtree:true}).filter(a=>a instanceof CSSAnimation).length];d.style.display='none';const hid=document.getAnimations().filter(a=>d.contains(a.effect&&a.effect.target)).length;d.remove();return{s,v0,v1,da,sw,hid}})()")
    ok([x[:2] for x in o['s']] == [[16, 16], [24, 24], [40, 40], [24, 24]], 'orbit loader in 16, 24 and 40 px', o['s'])
    ok(o['s'][0][2] == 2 and o['s'][3][2] == 0 and o['s'][3][3] == 'progressbar', 'orbiting runs on CSS animations only (two per loader); with progress it does not animate on its own', o['s'])
    ok(o['v0'] == '30' and o['v1'] == '75' and o['da'].startswith('75'), 'the orbit fills with the progress', [o['v0'], o['v1'], o['da']])
    ok(o['sw'] == [True, 0], 'an orbiting loader turns into a filling one when progress becomes known', o['sw'])
    ok(o['hid'] == 0, 'hidden loaders run no animation (paused when hidden)', o['hid'])
    bz = J("(()=>{busyOn('Opening test');const b=document.getElementById('busyPill'),r={orb:!!b.querySelector('svg.mdorb.mdo24'),old:!!b.querySelector('canvas'),txt:b.textContent};busyOff();return r})()")
    ok(bz['orb'] and not bz['old'] and 'Opening' in bz['txt'], 'project opening (busy pill) shows the orbit, the old badge is gone', bz)
    lb = J("[ldBadge(14,'a'),ldBadge(20,'b'),ldBadge(22,'c')].map(h=>(/mdo(\\d+)/.exec(h)||[])[1]+(h.includes('<canvas')?'canvas':''))")
    ok(lb == ['16', '24', '24'], 'every old busy badge (bounce, audio to MIDI, listening) is the orbit', lb)
    up = J("(()=>{updOpen();UPD.busy='check';updPaint();const s=document.querySelector('#updDlg .upds'),r={orb:!!s.querySelector('svg.mdorb'),bar:!!s.querySelector('.updbar')};UPD.busy='';updClose&&updClose();return r})()")
    ok(up['orb'] and not up['bar'], 'the update window shows the orbit while it looks for a version', up)
    pg.wait_for_timeout(500)
    cd = J("(()=>{const c=document.createElement('canvas');c.width=60;c.height=60;const g=c.getContext('2d');mdOrbDraw(g,30,30,40,.5,0);const d=g.getImageData(0,0,60,60).data;let n=0,cy=0;for(let i=0;i<d.length;i+=4){if(d[i+3]>40)n++;if(d[i]<120&&d[i+1]>170&&d[i+2]>200&&d[i+3]>150)cy++}return{n,cy}})()")
    ok(cd['n'] > 100 and cd['cy'] > 10, 'the canvas orbit (busy bounce clip) draws orbit, arc and nucleus', cd)
    # the quick stem split shows its progress in the job pill
    sj = J("(()=>{const r=[];mdJob('t','Splitting into stems',0);r.push(document.querySelector('#mdJob span').textContent+document.querySelector('#mdJob b').textContent);mdJob('t','Splitting into stems',.42);r.push(document.querySelector('#mdJob .mdorb').getAttribute('aria-valuenow'));mdJobEnd('t');r.push(document.getElementById('mdJob').hidden);return r})()")
    ok(sj == ['Splitting into stems0%', '42', True], 'the job pill (stem splitter) shows text, orbit and percent, and goes away', sj)
    # a real export: the orbit follows the render's progress
    R("(()=>{EX.fmt='wav';$('#exRange').value='pos';$('#exFolder').checked=false;pos=Math.max(0,loopEnd()-96)})()")
    R("window.__pr=[];window.__done=0;{const _o=mdOrbSet;mdOrbSet=function(root,p){const r=_o.apply(this,arguments);try{const e=document.querySelector('#exTop .mdorb');if(e&&root&&root.id==='exTop')__pr.push([+e.getAttribute('aria-valuenow'),Math.round(performance.now())])}catch(x){}return r}}")
    R("doExport(false).then(()=>{__done=1}).catch(e=>{__done=2;console.log('export',e)})")
    for i in range(600):
        pg.wait_for_timeout(250)
        if R("__done"): break
    pr = [x[0] for x in J("__pr")]; tt = J("__pr")
    print('export', len(pr), 'updates over', (tt[-1][1] - tt[0][1]) if tt else 0, 'ms;', R("(document.getElementById('exTop')||{}).textContent"))
    pr2 = [x for x in pr if x is not None]; pr2 = [x for i, x in enumerate(pr2) if i == 0 or x != pr2[i - 1]]
    ok(len(pr2) > 3 and pr2[-1] == 100 and len(set(pr2)) >= 3 and all(b >= a for a, b in zip(pr2[1:], pr2[2:])), 'an export shows its real progress in the orbit (rising to 100)', pr2[:4] + ['…'] + pr2[-3:])
    ok(not R("!!document.querySelector('#exTop>i')&&getComputedStyle(document.querySelector('#exTop>i')).display!=='none'"), 'the old export bar is not shown')
    shot(pg, 'export_pill', '#exTop')
    # ---------- M3: the caliper ----------
    st = J("(()=>{V.ppb=8;V.x=40;V.y=0;clampV();dirty=true;drawArr();const W=arr.width/(devicePixelRatio*ZOOM),H=arr.height/(devicePixelRatio*ZOOM);for(let i=0;i<S.tracks.length;i++){const t=S.tracks[i];for(const c of t.clips){const G=clipGeom(i,c);if(G.x>X0+40&&G.x+G.w<W-200&&G.w>60&&G.y>AY+30&&G.y+G.h<H-20){const r=arr.getBoundingClientRect();return{i,id:c.id,x:r.left+(G.x+G.w/2)*ZOOM,y:r.top+(G.y+G.h*.6)*ZOOM,xr:r.left+(G.x+G.w-2)*ZOOM,s:c.start,l:c.len,z:ZOOM,ry:r.top+(TY+RUL/2)*ZOOM,rx:r.left+(X0+60)*ZOOM}}}}return null})()")
    ok(st is not None, 'a clip to drag', st)
    if st:
        pg.mouse.move(st['x'], st['y']); pg.mouse.down(); pg.mouse.move(st['x'] + 30, st['y'], steps=4); pg.mouse.move(st['x'] + 72, st['y'], steps=4); pg.wait_for_timeout(300)
        cs = J("mdCalSpan()"); px = J("(()=>{const d=devicePixelRatio*ZOOM,g=arr.getContext('2d'),C=mdCalSpan(),x0=Math.round((X0+(C.a-V.x)*V.ppb)*d),w=Math.round((C.b-C.a)*V.ppb*d),y0=Math.round((Math.max(AY+9,C.y0-8)-24)*d),im=g.getImageData(x0-4,y0,w+8,Math.round(40*d)).data;let n=0;for(let i=0;i<im.length;i+=4)if(im[i]>220&&im[i+1]>150&&im[i+1]<200&&im[i+2]<110)n++;return n})()")
        moved = J("(()=>{const c=S.tracks.flatMap(t=>t.clips).find(c=>c.id==='%s');return c.start})()" % st['id'])
        ok(cs and abs(cs['b'] - cs['a'] - st['l']) < 1e-9 and abs(cs['a'] - moved) < 1e-9, 'moving a clip: the caliper spans the clip (start and length)', [cs, moved, st['l']])
        ok(px > 40, 'the amber dimension line and label are drawn', px)
        shot(pg, 'caliper_move', clip={'x': max(0, st['x'] - 260), 'y': max(0, st['y'] - 110), 'width': 700, 'height': 170})
        pg.mouse.up(); pg.wait_for_timeout(200)
        ok(J("mdCalSpan()") is None, 'gone when the drag ends')
        R("undo()"); pg.wait_for_timeout(200)
        # dragging the right edge
        st2 = J("(()=>{const i=%d,t=S.tracks[i],c=t.clips.find(c=>c.id==='%s'),G=clipGeom(i,c),r=arr.getBoundingClientRect();return{x:r.left+(G.x+G.w-2)*ZOOM,y:r.top+(G.y+G.h*.6)*ZOOM,l:c.len}})()" % (st['i'], st['id']))
        pg.mouse.move(st2['x'], st2['y']); pg.mouse.down(); pg.mouse.move(st2['x'] + 50, st2['y'], steps=5); pg.wait_for_timeout(250)
        k = R("ad&&ad.k"); cs2 = J("mdCalSpan()"); ln = J("S.tracks[%d].clips.find(c=>c.id==='%s').len" % (st['i'], st['id']))
        ok(k in ('res', 'stretch', 'resl') and cs2 and abs(cs2['b'] - cs2['a'] - ln) < 1e-9 and ln != st2['l'], 'dragging the edge: the caliper shows the new length', [k, cs2, ln, st2['l']])
        shot(pg, 'caliper_edge', clip={'x': max(0, st2['x'] - 360), 'y': max(0, st2['y'] - 110), 'width': 700, 'height': 170})
        pg.mouse.up(); R("undo()"); pg.wait_for_timeout(200)
        # drawing a loop in the ruler
        pg.mouse.move(st['rx'], st['ry']); pg.mouse.down(); pg.mouse.move(st['rx'] + 40, st['ry'], steps=4); pg.mouse.move(st['rx'] + 200, st['ry'], steps=6); pg.wait_for_timeout(250)
        cs3 = J("[mdCalSpan(),ad&&ad.k,ad&&ad.lr,loopA(),loopB()]")
        ok(cs3[0] and cs3[2] and abs(cs3[0]['a'] - cs3[3]) < 1e-9 and abs(cs3[0]['b'] - cs3[4]) < 1e-9, 'drawing a loop: the caliper spans the loop', cs3)
        shot(pg, 'caliper_loop', clip={'x': max(0, st['rx'] - 60), 'y': max(0, st['ry'] - 30), 'width': 700, 'height': 120})
        pg.mouse.up(); R("undo()"); pg.wait_for_timeout(200)
        # the setting turns it off
        R("SETT.set('caliper',false)")
        pg.mouse.move(st['x'], st['y']); pg.mouse.down(); pg.mouse.move(st['x'] + 72, st['y'], steps=6); pg.wait_for_timeout(200)
        off = J("[mdCalSpan(),UI.mdCal,document.getElementById('mdCalChk').checked]"); pg.mouse.up(); R("undo()"); R("SETT.reset('caliper')")
        ok(off[0] is None and off[1] is False and off[2] is False, 'Caliper while dragging off: nothing drawn', off)
        ok(R("UI.mdCal")!=False and R("document.getElementById('mdCalChk').checked"), 'back on after reset')
    s = J("(()=>{const r=SETT.get('caliper');return{r:r&&[r.pg,r.d,!!r.h,r.t],f:SETT.find('caliper'),f2:SETT.find('measuring line'),tip:document.getElementById('mdCalChk').closest('.row').title.length,row:!!SETT.row('caliper')}})()")
    ok(s['r'] and s['r'][0] == 'appearance' and s['r'][1] is True and s['r'][2] and 'caliper' in json.dumps(s['f']), 'setting row: Appearance (next to Density and motion), default on, help text, found by search', s)
    ok(s['tip'] > 40, 'the new setting has a tooltip', s['tip'])
    # ---------- Light level ----------
    R("pmSetOn(true)"); pg.wait_for_timeout(800); shot(pg, 'transport_light', '#tr')
    lt2 = J("[...document.querySelectorAll('#tr .mdu')].map(e=>getComputedStyle(e).color)")
    ok(len(lt2) == 3, 'labels at the Light level', lt2)
    R("pmSetOn(false)"); pg.wait_for_timeout(400)
    ok(not logs, 'no console errors', logs[:5])
print('\n%d checks, %d failed' % (N[0], len(FAIL)) + ((': ' + '; '.join(FAIL)) if FAIL else ''))
sys.exit(1 if FAIL else 0)
