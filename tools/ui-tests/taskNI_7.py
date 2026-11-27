"""Task NI-7 (lane D): I13 level journey.
Test song (audio, 120 BPM, 44.1 kHz, 16 bars): Tone, a 1 kHz sine at 0.25 in both channels, with a Pro EQ (Output +6 dB), a switched-off
Pro EQ (Output -12 dB) and its fader at 0.5; Other, a 200 Hz sine with no devices, in a group Bus. Checks: the command and the menu entry;
the window measures the selected track: Clips -15.05 dB RMS and -12.04 dB peak, the EQ +6.0 dB, the switched-off EQ shown as off with no
change, the fader -6.0 dB, "Into Master"; the biggest rise (the EQ) and drop (the fader) marked; switching to Other re-measures (into Bus);
an edit (EQ Output +3 dB) is measured again after it settles: +3.0; the range follows the loop; nothing measured while idle; the live
path and exports unchanged (a render of Tone bit-identical before and after); a Fractals track (screenshot, normal and Light level);
tooltips; no em dashes; no console errors. Screenshots go to the out dir.
  python3 tools/ui-tests/taskNI_7.py [repo dir] [out dir]"""
import sys, os, json, hashlib, re
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
pg.set_default_timeout(600000)
print('version', al.version)
def res(): return R("(()=>{const r=NI.jour.res;return r?{id:r.id,how:r.how,b0:r.b0,b1:r.b1,steps:r.steps.map(s=>({k:s.k,name:s.name,rms:s.rms,peak:s.peak,delta:s.delta==null?null:s.delta,big:s.big||''}))}:null})()")
def wait_runs(n0, timeout=60000):
    pg.wait_for_function("()=>NI.jour.runs>%d&&!NI.jour.busy&&NI.jour.res" % n0, timeout=timeout); pg.wait_for_timeout(150)

ck('the command ni.levelJourney is in the commands list', R("SCM.has('ni.levelJourney')&&!!SCM.get('ni.levelJourney').l"))

# 0. Fractals: the Kick track, for the screenshots
R("selectTrack(S.tracks.find(t=>t.name==='Kick').id);stop();pos=64;0")
n0 = R("NI.jour.runs"); R("NI_jourOpen();0"); wait_runs(n0, 120000)
r = res(); print('    Fractals Kick:', [(s['name'], round(s['rms'], 1) if s['rms'] is not None else None) for s in r['steps']])
ck('Fractals Kick: every step measured, sound at the clip', all(s['rms'] is not None for s in r['steps'] if s['k'] != 'off') and r['steps'][0]['rms'] > -40)
pg.locator('#niJour').screenshot(path=os.path.join(OUT, 'ni7_fractals.png'))
R("UI.lite=true;UI.liteMan=true;applyLite();0"); pg.wait_for_timeout(300); pg.locator('#niJour').screenshot(path=os.path.join(OUT, 'ni7_fractals_light.png'))
R("UI.lite=false;UI.liteMan=false;applyLite();0")
R("document.querySelector('#niJour .fwc').click();0"); pg.wait_for_timeout(200)
ck('closing stops its check', R("NI.jour.tm") == 0)

# 1. the test song
SR = 44100; nb = 64; n = nb * SR // 2; t = np.arange(n) / SR
def st2(x): return np.vstack([x, x]).astype(np.float32)
bt = al.add_audio(st2(.25 * np.sin(2 * np.pi * 1000 * t)), SR); bo = al.add_audio(st2(.2 * np.sin(2 * np.pi * 200 * t)), SR)
al.build({'bpm': 120, 'tracks': [{'kind': 'audio', 'name': 'Tone', 'vol': 1.0, 'clips': [{'start': 0, 'len': 64, 'name': 'Tone', 'buf': bt}]},
                                 {'kind': 'audio', 'name': 'Other', 'vol': 1.0, 'clips': [{'start': 0, 'len': 64, 'name': 'Other', 'buf': bo}]}]})
R("""(()=>{const t=S.tracks.find(x=>x.name==='Tone');const a=mkFx('eq');a.p.out=6;const b=mkFx('eq');b.p.out=-12;b.on=false;t.fx=[a,b];t.vol=.5;t.pan=0;
  const o=S.tracks.find(x=>x.name==='Other'),g={id:rid(),name:'Bus',kind:'group',color:'#b583ff',vol:1,pan:0,fx:[],clips:[],sends:{}};S.tracks.push(g);o.grp=g.id;
  S.loop=false;changed(true);stop();pos=24;selectTrack(t.id)})();0""")
