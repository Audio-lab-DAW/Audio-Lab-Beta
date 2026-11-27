"""Task IN-L (lane E): loudness, the user's pick L2 (the loudness history).
Checks the history drawer with a made-up history (the colour rule: cyan inside or under the band, yellow above it, red more than 3 LU above; momentary
faint; integrated dashed amber; the band; time marks), then live with signals played through the app (a 1 kHz sine at -18 dBFS in both channels,
pink noise, a step in level): the 10-a-second sampling of LM, the pop-up graph against the readings and the target (Spotify -14: under the band,
cyan; EBU -23: more than 3 LU over, red), its redraw rate (10 a second, 5 at the Light level), Reset, the top-bar graph, the mixer master box graph
(its target menu still opens), the Loudness device and the Meter device drawing through the drawer, LRA settling, nothing drawn while the pop-up is
closed or the frame gate is shut (background freeze), no console errors. Screenshots in the dark look and at the Light level.
  python3 tools/ui-tests/taskIN_L.py [repo dir] [out dir]"""
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
ck('IN-L is there (INS.lhist, INL)', R("typeof INS.lhist==='function'&&typeof INL==='object'&&typeof inlPop==='function'"))

# ---------- 1. the drawer with a made-up history (target -14, band ±1) ----------
D = json.loads(R(r"""(()=>{const c=document.createElement('canvas');c.width=400;c.height=200;const g=c.getContext('2d');g.fillStyle='#000';g.fillRect(0,0,400,200);
  /* 300 samples: S at -20 (under), -14.5 (in the band), -12 (+2, over the band), -9 (+5, far over), 75 each; M 6 LU above S; I -15 */
  const S=i=>i<75?-20:i<150?-14.5:i<225?-12:-9,M=i=>S(i)+6;const Y=INS.lhist(g,40,10,350,170,{lo:-38,hi:-5,target:-14,n:300,span:300,dt:.1,M,S,I:-30,legend:true,tlab:true});
  const px=(x,y)=>Array.from(g.getImageData(Math.floor(x),Math.floor(y),1,1).data.slice(0,3));const X=i=>40+350*i/299,f=(i,v,o={})=>{/* the line pixel nearest to (i,v) */let best=null;for(let d=-2;d<=2;d++){const p=px(X(i),Y(v)+d);const sc=q=>o.grey?(q[0]+q[1]+q[2])-3*(Math.max(...q)-Math.min(...q)):Math.max(...q)-Math.min(...q);if(!best||sc(p)>sc(best))best=p}return best};
  const tm=[];for(const s of[0,5,10,15,20,25])tm.push(px(40+350-s/0.1*350/299,180-1));
  return JSON.stringify({under:f(40,-20),inband:f(110,-14.5),over:f(190,-12),far:f(260,-9),mom:f(40,-14,{grey:1}),band:px(60,Y(-14.5)+2),bandOut:px(60,Y(-18.5)),I:[px(300,Y(-30)),px(303,Y(-30)),px(306,Y(-30)),px(309,Y(-30))],tm})})()"""))
print('   ', json.dumps(D))
cy, ye, rd = (76, 201, 240), (245, 200, 76), (255, 107, 107)
def hue(p):
    r, g, b = p
    if b > r + 60 and g > r + 40: return 'cyan'
    if r > b + 60 and g > b + 40 and r >= g: return 'yellow'
    if r > g + 60 and r > b + 60: return 'red'
    return '?'
