"""Task IN-O (lane E): stereo field and phase, the user's picks O0 (today's drawing kept), O1 (marks and afterglow) and O4 (polar view).
Checks with known stereo signals (a mono sine at -6 dBFS, the same left only, an anti-phase pair, independent pink noise): the marks sit
where such samples land on the display's own mapping; the dots, the newest amber dot, the afterglow fading by time (none at the Light level);
the phase bar's value, angle and scale; the polar view's angles, rings and in-phase share against the same sums done here; the Picture choice
in the stereo field's menu; the taps read at 512 in the stereo view only; the master box's value with a real minus and the angle; nothing
drawn when the mixer is closed or in the background freeze; no audio nodes, no console errors. Screenshots dark and Light.
  python3 tools/ui-tests/taskIN_O.py [repo dir] [out dir]"""
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
ck('IN-O is there', R("typeof inoField==='function'&&typeof inoMarks==='function'&&drawMixer.toString().length>0&&String(ANZD.stereo).includes('inoMarks')"))

# 1. the marks against the display's mapping, drawn with known samples into a test canvas (Light level: dots straight on the canvas)
MAP = r"""(sig=>{UI.lite=true;const S0=120,c=document.createElement('canvas');c.width=c.height=S0*2;const g=c.getContext('2d');g.setTransform(2,0,0,2,0,0);g.fillStyle='#000';g.fillRect(0,0,S0,S0);
  const n=512,bl=new Float32Array(n),br=new Float32Array(n),a=Math.pow(10,-6/20);for(let i=0;i<n;i++){const v=a*Math.sin(i/n*2*Math.PI*8);bl[i]=sig==='right'?0:v;br[i]=sig==='left'?0:sig==='anti'?-v:v}
  const H0={b3:[0,0,0]},R=S0/2-3,cx=S0/2,cy=S0/2;inoField(c,g,0,0,S0,cx,cy,R,bl,br,n,'white','#fff',H0);UI.lite=false;
  const d=g.getImageData(0,0,S0*2,S0*2).data;let top=1e9,bot=-1,left=1e9,right=-1;for(let y=0;y<S0*2;y++)for(let x=0;x<S0*2;x++){const k=(y*S0*2+x)*4;if(d[k]+d[k+1]+d[k+2]>200&&!(d[k]>200&&d[k+2]<120)){top=Math.min(top,y);bot=Math.max(bot,y);left=Math.min(left,x);right=Math.max(right,x)}}
  return JSON.stringify({top:top/2,bot:bot/2,left:left/2,right:right/2,cx,cy,R,m6:cy-a*Math.SQRT2*R,d6:a*R/Math.SQRT2})})"""
M = json.loads(R(MAP + "('mono')"))
ck('mono sine at -6 dBFS: the dots reach the -6 dB mark on the M axis (top %.1f, mark %.1f) and stay on the upright line' % (M['top'], M['m6']), abs(M['top'] - M['m6']) < 1.6 and M['right'] - M['left'] < 4, M)
L = json.loads(R(MAP + "('left')"))
ck('left only at -6 dBFS: on the L diagonal (both ways through the centre), reaching the -6 dB tick (%.1f, %.1f against %.1f, %.1f)' % (L['left'], L['top'], L['cx'] - L['d6'], L['cy'] - L['d6']), abs(L['left'] - (L['cx'] - L['d6'])) < 1.6 and abs(L['top'] - (L['cy'] - L['d6'])) < 1.6 and abs(L['right'] - (L['cx'] + L['d6'])) < 2.2 and abs(L['bot'] - (L['cy'] + L['d6'])) < 2.2, L)
A = json.loads(R(MAP + "('anti')"))
ck('anti-phase pair: a flat line through the centre (height %.1f px)' % (A['bot'] - A['top']), A['bot'] - A['top'] <= 3.5 and A['right'] - A['left'] > 40)
TX = R(r"""(()=>{const t=[];const c=document.createElement('canvas');c.width=c.height=240;const g=c.getContext('2d');g.setTransform(2,0,0,2,0,0);const f=g.fillText.bind(g);g.fillText=(s,x,y)=>{t.push(String(s));return f(s,x,y)};inoMarks(g,60,60,57,59);return JSON.stringify(t)})()""")
ck('the marks are labelled 0, −6 and −12 with +S and −S', all(x in json.loads(TX) for x in ('−6', '−12', '+S', '−S')), TX)

