"""Meter (v0.186) on the Fractals demo master:
 1. the sound is bit for bit the same with and without a Meter (on the Kick track and on the master);
 2. playing 30 s of Drop 1 live, the Meter's integrated loudness and highest true peak agree with the master read-out (LM),
    with the master limiter switched off so both see the same signal;
 3. an offline render of the same beats, measured here in Python (ITU-R BS.1770-5: K-weighting with the printed 48 kHz
    coefficients, 400 ms blocks every 100 ms, -70 LUFS and -10 LU gates; true peak with the Annex 2 filter and, as a
    second opinion, scipy's 4x resample_poly), agrees with both;
 4. the cost on the audio thread with the Meter on the master (the app's own load reading from the meter worklet).
    python3 tools/engine-tests/meter_fractals.py [index.html]"""
import sys, os, json, hashlib, time
import numpy as np
from scipy.signal import lfilter, resample_poly
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab

def kweight(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]; a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]; a2 = [1.0, -1.99004745483398, 0.99007225036621]
    return lfilter(b2, a2, lfilter(b1, a1, x))
def integrated(x, sr=48000):
    y = np.array([kweight(c.astype(np.float64)) for c in x]); blk, hop = int(.4 * sr), int(.1 * sr)
    z = np.array([np.sum(np.mean(y[:, i:i + blk] ** 2, axis=1)) for i in range(0, y.shape[1] - blk + 1, hop)])
    L = -0.691 + 10 * np.log10(np.maximum(z, 1e-20)); g1 = z[L > -70]
    thr = -0.691 + 10 * np.log10(np.mean(g1)) - 10; g2 = z[(L > -70) & (L > thr)]
    return -0.691 + 10 * np.log10(np.mean(g2))
H = [0.001708984375,0.010986328125,-0.0196533203125,0.033203125,-0.0594482421875,0.1373291015625,0.97216796875,-0.102294921875,0.047607421875,-0.0266113281250,0.014892578125,-0.00830078125,
     -0.0291748046875,0.029296875,-0.0517578125,0.089111328125,-0.16650390625,0.465087890625,0.77978515625,-0.2003173828125,0.1015625,-0.0582275390625,0.0330810546875,-0.0189208984375]
PH = [H[:12], H[12:], H[12:][::-1], H[:12][::-1]]
def truepeak_1770(x): return 20 * np.log10(max(max(np.max(np.abs(np.convolve(c.astype(np.float64), p))) for p in PH) for c in x))
def truepeak_scipy(x): return 20 * np.log10(max(np.max(np.abs(resample_poly(c.astype(np.float64), 4, 1))) for c in x))

al = AudioLab(sys.argv[1] if len(sys.argv) > 1 else 'index.html'); al.start()
al.tracks = json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
md5 = lambda x: hashlib.md5(x.tobytes()).hexdigest()[:12]
# 1. pass-through
a, sr = al.render(b0=64, b1=96, only='Kick')
al.run("(()=>{const t=S.tracks.find(t=>t.name==='Kick');t.fx.push(mkFx('measure'));S.mfx.push(mkFx('measure'));changed(true)})()")
b, sr = al.render(b0=64, b1=96, only='Kick')
print('1. Kick beats 64-96 without / with a Meter on the track and on the master:', md5(a), md5(b), 'same' if np.array_equal(a, b) else 'DIFFERENT')
al.run("(()=>{const t=S.tracks.find(t=>t.name==='Kick');t.fx=t.fx.filter(f=>f.type!=='measure');changed(true)})()")
# 2. live, limiter off, Meter last on the master
al.run("(()=>{UI.limiter=false;ensureCtx();routeMaster();selectTrack('__m');renderFx()})()")
b0 = 32 * 4
al.run("pos=%d;start()" % b0); time.sleep(1.0)
st = al.run("(()=>{const X=MFXM.get(S.mfx.find(f=>f.type==='measure').id);X.reset();LM.w.cmd('reset');setTimeout(()=>{LM.tpMax=-90},300);return JSON.stringify({b:curDisp(),sr:ctx.sampleRate})})()")
st = json.loads(st); time.sleep(30)
rd = json.loads(al.run("(()=>{const X=MFXM.get(S.mfx.find(f=>f.type==='measure').id);return JSON.stringify({b:curDisp(),I:X.I,tp:X.tp,LRA:X.LRA,psr:X.psr,LMI:LM.I,LMtp:LM.tpMax,LMlra:LM.LRA,load:CPU.aud})})()"))
al.run("stop()")
print('2. live from beat %.2f to %.2f (%s Hz): Meter I %.2f LUFS, true peak %.2f dBTP, LRA %.1f | master read-out I %.2f, true peak %.2f, LRA %.1f'
      % (st['b'], rd['b'], st['sr'], rd['I'], rd['tp'], rd['LRA'], rd['LMI'], rd['LMtp'], rd['LMlra']))
# 3. offline render of the same beats (limiter off), measured in Python
x, sr = al.render(b0=st['b'], b1=rd['b'], sr=48000, lim=False)
print('3. offline render, Python BS.1770: I %.2f LUFS, true peak %.2f dBTP (Annex 2 filter), %.2f dBTP (scipy 4x), sample peak %.2f dBFS'
      % (integrated(x), truepeak_1770(x), truepeak_scipy(x), 20 * np.log10(np.max(np.abs(x)))))
# 4. audio-thread load (the app's own reading), playing the drop, without and with the Meter on the master
def load(sec=12):
    al.run("pos=%d;start()" % b0); time.sleep(2); v=[]
    for i in range(sec*4):
        time.sleep(.25); q=al.run("CPU.aud"); v.append(q)
    al.run("stop()"); v=[q for q in v if q is not None]; return (np.mean(v), len(v)) if v else (None, 0)
with_m = load()
al.run("(()=>{S.mfx=S.mfx.filter(f=>f.type!=='measure');changed(true);routeMaster()})()")
without_m = load()
print('4. audio load while playing (fraction of the time per block, %d / %d readings): without Meter %s, with Meter on the master %s' % (without_m[1], with_m[1], without_m[0], with_m[0]))
print('errors', al.errors); al.stop()
