"""Task NI-8 (lane D): I4 mono-loss map.
Test song (audio, 120 BPM, 44.1 kHz, 32 beats):
  Pad    a 100 Hz sine in both channels (holds in mono) plus a 400 Hz sine at +1 left and -0.5 right: in its 400 Hz band mid 0.25,
         side 0.75, so mono keeps 0.0625 / 0.625 of the power: -10.0 dB
  Mono   a 1 kHz sine, the same in both channels: no loss
  Left   a 150 Hz sine on the left channel only; Right the same sine, inverted, on the right only: each loses 3 dB (one-sided), and
         together they cancel completely in mono but not in stereo, so they are joined by a line
Checks: the command, the menu entry, the Loss button next to Mono on the master strip; the per-band numbers above; the words; the pair and
only that pair; the pair goes away when Right plays another note; Hear in mono switches the master's Mono; the whole-song switch; the
range; idle does nothing; a render of Pad bit-identical before and after; NI-7's render unchanged in its normal use; screenshots
(test song, Fractals at the normal and the Light level); tooltips; no em dashes; no console errors.
  python3 tools/ui-tests/taskNI_8.py [repo dir] [out dir]"""
import sys, os, hashlib, re
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
def wait_runs(n0, timeout=300000):
    pg.wait_for_function("()=>NI.mono.runs>%d&&!NI.mono.busy&&NI.mono.res&&NI.mono.res.pairs" % n0, timeout=timeout); pg.wait_for_timeout(200)
def res():
    return R("""(()=>{const r=NI.mono.res;if(!r)return null;const B=NI.an.bands;return{b0:r.b0,b1:r.b1,how:r.how,
      tracks:r.tracks.map(x=>({name:x.name,tot:x.tot,loss:Array.from(x.loss),sig:Array.from(x.sig),worst:x.worst?{loss:x.worst.loss,fa:x.worst.fa,fb:x.worst.fb}:null,words:NI_mlWords(x).t})),
      pairs:r.pairs?{n:r.pairs.n,b0:r.pairs.b0,b1:r.pairs.b1,list:r.pairs.pairs.map(p=>({a:p.a.name,b:p.b.name,mono:p.mono,stereo:p.stereo,fa:p.fa,fb:p.fb}))}:null,bands:B}})()""")
def band_of(B, f): return int(np.argmin([abs(np.log2(b / f)) for b in B]))

ck('the command ni.monoLoss is in the commands list', R("SCM.has('ni.monoLoss')&&!!SCM.get('ni.monoLoss').l"))
ck('the main menu has "Mono loss…"', R("[...document.scripts].some(s=>s.textContent.includes(\"label:'Mono loss…'\"))"))

# Fractals, for the screenshots
if R("S.tracks.some(t=>t.name==='Kick')"):
    R("stop();pos=128;0")
    n0 = R("NI.mono.runs"); R("NI_mlOpen();0"); wait_runs(n0, 900000)
    r = res(); print('    Fractals:', [(x['name'], round(x['tot'], 1), x['words']) for x in r['tracks']], r['pairs']['list'][:4])
    ck('Fractals: rows for the tracks that play', len(r['tracks']) >= 5, len(r['tracks']))
    pg.locator('#niMono').screenshot(path=os.path.join(OUT, 'ni8_fractals.png'))
    R("UI.lite=true;UI.liteMan=true;applyLite();0"); pg.wait_for_timeout(300); pg.locator('#niMono').screenshot(path=os.path.join(OUT, 'ni8_fractals_light.png'))
    R("UI.lite=false;UI.liteMan=false;applyLite();0")
else:
    print('    (Fractals demo not loaded here; screenshots of the test song only)')
    R("document.querySelector('#niMono .fwc').click();0"); pg.wait_for_timeout(150)

# the test song
SR = 44100; nb = 32; n = nb * SR // 2; t = np.arange(n) / SR
s100 = .25 * np.sin(2 * np.pi * 100 * t); s400 = .25 * np.sin(2 * np.pi * 400 * t)
pad = np.vstack([s100 + s400, s100 - .5 * s400]).astype(np.float32)
mono = np.vstack([.2 * np.sin(2 * np.pi * 1000 * t)] * 2).astype(np.float32)
s150 = .25 * np.sin(2 * np.pi * 150 * t); z = np.zeros(n)
left = np.vstack([s150, z]).astype(np.float32); right = np.vstack([z, -s150]).astype(np.float32)
right2 = np.vstack([z, .25 * np.sin(2 * np.pi * 2500 * t)]).astype(np.float32)
B = {k: al.add_audio(v, SR) for k, v in [('Pad', pad), ('Mono', mono), ('Left', left), ('Right', right), ('R2', right2)]}
al.build({'bpm': 120, 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'clips': [{'start': 0, 'len': nb, 'name': k, 'buf': B[k]}]} for k in ['Pad', 'Mono', 'Left', 'Right']]})
R("S.loop=false;stop();pos=12;selectTrack(S.tracks.find(t=>t.name==='Pad').id);0")
x, _ = al.render(b0=0, b1=16, only='Pad'); hash0 = hashlib.md5(x.tobytes()).hexdigest()
hj0 = R("(async()=>{const t=S.tracks.find(x=>x.name==='Pad');const r=await NI_jourMeasure(t,0,16);return r.steps.map(s=>[s.rms,s.peak])})()")

