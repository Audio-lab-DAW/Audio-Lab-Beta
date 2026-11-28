"""Task NI-10a (lane D): I7 draw the arc, part 1.
Test song (NI-6's: audio, 120 BPM, 64 beats, sections Intro, Drop, Break, Drop 2): Pad 500 Hz all through (quiet); Kick 55 Hz, Bass
110 Hz and Hat 8 kHz only in the drops (beats 16 to 32 and 48 to 64). The break (bars 9 to 12) dips.
Checks: the command and the lane's menu; an old project (no S.ni_arc) loads with no line and nothing marked; a line drawn with the mouse
in draw mode is one undo step and follows the pointer; a flat line at the drops' energy over beats 16 to 64 marks exactly the break
(bars 9 to 12, edges within a bar) with the dB the gap stands for (computed from the measured energy, within 1 dB), and nothing in
the drops; the toast and the menu say it; a line drawn under the song marks nothing; Alt-drag erases; Undo removes a stroke; Clear;
the line is saved with the song (S.ni_arc v1) and comes back after a save and reopen; Esc ends drawing; while idle nothing is drawn
again; a render the same with and without a line (within 1e-6); screenshots (the lane with the line and the shortfall, the Light level);
no em dashes; no console errors.
  python3 tools/ui-tests/taskNI_10a.py [repo dir] [out dir]"""
# for: task NI-10a (lane D)
import sys, os, hashlib, re, json
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
def shot_arr(name):
    R("dirty=true;0"); pg.wait_for_timeout(250)
    box = pg.locator('#arr').bounding_box(); y = R("NI_arcY()")
    sc = box['height'] / R("arr.height/((devicePixelRatio||1)*ZOOM)")
    pg.screenshot(path=os.path.join(OUT, name), clip={'x': box['x'], 'y': box['y'], 'width': box['width'], 'height': min(box['height'], (y + 40) * sc + 60)})

ck('the command ni.drawArc is in the commands list', R("SCM.has('ni.drawArc')&&!!SCM.get('ni.drawArc').l"))
ck('the energy lane\'s menu has Draw your line', R("NI_alMenuItems().some(i=>i.label==='Draw your line…')"))

SR = 44100; BPM = 120; nb = 64; n = nb * SR // 2; t = np.arange(n) / SR
st2 = lambda x: np.vstack([x, x]).astype(np.float32)
drop = np.zeros(n); spb = SR // 2; drop[16 * spb:32 * spb] = 1; drop[48 * spb:64 * spb] = 1
TR = {'Pad': 0.08 * np.sin(2 * np.pi * 500 * t), 'Kick': 0.5 * np.sin(2 * np.pi * 55 * t) * drop,
      'Bass': 0.3 * np.sin(2 * np.pi * 110 * t) * drop, 'Hat': 0.1 * np.sin(2 * np.pi * 8000 * t) * drop}
B = {k: al.add_audio(st2(v), SR) for k, v in TR.items()}
al.build({'bpm': BPM, 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'clips': [{'start': 0, 'len': 64, 'name': k, 'buf': b}]} for k, b in B.items()]})
R("S.sections=[['Intro',0,'#4cc9f0'],['Drop',16,'#ff6b6b'],['Break',32,'#b583ff'],['Drop 2',48,'#ff6b6b']].map(([n,s,c])=>({id:rid(),name:n,start:s,len:16,color:c}));UNDO.length=0;changed(true);stop();pos=0;V.x=-2;V.ppb=arrW/70;dirty=true;0")
ck('a project without the key: no line, nothing marked', R("S.ni_arc===undefined&&NI_alLine()===null&&NI_alShort().length===0&&!NI_alHas()"))
R("SCM.get('ni.drawArc').run();0")
ck('the command turns on the energy lane and draw mode', R("!!UI.niArc&&NI.al.draw"))
pg.wait_for_function("()=>{const d=NI.arc.data();return NI.arc.res&&d.complete&&d.nb===64}", timeout=180000); pg.wait_for_timeout(300)
d = R("(()=>{const d=NI.arc.data();return{E:Array.from(d.E)}})()"); E = d['E']
x0, _ = al.render(b0=0, b1=32); h0 = hashlib.md5(x0.tobytes()).hexdigest()
eD = sum(E[20:28]) / 8; eB = sum(E[36:44]) / 8
print('    energy drop %.3f, break %.3f' % (eD, eB))

