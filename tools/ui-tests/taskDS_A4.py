#!/usr/bin/env python3
"""Task DS-A4 (design round 2, AW3): audio clips in three bands (lows, mids, highs), analysis once per buffer, cached drawing.
   python3 tools/ui-tests/taskDS_A4.py [index.html] [--shots OUTDIR]
At the user's size (2194 x 1139 CSS px at 1.75x) with Fractals plus a made-up stereo audio clip (kick on the beats: lows,
a voice-like tone on beats 2 and 4: mids, a hat on the off-beats: highs), Dark (glass) and Light. SwiftShader: correctness only."""
import sys, json
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

# 16 beats at the song tempo, stereo 48 kHz: kick (55 Hz, falling) on every beat, tone (220 Hz with harmonics to 1.8 kHz)
# on the second half of beats 2 and 4 of each bar, hat (white noise, 40 ms) on every off-beat
MAKE = r"""(()=>{ensureCtx();const sr=48000,spb=60/S.bpm,len=Math.round(16*spb*sr),b=ctx.createBuffer(2,len,sr);let z=12345;const rn=()=>((z=(z*16807)%2147483647)/2147483647)*2-1;
  for(let c=0;c<2;c++){const d=b.getChannelData(c);for(let i=0;i<len;i++){const t=i/sr,bt=t/spb,ph=bt%1,tb=ph*spb;let v=0;
    v+=.8*Math.exp(-tb*14)*Math.sin(2*Math.PI*(55*tb+60*(1-Math.exp(-tb*30))/30));
    const bb=Math.floor(bt)%4;if((bb===1||bb===3)&&ph>=.5)for(let k=1;k<=8;k++)v+=.22/k*Math.sin(2*Math.PI*220*k*t+c*.3);
    if(ph>=.5&&ph<.5+.04/spb)v+=.35*rn()*Math.exp(-(tb-spb/2)*60);d[i]=v*.8}}
  const id=addBuf(b),t=mkTrack('audio',null,'Band test','#b583ff');S.tracks.unshift(t);const c=mkClip({start:128,len:16,name:'Band test',buf:id,dur:b.duration,gain:0,fi:0,fo:0});t.clips.push(c);
  layoutRows();dirty=true;return{id:c.id,tid:t.id,buf:id}})()"""

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
    f = J("['dsBands','dsBandJob','dsBandCols','dsWaveDraw'].map(n=>typeof window[n])")
    ok(all(x == 'function' for x in f), 'the DS-A4 helpers exist', f)
    old = J("S.tracks.filter(t=>t.clips.some(c=>!c.notes)).length")
    print('Fractals tracks with audio clips:', old)
    m = J(MAKE)
    R("(()=>{V.ppb=25;V.x=127;V.y=0;clampV();dirty=true})()")
    first = J("(()=>{const c=S.tracks[0].clips[0],v=srcView(c);return dsBands(v)===null})()")
    ok(first, 'first ask: no analysis yet (today\'s waveform is drawn meanwhile)')
    pg.wait_for_timeout(3000)
    e = J("(()=>{const v=srcView(S.tracks[0].clips[0]),e=dsBandMap().get(v.peaks);return{ok:e.ok,ms:e.ms,n:e.n,N:e.ch[0].length/3,ch:e.ch.length,len:v.buf.length}})()")
    ok(e['ok'] and e['ch'] == 2 and e['N'] == 2000, 'analysis ready: both channels, the peaks resolution (2000 bins)', e)
    ok(e['n'] >= 2, 'worked out in slices (not one long block)', e['n'])
    # band content at known places: bins at a kick, at the tone, at a hat
    b = J(r"""(()=>{const v=srcView(S.tracks[0].clips[0]),e=dsBandMap().get(v.peaks),A=e.mono,N=A.length/3,at=bt=>{const k=Math.floor(bt/16*N);let r=[0,0,0];for(let q=k;q<k+3;q++)for(let j=0;j<3;j++)r[j]=Math.max(r[j],A[3*q+j]);return r.map(x=>+x.toFixed(3))};
      return{kick:at(4.02),tone:at(5.78),hat:at(6.505)}})()""")
    ok(b['kick'][0] > b['kick'][1] and b['kick'][0] > b['kick'][2], 'at a kick the lows lead', b['kick'])
    ok(b['tone'][1] > b['tone'][0] and b['tone'][1] > b['tone'][2], 'in the tone the mids lead', b['tone'])
    ok(b['hat'][2] > b['hat'][1] * .6 and b['hat'][2] > .1, 'at a hat the highs show', b['hat'])
    # drawn: count calls; nothing per frame while idle; zoom redraws from the stored analysis
    R("(()=>{const f=dsWaveDraw;window.DSN=0;dsWaveDraw=function(){DSN++;return f.apply(this,arguments)}})()")
    R("CLC.clear();dirty=true"); pg.wait_for_timeout(600); n1 = J("DSN")
    ok(n1 >= 1, 'the clip is drawn in bands', n1)
    R("DSN=0"); pg.wait_for_timeout(1500); n2 = J("DSN")
    ok(n2 == 0, 'nothing redrawn while idle', n2)
    jobs0 = e['n']
    R("V.ppb=60;clampV();dirty=true"); pg.wait_for_timeout(600); n3 = J("DSN")
    e2 = J("(()=>{const v=srcView(S.tracks[0].clips[0]),e=dsBandMap().get(v.peaks);return{n:e.n}})()")
    ok(n3 >= 1 and e2['n'] == jobs0, 'zoom: drawn again from the stored analysis, no new analysis', [n3, e2])
    R("V.ppb=25;V.x=127;clampV();dirty=true"); pg.wait_for_timeout(600)
    # pixels: blue (lows) far from the centre at a kick, white near the centre at a hat
    def px(mode):
        return J(r"""(()=>{CLC.clear();drawArr();const d=DPX,g=arr.getContext('2d'),c=S.tracks[0].clips[0],G=clipGeom(0,c),hh=(G.bh-4)/2,cy=G.by+1+hh/2;
          const at=(bt,dy)=>Array.from(g.getImageData(Math.round((X0+(bt-V.x)*V.ppb)*d),Math.round((cy+dy)*d),1,1).data).slice(0,3);
          return{kickOut:[.3,.26,.22,.18].map(f=>at(132.02,-hh*f)).sort((a,b)=>(b[2]-b[0])-(a[2]-a[0]))[0],hatC:at(134.52,0),empty:at(131.85,-hh*.45),bh:G.bh}})()""")
    for mode in ['dark', 'light']:
        R("pmSetOn(%s)" % ('true' if mode == 'light' else 'false')); pg.wait_for_timeout(1200)
        q = px(mode)
        ok(q['kickOut'][2] > q['kickOut'][0] + 25, mode + ': the kick shows in blue (lows)', q)
        ok(min(q['hatC']) > 150, mode + ': the hat shows white at the centre (highs)', q['hatC'])
        if SHOTS:
            import os; os.makedirs(SHOTS, exist_ok=True); clean(pg)
            r = J("(()=>{const a=arr.getBoundingClientRect(),G=clipGeom(0,S.tracks[0].clips[0]);return{x:a.left+X0,y:a.top+G.y-24}})()")
            pg.screenshot(path=f'{SHOTS}/{mode}-a4.png', clip={'x': r['x'], 'y': r['y'], 'width': 900, 'height': 230})
            pg.screenshot(path=f'{SHOTS}/{mode}-a4-win.png')
    R("pmSetOn(false)"); pg.wait_for_timeout(800)
    # other look: today's waveform, no bands
    R("UI.dawLook='fl';applyTheme()"); pg.wait_for_timeout(600); R("DSN=0;CLC.clear();drawArr()")
    ok(J("DSN") == 0 and not J("dsAC3()"), 'FL style: no bands, today\'s waveform', J("DSN"))
    R("delete UI.dawLook;applyTheme()"); pg.wait_for_timeout(600)
        # a muted clip and a clip with a fade still draw; an unloaded buffer falls back
    R("(()=>{const c=S.tracks[0].clips[0];c.fi=1;c.fo=1;c.gain=-6;c.mute=true;CLC.clear();drawArr();c.mute=false;c.fi=0;c.fo=0;c.gain=0;CLC.clear();dirty=true})()")
    nb = J("(()=>{const c=mkClip({start:150,len:4,name:'x',buf:'nope',dur:1,gain:0,fi:0,fo:0});S.tracks[0].clips.push(c);CLC.clear();drawArr();S.tracks[0].clips.pop();dirty=true;return true})()")
    ok(nb, 'a clip whose audio is not loaded still draws its note')
    # remove the test track
    R("(()=>{S.tracks.shift();layoutRows();dirty=true})()")
    ok(not logs, 'no console errors', logs[:5])
    print(f'{N[0] - len(FAIL)} of {N[0]} checks passed'); sys.exit(1 if FAIL else 0)
