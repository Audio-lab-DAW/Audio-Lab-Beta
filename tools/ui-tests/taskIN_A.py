"""Task IN-A (lane E): the shared instrument base.
Checks the formatter, the colour maps, the scale drawers, the ballistics against the standards (digital peak IEC 60268-18, VU IEC 60268-17,
PPM type IIb IEC 60268-10, RMS AES17, K-weighting ITU-R BS.1770) with known test signals made in the page, the one-read-per-frame analyser cache,
the meter's "Loudness" reading played live (1 kHz sine at -18 dBFS in both channels reads -18 LUFS like the loudness box; a correlated and an
anti-phase pair; a 10 kHz sine reads higher by the K-weighting), the Sidechain device picture (the double vizSide), the Visualizer docked at the side,
and no console errors. A test sheet of the drawers is drawn and screenshotted in the dark look and at the Light level.
  python3 tools/ui-tests/taskIN_A.py [repo dir] [out dir]"""
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

al = AudioLab(os.path.join(ROOT, 'index.html'), 1600, 1000); al.start(); pg = al.page
R = al.run
print('version', al.version)
ck('INS is there', R("typeof INS==='object'&&typeof INS.fmt==='function'"))

# ---------- 1. the formatter ----------
F = json.loads(R("""JSON.stringify([INS.fmt(12400,'Hz'),INS.fmt(0.0005,'s'),INS.fmt(-3.24,'dB'),INS.fmt(-Infinity,'dBFS'),INS.fmt(2,'LU'),INS.fmt(-0.04,'dB'),
 INS.fmt(440,'Hz'),INS.fmt(1250,'Hz'),INS.fmt(20,'Hz'),INS.fmt(-14.04,'LUFS'),INS.fmt(-1.26,'dBTP'),INS.fmt(4,':1'),INS.fmt(37.6,'%'),INS.hz(440,{note:true}),
 INS.note(261.63).name,Math.round(INS.note(452).ct),INS.fmt(0.0125,'s'),INS.fmt(999.7,'Hz'),INS.parts(-6,'dBFS'),INS.fmt(48000,'Hz'),INS.num(-0.0,1),INS.ucap('\u00b5s')])"""))
TS, MI = ' ', '−'
exp = ['12.4' + TS + 'kHz', '500' + TS + 'µs', MI + '3.2' + TS + 'dB', MI + '∞' + TS + 'dBFS', '+2.0' + TS + 'LU', '0.0' + TS + 'dB',
       '440' + TS + 'Hz', '1.25' + TS + 'kHz', '20.0' + TS + 'Hz', MI + '14.0' + TS + 'LUFS', MI + '1.3' + TS + 'dBTP', '4.00:1', '38%']
ck('formatter: units, SI prefixes, real minus sign, thin space', F[:13] == exp, [(a, b) for a, b in zip(F, exp) if a != b])
ck('formatter: frequency with its note (X8)', F[13] == '440' + TS + 'Hz  A4 +0' + TS + 'ct', F[13])
ck('formatter: note names and cents', F[14] == 'C4' and F[15] == 47, (F[14], F[15]))
ck('formatter: 12.5 ms, 1.00 kHz at the prefix edge, 48.0 kHz', F[16] == '12.5' + TS + 'ms' and F[17] == '1.00' + TS + 'kHz' and F[19] == '48.0' + TS + 'kHz', (F[16], F[17], F[19]))
ck('unit capitals keep the micro sign', F[21] == '\u00b5S', F[21])
ck('formatter: parts for an amber unit apart', F[18] == [MI + '6.0', 'dBFS'] and F[20] == '0.0', (F[18], F[20]))

