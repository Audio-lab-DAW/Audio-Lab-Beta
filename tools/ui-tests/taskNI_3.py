"""Task NI-3 (lane D): the analysis worker and the per-beat band cache (NI.an).
Checks:
  - the Fractals demo, beats 64 to 160, every track analysed in the background while the song plays: the dropout counter does not move,
    the song is not changed, silent pieces are skipped without a render; the time per piece is printed
  - known signals (audio tracks, 120 BPM, 44.1 kHz): a 110 Hz sine is found as the strongest peak within 0.3 Hz and reads in its band
    at its level (a full-scale sine reads -3 dB) within 0.6 dB, silence before it is "not playing"; an anti-phase 2 kHz tone has no
    mid and its side band at its level; a 1 kHz tone at -20 dBFS in both channels reads -20.0 LUFS within 0.3 (scaled by the render
    gain); its centroid is 1 kHz; white noise: every band from 60 Hz up equals a direct numpy calculation of the render within 0.6 dB
  - cache: a second ensure renders nothing; with memory cleared (as after a reopen) the pieces come from IndexedDB, no render;
    a one-clip edit re-analyses only the piece of that clip's track; get() of a missing beat queues it and later answers
  - waits while an export runs; a project switch cancels; the worker is a real Worker; no audio nodes in the block; no em dashes;
    no console errors
  python3 tools/ui-tests/taskNI_3.py [repo dir]"""
import sys, os, json, math, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
N = [0, 0]; FAIL = []
def ck(name, ok, info=''):
    N[0] += 1
    if ok: N[1] += 1; print('  ok  ', name, info if info != '' else '')
    else: FAIL.append(name); print('  FAIL', name, info)

al = AudioLab(os.path.join(ROOT, 'index.html')); al.start(); pg = al.page; R = al.run
print('version', al.version)
def A(expr, timeout=None):
    return pg.evaluate("c=>AudioLab.run(c)", "(async()=>{const r=await %s;return JSON.parse(JSON.stringify(r===undefined?null:r))})()" % expr)
SJ = "JSON.stringify(S,function(k,v){return this===S&&k==='work'?undefined:v})"

# 1. the Fractals demo while it plays
pg.set_default_timeout(600000)
before = R(SJ)
# a baseline: 45 s of playing without the analysis (this machine may drop now and then by itself)
R("stop();S.loop=false;pos=64;toggle();0"); pg.wait_for_timeout(1500); b0_ = R("CPU.drop"); pg.wait_for_timeout(45000); base = R("CPU.drop") - b0_; R("stop();0")
R("stop();S.loop=false;pos=64;toggle();0"); pg.wait_for_timeout(1500)
d0 = R("CPU.drop"); t0 = time.time()
pg.evaluate("c=>AudioLab.run(c)", "(window.__fr=NI.an.ensure({b0:64,b1:160}),0)")
pg.wait_for_timeout(45000)
d1 = R("CPU.drop"); on = R("play.on"); mid_st = R("JSON.parse(JSON.stringify(NI.an.status()))"); R("stop();0")
print('    while playing 45 s: baseline drops %d, with the analysis %d; status' % (base, d1 - d0), mid_st)
res = A("window.__fr"); secs = time.time() - t0
st = R("JSON.parse(JSON.stringify(NI.an.status()))")
print('    Fractals 64 to 160:', res, st, '%.1f s' % secs)
ck('Fractals beats 64 to 160: every non-silent piece of every track analysed', res['done'] == res['total'] and not res['cancelled'] and res['renders'] > 0, res)
ck('silent pieces skipped without a render', st['skipped'] > 0 and res['renders'] < res['total'], (st['skipped'], res['renders'], res['total']))
ck('while the song played: no more dropouts than without the analysis', on and d1 - d0 <= base, (base, d1 - d0))
ck('the analysis does not change the song', R(SJ) == before, '')
ck('the analysis runs in a real Worker', R("NI.an.w instanceof Worker"))
kb = R("JSON.parse(JSON.stringify(NI.an.get(S.tracks.find(t=>t.name==='Kick').id,80)))")
ck('Fractals Kick at beat 80: playing, a low peak, loudness and centroid present', kb and kb['play'] == 1 and kb['peaks'] and kb['peaks'][0]['hz'] < 200 and kb['loud'] > -40, kb and (kb['peaks'][:2], kb['loud'], kb['cent']))

