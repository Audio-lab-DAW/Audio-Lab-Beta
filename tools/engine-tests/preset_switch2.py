"""Preset switch on every instrument, measured against a reference (task AA): python3 tools/engine-tests/preset_switch2.py [index.html] [case,...] [only,...]

Two tracks play the same notes: A starts on preset k0 and is switched to k1 through its preset menu (a change event, as a click or a key gives),
B plays k1 all along. Both are recorded on the audio thread (after the fader) with a marker at the moment of the click.
 new sound  ms from the click until A sounds like B (band levels within the threshold, and staying there for 100 ms). The threshold is
            what A and B differ by 0.6 to 1.0 s after the switch (they never match to the sample: free phases), plus 2 dB.
 glitch     high-frequency energy (first difference) of A against B in the 30 ms after the click, in dB over what it is 0.3 to 0.6 s later:
            a click or a hard cut shows here.
 over/dip   the loudest 10 ms of A against B in the 30 to 300 ms after the click (over: two sounds at once or a level jump; dip: a hole or
            an envelope that starts again).
 handler    ms the page spent in the change event (the picture is drawn after it).
Cases: held (one long note while playing), pattern (sixteenth notes while playing), keys (a key held while stopped, through voiceOn).
"""
import sys, os, json, base64
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preset_switch import JS_HELP

INDEX = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
CASES = sys.argv[2].split(',') if len(sys.argv) > 2 and sys.argv[2] else ['held', 'pattern', 'keys']
ONLY = sys.argv[3].split(',') if len(sys.argv) > 3 and sys.argv[3] else None
PITCH = {'sub': 36, 'bass': 36, 'reese': 36, 'acid': 45, 'sbass': 33, 'psyb': 33, 'crk': 45, 'growl': 40, 'drums': 36, 'kick': 36, 'venom': 48}

PRE = r"""(I=>{const D=fxin.querySelector('.dev[data-d=inst]');if(!D)return null;return D.querySelector('select[data-s=ipre],select[data-vnp],select[data-s=kpre]')})"""
JS_SW = r"""window.__sw=function(t,val,mark){selT=t.id;renderFx();const s=(%s)(t.inst);if(!s)return 'no menu';const o=[...s.options].map(o=>o.value);
  if(val==null){const i=o.indexOf(s.value);val=o[(i+1)%%o.length]}const k0=s.value;s.value=val;if(mark)window.__mark(t);const q=performance.now();s.dispatchEvent(new Event('change',{bubbles:true}));
  return JSON.stringify([k0,val,performance.now()-q])};1""" % PRE


def bands(x, sr):
    n, hop = 1024, int(sr * .005)
    w = np.hanning(n)
    f = np.fft.rfftfreq(n, 1 / sr)
    edges = np.geomspace(60, 16000, 33)
    idx = [(np.searchsorted(f, edges[i]), max(np.searchsorted(f, edges[i + 1]), np.searchsorted(f, edges[i]) + 1)) for i in range(32)]
    fr = []
    for s in range(0, len(x) - n, hop):
        S = np.abs(np.fft.rfft(x[s:s + n] * w)) ** 2
        fr.append([10 * np.log10(S[a:b].sum() + 1e-12) for a, b in idx])
    return np.array(fr), hop


def dist(FA, FB):
    m = np.maximum(FA, FB)
    top = m.max(axis=1, keepdims=True)
    use = m > top - 45
    d = np.abs(FA - FB) * use
    return d.sum(axis=1) / np.maximum(use.sum(axis=1), 1)


def measure(xa, xb, i, sr):
    L = min(len(xa), len(xb))
    xa, xb = xa[:L], xb[:L]
    s0 = max(0, i - int(.3 * sr))
    FA, hop = bands(xa[s0:], sr)
    FB, _ = bands(xb[s0:], sr)
    D = dist(FA, FB)
    k0 = (i - s0) // hop  # frame index of the click
    late = D[k0 + int(.6 / .005):k0 + int(1.0 / .005)]
    thr = (np.median(late) if len(late) else 3) + 2
    need = int(.1 / .005)
    t_new = None
    for k in range(k0, len(D) - need):
        if (D[k:k + need] < thr).all():
            t_new = (k - k0) * 5 + 1024 / sr * 1000 / 2  # centre of the frame
            break
    hp = lambda a: np.diff(a) ** 2
    ga, gb = hp(xa[i:i + int(.03 * sr)]).sum(), hp(xb[i:i + int(.03 * sr)]).sum()
    ra, rb = hp(xa[i + int(.3 * sr):i + int(.6 * sr)]).sum() / 10, hp(xb[i + int(.3 * sr):i + int(.6 * sr)]).sum() / 10
    glitch = 10 * np.log10((ga / max(ra, 1e-12)) / max(gb / max(rb, 1e-12), 1e-6)) if ra > 1e-10 and rb > 1e-10 and gb > 1e-12 else 0.0
    w = int(.01 * sr)
    seg = lambda a, s: np.sqrt(np.mean(a[s:s + w] ** 2) + 1e-12)
    rel = [20 * np.log10(seg(xa, s) / seg(xb, s)) for s in range(i + int(.03 * sr), i + int(.3 * sr), w) if seg(xb, s) > 1e-4 or seg(xa, s) > 1e-4]
    over = max(rel) if rel else 0
    dip = min(rel) if rel else 0
    lvl = 20 * np.log10(np.sqrt(np.mean(xb[i:i + int(.5 * sr)] ** 2)) + 1e-9)
    return t_new, glitch, over, dip, thr, lvl


