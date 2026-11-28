"""Task NI-9 (lane D): I5 harmonic ruler.
Test song (audio, 120 BPM, 44.1 kHz) through a Spectrum device (FFT 8192):
  Tones  a 110 Hz sine (A2), 440 Hz (A4), 1244.5 Hz (D#6) and 3300 Hz (G#7 -12 c), steady
  Ring   every 4 beats: a 60 ms noise burst with a 200 Hz tone that starts with it and decays slowly (time constant 2 s, about 2 dB a beat), so the tone keeps
         ringing for more than a beat after the noise is gone
Checks: the command, the menu entry, the settings row; A2 named "A2 0 c" and the others with their cents; in A minor the D#6 and G#7
peaks are amber and A2/A4 are not; steady tones are not red; the ringing tone is red with "rings", and only after a beat; the switch
off draws nothing and on again draws; stopped: nothing found again (idle); the Visualizer gets the ruler too; Light level; the hook
draws into any canvas; a render is bit-identical with the ruler on and off; tooltips (menu); no em dashes; no console errors; screenshots.
  python3 tools/ui-tests/taskNI_9.py [repo dir] [out dir]"""
import sys, os, hashlib, json
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
al = AudioLab(os.path.join(ROOT, 'index.html')); al.start(); pg = al.page; R = al.run
print('version', al.version)
AMBER, RED, INK = '#ffb547', '#ff6b6b', '#ececf1'

ck('the command ni.harmonicRuler is in the commands list', R("SCM.has('ni.harmonicRuler')&&!!SCM.get('ni.harmonicRuler').l"))
ck('the main menu has "Harmonic ruler: on"', R("[...document.scripts].some(s=>s.textContent.includes(\"label:NI_hrOn()?'Harmonic ruler: on':'Harmonic ruler: off'\"))"))
ck('a settings row ni.harmonicRuler (S4 shape, on by default)', R("NI_SETTINGS.some(r=>r.id==='ni.harmonicRuler'&&r.key==='niHr'&&r.default===true&&r.help&&r.label)"))
ck('lane E\'s drawer is wrapped once, its own function kept', R("NI.hr.wrapped&&typeof INS.spec.niBase==='function'&&!String(INS.spec.niBase).includes('NI_hr')"))

SR = 44100; nb = 32; n = nb * SR // 2; t = np.arange(n) / SR
tones = .3 * np.sin(2 * np.pi * 110 * t) + .1 * np.sin(2 * np.pi * 440 * t) + .05 * np.sin(2 * np.pi * 1244.51 * t) + .05 * np.sin(2 * np.pi * 3300 * t)
rng = np.random.default_rng(7); ring = np.zeros(n)
for b in range(0, nb, 4):
    i0 = b * SR // 2; m = min(n - i0, 4 * SR // 2); tt = np.arange(m) / SR
    burst = rng.standard_normal(m) * .5 * (tt < .06)
    ring[i0:i0 + m] += burst + .3 * np.sin(2 * np.pi * 200 * tt) * np.exp(-tt / 2.0)
BT = al.add_audio(np.vstack([tones, tones]).astype(np.float32), SR)
BR = al.add_audio(np.vstack([ring, ring]).astype(np.float32), SR)
SPEC = {'type': 'spec', 'p': {'fft': '8192'}}
def song(buf):
    al.build({'bpm': 120, 'tracks': [{'kind': 'audio', 'name': 'T', 'vol': 1.0, 'clips': [{'start': 0, 'len': nb, 'name': 'T', 'buf': buf}], 'fx': [SPEC]}]})
    R("PR.root=9;PR.scale='minor';NI.hr.kt=0;selectTrack(S.tracks[0].id);S.loop=false;stop();pos=0;0")
def peaks():
    return json.loads(R("(()=>{const X=vizInst(S.tracks[0].fx[0]);const H=X&&X.sp&&X.sp.niHr;return JSON.stringify(H?H.pk.map(q=>({txt:q.note.txt,hz:q.hz,c:q.note.c,out:q.out,ring:q.ring,beats:q.beats})):[])})()"))
dev = lambda: pg.locator('.dev[data-id="' + R('S.tracks[0].fx[0].id') + '"]').first

