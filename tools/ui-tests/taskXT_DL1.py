"""Task XT-DL1: control ids, part 1 (docs/extensions-plan.md 9.7, docs/ids.md).
Fails when a control in the transport bar, a track header or the mixer has no id (data-al), or when an id listed in
docs/ids.md disappears from CONTROLS (a retired id must stay in CONTROL_ALIAS and point at a living one).
Scenario: the Fractals song, the track header layout "Everything", an automation lane open, every extra transport module
added, the mixer open with its sends, monitor, A/B and cable legend; then the same after the areas are built again.
  python3 tools/ui-tests/taskXT_DL1.py [index.html] [out dir]"""
import sys, os, json, re
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
IDX = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
SRC = open(IDX, encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
IDS_MD = os.path.join(HERE, '..', '..', 'docs', 'ids.md')
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
# released ids: every table row of docs/ids.md whose first cell is `an.id`
REL = []
for l in open(IDS_MD, encoding='utf-8'):
    m = re.match(r'^\|\s*`([a-z]+(?:\.[A-Za-z0-9]+)+)`\s*\|', l)
    if m: REL.append(m.group(1))
# controls that only exist in some states (named in docs/ids.md as such)
COND = {'transport.tutorial'}
INIT = "if(!sessionStorage.getItem('dl1')){sessionStorage.setItem('dl1','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
# what counts as a control: anything a person can press, type into, drag or focus
Q = "button,input,select,textarea,[data-c],[role=button],[role=slider],[role=tab],[contenteditable=true]"
UNTAGGED = r"""(Q=>{const R={transport:'#tr',track:'#hdrin',mixer:'#mixWin'},out=[];
 const sig=e=>{let s=e.tagName.toLowerCase();if(e.id)s+='#'+e.id;for(const c of e.classList)s+='.'+c;for(const a of e.attributes)if(/^data-(a|z|c|la|add|mact|mon|ab|cl|ni|sn|gfold)$/.test(a.name))s+=`[${a.name}=${a.value.slice(0,14)}]`;return s};
 for(const[k,sel] of Object.entries(R)){const r=document.querySelector(sel);if(!r)continue;
  for(const e of r.querySelectorAll(Q)){if(e.closest('[role=menu],[role=dialog],.pop,[popover]'))continue;
   /* a part inside a tagged control (the input of a knob, a button inside an extra module) belongs to that control */
   if(!e.closest('[data-al]'))out.push(k+': '+sig(e)+' in .'+String(e.parentElement.className).split(' ')[0])}}
 return [...new Set(out)]})"""
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.add_init_script(INIT)
    pg.route('https://app.test/**', lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body=''))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(2500)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 266), 'version 0.266 or later', R('VERSION'))
    # the table itself
    T = J("CONTROLS.map(c=>[c[0],c[1],c[2]])")
    ids = [c[0] for c in T]
    ok(len(ids) == len(set(ids)), 'every id in CONTROLS is used once', len(ids))
    bad = [i for i in ids if not re.match(r'^(transport|track|mixer)(\.[a-z][A-Za-z0-9]*)+$', i)]
    ok(not bad, 'ids are dotted, start with their area and use plain letters', bad)
    ok(all(c[2] and '—' not in c[2] and len(c[2]) <= 48 for c in T), 'every control has a plain name (no em dash)', [c for c in T if not c[2]])
    sel_err = J("CONTROLS.filter(c=>{try{document.querySelector(c[1]);return false}catch(e){return true}}).map(c=>c[0])")
    ok(not sel_err, 'every selector is valid', sel_err)
    # released ids never disappear
    ok(len(REL) >= 90, 'docs/ids.md lists the released ids', len(REL))
    alias = J("CONTROL_ALIAS")
    gone = [i for i in REL if i not in ids and not (i in alias and alias[i] in ids)]
    ok(not gone, 'every released id is in CONTROLS (or an alias of one)', gone)
    new = [i for i in ids if i not in REL]
    ok(not new, 'every id in CONTROLS is listed in docs/ids.md', new)
    # the scenario
    R("openDemoFractals()"); pg.wait_for_timeout(7000)
    R("hczSet(HCZP.all.c,true)")
    R("(()=>{const t=S.tracks.find(x=>x.kind!=='group'&&x.kind!=='return');t.lanes=['vol'];layoutRows&&layoutRows();renderHeaders()})()")
    R("(()=>{UI.trX=Object.keys(TRX).map((k,i)=>({id:'xdl1'+i,type:k}));saveUI();trApply()})()")
    R("$('#mBtn').click()"); pg.wait_for_timeout(1800)
    un = J(UNTAGGED + "(" + json.dumps(Q) + ")")
    ok(not un, 'every control in the transport bar, the track headers and the mixer has an id', un[:40])
    found = J("[...document.querySelectorAll('[data-al]')].map(e=>e.dataset.al).filter((v,i,a)=>a.indexOf(v)===i)")
    miss = [i for i in ids if i not in found and i not in COND]
    ok(not miss, 'every id in CONTROLS is on a control in this scenario', miss)
    cnt = J("(()=>{const o={};for(const e of document.querySelectorAll('[data-al]'))o[e.dataset.al]=(o[e.dataset.al]||0)+1;return o})()")
    nt = J("S.tracks.length")
    ok(cnt.get('track.mute', 0) >= nt - 2 and cnt.get('mixer.strip.mute', 0) >= nt - 2, 'repeated controls share one id (one per track)', (cnt.get('track.mute'), cnt.get('mixer.strip.mute'), nt))
    ok(cnt.get('transport.play') == 1 and cnt.get('mixer.master.volume') == 1 and cnt.get('track.master.volume') == 1, 'single controls are tagged once')
    # the master strip and the master header are not taken as a track
    ok(J("!document.querySelector('.mx.master [data-al^=\"mixer.strip.\"]')") and J("!document.querySelector('.mhdr [data-al^=\"track.\"]:not([data-al^=\"track.master.\"])')"), 'the master strip and master header carry master ids, not track ids')
    ok(J("xtControlOf($('#bLoop svg')||$('#bLoop'))[0]") == 'transport.loop' and J("xtControlOf(document.querySelector('.hdr [data-a=solo]'))[0]") == 'track.solo' and J("xtControlOf(document.body)") is None,
       'xtControlOf finds the control an element belongs to', J("xtControlOf($('#bLoop'))"))
    R("CONTROL_ALIAS['transport.cycle']='transport.loop'")
    ok(J("(()=>{const b=$('#bLoop');b.dataset.al='transport.cycle';const r=xtControlOf(b)[0];b.dataset.al='transport.loop';delete CONTROL_ALIAS['transport.cycle'];return r})()") == 'transport.loop', 'an old id is followed through CONTROL_ALIAS')
    # built again: ids come back on the new elements
    R("renderHeaders();renderMixer();trApply()"); pg.wait_for_timeout(300)
    un2 = J(UNTAGGED + "(" + json.dumps(Q) + ")")
    ok(not un2, 'after the headers, the mixer and the transport bar are built again every control still has its id', un2[:20])
    R("hczSet(HCZP.min.c,true)"); R("$('#mxCmp').click()"); pg.wait_for_timeout(600)
    un3 = J(UNTAGGED + "(" + json.dumps(Q) + ")")
    ok(not un3, 'the same with the Minimal header layout and compact channels', un3[:20])
    R("$('#mxCmp').click()"); R("hczSet(HCZD,true)"); pg.wait_for_timeout(300)
    # the test catches what it should
    R("(()=>{const x=document.createElement('button');x.id='dl1probe';document.querySelector('#tr').appendChild(x)})()"); pg.wait_for_timeout(50)
    un4 = J(UNTAGGED + "(" + json.dumps(Q) + ")")
    ok(any('dl1probe' in u for u in un4), 'a new button without an id is caught', un4[:3])
    R("$('#dl1probe').remove()")
    # nothing else changes: no attribute other than data-al, nothing per frame
    calls = J("(()=>{window.__dl1=0;const o=xtTag;xtTag=function(){window.__dl1++;return o.apply(this,arguments)};return 1})()")
    R("play.on||toggle()"); pg.wait_for_timeout(3000); R("play.on&&toggle()")
    n3 = J("window.__dl1")
    ok(n3 <= 12, 'while playing, the ids are written only when an area is built again (not per frame)', '%d tag passes in 3 s' % n3)
    ms = J("(()=>{const t0=performance.now();for(let i=0;i<20;i++){document.querySelectorAll('[data-al]').forEach(e=>delete e.dataset.al);xtTag('track');xtTag('mixer');xtTag('transport')}return (performance.now()-t0)/20})()")
    ok(ms < 8, 'one pass over all three areas with %d tracks is cheap' % nt, '%.2f ms' % ms)
    ok(not errs, 'no console errors', errs[:5])
    pg.screenshot(path=os.path.join(OUT, 'xt_dl1.png'))
    b.close()
print('%d of %d checks passed' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