def pull(al, tid):
    d = json.loads(al.run("window.__pull(%s)" % json.dumps(tid)))
    x = np.frombuffer(base64.b64decode(d['x']), dtype=np.float32)
    m = np.frombuffer(base64.b64decode(d['m']), dtype=np.float32)
    return x, (int(np.argmax(m > .5)) if (m > .5).any() else -1), d['sr']


al = AudioLab(INDEX, 1600, 1000); al.start()
W = al.page.wait_for_timeout
al.build({'tracks': [{'name': 'x', 'preset': 'pluck'}]})
insts = json.loads(al.run("JSON.stringify(Object.keys(PRESETS).filter(k=>!PRESETS[k].hide))"))
if ONLY: insts = [k for k in insts if k in ONLY]
rows = []
for case in CASES:
    print('\n== %s ==' % {'held': 'one long note, playing', 'pattern': 'sixteenth notes, playing', 'keys': 'a key held, stopped'}[case])
    print('%-8s | %-26s | new sound | glitch | over / dip (dB) | handler | ref level' % ('inst', 'switch'))
    for k in insts:
        p = PITCH.get(k, 60)
        notes = [{'p': p, 's': 0, 'l': 60, 'v': .8}] if case == 'held' else [{'p': p, 's': j * .25, 'l': .2, 'v': .8} for j in range(240)] if case == 'pattern' else []
        al.build({'bpm': 120, 'tracks': [{'name': 'A', 'preset': k, 'clips': [{'start': 0, 'len': 64, 'notes': notes}]}, {'name': 'B', 'preset': k, 'clips': [{'start': 0, 'len': 64, 'notes': notes}]}]})
        al.run("UI.countIn=false;S.loop=false;S.click=false;1"); al.run(JS_HELP); al.run(JS_SW)
        # B gets the next preset before anything plays; A keeps the first
        r = al.run("(()=>{const[A,B]=S.tracks;return window.__sw(B,null,0)})()")
        if r == 'no menu': print('%-8s | no preset menu' % k); continue
        k0, k1, _ = json.loads(r)
        al.run("(()=>{const[A,B]=S.tracks;selT=A.id;renderFx();return 1})()"); W(400)
        if case == 'keys':
            al.run("(()=>{ensureCtx();ctx.resume();for(const t of S.tracks)window.__rec(t);window.__keys=S.tracks.map(t=>voiceOn(t,%d,.8));return 1})()" % p)
            W(1200)
        else:
            al.run("(()=>{for(const t of S.tracks)window.__rec(t);pos=0;start();return 1})()"); W(1500)
        k0b, k1b, hms = json.loads(al.run("(()=>{const[A,B]=S.tracks;return window.__sw(A,%s,1)})()" % json.dumps(k1)))
        W(1400)
        al.run("(()=>{if(play.on)stop();if(window.__keys){for(const h of window.__keys)try{h&&h.off()}catch(e){}window.__keys=null}return 1})()")
        ids = [al.tracks['A'], al.tracks['B']]
        xa, ia, sr = pull(al, ids[0]); xb, ib, _ = pull(al, ids[1])
        if ia < 0: print('%-8s | no marker' % k); continue
        # B has no marker of its own: the two recorders started in the same call, so the same sample index is the same moment
        t_new, gl, ov, dp, thr, lvl = measure(xa, xb, ia, sr)
        rows.append((case, k, k0b, k1b, None if t_new is None else float(t_new), float(gl), float(ov), float(dp), float(hms), float(lvl)))
        if os.environ.get('SAVE'): np.savez(os.path.join(os.environ['SAVE'], '%s_%s.npz' % (case, k)), a=xa, b=xb, i=ia, sr=sr)
        print('%-8s | %-26s | %9s | %5.1f  | %+5.1f / %+5.1f    | %5.1f ms | %6.1f dB%s' % (k, ('%s > %s' % (k0b, k1b))[:26], ('%.0f ms' % t_new) if t_new is not None else 'never', gl, ov, dp, hms, lvl,
              '  silent ref' if lvl < -70 else ''), flush=True)
print('\nerrors', al.errors[:3])
json.dump(rows, open(os.environ.get('OUT', 'preset_switch2.json'), 'w'))
al.stop()
