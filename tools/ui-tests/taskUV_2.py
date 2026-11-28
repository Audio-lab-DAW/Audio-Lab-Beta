#!/usr/bin/env python3
"""Task UV-2 (lane O, view engine), part a: S14 tiled arrangement on the 2D canvas.

The real app at the user's size (2194 x 1139 CSS px at 1.75x), Fractals open, glass engine on (SwiftShader), as frametime.py.
Every comparison is against a fresh full drawing of the same view by lane A's drawArr (the tiles switched off for that one drawing).
Checks:
  scroll   sideways and up and down by whole device pixels: the tiled frame is pixel for pixel the fresh drawing, one step and after
           40 steps in a row; most of the picture is kept (only the new strip, the ruler, the header column, the master lane and the
           clips at the left edge are painted)
  trackpad sideways by 6 CSS px a frame (10.5 device px: not whole pixels): tiled while it moves, and UV.rest ms after the last step
           the picture is drawn once in full: pixel for pixel the fresh drawing
  edit     scrolled to the middle: a clip muted, a clip moved by a beat, a note changed in a MIDI clip, a clip selected, the hover:
           only those clips' boxes are painted (a few % of the picture), pixel for pixel the fresh drawing
  full     a setting (clip opacity), the zoom, the track height, a loop change and UV_HOOKS.bump() draw in full
  Light    the scroll and edit checks again in Light
  idle     after the rest drawing no timer of UV-2 is left and nothing draws; no console errors
  python3 tools/ui-tests/taskUV_2.py [repo dir] [out dir]
"""
import sys, os, json
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
SRC = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
N = [0, 0]; FAIL = []
def ck(name, ok, info=''):
    N[0] += 1
    if ok: N[1] += 1; print('  ok  ', name, info if info != '' else '')
    else: FAIL.append(name); print('  FAIL', name, info)

