"""Task SND-1 (lane L): A/B renders for listening, through the app's own render, written to tools/engine-lab/snd/renders/ (44.1 kHz, 16 bit,
peaks at -6 dBFS so the pairs compare by sound, not level).
  python3 tools/engine-lab/snd/snd1_renders.py [index.html]
- snd1_afilt_<preset>_classic / _clean: the Auto Filter's own presets on a saw bass line (F1, K-B-B-B at 145 BPM, 8 bars), Classic
  (the biquads, as every saved song) against Clean (the new models at 2x);
- snd1_filter2_<preset>: Filter v2's presets on the same line."""
import sys, os, json, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'remake'))
from alab import AudioLab
IDX = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = os.path.join(HERE, 'renders'); os.makedirs(OUT, exist_ok=True)
SR = 44100
al = AudioLab(IDX); al.start(); print('version', al.version)
def wav(name, x):
    x = x.astype(np.float64); pk = np.abs(x).max()
    if pk > 0: x = x / pk * 10 ** (-6 / 20)
    y = (np.clip(x.T, -1, 1) * 32767).astype('<i2')
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())
    print('wrote', name)
notes = []
for bar in range(8):
    for beat in range(4):
        for k in (1, 2, 3): notes.append({'p': 29, 's': bar * 4 + beat + k * .25, 'l': .2, 'v': .9 if k == 1 else .75})
def line(fx, b1=32):
    al.build({'bpm': 145, 'tracks': [{'name': 'B', 'preset': 'saw', 'fx': fx, 'clips': [{'start': 0, 'len': 32, 'notes': notes}]}]})
    x, _ = al.render(b0=0, b1=b1, sr=SR, tail=0.5); return x
pres = json.loads(al.run("JSON.stringify(Object.fromEntries(Object.entries(FXPRE.afilt).map(([k,v])=>[k,v[1]])))"))
for k in ('acid', 'wobble', 'lpslow', 'talkb', 'rolling'):
    p = dict(pres[k]); p.pop('pre', None)
    for q in ('classic', 'clean'):
        p['q'] = q; wav('snd1_afilt_%s_%s' % (k, q), line([{'type': 'afilt', 'p': dict(p)}]))
pf = json.loads(al.run("JSON.stringify(Object.fromEntries(Object.entries(FXPRE.filter2).map(([k,v])=>[k,v[1]])))"))
for k in ('warm', 'acid', 'ms20', 'butter', 'comb', 'vowo'):
    p = dict(pf[k]); p.pop('pre', None); wav('snd1_filter2_%s' % k, line([{'type': 'filter2', 'p': p}]))
al.stop()
