"""Task NI-2b (lane D): I2 kick and bass tuning lab, the view and the fixes.
Checks:
  - the command ni.kickBass and the main menu entry open the card; it finds Kick and Bass, the bar under the playhead,
    read-outs with units (kick note, key, clash with the beat rate, gap in ms), the words, the canvas drawn
  - "Tune the kick to the root" changes only the Kick designer's Pitch (or the drum pad's Tune), is one undo step,
    and removes the clash read-out; Undo puts it back
  - "Bass down an octave" moves only the notes of the bass clips of this bar by 12 semitones, one undo step
  - an audio kick: no tune button, the note says why; bar navigation; track pickers; Play this bar loops the bar
  - nothing is drawn while idle (the canvas is drawn once per measurement); Escape closes; NI_HOOKS.kickBassView rows
  - screenshots (normal and the Light level) to the out dir; no em dashes; no console errors
  python3 tools/ui-tests/taskNI_2b.py [repo dir] [out dir]"""
import sys, os, json, math, copy
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
OUT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, '..', 'ni-shots'))
os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ck(name, ok, info=''):
    N[0] += 1
    if ok: N[1] += 1; print('  ok  ', name, info if info != '' else '')
    else: FAIL.append(name); print('  FAIL', name, info)

BPM = 120
al = AudioLab(os.path.join(ROOT, 'index.html')); al.start(); pg = al.page; R = al.run
print('version', al.version)
def wait_card():
    pg.wait_for_function("()=>{const W=document.getElementById('niKB');return W&&!W.hidden&&NI.kbv.r&&W.querySelector('.nist').textContent===''||(W&&!W.hidden&&NI.kbv.r&&NI.kbv.r.why)}", timeout=20000)
    pg.wait_for_timeout(150)
def card():
    return R("""(()=>{const W=document.getElementById('niKB'),q=k=>W.querySelector('[data-nk="'+k+'"]');return{open:!W.hidden,kn:q('kn').textContent,key:q('key').textContent,cl:q('cl').textContent,gap:q('gap').textContent,bar:q('bar').textContent,
      w:W.querySelector('.niw').textContent,note:W.querySelector('.ninote').textContent,tune:q('tune').hidden?null:q('tune').textContent,oct:!q('oct').hidden,kick:q('kick').selectedOptions[0].textContent,bass:q('bass').selectedOptions[0].textContent,
      tips:[...W.querySelectorAll('button,select,canvas,.nird span')].every(e=>e.title&&e.title.length>8)}})()""")
def tracks(): return json.loads(R("JSON.stringify(S.tracks)"))

