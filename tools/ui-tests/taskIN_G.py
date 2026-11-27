"""Task IN-G (lane E): the dynamics displays, the user's picks G1 (gain reduction history), G3 (transfer curve with a live point) and
G4 (per-band gain reduction).
Checks the compressor's drawn curve against Chromium's DynamicsCompressor measured offline (square waves at known levels, several settings),
the live point and its caliper with a 1 kHz sine at -6 dBFS, the G1 history (input, output, reduction, numbers) on the Compressor, Limiter
(+6 dB into a -1 dB ceiling), Gate (tone bursts) and Ducker, the G4 bars on the studio scale (first dB widest, falls 25 dB/s, tick held 2 s)
on OTT, Multiband Dynamics and the De-Esser with pink noise (bars equal the reductions the devices report, band edges), the Light level
(no trail), nothing drawn when hidden or in the background freeze, no audio nodes in the block, no console errors. Screenshots dark and Light.
  python3 tools/ui-tests/taskIN_G.py [repo dir] [out dir]"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ck(name, ok, info=''):
    N[0] += 1
    if ok: N[1] += 1; print('  ok  ', name, info if info != '' else '')
    else: FAIL.append(name); print('  FAIL', name, info)

al = AudioLab(os.path.join(ROOT, 'index.html'), 2194, 1139); al.start(); pg = al.page
ERR = []; pg.on('console', lambda m: ERR.append(m.text) if m.type == 'error' else None); pg.on('pageerror', lambda e: ERR.append(str(e)))
R0 = al.run
def R(c):
    v = R0(c)
    return v.replace(' ', ' ') if isinstance(v, str) else v
print('version', al.version)
R("UI.lite=false;0")
ck('IN-G is there', R("typeof INS.grh==='function'&&typeof ingBar==='function'&&vizComp.toString().includes('ingComp')&&vizOTT.toString().includes('ingOTT')"))

# 1. the drawn curve against Chromium's compressor, measured offline (square waves: the level is the peak and the mean)
CUR = r"""(async()=>{const out=[];for(const[T,Rt]of[[-18,4],[-30,8],[-10,2]]){for(const lv of[-40,-24,-18,-16,-14,-12,-9,-6,-3,0]){const sr=48000,c=new OfflineAudioContext(1,sr*2,sr);const o=c.createOscillator();o.type='square';o.frequency.value=500;const g=c.createGain();g.gain.value=Math.pow(10,lv/20)/1.18;const k=c.createDynamicsCompressor();k.threshold.value=T;k.ratio.value=Rt;k.knee.value=6;k.attack.value=.01;k.release.value=.2;o.connect(g);g.connect(k);k.connect(c.destination);o.start();const b=await c.startRendering();const d=b.getChannelData(0);let mi=0,mo=0;for(let i=sr;i<2*sr;i++){mo=Math.max(mo,Math.abs(d[i]))}
  const c2=new OfflineAudioContext(1,sr,sr),o2=c2.createOscillator();o2.type='square';o2.frequency.value=500;const g2=c2.createGain();g2.gain.value=Math.pow(10,lv/20)/1.18;o2.connect(g2);g2.connect(c2.destination);o2.start();const b2=await c2.startRendering(),d2=b2.getChannelData(0);for(let i=sr/2;i<sr;i++)mi=Math.max(mi,Math.abs(d2[i]));
  const xin=20*Math.log10(mi),red=k.reduction,mk=-.6*ingRed(0,T,Rt,6);out.push([T,Rt,lv,+xin.toFixed(2),+red.toFixed(2),+ingRed(xin,T,Rt,6).toFixed(2),+(20*Math.log10(mo)).toFixed(2),+(xin+ingRed(xin,T,Rt,6)+mk).toFixed(2)])}}return JSON.stringify(out)})()"""
C = json.loads(pg.evaluate("async c=>await eval(c)", CUR))
dred = max(abs(r[4] - r[5]) for r in C); dout = max(abs(r[6] - r[7]) for r in C)
for r in C: print('    T %d R %g in %.2f: reduction %.2f, drawn %.2f; out %.2f, drawn %.2f' % (r[0], r[1], r[3], r[4], r[5], r[6], r[7]))
ck('the drawn curve (Chromium\'s knee and ratio) equals Chromium\'s reduction within %.2f dB at 3 settings and 10 levels (the knee within 0.05; above it the reported reduction is 1 to 2 %% shallower)' % dred, dred < .35, dred)
ck('the history\'s output (input + reduction + Chromium\'s own make-up) equals the measured output within %.2f dB' % dout, dout < .45, dout)

# test signals
SR = int(R('ctx.sampleRate')); n = int(30 * SR); t = np.arange(n) / SR
sine = (10 ** (-6 / 20) * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
rng = np.random.default_rng(1)
wn = rng.standard_normal(n); f = np.fft.rfftfreq(n, 1 / SR); X = np.fft.rfft(wn); X[1:] /= np.sqrt(f[1:]); X[0] = 0; pk = np.fft.irfft(X, n)
pk = (pk / np.sqrt(np.mean(pk ** 2)) * 10 ** (-20 / 20)).astype(np.float32)
burst = (10 ** (-20 / 20) * np.sin(2 * np.pi * 300 * t) * ((t % 1.0) < .5)).astype(np.float32)
R("UI.headroom=-6;UI.bitPerfect=false;UI.limiter=false;0")
ids = {'Sine': al.add_audio(np.vstack([sine, sine]), SR), 'Pink': al.add_audio(np.vstack([pk, pk]), SR), 'Burst': al.add_audio(np.vstack([burst, burst]), SR)}
def play(name, fx, wait=1500):
    R("stop();0")
    al.build({'bpm': 120, 'master': 20 * math.log10(2), 'tracks': [{'kind': 'audio', 'name': name, 'vol': 1.0, 'clips': [{'start': 0, 'len': 60, 'name': name, 'buf': ids[name]}], 'fx': fx}]})
    R("UI.limiter=false;routeMaster();stop();pos=0;toggle();selectTrack(S.tracks[0].id);renderFx();0"); pg.wait_for_timeout(wait)
# draw one device display into a test canvas, recording texts, G1 results and G4 bars
CAP = r"""(()=>{const txt=[],grh=[],bars=[],arcs=[0];const oh=INS.grh,ob=ingBar;INS.grh=function(g,x0,y0,w,h,o){const r=oh.apply(this,arguments);grh.push({r,top:o.top,bot:o.bot,x0,w});return r};ingBar=function(g,x,y0,bw,h,st,gr){const q=ob.apply(this,arguments);bars.push({gr,d:q.d,h:q.h});return q};
  const c=document.createElement('canvas');c.width=%d*2;c.height=%d*2;const g=c.getContext('2d');g.setTransform(2,0,0,2,0,0);const ft=g.fillText.bind(g);g.fillText=(s,x,y)=>{txt.push([String(s),x,y]);return ft(s,x,y)};const oa=g.arc.bind(g);g.arc=function(){arcs[0]++;return oa.apply(null,arguments)};
  const f=S.tracks[0].fx[0],X=vizInst(f);try{const W=%d,H=%d;if(f.type==='comp')vizComp(g,W,H,f,X);else if(f.type==='ott')vizOTT(g,W,H,f,X);else VIZX[f.type](g,W,H,f,X)}finally{INS.grh=oh;ingBar=ob}
  return JSON.stringify({txt,grh,bars,arcs:arcs[0],tr:(INSG.st.get(f.id+'|c')||{}).tr||[]})})()"""
def cap(w=520, h=200): return json.loads(R(CAP % (w, h, w, h)))
def shot(name):
    try: pg.locator('canvas.viz').nth(0).screenshot(path=os.path.join(OUT, name))
    except Exception as e: print('   (shot)', e)

# 2. compressor, live, 1 kHz sine at -6 dBFS: threshold -18, 4:1
play('Sine', [{'type': 'comp', 'p': {'threshold': -18, 'ratio': 4, 'attack': 10, 'release': 200, 'makeup': 0}}], 2500)
D = cap(); tr = D['tr']
xin, xo = (tr[-2], tr[-1]) if len(tr) >= 2 else (-99, -99)
red = R("vizInst(S.tracks[0].fx[0]).k.reduction"); model = R("ingRed(-6,-18,4,6)")
print('    live point', round(xin, 2), round(xo, 2), 'reduction', round(red, 2), 'curve', round(model, 2))
ck('the live point sits at the input peak (-6.0 dBFS) and the reduction the compressor reports (%.2f dB)' % red, abs(xin + 6) < .15 and abs((xo - xin) - red) < .05, (xin, xo))
ck('the point rides the drawn curve (%.2f against %.2f dB)' % (xo - xin, model), abs((xo - xin) - model) < .2)
T = [x[0] for x in D['txt']]
cal = [x for x in D['txt'] if x[0].endswith(' dB') and x[0].startswith('−') and len(x[0]) < 9]
ck('the amber caliper to the 1:1 line gives the reduction with its number', any(abs(float(x[0].split()[0].replace('−', '-')) - red) < .06 for x in cal), cal)
ck('grid labels every 12 dB with real minus signs, IN dBFS, the threshold and ratio in the title', all(s in T for s in ('−48', '−36', '−24', '−12', 'IN dBFS')) and '−18.0 dB · 4.0:1' in T, [s for s in T if s.startswith('−')][:12])
g1 = D['grh'][0]['r'] if D['grh'] else {}
ck('G1 history on the compressor: reduction now %.2f, most in 4 s %.2f, scale 0 to %d dBFS' % (g1.get('now', 0), g1.get('mx', 0), D['grh'][0]['bot'] if D['grh'] else 0), D['grh'] and abs(g1['now'] - red) < .3 and g1['mx'] <= g1['now'] + .01 and D['grh'][0]['bot'] == -30)
ck('the big number and the 4 s maximum are drawn', any(s.startswith('max −') and s.endswith(' in 4 s') for s in T) and any(abs(float(s.replace('−', '-')) - red) < .06 for s in T if s.replace('−', '').replace('.', '').isdigit() and s.startswith('−')), [s for s in T if 'max' in s])
nn = len(tr) // 2
ck('a short trail of 30 points', nn == 30 and D['arcs'] >= 30, (nn, D['arcs']))
shot('inG_comp.png')
R("UI.lite=true;0"); pg.wait_for_timeout(300); DL = cap(); R("UI.lite=false;0")
ck('the Light level draws no trail (%d dots against %d)' % (DL['arcs'], D['arcs']), DL['arcs'] <= 2 and D['arcs'] > 25)
R("UI.lite=true;0"); pg.wait_for_timeout(600); shot('inG_comp_light.png'); R("UI.lite=false;0")

# hidden and frozen: nothing drawn (the app's heartbeat aoEval is held during the probe: headless, it takes the page for a front window and wakes it)
R("window.__gc=0;window.__go=INS.grh;INS.grh=function(){__gc++;return __go.apply(this,arguments)};0"); pg.wait_for_timeout(1000); open_n = R("__gc")
fz = pg.evaluate("()=>new Promise(r=>{const Q=c=>window.AudioLab.run(c);Q('window.__ae=aoEval;aoEval=()=>0;aoLevel(1);0');setTimeout(()=>{const n0=Q('__gc');setTimeout(()=>{const n1=Q('__gc');Q('aoEval=__ae;aoFront(\\'test\\');0');r(n1-n0)},900)},300)})")
R("S.tracks[0].fx=[];renderFx();0"); pg.wait_for_timeout(300); R("__gc=0;0"); pg.wait_for_timeout(1000); closed_n = R("__gc"); R("INS.grh=__go;0")
ck('the display draws while shown (%d in 1 s), not in the background freeze (%d), nothing when no panel is shown (%d)' % (open_n, fz, closed_n), open_n > 20 and fz == 0 and closed_n == 0, (open_n, fz, closed_n))

# 3. limiter: the sine +6 dB into a -1 dB ceiling
play('Sine', [{'type': 'limit', 'p': {'gain': 6, 'ceil': -1, 'rel': 120, 'look': 2, 'out': 0}}], 5200)
D = cap(); g1 = D['grh'][0]['r'] if D['grh'] else {}
H = json.loads(R("JSON.stringify(vizInst(S.tracks[0].fx[0]).H.slice(-20).map(q=>[toDb(q.i),toDb(q.o),toDb(q.g)]))"))
mi = np.mean([h[0] for h in H]); mo = np.mean([h[1] for h in H]); mg = np.mean([h[2] for h in H])
print('    limiter in %.2f out %.2f gr %.2f; drawn now %.2f max %.2f' % (mi, mo, mg, g1.get('now', 0), g1.get('mx', 0)))
ck('Limiter: input 0 dBFS, output at the ceiling, about 1 dB of reduction, as G1 reads (now %.2f dB)' % g1.get('now', 0), abs(mi) < .3 and mo <= -.95 and abs(g1.get('now', 0) - mg) < .3 and -1.6 < g1.get('now', 0) < -.7)
T = [x[0] for x in D['txt']]
ck('Limiter: dBFS scale on the left, GR scale on the right, the numbers, the ceiling', all(s in T for s in ('−24', '−6', 'dBFS', 'GR', 'ceiling −1.0 dB')) and any(s.startswith('max ') for s in T), [s for s in T][:30])
ck('Limiter: the history spans 4 s (%d messages of 1024 samples)' % len(R("vizInst(S.tracks[0].fx[0]).H.map(q=>0)")), len(R("vizInst(S.tracks[0].fx[0]).H.map(q=>0)")) * 1024 / SR > 4)
ck('Limiter: the handles keep their places (ceiling at its line)', abs(R("HND.limit(S.tracks[0].fx[0].p,520,200)[0].y") - (10 + (1 - (29 / 33)) * 178)) < .01)
shot('inG_limit.png')

# 4. gate: tone bursts at -20 dBFS, threshold -40
play('Burst', [{'type': 'gate', 'p': {'thr': -40, 'hyst': 4, 'floor': -80, 'att': 1, 'hold': 40, 'rel': 60}}], 4800)
D = cap(540, 200)
G = json.loads(R("JSON.stringify(vizInst(S.tracks[0].fx[0]).H.map(q=>[q.lv,toDb(q.g),q.open]))"))
op = [g for g in G if g[2]]; cl = [g for g in G if not g[2] and g[1] < -40]
ck('Gate: 4 s of history kept (%d messages, %.1f s)' % (len(G), len(G) * 512 / SR), len(G) * 512 / SR > 4)
ck('Gate: open while the tone plays (0 dB reduction), closed in the gaps (falling toward the -80 dB floor with its 60 ms release)', op and cl and float(np.median([abs(g[1]) for g in op])) < .5 and len(cl) > 20, (len(op), len(cl)))
g1 = D['grh'][0]['r'] if D['grh'] else {}
ck('Gate: G1 on its -80 to 0 scale, the most in 4 s (%.1f dB) is the deepest the gate went (%.1f dB)' % (g1.get('mx', 0), min(g[1] for g in G)), D['grh'] and D['grh'][0]['bot'] == -80 and abs(g1.get('mx', 0) - min(g[1] for g in G[-int(4 * SR / 512):])) < .5)
T = [x[0] for x in D['txt']]
ck('Gate: its lines, open mark and envelope stay', any(s.startswith('open ') for s in T) and ('OPEN' in T or 'CLOSED' in T) and 'ATK' in T and 'REL' in T, [s for s in T if s.isupper()])
shot('inG_gate.png')

# 5. ducker (its display, fed known values: half gain is -6.0 dB)
DK = R(r"""(()=>{const f={id:'dk1',type:'duck',p:{th:-30}},X={H:{k:new Float32Array(400).fill(.3),g:new Float32Array(400).fill(.5),i:0},m:{k:.3,g:.5,t:performance.now()}};const rec=[];const oh=INS.grh;INS.grh=function(){const r=oh.apply(this,arguments);rec.push(r);return r};const c=document.createElement('canvas');c.width=1040;c.height=360;const g=c.getContext('2d');g.setTransform(2,0,0,2,0,0);try{abxPaint(g,520,180,f,X,true)}finally{INS.grh=oh}return JSON.stringify(rec)})()""")
DK = json.loads(DK)
ck('Ducker: the reduction in dB on the trigger\'s scale (half gain reads %.2f dB), 4 s of history' % (DK[0]['now'] if DK else 0), DK and abs(DK[0]['now'] + 6.02) < .02 and 'Float32Array(400)' in open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read())

# 6. G4 bars: the scale and the ballistics
B = json.loads(R(r"""(()=>{const st={};const c=document.createElement('canvas'),g=c.getContext('2d');const t0=performance.now();let o=[];const P=performance.now.bind(performance);let tt=t0;performance.now=()=>tt;try{ingBar(g,10,0,10,100,st,10,'#f00');for(let i=1;i<=24;i++){tt=t0+i*1000/60;ingBar(g,10,0,10,100,st,0,'#f00')}o.push(st.d,st.h);for(let i=25;i<=150;i++){tt=t0+i*1000/60;ingBar(g,10,0,10,100,st,0,'#f00')}o.push(st.d,st.h)}finally{performance.now=P}return JSON.stringify([ingGY(1,0,100),ingGY(3,0,100),ingGY(10,0,100),ingGY(30,0,100)].concat(o))})()"""))
print('    scale', B[:4], 'after 0.4 s', B[4:6], 'after 2.5 s', B[6:8])
ck('G4 scale: the first dB gets %.0f %% of the bar, 3 dB %.0f %%, 10 dB %.0f %%, 30 dB all' % (B[0], B[1], B[2]), abs(B[0] - 18.26) < .1 and abs(B[3] - 100) < .01)
ck('G4 ballistics: falls 25 dB/s (10 dB gone in 0.4 s), the tick held 2 s then falls', B[4] < .01 and abs(B[5] - 10) < .01 and B[7] < 9)

# 7. OTT, Multiband, De-Esser with pink noise
play('Pink', [{'type': 'ott', 'p': {'depth': 100, 'time': 120, 'up': 70, 'down': 75}}], 2000)
D = cap(520, 200); red = R("JSON.stringify(vizInst(S.tracks[0].fx[0]).comps.map(c=>c.reduction))"); red = json.loads(red)
print('    OTT bars', [round(b['gr'], 2) for b in D['bars']], 'reported', [round(-r, 2) for r in red])
T = [x[0] for x in D['txt']]
ck('OTT: one bar per band: each bar shows the reading it was given (it rises at once), and that reading is the band\'s reduction (read a moment later, within 1 dB)', len(D['bars']) == 3 and all(abs(b['d'] - b['gr']) < .01 or b['d'] > b['gr'] for b in D['bars']) and all(abs(b['gr'] + r) < 1.0 for b, r in zip(D['bars'], red)), [(round(b['gr'], 2), round(b['d'], 2), round(-r, 2)) for b, r in zip(D['bars'], red)])
ck('OTT: the band edges and the numbers', all(s in T for s in ('< 120 Hz', '120 Hz to 2.5 kHz', '> 2.5 kHz', '0', '1', '3', '10', '30')), T[:40])
shot('inG_ott.png')
play('Pink', [{'type': 'mband', 'p': {'t1': -40, 't2': -40, 't3': -40, 'r1': 4, 'r2': 4, 'r3': 4}}], 2000)
D = cap(580, 200); red = json.loads(R("JSON.stringify(vizInst(S.tracks[0].fx[0]).B.map(b=>b.comp.reduction))"))
T = [x[0] for x in D['txt']]
print('    Multiband bars', [round(b['gr'], 2) for b in D['bars']], 'reported', [round(-r, 2) for r in red])
ck('Multiband: three bars with the bands\' reductions (%s dB)' % ', '.join('%.1f' % -r for r in red), len(D['bars']) == 3 and all(abs(b['gr'] + r) < .6 for b, r in zip(D['bars'], red)) and max(-r for r in red) > 1)
XO = json.loads(R("JSON.stringify([S.tracks[0].fx[0].p.x1,S.tracks[0].fx[0].p.x2])"))
E1 = R('ingHz(%r)' % XO[0]); E2 = R('ingHz(%r)' % XO[1])
ck('Multiband: the band edges from its crossovers (%s Hz and %s Hz)' % (E1, E2), all(s in T for s in ('<' + E1, E1 + '-' + E2, '>' + E2, 'GR dB')), [s for s in T if 'k' in s or '<' in s])
shot('inG_mband.png')
play('Pink', [{'type': 'deess', 'p': {'freq': 6500, 'q': 1.5, 'thr': -50, 'ratio': 4, 'range': 12}}], 4800)
D = cap(560, 200); H = json.loads(R("JSON.stringify(vizInst(S.tracks[0].fx[0]).H.slice(-1).map(q=>q.gr))"))
T = [x[0] for x in D['txt']]
ck('De-Esser: the bar reads the reduction (%.1f dB), 4 s of history (%d messages)' % (D['bars'][0]['gr'] if D['bars'] else 0, len(R("vizInst(S.tracks[0].fx[0]).H.map(q=>0)"))), D['bars'] and abs(D['bars'][0]['gr'] - H[0]) < .01 and H[0] > .5 and len(R("vizInst(S.tracks[0].fx[0]).H.map(q=>0)")) * 512 / SR > 4)
ck('De-Esser: the band\'s edges (Q 1.5 at 6.5 kHz: 4.7 to 9.0 kHz)', '4.7-9.0 kHz' in T, [s for s in T if 'kHz' in s])
shot('inG_deess.png')
R("UI.lite=true;0"); pg.wait_for_timeout(600); shot('inG_deess_light.png'); R("UI.lite=false;stop();0")

src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
b0 = src.find('/* ===== lane E (task IN-G)'); b1 = src.find('/* ===== end of lane E IN-G')
ck('no audio nodes made by the block; no em dashes in its text', b0 > 0 and not any(k in src[b0:b1] for k in ('createGain', 'createBiquad', 'createAnalyser', 'audioWorklet', '.connect(', 'wk(')) and '—' not in src[b0:b1])
ck('no console errors', not ERR, ERR[:5])
al.stop() if hasattr(al, 'stop') else None
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
