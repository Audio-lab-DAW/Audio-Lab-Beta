"""Task NI-6 (lane D): I6 energy arc.
Test song (audio tracks, 120 BPM, 44.1 kHz, 16 bars, sections Intro, Drop, Break, Drop 2): Pad 500 Hz all through (quiet), Kick 55 Hz,
Bass 110 Hz and Hat 8 kHz in the two drops only, nothing but the Pad in the intro and the break. Checks: off by default (no lane, no
height); the command ni.energyArc shows it under the sections and measures the song; the break dips (energy, loudness, tracks playing);
loudness of a one-track beat equals that track's own NI-3 loudness, of a four-track beat their power sum; brightness of a pad-only beat
near 500 Hz; the typical arc follows the section names (break 0.4, drop 0.95); pointing draws the read-out and the ingredients (pixels),
with the tooltip; a click moves the playhead and selects nothing; the right-click menu changes the comparison; nothing drawn or worked
out while idle; an edit re-measures only the edited track after it settles; with the tempo lane both lanes stack and the tempo lane keeps
its 44 px; hiding removes the lane and cancels the measuring; no project field; no em dashes; the Fractals demo partly measured
(screenshots normal and Light level); no console errors. Screenshots go to the out dir.
  python3 tools/ui-tests/taskNI_6.py [repo dir] [out dir]"""
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
al = AudioLab(os.path.join(ROOT, 'index.html')); al.start(); pg = al.page; R = al.run
pg.set_default_timeout(600000)
print('version', al.version)
def A(expr): return pg.evaluate("c=>AudioLab.run(c)", "(async()=>{const r=await %s;return JSON.parse(JSON.stringify(r===undefined?null:r))})()" % expr)
def shot_arr(name):
    R("dirty=true;0"); pg.wait_for_timeout(250)
    box = pg.locator('#arr').bounding_box(); y = R("NI_arcY()") if R("!!UI.niArc") else 60
    sc = box['height'] / R("arr.height/((devicePixelRatio||1)*ZOOM)")
    pg.screenshot(path=os.path.join(OUT, name), clip={'x': box['x'], 'y': box['y'], 'width': box['width'], 'height': min(box['height'], (y + 40) * sc + 140)})

# 0. defaults
ck('off by default: no lane, no height', not R("!!UI.niArc") and R("NI_arcH()") == 0 and R("TMPH()") == 0)
ck('the command ni.energyArc is in the commands list', R("SCM.has('ni.energyArc')&&!!SCM.get('ni.energyArc').l"))
ck('three settings rows in the S4 shape', R("NI_SETTINGS.filter(r=>r.id.startsWith('ni.energyArc')&&r.label&&r.page&&r.block&&r.scope&&'default' in r&&r.help&&r.search.length).length") == 3)

# 1. the Fractals demo, partly measured, for the screenshots
A("NI.an.ensure({b0:0,b1:256})")
R("NI_arcShow(true);0"); pg.wait_for_timeout(2500)
shot_arr('ni6_fractals.png')
R("UI.lite=true;UI.liteMan=true;applyLite();0"); pg.wait_for_timeout(300); shot_arr('ni6_fractals_light.png')
R("UI.lite=false;UI.liteMan=false;applyLite();0")
ck('Fractals: the arc shows the measured part (some energy) and says it is still measuring or done', R("(()=>{const d=NI.arc.data();let n=0;for(let b=0;b<256;b++)if(d.E[b]>0)n++;return n>100})()"), R("(()=>{const d=NI.arc.data();return d.all+' pieces, '+d.left+' left'})()"))
R("NI_arcShow(false);0"); pg.wait_for_timeout(200)
ck('hiding the arc cancels the measuring', R("NI.an.q.length===0&&NI_arcH()===0"), R("JSON.stringify(NI.an.status())"))

# 2. the test song
SR = 44100; BPM = 120; nb = 64; n = nb * SR // 2; t = np.arange(n) / SR
def st2(x): return np.vstack([x, x]).astype(np.float32)
drop = np.zeros(n); spb = SR // 2
drop[16 * spb:32 * spb] = 1; drop[48 * spb:64 * spb] = 1
TR = {'Pad': 0.08 * np.sin(2 * np.pi * 500 * t), 'Kick': 0.5 * np.sin(2 * np.pi * 55 * t) * drop,
      'Bass': 0.3 * np.sin(2 * np.pi * 110 * t) * drop, 'Hat': 0.1 * np.sin(2 * np.pi * 8000 * t) * drop}