# 1. steady tones
song(BT); x0, _ = al.render(b0=0, b1=8); h_on = hashlib.md5(x0.tobytes()).hexdigest()
R("toggle();0"); pg.wait_for_timeout(2500)
P = peaks(); print('    peaks:', [(p['txt'], round(p['hz'], 2), p['out'], p['ring']) for p in P])
T = {p['txt'].split(' ')[0]: p for p in P}
ck('110 Hz is named "A2 0 c"', 'A2' in T and T['A2']['txt'] == 'A2 0 c', T.get('A2'))
ck('110 Hz measured within 0.05 Hz', 'A2' in T and abs(T['A2']['hz'] - 110) < .05, T.get('A2', {}).get('hz'))
ck('440 Hz "A4 0 c", 1244.5 Hz "D♯6 0 c", 3300 Hz "G♯7 −12 c"', T.get('A4', {}).get('txt') == 'A4 0 c' and T.get('D♯6', {}).get('txt') == 'D♯6 0 c' and T.get('G♯7', {}).get('txt') == 'G♯7 −12 c', [p['txt'] for p in P])
ck('four peaks, no false ones', len(P) == 4, len(P))
ck('A minor: D♯6 and G♯7 outside the key, A2 and A4 inside', T.get('D♯6', {}).get('out') and T.get('G♯7', {}).get('out') and not T.get('A2', {}).get('out') and not T.get('A4', {}).get('out'))
ck('steady tones are not called ringing', not any(p['ring'] for p in P))
L = json.loads(R("JSON.stringify(NI.hr.last||[])"))
cols = {l['t']: l['c'] for l in L}
ck('drawn colours: amber for D♯6 and G♯7, ink for A2 and A4', cols.get('D♯6 0 c') == AMBER and cols.get('G♯7 −12 c') == AMBER and cols.get('A2 0 c') == INK and cols.get('A4 0 c') == INK, cols)
dev().screenshot(path=os.path.join(OUT, 'ni9_tones.png'))
R("PR.scale='none';NI.hr.kt=0;0"); pg.wait_for_timeout(600)
ck('no scale set: nothing amber', not any(p['out'] for p in peaks()))
R("PR.scale='minor';NI.hr.kt=0;0")

# 2. the switch
R("SCM.get('ni.harmonicRuler').run();0"); d0 = R("NI.hr.draws"); r0 = R("NI.hr.runs"); pg.wait_for_timeout(800)
ck('off: the ruler draws nothing and finds nothing while the view plays', R("UI.niHr===false") and R("NI.hr.draws") == d0 and R("NI.hr.runs") == r0, (d0, R("NI.hr.draws")))
dev().screenshot(path=os.path.join(OUT, 'ni9_off.png'))
R("SCM.get('ni.harmonicRuler').run();0"); d0 = R("NI.hr.draws"); pg.wait_for_timeout(800)
ck('on again: it draws', R("UI.niHr===true") and R("NI.hr.draws") > d0)
r0 = R("NI.hr.runs"); pg.wait_for_timeout(1000); r1 = R("NI.hr.runs")
ck('peaks found at most 8 times a second per view', 0 < r1 - r0 <= 9, r1 - r0)

# 3. the Light level
R("UI.lite=true;UI.liteMan=true;applyLite();0"); pg.wait_for_timeout(400); r0 = R("NI.hr.runs"); pg.wait_for_timeout(1000); r1 = R("NI.hr.runs")
ck('Light level: at most 3 times a second', 0 < r1 - r0 <= 4, r1 - r0)
dev().screenshot(path=os.path.join(OUT, 'ni9_light.png'))
R("UI.lite=false;UI.liteMan=false;applyLite();0")

