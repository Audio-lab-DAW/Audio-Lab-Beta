#!/usr/bin/env python3
"""Task LK (look tokens): the LOOK object and CSS tokens, G3 drafting grid in W1 hairlines, L2 amber units, A1 yellow selection, M3 motion levels, N3 density.
   python3 tools/ui-tests/taskLK.py [index.html]
At the user's size (2194 x 1139 CSS px at 1.75x) with Fractals, plus the hairline check at 1x and 2x. SwiftShader: correctness only."""
import sys, json
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)

# hairline check: one bar line in an empty lane of the arrangement canvas must be whole device pixels wide (1 column), not smeared
HAIR = r"""(()=>{V.ppb=40;V.x=128;V.y=0;clampV();drawArr();const c=arr,g=c.getContext('2d'),d=devicePixelRatio*ZOOM;
  const xb=X0+(132-V.x)*V.ppb,row=S.tracks.findIndex(t=>!t.clips.some(q=>q.start<=133&&q.start+q.len>131));if(row<0)return null;
  const y=Math.round((AY+TRY[row]-V.y+V.th*.4)*d),x0=Math.round(xb*d)-6,im=g.getImageData(x0,y,13,1).data,v=[];for(let i=0;i<13;i++)v.push(im[i*4]+im[i*4+1]+im[i*4+2]);
  const base=Math.min(...v),hot=v.map(q=>q-base>6?1:0);return{v,hot:hot.join(''),n:hot.reduce((a,b)=>a+b,0)}})()"""

def load(p, w, h, dsf, logs):
    ctx = p.chromium.launch(args=ARGS).new_context(viewport={'width': w, 'height': h}, device_scale_factor=dsf); pg = ctx.new_page()
    pg.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text else None)
    pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    R("pmSetOn(false)"); R("openDemoFractals()"); pg.wait_for_timeout(6000)
    return pg, R

