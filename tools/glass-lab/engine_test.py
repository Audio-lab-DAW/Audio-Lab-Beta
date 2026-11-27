#!/usr/bin/env python3
"""Headless checks for tools/glass-lab/glass-engine.js and engine-test.html.
Run: python3 tools/glass-lab/engine_test.py      (needs Python Playwright with Chromium)
The cloud machine has no GPU (software renderer), so only correctness is checked here; frame rates mean nothing.
Default path: the engine draws its own backdrop on the GPU (setScene); the small copy of a canvas (setBackdrop) is the fallback.
GLASS_UNIT_ONLY=1 skips the test page; GLASS_OUT=dir is where the screenshots go."""
import os, sys, json
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = ["--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
RES, LOGS = [], []

def ok(name, cond, detail=''):
    RES.append((name, bool(cond), detail))
    print(('PASS ' if cond else 'FAIL ') + name + (('   ' + str(detail)) if detail != '' else ''), flush=True)

def watch(pg):
    def con(m):
        # SwiftShader prints a driver performance note when a 2D canvas is uploaded; it is not an error
        if m.type == 'error' or (m.type == 'warning' and 'GPU stall due to ReadPixels' not in m.text and 'willReadFrequently' not in m.text): LOGS.append(m.type + ': ' + m.text)   # the second note comes from this test reading the fallback canvas back
    pg.on('console', con); pg.on('pageerror', lambda e: LOGS.append('pageerror: ' + str(e)))

HELP = r"""
window.T = {
  // a picture where red = x and green = y (one step per pixel up to 255), so the place a glass pixel was taken from can be read back
  ramp(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'), d = x.createImageData(w, h);
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) { const k = (j * w + i) * 4; d.data[k] = Math.min(255, i); d.data[k + 1] = Math.min(255, j); d.data[k + 2] = 0; d.data[k + 3] = 255; }
    x.putImageData(d, 0, 0); return c; },
  stripes(w, h, t) { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'); x.fillStyle = '#101018'; x.fillRect(0, 0, w, h);
    for (let i = 0; i < w; i += 16) { x.fillStyle = ['#e5534b', '#4c8dff', '#e3b341', '#3ecf8e'][(i / 16 + (t | 0)) & 3]; x.fillRect(i, 0, 8, h); } return c; },
  flat(w, h, col) { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'); x.fillStyle = col; x.fillRect(0, 0, w, h); return c; },
  make(w, h, opts) { const c = document.createElement('canvas'); c.style.cssText = 'position:absolute;left:0;top:0;width:' + w + 'px;height:' + h + 'px'; document.body.appendChild(c);
    const g = AudioLabGlass.create(c, Object.assign({ allowSoftware: true, autoResize: false, dpr: 1 }, opts || {})); g.resize(w, h, 1); return g; },
  // the whole frame, top row first. Call right after render(), in the same task.
  read(g) { const gl = g.gl, w = gl.drawingBufferWidth, h = gl.drawingBufferHeight, b = new Uint8Array(w * h * 4), o = new Uint8Array(w * h * 4);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, b);
    for (let j = 0; j < h; j++) o.set(b.subarray((h - 1 - j) * w * 4, (h - j) * w * 4), j * w * 4); o.w = w; o.h = h; return o; },
  px(b, x, y) { const k = (y * b.w + x) * 4; return [b[k], b[k + 1], b[k + 2], b[k + 3]]; },
  maxDiff(a, b, x0, y0, x1, y1) { let m = 0; for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) { const k = (y * a.w + x) * 4; for (let c = 0; c < 4; c++) m = Math.max(m, Math.abs(a[k + c] - b[k + c])); } return m; },
  plain: { rim: { base: 0, lit: 0 }, face: { sat: 1, mul: 1, add: 0 } }
};
"""

def unit_page(b, init=None, dsf=1):
    ctx = b.new_context(viewport={'width': 800, 'height': 600}, device_scale_factor=dsf)
    pg = ctx.new_page(); watch(pg)
    if init: pg.add_init_script(init)
    pg.goto('about:blank'); pg.add_script_tag(path=os.path.join(HERE, 'glass-engine.js'))
    pg.evaluate(HELP)
    return ctx, pg

def unit_tests(b):
    import math
    ctx, pg = unit_page(b)
    # ---- 1. lens: rim bends by Apple's profile, the middle is flat (small-copy route: a picture whose colour is its coordinate) ----
    r = pg.evaluate(r"""()=>{ const g=T.make(256,256,Object.assign({blur:'light'},T.plain)); g.setBackdrop(T.ramp(256,256));
      g.addPanel({id:'a',rect:[28,28,200,200],radius:16,kind:'window',tintAmount:0,shadow:0});
      const out={}; for(const l of ['off','fine','apple','wide']){ g.setLensPreset(l); g.render(); const b=T.read(g), row=[];
        for(const dd of [2,5,10,15,19,25,40,48,100]) row.push([dd, T.px(b,28+dd,128)[0]-(28+dd), T.px(b,128,28+dd)[1]-(28+dd), T.px(b,227-dd,128)[0]-(227-dd)]);
        out[l]=row; out[l+'_mid']=T.px(b,128,128); out[l+'_out']=T.px(b,10,128); }
      out.info=g.info; out.def=AudioLabGlass.create(document.createElement('canvas'),{forceFallback:true}).info; g.destroy(); return out; }""")
    def expect(dd, band, amt):
        x = min(1, max(0, (dd + .5) / band)); return (1 - math.sqrt(max(0, 1 - (1 - x) ** 2))) * amt
    worst = 0
    for name, band, amt in [('fine', 12, 24), ('apple', 20, 24), ('wide', 45, 54)]:
        for dd, left, topv, right in r[name]:
            e = expect(dd, band, amt); worst = max(worst, abs(left - e), abs(topv - e), abs(right + e))
    ok('defaults: lens wide (up to 45 px), blur light, level glass', r['def']['lens'] == 'wide' and r['def']['blur'] == 'light' and r['def']['level'] == 'glass' and AUDIT_LENS(pg) == [3, 45], [r['def']['lens'], r['def']['blur'], r['def']['level']])
    ok('lens: rim displacement follows the quarter-circle profile on left, top and right edges (fine, Apple, wide 45)', worst <= 2.5, 'worst error %.2f px' % worst)
    ok('lens: band is min(short side / 4, 20) for Apple (200 px panel: 20 px; nothing bends at 25 px and beyond)', all(abs(v[1]) <= 1 for v in r['apple'] if v[0] >= 25) and r['apple'][0][1] > 10, 'at 2 px: %d px, at 25 px: %d px' % (r['apple'][0][1], r['apple'][5][1]))
    ok('lens wide: bends up to 45 px from the edge, nothing at 48 px and beyond', r['wide'][5][1] >= 3 and all(abs(v[1]) <= 1 for v in r['wide'] if v[0] >= 48) and r['wide'][0][1] > 25, 'at 2 px: %d px, at 25 px: %d px, at 48 px: %d px' % (r['wide'][0][1], r['wide'][5][1], r['wide'][7][1]))
    ok('lens off: nothing bends anywhere', all(abs(v[1]) <= 1 and abs(v[2]) <= 1 for v in r['off']))
    ok('middle is flat: same pixel with every lens preset', len({tuple(r[l + '_mid']) for l in ['off', 'fine', 'apple', 'wide']}) == 1, r['apple_mid'])
    ok('outside the panel the canvas is transparent', r['apple_out'] == [0, 0, 0, 0], r['apple_out'])

    # the same on the scene path: 64 clips, each 4 px wide, whose red is their x, drawn on the GPU
    r = pg.evaluate(r"""()=>{ const g=T.make(256,256,Object.assign({blur:'light'},T.plain)); const clips=[]; for(let i=0;i<64;i++) clips.push({x:i*4,y:0,w:4,h:256,color:[(i*4+1.5)/255,0,0],alpha:1,titleH:0});
      g.setScene({clips}); g.addPanel({id:'a',rect:[28,28,200,200],radius:16,kind:'window',tintAmount:0,shadow:0});
      const out={}; for(const l of ['off','wide']){ g.setLensPreset(l); g.render(); const b=T.read(g), row=[];
        for(const dd of [2,5,10,15,19,25,40,48,100]) row.push([dd, T.px(b,28+dd,128)[0]-(28+dd), T.px(b,227-dd,128)[0]-(227-dd)]); out[l]=row; }
      out.st={...g.stats}; out.src=g.info.source; g.destroy(); return out; }""")
    worst = max(max(abs(l - expect(dd, 45, 54)), abs(rt + expect(dd, 45, 54))) for dd, l, rt in r['wide'])
    ok('scene path: the rim bends the GPU-drawn backdrop by the same profile (wide), lens off bends nothing, no canvas uploaded', worst <= 2.5 and all(abs(v[1]) <= 1 for v in r['off']) and r['st']['uploads'] == 0 and r['src'] == 'scene', 'worst error %.2f px, uploads %d' % (worst, r['st']['uploads']))

    # lens band follows the panel size: a 48 px bar gets 12 px with Apple, 16 px with wide (48 / 3); a 32 px pill 8 px.
    # Measured as how far in the bend is still 2 px or more (by the profile: 7, 10 and 4 px)
    r = pg.evaluate(r"""()=>{ const g=T.make(256,256,Object.assign({blur:'light',lens:'apple'},T.plain)); g.setBackdrop(T.ramp(256,256));
      g.addPanel({id:'a',rect:[20,100,216,48],radius:0,kind:'docked',tintAmount:0}); g.render(); let b=T.read(g);
      const bar=[]; for(let d=0;d<24;d++) bar.push(T.px(b,128,100+d)[1]-(100+d));
      g.setLensPreset('wide'); g.render(); b=T.read(g); const barW=[]; for(let d=0;d<24;d++) barW.push(T.px(b,128,100+d)[1]-(100+d)); g.setLensPreset('apple');
      g.updatePanel('a',{rect:[40,100,150,32],radius:16}); g.render(); b=T.read(g); const pill=[]; for(let d=0;d<16;d++) pill.push(T.px(b,115,100+d)[1]-(100+d)); g.destroy(); return {bar,barW,pill}; }""")
    band = lambda v: max(i for i, x in enumerate(v) if x >= 2) + 1
    ok('lens width follows the panel: 48 px bar band 12 px (Apple) and 16 px (wide), 32 px pill 8 px (a bend of 2 px or more reaches 7, 10 and 4 px in)', 6 <= band(r['bar']) <= 8 and 9 <= band(r['barW']) <= 11 and 3 <= band(r['pill']) <= 5, 'bar %d px, bar wide %d px, pill %d px' % (band(r['bar']), band(r['barW']), band(r['pill'])))

    # ---- 2. no corner seam ----
    r = pg.evaluate(r"""()=>{ const res={}; for(const l of ['apple','wide']) for(const rad of [0,6,16]){ const g=T.make(256,256,Object.assign({blur:'light',lens:l},T.plain)); g.setBackdrop(T.ramp(256,256));
      g.addPanel({id:'a',rect:[28,28,200,200],radius:rad,kind:'window',tintAmount:0,shadow:0}); g.render(); const b=T.read(g);
      let worst=0, inward=true, n=0;
      for(let i=1;i<34;i++){ // pairs on the two sides of the corner diagonal, 1.4 px apart
        const p=T.px(b,28+i+1,28+i), q=T.px(b,28+i,28+i+1); if(p[3]<255||q[3]<255) continue; n++;
        const v1=[p[0]-(28+i+1),p[1]-(28+i)], v2=[q[0]-(28+i),q[1]-(28+i+1)], dv=Math.hypot(v1[0]-v2[0],v1[1]-v2[1]), len=Math.hypot(v1[0],v1[1]);
        worst=Math.max(worst, dv-0.15*len); if(v1[0]<-1||v1[1]<-1||v2[0]<-1||v2[1]<-1) inward=false; }
      res[l+rad]={worst,inward,n}; g.destroy(); } return res; }""")
    ok('no corner seam: bending direction is continuous across the corner diagonal (Apple and wide, radius 0, 6, 16)', all(v['worst'] <= 3 and v['inward'] and v['n'] > 10 for v in r.values()), json.dumps({k: round(v['worst'], 2) for k, v in r.items()}))

    # ---- 3. the GPU-drawn backdrop is the right picture ----
    r = pg.evaluate(r"""()=>{ const o={}, g=T.make(512,256,Object.assign({blur:'light',lens:'off'},T.plain));
      const sc={bg:[0,0,0], lanes:[{y:0,h:128,color:'rgb(0, 0, 255)'},{y:128,h:128,color:'rgba(0,0,0,1)'}],
        clips:[{x:0,y:0,w:120,h:128,color:[1,0,0],alpha:1,titleH:64},{x:200,y:128,w:120,h:128,color:'#00ff00',alpha:.5,titleH:0},{x:360,y:128,w:120,h:128,color:[0,0,1],alpha:1,titleH:0,selected:true}], selColor:[1,1,1,.5]};
      g.setScene(sc); g.addPanel({id:'a',rect:[0,0,512,256],kind:'docked',tintAmount:0}); g.render(); let b=T.read(g);
      o.title=T.px(b,60,32); o.body=T.px(b,60,96); o.lane=T.px(b,300,64); o.half=T.px(b,260,192); o.bg=T.px(b,160,192); o.sel=T.px(b,420,192);
      g.setPlayhead(300); g.render(); b=T.read(g); o.ph=T.px(b,300,64); o.phFar=T.px(b,340,64);
      g.setScene({playheadW:40}); g.render(); b=T.read(g); o.phWide=T.px(b,300,64); g.setScene({playheadW:1}); g.setPlayhead(null);
      g.setView({scrollX:-100}); g.render(); b=T.read(g); o.scrolled=T.px(b,160,96); o.scrolledOld=T.px(b,40,96);
      g.setView({scrollX:0,zoom:2}); g.render(); b=T.read(g); o.zoomed=T.px(b,200,96); o.zoomedOut=T.px(b,280,96);
      g.setView({zoom:1,scrollY:64}); g.render(); b=T.read(g); o.scrollY=T.px(b,60,20); o.laneY=T.px(b,300,20); o.laneY2=T.px(b,160,100);
      g.setView({scrollY:0,rect:[256,0,256,256],originX:20}); g.render(); b=T.read(g); o.rectOut=T.px(b,120,96); o.rectIn=T.px(b,330,96); o.rectLane=T.px(b,480,64);
      o.st={...g.stats}; o.n=g.info.sceneRects; g.destroy(); return o; }""")
    near = lambda a, e, tol=8: all(abs(x - y) <= tol for x, y in zip(a[:3], e))
    ok('scene: clip title band, body, lane background, half-transparent body, background and selection tint have the right colours',
       near(r['title'], [255, 0, 0]) and near(r['body'], [255, 0, 0]) and near(r['lane'], [0, 0, 255]) and near(r['half'], [0, 128, 0]) and near(r['bg'], [0, 0, 0]) and near(r['sel'], [128, 128, 255]),
       'title %s body %s lane %s half %s selected %s' % (r['title'][:3], r['body'][:3], r['lane'][:3], r['half'][:3], r['sel'][:3]))
    ok('scene: a 1 px playhead leaves a faint line at its place and nothing 40 px away; a 40 px one is solid', r['ph'][1] > r['lane'][1] + 8 and near(r['phFar'], [0, 0, 255]) and r['phWide'][1] > 150, 'at the line %s, wide line %s' % (r['ph'][:3], r['phWide'][:3]))
    ok('scene: scrollX moves the clips (uniform only), zoom scales them, scrollY moves lanes and clips', near(r['scrolled'], [255, 0, 0]) and near(r['scrolledOld'], [0, 0, 255]) and near(r['zoomed'], [255, 0, 0]) and near(r['zoomedOut'], [0, 0, 255]) and near(r['scrollY'], [255, 0, 0]) and near(r['laneY'], [0, 0, 255]) and near(r['laneY2'], [0, 0, 0]),
       json.dumps({k: r[k][:3] for k in ['scrolled', 'scrolledOld', 'zoomed', 'zoomedOut', 'scrollY', 'laneY', 'laneY2']}))
    ok('scene: view rectangle and origin place the arrangement on the canvas; outside it the base colour', near(r['rectIn'], [255, 0, 0]) and near(r['rectLane'], [0, 0, 255]) and near(r['rectOut'], [10, 10, 12]), 'inside %s outside %s' % (r['rectIn'][:3], r['rectOut'][:3]))
    ok('scene: all of that with the rectangle list sent twice (start, playhead width) and no canvas upload', r['st']['sceneSends'] == 3 and r['st']['uploads'] == 0 and r['st']['flatUploads'] == 0 and r['n'] == 1 + 2 + 3 + 1 + 1 + 1, r['st'])

    # the GPU-drawn backdrop and a small copy of the same picture give the same glass
    r = pg.evaluate(r"""()=>{ const out={}; for(const lv of ['glass','light']){ const C=T.flat(512,256,'#0a0a0c'), x=C.getContext('2d'), clips=[]; const col=['#e5534b','#4c8dff','#e3b341','#3ecf8e'];
      for(let r=0;r<4;r++) for(let i=0;i<5;i++){ const c={x:16+i*104+r*8,y:r*64+8,w:88,h:48,color:col[(r+i)&3],alpha:1,titleH:16}; clips.push(c); x.fillStyle=c.color; x.fillRect(c.x,c.y,c.w,c.h); }
      const a=T.make(512,256,{level:lv}); a.setScene({clips,bg:'#0a0a0c'}); const b=T.make(512,256,{level:lv}); b.setBackdrop(C);
      for(const g of [a,b]){ g.addPanel({id:'a',rect:[40,24,432,208],radius:14,kind:'window'}); g.render(); }
      out[lv]={d:T.maxDiff(T.read(a),T.read(b),60,44,452,212),ua:a.stats.uploads,ub:b.stats.uploads,px:b.stats.uploadPixels}; a.destroy(); b.destroy(); } return out; }""")
    ok('scene and small copy of the same picture look the same under glass (levels Glass and Light)', all(v['d'] <= 6 and v['ua'] == 0 and v['ub'] == 1 for v in r.values()), json.dumps(r))

    # ---- 4. frosted middle, colour, tint ----
    r = pg.evaluate(r"""()=>{ const out={};
      const energy=(b,x0,x1,y)=>{let e=0;for(let x=x0;x<x1;x++){const p=T.px(b,x,y),q=T.px(b,x+1,y);e+=Math.abs(p[0]-q[0])+Math.abs(p[1]-q[1])+Math.abs(p[2]-q[2])}return e/(x1-x0)};
      // clips 11 px wide every 23 px (does not line up with the quarter-size grid), as a picture and as a scene
      const S=T.flat(512,256,'#101018'), x=S.getContext('2d'), clips=[], col=['#e5534b','#4c8dff','#e3b341','#3ecf8e'];
      for(let i=0;i*23<512;i++){ x.fillStyle=col[i&3]; x.fillRect(i*23,0,11,256); clips.push({x:i*23,y:0,w:11,h:256,color:col[i&3],alpha:1,titleH:0}); }
      const d=x.getImageData(0,0,512,256).data; d.w=512; out.src=energy(d,150,350,128);
      for(const way of ['scene','copy']) for(const lv of ['glass','light']) for(const bl of ['light','regular','heavy']){ const g=T.make(512,256,{blur:bl,level:lv});
        if(way==='scene') g.setScene({clips,bg:'#101018'}); else g.setBackdrop(S);
        g.addPanel({id:'a',rect:[56,28,400,200],radius:16,kind:'window'}); g.render(); const b=T.read(g); out[way+' '+lv+' '+bl]={e:energy(b,150,350,128),mid:T.px(b,256,128),lv:g.info.levels,up:g.stats.uploads}; g.destroy(); }
      return out; }""")
    rows = {k: v for k, v in r.items() if k != 'src'}
    lim = lambda k: (.35 if k.endswith(' light') else .15 if k.endswith('regular') else .04) if ' glass ' in k else (.20 if not k.endswith('heavy') else .05)
    ok('middle is frosted: detail under glass drops to under 35 % of the picture (blur light), 15 % (regular), 4 % (heavy) at Glass; under 20 % at Light; scene and small copy',
       all(v['e'] < r['src'] * lim(k) for k, v in rows.items()), ' | '.join('%s %.0f%%' % (k, 100 * v['e'] / r['src']) for k, v in rows.items()))
    ok('more blur = less detail (light > regular > heavy), on both routes', all(r[w + ' glass light']['e'] > r[w + ' glass regular']['e'] > r[w + ' glass heavy']['e'] for w in ['scene', 'copy']))
    ok('pyramid plan: Glass starts at quarter size (4 / 4,8 / 4,8,16), Light at an eighth (8 / 8 / 8,16)', [r['scene glass ' + k]['lv'] for k in ['light', 'regular', 'heavy']] == [[4], [4, 8], [4, 8, 16]] and [r['scene light ' + k]['lv'] for k in ['light', 'regular', 'heavy']] == [[8], [8], [8, 16]], json.dumps({k: v['lv'] for k, v in rows.items() if k.startswith('scene')}))
    ok('scene route uploads nothing, copy route one small copy each', all(v['up'] == (0 if k.startswith('scene') else 1) for k, v in rows.items()))

    r = pg.evaluate(r"""()=>{ const clips=[]; for(let i=0;i*23<512;i++) clips.push({x:i*23,y:0,w:11,h:256,color:['#e5534b','#4c8dff','#e3b341','#3ecf8e'][i&3],alpha:1,titleH:0}); const out={};
      const amp=(b,x0,x1,y)=>{let lo=255,hi=0;for(let x=x0;x<x1;x++){const v=T.px(b,x,y)[0];lo=Math.min(lo,v);hi=Math.max(hi,v)}return hi-lo};
      for(const lv of ['glass','light']){ const a=T.make(512,256,{level:lv}); a.setScene({clips}); a.addPanel({id:'a',rect:[56,28,400,200],radius:16,kind:'window'}); a.render(); const A=T.read(a);
        const c=T.make(512,256,{level:lv}); c.resize(512,256,2); c.setScene({clips}); c.addPanel({id:'a',rect:[56,28,400,200],radius:16,kind:'window'}); c.render(); const C=T.read(c);
        out[lv]={one:amp(A,150,350,128),two:amp(C,300,700,256),w:C.w,in2:T.px(C,116,256)[3],out2:T.px(C,110,256)[3]}; a.destroy(); c.destroy(); } return out; }""")
    ok('2x screen: the blur is as strong as on a 1x screen (backdrop sized in CSS pixels), panel edges at the right place', all(v['w'] == 1024 and abs(v['one'] - v['two']) <= max(4, .25 * v['one']) and v['in2'] == 255 and v['out2'] < 120 for v in r.values()), json.dumps(r))

    r = pg.evaluate(r"""()=>{ const g=T.make(256,256,{blur:'light',rim:{base:0,lit:0}}); g.setScene({bg:[200/255,100/255,50/255]});
      g.addPanel({id:'a',rect:[28,28,200,200],radius:0,kind:'window',shadow:0}); g.render(); const a=T.px(T.read(g),128,128);
      g.setFace({sat:1.3,mul:1.125,add:.125}); g.render(); const b=T.px(T.read(g),128,128); g.destroy(); return {a,b}; }""")
    # expected: saturation 1.3 around luma, then half tint (22,28,42)
    L = .2126 * 200 + .7152 * 100 + .0722 * 50; exp = [min(255, (L + (c - L) * 1.3)) * .5 + t * .5 for c, t in zip([200, 100, 50], [.086 * 255, .11 * 255, .165 * 255])]
    ok('face colour: saturation 1.3 then half panel tint', all(abs(a - e) <= 2 for a, e in zip(r['a'], exp)), '%s expected %s' % (r['a'][:3], [round(e) for e in exp]))
    ok("face matrix option (Apple's 0.125 / 1.125) brightens the face", r['b'][1] > r['a'][1] + 8, r['b'][:3])

    # ---- 5. glass never samples glass ----
    r = pg.evaluate(r"""()=>{ const S=T.stripes(512,256,0), g=T.make(512,256,{}); g.setBackdrop(S);
      g.addPanel({id:'top',rect:[150,60,200,120],radius:14,kind:'window',z:5}); g.render(); const alone=T.read(g);
      g.addPanel({id:'under',rect:[0,0,512,256],radius:0,kind:'docked',tint:[1,0,0],tintAmount:.9}); g.render(); const both=T.read(g);
      const d=Math.max(T.maxDiff(alone,both,165,60,335,180),T.maxDiff(alone,both,150,75,350,165)), outside=T.px(both,40,128); g.removePanel('top'); g.render(); const und=T.read(g);
      const r={d,outside,under:T.px(und,250,120),top:T.px(both,250,120),uploads:g.stats.uploads,pyr:g.stats.pyramids}; g.destroy(); return r; }""")
    ok('no glass on glass: a window over a red docked panel is pixel-identical to the window alone', r['d'] == 0, 'max difference %d; under panel there %s, window %s' % (r['d'], r['under'][:3], r['top'][:3]))
    ok('...while the docked panel itself is red there', r['under'][0] > 150 and r['top'][0] < 120)

    # ---- 6. dirty logic on the scene path ----
    r = pg.evaluate(r"""()=>{ const clips=[]; for(let i=0;i<400;i++) clips.push({x:i*30,y:(i%4)*64,w:24,h:60,color:'#4c8dff'}); const lanes=[0,1,2,3].map(i=>({y:i*64,h:64,color:i%2?'#101014':'#0c0c10'}));
      const g=T.make(512,256,{}); g.setScene({lanes,clips,playheadX:10,scrollX:0,zoom:1});
      g.addPanel({id:'d',rect:[0,200,512,56],kind:'docked'}); g.addPanel({id:'w',rect:[100,40,200,120],radius:14,kind:'window'});
      const o={}; g.render(); o.first={...g.stats}; o.n=g.info.sceneRects;
      let drew=0; for(let i=0;i<50;i++){ g.updatePanel('w',{rect:[101+i,40,200,120]}); if(g.render()) drew++; } o.move={...g.stats}; o.moveDrew=drew;
      drew=0; for(let i=0;i<50;i++) if(g.render()) drew++; o.idle={...g.stats}; o.idleDrew=drew;
      drew=0; for(let i=0;i<50;i++){ g.updatePanel('w',{rect:[150,40,200,120]}); if(g.render()) drew++; } o.same={...g.stats}; o.sameDrew=drew;
      for(let i=0;i<20;i++){ g.setPlayhead(11+i); g.render(); } o.play={...g.stats};
      for(let i=0;i<20;i++){ g.setPlayhead(30); g.setView({scrollX:0,zoom:1}); g.setScene({playheadX:30,scrollX:0}); g.render(); } o.playSame={...g.stats};
      for(let i=0;i<20;i++){ g.setView({scrollX:i+1}); g.render(); } o.scroll={...g.stats};
      for(let i=0;i<20;i++){ g.setView({zoom:1+i/10}); g.setPlayhead(40+i); g.render(); } o.zoom={...g.stats};
      clips[3].selected=true; g.setScene({clips}); g.render(); o.edit={...g.stats};
      g.setLensPreset('apple'); g.render(); o.lens={...g.stats}; g.setBlurPreset('heavy'); g.render(); o.blur={...g.stats};
      g.updatePanel('w',{visible:false}); g.updatePanel('d',{visible:false}); g.setPlayhead(99); g.setScene({clips}); g.render(); o.hidden={...g.stats};
      g.destroy(); return o; }""")
    f, m, i_, s_, pl, ps, sc, zm, ed, l, bl, hd = (r[k] for k in ['first', 'move', 'idle', 'same', 'play', 'playSame', 'scroll', 'zoom', 'edit', 'lens', 'blur', 'hidden'])
    ok('scene, first frame: rectangles sent once (400 clips), backdrop drawn once, one pyramid, no upload', f['sceneSends'] == 1 and f['sceneDraws'] == 1 and f['pyramids'] == 1 and f['uploads'] == 0 and r['n'] == 1 + 4 + 800 + 1, f)
    ok('scene, moving a panel 50 times: 50 quad redraws, backdrop not drawn again, nothing sent', r['moveDrew'] == 50 and m['sceneDraws'] == 1 and m['sceneSends'] == 1 and m['pyramids'] == 1 and m['draws'] == f['draws'] + 50, m)
    ok('nothing changed: render() does nothing (50 calls, 0 draws)', r['idleDrew'] == 0 and i_['draws'] == m['draws'] and i_['skipped'] == m['skipped'] + 50)
    ok('updatePanel with the same rectangle: nothing drawn', r['sameDrew'] == 0 and s_['draws'] == i_['draws'])
    ok('playhead moves 20 times: backdrop drawn 20 times, the clips are NOT sent again', pl['sceneDraws'] == 21 and pl['sceneSends'] == 1 and pl['pyramids'] == 21 and pl['uploads'] == 0, pl)
    ok('playhead, scroll and zoom set to the values they already have: nothing happens', ps['sceneDraws'] == 21 and ps['draws'] == pl['draws'] and ps['sceneSends'] == 1, ps)
    ok('scrolling 20 times and zooming 20 times: one uniform each, backdrop drawn 40 times, the clips are NOT sent again', sc['sceneDraws'] == 41 and zm['sceneDraws'] == 61 and zm['sceneSends'] == 1 and zm['uploads'] == 0, zm)
    ok('an edit (new clip list): sent once more, drawn once more', ed['sceneSends'] == 2 and ed['sceneDraws'] == 62, ed)
    ok('lens preset change: faces only; blur preset change: backdrop and pyramid again, nothing sent', l['pyramids'] == ed['pyramids'] and l['draws'] == ed['draws'] + 1 and bl['pyramids'] == ed['pyramids'] + 1 and bl['sceneSends'] == 2, [l, bl])
    ok('no visible glass: the canvas is cleared once, nothing is sent and no backdrop drawn', hd['sceneSends'] == bl['sceneSends'] and hd['sceneDraws'] == bl['sceneDraws'] and hd['draws'] == bl['draws'] + 1 and hd['uploads'] == 0, hd)

    # scrolling and playing for one second at 240 frames per second, panel moving: scene path
    r = pg.evaluate(r"""()=>{ const out={}; const clips=[]; for(let i=0;i<300;i++) clips.push({x:i*30,y:(i%4)*64,w:24,h:60,color:'#e5534b'});
      for(const lv of ['glass','light','solid']){ const g=T.make(256,256,{level:lv}); g.setScene({clips}); g.addPanel({id:'w',rect:[20,20,100,100],radius:10,kind:'window'});
      g.render(0); const s0={...g.stats}; let drew=0, pend=0; for(let i=1;i<=240;i++){ g.setView({scrollX:i*3}); g.setPlayhead(i*3+100); g.updatePanel('w',{rect:[20+i%50,20,100,100]}); if(g.render(i*1000/240)) drew++; if(g.pending) pend++; }
      out[lv]={sd:g.stats.sceneDraws-s0.sceneDraws,ss:g.stats.sceneSends-s0.sceneSends,py:g.stats.pyramids-s0.pyramids,up:g.stats.uploads,fu:g.stats.flatUploads,drew,pend,info:g.info}; g.destroy(); } return out; }""")
    ok('level Glass, scrolling and playing at 240 per second: backdrop drawn on every frame, uploads 0, clips sent 0 times', r['glass']['sd'] == 240 and r['glass']['up'] == 0 and r['glass']['fu'] == 0 and r['glass']['ss'] == 0 and r['glass']['drew'] == 240 and r['glass']['info']['lens'] == 'wide', {k: r['glass'][k] for k in ['sd', 'ss', 'up', 'drew']})
    ok('level Light: lens off, backdrop an eighth of the size and drawn 30 times per second, panels still move 240 times, uploads 0', 29 <= r['light']['sd'] <= 31 and r['light']['py'] == r['light']['sd'] and r['light']['up'] == 0 and r['light']['drew'] == 240 and r['light']['pend'] > 150 and r['light']['info']['lens'] == 'off' and r['light']['info']['levels'] == [8] and r['light']['info']['rate'] == 30, {k: r['light'][k] for k in ['sd', 'ss', 'up', 'drew', 'pend']})
    ok('level Solid: no backdrop work at all, panels still move', r['solid']['sd'] == 0 and r['solid']['py'] == 0 and r['solid']['up'] == 0 and r['solid']['drew'] == 240 and r['solid']['info']['isStatic'], {k: r['solid'][k] for k in ['sd', 'py', 'up', 'drew']})

    # ---- 7. the small-copy fallback ----
    r = pg.evaluate(r"""()=>{ const out={}; for(const lv of ['glass','light']){ const S=T.stripes(1600,1000,0), g=T.make(800,500,{level:lv}); g.setBackdrop(S); g.addPanel({id:'w',rect:[20,20,300,200],radius:10,kind:'window'});
      g.render(0); const s0={...g.stats}; let drew=0, pend=0; for(let i=1;i<=240;i++){ g.markDirty(); g.updatePanel('w',{rect:[20+i%50,20,300,200]}); if(g.render(i*1000/240)) drew++; if(g.pending) pend++; }
      const s1={...g.stats}; for(let i=241;i<=300;i++) g.render(i*1000/240+500);
      out[lv]={first:s0.uploads,up:s1.uploads-s0.uploads,py:s1.pyramids-s0.pyramids,idle:g.stats.uploads-s1.uploads,px:g.stats.uploadPixels,drew,pend,src:g.info.source,rate:g.info.rate,sd:g.stats.sceneDraws}; g.destroy(); }
      const g=T.make(256,256,{copyRate:0}); g.setBackdrop(T.stripes(256,256,0)); g.addPanel({id:'w',rect:[20,20,100,100],kind:'window'}); g.render(0); for(let i=1;i<=20;i++){ g.markDirty(); g.render(i); } out.free=g.stats.uploads; g.destroy(); return out; }""")
    ok('small copy: a 1600x1000 canvas over an 800x500 engine is reduced to quarter size before the upload (200x125 = 25000 pixels, never the 1.6 million)', r['glass']['px'] == 200 * 125 and r['glass']['first'] == 1 and r['glass']['src'] == 'copy', 'largest upload %d pixels' % r['glass']['px'])
    ok('small copy at Glass: at most 60 uploads per second with the picture dirty on every frame at 240 per second; panels still move 240 times', 58 <= r['glass']['up'] <= 61 and r['glass']['py'] == r['glass']['up'] and r['glass']['drew'] == 240 and r['glass']['rate'] == 60, r['glass'])
    ok('small copy at Light: an eighth of the size (100x63), at most 30 uploads per second', r['light']['px'] == 100 * 63 and 29 <= r['light']['up'] <= 31 and r['light']['drew'] == 240 and r['light']['pend'] > 150, r['light'])
    ok('small copy: uploads only after markDirty (60 more frames without it: at most the one that was waiting)', r['glass']['idle'] <= 1 and r['light']['idle'] <= 1, [r['glass']['idle'], r['light']['idle']])
    ok('copyRate 0 lifts the cap (20 markDirty, 20 uploads)', r['free'] == 21, r['free'])

    r = pg.evaluate(r"""()=>{ const S=T.stripes(512,256,0), g=T.make(512,256,{}); const sc={clips:[{x:0,y:0,w:512,h:256,color:[1,0,0],alpha:1,titleH:0}]}; const o={};
      g.addPanel({id:'w',rect:[100,40,300,160],radius:0,kind:'window',tintAmount:0,shadow:0,lens:false}); g.render(); o.none=[g.info.source,g.info.isStatic];
      g.setScene(sc); g.render(); o.scene=[g.info.source,T.px(T.read(g),250,120)]; g.setBackdrop(T.flat(512,256,'#00f')); g.render(); o.copy=[g.info.source,T.px(T.read(g),250,120)];
      g.setBackdrop(null); g.render(); o.back=[g.info.source,T.px(T.read(g),250,120)]; g.setBackdrop(T.flat(512,256,'#00f')); g.setScene({}); g.render(); o.again=[g.info.source,T.px(T.read(g),250,120)];
      g.setScene(null); g.render(); o.copy2=[g.info.source,T.px(T.read(g),250,120)]; o.st={...g.stats}; g.destroy(); return o; }""")
    ok('switching the source: none (plain tint) -> scene -> small copy -> scene again -> copy; the last one set decides', r['none'] == ['none', True] and r['scene'][0] == 'scene' and r['scene'][1][0] > 200 and r['copy'][0] == 'copy' and r['copy'][1][2] > 200 and r['back'][0] == 'scene' and r['back'][1][0] > 200 and r['again'][0] == 'scene' and r['again'][1][0] > 200 and r['copy2'][0] == 'copy' and r['copy2'][1][2] > 200, [r[k][0] for k in ['scene', 'copy', 'back', 'again', 'copy2']])

    # ---- 8. only the area under docked glass is worked on, with the same pixels ----
    r = pg.evaluate(r"""()=>{ const out={}; const S=T.stripes(800,600,0), clips=[]; for(let i=0;i<60;i++) clips.push({x:i*37,y:(i%9)*64,w:29,h:60,color:['#e5534b','#4c8dff','#e3b341','#3ecf8e'][i&3]});
      for(const way of ['scene','copy']) for(const lv of ['glass','light']) for(const bl of ['light','regular','heavy']){ const mk=cull=>{ const g=T.make(800,600,{level:lv,blur:bl,regionCull:cull}); if(way==='scene') g.setScene({clips,playheadX:300,scrollX:13}); else g.setBackdrop(S);
        g.addPanel({id:'h',rect:[0,20,108,400],kind:'docked'}); g.addPanel({id:'t',rect:[0,576,800,24],kind:'docked'}); g.addPanel({id:'dv',rect:[0,446,800,130],kind:'docked'}); g.addPanel({id:'b',rect:[0,432,800,14],kind:'docked'}); g.render(); return g; };
      const a=mk(true), A=T.read(a), b=mk(false), B=T.read(b); const o={d:T.maxDiff(A,B,0,0,800,600),regA:a.info.regions,regB:b.info.regions};
      // a moving panel appears: the whole picture must be blurred again, without a new upload or a new send
      a.addPanel({id:'w',rect:[300,60,300,200],radius:12,kind:'window'}); a.render(); b.addPanel({id:'w',rect:[300,60,300,200],radius:12,kind:'window'}); b.render();
      o.d2=T.maxDiff(T.read(a),T.read(b),0,0,800,600); o.up=a.stats.uploads; o.ss=a.stats.sceneSends; o.py=a.stats.pyramids; o.reg2=a.info.regions; a.destroy(); b.destroy(); out[way+' '+lv+' '+bl]=o; } return out; }""")
    ok('working only under docked glass gives identical pixels to working on everything (scene and copy, Glass and Light, 3 blur presets)', all(v['d'] == 0 and v['regA'] >= 2 and v['regB'] == 0 for v in r.values()), json.dumps({k: [v['d'], v['regA']] for k, v in r.items()}))
    ok('a floating panel appears: the full backdrop is rebuilt (no new upload, no new send), identical pixels', all(v['d2'] == 0 and v['up'] + v['ss'] == 1 and v['py'] == 2 and v['reg2'] == 0 for v in r.values()), json.dumps({k: [v['d2'], v['up'], v['ss'], v['py']] for k, v in r.items()}))

    # ---- 9. flat picture for glass over DOM, backdrop rectangle ----
    r = pg.evaluate(r"""()=>{ const g=T.make(512,256,{blur:'light',rim:{base:0,lit:0}}); g.setScene({bg:[0,0,1]});
      g.setFlat('panel',{rect:[0,128,512,128],color:[1,0,0,1]}); const disp=T.flat(640,480,'rgb(0,255,0)'); g.setFlat('disp',{rect:[300,150,120,90],source:disp});
      g.addPanel({id:'dock',rect:[0,128,512,128],kind:'docked',tintAmount:0}); g.addPanel({id:'menu',rect:[100,20,360,220],radius:12,kind:'menu',over:'flats',tintAmount:0,shadow:0,lens:false,z:2});
      g.render(); const b=T.read(g); const o={overBackdrop:T.px(b,200,60),overPanel:T.px(b,200,200),overDisp:T.px(b,360,195),dock:T.px(b,40,200),st:{...g.stats}};
      for(let i=0;i<10;i++){ g.updatePanel('menu',{rect:[100+i,20,360,220]}); g.render(); } o.move={...g.stats};
      g.markFlatDirty('disp'); g.render(1e9); o.fd={...g.stats}; for(let i=0;i<3;i++){ g.setPlayhead(5+i); g.render(); } o.later=T.px(T.read(g),200,200); g.removeFlat('panel'); g.removeFlat('disp'); g.render(); o.noflat=T.px(T.read(g),200,200); g.destroy(); return o; }""")
    ok('flat picture: floating glass sees the backdrop, the flat panel colour and the fed display canvas', r['overBackdrop'][2] > 200 and r['overPanel'][0] > 200 and r['overPanel'][2] < 40 and r['overDisp'][1] > 200, [r['overBackdrop'][:3], r['overPanel'][:3], r['overDisp'][:3]])
    ok('flat picture: docked glass does not see it', r['dock'][2] > 200 and r['dock'][0] < 30, r['dock'][:3])
    ok('flat picture: still there after the backdrop was drawn again three times (playhead moved)', r['later'][0] > 200 and r['later'][2] < 40, r['later'][:3])
    ok('flat picture: moving the floating glass rebuilds nothing; a changed display rebuilds only the flat pyramid', r['move']['flatPyramids'] == r['st']['flatPyramids'] == 1 and r['move']['flatUploads'] == 1 and r['fd']['flatPyramids'] == 2 and r['fd']['flatUploads'] == 2 and r['fd']['pyramids'] == r['st']['pyramids'], [r['st'], r['fd']])
    ok('fed display canvas (640x480 shown at 120x90) goes the small-copy route: 30x23 pixels uploaded; the backdrop itself: no upload', r['fd']['uploadPixels'] == 30 * 23 and r['fd']['uploads'] == 0, 'largest upload %d pixels' % r['fd']['uploadPixels'])
    rc = pg.evaluate(r"""()=>{ const out={}; for(const lv of ['glass','light']){ const g=T.make(256,256,{level:lv}); g.setScene({bg:[0,0,0]}); const d=T.flat(32,32,'#0f0'); g.setFlat('d',{rect:[0,0,256,256],source:d}); g.addPanel({id:'w',rect:[20,20,100,100],kind:'menu',over:'flats'});
      g.render(0); const s0={...g.stats}; let pend=0; for(let i=1;i<=240;i++){ g.markFlatDirty('d'); g.render(i*1000/240); if(g.pending) pend++; } out[lv]={fu:g.stats.flatUploads-s0.flatUploads,fp:g.stats.flatPyramids-s0.flatPyramids,pend}; g.destroy(); } return out; }""")
    ok('a fed display that repaints every frame is refreshed at most 60 times per second at Glass, 30 at Light', 58 <= rc['glass']['fu'] <= 61 and 29 <= rc['light']['fu'] <= 31 and rc['light']['fp'] == rc['light']['fu'] and rc['light']['pend'] > 150, rc)
    ok('flat removed: the glass sees the backdrop again', r['noflat'][2] > 200, r['noflat'][:3])

    r = pg.evaluate(r"""()=>{ const g=T.make(512,256,{blur:'light',rim:{base:0,lit:0},backdropColor:[1,1,0]}); g.setBackdrop(T.flat(100,50,'rgb(0,0,255)'),{rect:[256,0,256,256]});
      g.addPanel({id:'a',rect:[20,20,472,216],kind:'window',tintAmount:0,shadow:0,lens:false}); g.render(); const b=T.read(g); g.destroy(); return {l:T.px(b,100,128),r:T.px(b,400,128)}; }""")
    ok('backdrop rectangle (small copy): the picture sits where it is told, the rest is the base colour', r['l'][0] > 200 and r['l'][1] > 200 and r['l'][2] < 40 and r['r'][2] > 200 and r['r'][0] < 40, [r['l'][:3], r['r'][:3]])

    # ---- 10. shadow, opacity, levels ----
    r = pg.evaluate(r"""()=>{ const g=T.make(512,400,{}); g.setScene({bg:'#888888'});
      g.addPanel({id:'w',rect:[100,60,300,200],radius:16,kind:'window'}); g.render(); let b=T.read(g);
      const o={below:T.px(b,250,268),below2:T.px(b,250,285),above:T.px(b,250,52),side:T.px(b,92,160),far:T.px(b,250,330)};
      g.updatePanel('w',{kind:'docked'}); g.render(); b=T.read(g); o.dock=T.px(b,250,268);
      g.updatePanel('w',{kind:'pill',rect:[100,60,150,32]}); g.render(); b=T.read(g); o.pill=T.px(b,175,97);
      g.updatePanel('w',{kind:'window',rect:[100,60,300,200],opacity:.5}); g.render(); b=T.read(g); o.half=T.px(b,250,160);
      g.updatePanel('w',{opacity:1}); g.setLevel('solid'); g.render(); b=T.read(g); o.stat=T.px(b,250,160); o.stat2=T.px(b,251,160); o.statInfo=g.info.isStatic; const s1={...g.stats}; g.setPlayhead(5); g.render(); o.statUp=g.stats.sceneDraws-s1.sceneDraws;
      g.setLevel('glass'); g.render(); o.back=T.px(T.read(g),250,160); g.setQuality(1); o.q1=g.info.level; g.setQuality(0); o.q0=g.info.level; g.setQuality(3); o.q3=g.info.level; g.destroy(); return o; }""")
    ok("shadow (Apple's numbers): below a 200 px window about 0.6 x falloff, weaker above, none far away, none for docked, faint for a pill",
       r['below'][3] > 60 and r['below'][3] > r['above'][3] and r['below'][3] > r['below2'][3] > 0 and r['far'][3] == 0 and r['dock'][3] == 0 and 0 < r['pill'][3] < 12 and r['below'][:3] == [0, 0, 0],
       'alpha below %d, 25 px below %d, above %d, side %d, pill %d' % (r['below'][3], r['below2'][3], r['above'][3], r['side'][3], r['pill'][3]))
    ok('panel opacity 0.5 gives alpha 128', abs(r['half'][3] - 128) <= 1, r['half'])
    ok('level Solid: plain tint with noise, no backdrop work', r['statInfo'] and r['statUp'] == 0 and all(abs(a - b_) <= 4 for a, b_ in zip(r['stat'][:3], [22, 28, 42])) and r['stat'][3] == 255, [r['stat'], r['stat2']])
    ok('back to Glass: glass again; the older setQuality maps 3 -> glass, 1 -> light, 0 -> solid', r['back'][0] > 60 and [r['q3'], r['q1'], r['q0']] == ['glass', 'light', 'solid'], r['back'])
    r = pg.evaluate(r"""()=>{ const mk=lv=>{ const g=T.make(256,256,Object.assign({level:lv},T.plain)); g.setBackdrop(T.ramp(256,256)); g.addPanel({id:'a',rect:[28,28,200,200],radius:16,kind:'window',tintAmount:0,shadow:0}); g.render(); return g; };
      const a=mk('glass'), b=mk('light'), A=T.read(a), B=T.read(b); const o={glassRim:T.px(A,33,128)[0]-33,lightRim:T.px(B,33,128)[0]-33,lightMid:T.px(B,128,128),ia:a.info,ib:b.info}; a.destroy(); b.destroy(); return o; }""")
    ok('level Light is the same engine with the lens off: the rim bends at Glass (wide) and not at Light, the middle is still glass', r['glassRim'] > 20 and abs(r['lightRim']) <= 2 and abs(r['lightMid'][0] - 128) <= 3 and r['ib']['lens'] == 'off' and r['ia']['lens'] == 'wide' and not r['ib']['isStatic'], 'rim shift glass %d px, light %d px' % (r['glassRim'], r['lightRim']))

    # ---- 11. Reduce Transparency and Increase Contrast ----
    setup = r"""()=>{ window.g=T.make(256,256,T.plain); g.setBackdrop(T.ramp(256,256)); g.addPanel({id:'a',rect:[28,28,200,200],radius:16,kind:'window',shadow:0}); window.asked=0; }"""
    probe = r"""()=>{ g.render(); const b=T.read(g); return {info:g.info, mid:T.px(b,128,128), edge:T.px(b,28,128), rim:T.px(b,33,128), up:g.stats.uploads, py:g.stats.pyramids}; }"""
    pg.evaluate(setup); base = pg.evaluate(probe)
    cdp = ctx.new_cdp_session(pg)
    cdp.send('Emulation.setEmulatedMedia', {'features': [{'name': 'prefers-reduced-transparency', 'value': 'reduce'}]}); pg.wait_for_timeout(100)
    rt = pg.evaluate(probe)
    ok('Reduce Transparency (system setting): plain tint, no backdrop work', rt['info']['reduceTransparency'] and rt['info']['isStatic'] and all(abs(a - b_) <= 4 for a, b_ in zip(rt['mid'][:3], [22, 28, 42])) and rt['py'] == base['py'], rt['mid'])
    cdp.send('Emulation.setEmulatedMedia', {'features': [{'name': 'prefers-contrast', 'value': 'more'}]}); pg.wait_for_timeout(100)
    ic = pg.evaluate(probe)
    ok('Increase Contrast (system setting): bright border, heavier tint, no lens', ic['info']['increaseContrast'] and not ic['info']['isStatic'] and ic['edge'][0] > base['edge'][0] + 60 and ic['mid'][0] < base['mid'][0] * .6 and abs(ic['rim'][0] - (33 * .18 + 22 * .82)) <= 5, 'edge %s (was %s), middle %s (was %s)' % (ic['edge'][:3], base['edge'][:3], ic['mid'][:3], base['mid'][:3]))
    cdp.send('Emulation.setEmulatedMedia', {'features': []}); pg.wait_for_timeout(100)
    back = pg.evaluate(probe)
    ok('settings off again: same pixels as before', back['mid'] == base['mid'] and back['edge'] == base['edge'])
    r = pg.evaluate(r"""()=>{ g.setAccessibility({reduceTransparency:true}); g.render(); const a=g.info.isStatic; g.setAccessibility({reduceTransparency:null,increaseContrast:true}); g.render(); const b=g.info.increaseContrast; g.setAccessibility({increaseContrast:null}); g.render(); const c=g.info; g.destroy();
      const s=T.make(256,256,{reduceTransparency:true}); s.setScene({clips:[{x:0,y:0,w:99,h:99,color:'#f00'}]}); s.addPanel({id:'a',rect:[28,28,200,200],kind:'window'}); s.render(); s.setPlayhead(4); s.render(); const d=s.stats.sceneDraws+s.stats.sceneSends; s.destroy(); return {a,b,c:c.isStatic||c.increaseContrast,d}; }""")
    ok('the same two behaviours can be forced by the app (setAccessibility); with Reduce Transparency the scene is neither sent nor drawn', r['a'] and r['b'] and not r['c'] and r['d'] == 0)

    # ---- 12. context loss and restore: scene path ----
    pg.evaluate(r"""()=>{ window.fbLog=[]; window.asks=0; window.g=T.make(256,256,{onFallback:(on,why)=>fbLog.push([on,why]),requestRender:()=>asks++});
      const clips=[]; for(let i=0;i<40;i++) clips.push({x:i*23,y:(i%4)*64,w:17,h:60,color:['#e5534b','#4c8dff','#e3b341','#3ecf8e'][i&3],selected:i===5}); g.setScene({clips,lanes:[{y:0,h:64,color:'#14141c'}],playheadX:77,scrollX:9});
      g.setFlat('f',{rect:[0,128,256,128],source:T.flat(8,8,'#0f0')}); g.addPanel({id:'a',rect:[28,28,200,100],radius:16,kind:'window'}); g.addPanel({id:'b',rect:[28,150,200,80],radius:8,kind:'menu',over:'flats'}); g.render(); window.before=T.read(g); window.st0={...g.stats}; }""")
    pg.evaluate("()=>g.debug.lose()"); pg.wait_for_function("()=>g.mode==='fallback'", timeout=5000)
    r = pg.evaluate(r"""()=>{ const drew=g.render(), again=g.render(), sib=g.canvas.nextSibling, x=sib&&sib.getContext('2d'); const d=x?x.getImageData(128,78,1,1).data:[], out=x?x.getImageData(5,5,1,1).data:[];
      return {mode:g.mode,reason:g.reason,drew,again,sib:!!sib&&sib.tagName,hidden:g.canvas.style.visibility,mid:[...d],out:[...out],log:fbLog,asks,w:sib&&sib.width,cw:sib&&sib.style.width}; }""")
    ok('context lost: engine switches to the fallback and tells the app', r['mode'] == 'fallback' and r['reason'] == 'lost' and r['log'] == [[True, 'lost']] and r['asks'] >= 1, r['log'])
    ok('fallback: plain tint with noise on a 2D canvas in the same place, drawn once', r['sib'] == 'CANVAS' and r['hidden'] == 'hidden' and r['drew'] and not r['again'] and all(abs(a - b_) <= 12 for a, b_ in zip(r['mid'][:3], [22, 28, 42])) and r['mid'][3] == 255 and r['out'][3] == 0 and r['w'] == 256, r['mid'])
    r = pg.evaluate(r"""()=>{ g.updatePanel('a',{rect:[40,28,200,100]}); const d=g.render(); g.updatePanel('a',{rect:[28,28,200,100]}); g.setPlayhead(80); g.setView({scrollX:10}); g.render(); g.setPlayhead(77); g.setView({scrollX:9}); return d; }""")
    ok('fallback: panels still move while the context is lost; scene calls are harmless', r)
    pg.evaluate("()=>g.debug.restore()"); pg.wait_for_function("()=>g.mode==='gl'", timeout=5000)
    r = pg.evaluate(r"""()=>{ const drew=g.render(), after=T.read(g); return {drew,d:T.maxDiff(before,after,0,0,256,256),sib:g.canvas.nextSibling&&g.canvas.nextSibling.tagName,vis:g.canvas.style.visibility,log:fbLog,st:{...g.stats},st0,asks}; }""")
    ok('context restored: glass is back, pixel-identical to before the loss, fallback canvas removed; the rectangles were sent again once, no backdrop upload', r['drew'] and r['d'] == 0 and r['sib'] != 'CANVAS' and r['vis'] != 'hidden' and r['log'][-1] == [False, ''] and r['st']['lost'] == 1 and r['st']['restored'] == 1 and r['st']['sceneSends'] == r['st0']['sceneSends'] + 1 and r['st']['uploads'] == 0, 'max difference %d, %s' % (r['d'], r['st']))
    r = pg.evaluate(r"""async()=>{ for(let i=0;i<3;i++){ g.debug.lose(); await new Promise(r=>setTimeout(r,60)); g.render(); g.debug.restore(); await new Promise(r=>setTimeout(r,60)); g.render(); }
      const d=T.maxDiff(before,T.read(g),0,0,256,256), n=document.querySelectorAll('canvas').length; g.destroy(); return {d,n,mode:g.mode}; }""")
    ok('three more losses in a row: recovers every time, no canvases left behind', r['d'] == 0 and r['mode'] == 'gl', r)
    # the same with the small copy as the source
    pg.evaluate(r"""()=>{ window.g=T.make(256,256,{}); g.setBackdrop(T.stripes(256,256,0)); g.addPanel({id:'a',rect:[28,28,200,100],radius:16,kind:'window'}); g.render(); window.before=T.read(g); }""")
    pg.evaluate("()=>g.debug.lose()"); pg.wait_for_function("()=>g.mode==='fallback'", timeout=5000); pg.evaluate("()=>{g.render();g.debug.restore()}"); pg.wait_for_function("()=>g.mode==='gl'", timeout=5000)
    r = pg.evaluate(r"""()=>{ g.render(); const d=T.maxDiff(before,T.read(g),0,0,256,256), o={d,up:g.stats.uploads,px:g.stats.uploadPixels}; g.destroy(); return o; }""")
    ok('context loss with the small copy as the source: identical after the restore, the copy uploaded once more', r['d'] == 0 and r['up'] == 2 and r['px'] == 64 * 64, r)

    # ---- 13. resize, panel bookkeeping, destroy ----
    r = pg.evaluate(r"""()=>{ const g=T.make(256,256,{}); g.setScene({clips:[{x:0,y:0,w:900,h:900,color:'#4c8dff'}]}); g.addPanel({id:'a',rect:{x:10,y:10,w:100,h:100},radius:999,kind:'window'}); g.addPanel({id:'a',rect:{left:20,top:20,width:100,height:100}}); g.render();
      const o={n:g.info.panels,has:g.hasPanel('a'),upd:g.updatePanel('zz',{}),rm:g.removePanel('zz')}; g.canvas.style.width='400px'; g.canvas.style.height='300px'; o.rs=g.resize(400,300,2); o.drew=g.render(); o.info=g.info; o.cw=g.canvas.width; o.ss=g.stats.sceneSends; o.sd=g.stats.sceneDraws; o.py=g.stats.pyramids;
      o.px=T.px(T.read(g),140,140); g.removePanel('a'); g.render(); o.empty=T.px(T.read(g),140,140); g.destroy(); o.after=g.render(); return o; }""")
    ok('resize: canvas 800x600 at 2x, backdrop drawn again at the new size without a new send, panel drawn at the right place', r['rs'] and r['drew'] and r['cw'] == 800 and r['info']['dpr'] == 2 and r['ss'] == 1 and r['sd'] == 2 and r['py'] == 2 and r['px'][3] == 255 and r['px'][2] > r['px'][0], r['px'])
    ok('addPanel twice with one id updates it; unknown ids are refused; removed panel is gone; destroy stops render', r['n'] == 1 and r['has'] and not r['upd'] and not r['rm'] and r['empty'] == [0, 0, 0, 0] and r['after'] is False)
    ctx.close()

    # ---- 14. WebGL2 missing ----
    ctx, pg = unit_page(b, init="const og=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(t,a){return /webgl/.test(t)?null:og.call(this,t,a)};")
    r = pg.evaluate(r"""()=>{ const log=[], g=T.make(256,256,{onFallback:(on,why)=>log.push([on,why])}); g.setScene({lanes:[{y:0,h:64,color:'#222'}],clips:[{x:0,y:0,w:50,h:60,color:'#f00',selected:true}],playheadX:3}); g.addPanel({id:'a',rect:[28,28,200,100],radius:16,kind:'window'});
      const drew=g.render(), again=g.render(); g.markDirty(); g.setPlayhead(9); g.setView({scrollX:4,zoom:2}); const d3=g.render(); const x=g.canvas.getContext('2d'), mid=[...x.getImageData(128,78,1,1).data], out=[...x.getImageData(5,5,1,1).data], corner=[...x.getImageData(29,29,1,1).data];
      g.updatePanel('a',{rect:[28,100,200,100]}); const d4=g.render(), moved=[...x.getImageData(128,60,1,1).data]; g.setLevel('light'); g.setLevel('solid'); g.setLevel('glass'); g.setQuality(1); g.setLensPreset('wide'); g.setBlurPreset('heavy'); g.setFlat('f',{rect:[0,0,9,9],color:[1,1,1,1]}); g.setBackdrop(T.stripes(64,64,0)); g.setScene(null); g.resize(300,200,1); const d5=g.render();
      const o={mode:g.mode,reason:g.reason,log,drew,again,d3,d4,d5,mid,out,corner,moved,sibs:document.querySelectorAll('canvas').length,w:g.canvas.width,pend:g.pending,st:{...g.stats}}; g.destroy(); return o; }""")
    ok('WebGL2 missing: fallback (the Solid look) on the same canvas, app told why', r['mode'] == 'fallback' and r['reason'] == 'no webgl2' and r['log'] == [[True, 'no webgl2']] and r['sibs'] == 1, r['log'])
    ok('WebGL2 missing: plain tint with noise, rounded corners, redrawn only when a panel changes, every API call harmless (scene, playhead, view, levels)', r['drew'] and not r['again'] and not r['d3'] and r['d4'] and r['d5'] and r['w'] == 300 and not r['pend'] and r['st']['sceneSends'] == 0 and r['st']['uploads'] == 0 and all(abs(a - b_) <= 12 for a, b_ in zip(r['mid'][:3], [22, 28, 42])) and r['out'][3] == 0 and r['corner'][3] < 60 and r['moved'][3] == 0, [r['mid'], r['corner']])
    ctx.close()

    # ---- 15. software drawing is refused unless allowed ----
    ctx, pg = unit_page(b)
    r = pg.evaluate(r"""()=>{ const c=document.createElement('canvas'); document.body.appendChild(c); c.style.cssText='width:100px;height:100px'; const g=AudioLabGlass.create(c,{}); const o={mode:g.mode,reason:g.reason}; g.destroy(); return o; }""")
    print('NOTE without allowSoftware on this machine (software GL): mode %s %s' % (r['mode'], r['reason']), flush=True)
    ok('software GL is refused by default (falls back to the plain tint) or accepted where the browser does not report it', r['mode'] in ('fallback', 'gl'), r)
    ctx.close()

def AUDIT_LENS(pg):
    return pg.evaluate("()=>AudioLabGlass.LENS.wide")

def page_tests(b, dsf):
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=dsf)
    pg = ctx.new_page(); watch(pg)
    pg.goto('file://' + HERE + '/engine-test.html?soft=1'); pg.wait_for_function("()=>window.__t&&__t.gA.stats.draws>0", timeout=30000)
    tag = ' (%dx)' % dsf
    info = pg.evaluate("()=>({a:__t.gA.info,b:__t.gB.info})")
    ok('test page loads, both layers draw glass from the GPU-drawn scene; defaults Glass, lens wide, blur light' + tag, all(info[k]['mode'] == 'gl' and info[k]['source'] == 'scene' and info[k]['level'] == 'glass' and info[k]['lens'] == 'wide' and info[k]['blur'] == 'light' and info[k]['levels'] == [4] for k in 'ab') and info['a']['panels'] == 4 and info['b']['panels'] == 3 and info['a']['width'] == 1600 * dsf, info['a'])
    ok('test page: docked layer works only on the area under glass, floating layer on everything' + tag, info['a']['regions'] >= 1 and info['b']['regions'] == 0, 'docked layer: %d rectangles' % info['a']['regions'])
    count = r"""async(ms)=>{ const s=g=>({...g.stats}), a0=s(__t.gA), b0=s(__t.gB); await new Promise(r=>{let n=0;const f=()=>{if(++n>=ms)r();else requestAnimationFrame(f)};requestAnimationFrame(f)}); const a1=s(__t.gA), b1=s(__t.gB), d=(x,y)=>Object.fromEntries(Object.keys(x).map(k=>[k,k==='uploadPixels'?y[k]:y[k]-x[k]])); return {a:d(a0,a1),b:d(b0,b1)}; }"""
    setsel = "([id,v])=>{const e=document.querySelector(id);if(e.type==='checkbox')e.checked=v;else e.value=v;e.dispatchEvent(new Event('change',{bubbles:true}))}"
    N = 30
    noup = lambda r: all(r[k]['uploads'] == 0 and r[k]['flatUploads'] == 0 and r[k]['sceneSends'] == 0 for k in 'ab')
    short = lambda r: {k: {f: r[k][f] for f in ['sceneDraws', 'sceneSends', 'uploads', 'flatUploads', 'draws']} for k in 'ab'}
    r = pg.evaluate(count, N)
    ok('scene path, scrolling + mixer moving: uploads == 0, clip list not sent again, backdrop drawn on the GPU every frame on both layers' + tag, noup(r) and r['a']['sceneDraws'] >= N - 2 and r['b']['sceneDraws'] >= N - 2 and r['a']['pyramids'] >= N - 2 and r['b']['flatPyramids'] >= N - 2, short(r))
    pg.evaluate(setsel, ['#scn', 'play']); pg.wait_for_timeout(400)
    r = pg.evaluate(count, N)
    ok('scene path, playing + mixer moving: uploads == 0, the playhead-only change does not send the clips again, backdrop drawn every frame' + tag, noup(r) and r['a']['sceneDraws'] >= N - 2 and r['b']['sceneDraws'] >= N - 2, short(r))
    pg.evaluate(setsel, ['#scn', 'still']); pg.wait_for_timeout(400)
    r = pg.evaluate(count, N)
    ok('still picture + mixer moving: nothing uploaded, sent or drawn into the backdrop; docked layer not redrawn at all; floating layer redraws its quads' + tag,
       noup(r) and r['a']['sceneDraws'] == 0 and r['b']['sceneDraws'] == 0 and r['a']['draws'] == 0 and r['b']['flatPyramids'] == 0 and r['b']['draws'] >= N * .5, short(r))
    pg.evaluate(setsel, ['#drag', False]); pg.wait_for_timeout(300)
    r = pg.evaluate(count, N)
    ok('nothing moves: no GL work at all (0 draws on both layers)' + tag, r['a']['draws'] == 0 and r['b']['draws'] == 0 and r['a']['skipped'] >= N - 1, short(r))

    # screenshots: what the user sees (compositor output)
    pg.evaluate("()=>{document.querySelector('#hud').hidden=true;__t.P.mix.dx=0;__t.layout()}"); pg.wait_for_timeout(500)
    from PIL import Image
    import io
    shot = lambda: Image.open(io.BytesIO(pg.screenshot())).convert('RGB')
    glass = shot()
    pg.evaluate("()=>document.querySelectorAll('canvas.glA,canvas.glB,.gp,#disp').forEach(e=>e.style.visibility='hidden')"); pg.wait_for_timeout(300)
    bare = shot()
    pg.evaluate("()=>document.querySelectorAll('canvas.glA,canvas.glB,.gp,#disp').forEach(e=>e.style.visibility='')"); pg.wait_for_timeout(300)
    def energy(im, box):
        c = im.crop(tuple(int(v * dsf) for v in box)); w, h = c.size; p = c.load(); e = 0
        for y in range(0, h, 3):
            for x in range(w - 1): e = max(e, sum(abs(p[x, y][k] - p[x + 1, y][k]) for k in range(3)))
        return e
    def mean(im, box):
        c = im.crop(tuple(int(v * dsf) for v in box)).resize((1, 1), Image.BOX); return c.getpixel((0, 0))
    eg, eb = energy(glass, (60, 120, 160, 560)), energy(bare, (60, 120, 160, 560))
    ok('screenshot: track headers are frosted (sharpest edge under 20 % of the bare arrangement)' + tag, eg < eb * .2, 'glass %d, bare %d' % (eg, eb))
    em, ebm = energy(glass, (330, 130, 1270, 440)), energy(bare, (330, 130, 1270, 440))
    ok('screenshot: mixer window is frosted' + tag, em < ebm * .2, 'glass %d, bare %d' % (em, ebm))
    eo, ebo = energy(glass, (1525, 120, 1595, 560)), energy(bare, (1525, 120, 1595, 560))
    ok('screenshot: the arrangement outside glass is untouched' + tag, eo == ebo and eo > 100, 'glass %d, bare %d' % (eo, ebo))
    # the glass shows the clips that are really under it: the average colour of the mixer follows the arrangement (red-ish row vs blue-ish row), mixed half with the panel tint
    P = pg.evaluate("()=>Object.fromEntries(Object.entries(__t.P).map(([k,p])=>[k,[p.x+p.dx,p.y,p.w,p.h]]))")
    x0, y0, w0, h0 = P['mix']
    rows_ok = True; det = []
    for ry in (104, 168, 232, 296):   # rows of the fake arrangement start at 40, 64 px each; row bodies at 104.., 168.., ...
        box = (x0 + 80, ry + 20, x0 + w0 - 80, ry + 56); g_, b_ = mean(glass, box), mean(bare, box)
        gi, bi = max(range(3), key=lambda k: g_[k]), max(range(3), key=lambda k: b_[k]); det.append('%s/%s' % (g_, b_)); rows_ok = rows_ok and gi == bi
    ok('screenshot: under the mixer each track row keeps the colour of the clips that are really there (GPU-drawn backdrop lines up with the picture)' + tag, rows_ok, ' '.join(det))
    # the menu over the device panel: sees the flat panel colour and the display (dark box), not the arrangement
    mx, my, mw, mh = P['menu']; dv = P['dev']
    c1 = glass.getpixel((int((mx + 60) * dsf), int((dv[1] + 12) * dsf)))   # menu over the plain device panel
    exp = [(.13 * .4 + .086 * .6) * 255, (.15 * .4 + .11 * .6) * 255, (.2 * .4 + .165 * .6) * 255]
    ok('screenshot: menu over the device panel shows the flat panel colour, not the arrangement' + tag, all(abs(a - e) <= 14 for a, e in zip(c1, exp)), '%s expected about %s' % (c1, [round(e) for e in exp]))
    # lens on / off screenshots: rim differs, middle identical
    settle = lambda: pg.evaluate('()=>new Promise(r=>{let n=0;const f=()=>{if(++n>4)r();else requestAnimationFrame(f)};requestAnimationFrame(f)})')
    def diff(a, b_, box):
        A, B = a.crop(tuple(int(v * dsf) for v in box)), b_.crop(tuple(int(v * dsf) for v in box)); pa, pb = A.load(), B.load(); w, h = A.size; m = 0; s = 0
        for y in range(h):
            for x in range(w):
                d = max(abs(pa[x, y][k] - pb[x, y][k]) for k in range(3)); m = max(m, d); s += d
        return m, s / (w * h)
    rimbox = lambda a, b_: max(diff(a, b_, (x0 + 2, y0 + 60, x0 + 30, y0 + h0 - 60)), diff(a, b_, (x0 + 60, y0 + 2, x0 + w0 - 60, y0 + 30)))
    midbox = (x0 + 50, y0 + 50, x0 + w0 - 50, y0 + h0 - 50)
    pg.evaluate(setsel, ['#lens', 'off']); settle(); off = shot(); pg.evaluate(setsel, ['#lens', 'wide']); settle()
    rim = rimbox(glass, off); mid = diff(glass, off, midbox)
    ok('screenshot: lens wide and lens off differ in the rim of the mixer window and are identical in its middle' + tag, rim[0] >= 6 and mid[0] <= 1, 'rim max %d mean %.1f, middle max %d' % (rim[0], rim[1], mid[0]))
    glass.save(os.path.join(OUT, 'engine-test-glass-%dx.png' % dsf))

    # level Light: the same engine, lens off, backdrop an eighth of the size; still frosted, no uploads
    pg.evaluate("()=>__t.setLevel('light')"); settle(); light = shot(); li = pg.evaluate("()=>__t.gA.info")
    rim = rimbox(light, off); el = energy(light, (330, 130, 1270, 440))
    ok('level Light on the page: lens off (rim like "lens off" within the stronger blur), mixer still frosted, backdrop an eighth of the size, 30 per second' + tag, li['level'] == 'light' and li['lens'] == 'off' and li['levels'] == [8] and li['rate'] == 30 and el < ebm * .2 and el > 0, 'sharpest edge %d of %d' % (el, ebm))
    pg.evaluate(setsel, ['#scn', 'scroll']); pg.evaluate(setsel, ['#drag', True]); pg.wait_for_timeout(300); r = pg.evaluate(count, N)
    ok('level Light, scrolling + mixer moving: uploads == 0, clips not sent again, faces redrawn every frame' + tag, noup(r) and r['b']['draws'] >= N - 2 and 1 <= r['a']['sceneDraws'] <= N, short(r))
    light.save(os.path.join(OUT, 'engine-test-light-%dx.png' % dsf))
    # level Solid: plain tint, no backdrop work
    pg.evaluate("()=>__t.setLevel('solid')"); pg.wait_for_timeout(300); r = pg.evaluate(count, 10); c = shot().getpixel((int(100 * dsf), int(300 * dsf)))
    ok('level Solid on the page: plain panel colour, no backdrop drawn, nothing uploaded while scrolling' + tag, noup(r) and r['a']['sceneDraws'] == 0 and r['b']['sceneDraws'] == 0 and all(abs(a - e) <= 14 for a, e in zip(c, [22, 28, 42])), c)
    pg.evaluate("()=>__t.setLevel('glass')")

    # the small-copy fallback on the page
    pg.evaluate("()=>__t.setSource('copy')"); pg.wait_for_timeout(400); r = pg.evaluate(count, N); ci = pg.evaluate("()=>__t.gA.info")
    lim = 400 * 250
    ok('small-copy fallback, scrolling: the canvas is uploaded as a quarter-size copy (400x250 for a 1600x1000 window, also at 2x), at most once per frame, no scene drawn' + tag,
       ci['source'] == 'copy' and 1 <= r['a']['uploads'] <= N and 1 <= r['b']['uploads'] <= N and r['a']['uploadPixels'] == lim and r['b']['uploadPixels'] == lim and r['a']['sceneDraws'] == 0, {k: [r[k]['uploads'], r[k]['uploadPixels']] for k in 'ab'})
    pg.evaluate(setsel, ['#scn', 'play']); pg.wait_for_timeout(400); r = pg.evaluate(count, N)
    ok('small-copy fallback, playing (playhead on its own layer): 0 uploads' + tag, r['a']['uploads'] == 0 and r['b']['uploads'] == 0, short(r))
    pg.evaluate(setsel, ['#scn', 'still']); pg.evaluate(setsel, ['#drag', False]); pg.evaluate("()=>{__t.P.mix.dx=0;__t.layout()}"); pg.wait_for_timeout(500); copyshot = shot()
    d = diff(glass, copyshot, midbox)
    ok('small copy and GPU-drawn backdrop give nearly the same mixer glass on screen (the copy also has the note marks and grid, the scene leaves them out)' + tag, d[1] < 6, 'mean difference %.1f, max %d of 255' % (d[1], d[0]))
    pg.evaluate("()=>__t.setSource('scene')"); pg.evaluate(setsel, ['#scn', 'scroll']); pg.evaluate(setsel, ['#drag', True])
    # a moving device display under floating glass: small copies of the display only
    pg.evaluate("()=>{__t.gA.stats.uploadPixels=0;__t.gB.stats.uploadPixels=0}"); pg.evaluate(setsel, ['#dmove', True]); pg.wait_for_timeout(300); r = pg.evaluate(count, N)
    ok('scene path with a moving device display: the display goes up as a small copy (105x52 for 420x206), the arrangement still 0 uploads' + tag, r['a']['uploads'] == 0 and r['b']['uploads'] == 0 and r['b']['flatUploads'] >= 1 and r['b']['uploadPixels'] <= 110 * 55 and r['a']['flatUploads'] == 0, [r['b']['flatUploads'], r['b']['uploadPixels']])
    pg.evaluate(setsel, ['#dmove', False])

    # presets, accessibility, context loss through the page's own controls
    for sel, v in [('#blur', 'heavy'), ('#blur', 'regular'), ('#lens', 'apple'), ('#lens', 'fine'), ('#face', 'apple')]:
        pg.evaluate(setsel, [sel, v]); pg.wait_for_timeout(250)
    r = pg.evaluate("()=>({a:__t.gA.info,b:__t.gB.info})")
    ok('page controls reach both layers (lens fine, blur regular)' + tag, all(r[k]['lens'] == 'fine' and r[k]['blur'] == 'regular' and r[k]['levels'] == [4, 8] for k in 'ab'))
    pg.evaluate(setsel, ['#lens', 'wide']); pg.evaluate(setsel, ['#blur', 'light']); pg.evaluate(setsel, ['#face', 'bench'])
    pg.evaluate(setsel, ['#rt', True]); pg.wait_for_timeout(300); r = pg.evaluate(count, 10)
    ok('Reduce transparency on the page: no backdrop work while scrolling' + tag, noup(r) and r['a']['sceneDraws'] == 0 and r['b']['sceneDraws'] == 0)
    pg.evaluate(setsel, ['#rt', False]); pg.evaluate(setsel, ['#ic', True]); pg.wait_for_timeout(300); ici = pg.evaluate("()=>__t.gA.info.increaseContrast"); pg.evaluate(setsel, ['#ic', False])
    s0 = pg.evaluate("()=>[__t.gA.stats.sceneSends,__t.gB.stats.sceneSends]")
    pg.evaluate("()=>document.querySelector('#lose').click()"); pg.wait_for_function("()=>__t.gA.mode==='fallback'&&__t.gB.mode==='fallback'", timeout=5000); pg.wait_for_timeout(400)
    fb = shot(); c = fb.getpixel((int(100 * dsf), int(300 * dsf)))
    ok('page: lose the context -> both layers show the plain tint (track headers are the solid colour); Increase contrast reached the engine' + tag, ici and all(abs(a - e) <= 14 for a, e in zip(c, [22, 28, 42])), c)
    pg.evaluate("()=>document.querySelector('#rest').click()"); pg.wait_for_function("()=>__t.gA.mode==='gl'&&__t.gB.mode==='gl'", timeout=5000); pg.wait_for_timeout(500)
    r = pg.evaluate(count, 10); s1 = pg.evaluate("()=>[__t.gA.stats.sceneSends,__t.gB.stats.sceneSends]")
    ok('page: restore -> glass again from the scene (clip list sent once more per layer, still 0 uploads), no stray canvases' + tag, r['a']['sceneDraws'] >= 8 and r['a']['uploads'] == 0 and s1 == [s0[0] + 1, s0[1] + 1] and pg.evaluate("()=>document.querySelectorAll('#stage canvas').length") == 4, [s0, s1])
    if dsf == 1:
        pg.evaluate("()=>{document.querySelector('#hud').hidden=false}")
        pc = pg.evaluate("async()=>{const d=await __t.pieces(4);return {d,t:document.querySelector('#res').textContent,src:__t.gA.info.source}}")
        print(pc['t'], flush=True)
        print('NOTE the times above are from a software renderer (no GPU here): they say nothing about the Mac.', flush=True)
        ok('Time the pieces runs (send, draw + blur, faces, small copy) and puts the source back', len(pc['d']) == 10 and all(v[1] >= 0 for v in pc['d']) and pc['src'] == 'scene' and 'send the clip list' in pc['t'])
        rn = pg.evaluate("async()=>{const rows=await __t.run(700);await new Promise(r=>setTimeout(r,1300));return {rows,t:document.querySelector('#res').textContent,live:document.querySelector('#live').textContent,a:__t.gA.info,scn:document.querySelector('#scn').value}}")
        print(rn['t'], flush=True)
        print('NOTE fps and kept% above come from a cloud machine without a GPU: they mean nothing. Only the last three columns (counters) are checked.', flush=True)
        tail = {x[:29].strip(): [float(v) for v in x.split()[-3:]] for x in rn['rows']}
        ok('Run fills the table: rows for Solid, Light, Glass, playing and the small-copy fallback at Light and Glass', list(tail) == ['Solid', 'Light, drawn on GPU', 'Glass, drawn on GPU', 'Glass, drawn on GPU, playing', 'Light, small copy', 'Glass, small copy'] and 'kept%' in rn['t'], list(tail))
        ok('Run: the "drawn on GPU" rows upload 0 canvases and send 0 clip lists while drawing the backdrop; Solid does nothing; the small-copy rows upload and draw no scene',
           tail['Solid'] == [0, 0, 0] and all(tail[k][0] > 0 and tail[k][1] == 0 and tail[k][2] == 0 for k in ['Light, drawn on GPU', 'Glass, drawn on GPU', 'Glass, drawn on GPU, playing']) and all(tail[k][0] == 0 and tail[k][1] > 0 for k in ['Light, small copy', 'Glass, small copy']), json.dumps(tail))
        ok('Run puts level, source and scene back; the live readout shows the frame share', rn['a']['level'] == 'glass' and rn['a']['source'] == 'scene' and rn['scn'] == 'scroll' and 'frames delivered' in rn['live'] and 'canvas uploads 0' in rn['live'], rn['live'].split('\n')[0])
    ctx.close()

    # phone width: nothing wider than the screen
    if dsf == 1:
        ctx = b.new_context(viewport={'width': 400, 'height': 800}); pg = ctx.new_page(); watch(pg)
        pg.goto('file://' + HERE + '/engine-test.html?soft=1'); pg.wait_for_function("()=>window.__t&&__t.gA.stats.draws>0", timeout=30000)
        r = pg.evaluate("()=>({sw:document.documentElement.scrollWidth,hud:document.querySelector('#hud').getBoundingClientRect().toJSON()})")
        ok('phone width (400 px): no sideways scroll, control card inside the screen', r['sw'] <= 400 and r['hud']['left'] >= 16 and r['hud']['right'] <= 384.5, r['hud'])
        ctx.close()

OUT = os.environ.get('GLASS_OUT', '/tmp')
if __name__ == '__main__':
    with sync_playwright() as p:
        b = p.chromium.launch(args=ARGS)
        unit_tests(b)
        if not os.environ.get('GLASS_UNIT_ONLY'):
            for dsf in (1, 2): page_tests(b, dsf)
        b.close()
    ok('no console errors or warnings in any test', not LOGS, LOGS[:5])
    bad = [r for r in RES if not r[1]]
    print('\n%d checks, %d failed' % (len(RES), len(bad)))
    sys.exit(1 if bad else 0)
