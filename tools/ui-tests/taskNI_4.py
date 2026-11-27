"""Task NI-4 (lane D): I1 frequency map of the whole song, the view.
Test song (audio tracks, 120 BPM, 44.1 kHz, 8 bars, sections Intro and Drop): Kick 50 Hz in bars 1 and 2 only, Pad 500 Hz all through,
Hat 8 kHz from bar 5. Checks: the command ni.freqMap opens the window and measures the song; the owner at a kick-only spot is Kick, at
500 Hz Pad, at 8 kHz Hat, silence where nothing plays; the cells there have the track's colour; clicking the kick-only spot moves the
playhead there and selects Kick; the hover read-out names bar, frequency and owner; the one-track layer (select and legend chip) shows the
rest in grey; colours by group; the playhead marker moves only while playing; nothing drawn per frame while open and stopped; an edit is
measured again in the background; closing stops its check; tooltips; no em dashes; inside the window; the Fractals demo partly measured
(screenshot, normal and Light level); no console errors. Screenshots go to the out dir.
  python3 tools/ui-tests/taskNI_4.py [repo dir] [out dir]"""
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

# 0. the Fractals demo, partly measured (the first 96 bars), for the screenshots
A("NI.an.ensure({b0:0,b1:384})")
R("NI_mapOpen();0"); pg.wait_for_timeout(1500)
pg.locator('#niMap').screenshot(path=os.path.join(OUT, 'ni4_fractals.png'))
R("UI.lite=true;UI.liteMan=true;applyLite();NI.map.draw();0"); pg.wait_for_timeout(500)
pg.locator('#niMap').screenshot(path=os.path.join(OUT, 'ni4_fractals_light.png'))
R("UI.lite=false;UI.liteMan=false;applyLite();0")
ck('Fractals: the map shows the measured part and says it is still measuring', 'Measuring' in R("document.querySelector('#niMap .nimst').textContent") or 'tracks' in R("document.querySelector('#niMap .nimst').textContent"), R("document.querySelector('#niMap .nimst').textContent"))
R("document.querySelector('#niMap .fwc').click();0"); pg.wait_for_timeout(300)
ck('closing the window stops its check and the measuring', R("NI.map.ph===0&&NI.an.q.length===0"), R("JSON.stringify(NI.an.status())"))

# 1. the test song
SR = 44100; BPM = 120; nb = 32; n = nb * SR // 2; t = np.arange(n) / SR
def st2(x): return np.vstack([x, x]).astype(np.float32)
kick = 0.6 * np.sin(2 * np.pi * 50 * t); kick[8 * SR // 2:] = 0
pad = 0.2 * np.sin(2 * np.pi * 500 * t)
hat = 0.1 * np.sin(2 * np.pi * 8000 * t); hat[:16 * SR // 2] = 0
B = {k: al.add_audio(st2(v), SR) for k, v in (('Kick', kick), ('Pad', pad), ('Hat', hat))}
COL = {'Kick': '#ff4d4d', 'Pad': '#4c8dff', 'Hat': '#3ecf8e'}
al.build({'bpm': BPM, 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'color': COL[k], 'clips': [{'start': 0, 'len': 32, 'name': k, 'buf': b}]} for k, b in B.items()]})
R("for(const[k,c] of Object.entries(%s)){const t=S.tracks.find(x=>x.name===k);t.color=c}S.sections=[{id:rid(),name:'Intro',start:0,len:16,color:'#4cc9f0'},{id:rid(),name:'Drop',start:16,len:16,color:'#ff6b6b'}];changed(true);stop();pos=0;0" % json.dumps(COL))
ck('the command ni.freqMap is in the commands list', R("SCM.has('ni.freqMap')&&!!SCM.get('ni.freqMap').l"))
R("SCM.get('ni.freqMap').run();0")
pg.wait_for_function("()=>NI.map.res&&!NI.map.res.cancelled&&NI.map.g&&NI.map.g.complete", timeout=120000); pg.wait_for_timeout(300)
st = R("document.querySelector('#niMap .nimst').textContent")
ck('the window opens and the song is measured: 3 tracks, 32 beats', st.startswith('3 tracks') and '32 beats' in st, st)
band = lambda f: int(round(6 * math.log2(f / 20)))
own = lambda b, f: R("NI.map.own(%d,%d).map(o=>o.name)" % (b, band(f)))
ck('beat 4 at 50 Hz: Kick owns it', own(4, 50)[:1] == ['Kick'], own(4, 50))
ck('beat 20 at 50 Hz: nothing (the kick stops after bar 2)', own(20, 50) == [], own(20, 50))
ck('beat 20 at 500 Hz: Pad; at 8 kHz: Hat', own(20, 500)[:1] == ['Pad'] and own(20, 8000)[:1] == ['Hat'], (own(20, 500), own(20, 8000)))
PIX = """((b,f)=>{const M=NI.map,G=M.geo,cv=M.w.querySelector('canvas'),x=G.x0+(b+.5)/G.nb*G.pw,y=G.FY(f),g=cv.getContext('2d'),sx=cv.width/G.W,sy=cv.height/G.H,d=g.getImageData(Math.round(x*sx),Math.round(y*sy),1,1).data;return[d[0],d[1],d[2]]})(%d,%g)"""
def pix(b, f): return R(PIX % (b, f))
def hue_like(p, hexc):
    c = [int(hexc[i:i + 2], 16) for i in (1, 3, 5)]; m = max(p) or 1; cm = max(c)
    return all(abs(p[i] / m - c[i] / cm) < .2 for i in range(3)) and max(p) > 40
