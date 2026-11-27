"""Task NI-1b (lane D): I3 "Why is this clipping?", the card.
Test project from known signals (as taskNI_1a.py): Kick + Bass clip at bar 9; played live (safety limiter off and on) so the log has events.
Checks: the dot on the master peak read-out; a click on it opens the card; the card names bar 9 and both tracks, shows peak and inter-sample
peak with units and a bar per track (the phase-inverted one negative); "Lower Kick" is one undo step, changes only Kick's volume and the
re-render shows no clip (Undo puts it back); "Limiter on the master" is one undo step and the re-render shows no clip; "Play the moment"
loops the 2 bars around it; the command ni.clipExplain opens it; a strip event shows the strip's own level; Escape closes; every control
has a tooltip; no em dashes; nothing drawn per frame while the card is open and the song stopped; no console errors.
Screenshots (normal and the Light level) go to the out dir.
  python3 tools/ui-tests/taskNI_1b.py [repo dir] [out dir]"""
import sys, os, json, math
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

SR = 44100; BPM = 120; n = int(24.0 * SR); t = np.arange(n) / SR
def kick_sig():
    x = np.zeros(n)
    for b in range(48):
        s0 = int(b * 60 / BPM * SR); amp = 0.8 if b == 32 else 0.2
        m = min(n - s0, int(0.4 * SR)); tt = np.arange(m) / SR
        x[s0:s0 + m] += amp * np.exp(-tt / 1.0) * np.cos(2 * np.pi * 55 * tt)
    return x
SIG = {'Kick': kick_sig(), 'Bass': 0.5 * np.cos(2 * np.pi * 110 * t), 'Anti': -0.1 * np.cos(2 * np.pi * 110 * t)}
st = lambda x: np.vstack([x, x]).astype(np.float32)

al = AudioLab(os.path.join(ROOT, 'index.html')); al.start(); pg = al.page
print('version', al.version)
R = al.run
def A(expr): return pg.evaluate("c=>AudioLab.run(c)", "(async()=>{const r=await %s;return JSON.parse(JSON.stringify(r===undefined?null:r))})()" % expr)
R("UI.headroom=-6;UI.bitPerfect=false;0")
ids = {k: al.add_audio(st(v), SR) for k, v in SIG.items()}
al.build({'bpm': BPM, 'master': 20 * math.log10(2), 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'clips': [{'start': 0, 'len': 48, 'name': k + ' clip', 'buf': ids[k]}]} for k in SIG]})
R("NI_clipClear();UI.limiter=false;routeMaster();0")
def live(b0, secs):
    R("stop();pos=%g;toggle();0" % b0); pg.wait_for_timeout(int(secs * 1000)); R("stop();0")
live(30, 4.0)
R("UI.limiter=true;routeMaster();0"); live(30, 4.0)
log = R("JSON.parse(JSON.stringify(NI_clipLog()))")
ck('two master events logged (limiter off, then on)', len([e for e in log if e['src'] == 'master']) == 2, [(round(e['t'], 2), e['lim'], e['sat']) for e in log])
ck('the master peak read-out shows the dot and a tooltip about it', R("document.getElementById('peakBox').classList.contains('niev')&&/see why/.test(document.getElementById('peakBox').title)"))
ck('the Clip button next to the mixer button shows, with a tooltip', R("(b=>!!b&&!b.hidden&&b.offsetWidth>0&&/see why/.test(b.title))(document.getElementById('niClipB'))"))
pg.locator('.mgrp').screenshot(path=os.path.join(OUT, 'ni1b_clip_button.png'))
def card(): return R("""(()=>{const W=document.getElementById('niClip');if(!W)return null;const q=s=>W.querySelector(s);
  return{open:!W.hidden,st:q('.nist').textContent,w:q('.niw').textContent,at:q('[data-ni="at"]').textContent,pk:q('[data-ni="pk"]').textContent,tp:q('[data-ni="tp"]').textContent,
  bars:[...W.querySelectorAll('.nibr')].map(r=>[r.querySelector('span').textContent,r.querySelector('b').textContent]),low:q('[data-ni="low"]').hidden?null:q('[data-ni="low"]').textContent,
  lim:!q('[data-ni="lim"]').hidden,nev:q('[data-ni="ev"]').options.length,note:q('.ninote').textContent,
  untitled:[...W.querySelectorAll('button,select')].filter(b=>!b.hidden&&!b.title).map(b=>b.outerHTML.slice(0,60)),text:W.innerText,
  rect:(b=>[b.left,b.top,b.right,b.bottom])(W.getBoundingClientRect()),vw:innerWidth,vh:innerHeight}})()""")
