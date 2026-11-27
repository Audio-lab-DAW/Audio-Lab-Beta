#!/usr/bin/env python3
"""Glass step 1 (task GS1, v0.223): the glass engine draws the docked panels.
   (The test page has no service worker file, so the one console line about fetching that script is left out.)
   python3 tools/ui-tests/glass_gs1.py [index.html] [out dir]
The cloud machine has no graphics card (software renderer): only correctness is checked here, frame rates mean nothing."""
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
# helpers that run in the page: read the engine's own canvas (right after a draw, in the same task) and small picture measures
HELP = r"""
window.GT={
 R:c=>AudioLab.run(c),
 read(){const g=GT.R('GLE.g');g.render(performance.now());g.debug.draw();const gl=g.gl,w=gl.drawingBufferWidth,h=gl.drawingBufferHeight,b=new Uint8Array(w*h*4),o=new Uint8Array(w*h*4);gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,b);
   for(let j=0;j<h;j++)o.set(b.subarray((h-1-j)*w*4,(h-j)*w*4),j*w*4);o.w=w;o.h=h;return o},
 px(b,x,y){const k=((y|0)*b.w+(x|0))*4;return[b[k],b[k+1],b[k+2],b[k+3]]},
 rect(id){const m=document.getElementById('glassCv').getBoundingClientRect(),r=document.getElementById(id).getBoundingClientRect();return{x:Math.round(r.left-m.left),y:Math.round(r.top-m.top),w:Math.round(r.width),h:Math.round(r.height)}},
 maxDiff(a,b,x0,y0,x1,y1){let m=0;for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){const k=(y*a.w+x)*4;for(let c=0;c<3;c++)m=Math.max(m,Math.abs(a[k+c]-b[k+c]))}return m},
 /* fine detail: mean difference between pixels 1 apart along a row; coarse: spread of the colours over the row */
 rowStats(get,x0,x1,y){let d=0,n=0,mn=[255,255,255],mx=[0,0,0],p=null;for(let x=x0;x<x1;x++){const q=get(x,y);for(let c=0;c<3;c++){mn[c]=Math.min(mn[c],q[c]);mx[c]=Math.max(mx[c],q[c])}if(p){d+=Math.abs(q[0]-p[0])+Math.abs(q[1]-p[1])+Math.abs(q[2]-p[2]);n++}p=q}return{fine:d/n/3,spread:Math.max(mx[0]-mn[0],mx[1]-mn[1],mx[2]-mn[2])}},
 st(){return JSON.parse(GT.R("JSON.stringify({v:VERSION,on:GLE.on,lv:GLE.lv,fail:GLE.fail,info:GLE.g&&GLE.g.info,stats:GLE.g&&Object.assign({},GLE.g.stats),n:Object.assign({},GLE.n),phl:Object.assign({},PHL.n),frn:FRN,gl:UI.gl||null,pm:UI.pm,body:document.body.className})"))},
 bf(){return ['hglass','tr','fxglass','fxband'].map(i=>{const e=document.getElementById(i);return e?[getComputedStyle(e).backdropFilter,e.style.backdropFilter||'']:['none','']})},
 wait:ms=>new Promise(r=>setTimeout(r,ms))
};"""

def boot(p, init=None, w=1600, h=1000, dsf=1):
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dsf); pg = ctx.new_page(); logs = []
    def con(m):
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall due to ReadPixels' not in m.text and 'willReadFrequently' not in m.text): logs.append(m.type + ': ' + m.text[:200])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT)
    if init: pg.add_init_script(init)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(5000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}"); pg.evaluate(HELP)
    return b, pg, logs