# drawing with the mouse
box = pg.locator('#arr').bounding_box(); sc = box['height'] / R("arr.height/((devicePixelRatio||1)*ZOOM)")
def at(b, v): return (box['x'] + R("X0+(%g-V.x)*V.ppb" % b) * sc, box['y'] + R("NI_arcY()+5+(1-%g)*(%d-10)" % (v, 40)) * sc)
u0 = R("UNDO.length")
x, y = at(16.2, .3); pg.mouse.move(x, y); pg.mouse.down()
for b in range(17, 64, 3):
    x, y = at(b + .2, .3 + .5 * (b - 16) / 48); pg.mouse.move(x, y)
x, y = at(63.6, .8); pg.mouse.move(x, y); pg.mouse.up(); pg.wait_for_timeout(200)
L = R("NI_alLine()")
ck('a stroke is one undo step', R("UNDO.length") == u0 + 1, (u0, R("UNDO.length")))
ck('the line follows the pointer: beats 16 to 63 drawn, rising from 0.3 to 0.8 (within 0.03)', L is not None and L[15] is None and all(L[b] is not None for b in range(16, 64)) and abs(L[16] - .3) < .03 and abs(L[63] - .8) < .03 and abs(L[40] - .55) < .04, (L[14:18] if L else None, L[40] if L else None, L[-1] if L else None))
ck('the playhead did not move while drawing', R("pos") == 0)
R("undo();0"); pg.wait_for_timeout(100)
ck('Undo removes the stroke', R("NI_alLine()===null&&S.ni_arc===undefined"))

# a flat line at the drops' energy over beats 16 to 64
R("(()=>{pushUndo();NI_alSet(16,64,%g,%g);changed(false);dirty=true})();0" % (eD, eD))
sh = R("NI_alShort()")
print('    shortfall:', [(s['bar0'], s['bar1'], s['db'], round(s['gap'], 3), s['txt']) for s in sh])
ck('exactly one stretch: the break, bars 9 to 12 (edges within a bar)', len(sh) == 1 and sh[0]['bar0'] in (8, 9) and sh[0]['bar1'] in (12, 13), [(s['bar0'], s['bar1']) for s in sh])
if sh:
    s0 = sh[0]; g = sum(max(0, eD - E[b]) for b in range(s0['b0'], s0['b1'])) / (s0['b1'] - s0['b0']); db = round(g / .55 * 30)
    ck('its dB is the measured gap (energy / 0.55 x 30 dB), within 1 dB', abs(s0['db'] - db) <= 1 and s0['db'] >= 10, (s0['db'], db))
    ck('in words: "bars 9 to 12 sit about N dB under your line"', re.fullmatch(r'bars \d+ to \d+ sit about \d+ dB under your line', s0['txt']) is not None, s0['txt'])
