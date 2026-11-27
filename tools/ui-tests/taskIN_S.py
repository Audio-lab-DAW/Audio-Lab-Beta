"""Task IN-S (lane E): the spectrum, the user's pick S2 (the analyzer front panel).
Checks the drawer INS.spec with a made-up analyser (known peaks): the 10 by 10 graticule, REF on the top line and dB/div, START, STOP, RBW (the
Blackman window's 1.73 bins), AVG, DET; marker 1 on the strongest peak and the delta marker on the next with their read-outs, trace 1 yellow live,
trace 2 cyan max hold, the hold's fall in dB/s, averaging by time, the tilt, silence, the three sizes. Then live with signals played through the
app: a 1 kHz sine at -18 dBFS reads 1.00 kHz and -18.0 dBFS on marker 1 (the level calibrated so a sine reads its peak level), a log sweep at
-12 dBFS leaves a flat max hold, a correlated pair reads its level and an anti-phase pair cancels (the analyser reads the mono sum, as before);
the Spectrum device (its dots, Hold ref, FFT size), the analyser overlay (picture where it was, sources, Peak), the Visualizer (no max hold and
half rate at the Light level), the mixer's spec view (bars kept, decade marks); nothing drawn while closed or in the background freeze; no
console errors. Screenshots in the dark look and at the Light level.
  python3 tools/ui-tests/taskIN_S.py [repo dir] [out dir]"""
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
R = al.run
print('version', al.version)
R("UI.lite=false;0")  # the headless app starts at the Light level; the normal level first
ck('IN-S is there (INS.spec, INS.an; the overlay and the Visualizer draw through it)', R("typeof INS.spec==='function'&&typeof INS.an==='function'&&ANZD.spec===insSpoSpec&&(VZD.fft===insVzSpec||typeof INV==='object'&&VZD.fft===INV.fft)/* IN-V draws the same panel through INV.fft, with the menu tilt and hold */"))

# ---------- 1. the drawer with a made-up analyser ----------
FAKE = r"""
window.__fk=(peaks)=>{/* a made-up analyser: noise floor at -130, each peak a parabola in dB (its top between bins, like a real window) */const sr=ctx.sampleRate,n=4096,bh=sr/2/n;
  const an={fftSize:8192,frequencyBinCount:n,smoothingTimeConstant:0,peaks,getFloatFrequencyData(b){b.fill(-130);for(const[f,db] of this.peaks){const k0=f/bh,raw=db-INS.SPCAL;for(let k=Math.floor(k0)-2;k<=Math.ceil(k0)+2;k++)if(k>0&&k<n)b[k]=Math.max(b[k],raw-3*(k-k0)*(k-k0))}}};return an};
window.__dr=(an,o,W,H)=>{const c=document.createElement('canvas');c.width=W||600;c.height=H||260;const g=c.getContext('2d');g.fillStyle='#000';g.fillRect(0,0,c.width,c.height);
  const seen=[],f=g.fillText.bind(g);g.fillText=(t,x,y)=>{seen.push([String(t),x,y]);return f(t,x,y)};const gr=INS.graticule,ga=[];INS.graticule=function(){ga.push(arguments[5]);return gr.apply(this,arguments)};
  let r;try{an._insFf=-1;r=INS.spec(g,0,0,c.width,c.height,Object.assign({tr:[{an,hold:true,st:o.tst||(o.tst={})}],st:o.pst||(o.pst={})},o))}finally{INS.graticule=gr}
  const px=(x,y)=>Array.from(g.getImageData(Math.floor(x),Math.floor(y),1,1).data.slice(0,3));return{r,seen,ga,px,g,c}};0"""
R(FAKE)
D = json.loads(R(r"""(()=>{const an=__fk([[1000,-18],[3000,-30]]),o={lo:20,hi:20000,top:0,bot:-100};const d=__dr(an,o);const r=d.r,mk=r.mk,txt=d.seen.map(s=>s[0]).join('|');
  const near=(c,v)=>{let best=null;for(let dx=-2;dx<=2;dx++)for(let dy=-4;dy<=2;dy++){const p=d.px(r.gx+mk.a+.5+c+dx,r.Y(v)+dy);if(!best||p[0]+p[1]-p[2]>best[0]+best[1]-best[2])best=p}return best};
  return JSON.stringify({mk,txt,ga:d.ga,gx:r.gx,gy:r.gy,gw:r.gw,gh:r.gh,y0:r.Y(0),y100:r.Y(-100),y50:r.Y(-50),pk:near(0,-18),rbw:INS.rbw(an,ctx.sampleRate),sr:ctx.sampleRate,
    out:d.seen.filter(s=>s[1]<-1||s[1]>601||s[2]<0||s[2]>261).length})})()"""))