h0 = R("1") and None
x, _ = al.render(b0=16, b1=48, only='Tone'); hash0 = hashlib.md5(x.tobytes()).hexdigest()
ck('the main menu has "Level journey…"', 'act:()=>NI_jourOpen()' in R("String(document.getElementById('bLogo').oncontextmenu||'')+[...document.scripts].map(s=>s.textContent.includes(\"label:'Level journey…'\")).some(Boolean)") or R("[...document.scripts].some(s=>s.textContent.includes(\"label:'Level journey…'\"))"))
n0 = R("NI.jour.runs"); R("SCM.get('ni.levelJourney').run();0"); wait_runs(n0)
r = res(); S_ = {s['name'] + ('*' if s['k'] == 'off' else ''): s for s in r['steps']}
print('    steps:', [(s['k'], s['name'], None if s['rms'] is None else round(s['rms'], 2), None if s['delta'] is None else round(s['delta'], 2), s['big']) for s in r['steps']])
ck('the steps in order: Clips, Pro EQ, Pro EQ (off), Fader and pan, Into Master', [s['k'] for s in r['steps']] == ['src', 'fx', 'off', 'fader', 'dest'] and r['steps'][-1]['name'] == 'Into Master', [s['name'] for s in r['steps']])
s0, s1, s2, s3 = r['steps'][:4]
ck('Clips: -15.05 dB RMS and -12.04 dB peak (a 0.25 sine)', abs(s0['rms'] + 15.05) < .05 and abs(s0['peak'] + 12.04) < .05, (s0['rms'], s0['peak']))
ck('the Pro EQ with Output +6 dB: +6.0 dB', abs(s1['delta'] - 6.0) < .05, s1['delta'])
ck('the switched-off EQ: shown as off, not measured, no change', s2['rms'] is None and s2['delta'] is None)
ck('the fader at 0.5: -6.0 dB', abs(s3['delta'] + 6.02) < .05, s3['delta'])
ck('the biggest rise (the EQ) and the biggest drop (the fader) marked', s1['big'] == 'up' and s3['big'] == 'dn')
ck('Into Master: the level after the fader', abs(r['steps'][4]['rms'] - s3['rms']) < 1e-9)
ck('the range: the 8 bars around the playhead (bars 3 to 10 at beat 24)', r['b0'] == 8 and r['b1'] == 40 and '8 bars' in r['how'], (r['b0'], r['b1']))
txt = R("document.querySelector('#niJour .njg').textContent")
ck('the window shows the numbers with units and the marks', re.search(r'[−-]15\.1\W?dB', txt) is not None and '▲' in txt and '▼' in txt, txt[:160])
pg.locator('#niJour').screenshot(path=os.path.join(OUT, 'ni7_test.png'))
tips = R("[...document.querySelectorAll('#niJour button,#niJour label,#niJour .njnm,#niJour .njb,#niJour .njh')].filter(e=>!e.title).map(e=>e.outerHTML.slice(0,60))")
ck('tooltips on every control, step and column', not tips, tips[:3])

# idle
pg.wait_for_timeout(1500); n1 = R("NI.jour.runs"); pg.wait_for_timeout(2000)
ck('idle 2 s: nothing measured again', R("NI.jour.runs") == n1)

# switching tracks
n0 = R("NI.jour.runs"); R("selectTrack(S.tracks.find(x=>x.name==='Other').id);0"); wait_runs(n0)
r = res()
ck('selecting Other measures it: Clips then Fader and pan, into Bus', r['id'] == R("S.tracks.find(x=>x.name==='Other').id") and [s['k'] for s in r['steps']] == ['src', 'fader', 'dest'] and r['steps'][-1]['name'] == 'Into Bus', [s['name'] for s in r['steps']])
R("selectTrack(S.tracks.find(x=>x.name==='Bus').id);0"); pg.wait_for_timeout(600)
ck('a group: says to pick one of its tracks', 'group' in R("document.querySelector('#niJour .njst').textContent"))
n0 = R("NI.jour.runs"); R("selectTrack(S.tracks.find(x=>x.name==='Tone').id);0"); wait_runs(n0)

# an edit
n0 = R("NI.jour.runs"); R("(()=>{pushUndo();S.tracks.find(x=>x.name==='Tone').fx[0].p.out=3;changed(false)})();0")
pg.wait_for_timeout(400); ck('right after an edit: not measured yet (waits for it to settle)', R("NI.jour.runs") == n0)
wait_runs(n0); r = res()
ck('after the edit: the EQ +3.0 dB', abs(r['steps'][1]['delta'] - 3.0) < .05, r['steps'][1]['delta'])

# the loop
n0 = R("NI.jour.runs"); R("S.loopRange={a:32,b:48};S.loop=true;syncTransportUI();0"); wait_runs(n0)
r = res(); ck('loop on: measures the loop (beats 32 to 48)', r['b0'] == 32 and r['b1'] == 48 and r['how'] == 'the loop', (r['b0'], r['b1'], r['how']))
R("S.loop=false;S.loopRange=null;syncTransportUI();0")

# follow off
R("(()=>{const c=document.querySelector('#niJour [data-nj=\"follow\"]');c.checked=false;c.dispatchEvent(new Event('change'))})();0")
n1 = R("NI.jour.runs"); R("selectTrack(S.tracks.find(x=>x.name==='Other').id);0"); pg.wait_for_timeout(1500)
ck('follow off: selecting another track keeps the journey on Tone', R("NI.jour.tid") == R("S.tracks.find(x=>x.name==='Tone').id"))

# live path and exports
R("S.tracks.find(x=>x.name==='Tone').fx[0].p.out=6;0")
x, _ = al.render(b0=16, b1=48, only='Tone')
ck('a render of Tone is bit-identical after the journey measured it', hashlib.md5(x.tobytes()).hexdigest() == hash0)
ck('no em dashes in the new UI text', '—' not in R("document.getElementById('niJour').textContent+String(NI_jourSteps)+String(NI_jourRun)+String(NI_jourShow)"))
R("document.querySelector('#niJour .fwc').click();0")
ck('no console errors', not al.errors, al.errors[:3])
al.stop()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