def song(kick):
    tr = [kick,
          {'name': 'Bass', 'preset': 'saw', 'vol': .8, 'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 30, 's': b + q, 'l': 0.2, 'v': 0.8} for b in range(16) for q in (.25, .5, .75)]}]},
          {'name': 'Lead', 'preset': 'saw', 'vol': .4, 'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 66, 's': 0, 'l': 4, 'v': .5}]}]}]
    al.build({'bpm': BPM, 'tracks': tr})
    R("PR.root=6;PR.scale='minor';pos=9;0")
KD = {'name': 'Kick', 'preset': 'kick', 'vol': 1.0, 'inst': {'tune': 31}, 'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 36, 's': b, 'l': .25, 'v': .9} for b in range(16)]}]}
song(KD)

# 1. open from the command
ck('the command ni.kickBass is in the commands list', R("SCM.has('ni.kickBass')&&!!SCM.get('ni.kickBass').l"))
R("SCM.get('ni.kickBass').run();0"); wait_card(); c = card(); print('   ', c)
ck('the card opens, finds Kick and Bass (not the Lead)', c['open'] and c['kick'] == 'Kick' and c['bass'] == 'Bass', (c['kick'], c['bass']))
ck('the bar under the playhead (beat 9: bar 3)', c['bar'] == 'bar 3', c['bar'])
ck('kick note G1 with its frequency in Hz', c['kn'].startswith('G1') and '49.0 Hz' in c['kn'], c['kn'])
ck('key F♯ minor', c['key'] == 'F♯ minor', c['key'])
ck('clash: 2.8 Hz with the bass note F♯1 (G1 49.00 Hz against F♯1 46.25 Hz)', c['cl'].startswith('2.8 Hz') and 'F♯1' in c['cl'], c['cl'])
ck('gap 125 ms (bass on the second 16th)', c['gap'] == '125ms', c['gap'])
ck('every control, read-out and the picture has a tooltip', c['tips'])
ck('the tune button names the root: Tune the kick to F♯1', c['tune'] == 'Tune the kick to F♯1', c['tune'])
ck('no em dashes in the card', '—' not in R("document.getElementById('niKB').textContent") and '—' not in R("[...document.querySelectorAll('#niKB [title]')].map(e=>e.title).join(' ')"))
draws = R("(()=>{let n=0;const o=NI_kbDraw;window.NI_kbDraw=function(){n++;return o.apply(this,arguments)};window.__kbn=()=>n;return 1})()")
# the canvas has red clash pixels and the ruler has lit key rows
px = R("""(()=>{const cv=document.querySelector('#niKB canvas'),g=cv.getContext('2d'),d=g.getImageData(0,0,cv.width,cv.height).data;let red=0,blue=0;
   for(let i=0;i<d.length;i+=4){if(d[i]>200&&d[i+1]<120&&d[i+2]<120)red++;if(d[i+2]>150&&d[i]<120&&d[i+1]>130)blue++}return{red,blue,w:cv.width}})()""")
ck('the picture is drawn: clash bars in red and the key lit on the ruler', px['red'] > 200 and px['blue'] > 50, px)
pg.locator('#niKB').screenshot(path=os.path.join(OUT, 'ni2b_card.png'))
pg.screenshot(path=os.path.join(OUT, 'ni2b_window.png'))
pg.wait_for_timeout(1200)
ck('nothing is drawn while idle', R("window.__kbn()") == 0, R("window.__kbn()"))
R("window.NI_kbDraw=NI_kbDraw;0")

# 2. tune the kick to the root
before = tracks(); u0 = R("UNDO.length")
pg.click('#niKB [data-nk="tune"]'); pg.wait_for_timeout(100); wait_card(); c2 = card()
after = tracks(); exp = copy.deepcopy(before)
ki = [i for i, t in enumerate(exp) if t['name'] == 'Kick'][0]; exp[ki]['inst']['tune'] = 30
ck('tune: only the Kick designer Pitch changes, 31 to 30', after == exp, after[ki]['inst']['tune'])
ck('tune: one undo step', R("UNDO.length") == u0 + 1, R("UNDO.length") - u0)
ck('tune: the clash read-out is gone (none) and the kick note is F♯1', c2['cl'] == 'none' and c2['kn'].startswith('F♯1'), (c2['cl'], c2['kn']))
ck('tune: the button hides once the kick is on the root', c2['tune'] is None, c2['tune'])
pg.locator('#niKB').screenshot(path=os.path.join(OUT, 'ni2b_card_tuned.png'))
R("undo();0"); pg.wait_for_timeout(100)
ck('Undo puts the Pitch back to 31', tracks() == before)

# 3. bass down an octave
R("NI_kbShow();0"); wait_card()
before = tracks(); u0 = R("UNDO.length")
ck('the octave button shows', card()['oct'])
pg.click('#niKB [data-nk="oct"]'); pg.wait_for_timeout(100); wait_card(); c3 = card()
after = tracks(); exp = copy.deepcopy(before)
bi = [i for i, t in enumerate(exp) if t['name'] == 'Bass'][0]
for n in exp[bi]['clips'][0]['notes']: n['p'] -= 12
ck('octave: only the bass notes move, every one 12 semitones down', after == exp, after[bi]['clips'][0]['notes'][0]['p'])
ck('octave: one undo step', R("UNDO.length") == u0 + 1)
ck('octave: the clash moves to the bass overtone, same rate (F♯0 overtone against G1: 2.8 Hz)', c3['cl'].startswith('2.8 Hz') and 'F♯0, overtone' in c3['cl'], c3['cl'])
R("undo();0"); ck('Undo puts the bass back', tracks() == before)

# 4. bar navigation, pickers, play this bar
R("NI_kbShow();0"); wait_card()
pg.click('#niKB [data-nk="next"]'); wait_card(); ck('› measures the next bar', card()['bar'] == 'bar 4', card()['bar'])
pg.click('#niKB [data-nk="prev"]'); pg.click('#niKB [data-nk="prev"]'); wait_card(); ck('‹ twice: bar 2', card()['bar'] == 'bar 2', card()['bar'])
lead = al.tracks['Lead']
pg.select_option('#niKB [data-nk="bass"]', str(lead)); wait_card(); c4 = card()
ck('picking the Lead as the bass measures the Lead (it plays only in bar 1)', c4['bass'] == 'Lead' and 'The bass plays no notes in bar 2' in c4['w'], c4['w'][:160])
pg.select_option('#niKB [data-nk="bass"]', str(al.tracks['Bass'])); wait_card()
pg.click('#niKB [data-nk="play"]'); pg.wait_for_timeout(300)
lp = R("({on:play.on,loop:S.loop,r:S.loopRange})")
ck('Play this bar loops bar 2 (beats 4 to 8) and plays', lp['on'] and lp['loop'] and lp['r'] == {'a': 4, 'b': 8}, lp)
R("stop();S.loop=false;S.loopRange=null;syncTransportUI();0")

# 5. the hook for lane C
R("NI_HOOKS.kickBassView.addRow((r,el)=>{el.className='ftrow';el.textContent='F18 row: '+(r&&r.kick?r.kick.endTxt:'')});NI_HOOKS.kickBassView.refresh();0"); wait_card()
ck('NI_HOOKS.kickBassView rows render under the words', R("(e=>!!e&&e.textContent.startsWith('F18 row: G1'))(document.querySelector('#niKB .nikbx .ftrow'))"))
R("NI.kbv.rows.length=0;0")

# 6. Escape, the menu entry, the Light level
pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
ck('Escape closes the card', R("document.getElementById('niKB').hidden"))
ck('the main menu has "Kick and bass lab…"', R("(()=>{const s=String(typeof appMenu==='function'?appMenu:'');return 1})()") == 1 and 'Kick and bass lab…' in open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read())
R("UI.lite=true;UI.liteMan=true;applyLite();0"); pg.wait_for_timeout(300)
R("NI_kbOpen();0"); wait_card()
pg.locator('#niKB').screenshot(path=os.path.join(OUT, 'ni2b_card_light.png'))
ck('the card opens at the Light level too', card()['open'])
R("NI_kbClose();UI.lite=false;UI.liteMan=false;applyLite();0")

# 7. a drum machine kick: the pad's Tune
al.build({'bpm': BPM, 'tracks': [{'name': 'Drums', 'preset': 'drums', 'vol': 1.0, 'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 36, 's': b, 'l': .25, 'v': .9} for b in range(16)]}]},
          {'name': 'Bass', 'preset': 'saw', 'vol': .8, 'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 31, 's': b + .5, 'l': .4, 'v': .8} for b in range(16)]}]}]})
R("PR.root=7;PR.scale='minor';pos=1;0")
base = R("KPRE.house.tune")
R("NI_kbOpen();0"); wait_card(); c7 = card()
before = tracks(); pg.click('#niKB [data-nk="tune"]'); pg.wait_for_timeout(100); wait_card()
after = tracks(); exp = copy.deepcopy(before); exp[0]['inst']['pads'][0]['tune'] = round(31 - base, 2)
ck('drum machine: tune changes only pad 1\'s Tune (house kick %g to G1)' % base, after == exp, (c7['tune'], after[0]['inst']['pads'][0]['tune']))
ck('drum machine: in tune with the bass afterwards', card()['cl'] == 'none', card()['cl'])
R("NI_kbClose();0")

# 8. an audio kick: measured, no tune fix
SR = 48000; n = int(16 * 0.5 * SR); x = np.zeros(n); m = int(.35 * SR); tt = np.arange(m) / SR
f = np.exp(np.log(49) + (np.log(250) - np.log(49)) * (1 - np.minimum(1, tt / .04)) ** 3); hit = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 - tt / .35)
for b in range(16): s0 = int(b * .5 * SR); x[s0:s0 + m] += hit[:min(m, n - s0)]
buf = al.add_audio(np.vstack([x, x]).astype(np.float32), SR)
al.build({'bpm': BPM, 'tracks': [{'kind': 'audio', 'name': 'Kick', 'vol': 1.0, 'clips': [{'start': 0, 'len': 16, 'name': 'k', 'buf': buf}]},
          {'name': 'Bass', 'preset': 'saw', 'vol': .8, 'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 30, 's': b + .5, 'l': .4, 'v': .8} for b in range(16)]}]}]})
R("PR.root=6;PR.scale='minor';pos=5;0")
R("NI_kbOpen();0"); wait_card(); c8 = card()
ck('audio kick: measured (about G1), no tune button, the note says it is measured and why', c8['tune'] is None and 'measured from its sound' in c8['note'] and c8['kn'].startswith('≈ G1'), (c8['kn'], c8['note'][:90]))
pg.locator('#niKB').screenshot(path=os.path.join(OUT, 'ni2b_card_audio.png'))
R("NI_kbClose();0")

src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
blk = src[src.index('/* ===== lane D (task NI-2b)'):src.index('/* ===== end of lane D NI-2b')]
ck('no audio nodes, no animation loop in the NI-2b block', not any(k in blk for k in ('createGain', 'createBiquad', 'AudioWorklet', '.connect(', 'requestAnimationFrame', 'setInterval')), '')
ck('no em dashes in the NI-2b block', '—' not in blk)
ck('no console errors', not al.errors, al.errors)
al.stop()
print('%d/%d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