print('   ', {k: D[k] for k in ('mk', 'ga', 'gx', 'gy', 'gw', 'gh', 'rbw')})
ck('graticule 10 by 10 (IN-A drawer)', D['ga'] and D['ga'][0].get('nx') == 10 and D['ga'][0].get('ny') == 10, D['ga'])
ck('REF on the top line, 10 dB per division (0 dBFS at the top, -50 in the middle, -100 at the bottom)', abs(D['y0'] - D['gy']) < .01 and abs(D['y100'] - D['gy'] - D['gh']) < .01 and abs(D['y50'] - D['gy'] - D['gh'] / 2) < .01)
ck('front-panel text: REF 0.0 dBFS, 10 dB/div, START 20 Hz, LOG, STOP 20.0 kHz, RBW, AVG OFF, DET PEAK, 1 CLRW, 2 MAXH',
   all(k in D['txt'] for k in ('REF |0.0| dBFS', '10 |dB/div', 'START |20.0| Hz', 'LOG', 'STOP |20.0| kHz', 'RBW ', 'AVG |OFF', 'DET |PEAK', '1 CLRW', '2 MAXH')), D['txt'][:400])
rbw = 1.73 * D['sr'] / 8192
ck('RBW is the Blackman window\'s noise bandwidth: 1.73 x rate / FFT size', abs(D['rbw'] - rbw) < 1e-6 and ('%.2f' % rbw) in D['txt'].replace('|', ''), (D['rbw'], rbw))
mk = D['mk']
ck('marker 1 on the strongest peak: 1.00 kHz, -18.0 dBFS (the bins\' parabola, not the column)', abs(mk['af'] - 1000) < 1.5 and abs(mk['av'] + 18) < .06, (mk['af'], mk['av']))
ck('delta marker on the next peak: 3.00 kHz, -30.0 dBFS; the read-out says +2.00 kHz and -12.0 dB', abs(mk['bf'] - 3000) < 3 and abs(mk['bv'] + 30) < .06 and 'ΔMKR2 |+2.00| kHz' in D['txt'] and '−12.0| dB' in D['txt'], (mk['bf'], mk['bv']))
ck('marker 1 read-out in the header: MKR1 1.00 kHz with the note, -18.0 dBFS (real minus sign)', 'MKR1 |1.00| kHz' in D['txt'] and '−18.0| dBFS' in D['txt'])
ck('trace 1 (live) is yellow at the peak', D['pk'][0] > 180 and D['pk'][1] > 150 and D['pk'][2] < 120, D['pk'])
ck('all text inside the box', D['out'] == 0, D['out'])
# max hold, its fall, averaging by time, tilt, silence
H = json.loads(R(r"""(()=>{const an=__fk([[1000,-18]]),o={lo:20,hi:20000,top:0,bot:-100};__dr(an,o);const c=o.tst.mk,cl=o.pst.mk.a;an.peaks=[];
  /* tone gone: trace 1 falls to the floor, trace 2 holds -18 (fall 0 = max hold) */const d=__dr(an,o);const r=d.r;const hold=o.tst.mh[cl],live=o.tst.sm[cl];let cy=[0,0,0];for(let dx=-2;dx<=2;dx++)for(let dy=-4;dy<=2;dy++){const p=d.px(r.gx+cl+.5+dx,r.Y(-18)+dy);if(p[2]-p[0]>cy[2]-cy[0])cy=p}
  /* the hold falls at the set rate: 10 dB/s, half a second */o.tr=[{an,hold:true,fall:10,st:o.tst}];an.peaks=[];o.tst.tt=performance.now()-200;__dr(an,o);const fell=o.tst.mh[cl];
  /* averaging by time: 0.1 s, a step from -60 to -18 dBFS, 0.1 s later: -60 e^-1 - 18 (1 - e^-1) */const an2=__fk([[1000,-60]]),o2={lo:20,hi:20000,top:0,bot:-100,tr:[{an:an2,avg:.1,st:{}}]};__dr(an2,o2);an2.peaks=[[1000,-18]];o2.tr[0].st.tt=performance.now()-100;__dr(an2,o2);const avg=o2.pst.mk.av,avgT=o2.tr[0].st.avgT;
  const d2=__dr(an2,o2),txt2=d2.seen.map(s=>s[0]).join('|');
  /* tilt 4.5 dB/oct: a -18 dBFS tone at 2 kHz reads -13.5 */const an3=__fk([[2000,-18]]),o3={lo:20,hi:20000,top:0,bot:-100,tilt:4.5};const d3=__dr(an3,o3);const tl=o3.pst.mk.av,txt3=d3.seen.map(s=>s[0]).join('|');
  /* silence: no trace, no marker; live false: graticule only */const an4=__fk([]);an4.getFloatFrequencyData=b=>b.fill(-Infinity);const o4={};const d4=__dr(an4,o4);let lit=0;const id=d4.g.getImageData(1,14,598,200).data;for(let i=0;i<id.length;i+=4)if(id[i]>200&&id[i+1]>160&&id[i+2]<120)lit++;
  const o5={live:false};__dr(__fk([[1000,-18]]),o5);
  return JSON.stringify({hold,live,cy,fell,avg,avgT,txt2,tl,txt3,sil:o4.pst.mk.a,lit,nolive:o5.pst.mk.a,nolT:o5.tst.tt||0})})()"""))
