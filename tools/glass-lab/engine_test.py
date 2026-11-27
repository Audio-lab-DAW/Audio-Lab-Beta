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
    ok('scene: all of that with the rectangle list sent twice (start, playhead width) and no canvas upload', r['st']['sceneSends'] == 3 and r['st']['uploads'] == 0 and r['st']['flatUploads'] == 0 and r['n'] == 2 + 3 + 1 + 1 + 1, r['st'])

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
    ok('scene, first frame: rectangles sent once (400 clips), backdrop drawn once, one pyramid, no upload', f['sceneSends'] == 1 and f['sceneDraws'] == 1 and f['pyramids'] == 1 and f['uploads'] == 0 and r['n'] == 4 + 800 + 1, f)
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

def g2c_tests(b):
    # engine 2.1 (task G2c): small canvas with setOrigin, background as a clear, backdrop rate, the test page's debug switches, cached regions
    ctx, pg = unit_page(b)
    r = pg.evaluate(r"""()=>{ const out={}; const clips=[]; for(let i=0;i<80;i++) clips.push({x:i*37,y:(i%9)*64,w:29,h:60,color:['#e5534b','#4c8dff','#e3b341','#3ecf8e'][i&3]});
      const S=T.stripes(800,600,0);
      for(const way of ['scene','copy']) for(const over of ['backdrop','flats']) for(const [ox,oy] of [[264,124],[265,125]]){
        const mk=(w,h,x,y)=>{ const g=T.make(w,h,{blur:'light'}); if(way==='scene') g.setScene({clips,lanes:[{y:128,h:64,color:'#202838'}],playheadX:420,scrollX:13,rect:[0,0,800,600]}); else g.setBackdrop(S,{rect:[0,0,800,600]});
          g.setFlat('f',{rect:[0,300,800,300],color:[.5,.1,.1,1]}); g.addPanel({id:'w',rect:[300,160,300,200],radius:12,kind:'window',over}); g.setOrigin(x,y); g.render(); return g; };
        const full=mk(800,600,0,0), A=T.read(full), small=mk(372,272,ox,oy), B=T.read(small); let m=0,sum=0,n=0;
        for(let y=16;y<256;y++) for(let x=16;x<356;x++){ const ka=((y+oy)*A.w+x+ox)*4, kb=(y*B.w+x)*4; for(let c=0;c<4;c++){ const d=Math.abs(A[ka+c]-B[kb+c]); if(d>m)m=d; sum+=d; n++; } }
        const o={max:m,mean:sum/n,info:small.info.origin,up:small.stats.uploads,ss:small.stats.sceneSends,mid:T.px(B,186,136)};
        // the window moves by 8 px with its canvas: same picture again, nothing uploaded or sent again; setting the same origin again draws nothing
        full.updatePanel('w',{rect:[308,160,300,200]}); full.render(); small.updatePanel('w',{rect:[308,160,300,200]}); small.setOrigin(ox+8,oy); o.drew=small.render(); const A2=T.read(full), B2=T.read(small); let m2=0;
        for(let y=16;y<256;y++) for(let x=16;x<356;x++){ const ka=((y+oy)*A2.w+x+ox+8)*4, kb=(y*B2.w+x)*4; for(let c=0;c<4;c++) m2=Math.max(m2,Math.abs(A2[ka+c]-B2[kb+c])); }
        o.max2=m2; o.up2=small.stats.uploads; o.ss2=small.stats.sceneSends; small.setOrigin(ox+8,oy); o.again=small.render(); full.destroy(); small.destroy(); out[way+' '+over+' '+ox]=o; }
      return out; }""")
    al = {k: v for k, v in r.items() if k.endswith('264')}; od = {k: v for k, v in r.items() if k.endswith('265')}
    ok('setOrigin: a 372x272 canvas placed at (264,124) draws the same window, shadow and backdrop as an 800x600 canvas (scene and copy, over the backdrop and over flats)', all(v['max'] <= 2 and v['info'] == [264, 124] and v['mid'][3] == 255 for v in al.values()), json.dumps({k: [v['max'], round(v['mean'], 2)] for k, v in al.items()}))
    ok('setOrigin: an origin that is not a multiple of the small pixel gives the same picture within the blur (no jump)', all(v['mean'] < 1.5 and v['max'] <= 40 for v in od.values()), json.dumps({k: [v['max'], round(v['mean'], 2)] for k, v in od.items()}))
    ok('setOrigin: the canvas moves with its window: same picture, drawn once, no upload and no clip list sent again; the same origin again draws nothing', all(v['max2'] <= 2 and v['drew'] is True and v['again'] is False and v['up2'] == v['up'] and v['ss2'] == v['ss'] for v in al.values()), json.dumps({k: v['max2'] for k, v in al.items()}))
    r = pg.evaluate(r"""()=>{ const g=T.make(512,256,Object.assign({blur:'light',backdropColor:[0,0,1]},T.plain)); g.setScene({bg:[1,0,0,.5],rect:[128,0,256,256]});
      g.addPanel({id:'a',rect:[0,0,512,256],kind:'docked',tintAmount:0,lens:false}); g.render(); let b=T.read(g); const o={inside:T.px(b,256,128),outside:T.px(b,460,128),n:g.info.sceneRects,s0:{...g.stats}};
      g.setScene({bg:[0,1,0]}); g.render(); b=T.read(g); o.green=T.px(b,256,128); o.out2=T.px(b,40,128); o.s1={...g.stats};
      g.setScene({rect:[0,0,512,256]}); g.render(); b=T.read(g); o.all=T.px(b,460,128); g.destroy(); return o; }""")
    near = lambda a, e, tol=8: all(abs(x - y) <= tol for x, y in zip(a[:3], e))
    ok('scene background is the clear of the view rectangle: right colour inside (half-transparent over the backdrop colour), backdrop colour outside, it is not a rectangle in the list',
       near(r['inside'], [128, 0, 128]) and near(r['outside'], [0, 0, 255]) and r['n'] == 1 and near(r['green'], [0, 255, 0]) and near(r['out2'], [0, 0, 255]) and near(r['all'], [0, 255, 0]), [r['inside'], r['outside'], r['green'], r['all']])
    ok('a new background colour is one backdrop draw and does not send the list again', r['s1']['sceneSends'] == r['s0']['sceneSends'] == 1 and r['s1']['sceneDraws'] == r['s0']['sceneDraws'] + 1 and r['s1']['uploads'] == 0, [r['s0']['sceneSends'], r['s1']['sceneDraws']])
    r = pg.evaluate(r"""()=>{ const out={}; const clips=[]; for(let i=0;i<60;i++) clips.push({x:i*37,y:(i%9)*64,w:29,h:60,color:'#e5534b'});
      const g=T.make(800,600,{blur:'light'}); g.setScene({clips}); g.addPanel({id:'w',rect:[100,60,300,200],radius:12,kind:'window'}); g.render(0);
      const sec=(t0)=>{ const s={...g.stats}; for(let i=1;i<=240;i++){ g.setView({scrollX:i+t0}); g.updatePanel('w',{rect:[100+(i&63),60,300,200]}); g.render(t0+i*1000/240); } return {sd:g.stats.sceneDraws-s.sceneDraws,dr:g.stats.draws-s.draws,ss:g.stats.sceneSends-s.sceneSends,up:g.stats.uploads-s.uploads}; };
      out.every=sec(1000); g.setBackdropRate(120); out.r120=sec(3000); out.i120=g.info.rate; g.setBackdropRate(60); out.r60=sec(5000); g.setBackdropRate(0); out.back=sec(7000); out.i0=g.info.rate;
      g.setBackdropRate(120); g.setLevel('light'); out.light=g.info.rate; g.setLevel('glass'); g.setBackdropRate(null);
      // the test page's switches: hard edges, and a frozen backdrop with the faces still drawn
      g.setView({scrollX:13}); g.render(9000); const A=T.read(g); g.debug.set({aa:false}); g.render(9001); const B=T.read(g); let sum=0,n=0,lit=0; for(let k=0;k<A.length;k+=4){ sum+=Math.abs(A[k]-B[k]); n++; if(B[k]>40)lit++; } out.aa={mean:sum/n,lit};
      g.debug.set({aa:true}); g.render(9002); out.aaBack=T.maxDiff(A,T.read(g),0,0,800,600);
      g.debug.set({freeze:true}); g.render(9003); const s={...g.stats}; for(let i=1;i<=20;i++){ g.setView({scrollX:500+i}); g.render(9003+i*5); } out.frozen={sd:g.stats.sceneDraws-s.sceneDraws,py:g.stats.pyramids-s.pyramids,dr:g.stats.draws-s.draws};
      g.debug.set({freeze:false}); const s2={...g.stats}; for(let i=1;i<=20;i++){ g.setView({scrollX:600+i}); g.render(9200+i*5); } out.thaw={sd:g.stats.sceneDraws-s2.sceneDraws,dr:g.stats.draws-s2.draws}; out.err=g.gl.getError(); g.destroy();
      // the area under docked glass is worked out when a panel changes, not per frame: a docked panel that is moved or resized still gives the same pixels as working on everything
      const mk=cull=>{ const h=T.make(800,600,{blur:'regular',regionCull:cull}); h.setScene({clips,playheadX:300}); h.addPanel({id:'h',rect:[0,20,108,400],kind:'docked'}); h.addPanel({id:'t',rect:[0,576,800,24],kind:'docked'}); h.render();
        h.updatePanel('h',{rect:[0,20,180,300]}); h.render(); h.setView({scrollX:9}); h.render(); h.updatePanel('t',{rect:[0,500,800,100]}); h.setView({scrollX:20}); h.render(); return h; };
      const a=mk(true), b=mk(false); out.reg={d:T.maxDiff(T.read(a),T.read(b),0,0,800,600),ra:a.info.regions,rb:b.info.regions}; a.removePanel('h'); a.render(); b.removePanel('h'); b.render(); out.reg.d2=T.maxDiff(T.read(a),T.read(b),0,0,800,600); out.reg.ra2=a.info.regions; a.destroy(); b.destroy();
      return out; }""")
    ok('setBackdropRate at a simulated 240 frames per second: every change by default (240), 120 and 60 per second when asked, panels still redrawn on every frame, no upload, no list sent; a level with a lower rate keeps it',
       r['every']['sd'] == 240 and 118 <= r['r120']['sd'] <= 122 and 59 <= r['r60']['sd'] <= 61 and r['back']['sd'] == 240 and all(r[k]['dr'] == 240 and r[k]['ss'] == 0 and r[k]['up'] == 0 for k in ['every', 'r120', 'r60', 'back']) and r['i120'] == 120 and r['i0'] == 0 and r['light'] == 30, json.dumps({k: r[k] for k in ['every', 'r120', 'r60', 'back']}))
    ok('debug switch "anti-aliasing off": the backdrop is still drawn (hard edges, nearly the same picture) and comes back identical when switched on again', r['aa']['mean'] < 4 and r['aa']['lit'] > 1000 and r['aaBack'] == 0 and r['err'] == 0, r['aa'])
    ok('debug switch "frozen": a scroll redraws the faces but not the backdrop or its blur; switched off, the backdrop is drawn on every change again', r['frozen'] == {'sd': 0, 'py': 0, 'dr': 20} and r['thaw'] == {'sd': 20, 'dr': 20}, [r['frozen'], r['thaw']])
    ok('area under docked glass (now worked out only when a panel changes): after moving, resizing and removing docked panels the pixels are identical to working on everything', r['reg']['d'] == 0 and r['reg']['d2'] == 0 and r['reg']['ra'] >= 1 and r['reg']['rb'] == 0 and r['reg']['ra2'] >= 1, r['reg'])
    ctx.close()