B = {k: al.add_audio(st2(v), SR) for k, v in TR.items()}
al.build({'bpm': BPM, 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'clips': [{'start': 0, 'len': 64, 'name': k, 'buf': b}]} for k, b in B.items()]})
R("S.sections=[['Intro',0,'#4cc9f0'],['Drop',16,'#ff6b6b'],['Break',32,'#b583ff'],['Drop 2',48,'#ff6b6b']].map(([n,s,c])=>({id:rid(),name:n,start:s,len:16,color:c}));changed(true);stop();pos=0;V.x=-2;V.ppb=arrW/70;dirty=true;0")
ay0 = R("(drawArr(),AY)")
R("SCM.get('ni.energyArc').run();0")
ck('the command shows the lane: 40 px more above the tracks', R("!!UI.niArc") and R("(drawArr(),AY)") == ay0 + 40, (ay0, R("AY")))
pg.wait_for_function("()=>{const d=NI.arc.data();return NI.arc.res&&d.complete&&d.nb===64}", timeout=180000); pg.wait_for_timeout(300)
d = R("(()=>{const d=NI.arc.data();const f=a=>Array.from(a);return{E:f(d.E),lu:f(d.lu),dn:f(d.dn),br:f(d.br),nT:d.nT,cmp:d.cmp?f(d.cmp):null,how:d.cmp&&d.cmp.how}})()")
mean = lambda a, i, j: sum(a[i:j]) / (j - i)
eD, eB, eI = mean(d['E'], 20, 28), mean(d['E'], 36, 44), mean(d['E'], 4, 12)
print('    energy intro %.2f, drop %.2f, break %.2f, drop 2 %.2f' % (eI, eD, eB, mean(d['E'], 52, 60)))
ck('the break dips: energy at least 0.25 under the drop, and the second drop comes back', eB < eD - .25 and abs(mean(d['E'], 52, 60) - eD) < .03, (eD, eB))
ck('tracks playing: 4 of 4 in the drop, 1 of 4 in the break', d['nT'] == 4 and abs(d['dn'][24] - 1) < .01 and abs(d['dn'][40] - .25) < .01, (d['dn'][24], d['dn'][40]))
# loudness against NI-3's own numbers per track
own = R("(()=>{const o={};for(const t of NI_anTracks()){const a=[24,40].map(b=>{let p=0,m=0;for(let i=b-2;i<=b+1;i++){const r=NI.an.get(t,i);m++;if(r&&r.play)p+=Math.pow(10,(r.loud+.691)/10)}return p});o[t.name]=a}return o})()")
l24 = 10 * math.log10(sum(v[0] for v in own.values()) / 4) - .691; l40 = 10 * math.log10(own['Pad'][1] / 4) - .691
ck('loudness of a pad-only beat = the Pad\'s own loudness; of a drop beat = the four tracks\' power sum (within 0.05 dB)', abs(d['lu'][40] - l40) < .05 and abs(d['lu'][24] - l24) < .05, (round(d['lu'][40], 2), round(l40, 2), round(d['lu'][24], 2), round(l24, 2)))
ck('the break is quieter than the drop by more than 10 dB', d['lu'][24] - d['lu'][40] > 10, (d['lu'][24], d['lu'][40]))
ck('brightness of a pad-only beat near 500 Hz (within 15%)', abs(d['br'][40] / 500 - 1) < .15, d['br'][40])
ck('typical arc from the section names: break 0.40, drop 0.95, intro rising', d['how'] == 'sections' and abs(d['cmp'][40] - .4) < .01 and abs(d['cmp'][24] - .95) < .01 and d['cmp'][2] < d['cmp'][14], (d['how'], d['cmp'][40], d['cmp'][24]))
shot_arr('ni6_song.png')

