"""Task NI-7b (lane D): X23 the gain staging check for the whole mix.
Test song (audio, 120 BPM, 44.1 kHz, 32 beats; the range is the 8 bars around the playhead at beat 8 = beats 0 to 32):
  Hot     a 220 Hz sine at 1.4 (+2.92 dBFS), no device, fader 0.2: hot into the fader at +2.9 dB after its clips, turn down 4.5 dB
  Hot2    a 1 kHz sine at 0.5 (-6.02 dBFS), Pro EQ with +12 dB output, then a Compressor, fader 0.1: hot into Compressor at +6.0 dB after Pro EQ
  Quiet   a 330 Hz sine at 0.02 (-33.98 dBFS) into a Compressor, fader 1: quiet into Compressor at -34.0 dB (and not barely heard)
  Faint   a 440 Hz sine at 0.005 (-46.02 dBFS), no device, fader 1: barely heard at -46.0 dB after its fader
  Clean   a 550 Hz sine at 0.1: nothing
Checks: the command and the menu entry; exactly those four lines, in order hot first, with the numbers within 0.2 dB; the master's peak
against a direct render; a clean mix lists nothing; a master over -1 dBFS is a problem, and not with a Limiter on the master; a click
selects the track, Journey opens the level journey of that track; an edit measures again; idle does nothing; a render of Hot bit-identical
before and after; screenshots (test song, Fractals, the Light level); tooltips; no em dashes; no console errors.
  python3 tools/ui-tests/taskNI_7b.py [repo dir] [out dir]"""
# for: task NI-7b (lane D)
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
def wait_runs(n0, timeout=600000):
    pg.wait_for_function("()=>NI.gs.runs>%d&&!NI.gs.busy&&NI.gs.res" % n0, timeout=timeout); pg.wait_for_timeout(200)
def res():
    return R("""(()=>{const r=NI.gs.res;return{b0:r.b0,b1:r.b1,how:r.how,master:r.master,n:r.tracks.length,probs:r.probs.map(p=>({kind:p.kind,name:p.t?p.t.name:'Master',peak:p.peak,by:p.by||null,to:p.to?p.to.name:null,txt:p.txt}))}})()""")

ck('the command ni.gainStaging is in the commands list', R("SCM.has('ni.gainStaging')&&!!SCM.get('ni.gainStaging').l"))
ck('the main menu has "Gain staging…"', R("[...document.scripts].some(s=>s.textContent.includes(\"label:'Gain staging…'\"))"))

if R("S.tracks.some(t=>t.name==='Kick')"):
    R("stop();pos=128;0")
    n0 = R("NI.gs.runs"); R("NI_gsOpen();0"); wait_runs(n0)
    r = res(); print('    Fractals:', r['n'], 'tracks;', [(p['name'], p['kind'], round(p['peak'], 1), p['to']) for p in r['probs']], 'master', r['master'])
    ck('Fractals: every track that plays is measured and the master read', r['n'] >= 5 and r['master']['peak'] < 6, (r['n'], r['master']))
    pg.locator('#niGain').screenshot(path=os.path.join(OUT, 'ni7b_fractals.png'))
    R("UI.lite=true;UI.liteMan=true;applyLite();0"); pg.wait_for_timeout(300); pg.locator('#niGain').screenshot(path=os.path.join(OUT, 'ni7b_fractals_light.png'))
    R("UI.lite=false;UI.liteMan=false;applyLite();0")
    R("document.querySelector('#niGain .fwc').click();0"); pg.wait_for_timeout(150)

SR = 44100; nb = 32; n = nb * SR // 2; t = np.arange(n) / SR
st = lambda x: np.vstack([x, x]).astype(np.float32)
src = {'Hot': 1.4 * np.sin(2 * np.pi * 220 * t), 'Hot2': .5 * np.sin(2 * np.pi * 1000 * t), 'Quiet': .02 * np.sin(2 * np.pi * 330 * t),
       'Faint': .005 * np.sin(2 * np.pi * 440 * t), 'Clean': .1 * np.sin(2 * np.pi * 550 * t)}