ck('the lane\'s menu lists the stretch and Clear your line', R("(()=>{const L=NI_alMenuItems().map(i=>i.label||'');return L.some(l=>/^Bars \\d+ to \\d+ sit about/.test(l))&&L.includes('Clear your line')&&L.includes('Stop drawing your line')})()"))
R("NI_alMenuItems().find(i=>/^Bars/.test(i.label||'')).act();0")
ck('a stretch in the menu moves the playhead to it', R("pos") == sh[0]['b0'] if sh else False, R("pos"))
ck('what the toast says', R("NI_alSay()").startswith(sh[0]['txt']) if sh else False, R("NI_alSay()"))
R("pos=0;V.x=-2;dirty=true;0")
shot_arr('ni10a_song.png')
R("UI.lite=true;UI.liteMan=true;applyLite();0"); pg.wait_for_timeout(300); shot_arr('ni10a_song_light.png')
R("UI.lite=false;UI.liteMan=false;applyLite();0")
# red pixels in the break, none in the drop
PIX = "((x,y)=>{const d=(devicePixelRatio||1)*ZOOM,p=arr.getContext('2d').getImageData(Math.round(x*d),Math.round(y*d),1,1).data;return[p[0],p[1],p[2]]})(X0+(%g-V.x)*V.ppb,NI_arcY()+5+(1-%g)*30)"
R("dirty=true;0"); pg.wait_for_timeout(200)
mid = (eD + eB) / 2
pb, pa = R(PIX % (40.5, mid)), R(PIX % (24.5, min(.97, eD + .15)))
keep = R("JSON.stringify(S.ni_arc)"); R("delete S.ni_arc;NI.al.shKey='';dirty=true;0"); pg.wait_for_timeout(200)
p0 = R(PIX % (40.5, mid)); R("S.ni_arc=JSON.parse(%s);NI.al.shKey='';dirty=true;0" % json.dumps(keep)); pg.wait_for_timeout(200)
ck('the break is shaded red between the line and the energy; above the drop nothing red', pb[0] - p0[0] > 30 and pb[0] > pb[1] + 30 and pa[0] < 60, (pb, p0, pa))
# idle
pg.wait_for_timeout(500); d1 = R("NI.arc.draws"); pg.wait_for_timeout(2000)
ck('idle 2 s: the lane is not drawn again', R("NI.arc.draws") == d1, (d1, R("NI.arc.draws")))

# Alt-drag erases
u0 = R("UNDO.length")
x, y = at(56.2, .5); pg.keyboard.down('Alt'); pg.mouse.move(x, y); pg.mouse.down()
x, y = at(63.8, .5); pg.mouse.move(x, y); pg.mouse.up(); pg.keyboard.up('Alt'); pg.wait_for_timeout(200)
L = R("NI_alLine()")
ck('Alt-drag erases beats 56 to 63, one undo step', L is not None and len(L) == 56 and L[55] is not None and R("UNDO.length") == u0 + 1, (len(L) if L else None))

# saved with the song
pj = R("JSON.parse(JSON.stringify(S.ni_arc))")
R("restore(undoSnap());0"); pg.wait_for_timeout(200)
ck('the line is in the saved song (S.ni_arc v1) and comes back after a reopen', pj['v'] == 1 and R("JSON.stringify(S.ni_arc)") == json.dumps(pj, separators=(',', ':')), pj['v'])

# a line under the song marks nothing
R("(()=>{pushUndo();delete S.ni_arc;NI_alSet(0,64,.05,.05);changed(false)})();0")
ck('a line under the song marks nothing', R("NI_alShort().length") == 0 and R("NI_alSay()") == 'The song reaches your line everywhere it is drawn.', R("NI_alShort()"))
R("NI_alClear();0")
ck('Clear removes the line (one undo step brings it back)', R("S.ni_arc===undefined") and (R("undo(),!!NI_alLine()")))

# Esc ends drawing
pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
ck('Esc ends draw mode', not R("NI.al.draw"))
x1, _ = al.render(b0=0, b1=32)
keep = R("JSON.stringify(S.ni_arc)"); R("delete S.ni_arc;0"); x2, _ = al.render(b0=0, b1=32); R("S.ni_arc=JSON.parse(%s);0" % json.dumps(keep))
x3, _ = al.render(b0=0, b1=32)
dd = [float(np.abs(a - b).max()) for a, b in ((x1, x2), (x2, x3), (x1, x0))]
print('    renders: largest differences', dd, '(the same song renders a few last-bit apart between runs, with or without a line)')
ck('a render is the same with and without the line (within 1e-6, the last-bit spread of repeated renders)', keep != 'null' and max(dd) < 1e-6, dd)
ck('no em dashes in the new UI text', '—' not in R("String(NI_alDraw)+String(NI_alSay)+String(NI_alMenuItems)+String(NI_alMode)+String(NI_alShort)+String(NI_alClear)"))
ck('no console errors', not al.errors, al.errors[:3])
al.stop()
print('%d of %d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
