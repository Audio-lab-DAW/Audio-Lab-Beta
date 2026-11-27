"""Task NI-5c (lane D): X16, the clash measure that knows the beat.
Test song (audio tracks, 145 BPM, 44.1 kHz, 16 beats):
  Kick   a 55 Hz sine on every beat, 110 ms with a fast decay (70 ms) (kick on the quarter)
  Bass   a 55 Hz sine on the three 16ths after each kick (KBBB), 85 ms each: the same band, taking turns with the kick
  Pad    a 400 Hz sine all through; Lead a 410 Hz sine all through, 2 dB quieter (the same band, together all the time)
Checks: the per-beat average (NI-5a before the timing) flags Kick and Bass and Pad and Lead; with the timing, Kick and Bass "take turns"
(a share under 25 %), Pad and Lead stay a clash near 100 %; the legend counts 1; the Kick and Bass cable is dashed and labelled "take
turns"; the card shows the pair view with the share; the timing is kept (a second look renders nothing) and measured again after an edit
of one track only for that track; the song is not changed; renders bit-identical; NI-5a and NI-5b tests' basics (fixes still in the card);
tooltips; no em dashes; no console errors; screenshots.
  python3 tools/ui-tests/taskNI_5c.py [repo dir] [out dir]"""
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
SR = 44100; BPM = 145; nb = 16; spb = 60 / BPM; n = int(nb * spb * SR) + SR; t = np.arange(n) / SR
kick = np.zeros(n); bass = np.zeros(n)
for b in range(nb):
    s0 = int(b * spb * SR); L = int(.110 * SR); tt = np.arange(L) / SR
    kick[s0:s0 + L] += 1.0 * np.sin(2 * np.pi * 55 * tt) * np.exp(-tt / .07)
    for k in (1, 2, 3):
        s1 = int((b + k / 4) * spb * SR); L2 = int(.085 * SR); t2 = np.arange(L2) / SR
        env = np.minimum(1, t2 / .003) * np.minimum(1, (L2 / SR - t2) / .01)
        bass[s1:s1 + L2] += .3 * np.sin(2 * np.pi * 55 * t2) * env
pad = .2 * np.sin(2 * np.pi * 400 * t); lead = .16 * np.sin(2 * np.pi * 410 * t)
def st2(x): return np.vstack([x, x]).astype(np.float32)
B = {k: al.add_audio(st2(v), SR) for k, v in (('Kick', kick), ('Bass', bass), ('Pad', pad), ('Lead', lead))}
COL = {'Kick': '#f5c84c', 'Bass': '#4c8dff', 'Pad': '#3ecf8e', 'Lead': '#ff9a3c'}
al.build({'bpm': BPM, 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'clips': [{'start': 0, 'len': nb, 'name': k, 'buf': b}]} for k, b in B.items()]})
R("for(const[k,c] of Object.entries(%s)){const t=S.tracks.find(x=>x.name===k);t.color=c}changed(true);stop();pos=5;0" % json.dumps(COL))
x0, _ = al.render(b0=0, b1=8, only='Bass'); h0 = hashlib.md5(x0.tobytes()).hexdigest()
u0 = R("UNDO.length+'|'+JSON.stringify(S.tracks.map(t=>[t.id,t.vol,t.fx,t.clips.map(c=>[c.start,c.len])]))")
R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove()})();SCM.get('ni.clashes').run();0")
pg.wait_for_function("()=>NI.clash.beat===5&&!NI.clash.meas&&NI.clash.list.length>=2&&NI.clash.list.every(c=>c.gate||c.duck)&&!NI.cg.busy", timeout=300000); pg.wait_for_timeout(500)
L = R("NI.clash.list.map(c=>({a:c.a.name,b:c.b.name,r:c.range,s:c.s,share:c.gate&&c.gate.share,turns:c.turns}))")
print('    clashes at beat 5:', L)
pair = lambda x, y: next((c for c in L if {c['a'], c['b']} == {x, y}), None)
kb, pl = pair('Kick', 'Bass'), pair('Pad', 'Lead')
ck('the per-beat average flags Kick and Bass (both in the 55 Hz band in that beat)', kb is not None, L)
ck('…and Pad and Lead', pl is not None, L)
if kb: ck('with the timing, Kick and Bass take turns (loud together under 25 % of the time)', kb['turns'] and kb['share'] < .25, kb)
if pl: ck('Pad and Lead stay a clash, loud together nearly all the time (over 90 %)', not pl['turns'] and pl['share'] > .9, pl)
ck('the real clash comes first in the list', L and L[0]['a'] in ('Pad', 'Lead'), L[:1])
ck('the legend counts 1 (take turns is not counted)', R("document.querySelector('#mixWin .cablg .niclb b').textContent") == '1', R("document.querySelector('#mixWin .cablg .niclb').textContent"))
cls = R("[...document.querySelectorAll('#mixWin svg.cabs .nicg .nicc')].map(e=>e.getAttribute('class')+'|'+e.getAttribute('stroke-width'))")
lab = R("[...document.querySelectorAll('#mixWin svg.cabs .nicg .nicl')].map(e=>e.textContent)")
print('    cables:', cls, lab)
ck('two cables drawn, one dashed (take turns) and thin', len(cls) == 2 and sum('nitn' in c for c in cls) == 1 and all(float(c.split('|')[1]) <= 1.25 for c in cls if 'nitn' in c), cls)
ck('its label says "take turns"', any('take turns' in x and 'Kick' in x and 'Bass' in x for x in lab), lab)
tips = R("[...document.querySelectorAll('#mixWin svg.cabs .nicg .nich title')].map(e=>e.textContent)")
ck('the tooltips give the share and say it is an estimate', all('% of the time' in x and 'estimate' in x for x in tips) and len(tips) == 2, tips)
pg.locator('#mixWin').screenshot(path=os.path.join(OUT, 'ni5c_mixer.png'))
# the cards
def card(i):
    R("NI_clPopClose();(()=>{const c=NI.clash.list[%d];NI_clashPop(c,300,200)})();0" % i); pg.wait_for_timeout(200)
    return R("(()=>{const p=document.getElementById('niClashPop');return{t:p.textContent,cv:!!p.querySelector('.nicgv canvas'),fx:p.querySelectorAll('[data-nf]').length,kb:!!p.querySelector('[data-ncg=kb]'),notitle:[...p.querySelectorAll('canvas,.nicgt,button')].filter(e=>!e.title).length}})()")
