"""Task NI-5a (lane D): I12 masking cables, part 1: the clashes.
Test song (audio tracks, 120 BPM, 44.1 kHz, 8 bars): Bass 100 Hz all through; Kick 106 Hz in bars 1 to 4 (the same 1/3-octave band as the
bass), then 3 kHz in bars 5 to 8 (moved away); Pad 1 kHz all through; Hat 8 kHz all through.
Checks (research section 5, NF5): the two tones in the same band give one cable, labelled with both names and the band; moving one tone away
(bar 5 on) removes it; the strength and thickness; normal cables and "Selected only" unchanged (and Selected only limits the clashes to the
selected channel); the switch in the legend; the click card and its Select button; the command ni.clashes; an edit is measured again; nothing
worked or drawn while the playhead stands still; while playing it follows the playhead; closing the mixer stops the check; tooltips; no em
dashes; no audio nodes; screenshots (normal and Light level); no console errors.
  python3 tools/ui-tests/taskNI_5a.py [repo dir] [out dir]"""
import sys, os, json
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
def A(expr): return pg.evaluate("c=>AudioLab.run(c)", "(async()=>{const r=await %s;return JSON.parse(JSON.stringify(r===undefined?null:r))})()" % expr)

SR = 44100; BPM = 120; nb = 32; n = nb * SR // 2; t = np.arange(n) / SR; half = 16 * SR // 2
def st2(x): return np.vstack([x, x]).astype(np.float32)
bass = 0.3 * np.sin(2 * np.pi * 100 * t)
kick = 0.3 * np.sin(2 * np.pi * 106 * t); kick[half:] = 0.3 * np.sin(2 * np.pi * 3000 * t[half:])
pad = 0.2 * np.sin(2 * np.pi * 1000 * t)
hat = 0.1 * np.sin(2 * np.pi * 8000 * t)
B = {k: al.add_audio(st2(v), SR) for k, v in (('Bass', bass), ('Kick', kick), ('Pad', pad), ('Hat', hat))}
COL = {'Bass': '#4c8dff', 'Kick': '#f5c84c', 'Pad': '#3ecf8e', 'Hat': '#c9a0ff'}
al.build({'bpm': BPM, 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'color': COL[k], 'clips': [{'start': 0, 'len': 32, 'name': k, 'buf': b}]} for k, b in B.items()]})
R("for(const[k,c] of Object.entries(%s)){const t=S.tracks.find(x=>x.name===k);t.color=c}changed(true);stop();pos=4;0" % json.dumps(COL))
R("(()=>{const r=mkTrack('return',null,'Verb','#9aa3b5');S.tracks.push(r);S.tracks.find(t=>t.name==='Pad').sends={[r.id]:.5};changed(true)})();0")
ck('the command ni.clashes is in the commands list', R("SCM.has('ni.clashes')&&!!SCM.get('ni.clashes').l"))
# normal cables before: a sidechain from Kick to Bass is a normal cable (the lane must not change with Clashes on)
R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();openMixer()})()"); pg.wait_for_timeout(800)
R("mxsSet('cab',1);mxsSet('niClash',0);cabSoon();0"); pg.wait_for_timeout(500)
ck('the legend has a Clashes switch, off', R("(()=>{const b=document.querySelector('#mixWin .cablg .niclb');return !!b&&!b.classList.contains('on')&&/Clashes/.test(b.textContent)})()"))
cfg0 = R("document.querySelector('#mixWin svg.cabs .cfg').innerHTML")
cfi0 = R("[...document.querySelectorAll('#mixWin svg.cabs .cfg .cfr')].map(e=>e.dataset.i+e.getAttribute('stroke')).join()"); T0 = R("cs2T()")
ck('the test song has a normal cable (Pad send to Verb)', R("document.querySelectorAll('#mixWin svg.cabs .cfg .cfr').length") >= 1)
lg0 = R("[...document.querySelectorAll('#mixWin .cablg [data-cl]')].map(b=>b.dataset.cl+(b.classList.contains('on')?1:0)).join()")
# the command turns it on and the clashes are measured in the background
u0 = R("UNDO.length+'|'+JSON.stringify(S.tracks.map(t=>[t.id,t.vol,t.fx,t.clips.map(c=>[c.start,c.len])]))")
R("SCM.get('ni.clashes').run();0")
pg.wait_for_function("()=>NI.clash.list.length>0||(!NI.an.busy&&NI.clash.beat!=null&&!NI.clash.meas)", timeout=120000); pg.wait_for_timeout(400)
ck('the command opens the mixer with the cable lane and Clashes on', R("!document.getElementById('mixWin').hidden&&mxsO().cab&&mxsO().niClash&&NI.clash.tm>0"))
L = R("NI.clash.list.map(c=>({a:c.a.name,b:c.b.name,r:c.range,s:c.s,la:c.la,lb:c.lb}))")
print('    at beat 4:', L)
ck('beat 4: Bass at 100 Hz and Kick at 106 Hz (one 1/3-octave band) give exactly one clash', len(L) == 1 and sorted([L[0]['a'], L[0]['b']]) == ['Bass', 'Kick'], L)
ck('the band of the clash holds 100 Hz', len(L) == 1 and R("(()=>{const c=NI.clash.list[0],a=NI_clEdges(c.m0)[0],b=NI_clEdges(c.m1)[1];return a<=100&&b>=106})()"), L and L[0]['r'])
drawn = R("[...document.querySelectorAll('#mixWin svg.cabs .nicg .nicc')].length")
lab = R("[...document.querySelectorAll('#mixWin svg.cabs .nicg .nicl')].map(x=>x.textContent)")
ck('one magenta cable is drawn in the cable lane, labelled with both names and the band', drawn == 1 and len(lab) == 1 and 'Bass' in lab[0] and 'Kick' in lab[0] and ' vs ' in lab[0] and 'Hz' in lab[0], (drawn, lab))
ck('the legend shows the count (1)', R("document.querySelector('#mixWin .cablg .niclb b').textContent") == '1', R("document.querySelector('#mixWin .cablg .niclb').textContent"))
ck('the normal cables are all still drawn, same cables and colours (the lane is taller, so their paths sit lower)', R("[...document.querySelectorAll('#mixWin svg.cabs .cfg .cfr')].map(e=>e.dataset.i+e.getAttribute('stroke')).join()") == cfi0)
ck('with Clashes on the lane is taller (two rows more) when the channels leave room', R("cs2T()") > T0, (T0, R("cs2T()")))
ck('the normal legend buttons are unchanged', R("[...document.querySelectorAll('#mixWin .cablg [data-cl]')].map(b=>b.dataset.cl+(b.classList.contains('on')?1:0)).join()") == lg0)
# direct calculation: the strength from the levels
FLr = R("NI_clashAt(4).floor")
ck('the floor is 36 dB under the loudest band (here the bass and kick band), and the strength is the quieter one over it, less for the gap', len(L) == 1 and abs(L[0]['s'] - (L[0]['lb'] - FLr) * (1 - (L[0]['la'] - L[0]['lb']) / 24)) < .01 and abs(FLr - max(-80, min(-50, L[0]['la'] - 36))) < .01, (L, FLr))
ck('measuring and showing clashes changes nothing in the song (no undo step, same tracks)', R("UNDO.length+'|'+JSON.stringify(S.tracks.map(t=>[t.id,t.vol,t.fx,t.clips.map(c=>[c.start,c.len])]))") == u0)
pg.screenshot(path=os.path.join(OUT, 'ni5a_window.png'))
pg.locator('#mixWin').screenshot(path=os.path.join(OUT, 'ni5a_mixer.png'))
# moving one tone away removes it
R("pos=20;0"); pg.wait_for_function("()=>NI.clash.beat===20&&!NI.clash.meas", timeout=120000); pg.wait_for_timeout(400)
L2 = R("NI.clash.list.map(c=>c.a.name+'/'+c.b.name)")
ck('beat 20: the kick moved to 3 kHz, no clash left (Pad 1 kHz, Hat 8 kHz apart too)', L2 == [], L2)
ck('no clash cable drawn at beat 20, the legend says 0', R("document.querySelectorAll('#mixWin svg.cabs .nicg .nicc').length") == 0 and R("document.querySelector('#mixWin .cablg .niclb b').textContent") == '0')
# nothing worked while the playhead stands
R("pos=4;0"); pg.wait_for_function("()=>NI.clash.beat===4", timeout=30000); pg.wait_for_timeout(500)
fr = A("new Promise(r=>{const o=NI_clashAt,d=NI_clDraw;window.__nc=0;NI_clashAt=function(){__nc++;return o.apply(this,arguments)};NI_clDraw=function(){__nc+=100;return d.apply(this,arguments)};setTimeout(()=>{NI_clashAt=o;NI_clDraw=d;r(__nc)},1500)})")
ck('nothing worked out or drawn while the playhead stands still', fr == 0, fr)
# the click card
R("(()=>{const p=document.querySelector('#mixWin svg.cabs .nicg .nich'),L=p.getTotalLength(),q=p.getPointAtLength(L/2),m=p.getScreenCTM(),x=q.x*m.a+q.y*m.c+m.e,y=q.x*m.b+q.y*m.d+m.f;window.__pt=[x,y]})()")
x, y = R("window.__pt"); z = R("ZOOM||1")
pg.mouse.move(x * z, y * z); pg.wait_for_timeout(150)
ck('hovering the clash lights its cable', R("document.querySelectorAll('#mixWin svg.cabs .nicg .nicc.hi').length") == 1)
pg.mouse.click(x * z, y * z); pg.wait_for_timeout(200)
pop = R("(()=>{const p=document.getElementById('niClashPop');return p?p.innerText:''})()")
ck('click: a card with both names, the band, the bar and both levels', 'Bass' in pop and 'Kick' in pop and 'Hz' in pop and 'bar 2' in pop and pop.count('dB') >= 3, pop)
pg.locator('#niClashPop').screenshot(path=os.path.join(OUT, 'ni5a_card.png'))
quiet = R("NI.clash.list[0].b.id")
R("document.querySelector('#niClashPop [data-nc=\"sel\"]').click()"); pg.wait_for_timeout(150)
ck('Select in the card selects the covered (quieter) channel and closes the card', R("selT") == quiet and not R("!!document.getElementById('niClashPop')"))
# Selected only
R("selectTrack(%s);mxsSet('cabSel',1);cabSoon();0" % json.dumps(al.tracks['Pad'])); pg.wait_for_timeout(700)
ck('Selected only with Pad selected: no clash (Pad clashes with nothing)', R("NI.clash.list.length") == 0, R("NI.clash.list.map(c=>c.a.name+'/'+c.b.name)"))
R("selectTrack(%s);cabSoon();0" % json.dumps(al.tracks['Kick'])); pg.wait_for_timeout(700)
ck('Selected only with Kick selected: the Bass and Kick clash', R("NI.clash.list.map(c=>[c.a.name,c.b.name].sort().join('/'))") == ['Bass/Kick'])
R("mxsSet('cabSel',0);cabSoon();0"); pg.wait_for_timeout(400)
# while playing it follows the playhead
R("pos=12;S.loop=false;toggle();0"); pg.wait_for_function("()=>NI.clash.beat>=16", timeout=30000); pg.wait_for_timeout(1200)
pl = R("[NI.clash.beat,NI.clash.list.length,NI.clash.meas]"); R("stop();0")
ck('while playing the clashes follow the playhead (past bar 5 the clash is gone)', pl[0] >= 16 and pl[1] == 0, pl)
# an edit is measured again: the bass now starts at bar 5, so at beat 4 nothing clashes
R("pos=4;0"); pg.wait_for_timeout(400)
R("(()=>{const t=S.tracks.find(t=>t.name==='Bass');pushUndo();t.clips[0].start=16;t.clips[0].len=16;changed(false)})()")
pg.wait_for_function("()=>NI.clash.beat===4&&!NI.clash.meas&&!NI.an.busy", timeout=120000); pg.wait_for_timeout(600)
ck('an edit (the bass moved to bar 5) is measured again: no clash at beat 4', R("NI.clash.list.length") == 0, R("NI.clash.list.map(c=>c.a.name+'/'+c.b.name)"))
R("undo();0"); pg.wait_for_function("()=>NI.clash.list.length===1", timeout=60000)
ck('undo brings the clash back (from the cache, nothing measured again)', R("NI.clash.list.length") == 1)
# switch off from the legend
R("document.querySelector('#mixWin .cablg .niclb').click()"); pg.wait_for_timeout(400)
ck('the legend switch turns it off: no clash cables, no check', R("!mxsO().niClash&&!document.querySelector('#mixWin svg.cabs .nicg')&&NI.clash.tm===0"))
ck('with Clashes off the normal cables are as before', R("document.querySelector('#mixWin svg.cabs .cfg').innerHTML") == cfg0)
R("document.querySelector('#mixWin .cablg .niclb').click()"); pg.wait_for_timeout(600)
ck('on again from the legend: the clash is back', R("NI.clash.tm>0&&NI.clash.list.length===1&&document.querySelectorAll('#mixWin svg.cabs .nicg .nicc').length===1"))
# Light level screenshot
R("UI.lite=true;UI.liteMan=true;applyLite();cabSoon();0"); pg.wait_for_timeout(600)
pg.locator('#mixWin').screenshot(path=os.path.join(OUT, 'ni5a_mixer_light.png'))
ck('at the Light level the clash cable is still drawn', R("document.querySelectorAll('#mixWin svg.cabs .nicg .nicc').length") == 1)
R("UI.lite=false;UI.liteMan=false;applyLite();0"); pg.wait_for_timeout(300)
c = R("""(()=>{const b=document.querySelector('#mixWin .cablg .niclb'),h=[...document.querySelectorAll('#mixWin svg.cabs .nicg .nich')];return{b:b.title,h:h.map(x=>x.querySelector('title')&&x.querySelector('title').textContent)}})()""")
ck('the switch and every clash cable have a tooltip', len(c['b']) > 40 and c['h'] and all(c['h']), c)
ck('no em dashes in tooltips or labels', '—' not in json.dumps(c) and '—' not in pop)
# closing the mixer stops the check
R("document.querySelector('#mixWin .fwc').click();0"); pg.wait_for_timeout(600)
ck('closing the mixer stops the check', R("NI.clash.tm") == 0, R("NI.clash.tm"))
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
blk = src[src.index('/* ===== lane D (task NI-5a)'):src.index('/* ===== end of lane D NI-5a')]
ck('no audio nodes or animation frames in the NI-5a block', not any(k in blk for k in ('createGain', 'createBiquad', 'audioWorklet', '.connect(', 'requestAnimationFrame')), '')
ck('no em dashes in the NI-5a block', '—' not in blk, '')
ck('no console errors', not al.errors, al.errors)
al.stop()
print('%d/%d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
