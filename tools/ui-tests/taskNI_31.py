"""Task NI-31 (lane D): X18 high-pass hints with a one-click cut.
Test song (120 BPM, 44.1 kHz, 32 beats):
  Pad    audio: a 440 Hz sine plus a 50 Hz rumble 15 dB under it: 3.1 % of its level under 150 Hz: a hint "Cut under 150 Hz"
  Clean  audio: a 1 kHz sine: no hint
  Bass   audio: a 55 Hz sine, named Bass: never a hint (skipped, low end is its job)
  Loop   audio: an 80 Hz sine as loud as its 1 kHz: 50 % under the line: skipped as probably needed
  Keys   notes C4 to C5 on the saw synth: its line is 0.6 x 261.6 Hz = 155 Hz; a saw has nothing under its note: no hint
Checks: command, menu entry, the hints and their numbers, the words, the skipped list; the cut: one undo step, a Pro EQ first in the chain
with a 12 dB/oct high-pass at 150 Hz, the 50 Hz rumble down by 15 dB or more, the 440 Hz tone within 0.6 dB; the hint goes after the
cut; a second cut does nothing; Undo restores a bit-identical render; an existing Pro EQ is reused; idle does nothing; tooltips;
no em dashes; no console errors; screenshots (test song; Fractals).
  python3 tools/ui-tests/taskNI_31.py [repo dir] [out dir]"""
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
pg.set_default_timeout(900000)
print('version', al.version)
ck('the command ni.hpHints is in the commands list', R("SCM.has('ni.hpHints')&&!!SCM.get('ni.hpHints').l"))
ck('the main menu has "High-pass hints…"', R("[...document.scripts].some(s=>s.textContent.includes(\"label:'High-pass hints…'\"))"))
def wait_runs(n0):
    pg.wait_for_function("()=>NI.hp.runs>%d&&!NI.hp.busy&&NI.hp.res" % n0, timeout=900000); pg.wait_for_timeout(200)
def res():
    return json.loads(R("JSON.stringify({h:NI.hp.res.hints.map(h=>({name:h.name,cut:h.cut,share:h.share,why:h.why})),s:NI.hp.res.skipped})"))

# Fractals first (the demo opens with it), for a look and a screenshot
if R("S.tracks.some(t=>t.name==='Kick')"):
    n0 = R("NI.hp.runs"); R("NI_hpOpen();0"); wait_runs(n0); r = res()
    print('    Fractals hints:', [(h['name'], h['cut'], round(h['share'] * 100, 2)) for h in r['h']], 'skipped:', [s['name'] for s in r['s']])
    ck('Fractals: kick and bass are never hinted', not any(h['name'] in ('Kick', 'Bass') for h in r['h']))
    pg.locator('#niHp').screenshot(path=os.path.join(OUT, 'ni31_fractals.png'))
    R("NI_hpClose();0")

SR = 44100; nb = 32; n = nb * SR // 2; t = np.arange(n) / SR
s = lambda f, a: a * np.sin(2 * np.pi * f * t)
pad = s(440, .3) + s(50, .3 * 10 ** (-15 / 20)); clean = s(1000, .25); bass = s(55, .3); loop = s(80, .2) + s(1000, .2)
B = {k: al.add_audio(np.vstack([v, v]).astype(np.float32), SR) for k, v in [('Pad', pad), ('Clean', clean), ('Bass', bass), ('Loop', loop)]}
notes = [{'p': 60 + (i % 13), 's': i, 'l': .9, 'v': .8} for i in range(nb)]
def song():
    al.build({'bpm': 120, 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'clips': [{'start': 0, 'len': nb, 'name': k, 'buf': B[k]}]} for k in ['Pad', 'Clean', 'Bass', 'Loop']]
              + [{'name': 'Keys', 'preset': 'saw', 'clips': [{'start': 0, 'len': nb, 'notes': notes}]}]})
    R("S.loop=false;stop();pos=0;0")
song()
x0, _ = al.render(b0=0, b1=16, only='Pad'); h0 = hashlib.md5(x0.tobytes()).hexdigest()
n0 = R("NI.hp.runs"); R("SCM.get('ni.hpHints').run();0"); wait_runs(n0); r = res()
print('    hints:', r['h']); print('    skipped:', r['s'])
H = {h['name']: h for h in r['h']}; SK = {x['name']: x['why'] for x in r['s']}
ck('exactly one hint: Pad', list(H) == ['Pad'], list(H))
if 'Pad' in H:
    ck('Pad: cut under 150 Hz, about 3.1 % of its level there (within 0.6 %)', H['Pad']['cut'] == 150 and abs(H['Pad']['share'] - .0307) < .006, H['Pad'])
