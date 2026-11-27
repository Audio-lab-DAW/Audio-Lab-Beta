"""Task NI-1a (lane D): I3 "Why is this clipping?", the engine (clip event log and NI_clipExplain).
Builds test projects from known signals (audio clips, stereo, so the pan law does not touch them) and checks:
  - a project where Kick plus Bass clip at bar 9 (beat 32 at 120 BPM): played live, the clip event is logged there (master),
    the explanation finds bar 9, names Kick and Bass, the shares are within 2% of a direct calculation from the signals,
    a phase-inverted track shows a negative share, the overshoot and the words are right, a second call comes from the cache
  - the same project with a quiet kick: played live, nothing is logged, and the explanation says there is no clip
  - a strip explanation reports the track's own level (master gain taken out)
  - inter-sample peak: a sine at a quarter of the sample rate, phase 45 degrees, amplitude 1.2: sample peak -1.4 dB, true peak +1.6 dB
  - no console errors
  python3 tools/ui-tests/taskNI_1a.py [repo dir]"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
N = [0, 0]; FAIL = []
def ck(name, ok, info=''):
    N[0] += 1
    if ok: N[1] += 1; print('  ok  ', name, info if info != '' else '')
    else: FAIL.append(name); print('  FAIL', name, info)

SR = 44100; BPM = 120; LEN_S = 24.0; n = int(LEN_S * SR); t = np.arange(n) / SR
def kick_sig(big):
    x = np.zeros(n)
    for b in range(0, 48):
        s0 = int(b * 60 / BPM * SR); amp = (0.8 if big else 0.2) if b == 32 else 0.2
        m = min(n - s0, int(0.4 * SR)); tt = np.arange(m) / SR
        x[s0:s0 + m] += amp * np.exp(-tt / 1.0) * np.cos(2 * np.pi * 55 * tt)
    return x
bass = 0.5 * np.cos(2 * np.pi * 110 * t)
anti = -0.1 * np.cos(2 * np.pi * 110 * t)
st = lambda x: np.vstack([x, x]).astype(np.float32)

al = AudioLab(os.path.join(ROOT, 'index.html')); al.start()
print('version', al.version)
al.run("UI.headroom=-6;UI.bitPerfect=false;0")
MASTER = 20 * math.log10(2)  # the master fader at +6 dB makes up for the default 6 dB headroom: master gain exactly 1
def build(big):
    ids = {k: al.add_audio(st(v), SR) for k, v in (('Kick', kick_sig(big)), ('Bass', bass), ('Anti', anti))}
    tr = [{'kind': 'audio', 'name': k, 'vol': 1.0, 'clips': [{'start': 0, 'len': 48, 'name': k + ' clip', 'buf': ids[k]}]} for k in ('Kick', 'Bass', 'Anti')]
    al.build({'bpm': BPM, 'master': MASTER, 'tracks': tr})
    al.run("NI_clipClear();0")
def play_live(b0, secs):
    al.run("stop();pos=%g;toggle();0" % b0); al.page.wait_for_timeout(int(secs * 1000)); al.run("stop();0")
def explain(expr):
    return al.page.evaluate("c=>AudioLab.run(c)", "(async()=>{const r=await %s;return JSON.parse(JSON.stringify(r))})()" % expr)

# 1. Kick plus Bass clip at bar 9
build(True)
mg = al.run("masterGain()"); ck('master gain is about 1 for the test (6 dB headroom, master at +6 dB)', abs(mg - 1) < 0.01, mg)
for limOn in (False, True):
    al.run("UI.limiter=%s;routeMaster();NI_clipClear();0" % ('true' if limOn else 'false'))
    tag = 'safety limiter %s' % ('on' if limOn else 'off')
    play_live(30, 4.0)
    log = al.run("JSON.parse(JSON.stringify(NI_clipLog()))")
    mlog = [e for e in log if e['src'] == 'master']
    ck(tag + ': played live, one master clip event logged', len(mlog) == 1, [(round(e['t'], 2), round(e['db'], 2), e['lim']) for e in log])
    ck(tag + ': the event is at beat 32 (bar 9), within one beat', bool(mlog) and abs(mlog[0]['t'] - 32) < 1, mlog and mlog[0]['t'])
    ck(tag + ': the event says whether the limiter caught it', bool(mlog) and mlog[0]['lim'] == limOn, mlog and mlog[0])
    if limOn: ck(tag + ': the limiter was at its ceiling, so only a lower bound under the real +1.6 dB', bool(mlog) and mlog[0]['sat'] and mlog[0]['db'] < 20 * math.log10(1.2 * mg), mlog and mlog[0])
    else: ck(tag + ': the level read live is over 0 dB and not above the real peak (+1.6 dB; the meter samples once a frame)', bool(mlog) and 0 < mlog[0]['db'] < 20 * math.log10(1.2 * mg) + 0.3, mlog and mlog[0]['db'])
    ck(tag + ': no strip event (no track is over 0 dB on its own)', all(e['src'] == 'master' for e in log), [e['src'] for e in log])
r = explain("NI_clipExplain()")
ck('explanation of the last event: a clip', r and r.get('clip') is True, r and r.get('peakDb'))
ck('it is at bar 9, beat 1', r['where']['bar'] == 9 and r['where']['beat'] == 1, r['where'])
names = [q['name'] for q in r['tracks']]
ck('Kick and Bass named, Bass and Kick the top two', set(names[:2]) == {'Kick', 'Bass'}, names)
# direct calculation from the signals at the peak sample
i = round((al.run("secOf(%r)" % r['b0']) * SR)) + r['i']
k, b, a = kick_sig(True)[i], bass[i], anti[i]; m = mg * (k + b + a)
sh = {q['name']: q['share'] for q in r['tracks']}
ck('peak sample value matches the signals (within 0.1%)', abs(r['peak'] - abs(m)) < 1e-3 * abs(m), (r['peak'], m))
for nm, v in (('Kick', mg * k), ('Bass', mg * b), ('Anti', mg * a)):
    ck('%s share within 2%% of the direct calculation' % nm, abs(sh[nm] - v / m) < 0.02, (round(sh[nm], 4), round(v / m, 4)))
ck('the phase-inverted track shows a negative share', sh['Anti'] < 0, sh['Anti'])
ck('nothing left over (no sends, groups or master effects)', abs(r['rest']['share']) < 0.005, r['rest'])
ck('overshoot is 20 log10 of the peak', abs(r['overDb'] - 20 * math.log10(abs(m))) < 0.01, (r['overDb'], 20 * math.log10(abs(m))))
ck('inter-sample peak at or above the sample peak', r['tpDb'] >= r['peakDb'] - 1e-6, (r['tpDb'], r['peakDb']))
w = r['words']; print('    words:', w)
ck('words: "Bass + Kick add up here", bar 9, the other way: Anti', ('add up here' in w) and ('bar 9, beat 1' in w) and ('Pulling the other way: Anti' in w) and ('—' not in w), w)
same = al.page.evaluate("c=>AudioLab.run(c)", "(async()=>{const a=await NI_clipExplain(32),t0=performance.now(),b=await NI_clipExplain(32);return [a===b,performance.now()-t0]})()")
ck('a second call is served from the cache', same[0] and same[1] < 50, same)
ck('measured in reasonable time (under 5 s)', r['ms'] < 5000, r['ms'])
# a strip explanation: the Kick's own level, master gain taken out
rs = explain("NI_clipExplain(32,{src:%s})" % json.dumps(al.tracks['Kick']))
ck('strip explanation: Kick on its own peaks at -1.9 dB (0.8)', rs['strip'] and abs(rs['strip']['pkDb'] - 20 * math.log10(0.8)) < 0.2, rs.get('strip'))
ck('strip explanation names the clip that plays', rs['strip'] and rs['strip']['clips'] == ['Kick clip'], rs.get('strip'))
# a change to the song gives a fresh measurement
al.run("trkById(%s).vol=0.5;changed(false);0" % json.dumps(al.tracks['Bass']))
r2 = explain("NI_clipExplain(32)")
ck('after an edit the result is measured again (Bass share drops)', r2['tracks'] and {q['name']: q['share'] for q in r2['tracks']}['Bass'] < sh['Bass'] - 0.05, r2.get('words'))

# 2. no overs
build(False)
al.run("UI.limiter=true;routeMaster();0")
play_live(30, 4.0)
log = al.run("JSON.parse(JSON.stringify(NI_clipLog()))")
ck('quiet project played live: nothing logged', len(log) == 0, log)
r = explain("NI_clipExplain(32)")
ck('quiet project: the explanation says no clip', r['clip'] is False and r['words'].startswith('No clip here'), r['words'])
ck('quiet project: no event, no explanation of the last event', al.page.evaluate("c=>AudioLab.run(c)", "(async()=>await NI_clipExplain()===null)()"))

# 3. inter-sample peak
x = 1.2 * np.sin(2 * np.pi * (SR / 4) * t + np.pi / 4)
idx = al.add_audio(st(x), SR)
al.build({'bpm': BPM, 'master': MASTER, 'tracks': [{'kind': 'audio', 'name': 'Quarter', 'vol': 1.0, 'clips': [{'start': 0, 'len': 16, 'name': 'q', 'buf': idx}]}]})
r = explain("NI_clipExplain(8,{sr:%d})" % SR)
ck('quarter-rate sine: sample peak -1.4 dB (no clip)', r['clip'] is False and abs(r['peakDb'] - 20 * math.log10(1.2 * math.sqrt(.5))) < 0.1, r['peakDb'])
ck('quarter-rate sine: inter-sample peak +1.6 dB (within 0.15 dB)', abs(r['tpDb'] - 20 * math.log10(1.2)) < 0.15, r['tpDb'])

# 4. the audio path is untouched: the meters' hooks only read
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
blk = src[src.index('/* ===== lane D (task NI-1a)'):src.index('/* ===== end of lane D NI-1a')]
ck('no audio nodes or worklets made in the lane D block', not any(k in blk for k in ('createGain', 'createBiquad', 'AudioWorklet', 'audioWorklet', '.connect(')), '')
ck('no em dashes in lane D text', '—' not in blk, '')
ck('no console errors', not al.errors, al.errors)
al.stop()
print('%d/%d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