print('   ', {k: H[k] for k in ('hold', 'live', 'cy', 'fell', 'avg', 'avgT', 'tl', 'sil', 'lit', 'nolive')})
ck('trace 2 (max hold) keeps -18 dBFS after the tone stops, trace 1 falls', abs(H['hold'] + 18) < .5 and H['live'] < -60, (H['hold'], H['live']))
ck('trace 2 is cyan', H['cy'][2] > 150 and H['cy'][1] > 120 and H['cy'][0] < 140, H['cy'])
ck('the hold falls at its rate (10 dB/s for 0.2 s: 2 dB)', abs(H['fell'] - (H['hold'] - 2)) < .3, H['fell'])
e1 = math.exp(-1); want = -60 * e1 - 18 * (1 - e1)
ck('averaging by time: 0.1 s after a step from -60 to -18 dBFS the trace reads %.2f (one time constant)' % want, abs(H['avg'] - want) < .4, H['avg'])
ck('AVG shows the time constant (100 ms)', 'AVG |100| ms' in H['txt2'], H['txt2'][H['txt2'].find('AVG'):H['txt2'].find('AVG') + 20])
ck('tilt 4.5 dB/oct around 1 kHz: a -18 dBFS tone at 2 kHz reads -13.5, the tilt is named', abs(H['tl'] + 13.5) < .06 and 'TILT |4.5| dB/oct' in H['txt3'], H['tl'])
ck('silence: no trace and no marker; not live: graticule only', H['sil'] == -1 and H['lit'] == 0 and H['nolive'] == -1, (H['sil'], H['lit'], H['nolive']))
SZ = json.loads(R(r"""JSON.stringify([[600,260],[300,120],[200,70]].map(([w,h])=>{const o={};const d=__dr(__fk([[1000,-18],[3000,-30]]),o,w,h);const t=d.seen.map(s=>s[0]).join('|');return{t,out:d.seen.filter(s=>s[1]<-1||s[1]>w+1||s[2]<0||s[2]>h+1).length}}))"""))
ck('three sizes: full (two footer rows), mid (one), mini (settings inside the corners); text always inside',
   'ΔMKR2' in SZ[0]['t'] and 'START' in SZ[1]['t'] and 'ΔMKR2' not in SZ[1]['t'] and 'START' not in SZ[2]['t'] and 'REF ' in SZ[2]['t'] and all(s['out'] == 0 for s in SZ), [s['t'][:80] for s in SZ])