# 2. the polar view's geometry and in-phase share
POL = r"""(sig=>{const n=512,bl=new Float32Array(n),br=new Float32Array(n);const rng=(s=>()=>(s=(s*16807)%2147483647)/2147483647)(7);for(let i=0;i<n;i++){const v=.5*Math.sin(i/n*2*Math.PI*8);bl[i]=sig==='pink'?rng()-.5:sig==='right'?0:v;br[i]=sig==='pink'?rng()-.5:sig==='left'?0:sig==='anti'?-v:v}
  mxSet('stereo','pol',true);UI.lite=true;const S0=120,c=document.createElement('canvas');c.width=c.height=S0*2;const g=c.getContext('2d');g.setTransform(2,0,0,2,0,0);const t=[];const f=g.fillText.bind(g);g.fillText=(s,x,y)=>{t.push(String(s));return f(s,x,y)};
  INSO.ip=new WeakMap();inoField(c,g,0,0,S0,60,60,57,bl,br,n,'white','#fff',{b3:[0,0,0]});UI.lite=false;mxSet('stereo','pol',false);
  let ip=0,tot=0;for(let i=0;i<n;i++){let m=(bl[i]+br[i])/2,s=(br[i]-bl[i])/2;if(m<0){m=-m;s=-s}if(Math.hypot(m,s)<1e-5)continue;tot++;if(Math.abs(Math.atan2(s,m))<=.7854)ip++}
  const B=inoPolBox(0,0,S0),P=inoPol(0,.5,B.R),Q=inoPol(Math.PI/4,.5,B.R);return JSON.stringify({t,share:ip/tot,R:B.R,mono:P,left:Q})})"""
for sig, want in (('mono', 100), ('anti', 0), ('left', 100)):
    P = json.loads(R(POL + "('%s')" % sig))
    ck('polar view, %s: in phase %d %% (shown %s)' % (sig, want, [x for x in P['t'] if x.endswith('%')]), ('%d %%' % want) in P['t'])
P = json.loads(R(POL + "('pink')"))
ck('polar view, independent noise: the share shown (%s) is the share of samples within 45 degrees (%.0f %%)' % ([x for x in P['t'] if x.endswith('%')], P['share'] * 100), ('%d %%' % round(P['share'] * 100)) in P['t'])
r6 = P['R'] * (1 + 20 * math.log10(.5) / 48)
ck('polar: a mono sample of -6 dB lies straight up at %.1f px, a left-only one at 45 degrees (rings every 12 dB from -48)' % r6, abs(P['mono'][0]) < 1e-6 and abs(-P['mono'][1] - r6) < .01 and abs(P['left'][0] - r6 / math.sqrt(2)) < .01, (P['mono'], P['left']))

# 3. the phase bar
CB = r"""(v=>{const t=[];const c=document.createElement('canvas');c.width=200;c.height=60;const g=c.getContext('2d');const f=g.fillText.bind(g);g.fillText=(s,x,y)=>{t.push(String(s));return f(s,x,y)};g.font='8px Inter';inoCorr(g,3,20,80,v,'#3ecf8e');return JSON.stringify([t,g.font])})"""
for v, s in ((1, '+1.00  0°'), (-1, '−1.00  180°'), (0, '0.00  90°'), (.5, '+0.50  60°')):
    T, font = json.loads(R(CB + "(%r)" % v))
    ck('phase bar at %+g reads "%s" (value with a real minus, the phase angle), the canvas font put back' % (v, s), s in T and '8px' in font, (T, font))

# 4. afterglow by time
AG = R(r"""(()=>{const c=document.createElement('canvas');c.width=c.height=100;const g=c.getContext('2d');const key={};const P=performance.now.bind(performance);let t=P();performance.now=()=>t;const a=[];
  try{inoLayer(key,g,0,0,50,lg=>{lg.fillStyle='#fff';lg.fillRect(20,20,10,10)});for(let i=1;i<=10;i++){t+=1000/60;inoLayer(key,g,0,0,50,()=>{})}
  const st=INSO.st.get(key);a.push(st.g.getImageData(25,25,1,1).data[3]/255);t+=1000;inoLayer(key,g,0,0,50,()=>{});a.push(st.g.getImageData(25,25,1,1).data[3]/255)}finally{performance.now=P}return JSON.stringify(a)})()""")
AG = json.loads(AG)
ck('afterglow: a dot fades to %.0f %% in 1/6 s (0.82 per 60th: 14 %%) and is gone after a second' % (AG[0] * 100), abs(AG[0] - .82 ** 10) < .03 and AG[1] < .01, AG)

# 5. live in the mixer
SR = int(R('ctx.sampleRate')); n = int(30 * SR); t = np.arange(n) / SR
v = (10 ** (-6 / 20) * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
rng = np.random.default_rng(3); pl = (rng.standard_normal(n) * .1).astype(np.float32); pr = (rng.standard_normal(n) * .1).astype(np.float32)
R("UI.headroom=-6;UI.bitPerfect=false;UI.limiter=false;0")
ids = {'Mono': al.add_audio(np.vstack([v, v]), SR), 'Anti': al.add_audio(np.vstack([v, -v]), SR), 'Left': al.add_audio(np.vstack([v, 0 * v]), SR), 'Pink': al.add_audio(np.vstack([pl, pr]), SR)}
def build(names):
    R("stop();0")
    al.build({'bpm': 120, 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'clips': [{'start': 0, 'len': 60, 'name': k, 'buf': ids[k]}]} for k in names]})
    R("UI.limiter=false;routeMaster();stop();pos=0;toggle();0")