kp = pix(4, 50); pp = pix(20, 500); hp = pix(20, 8000); sp = pix(20, 50)
ck('cells in the owner\'s colour: kick spot red, pad spot blue, hat spot green', hue_like(kp, COL['Kick']) and hue_like(pp, COL['Pad']) and hue_like(hp, COL['Hat']), (kp, pp, hp))
ck('a silent cell is dark', max(sp) < 20, sp)
pg.screenshot(path=os.path.join(OUT, 'ni4_window.png'))
pg.locator('#niMap').screenshot(path=os.path.join(OUT, 'ni4_test_song.png'))
# hover and click
box = pg.locator('#niMap canvas').bounding_box(); G = R("JSON.parse(JSON.stringify(NI.map.geo))")
def css(b, f): return (box['x'] + (G['x0'] + (b + .5) / G['nb'] * G['pw']) * box['width'] / G['W'], box['y'] + R("NI.map.geo.FY(%g)" % f) * box['height'] / G['H'])
x, y = css(4, 50); pg.mouse.move(x, y); pg.wait_for_timeout(100)
ro = R("document.querySelector('#niMap .nimro').textContent"); print('    hover:', ro)
ck('hover read-out: bar 2.1, the frequency with Hz and the note, Kick with its level', ro.startswith('bar 2.1') and 'Hz' in ro and 'Kick' in ro and 'dB' in ro, ro)
pg.mouse.click(x, y); pg.wait_for_timeout(200)
ck('click on the kick-only spot: playhead at beat 4, Kick selected', R("pos") == 4 and R("selT") == al.tracks['Kick'], (R("pos"), R("selT"), al.tracks['Kick']))
# the layer
R("(()=>{const s=document.querySelector('#niMap [data-nm=\"layer\"]');s.value=%s;s.dispatchEvent(new Event('change'))})()" % json.dumps(al.tracks['Pad'])); pg.wait_for_timeout(150)
kp2 = pix(4, 50); pp2 = pix(20, 500)
ck('layer Pad: the kick spot is grey, the pad glows in its colour', abs(kp2[0] - kp2[1]) < 6 and abs(kp2[1] - kp2[2]) < 6 and hue_like(pp2, COL['Pad']), (kp2, pp2))
pg.locator('#niMap').screenshot(path=os.path.join(OUT, 'ni4_layer.png'))
R("[...document.querySelectorAll('#niMap .nimlg button')].find(b=>b.dataset.id===%s).click()" % json.dumps(al.tracks['Pad'])); pg.wait_for_timeout(100)
ck('clicking the chosen legend chip again shows all tracks', R("NI.map.layer") == '', R("NI.map.layer"))
lg = R("[...document.querySelectorAll('#niMap .nimlg button')].map(b=>b.textContent)")
cn = R("(()=>{const G=NI.map.g;return G.L.map((t,i)=>[t.name,G.cnt[i]]).filter(x=>x[1]>0).sort((a,b)=>b[1]-a[1]).map(x=>x[0])})()")
ck('the legend lists the three owners, most spots (over -60 dB) first', sorted(lg) == ['Hat', 'Kick', 'Pad'] and lg == cn, (lg, cn))
# colours by group
R("(()=>{const g=mkTrack('group',null,'Drums','#f5c84c');S.tracks.unshift(g);S.tracks.find(t=>t.name==='Kick').grp=g.id;changed(true)})();0")
r0g = R("NI.an.stats.renders")
pg.wait_for_timeout(1800); pg.wait_for_function("()=>!NI.an.busy&&NI.map.g&&NI.map.g.complete", timeout=60000)
R("(()=>{const s=document.querySelector('#niMap [data-nm=\"col\"]');s.value='grp';s.dispatchEvent(new Event('change'))})()"); pg.wait_for_timeout(200)
ck('putting Kick in a group does not measure anything again', R("NI.an.stats.renders") == r0g, R("NI.an.stats.renders") - r0g)
ck('colours by group: the kick spot takes the Drums group colour, the pad keeps its own', hue_like(pix(4, 50), '#f5c84c') and hue_like(pix(20, 500), COL['Pad']), (pix(4, 50), pix(20, 500)))
lg2 = R("[...document.querySelectorAll('#niMap .nimlg button')].map(b=>b.textContent)")
ck('by group the legend lists the group (Drums) and the ungrouped tracks', sorted(lg2) == ['Drums', 'Hat', 'Pad'], lg2)
gid = R("S.tracks.find(t=>t.name==='Drums').id")
R("(()=>{const s=document.querySelector('#niMap [data-nm=\"layer\"]');s.value=%s;s.dispatchEvent(new Event('change'))})()" % json.dumps(gid)); pg.wait_for_timeout(150)
ck('layer Drums (a group): its kick glows in the group colour, the pad is grey', hue_like(pix(4, 50), '#f5c84c') and abs(pix(20, 500)[0] - pix(20, 500)[2]) < 6, (pix(4, 50), pix(20, 500)))
pg.locator('#niMap').screenshot(path=os.path.join(OUT, 'ni4_group_layer.png'))
x, y = css(4, 50); pg.mouse.click(x, y); pg.wait_for_timeout(150)
ck('with a group layer a click selects the group track that sounds there (Kick)', R("selT") == al.tracks['Kick'], R("selT"))
R("(()=>{const s=document.querySelector('#niMap [data-nm=\"layer\"]');s.value='';s.dispatchEvent(new Event('change'))})()")
R("(()=>{const s=document.querySelector('#niMap [data-nm=\"col\"]');s.value='auto';s.dispatchEvent(new Event('change'))})()")
bl = R("NI.map.geo.step")
ck('bar numbers every bar when there is room (8 bars)', bl == 1, bl)
# nothing per frame, the playhead marker
pg.wait_for_timeout(1500)
fr = A("new Promise(r=>{const o=NI_mapDraw;window.__nd=0;NI_mapDraw=function(){__nd++;return o.apply(this,arguments)};setTimeout(()=>{NI_mapDraw=o;r(__nd)},1500)})")
ck('nothing drawn while open and stopped', fr == 0, fr)
ck('the playhead marker is hidden while stopped', R("document.querySelector('#niMap .nimph').hidden"))
R("pos=8;S.loop=false;toggle();0"); pg.wait_for_timeout(1200)
l1 = R("parseFloat(document.querySelector('#niMap .nimph').style.left)"); vis = not R("document.querySelector('#niMap .nimph').hidden")
fr2 = A("new Promise(r=>{const o=NI_mapDraw;window.__nd=0;NI_mapDraw=function(){__nd++;return o.apply(this,arguments)};setTimeout(()=>{NI_mapDraw=o;r(__nd)},1000)})")
l2 = R("parseFloat(document.querySelector('#niMap .nimph').style.left)"); R("stop();0")
ck('while playing the marker shows and moves, without redrawing the map', vis and l2 > l1 and fr2 == 0, (l1, l2, fr2))
# an edit is measured again
r0 = R("NI.an.stats.renders")
R("(()=>{const t=S.tracks.find(t=>t.name==='Hat');t.clips[0].len=24;changed(false)})()")
pg.wait_for_function("r=>NI.an.stats.renders>r&&!NI.an.busy&&NI.map.g&&NI.map.g.complete", arg=r0, timeout=60000); pg.wait_for_timeout(1200)
ck('an edit (Hat ends at bar 7) is measured again: beat 28 at 8 kHz is now silent', own(28, 8000) == [] and own(20, 8000)[:1] == ['Hat'], (own(28, 8000), R("NI.an.stats.renders") - r0))
c = R("""(()=>{const W=document.getElementById('niMap'),b=W.getBoundingClientRect();return{untitled:[...W.querySelectorAll('button,select,canvas,label')].filter(x=>!x.hidden&&!x.title&&!x.dataset.tip&&!x.closest('label[title]')&&!x.getAttribute('aria-label')).map(x=>x.outerHTML.slice(0,70)),text:W.innerText,rect:[b.left,b.top,b.right,b.bottom],vw:innerWidth,vh:innerHeight}})()""")
ck('every control has a tooltip', not c['untitled'], c['untitled'])
ck('no em dashes in the window', '—' not in c['text'], '')
ck('the window is inside the app', c['rect'][0] >= 0 and c['rect'][1] >= 0 and c['rect'][2] <= c['vw'] and c['rect'][3] <= c['vh'], c['rect'])
R("document.querySelector('#niMap .fwc').click();0"); pg.wait_for_timeout(300)
ck('closed: no check left running', R("NI.map.ph===0&&NI.map.w.hidden"))
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
blk = src[src.index('/* ===== lane D (task NI-4)'):src.index('/* ===== end of lane D NI-4')]
ck('no audio nodes or animation frames in the NI-4 block', not any(k in blk for k in ('createGain', 'createBiquad', 'audioWorklet', '.connect(', 'requestAnimationFrame')), '')
ck('no em dashes in the NI-4 block', '—' not in blk, '')
ck('no console errors', not al.errors, al.errors)
al.stop()
print('%d/%d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
