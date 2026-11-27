"""Task IN-C and IN-D (lane E): the CPU graph, the user's pick C1 (load against budget), and the scope preview in devices, pick D1.
C1: the button's graph (green below the 75 % budget, red only above it, the amber budget tick), the pop-up's large graph (scale, dashed budget
line, now, peak of 4 s, ms per frame) kept across the pop-up's rebuilds, the 100 ms history and its 4 s peak.
D1: the Soft Clipper's scope with known signals played through the app (a 1 kHz sine at -6 dBFS reads -6.0 dBFS; 300 ms of columns, a burst of
100 ms in 300 fills a third of them; a sine above full scale gives red marks and a red read-out; the input level and the clipping amount at
the real level), the Bitcrusher's read-out and scale bar, nothing drawn when hidden or in the background freeze, no audio nodes in the block,
no console errors. Screenshots dark and Light.
  python3 tools/ui-tests/taskIN_CD.py [repo dir] [out dir]"""
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
print('    parts', R("JSON.stringify([typeof INC,typeof IND,cpuFrame.toString().includes('INC.tick'),cpuFrame.toString().includes('INC.btn'),cpuPopFill.toString().includes('INC.pop'),VIZX.clip.toString().includes('IND.clip'),VIZX.crush.toString().includes('IND.crush')])"))
ck('IN-C and IN-D are there', R("typeof INC==='object'&&typeof IND==='object'&&cpuFrame.toString().includes('INC.tick')&&cpuFrame.toString().includes('INC.btn')&&(cpuPopFill.toString().includes('INC.pop')||document.documentElement.innerHTML.includes('P.innerHTML=_ph}INC.pop(P)'))&&VIZX.clip.toString().includes('IND.clip')&&VIZX.crush.toString().includes('IND.crush')"))

# ---------- C1: the button's graph ----------
PIX = r"""(()=>{const sv=CPU.hist.slice(),si=CPU.i;CPU.hist.fill(%s);const c=document.createElement('canvas');c.width=72;c.height=36;const g=c.getContext('2d');g.setTransform(2,0,0,2,0,0);try{INC.btn(g,36,18)}finally{CPU.hist.set(sv);CPU.i=si}
  const d=g.getImageData(0,0,72,36).data,px=(x,y)=>Array.from(d.slice((y*72+x)*4,(y*72+x)*4+3));const col=[];for(let y=0;y<36;y++)col.push(px(40,y));return JSON.stringify(col)})()"""
def kind(p):
    r, g_, b = p
    if r > 120 and g_ < 90: return 'R'
    if g_ > r + 25 and g_ > 50: return 'G'
    if r > 150 and g_ > 100 and b < 110: return 'A'
    return '.'
col9 = ''.join(kind(p) for p in json.loads(R(PIX % '.9')))
col5 = ''.join(kind(p) for p in json.loads(R(PIX % '.5')))
print('    column at 90 %:', col9, ' at 50 %:', col5)
ck('button graph at 90 %: red above the budget, amber tick at 75 %, green below', 'R' in col9 and 'G' in col9 and 'A' in col9 and col9.index('R') < col9.index('A') < col9.rindex('G') and col9.rfind('R') < col9.find('G'))
ck('button graph at 50 %: green only (no red under the budget), the tick drawn', 'R' not in col5 and 'G' in col5 and 'A' in col5)
y75 = col5.index('A')
ck('the budget tick sits at 75 %% of the height (row %d of 36)' % y75, abs(y75 - (2 + 32 * .25)) <= 2)

# ---------- C1: the history and its 4 s peak ----------
H = json.loads(R(r"""(()=>{const sv={h:INC.h.slice(),i:INC.i,n:INC.n,li:INC.li,pk:INC.pk};const out=[];try{INC.li=-1;INC.n=0;INC.h.fill(0);for(let k=0;k<60;k++){INC.tick(performance.now(),k===10?.95:k===30?.6:.2)}out.push(INC.pk,INC.n);
  for(let k=0;k<25;k++)INC.tick(performance.now(),.2);out.push(INC.pk)}finally{INC.h.set(sv.h);INC.i=sv.i;INC.n=sv.n;INC.li=sv.li;INC.pk=sv.pk}return JSON.stringify(out)})()"""))
ck('PEAK 4 S is the highest of the last 40 points (0.95 is 49 points old: %.2f; 0.6 gone after 25 more: %.2f)' % (H[0], H[2]), abs(H[0] - .6) < 1e-6 and abs(H[2] - .2) < 1e-6 and H[1] == 60, H)