# 2. known signals
SR = 44100; BPM = 120; nb = 48; n = nb * SR // 2; t = np.arange(n) / SR
def st2(l, r=None): return np.vstack([l, l if r is None else r]).astype(np.float32)
sine = 0.5 * np.sin(2 * np.pi * 110 * t); sine[:4 * SR // 2] = 0
wide = 0.3 * np.sin(2 * np.pi * 2000 * t)
tone = 0.1 * np.sin(2 * np.pi * 1000 * t)
noise = np.random.default_rng(7).standard_normal(n) * 0.1
bufs = {'Sine110': al.add_audio(st2(sine), SR), 'Wide': al.add_audio(st2(wide, -wide), SR), 'Tone1k': al.add_audio(st2(tone), SR), 'Noise': al.add_audio(st2(noise), SR)}
def build():
    al.build({'bpm': BPM, 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'clips': [{'start': 0, 'len': 24, 'name': k + ' a', 'buf': b}, {'start': 24, 'len': 24, 'off': 24, 'name': k + ' b', 'buf': b}]} for k, b in bufs.items()]})
build()
x, _ = al.render(b0=0, b1=48, sr=SR, only='Tone1k')
g = float(np.sqrt(np.mean(x[0, SR:20 * SR].astype(np.float64) ** 2)) / (0.1 / math.sqrt(2)))
print('    render gain %.5f (%.2f dB)' % (g, 20 * math.log10(g)))
xs, _ = al.render(b0=0, b1=48, sr=SR, only='Sine110')
ck('the second clip continues the first (off 24): the render is one continuous sine', abs(float(np.sqrt(np.mean(xs[0, 15 * SR:20 * SR] ** 2))) - 0.5 * g / math.sqrt(2)) < 1e-3)
res = A("NI.an.ensure({})")
ck('four tracks, two pieces each: 8 renders', res['done'] == 8 and res['renders'] == 8, res)
def get(name, beat): return R("JSON.parse(JSON.stringify((r=>r&&Object.assign({},r,{mid:r.mid&&[...r.mid],side:r.side&&[...r.side]}))(NI.an.get(%s,%g))))" % (json.dumps(al.tracks[name]), beat))
bands = R("NI.an.bands")
bi = lambda f: int(np.argmin([abs(math.log2(f / c)) for c in bands]))
a = get('Sine110', 2); b = get('Sine110', 10); b2 = get('Sine110', 30)
exp = 20 * math.log10(0.5 * g) - 3
ck('silent beat 2 of Sine110 is not playing', a['play'] == 0, a['rms'])
ck('110 Hz sine: strongest peak at 110 Hz within 0.3 Hz (beats 10 and 30, both pieces)', abs(b['peaks'][0]['hz'] - 110) < .3 and abs(b2['peaks'][0]['hz'] - 110) < .3, (b['peaks'][0], b2['peaks'][0]))
ck('110 Hz sine: its band (%.0f Hz) at %.2f dB within 0.6 dB' % (bands[bi(110)], exp), abs(b['mid'][bi(110)] - exp) < .6, b['mid'][bi(110)])
ck('110 Hz sine (L = R): no side', max(b['side']) < -100, max(b['side']))
w = get('Wide', 10); expw = 20 * math.log10(0.3 * g) - 3
ck('anti-phase 2 kHz tone: no mid, its side band at %.2f dB within 0.6 dB' % expw, max(w['mid']) < -100 and abs(w['side'][bi(2000)] - expw) < .6, (max(w['mid']), w['side'][bi(2000)]))
tn = get('Tone1k', 10); expl = -20 + 20 * math.log10(g)
ck('1 kHz tone at -20 dBFS in both channels: %.2f LUFS within 0.3' % expl, abs(tn['loud'] - expl) < .3, tn['loud'])
ck('1 kHz tone: centroid 1 kHz within 30 Hz', abs(tn['cent'] - 1000) < 30, tn['cent'])
# white noise against numpy, beats 4 to 8
xn, _ = al.render(b0=0, b1=48, sr=SR, only='Noise')
NF = 8192; win = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(NF) / NF); nrm = 2 / (NF * np.sum(win ** 2)); bw = SR / NF
worst = 0; info = []
for beat in (4, 7, 30):
    s0 = beat * SR // 2; L = SR // 2; F = (L - NF) // (NF // 2) + 1
    P = np.zeros(NF // 2 + 1)
    for f in range(F):
        seg = 0.5 * (xn[0, s0 + f * NF // 2: s0 + f * NF // 2 + NF] + xn[1, s0 + f * NF // 2: s0 + f * NF // 2 + NF]) * win
        P += np.abs(np.fft.rfft(seg)) ** 2
    P *= nrm / F
    r = get('Noise', beat)
    for k, c in enumerate(bands):
        if c < 60: continue
        lo, hi = c * 2 ** (-1 / 12) / bw, c * 2 ** (1 / 12) / bw
        i0, i1 = int(math.ceil(lo)), int(math.floor(hi))
        if i1 - i0 >= 1: pw = P[i0:i1 + 1].sum()
        else: xx = c / bw; ii = int(xx); fr = xx - ii; pw = (P[ii] * (1 - fr) + P[ii + 1] * fr) * (hi - lo)  # under two bins: the density at the centre times the width
        v = 10 * math.log10(pw + 1e-14)
        worst = max(worst, abs(v - r['mid'][k])); info.append((beat, round(c), round(v - r['mid'][k], 2)))
ck('white noise: every band from 60 Hz up equals numpy on the render within 0.6 dB (beats 4, 7, 30)', worst < .6, ('worst %.2f dB' % worst, [q for q in info if abs(q[2]) > .4][:12]))
# 3. cache
res = A("NI.an.ensure({})")
ck('a second ensure renders nothing', res['renders'] == 0 and res['done'] == 8, res)
i0 = R("NI.an.stats.idb"); R("NI.an.mem.clear();0")
res = A("NI.an.ensure({})")
ck('memory cleared (as after a reopen): all 8 pieces from IndexedDB, no render', res['renders'] == 0 and R("NI.an.stats.idb") - i0 == 8, (res, R("NI.an.stats.idb") - i0))
R("(()=>{const t=trkById(%s);t.clips[1].len=20;changed(false)})()" % json.dumps(al.tracks['Sine110']))
res = A("NI.an.ensure({})")
ck('a one-clip edit (the second Sine110 clip) re-analyses one piece of that track only', res['renders'] == 1 and R("NI.an.last[NI.an.last.length-1]") == 'Sine110 24', (res, R("NI.an.last.slice(-2)")))
R("(()=>{const t=trkById(%s);t.clips[1].len=22;changed(false)})()" % json.dumps(al.tracks['Sine110']))
ck('get() of a beat not analysed yet answers null and queues it', R("NI.an.get(%s,30)===null&&NI.an.q.length+(NI.an.busy?1:0)>0" % json.dumps(al.tracks['Sine110'])))
pg.wait_for_function("id=>!!NI.an.get(id,30,{noQueue:true})", arg=al.tracks['Sine110'], timeout=30000)
ck('... and answers once it is done', R("NI.an.get(%s,30).peaks[0].hz>109" % json.dumps(al.tracks['Sine110'])))
ck('a beat past the clips answers "silent" with no render', R("NI.an.get(%s,80).silent===true" % json.dumps(al.tracks['Sine110'])))
# 4. export, project switch
R("NI.an.mem.clear();EXR=true;0")
pg.evaluate("c=>AudioLab.run(c)", "(window.__ens=NI.an.ensure({tracks:[%s]}),0)" % json.dumps(al.tracks['Noise']))
pg.wait_for_timeout(500)
r1 = R("JSON.parse(JSON.stringify(NI.an.status()))")
ck('while an export runs the analysis waits and says why', r1['paused'] == 'an export is running' and r1['busy'], r1)
R("EXR=false;0")
res = A("window.__ens")
ck('after the export it goes on', res['done'] == 2 and not res['cancelled'], res)
R("NI.an.mem.clear();for(const t of S.tracks)t.vol=.9;changed(false);0")  # new content: nothing in the cache
pg.evaluate("c=>AudioLab.run(c)", "(window.__ens=NI.an.ensure({}),0)")
pg.wait_for_timeout(150)
R("(()=>{const id='p'+rid();PJ.list.push({id,name:'Other',S:JSON.parse(JSON.stringify(S))});switchProject(id)})()")
res = A("window.__ens")
ck('switching to another project cancels the pass', res['cancelled'] and res['done'] < res['total'], res)
pg.wait_for_timeout(1500)
ck('the queue is empty after the switch', R("NI.an.q.length===0&&!NI.an.busy"), R("JSON.stringify(NI.an.status())"))
# 5. the code
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
blk = src[src.index('/* ===== lane D (task NI-3)'):src.index('/* ===== end of lane D NI-3')]
ck('no audio nodes, worklets or animation frames in the NI-3 block', not any(k in blk for k in ('createGain', 'createBiquad', 'AudioWorklet', 'audioWorklet', '.connect(', 'requestAnimationFrame', 'setInterval')), '')
ck('no em dashes in the NI-3 block', '—' not in blk, '')
ck('no console errors', not al.errors, al.errors)
al.stop()
print('%d/%d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