# ---------- 2. colour maps ----------
L = json.loads(R("JSON.stringify(Object.fromEntries(INS.cmapNames.map(k=>[k,Array.from(INS.cmap(k))])))"))
def near(a, b, t=3): return all(abs(x - y) <= t for x, y in zip(a, b))
ck('viridis ends as matplotlib (68,1,84) to (253,231,37)', near(L['viridis'][:3], [68, 1, 84]) and near(L['viridis'][-3:], [253, 231, 37]), (L['viridis'][:3], L['viridis'][-3:]))
ck('magma and inferno ends', near(L['magma'][:3], [0, 0, 4]) and near(L['magma'][-3:], [252, 253, 191]) and near(L['inferno'][-3:], [252, 255, 164]), (L['magma'][-3:], L['inferno'][-3:]))
try:
    import matplotlib; from matplotlib import colormaps
    err = max(max(abs(L[k][i * 3 + c] - round(colormaps[k](i / 255)[c] * 255)) for i in range(256) for c in range(3)) for k in ('magma', 'inferno', 'viridis'))
    ck('the three maps match matplotlib within 2 levels at all 256 steps', err <= 2, err)
except ImportError:
    pass
def lstar(r, g, b):
    def f(c): c /= 255; return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
    Y = .2126 * f(r) + .7152 * f(g) + .0722 * f(b); return 116 * (Y ** (1 / 3) if Y > .008856 else 7.787 * Y + 16 / 116) - 16
mono = {k: all(lstar(*L[k][(i + 8) * 3:(i + 8) * 3 + 3]) > lstar(*L[k][i * 3:i * 3 + 3]) for i in range(0, 248, 8)) for k in ('magma', 'inferno', 'viridis')}
ck('lightness rises steadily in magma, inferno and viridis', all(mono.values()), mono)
ck("today's heat matches the app's heat colours", R("(()=>{const a=INS.cmap('heat');return [0,.22,.45,.65,.85,1].every(v=>{const q=Math.round(v*255)*3,m=heatCol0(v).match(/\\d+/g).map(Number);return Math.abs(a[q]-m[0])<=3&&Math.abs(a[q+1]-m[1])<=3&&Math.abs(a[q+2]-m[2])<=3})})()"))

# ---------- 3. ballistics with known signals (made in the page, 48 kHz) ----------
B = json.loads(R(r"""(()=>{const sr=48000,o={},sine=(n,f,db)=>{const a=new Float32Array(n),A=Math.pow(10,db/20);for(let i=0;i<n;i++)a[i]=A*Math.sin(2*Math.PI*f*i/sr);return a};
 /* digital peak: one 0 dB hit, then silence, at 60 frames a second */
 {const st={};INS.peak(st,0,1/60);let t=0,at17=null,h19=null,h25=null;while(t<3.5){INS.peak(st,-240,1/60);t+=1/60;if(at17==null&&t>=1.7-1e-9)at17=st.d;if(h19==null&&t>=1.9)h19=st.h;if(h25==null&&t>=2.5)h25=st.h}o.pk={at17,h19,h25,mx:st.mx}}
 /* VU: 1 kHz at -18 dBFS switched on */
 {const st={},a=sine(sr*2,1000,-18);let mx=-1e9,t99=null,vals=[];for(let i=0;i<a.length;i+=48){const v=INS.vu(st,a,i,i+48,sr);vals.push(v);if(v>mx)mx=v}const fin=vals[vals.length-1];
  for(let j=0;j<vals.length;j++){if(t99==null&&Math.pow(10,(vals[j]-fin)/20)>=.99){t99=(j+1)*48/sr}}o.vu={fin,ov:(Math.pow(10,(mx-fin)/20)-1)*100,t99}}
 /* PPM type IIb: a 10 ms burst of 5 kHz at 0 dBFS, then the fall; and a steady sine */
 {const st={},b=sine(480,5000,0),z=new Float32Array(sr*3);const r0=INS.ppm(st,b,0,480,sr);let mx=r0;const r1=INS.ppm(st,z,0,Math.round(2.8*sr),sr);
  const st2={},s=sine(sr,5000,-6);const r2=INS.ppm(st2,s,0,sr,sr);o.ppm={burst:r0,fall:r1,steady:r2}}
 /* RMS AES17 300 ms: -18 dBFS sine reads -18 */
 {const st={},a=sine(sr,1000,-18);o.rms=INS.rms(st,a,0,a.length,sr)}
 /* K-weighted momentary: sines at 1 kHz, 100 Hz, 10 kHz, 25 Hz at -18 dBFS (one channel) */
 o.k={};for(const f of[1000,100,10000,25,4000]){const st={},a=sine(sr,f,-18);o.k[f]=10*Math.log10(INS.kms(st,a,0,a.length,sr))-.691}
 /* the same signal in odd pieces gives the same answer (filter state kept) */
 {const st={},a=sine(sr,10000,-18);let i=0,q=0;while(i<a.length){const n=Math.min(a.length-i,97+(i%1000));q=INS.kms(st,a,i,i+n,sr);i+=n}o.kpieces=10*Math.log10(q)-.691}
 return JSON.stringify(o)})()"""))