B = {k: al.add_audio(st(v), SR) for k, v in src.items()}
vol = {'Hot': .2, 'Hot2': .1, 'Quiet': 1.0, 'Faint': 1.0, 'Clean': 1.0}
def build(names):
    al.build({'bpm': 120, 'tracks': [{'kind': 'audio', 'name': k, 'vol': vol[k], 'clips': [{'start': 0, 'len': nb, 'name': k, 'buf': B[k]}]} for k in names]})
    R("""(()=>{const T=n=>S.tracks.find(t=>t.name===n);const h=T('Hot2');if(h){const e=mkFx('eq');e.p.out=12;h.fx=[e,mkFx('comp')]}const q=T('Quiet');if(q)q.fx=[mkFx('comp')];S.mfx=[];UNDO.length=0;changed(true)})();0""")
    R("S.loop=false;stop();pos=8;0")
build(['Hot', 'Hot2', 'Quiet', 'Faint', 'Clean'])
x0, _ = al.render(b0=0, b1=16, only='Hot'); h0 = hashlib.md5(x0.tobytes()).hexdigest()
n0 = R("NI.gs.runs"); R("SCM.get('ni.gainStaging').run();0"); wait_runs(n0)
r = res(); P = r['probs']
print('    problems:', [(p['name'], p['kind'], round(p['peak'], 2), p['to'], p['by'], p['txt']) for p in P]); print('    master:', r['master'])
ck('the range: beats 0 to 32 (8 bars around the playhead)', (r['b0'], r['b1'], r['how']) == (0, 32, '8 bars around the playhead'), (r['b0'], r['b1'], r['how']))
ck('all five tracks measured', r['n'] == 5, r['n'])
ck('exactly four lines: Hot2 and Hot hot, Quiet quiet, Faint barely heard', [(p['name'], p['kind']) for p in P] == [('Hot2', 'hot'), ('Hot', 'hot'), ('Quiet', 'quiet'), ('Faint', 'low')], [(p['name'], p['kind']) for p in P])
D = {p['name']: p for p in P}
if 'Hot' in D:
    ck('Hot: +2.9 dB into the fader, after its clips; turn down 4.5 dB', abs(D['Hot']['peak'] - 2.92) < .2 and D['Hot']['to'] == 'the fader' and D['Hot']['by'] == 4.5 and re.search(r'hot into the fader: peaks at \+2\.9\W?dBFS after its clips', D['Hot']['txt']), D['Hot'])
if 'Hot2' in D:
    ck('Hot2: +6.0 dB into Compressor, after Pro EQ', abs(D['Hot2']['peak'] - 6.02) < .2 and D['Hot2']['to'] == 'Compressor' and 'after Pro EQ' in D['Hot2']['txt'], D['Hot2'])
if 'Quiet' in D:
    ck('Quiet: -34.0 dB into Compressor', abs(D['Quiet']['peak'] + 33.98) < .2 and D['Quiet']['to'] == 'Compressor' and re.search(r'quiet into Compressor: peaks at −34\.0\W?dBFS', D['Quiet']['txt']), D['Quiet'])
if 'Faint' in D:
    ck('Faint: -46.0 dB after its fader', abs(D['Faint']['peak'] + 46.02) < .2 and re.search(r'barely heard: peaks at −46\.0\W?dBFS after its fader', D['Faint']['txt']), D['Faint'])
xm, _ = al.render(b0=0, b1=32)
pm = 20 * np.log10(np.abs(xm).max())
ck('the master peak matches a direct render of the mix (within 0.1 dB)', abs(r['master']['peak'] - pm) < .1, (r['master']['peak'], pm))
txt = R("document.querySelector('#niGain .fwb').textContent")
ck('the window shows the master headroom in words', re.search(r'Master: peaks at −\d+\.\d\W?dBFS, \d+\.\d\W?dB of headroom', txt) is not None, txt[-300:])
ck('the status names the count and the range', R("document.querySelector('#niGain .ngst').textContent") == '4 to look at, bars 1 to 8 (8 bars around the playhead)', R("document.querySelector('#niGain .ngst').textContent"))
pg.locator('#niGain').screenshot(path=os.path.join(OUT, 'ni7b_test.png'))
tips = R("[...document.querySelectorAll('#niGain button,#niGain .ngr,#niGain .ngm span,#niGain .ngt span:not(.ngst),#niGain .ngnote')].filter(e=>!e.title).map(e=>e.outerHTML.slice(0,60))")
ck('tooltips on every control and line', not tips, tips[:3])

