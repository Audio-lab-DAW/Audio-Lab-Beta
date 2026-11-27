#!/usr/bin/env python3
"""Glass step 2 (task GS2, v0.227): windows, sheets and menus on the glass engine; backdrop-filter nowhere in the app.
   python3 tools/ui-tests/glass_gs2.py [index.html] [out dir]
The cloud machine has no graphics card (software renderer): only correctness and counters are checked here, frame rates mean nothing."""
import sys, os, json
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
NOGL = "const og=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(t,a){return /webgl/.test(t)?null:og.call(this,t,a)};"
HELP = r"""
window.GT={
 R:c=>AudioLab.run(c),
 L:i=>AudioLab.run('GLF.L')[i],
 /* a layer's own picture, read right after a draw in the same task */
 read(i){const L=GT.L(i),g=L.g;g.render(performance.now());g.debug.draw();const gl=g.gl,w=gl.drawingBufferWidth,h=gl.drawingBufferHeight,b=new Uint8Array(w*h*4),o=new Uint8Array(w*h*4);gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,b);
   for(let j=0;j<h;j++)o.set(b.subarray((h-1-j)*w*4,(h-j)*w*4),j*w*4);o.w=w;o.h=h;return o},
 px(b,x,y){const k=((y|0)*b.w+(x|0))*4;return[b[k],b[k+1],b[k+2],b[k+3]]},
 item(sel){const el=document.querySelector(sel);return AudioLab.run('GLF.items').find(i=>i.el===el)||null},
 /* every element and pseudo element: computed backdrop-filter */
 bf(){let n=0,ex=[],all=0;for(const e of document.querySelectorAll('*')){all++;for(const ps of[null,'::before','::after']){const c=getComputedStyle(e,ps),v=c.backdropFilter||c.webkitBackdropFilter;if(v&&v!=='none'){n++;if(ex.length<6)ex.push((e.id||e.className||e.tagName)+(ps||''))}}}return{n,ex,all}},
 stats(){return AudioLab.run('GLF.L').map(L=>L?Object.assign({vis:L.vis},L.g.stats):null)},
 colStats(b,x,y0,y1){let d=0,n=0,mn=[255,255,255],mx=[0,0,0],p=null;for(let y=y0;y<y1;y++){const q=GT.px(b,x,y);for(let c=0;c<3;c++){mn[c]=Math.min(mn[c],q[c]);mx[c]=Math.max(mx[c],q[c])}if(p){d+=Math.abs(q[0]-p[0])+Math.abs(q[1]-p[1])+Math.abs(q[2]-p[2]);n++}p=q}return{fine:d/n/3,spread:Math.max(mx[0]-mn[0],mx[1]-mn[1],mx[2]-mn[2])}},
 wait:ms=>new Promise(r=>setTimeout(r,ms))
};"""

def boot(p, init=None, w=1600, h=1000):
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': w, 'height': h}); pg = ctx.new_page(); logs = []
    def con(m):
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall due to ReadPixels' not in m.text and 'willReadFrequently' not in m.text): logs.append(m.type + ': ' + m.text[:200])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT)
    if init: pg.add_init_script(init)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(4000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}"); pg.evaluate(HELP)
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    R("openDemoFractals()"); pg.wait_for_timeout(5000); pg.evaluate("()=>{const s=document.getElementById('liteNote');if(s)s.remove()}")
    return b, pg, logs, R

def menu_at(R, x, y):
    R("openMenu(%d,%d,[{label:'One',fn:()=>{}},{label:'Two',fn:()=>{}},{label:'Three',fn:()=>{}},'-',{label:'Four',fn:()=>{}}])" % (x, y))

