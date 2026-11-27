"""Task IN-E (lane E): the EQ displays, the user's pick E3 (bandwidth calipers).
Checks the Pro EQ with known bands: a bell's caliper width against the filter theory (a +6 dB bell with Q 1.41 is 1.00 octave wide at its
half-gain points, 2/ln2 asinh(1/2Q)), a cut bell and a narrow one, a band-pass, the corner marks on a low cut and a shelf, the fill between the
summed curve and 0 dB, the gain scale on the left, the analyzer's dBFS scale and tilt on the right, the band read-out with the note and the
width in octaves, the hit test and the dots unchanged (same ±24 dB mapping); the Filter and the Auto Filter (fill to 0 dB, corner mark, caliper
for band-pass and notch); live with pink noise and a sine through the EQ (the response measured from the output against the caliper);
no audio nodes, no console errors. Screenshots in the dark look and at the Light level.
  python3 tools/ui-tests/taskIN_E.py [repo dir] [out dir]"""
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
    return v.replace('\u2009', ' ') if isinstance(v, str) else v  # the formatter's thin space before units, read as a space
print('version', al.version)
R("UI.lite=false;0")
ck('IN-E is there', R("typeof ineBW==='function'&&typeof INSE==='object'&&vizEQ2.toString().includes('ineMarks(g,w,h)')"))

SR = int(R('ctx.sampleRate')); n = int(20 * SR)
rng = np.random.default_rng(1)
wn = rng.standard_normal(n); f = np.fft.rfftfreq(n, 1 / SR); X = np.fft.rfft(wn); X[1:] /= np.sqrt(f[1:]); X[0] = 0; pk = np.fft.irfft(X, n)
pk = pk / np.sqrt(np.mean(pk ** 2)) * 10 ** (-20 / 20)
R("UI.headroom=-6;UI.bitPerfect=false;UI.limiter=false;0")
ids = {'Pink': al.add_audio(np.vstack([pk, pk]).astype(np.float32), SR)}
def play(name, fx, wait=1200):
    R("stop();0")
    al.build({'bpm': 120, 'master': 20 * math.log10(2), 'tracks': [{'kind': 'audio', 'name': name, 'vol': 1.0, 'clips': [{'start': 0, 'len': 40, 'name': name, 'buf': ids[name]}], 'fx': fx}]})
    R("UI.limiter=false;routeMaster();stop();pos=0;toggle();selectTrack(S.tracks[0].id);renderFx();0"); pg.wait_for_timeout(wait)
play('Pink', [{'type': 'eq'}], 800)
BANDS = "[{t:'highpass',f:30,g:0,q:.71,on:true,sl:12},{t:'lowshelf',f:100,g:3,q:.71,on:true},{t:'peaking',f:1000,g:6,q:1.41,on:true},{t:'peaking',f:4000,g:-6,q:4,on:true},{t:'highshelf',f:12000,g:2,q:.71,on:true}]"
SETUP = r"""(()=>{const f=S.tracks[0].fx[0],X=vizInst(f);f.p.bands=%s;f.p.an='prepost';if(X&&X.set)X.set(f.p);if(typeof syncFx==='function')try{syncFx()}catch(e){}renderFx();return!!X})()""" % BANDS
ck('a Pro EQ with known bands (low cut 30 Hz, low shelf 100 Hz, bells +6 dB at 1 kHz Q 1.41 and -6 dB at 4 kHz Q 4, high shelf 12 kHz)', R(SETUP))
pg.wait_for_timeout(600)
CAP = r"""(()=>{const cal=[],cor=[],txt=[];const oc=ineCaliper,ok=ineCorners;ineCaliper=function(g,a,b,y,s,up){cal.push({a,b,y,s,up});return oc.apply(this,arguments)};ineCorners=function(g,l){for(const q of l)cor.push(q.slice());return ok.apply(this,arguments)};
  const c=document.createElement('canvas');c.width=600;c.height=264;const g=c.getContext('2d');g.setTransform(2,0,0,2,0,0);const ft=g.fillText.bind(g);g.fillText=(t,x,y)=>{txt.push([String(t),x,y]);return ft(t,x,y)};
  const f=S.tracks[0].fx[0],X=vizInst(f);%s;try{vizEQ2(g,300,132,f,X)}finally{ineCaliper=oc;ineCorners=ok}
  const px=(x,y)=>Array.from(g.getImageData(Math.round(x*2),Math.round(y*2),1,1).data.slice(0,3));const dy=db=>66-db/24*(66-12);
  return JSON.stringify({cal,cor,txt,bw:INSE.bw.slice(),fillIn:px(fX(1000,300),dy(2)),fillOut:px(fX(300,300)-3,dy(2)),hit:eqHit(f,fX(1000,300),dy(6),300,132)})})()"""