print('   ', json.dumps(B))
ck('digital peak falls 20 dB in 1.7 s (11.8 dB/s, IEC 60268-18)', abs(B['pk']['at17'] + 20) < 0.25, B['pk']['at17'])
ck('peak hold waits 2 s, then falls; the maximum stays latched', B['pk']['h19'] == 0 and B['pk']['h25'] < -1 and B['pk']['mx'] == 0, B['pk'])
ck('VU: a -18 dBFS sine reads -18 (aligned), 99 % within 0.3 s, overshoot 1 to 1.5 % (IEC 60268-17)', abs(B['vu']['fin'] + 18) < 0.1 and 0.25 <= B['vu']['t99'] <= 0.32 and 0.9 <= B['vu']['ov'] <= 1.6, B['vu'])
ck('PPM IIb: a 10 ms burst reads 2 dB low, falls 24 dB in 2.8 s, a steady sine reads its peak', abs(B['ppm']['burst'] + 2) < 0.5 and abs(B['ppm']['fall'] - B['ppm']['burst']) < 0.01 and abs(B['ppm']['steady'] + 6) < 0.2, B['ppm'])
ck('RMS (AES17, 300 ms): a -18 dBFS sine reads -18.0', abs(B['rms'] + 18) < 0.05, B['rms'])
# K-weighting against the standard's own 48 kHz coefficients (BS.1770-5, table 1 and 2)
def kmag(f, sr=48000):
    z = np.exp(1j * 2 * np.pi * f / sr)
    def H(b, a): return (b[0] + b[1] / z + b[2] / z ** 2) / (1 + a[0] / z + a[1] / z ** 2)
    return 20 * np.log10(abs(H([1.53512485958697, -2.69169618940638, 1.19839281085285], [-1.69065929318241, 0.73248077421585]) * H([1, -2, 1], [-1.99004745483398, 0.99007225036621])))
kexp = {f: -18 - 3.0103 + kmag(f) - 0.691 for f in (1000, 100, 10000, 25, 4000)}
kd = {f: round(B['k'][str(f)] - kexp[f], 3) for f in kexp}
ck('K-weighting follows BS.1770 at 25 Hz, 100 Hz, 1, 4 and 10 kHz (within 0.1 dB of the standard coefficients)', all(abs(v) < 0.1 for v in kd.values()), kd)
ck('one channel at -18 dBFS, 1 kHz reads -21.0 LUFS (the standard: -3.01 for one channel)', abs(B['k']['1000'] + 21.01) < 0.05, B['k']['1000'])
ck('K-weighting in odd pieces gives the same reading (filter state kept)', abs(B['kpieces'] - B['k']['10000']) < 0.02, (B['kpieces'], B['k']['10000']))