ik = R("NI.clash.list.findIndex(c=>c.turns)"); ip = R("NI.clash.list.findIndex(c=>!c.turns)")
c1 = card(ik); print('    take turns card:', c1['t'][:220])
ck('the take-turns card: the pair view, "Loud together N% of the time: they take turns"', c1['cv'] and re.search(r'Loud together \d+%.*they take turns', c1['t']) is not None, c1['t'][:200])
ck('the take-turns card offers no fix, the kick and bass lab instead (a low band)', c1['fx'] == 0 and c1['kb'] and 'Nothing to fix here' in c1['t'], (c1['fx'], c1['kb']))
pix = R("(()=>{const c=document.querySelector('#niClashPop .nicgv canvas'),x=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=0;i<x.length;i+=4)if(x[i]+x[i+1]+x[i+2]>120)n++;return n})()")
ck('the pair view is drawn (curves on the dark ground)', pix > 200, pix)
pg.locator('#niClashPop').screenshot(path=os.path.join(OUT, 'ni5c_card_turns.png'))
c2 = card(ip)
ck('the clash card: the share over 90 % and NI-5b\'s two fixes still there', re.search(r'Loud together (9\d|100)%', c2['t']) is not None and c2['fx'] == 2, (c2['t'][:200], c2['fx']))
ck('tooltips on the new parts of the card', c2['notitle'] == 0 and c1['notitle'] == 0, (c1['notitle'], c2['notitle']))
pg.locator('#niClashPop').screenshot(path=os.path.join(OUT, 'ni5c_card_clash.png'))
R("UI.lite=true;UI.liteMan=true;applyLite();0"); pg.wait_for_timeout(300); pg.locator('#mixWin').screenshot(path=os.path.join(OUT, 'ni5c_mixer_light.png'))
R("UI.lite=false;UI.liteMan=false;applyLite();0")
R("NI_clPopClose();0")
# kept: a second look renders nothing
r0 = R("NI.cg.renders"); R("NI.clash.drawn='';NI_clTick(true);0"); pg.wait_for_timeout(1500)
ck('the timing is kept: looking again renders nothing', R("NI.cg.renders") == r0, (r0, R("NI.cg.renders")))
# an edit of Lead (2 dB down): only Lead's window is measured again
R("(()=>{pushUndo();const t=S.tracks.find(x=>x.name==='Lead');t.vol=.8;changed(true)})();0")
pg.wait_for_function("()=>NI.cg.renders>%d" % r0, timeout=300000)
pg.wait_for_function("()=>!NI.clash.meas&&!NI.cg.busy&&!NI.an.busy&&NI.clash.list.every(c=>c.gate||c.duck)", timeout=300000); pg.wait_for_timeout(1200)
r1 = R("NI.cg.renders")
ck('an edit of Lead: its window measured again, the others kept (one render)', r1 - r0 == 1, r1 - r0)
# nothing changed in the song by the measure
R("(()=>{const t=S.tracks.find(x=>x.name==='Lead');UNDO.pop();t.vol=1;changed(true)})();0")
ck('measuring changes nothing in the song', R("UNDO.length+'|'+JSON.stringify(S.tracks.map(t=>[t.id,t.vol,t.fx,t.clips.map(c=>[c.start,c.len])]))") == u0)
x1, _ = al.render(b0=0, b1=8, only='Bass')
ck('a render of Bass is bit-identical', hashlib.md5(x1.tobytes()).hexdigest() == h0)
# nothing while still
pg.wait_for_timeout(1500); fr = pg.evaluate("c=>AudioLab.run(c)", "(async()=>new Promise(r=>{const o=NI_cgGate;window.__n=0;NI_cgGate=function(){__n++;return o.apply(this,arguments)};setTimeout(()=>{NI_cgGate=o;r(__n)},1500)}))()")
ck('nothing worked out while the playhead stands still', fr == 0, fr)
ck('no em dashes in the new UI text', '—' not in R("String(NI_clWords)+String(NI_HOOKS.clashPop)+String(NI_clDraw)+String(NI_clLegend)"))
ck('no audio nodes in the new code', not re.search(r'create(Gain|BufferSource|Oscillator|BiquadFilter)', R("String(NI_cgWork)+String(NI_cgGate)+String(NI_cgPump)")))
ck('no console errors', not al.errors, al.errors[:3])
al.stop()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