# ---------- C1: the pop-up ----------
R("const b=$('#cpu');b.click();0"); pg.wait_for_timeout(700)
opened = R("!$('#cpuPop').hidden")
if not opened: R("$('#cpuPop').hidden=false;cpuPopFill();0"); pg.wait_for_timeout(300)
P = json.loads(R("JSON.stringify({c:!!$('#cpuPop .incC'),after:$('#cpuPop .incC')&&$('#cpuPop .incC').previousElementSibling&&$('#cpuPop .incC').previousElementSibling.textContent,w:$('#cpuPop .incC')?$('#cpuPop .incC').clientWidth:0,h:$('#cpuPop .incC')?$('#cpuPop .incC').clientHeight:0})"))
ck('the pop-up shows the large graph under its title (%dx%d)' % (P['w'], P['h']), P['c'] and P['after'] == 'Performance' and P['w'] > 200 and P['h'] > 80, P)
same = R("const c=$('#cpuPop .incC');CPU.drop++;$('#cpuPop')._h='';cpuPopFill();const k=$('#cpuPop .incC');CPU.drop--;k===c&&k.previousElementSibling.textContent==='Performance'")
ck('the graph is kept when the pop-up rebuilds its HTML', same)
T = json.loads(R(r"""(()=>{const c=INC.cv,g=c.getContext('2d'),t=[],sv=g.fillText;g.fillText=function(s,x,y){t.push(String(s));return sv.apply(this,arguments)};try{INC.big()}finally{delete g.fillText}t.push('@'+FPS.js);return JSON.stringify(t)})()"""))
print('    pop-up texts', T)
ck('scale 0, 50, 100 %, the budget label, NOW, PEAK 4 S, MS PER FRAME OF 16.7', all(s in T for s in ('0%', '50%', '100%', 'BUDGET 75 %', 'NOW', 'PEAK 4 S', 'MS', '%')) and any(s.startswith('PER FRAME OF ') for s in T))
ms = float(T.pop()[1:]); fr = [s for s in T if s.replace('.', '').isdigit() and '.' in s]
ck('ms per frame is the main thread\'s own time per frame (FPS.js %.2f)' % (ms or 0), fr and abs(float(fr[0]) - ms) < .3, fr)
n0 = R("window.__bc=0;window.__bo=INC.big;INC.big=function(){__bc++;return __bo.apply(this,arguments)};0"); pg.wait_for_timeout(1000); nb = R("__bc")
ck('the large graph is redrawn 10 times a second while the pop-up is open (%d in 1 s)' % nb, 7 <= nb <= 14)
try: pg.locator('#cpuPop').screenshot(path=os.path.join(OUT, 'inC_pop.png'))
except Exception as e: print('   (shot)', e)
R("$('#cpuPop').hidden=true;0"); pg.wait_for_timeout(300); R("__bc=0;0"); pg.wait_for_timeout(1000); nb2 = R("__bc"); R("INC.big=__bo;0")
ck('nothing drawn for the pop-up while it is closed (%d)' % nb2, nb2 == 0)
try:
    pg.evaluate("()=>{document.body.style.zoom=1}")
    pg.locator('#cpu').screenshot(path=os.path.join(OUT, 'inC_button.png'))
except Exception as e: print('   (shot)', e)

# ---------- D1: test signals ----------
SR = int(R('ctx.sampleRate')); n = int(30 * SR); t = np.arange(n) / SR
def sine(db, f=1000): return (10 ** (db / 20) * np.sin(2 * np.pi * f * t)).astype(np.float32)
s6 = sine(-6); s3 = sine(-3)
burst = (10 ** (-6 / 20) * np.sin(2 * np.pi * 1000 * t) * ((t % .3) < .1)).astype(np.float32)
R("UI.headroom=-6;UI.bitPerfect=false;UI.limiter=false;0")
ids = {k: al.add_audio(np.vstack([v, v]), SR) for k, v in (('S6', s6), ('S3', s3), ('Burst', burst))}
def play(name, fx, wait=1500):
    R("stop();0")
    al.build({'bpm': 120, 'master': 0, 'tracks': [{'kind': 'audio', 'name': name, 'vol': 1.0, 'clips': [{'start': 0, 'len': 60, 'name': name, 'buf': ids[name]}], 'fx': fx}]})
    R("UI.limiter=false;routeMaster();stop();pos=0;toggle();selectTrack(S.tracks[0].id);renderFx();0"); pg.wait_for_timeout(wait)