D = json.loads(R(CAP % ''))
print('    calipers', [(c['s'], round(c['a'], 1), round(c['b'], 1)) for c in D['cal']], 'corners', D['cor'], 'bw', D['bw'])
th = 2 / math.log(2) * math.asinh(1 / (2 * 1.41)); th4 = 2 / math.log(2) * math.asinh(1 / (2 * 4))
bw = D['bw']
ck('bell +6 dB at 1 kHz, Q 1.41: caliper %.2f oct, theory %.3f (half-gain points)' % (bw[2] if len(bw) > 2 and bw[2] else -1, th), len(bw) > 2 and bw[2] and abs(bw[2] - th) < .03, bw)
ck('bell -6 dB at 4 kHz, Q 4: caliper %.3f oct, theory %.3f (within the 2 px sampling and the digital warping near 4 kHz)' % (bw[3] if len(bw) > 3 and bw[3] else -1, th4), len(bw) > 3 and bw[3] and abs(bw[3] - th4) < .04, bw)
cal = D['cal']
ck('two calipers with their widths, the boost one above its bell, the cut one below', len(cal) == 2 and cal[0]['up'] and not cal[1]['up'] and cal[0]['s'].endswith(' oct') and cal[0]['a'] < 300 * math.log(1000 / 20) / math.log(1000) < cal[0]['b'], cal)
ck('corner marks on the low cut, the low shelf and the high shelf with their frequencies', [c[1] for c in sorted(D['cor'])] == ['30.0 Hz', '100 Hz', '12.0 kHz'], D['cor'])
T = [t[0] for t in D['txt']]
ck('the gain scale on the left in its colour, with signs and a real minus', any(t[0] == '+6' and t[1] < 10 for t in D['txt']) and any(t[0] == '−12' and t[1] < 10 for t in D['txt']), [t for t in D['txt'] if t[1] < 10][:8])
ck('the analyzer scale on the right in dBFS, with its tilt named', any(t.endswith(' dBFS') for t in T) and 'analyzer, tilt 4.5 dB/oct' in T, [t for t in T if 'dBFS' in t or 'tilt' in t])
ck('the area between the summed curve and 0 dB is filled (under the 1 kHz bell), and not outside it', sum(D['fillIn']) > sum(D['fillOut']) + 6 and D['fillIn'][0] >= D['fillIn'][2], (D['fillIn'], D['fillOut']))
ck('hit test unchanged: the dot of the 1 kHz bell is found at +6 dB on the ±24 dB mapping', D['hit'] == 2 or (isinstance(D['hit'], dict) and 2 in (D['hit'].get('band'), D['hit'].get('i'))), D['hit'])
# read-out with the note and the width: select band 2
R("(()=>{const f=S.tracks[0].fx[0];const s=eqSel(f);s.clear();s.add(2);0})()")
D2 = json.loads(R(CAP % ''))
ro = [t for t in D2['txt'] if t[0].startswith('Bell')]
ck('the selected band\'s read-out adds the note and the width in octaves (Bell 1 kHz B5, Q 1.41, 1.00 oct)', ro and 'B5' in ro[0][0] and ' · Q 1.41 · 1.00 oct' in ro[0][0], ro)
# band-pass and notch
R("(()=>{const f=S.tracks[0].fx[0],X=vizInst(f);f.p.bands=[{t:'bandpass',f:500,g:0,q:2,on:true},{t:'notch',f:3000,g:0,q:2,on:true}];X.set(f.p);eqSel(f).clear();0})()"); pg.wait_for_timeout(300)
D3 = json.loads(R(CAP % ''))
print('    band-pass and notch', [(c['s']) for c in D3['cal']])
th2 = 2 / math.log(2) * math.asinh(1 / (2 * 2))
ck('band-pass (Q 2) and notch (Q 2): calipers at 3 dB under their top and under 0 dB, about %.2f oct each' % th2, len(D3['cal']) == 2 and all(abs(float(c['s'].split()[0]) - th2) < .06 for c in D3['cal']), [c['s'] for c in D3['cal']])
R("(()=>{const f=S.tracks[0].fx[0],X=vizInst(f);f.p.bands=%s;X.set(f.p);0})()" % BANDS); pg.wait_for_timeout(1500)
try: pg.locator('canvas.viz').nth(0).screenshot(path=os.path.join(OUT, 'inE_proeq.png'))
except Exception as e: print('   (shot)', e)
# live: the EQ's output measured against the caliper (pink noise, the post analyser against the pre one)
LV = json.loads(R(r"""(()=>{const X=vizInst(S.tracks[0].fx[0]);const a=INS.fft(X.pre).slice(),b=INS.fft(X.an).slice(),n=a.length,bh=ctx.sampleRate/2/n;const at=f=>{let s=0,c=0;for(let k=Math.round(f/1.06/bh);k<=Math.round(f*1.06/bh);k++){s+=b[k]-a[k];c++}return s/c};return JSON.stringify({g1k:at(1000),g4k:at(4000),g300:at(300)})})()"""))
ck('live, pink noise: post minus pre reads about +6 dB at 1 kHz and -6 dB at 4 kHz (the bells the calipers measure)', abs(LV['g1k'] - 6) < 1.5 and abs(LV['g4k'] + 6) < 2, LV)
R("UI.lite=true;0"); pg.wait_for_timeout(500)
try: pg.locator('canvas.viz').nth(0).screenshot(path=os.path.join(OUT, 'inE_proeq_light.png'))
except Exception as e: print('   (shot)', e)
R("UI.lite=false;0")