# ---------- 2. live ----------
SR = int(R('ctx.sampleRate')); n = int(30 * SR); t = np.arange(n) / SR
A18 = 10 ** (-18 / 20); A12 = 10 ** (-12 / 20)
s1k = A18 * np.sin(2 * np.pi * 1000 * t)
ts = t[:int(12 * SR)]; sw = A12 * np.sin(2 * np.pi * 20 * 10 / math.log(1000) * (np.exp(ts / 10 * math.log(1000)) - 1))  # 20 Hz to 20 kHz in 10 s
sw = np.concatenate([sw[:int(10 * SR)], np.zeros(int(20 * SR))])
R("UI.headroom=-6;UI.bitPerfect=false;UI.limiter=false;0")
THIRD = [31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000]
stp = np.zeros(int(30 * SR))
for j, f0 in enumerate(THIRD):
    a, b = int(j * .35 * SR), int((j * .35 + .33) * SR); tt = np.arange(b - a) / SR; stp[a:b] = A12 * np.sin(2 * np.pi * f0 * tt) * np.minimum(1, np.minimum(tt, (b - a) / SR - tt) / .005)
ids = {'Steps': al.add_audio(np.vstack([stp, stp]).astype(np.float32), SR), 'Sine': al.add_audio(np.vstack([s1k, s1k]).astype(np.float32), SR), 'Anti': al.add_audio(np.vstack([s1k, -s1k]).astype(np.float32), SR),
       'Sweep': al.add_audio(np.vstack([sw, sw]).astype(np.float32), SR)}
SPEC = {'type': 'spec', 'p': {'fft': '8192', 'top': 0, 'floor': -100, 'slope': 0, 'smooth': 0, 'peak': True, 'decay': 0, 'lo': 20, 'hi': 20000}}
def play(name, wait=1500, fx=None):
    R("stop();0")
    al.build({'bpm': 120, 'master': 20 * math.log10(2), 'tracks': [{'kind': 'audio', 'name': name, 'vol': 1.0, 'clips': [{'start': 0, 'len': 60, 'name': name, 'buf': ids[name]}], 'fx': fx or []}]})
    R("UI.limiter=false;routeMaster();stop();pos=0;toggle();selectTrack(S.tracks[0].id);renderFx();0"); pg.wait_for_timeout(wait)
DEV = "(()=>{const f=S.tracks[0].fx[0],X=vizInst(f);return JSON.stringify({mk:X.sp&&X.sp.mk,mh:X.st.mh?Array.from(X.st.mh):null,gw:X.sp&&X.sp.map&&X.sp.map.n,lo:+f.p.lo,hi:+f.p.hi})})()"
play('Sine', 2000, [SPEC])
L = json.loads(R(DEV)); mk = L['mk']
ck('live: Spectrum device, a 1 kHz sine at -18 dBFS: marker 1 reads 1.00 kHz and -18.0 dBFS', abs(mk['af'] - 1000) < 1.5 and abs(mk['av'] + 18) < .2, (mk['af'], mk['av']))
try: pg.locator('canvas.viz').nth(0).screenshot(path=os.path.join(OUT, 'inS_device_sine.png'))
except Exception as e: print('   (shot)', e)
ck('the device\'s dots stay (Top, Floor, Slope, Smoothing) and Hold ref still holds a trace the panel draws', R("(()=>{const f=S.tracks[0].fx[0],X=vizInst(f);const hs=HND.spec(f.p,540,230).map(h=>h.l).join(',');NACT.spec.ref(f);return hs==='Top,Floor,Slope,Smoothing'&&X.ref&&X.ref.length===X.sp.map.n})()"))
ck('the device\'s FFT size goes through INS.an (2048 fast)', R("(()=>{const f=S.tracks[0].fx[0],X=vizInst(f);f.p.fft='2048';X.set(f.p);const ok=X.an.fftSize===2048;f.p.fft='8192';X.set(f.p);return ok&&X.an.fftSize===8192})()"))
play('Anti', 1500, [SPEC])
A = json.loads(R(DEV))
play('Sine', 1500, [SPEC])
B = json.loads(R(DEV))
ck('a correlated pair reads its level; an anti-phase pair cancels (the analyser reads the mono sum of the input, as before)', abs(B['mk']['av'] + 18) < .2 and (A['mk']['a'] < 0 or A['mk']['av'] < -90), (B['mk']['av'], A['mk']))
SP2 = json.loads(json.dumps(SPEC)); SP2['p']['top'] = 0
play('Sweep', 11000, [SP2])
W = json.loads(R(DEV))
mh = np.array(W['mh']); gw = len(mh); fc = 20 * np.power(1000, (np.arange(gw) + .5) / gw)
sel = (fc > 25) & (fc < 100); v = mh[sel]
print('    sweep max hold 25 to 100 Hz: min %.2f at %.1f Hz, max %.2f, median %.2f' % (v.min(), fc[sel][np.argmin(v)], v.max(), np.median(v)))
ck('a log sweep at -12 dBFS (20 Hz to 20 kHz in 10 s) leaves a flat max hold from 25 to 100 Hz: -12 dBFS within -2 / +0.5 dB (window scalloping up to 1.1 dB, columns between two bins, a little sweep smear; higher up the sweep moves more than a bin per 186 ms window and smears, as on any analyser)', v.min() > -14 and v.max() < -11.5, (v.min(), v.max()))
try: pg.locator('canvas.viz').nth(0).screenshot(path=os.path.join(OUT, 'inS_device_sweep.png'))
except Exception as e: print('   (shot)', e)
play('Steps', 10500, [SP2])
W = json.loads(R(DEV)); mh = np.array(W['mh']); gw = len(mh); fc = 20 * np.power(1000, (np.arange(gw) + .5) / gw)
got = []
for f0 in THIRD:
    i = int(np.argmin(abs(fc - f0))); got.append(float(mh[max(0, i - 3):i + 4].max()))