# clicks
R("document.querySelector('#niGain .ngr[data-ngt=\"'+S.tracks.find(t=>t.name==='Faint').id+'\"]').click();0")
ck('clicking a line selects its track', R("selT===S.tracks.find(t=>t.name==='Faint').id"))
R("document.querySelector('#niGain [data-ngj=\"'+S.tracks.find(t=>t.name==='Quiet').id+'\"]').click();0"); pg.wait_for_timeout(300)
ck('Journey selects the track and opens its level journey', R("selT===S.tracks.find(t=>t.name==='Quiet').id&&!!document.getElementById('niJour')&&!document.getElementById('niJour').hidden&&NI.jour.tid===S.tracks.find(t=>t.name==='Quiet').id"))
R("(()=>{const w=document.getElementById('niJour');const c=w&&w.querySelector('.fwc');if(c)c.click()})();0"); pg.wait_for_timeout(200)

# idle
pg.wait_for_timeout(1500); n1 = R("NI.gs.runs"); pg.wait_for_timeout(2000)
ck('idle 2 s: nothing measured again', R("NI.gs.runs") == n1)

# an edit: Hot's fader is not the problem, its clip is; lower the clip gain by 4.5 dB: the line goes
n0 = R("NI.gs.runs"); R("(()=>{pushUndo();const c=S.tracks.find(t=>t.name==='Hot').clips[0];c.gain=(c.gain||0)-4.5;changed(true)})();0"); wait_runs(n0)
P2 = [(p['name'], p['kind']) for p in res()['probs']]
ck('Hot\'s clip turned down by 4.5 dB: its line goes, the others stay', ('Hot', 'hot') not in P2 and ('Hot2', 'hot') in P2, P2)
R("undo();0"); pg.wait_for_timeout(1500)

# the master over -1 dBFS, then with a Limiter on the master
n0 = R("NI.gs.runs"); R("(()=>{pushUndo();S.tracks.find(t=>t.name==='Hot').vol=1;S.master=6;changed(true)})();0"); wait_runs(n0)
r = res(); print('    master loud:', r['master'], [(p['name'], p['txt']) for p in r['probs'] if p['kind'] == 'master'])
ck('a master over -1 dBFS without a limiter is the first line', r['probs'][0]['kind'] == 'master' and 'it clips' in r['probs'][0]['txt'], r['probs'][:1])
n0 = R("NI.gs.runs"); R("(()=>{S.mfx=[mkFx('limit')];changed(true)})();0"); wait_runs(n0)
r = res()
ck('with a Limiter on the master it is not a problem, and the master line says so', not any(p['kind'] == 'master' for p in r['probs']) and r['master']['lim'] == 'Limiter' and 'after its Limiter' in R("document.querySelector('#niGain .ngm').textContent"), (r['master'], R("document.querySelector('#niGain .ngm').textContent")))

# a clean mix
build(['Clean'])
n0 = R("NI.gs.runs"); R("NI_gsOpen();0"); wait_runs(n0)
r = res()
ck('a clean mix lists nothing and says so', not r['probs'] and 'Nothing to fix' in R("document.querySelector('#niGain .ngl').textContent"), r['probs'])
pg.locator('#niGain').screenshot(path=os.path.join(OUT, 'ni7b_clean.png'))
R("document.querySelector('#niGain .fwc').click();0"); pg.wait_for_timeout(200)
ck('closing stops its check', R("NI.gs.tm") == 0)

build(['Hot', 'Hot2', 'Quiet', 'Faint', 'Clean'])
x1, _ = al.render(b0=0, b1=16, only='Hot')
ck('a render of Hot is bit-identical after the check measured it', hashlib.md5(x1.tobytes()).hexdigest() == h0)
ck('no em dashes in the new UI text', '—' not in R("(document.getElementById('niGain')||{}).textContent+String(NI_gsJudge)+String(NI_gsShow)+String(NI_gsOpen)+String(NI_gsMeasure)"))
ck('no console errors', not al.errors, al.errors[:3])
al.stop()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
