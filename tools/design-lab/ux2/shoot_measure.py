#!/usr/bin/env python3
"""Task UX2 (long sessions research): headless screenshots of today's app at the user's size and the raw measurements.
   python3 -m http.server 8765 --bind 127.0.0.1   (in the repo, first)
   python3 tools/design-lab/ux2/shoot_measure.py [out dir]
Reads index.html only; changes nothing in the app.
The user's screen: Samsung Odyssey OLED G8 (G80SD), 32 inch 3840x2160, macOS 'looks like' 2194x1139 points at 1.75x (window size used here).
Writes, per mode (dark = AudioLab theme with full glass; lite = Light mode on; bright = the Pro Tools style theme, the only bright arrangement):
  <mode>-arr.png, <mode>-mix.png  screenshots at 1.75x
  text-<mode>.json                 every visible text element: colour, size, weight, rect, and the background sampled from the screenshot
  motion.json                      share of screen pixels that change between frames while playing and while stopped
"""
import sys, os, json
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image
import io

OUT = sys.argv[1] if len(sys.argv) > 1 else 'ux2-out'
os.makedirs(OUT, exist_ok=True)
URL = os.environ.get('UX2_URL', 'http://127.0.0.1:8765/index.html')
W, H, D = 2194, 1139, 1.75
ARGS = ["--autoplay-policy=no-user-gesture-required", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-proxy-server"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"

TEXTJS = r"""()=>{const out=[];const z=parseFloat(getComputedStyle(document.documentElement).zoom)||1;
 const walk=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;const seen=new Set();
 while(n=walk.nextNode()){const t=n.textContent.trim();if(!t)continue;const el=n.parentElement;if(!el||seen.has(el))continue;seen.add(el);
  const cs=getComputedStyle(el);if(cs.visibility==='hidden'||cs.display==='none'||+cs.opacity===0)continue;
  const r=document.createRange();r.selectNodeContents(n);const b=r.getBoundingClientRect();if(b.width<2||b.height<2)continue;
  if(b.right<0||b.bottom<0||b.left>innerWidth||b.top>innerHeight)continue;
  let o=1,e=el;while(e&&e!==document.body){o*=+getComputedStyle(e).opacity;e=e.parentElement}
  if(o<.05)continue;
  /* the element on top at the text's middle must be this element or inside it (else the text is covered) */
  const top=document.elementFromPoint(Math.min(innerWidth-1,b.left+b.width/2),Math.min(innerHeight-1,b.top+b.height/2));
  if(top&&!(top===el||el.contains(top)||top.contains(el)))continue;
  out.push({t:t.slice(0,40),tag:el.tagName,id:el.id,cls:String(el.className).slice(0,40),c:cs.color,fs:parseFloat(cs.fontSize)*z,fw:+cs.fontWeight,ff:cs.fontFamily.split(',')[0],o,
   x:b.left,y:b.top,w:b.width,h:b.height})}
 return out}"""

def png(pg, scale=None):
    return np.asarray(Image.open(io.BytesIO(pg.screenshot())).convert('RGB'))

def sample_bg(img, it):
    """background behind a text run: the most common colour in a ring just around the text box (device pixels)"""
    x0, y0 = int(max(0, (it['x'] - 3) * D)), int(max(0, (it['y'] - 2) * D))
    x1, y1 = int(min(img.shape[1] - 1, (it['x'] + it['w'] + 3) * D)), int(min(img.shape[0] - 1, (it['y'] + it['h'] + 2) * D))
    if x1 - x0 < 3 or y1 - y0 < 3: return None
    reg = img[y0:y1, x0:x1].reshape(-1, 3)
    edge = np.concatenate([img[y0, x0:x1], img[y1, x0:x1], img[y0:y1, x0], img[y0:y1, x1]])
    q = (edge // 4).astype(np.int32)
    keys = q[:, 0] * 65536 + q[:, 1] * 256 + q[:, 2]
    vals, cnt = np.unique(keys, return_counts=True)
    k = vals[cnt.argmax()]
    m = keys == k
    return [int(v) for v in edge[m].mean(axis=0)]

def motion(pg, n=24, gap=125, thr=12):
    frames = []
    for i in range(n):
        frames.append(png(pg).astype(np.int16)); pg.wait_for_timeout(gap)
    shares, union = [], np.zeros(frames[0].shape[:2], bool)
    for a, b in zip(frames, frames[1:]):
        d = np.abs(a - b).max(axis=2) > thr
        shares.append(float(d.mean())); union |= d
    return {'mean_changed_share_per_step': float(np.mean(shares)), 'max': float(np.max(shares)), 'union_share': float(union.mean()), 'step_ms': gap,
            'union_mask': union}

with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': W, 'height': H}, device_scale_factor=D)
    pg = ctx.new_page()
    pg.route('**/fonts.googleapis.com/**', lambda r: r.abort()); pg.route('**/fonts.gstatic.com/**', lambda r: r.abort())
    pg.add_init_script("if(!sessionStorage.getItem('u2')){sessionStorage.setItem('u2','1');" + INIT + "}")
    pg.goto(URL, wait_until='commit'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=180000); pg.wait_for_timeout(5000)
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    clean = "()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}"
    pg.evaluate(clean); R("openDemoFractals()"); pg.wait_for_timeout(8000); pg.evaluate(clean)
    print('version', pg.evaluate("()=>AudioLab.version"), flush=True)
    meta = {'version': pg.evaluate("()=>AudioLab.version"), 'viewport': [W, H], 'dpr': D}

    def mixclose():
        R("const w=document.getElementById('mixWin');if(w)w.remove()"); pg.wait_for_timeout(300)

    def mode(name):
        pg.evaluate(clean); R("closeMenu();for(const m of document.querySelectorAll('.modal'))m.hidden=true"); pg.wait_for_timeout(1500)
        pg.screenshot(path=f'{OUT}/{name}-arr.png')
        img = png(pg); items = pg.evaluate(TEXTJS)
        for it in items: it['bg'] = sample_bg(img, it)
        R("openMixer()"); pg.wait_for_timeout(2500)
        pg.screenshot(path=f'{OUT}/{name}-mix.png')
        img2 = png(pg); items2 = pg.evaluate(TEXTJS)
        for it in items2: it['bg'] = sample_bg(img2, it); it['view'] = 'mixer'
        mixclose()
        pg.wait_for_timeout(800)
        json.dump(items + items2, open(f'{OUT}/text-{name}.json', 'w'))
        print(name, len(items), len(items2), flush=True)

    mode('dark')
    # motion while stopped (ambient), then while playing
    mo = {}
    m0 = motion(pg); Image.fromarray((m0.pop('union_mask') * 255).astype(np.uint8)).save(f'{OUT}/motion-stopped.png'); mo['stopped'] = m0
    pg.click('#bPlay'); pg.wait_for_timeout(2500)
    m1 = motion(pg); Image.fromarray((m1.pop('union_mask') * 255).astype(np.uint8)).save(f'{OUT}/motion-playing.png'); mo['playing'] = m1
    pg.screenshot(path=f'{OUT}/dark-arr-playing.png')
    R("openMixer()"); pg.wait_for_timeout(2500)
    m2 = motion(pg); Image.fromarray((m2.pop('union_mask') * 255).astype(np.uint8)).save(f'{OUT}/motion-playing-mixer.png'); mo['playing_mixer'] = m2
    pg.screenshot(path=f'{OUT}/dark-mix-playing.png')
    mixclose()
    pg.click('#bPlay'); pg.wait_for_timeout(800)
    # Light mode
    R("UI.lite=true;UI.liteMan=true;saveUI();applyLite()"); pg.wait_for_timeout(2500)
    mode('lite')
    pg.click('#bPlay'); pg.wait_for_timeout(2500)
    m3 = motion(pg); Image.fromarray((m3.pop('union_mask') * 255).astype(np.uint8)).save(f'{OUT}/motion-playing-lite.png'); mo['playing_lite'] = m3
    pg.click('#bPlay'); pg.wait_for_timeout(800)
    R("UI.lite=false;UI.liteMan=false;saveUI();applyLite()"); pg.wait_for_timeout(1500)
    # the bright arrangement (Pro Tools style), the nearest thing to a light theme
    R("thPick('protools')"); pg.wait_for_timeout(2000)
    mode('bright')
    R("thPick('audiolab')")
    json.dump({'meta': meta, 'motion': mo}, open(f'{OUT}/motion.json', 'w'), indent=1)
    print(json.dumps(mo, indent=1))
    b.close()
