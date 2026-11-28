#!/usr/bin/env python3
"""Task DS-P2 (design round 2, PN3, PV3, PG1): piano roll notes (crisp edge, lit top, name inside), velocity bars with
their values (edit anywhere over a bar), other tracks as faint outlines.
   python3 tools/ui-tests/taskDS_P2.py [index.html] [--shots OUTDIR]
At the user's size (2194 x 1139 CSS px at 1.75x) with Fractals plus a made-up pad (Am F C G, one bar each) and lead
(A minor with one G#), Dark (glass) and Light. SwiftShader: correctness only."""
import sys, json, os
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'index.html'
SHOTS = sys.argv[sys.argv.index('--shots') + 1] if '--shots' in sys.argv else None
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)

# pad: Am F C G (whole bars, from beat 512, far from the song), lead in A minor with one G#3 (MIDI 56)
MAKE = r"""(()=>{const pr=Object.keys(PRESETS).find(k=>k!=='drums')||Object.keys(PRESETS)[0];
  const pad=mkTrack('inst',pr,'Pad test','#7b6cff'),lead=mkTrack('inst',pr,'Lead test','#4cc9f0');
  const CH=[[57,60,64],[53,57,60],[55,60,64],[55,59,62]],pn=[];CH.forEach((c,i)=>c.forEach(p=>pn.push({p,s:i*4,l:4,v:.7})));
  let E=0;for(const t of S.tracks)for(const c of t.clips)E=Math.max(E,c.start+c.len);const B0=Math.ceil(E/4)*4+64;
  pad.clips.push(mkClip({start:B0,len:16,name:'Pad',notes:pn}));
  const M=[[0,.75,69,.9],[.75,.25,72,.5],[1,.5,76,.75],[1.5,.5,74,.6],[2,1,72,.8],[3,.5,71,.5],[3.5,.5,67,.7],[4,.75,69,.85],[4.75,.25,72,.45],[5,.5,76,.7],[5.5,.5,74,.6],[6,1.5,72,.8],[7.5,.5,56,.55]];
  lead.clips.push(mkClip({start:B0,len:16,name:'Lead',notes:M.map(m=>({s:m[0],l:m[1],p:m[2],v:m[3]}))}));
  S.tracks.push(pad,lead);layoutRows();changed(true);return{tid:lead.id,cid:lead.clips[0].id,pid:pad.id}})()"""

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

def clean(pg): pg.evaluate("()=>{for(const i of['splash','liteNote','toast']){const s=document.getElementById(i);if(s&&i!=='toast')s.remove();else if(s)s.style.display='none'}}")