n0 = R("NI.mono.runs"); R("SCM.get('ni.monoLoss').run();0"); wait_runs(n0)
r = res(); T = {x['name']: x for x in r['tracks']}; Bd = r['bands']
print('    tracks:', [(x['name'], round(x['tot'], 2), x['words']) for x in r['tracks']])
print('    pairs:', r['pairs'])
ck('every track with sound has a row', set(T) == {'Pad', 'Mono', 'Left', 'Right'}, list(T))
k4 = band_of(Bd, 400); k1 = band_of(Bd, 100)
ck('Pad: -10.0 dB in its 400 Hz band (within 0.6 dB)', abs(T['Pad']['loss'][k4] - 10.0) < .6, T['Pad']['loss'][k4])
ck('Pad: nothing lost in its 100 Hz band', T['Pad']['loss'][k1] < .6, T['Pad']['loss'][k1])
w = T['Pad']['worst']
ck('Pad: the worst stretch is around 400 Hz, -10 dB, in words', w and w['fa'] < 400 < w['fb'] and w['fb'] / w['fa'] < 2.2 and abs(w['loss'] - 10) < .8 and re.search(r'−10(\.\d)?\W?dB at \d+ to \d+\W?Hz', T['Pad']['words']), (w, T['Pad']['words']))
sigm = [l for l, s in zip(T['Mono']['loss'], T['Mono']['sig']) if s > .15]
ck('Mono: no loss in any band where it plays', max(sigm) < .6 and T['Mono']['words'] == 'holds up in mono', (max(sigm), T['Mono']['words']))
k15 = band_of(Bd, 150)
ck('Left and Right on their own: -3.0 dB each (one-sided), not flagged', abs(T['Left']['loss'][k15] - 3.0) < .6 and abs(T['Right']['loss'][k15] - 3.0) < .6 and T['Left']['words'] == 'wide, nothing cancels', (T['Left']['loss'][k15], T['Right']['loss'][k15], T['Left']['words']))
P = r['pairs']['list']
ck('exactly one pair: Left and Right', len(P) == 1 and {P[0]['a'], P[0]['b']} == {'Left', 'Right'}, P)
if P:
    ck('the pair cancels in mono around 150 Hz and not in stereo', P[0]['mono'] < -30 and P[0]['stereo'] > -1 and P[0]['fa'] < 150 < P[0]['fb'], P[0])
txt = R("document.querySelector('#niMono .nmp').textContent")
ck('the pair in words: "Left and Right cancel at … they cancel out in mono, fine in stereo"', 'Left and Right cancel at' in txt and 'cancel out in mono' in txt and 'fine in stereo' in txt, txt)
ck('a line joins Left and Right', R("document.querySelectorAll('#niMono .nmline').length") == 1 and R("(()=>{const l=document.querySelector('#niMono .nmline'),g=document.querySelector('#niMono .nmg'),j=[...g.querySelectorAll('.nmj')],y=n=>{const e=j.find(e=>e.dataset.nmj===S.tracks.find(t=>t.name===n).id);return e.offsetTop+e.offsetHeight/2};return Math.abs(l.offsetTop-Math.min(y('Left'),y('Right')))<1.5&&Math.abs(l.offsetTop+l.offsetHeight-Math.max(y('Left'),y('Right')))<1.5})()"))
ck('the range: 8 bars around the playhead (beats 0 to 32 at beat 12)', r['b0'] == 0 and r['b1'] == 32 and '8 bars' in r['how'], (r['b0'], r['b1'], r['how']))
gtxt = R("document.querySelector('#niMono .nmg').textContent")
ck('the window shows units and the words', re.search(r'−10(\.\d)?\W?dB at', gtxt) is not None and 'holds up in mono' in gtxt, gtxt[:200])
pg.locator('#niMono').screenshot(path=os.path.join(OUT, 'ni8_test.png'))
tips = R("[...document.querySelectorAll('#niMono button,#niMono label,#niMono .nmnm,#niMono .nmb,#niMono .nmh,#niMono .nmn,#niMono .nmw,#niMono .nmpr,#niMono .nmline,#niMono .nmk')].filter(e=>!e.title).map(e=>e.outerHTML.slice(0,60))")
ck('tooltips on every control, row, column and line', not tips, tips[:3])

# clicking a row selects the track
R("document.querySelector('#niMono .nmnm[data-nmt=\"'+S.tracks.find(t=>t.name==='Mono').id+'\"]').click();0")
ck('clicking a row selects its track', R("selT===S.tracks.find(t=>t.name==='Mono').id"))

# idle
pg.wait_for_timeout(1500); n1 = R("NI.mono.runs"); pg.wait_for_timeout(2000)
ck('idle 2 s: nothing measured again', R("NI.mono.runs") == n1)