HELP = r"""
window.__t={
 hash(){const g=arr.getContext('2d'),d=g.getImageData(0,0,arr.width,arr.height).data,u=new Uint32Array(d.buffer);let h=2166136261>>>0;for(let i=0;i<u.length;i++){h=Math.imul(h^u[i],16777619)>>>0}return h+':'+arr.width+'x'+arr.height},
 px(){const g=arr.getContext('2d');return g.getImageData(0,0,arr.width,arr.height).data},
 /* the last device column (2194 CSS px at 1.75 = 3839.5) is half covered: lane A's own drawing blends it with what was there before, so it is left out */
 diff(a,b){this.md=0;let n=0,W=arr.width,XE=Math.floor(arr.getBoundingClientRect().width*(window.devicePixelRatio||1)-1e-6),bx=[1e9,1e9,-1,-1];for(let i=0;i<a.length;i+=4)if(a[i]!==b[i]||a[i+1]!==b[i+1]||a[i+2]!==b[i+2]){const x=(i/4)%W,y=(i/4-x)/W;if(x>=XE)continue;n++;const dd=Math.max(Math.abs(a[i]-b[i]),Math.abs(a[i+1]-b[i+1]),Math.abs(a[i+2]-b[i+2]));if(dd>this.md)this.md=dd;if(x<bx[0])bx[0]=x;if(y<bx[1])bx[1]=y;if(x>bx[2])bx[2]=x;if(y>bx[3])bx[3]=y}this.bx=n?bx:null;return n},
 /* one tiled frame (what the frame loop does when dirty), then the same view drawn fresh; returns both hashes and the mode */
 tiled(){drawArr(false);return{mode:UVT.last.mode,why:UVT.why,area:UVT.last.rects?UVT.last.rects.reduce((a,r)=>a+r[2]*r[3],0)/(arr.width*arr.height):1}},
 fresh(){/* twice: a few things lane A lays out at the end of a drawing are used by the next one */UVT.force=1;drawArr(false);UVT.force=1;drawArr(false)},
 cmp(){const m=this.tiled(),a=this.px();this.fresh();const b=this.px();return Object.assign(m,{diff:this.diff(a,b),md:this.md,bx:this.bx})},
 /* near: while it moves, a tiled frame may differ from a fresh drawing only on anti-aliased edges (Skia rasterises curves a little
    differently under a clip of several rectangles): under 0.3 % of the pixels, by at most 24 levels. At rest it is drawn in full. */
 near(r){return r.diff<=arr.width*arr.height*.003&&(r.md||0)<=24},
 /* the drawing at rest: what the timer asks for, then compared with a fresh one */
 rest(){return new Promise(res=>setTimeout(()=>{const f=UVT.force,dd=dirty;if(dirty){dirty=false;drawArr(false)}const A=this.px(),mode=UVT.last.mode;this.fresh();const C=this.px(),o={f,dd,mode,diff:this.diff(A,C),tm:!!UVT.tm};if(window.__A){o.dA=this.diff(__A,C);o.mdA=this.md;o.bxA=this.bx;window.__A=null}res(JSON.stringify(o))},UV.rest+120))},
 D(){return(window.devicePixelRatio||1)*ZOOM},
 home(){if(play.on)stop();Object.assign(V,{x:96,ppb:24,th:64,y:0});clampV();UVT.force=1;drawArr(false);UVT.force=0;this.prime()},
 /* the first frame that moves after rest draws in full and keeps a copy for the next ones */
 prime(){V.x+=1/this.D()/V.ppb;clampV();drawArr(false);return UVT.last.mode+':'+UVT.why},
};0
"""

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(args=ARGS)
        ctx = b.new_context(viewport={'width': 2194, 'height': 1139}, device_scale_factor=1.75); pg = ctx.new_page(); errs = []
        pg.on('console', lambda m: errs.append(m.text[:200]) if m.type == 'error' and 'fetching the script' not in m.text else None)
        pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)[:300]))
        pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
        pg.add_init_script(INIT); pg.set_default_timeout(300000)
        pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(4000)
        pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
        R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
        R("openDemoFractals()"); pg.wait_for_timeout(7000); pg.evaluate("()=>{const s=document.getElementById('liteNote');if(s)s.remove()}")
        R("pmSetOn(false);UI.follow=false;stop();hovC=null;0"); pg.wait_for_timeout(800)
        R(HELP)
        J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
        print('version', R("VERSION"), 'tracks', R("S.tracks.length"), 'clips', R("S.tracks.reduce((a,t)=>a+t.clips.length,0)"), 'canvas', R("arr.width+'x'+arr.height"))
        # the frame loop must not draw between the test's own drawings
        for _ in range(240):
            if R("!MAP.busy&&!MAP.tm&&!MAP.et"): break
            pg.wait_for_timeout(1000)
        pg.wait_for_timeout(500)
        gpu = R("uvGpu()"); print('graphics card for the canvas:', gpu, R("UVT.gpuName"), '(tiles are on by themselves only with one; switched on here for the test)')
        ck('the tiles are on by themselves only with a graphics card (this machine: %s)' % ('one' if gpu else 'software rendering'), R("UVT.on==='auto'"))
        if not gpu:
            r = J("(()=>{const o=[];V.x=96;V.ppb=24;V.y=0;clampV();UVT.force=1;drawArr(false);for(let k=0;k<3;k++){V.x+=7/((window.devicePixelRatio||1)*ZOOM)/V.ppb;drawArr(false);o.push(UVT.last.mode+':'+UVT.why)}const c=S.tracks.find(t=>t.clips.length).clips[0];c.mute=!c.mute;drawArr(false);o.push(UVT.last.mode);c.mute=!c.mute;drawArr(false);o.push(UVT.last.mode);return o})()")
            ck('standard setting without a graphics card: scrolling draws in full, an edit is tiled', r[:3] == ['full:cpu'] * 3 and r[3] == 'edit', r)
        R("UVT.on=true;0")
        R("window.__fz=frame0;frame0=function(){};0")

        for look in ('dark', 'light'):
            if look == 'light': R("frame0=__fz;UI.lite=true;UI.liteMan=true;applyLite();dirty=true;0"); pg.wait_for_timeout(1200); R("frame0=function(){};0")
            L = ' (' + look + ')'
            RS_ = lambda: json.loads(R("__t.rest()"))
            def at_rest(name):
                q = RS_()
                ck(name + ': UV.rest ms after the last tiled frame one full drawing is asked for' + L, q['f'] == 1 and q['dd'] and q['mode'] == 'full', q)
                ck(name + ': at rest pixel for pixel the fresh drawing' + L, q['diff'] == 0, q['diff'])
                ck(name + ': no UV-2 timer is left' + L, not q['tm'])
            # ---- scroll by whole device pixels
            R("__t.home();0")
            r = J("(()=>{V.x+=7/__t.D()/V.ppb;return __t.cmp()})()")
            ck('one sideways step of 7 device px is tiled' + L, r['mode'] == 'shift', r)
            ck('... and the same picture as a fresh drawing (anti-aliased edges aside)' + L, R("__t.near(%s)" % json.dumps(r)), r)
            ck('... painting under 40 % of the picture' + L, r['area'] < .4, '%.1f %%' % (100 * r['area']))
            R("__t.home();0")
            r = J("(()=>{let a=0,ms=new Set();for(let k=0;k<40;k++){V.x+=(k%10<6?9:-4)/__t.D()/V.ppb;const m=__t.tiled();a+=m.area;ms.add(m.mode)}const A=__t.px();const m=UVT.last.mode;__t.fresh();const d=__t.diff(A,__t.px());__t.fresh();return{modes:[...ms],area:a/40,diff:d,md:__t.md}})()")
            ck('40 tiled sideways steps in a row (9 and 4 device px)' + L, r['modes'] == ['shift'] and R("__t.near(%s)" % json.dumps(r)), r)
            ck('... painting on average under 40 % of the picture' + L, r['area'] < .4, '%.1f %%' % (100 * r['area']))
            R("__t.home();V.y=200;clampV();__t.fresh();__t.prime();0")
            r = J("(()=>{let ms=new Set(),a=0;for(let k=0;k<20;k++){V.y+=(k%8<5?8:-4);clampV();const m=__t.tiled();a+=m.area;ms.add(m.mode)}const A=__t.px();__t.fresh();return{modes:[...ms],area:a/20,diff:__t.diff(A,__t.px()),md:__t.md}})()")
            ck('20 tiled steps up and down by 4 or 8 CSS px (7 or 14 device px)' + L, r['modes'] == ['shift'] and R("__t.near(%s)" % json.dumps(r)), r)
            R("__t.home();0")
            r = J("(()=>{let ms=new Set();for(let k=0;k<20;k++){V.x+=11/__t.D()/V.ppb;V.y+=4;clampV();ms.add(__t.tiled().mode)}const A=__t.px();__t.fresh();return{modes:[...ms],diff:__t.diff(A,__t.px()),md:__t.md}})()")
            ck('20 diagonal steps' + L, r['modes'] == ['shift'] and R("__t.near(%s)" % json.dumps(r)), r)
            # ---- trackpad: fractional steps, drawn in full at rest
            R("__t.home();0")
            r = J("(()=>{let ms=new Set(),a=0;for(let k=0;k<30;k++){V.x+=6/V.ppb;clampV();const m=__t.tiled();a+=m.area;ms.add(m.mode)}return{modes:[...ms],area:a/30,tm:!!UVT.tm}})()")
            ck('a trackpad scroll of 6 CSS px a frame (10.5 device px) is tiled' + L, r['modes'] == ['shift'], r)
            ck('... painting on average under 40 % of the picture' + L, r['area'] < .4, '%.1f %%' % (100 * r['area']))
            at_rest('trackpad scroll')
            # ---- edits while scrolled
            R("__t.home();V.x=160;clampV();__t.fresh();0")
            vis = J("(()=>{const o=[];S.tracks.forEach((t,i)=>{for(const c of t.clips){const G=clipGeom(i,c);if(G.x>X0+40&&G.x+G.w<arr.width/__t.D()-40&&G.y>AY+10&&G.y+G.h<arr.height/__t.D()-BY-10)o.push([i,t.clips.indexOf(c),!!c.notes])}});return o})()")
            ck('there are clips in view to edit' + L, len(vis) >= 3, len(vis))
            i, j, _ = vis[0]
            EDITS = [('muting a clip paints only its box', "const c=S.tracks[%d].clips[%d];c.mute=!c.mute" % (i, j), "c.mute=!c.mute", .08, 'edit'),
                     ('moving a clip by a beat paints only its old and new box', "const c=S.tracks[%d].clips[%d];c.start+=1" % (i, j), "c.start-=1", .1, 'edit'),
                     ('selecting a clip paints only the clips whose look changed', "const c=S.tracks[%d].clips[%d],s0=selC;selC=c.id" % (i, j), "selC=s0", .15, 'edit'),
                     ('the hover on a clip paints only that clip', "const c=S.tracks[%d].clips[%d];hovC=c.id" % tuple(vis[1][:2]), "hovC=null", .08, 'edit'),
                     ('an edit and a scroll in the same frame are tiled together', "const c=S.tracks[%d].clips[%d];c.mute=!c.mute;V.x+=8/__t.D()/V.ppb" % (i, j), "c.mute=!c.mute", .6, 'shift')]
            mi = [v for v in vis if v[2]]
            if mi: EDITS.insert(2, ('changing a note in a MIDI clip (the piano roll) paints only that clip', "const c=S.tracks[%d].clips[%d],n=c.notes.find(n=>n.s>=c.off&&n.s<c.off+c.len);n.p+=3" % tuple(mi[0][:2]), "n.p-=3", .08, 'edit'))
            for name, do, undo, lim, mode in EDITS:
                if mode == 'shift': R("__t.prime();0")
                R("window.__do=()=>{%s;window.__undo=()=>{%s}};0" % (do, undo))
                r = J("(()=>{__do();const r=__t.tiled();window.__A=__t.px();return r})()")
                q = RS_(); r.update(diff=q.get('dA'), md=q.get('mdA'), bx=q.get('bxA'))
                ck(name + L, r['mode'] == mode and r['area'] < lim and R("__t.near(%s)" % json.dumps(r)), r)
                nm = name.split(' paints')[0].split(' are')[0]
                ck(nm + ': UV.rest ms later one full drawing, pixel for pixel the fresh drawing' + L, q['f'] == 1 and q['dd'] and q['mode'] == 'full' and q['diff'] == 0 and not q['tm'], q)
                R("__undo();__t.fresh();0")
            # ---- what draws in full
            for name, js, undo in (
                    ('a setting (clip opacity)', "UI.clipA=(UI.clipA??36)+10", "UI.clipA-=10"),
                    ('a zoom', "V.ppb*=1.05", "V.ppb/=1.05"),
                    ('the track height', "V.th+=6", "V.th-=6"),
                    ('the loop', "S.loopRange=null;S.loop={a:8,b:24,on:!(S.loop&&S.loop.on)}", ""),
                    ('lane A\'s hook UV_HOOKS.bump()', "UV_HOOKS.bump()", ""),
                    ('nothing that the tiles can see', "0", "")):
                R("__t.fresh();0")
                r = J("(()=>{%s;clampV();const r=__t.cmp();%s;clampV();__t.fresh();return r})()" % (js, undo))
                ck(name + ' draws in full' + L, r['mode'] == 'full', r)
        R("frame0=__fz;0"); pg.wait_for_timeout(600)
        idle = json.loads(R("new Promise(res=>{const n0=UVT.n.full+UVT.n.shift+UVT.n.edit;setTimeout(()=>res(JSON.stringify({draws:UVT.n.full+UVT.n.shift+UVT.n.edit-n0,tm:!!UVT.tm})),1500)})"))
        ck('idle: nothing is drawn and no UV-2 timer runs', idle['draws'] == 0 and not idle['tm'], idle)
        pg.screenshot(path=os.path.join(OUT, 'taskUV_2_light.png'))
        ck('no console errors', not errs, errs[:5])
        b.close()
    print('%d/%d checks passed' % (N[1], N[0]))
    if FAIL: print('FAILED:', FAIL); sys.exit(1)

if __name__ == '__main__':
    main()
