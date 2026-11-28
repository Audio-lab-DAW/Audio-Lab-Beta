"""The Devices button and the drum designers (task AF): python3 tools/ui-tests/taskAF.py [index.html] [out dir]
Fractals demo at 1600 x 1000, normal and Light mode:
- open: the track tabs and Master stand with nothing behind them (no strip, no blur), the Devices button is a fully rounded pill in the tab row,
  clear of the panel's edge; folded away: no tabs and no bar, only the pill, raised off the edge;
- the pill never overlaps a device (its coloured top included) while the devices are scrolled sideways and up and down, on every track and Master;
- the Clap designer has only dials and the Level fader like the Snare, Hat and Tom designers, and each designer's preset row is one line;
- the pill folds and opens the panel, tooltips on every control, no page errors. Screenshots (2x) of each state."""
import sys, os, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
FAIL = []
def ok(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: FAIL.append(m)
GEO = """(()=>{const T=document.getElementById('fxTitle'),cs=getComputedStyle(T),b=document.getElementById('fxHide').getBoundingClientRect(),bs=getComputedStyle(document.getElementById('fxHide')),fx=document.getElementById('fx').getBoundingClientRect(),
 tabs=[...document.querySelectorAll('#fxTitle .fxsc button')].filter(e=>e.getBoundingClientRect().width>0).length,
 tips=[...document.querySelectorAll('#fxTitle button,#fxHide')].filter(e=>e.offsetParent&&!(e.title||e.getAttribute('aria-label'))).length;
 return JSON.stringify({disp:cs.display,bg:cs.backgroundColor,bf:cs.backdropFilter||cs.webkitBackdropFilter||'none',sh:cs.boxShadow,bt:b.top,bb:b.bottom,bh:b.height,bl:b.left,br:b.right,rad:parseFloat(bs.borderTopLeftRadius),fxt:fx.top,fxr:fx.right,tabs,tips})})()"""
OVL = """(()=>{const fx=document.getElementById('fxin'),b=document.getElementById('fxHide').getBoundingClientRect();let worst=null,n=0;
 const xs=[],mx=fx.scrollWidth-fx.clientWidth,my=fx.scrollHeight-fx.clientHeight;for(let i=0;i<=12;i++)xs.push(Math.round(mx*i/12));
 for(const y of [0,Math.round(my/2),my])for(const x of xs){fx.scrollLeft=x;fx.scrollTop=y;
  for(const d of fx.querySelectorAll('.dev')){const r=d.getBoundingClientRect();if(!r.width)continue;n++;
   const ix=Math.min(r.right,b.right)-Math.max(r.left,b.left),iy=Math.min(r.bottom,b.bottom)-Math.max(r.top,b.top);if(ix>0&&iy>0)worst={x,y,dev:d.className,r:[r.left,r.top,r.right,r.bottom]}}}
 fx.scrollLeft=0;fx.scrollTop=0;return JSON.stringify({n,worst,mx,my})})()"""
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}, device_scale_factor=2); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:400]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404, body=b'')))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html'); pg.wait_for_timeout(7000)
    pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
    ok(not errs, 'no page errors on load ' + '; '.join(errs))
    R = lambda c: pg.evaluate("c=>window.AudioLab.run(c)", c)
    sel = lambda nm: R("(()=>{selectTrack(S.tracks.find(t=>t.name==='%s').id);return 1})()" % nm)
    sel('Clap'); pg.wait_for_timeout(500)
    for lite in (False, True):
        R("(()=>{UI.lite=%s;applyLite();if(!UI.lite)fxSet({blur:'copy'},true);return document.body.className})()" % ('true' if lite else 'false'))
        for hid in (False, True):
            R("(()=>{devHide(%s);return 1})()" % ('true' if hid else 'false')); pg.wait_for_timeout(600)
            g = json.loads(R(GEO)); tag = '%s, %s' % ('Light mode' if lite else 'normal', 'folded away' if hid else 'open')
            ok(g['rad'] >= g['bh'] / 2 - 0.5, '%s: the Devices button is a full pill (radius %.0f, height %.0f)' % (tag, g['rad'], g['bh']))
            if hid:
                ok(g['disp'] == 'none', '%s: no bar and no tabs, only the button (title %s)' % (tag, g['disp']))
                ok(g['bb'] <= g['fxt'] - 4, '%s: the button is raised off the edge (button bottom %.0f, edge %.0f)' % (tag, g['bb'], g['fxt']))
            else:
                ok(g['tabs'] > 0 and g['bg'] in ('rgba(0, 0, 0, 0)', 'transparent') and g['bf'] == 'none' and g['sh'] == 'none', '%s: tabs with nothing behind them (bg %s, blur %s, shadow %s, %d tabs)' % (tag, g['bg'], g['bf'], g['sh'][:30], g['tabs']))
                ok(g['bb'] <= g['fxt'] - 1, '%s: the button sits in the tab row, above the panel (button bottom %.0f, panel top %.0f)' % (tag, g['bb'], g['fxt']))
                ok(g['tips'] == 0, '%s: every control in the tab row has a tooltip' % tag)
            band = R("(()=>{const b=document.getElementById('fxband');return b?b.getBoundingClientRect().height:0})()")
            ok(band == 0, '%s: no blurred band behind the tabs (#fxband %s px high)' % (tag, band))
            y = max(0, g['fxt'] - 60)
            pg.screenshot(path=os.path.join(OUT, 'af_%s_%s_right.png' % ('light' if lite else 'normal', 'folded' if hid else 'open')), clip={'x': 1000, 'y': y, 'width': 600, 'height': 150})
            pg.screenshot(path=os.path.join(OUT, 'af_%s_%s_left.png' % ('light' if lite else 'normal', 'folded' if hid else 'open')), clip={'x': 0, 'y': y, 'width': 600, 'height': 150})
    R("(()=>{UI.lite=false;applyLite();devHide(false);return 1})()"); pg.wait_for_timeout(400)
    # the pill never covers a device while the devices scroll
    names = json.loads(R("JSON.stringify(S.tracks.filter(t=>t.kind!=='group').map(t=>t.name))"))
    bad = []
    for nm in names + ['__master']:
        if nm == '__master': R("(()=>{const b=document.querySelector('#fxTitle .fxmst');if(b&&!b.classList.contains('on'))b.click();return 1})()")
        else: sel(nm)
        pg.wait_for_timeout(250)
        o = json.loads(R(OVL))
        if o['worst']: bad.append((nm, o['worst']))
    ok(not bad, 'the button overlaps no device while scrolling, %d tracks and Master %s' % (len(names), json.dumps(bad[:2])))
    # a shorter panel (devices scroll up and down) and a device scrolled under the button's x range
    R("(()=>{document.getElementById('fx').style.height='200px';return 1})()"); pg.wait_for_timeout(400); sel('Clap'); pg.wait_for_timeout(300)
    o = json.loads(R(OVL)); ok(not o['worst'], 'short panel: no overlap (%s)' % json.dumps(o))
    R("(()=>{document.getElementById('fx').style.height='';return 1})()"); pg.wait_for_timeout(400)
    sel('Clap'); pg.wait_for_timeout(300)
    x = json.loads(R("(()=>{const fx=document.getElementById('fxin'),d=fx.querySelector('.pzd'),b=document.getElementById('fxHide').getBoundingClientRect(),r=d.getBoundingClientRect();fx.scrollLeft+=r.left-(b.left-80);return JSON.stringify(1)})()"))
    pg.wait_for_timeout(200)
    g = json.loads(R(GEO))
    pg.screenshot(path=os.path.join(OUT, 'af_clap_under_button.png'), clip={'x': 1000, 'y': g['fxt'] - 40, 'width': 600, 'height': 120})
    R("(()=>{document.getElementById('fxin').scrollLeft=0;return 1})()")
    # the drum designers
    for nm in ('Clap', 'Snare', 'Hat', 'Toms'):
        sel(nm); pg.wait_for_timeout(500)
        d = json.loads(R("""(()=>{const D=document.querySelector('#fxin .dev.pzd'),S=D.querySelector(':scope>.devb>.dfs'),row=S.querySelector('.dspr'),r=D.getBoundingClientRect();
          const out=[...D.querySelectorAll('[data-c],button')].filter(e=>{const q=e.getBoundingClientRect();return q.width&&(q.left<r.left-1||q.right>r.right+1||q.top<r.top-1||q.bottom>r.bottom+1)}).length;
          const kn=S.querySelectorAll('.pg-kn [data-c]').length,hb=S.querySelectorAll('.pg-hb [data-c]').length,lv=[...S.querySelectorAll('.pg-lv [data-c]')].map(e=>CT.get(e.dataset.c).label);
          const tips=[...D.querySelectorAll('button,[data-c],select')].filter(e=>e.offsetParent&&!(e.title||e.getAttribute('aria-label')||(e.closest('[title]')&&D.contains(e.closest('[title]'))))).length;
          return JSON.stringify({kn,hb,lv,rowh:row?row.offsetHeight:0,out,tips,y:r.top,x:r.left,w:r.width,h:r.height})})()"""))
        ok(d['hb'] == 0 and d['lv'] == ['Level'] and d['rowh'] <= 26 and d['out'] == 0, '%s designer: %d dials, no bars, only Level as a fader (%s), preset row one line (%d px), nothing outside' % (nm, d['kn'], d['lv'], d['rowh']))
        ok(d['tips'] == 0, '%s designer: tooltips on every control' % nm)
        pg.screenshot(path=os.path.join(OUT, 'af_designer_%s.png' % nm.lower()), clip={'x': d['x'] - 4, 'y': d['y'] - 30, 'width': d['w'] + 8, 'height': d['h'] + 34})
    # the button works
    pg.click('#fxHide'); pg.wait_for_timeout(400); h1 = R("UI.fxHide"); pg.click('#fxHide'); pg.wait_for_timeout(400); h2 = R("UI.fxHide")
    ok(h1 is True and h2 is False, 'the Devices button folds the panel away and brings it back')
    ok(not errs, 'no page errors ' + '; '.join(errs[:3]))
    b.close()
print('\n%d failures' % len(FAIL)); sys.exit(1 if FAIL else 0)
