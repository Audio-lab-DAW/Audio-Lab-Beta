"""Task IN-V (lane E): the Visualizer, the user's pick V1 (one frequency axis) with viridis, and the right-click menu entries.
Checks with known signals played through the app (a 1 kHz sine at -18 dBFS, a 4 kHz sine at -18 dBFS, pink noise):
  1. the shared axis: the spectrogram's brightest row and the sideways spectrum's peak are the same row, at the height of 1 kHz on the axis
  2. calibration: the row reads -18 dBFS (IN-S's calibration), and its spectrogram pixel is viridis at (-18 + 90) / 90
  3. a new colour map or range repaints the history (not cleared): the same pixel becomes magma, then the 60 dB colour
  4. tilt: 4.5 dB per octave around 1 kHz lifts a 4 kHz sine by 9 dB in the sideways spectrum, leaves 1 kHz alone; off: no lift
  5. speed: fast writes twice the columns of normal, slow half
  6. max hold falls 3 dB a second; none at the Light level
  7. All: the spectrogram and spectrum panes are one module; Spectrum alone keeps IN-S's front panel; the waveform's time scale bar;
     levels as M2 (the RMS core under a fainter peak part)
  8. the menu: Colour map, Range, Spectrum tilt, Max hold, Speed (kept in UI.vzO; a project without it opens on viridis, 90 dB, 4.5, hold, normal)
  9. nothing drawn while the Visualizer is hidden or in the background freeze; no console errors; no audio nodes in the block
Screenshots dark and Light.
  python3 tools/ui-tests/taskIN_V.py [repo dir] [out dir]"""
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
ck('IN-V is there: the Visualizer draws through INV', R("typeof INV==='object'&&VZD.spec===INV.mod&&VZD.fft===INV.fft&&VZD.lev===INV.lev"))
ck('a project or settings without the new choices: viridis, 90 dB, tilt 4.5, max hold, normal speed', R("(()=>{const s=UI.vzO;delete UI.vzO;const o=INV.O();UI.vzO=s;return o.map==='viridis'&&o.range===90&&o.tilt===4.5&&o.hold&&o.speed==='normal'})()"))

SR = int(R('ctx.sampleRate')); n = int(20 * SR); t = np.arange(n) / SR
A18 = 10 ** (-18 / 20)
rng = np.random.default_rng(5)
def pinkn(n):
    X = np.fft.rfft(rng.standard_normal(n)); f = np.arange(len(X)); f[0] = 1; y = np.fft.irfft(X / np.sqrt(f), n); return y / np.sqrt(np.mean(y ** 2)) * 10 ** (-20 / 20)
sig = {'S1k': A18 * np.sin(2 * np.pi * 1000 * t), 'S4k': A18 * np.sin(2 * np.pi * 4000 * t), 'Pink': pinkn(n)}
R("UI.headroom=0;UI.bitPerfect=false;UI.limiter=false;UI.lite=false;UI.liteMan=false;applyLite();UI.vzO={};0")
ids = {k: al.add_audio(np.vstack([v, v]).astype(np.float32), SR) for k, v in sig.items()}
def play(name, wait=1500, mode='all'):
    R("stop();0")
    al.build({'bpm': 120, 'master': 0, 'tracks': [{'kind': 'audio', 'name': name, 'vol': 1.0, 'clips': [{'start': 0, 'len': 32, 'name': name, 'buf': ids[name]}], 'fx': []}]})
    R("UI.limiter=false;routeMaster();UI.viz=true;UI.vizDock='bottom';UI.vizH=300;UI.vizMode='%s';vizApply();stop();pos=0;toggle();0" % mode)
    pg.wait_for_timeout(wait)
# the master: is a full-scale sine heard at full scale? (the master fader at 0 dB, no limiter)
play('S1k', 2500)
A = json.loads(R(r"""(()=>{const v=INV._cv,S=VZ.isg,SD=VZ.iside;if(!v||!S||!SD)return JSON.stringify(null);let im=0,is=0;for(let r=0;r<v.length;r++){if(v[r]>v[im])im=r;if(SD.sv[r]>SD.sv[is])is=r}
 const H=v.length,fyRow=Math.floor((1-Math.log(1000/20)/Math.log(1000))*H),pcol=(S.p-1+S.W)%S.W,px=S.x.getImageData(pcol,im,1,1).data,L=INS.cmap('viridis'),k=Math.round((v[im]+90)/90*255)*3;
 return JSON.stringify({im,is,fyRow,db:v[im],side:SD.sv[is],px:[px[0],px[1],px[2]],want:[L[k],L[k+1],L[k+2]],H,pcol})})()"""))
print('   ', A)
ck('one frequency axis: the spectrogram\'s brightest row is the sideways spectrum\'s peak row, at 1 kHz on the axis (within a row)', A and abs(A['im'] - A['is']) <= 1 and abs(A['im'] - A['fyRow']) <= 1, A)
ck('calibrated: the 1 kHz sine at −18 dBFS reads −18 dBFS (within 0.7 dB) in the spectrogram row and the sideways spectrum', A and abs(A['db'] + 18) < 0.7 and abs(A['side'] + 18) < 0.7, A)
ck('the spectrogram pixel is viridis at (−18 + 90) / 90 (within 12 per channel)', A and max(abs(a - b) for a, b in zip(A['px'], A['want'])) <= 12, A)
pg.screenshot(path=os.path.join(OUT, 'inV_all_1k.png'))
try: pg.locator('#vizp').screenshot(path=os.path.join(OUT, 'inV_panel_1k.png'))
except Exception as e: print('   (shot)', e)