with sync_playwright() as p:
    logs = []
    pg, R = load(p, 2194, 1139, 1.75, logs)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    print('version', R("VERSION"))
    # ---- 1. tokens ----
    t = J("{o:typeof LOOK==='object'&&!Array.isArray(LOOK),k:Object.keys(LOOK),sl:Array.isArray(LOOK_SL)&&LOOK_SL.length,ins:INS._src()===LOOK,il:INS.look().sel,g:LOOK.grid,l:LOOK.lines,lb:LOOK.labels,a:LOOK.accent,m:LOOK.motion,d:LOOK.density}")
    ok(t['o'], 'LOOK is one plain object (the Settings sliders are LOOK_SL)', t['sl'])
    ok(all(k in t['k'] for k in ['grid','lines','labels','accent','motion','density','gr','pr','gMaj','gMid','gMin','lwGrid','lwLine','lwCurve','unit','meas','sel','warn','over','ink','mut','mono','ui']), 'LOOK has grid, line weights, label style, accent roles, motion and density')
    ok([t['g'], t['l'], t['lb'], t['a'], t['m'], t['d']] == ['G3', 'W1', 'L2', 'A1', 'ambient', 'dense'], 'the picked values: G3 W1 L2 A1 M3 (Ambient) N3 (Dense)', [t['g'], t['l'], t['lb'], t['a'], t['m'], t['d']])
    ok(t['ins'] and t['il'] == '#f5c84c', 'INS (lane E) reads LOOK', t['il'])
    c = J("(()=>{const s=getComputedStyle(document.documentElement);return['--sel','--meas','--unit','--lk-hair','--lk-row'].map(k=>s.getPropertyValue(k).trim())})()")
    ok(c[0] == '#f5c84c' and c[1] == '#ffb547' and c[2] == '#ffb547', 'CSS tokens: --sel yellow, --meas and --unit amber', c)
    ok(abs(float(c[3][:-2]) - 1 / 1.75) < 1e-3, 'CSS hairline is one device pixel at 1.75x', c[3])
    # Settings sliders still work under their new name
    g0 = R("UI.gridB"); R("(()=>{const e=document.getElementById('setGrid');e.value=70;e.dispatchEvent(new Event('input',{bubbles:true}))})()"); g1 = R("UI.gridB")
    R("(()=>{const e=document.getElementById('setGrid');e.value=%s;e.dispatchEvent(new Event('input',{bubbles:true}))})()" % (g0 if g0 is not None else 50))
    ok(g1 == 70, 'the grid brightness slider still works (LOOK_SL)', [g0, g1])
    # ---- 2. density ----
    d = J("{th:V.th,thD:V.thD,row:getComputedStyle(document.documentElement).getPropertyValue('--lk-row').trim()}")
    ok(d['th'] == 74 and d['thD'] == 74, 'Dense default: tracks 74 px (96 x 48/62) on Fractals (its view has the old default 96)', d)
    res = {}
    for k in ['roomy', 'today', 'dense']:
        R("(()=>{const e=document.getElementById('lkDens');e.value='%s';e.dispatchEvent(new Event('change',{bubbles:true}))})()" % k); pg.wait_for_timeout(300)
        res[k] = J("{th:V.th,row:getComputedStyle(document.documentElement).getPropertyValue('--lk-row').trim(),ui:UI.lkDens}")
    ok(res['roomy']['th'] == 118 and res['today']['th'] == 96 and res['dense']['th'] == 74, 'Density Roomy / Today / Dense: 118 / 96 / 74 px tracks', res)
    ok(int(res['dense']['row'][:-2]) >= 24 and res['today']['row'] == '28px' and int(res['roomy']['row'][:-2]) > 28, 'menu rows follow density, never below 24 px (click targets)', [r['row'] for r in res.values()])
    R("(()=>{const e=document.getElementById('ctxm');e.hidden=false;e.innerHTML='<button>One</button>'})()"); hb = R("document.querySelector('#ctxm button').getBoundingClientRect().height"); R("(()=>{const e=document.getElementById('ctxm');e.hidden=true;e.innerHTML=''})()")
    ok(hb >= 24, 'a menu row is at least 24 px high at Dense', hb)
    # own heights are kept; old default follows the setting
    own = J("""(()=>{const cur=PJ.cur,a='p'+rid(),b='p'+rid(),S0=JSON.parse(JSON.stringify(S));PJ.list.push({id:a,name:'own',S:JSON.parse(JSON.stringify(S0)),view:{x:0,ppb:20,y:0,th:130}});PJ.list.push({id:b,name:'old',S:JSON.parse(JSON.stringify(S0)),view:{x:0,ppb:20,y:0,th:96}});
      switchProject(a);const r1=V.th;switchProject(b);const r2=V.th;V.th=140;switchProject(a);const r3=V.th;switchProject(b);const r4=V.th;switchProject(cur);PJ.list=PJ.list.filter(p=>p.id!==a&&p.id!==b);return[r1,r2,r3,r4,V.th]})()""")
    ok(own[0] == 130 and own[1] == 74 and own[2] == 130 and own[3] == 140, 'a project with its own track height keeps it; an old view at the old default gets Dense; a height set later is kept', own)
    # ---- 3. settings rows ----
    s = J("{r:['density','motion'].map(id=>{const r=SETT.get(id);return r&&[r.pg,r.ap,r.d,!!r.h,!!r.w,SETT.isDefault(id)]}),f:SETT.find('dense'),f2:SETT.find('ambient motion'),h:LK_HOOKS.appearanceRows().map(r=>r.pg+':'+r.id),row:!!SETT.row('density')}")
    # from v0.250 (task ST-S5) the rows sit on their own page, Appearance (page 'appearance'); before it on Layout
    ok(s['r'][0][1:] == ['appearance', 'dense', True, True, True] and s['r'][1][1:] == ['appearance', 'ambient', True, True, True] and s['r'][0][0] in ('layout', 'appearance') and s['r'][1][0] == s['r'][0][0], 'Density and Motion rows in the S4 table (id, label, page, default, help, search words), at their defaults', s['r'])
    ok('density' in s['f'] and 'motion' in s['f2'] and s['row'], 'found by search, row found in the window', [s['f'], s['f2']])
    ok(s['h'] == ['appearance:density', 'appearance:motion'], 'LK_HOOKS.appearanceRows gives them for an Appearance page', s['h'])
    R("SETT.set('motion','signal')"); m1 = J("{b:document.body.className.includes('lkm1'),st:document.body.classList.contains('lkstill'),ui:UI.lkMotion,l:LOOK.motion,amb:LOOK.ambientOK(),logo:aoStill(),tr:getComputedStyle(document.querySelector('#ctxm')).transitionDuration}")
    ok(m1['b'] and m1['st'] and m1['ui'] == 'signal' and not m1['amb'] and m1['logo'], 'Motion Signal only: transitions off, ambient drawings and logos still', m1)
    R("SETT.set('motion','trans')"); m2 = J("{b:document.body.classList.contains('lkm1'),st:document.body.classList.contains('lkstill'),amb:LOOK.ambientOK()}")
    ok(not m2['b'] and m2['st'] and not m2['amb'], 'Signal and transitions: transitions on, no ambient drawings', m2)
    R("SETT.reset('motion')"); m3 = J("{st:document.body.classList.contains('lkstill'),amb:LOOK.ambientOK(),l:LOOK.motion}")
    ok(not m3['st'] and m3['amb'] and m3['l'] == 'ambient', 'Ambient (default): ambient drawings allowed', m3)
    R("pmSetOn(true)"); pg.wait_for_timeout(600); ml = J("{amb:LOOK.ambientOK(),lite:!!UI.lite}"); R("pmSetOn(false)"); pg.wait_for_timeout(600)
    ok(ml['lite'] and not ml['amb'], 'never ambient motion in Light mode', ml)
    # ---- 4. L2 units ----
    R("(()=>{const t=S.tracks.find(t=>/^bass/i.test(t.name));selectTrack(t.id)})()"); pg.wait_for_timeout(1200)
    u = J("(()=>{const o=[...document.querySelectorAll('#fxin output')].filter(o=>o.querySelector('.lku'));const q=o[0];const tv=document.querySelector('#fxin .tdvo');return{n:o.length,txt:q&&q.textContent,u:q&&q.querySelector('.lku').textContent,col:q&&getComputedStyle(q.querySelector('.lku')).color,vcol:q&&getComputedStyle(q).color,tv:tv&&tv.textContent,tvu:tv&&!!tv.querySelector('.lku')}})()")
    ok(u['n'] > 0 and u['col'] == 'rgb(255, 181, 71)' and u['vcol'] != u['col'], 'control read-outs: units in amber, values in the normal colour', u)
    ok(u['tv'] and u['tv'].endswith(' dB') and u['tvu'], 'channel volume read-out: text unchanged, unit amber', u['tv'])
    tx = J("['1.2 kHz','50%','4.0:1','−∞ dB','Off','1/4','C3','12 dB/oct'].map(s=>{const o=document.createElement('output');lkOut(o,s);return[o.textContent===s,o.querySelector('.lku')?o.querySelector('.lku').textContent:'']})")
    ok(all(a for a, b in tx) and [b for a, b in tx] == ['kHz', '%', ':1', 'dB', '', '', '', 'dB/oct'], 'unit splitting keeps the text and finds the unit', tx)
    # ---- 5. A1 selection ----
    a = J("(()=>{selT=S.tracks.find(t=>/^bass/i.test(t.name)).id;renderHdr&&renderHdr();const h=document.querySelector('.hdr.sel');return{h:h&&getComputedStyle(h).boxShadow}})()") if R("typeof renderHdr==='function'") else J("{h:(document.querySelector('.hdr.sel')?getComputedStyle(document.querySelector('.hdr.sel')).boxShadow:null)}")
    ok(a['h'] and '245, 200, 76' in a['h'], 'the selected track header is marked in yellow', a['h'])
    R("openMixer()"); pg.wait_for_timeout(1500)
    mx = J("(()=>{const m=document.querySelector('#mixWin .mx.sel')||(()=>{const x=document.querySelector('#mixWin .mx:not(.master)');x.classList.add('sel');return x})();return getComputedStyle(m).borderLeftColor})()")
    ok('245, 200, 76' in mx, 'the selected mixer strip is marked in yellow', mx)
    tk = J("(()=>{const s=document.querySelector('#mixWin .fsc span');return s?getComputedStyle(s,'::after').height:null})()")
    ok(tk and abs(float(tk[:-2]) - 1 / 1.75) < .01, 'mixer scale ticks are hairlines', tk)
    R("(()=>{const w=document.getElementById('mixWin');if(w)w.hidden=true})()")
    cl = J("""(()=>{V.ppb=40;V.x=128;V.y=0;clampV();const i=S.tracks.findIndex(t=>t.clips.some(c=>c.start<=136&&c.start+c.len>136));const t=S.tracks[i],c=t.clips.find(c=>c.start<=136&&c.start+c.len>136);selC=c.id;drawArr();
      const G=clipGeom(i,c),d=devicePixelRatio*ZOOM,g=arr.getContext('2d'),x=Math.round((Math.max(G.x,X0)+60)*d),y=Math.round((G.y+G.h-.7)*d);let best=null;for(let k=-3;k<=3;k++){const p=g.getImageData(x,y+k,1,1).data;if(p[0]>200&&p[1]>160&&p[2]<120)best=[p[0],p[1],p[2]]}selC=null;drawArr();return best})()""")
    ok(cl is not None, 'a selected clip is outlined in yellow', cl)
    # ---- 6. W1 hairlines on device pixels ----
    hh = J(HAIR)
    ok(hh and hh['n'] >= 1 and '11' not in hh['hot'], 'G3 grid lines are single device pixels at 1.75x', hh)
    print('console errors', logs[:5]); ok(not logs, 'no console errors')
    for dsf in (1, 2):
        lg = []; pg2, R2 = load(p, 1400, 860, dsf, lg); h2 = json.loads(R2("JSON.stringify(" + HAIR + ")"))
        ok(h2 and h2['n'] >= 1 and '11' not in h2['hot'], 'G3 grid lines are single device pixels at %dx' % dsf, h2)
        ok(not lg, 'no console errors at %dx' % dsf, lg[:3])
print('%d checks, %d failed' % (N[0], len(FAIL)))
for f in FAIL: print('  FAIL', f)
sys.exit(1 if FAIL else 0)
