#!/usr/bin/env python3
"""Task DS-A3 (design round 2, AC3): clips without a title band, name on the body, 2 px colour edge, darker body.
   python3 tools/ui-tests/taskDS_A3.py [index.html]
At the user's size (2194 x 1139 CSS px at 1.75x) with Fractals, Dark (glass) and Light mode. SwiftShader: correctness only."""
import sys, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)

# pixels of one clip on the arrangement canvas: the top edge row, a row in the old band zone (7 px down), and the body
PIX = r"""(()=>{V.ppb=25;V.x=128;V.y=0;clampV();selC=null;SELCS.clear();CLC.clear();drawArr();const d=DPX,g=arr.getContext('2d');
  const i=S.tracks.findIndex(t=>/^kick$/i.test(t.name)),t=S.tracks[i],c=t.clips.find(c=>c.start<=136&&c.start+c.len>136),G=clipGeom(i,c);
  const px=(x,y)=>Array.from(g.getImageData(Math.round(x*d),Math.round(y*d),1,1).data).slice(0,3);
  const xm=X0+(137.3-V.x)*V.ppb;return{col:t.color,top:G.top,edge:px(xm,G.y+.5),band:px(xm,G.y+7),body:px(xm,G.by+G.bh*.25),lane:px(xm,G.y-1.5)}})()"""

def load(p, logs):
    ctx = p.chromium.launch(args=ARGS).new_context(viewport={'width': 2194, 'height': 1139}, device_scale_factor=1.75); pg = ctx.new_page()
    pg.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text else None)
    pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    R("pmSetOn(false)"); R("openDemoFractals()"); pg.wait_for_timeout(6000)
    return pg, R

def rgb(h): n = int(h[1:], 16); return [n >> 16, (n >> 8) & 255, n & 255]
def dist(a, b): return sum(abs(x - y) for x, y in zip(a, b))

with sync_playwright() as p:
    logs = []
    pg, R = load(p, logs)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    print('version', R("VERSION"))
    f = J("{a:typeof dsAC3,b:typeof dsBody,n:typeof dsClipName,e:typeof dsClipEdge,on:dsAC3(),k:dsBody(),look:UI.dawLook||'audiolab'}")
    ok(f['a'] == f['b'] == f['n'] == f['e'] == 'function', 'the DS-A3 helpers exist', f)
    ok(f['on'] and abs(f['k'] - .42) < 1e-9, 'AudioLab look: AC3 on, body factor 0.42 (36 % gives 15 %)', f)
    for mode in ['dark', 'light']:
        R("pmSetOn(%s)" % ('true' if mode == 'light' else 'false')); pg.wait_for_timeout(1200)
        x = J(PIX); col = rgb(x['col'])
        ok(x['top'] == 14, mode + ': the 14 px top zone is kept (hit areas unchanged)', x['top'])
        ok(dist(x['edge'], col) < 90, mode + ': 2 px edge in the track colour', [x['edge'], col])
        ok(dist(x['band'], x['body']) < 40 and dist(x['band'], col) > 200, mode + ': no title band (the name zone is the body tint, not the colour)', [x['band'], x['body']])
        ok(sum(x['body']) < 240, mode + ': darker body', x['body'])
    R("pmSetOn(false)"); pg.wait_for_timeout(800)
    # before/after body: the opacity setting still changes the body
    b1 = J(PIX)['body']; R("UI.clipA=80;CLC.clear();dirty=true"); b2 = J(PIX)['body']; R("UI.clipA=36;CLC.clear();dirty=true")
    ok(sum(b2) > sum(b1) + 30, 'the clip opacity setting still works', [b1, b2])
    # glass engine list: an edge, no band
    gl = J("(()=>{const r=gleBuild(),cl=r.clips||r[1]||[];return{n:cl.length,band:cl.filter(q=>q.h===14).length,edge:cl.filter(q=>q.h===2).length}})()")
    ok(gl['band'] == 0 and gl['edge'] > 0, 'glass engine list: colour edges, no title bands', gl)
    # another look keeps its title bar
    R("UI.dawLook='fl';applyTheme()"); pg.wait_for_timeout(600)
    y = J(PIX); gl2 = J("(()=>{const r=gleBuild(),cl=r.clips||r[1]||[];return cl.filter(q=>q.h===14).length})()")
    ok(not J("dsAC3()") and dist(y['band'], y['body']) > 30 and gl2 > 0, 'FL style keeps its title bar (drawing and glass list)', [y['band'], y['body'], gl2])
    R("delete UI.dawLook;applyTheme()"); pg.wait_for_timeout(600)
    ok(J("dsAC3()"), 'back to AudioLab: AC3 again')
    # the name zone still selects and drags the clip
    h = J("""(()=>{V.ppb=25;V.x=128;V.y=0;clampV();selC=null;drawArr();const i=S.tracks.findIndex(t=>/^bass$/i.test(t.name)),t=S.tracks[i],c=t.clips.find(c=>c.start<=136&&c.start+c.len>136),G=clipGeom(i,c),a=arr.getBoundingClientRect();
      return{x:a.left+G.x+40,y:a.top+G.y+7,id:c.id,st:c.start}})()""")
    pg.mouse.click(h['x'], h['y']); pg.wait_for_timeout(300)
    ok(J("selC") == h['id'], 'a click on the name zone selects the clip', [J("selC"), h['id']])
    pg.mouse.move(h['x'], h['y']); pg.mouse.down(); pg.mouse.move(h['x'] + 60, h['y'], steps=6); pg.mouse.up(); pg.wait_for_timeout(300)
    st = J("(()=>{for(const t of S.tracks)for(const c of t.clips)if(c.id===%s)return c.start})()" % json.dumps(h['id']))
    ok(st != h['st'], 'dragging by the name zone moves the clip', [h['st'], st])
    R("undo()"); pg.wait_for_timeout(300)
    st2 = J("(()=>{for(const t of S.tracks)for(const c of t.clips)if(c.id===%s)return c.start})()" % json.dumps(h['id']))
    ok(st2 == h['st'], 'undo puts it back', st2)
    # muted clip keeps its label
    m = J("""(()=>{const t=S.tracks.find(t=>/^snare$/i.test(t.name)),c=t.clips[0];c.mute=true;CLC.clear();drawArr();c.mute=false;CLC.clear();dirty=true;return true})()""")
    ok(m, 'a muted clip draws')
    ok(not logs, 'no console errors', logs[:5])
    print(f'{N[0] - len(FAIL)} of {N[0]} checks passed'); sys.exit(1 if FAIL else 0)