# 3. repaint on a new map and range
RP = json.loads(R(r"""(()=>{const S=VZ.isg,col=(S.p-30+S.W)%S.W;let r=0;for(let y=0;y<S.H;y++)if(S.q[y*S.W+col]&&(!S.q[r*S.W+col]||S.q[y*S.W+col]<S.q[r*S.W+col]))r=y;const q=S.q[r*S.W+col],db=-q*.6,get=()=>Array.from(S.x.getImageData(col,r,1,1).data.slice(0,3));
 const a=get(),g0=document.createElement('canvas').getContext('2d'),again=()=>INV.sg(g0,0,0,S.W*2,S.H,null,INV.O());INV.set('map','magma');again();const b=get();INV.set('range',60);again();const c=get();INV.set('map','viridis');INV.set('range',90);
 const M=INS.cmap('magma'),k1=Math.round((db+90)/90*255)*3,k2=Math.round((db+60)/60*255)*3;return JSON.stringify({db,a,b,c,m90:[M[k1],M[k1+1],M[k1+2]],m60:[M[k2],M[k2+1],M[k2+2]]})})()"""))
print('   ', RP)
d = lambda a, b: max(abs(x - y) for x, y in zip(a, b))
ck('a new colour map repaints the history: the same old column turns magma (not cleared)', d(RP['b'], RP['m90']) <= 3 and d(RP['a'], RP['b']) > 20, RP)
ck('a new range repaints it too: the 60 dB colour of the same level', d(RP['c'], RP['m60']) <= 3, RP)

# 4. tilt
def side_peak():
    return json.loads(R("(()=>{const S=VZ.iside;let i=0;for(let r=0;r<S.sv.length;r++)if(S.sv[r]>S.sv[i])i=r;return JSON.stringify([S.sv[i],i])})()"))
play('S4k', 2000); R("INV.set('tilt',0);0"); pg.wait_for_timeout(1200); t0 = side_peak()
R("INV.set('tilt',4.5);0"); pg.wait_for_timeout(1200); t45 = side_peak()
print('    tilt off / 4.5', t0, t45)
ck('tilt 4.5 dB per octave lifts the 4 kHz sine by 9 dB (two octaves above 1 kHz; within 0.8; off, it reads −18 within the window scalloping, 1.2 dB)', abs(t45[0] - t0[0] - 9) < 0.8 and abs(t0[0] + 18) < 1.2, (t0, t45))

# 5. speed
def cols(sec=1.0):
    a = R("INV.n"); pg.wait_for_timeout(int(sec * 1000)); return R("INV.n") - a
R("INV.set('speed','normal');0"); cn = cols(); R("INV.set('speed','fast');0"); cf = cols(); R("INV.set('speed','slow');0"); cs = cols(); R("INV.set('speed','normal');0")
print('    columns per second slow/normal/fast', cs, cn, cf)
ck('speed: fast writes about twice the columns of normal, slow about half', cn > 10 and 1.6 < cf / cn < 2.4 and 0.35 < cs / cn < 0.65, (cs, cn, cf))

# 6. max hold falls 3 dB a second
R("stop();0"); pg.wait_for_timeout(100)
MH = json.loads(R(r"""(()=>{const S=VZ.iside,i=S.mh.indexOf(Math.max(...S.mh)),a=S.mh[i];const vals=new Float32Array(S.sv.length).fill(-200);const g=document.createElement('canvas').getContext('2d');VZ.itv=performance.now()-1000;
 const X=INV.side(g,0,0,100,S.sv.length,vals,INV.O(),1);return JSON.stringify([a,S.mh[i]])})()"""))
ck('max hold falls 3 dB in a second', abs(MH[0] - MH[1] - 3) < 0.01, MH)

# 7. layouts
play('Pink', 1800)
LY = json.loads(R(r"""(()=>{const P=[['spec',0,0,300,100],['fft',300,0,300,100],['wave',600,0,300,100],['lev',900,0,100,100]];INV.merge(P);return JSON.stringify(P)})()"""))
ck('All: the spectrogram and spectrum panes become one module over both', LY[0] == ['spec', 0, 0, 600, 100] and len(LY) == 3, LY)
pg.wait_for_timeout(1500)
ck('waveform: a time scale bar from the real column rate', R("[.25,.5,1,2,5,10].includes(INV.sb)"), R("INV.sb"))
pg.screenshot(path=os.path.join(OUT, 'inV_all_pink.png'))
try: pg.locator('#vizp').screenshot(path=os.path.join(OUT, 'inV_panel_pink.png'))
except Exception as e: print('   (shot)', e)
LV = json.loads(R(r"""(()=>{const c=document.createElement('canvas');c.width=120;c.height=200;const g=c.getContext('2d');VZ.hold=[];INV.lev(g,120,200,true);const a=y=>g.getImageData(40,y,1,1).data;
 const col=[];for(let y=14;y<184;y++){const p=a(y);col.push(p[3]&&(p[0]+p[1]+p[2]))}return JSON.stringify(col)})()"""))
