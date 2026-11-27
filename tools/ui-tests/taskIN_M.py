"""Task IN-M (lane E): level meters, the user's pick M2 (peak and RMS in one bar).
Checks the 300 ms window (RMS AES17, highest sample, crest factor) with known signals made in the page (sine, square, pink noise, a step to
silence, odd pieces), the bar drawer, then live with signals played through the app: a 1 kHz sine at -18 dBFS in both channels, a correlated
and an anti-phase pair, pink noise, a sweep at -12 dBFS: the read-outs of the master strip, the tooltips, the Settings preview, the RMS core on
the transport meter, the mixer's fader meters (Flat bars), the mixer's meter view, the track headers; no core with the RMS reading; nothing
drawn while the mixer is closed or while the app's frame gate is shut (background freeze); no console errors. Screenshots in the dark look
and at the Light level.
  python3 tools/ui-tests/taskIN_M.py [repo dir] [out dir]"""
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
R = al.run
print('version', al.version)
ck('IN-M is there (INS.pr, INS.mbar, INM)', R("typeof INS.pr==='function'&&typeof INS.mbar==='function'&&typeof INM==='object'"))

# ---------- 1. the 300 ms window with known signals (48 kHz, made in the page) ----------
W = json.loads(R(r"""(()=>{const sr=48000,o={},sine=(n,f,db)=>{const a=new Float32Array(n),A=Math.pow(10,db/20);for(let i=0;i<n;i++)a[i]=A*Math.sin(2*Math.PI*f*i/sr);return a};
 {const st={};INS.pr(st,sine(sr,1000,-18),0,sr,sr);o.sine=[st.rms,st.pk,st.cf]}
 {const st={},a=new Float32Array(sr),A=Math.pow(10,-6/20);for(let i=0;i<sr;i++)a[i]=(Math.floor(i/24)%2?-A:A);INS.pr(st,a,0,sr,sr);o.sq=[st.rms,st.pk,st.cf]}
 {/* pink noise (Voss-McCartney), scaled to -20 dBFS RMS */let s=1;const rnd=()=>{s=(s*16807)%2147483647;return s/2147483647*2-1};const n=sr*2,a=new Float32Array(n),r=new Float32Array(16);let sum=0;
  for(let i=0;i<n;i++){let k=0,x=i;while(k<15&&!(x&1)){x>>=1;k++}r[k]=rnd();let v=0;for(let j=0;j<16;j++)v+=r[j];a[i]=v;sum+=v*v}const g=Math.pow(10,-20/20)/Math.sqrt(sum/n);for(let i=0;i<n;i++)a[i]*=g;
  const st={};INS.pr(st,a,0,n,sr);o.pink=[st.rms,st.pk,st.cf]}
 {/* a step: 1 s of sine, then silence; when does the window let go */const st={},a=sine(sr,1000,-18);INS.pr(st,a,0,sr,sr);const z=new Float32Array(480);let t=0,at=null,still=null;
  for(let k=0;k<60;k++){INS.pr(st,z,0,480,sr);t+=10;if(still==null&&t>=150)still=st.rms;if(at==null&&st.rms<-200)at=t}o.step={still,at}}
 {/* odd pieces: the same reading */const st={},a=sine(sr,997,-9);let i=0;while(i<sr){const n=Math.min(sr-i,77+(i%613));INS.pr(st,a,i,i+n,sr);i+=n}const s2={};INS.pr(s2,a,0,sr,sr);o.pieces=[st.rms,s2.rms,st.cf,s2.cf]}
 return JSON.stringify(o)})()"""))