# pointing
box = pg.locator('#arr').bounding_box(); sc = box['height'] / R("arr.height/((devicePixelRatio||1)*ZOOM)")
def at(b): return (box['x'] + R("X0+(%g-V.x)*V.ppb" % (b + .5)) * sc, box['y'] + (R("NI_arcY()") + 20) * sc)
PIX = "((x,y)=>{const d=(devicePixelRatio||1)*ZOOM,p=arr.getContext('2d').getImageData(Math.round(x*d),Math.round(y*d),1,1).data;return[p[0],p[1],p[2]]})(%g,%g)"
d0 = R("NI.arc.draws")
x, y = at(40); pg.mouse.move(x, y); pg.wait_for_timeout(250)
ck('pointing at beat 40: the read-out and a redraw, the tooltip says what energy is', R("NI.arc.hov") == 40 and R("NI.arc.draws") > d0 and 'Energy arc' in (R("arr.title") or ''), (R("NI.arc.hov"), R("arr.title")[:40]))
# the cyan loudness line drawn while pointing: look for a cyan pixel in the lane at beat 24
cy = R("(()=>{const y0=NI_arcY(),x=X0+(24.5-V.x)*V.ppb;for(let y=y0+2;y<y0+38;y++){const d=(devicePixelRatio||1)*ZOOM,p=arr.getContext('2d').getImageData(Math.round(x*d),Math.round(y*d),1,1).data;if(p[2]>180&&p[1]>150&&p[0]<140)return true}return false})()")
ck('the three ingredients drawn while pointing (a cyan loudness line at beat 24)', cy)
shot_arr('ni6_hover.png')
pg.mouse.move(box['x'] + 400, box['y'] + box['height'] - 40); pg.wait_for_timeout(200)
ck('pointer away: the read-out goes, the tooltip is removed', R("NI.arc.hov") == -1 and not R("arr.getAttribute('title')"))
cy2 = R("(()=>{const y0=NI_arcY(),x=X0+(24.5-V.x)*V.ppb;for(let y=y0+2;y<y0+38;y++){const d=(devicePixelRatio||1)*ZOOM,p=arr.getContext('2d').getImageData(Math.round(x*d),Math.round(y*d),1,1).data;if(p[2]>180&&p[1]>150&&p[0]<140)return true}return false})()")
ck('the ingredients are not drawn when not pointing (default)', not cy2)
# click
sel0 = R("selT"); x, y = at(24); pg.mouse.click(x, y); pg.wait_for_timeout(200)
ck('click in the lane: playhead at beat 24, the selection unchanged', R("pos") == 24 and R("selT") == sel0, (R("pos"), R("selT"), sel0))
# right-click menu
pg.mouse.click(x, y, button='right'); pg.wait_for_timeout(200)
ck('right-click: the energy arc menu', 'Energy arc: compare with' in R("ctxm.hidden?'':ctxm.textContent"))
tips = R("[...ctxm.querySelectorAll('.mchips button')].map(b=>b.title+' '+b.textContent+' '+b.disabled)")
ck('compare chips with tooltips; the reference chip is off until reference tracks exist', len(tips) == 3 and 'True' not in tips[0] and tips[2].endswith('true'), tips)
R("[...ctxm.querySelectorAll('.mchips button')][0].click();0"); pg.wait_for_timeout(200)
ck('compare with Nothing: no comparison curve', R("UI.niArcCmp") == 'none' and R("NI.arc.data().cmp===null"))
R("NI.arc.setRef({name:'Ref A',at:f=>f});NI_arcCmp('ref');0")
ck('a reference given by another lane (NI.arc.setRef) is drawn as the comparison', R("(()=>{const c=NI.arc.data().cmp;return!!c&&Math.abs(c[63]-63.5/64)<1e-6})()"))
R("NI.arc.setRef(null);NI_arcCmp('typ');0")
ck('reference taken away: back to the typical arc', R("UI.niArcCmp") == 'typ' and R("!!NI.arc.data().cmp"))
R("ctxm.hidden=true;0")
# generic arc without known section names
R("S.sections[1].name='Part 2';NI.arc.stale=true;0")
ck('a section without a known name: the generic arc over the song length', R("NI.arc.data().cmp.how") == 'length')
R("S.sections[1].name='Drop';NI.arc.stale=true;dirty=true;0")

# idle: nothing drawn, nothing worked out
pg.wait_for_timeout(1500); dr, cl = R("NI.arc.draws"), R("NI.arc.calcs"); pg.wait_for_timeout(2000)
ck('idle 2 s: the arc is not drawn or worked out again', R("NI.arc.draws") == dr and R("NI.arc.calcs") == cl, (R("NI.arc.draws") - dr, R("NI.arc.calcs") - cl))

# an edit: only the edited track is measured again
r0 = R("NI.an.status().renders"); tk0 = R("NI.arc.tok")
R("(()=>{pushUndo();const t=S.tracks.find(x=>x.name==='Hat');t.vol=0.5;changed(false);dirty=true})();0")
pg.wait_for_timeout(400); ck('right after an edit nothing is measured yet (it waits for the edit to settle)', R("NI.an.status().renders") == r0)
pg.wait_for_function("()=>NI.arc.tok>%d&&!NI.arc.et&&NI.arc.pend===''&&NI.arc.data().complete&&!NI.an.busy&&!NI.an.q.length" % tk0, timeout=120000); pg.wait_for_timeout(300)
ck('after the edit: only the Hat\'s 3 pieces measured again', R("NI.an.status().renders") - r0 == 3, R("NI.an.status().renders") - r0)

# with the tempo lane
R("tempoLaneShow(true);drawArr();0")
ck('tempo lane and arc stacked: 84 px, the tempo lane keeps 44 px, the arc under it', R("TMPH()") == 84 and R("tmpGeo().h") == 44 and R("NI_arcY()") == R("TY+RUL+SECH+44"))
ck('a point in the arc is not taken by the tempo lane', R("tmpHit(X0+50,NI_arcY()+20)") is None)
shot_arr('ni6_tempo.png')
R("tempoLaneShow(false);0")

# the switch in the section row's menu
R("secMenu(200,200,%g);0" % 200)
ck('the section row\'s menu offers "Hide the energy arc"', 'Hide the energy arc' in R("ctxm.textContent"))
R("ctxm.hidden=true;0")

# no project field, no em dashes
ck('nothing stored in the project', not any(k.startswith('ni_arc') or k == 'niArc' for k in R("Object.keys(S)")))
txt = R("NI_ARC_TIP+JSON.stringify(NI_SETTINGS)+String(NI_arcMenu)+String(NI_arcDraw)")
ck('no em dashes in the new UI text', '—' not in txt)

R("NI_arcShow(false);drawArr();0")
ck('hidden: the lane and its height are gone, the measuring stopped', R("AY") == ay0 and R("NI.an.q.length") == 0, (R("AY"), ay0))
ck('no console errors', not al.errors, al.errors[:3])
al.stop()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