# Hear in mono
m0 = R("!!UI.monoChk"); R("document.querySelector('#niMono [data-nm=\"mono\"]').click();0")
ck('Hear in mono switches the master Mono on, and the button shows it', R("!!UI.monoChk") != m0 and R("document.querySelector('#niMono [data-nm=\"mono\"]').classList.contains('on')") == R("!!UI.monoChk"))
R("document.querySelector('#niMono [data-nm=\"mono\"]').click();0")
ck('and off again', R("!!UI.monoChk") == m0)

# the Loss button on the master strip
R("openMixer();0")
pg.wait_for_timeout(400)
has = R("!!document.querySelector('#mixWin .mx.master .mxmon [data-niml]')")
ck('a Loss button next to Mono on the master strip', has, R("!!document.getElementById('mixWin')"))
if has:
    R("document.querySelector('#niMono .fwc').click();0"); pg.wait_for_timeout(150)
    n0 = R("NI.mono.runs"); R("document.querySelector('#mixWin .mx.master .mxmon [data-niml]').click();0"); wait_runs(n0)
    ck('the Loss button opens the map', R("!document.getElementById('niMono').hidden"))
    pg.locator('#mixWin .mx.master').screenshot(path=os.path.join(OUT, 'ni8_master.png'))
    R("(()=>{const w=document.getElementById('mixWin');const c=w&&w.querySelector('.fwc');if(c)c.click()})();0")

# an edit: Right plays another note: the pair goes
n0 = R("NI.mono.runs")
R("(()=>{pushUndo();const t=S.tracks.find(x=>x.name==='Right');t.mute=true;changed(true)})();0")
wait_runs(n0)
r = res()
ck('with Right muted: no pair, and Right has no row', not r['pairs']['list'] and 'Right' not in [x['name'] for x in r['tracks']], (r['pairs']['list'], [x['name'] for x in r['tracks']]))
R("(()=>{pushUndo();const t=S.tracks.find(x=>x.name==='Right');t.mute=false;changed(true)})();0")

# a second track at another note on the right: Left and R2 do not cancel
al.build({'bpm': 120, 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'clips': [{'start': 0, 'len': nb, 'name': k, 'buf': B[b]}]} for k, b in [('Pad', 'Pad'), ('Left', 'Left'), ('Right', 'R2')]]})
R("S.loop=false;stop();pos=12;0")
n0 = R("NI.mono.runs"); R("NI_mlOpen();0"); wait_runs(n0)
r = res()
ck('Right playing 2.5 kHz instead: the pair is gone', not r['pairs']['list'], r['pairs']['list'])
ck('…and the text says no tracks cancel', 'No tracks cancel each other' in R("document.querySelector('#niMono .nmp').textContent"))

# whole song and loop
n0 = R("NI.mono.runs"); R("(()=>{const c=document.querySelector('#niMono [data-nm=\"song\"]');c.checked=true;c.dispatchEvent(new Event('change'))})();0"); wait_runs(n0)
r = res(); ck('Whole song: beats 0 to 32', r['b0'] == 0 and r['b1'] == 32 and r['how'] == 'the whole song', (r['b0'], r['b1'], r['how']))
R("(()=>{const c=document.querySelector('#niMono [data-nm=\"song\"]');c.checked=false;c.dispatchEvent(new Event('change'))})();0"); wait_runs(R("NI.mono.runs") - 1)
n0 = R("NI.mono.runs"); R("S.loopRange={a:8,b:24};S.loop=true;syncTransportUI();0"); wait_runs(n0)
r = res(); ck('loop on: measures the loop (beats 8 to 24)', r['b0'] == 8 and r['b1'] == 24 and r['how'] == 'the loop', (r['b0'], r['b1'], r['how']))
R("S.loop=false;S.loopRange=null;syncTransportUI();0")
R("document.querySelector('#niMono .fwc').click();0"); pg.wait_for_timeout(200)
ck('closing stops its check', R("NI.mono.tm") == 0)

# live path, exports and NI-7 unchanged (back on the first test song)
al.build({'bpm': 120, 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'clips': [{'start': 0, 'len': nb, 'name': k, 'buf': B[k]}]} for k in ['Pad', 'Mono', 'Left', 'Right']]})
x, _ = al.render(b0=0, b1=16, only='Pad')
ck('a render of Pad is bit-identical after the map measured it', hashlib.md5(x.tobytes()).hexdigest() == hash0)
hj1 = R("(async()=>{const t=S.tracks.find(x=>x.name==='Pad');const r=await NI_jourMeasure(t,0,16);return r.steps.map(s=>[s.rms,s.peak])})()")
ck('the level journey (NI-7) measures the same as before', hj0 == hj1, (hj0, hj1))

ck('no em dashes in the new UI text', '—' not in R("(document.getElementById('niMono')||{}).textContent+String(NI_mlWords)+String(NI_mlShow)+String(NI_mlOpen)+String(NI_mlMxBtn)"))
ck('no console errors', not al.errors, al.errors[:3])
al.stop()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