with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    R("pmSetOn(false)"); pg.wait_for_timeout(1500)
    s = json.loads(R("JSON.stringify({v:VERSION,on:GLE.on,lv:GLE.lv,mode:GLF.mode,max:GLF.max,act:GLF.act,L:GLF.L.length,cv:document.querySelectorAll('canvas.glfCv').length})"))
    ok(tuple(map(int, s['v'].split('.'))) >= (0, 227), 'version 0.227 or later', s['v'])
    ok(s['on'] and s['lv'] == 'glass' and s['mode'] == 'layer' and s['max'] == 3, 'Full effects: docked engine at Glass, floating glass in layer mode, at most 3 layers', s)
    ok(not s['act'] and s['cv'] == 0, 'nothing floating open: no floating engine, no extra canvas', s)
    r = pg.evaluate("()=>GT.bf()")
    ok(r['n'] == 0, 'no element or pseudo element has a backdrop-filter (Full effects, nothing open)', r)
    if R("typeof RFX==='undefined'"):   # v0.228 (task GS3, glass step 3): deleted
        ok(R("typeof rfBuild==='undefined'&&typeof rfMap==='undefined'&&typeof rfStyle==='undefined'") and "mk('feImage'" not in SRC and not R("!!document.querySelector('svg filter[id^=rf]')"), 'old lens code deleted (glass step 3): no rfBuild, rfMap, rfStyle, no feImage, no SVG filter in the page')
    else:
        r = json.loads(R("JSON.stringify({svg:!!rfSvg,rfx:RFX.size,old:[typeof rfBuild,typeof rfMap,typeof rfStyle,typeof rfAttach]})"))
        ok(not r['svg'] and r['rfx'] == 0 and r['old'][:4] == ['function'] * 4, 'old lens code still in the file but unused: no SVG filter, no map, nothing attached', r)
        ok("const f=mk('filter'" in SRC and 'function rfMap(' in SRC and 'feImage' in SRC, 'rfAttach, rfBuild, rfMap, rfStyle and the feImage lens are still in the file (step 3 deletes them)')

    # ---- the mixer window ----
    R("openMixer()"); pg.wait_for_timeout(1500)
    s = json.loads(R("JSON.stringify({act:GLF.act,items:GLF.items.map(i=>[i.el.id||i.el.className,i.k,i.lv,i.opaque]),L:GLF.L.map(L=>L&&{vis:L.vis,z:L.z,next:L.cv.nextSibling&&L.cv.nextSibling.id,parent:L.cv.parentElement.tagName,ids:[...L.ids],flats:[...L.flats.keys()],info:L.g.info}),mz:getComputedStyle(document.getElementById('mixWin')).zIndex})"))
    L0 = s['L'][0] if s['L'] else None
    ok(s['act'] and L0 and L0['vis'] and L0['parent'] == 'BODY' and L0['next'] == 'mixWin' and L0['z'] == s['mz'], 'mixer open: one layer, its canvas directly before the mixer in the page with the same z-index', [L0 and L0['next'], L0 and L0['z'], s['mz']])
    ok(L0 and L0['info']['source'] == 'scene' and L0['info']['sceneRects'] > 100 and L0['info']['mode'] == 'gl', 'the layer draws the same rectangle scene on the graphics card', L0 and [L0['info']['source'], L0['info']['sceneRects']])
    kinds = {x[0]: x for x in s['items']}
    ok('mixWin' in kinds and kinds['mixWin'][1] == 'window' and kinds['mixWin'][2] == 0 and len(L0['ids']) == 2, 'mixer window and its tab are two faces in layer 1', [s['items'], L0['ids']])
    ok(any(k.startswith('d:') for k in L0['flats']) and 'd:fxglass' in L0['flats'], 'flat pictures of what is underneath: the docked panels', L0['flats'])
    ok(any(k.startswith('s:') for k in L0['flats']), 'and the device displays (small-copy route)', L0['flats'])
    src = json.loads(R("JSON.stringify(GLF.L.filter(Boolean).map(L=>[...L.flats.keys()].map(k=>{const f=GLF.disp.find(d=>d.k===k);return f?[f.cv.id,f.cv.className,f.cv.width*f.cv.height]:null}).filter(Boolean)))"))
    flat_src = [x for l in src for x in l]
    ok(flat_src and all('glfCv' not in x[1] and x[0] != 'glassCv' for x in flat_src), 'glass never samples glass: no flat source is an engine canvas', flat_src[:4])
    up = json.loads(R("JSON.stringify(GLF.L[0].g.stats)"))
    ok(up['uploadPixels'] <= max(x[2] for x in flat_src) // 16 + 64, 'displays go up as small copies (largest copy %d px, display %d px)' % (up['uploadPixels'], max(x[2] for x in flat_src)), up['uploadPixels'])
    r = pg.evaluate("()=>GT.bf()")
    ok(r['n'] == 0, 'mixer open: no backdrop-filter anywhere (the tab .fwh and the pan handles .ck included)', r)
    r = pg.evaluate("()=>{const c=getComputedStyle(document.querySelector('#mixWin .mxp .cs .ck')||document.body),t=getComputedStyle(document.querySelector('#mixWin>.fwh'));return [c.backdropFilter,t.backdropFilter]}")
    ok(r == ['none', 'none'], 'nested blurs in the mixer are gone: tab and pan handle', r)
    # pixels of the layer under the mixer
    m = pg.evaluate("()=>{const it=GT.item('#mixWin');return it&&it.R}")
    pg.evaluate("()=>{window.__b=GT.read(0)}")
    r = pg.evaluate("""(m)=>{const b=window.__b,x0=Math.round(m[0]),y0=Math.round(m[1]),x1=Math.round(m[0]+m[2]),y1=Math.round(m[1]+m[3]);
       const a=[GT.px(b,x0+m[2]/2,y0+m[3]/2)[3],GT.px(b,x0+60,y0+60)[3],GT.px(b,x1-60,y1-60)[3]],out=[GT.px(b,x1+30,y0+40)[3],GT.px(b,x0+m[2]/2,y1+30)[3]];
       const cs=GT.colStats(b,Math.round(x0+m[2]*.4),y0+50,y1-50);return{a,out,cs}}""", m)
    ok(min(r['a']) == 255 and max(r['out']) == 0, 'the face is opaque under the mixer and the layer is empty beside it', r)
    ok(r['cs']['fine'] < 1.6 and r['cs']['spread'] > 12, 'under the mixer the arrangement is frosted: colours of the track rows, no fine detail', r['cs'])
    # lens on the mixer: Off against Wide changes the rim, not the middle
    pg.evaluate("()=>{window.__w=GT.read(0)}")
    R("gleSet('lens','off')"); pg.wait_for_timeout(500); pg.evaluate("()=>{window.__o=GT.read(0)}")
    r = pg.evaluate("""(m)=>{const a=window.__w,o=window.__o,x0=Math.round(m[0]),y0=Math.round(m[1]);let rim=0,mid=0;
       /* the whole rim (a ring 40 px wide inside the face) against the middle (more than 100 px in); one edge alone can lie over a single flat colour, where a bend changes nothing */
       const x1=Math.round(m[0]+m[2]),y1=Math.round(m[1]+m[3]);for(let y=y0+2;y<y1-2;y+=2)for(let x=x0+2;x<x1-2;x+=2){const p=GT.px(a,x,y),q=GT.px(o,x,y),d=Math.abs(p[0]-q[0])+Math.abs(p[1]-q[1])+Math.abs(p[2]-q[2]),e=Math.min(x-x0,x1-x,y-y0,y1-y);
         if(e<40)rim=Math.max(rim,d);else if(e>100)mid=Math.max(mid,d)}return{rim,mid}}""", m)
    ok(r['rim'] > 6 and r['mid'] <= 3, 'lens Wide bends the mixer face at its edge, the middle stays flat (Wide against Off)', r)
    R("gleSet('lens','wide')"); pg.wait_for_timeout(400)
    pg.screenshot(path=OUT + '/gs2-mixer-glass.png')

    # ---- uploads 0 while scrolling and playing; the list is not sent again ----
    s0 = pg.evaluate("()=>GT.stats()")[0]; g0 = json.loads(R("JSON.stringify(GLE.g.stats)"))
    for i in range(30):
        R("(()=>{V.x+=0.5;dirty=true})()"); pg.wait_for_timeout(30)
    R("(()=>{pos=40;UI.follow=false;start()})()"); pg.wait_for_timeout(2500); R("stop()"); pg.wait_for_timeout(300)
    s1 = pg.evaluate("()=>GT.stats()")[0]; g1 = json.loads(R("JSON.stringify(GLE.g.stats)"))
    ok(s1['uploads'] == 0 and g1['uploads'] == 0, 'upload counter 0 for the arrangement scene while scrolling and playing (floating layer and docked engine)', [s1['uploads'], g1['uploads']])
    ok(s1['sceneSends'] == s0['sceneSends'] and s1['sceneDraws'] > s0['sceneDraws'], 'scrolling and playing: the rectangle list is not sent again, the backdrop is redrawn (uniforms)', [s0['sceneSends'], s1['sceneSends'], s0['sceneDraws'], s1['sceneDraws']])

    # ---- dragging the mixer: one quad redraw per move, no scene, no backdrop, no pyramid ----
    # over the arrangement, away from the device displays (they are refreshed under glass on their own)
    R("(()=>{const w=document.getElementById('mixWin');w.style.left='40px';w.style.top='50px'})()"); pg.wait_for_timeout(600)
    h = pg.evaluate("()=>{const t=document.querySelector('#mixWin>.fwh'),r=t.getBoundingClientRect();for(let x=r.left+3;x<r.right;x+=4){const e=document.elementFromPoint(x,r.top+r.height/2);if(e&&t.contains(e)&&!e.closest('button,select,input,.seg'))return [x,r.top+r.height/2]}return [r.left+5,r.top+r.height/2]}")
    r0 = pg.evaluate("()=>document.getElementById('mixWin').getBoundingClientRect().left")
    s0 = pg.evaluate("()=>GT.stats()")[0]; n0 = json.loads(R("JSON.stringify(GLF.n)"))
    pg.mouse.move(h[0], h[1]); pg.mouse.down()
    for i in range(1, 25):
        pg.mouse.move(h[0] + i * 6, h[1] + i); pg.wait_for_timeout(25)
    r1 = pg.evaluate("()=>document.getElementById('mixWin').getBoundingClientRect().left")   # measured during the drag (on release the mixer's own placement takes over)
    pg.mouse.up(); pg.wait_for_timeout(300)
    s1 = pg.evaluate("()=>GT.stats()")[0]; n1 = json.loads(R("JSON.stringify(GLF.n)"))
    moved = r1 - r0
    ok(moved > 60, 'the mixer was dragged with the mouse (%d px)' % moved, moved)
    same = {k: (s0[k], s1[k]) for k in ['sceneSends', 'sceneDraws', 'pyramids', 'flatPyramids', 'uploads', 'flatUploads']}
    ok(all(a == b for a, b in same.values()) and s1['draws'] - s0['draws'] >= 10, 'dragging the mixer: %d face redraws, 0 lists sent, 0 backdrops drawn, 0 pyramid or flat-pyramid builds' % (s1['draws'] - s0['draws']), same)
    ok(n1['regroup'] == n0['regroup'] and n1['made'] == n0['made'], 'and no new layer or regrouping', [n0['regroup'], n1['regroup']])

    # ---- a menu over the mixer: the next layer, sees the mixer as a flat picture ----
    m = pg.evaluate("()=>GT.item('#mixWin').R")
    menu_at(R, int(m[0] + 300), int(m[1] + 120)); pg.wait_for_timeout(700)
    s = json.loads(R("JSON.stringify({items:GLF.items.map(i=>[i.el.id||i.el.className,i.lv]),L:GLF.L.map(L=>L&&{vis:L.vis,z:L.z,next:L.cv.nextSibling&&L.cv.nextSibling.id,flats:[...L.flats.keys()],ids:[...L.ids]}),cz:getComputedStyle(document.getElementById('ctxm')).zIndex,mid:document.getElementById('mixWin')._glf})"))
    L1 = s['L'][1] if len(s['L']) > 1 else None
    ok(L1 and L1['vis'] and L1['next'] == 'ctxm' and L1['z'] == s['cz'] and ['ctxm', 1] in s['items'], 'menu over the mixer: layer 2, directly before the menu with its z-index', [L1, s['cz'], s['items']])
    ok(L1 and ('w:' + s['mid']) in L1['flats'], 'the menu sees the mixer as a flat picture (glass never samples glass)', L1 and L1['flats'])
    mr = pg.evaluate("()=>GT.item('#ctxm').R")
    pg.evaluate("()=>{window.__m=GT.read(1)}")
    r = pg.evaluate("""(m)=>{const b=window.__m,p=GT.px(b,m[0]+m[2]/2,m[1]+m[3]/2),q=GT.px(b,m[0]+m[2]+40,m[1]+m[3]/2);const cs=GT.colStats(b,Math.round(m[0]+m[2]/2),Math.round(m[1]+20),Math.round(m[1]+m[3]-20));return{p,q,cs}}""", mr)
    mc = json.loads(R("JSON.stringify(GT.item('#mixWin').bg.map(v=>Math.round(v*255)))"))
    ok(r['p'][3] == 255 and r['q'][3] == 0, 'menu face opaque, layer 2 empty beside the menu', r)
    d = max(abs(r['p'][i] - mc[i]) for i in range(3))
    ok(d <= 40 and r['cs']['fine'] < 1.5, 'pixel check on the menu: its glass shows the mixer colour, frosted (difference %d of 255 to the mixer colour)' % d, [r['p'], mc, r['cs']])
    r = pg.evaluate("()=>GT.bf()")
    ok(r['n'] == 0, 'menu open: no backdrop-filter anywhere', r)
    pg.screenshot(path=OUT + '/gs2-menu-over-mixer.png')
    R("closeMenu()"); pg.wait_for_timeout(400)
    s = json.loads(R("JSON.stringify(GLF.L.map(L=>L&&{vis:L.vis,hid:L.cv.hidden,ids:L.ids.size}))"))
    ok(s[1] and not s[1]['vis'] and s[1]['hid'] and s[1]['ids'] == 0, 'menu closed: layer 2 hidden, no panels', s)
    # a menu over the arrangement only: layer 1 is enough
    m = pg.evaluate("()=>GT.item('#mixWin').R")
    menu_at(R, 1380, int(m[1] + m[3] + 60)); pg.wait_for_timeout(600)
    s = json.loads(R("JSON.stringify(GLF.items.map(i=>[i.el.id||i.el.className,i.lv]))"))
    ok(['ctxm', 0] in s, 'a menu that covers no other floating glass stays in layer 1', s)
    R("closeMenu()"); pg.wait_for_timeout(300)

    # ---- sheets: Settings and askChoice ----
    R("openSettings()"); pg.wait_for_timeout(1200)
    s = json.loads(R("JSON.stringify(GLF.items.map(i=>[i.el.parentElement.id||i.el.id,i.k,i.lv,i.opaque]))"))
    st = [x for x in s if x[0] == 'set']
    ok(st and st[0][1] == 'sheet' and not st[0][3], 'Settings sheet has a face', s)
    r = pg.evaluate("()=>GT.bf()"); ok(r['n'] == 0, 'Settings open: no backdrop-filter anywhere', r)
    ui = pg.evaluate("()=>{const b=document.getElementById('glBox');return b?{head:b.previousElementSibling.textContent,t:b.textContent+[...b.querySelectorAll('[title]')].map(e=>e.title).join(' '),r:[...document.querySelectorAll('[data-pr=refr],[data-pr=blur],[data-pr=glPlay]')].map(e=>e.title)}:null}")
    ok(ui and 'windows, sheets and menus' in ui['head'] and all('changes nothing now' in t for t in ui['r']) and not any(c in ui['t'] for c in '—–'), 'Settings, Performance: the glass block covers windows, sheets and menus; the old switches say they change nothing now; no em dash', ui and [ui['head'], ui['r']])
    pg.screenshot(path=OUT + '/gs2-settings.png')
    R("closeSettings()") if R("typeof closeSettings==='function'") else pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    R("(window.__ac=askChoice('Delete this?','A short question for the test.',[{label:'Cancel',v:0},{label:'Delete',v:1}]),0)"); pg.wait_for_timeout(800)
    s = json.loads(R("JSON.stringify(GLF.items.map(i=>[i.el.parentElement.id,i.k,i.lv,i.opaque]))"))
    cd = [x for x in s if x[0] == 'cdlg']
    ok(cd and cd[0][1] == 'sheet' and not cd[0][3], 'askChoice window has a face', s)
    L = json.loads(R("JSON.stringify(GLF.L.map(L=>L&&{vis:L.vis,next:L.cv.nextSibling&&L.cv.nextSibling.id}))"))
    ok(any(l and l['vis'] and l['next'] == 'cdlg' for l in L), 'its layer canvas sits directly before it in the page', L)
    pg.screenshot(path=OUT + '/gs2-askchoice.png')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(500)

    # ---- the other floating windows the app makes ----
    sel = R("JSON.stringify(GLFSEL.map(x=>x[0]))")
    ok(all(x in sel for x in ['.fwin', '.abxw', '#uywM .uyww', '.modal>.sheet', '#ctxm', '.pop']), 'covered: floating windows, sidechain window, update window, sheets (askChoice, audio to MIDI), menus and pop-ups', sel)

    # ---- context loss on a floating layer ----
    menu_at(R, 1380, 300); pg.wait_for_timeout(400); R("closeMenu()")
    pg.evaluate("()=>GT.L(0).g.debug.lose()"); pg.wait_for_function("()=>AudioLab.run('GLF.L[0].g.mode')==='fallback'", timeout=8000); pg.wait_for_timeout(500)
    r = pg.evaluate("()=>({mode:GT.L(0).g.mode,n:document.querySelectorAll('canvas.glfCv').length})")
    ok(r['mode'] == 'fallback', 'context lost on the floating layer: the engine shows its solid look', r)
    pg.evaluate("()=>GT.L(0).g.debug.restore()"); pg.wait_for_function("()=>AudioLab.run('GLF.L[0].g.mode')==='gl'", timeout=8000); pg.wait_for_timeout(700)
    r = json.loads(R("JSON.stringify({mode:GLF.L[0].g.mode,st:GLF.L[0].g.stats,rects:GLF.L[0].g.info.sceneRects,c:document.querySelectorAll('canvas.glfCv').length})"))
    ok(r['mode'] == 'gl' and r['st']['restored'] >= 1 and r['rects'] > 100, 'context restored: glass back, scene sent again by the engine', [r['mode'], r['st']['restored'], r['rects'], r['c']])

    # ---- levels ----
    R("pmSetStop(1)"); pg.wait_for_timeout(1500)
    s = json.loads(R("JSON.stringify({lv:GLE.lv,L:GLF.L.map(L=>L&&{lv:L.g.info.level,lens:L.g.info.lens,vis:L.vis})})"))
    ok(s['lv'] == 'light' and s['L'][0] and s['L'][0]['lv'] == 'light' and s['L'][0]['lens'] == 'off', 'Lighter: the floating glass is at Light too (lens off)', s)
    pg.screenshot(path=OUT + '/gs2-mixer-light.png')
    r = pg.evaluate("()=>GT.bf()"); ok(r['n'] == 0, 'Lighter: no backdrop-filter anywhere', r)
    R("pmSetStop(0)"); pg.wait_for_timeout(1500)
    s = json.loads(R("JSON.stringify({on:GLE.on,L:GLF.L.length,c:document.querySelectorAll('canvas.glfCv').length,bg:getComputedStyle(document.getElementById('mixWin')).backgroundColor})"))
    ok(not s['on'] and s['L'] == 0 and s['c'] == 0 and s['bg'].startswith('rgb('), 'Lightest: no floating engine, no canvas, the mixer is solid', s)
    r = pg.evaluate("()=>GT.bf()"); ok(r['n'] == 0, 'Lightest: no backdrop-filter anywhere', r)
    R("pmSetOn(false)"); pg.wait_for_timeout(1200)
    R("gleSet('lv','solid')"); pg.wait_for_timeout(1000)
    s = json.loads(R("JSON.stringify({on:GLE.on,L:GLF.L.length,bg:getComputedStyle(document.getElementById('mixWin')).backgroundColor})"))
    ok(not s['on'] and s['L'] == 0 and s['bg'].startswith('rgb('), 'Solid picked by hand: solid mixer, no floating engine', s)
    r = pg.evaluate("()=>GT.bf()"); ok(r['n'] == 0, 'Solid: no backdrop-filter anywhere', r)
    R("gleSet('lv',null)"); pg.wait_for_timeout(1200)

    # ---- face mode (the other way the task asked to measure): works, and a move rebuilds the backdrop ----
    R("GLF.mode='face';glfReset()"); pg.wait_for_timeout(1000)
    s0 = json.loads(R("JSON.stringify({L:GLF.L.map(L=>L&&{fit:L.fit,st:Object.assign({},L.g.stats)}),n:GLF.n.move})"))
    R("(()=>{const w=document.getElementById('mixWin');w.style.left=(parseFloat(w.style.left)+80)+'px'})()"); pg.wait_for_timeout(400)
    s1 = json.loads(R("JSON.stringify({L:GLF.L.map(L=>L&&{fit:L.fit,st:Object.assign({},L.g.stats)}),n:GLF.n.move})"))
    ok(s0['L'][0] and s0['L'][0]['fit'] and s1['L'][0]['fit'] != s0['L'][0]['fit'] and s1['L'][0]['st']['pyramids'] + s1['L'][0]['st']['flatPyramids'] > s0['L'][0]['st']['pyramids'] + s0['L'][0]['st']['flatPyramids'], 'face mode: the canvas fits the window and moves with it, but each move rebuilds the blur (why layer mode is the default)', [s0['L'][0] and s0['L'][0]['fit'], s1['L'][0]['fit']])
    R("GLF.mode='layer';glfReset()"); pg.wait_for_timeout(800)

    # ---- the Ableton light theme with the mixer and a menu ----
    pg.evaluate("()=>{const b=document.createElement('button');b.dataset.dl='ableton';document.body.appendChild(b);b.click();b.remove()}"); pg.wait_for_timeout(1500)
    m = pg.evaluate("()=>GT.item('#mixWin').R")
    menu_at(R, int(m[0] + 300), int(m[1] + 150)); pg.wait_for_timeout(600)
    pg.screenshot(path=OUT + '/gs2-ableton-mixer-menu.png'); R("closeMenu()")
    pg.evaluate("()=>{const b=document.createElement('button');b.dataset.dl='audiolab';document.body.appendChild(b);b.click();b.remove()}"); pg.wait_for_timeout(800)
    ok(not logs, 'no console errors', logs[:6])
    b.close()

    # ---- without WebGL2: Solid ----
    b, pg, logs, R = boot(p, NOGL)
    R("pmSetOn(false)"); pg.wait_for_timeout(1200); R("openMixer()"); pg.wait_for_timeout(1200)
    menu_at(R, 900, 300); pg.wait_for_timeout(500)
    s = json.loads(R("JSON.stringify({fail:GLE.fail,on:GLE.on,L:GLF.L.length,c:document.querySelectorAll('canvas.glfCv').length,bg:getComputedStyle(document.getElementById('mixWin')).backgroundColor,mb:getComputedStyle(document.getElementById('ctxm')).backgroundColor,gls:document.body.classList.contains('gls')})"))
    ok(s['fail'] != '' and not s['on'] and s['L'] == 0 and s['c'] == 0 and s['bg'].startswith('rgb(') and s['mb'].startswith('rgb(') and s['gls'], 'WebGL2 switched off: Solid, no floating engine, mixer and menu solid', s)
    r = pg.evaluate("()=>GT.bf()"); ok(r['n'] == 0, 'without WebGL2: no backdrop-filter anywhere', r)
    pg.screenshot(path=OUT + '/gs2-nogl-solid.png'); R("closeMenu()")
    R("(()=>{pos=30;start()})()"); pg.wait_for_timeout(1500); R("stop()")
    ok(not logs, 'without WebGL2: no console errors', logs[:6])
    b.close()

print('\n%d checks, %d failed' % (N[0], len(FAIL)))
for f in FAIL: print('FAILED:', f)
sys.exit(1 if FAIL else 0)
