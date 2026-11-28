#!/usr/bin/env python3
"""Task GS4 (glass step 4): the device panel and the transport float, the transport gets the lens, the bottom-left corner is engine glass.
   python3 tools/ui-tests/taskGS4.py [index.html] [out dir]
At the user's size (2194 x 1139 CSS px at 1.75x), Fractals open, Open hat selected (Modulators, Open hat strip, Hat designer, as in the user's screenshots).
The cloud machine has no graphics card (SwiftShader): correctness only.
Pixel check, per case: A = the page with the panels' own elements made transparent (what is behind them: the sharp layers plus the engine's glass);
B = the same with the engine canvas hidden too (only the sharp layers). Under the glass A must be frosted (no fine detail: nothing sharp lies on top of
the engine's face) and differ from B (the engine draws there); outside the glass A must equal B (nothing blurred where there is no glass)."""
import sys, os, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageStat
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'gs4-out'
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)
W, H, DSF = 2194, 1139, 1.75
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS); ctx = b.new_context(viewport={'width': W, 'height': H}, device_scale_factor=DSF); pg = ctx.new_page(); logs = []
    def con(m):
        if m.type == 'error' and 'fetching the script' not in m.text: logs.append(m.text[:300])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(4000)
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R("pmSetOn(false)"); R("openDemoFractals()"); pg.wait_for_timeout(7000); pg.evaluate("()=>{const s=document.getElementById('liteNote');if(s)s.remove()}")
    R("(()=>{const t=S.tracks.find(t=>/open hat/i.test(t.name));selectTrack(t.id)})()"); pg.wait_for_timeout(1500)
    v = R("VERSION"); new = R("typeof GS4!=='undefined'"); rad = R("GS4.rad") if new else 0
    print('version', v)
    # ---- 1. engine and panels ----
    s = json.loads(R("JSON.stringify({v:AudioLabGlass.version,lv:GLE.lv,tr:GLE.g.panelInfo('tr'),fx:GLE.g.panelInfo('fxglass'),hg:GLE.g.panelInfo('hglass'),info:GLE.g.info})"))
    ok(s['lv'] == 'glass' and s['info']['lens'] == 'wide' and s['info']['blur'] == 'light', 'Full effects: Glass, lens Wide, blur Light (defaults)', [s['lv'], s['info']['lens'], s['info']['blur']])
    if new:
        ok(s['v'] == '2.4.0', 'engine 2.4.0 (lensX, lensY per panel)', s['v'])
        ok(s['tr'] and s['tr']['edges'] == 'trbl' and s['tr']['band'] > 5, 'the transport has the lens on every edge', s['tr'])
        ok(s['fx'] and s['fx']['edges'] == 'trbl' and s['fx']['lensRadius'] >= 12, 'the device panel bends on every edge and its lens follows the rounded corners', s['fx'])
        ok(s['tr']['lensY'] > 1 and s['fx']['lensY'] > 1 and s['tr']['lensY'] <= 1.5 and s['fx']['lensY'] <= 1.5 and s['hg'].get('lensY', 1) == 1, 'a little extra vertical bend on the transport and the device panel, the header glass as before', [s['tr']['lensY'], s['fx']['lensY'], s['hg'].get('lensY')])
        g = json.loads(R("""JSON.stringify((()=>{const q=i=>{const r=document.getElementById(i).getBoundingClientRect();return[r.left,r.top,r.right,r.bottom]},cs=i=>getComputedStyle(document.getElementById(i));
          return{fg:q('fxglass'),tr:q('tr'),fxin:q('fxin'),tab:(()=>{const t=document.querySelector('#fxTitle button, #fxTitle .fxsw');return t?t.getBoundingClientRect().left:null})(),rfg:cs('fxglass').borderTopLeftRadius,rtr:cs('tr').borderTopLeftRadius,rin:cs('fxin').borderTopLeftRadius,ovf:cs('fxin').overflowX,GS4:{ins:GS4.ins,rad:GS4.rad,gap:GS4.gap,lensY:GS4.lensY}}})())"""))
        ins, rad, gap = g['GS4']['ins'], g['GS4']['rad'], g['GS4']['gap']
        ok(abs(g['fg'][0] - ins) < .6 and abs(W - g['fg'][2] - ins) < .6 and abs(g['tr'][0] - ins) < .6 and abs(W - g['tr'][2] - ins) < .6, 'device panel and transport float %d px in from both window edges' % ins, [g['fg'], g['tr']])
        ok(g['rfg'] == '%dpx' % rad and g['rtr'] == '%dpx' % rad and g['rin'] == '%dpx' % rad, 'rounded corners (%d px) on the device glass, the transport and the device row' % rad, [g['rfg'], g['rtr'], g['rin']])
        ok(abs(g['tr'][1] - g['fg'][3] - gap) < 1.1, 'a %d px gap between the device panel and the transport' % gap, g['tr'][1] - g['fg'][3])
        ok(g['fxin'][0] >= g['fg'][0] - .5 and g['fxin'][2] <= g['fg'][2] + .5 and g['fxin'][3] <= g['fg'][3] + 2.5 and g['ovf'] in ('auto', 'scroll'), 'the device row scrolls inside the glass (its clip is the glass shape)', [g['fxin'], g['fg']])
        ok(g['tab'] is None or abs(g['tab'] - ins) < 6, 'the gap matches the tab band above', g['tab'])
        ly = json.loads(R("JSON.stringify({arr:arr.style.clipPath,ph:(document.getElementById('arrPhW')||{style:{}}).style.clipPath||'',col:GB.col?GB.col.style.display:'none',z:getComputedStyle(document.getElementById('glassCv')).zIndex,hz:getComputedStyle(document.getElementById('hdrcol')).zIndex,hdr:document.getElementById('hdrclip').style.clipPath.slice(0,5),order:[...document.getElementById('main').children].map(e=>e.id)})"))
        ok(ly['arr'] == '' and ly['ph'] == '' and ly['col'] == 'none', 'nothing is cut out of the arrangement canvas and its playhead layer, no header column copy (the engine canvas lies above them)', ly)
        ok(ly['z'] == '1' and ly['hz'] == '2' and ly['hdr'] == 'path(', 'the engine canvas is above the arrangement (z-index 1) and under the header column (2); the header rows are cut under the glass', [ly['z'], ly['hz'], ly['hdr']])
    # ---- 2. pixel checks at the user's size, device row left, middle, right; Glass and Light ----
    HIDE = "(()=>{for(const i of['fx','fxglass','tr'])document.getElementById(i).style.opacity='0';const c=document.getElementById('dcBtn');})()"
    SHOW = "(()=>{for(const i of['fx','fxglass','tr'])document.getElementById(i).style.opacity=''})()"
    def shot(name, clip):
        pg.screenshot(path=os.path.join(OUT, name), clip=clip); return Image.open(os.path.join(OUT, name)).convert('RGB')
    def region(im, box, clip):  # box in CSS px of the page -> crop of an image taken with clip
        x0, y0, x1, y1 = box; k = DSF
        return im.crop((round((x0 - clip['x']) * k), round((y0 - clip['y']) * k), round((x1 - clip['x']) * k), round((y1 - clip['y']) * k)))
    def detail(im):  # mean difference between neighbouring pixels along rows (sharp content is high, a flat or frosted area low)
        a = ImageChops.difference(im.crop((1, 0, im.width, im.height)), im.crop((0, 0, im.width - 1, im.height)))
        return sum(ImageStat.Stat(a).mean) / 3
    def maxdiff(a, b): return max(e[1] for e in ImageChops.difference(a, b).getextrema())
    def case(tag):
        pg.wait_for_timeout(700)
        R("(()=>{GB.lt=0;gbCopy();dirty=true})()"); pg.wait_for_timeout(700)
        geo = json.loads(R("JSON.stringify((()=>{const q=i=>{const r=document.getElementById(i).getBoundingClientRect();return[r.left,r.top,r.right,r.bottom]};return{fg:q('fxglass'),tr:q('tr'),hdr:q('hdrclip'),hasHdr:!!document.querySelector('#hdrin .hdr')}})())"))
        clip = {'x': 0, 'y': geo['fg'][1] - 30, 'width': 700, 'height': H - (geo['fg'][1] - 30)}
        full = shot('%s-look.png' % tag, clip)
        shot('%s-look-right.png' % tag, {'x': W - 700, 'y': clip['y'], 'width': 700, 'height': clip['height']})
        R(HIDE); pg.wait_for_timeout(400); A = shot('%s-A.png' % tag, clip)
        R("document.getElementById('glassCv').style.visibility='hidden'"); pg.wait_for_timeout(400); B = shot('%s-B.png' % tag, clip)
        R("document.getElementById('glassCv').style.visibility=''"); R(SHOW); pg.wait_for_timeout(300)
        fg, tr = geo['fg'], geo['tr']
        # under the glass, left part (where the header rows run behind it), away from the rounded corners
        under = [(fg[0] + 3, fg[1] + rad + 2, 200, fg[3] - rad - 2), (tr[0] + rad + 2, tr[1] + 3, 200, tr[3] - 3)]
        uB = [detail(region(B, u, clip)) for u in under]; uA = [detail(region(A, u, clip)) for u in under]
        ok(max(uA) < 0.6, '%s: nothing sharp under the device glass and the transport on the left (the header rows are cut away there, the engine\'s face covers the arrangement)' % tag, [round(x, 3) for x in uA])
        ok(min(maxdiff(region(A, u, clip), region(B, u, clip)) for u in under) > 8, '%s: under that glass the engine draws (frost and lens)' % tag)
        # outside the glass: the gap at the left window edge, the gap between the panels, the arrangement above
        outs = [(0, fg[1] + 2, fg[0] - 1, tr[3] - 2), (fg[0] + rad + 4, fg[3] + 1.5, 600, tr[1] - 1.5), (230, fg[1] - 24, 600, fg[1] - 2)]
        outs = [o for o in outs if o[2] - o[0] >= 1 and o[3] - o[1] >= 1]
        od = [maxdiff(region(A, o, clip), region(B, o, clip)) for o in outs]
        ok(max(od) <= 2, '%s: nothing blurred outside the glass (left edge gap, the gap between the panels, above the panel)' % tag, od)
        if fg[0] >= 2: ok(detail(region(B, outs[0], clip)) > 0.3 if geo['hasHdr'] else True, '%s: the left edge gap shows the header rows sharp' % tag, round(detail(region(B, outs[0], clip)), 3))
        # the rounded corner: its cut-out shows the sharp layers, not glass
        cx, cy = fg[0] + 1.5, fg[1] + 1.5
        ok(maxdiff(region(A, (cx - 1, cy - 1, cx, cy), clip), region(B, (cx - 1, cy - 1, cx, cy), clip)) <= 2, '%s: the device panel\'s top left corner cut-out is not glass' % tag)
        return geo
    if not new:   # before task GS4: only the pixel check, to show what the user saw
        R("fxin.scrollLeft=0"); case('before-glass-left'); R("fxin.scrollLeft=fxin.scrollWidth"); case('before-glass-right')
    if new:
        R("fxin.scrollLeft=0"); case('glass-left')
        R("fxin.scrollLeft=Math.round((fxin.scrollWidth-fxin.clientWidth)/2)"); case('glass-middle')
        R("fxin.scrollLeft=fxin.scrollWidth"); case('glass-right')
        # scrolling the device row does not move the glass shape and the engine panel
        a = R("JSON.stringify([document.getElementById('hdrclip').style.clipPath,JSON.stringify(GS4.holes),GLE.g.panelInfo('fxglass').edges])")
        R("fxin.scrollLeft=0"); pg.wait_for_timeout(500); R("(()=>{GB.lt=0;gbCopy()})()"); pg.wait_for_timeout(300)
        b2 = R("JSON.stringify([document.getElementById('hdrclip').style.clipPath,JSON.stringify(GS4.holes),GLE.g.panelInfo('fxglass').edges])")
        ok(a == b2, 'scrolling the device row leaves the glass shape, the cut and the lens as they are')
        # devices are clipped at the rounded ends: a point in the top left corner cut-out does not hit a device
        hit = R("(()=>{fxin.scrollLeft=40;const r=document.getElementById('fxglass').getBoundingClientRect();const e=document.elementFromPoint(r.left+1.5,r.top+1.5);return e?(e.closest('#fxin')?'device':e.id||e.tagName):'none'})()")
        ok(hit != 'device', 'a device scrolled to the left end does not show in the rounded corner', hit)
        R("fxin.scrollLeft=0")
        # Light level: no lens, the same cut
        R("(()=>{UI.gl={...(UI.gl||{}),lv:'light'};gleApply()})()"); pg.wait_for_timeout(1200)
        ok(R("GLE.lv") == 'light' and R("GLE.g.panelInfo('tr').band") == 0, 'level Light: glass without lens')
        case('light-left')
        R("(()=>{UI.gl={...(UI.gl||{}),lv:'solid'};gleApply()})()"); pg.wait_for_timeout(1200)
        so = json.loads(R("JSON.stringify([GLE.on,arr.style.clipPath,document.getElementById('hdrclip').style.clipPath,document.getElementById('tr').className,document.getElementById('fxglass').className])"))
        ok(so[0] is False and so[1] == '' and so[2] == '', 'level Solid: no engine, nothing cut (the solid panels cover what is behind them)', so)
        shot('solid-look.png', {'x': 0, 'y': 650, 'width': 700, 'height': H - 650})
        R("(()=>{UI.gl={...(UI.gl||{}),lv:null};gleApply()})()"); pg.wait_for_timeout(1200)
        ok(R("GLE.lv") == 'glass' and R("document.getElementById('hdrclip').style.clipPath.startsWith('path(')"), 'back to Glass, the header rows are cut under the glass again')
        # a window over the floating panels sees them with their corners (glass never samples glass: the flat-picture route)
        R("openMixer()"); pg.wait_for_timeout(1500)
        fl = R("JSON.stringify((GLF.L||[]).filter(Boolean).map(L=>[...L.flats.entries()].filter(([k])=>k==='d:tr'||k==='d:fxglass').map(([k,v])=>k)))")
        ok('d:tr' in fl, 'the mixer\'s glass gets the transport as a flat picture', fl)
        R("openMixer()")
        pg.wait_for_timeout(800)
    # ---- 3. rules ----
    bf = R("[...document.querySelectorAll('*')].filter(e=>{const c=getComputedStyle(e);return c.backdropFilter&&c.backdropFilter!=='none'}).length")
    ok(bf == 0, 'backdrop-filter nowhere', bf)
    st = json.loads(R("JSON.stringify(GLE.g.stats)"))
    ok(st['uploads'] == 0, 'no canvas uploads on the scene path', st['uploads'])
    s0 = R("GLE.g.stats.sceneSends")
    R("(()=>{let i=0;const f=()=>{V.x+=0.5;dirty=true;if(++i<40)requestAnimationFrame(f)};f()})()"); pg.wait_for_timeout(2500)
    ok(R("GLE.g.stats.sceneSends") == s0, 'scrolling sideways sends no rectangle list', [s0, R("GLE.g.stats.sceneSends")])
    ok(not logs, 'no console errors', logs[:5])
    b.close()
print('\n%d checks, %d failed' % (N[0], len(FAIL)))
for f in FAIL: print('  FAIL', f)
sys.exit(1 if FAIL else 0)