build(['Mono', 'Anti', 'Left', 'Pink'])
R("UI.mxView='stereo';mxSet('stereo','phase',true);mxSet('stereo','pol',false);openMixer();renderMixer();0"); pg.wait_for_timeout(6000)
CO = json.loads(R("JSON.stringify(S.tracks.map(t=>[t.name,(MXH.get(t.id)||{}).co,NODES.get(t.id).aL.fftSize]))"))
print('    correlation per strip', CO)
cmap = {c[0]: c[1] for c in CO}
ck('live correlation (today\'s sums, smoothed): mono +1, anti-phase -1, left only 0, independent noise near 0', cmap['Mono'] > .95 and cmap['Anti'] < -.95 and abs(cmap['Left']) < .05 and abs(cmap['Pink']) < .2, cmap)
ck('the taps stay at 256 samples (low CPU first)', all(c[2] == 256 for c in CO), CO)
R("inoCnt0=INSO.cnt[0];0"); pg.wait_for_timeout(1000); on = R("INSO.cnt[0]-inoCnt0")
ck('the stereo fields draw while the mixer is open (%d in 1 s for 4 strips; the mixer draws every second frame, slow headless at this size)' % on, on > 20)
try: pg.locator('#mixWin').screenshot(path=os.path.join(OUT, 'inO_mixer.png'))
except Exception as e: print('   (shot)', e)
MI = json.loads(R("JSON.stringify(mxMenuItems('stereo').filter(x=>x&&x.label).map(x=>[x.label,!!x.check]))"))
ck('the stereo field\'s menu offers the Picture: Stereo field (checked) or Polar view', ['Stereo field', True] in MI and ['Polar view', False] in MI, MI)
R("mxMenuItems('stereo').find(x=>x&&x.label==='Polar view').act();0"); pg.wait_for_timeout(1500)
ck('choosing Polar view sets it (kept with the other mixer options)', R("!!mxOpt('stereo','pol')"))
try: pg.locator('#mixWin').screenshot(path=os.path.join(OUT, 'inO_mixer_polar.png'))
except Exception as e: print('   (shot)', e)
R("UI.lite=true;0"); pg.wait_for_timeout(1200)
try: pg.locator('#mixWin').screenshot(path=os.path.join(OUT, 'inO_mixer_polar_light.png'))
except Exception as e: print('   (shot)', e)
R("mxSet('stereo','pol',false);0"); pg.wait_for_timeout(1200)
try: pg.locator('#mixWin').screenshot(path=os.path.join(OUT, 'inO_mixer_light.png'))
except Exception as e: print('   (shot)', e)
R("UI.lite=false;0")
# frozen and closed
fz = pg.evaluate("()=>new Promise(r=>{const Q=c=>window.AudioLab.run(c);Q('window.__ae=aoEval;aoEval=()=>0;aoLevel(1);0');setTimeout(()=>{const n0=Q('INSO.cnt[0]');setTimeout(()=>{const n1=Q('INSO.cnt[0]');Q('aoEval=__ae;aoFront(\\'test\\');0');r(n1-n0)},900)},300)})")
R("{const w=document.getElementById('mixWin');if(w)w.hidden=true}0"); pg.wait_for_timeout(300); c0 = R("INSO.cnt[0]"); pg.wait_for_timeout(1000); closed = R("INSO.cnt[0]") - c0
ck('nothing drawn in the background freeze (%d) or with the mixer closed (%d)' % (fz, closed), fz == 0 and closed == 0)
# master box with the anti-phase pair alone
build(['Anti'])
R("UI.mxView='wave';{const w=document.getElementById('mixWin');if(w)w.hidden=false}openMixer();renderMixer();0"); pg.wait_for_timeout(2500)
MB = R("(document.querySelector('#mixWin .mxme .mxco b')||{}).textContent||''")
ck('the master box\'s Stereo value has a real minus and the phase angle (%s; the value is smoothed, the angle near 180 moves fast)' % MB, MB.startswith('−1.00') and MB.endswith('°') and int(MB.split()[-1][:-1]) >= 170, MB)
ck('the master box\'s Stereo bar hatches its negative half', 'repeating-linear-gradient' in R("getComputedStyle(document.querySelector('#mixWin .mxme .mxco .mxbar')).backgroundImage"))
try: pg.locator('#mixWin .mx.master').screenshot(path=os.path.join(OUT, 'inO_master.png'))
except Exception as e: print('   (shot)', e)
R("stop();0")
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
b0 = src.find('/* ===== lane E (task IN-O)'); b1 = src.find('/* ===== end of lane E IN-O')
ck('no audio nodes made by the block; no em dashes in its text', b0 > 0 and not any(k in src[b0:b1] for k in ('createGain', 'createBiquad', 'createAnalyser', 'audioWorklet', '.connect(', 'wk(')) and '—' not in src[b0:b1])
ck('no console errors', not ERR, ERR[:5])
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