# ---------- 4. fresh samples: a fake analyser buffer that moves by whole render blocks ----------
FR = json.loads(R(r"""(()=>{const n=2048,src=new Float32Array(48000*4);for(let i=0;i<src.length;i++)src[i]=Math.sin(i*.0137)+.3*Math.sin(i*.31);let end=4096,st={},got=0,err=0;
  const steps=[384,512,256,768,384,128,640,0,512,1024,384];for(let r=0;r<200;r++){const add=steps[r%steps.length];end+=add;const a=src.subarray(end-n,end);
   const exp=add+((r%3)-1)*128;/* the frame clock and the audio clock disagree by a block either way */const s=INS.fresh(a,st,exp);if(r>0){got+=n-s;if(n-s!==add)err++}}
  return JSON.stringify({err})})()"""))
ck('the new samples are found exactly when the frame and audio clocks disagree by a block', FR['err'] == 0, FR)

# ---------- 5. the analyser cache: one read per analyser per frame ----------
CA = json.loads(R(r"""(()=>{const an=ctx.createAnalyser();an.fftSize=2048;let nat=0;const o=an.getFloatFrequencyData.bind(an);an.getFloatFrequencyData=b=>{nat++;return o(b)};
  const a=new Float32Array(1024),b=new Float32Array(1024);INS.fft(an,a);INS.fft(an,b);INS.fft(an);const same=nat;FRN++;INS.fft(an,a);
  const t1=INS.td(an),t2=INS.td(an);return JSON.stringify({same,after:nat,shared:t1===t2})})()"""))
ck('three reads of one analyser in one frame call the analyser once; the next frame reads again', CA['same'] == 1 and CA['after'] == 2 and CA['shared'], CA)
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
blk0 = src.index('/* ===== lane E (task IN-A)'); blk1 = src.index('/* ===== end of lane E IN-A')
rest = src[:blk0] + src[blk1:]
import re
ck('every analyser frequency read in the app goes through the cache', not re.search(r'\.get(Float|Byte)FrequencyData\(', rest), re.findall(r'.{40}\.get(?:Float|Byte)FrequencyData\(.{20}', rest))
ck('no audio nodes made by the block', not any(k in src[blk0:blk1] for k in ('createGain', 'createBiquad', 'audioWorklet', '.connect(')))
ck('no em dashes in the block or the new hint', '—' not in src[blk0:blk1] and 'Loudness is K-weighted like the loudness meter' in src)

# ---------- 6. the double vizSide ----------
ck('one vizSide (the Sidechain picture, 5 arguments) and one vizDockSide', R("vizSide.length===5&&typeof vizDockSide==='function'"))

# ---------- 7. live: the meter's Loudness reading ----------
SR = int(R('ctx.sampleRate')); n = int(14 * SR); t = np.arange(n) / SR  # at the context's own rate, so nothing is resampled
A18 = 10 ** (-18 / 20)
s1k = A18 * np.sin(2 * np.pi * 1000 * t); s10k = A18 * np.sin(2 * np.pi * 10000 * t)
R("UI.headroom=-6;UI.bitPerfect=false;UI.limiter=false;0")
ids = {'Same': al.add_audio(np.vstack([s1k, s1k]).astype(np.float32), SR), 'Anti': al.add_audio(np.vstack([s1k, -s1k]).astype(np.float32), SR),
       'High': al.add_audio(np.vstack([s10k, s10k]).astype(np.float32), SR)}
ids['Side'] = ids['Same']
def song(name):
    al.build({'bpm': 120, 'master': 20 * math.log10(2), 'tracks': [{'kind': 'audio', 'name': name, 'vol': 1.0, 'clips': [{'start': 0, 'len': 28, 'name': name, 'buf': ids[name]}], 'fx': [{'type': 'side', 'p': {}}] if name == 'Side' else []}]})
    R("UI.limiter=false;routeMaster();0")
