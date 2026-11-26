#!/usr/bin/env python3
"""Headless checks for tools/glass-lab/glass-engine.js and engine-test.html.
Run: python3 tools/glass-lab/engine_test.py      (needs Python Playwright with Chromium)
The cloud machine has no GPU (SwiftShader), so only correctness is checked here; frame rates mean nothing."""
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
    ctx, pg = unit_page(b)
    # ---- 1. lens: rim bends by Apple's profile, the middle is flat ----
    r = pg.evaluate(r"""()=>{ const g=T.make(256,256,Object.assign({blur:'light'},T.plain)); g.setBackdrop(T.ramp(256,256));
      g.addPanel({id:'a',rect:[28,28,200,200],radius:16,kind:'window',tintAmount:0,shadow:0});
      const out={}; for(const l of ['off','fine','apple','wide']){ g.setLensPreset(l); g.render(); const b=T.read(g), row=[];
        for(const dd of [2,5,10,15,19,25,40,100]) row.push([dd, T.px(b,28+dd,128)[0]-(28+dd), T.px(b,128,28+dd)[1]-(28+dd), T.px(b,227-dd,128)[0]-(227-dd)]);
        out[l]=row; out[l+'_mid']=T.px(b,128,128); out[l+'_out']=T.px(b,10,128); }
      out.info=g.info; g.destroy(); return out; }""")
    import math
    def expect(dd, band, amt):
        x = min(1, max(0, (dd + .5) / band)); return (1 - math.sqrt(max(0, 1 - (1 - x) ** 2))) * amt
    worst = 0
    for name, band, amt in [('fine', 12, 24), ('apple', 20, 24), ('wide', 40, 48)]:
        for dd, left, topv, right in r[name]:
            e = expect(dd, band, amt); worst = max(worst, abs(left - e), abs(topv - e), abs(right + e))
    ok('lens: rim displacement follows the quarter-circle profile on left, top and right edges (fine, Apple, wide)', worst <= 2.0, 'worst error %.2f px' % worst)
    ok('lens: band is min(short side / 4, 20) for Apple (200 px panel: 20 px; nothing bends at 25 px and beyond)', all(abs(v[1]) <= 1 for v in r['apple'] if v[0] >= 25) and r['apple'][0][1] > 10, 'at 2 px: %d px, at 25 px: %d px' % (r['apple'][0][1], r['apple'][5][1]))
    ok('lens off: nothing bends anywhere', all(abs(v[1]) <= 1 and abs(v[2]) <= 1 for v in r['off']))
    ok('middle is flat: same pixel with every lens preset', len({tuple(r[l + '_mid']) for l in ['off', 'fine', 'apple', 'wide']}) == 1, r['apple_mid'])
    ok('outside the panel the canvas is transparent', r['apple_out'] == [0, 0, 0, 0], r['apple_out'])

    # lens band follows the panel size: 48 px bar gets 12 px, 32 px pill gets 8 px
    r = pg.evaluate(r"""()=>{ const g=T.make(256,256,Object.assign({blur:'light'},T.plain)); g.setBackdrop(T.ramp(256,256));
      g.addPanel({id:'a',rect:[20,100,216,48],radius:0,kind:'docked',tintAmount:0}); g.render(); let b=T.read(g);
      const bar=[]; for(let d=0;d<24;d++) bar.push(T.px(b,128,100+d)[1]-(100+d));
      g.updatePanel('a',{rect:[40,100,150,32],radius:16}); g.render(); b=T.read(g); const pill=[]; for(let d=0;d<16;d++) pill.push(T.px(b,115,100+d)[1]-(100+d)); g.destroy(); return {bar,pill}; }""")
    bar_band = max(i for i, v in enumerate(r['bar']) if v >= 2) + 1; pill_band = max(i for i, v in enumerate(r['pill']) if v >= 2) + 1
    ok('lens width follows the panel: 48 px bar about 12 px, 32 px pill about 8 px', 9 <= bar_band <= 13 and 5 <= pill_band <= 9, 'bar %d px, pill %d px' % (bar_band, pill_band))

    # ---- 2. no corner seam ----
    r = pg.evaluate(r"""()=>{ const res={}; for(const rad of [0,6,16]){ const g=T.make(256,256,Object.assign({blur:'light'},T.plain)); g.setBackdrop(T.ramp(256,256));
      g.addPanel({id:'a',rect:[28,28,200,200],radius:rad,kind:'window',tintAmount:0,shadow:0}); g.render(); const b=T.read(g);
      let worst=0, inward=true, n=0;
      for(let i=1;i<34;i++){ // pairs on the two sides of the corner diagonal, 1.4 px apart
        const p=T.px(b,28+i+1,28+i), q=T.px(b,28+i,28+i+1); if(p[3]<255||q[3]<255) continue; n++;
        const v1=[p[0]-(28+i+1),p[1]-(28+i)], v2=[q[0]-(28+i),q[1]-(28+i+1)], dv=Math.hypot(v1[0]-v2[0],v1[1]-v2[1]), len=Math.hypot(v1[0],v1[1]);
        worst=Math.max(worst, dv-0.15*len); if(v1[0]<-1||v1[1]<-1||v2[0]<-1||v2[1]<-1) inward=false; }
      res[rad]={worst,inward,n}; g.destroy(); } return res; }""")
    ok('no corner seam: bending direction is continuous across the corner diagonal (radius 0, 6, 16)', all(v['worst'] <= 2.5 and v['inward'] and v['n'] > 10 for v in r.values()), json.dumps(r))

    # ---- 3. frosted middle, colour, tint ----
    r = pg.evaluate(r"""()=>{ const S=T.stripes(512,256,0), out={};
      const energy=(b,x0,x1,y)=>{let e=0;for(let x=x0;x<x1;x++){const p=T.px(b,x,y),q=T.px(b,x+1,y);e+=Math.abs(p[0]-q[0])+Math.abs(p[1]-q[1])+Math.abs(p[2]-q[2])}return e/(x1-x0)};
      const sx=S.getContext('2d').getImageData(0,0,512,256); sx.w=512; out.src=energy(sx.data.w?sx.data:Object.assign(sx.data,{w:512}),150,350,128);
      for(const [bl,q] of [['light',3],['regular',3],['heavy',3],['light',2],['regular',2],['heavy',2]]){ const g=T.make(512,256,{blur:bl,quality:q}); g.setBackdrop(S);
        g.addPanel({id:'a',rect:[56,28,400,200],radius:16,kind:'window'}); g.render(); const b=T.read(g); out[bl+q]={e:energy(b,150,350,128),mid:T.px(b,256,128),lv:g.info.levels}; g.destroy(); }
      return out; }""")
    ok('middle is frosted: detail under glass drops to under 10 % of the picture (regular), 3 % (heavy), 25 % (light), at half and quarter size',
       all(r[k]['e'] < r['src'] * (.25 if k.startswith('light') else .1 if k.startswith('regular') else .03) for k in r if k != 'src'), ' '.join('%s %.1f' % (k, r[k]['e']) for k in r if k != 'src') + '  picture %.1f' % r['src'])
    ok('more blur = less detail (light > regular > heavy)', r['light3']['e'] > r['regular3']['e'] > r['heavy3']['e'] and r['light2']['e'] > r['regular2']['e'] >= r['heavy2']['e'])
    ok('pyramid plan: half size 2,4,8 for regular; quarter size 4,8 for regular', r['regular3']['lv'] == [2, 4, 8] and r['regular2']['lv'] == [4, 8] and r['light2']['lv'] == [4] and r['heavy3']['lv'] == [2, 4, 8, 16], json.dumps({k: r[k]['lv'] for k in r if k != 'src'}))

    r = pg.evaluate(r"""()=>{ const S2=T.stripes(1024,512,0), S1=T.flat(512,256,'#000'); S1.getContext('2d').drawImage(S2,0,0,512,256); const out={};
      const amp=(b,x0,x1,y)=>{let lo=255,hi=0;for(let x=x0;x<x1;x++){const v=T.px(b,x,y)[0];lo=Math.min(lo,v);hi=Math.max(hi,v)}return hi-lo};
      for(const q of [3,2]){ const a=T.make(512,256,{quality:q}); a.setBackdrop(S1); a.addPanel({id:'a',rect:[56,28,400,200],radius:16,kind:'window'}); a.render(); const A=T.read(a);
        const c=T.make(512,256,{quality:q}); c.resize(512,256,2); c.setBackdrop(S2); c.addPanel({id:'a',rect:[56,28,400,200],radius:16,kind:'window'}); c.render(); const C=T.read(c);
        out[q]={one:amp(A,150,350,128),two:amp(C,300,700,256),w:C.w,edge1:T.px(A,56,128)[3],edge2:T.px(C,112,256)[3],in2:T.px(C,116,256)[3],out2:T.px(C,110,256)[3]}; a.destroy(); c.destroy(); } return out; }""")
    ok('2x screen: the blur is as strong as on a 1x screen (pyramid sized in CSS pixels), panel edges at the right place', all(v['w'] == 1024 and abs(v['one'] - v['two']) <= max(4, .5 * v['one']) and v['in2'] == 255 and v['out2'] < 120 for v in r.values()), json.dumps(r))

    r = pg.evaluate(r"""()=>{ const g=T.make(256,256,{blur:'light',rim:{base:0,lit:0}}); g.setBackdrop(T.flat(256,256,'rgb(200,100,50)'));
      g.addPanel({id:'a',rect:[28,28,200,200],radius:0,kind:'window',shadow:0}); g.render(); const a=T.px(T.read(g),128,128);
      g.setFace({sat:1.3,mul:1.125,add:.125}); g.render(); const b=T.px(T.read(g),128,128); g.destroy(); return {a,b}; }""")
    # expected: saturation 1.3 around luma, then half tint (22,28,42)
    L = .2126 * 200 + .7152 * 100 + .0722 * 50; exp = [min(255, (L + (c - L) * 1.3)) * .5 + t * .5 for c, t in zip([200, 100, 50], [.086 * 255, .11 * 255, .165 * 255])]
    ok('face colour: saturation 1.3 then half panel tint', all(abs(a - e) <= 2 for a, e in zip(r['a'], exp)), '%s expected %s' % (r['a'][:3], [round(e) for e in exp]))
    ok("face matrix option (Apple's 0.125 / 1.125) brightens the face", r['b'][1] > r['a'][1] + 8, r['b'][:3])

    # ---- 4. glass never samples glass ----
    r = pg.evaluate(r"""()=>{ const S=T.stripes(512,256,0), g=T.make(512,256,{}); g.setBackdrop(S);
      g.addPanel({id:'top',rect:[150,60,200,120],radius:14,kind:'window',z:5}); g.render(); const alone=T.read(g);
      g.addPanel({id:'under',rect:[0,0,512,256],radius:0,kind:'docked',tint:[1,0,0],tintAmount:.9}); g.render(); const both=T.read(g);
      const d=Math.max(T.maxDiff(alone,both,165,60,335,180),T.maxDiff(alone,both,150,75,350,165)), outside=T.px(both,40,128); g.removePanel('top'); g.render(); const und=T.read(g);
      const r={d,outside,under:T.px(und,250,120),top:T.px(both,250,120),uploads:g.stats.uploads,pyr:g.stats.pyramids}; g.destroy(); return r; }""")
    ok('no glass on glass: a window over a red docked panel is pixel-identical to the window alone', r['d'] == 0, 'max difference %d; under panel there %s, window %s' % (r['d'], r['under'][:3], r['top'][:3]))
    ok('...while the docked panel itself is red there', r['under'][0] > 150 and r['top'][0] < 120)

    # ---- 5. dirty logic ----
    r = pg.evaluate(r"""()=>{ const S=T.stripes(512,256,0), g=T.make(512,256,{}); g.setBackdrop(S);
      g.addPanel({id:'d',rect:[0,200,512,56],kind:'docked'}); g.addPanel({id:'w',rect:[100,40,200,120],radius:14,kind:'window'});
      const o={}; g.render(); o.first={...g.stats};
      let drew=0; for(let i=0;i<50;i++){ g.updatePanel('w',{rect:[101+i,40,200,120]}); if(g.render()) drew++; } o.move={...g.stats}; o.moveDrew=drew;
      drew=0; for(let i=0;i<50;i++) if(g.render()) drew++; o.idle={...g.stats}; o.idleDrew=drew;
      drew=0; for(let i=0;i<50;i++){ g.updatePanel('w',{rect:[150,40,200,120]}); if(g.render()) drew++; } o.same={...g.stats}; o.sameDrew=drew;
      for(let i=0;i<20;i++){ g.markDirty(); g.render(); } o.dirty={...g.stats};
      g.setLensPreset('wide'); g.render(); o.lens={...g.stats}; g.setBlurPreset('heavy'); g.render(); o.blur={...g.stats};
      g.updatePanel('w',{visible:false}); g.updatePanel('d',{visible:false}); g.markDirty(); g.render(); o.hidden={...g.stats};
      g.destroy(); return o; }""")
    f, m, i_, s_, d, l, bl, hd = (r[k] for k in ['first', 'move', 'idle', 'same', 'dirty', 'lens', 'blur', 'hidden'])
    ok('first frame: one upload, one pyramid', f['uploads'] == 1 and f['pyramids'] == 1, f)
    ok('moving a panel 50 times: 50 quad redraws, 0 uploads, 0 pyramid rebuilds', r['moveDrew'] == 50 and m['uploads'] == 1 and m['pyramids'] == 1 and m['draws'] == f['draws'] + 50, m)
    ok('nothing changed: render() does nothing (50 calls, 0 draws)', r['idleDrew'] == 0 and i_['draws'] == m['draws'] and i_['skipped'] == m['skipped'] + 50)
    ok('updatePanel with the same rectangle: nothing drawn', r['sameDrew'] == 0 and s_['draws'] == i_['draws'])
    ok('markDirty 20 times: 20 uploads, 20 pyramids', d['uploads'] == 21 and d['pyramids'] == 21, d)
    ok('lens preset change: faces only, no pyramid; blur preset change: one pyramid, no upload', l['pyramids'] == 21 and l['draws'] == d['draws'] + 1 and bl['pyramids'] == 22 and bl['uploads'] == 21, [l, bl])
    ok('no visible glass: a dirty backdrop is not uploaded', hd['uploads'] == 21 and hd['pyramids'] == 22, hd)

    # backdrop refresh cap at 240 Hz for one second while a panel moves every frame
    r = pg.evaluate(r"""()=>{ const out={}; for(const q of [3,2,1]){ const g=T.make(256,256,{quality:q}); g.setBackdrop(T.stripes(256,256,0)); g.addPanel({id:'w',rect:[20,20,100,100],radius:10,kind:'window'});
      g.render(0); const s0={...g.stats}; let drew=0, pend=0; for(let i=1;i<=240;i++){ g.markDirty(); g.updatePanel('w',{rect:[20+i%50,20,100,100]}); if(g.render(i*1000/240)) drew++; if(g.pending) pend++; }
      out[q]={up:g.stats.uploads-s0.uploads,py:g.stats.pyramids-s0.pyramids,drew,pend,rate:g.info.rate}; g.destroy(); } return out; }""")
    ok('quality high: backdrop every frame (240 of 240)', r['3']['up'] == 240 and r['3']['drew'] == 240, r['3'])
    ok('quality medium: backdrop 60 per second, panels still move 240 per second', 58 <= r['2']['up'] <= 61 and r['2']['py'] == r['2']['up'] and r['2']['drew'] == 240, r['2'])
    ok('quality low: backdrop 30 per second, panels still move 240 per second', 29 <= r['1']['up'] <= 31 and r['1']['drew'] == 240 and r['1']['pend'] > 150, r['1'])

    # ---- 6. only the area under docked glass is blurred, with the same pixels ----
    r = pg.evaluate(r"""()=>{ const out={}; for(const q of [3,2]) for(const bl of ['light','regular','heavy']){ const S=T.stripes(800,600,0), mk=cull=>{ const g=T.make(800,600,{quality:q,blur:bl,regionCull:cull}); g.setBackdrop(S);
        g.addPanel({id:'h',rect:[0,20,108,400],kind:'docked'}); g.addPanel({id:'t',rect:[0,576,800,24],kind:'docked'}); g.addPanel({id:'dv',rect:[0,446,800,130],kind:'docked'}); g.addPanel({id:'b',rect:[0,432,800,14],kind:'docked'}); g.render(); return g; };
      const a=mk(true), A=T.read(a), b=mk(false), B=T.read(b); const o={d:T.maxDiff(A,B,0,0,800,600),regA:a.info.regions,regB:b.info.regions};
      // a moving panel appears: the whole picture must be blurred again, without a new upload
      a.addPanel({id:'w',rect:[300,60,300,200],radius:12,kind:'window'}); a.render(); b.addPanel({id:'w',rect:[300,60,300,200],radius:12,kind:'window'}); b.render();
      o.d2=T.maxDiff(T.read(a),T.read(b),0,0,800,600); o.up=a.stats.uploads; o.py=a.stats.pyramids; o.reg2=a.info.regions; a.destroy(); b.destroy(); out[bl+q]=o; } return out; }""")
    ok('blurring only under docked glass gives identical pixels to blurring everything (3 blur presets, half and quarter size)', all(v['d'] == 0 and v['regA'] >= 2 and v['regB'] == 0 for v in r.values()), json.dumps({k: [v['d'], v['regA']] for k, v in r.items()}))
    ok('a floating panel appears: full blur rebuilt from the kept picture (no new upload), identical pixels', all(v['d2'] == 0 and v['up'] == 1 and v['py'] == 2 and v['reg2'] == 0 for v in r.values()), json.dumps({k: [v['d2'], v['up'], v['py']] for k, v in r.items()}))

    # ---- 7. flat picture for glass over DOM, backdrop rectangle ----
    r = pg.evaluate(r"""()=>{ const g=T.make(512,256,{blur:'light',rim:{base:0,lit:0}}); g.setBackdrop(T.flat(512,256,'rgb(0,0,255)'));
      g.setFlat('panel',{rect:[0,128,512,128],color:[1,0,0,1]}); const disp=T.flat(64,64,'rgb(0,255,0)'); g.setFlat('disp',{rect:[300,150,120,90],source:disp});
      g.addPanel({id:'dock',rect:[0,128,512,128],kind:'docked',tintAmount:0}); g.addPanel({id:'menu',rect:[100,20,360,220],radius:12,kind:'menu',over:'flats',tintAmount:0,shadow:0,lens:false,z:2});
      g.render(); const b=T.read(g); const o={overBackdrop:T.px(b,200,60),overPanel:T.px(b,200,200),overDisp:T.px(b,360,195),dock:T.px(b,40,200),st:{...g.stats}};
      for(let i=0;i<10;i++){ g.updatePanel('menu',{rect:[100+i,20,360,220]}); g.render(); } o.move={...g.stats};
      g.markFlatDirty('disp'); g.render(); o.fd={...g.stats}; g.removeFlat('panel'); g.removeFlat('disp'); g.render(); o.noflat=T.px(T.read(g),200,200); g.destroy(); return o; }""")
    ok('flat picture: floating glass sees the backdrop, the flat panel colour and the fed display canvas', r['overBackdrop'][2] > 200 and r['overPanel'][0] > 200 and r['overPanel'][2] < 40 and r['overDisp'][1] > 200, [r['overBackdrop'][:3], r['overPanel'][:3], r['overDisp'][:3]])
    ok('flat picture: docked glass does not see it', r['dock'][2] > 200 and r['dock'][0] < 30, r['dock'][:3])
    ok('flat picture: moving the floating glass rebuilds nothing; a changed display rebuilds only the flat pyramid', r['move']['flatPyramids'] == r['st']['flatPyramids'] == 1 and r['move']['uploads'] == 1 and r['fd']['flatPyramids'] == 2 and r['fd']['uploads'] == 1 and r['fd']['pyramids'] == r['st']['pyramids'], [r['st'], r['fd']])
    rc = pg.evaluate(r"""()=>{ const g=T.make(256,256,{quality:1}); g.setBackdrop(T.stripes(256,256,0)); const d=T.flat(32,32,'#0f0'); g.setFlat('d',{rect:[0,0,256,256],source:d}); g.addPanel({id:'w',rect:[20,20,100,100],kind:'menu',over:'flats'});
      g.render(0); const s0={...g.stats}; let pend=0; for(let i=1;i<=240;i++){ g.markFlatDirty('d'); g.render(i*1000/240); if(g.pending) pend++; } const o={fu:g.stats.flatUploads-s0.flatUploads,fp:g.stats.flatPyramids-s0.flatPyramids,pend}; g.destroy(); return o; }""")
    ok('quality low: a fed display that repaints every frame is also refreshed only 30 times per second', 29 <= rc['fu'] <= 31 and rc['fp'] == rc['fu'] and rc['pend'] > 150, rc)
    ok('flat removed: the glass sees the backdrop again', r['noflat'][2] > 200, r['noflat'][:3])

    r = pg.evaluate(r"""()=>{ const g=T.make(512,256,{blur:'light',rim:{base:0,lit:0},backdropColor:[1,1,0]}); g.setBackdrop(T.flat(100,50,'rgb(0,0,255)'),{rect:[256,0,256,256]});
      g.addPanel({id:'a',rect:[20,20,472,216],kind:'window',tintAmount:0,shadow:0,lens:false}); g.render(); const b=T.read(g); g.destroy(); return {l:T.px(b,100,128),r:T.px(b,400,128)}; }""")
    ok('backdrop rectangle: the picture sits where it is told, the rest is the base colour', r['l'][0] > 200 and r['l'][1] > 200 and r['l'][2] < 40 and r['r'][2] > 200 and r['r'][0] < 40, [r['l'][:3], r['r'][:3]])

    # ---- 8. shadow, opacity, quality static ----
    r = pg.evaluate(r"""()=>{ const g=T.make(512,400,{}); g.setBackdrop(T.flat(512,400,'#888'));
      g.addPanel({id:'w',rect:[100,60,300,200],radius:16,kind:'window'}); g.render(); let b=T.read(g);
      const o={below:T.px(b,250,268),below2:T.px(b,250,285),above:T.px(b,250,52),side:T.px(b,92,160),far:T.px(b,250,330)};
      g.updatePanel('w',{kind:'docked'}); g.render(); b=T.read(g); o.dock=T.px(b,250,268);
      g.updatePanel('w',{kind:'pill',rect:[100,60,150,32]}); g.render(); b=T.read(g); o.pill=T.px(b,175,97);
      g.updatePanel('w',{kind:'window',rect:[100,60,300,200],opacity:.5}); g.render(); b=T.read(g); o.half=T.px(b,250,160);
      g.updatePanel('w',{opacity:1}); g.setQuality(0); g.render(); b=T.read(g); o.stat=T.px(b,250,160); o.stat2=T.px(b,251,160); o.statInfo=g.info.isStatic; const s1={...g.stats}; g.markDirty(); g.render(); o.statUp=g.stats.uploads-s1.uploads;
      g.setQuality('high'); g.render(); o.back=T.px(T.read(g),250,160); g.destroy(); return o; }""")
    ok("shadow (Apple's numbers): below a 200 px window about 0.6 x falloff, weaker above, none far away, none for docked, faint for a pill",
       r['below'][3] > 60 and r['below'][3] > r['above'][3] and r['below'][3] > r['below2'][3] > 0 and r['far'][3] == 0 and r['dock'][3] == 0 and 0 < r['pill'][3] < 12 and r['below'][:3] == [0, 0, 0],
       'alpha below %d, 25 px below %d, above %d, side %d, pill %d' % (r['below'][3], r['below2'][3], r['above'][3], r['side'][3], r['pill'][3]))
    ok('panel opacity 0.5 gives alpha 128', abs(r['half'][3] - 128) <= 1, r['half'])
    ok('quality static: plain tint with noise, no upload', r['statInfo'] and r['statUp'] == 0 and all(abs(a - b_) <= 4 for a, b_ in zip(r['stat'][:3], [22, 28, 42])) and r['stat'][3] == 255, [r['stat'], r['stat2']])
    ok('back to high: glass again', r['back'][0] > 60, r['back'])

    # ---- 9. Reduce Transparency and Increase Contrast ----
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
    r = pg.evaluate(r"""()=>{ g.setAccessibility({reduceTransparency:true}); g.render(); const a=g.info.isStatic; g.setAccessibility({reduceTransparency:null,increaseContrast:true}); g.render(); const b=g.info.increaseContrast; g.setAccessibility({increaseContrast:null}); g.render(); const c=g.info; g.destroy(); return {a,b,c:c.isStatic||c.increaseContrast}; }""")
    ok('the same two behaviours can be forced by the app (setAccessibility)', r['a'] and r['b'] and not r['c'])

    # ---- 10. context loss and restore ----
    pg.evaluate(r"""()=>{ window.fbLog=[]; window.asks=0; window.g=T.make(256,256,{onFallback:(on,why)=>fbLog.push([on,why]),requestRender:()=>asks++}); g.setBackdrop(T.stripes(256,256,0));
      g.setFlat('f',{rect:[0,128,256,128],source:T.flat(8,8,'#0f0')}); g.addPanel({id:'a',rect:[28,28,200,100],radius:16,kind:'window'}); g.addPanel({id:'b',rect:[28,150,200,80],radius:8,kind:'menu',over:'flats'}); g.render(); window.before=T.read(g); }""")
    pg.evaluate("()=>g.debug.lose()"); pg.wait_for_function("()=>g.mode==='fallback'", timeout=5000)
    r = pg.evaluate(r"""()=>{ const drew=g.render(), again=g.render(), sib=g.canvas.nextSibling, x=sib&&sib.getContext('2d'); const d=x?x.getImageData(128,78,1,1).data:[], out=x?x.getImageData(5,5,1,1).data:[];
      return {mode:g.mode,reason:g.reason,drew,again,sib:!!sib&&sib.tagName,hidden:g.canvas.style.visibility,mid:[...d],out:[...out],log:fbLog,asks,w:sib&&sib.width,cw:sib&&sib.style.width}; }""")
    ok('context lost: engine switches to the fallback and tells the app', r['mode'] == 'fallback' and r['reason'] == 'lost' and r['log'] == [[True, 'lost']] and r['asks'] >= 1, r['log'])
    ok('fallback: plain tint with noise on a 2D canvas in the same place, drawn once', r['sib'] == 'CANVAS' and r['hidden'] == 'hidden' and r['drew'] and not r['again'] and all(abs(a - b_) <= 12 for a, b_ in zip(r['mid'][:3], [22, 28, 42])) and r['mid'][3] == 255 and r['out'][3] == 0 and r['w'] == 256, r['mid'])
    r = pg.evaluate(r"""()=>{ g.updatePanel('a',{rect:[40,28,200,100]}); const d=g.render(); g.updatePanel('a',{rect:[28,28,200,100]}); g.markDirty(); g.render(); return d; }""")
    ok('fallback: panels still move while the context is lost', r)
    pg.evaluate("()=>g.debug.restore()"); pg.wait_for_function("()=>g.mode==='gl'", timeout=5000)
    r = pg.evaluate(r"""()=>{ const drew=g.render(), after=T.read(g); return {drew,d:T.maxDiff(before,after,0,0,256,256),sib:g.canvas.nextSibling&&g.canvas.nextSibling.tagName,vis:g.canvas.style.visibility,log:fbLog,st:g.stats,asks}; }""")
    ok('context restored: glass is back, pixel-identical to before the loss, fallback canvas removed', r['drew'] and r['d'] == 0 and r['sib'] != 'CANVAS' and r['vis'] != 'hidden' and r['log'][-1] == [False, ''] and r['st']['lost'] == 1 and r['st']['restored'] == 1, 'max difference %d, %s' % (r['d'], r['st']))
    r = pg.evaluate(r"""async()=>{ for(let i=0;i<3;i++){ g.debug.lose(); await new Promise(r=>setTimeout(r,60)); g.render(); g.debug.restore(); await new Promise(r=>setTimeout(r,60)); g.render(); }
      const d=T.maxDiff(before,T.read(g),0,0,256,256), n=document.querySelectorAll('canvas').length; g.destroy(); return {d,n,mode:g.mode}; }""")
    ok('three more losses in a row: recovers every time, no canvases left behind', r['d'] == 0 and r['mode'] == 'gl', r)

    # ---- 11. resize, panel bookkeeping, destroy ----
    r = pg.evaluate(r"""()=>{ const g=T.make(256,256,{}); g.setBackdrop(T.stripes(512,512,0)); g.addPanel({id:'a',rect:{x:10,y:10,w:100,h:100},radius:999,kind:'window'}); g.addPanel({id:'a',rect:{left:20,top:20,width:100,height:100}}); g.render();
      const o={n:g.info.panels,has:g.hasPanel('a'),upd:g.updatePanel('zz',{}),rm:g.removePanel('zz')}; g.canvas.style.width='400px'; g.canvas.style.height='300px'; o.rs=g.resize(400,300,2); o.drew=g.render(); o.info=g.info; o.cw=g.canvas.width; o.up=g.stats.uploads; o.py=g.stats.pyramids;
      o.px=T.px(T.read(g),140,140); g.removePanel('a'); g.render(); o.empty=T.px(T.read(g),140,140); g.destroy(); o.after=g.render(); return o; }""")
    ok('resize: canvas 800x600 at 2x, pyramid rebuilt from the kept picture, panel drawn at the right place', r['rs'] and r['drew'] and r['cw'] == 800 and r['info']['dpr'] == 2 and r['up'] == 1 and r['py'] == 2 and r['px'][3] == 255, r['px'])
    ok('addPanel twice with one id updates it; unknown ids are refused; removed panel is gone; destroy stops render', r['n'] == 1 and r['has'] and not r['upd'] and not r['rm'] and r['empty'] == [0, 0, 0, 0] and r['after'] is False)
    ctx.close()

    # ---- 12. WebGL2 missing ----
    ctx, pg = unit_page(b, init="const og=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(t,a){return /webgl/.test(t)?null:og.call(this,t,a)};")
    r = pg.evaluate(r"""()=>{ const log=[], g=T.make(256,256,{onFallback:(on,why)=>log.push([on,why])}); g.setBackdrop(T.stripes(256,256,0)); g.addPanel({id:'a',rect:[28,28,200,100],radius:16,kind:'window'});
      const drew=g.render(), again=g.render(); g.markDirty(); const d3=g.render(); const x=g.canvas.getContext('2d'), mid=[...x.getImageData(128,78,1,1).data], out=[...x.getImageData(5,5,1,1).data], corner=[...x.getImageData(29,29,1,1).data];
      g.updatePanel('a',{rect:[28,100,200,100]}); const d4=g.render(), moved=[...x.getImageData(128,60,1,1).data]; g.setQuality(1); g.setLensPreset('wide'); g.setBlurPreset('heavy'); g.setFlat('f',{rect:[0,0,9,9],color:[1,1,1,1]}); g.resize(300,200,1); const d5=g.render();
      const o={mode:g.mode,reason:g.reason,log,drew,again,d3,d4,d5,mid,out,corner,moved,sibs:document.querySelectorAll('canvas').length,w:g.canvas.width,pend:g.pending}; g.destroy(); return o; }""")
    ok('WebGL2 missing: fallback on the same canvas, app told why', r['mode'] == 'fallback' and r['reason'] == 'no webgl2' and r['log'] == [[True, 'no webgl2']] and r['sibs'] == 1, r['log'])
    ok('WebGL2 missing: plain tint with noise, rounded corners, redrawn only when a panel changes, every API call harmless', r['drew'] and not r['again'] and not r['d3'] and r['d4'] and r['d5'] and r['w'] == 300 and not r['pend'] and all(abs(a - b_) <= 12 for a, b_ in zip(r['mid'][:3], [22, 28, 42])) and r['out'][3] == 0 and r['corner'][3] < 60 and r['moved'][3] == 0, [r['mid'], r['corner']])
    ctx.close()

    # ---- 13. software drawing is refused unless allowed ----
    ctx, pg = unit_page(b)
    r = pg.evaluate(r"""()=>{ const c=document.createElement('canvas'); document.body.appendChild(c); c.style.cssText='width:100px;height:100px'; const g=AudioLabGlass.create(c,{}); const o={mode:g.mode,reason:g.reason}; g.destroy(); return o; }""")
    print('NOTE without allowSoftware on this machine (software GL): mode %s %s' % (r['mode'], r['reason']), flush=True)
    ok('software GL is refused by default (falls back to the plain tint) or accepted where the browser does not report it', r['mode'] in ('fallback', 'gl'), r)
    ctx.close()

