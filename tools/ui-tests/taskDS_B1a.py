#!/usr/bin/env python3
"""Task DS-B1a (design round 2, B3 with BR2 and BP1): the catalogue browser with a measured preview.
   python3 tools/ui-tests/taskDS_B1a.py [index.html] [--shots OUTDIR]
At the user's size (2194 x 1139 CSS px at 1.75x) with Fractals, Dark (glass) and Light. SwiftShader: correctness only.
Checks: the catalogue behind openBrowser, openFxBrowser and Change; categories with counts; search (names, kinds, presets);
arrow keys choose and play; the preview's waveform (rendered offline once, cached), time scale and scrub line; presets with
left and right; Enter adds, uses and keeps; Escape in Change puts the old sound back; Cards and List; other looks keep
today's browser; no console errors."""
# for: task DS-B1a (lane A)
import sys, json, os
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'index.html'
SHOTS = sys.argv[sys.argv.index('--shots') + 1] if '--shots' in sys.argv else None
SRC = open(F, encoding='utf-8').read()
if 'task DS-B1a (lane A' not in SRC:
    print('DS-B1a is not in this index.html yet: nothing to test'); sys.exit(0)
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)

WAVEPX = r"""(()=>{const c=$('#dsbWv');if(!c)return null;const g=c.getContext('2d'),d=g.getImageData(0,0,c.width,Math.round(c.height*.8)).data;let lit=0,n=0;for(let i=0;i<d.length;i+=4){n++;if(d[i]>120&&d[i+1]>120&&d[i+2]>120)lit++}return lit/n})()"""