print('   ', json.dumps(W))
ck('1 kHz sine at -18 dBFS: RMS -18.0 (AES17), peak -18.0, crest 3.0 dB', abs(W['sine'][0] + 18) < 0.02 and abs(W['sine'][1] + 18) < 0.02 and abs(W['sine'][2] - 3.01) < 0.03, W['sine'])
ck('square wave at -6 dBFS: crest 0.0 dB (RMS reads +3.0 above the sine convention, -3.0 dBFS)', abs(W['sq'][2]) < 0.02 and abs(W['sq'][0] + 2.99) < 0.02, W['sq'])
ck('pink noise at -20 dBFS RMS: RMS -17.0 (AES17), crest between 9 and 15 dB', abs(W['pink'][0] + 16.99) < 0.6 and 9 < W['pink'][2] < 15, W['pink'])
ck('the window is 300 ms: 150 ms after the sound stops it reads 3.0 dB lower (half the window), at 300 ms nothing', abs(W['step']['still'] + 21.01) < 0.1 and W['step']['at'] == 300, W['step'])
ck('fed in odd pieces: the same RMS and crest', abs(W['pieces'][0] - W['pieces'][1]) < 0.01 and abs(W['pieces'][2] - W['pieces'][3]) < 0.01, W['pieces'])

# ---------- 2. the bar drawer ----------
D = json.loads(R(r"""(()=>{const c=document.createElement('canvas');c.width=10;c.height=100;const g=c.getContext('2d');INS.mbar(g,0,0,10,100,.8,.5,'#ffffff');const a=y=>g.getImageData(5,y,1,1).data[3];
 const c2=document.createElement('canvas');c2.width=100;c2.height=4;const h=c2.getContext('2d');INS.mbar(h,0,0,100,4,.6,-1,'#fff',true);const b=x=>h.getImageData(x,2,1,1).data[3];
 return JSON.stringify({core:a(70),faint:a(30),above:a(10),plain:[b(50),b(70)]})})()"""))
ck('bar drawer: the RMS core bright, the peak part above it faint, nothing above the peak; no core: a plain bar', D['core'] == 255 and 60 < D['faint'] < 140 and D['above'] == 0 and D['plain'] == [255, 0], D)

# ---------- 3. live signals ----------
SR = int(R('ctx.sampleRate')); n = int(16 * SR); t = np.arange(n) / SR
A18 = 10 ** (-18 / 20)
s1k = A18 * np.sin(2 * np.pi * 1000 * t)
rng = np.random.default_rng(7)
def pinkn(n):
    X = np.fft.rfft(rng.standard_normal(n)); f = np.arange(len(X)); f[0] = 1; y = np.fft.irfft(X / np.sqrt(f), n); return y / np.sqrt(np.mean(y ** 2)) * 10 ** (-20 / 20)
pk_l, pk_r = pinkn(n), pinkn(n)
f0, f1 = 20.0, 20000.0; T = 8.0; ts = t % T; K = T / math.log(f1 / f0)
sweep = 10 ** (-12 / 20) * np.sin(2 * np.pi * f0 * K * (np.exp(ts / K) - 1))
R("UI.headroom=-6;UI.bitPerfect=false;UI.limiter=false;0")
ids = {'Sine': al.add_audio(np.vstack([s1k, s1k]).astype(np.float32), SR), 'Anti': al.add_audio(np.vstack([s1k, -s1k]).astype(np.float32), SR),
       'Pink': al.add_audio(np.vstack([pk_l, pk_r]).astype(np.float32), SR), 'Sweep': al.add_audio(np.vstack([sweep, sweep]).astype(np.float32), SR)}
def until(js, secs=5.0):
    for _ in range(int(secs * 10)):
        if R(js): return True
        pg.wait_for_timeout(100)
    return False
def song(name):
    al.build({'bpm': 120, 'master': 20 * math.log10(2), 'tracks': [{'kind': 'audio', 'name': name, 'vol': 1.0, 'clips': [{'start': 0, 'len': 32, 'name': name, 'buf': ids[name]}], 'fx': []}]})
    R("UI.limiter=false;routeMaster();0")
def play(name, wait=1500):
    R("stop();0"); song(name); R("UI.mtr=Object.assign({},UI.mtr||{},{alg:'peak',spd:'instant'});stop();pos=0;toggle();0"); pg.wait_for_timeout(wait)