# Filter and Auto Filter
play('Pink', [{'type': 'filter', 'p': {'freq': 2000, 'q': 1}}], 800)
F1 = json.loads(R(r"""(()=>{const cor=[];const ok=ineCorners;ineCorners=function(g,l){for(const q of l)cor.push(q.slice());return ok.apply(this,arguments)};const c=document.createElement('canvas');c.width=600;c.height=264;const g=c.getContext('2d');g.setTransform(2,0,0,2,0,0);
  const f=S.tracks[0].fx[0];try{vizFilter(g,300,132,f,null)}finally{ineCorners=ok}const px=(x,y)=>Array.from(g.getImageData(Math.round(x*2),Math.round(y*2),1,1).data.slice(0,3));return JSON.stringify({cor,cut:px(fX(10000,300),132*.5+8),under:px(fX(300,300),132-8)})})()"""))
ck('Filter: the corner mark at its cutoff (2.00 kHz); the fill lies between the curve and 0 dB (filled under 0 dB at 10 kHz where it cuts, nothing at the bottom at 300 Hz where the curve is at 0 dB)', F1['cor'] and F1['cor'][0][1] == '2.00 kHz' and F1['cut'][1] > F1['cut'][0] + 8 and F1['under'][1] < 14, F1)
try: pg.locator('canvas.viz').nth(0).screenshot(path=os.path.join(OUT, 'inE_filter.png'))
except Exception as e: print('   (shot)', e)
AF = {}
for t in ('lp24', 'bp', 'notch', 'peak'):
    play('Pink', [{'type': 'afilt', 'p': {'type': t, 'freq': 1000, 'res': 3, 'mix': 100, 'lamt': 0}}], 700)
    AF[t] = json.loads(R(r"""(()=>{const cal=[],cor=[];const oc=ineCaliper,ok=ineCorners;ineCaliper=function(g,a,b,y,s){cal.push(s);return oc.apply(this,arguments)};ineCorners=function(g,l){for(const q of l)cor.push(q[1]);return ok.apply(this,arguments)};
      const c=document.createElement('canvas');c.width=1080;c.height=264;const g=c.getContext('2d');g.setTransform(2,0,0,2,0,0);const f=S.tracks[0].fx[0];try{VIZX.afilt(g,540,132,f,vizInst(f))}finally{ineCaliper=oc;ineCorners=ok}return JSON.stringify({cal,cor,type:f.p.type})})()"""))
    if t == 'bp':
        try: pg.locator('canvas.viz').nth(0).screenshot(path=os.path.join(OUT, 'inE_afilt_bp.png'))
        except Exception as e: print('   (shot)', e)
print('    Auto Filter', AF)
ck('Auto Filter: corner mark for low-pass 24, a caliper for band-pass, notch and peak', AF['lp24']['cor'] == ['1.00 kHz'] and all(AF[k]['cal'] and AF[k]['cal'][0].endswith(' oct') for k in ('bp', 'notch', 'peak')), AF)
R("stop();0")
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
b0 = src.find('/* ===== lane E (task IN-E)'); b1 = src.find('/* ===== end of lane E IN-E')
ck('no audio nodes made by the block; no em dashes in its text', b0 > 0 and not any(k in src[b0:b1] for k in ('createGain', 'createBiquad', 'createAnalyser', 'audioWorklet', '.connect(', 'wk(')) and '—' not in src[b0:b1])
ck('no console errors', not ERR, ERR[:5])
al.stop()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