def wait_card(ms=15000):
    pg.wait_for_function("()=>{const W=document.getElementById('niClip');return W&&!W.hidden&&W.querySelector('.nist').textContent===''&&W.querySelector('.niw').textContent!==''}", timeout=ms)
    pg.wait_for_timeout(100)
# 1. a click on the Clip button
pg.click('#niClipB'); wait_card(); c = card()
print('    words:', c['w'])
ck('click on the Clip button opens the card', c['open'], c['st'])
ck('the card names bar 9', c['at'].startswith('9.1') and 'bar 9, beat 1' in c['w'], (c['at'], c['w']))
ck('the card names Kick and Bass, the chain in words', 'Kick + Bass add up here' in c['w'], c['w'])
ck('peak and inter-sample peak with units', c['pk'].endswith('dBFS') and c['pk'].startswith('+') and c['tp'].endswith('dBTP'), (c['pk'], c['tp']))
names = [b[0] for b in c['bars']]
ck('one bar per track, Kick and Bass first, Anti negative', names[:2] == ['Kick', 'Bass'] and 'Anti' in names and c['bars'][names.index('Anti')][1].startswith('-'), c['bars'])
ck('the event list has both events', c['nev'] == 2, c['nev'])
ck('the limiter note for the newest event (heard through the safety limiter)', 'safety limiter' in c['note'], c['note'])
ck('the fixes are offered: lower Kick, limiter on the master', c['low'] and c['low'].startswith('Lower Kick by') and c['lim'], (c['low'], c['lim']))
ck('every visible control has a tooltip', not c['untitled'], c['untitled'])
ck('no em dashes in the card', '—' not in c['text'], '')
ck('the card is inside the window', c['rect'][0] >= 0 and c['rect'][1] >= 0 and c['rect'][2] <= c['vw'] and c['rect'][3] <= c['vh'], c['rect'])
pg.screenshot(path=os.path.join(OUT, 'ni1b_card.png'))
pg.locator('#niClip').screenshot(path=os.path.join(OUT, 'ni1b_card_only.png'))
# nothing per frame while open and stopped
fr = A("new Promise(r=>{let n=0;const o=NI_cardFill,o2=NI_cardPlace;window.__nf=0;NI_cardPlace=function(){__nf++;return o2.apply(this,arguments)};setTimeout(()=>{NI_cardPlace=o2;r(__nf)},1500)})")
ck('nothing redrawn per frame while the card is open', fr == 0, fr)
# 2. Lower Kick: one undo step, only Kick's volume, the clip is gone
vol0 = R("JSON.stringify(S.tracks.map(t=>[t.name,t.vol]))"); u0 = R("UNDO.length")
pg.click('#niClip [data-ni="low"]'); wait_card(); c2 = card(); vol1 = json.loads(R("JSON.stringify(S.tracks.map(t=>[t.name,t.vol]))"))
ck('Lower Kick is one undo step', R("UNDO.length") == u0 + 1, R("UNDO.length") - u0)
ck('only Kick\'s volume changed', [v for nm, v in vol1 if nm != 'Kick'] == [v for nm, v in json.loads(vol0) if nm != 'Kick'] and dict(vol1)['Kick'] < 1, vol1)
print('    after:', c2['w'])
ck('re-rendered: no clip any more', c2['w'].startswith('No clip here') and not c2['pk'].startswith('+'), (c2['pk'], c2['w']))
R("undo();0")
ck('Undo puts the volume back', R("JSON.stringify(S.tracks.map(t=>[t.name,t.vol]))") == vol0 and R("UNDO.length") == u0, R("JSON.stringify(S.tracks.map(t=>[t.name,t.vol]))"))
# 3. Limiter on the master
R("NI_cardShow(NI.card.ev);0"); wait_card(); u0 = R("UNDO.length")
pg.click('#niClip [data-ni="lim"]'); wait_card(); c3 = card()
ck('Limiter on the master is one undo step', R("UNDO.length") == u0 + 1, R("UNDO.length") - u0)
ck('a limiter is on at the end of the master chain', R("(()=>{const f=(S.mfx||[]).slice(-1)[0];return !!f&&f.type==='limit'&&f.on&&f.p.ceil===-1})()"))
ck('re-rendered with the limiter: no clip', c3['w'].startswith('No clip here') and float(c3['pk'].replace('dBFS', '')) <= -0.9, (c3['pk'], c3['w']))
R("undo();0")
ck('Undo takes the limiter away', R("(S.mfx||[]).filter(f=>f.type==='limit').length") == 0)
# 4. Play the moment
R("NI_cardShow(NI.card.ev);0"); wait_card()
pg.click('#niClip [data-ni="play"]'); pg.wait_for_timeout(600)
lp = R("JSON.parse(JSON.stringify({on:play.on,loop:S.loop,r:S.loopRange,b:curDisp()}))")
ck('Play the moment loops bars 8 and 9 and plays', lp['on'] and lp['loop'] and lp['r']['a'] == 28 and lp['r']['b'] == 36 and 28 <= lp['b'] < 36, lp)
R("stop();S.loop=false;S.loopRange=null;syncTransportUI();0")
# 5. Escape, the command, a strip event, the Light level
pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
ck('Escape closes the card', R("document.getElementById('niClip').hidden"))
ck('the command ni.clipExplain is in the commands list', R("SCM.has('ni.clipExplain')&&!!SCM.get('ni.clipExplain').l"))
R("SCM.get('ni.clipExplain').run();0"); wait_card()
ck('the command opens the card for the last clip', card()['open'])
R("NI_cardClose();0")
kid = al.tracks['Kick']
R("NI.clips.log.push({id:999,src:%s,t:32,lb:32,db:2,lim:false,sat:false,w:0,at:Date.now(),proj:PJ.cur});0" % json.dumps(kid))
R("NI_clipCard(NI.clips.log[NI.clips.log.length-1]);0"); wait_card(); c5 = card()
ck('a strip event: the card gives the strip\'s own level and clip', c5['w'].startswith('Kick') and 'on its own' in c5['w'] and 'Kick clip' in c5['w'] and '-1.9 dB' in c5['w'], c5['w'])
R("NI_cardClose();openMixer();0"); pg.wait_for_timeout(500)
pg.click('#mxClip'); wait_card()
ck("the mixer's master clip dot opens the card", card()['open'])
R("NI_cardClose();document.getElementById('mixWin').hidden=true;UI.lite=true;UI.liteMan=true;applyLite();0"); pg.wait_for_timeout(400)
pg.click('#niClipB'); wait_card()
R("NI_clipCard(NI_clipLog()[1]);0"); wait_card()
pg.locator('#niClip').screenshot(path=os.path.join(OUT, 'ni1b_card_light.png'))
ck('the card opens at the Light level too', card()['open'])
R("UI.lite=false;UI.liteMan=false;applyLite();0")
# 6. Clear
pg.click('#niClip [data-ni="clr"]'); pg.wait_for_timeout(200)
ck('Clear empties the log, hides the card and removes the dot', R("NI_clipLog().length===0&&document.getElementById('niClip').hidden&&!document.getElementById('peakBox').classList.contains('niev')"))
ck('Clear hides the Clip button', R("document.getElementById('niClipB').hidden"))
R("document.getElementById('peakBox').click();0"); pg.wait_for_timeout(200)
ck('with no events a click on the peak read-out only resets it (old behaviour)', R("document.getElementById('niClip').hidden&&!document.getElementById('peakBox').classList.contains('clip')"))
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
blk = src[src.index('/* ===== lane D (task NI-1b)'):src.index('/* ===== end of lane D NI-1b')]
ck('no audio nodes made in the card block', not any(k in blk for k in ('createGain', 'createBiquad', 'audioWorklet', '.connect(')))
ck('no em dashes in lane D text', '—' not in blk)
ck('no console errors', not al.errors, al.errors)
al.stop()
print('%d/%d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