with sync_playwright() as p:
    logs = []
    pg, R = load(p, logs)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    print('version', R("VERSION"))
    f = J("['dsP2Note','dsP2Name','dsP2Ghost','dsP2Vel','dsP2VelHit'].map(n=>typeof window[n])")
    ok(all(x == 'function' for x in f), 'the DS-P2 helpers exist', f)
    m = J(MAKE)
    R("(()=>{const t=S.tracks.find(t=>t.id==='%s'),c=t.clips[0];openPR(t,c);PR.root=9;PR.scale='minor';PR.ghost=true;window.DSPM=UI.prMode;setTimeout(()=>prMode('full'),300)})()" % m['tid'])
    pg.wait_for_timeout(1500)
    R("(()=>{PR.x=-.25;PR.rh=16;PR.y=(127-79)*PR.rh;clampPR();PR.ppb=(prc.clientWidth-KEYW)/8.5;dirty=true})()")
    pg.wait_for_timeout(600)
    PX = r"""(()=>{dirty=true;drawPR();const d=(window.devicePixelRatio||1)*ZOOM,g=prc.getContext('2d'),o=prClip(),gh=prc.clientHeight-VELH,h=prc.clientHeight;
      const P=(x,y)=>Array.from(g.getImageData(Math.round(x*d),Math.round(y*d),1,1).data).slice(0,3);
      const nx=n=>KEYW+(n.s-PR.x)*PR.ppb,N=o.c.notes,hi=N[0],lo=N[1],wide=N[4];
      const dark=(n)=>{let k=0;for(let x=nx(n)+4;x<nx(n)+20;x+=.5)for(let y=py(n.p)+4;y<py(n.p)+PR.rh-3;y+=.5){const p=P(x,y);if(p[0]+p[1]+p[2]<200)k++}return k};
      const ghost=o.c.notes&&(()=>{const y=py(64)+PR.rh/2,x=KEYW+(1.5-PR.x)*PR.ppb;return P(x,y)})();
      const bar=n=>{const top=gh+6+(1-n.v)*(VELH-12);return{mid:P(nx(n)+n.l*PR.ppb*.6,(top+h-4)/2),top}};
      let lit=0;{const top=gh+6+(1-wide.v)*(VELH-12);for(let x=nx(wide)+3;x<nx(wide)+22;x+=.5)for(let y=top+2;y<top+14;y+=.5){const p=P(x,y);if(p[0]>180&&p[1]>180&&p[2]>180)lit++}}
      return{hiC:P(nx(hi)+PR.ppb*.5,py(hi.p)+PR.rh*.65),loC:P(nx(lo)+PR.ppb*.15,py(lo.p)+PR.rh*.65),topL:P(nx(hi)+PR.ppb*.5,py(hi.p)+2.5),dark:dark(wide),ghost,row:P(KEYW+(5.5-PR.x)*PR.ppb,py(64)+PR.rh/2),bar:bar(wide).mid,lane:P(nx(wide)-3,gh+VELH*.7),lit,gh,vv:[hi.v,lo.v]}})()"""
    for mode in ['dark', 'light']:
        R("pmSetOn(%s)" % ('true' if mode == 'light' else 'false')); pg.wait_for_timeout(1200)
        q = J(PX)
        ok(abs(sum(q['hiC']) - sum(q['loC'])) < 30, mode + ': notes in the full colour whatever their velocity', [q['hiC'], q['loC'], q['vv']])
        ok(sum(q['topL']) > sum(q['hiC']) + 20, mode + ': a lit top line', [q['topL'], q['hiC']])
        ok(q['dark'] > 10, mode + ': the name inside a wide note', q['dark'])
        ok(abs(sum(q['ghost']) - sum(q['row'])) < 25, mode + ': ghost note not filled (outline only)', [q['ghost'], q['row']])
        ok(sum(q['bar']) > 15+15+18 + 40 and q['bar'][2] > q['bar'][0] + 15, mode + ': velocity bar as wide as the note', [q['bar'], q['lane']])
        ok(q['lit'] > 3, mode + ': the value on the bar', q['lit'])
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True); clean(pg)
            r = J("(()=>{const a=prc.getBoundingClientRect();return{x:a.left,y:a.top,w:a.width,h:a.height}})()")
            pg.screenshot(path=f'{SHOTS}/{mode}-p2.png', clip={'x': r['x'], 'y': r['y'], 'width': min(1100, r['w']), 'height': r['h']})
            pg.screenshot(path=f'{SHOTS}/{mode}-p2-win.png')
    R("pmSetOn(false)"); pg.wait_for_timeout(800)
    # editing over a bar (not near its start), then undo
    e = J(r"""(()=>{const o=prClip(),n=o.c.notes[4],r=prc.getBoundingClientRect(),z=ZOOM,h=prc.clientHeight,x=KEYW+(n.s+n.l*.6-PR.x)*PR.ppb,y=h-VELH+6+(1-.3)*(VELH-12);
       return{cx:r.left+x*z,cy:r.top+y*z,v0:n.v}})()""")
    pg.mouse.move(e['cx'], e['cy']); pg.mouse.down(); pg.mouse.up(); pg.wait_for_timeout(300)
    v1 = J("prClip().c.notes[4].v")
    ok(abs(v1 - 0.3) < 0.03 and abs(e['v0'] - 0.3) > 0.1, 'a click over the middle of a bar sets that note\'s velocity', [e['v0'], v1])
    R("undo()"); pg.wait_for_timeout(300)
    ok(abs(J("prClip().c.notes[4].v") - e['v0']) < 1e-6, 'undo brings it back')
    # near the start still works as before
    e2 = J(r"""(()=>{const o=prClip(),n=o.c.notes[0],r=prc.getBoundingClientRect(),z=ZOOM,h=prc.clientHeight,x=KEYW+(n.s-PR.x)*PR.ppb+1,y=h-VELH+6+(1-.5)*(VELH-12);return{cx:r.left+x*z,cy:r.top+y*z}})()""")
    pg.mouse.move(e2['cx'], e2['cy']); pg.mouse.down(); pg.mouse.up(); pg.wait_for_timeout(300)
    ok(abs(J("prClip().c.notes[0].v") - 0.5) < 0.03, 'a click at a note\'s start edits it as before', J("prClip().c.notes[0].v"))
    R("undo()")
    # another look: today's notes (velocity as strength)
    R("UI.dawLook='fl';applyTheme()"); pg.wait_for_timeout(600)
    q = J(PX)
    ok(abs(sum(q['hiC']) - sum(q['loC'])) >= 30 and not J("dsAC3()"), 'FL style: today\'s notes (velocity as strength)', [q['hiC'], q['loC']])
    R("delete UI.dawLook;applyTheme()"); pg.wait_for_timeout(600)
    tm = J(r"""(()=>{const T=[];for(let i=0;i<200;i++){dirty=true;const a=performance.now();drawPR();T.push(performance.now()-a)}T.sort((a,b)=>a-b);return[+T[100].toFixed(3),+(T.reduce((a,b)=>a+b)/T.length).toFixed(3)]})()""")
    print('drawPR median, mean ms:', tm)
    R("prMode(DSPM||'dock');closePR()")
    R("(()=>{S.tracks=S.tracks.filter(t=>t.name!=='Pad test'&&t.name!=='Lead test');layoutRows();changed(true)})()")
    ok(not logs, 'no console errors', logs[:5])
    print(f'{N[0] - len(FAIL)} of {N[0]} checks passed'); sys.exit(1 if FAIL else 0)