def page_tests(b, dsf):
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=dsf)
    pg = ctx.new_page(); watch(pg)
    pg.goto('file://' + HERE + '/engine-test.html?soft=1'); pg.wait_for_function("()=>window.__t&&__t.gA.stats.draws>0", timeout=30000)
    tag = ' (%dx)' % dsf
    info = pg.evaluate("()=>({a:__t.gA.info,b:__t.gB.info})")
    ok('test page loads, both layers draw glass' + tag, info['a']['mode'] == 'gl' and info['b']['mode'] == 'gl' and info['a']['panels'] == 4 and info['b']['panels'] == 3 and info['a']['width'] == 1600 * dsf, info['a'])
    ok('test page: docked layer blurs only the area under glass, floating layer everything' + tag, info['a']['regions'] >= 1 and info['b']['regions'] == 0, 'docked layer: %d rectangles' % info['a']['regions'])
    count = r"""async(ms)=>{ const s=g=>({...g.stats}), a0=s(__t.gA), b0=s(__t.gB); await new Promise(r=>{let n=0;const f=()=>{if(++n>=ms)r();else requestAnimationFrame(f)};requestAnimationFrame(f)}); const a1=s(__t.gA), b1=s(__t.gB), d=(x,y)=>Object.fromEntries(Object.keys(x).map(k=>[k,y[k]-x[k]])); return {a:d(a0,a1),b:d(b0,b1)}; }"""
    setsel = "([id,v])=>{const e=document.querySelector(id);if(e.type==='checkbox')e.checked=v;else e.value=v;e.dispatchEvent(new Event('change',{bubbles:true}))}"
    N = 30
    r = pg.evaluate(count, N)
    ok('scrolling + mixer moving: every frame uploads and rebuilds (worst case)' + tag, r['a']['uploads'] >= N - 2 and r['a']['pyramids'] >= N - 2 and r['b']['flatPyramids'] >= N - 2 and r['b']['pyramids'] == 0, r)
    pg.evaluate(setsel, ['#scn', 'still']); pg.wait_for_timeout(400)
    r = pg.evaluate(count, N)
    ok('still picture + mixer moving: 0 uploads, 0 pyramid rebuilds; docked layer not redrawn at all; floating layer redraws its quads' + tag,
       r['a']['uploads'] == 0 and r['a']['pyramids'] == 0 and r['a']['draws'] == 0 and r['b']['uploads'] == 0 and r['b']['pyramids'] == 0 and r['b']['flatPyramids'] == 0 and r['b']['flatUploads'] == 0 and r['b']['draws'] >= N * .5, r)
    pg.evaluate(setsel, ['#scn', 'play']); pg.wait_for_timeout(400)
    r = pg.evaluate(count, N)
    ok('playhead on its own layer + mixer moving: 0 uploads, 0 pyramid rebuilds' + tag, r['a']['uploads'] == 0 and r['a']['pyramids'] == 0 and r['b']['uploads'] == 0 and r['b']['flatPyramids'] == 0, r)
    pg.evaluate(setsel, ['#drag', False]); pg.wait_for_timeout(300)
    r = pg.evaluate(count, N)
    ok('nothing moves: no GL work at all (0 draws on both layers)' + tag, r['a']['draws'] == 0 and r['b']['draws'] == 0 and r['a']['skipped'] >= N - 1, r)

    # screenshots: what the user sees (compositor output)
    pg.evaluate(setsel, ['#scn', 'still']); pg.evaluate("()=>{document.querySelector('#hud').hidden=true;__t.P.mix.dx=0;__t.layout()}"); pg.wait_for_timeout(500)
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
    eg, eb = energy(glass, (30, 120, 190, 560)), energy(bare, (30, 120, 190, 560))
    ok('screenshot: track headers are frosted (sharpest edge under 15 % of the bare arrangement)' + tag, eg < eb * .15, 'glass %d, bare %d' % (eg, eb))
    em, ebm = energy(glass, (300, 120, 1300, 460)), energy(bare, (300, 120, 1300, 460))
    ok('screenshot: mixer window is frosted' + tag, em < ebm * .15, 'glass %d, bare %d' % (em, ebm))
    eo, ebo = energy(glass, (1525, 120, 1595, 560)), energy(bare, (1525, 120, 1595, 560))
    ok('screenshot: the arrangement outside glass is untouched' + tag, eo == ebo and eo > 100, 'glass %d, bare %d' % (eo, ebo))
    # the menu over the device panel: sees the flat panel colour and the display (dark box), not the arrangement
    P = pg.evaluate("()=>Object.fromEntries(Object.entries(__t.P).map(([k,p])=>[k,[p.x+p.dx,p.y,p.w,p.h]]))")
    mx, my, mw, mh = P['menu']; dv = P['dev']
    c1 = glass.getpixel((int((mx + 60) * dsf), int((dv[1] + 12) * dsf)))   # menu over the plain device panel
    exp = [(.13 * .4 + .086 * .6) * 255, (.15 * .4 + .11 * .6) * 255, (.2 * .4 + .165 * .6) * 255]
    ok('screenshot: menu over the device panel shows the flat panel colour, not the arrangement' + tag, all(abs(a - e) <= 14 for a, e in zip(c1, exp)), '%s expected about %s' % (c1, [round(e) for e in exp]))
    # lens on / off screenshots: rim differs, middle identical
    settle = lambda: pg.evaluate('()=>new Promise(r=>{let n=0;const f=()=>{if(++n>4)r();else requestAnimationFrame(f)};requestAnimationFrame(f)})')
    pg.evaluate(setsel, ['#lens', 'off']); settle(); off = shot(); pg.evaluate(setsel, ['#lens', 'apple']); settle()
    def diff(a, b_, box):
        A, B = a.crop(tuple(int(v * dsf) for v in box)), b_.crop(tuple(int(v * dsf) for v in box)); pa, pb = A.load(), B.load(); w, h = A.size; m = 0; s = 0
        for y in range(h):
            for x in range(w):
                d = max(abs(pa[x, y][k] - pb[x, y][k]) for k in range(3)); m = max(m, d); s += d
        return m, s / (w * h)
    x0, y0, w0, h0 = P['mix']
    rim = max(diff(glass, off, (x0 + 2, y0 + 60, x0 + 18, y0 + h0 - 60)), diff(glass, off, (x0 + 60, y0 + 2, x0 + w0 - 60, y0 + 18))); mid = diff(glass, off, (x0 + 40, y0 + 40, x0 + w0 - 40, y0 + h0 - 40))
    ok('screenshot: lens on and off differ in the rim of the mixer window and are identical in its middle' + tag, rim[0] >= 6 and mid[0] <= 1, 'rim max %d mean %.1f, middle max %d' % (rim[0], rim[1], mid[0]))
    glass.save(os.path.join(OUT, 'engine-test-%dx.png' % dsf))

    # presets, quality, accessibility, context loss through the page's own controls
    for sel, v in [('#blur', 'heavy'), ('#blur', 'light'), ('#lens', 'wide'), ('#lens', 'fine'), ('#qual', '2'), ('#qual', '1'), ('#face', 'apple'), ('#scn', 'scroll'), ('#drag', True)]:
        pg.evaluate(setsel, [sel, v]); pg.wait_for_timeout(250)
    r = pg.evaluate("()=>({a:__t.gA.info,b:__t.gB.info})")
    ok('page controls reach both layers (lens fine, blur light, quality low)' + tag, all(r[k]['lens'] == 'fine' and r[k]['blur'] == 'light' and r[k]['quality'] == 1 and r[k]['rate'] == 30 for k in 'ab'))
    pg.evaluate(setsel, ['#qual', '0']); pg.wait_for_timeout(300); r = pg.evaluate(count, 10)
    ok('quality static on the page: no uploads while scrolling' + tag, r['a']['uploads'] == 0 and r['b']['uploads'] == 0, r)
    pg.evaluate(setsel, ['#qual', '3']); pg.evaluate(setsel, ['#rt', True]); pg.wait_for_timeout(300); r = pg.evaluate(count, 10)
    ok('Reduce transparency on the page: no uploads while scrolling' + tag, r['a']['uploads'] == 0 and r['b']['uploads'] == 0)
    pg.evaluate(setsel, ['#rt', False]); pg.evaluate(setsel, ['#ic', True]); pg.wait_for_timeout(300); pg.evaluate(setsel, ['#ic', False])
    pg.evaluate("()=>document.querySelector('#lose').click()"); pg.wait_for_function("()=>__t.gA.mode==='fallback'&&__t.gB.mode==='fallback'", timeout=5000); pg.wait_for_timeout(400)
    fb = shot(); c = fb.getpixel((int(100 * dsf), int(300 * dsf)))
    ok('page: lose the context -> both layers show the plain tint (track headers are the solid colour)' + tag, all(abs(a - e) <= 14 for a, e in zip(c, [22, 28, 42])), c)
    pg.evaluate("()=>document.querySelector('#rest').click()"); pg.wait_for_function("()=>__t.gA.mode==='gl'&&__t.gB.mode==='gl'", timeout=5000); pg.wait_for_timeout(500)
    r = pg.evaluate(count, 10)
    ok('page: restore -> glass again, uploads resume, no stray canvases' + tag, r['a']['uploads'] >= 8 and pg.evaluate("()=>document.querySelectorAll('#stage canvas').length") == 4, r['a'])
    c = shot().getpixel((int(100 * dsf), int(300 * dsf)))
    if dsf == 1:
        cost = pg.evaluate("()=>__t.costSync(4)")
        print('NOTE cost of the whole glass per frame, both layers, software renderer (no GPU here, only the comparison means anything): ' + json.dumps(cost), flush=True)
        ok('costSync runs for every preset', len(cost) == 9 and all(v > 0 for v in cost.values()))
        pg.evaluate("()=>{document.querySelector('#hud').hidden=false}")
        s = pg.evaluate("async()=>{const s=await __t.measure(1200);return {s,t:document.querySelector('#res').textContent,live:document.querySelector('#live').textContent}}")
        bk = pg.evaluate("async()=>{await __t.breakdown();return {t:document.querySelector('#res').textContent,a:__t.gA.info,on:Object.values(__t.P).every(p=>p.on)}}")
        print(bk['t'], flush=True)
        ok('Find the cost runs, fills both tables and puts every setting back', 'all glass, low' in bk['t'] and 'floating layer: blur' in bk['t'] and bk['a']['quality'] == 3 and bk['on'], '')
        ok('Measure fills the table and the live readout shows frame time', 'median' in s['t'] and 'fps' in s['live'] and 'blur rebuilds' in s['live'], s['live'].split('\n')[0])
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
        for dsf in (1, 2): page_tests(b, dsf)
        b.close()
    ok('no console errors or warnings in any test', not LOGS, LOGS[:5])
    bad = [r for r in RES if not r[1]]
    print('\n%d checks, %d failed' % (len(RES), len(bad)))
    sys.exit(1 if bad else 0)