ck('colour rule: under the band cyan, in the band cyan, above the band yellow, more than 3 LU above red', [hue(D[k]) for k in ('under', 'inband', 'over', 'far')] == ['cyan', 'cyan', 'yellow', 'red'], [(D[k], hue(D[k])) for k in ('under', 'inband', 'over', 'far')])
ck('momentary is a faint grey line behind', 40 < D['mom'][0] < 140 and abs(D['mom'][0] - D['mom'][2]) < 12, D['mom'])
ck('the target band (±1 LU) is shaded green, outside it is not', D['band'][1] >= D['band'][0] + 5 and D['bandOut'][1] - D['bandOut'][0] < 3, (D['band'], D['bandOut']))
ck('integrated is a dashed amber line', any(p[0] > 150 and p[2] < 120 for p in D['I']) and any(p[0] < 60 for p in D['I']), D['I'])
ck('time marks every 5 s along the bottom (30 s window)', all(sum(p) > 60 for p in D['tm']), D['tm'])
TS = json.loads(R("JSON.stringify([30,60,240,600].map(secs=>{const c=document.createElement('canvas');c.width=300;c.height=60;const g=c.getContext('2d');const seen=[];const f=g.fillText.bind(g);g.fillText=(t,...a)=>{seen.push(t);return f(t,...a)};INS.lhist(g,0,0,300,40,{lo:-40,hi:0,target:-14,n:2,span:secs*10,dt:.1,S:()=>-20,tlab:true,lab:false});return seen}))"))
ck('time labels: 5 s steps for 30 s, coarser for longer spans, with a real minus sign', TS[0][:3] == ['now', '−5 s', '−10 s'] and TS[1][1] in ('−10 s', '−15 s') and any('min' in t for t in TS[3]), TS)

# ---------- 2. live ----------
SR = int(R('ctx.sampleRate')); n = int(30 * SR); t = np.arange(n) / SR
A18 = 10 ** (-18 / 20)
s1k = A18 * np.sin(2 * np.pi * 1000 * t)
step = np.where(t < 8, 10 ** (-30 / 20), A18) * np.sin(2 * np.pi * 1000 * t)
R("UI.headroom=-6;UI.bitPerfect=false;UI.limiter=false;0")
ids = {'Sine': al.add_audio(np.vstack([s1k, s1k]).astype(np.float32), SR), 'Step': al.add_audio(np.vstack([step, step]).astype(np.float32), SR)}
def play(name, wait=1500, fx=None):
    R("stop();0")
    al.build({'bpm': 120, 'master': 20 * math.log10(2), 'tracks': [{'kind': 'audio', 'name': name, 'vol': 1.0, 'clips': [{'start': 0, 'len': 60, 'name': name, 'buf': ids[name]}], 'fx': fx or []}]})
    R("UI.limiter=false;routeMaster();stop();pos=0;toggle();0"); pg.wait_for_timeout(wait)
R("UI.lufsP='spot';0")
play('Sine', 500)
R("if(LM.w)LM.w.cmd('reset');LM.tpMax=-90;LM.hist=[];0"); pg.wait_for_timeout(5000)
L = json.loads(R("JSON.stringify({n:INL.n,S:INL.at(INL.S,INL.n-1,INL.n),M:INL.at(INL.M,INL.n-1,INL.n),LS:LM.S,LM:LM.M,I:LM.I})"))
print('   ', L)
ck('live: the master history samples LM 10 times a second (about 50 in 5 s after a reset)', 40 <= L['n'] <= 56, L['n'])
ck('live: the newest samples are the readings (a -18 dBFS sine in both channels: about -18 LUFS)', abs(L['S'] - L['LS']) < 0.3 and abs(L['M'] + 18) < 0.5, L)
R("lmOpen();0"); pg.wait_for_timeout(700)
P = json.loads(R(r"""(()=>{const cv=document.getElementById('lmC');const g=cv.getContext('2d'),d=Math.min(2,devicePixelRatio||1);const w=cv.width,h=cv.height;let c=0,y=0,r=0;const data=g.getImageData(Math.round(w*.75),0,Math.round(w*.2),h).data;
  for(let i=0;i<data.length;i+=4){const R=data[i],G=data[i+1],B=data[i+2];if(B>180&&G>150&&R<130)c++;if(R>200&&G>160&&B<110)y++;if(R>220&&G<130&&B<130)r++}return JSON.stringify({c,y,r})})()"""))