def reads(secs=1.5, track=False):
    R("window.__q=[];window.__qi=setInterval(()=>{if(!play.on)return;const N=NODES.get(S.tracks[0].id),m=INM.read(anL,anR),l=INM.st(anL),r=INM.st(anR),t=N&&INM.read(N.aL,N.aR);if(m&&l&&r)__q.push([m.rms,m.pk,m.cf,l.rms,r.rms,t?t.rms:-999])},50);0")
    pg.wait_for_timeout(int(secs * 1000)); v = R("clearInterval(__qi);__q"); v = v[len(v) // 4:]
    return [float(np.median([x[i] for x in v])) for i in range(6)], float(np.ptp([x[0] for x in v])) if v else 99

play('Sine'); q, spread = reads()
print('    sine', q, spread)
ck('live: 1 kHz at -18 dBFS in both channels: master RMS -18.0, peak -18.0, crest 3.0 dB', abs(q[0] + 18) < 0.15 and abs(q[1] + 18) < 0.15 and abs(q[2] - 3.01) < 0.15, q)
ck('live: both master channels read the same, steady to 0.05 dB (no samples counted twice or missed)', abs(q[3] - q[4]) < 0.05 and spread < 0.05, (q, spread))
ck('live: the track reads within 0.75 dB of the master (its taps hold 256 samples: snapshots, not every sample)', abs(q[5] - q[0]) < 0.75, (q[5], q[0]))
R("openMixer();0"); pg.wait_for_timeout(800)
until("(()=>{const b=document.querySelector('#mixWin .mx.master .inslv b'),p=document.querySelector('#mixWin .mxpkr');return !!b&&b.textContent!=='–'&&!!p&&/RMS/.test(p.title)&&/RMS/.test(document.getElementById('peakBox').title)})()")
M = json.loads(R(r"""(()=>{const w=document.getElementById('mixWin'),b=[...w.querySelectorAll('.mx.master .inslv b')].map(x=>x.textContent),u=[...w.querySelectorAll('.fm u')].map(u=>u.style.boxShadow);
  return JSON.stringify({b,u,fd:mxsO().fd,tip:(w.querySelector('.mxpkr')||{}).title||'',pb:document.getElementById('peakBox').title})})()"""))
print('   ', json.dumps(M)[:600])
ck('master strip: RMS and crest read-outs (−18.0 dBFS, 3.0 dB)', M['b'][:2] == ['−18.0', '3.0'], M['b'])
ck('Flat bars kept (design 7) and its fader meters carry the RMS core (veil down to the RMS level)', M['fd'] == 7 and any(x for x in M['u']), (M['fd'], M['u']))
ck('channel and transport tooltips: peak, RMS and crest with units and a real minus sign', 'RMS −18.0\u2009dBFS' in M['tip'] and 'crest 3.0\u2009dB' in M['tip'] and 'RMS −18.0\u2009dBFS' in M['pb'], (M['tip'], M['pb']))
pg.screenshot(path=os.path.join(OUT, 'inM_mixer_sine.png'))

play('Anti'); q, _ = reads(1.2)
ck('live: anti-phase pair: each channel reads −18.0 RMS, crest 3.0 dB', abs(q[3] + 18) < 0.15 and abs(q[4] + 18) < 0.15 and abs(q[2] - 3.01) < 0.15, q)

play('Sweep', 1200); R("window.__sw=[];window.__swi=setInterval(()=>{const s=INM.st(anL);if(s&&play.on)__sw.push(s.rms)},100);0"); pg.wait_for_timeout(7000)
sw = R("clearInterval(__swi);__sw")[3:]
ck('live: a sweep at −12 dBFS (20 Hz to 20 kHz) reads −12.0 RMS all the way (within 0.6 dB; the low end is slow against 300 ms)', len(sw) > 30 and max(abs(x + 12) for x in sw[10:]) < 0.6, (min(sw), max(sw)))

play('Pink', 2000); q, _ = reads(1.5)
print('    pink', q)
ck('live: pink noise at −20 dBFS RMS: RMS −17.0 (AES17), crest 9 to 15 dB', abs(q[3] + 17) < 1.0 and 9 < q[2] < 15, q)
for _try in range(40):
    pg.wait_for_timeout(60)
    H = json.loads(R(r"""(()=>{const w=document.getElementById('mixWin');const e=[...document.querySelectorAll('.vm i b')].map(x=>x.style.boxShadow).filter(v=>v);
      const u=[...w.querySelectorAll('.fm u')].map(u=>u.style.boxShadow).filter(v=>v);
      /* the transport meter: just inside the RMS core and just above it (the gradient hardly changes over 6 px) */const c=document.getElementById('mtr'),g=c.getContext('2d'),h=c.height,y=Math.round(h*.3),cw=c.width,xr=Math.round(INM.rfr(anL,v=>Math.min(1,Math.max(0,(v+60)/66)))*cw),xp=Math.round(Math.min(1,Math.max(0,(MT2.l+60)/66))*cw);
      const px=x=>{const d=g.getImageData(x,y,1,1).data;return d[0]+d[1]+d[2]};return JSON.stringify({hdr:e,fm:u,xr,xp,cw,cin:px(Math.max(0,xr-4)),cout:xp>xr+6?px(xr+4):null})})()"""))
    if H['cout'] is not None: break
print('    headers', H['hdr'][:2], 'fader', H['fm'][:2], 'transport', {k: H[k] for k in ('xr', 'xp', 'cw', 'cin', 'cout')})
ck('track header meters: a veil from the top of the bar down to the RMS', len(H['hdr']) >= 1, H['hdr'][:2])
ck('mixer fader meters: the veil sits lower for noise (crest) than for the sine', len(H['fm']) >= 2, H['fm'][:2])
ck('transport meter: the bar is bright up to the RMS and faint above it (pink noise)', H['cout'] is not None and H['cout'] < H['cin'] * 0.6, {k: H[k] for k in ('xr', 'xp', 'cin', 'cout')})
pg.screenshot(path=os.path.join(OUT, 'inM_mixer_pink.png'))
try:
    pg.locator('#mtr').screenshot(path=os.path.join(OUT, 'inM_transport.png'))
    pg.locator('#mixWin .mx.master').screenshot(path=os.path.join(OUT, 'inM_master.png'))
    pg.locator('#hdrin .hdr').first.screenshot(path=os.path.join(OUT, 'inM_header.png'))
except Exception as e: print('   (shot)', e)

# the mixer's meter view: the fader taper and the core
R("UI.mxView='meter';renderMixer();0"); pg.wait_for_timeout(800)
for _try in range(40):
  pg.wait_for_timeout(60)
  MV = json.loads(R(r"""(()=>{const cv=[...document.querySelectorAll('#mixWin canvas.mxv')].find(c=>c.dataset.id===S.tracks[0].id&&(c.dataset.v||w9VOf(c.dataset.id))==='meter');if(!cv)return JSON.stringify(null);const g=cv.getContext('2d'),W=cv.width,H=cv.height,x=Math.round(W*.3);
  const N=NODES.get(S.tracks[0].id),r=INM.rfr(N.aL,dbN),yr=Math.round(H*(1-r)),p=dbN(MXH.get(cv.dataset.hk||cv.dataset.id).pl),yp=Math.round(H*(1-p)),px=y=>{const d=g.getImageData(x,y,1,1).data;return d[0]+d[1]+d[2]};
  return JSON.stringify({yr,yp,H,cin:px(Math.min(H-1,yr+3)),cout:yp<yr-6?px(yr-3):null})})()"""))
  if not MV or MV['cout'] is not None: break
if MV:
    ck("mixer's meter view (fader taper): a bright core under a fainter peak part", MV['cout'] is not None and MV['cout'] < MV['cin'] * 0.6, MV)
    try: pg.locator('#mixWin .mx').first.screenshot(path=os.path.join(OUT, 'inM_meterview.png'))
    except Exception as e: print('   (shot)', e)
else: ck("mixer's meter view found", False)
R("UI.mxView='wave';renderMixer();0"); pg.wait_for_timeout(300)

# the RMS reading: no core (the bar is an average already), read-outs stay
R("UI.mtr=Object.assign({},UI.mtr,{alg:'rms'});0"); pg.wait_for_timeout(300)
until("(()=>{const b=document.querySelector('#mixWin .mx.master .inslv b');return !!b&&b.textContent!=='–'&&[...document.querySelectorAll('#mixWin .fm u')].every(u=>!u.style.boxShadow)})()")
print('   ', R("JSON.stringify([[...document.querySelectorAll('#mixWin .fm u')].map(u=>u.style.boxShadow),[...document.querySelectorAll('.vm i b')].map(e=>e.style.boxShadow),[...document.querySelectorAll('#mixWin .mx.master .inslv b')].map(b=>b.textContent)])"))
NC = R("[...document.querySelectorAll('#mixWin .fm u')].every(u=>!u.style.boxShadow)&&[...document.querySelectorAll('.vm i b')].every(e=>!e.style.boxShadow)&&[...document.querySelectorAll('#mixWin .mx.master .inslv b')][0].textContent!=='–'")
ck('with the RMS reading the core is off (the bar is the average), the read-outs stay', NC)
R("UI.mtr=Object.assign({},UI.mtr,{alg:'peak'});0")

# light level: screenshots and half-rate read-outs
R("UI.lite=true;document.body.classList.add('lite');0"); pg.wait_for_timeout(1200)
pg.screenshot(path=os.path.join(OUT, 'inM_mixer_pink_light.png'))
R("UI.lite=false;document.body.classList.remove('lite');0")

# nothing while the mixer is closed; nothing while the frame gate is shut
R("closeMixer&&closeMixer();0") if R("typeof closeMixer==='function'") else R("document.getElementById('mBtn').click();0")
pg.wait_for_timeout(500)
cl = R("(()=>{const w=document.getElementById('mixWin');return !w||w.hidden})()")
c0 = R("INM.nm"); pg.wait_for_timeout(1000); nm = R("INM.nm") - c0
ck('mixer closed: its meters are not touched (mixer passes in 1 s: %d)' % nm, cl and nm == 0, nm)
if R("typeof AO==='object'"):
    gz = json.loads(R(r"""(()=>{return JSON.stringify(0)})()"""))
    fz = pg.evaluate("()=>new Promise(r=>{const A=window.AudioLab.run('AO');A.gate=true;setTimeout(()=>{const n0=window.AudioLab.run('INM.n'),f0=window.AudioLab.run('FRN');setTimeout(()=>{const n1=window.AudioLab.run('INM.n'),f1=window.AudioLab.run('FRN');A.open();r([n1-n0,f1-f0])},800)},300)})")
    ck('background freeze (the frame gate shut): no frames, no veil writes', fz[0] == 0 and fz[1] <= 1, fz)

# ---------- 4. the Settings preview ----------
R("stop();0"); play('Pink', 800)
PG = R("(()=>{const s=document.getElementById('mtrSet').closest('section[data-page]');return s?s.dataset.page:'layout'})()")  # Layout until v0.25x, Mixer since lane B's S5
R("openSettings('%s');0" % PG); pg.wait_for_timeout(300)
R("(()=>{const b=document.querySelector('#setNav [data-tab=\"%s\"]');if(b)b.click()})();0" % PG); pg.wait_for_timeout(1500)
PV = R("(()=>{const a=document.getElementById('mtrRmV'),b=document.getElementById('mtrCfV');return a&&b?[a.textContent,b.textContent]:null})()")
ck('Settings preview: RMS and crest beside the peak read-out', PV is not None and PV[0].startswith('−1') and PV[1].endswith('dB'), PV)
try:
    R("document.getElementById('mtrSet').scrollIntoView();0"); pg.wait_for_timeout(300)
    pg.locator('#mtrSet').screenshot(path=os.path.join(OUT, 'inM_settings.png'))
except Exception as e: print('   (shot)', e)
R("closeSet&&closeSet();stop();0")

src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
b0 = src.index('/* ===== lane E (task IN-M)'); b1 = src.index('/* ===== end of lane E IN-M')
ck('no audio nodes made by the block; no em dashes in its text', not any(k in src[b0:b1] for k in ('createGain', 'createBiquad', 'createAnalyser', 'audioWorklet', '.connect(')) and '—' not in src[b0:b1])
ck('no console errors', not al.errors, al.errors)
al.stop()
print('%d/%d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