lit = [v for v in LV if v]
ck('levels as M2: a bright RMS core under a fainter peak part', len(lit) > 10 and max(lit) > 1.4 * min(lit), (len(lit), min(lit) if lit else None, max(lit) if lit else None))
for m in ('spec', 'fft', 'wave', 'lev'):
    R("UI.vizMode='%s';vizPaintBtns();VZ.cols=[];0" % m); pg.wait_for_timeout(900)
    try: pg.locator('#vizp').screenshot(path=os.path.join(OUT, 'inV_%s.png' % m))
    except Exception as e: print('   (shot)', e)
ck('Spectrum alone keeps the front panel (INS.spec) with the menu\'s tilt', R("(()=>{let t=null;const o=INS.spec;INS.spec=function(g,x,y,w,h,O){t=O.tilt;return o.apply(this,arguments)};try{INV.fft(document.createElement('canvas').getContext('2d'),300,150,true)}finally{INS.spec=o}return t===4.5})()"))
R("UI.vizMode='all';vizPaintBtns();VZ.cols=[];0")
R("UI.lite=true;document.body.classList.add('lite');0"); pg.wait_for_timeout(1500)
try: pg.locator('#vizp').screenshot(path=os.path.join(OUT, 'inV_panel_pink_light.png'))
except Exception as e: print('   (shot)', e)
ck('Light level: no max hold line drawn', R("(()=>{let n=0;const c=document.createElement('canvas').getContext('2d'),o=c.stroke.bind(c);c.stroke=function(){if(String(this.strokeStyle).includes('255, 255, 255, 0.3')||this.strokeStyle==='rgba(255,255,255,.3)')n++;return o()};INV.side(c,0,0,100,100,new Float32Array(100).fill(-30),INV.O(),.016);return n===0})()"))
R("UI.lite=false;document.body.classList.remove('lite');0")

# 8. the menu
MN = json.loads(R("JSON.stringify(INV.menu().filter(x=>x&&x.label).map(x=>[x.label,(x.kids||[]).map(k=>k.label)]))"))
print('   ', MN)
labs = [m[0] for m in MN]
ck('menu: Colour map (Viridis, Magma, Inferno, Today’s heat), Range (60, 90, 120), Spectrum tilt (off, 3, 4.5), Max hold, Speed', labs == ['Colour map', 'Range', 'Spectrum tilt', 'Max hold', 'Speed'] and MN[0][1] == ['Viridis', 'Magma', 'Inferno', 'Today’s heat'] and MN[1][1] == ['60 dB', '90 dB', '120 dB'] and len(MN[2][1]) == 3 and MN[4][1] == ['Slow', 'Normal', 'Fast'], MN)
ck('menu choices are kept in UI.vzO', R("(()=>{INV.menu().find(x=>x.label==='Colour map').kids[1].act();INV.menu().find(x=>x.label==='Max hold').act();const o=JSON.stringify(UI.vzO);INV.set('map','viridis');INV.set('hold',true);return o.includes('magma')&&o.includes('\"hold\":false')})()"))
ck('the Visualizer\'s right-click menu carries them', R("(()=>{let it=null;const o=openMenu;openMenu=(x,y,i)=>{it=i};try{pvMenu({target:document.body,preventDefault(){},stopPropagation(){},clientX:10,clientY:10})}finally{openMenu=o}return !!it&&it.some(x=>x&&x.label==='Colour map')&&it.some(x=>x&&x.label==='Visualizer')})()"))

# 9. nothing while hidden or frozen
R("UI.viz=false;vizApply();0"); pg.wait_for_timeout(300); a = R("INV.n"); pg.wait_for_timeout(1000); b = R("INV.n")
ck('Visualizer hidden: no columns written (%d in 1 s)' % (b - a), a == b, b - a)
R("UI.viz=true;vizApply();0"); pg.wait_for_timeout(600)
if R("typeof AO==='object'"):
    fz = pg.evaluate("()=>new Promise(r=>{const Q=c=>window.AudioLab.run(c);Q('aoLevel(1);0');setTimeout(()=>{const n0=Q('INV.n');setTimeout(()=>{const n1=Q('INV.n');Q('aoFront(\\'test\\');0');r(n1-n0)},900)},300)})")
    ck('background freeze: no columns written', fz == 0, fz)
R("stop();0")
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
b0 = src.index('/* ===== lane E (task IN-V)'); b1 = src.index('/* ===== end of lane E IN-V')
ck('no audio nodes made by the block; no em dashes in its text', not any(k in src[b0:b1] for k in ('createGain', 'createBiquad', 'createAnalyser', 'audioWorklet', '.connect(')) and '—' not in src[b0:b1])
ck('no console errors', not al.errors, al.errors)
al.stop()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