ck('pop-up: -18 LUFS against Spotify (-14) is under the band: the line is cyan', P['c'] > 20 and P['r'] < 5, P)
try: pg.locator('#lufsPop').screenshot(path=os.path.join(OUT, 'inL_popup_spot.png'))
except Exception as e: print('   (shot)', e)
R("UI.lufsP='ebu';lmPaint();0"); pg.wait_for_timeout(500)
P2 = json.loads(R(r"""(()=>{const cv=document.getElementById('lmC');const g=cv.getContext('2d'),w=cv.width,h=cv.height;let c=0,r=0;const data=g.getImageData(Math.round(w*.75),0,Math.round(w*.2),h).data;
  for(let i=0;i<data.length;i+=4){const R=data[i],G=data[i+1],B=data[i+2];if(B>180&&G>150&&R<130)c++;if(R>220&&G<130&&B<130)r++}return JSON.stringify({c,r})})()"""))
ck('pop-up: the same against EBU R128 (-23) is 5 LU over: the line is red', P2['r'] > 20 and P2['c'] < 5, P2)
try: pg.locator('#lufsPop').screenshot(path=os.path.join(OUT, 'inL_popup_ebu.png'))
except Exception as e: print('   (shot)', e)
R("UI.lufsP='spot';lmPaint();0")
R("UI.lite=false;window.__pc=0;const o=inlPop;inlPop=function(){__pc++;return o.apply(this,arguments)};window.__op=o;0")
pg.wait_for_timeout(2000); full = R("__pc")
R("__pc=0;UI.lite=true;0"); pg.wait_for_timeout(2000); lite = R("__pc")
print('    pop-up redraws in 2 s:', full, 'Light:', lite)
ck('pop-up redrawn about 10 times a second (plus lmPaint 4), half at the Light level', 22 <= full <= 32 and lite < full * 0.75, (full, lite))
if R("typeof AO==='object'"):
    fz = pg.evaluate("()=>new Promise(r=>{const Q=c=>window.AudioLab.run(c);Q('aoLevel(1);0');setTimeout(()=>{const n0=Q('__pc');setTimeout(()=>{const n1=Q('__pc');Q('aoFront(\\'test\\');0');r(n1-n0)},900)},300)})")
    ck('background freeze (aoLevel 1: the frame gate shut, screen timers off): the pop-up graph is not redrawn', fz == 0, fz)
R("document.querySelector('#lufsPop [data-lm=\"reset\"]').click();0"); pg.wait_for_timeout(150)
ck('Reset in the pop-up clears the history', R("INL.n") <= 2, R("INL.n"))
R("lmClose();__pc=0;0"); pg.wait_for_timeout(1000)
ck('pop-up closed: its graph is not drawn', R("__pc") == 0, R("__pc"))
R("inlPop=__op;0")
pg.wait_for_timeout(6000)
TB = json.loads(R(r"""(()=>{const cv=document.querySelector('#lufsB .lfgr');if(!cv||!cv.offsetParent)return JSON.stringify(null);const g=cv.getContext('2d'),d=g.getImageData(0,0,cv.width,cv.height).data;let c=0,gr=0;for(let i=0;i<d.length;i+=4){if(d[i+2]>180&&d[i+1]>150&&d[i]<130)c++;if(d[i+1]>d[i]+10&&d[i+1]>20)gr++}return JSON.stringify({c,gr})})()"""))
ck('top-bar graph: the band and the cyan short-term line', TB is not None and TB['c'] > 3 and TB['gr'] > 10, TB)
try: pg.locator('#lufsB').screenshot(path=os.path.join(OUT, 'inL_topbar.png'))
except Exception as e: print('   (shot)', e)

# mixer master box
R("openMixer();0"); pg.wait_for_timeout(2500)
MX = json.loads(R(r"""(()=>{const cv=document.querySelector('#mixWin .mxme .mxtg canvas.inlh');if(!cv)return JSON.stringify(null);const g=cv.getContext('2d'),d=g.getImageData(0,0,cv.width,cv.height).data;let c=0;for(let i=0;i<d.length;i+=4)if(d[i+2]>180&&d[i+1]>150&&d[i]<130)c++;
  const bar=document.querySelector('#mixWin .mxme .mxtg .mxbar');return JSON.stringify({c,w:cv.width,barHidden:!bar||getComputedStyle(bar).display==='none'})})()"""))
