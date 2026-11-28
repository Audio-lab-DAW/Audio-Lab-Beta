import os, sys, json, time
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
INDEX = os.environ.get('ALAB_INDEX', '/home/claude/audio-lab-beta/index.html')
GPU_ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist",
            "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--enable-zero-copy",
            "--disable-frame-rate-limit", "--disable-gpu-vsync"]
# On a real machine: ALAB_HEADED=1 ALAB_ARGS="" python3 bench.py   (keeps vsync, uses the real GPU)
if os.environ.get('ALAB_CAPPED'): GPU_ARGS = [a for a in GPU_ARGS if a not in ('--disable-frame-rate-limit', '--disable-gpu-vsync')]
if os.environ.get('ALAB_ARGS') is not None:
    GPU_ARGS = ["--autoplay-policy=no-user-gesture-required"] + os.environ['ALAB_ARGS'].split()

LIST_GLASS = r"""() => {
  const out=[]; const vw=innerWidth, vh=innerHeight;
  for(const el of document.querySelectorAll('body *')){
    const cs=getComputedStyle(el); const bf=cs.backdropFilter||cs.webkitBackdropFilter;
    if(!bf||bf==='none') continue;
    const r=el.getBoundingClientRect();
    const x0=Math.max(0,r.left),y0=Math.max(0,r.top),x1=Math.min(vw,r.right),y1=Math.min(vh,r.bottom);
    const vis=cs.display!=='none'&&cs.visibility!=='hidden'&&+cs.opacity>0.01&&el.offsetParent!==null||cs.position==='fixed';
    const area=Math.max(0,x1-x0)*Math.max(0,y1-y0);
    let hid=false; for(let p=el;p;p=p.parentElement){const c=getComputedStyle(p); if(c.display==='none'||c.visibility==='hidden'||+c.opacity<0.01){hid=true;break}}
    if(area<1||hid) continue;
    const m=/blur\(([\d.]+)px\)/.exec(bf);
    out.push({sel:(el.id?'#'+el.id:el.tagName.toLowerCase()+'.'+[...el.classList].join('.')), id:el.id, cls:[...el.classList].join(' '),
      x:Math.round(x0),y:Math.round(y0),w:Math.round(x1-x0),h:Math.round(y1-y0),area:Math.round(area),
      lens:/url\(/.test(bf), blur:m?+m[1]:0, bf:bf.slice(0,90), z:cs.zIndex, pos:cs.position,
      canv:el.querySelectorAll('canvas').length});
  }
  out.sort((a,b)=>b.area-a.area); return out; }"""

def launch(p, dsf=1, w=1600, h=1000):
    b = p.chromium.launch(headless=not os.environ.get('ALAB_HEADED'), args=GPU_ARGS)
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dsf)
    pg = ctx.new_page()
    src = open(INDEX, encoding='utf-8').read()
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=src) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
    pg.goto('https://app.test/index.html')
    pg.wait_for_function("() => window.AudioLab && window.AudioLab.version", timeout=90000)
    pg.wait_for_timeout(2500)
    return b, pg

def run(pg, code):
    return pg.evaluate("c => AudioLab.run(c)", code)
