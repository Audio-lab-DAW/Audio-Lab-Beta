"""Test material for the effect presets (preset library part 3), rendered by the app itself at 145 BPM and saved to an .npz:
drums (a psytrance kit beat), bass (Psy Bass rolling K-B-B-B on A), pad (a held A minor chord), lead (a saw lead phrase),
vocal (two of the Fractals voice samples), mix (the Fractals demo, beats 64 to 72, through its master chain), kick (the kit's kick on every beat, the source for the Ducker),
click (one 4 ms burst), noise (pink) and glide (a saw gliding an octave up and down); the MIDI effects play an instrument live instead. Every material is 8 beats long (3.31 s) and peaks at -6 dBFS; mix and pad are made stereo (see below).
python3 tools/engine-tests/fx_materials.py index.html out.npz"""
import sys, os, json, numpy as np
from scipy.io import wavfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
IDX = sys.argv[1] if len(sys.argv) > 1 else 'index.html'; OUT = sys.argv[2] if len(sys.argv) > 2 else 'fx_materials.npz'
ROOT = os.path.dirname(os.path.abspath(IDX)); SR = 44100; BPM = 145; NB = 8; N = int(NB*60/BPM*SR)
al = AudioLab(IDX); al.start(); print('version', al.version, 'errors', al.errors)
M = {}
def norm(x):
    x = x[:, :N] if x.shape[1] >= N else np.pad(x, ((0, 0), (0, N-x.shape[1])))
    return (x/np.abs(x).max()*10**(-6/20)).astype(np.float32)
# the Fractals demo is loaded at start
al.tracks = json.loads(al.run("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
mx, sr = al.render(b0=64, b1=64+NB); M['mix'] = norm(mx)
drum = [{'p': 36, 's': b, 'l': .25, 'v': 1} for b in range(NB)] + [{'p': 38, 's': b+1, 'l': .25, 'v': .9} for b in range(0, NB, 2)] + \
       [{'p': 42, 's': b*.25, 'l': .1, 'v': .55 + .2*(b % 2)} for b in range(NB*4)] + [{'p': 46, 's': b+.5, 'l': .2, 'v': .7} for b in range(NB)]
roll = [{'p': 33, 's': b+st*.25, 'l': .22, 'v': .8 if st == 1 else 1} for b in range(NB) for st in (1, 2, 3)]
pad = [{'p': p, 's': 0, 'l': NB-1, 'v': .8} for p in (57, 60, 64, 69)]
lead = [{'p': p, 's': i*.5, 'l': .45, 'v': .85} for i, p in enumerate([69, 72, 76, 79, 76, 72, 74, 69, 81, 79, 76, 72, 74, 76, 72, 69])]
kick = [{'p': 36, 's': b, 'l': .25, 'v': 1} for b in range(NB)]
for nm, pre, notes in (('drums', 'drums', drum), ('kick', 'drums', kick), ('bass', 'psyb', roll), ('pad', 'pad', pad), ('lead', 'saw', lead)):
    al.build({'bpm': BPM, 'tracks': [{'name': nm, 'preset': pre, 'clips': [{'start': 0, 'len': NB, 'notes': notes}]}]})
    x, sr = al.render(b0=0, b1=NB); M[nm] = norm(x)
v = []
for i in (2, 5, 7):
    r, a = wavfile.read(os.path.join(ROOT, 'vox', 'fractals_vox_%02d.wav' % i)); a = a.astype(np.float64)
    if a.dtype.kind == 'i' or np.abs(a).max() > 2: a = a/32768.0
    if a.ndim == 1: a = np.vstack([a, a])
    else: a = a.T
    if r != SR:
        from scipy.signal import resample_poly; a = resample_poly(a, SR, r, axis=1)
    v.append(a); v.append(np.zeros((2, int(.15*SR))))
M['vocal'] = norm(np.hstack(v))
# the app renders these parts centred (left = right); a mix and a pad get a side signal like a real stereo mix: mono under 300 Hz,
# above it a copy 7 ms later at -9 dB, added to the left and taken from the right
from scipy.signal import butter, sosfilt
for k in ('mix', 'pad'):
    m = M[k].mean(axis=0).astype(np.float64); sd = np.roll(sosfilt(butter(2, 300, 'hp', fs=SR, output='sos'), m), int(.007*SR))*10**(-9/20)
    M[k] = norm(np.vstack([m+sd, m-sd]))
rng = np.random.default_rng(1)
c = np.zeros((2, N)); c[:, :int(.004*SR)] = rng.uniform(-1, 1, int(.004*SR)); M['click'] = norm(c)   # one 4 ms burst: echoes and decay of the space effects
w = rng.standard_normal((2, N)); W = np.fft.rfft(w, axis=1); fr = np.maximum(np.fft.rfftfreq(N, 1/SR), 20); w = np.fft.irfft(W/np.sqrt(fr/20), N, axis=1)  # pink noise: frequency response
M['noise'] = norm(w)
# a saw that glides slowly from A3 up to A4 and back with a 5 Hz vibrato: what a pitch corrector does with it depends on its scale and speed
t = np.arange(N)/SR; f = 220*2**(np.where(t < N/SR/2, t/(N/SR/2), 2-t/(N/SR/2)) + .01*np.sin(2*np.pi*5*t)); ph = np.cumsum(f)/SR
g = sum((-1)**(n+1)*np.sin(2*np.pi*n*ph)/n for n in range(1, 30))*2/np.pi; M['glide'] = norm(np.vstack([g, g]))
for k, x in M.items(): print(k, x.shape, 'peak %.3f rms %.1f dB' % (np.abs(x).max(), 20*np.log10(np.sqrt((x**2).mean()))))
np.savez(OUT, **M); print('errors', al.errors); al.stop()