CAP = r"""(()=>{const txt=[];const c=document.createElement('canvas');c.width=%d*2;c.height=%d*2;const g=c.getContext('2d');g.setTransform(2,0,0,2,0,0);const ft=g.fillText.bind(g);g.fillText=(s,x,y)=>{txt.push(String(s));return ft(s,x,y)};
  const f=S.tracks[0].fx[0],X=vizInst(f);VIZX[f.type](g,%d,%d,f,X);const so=IND.st.get(f.id+(f.type==='clip'?'|o':'|c')),si=IND.st.get(f.id+'|i');
  const sp=s=>{if(!s)return null;let mx=-9,mn=9,lit=0,fs=0;for(let q=0;q<s.cols;q++){if(s.mx[q]>mx)mx=s.mx[q];if(s.mn[q]<mn)mn=s.mn[q];if(s.mx[q]-s.mn[q]>.05)lit++;if(s.fs[q])fs++}return{mx,mn,lit,fs,cols:s.cols,span:s.per*s.cols/s.sr,pk:s.pk.h}};
  return JSON.stringify({txt,o:sp(so),i:sp(si)})})()"""
def cap(w=520, h=200): return json.loads(R(CAP % (w, h, w, h)))
def shot(name):
    try: pg.locator('canvas.viz').nth(0).screenshot(path=os.path.join(OUT, name))
    except Exception as e: print('   (shot)', e)
def num(s): return float(s.replace('−', '-').replace('+', ''))

# 1. Soft Clipper, a 1 kHz sine at -6 dBFS, mix 0 (its dry path: out = in, exactly)
play('S6', [{'type': 'clip', 'p': {'gain': 0, 'thr': 0, 'ceil': -.3, 'bias': 0, 'mix': 0, 'out': 0}}], 1800)
D = cap(); T = D['txt']; o = D['o']; i_ = D['i']
print('    out', o, 'in', i_)
print('    texts', T)
ck('300 ms of min and max columns, one per pixel (%d columns, %.3f s)' % (o['cols'], o['span']), abs(o['span'] - .3) < 1e-9 and 250 < o['cols'] < 400)
ck('the output columns reach the sine\'s peak (%.3f, %.3f; -6 dBFS is 0.501)' % (o['mx'], o['mn']), abs(o['mx'] - .501) < .01 and abs(o['mn'] + .501) < .01 and o['lit'] >= o['cols'] - 2)
ck('the input is shown at its real level (the tap sits at a quarter): %.3f' % i_['mx'], abs(i_['mx'] - .501) < .01)
T = [x.strip() for x in T]; pkt = [T[T.index('PEAK') + 1]] if 'PEAK' in T else []
ck('PEAK %s dBFS read-out (-6.0)' % (pkt[:1],), 'PEAK' in T and 'dBFS' in T and any(abs(num(s) + 6.0) < .06 for s in pkt), pkt)
ck('scale +1, +0.5, 0, −0.5, −1; IN and OUT; the scale bar (50 MS at this width)', all(s in T for s in ('+1', '+0.5', '0', '−0.5', '−1', 'IN', 'OUT')) and '50 MS' in T, [s for s in T if 'MS' in s])
ck('below threshold: no clipping, no full-scale marks', 'below threshold' in T and o['fs'] == 0)
shot('inD_clip.png')
R("UI.lite=true;0"); pg.wait_for_timeout(700); shot('inD_clip_light.png'); R("UI.lite=false;0")

# 2. the same sine into a -18 dB threshold: clipping 12.0 dB at the real input level; the columns equal the analyser's own samples
play('S6', [{'type': 'clip', 'p': {'gain': 0, 'thr': -18, 'ceil': -.3, 'bias': 0, 'mix': 100, 'out': 0}}], 1800)
D = cap(); T = D['txt']
cl = [s for s in T if s.startswith('clipping ')]
ck('clipping amount from the real input level: %s (12.0 dB)' % cl, cl and abs(num(cl[0].split()[1]) - 12.0) < .1)
IR = json.loads(R("(()=>{const X=vizInst(S.tracks[0].fx[0]);let mx=-9,mn=9;const a=new Float32Array(X.anO.fftSize);for(let k=0;k<1;k++){X.anO.getFloatTimeDomainData(a);for(const v of a){if(v>mx)mx=v;if(v<mn)mn=v}}return JSON.stringify([mx,mn])})()"))
ck('the columns hold what the device puts out (columns %.3f, %.3f; its analyser %.3f, %.3f)' % (D['o']['mx'], D['o']['mn'], IR[0], IR[1]), abs(D['o']['mx'] - IR[0]) < .01 and abs(D['o']['mn'] - IR[1]) < .01)
ck('the output is clipped below the input (out %.3f, in %.3f)' % (D['o']['mx'], D['i']['mx']), D['o']['mx'] < D['i']['mx'] - .05)

