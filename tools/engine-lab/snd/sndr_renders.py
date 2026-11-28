"""Task SND-R (lane L): A/B renders for listening, through the app's own render (44.1 kHz, 16 bit, not normalised: the levels compare too).
  python3 tools/engine-lab/snd/sndr_renders.py before.html after.html
sndr_crush2_before / _after: two tracks, a saw bass and a saw lead, each through a Bitcrusher with dither and jitter (seed 12345), 8 bars
at 145 BPM. The noise pattern of the dither and jitter is new (each device its own stream); level and character stay."""
import sys, os, json, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'remake'))
from alab import AudioLab
OUT = os.path.join(HERE, 'renders'); os.makedirs(OUT, exist_ok=True)
SR = 44100
def wav(name, x):
    y = (np.clip(x.astype(np.float64).T, -1, 1) * 32767).astype('<i2')
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())
bass = [{'p': 29, 's': b * 4 + k * .25 + q, 'l': .2, 'v': .9} for b in range(8) for q in range(4) for k in (1, 2, 3)]
lead = [{'p': 65 + (b % 4) * 2, 's': b * 4, 'l': 3.5, 'v': .8} for b in range(8)]
cr = lambda bits, dith, jit, rate: [{'type': 'crush', 'p': {'bits': bits, 'dith': dith, 'jit': jit, 'rate': rate}}]
res = {}
for tag, f in (('before', sys.argv[1]), ('after', sys.argv[2])):
    al = AudioLab(f); al.start(); print(tag, 'version', al.version)
    al.run("S.seed=12345;UI.exSeed=true")
    al.build({'bpm': 145, 'seed': 12345, 'tracks': [{'name': 'B', 'preset': 'saw', 'fx': cr(6, 60, 30, 3), 'clips': [{'start': 0, 'len': 32, 'notes': bass}]},
                                                    {'name': 'L', 'preset': 'saw', 'fx': cr(5, 80, 50, 2), 'clips': [{'start': 0, 'len': 32, 'notes': lead}]}]})
    al.run("S.seed=12345")
    x, _ = al.render(b0=0, b1=32, sr=SR, tail=0.5); x = np.asarray(x)
    rms = 10 * np.log10(np.mean(x.astype(np.float64) ** 2) + 1e-30); pk = 20 * np.log10(np.abs(x).max() + 1e-30)
    res[tag] = dict(rms=round(float(rms), 3), peak=round(float(pk), 3)); print(tag, res[tag])
    wav('sndr_crush2_' + tag, x); al.stop() if hasattr(al, 'stop') else None
print(json.dumps(res))
json.dump(res, open(os.path.join(HERE, 'results_sndr_renders.json'), 'w'), indent=1)