ck('Bass skipped as a low-end track, Loop skipped as probably needed', SK.get('Bass') == 'a bass' and 'probably needed' in SK.get('Loop', ''), SK)
ck('Clean and Keys: no hint and not skipped (nothing under their lines)', 'Clean' not in H and 'Keys' not in H and 'Clean' not in SK and 'Keys' not in SK)
ck('Keys\' line is 0.6 x its lowest note: 157 Hz', R("Math.round(NI_hpLine(S.tracks.find(t=>t.name==='Keys')).hz)") == 157, R("NI_hpLine(S.tracks.find(t=>t.name==='Keys')).hz"))
txt = R("document.querySelector('#niHp .nhg').textContent")
pct = R("NI_hpPct(NI.hp.res.hints[0].share)") if H else ''
ck('the words: "%s under 150 Hz, a usual line…" and the button "Cut under 150 Hz"' % pct, (pct + ' under 150 Hz, a usual line') in txt and 'Cut under 150 Hz' in txt, txt[:160])
ck('the skipped list is shown', 'Not checked: ' in R("document.querySelector('#niHp .nhs').textContent") and 'Bass' in R("document.querySelector('#niHp .nhs').textContent"))
pg.locator('#niHp').screenshot(path=os.path.join(OUT, 'ni31_test.png'))
R("UI.lite=true;UI.liteMan=true;applyLite();0"); pg.wait_for_timeout(300); pg.locator('#niHp').screenshot(path=os.path.join(OUT, 'ni31_light.png')); R("UI.lite=false;UI.liteMan=false;applyLite();0")
tips = R("[...document.querySelectorAll('#niHp button,#niHp .nhnm,#niHp .nhw,#niHp .nhs,#niHp .nht span')].filter(e=>!e.title&&!e.closest('[title]')).map(e=>e.outerHTML.slice(0,60))")
ck('tooltips on every control and row', not tips, tips[:3])

# idle
pg.wait_for_timeout(1500); r1 = R("NI.hp.runs"); pg.wait_for_timeout(2000)
ck('idle 2 s: nothing measured again', R("NI.hp.runs") == r1)

# the cut
u0 = R("UNDO.length"); n0 = R("NI.hp.runs")
R("document.querySelector('#niHp [data-nhc]').click();0")
f = json.loads(R("JSON.stringify((()=>{const t=S.tracks.find(t=>t.name==='Pad');const e=t.fx[0];const b=e&&e.type==='eq'&&e.p.bands.find(q=>q.t==='highpass');return{n:t.fx.length,type:e&&e.type,b}})())"))
ck('one undo step', R("UNDO.length") == u0 + 1, (u0, R("UNDO.length")))
ck('a Pro EQ first in Pad\'s chain with a 12 dB/oct high-pass at 150 Hz', f['type'] == 'eq' and f['b'] and f['b']['on'] and f['b']['f'] == 150 and f['b']['sl'] == 12 and f['b']['q'] == .3, f)
x1, _ = al.render(b0=0, b1=16, only='Pad')
def lev(x, fr):
    m = (x[0].astype(np.float64) + x[1]) / 2; m = m[SR:]; w = np.hanning(len(m)); X = np.abs(np.fft.rfft(m * w)); fq = np.fft.rfftfreq(len(m), 1 / SR); k = np.argmin(abs(fq - fr))
    return 20 * np.log10(X[k - 3:k + 4].max() + 1e-12)
d50 = lev(x1, 50) - lev(x0, 50); d440 = lev(x1, 440) - lev(x0, 440)
print('    after the cut: 50 Hz %.2f dB, 440 Hz %.2f dB' % (d50, d440))
ck('the 50 Hz rumble is 15 dB or more lower', d50 <= -15, d50)
ck('the 440 Hz tone changes by under 0.6 dB (the Pro EQ high-pass rises a little above its corner, at its lowest Q)', abs(d440) < .6, d440)
wait_runs(n0); r = res()
ck('after the cut the hint is gone', not any(h['name'] == 'Pad' for h in r['h']), r['h'])
u1 = R("UNDO.length"); R("NI_hpCut(S.tracks.find(t=>t.name==='Pad').id,150);0")
ck('a second cut at the same line does nothing (no undo step)', R("UNDO.length") == u1 and R("S.tracks.find(t=>t.name==='Pad').fx.length") == f['n'])
R("undo();0"); pg.wait_for_timeout(300)
x2, _ = al.render(b0=0, b1=16, only='Pad')
ck('Undo takes the cut back: the render is bit-identical to before', hashlib.md5(x2.tobytes()).hexdigest() == h0 and R("S.tracks.find(t=>t.name==='Pad').fx.length") == 0)

# an existing Pro EQ is reused (its high-pass band switched on), not a second one added
R("(()=>{pushUndo();const t=S.tracks.find(t=>t.name==='Clean');t.fx.push(mkFx('eq'));changed(true)})();0")
R("NI_hpCut(S.tracks.find(t=>t.name==='Clean').id,120);0")
e = json.loads(R("JSON.stringify(S.tracks.find(t=>t.name==='Clean').fx.map(f=>[f.type,(f.p.bands||[]).filter(b=>b.t==='highpass').map(b=>[b.on,b.f])]))"))
ck('an existing Pro EQ is reused', e == [['eq', [[True, 120]]]], e)
R("document.querySelector('#niHp .fwc').click();0"); pg.wait_for_timeout(200)
ck('closing stops its check', R("NI.hp.tm") == 0)
ck('no em dashes in the new UI text', '—' not in R("String(NI_hpShow)+String(NI_hpOpen)+String(NI_hpCut)+String(NI_hpLine)+String(NI_hpSkip)"))
ck('no console errors', not al.errors, al.errors[:3])
al.stop()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