# 3. a burst of 100 ms every 300 ms fills a third of the 300 ms columns
play('Burst', [{'type': 'clip', 'p': {'gain': 0, 'thr': 0, 'ceil': -.3, 'bias': 0, 'mix': 100, 'out': 0}}], 1800)
fr = []
for k in range(6):
    D = cap(); fr.append(D['o']['lit'] / D['o']['cols']); pg.wait_for_timeout(137)
print('    lit share', [round(x, 3) for x in fr])
ck('a 100 ms burst every 300 ms lights a third of the columns (%.3f to %.3f): the time across is true' % (min(fr), max(fr)), all(abs(x - 1 / 3) < .04 for x in fr))

# 4. above full scale: red marks and a red read-out
play('S3', [{'type': 'clip', 'p': {'gain': 0, 'thr': 0, 'ceil': 0, 'bias': 0, 'mix': 100, 'out': 6}}], 1800)
D = cap(); T = D['txt']; o = D['o']; exp = 20 * math.log10(max(abs(o['mx']), abs(o['mn'])))
T = [x.strip() for x in T]; pk = [T[T.index('PEAK') + 1]] if 'PEAK' in T else []; pk = [x for x in pk if x.startswith('+')]
ck('the output above full scale: red marks at the edge (%d columns), peak %s dBFS (the columns\' highest: %+.1f)' % (o['fs'], pk, exp), o['fs'] >= o['cols'] - 2 and pk and abs(num(pk[0]) - exp) < .1 and exp > 3)
shot('inD_clip_over.png')
R("UI.lite=true;0"); pg.wait_for_timeout(700); shot('inD_clip_over_light.png'); R("UI.lite=false;0")

# 5. Bitcrusher: the staircase stays, the input peak read-out and the scale bar for its window
play('S6', [{'type': 'crush', 'p': {'bits': 6, 'rate': 4}}], 1800)
D = cap(); T = [x.strip() for x in D['txt']]
pkt = [T[T.index('IN PEAK') + 1]] if 'IN PEAK' in T else []
print('    crusher fftSize', R("vizInst(S.tracks[0].fx[0]).an.fftSize"))
ck('Bitcrusher: IN PEAK %s dBFS (-6.0), the scale bar (%s), its own buffer kept (1024)' % (pkt[:1], [s for s in T if 'MS' in s]), 'IN PEAK' in T and pkt and abs(num(pkt[0]) + 6.0) < .06 and any(s.endswith(' MS') for s in T) and R("vizInst(S.tracks[0].fx[0]).an.fftSize") == 1024)
ck('Bitcrusher: its title line stays', any(s.startswith('6-bit') for s in T))
shot('inD_crush.png')

# 6. hidden and frozen: nothing read (the app's heartbeat aoEval held during the probe, as in taskIN_G)
play('S6', [{'type': 'clip', 'p': {'gain': 0, 'thr': 0, 'ceil': -.3, 'bias': 0, 'mix': 100, 'out': 0}}], 800)
R("window.__fc=0;window.__fo=IND.feed;IND.feed=function(){__fc++;return __fo.apply(this,arguments)};0"); pg.wait_for_timeout(1000); open_n = R("__fc")
fz = pg.evaluate("()=>new Promise(r=>{const Q=c=>window.AudioLab.run(c);Q('window.__ae=aoEval;aoEval=()=>0;aoLevel(1);0');setTimeout(()=>{const n0=Q('__fc');setTimeout(()=>{const n1=Q('__fc');Q('aoEval=__ae;aoFront(\\'test\\');0');r(n1-n0)},900)},300)})")
R("S.tracks[0].fx=[];renderFx();0"); pg.wait_for_timeout(300); R("__fc=0;0"); pg.wait_for_timeout(1000); closed_n = R("__fc"); R("IND.feed=__fo;stop();0")
ck('the scope reads while shown (%d in 1 s), not in the background freeze (%d), nothing when no panel is shown (%d)' % (open_n, fz, closed_n), open_n > 20 and fz == 0 and closed_n == 0, (open_n, fz, closed_n))

src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
b0 = src.find('/* ===== lane E (task IN-C and IN-D)'); b1 = src.find('/* ===== end of lane E IN-C and IN-D')
ck('no audio nodes made by the block; no em dashes in its text', b0 > 0 and not any(k in src[b0:b1] for k in ('createGain', 'createBiquad', 'createAnalyser', 'audioWorklet', '.connect(', 'wk(')) and '—' not in src[b0:b1])
ck('no console errors', not ERR, ERR[:5])
al.stop()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