def meas(alg, secs=2.5):
    R("UI.mtr=Object.assign({},UI.mtr||{},{alg:'%s',spd:'instant'});0" % alg)
    R("window.__mv=[];window.__mi=setInterval(()=>{if(anL&&play.on)__mv.push([20*Math.log10(Math.max(1e-9,mtrPeak(anL))),20*Math.log10(Math.max(1e-9,mtrPeak(anR))),LM.M])},50);0")
    pg.wait_for_timeout(int(secs * 1000)); v = R("clearInterval(__mi);__mv")
    v = v[len(v) // 3:]; return [float(np.median([x[i] for x in v])) for i in range(3)], (float(np.ptp([x[0] for x in v])), float(np.ptp([x[2] for x in v])))
song('Same'); R("stop();pos=0;toggle();0"); pg.wait_for_timeout(2500)
pk, _ = meas('peak', 1.5)
lu, spread = meas('lufs', 3.0)
rm, _ = meas('rms', 1.5)
print('    peak', pk, 'lufs', lu, 'rms', rm, 'spread', spread)
ck('live: the 1 kHz -18 dBFS sine reaches the meters at -18 dBFS (peak)', abs(pk[0] + 18) < 0.3, pk)
ck('live: Loudness reads -18.0 LUFS on both bars (1 kHz in both channels; within 0.15 of the peak reading, as for a sine)', abs(lu[0] - pk[0]) < 0.15 and abs(lu[1] - pk[1]) < 0.15, (lu, pk))
ck('live: the meter and the loudness box agree within 0.2 LU', abs(lu[0] - lu[2]) < 0.2, (lu[0], lu[2]))
ck('live: the reading is as steady as the loudness box (no samples counted twice or missed)', spread[0] <= spread[1] + 0.1, spread)
ck('live: RMS unchanged (a sine reads its peak level)', abs(rm[0] - pk[0]) < 0.3, (rm, pk))
R("stop();0")
song('Anti'); R("stop();pos=0;toggle();0"); pg.wait_for_timeout(2500)
la, _ = meas('lufs', 2.5)
ck('live: anti-phase pair: each bar still reads -18.0 LUFS (each side is a full sine)', abs(la[0] + 18) < 0.15 and abs(la[1] + 18) < 0.15, la)
R("stop();0")
song('High'); R("stop();pos=0;toggle();0"); pg.wait_for_timeout(2500)
ph, _ = meas('peak', 1.5)
lh, _ = meas('lufs', 2.5)
khi = kmag(10000) - kmag(1000)
ck('live: a 10 kHz sine reads higher by the K-weighting (BS.1770 shelf), as the loudness box does', abs((lh[0] - ph[0]) - khi) < 0.25 and abs(lh[0] - lh[2]) < 0.2, (lh, ph, round(khi, 2)))
R("stop();0")
song('Side'); R("stop();pos=0;toggle();0"); pg.wait_for_timeout(1200)
# the Sidechain device picture is back
R("selectTrack(S.tracks[0].id);renderFx();0"); pg.wait_for_timeout(600)
side = R("(()=>{const cv=document.querySelector('canvas.viz[data-t=\"side\"]')||[...document.querySelectorAll('canvas.viz')].find(c=>{const t=curT();const f=t&&t.fx.find(f=>f.id===c.dataset.id);return f&&f.type==='side'});if(!cv)return -1;const g=cv.getContext('2d'),d=g.getImageData(0,0,cv.width,cv.height).data;let k=0;for(let i=3;i<d.length;i+=4)if(d[i]>40)k++;return k/(d.length/4)})()")
ck('the Sidechain device draws its picture again', side > 0.05, side)
try:
    pg.locator('canvas.viz').first.screenshot(path=os.path.join(OUT, 'inA_sidechain.png'))
except Exception as e: print('   (no sidechain shot)', e)
R("stop();0")

# ---------- 8. the Visualizer docked at the side still sizes itself ----------
R("UI.viz=true;UI.vizDock='right';if(typeof vizApply==='function')vizApply();0"); pg.wait_for_timeout(500)
vz = R("(()=>{const el=VZ.el;return !!el&&el.getBoundingClientRect().height>100&&getComputedStyle(document.body).getPropertyValue('--vzw').trim()!==''})()")
ck('the Visualizer docked on the right is placed by vizDockSide', vz)
R("UI.vizDock='bottom';vizApply();UI.viz=false;vizApply();0")

# ---------- 9. the test sheet of the drawers (dark, then the Light level) ----------
SHEET = r"""(lite)=>{UI.lite=lite;let cv=document.getElementById('__inA');if(!cv){cv=document.createElement('canvas');cv.id='__inA';Object.assign(cv.style,{position:'fixed',left:'10px',top:'10px',width:'900px',height:'420px',zIndex:9999,background:'#07080b'});document.body.appendChild(cv)}
  const d=Math.min(2,devicePixelRatio||1);cv.width=900*d;cv.height=420*d;const g=cv.getContext('2d');g.setTransform(d,0,0,d,0,0);g.fillStyle='#07080b';g.fillRect(0,0,900,420);const L=INS.look();
  /* a meter scale beside two bars */g.fillStyle='#15171d';g.fillRect(40,20,6,300);g.fillRect(49,20,6,300);INS.scaleTaper(g,36,20,300,{});
  /* a spectrum frame: dB grid and the log axis */const x0=110,y0=20,w=420,h=170;g.fillStyle='#050507';g.fillRect(x0,y0,w,h);INS.dbGrid(g,x0,y0,w,h,0,-90,10,{major:30});INS.fAxis(g,x0,w,y0,h,{});
  INS.corner(g,'FFT 8192 · Hann · RBW '+INS.fmt(48000/8192*1.5,'Hz'),x0+w-4,y0+4,'right');
  /* an oscilloscope graticule */g.fillStyle='#050507';g.fillRect(560,20,320,240);INS.graticule(g,560,20,320,240,{nx:10,ny:8,fine:true});INS.corner(g,'2 ms/div  0.25/div',564,24);
  /* colour bars */INS.cmapNames.forEach((k,i)=>{INS.cbar(g,110,230+i*20,420,12,k);g.font='8px '+L.mono;g.fillStyle=L.mut;g.textAlign='left';g.textBaseline='middle';g.fillText(k,536,236+i*20)});
  /* read-outs: value in ink, unit in amber (L2) */[[-14.0,'LUFS'],[-1.3,'dBTP'],[12400,'Hz'],[0.0005,'s']].forEach(([v,u],i)=>{const[a,b]=INS.parts(v,u);g.font='600 13px '+L.mono;g.fillStyle=L.ink;g.textAlign='right';g.fillText(a,640,300+i*26);g.font='9px '+L.mono;g.fillStyle=L.unit;g.textAlign='left';g.fillText(INS.ucap(b),646,300+i*26)});
  g.font='10px '+L.mono;g.fillStyle=L.sel;g.textAlign='left';g.fillText(INS.hz(440,{note:true}),720,300);return 1}"""
pg.evaluate("s=>AudioLab.run('('+s+')(false)')", SHEET); pg.wait_for_timeout(200)
pg.locator('#__inA').screenshot(path=os.path.join(OUT, 'inA_sheet_dark.png'))
pg.evaluate("s=>AudioLab.run('('+s+')(true)')", SHEET); pg.wait_for_timeout(200)
pg.locator('#__inA').screenshot(path=os.path.join(OUT, 'inA_sheet_light.png'))
R("UI.lite=false;document.getElementById('__inA').remove();0")
ck('the Settings look-slider array named LOOK is not taken for tokens; LK tokens (task LK) win over the constants when it exists', R("(()=>{const o=INS._src,a=INS._src();INS._src=()=>({unit:'#123456'});FRN++;const u=INS.look().unit;INS._src=o;FRN++;return(a===null||(typeof LOOK==='object'&&!Array.isArray(LOOK)&&a===LOOK&&!Array.isArray(a)))&&u==='#123456'&&INS.look().unit==='#ffb547'})()"))
ck('no console errors', not al.errors, al.errors)
al.stop()
print('%d/%d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