def g2d_tests(b):
    # engine 2.2 (task G2d): square panels get a square lens (no arc inside a square corner, nothing jumps on the diagonal), the lens only on chosen or free edges, rounded panels as before
    import math
    ctx, pg = unit_page(b)
    kf = lambda d, band=45, amt=54: (1 - math.sqrt(max(0, 1 - (1 - min(1, max(0, (d + .5) / band))) ** 2))) * amt
    r = pg.evaluate(r"""()=>{ const out={}, D=[2,6,12,20,30,40], E=[2,6,12,20,30,40,100];
      for(const m of ['square','round','blend','fade']){ const g=T.make(256,256,Object.assign({blur:'light',corners:m},T.plain)); g.setBackdrop(T.ramp(256,256));
        g.addPanel({id:'a',rect:[28,28,200,200],radius:0,kind:'window',tintAmount:0,shadow:0}); g.render(); const b=T.read(g); let worst=0, prof=[], diag=[];
        // corner region against the straight-edge region: the sideways bend at a given distance from the left edge must be the same near the top edge as in the middle of the edge (and the same for the top edge)
        for(const dx of D) for(const dy of E){ worst=Math.max(worst, Math.abs(T.px(b,28+dx,28+dy)[0]-T.px(b,28+dx,128)[0]), Math.abs(T.px(b,28+dy,28+dx)[1]-T.px(b,128,28+dx)[1]),
          Math.abs(T.px(b,227-dx,227-dy)[0]-T.px(b,227-dx,128)[0]), Math.abs(T.px(b,227-dy,227-dx)[1]-T.px(b,128,227-dx)[1])); }
        for(const dx of D) prof.push([dx, T.px(b,28+dx,28+dx)[0]-(28+dx), T.px(b,28+dx,28+dx)[1]-(28+dx), T.px(b,28+dx,128)[0]-(28+dx)]);
        for(let i=2;i<40;i+=3) diag.push(Math.hypot(T.px(b,28+i,28+i)[0]-(28+i), T.px(b,28+i,28+i)[1]-(28+i)));
        out[m]={worst,prof,diag,info:g.panelInfo('a'),corners:g.info.corners}; g.destroy(); }
      out.def=AudioLabGlass.create(document.createElement('canvas'),{forceFallback:true}).info.corners; out.ver=AudioLabGlass.version; out.list=AudioLabGlass.CORNERS; return out; }""")
    ok('engine 2.2.0; the default corner model is "square"; the others are still there (blend, fade, round)', r['ver'] == '2.2.0' and r['def'] == 'square' and sorted(r['list']) == ['blend', 'fade', 'round', 'square'], [r['ver'], r['def']])
    perr = max(max(abs(x - kf(dx)), abs(y - kf(dx)), abs(m - kf(dx))) for dx, x, y, m in r['square']['prof'])
    ok('square panel (radius 0, lens wide): NO curved band in the corner: at every distance from an edge the bend is the same in the corner region as along the straight edge (all four edges, two corners)',
       r['square']['worst'] <= 1.5 and r['square']['info'] == {'edges': 'trbl', 'square': True, 'band': 45}, 'worst difference %.1f px' % r['square']['worst'])
    ok('square panel: on the corner diagonal each edge bends by its own profile (the two add), so nothing can jump there', perr <= 2.5, 'worst error %.2f px' % perr)
    ok('...and the same comparison does see the arc of the rounded lens (2.1 look, corners "round") and the diagonal of "blend" and "fade", so the check above means something',
       all(r[m]['worst'] >= 8 for m in ['round', 'blend', 'fade']) and not r['round']['info']['square'], {m: round(r[m]['worst'], 1) for m in r if m in ('round', 'blend', 'fade')})
    ok('"fade": no bend at all on the diagonal; "blend": the bend there is as long as one edge\'s', max(r['fade']['diag']) <= 1.5 and all(abs(a - kf(2 + 3 * i - 1)) <= 4 for i, a in enumerate(r['blend']['diag'])), [round(max(r['fade']['diag']), 1), [round(x) for x in r['blend']['diag'][:4]]])

    # rounded panels: identical pixels with every corner model
    r = pg.evaluate(r"""()=>{ const res={}, shots={}; for(const m of ['round','square','blend','fade']){ const g=T.make(400,300,{blur:'light',corners:m}); g.setBackdrop(T.stripes(400,300,0));
        g.addPanel({id:'w',rect:[20,20,220,160],radius:16,kind:'window'}); g.addPanel({id:'m',rect:[250,30,130,150],radius:12,kind:'menu'}); g.addPanel({id:'p',rect:[40,220,150,32],radius:16,kind:'pill'}); g.addPanel({id:'e',rect:[230,210,150,70],radius:8,kind:'sheet'});
        g.render(); shots[m]=T.read(g); res[m]={sq:['w','m','p','e'].map(k=>g.panelInfo(k).square)}; g.destroy(); }
      for(const m of ['square','blend','fade']) res[m].d=T.maxDiff(shots.round,shots[m],0,0,400,300); let lit=0; for(let i=3;i<shots.round.length;i+=4) if(shots.round[i]>250) lit++; res.lit=lit; return res; }""")
    ok('rounded panels are unchanged: a window (radius 16), a menu (12), a pill (16) and a sheet (8) are pixel-identical with every corner model, "round" (the 2.1 lens) included',
       all(r[m]['d'] == 0 and r[m]['sq'] == [False] * 4 for m in ['square', 'blend', 'fade']) and r['lit'] > 40000, {m: r[m]['d'] for m in ['square', 'blend', 'fade']})

    # which panels count as square
    r = pg.evaluate(r"""()=>{ const g=T.make(300,300,{blur:'light'}); g.setBackdrop(T.ramp(300,300)); const sq=(d)=>{ g.addPanel(Object.assign({id:'a',rect:[40,40,200,200],kind:'window',corners:undefined,edges:undefined},d)); return g.panelInfo('a').square; };
      const o={r0:sq({radius:0}),r6:sq({radius:6}),r8:sq({radius:8}),r16:sq({radius:16}),force:sq({radius:16,corners:'square'}),keep:sq({radius:0,corners:'round'}),edge:sq({radius:16,edges:'tb'})};
      const h=T.make(300,300,{blur:'light',squareBelow:20}); h.addPanel({id:'a',rect:[40,40,200,200],radius:16}); o.opt=h.panelInfo('a').square; h.destroy(); g.destroy(); return o; }""")
    ok('square lens for a radius under 8 px (option squareBelow); corners:"square" / "round" on a panel decide for that panel; a rounded panel that bends only along some edges takes the square lens',
       r == {'r0': True, 'r6': True, 'r8': False, 'r16': False, 'force': True, 'keep': False, 'edge': True, 'opt': True}, r)

    # edges: only the named edges bend
    r = pg.evaluate(r"""()=>{ const g=T.make(256,256,Object.assign({blur:'light'},T.plain)); g.setBackdrop(T.ramp(256,256)); const out={};
      const P=(d)=>{ g.addPanel(Object.assign({id:'a',rect:[28,28,200,200],radius:0,kind:'window',tintAmount:0,shadow:0},d)); g.render(); return T.read(g); };
      const dv=(b,x,y)=>[T.px(b,x,y)[0]-x, T.px(b,x,y)[1]-y];
      let b=P({edges:'tr'}); out.tr={left:dv(b,33,128),top:dv(b,128,33),right:dv(b,222,128),bottom:dv(b,128,222),tl:dv(b,33,33),bl:dv(b,33,222),br:dv(b,222,222),info:g.panelInfo('a')};
      const none=P({edges:'none'}), off=P({edges:'all',lens:false}); out.none=T.maxDiff(none,off,0,0,256,256); out.noneInfo=g.panelInfo('a');
      g.updatePanel('a',{lens:true,edges:'none'}); out.noneE=g.panelInfo('a').edges; g.updatePanel('a',{edges:'l'}); g.render(); b=T.read(g); out.l={left:dv(b,33,128),top:dv(b,128,33),tl:dv(b,33,33)};
      g.updatePanel('a',{edges:'all'}); out.all=g.panelInfo('a').edges; g.updatePanel('a',{edges:'tb'}); const dr=g.render(), st=g.stats.draws, again=(g.updatePanel('a',{edges:'tb'}), g.render()); out.dirty=[dr,again,g.stats.draws-st]; g.destroy(); return out; }""")
    e5 = kf(5); t = r['tr']; z = lambda v: abs(v[0]) <= 1 and abs(v[1]) <= 1
    ok('edges "tr": the top and right edges bend by the usual profile, the left and bottom edges not at all; in the corners only the edge that carries the lens bends (straight to the end)',
       z(t['left']) and z(t['bottom']) and z(t['bl']) and abs(t['top'][1] - e5) <= 2.5 and abs(t['top'][0]) <= 1 and abs(t['right'][0] + e5) <= 2.5 and abs(t['tl'][1] - e5) <= 2.5 and abs(t['tl'][0]) <= 1 and abs(t['br'][0] + e5) <= 2.5 and abs(t['br'][1]) <= 1 and t['info']['edges'] == 'tr' and t['info']['square'],
       {k: v for k, v in t.items() if k != 'info'})
    ok('edges "none" is pixel-identical to a panel without lens; "l" bends only the left edge; changing edges redraws the faces once, the same value again nothing',
       r['none'] == 0 and r['noneE'] == '' and abs(r['l']['left'][0] - e5) <= 2.5 and z(r['l']['top']) and abs(r['l']['tl'][0] - e5) <= 2.5 and abs(r['l']['tl'][1]) <= 1 and r['all'] == 'trbl' and r['dirty'] == [True, False, 0], [r['none'], r['l'], r['dirty']])

    # edges 'auto' (the default for docked panels): only the free edges
    r = pg.evaluate(r"""()=>{ const g=T.make(256,256,Object.assign({blur:'light'},T.plain)); g.setBackdrop(T.ramp(256,256)); const o={}, E=()=>['a','b','c'].map(k=>g.panelInfo(k).edges).join(' ');
      const dk=(id,rect,d)=>g.addPanel(Object.assign({id,rect,radius:0,kind:'docked',tintAmount:0},d)); dk('a',[0,40,100,160]); dk('b',[0,200,256,30]); dk('c',[0,230,256,26]);
      o.start=E(); g.render(); const b=T.read(g), dv=(x,y)=>[T.px(b,x,y)[0]-x, T.px(b,x,y)[1]-y]; o.px={bl:dv(5,194),left:dv(5,120),bottom:dv(50,194),right:dv(94,120),top:dv(50,45)};
      g.updatePanel('b',{visible:false}); o.hidden=E(); g.updatePanel('b',{visible:true}); o.back=E();
      dk('d',[0,0,60,40]); dk('e',[60,0,196,40]); o.joint=g.panelInfo('a').edges; g.removePanel('e'); o.part=g.panelInfo('a').edges; g.removePanel('d');
      g.updatePanel('b',{rect:[0,201.5,256,28.5]}); o.gap=g.panelInfo('a').edges; g.updatePanel('b',{rect:[0,200.6,256,29.4]}); o.close=g.panelInfo('a').edges; g.updatePanel('b',{rect:[0,200,256,30]});
      g.addPanel({id:'w',rect:[0,0,80,40],radius:0,kind:'window'}); o.win=g.panelInfo('w').edges; o.winNoNeighbour=g.panelInfo('a').edges; g.removePanel('w');
      g.updatePanel('a',{edges:'all'}); o.forced=g.panelInfo('a').edges; g.updatePanel('a',{edges:'auto'});
      g.setBounds([-50,-50,400,400]); o.bounds=E(); g.setBounds(null); o.boundsBack=E();
      g.setCorners('round'); o.round=E(); g.setCorners('square');
      // a canvas that is only a part of the window: its border is not the window's border unless the app says where the window is
      const s=T.make(120,100,Object.assign({blur:'light'},T.plain)); s.setOrigin(60,80); s.addPanel({id:'a',rect:[60,80,120,100],radius:0,kind:'docked'}); o.small=s.panelInfo('a').edges; s.setBounds([0,0,180,400]); o.smallB=s.panelInfo('a').edges; s.destroy();
      o.kinds=Object.fromEntries(Object.entries(AudioLabGlass.KINDS).map(([k,v])=>[k,v.edges||'all'])); g.destroy(); return o; }""")
    ok("edges 'auto' (docked panels): a panel on the left border with another panel under it bends only on top and right; a bar whose top is only partly covered keeps its top; the bottom bar bends nowhere",
       r['start'] == 'tr t ' and r['kinds'] == {'docked': 'auto', 'window': 'all', 'sheet': 'all', 'menu': 'all', 'pill': 'all'}, r['start'])
    p = r['px']; e4 = kf(5, 100 / 3, 40)   # a 100 px wide panel: band 33 px, bend up to 40 px
    ok('...in pixels: nothing bends in the bottom left corner, along the left edge or along the bottom edge of that panel; the right and top edges bend by the profile',
       z(p['bl']) and z(p['left']) and z(p['bottom']) and abs(p['right'][0] + e4) <= 2.5 and abs(p['top'][1] - e4) <= 2.5, p)
    ok('auto follows the panels: neighbour hidden -> the edge is free again; two panels that together cover an edge close it, one alone does not; a gap of 1.5 px is free, 0.6 px is closed',
       r['hidden'] == 'trb t t' and r['back'] == 'tr t ' and r['joint'] == 'r' and r['part'] == 'tr' and r['gap'] == 'trb' and r['close'] == 'tr', [r['hidden'], r['joint'], r['part'], r['gap'], r['close']])
    ok("auto: floating kinds keep every edge even on the border and do not close a docked panel's edge; edges:'all' on a docked panel wins; setBounds says where the window is (also for a canvas smaller than the window); corners 'round' ignores edges",
       r['win'] == 'trbl' and r['winNoNeighbour'] == 'tr' and r['forced'] == 'trbl' and r['bounds'] == 'trl trl rbl' and r['boundsBack'] == 'tr t ' and r['round'] == 'trbl trbl trbl' and r['small'] == '' and r['smallB'] == 'tbl',
       [r['bounds'], r['small'], r['smallB']])

    # switching the corner model costs one face redraw; context loss with another model
    r = pg.evaluate(r"""async()=>{ const g=T.make(256,256,{blur:'light'}); g.setScene({clips:[{x:10,y:10,w:100,h:60,color:'#e5534b'}]}); g.addPanel({id:'a',rect:[0,40,100,160],radius:0,kind:'docked'}); g.render(); const s0={...g.stats}, o={};
      g.setCorners('fade'); o.drew=g.render(); o.same=(g.setCorners('fade'), g.render()); o.bad=(g.setCorners('nope'), g.info.corners); const s1={...g.stats}; o.d={py:s1.pyramids-s0.pyramids,sd:s1.sceneDraws-s0.sceneDraws,ss:s1.sceneSends-s0.sceneSends,dr:s1.draws-s0.draws};
      g.debug.lose(); await new Promise(r=>setTimeout(r,200)); o.lost=g.mode; g.debug.restore(); await new Promise(r=>setTimeout(r,300)); g.render(); const b=T.read(g); o.mode=g.mode; o.px=T.px(b,50,120); o.corners=g.info.corners; g.destroy(); return o; }""")
    ok('setCorners: one face redraw, no backdrop work, nothing sent; the same value or an unknown one does nothing; after a lost and restored context the chosen model draws again',
       r['drew'] and not r['same'] and r['bad'] == 'fade' and r['d'] == {'py': 0, 'sd': 0, 'ss': 0, 'dr': 1} and r['lost'] == 'fallback' and r['mode'] == 'gl' and r['px'][3] == 255 and r['corners'] == 'fade', r)
    ctx.close()

