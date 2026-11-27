#!/usr/bin/env python3
"""Task DS-P1 (design round 2, PS3 and PK3): piano roll scale rows, root line, out-of-scale ring and label, chord names
in the ruler, narrow keys with every row named (cached key column).
   python3 tools/ui-tests/taskDS_P1.py [index.html] [--shots OUTDIR]
At the user's size (2194 x 1139 CSS px at 1.75x) with Fractals plus a made-up pad (Am F C G, one bar each) and lead
(A minor with one G#), Dark (glass) and Light. SwiftShader: correctness only."""
import sys, json, os
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
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
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
    f = J("['dsP1Begin','dsP1Keys','dsP1Ruler','dsP1Chords','dsP1Out','dsP1Labels','dsNN'].map(n=>typeof window[n])")
    ok(all(x == 'function' for x in f), 'the DS-P1 helpers exist', f)
    m = J(MAKE)
    R("(()=>{const t=S.tracks.find(t=>t.id==='%s'),c=t.clips[0];openPR(t,c);PR.root=9;PR.scale='minor';window.DSPM=UI.prMode;setTimeout(()=>prMode('full'),300)})()" % m['tid'])
    pg.wait_for_timeout(1500)
    R("(()=>{PR.x=-.25;PR.ppb=(prc.clientWidth-KEYW)/16.5;PR.rh=16;PR.y=(127-79)*PR.rh;clampPR();PR.ppb=(prc.clientWidth-KEYW)/16.5;dirty=true})()")
    pg.wait_for_timeout(600)
    # chords
    ch = J("(()=>{const o=prClip();return dsP1Chords(o.c).map(e=>[e.s,e.name])})()")
    ok([e[1] for e in ch] == ['Am', 'F', 'C', 'G'] and [e[0] for e in ch] == [0, 4, 8, 12], 'chords under the lead: Am F C G at bars 1 to 4 (the lead line does not change them)', ch)
    same = J("(()=>{const o=prClip();return dsP1Chords(o.c)===dsP1Chords(o.c)})()")
    ok(same, 'chord list cached between pictures')
    R("(()=>{const f=dsP1ChordOf;window.DSC=0;dsP1ChordOf=function(){DSC++;return f.apply(this,arguments)}})()")
    pg.wait_for_timeout(1500)
    ok(J("DSC") == 0, 'nothing worked out again while idle', J("DSC"))
    # an edit: G becomes G7 (add F to the pad's last bar)
    R("(()=>{const t=S.tracks.find(t=>t.id==='%s');t.clips[0].notes.push({p:65,s:12,l:4,v:.6});changed(false)})()" % m['pid'])
    pg.wait_for_timeout(400)
    ch2 = J("(()=>{const o=prClip();return dsP1Chords(o.c).map(e=>e.name)})()")
    ok(ch2 == ['Am', 'F', 'C', 'G7'], 'after an edit the chords follow (G7)', ch2)
    nm = J("[[[0,4,7],-1],[[9,0,4,7],9],[[0,3,7],-1],[[2,5,9],2],[[11,2,5],11],[[0,5,7],0]].map(([pcs,b])=>{const w=new Float32Array(12);pcs.forEach(p=>w[p]+=1);return dsP1ChordOf(w,b)})")
    ok(nm == ['C', 'Am7', 'Cm', 'Dm', 'Bdim', 'Csus4'], 'chord names for known sets (bass picks Am7 over C6)', nm)
    # rows and root line, read from the canvas
    def rows():
        return J(r"""(()=>{dirty=true;drawPR();const d=(window.devicePixelRatio||1)*ZOOM,g=prc.getContext('2d'),o=prClip();
          const free=p=>{for(let b=Math.ceil(PR.x+1)+.37;b<PR.x+8;b+=1){if(!o.c.notes.some(n=>n.p===p&&b>=n.s-.1&&b<n.s+n.l+.1))return b}return null};
          const at=(p,dy)=>{const b=free(p),x=KEYW+(b-PR.x)*PR.ppb;return Array.from(g.getImageData(Math.round(x*d),Math.floor((py(p)+dy)*d),1,1).data).slice(0,3)};
          return{inRow:at(72,PR.rh/2),outRow:at(73,PR.rh/2),rootLine:(()=>{const b=free(69),x=KEYW+(b-PR.x)*PR.ppb;return Array.from(g.getImageData(Math.round(x*d),Math.round((py(69)+PR.rh)*d)-1,1,1).data).slice(0,3)})(),rootMid:at(69,PR.rh/2)}})()""")
    for mode in ['dark', 'light']:
        R("pmSetOn(%s)" % ('true' if mode == 'light' else 'false')); pg.wait_for_timeout(1200)
        q = rows()
        ok(sum(q['inRow']) > sum(q['outRow']) + 15, mode + ': rows in the scale lift, the others sink', q)
        ok(q['rootLine'][0] > q['rootLine'][2] + 30 and q['rootLine'][0] > 60, mode + ': amber line on the root row (A)', q['rootLine'])
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True); clean(pg)
            r = J("(()=>{const a=prc.getBoundingClientRect();return{x:a.left,y:a.top,w:a.width,h:a.height}})()")
            pg.screenshot(path=f'{SHOTS}/{mode}-p1.png', clip={'x': r['x'], 'y': r['y'], 'width': min(1100, r['w']), 'height': r['h']})
            pg.screenshot(path=f'{SHOTS}/{mode}-p1-win.png')
    R("pmSetOn(false)"); pg.wait_for_timeout(800)
    # the key column: cached, names on every row, root name amber
    k = J(r"""(()=>{DSP1.kk='';dirty=true;drawPR();const cv=DSP1.kc,k1=DSP1.kk,c=cv.getContext('2d'),D=cv.width/KEYW;
       const row=p=>{const y0=Math.floor((py(p)-PRUL)*D),y1=Math.floor((py(p)-PRUL+PR.rh)*D),dat=c.getImageData(Math.round(30*D),y0,Math.round(24*D),y1-y0).data;let amb=0,lit=0,grey=0;
         for(let i=0;i<dat.length;i+=4){const r=dat[i],gg=dat[i+1],b=dat[i+2];if(r>150&&gg>100&&b<110&&r-b>70)amb++;else if(r>170&&gg>170&&b>170)lit++;else if(r>90&&Math.abs(r-b)<20&&r<170)grey++}return{amb,lit,grey}};
       dirty=true;drawPR();return{same:DSP1.kk===k1,root:row(69),inS:row(72),out:row(73)}})()""")
    ok(k['same'], 'the key column is not drawn again when the view did not change')
    ok(k['root']['amb'] > 3, 'the root row is named in amber', k['root'])
    ok(k['inS']['lit'] > 3, 'a row in the scale is named in the light tone', k['inS'])
    ok(k['out']['lit'] == 0 and k['out']['grey'] > 2, 'a row outside the scale is named in grey', k['out'])
    # out-of-scale ring and label
    R("(()=>{PR.y=(127-62)*PR.rh;clampPR();dirty=true})()")
    R("(()=>{const f=dsP1Labels;window.DSO=null;dsP1Labels=function(g,DQ){DSO=DQ.out.map(o=>dsNN(o.n.p));return f.apply(this,arguments)}})()")
    R("dirty=true;drawPR()")
    ok(J("DSO") == ['G♯4'] or J("DSO") == ['G♯3'], 'the G# is marked outside the scale (one note, so it is labelled)', J("DSO"))
    rg = J(r"""(()=>{const o=prClip(),n=o.c.notes.find(n=>n.p===56),d=(window.devicePixelRatio||1)*ZOOM,g=prc.getContext('2d');PR.y=(127-60)*PR.rh;clampPR();dirty=true;drawPR();
       const x=KEYW+(n.s-PR.x)*PR.ppb,y=py(56);let amb=0;for(let yy=y-1;yy<y+PR.rh+1;yy+=.5){const p=g.getImageData(Math.round((x-1.5)*d),Math.round(yy*d),1,1).data;if(p[0]>150&&p[2]<120)amb++}return amb})()""")
    ok(rg >= 3, 'the ring is drawn (amber pixels left of the note)', rg)
    if SHOTS:
        clean(pg); r = J("(()=>{const a=prc.getBoundingClientRect();return{x:a.left,y:a.top,w:a.width,h:a.height}})()")
        pg.screenshot(path=f'{SHOTS}/dark-p1-ring.png', clip={'x': r['x'], 'y': r['y'], 'width': min(1100, r['w']), 'height': r['h']})
    # no scale: today's rows, no ring, neutral names
    R("PR.scale='none';dirty=true;drawPR()")
    ok(J("DSO") == [], 'scale none: no ring, no label')
    R("PR.scale='minor';dirty=true")
    # chord names drawn in the ruler (amber pixels in the ruler above bar 2)
    ra = J(r"""(()=>{PR.y=(127-79)*PR.rh;clampPR();dirty=true;drawPR();const d=(window.devicePixelRatio||1)*ZOOM,g=prc.getContext('2d'),x0=KEYW+(4-PR.x)*PR.ppb;let amb=0;
       const dat=g.getImageData(Math.round(x0*d),0,Math.round(60*d),Math.round(PRUL*d)).data;for(let i=0;i<dat.length;i+=4)if(dat[i]>150&&dat[i+2]<120&&dat[i]-dat[i+2]>60)amb++;return amb})()""")
    ok(ra > 10, 'chord names in the ruler (amber)', ra)
    # another look: today's piano roll
    R("UI.dawLook='fl';applyTheme()"); pg.wait_for_timeout(600)
    R("dirty=true;drawPR()")
    ok(J("DSO") == [] and not J("dsAC3()"), 'FL style: today\'s piano roll (no ring, no new keys)')
    R("delete UI.dawLook;applyTheme()"); pg.wait_for_timeout(600)
    # drum clip: today's keys and pad names
    dr = J(r"""(()=>{const t=S.tracks.find(t=>t.inst&&t.inst.preset==='drums'&&t.clips.some(c=>c.notes&&c.notes.length));if(!t)return'none';openPR(t,t.clips.find(c=>c.notes&&c.notes.length));DSP1.kk='x';dirty=true;drawPR();return DSP1.kk})()""")
    ok(dr == 'x' or dr == 'none', 'drum clip: today\'s keys and pad names (key cache untouched)', dr)
    # draw time of the piano roll (cloud software renderer, while playing would redraw it each frame)
    tm = J(r"""(()=>{const t=S.tracks.find(t=>t.id==='%s');openPR(t,t.clips[0]);const T=[];for(let i=0;i<60;i++){dirty=true;const a=performance.now();drawPR();T.push(performance.now()-a)}T.sort((a,b)=>a-b);return +T[30].toFixed(3)})()""" % m['tid'])
    print('drawPR median ms (new):', tm)
    R("prMode(DSPM||'dock');closePR()")
    R("(()=>{S.tracks=S.tracks.filter(t=>t.name!=='Pad test'&&t.name!=='Lead test');layoutRows();changed(true)})()")
    ok(not logs, 'no console errors', logs[:5])
    print(f'{N[0] - len(FAIL)} of {N[0]} checks passed'); sys.exit(1 if FAIL else 0)