print('    stepped tones (max hold at each):', ' '.join('%g:%.2f' % (f, g) for f, g in zip(THIRD, got)))
ck('stepped 1/3-octave tones at -12 dBFS (31.5 Hz to 16 kHz, IEC 61260 centres): the max hold reads each within -1.2 / +0.3 dB', all(-13.2 < g < -11.7 for g in got), got)

# overlay
play('Sine', 800, [])
R("spoOpen('master');0"); pg.wait_for_timeout(1500)
O = json.loads(R(r"""(()=>{const ov=SPO.list[SPO.list.length-1];const M=ov.ms&&ov.ms.spec;if(!M)return JSON.stringify(null);const r=M.sp;return JSON.stringify({mk:r&&r.mk,ss:Object.keys(M.ss||{}),hold:!!ov.hold,mh:M.ss&&M.ss.master&&M.ss.master.mh?1:0,T0:Math.round(ANZTOP+INS.SPCAL),w:M.w,h:M.h})})()"""))
print('   ', O)
ck('overlay: its spectrum module draws through the panel; marker 1 on the master reads 1.00 kHz, -18 dBFS', O and O['mk'] and abs(O['mk']['af'] - 1000) < 2 and abs(O['mk']['av'] + 18) < .5, O and O['mk'])
# the picture where it was: old y = (top - (raw + tilt)) / 72 of the height with top -24; new (T0 - dBFS) / 72
old = (-24 - (-18 - 13.556)) / 72; new = (O['T0'] - (-18)) / 72 if O else 9
ck('overlay: the steady scale keeps the picture where it was (REF %d dBFS = the old top plus the calibration)' % (O['T0'] if O else 0), abs(old - new) < .01, (old, new))
ck('overlay: Peak shows a hold per source', O and O['hold'] and O['mh'] == 1, O)
try: pg.locator('.spov').last.screenshot(path=os.path.join(OUT, 'inS_overlay.png'))
except Exception as e: print('   (shot)', e)
R("for(const o of SPO.list.slice())spoClose(o);0")