with sync_playwright() as p:
    b, pg, logs = boot(p)
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    st = lambda: pg.evaluate("()=>GT.st()")
    R("pmSetOn(false)"); pg.wait_for_timeout(1500)   # Light mode off = Full effects (this weak machine starts on Lighter by itself)
    s = st()
    # ---- 1. the engine is in, with the defaults ----
    ok(tuple(map(int, s['v'].split('.'))) >= (0, 223), 'version 0.223 or later', s['v'])
    ok(s['on'] and s['lv'] == 'glass' and s['info']['mode'] == 'gl', 'Full effects: the engine runs at the level Glass', [s['on'], s['lv'], s['info'] and s['info']['mode']])
    ok(s['info']['lens'] == 'wide' and s['info']['blur'] == 'light' and s['gl'] is None, 'defaults: lens Wide, blur Light, nothing saved', [s['info']['lens'], s['info']['blur'], s['gl']])
    ok(s['info']['source'] == 'scene' and s['info']['sceneRects'] > 100, 'the backdrop is the rectangle scene drawn on the graphics card', [s['info']['source'], s['info']['sceneRects']])
    dom = pg.evaluate("()=>({kids:[...document.getElementById('main').children].map(e=>e.tagName+'#'+e.id),gl:[...document.querySelectorAll('canvas')].filter(c=>{try{return c.id==='glassCv'}catch(e){return false}}).length,back:(()=>{const c=document.getElementById('arrBack');return c?[c.width,c.height]:null})(),blur:(()=>{const c=document.getElementById('arrBlur');return c?[c.width,c.height,getComputedStyle(c).display]:null})(),pe:getComputedStyle(document.getElementById('glassCv')).pointerEvents})")
    k = dom['kids']
    ok(k[0] == 'CANVAS#glassCv' and k.index('CANVAS#glassCv') < k.index('CANVAS#arr') and dom['gl'] == 1 and dom['pe'] == 'none', 'one engine canvas in #main, before #arr, not clickable', k)
    ok(dom['back'] in (None, [2, 2]) and (dom['blur'] is None or dom['blur'][0] == 0), '#arrBack is an empty 2 x 2 layer, #arrBlur is not made', [dom['back'], dom['blur']])
    ok('fxpic' not in s['body'] and 'gle' in s['body'].split(), 'body: engine class on, no picture class', s['body'])
    ok(s['info']['panels'] >= 3 and s['info']['regions'] >= 1, 'faces for track headers, transport and device panel; backdrop worked out only under them', [s['info']['panels'], s['info']['regions']])
    # ---- 2. no backdrop-filter on a docked surface, the SVG lens does not run for them ----
    bf = pg.evaluate("()=>GT.bf()")
    ok(all(x[0] == 'none' and x[1] == '' for x in bf), 'Glass: no docked surface has a backdrop-filter (computed and inline)', bf)
    # v0.228 (task GS3, glass step 3): the old lens code is deleted; before that it was in the file but made nothing (v0.227) or nothing for the docked panels (v0.223)
    if R("typeof RFX==='undefined'"):
        ok(R("typeof rfBuild==='undefined'&&typeof rfMap==='undefined'&&typeof rfStyle==='undefined'") and "mk('feImage'" not in SRC and not R("!!document.querySelector('svg filter[id^=rf]')"), 'the old lens code is gone (glass step 3): no rfBuild, rfMap, rfStyle, no feImage map, no SVG filter in the page')
    else:
        rf = json.loads(R("JSON.stringify([...RFX.entries()].filter(([el])=>el.id==='hglass'||el.id==='tr'||el.id==='fxband').map(([el,o])=>[el.id,o.v,(o.img.getAttribute('href')||'').length,o.built]))"))
        ok(all(x[1] == '' and x[2] == 0 and x[3] == '' for x in rf), 'the old lens (rfBuild, rfMap, rfStyle) made no map and no filter for the docked panels', rf)
        ok(R("typeof rfAttach==='function'&&typeof rfBuild==='function'&&typeof rfMap==='function'&&typeof rfStyle==='function'") and 'feImage' in SRC, 'the old lens code is still there (step 3 removes it; since v0.227 it is in the file but makes no SVG filter)')
    # ---- 3. pixel checks on the engine canvas ----
    r = pg.evaluate(r"""()=>{const b=GT.read(),tr=GT.rect('tr'),fx=GT.rect('fxglass'),hg=GT.rect('hglass'),o={tr,fx,hg,w:b.w,h:b.h};
      o.aTr=GT.px(b,tr.x+tr.w/2,tr.y+tr.h/2)[3];o.aFx=GT.px(b,fx.x+fx.w/2,fx.y+fx.h/2)[3];o.aHg=GT.px(b,hg.x+hg.w/2,hg.y+hg.h/2)[3];o.aOpen=GT.px(b,900,200)[3];o.aOpen2=GT.px(b,400,400)[3];
      /* frosted middle: the same row in the arrangement picture and on the glass */
      const a=document.getElementById('arr'),c=document.createElement('canvas');c.width=a.width;c.height=a.height;const x=c.getContext('2d',{willReadFrequently:true});x.drawImage(a,0,0);const y=fx.y+Math.round(fx.h/2),im=x.getImageData(0,y,a.width,1).data;
      o.arrRow=GT.rowStats((xx)=>[im[xx*4],im[xx*4+1],im[xx*4+2]],300,1500,y);o.glassRow=GT.rowStats((xx,yy)=>GT.px(b,xx,yy),300,1500,y);
      return o}""")
    ok(r['aTr'] == 255 and r['aFx'] == 255 and r['aHg'] == 255, 'the faces of transport, device panel and track headers are drawn (opaque)', [r['aTr'], r['aFx'], r['aHg']])
    ok(r['aOpen'] == 0 and r['aOpen2'] == 0, 'the canvas is empty where there is no docked glass', [r['aOpen'], r['aOpen2']])
    ok(r['glassRow']['fine'] < r['arrRow']['fine'] * 0.5 and r['glassRow']['spread'] > 25, 'middle frosted: fine detail gone, the track colours still show', [r['arrRow'], r['glassRow']])
    lens = pg.evaluate(r"""()=>{const g=GT.R('GLE.g'),o={};const fx=GT.rect('fxglass'),tr=GT.rect('tr'),hg=GT.rect('hglass');
      g.setLensPreset('off');const off=GT.read();g.setLensPreset('wide');const on=GT.read();
      const band=(r,d0,d1)=>Math.max(GT.maxDiff(on,off,r.x+40,r.y+d0,r.x+r.w-40,r.y+d1),0);
      o.fxRim=Math.max(GT.maxDiff(on,off,fx.x+2,fx.y+1,fx.x+fx.w-2,fx.y+44),GT.maxDiff(on,off,fx.x+2,fx.y+fx.h-44,fx.x+fx.w-2,fx.y+fx.h-1));o.fxMid=GT.maxDiff(on,off,fx.x+60,fx.y+60,fx.x+fx.w-60,fx.y+fx.h-60);
      o.trRim=GT.maxDiff(on,off,tr.x+100,tr.y+1,tr.x+tr.w-100,tr.y+12);o.trMid=GT.maxDiff(on,off,tr.x+100,tr.y+19,tr.x+tr.w-100,tr.y+22);
      o.fxTop=GT.maxDiff(on,off,fx.x+2,fx.y+1,fx.x+fx.w-2,fx.y+44);o.fxBot=GT.maxDiff(on,off,fx.x+2,fx.y+fx.h-44,fx.x+fx.w-2,fx.y+fx.h-1);o.fxLeft=GT.maxDiff(on,off,fx.x+1,fx.y+50,fx.x+44,fx.y+fx.h-50);
      o.hgBot=GT.maxDiff(on,off,hg.x+2,hg.y+hg.h-40,hg.x+hg.w-60,hg.y+hg.h-1);o.edges=JSON.parse(GT.R("JSON.stringify(['hglass','tr','fxglass'].map(i=>GLE.g.panelInfo(i).edges))"));
      o.hgRim=GT.maxDiff(on,off,hg.x+hg.w-40,hg.y+60,hg.x+hg.w-1,hg.y+hg.h-60);o.hgMid=GT.maxDiff(on,off,hg.x+75,hg.y+75,hg.x+hg.w-75,hg.y+hg.h-75);
      /* corner: no jump across the diagonal (the bending direction must not flip there) */
      let jump=0,grad=0,n=0;for(let i=3;i<44;i++){const a=GT.px(on,fx.x+i+1,fx.y+i),c=GT.px(on,fx.x+i,fx.y+i+1),e=GT.px(on,fx.x+i+2,fx.y+i);for(let k=0;k<3;k++){jump=Math.max(jump,Math.abs(a[k]-c[k]));grad+=Math.abs(a[k]-e[k]);n++}}
      o.cornerJump=jump;o.cornerGrad=grad/n;return o}""")
    ok(lens['fxMid'] == 0, 'device panel: the middle is the same picture with and without the lens', [lens['fxRim'], lens['fxMid']])
    ok(lens['edges'] == ['r', '', 't'] and lens['fxBot'] == 0 and lens['fxLeft'] == 0 and lens['trRim'] == 0 and lens['hgBot'] == 0, 'the lens only on free edges (engine 2.2): headers towards the arrangement, device panel on its top edge, nothing on the window border, nothing where two panels meet', [lens['edges'], lens['fxTop'], lens['fxBot'], lens['fxLeft'], lens['trRim'], lens['hgBot']])
    R("devHide(true)"); pg.wait_for_timeout(1500)
    t2 = pg.evaluate(r"""()=>{const g=GT.R('GLE.g'),tr=GT.rect('tr');g.setLensPreset('off');const off=GT.read();g.setLensPreset('wide');const on=GT.read();return {rim:GT.maxDiff(on,off,tr.x+230,tr.y+1,tr.x+tr.w-20,tr.y+12),mid:GT.maxDiff(on,off,tr.x+230,tr.y+19,tr.x+tr.w-20,tr.y+22),e:GT.R("GLE.g.panelInfo('tr').edges"),a:GT.px(on,tr.x+800,tr.y+20)[3]}}""")
    ok(t2['rim'] >= 4 and t2['mid'] <= 2 and t2['a'] == 255, 'transport: rim refraction on its top edge while the devices are folded (band about 13 px on a 40 px bar), flat middle', t2)
    R("devHide(false)"); pg.wait_for_timeout(1500)
    ok(lens['hgRim'] >= 2 and lens['hgMid'] == 0, 'track headers: rim refraction on the edge towards the arrangement, flat middle', [lens['hgRim'], lens['hgMid']])
    ok(lens['cornerJump'] <= 14, 'no corner seam: no jump across the corner diagonal of the device panel', [lens['cornerJump'], round(lens['cornerGrad'], 2)])
    # the corner again with a picture whose colour is its place (red = x, green = y around the corner), fed by the small-copy route for this check only:
    # the place each glass pixel is taken from must not jump across the corner diagonal, and the rim must take its picture from further inside
    cr = pg.evaluate(r"""()=>{const g=GT.R('GLE.g'),fx=GT.rect('fxglass'),m=document.getElementById('glassCv'),W=m.clientWidth,H=m.clientHeight,c=document.createElement('canvas');c.width=W;c.height=H;const x=c.getContext('2d'),d=x.createImageData(W,H);
      for(let j=0;j<H;j++)for(let i=0;i<W;i++){const k=(j*W+i)*4;d.data[k]=Math.max(0,Math.min(255,i-fx.x+60));d.data[k+1]=Math.max(0,Math.min(255,j-fx.y+60));d.data[k+3]=255}x.putImageData(d,0,0);
      g.setBackdrop(c);g.markDirty();g.render(performance.now()+1000);g.setLensPreset('off');const b0=GT.read();g.setLensPreset('wide');const b=GT.read();let jump=0,bend=0;
      const top=GT.maxDiff(b,b0,fx.x+60,fx.y+1,fx.x+250,fx.y+40),left=GT.maxDiff(b,b0,fx.x+1,fx.y+60,fx.x+44,fx.y+190);
      for(let i=4;i<44;i++){const a=GT.px(b,fx.x+i+1,fx.y+i),e=GT.px(b,fx.x+i,fx.y+i+1);jump=Math.max(jump,Math.abs(a[0]-e[0]),Math.abs(a[1]-e[1]))}
      const up=g.stats.uploads,upx=g.stats.uploadPixels,rim=GT.px(b,fx.x+300,fx.y+3)[1]-63,mid=GT.px(b,fx.x+300,fx.y+120)[1]-180;
      g.setBackdrop(null);g.render(performance.now()+2000);const back=g.info.source;return {jump,rim,mid,top,left,up,upx,full:W*H,back}}""")
    ok(cr['jump'] <= 4 and cr['rim'] >= 8 and abs(cr['mid']) <= 3 and cr['top'] >= 8 and cr['left'] == 0, 'no corner seam and no arc with a place-coloured picture: no jump across the corner diagonal, the top rim is bent inward, the middle is not', cr)
    ok(cr['upx'] * 12 <= cr['full'] and cr['back'] == 'scene', 'the small-copy route (used by the overview) uploads a quarter-size copy, never the full canvas; then back to the scene', [cr['upx'], cr['full'], cr['back']])
    R("(()=>{GLE.g.stats.uploads=0;GLE.g.stats.uploadPixels=0})()")
    pg.screenshot(path=os.path.join(OUT, 'gs1_glass.png'))
    # ---- 4. counters: nothing uploaded, nothing sent again while scrolling and playing ----
    pg.wait_for_timeout(600); a = st()
    pg.mouse.move(900, 300)
    for i in range(45): pg.mouse.wheel(60, 0); pg.wait_for_timeout(16)
    for i in range(10): pg.mouse.wheel(0, 50); pg.wait_for_timeout(16)      # down and up again
    for i in range(10): pg.mouse.wheel(0, -50); pg.wait_for_timeout(16)
    for z in (1.25, 1.25, 0.8, 0.8): R("(()=>{V.ppb*=%s;dirty=true})()" % z); pg.wait_for_timeout(60)   # zoom in time: one uniform
    pg.wait_for_timeout(300); c = st()
    ok(c['stats']['uploads'] == 0 and c['stats']['uploadPixels'] == 0, 'scrolling and zooming: 0 canvas uploads', c['stats'])
    ok(c['stats']['sceneSends'] == a['stats']['sceneSends'] and c['n']['scene'] == a['n']['scene'], 'scrolling and zooming: the rectangle list is not sent again', [a['stats']['sceneSends'], c['stats']['sceneSends']])
    ok(c['stats']['sceneDraws'] > a['stats']['sceneDraws'] + 5 and c['n']['view'] > a['n']['view'] + 5, 'scrolling: the backdrop follows by a uniform (drawn again on the graphics card)', [a['stats']['sceneDraws'], c['stats']['sceneDraws']])
    R("(()=>{V.x=0;UI.follow=false;pos=24;dirty=true;start()})()"); pg.wait_for_timeout(1200); a = st(); pg.wait_for_timeout(2500); c = st(); R("stop()")
    fr = c['frn'] - a['frn']
    ok(c['stats']['uploads'] == 0 and c['stats']['sceneSends'] == a['stats']['sceneSends'], 'playing: 0 uploads, 0 lists sent', [c['stats']['uploads'], c['stats']['sceneSends'] - a['stats']['sceneSends']])
    ok(c['phl']['fast'] - a['phl']['fast'] >= fr * 0.8 and c['n']['scene'] == a['n']['scene'], 'playing: playhead-only frames do not rebuild the scene or redraw the arrangement', {'frames': fr, 'playhead-only': c['phl']['fast'] - a['phl']['fast'], 'full': c['n']['view'] - a['n']['view'], 'lists': c['n']['scene'] - a['n']['scene']})
    ok(0 < c['stats']['sceneDraws'] - a['stats']['sceneDraws'] <= fr, 'playing: the playhead under the glass is one uniform (2 px steps)', [c['stats']['sceneDraws'] - a['stats']['sceneDraws'], fr])
    # an edit sends the list once
    pg.wait_for_timeout(400); a = st()
    R("(()=>{const t=S.tracks.find(t=>t.clips.length>2);t.clips[1].start+=1;dirty=true})()"); pg.wait_for_timeout(500); c = st()
    ok(c['stats']['sceneSends'] == a['stats']['sceneSends'] + 1, 'an edit (a clip moved) sends the list once', [a['stats']['sceneSends'], c['stats']['sceneSends']])
    R("(()=>{const t=S.tracks.find(t=>t.clips.length>2);t.clips[1].start-=1;dirty=true})()"); pg.wait_for_timeout(300)
    # a taller track row (vertical zoom) changes the rows themselves: a new list, as after an edit
    a = st(); R("(()=>{V.th+=12;dirty=true})()"); pg.wait_for_timeout(400); c = st(); R("(()=>{V.th-=12;dirty=true})()"); pg.wait_for_timeout(400)
    ok(c['stats']['sceneSends'] == a['stats']['sceneSends'] + 1 and c['stats']['uploads'] == 0, 'a new track height makes one new list (still no upload)', [a['stats']['sceneSends'], c['stats']['sceneSends']])
    # ---- 5. the playhead layer ----
    ph = pg.evaluate(r"""async()=>{const R=GT.R,o={};R("(()=>{V.x=0;pos=40;dirty=true})()");await GT.wait(400);
      const w=document.getElementById('arrPhW'),c=document.getElementById('arrPhC'),a=document.getElementById('arr');o.after=a.nextElementSibling===w;o.pe=getComputedStyle(w).pointerEvents;o.clip=[a.style.clipPath,w.style.clipPath];
      const px=R("X0+(curDisp()-V.x)*V.ppb"),r=c.getBoundingClientRect(),m=a.getBoundingClientRect();o.px=px;o.left=r.left-m.left+80;
      /* the arrangement canvas has no playhead baked in: the pixel under the line equals its neighbour 4 px to the left */
      const t=document.createElement('canvas');t.width=a.width;t.height=a.height;const x=t.getContext('2d',{willReadFrequently:true});x.drawImage(a,0,0);const d=window.devicePixelRatio||1,y=Math.round(R("AY+TRY[1]+V.th-2")*d),p1=x.getImageData(Math.round((px+.7)*d),y,1,1).data,p0=x.getImageData(Math.round((px-4)*d),y,1,1).data;
      o.baked=Math.abs(p1[0]-p0[0])+Math.abs(p1[1]-p0[1])+Math.abs(p1[2]-p0[2]);
      const lx=t.getContext('2d');const pc=document.createElement('canvas');pc.width=c.width;pc.height=c.height;const pcx=pc.getContext('2d',{willReadFrequently:true});pcx.drawImage(c,0,0);const q=pcx.getImageData(Math.round(80.2*d),Math.round(200*d),1,1).data;o.line=[q[0],q[1],q[2],q[3]];
      o.fb=R("JSON.stringify(FB)");return o}""")
    ok(ph['after'] and ph['pe'] == 'none' and ph['clip'][0] == ph['clip'][1], 'the playhead layer sits right over the arrangement canvas with the same cut-out and takes no clicks', [ph['after'], ph['pe'], ph['clip']])
    ok(abs(ph['left'] - ph['px']) <= 1, 'the layer is where the playhead is', [ph['left'], ph['px']])
    ok(ph['baked'] <= 6 and ph['line'][3] > 200 and ph['line'][1] > 150, 'the line is on its own layer, not painted into the arrangement canvas', [ph['baked'], ph['line']])
    fbr = json.loads(ph['fb'])
    m = pg.evaluate("()=>{const r=document.getElementById('arr').getBoundingClientRect();return [r.left,r.top]}")
    f0 = R("!!UI.follow"); pg.mouse.click(m[0] + fbr['x'] + fbr['w'] / 2, m[1] + fbr['y'] + fbr['h'] / 2); pg.wait_for_timeout(300); f1 = R("!!UI.follow")
    ok(f0 != f1, 'the Follow button on the playhead still takes the click', [f0, f1])
    if f1 != f0: R("(()=>{setFollow(%s)})()" % ('true' if f0 else 'false'))
    # Follow centre: the arrangement is redrawn only when the view moved a pixel
    R("(()=>{UI.follow=true;UI.followMode='center';pos=120;dirty=true;start()})()"); pg.wait_for_timeout(1200); a = st(); pg.wait_for_timeout(2500); c = st(); R("stop()")
    fr = c['frn'] - a['frn']; full = c['n']['view'] - a['n']['view']
    ok(fr > 20 and full <= fr * 0.5 and c['stats']['uploads'] == 0 and c['stats']['sceneSends'] == a['stats']['sceneSends'], 'Follow centre: no full redraw in frames where the view did not move, no backdrop copy', {'frames': fr, 'full redraws': full, 'playhead-only': c['phl']['fast'] - a['phl']['fast']})
    R("(()=>{UI.follow=true;V.x=0;pos=0;dirty=true})()"); pg.wait_for_timeout(300)
    # ---- 6. levels: mapping from the Light mode slider, the choice by hand, Light, Solid ----
    lv = {}
    for stp in (3, 2, 1, 0):
        R("pmSetStop(%d)" % stp); pg.wait_for_timeout(1300); s = st(); bf = pg.evaluate("()=>GT.bf()")
        lv[stp] = s['lv']; ok(all(x[0] == 'none' and x[1] == '' for x in bf), 'no backdrop-filter on a docked surface at stop %d (%s)' % (stp, s['lv']), bf if not all(x[0] == 'none' for x in bf) else '')
        if stp == 1:
            ok(s['on'] and s['info']['level'] == 'light' and s['info']['lens'] == 'off' and s['info']['rate'] == 30 and s['info']['levels'][0] == 8, 'Light: the same engine, lens off, an eighth-size backdrop, 30 refreshes a second', [s['info']['level'], s['info']['lens'], s['info']['rate'], s['info']['levels']])
            r = pg.evaluate("()=>{const g=GT.R('GLE.g'),fx=GT.rect('fxglass');g.setLensPreset('off');const a=GT.read();g.setLensPreset('wide');const b=GT.read();return {d:GT.maxDiff(a,b,0,0,a.w,a.h),alpha:GT.px(b,fx.x+fx.w/2,fx.y+fx.h/2)[3],tr:getComputedStyle(document.getElementById('tr')).backgroundImage}}")
            ok(r['d'] == 0 and r['alpha'] == 255, 'Light has no lens: the lens preset changes nothing, the faces are drawn', r['d'])
            ok('0.5)' in r['tr'], 'Light: the docked panels stay see-through over the engine (their own tint value)', r['tr'][:70])
            pg.screenshot(path=os.path.join(OUT, 'gs1_light.png'))
        if stp == 0:
            r = pg.evaluate("()=>({cv:!!document.getElementById('glassCv'),g:!!GT.R('GLE.g'),sol:['hglass','tr','fxglass'].map(i=>document.getElementById(i).classList.contains('glsol')),clip:document.getElementById('arr').style.clipPath})")
            ok(not r['cv'] and not r['g'] and all(r['sol']) and r['clip'] == '', 'Lightest: Solid, no engine, no canvas, nothing cut out of the arrangement', r)
    ok(lv == {3: 'glass', 2: 'glass', 1: 'light', 0: 'solid'}, 'existing choices map: Full effects and Optimised = Glass, Lighter = Light, Lightest = Solid', lv)
    R("pmSetStop(3)"); pg.wait_for_timeout(800); R("gleSet('lv','solid')"); pg.wait_for_timeout(800); s = st()
    r = pg.evaluate("()=>({tr:getComputedStyle(document.getElementById('tr')).backgroundImage,fx:getComputedStyle(document.getElementById('fxglass')).backgroundColor,cv:!!document.getElementById('glassCv'),bf:GT.bf()})")
    ok(s['lv'] == 'solid' and not s['on'] and not r['cv'] and r['fx'].startswith('rgb(') and ', 0.' not in r['tr'], 'Solid picked by hand at Full effects: solid docked panels, no engine', [r['tr'][:60], r['fx']])
    ok(all(x[0] == 'none' for x in r['bf']), 'Solid: no backdrop-filter either (it is not used as a fallback)', r['bf'])
    pg.screenshot(path=os.path.join(OUT, 'gs1_solid.png'))
    R("gleSet('lv','light')"); pg.wait_for_timeout(800); s1 = st(); R("pmSetStop(2)"); pg.wait_for_timeout(900); s2 = st()
    ok(s1['lv'] == 'light' and s2['lv'] == 'glass' and (s2['gl'] or {}).get('lv') is None, 'a level picked by hand holds until the Light mode slider is moved, then follows the slider again', [s1['lv'], s2['lv'], s2['gl']])
    R("pmSetOn(false)"); pg.wait_for_timeout(900)
    r = pg.evaluate("()=>{const g=GT.R('GLE.g');GT.R(\"gleSet('lens','apple')\");const a=g.info.lens;GT.R(\"gleSet('blur','heavy')\");const b=g.info.blur,lv=g.info.levels.slice();GT.R(\"gleSet('lens','wide')\");GT.R(\"gleSet('blur','light')\");return {a,b,lv,back:[g.info.lens,g.info.blur]}}")
    ok(r['a'] == 'apple' and r['b'] == 'heavy' and len(r['lv']) == 3 and r['back'] == ['wide', 'light'], 'lens and blur presets reach the engine', r)
    # ---- 7. Settings ----
    R("openSettings('perf')"); pg.wait_for_timeout(900)
    ui = pg.evaluate("()=>{const b=document.getElementById('glBox');if(!b)return null;const segs=[...b.querySelectorAll('.glseg')].map(s=>[s.dataset.k,[...s.children].map(x=>[x.textContent,x.title.length>10,x.classList.contains('on'),x.disabled])]);const all=b.textContent+[...b.querySelectorAll('[title]')].map(e=>e.title).join(' ')+b.previousElementSibling.textContent;return {segs,rows:[...b.querySelectorAll('.glr')].map(r=>r.title.length>20),dash:/\\u2014|\\u2013/.test(all),sliders:b.querySelectorAll('input[type=range]').length,note:document.getElementById('glNote').textContent,head:b.previousElementSibling.textContent,vis:b.getBoundingClientRect().height>40}}")
    ok(ui and ui['vis'], 'Settings, Performance: the block for the docked panels is there', ui and ui['head'])
    if ui:
        names = {k: [x[0] for x in v] for k, v in ui['segs']}
        ok(names == {'lv': ['Glass', 'Light', 'Solid'], 'lens': ['Off', 'Fine', 'Apple', 'Wide'], 'blur': ['Light', 'Regular', 'Heavy']} and ui['sliders'] == 0, 'choices: Glass / Light / Solid, lens Off / Fine / Apple / Wide, blur Light / Regular / Heavy, no sliders', names)
        on = {k: [x[0] for x in v if x[2]] for k, v in ui['segs']}
        ok(on == {'lv': ['Glass'], 'lens': ['Wide'], 'blur': ['Light']}, 'the marked choices are the defaults: Glass, Wide, Light', on)
        ok(all(x[1] for k, v in ui['segs'] for x in v) and all(ui['rows']), 'every new control has a tooltip')
        ok(not ui['dash'], 'no em dash in the new texts')
    pg.click("#glBox .glseg[data-k=lv] button[data-v=light]"); pg.wait_for_timeout(900); s = st()
    r = pg.evaluate("()=>[...document.querySelectorAll('#glBox .glseg[data-k=lens] button')].map(b=>b.disabled)")
    ok(s['lv'] == 'light' and (s['gl'] or {}).get('lv') == 'light' and all(r), 'clicking Light switches the level and saves it; the lens choice is greyed out at Light', [s['lv'], s['gl'], r])
    pg.screenshot(path=os.path.join(OUT, 'gs1_settings.png'))
    pg.click("#glBox .glseg[data-k=lv] button[data-v=glass]"); pg.wait_for_timeout(700)
    R("(()=>{closeSettings&&closeSettings()})()") if R("typeof closeSettings==='function'") else pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    R("(()=>{UI.gl=null;saveUI();pmSetOn(false)})()"); pg.wait_for_timeout(900)
    # ---- 8. context loss and restore ----
    before = pg.evaluate("()=>{const b=GT.read(),tr=GT.rect('tr');window.__b0=b;return GT.px(b,tr.x+tr.w/2,tr.y+tr.h/2)}")
    pg.evaluate("()=>GT.R('GLE.g').debug.lose()"); pg.wait_for_function("()=>AudioLab.run('GLE.g.mode')==='fallback'", timeout=8000); pg.wait_for_timeout(400)
    r = pg.evaluate("()=>{const g=GT.R('GLE.g'),sib=g.canvas.nextElementSibling;return {mode:g.mode,reason:g.reason,sib:sib&&sib.tagName,vis:g.canvas.style.visibility,bf:GT.bf(),lost:g.stats.lost}}")
    ok(r['mode'] == 'fallback' and r['reason'] == 'lost' and r['sib'] == 'CANVAS' and all(x[0] == 'none' for x in r['bf']), 'context lost: the engine shows its plain solid look by itself, still no backdrop-filter', r)
    pg.evaluate("()=>GT.R('GLE.g').debug.restore()"); pg.wait_for_function("()=>AudioLab.run('GLE.g.mode')==='gl'", timeout=8000); pg.wait_for_timeout(600)
    r = pg.evaluate("()=>{const g=GT.R('GLE.g'),b=GT.read(),tr=GT.rect('tr'),fx=GT.rect('fxglass');return {mode:g.mode,restored:g.stats.restored,rects:g.info.sceneRects,d:GT.maxDiff(b,window.__b0,tr.x,tr.y,tr.x+tr.w,tr.y+tr.h),d2:GT.maxDiff(b,window.__b0,fx.x,fx.y,fx.x+fx.w,fx.y+fx.h),extra:document.querySelectorAll('#main>canvas').length}}")
    ok(r['mode'] == 'gl' and r['restored'] == 1 and r['rects'] > 100 and r['d'] <= 2 and r['d2'] <= 2, 'context restored: the glass is back and the same picture as before', r)
    # ---- 9. the background freeze stops the engine's loop ----
    r = json.loads(pg.evaluate("async()=>{const R=c=>AudioLab.run(c),g=R('GLE.g');R('AO.gate=true');await GT.wait(300);const a=g.stats.renders;await GT.wait(900);const b=g.stats.renders;R('AO.open()');await GT.wait(600);return JSON.stringify({frozen:b-a,after:g.stats.renders-b})}"))
    ok(r['frozen'] == 0 and r['after'] > 5, 'frames held back by the background freeze (task AO): the engine is not drawn; it runs again afterwards', r)
    # ---- 10. window drags keep the pointer ----
    R("openMixer()"); pg.wait_for_timeout(1200)
    bx = pg.evaluate("()=>{const h=document.querySelector('#mixWin .fwh'),r=h.getBoundingClientRect(),w=document.getElementById('mixWin');for(let x=r.left+6;x<r.right-6;x+=7){const y=r.top+r.height/2,e=document.elementFromPoint(x,y);if(e&&h.contains(e)&&!e.closest('button,select,input,.seg'))return [x,y,w.offsetLeft,w.offsetTop]}return null}")
    pg.mouse.move(bx[0], bx[1]); pg.mouse.down(); pg.mouse.move(bx[0] + 20, bx[1] + 10); pg.mouse.move(bx[0] + 80, bx[1] + 40)
    cap = pg.evaluate("()=>document.querySelector('#mixWin .fwh').hasPointerCapture(1)")
    pg.mouse.move(bx[0] + 120, bx[1] + 60); pg.mouse.up(); pg.wait_for_timeout(300)
    r = pg.evaluate("()=>{const w=document.getElementById('mixWin');return [w.offsetLeft,w.offsetTop,document.querySelector('#mixWin .fwh').hasPointerCapture(1),w.classList.contains('mv')]}")
    ok(cap and abs(r[1] - bx[3] - 60) <= 2 and not r[2] and not r[3], 'dragging a window (the mixer, which is as wide as the screen): the title bar holds the pointer during the drag, the window lands where it was dropped', [cap, bx[2:], r])
    R("(()=>{const w=document.getElementById('mixWin');if(w)w.hidden=true})()")
    pg.wait_for_timeout(300)
    ok(not logs, 'no console errors or warnings', logs[:6])
    b.close()

    # ---- 11. no WebGL2: Solid ----
    b, pg, logs = boot(p, init=NOGL)
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    R("pmSetOn(false)"); pg.wait_for_timeout(1500); s = pg.evaluate("()=>GT.st()")
    r = pg.evaluate("()=>({cv:!!document.getElementById('glassCv'),bf:GT.bf(),sol:['hglass','tr','fxglass'].map(i=>document.getElementById(i).classList.contains('glsol')),tr:getComputedStyle(document.getElementById('tr')).backgroundImage,clip:document.getElementById('arr').style.clipPath,ph:!!document.getElementById('arrPhC')})")
    ok(s['fail'] != '' and s['lv'] == 'solid' and not s['on'] and not r['cv'] and all(r['sol']) and ', 0.' not in r['tr'], 'WebGL2 switched off, Full effects: the docked panels are Solid', [s['fail'], s['lv'], r['tr'][:60]])
    ok(all(x[0] == 'none' and x[1] == '' for x in r['bf']), 'WebGL2 switched off: no backdrop-filter on the docked surfaces (the fallback is Solid)', r['bf'])
    R("openSettings('perf')"); pg.wait_for_timeout(800)
    note = pg.evaluate("()=>{const n=document.getElementById('glNote');return n?[n.textContent,[...document.querySelectorAll('#glBox .glseg[data-k=lv] button')].map(b=>b.disabled)]:null}")
    ok(note and 'cannot run the glass engine' in note[0] and note[1] == [True, True, False], 'Settings says why and offers only Solid', note)
    R("(()=>{pos=30;UI.follow=false;start()})()"); pg.wait_for_timeout(1500); R("stop()")
    ok(r['ph'] and not logs, 'without WebGL2 the app runs as before (playhead layer on), no console errors', logs[:5])
    pg.screenshot(path=os.path.join(OUT, 'gs1_nowebgl.png'))
    b.close()

    # ---- 12. a 2x screen and a zoomed interface ----
    b, pg, logs = boot(p, dsf=2, w=1400, h=900)
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    R("pmSetOn(false)"); pg.wait_for_timeout(1500)
    r = pg.evaluate("()=>{const b=GT.read(),g=GT.R('GLE.g'),tr=GT.rect('tr'),fx=GT.rect('fxglass');return {w:b.w,h:b.h,dpr:g.info.dpr,aTr:GT.px(b,(tr.x+tr.w/2)*2,(tr.y+tr.h/2)*2)[3],aFx:GT.px(b,(fx.x+fx.w/2)*2,(fx.y+fx.h/2)*2)[3],aOpen:GT.px(b,1600,400)[3],up:g.stats.uploads}}")
    ok(r['dpr'] == 2 and r['aTr'] == 255 and r['aFx'] == 255 and r['aOpen'] == 0 and r['up'] == 0, '2x screen: faces in the right place, nothing uploaded', r)
    R("(()=>{UI.scale=125;applyScale();dirty=true})()"); pg.wait_for_timeout(1800)
    r = pg.evaluate("()=>{const g=GT.R('GLE.g'),z=GT.R('ZOOM'),m=document.getElementById('glassCv').getBoundingClientRect(),t=document.getElementById('tr').getBoundingClientRect(),P=GT.R(\"JSON.stringify(['tr','fxglass','hglass'].map(i=>GLE.g.hasPanel(i)))\");const b=GT.read(),k=b.w/m.width;return {z,P,a:GT.px(b,(t.left-m.left+t.width/2)*k,(t.top-m.top+t.height/2)*k)[3],above:GT.px(b,(t.left-m.left+t.width/2)*k,(t.top-m.top)*k-300*k)[3]}}")
    ok(r['z'] == 1.25 and r['a'] == 255, 'interface size 125 %: the transport face is under the transport', r)
    ok(not logs, '2x and 125 %: no console errors', logs[:5])
    b.close()

print('\n%d checks, %d failed' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED: ' + f)
sys.exit(1 if FAIL else 0)