def g2d_page(b):
    # the Corners chooser and the zoomed corner on the test page
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1)
    pg = ctx.new_page(); watch(pg)
    pg.goto('file://' + HERE + '/engine-test.html?soft=1'); pg.wait_for_function("()=>window.__t&&__t.gA.stats.draws>0", timeout=30000)
    pg.wait_for_timeout(400)
    E = "()=>Object.fromEntries(Object.keys(__t.P).map(k=>[k,(k==='mix'||k==='menu'||k==='pill'?__t.gB:__t.gA).panelInfo(k)]))"
    r = pg.evaluate("()=>({opts:[...document.querySelectorAll('#ksel option')].map(o=>o.textContent),sel:document.querySelector('#ksel').value,k:__t.k,a:__t.gA.info.corners,b:__t.gB.info.corners,ver:document.querySelector('#ver').textContent})")
    ok('test page: Corners chooser K1 to K7, the star on K7 (square, lens only on free edges), which is selected and is what the engine does by default', len(r['opts']) == 7 and [o[:2] for o in r['opts']] == ['K%d' % i for i in range(1, 8)] and r['opts'][6].startswith('K7 ★') and sum('★' in o for o in r['opts']) == 1 and r['sel'] == 'K7' and r['k'] == 'K7' and r['a'] == 'square' and r['b'] == 'square' and r['ver'] == '2.2.0', r['opts'])
    e = pg.evaluate(E)
    ok('test page, K7 (as the app will use it: the engine finds the free edges): track headers bend on top and right only, the tab band on top only, device panel and transport nowhere; mixer, menu and pill on every edge with the rounded lens',
       [e[k]['edges'] for k in ['hdr', 'band', 'dev', 'tr', 'mix', 'menu', 'pill']] == ['tr', 't', '', '', 'trbl', 'trbl', 'trbl'] and all(e[k]['square'] for k in ['hdr', 'band', 'dev', 'tr']) and not any(e[k]['square'] for k in ['mix', 'menu', 'pill']), {k: v['edges'] for k, v in e.items()})
    # pixels of the docked layer, the same instant: lens on against lens off
    shot = r"""(k)=>{ const g=__t.gA, gl=g.gl, W=gl.drawingBufferWidth, H=gl.drawingBufferHeight, P=__t.P.hdr, rd=()=>{ g.render(); g.debug.draw(); const b=new Uint8Array(W*H*4); gl.readPixels(0,0,W,H,gl.RGBA,gl.UNSIGNED_BYTE,b); return b; };
      __t.setK(k); g.setLensPreset('wide'); const on=rd(); g.setLensPreset('off'); const off=rd(); g.setLensPreset('wide'); g.render();
      const diff=(x0,y0,x1,y1)=>{ let m=0; for(let y=y0;y<y1;y++) for(let x=x0;x<x1;x++){ const i=((H-1-y)*W+x)*4; for(let c=0;c<3;c++) m=Math.max(m,Math.abs(on[i+c]-off[i+c])); } return m; };
      const bot=P.y+P.h; return {bl:diff(0,bot-70,70,bot), left:diff(0,P.y+60,44,bot-60), tr:diff(P.x+P.w-44,P.y,P.x+P.w,P.y+44), right:diff(P.x+P.w-44,P.y+60,P.x+P.w,bot-60), dev:diff(0,__t.P.dev.y,300,__t.P.dev.y+60), trn:diff(0,__t.P.tr.y,300,__t.P.tr.y+48)}; }"""
    k7 = pg.evaluate(shot, 'K7'); k4 = pg.evaluate(shot, 'K4'); k1 = pg.evaluate(shot, 'K1'); pg.evaluate("()=>__t.setK('K7')")
    ok('test page, K7 in pixels: the bottom left corner and the left edge of the track headers, the device panel and the transport are identical with the lens on and off (no rim on edges that border nothing); the top right corner and the right edge still bend',
       k7['bl'] == 0 and k7['left'] == 0 and k7['dev'] == 0 and k7['trn'] == 0 and k7['tr'] > 8 and k7['right'] > 8, k7)
    ok('test page: K4 (every edge) and K1 (as before) do bend in that corner, so the chooser changes what it says it changes', k4['bl'] > 8 and k1['bl'] > 8 and k1['dev'] > 8, [k4, k1])
    r = pg.evaluate("""async()=>{ const s=(id,v)=>{const e=document.querySelector(id);if(e.type==='checkbox')e.checked=v;else e.value=v;e.dispatchEvent(new Event('change',{bubbles:true}))}, w=ms=>new Promise(r=>setTimeout(r,ms)), o={};
      const E=()=>['hdr','band','dev','tr'].map(k=>__t.gA.panelInfo(k).edges).join(' '); s('#p_band',false); await w(100); o.noBand=E(); s('#p_band',true); await w(100); o.back=E();
      const zc=document.querySelector('#zoom'), seen=()=>{ const d=zc.getContext('2d').getImageData(0,0,zc.width,zc.height).data, c=new Set(); for(let i=0;i<d.length;i+=16) c.add(d[i]>>3<<10|d[i+1]>>3<<5|d[i+2]>>3); return c.size; };
      o.zoom={}; for(const z of ['hdrBL','hdrTR','devTL','bandTL','mixTL']){ s('#zsel',z); await w(350); o.zoom[z]=seen(); } s('#zsel','hdrBL');
      s('#scn','still'); s('#drag',false); await w(500); const d0=__t.gA.stats.draws+__t.gB.stats.draws; await w(500); o.idle=__t.gA.stats.draws+__t.gB.stats.draws-d0;
      s('#ksel','K2'); await w(300); o.k2=[__t.k,__t.gA.info.corners,E()]; o.afterChange=__t.gA.stats.draws+__t.gB.stats.draws-d0; s('#ksel','K7'); await w(200);
      s('#zon',false); o.hidden=document.querySelector('#zbox').hidden; s('#zon',true); s('#scn','scroll'); s('#drag',true); return o; }""")
    ok('test page: hiding the tab band frees the edges it closed (track headers bottom, device panel top) and showing it closes them again', r['noBand'] == 'trb t t ' and r['back'] == 'tr t  ', [r['noBand'], r['back']])
    ok('test page: the zoomed corner shows a picture for each of its five corners; with nothing moving it draws nothing (0 face redraws in half a second) and a change of the chooser redraws it', all(v >= 4 for v in r['zoom'].values()) and r['idle'] == 0 and 1 <= r['afterChange'] <= 6 and r['k2'] == ['K2', 'blend', 'trbl trbl trbl trbl'] and r['hidden'], [r['zoom'], r['idle'], r['afterChange']])
    for k in ['K1', 'K4', 'K7']:
        pg.evaluate("k=>{__t.setK(k)}", k); pg.wait_for_timeout(400); pg.screenshot(path=os.path.join(OUT, 'engine-test-%s.png' % k))
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
       noup(r) and r['a']['sceneDraws'] == 0 and r['b']['sceneDraws'] == 0 and r['a']['draws'] == 0 and r['b']['flatPyramids'] == 0 and r['b']['draws'] >= N * .3, short(r))   # the mixer moves by whole pixels along a sine: near its turning points it stands still for a few frames
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
    # 2.1: the floating canvas only as large as its glass (setOrigin). Same picture, a fraction of the canvas.
    c8 = lambda v: -(-v // 8) * 8
    pg.evaluate(setsel, ['#p_menu', False]); pg.evaluate(setsel, ['#p_pill', False]); settle(); wide = shot()
    pg.evaluate(setsel, ['#fit', True]); settle(); fitted = shot(); fi = pg.evaluate("()=>({b:__t.gB.info,r:__t.bRect,tr:__t.cB.style.transform,w:__t.cB.getBoundingClientRect().toJSON()})")
    d = diff(wide, fitted, (x0 - 30, y0 - 20, x0 + w0 + 30, y0 + h0 + 34))
    ok('fitted floating canvas: the mixer window and its shadow look the same as with a full-window canvas, on a canvas of 1168x504 instead of 1600x1000' + tag,
       d[0] <= 3 and fi['r'] == [x0 - 34, y0 - 34, c8(w0 + 68), c8(h0 + 68)] and fi['b']['width'] == c8(w0 + 68) * dsf and fi['b']['height'] == c8(h0 + 68) * dsf and fi['b']['origin'] == [x0 - 34, y0 - 34] and abs(fi['w']['left'] - (x0 - 34)) < .01 and abs(fi['w']['width'] - c8(w0 + 68)) < .01, 'max difference %d of 255, mean %.2f; canvas %dx%d at %s' % (d[0], d[1], fi['b']['width'], fi['b']['height'], fi['b']['origin']))
    pg.evaluate(setsel, ['#scn', 'scroll']); pg.evaluate(setsel, ['#drag', True]); pg.wait_for_timeout(300)
    o0 = pg.evaluate("()=>__t.gB.info.origin"); r = pg.evaluate(count, N); pg.wait_for_timeout(250); fi2 = pg.evaluate("()=>({b:__t.gB.info,r:__t.bRect,mx:__t.P.mix.x+__t.P.mix.dx})")
    ok('fitted floating canvas, scrolling + mixer moving: the canvas travels with the window (origin follows, size stays), uploads == 0, clip list not sent again, backdrop drawn every frame' + tag,
       noup(r) and r['b']['sceneDraws'] >= N - 2 and r['a']['sceneDraws'] >= N - 2 and fi2['b']['width'] == c8(w0 + 68) * dsf and fi2['b']['origin'] == [fi2['mx'] - 34, y0 - 34] and fi2['r'][0] == fi2['mx'] - 34, [o0, fi2['b']['origin'], short(r)])
    pg.evaluate(setsel, ['#p_menu', True]); pg.wait_for_timeout(200); fi3 = pg.evaluate("()=>({b:__t.gB.info,r:__t.bRect})")
    ok('fitted floating canvas with a second floating panel: one canvas over both and the window\'s travel, standing still' + tag, fi3['b']['origin'] == fi3['r'][:2] and fi3['r'][2] > w0 + 68 and fi3['r'][2] % 8 == 0 and fi3['r'][2] < 1600 and fi3['b']['width'] == fi3['r'][2] * dsf, fi3['r'])
    pg.evaluate(setsel, ['#fit', False]); pg.evaluate(setsel, ['#p_pill', True]); pg.evaluate(setsel, ['#scn', 'still']); pg.evaluate(setsel, ['#drag', False]); pg.evaluate("()=>{__t.P.mix.dx=0;__t.layout()}"); settle()
    fi4 = pg.evaluate("()=>({b:__t.gB.info,r:__t.bRect})"); back = shot(); d = diff(glass, back, (0, 0, 1600, 1000))
    ok('fit off again: full-window canvas, origin 0, the page looks exactly as before' + tag, fi4['r'] == [0, 0, 1600, 1000] and fi4['b']['origin'] == [0, 0] and fi4['b']['width'] == 1600 * dsf and d[0] <= 1, 'max difference %d' % d[0])
    # 2.1: Solid as in Glass Bench 3 (no engine canvas, plain DOM panels) and Bench 3's own GPU path on this page
    pg.evaluate("()=>__t.setPm('dom')"); settle(); r = pg.evaluate(count, 10); dom = shot(); c = dom.getpixel((int(100 * dsf), int(300 * dsf)))
    dm = pg.evaluate("()=>[getComputedStyle(__t.cA).display,getComputedStyle(__t.cB).display,getComputedStyle(__t.DC).display]")
    ok('page mode "Solid as in Bench 3": both engine canvases and the display are out of the page, the engine is not called, the panels are plain DOM in the panel colour' + tag,
       dm == ['none', 'none', 'none'] and r['a']['renders'] == 0 and r['b']['renders'] == 0 and all(abs(a - e) <= 22 for a, e in zip(c, [22, 28, 42])), [dm, c])
    pg.evaluate("()=>__t.setPm('b3')"); settle(); settle(); b3 = shot(); r = pg.evaluate(count, 10)
    bi = pg.evaluate("()=>({ok:__t.B3.ok,n:document.querySelectorAll('#stage canvas').length,band:__t.P.band.el.hidden,menu:__t.P.menu.el.hidden,hh:__t.P.hdr.h,err:__t.B3.gl.getError()})")
    e3, em3 = energy(b3, (60, 120, 160, 560)), energy(b3, (330, 130, 1270, 440))
    ok('page mode "Bench 3 path": Bench 3\'s own canvas and GL code draw frosted headers and mixer (five panels, no tab band, no menu), the engine is not called, no GL error' + tag,
       bi['ok'] and bi['n'] == 5 and bi['band'] and bi['menu'] and bi['err'] == 0 and r['a']['renders'] == 0 and e3 < eb * .2 and em3 < ebm * .2 and e3 > 0, 'headers %d of %d, mixer %d of %d' % (e3, eb, em3, ebm))
    b3.save(os.path.join(OUT, 'engine-test-bench3-path-%dx.png' % dsf))
    pg.evaluate("()=>__t.setPm('engine')"); settle(); settle(); back = shot(); d = diff(glass, back, (0, 0, 1600, 1000))
    ok('back to the engine: Bench 3\'s canvas and context are gone, the glass looks exactly as before' + tag, d[0] <= 1 and pg.evaluate("()=>document.querySelectorAll('#stage canvas').length") == 4 and not pg.evaluate("()=>__t.B3.ok"), 'max difference %d' % d[0])

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
        rn = pg.evaluate("async()=>{const rows=await __t.run(700);await new Promise(r=>setTimeout(r,1300));return {rows,t:document.querySelector('#res').textContent,live:document.querySelector('#live').textContent,a:__t.gA.info,pm:__t.pm,cv:document.querySelectorAll('#stage canvas').length,scn:document.querySelector('#scn').value}}")
        print(rn['t'], flush=True)
        print('NOTE fps and kept% above come from a cloud machine without a GPU: they mean nothing. Only the last three columns (counters) are checked.', flush=True)
        tail = {x[:31].strip(): [float(v) for v in x.split()[-3:]] for x in rn['rows']}
        ok('Run fills the table: Solid as in Bench 3 (page only), Solid by the engine, Light, Glass, playing, the small-copy fallback at Light and Glass, and the Bench 3 path', list(tail) == ['Solid (page only, as Bench 3)', 'Solid, drawn by the engine', 'Light, drawn on GPU', 'Glass, drawn on GPU', 'Glass, drawn on GPU, playing', 'Light, small copy', 'Glass, small copy', 'Bench 3 path (its own GL code)'] and 'kept%' in rn['t'] and 'screen frame' in rn['t'], list(tail))
        ok('Run: the "drawn on GPU" rows upload 0 canvases and send 0 clip lists while drawing the backdrop; Solid does nothing; the small-copy rows upload and draw no scene',
           all(tail[k] == [0, 0, 0] for k in ['Solid (page only, as Bench 3)', 'Solid, drawn by the engine', 'Bench 3 path (its own GL code)']) and all(tail[k][0] > 0 and tail[k][1] == 0 and tail[k][2] == 0 for k in ['Light, drawn on GPU', 'Glass, drawn on GPU', 'Glass, drawn on GPU, playing']) and all(tail[k][0] == 0 and tail[k][1] > 0 for k in ['Light, small copy', 'Glass, small copy']), json.dumps(tail))
        ok('Run puts level, source, scene and the page mode back; the live readout shows the frame share', rn['pm'] == 'engine' and rn['cv'] == 4 and rn['a']['level'] == 'glass' and rn['a']['source'] == 'scene' and rn['scn'] == 'scroll' and 'frames delivered' in rn['live'] and 'canvas uploads 0' in rn['live'], rn['live'].split('\n')[0])
        fd = pg.evaluate("""async()=>{const rows=await __t.find(350);await new Promise(r=>setTimeout(r,700));const g=__t.gA,b=__t.gB,s0=g.stats.sceneDraws;await new Promise(r=>setTimeout(r,500));
          return {rows,t:document.querySelector('#res2').textContent,pm:__t.pm,X:__t.X,on:Object.values(__t.P).every(p=>p.on&&!p.el.hidden),a:g.info,b:b.info,bRect:__t.bRect,cv:document.querySelectorAll('#stage canvas').length,
            disp:[getComputedStyle(__t.cA).display,getComputedStyle(__t.cB).display],scn:document.querySelector('#scn').value,drag:document.querySelector('#drag').checked,fit:document.querySelector('#fit').checked,moving:g.stats.sceneDraws>s0,n:g.info.sceneRects}}""")
        print(fd['t'], flush=True)
        print('NOTE as above: no GPU here, the numbers mean nothing. Only that every row runs and everything is put back is checked.', flush=True)
        names = [x[:31].strip() for x in fd['rows']]
        ok('Find the cost: one row per switch (anti-aliasing, background rate, frozen, idle, each layer, each panel, 0 clips, page scrolling, mixer, lens, half size, fitted canvas, Bench 3 path, playing)',
           len(names) == 25 and names[1] == 'Glass scrolling, everything on' and all(any(k in n for n in names) for k in ['anti-aliasing off', '120 per second', '60 per second', 'frozen', 'engine idle', 'floating layer off', 'docked layer off', 'without track headers', 'without pill', '0 clips', 'page scrolling off', 'mixer not moving', 'lens off', 'half size', 'only the mixer', 'fitted', 'Bench 3 path', 'playing']) and 'change' in fd['t'], names)
        ok('Find the cost puts everything back (page mode, both canvases shown and full size, origin 0, all panels, level, source, scrolling, mixer moving, lens, rate, the clip list, backdrop drawn again)',
           fd['pm'] == 'engine' and not any(fd['X'].values()) and fd['on'] and fd['cv'] == 4 and fd['disp'] == ['block', 'block'] and fd['bRect'] == [0, 0, 1600, 1000] and fd['b']['origin'] == [0, 0] and fd['b']['width'] == 1600 and fd['a']['width'] == 1600 and fd['a']['dpr'] == 1
           and fd['a']['level'] == 'glass' and fd['a']['source'] == 'scene' and fd['a']['lens'] == 'wide' and fd['a']['rate'] == 0 and fd['scn'] == 'scroll' and fd['drag'] and not fd['fit'] and fd['moving'] and fd['n'] > 100, [fd['pm'], fd['bRect'], fd['n']])
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
        g2c_tests(b)
        g2d_tests(b)
        if not os.environ.get('GLASS_UNIT_ONLY'):
            g2d_page(b)
            for dsf in (1, 2): page_tests(b, dsf)
        b.close()
    ok('no console errors or warnings in any test', not LOGS, LOGS[:5])
    bad = [r for r in RES if not r[1]]
    print('\n%d checks, %d failed' % (len(RES), len(bad)))
    sys.exit(1 if bad else 0)