with sync_playwright() as p:
    logs = []
    ctx = p.chromium.launch(args=ARGS).new_context(viewport={'width': 2194, 'height': 1139}, device_scale_factor=1.75); pg = ctx.new_page()
    pg.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text else None)
    pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    W = pg.wait_for_timeout; K = pg.keyboard
    R("pmSetOn(false)"); R("openDemoFractals()"); W(6000)
    print('version', R("VERSION"))
    f = J("[typeof dsB1Cat,typeof dsB1Render,typeof dsB1List,typeof dsB1PvSync,typeof dsB1Wave,typeof dsB1WaveDraw,typeof dsB1Scrub,typeof dsB1T0,typeof dsB1PreSet,typeof dsB1Step]")
    ok(all(x == 'function' for x in f), 'the DS-B1a helpers exist', f)
    n0 = R("S.tracks.length")

    # 1. Instrument Browser: the catalogue
    R("openBrowser(null);1"); W(900)
    c = J("{cat:!!document.querySelector('#ibPlane.dsbcat'),rows:document.querySelectorAll('#dsbRows .dsbr').length,items:dsB1Items().length,side:[...document.querySelectorAll('#dsbSide [data-dsc]')].map(b=>b.textContent),focus:document.activeElement&&document.activeElement.id,tiles:document.querySelectorAll('#ibPlane .ibd').length,title:$('#ibT').textContent}")
    ok(c['cat'] and c['tiles'] == 0, 'Instrument Browser opens as the catalogue (no live cards)', c['title'])
    ok(c['rows'] == c['items'] and c['rows'] >= 15, 'one row per instrument', [c['rows'], c['items']])
    ok(c['side'][0].startswith('All') and len(c['side']) == 1 + J("IBG.length"), 'categories with counts', c['side'][:3])
    ok(c['focus'] == 'dsbQ', 'the search field has the focus', c['focus'])
    tg = J("[...document.querySelectorAll('#dsbRows .dsbr')].map(r=>r.querySelectorAll('.dsbtg i').length)")
    ok(max(tg) <= 3 and sum(1 for x in tg if x) >= 8, 'tag colours on the rows, at most three', tg)
    ok(J("document.querySelector('#dsbPv .dsbemp')!==null"), 'the preview asks to choose a sound')
    if SHOTS: os.makedirs(SHOTS, exist_ok=True)

    # 2. search
    K.type('bass'); W(300)
    s = J("{n:document.querySelectorAll('#dsbRows .dsbr').length,k:[...document.querySelectorAll('#dsbRows .dsbr')].map(r=>r.dataset.k),all:$('#dsbSide [data-dsc=\"-1\"] small').textContent}")
    ok(0 < s['n'] < c['rows'] and 'sub' in s['k'] and s['all'] == str(s['n']), 'search "bass" narrows the list and the counts', s)
    K.press('Escape'); W(200)
    ok(J("document.querySelectorAll('#dsbRows .dsbr').length") == c['rows'] and J("$('#ib').hidden") is False, 'Escape in the search field clears it first')
    R("(()=>{const q=$('#dsbQ');q.value='zzqq';q.dispatchEvent(new Event('input',{bubbles:true}))})()"); W(200)
    ok(J("!!document.querySelector('#dsbRows .dsbnone')"), 'nothing found says so')
    R("(()=>{const q=$('#dsbQ');q.value='';q.dispatchEvent(new Event('input',{bubbles:true}))})()"); W(200)
    R("document.querySelector('#dsbSide [data-dsc=\"2\"]').click()"); W(200)
    cat = J("{n:document.querySelectorAll('#dsbRows .dsbr').length,want:IBG[2][2].filter(k=>PRESETS[k]).length}")
    ok(cat['n'] == cat['want'], 'a category shows only its devices', cat)
    R("document.querySelector('#dsbSide [data-dsc=\"-1\"]').click()"); W(200)

    # 3. arrows choose and play; the preview side
    R("$('#dsbQ').focus()"); K.press('ArrowDown'); W(400)
    a = J("{sel:ib.sel,first:document.querySelector('#dsbRows .dsbr').dataset.k,ph:!!IBPH,live:!!document.querySelector('#dsbPv .dsblv #ibLive'),name:$('#dsbPv .dsbph b').textContent,focus:document.activeElement.id}")
    ok(a['sel'] == a['first'] and a['ph'], 'Down chooses the first row and plays it', a)
    ok(a['live'] and a['focus'] == 'dsbQ', 'the preview holds the one live device; the focus stays in search', a)
    K.press('ArrowDown'); W(250); K.press('ArrowDown'); W(250); K.press('ArrowUp'); W(300)
    ok(J("ib.sel===document.querySelectorAll('#dsbRows .dsbr')[1].dataset.k&&document.querySelectorAll('#dsbRows .dsbr.on').length===1"), 'Down, Down, Up lands on the second row, one row lit')
    R("document.querySelector('#dsbRows .dsbr[data-k=\"plant\"]').click()"); W(4500)
    wv = J("{cur:DSB.cur&&{pk:!!DSB.cur.pk,peak:DSB.cur.peak,err:!!DSB.cur.err},info:$('#dsbInfo').textContent,n:DSB.wv.size}")
    ok(wv['cur'] and wv['cur']['pk'] and wv['cur']['peak'] > 0.001, 'the waveform of the preview is measured (offline)', wv)
    ok('BPM' in wv['info'] and ' s' in wv['info'] and 'dBFS' in wv['info'] and 'Key A minor' in wv['info'], 'key, tempo, length and peak read-out', wv['info'])
    lit = J(WAVEPX)
    ok(lit is not None and lit > 0.04, 'the waveform is drawn', lit)
    t0 = R("performance.now()"); R("dsB1WaveSoon()"); W(600)
    ok(J("DSB.wv.size") == wv['n'], 'the same sound again comes from the cache', J("DSB.wv.size"))
    R("ibPlayPhrase()"); W(700)
    sc = J("{ph:!!DSB.ph,raf:!!DSB.raf}")
    ok(sc['ph'], 'the scrub line runs while the preview plays', sc)
    W(int(J("dsB1Dur()") * 1000) + 600)
    ok(J("!DSB.ph&&!DSB.raf"), 'and stops when it ends (nothing per frame at rest)')
    pr = J("{n:document.querySelectorAll('#dsbPre [data-dsp]').length,cur:dsB1PreCur()}")
    ok(pr['n'] >= 3, 'the presets of the instrument are listed', pr)
    R("$('#dsbQ').focus()"); K.press('ArrowRight'); W(500)
    pr2 = J("{cur:dsB1PreCur(),on:(document.querySelector('#dsbPre .on')||{}).dataset,ipk:ib.t.inst.ipk,sub:$('#dsbSub').textContent}")
    ok(pr2['cur'] and pr2['cur'] != pr['cur'] and pr2['ipk'] == pr2['cur'], 'Right plays the next preset', [pr['cur'], pr2])
    if SHOTS:
        for mode in ['dark', 'light']:
            R("pmSetOn(%s)" % ('true' if mode == 'light' else 'false')); W(2500)
            pg.screenshot(path=os.path.join(SHOTS, 'b1a_inst_%s.png' % mode))
        R("pmSetOn(false)"); W(1500)

    # 4. Enter adds the instrument with the chosen preset
    K.press('Enter'); W(800)
    ad = J("{hid:$('#ib').hidden,n:S.tracks.length,ipk:S.tracks[S.tracks.length-1]&&S.tracks.find(t=>t.inst&&t.inst.preset==='plant'&&t.inst.ipk===%s)!=null}" % json.dumps(pr2['cur']))
    ok(ad['hid'] and ad['n'] == n0 + 1 and ad['ipk'], 'Enter adds the instrument with that preset', ad)
    R("undo();1"); W(500)
    ok(R("S.tracks.length") == n0, 'undo removes it')

    # 5. Effects Browser
    R("openFxBrowser(S.tracks[0]);1"); W(900)
    fx = J("{cat:!!document.querySelector('#ibPlane.dsbcat'),rows:document.querySelectorAll('#dsbRows .dsbr').length,items:dsB1Items().length,ph:$('#dsbQ').placeholder}")
    ok(fx['cat'] and fx['rows'] == fx['items'] and fx['ph'] == 'Search effects', 'Effects Browser opens as the catalogue', fx)
    nf = R("S.tracks[0].fx.length")
    R("document.querySelector('#dsbRows .dsbr[data-k=\"delay\"]').click()"); W(3500)
    fw = J("{sel:ib.sel,t:ib.t&&ib.t.fx[0].type,cur:DSB.cur&&!!DSB.cur.pk,pre:document.querySelectorAll('#dsbPre [data-dsp]').length}")
    ok(fw['sel'] == 'delay' and fw['t'] == 'delay' and fw['cur'], 'an effect is measured with the test sound through it', fw)
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, 'b1a_fx_dark.png'))
    R("$('#dsbQ').focus()"); K.press('Enter'); W(700)
    ok(J("$('#ib').hidden") and R("S.tracks[0].fx.length") == nf + 1 and R("S.tracks[0].fx[S.tracks[0].fx.length-1].type") == 'delay', 'Enter adds the effect')
    R("undo();1"); W(400)

    # 6. Change instrument: the same Change mode, in the catalogue
    ti = R("S.tracks.findIndex(t=>t.kind==='inst'&&t.inst&&PRESETS[t.inst.preset]&&t.inst.preset!=='drums')")
    was = R("S.tracks[%d].inst.preset" % ti); snap = R("JSON.stringify(S.tracks[%d].inst)" % ti)
    R("openBrowser(S.tracks[%d]);1" % ti); W(1000)
    ch = J("{cat:!!document.querySelector('#ibPlane.dsbcat'),chg:!!(CHG&&ib.chg),add:$('#ibAdd').textContent,sel:ib.sel,was:!!document.querySelector('#dsbRows .dsbr[data-k=\"%s\"] em')}" % was)
    ok(ch['cat'] and ch['chg'] and ch['add'] == 'Keep' and ch['sel'] == was and ch['was'], 'Change opens the catalogue on the track\'s own sound', ch)
    other = 'saw' if was != 'saw' else 'pad'
    R("document.querySelector('#dsbRows .dsbr[data-k=\"%s\"]').click()" % other); W(700)
    ok(R("S.tracks[%d].inst.preset" % ti) == other, 'one click puts it on the track', R("S.tracks[%d].inst.preset" % ti))
    K.press('Escape'); W(600)
    ok(J("$('#ib').hidden") and R("JSON.stringify(S.tracks[%d].inst)" % ti) == snap, 'Escape brings the old one back')

    # 7. Cards and List
    R("openBrowser(null);1"); W(700)
    R("$('#dsbView').click()"); W(1500)
    cd = J("{cards:document.querySelectorAll('#ibPlane .ibd').length,cat:!!document.querySelector('#ibPlane.dsbcat'),list:!!$('#dsbView'),v:UI.ibView}")
    ok(cd['cards'] > 10 and not cd['cat'] and cd['list'] and cd['v'] == 'cards', 'Cards shows today\'s live cards, with a List button', cd)
    R("$('#dsbView').click()"); W(800)
    ok(J("!!document.querySelector('#ibPlane.dsbcat')&&UI.ibView==='list'"), 'List comes back to the catalogue')
    R("$('#ib').hidden=true"); W(300)

    # 8. other looks keep today's browser
    R("UI.dawLook='ableton'"); R("openBrowser(null);1"); W(1500)
    ok(J("!document.querySelector('#ibPlane.dsbcat')&&document.querySelectorAll('#ibPlane .ibd').length>10&&!$('#dsbView')"), 'the Live look keeps today\'s browser')
    R("$('#ib').hidden=true;UI.dawLook='audiolab'"); W(300)

    # 9. in tempo: the start waits for the next bar while the song plays
    R("play.on||toggle()"); W(1500)
    tt = J("(()=>{const n=ctx.currentTime,t=dsB1T0(),bp=barPos(curBeat());return{wait:t-n,bar:secOf(bp.len)}})()")
    ok(0 <= tt['wait'] <= tt['bar'] + 0.06, 'In tempo: the preview starts on the next bar', tt)
    R("play.on&&toggle()"); W(300)

    ids = J("[...new Set([...document.querySelectorAll('[data-al^=\"browser.\"]')].map(e=>e.dataset.al))]")
    R("openBrowser(null);1"); W(700); R("document.querySelector('#dsbRows .dsbr[data-k=\"plant\"]').click()"); W(900)
    ids = J("[...new Set([...document.querySelectorAll('[data-al^=\"browser.\"]')].map(e=>e.dataset.al))].sort()")
    want = sorted(['browser.search', 'browser.category', 'browser.row', 'browser.view', 'browser.close', 'browser.preset', 'browser.inTempo', 'browser.play', 'browser.device'])
    ok(ids == want, 'every new control has its stable id (docs/ids.md)', ids)
    R("$('#ib').hidden=true"); W(300)
    bad = [l for l in logs if 'AudioContext' not in l]
    ok(not bad, 'no console errors', bad[:5])
    print('%d checks, %d failed' % (N[0], len(FAIL)))
    sys.exit(1 if FAIL else 0)