ck('mixer master box: the 30 s graph replaces the target bar', MX is not None and MX['c'] > 3 and MX['barHidden'], MX)
R("document.querySelector('#mixWin .mxme .mxtg').click();0"); pg.wait_for_timeout(300)
ck('mixer master box: a click still opens the target menu', R("!document.getElementById('ctxm').hidden&&/Loudness target/.test(document.getElementById('ctxm').textContent)"))
R("closeMenu&&closeMenu();0")
try: pg.locator('#mixWin .mx.master').screenshot(path=os.path.join(OUT, 'inL_master.png'))
except Exception as e: print('   (shot)', e)
R("UI.lite=true;document.body.classList.add('lite');lmOpen();0"); pg.wait_for_timeout(1200)
pg.screenshot(path=os.path.join(OUT, 'inL_light.png'))
R("lmClose();UI.lite=false;document.body.classList.remove('lite');0")
R("closeMixer&&closeMixer();0") if R("typeof closeMixer==='function'") else None

# ---------- 3. the Loudness and Meter devices ----------
play('Step', 600, [{'type': 'loud', 'p': {'target': -14}}, {'type': 'measure', 'p': {'view': 'loud', 'tgt': 'spot'}}])
R("selectTrack(S.tracks[0].id);renderFx();0"); pg.wait_for_timeout(11000)
DV = json.loads(R(r"""(()=>{const t=curT(),out={};for(const f of t.fx){const cv=document.querySelector('canvas.viz[data-id="'+f.id+'"]');if(!cv){out[f.type]=null;continue}const g=cv.getContext('2d'),d=g.getImageData(0,0,cv.width,cv.height).data;let c=0,y=0,r=0;
  for(let i=0;i<d.length;i+=4){const R=d[i],G=d[i+1],B=d[i+2];if(B>180&&G>150&&R<130)c++;if(R>200&&G>160&&B<110)y++;if(R>220&&G<130&&B<130)r++}const X=vizInst(f);out[f.type]={c,y,r,settle:X&&X.H?inlSettle(X.H):(X?X.hn:null)}}return JSON.stringify(out)})()"""))
print('   ', DV)
ck('Loudness device: its history draws through the drawer (-30 then -18 LUFS, both under the -14 target: cyan)', DV.get('loud') and DV['loud']['c'] > 20, DV.get('loud'))
ck('Meter device: its history draws through the drawer', DV.get('measure') and DV['measure']['c'] > 20 and 'INS.lhist' in R("msuHist.toString()"), DV.get('measure'))
ck('LRA settling: under 60 s of sound since the start, both devices count it', DV.get('loud') and 0 < DV['loud']['settle'] < 600 and DV.get('measure') and DV['measure']['settle'] < 600, DV)
try:
    pg.locator('canvas.viz').nth(0).screenshot(path=os.path.join(OUT, 'inL_loud_device.png'))
    pg.locator('canvas.viz').nth(1).screenshot(path=os.path.join(OUT, 'inL_meter_device.png'))
except Exception as e: print('   (shot)', e)
ck('the Loudness device target line still drags on the -40 to 0 scale (unchanged handler)', 'p.target=clamp(-40+(1-(y-10)/(h-26))*40,-30,-5)' in open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read())
R("stop();0")

src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
b0 = src.index('/* ===== lane E (task IN-L)'); b1 = src.index('/* ===== end of lane E IN-L')
ck('no audio nodes made by the block; no em dashes in its text', not any(k in src[b0:b1] for k in ('createGain', 'createBiquad', 'createAnalyser', 'audioWorklet', '.connect(', "wk(")) and '—' not in src[b0:b1])
ck('no console errors', not al.errors, al.errors)
al.stop()
print('%d/%d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