# Visualizer
R("UI.viz=true;UI.vizMode='fft';UI.vizDock='bottom';UI.vizH=260;vizApply();0"); pg.wait_for_timeout(1500)
V = json.loads(R("JSON.stringify({mk:VZ.ins&&VZ.ins.mk,hold:!!(VZ.ins&&VZ.ins.tr&&VZ.ins.tr.mh)})"))
ck('Visualizer: its spectrum is the panel (REF 0 dBFS, 10 dB/div); marker 1 reads 1.00 kHz, -18 dBFS on the master', V['mk'] and abs(V['mk']['af'] - 1000) < 2 and abs(V['mk']['av'] + 18) < .5, V)
try: pg.locator('#vizp').screenshot(path=os.path.join(OUT, 'inS_viz.png'))
except Exception as e: print('   (shot)', e)
R("window.__sc=0;window.__sh=[];const o=INS.spec;INS.spec=function(g,x,y,w,h,q){__sc++;__sh.push(!!(q&&q.tr&&q.tr[0]&&q.tr[0].hold));return o.apply(this,arguments)};window.__so=o;0")
pg.wait_for_timeout(200); R("__sc=0;__sh=[];0"); pg.wait_for_timeout(2000); nN = R("__sc"); hN = R("__sh.every(x=>x)")
R("UI.lite=true;__sc=0;__sh=[];0"); pg.wait_for_timeout(2000); hL = R("__sh.some(x=>x)")
# the rate gate with a 60 Hz screen (this headless browser gives about 30 frames a second): 60 synthetic frames each way
GATE = "(lite=>{UI.lite=lite;const raf=window.requestAnimationFrame;window.requestAnimationFrame=()=>0;__sc=0;const t0=performance.now()+1e5;VZ.last=0;try{for(let i=0;i<60;i++)vizFrame(t0+i*1000/60)}finally{window.requestAnimationFrame=raf}return __sc})"
nN = R(GATE + "(false)"); nL = R(GATE + "(true)")
try: pg.locator('#vizp').screenshot(path=os.path.join(OUT, 'inS_viz_light.png'))
except Exception as e: print('   (shot)', e)
R("UI.lite=false;0")
ck('Visualizer: max hold on normally, none at the Light level', hN and not hL, (hN, hL))
ck('Visualizer at the Light level draws at half the rate (%d against %d in 60 frames of a 60 Hz screen)' % (nL, nN), nN >= 28 and nL <= nN * .7, (nN, nL))
R("UI.viz=false;vizApply();0"); pg.wait_for_timeout(300)

# mixer spec view
R("openMixer();UI.mxView='spec';renderMixer();window.__mt=0;const o2=insMxSpecTicks;insMxSpecTicks=function(){__mt++;return o2.apply(this,arguments)};0"); pg.wait_for_timeout(1200)
MT = R("__mt")
srcm = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
ck('mixer spec view: bars kept (colours, mirror, caps), decade marks drawn on its edge', MT > 5 and "insMxSpecTicks(g,W,H,an)/* IN-S */" in srcm and "mxOpt('spec','caps')" in srcm, MT)
try: pg.locator('#mixWin .mx.master').screenshot(path=os.path.join(OUT, 'inS_mixer_master.png'))
except Exception as e: print('   (shot)', e)
R("UI.mxView='wave';renderMixer();{const w=document.getElementById('mixWin');if(w)w.hidden=true}0")

# nothing drawn when closed or frozen
play('Sine', 800, [SPEC])
R("__sc=0;0"); pg.wait_for_timeout(1000); open_n = R("__sc")
fz = pg.evaluate("()=>new Promise(r=>{const Q=c=>window.AudioLab.run(c);Q('aoLevel(1);0');setTimeout(()=>{const n0=Q('__sc');setTimeout(()=>{const n1=Q('__sc');Q('aoFront(\\'test\\');0');r(n1-n0)},900)},300)})")
R("S.tracks[0].fx=[];renderFx();0"); pg.wait_for_timeout(300); R("__sc=0;0"); pg.wait_for_timeout(1000); closed_n = R("__sc")
ck('the device draws while shown (%d in 1 s), not in the background freeze (%d), nothing when no panel is shown (%d)' % (open_n, fz, closed_n), open_n > 20 and fz == 0 and closed_n == 0, (open_n, fz, closed_n))
R("INS.spec=__so;0")

# light-level screenshot of the device and the source checks
play('Sine', 1200, [SPEC])
R("UI.lite=true;0"); pg.wait_for_timeout(800)
try: pg.locator('canvas.viz').nth(0).screenshot(path=os.path.join(OUT, 'inS_device_light.png'))
except Exception as e: print('   (shot)', e)
R("UI.lite=false;stop();0")
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
b0 = src.find('/* ===== lane E (task IN-S)'); b1 = src.find('/* ===== end of lane E IN-S')
ck('no audio nodes made by the block; no em dashes in its text', b0 > 0 and not any(k in src[b0:b1] for k in ('createGain', 'createBiquad', 'createAnalyser', 'audioWorklet', '.connect(', 'wk(')) and '—' not in src[b0:b1])
ck('no console errors', not ERR, ERR[:5])
al.stop()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