# 4. the Visualizer (its spectrum mode, docked at the bottom)
R("UI.viz=true;UI.vizMode='fft';UI.vizDock='bottom';UI.vizH=260;vizApply();0"); pg.wait_for_timeout(1500)
nv = R("VZ.ins&&VZ.ins.niHr?VZ.ins.niHr.pk.map(q=>q.note.txt):null")
print('    Visualizer:', nv)
ck('the Visualizer\'s spectrum (FFT 4096, smoothed) gets the ruler too: A2 within 2 c', nv is not None and any(v in nv for v in ('A2 0 c', 'A2 +1 c', 'A2 −1 c', 'A2 +2 c', 'A2 −2 c')), nv)
try: pg.locator('#vizp').screenshot(path=os.path.join(OUT, 'ni9_viz.png'))
except Exception as e: print('   (shot)', e)
R("UI.viz=false;vizApply();0"); pg.wait_for_timeout(300)

# 5. idle: stopped, nothing is found again
R("stop();0"); pg.wait_for_timeout(1200); r0 = R("NI.hr.runs"); pg.wait_for_timeout(2000)
print('    stopped: runs %d -> %d' % (r0, R("NI.hr.runs")))
ck('stopped: no peaks on the ruler, at most a cheap empty look 8 times a second', len(peaks()) == 0 and R("NI.hr.runs") - r0 <= 17, R("NI.hr.runs") - r0)

# 6. a ringing tone
song(BR); R("toggle();0")
seen = {'early_red': False, 'red': False, 'red_txt': ''}
for i in range(40):
    pg.wait_for_timeout(100)
    for p in peaks():
        if abs(p['hz'] - 200) < 3:
            if p['ring'] and p['beats'] <= 1: seen['early_red'] = True
            if p['ring']: seen['red'] = True
    L = json.loads(R("JSON.stringify(NI.hr.last||[])"))
    for l in L:
        if l['c'] == RED: seen['red_txt'] = l['t']
    if seen['red'] and i > 25: break
print('    ringing:', seen, [(p['txt'], round(p['beats'], 2), p['ring']) for p in peaks()])
ck('the 200 Hz tone that keeps ringing after the noise is red', seen['red'])
ck('…and named with "rings" (G3 +35 c rings)', seen['red_txt'].endswith(' rings') and seen['red_txt'].startswith('G3 +35 c'), seen['red_txt'])
ck('not red before a beat has passed', not seen['early_red'])
dev().screenshot(path=os.path.join(OUT, 'ni9_ring.png'))
R("stop();0")

# 7. the hook into any canvas
r = R("""(()=>{const c=document.createElement('canvas');c.width=400;c.height=60;const g=c.getContext('2d');
  const k=NI_HOOKS.harmonicRuler(g,{x:0,y:40,w:400,h:12,lo:20,hi:20000},[{hz:110,db:-20,note:NI_hrNote(110),out:false,ring:false}],{size:'full'});
  const d=g.getImageData(0,0,400,60).data;let on=0;for(let i=3;i<d.length;i+=4)if(d[i])on++;return[k,on>500]})()""")
ck('NI_HOOKS.harmonicRuler draws a ruler with one peak into any canvas', r == [1, True], r)
ck('NI_hrNote: 220 Hz "A3 0 c", 261.63 Hz "C4 0 c", 116 Hz "A♯2 −8 c"', R("NI_hrNote(220).txt==='A3 0 c'&&NI_hrNote(261.63).txt==='C4 0 c'&&NI_hrNote(116).txt==='A♯2 −8 c'"), R("[NI_hrNote(220).txt,NI_hrNote(261.63).txt,NI_hrNote(116).txt]"))

# 8. the sound: a render with the ruler off is the same as with it on
song(BT); R("UI.niHr=false;0"); x1, _ = al.render(b0=0, b1=8); R("UI.niHr=true;0")
ck('a render is bit-identical with the ruler on and off', hashlib.md5(x1.tobytes()).hexdigest() == h_on)
ck('no em dashes in the new UI text', '—' not in R("String(NI_hrShow)+String(NI_hrDraw)+NI_SETTINGS.filter(r=>r.id==='ni.harmonicRuler').map(r=>r.label+r.help).join('')+SCM.get('ni.harmonicRuler').l"))
ck('the menu entry has a line under it (its tooltip)', R("[...document.scripts].some(s=>s.textContent.includes(\"sub:'note names of the strongest peaks under every spectrum view'\"))"))
ck('no console errors', not al.errors, al.errors[:3])
al.stop()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
