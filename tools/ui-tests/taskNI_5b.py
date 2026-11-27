"""Task NI-5b (lane D): I12 masking cables, part 2: the fixes.
Test song (audio, 120 BPM, 44.1 kHz, 8 bars): Kick 106 Hz (louder), Bass 100 Hz plus 1 kHz (quieter at 100 Hz: the covered one), Pad 3 kHz
(untouched). Checks (research section 5, NF5): the card offers two fixes with tooltips; Notch: one undo step, a -2 dB bell on the bass's Pro
EQ at the band centre, the measured clash weaker (NI-3 measures the bass again), undo restores the effects exactly; Duck: one undo step, a
Ducker on the bass triggered by the kick, listening to the band and ducking only it; rendered with the bass heard (the kick built as its
trigger) its 100 Hz drops by several dB while its 1 kHz stays within 0.3 dB; the clash cable is drawn dimmed, labelled "ducks under", not
counted, and the card offers to open the Ducker; the Ducker window shows "Only this band" on and turns it off (one undo step); the untouched
Pad renders bit-identical through all of it; a Ducker without the band mode renders the same with the mode off as before it existed (checked
against the parameters: bd 0 is the old path); no em dashes; no console errors. Screenshots to the out dir.
  python3 tools/ui-tests/taskNI_5b.py [repo dir] [out dir]"""
import sys, os, json, hashlib
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

SR = 44100; nb = 32; n = nb * SR // 2; t = np.arange(n) / SR
def st2(x): return np.vstack([x, x]).astype(np.float32)
kick = 0.35 * np.sin(2 * np.pi * 106 * t)
bass = 0.3 * np.sin(2 * np.pi * 100 * t) + 0.1 * np.sin(2 * np.pi * 1000 * t)
pad = 0.15 * np.sin(2 * np.pi * 3000 * t)
B = {k: al.add_audio(st2(v), SR) for k, v in (('Kick', kick), ('Bass', bass), ('Pad', pad))}
COL = {'Kick': '#f5c84c', 'Bass': '#4c8dff', 'Pad': '#3ecf8e'}
al.build({'bpm': 120, 'tracks': [{'kind': 'audio', 'name': k, 'vol': 1.0, 'color': COL[k], 'clips': [{'start': 0, 'len': 32, 'name': k, 'buf': b}]} for k, b in B.items()]})
R("for(const[k,c] of Object.entries(%s)){const t=S.tracks.find(x=>x.name===k);t.color=c}changed(true);stop();pos=4;0" % json.dumps(COL))
md5 = lambda x: hashlib.md5(x.tobytes()).hexdigest()[:12]
pad0 = md5(al.render(b0=0, b1=16, only='Pad')[0])
def band_db(x, f, a=8, b=24):
    seg = x[0, int(a * SR / 2):int(b * SR / 2)].astype(np.float64); w = np.hanning(len(seg)); S = np.abs(np.fft.rfft(seg * w)) ** 2
    fr = np.fft.rfftfreq(len(seg), 1 / SR); m = (fr > f * .93) & (fr < f * 1.07); return 10 * np.log10(S[m].sum() + 1e-20)
def bass_heard():
    x, _ = al.render(b0=0, b1=24, tracks=['Bass']); return band_db(x, 100), band_db(x, 1000)
lo0, hi0 = bass_heard()
print('    bass heard before: 100 Hz %.2f dB, 1 kHz %.2f dB' % (lo0, hi0))

R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();openMixer()})()"); pg.wait_for_timeout(800)
R("SCM.get('ni.clashes').run();0")
pg.wait_for_function("()=>NI.clash.list.length>0&&!NI.clash.meas", timeout=120000); pg.wait_for_timeout(400)
L = R("NI.clash.list.map(c=>({a:c.a.name,b:c.b.name,s:c.s,r:c.range}))"); print('    clash:', L)
ck('one clash: Kick louder, Bass covered', len(L) == 1 and L[0]['a'] == 'Kick' and L[0]['b'] == 'Bass', L)
s1 = L[0]['s'] if L else 0
def open_card():
    R("(()=>{const p=document.querySelector('#mixWin svg.cabs .nicg .nich'),q=p.getPointAtLength(p.getTotalLength()/2),m=p.getScreenCTM();window.__pt=[q.x*m.a+q.y*m.c+m.e,q.x*m.b+q.y*m.d+m.f]})()")
    x, y = R("window.__pt"); z = R("ZOOM||1"); pg.mouse.click(x * z, y * z); pg.wait_for_timeout(250)
open_card()
fx = R("[...document.querySelectorAll('#niClashPop .nicpf [data-nf]')].map(b=>[b.dataset.nf,b.textContent,b.title])")
ck('the card offers the two fixes, each with a tooltip naming one undo step', [f[0] for f in fx] == ['duck', 'notch'] and all('undo' in f[2] for f in fx) and 'Bass' in fx[0][1] and '2 dB' in fx[1][1], fx)
pg.locator('#niClashPop').screenshot(path=os.path.join(OUT, 'ni5b_card.png'))
# --- the notch
cB = R("NI.clash.band(NI.clash.list[0])")
fx0 = R("JSON.stringify(S.tracks.find(t=>t.name==='Bass').fx)"); u0 = R("UNDO.length")
R("document.querySelector('#niClashPop [data-nf=\"notch\"]').click()"); pg.wait_for_timeout(300)
eqb = R("(()=>{const f=S.tracks.find(t=>t.name==='Bass').fx.find(x=>x.type==='eq');return f?f.p.bands.filter(b=>b.on&&b.g<0).map(b=>[b.t,b.f,b.g,b.q]):null})()")
ck('Notch: one undo step', R("UNDO.length") == u0 + 1, R("UNDO.length") - u0)
ck('Notch: a -2 dB bell on the bass Pro EQ at the band centre, Q from the band width', eqb and len(eqb) == 1 and eqb[0][0] == 'peaking' and eqb[0][2] == -2 and abs(eqb[0][1] - cB['fc']) < 1 and abs(eqb[0][3] - round(cB['q'], 2)) < .02, (eqb, cB))
pg.wait_for_function("()=>!NI.clash.meas&&!NI.an.busy&&NI.clash.beat===4", timeout=120000); pg.wait_for_timeout(1500)
L2 = R("NI.clash.list.map(c=>({a:c.a.name,b:c.b.name,s:c.s}))")
ck('Notch: the measured clash is weaker (the bass measured again with its EQ)', not L2 or L2[0]['s'] < s1 - 1, (s1, L2))
ck('Notch: the untouched Pad renders bit-identical', md5(al.render(b0=0, b1=16, only='Pad')[0]) == pad0)
R("undo();0"); pg.wait_for_timeout(300)
ck('Notch: undo restores the bass effects exactly', R("JSON.stringify(S.tracks.find(t=>t.name==='Bass').fx)") == fx0)
pg.wait_for_function("()=>NI.clash.list.length===1&&!NI.clash.meas", timeout=60000); pg.wait_for_timeout(400)
# --- the duck
open_card(); u0 = R("UNDO.length")
R("document.querySelector('#niClashPop [data-nf=\"duck\"]').click()"); pg.wait_for_timeout(400)
dk = R("(()=>{const f=S.tracks.find(t=>t.name==='Bass').fx.find(x=>x.type==='duck');return f?Object.assign({id:f.id,srcName:trkById(f.p.src).name},f.p):null})()")
print('    ducker:', {k: dk[k] for k in ('srcName', 'fo', 'ff', 'bd', 'bq', 'amt', 'th')} if dk else None)
ck('Duck: one undo step', R("UNDO.length") == u0 + 1)
ck('Duck: a Ducker on Bass triggered by Kick, listening to the band, ducking only the band', dk and dk['srcName'] == 'Kick' and dk['fo'] == 'band' and dk['bd'] == 1 and abs(dk['ff'] - cB['fc']) < 1 and dk['amt'] == 50, dk)
lo1, hi1 = bass_heard(); print('    bass heard after duck: 100 Hz %.2f dB, 1 kHz %.2f dB' % (lo1, hi1))
ck('Duck: with the bass heard (kick built as trigger) its 100 Hz drops by at least 4 dB', lo0 - lo1 >= 4, round(lo0 - lo1, 2))
ck('Duck: its 1 kHz (outside the band) stays within 0.3 dB', abs(hi1 - hi0) < .3, round(hi1 - hi0, 3))
ck('Duck: the untouched Pad renders bit-identical', md5(al.render(b0=0, b1=16, only='Pad')[0]) == pad0)
pg.wait_for_timeout(1500)
st = R("(()=>{const c=document.querySelector('#mixWin svg.cabs .nicg .nicc');return{cls:c&&c.getAttribute('class'),lab:[...document.querySelectorAll('#mixWin svg.cabs .nicg .nicl')].map(x=>x.textContent),cnt:document.querySelector('#mixWin .cablg .niclb b').textContent,duck:NI.clash.list.map(c=>c.duck)}})()")
ck('Duck: the clash cable is dimmed and labelled "Bass ducks under Kick", not counted', st['cls'] and 'nidk' in st['cls'] and st['lab'] and 'ducks under Kick' in st['lab'][0] and st['cnt'] == '0' and st['duck'] == [True], st)
pg.locator('#mixWin').screenshot(path=os.path.join(OUT, 'ni5b_mixer_ducked.png'))
open_card()
o = R("[...document.querySelectorAll('#niClashPop .nicpf [data-nf]')].map(b=>b.dataset.nf)")
ck('the card of a handled clash offers to open the Ducker', o == ['open'], o)
R("document.querySelector('#niClashPop [data-nf=\"open\"]').click()"); pg.wait_for_timeout(500)
bb = R("(()=>{const b=document.querySelector('.abxw .nibd');return b?[b.classList.contains('on'),b.title]:null})()")
ck('the Ducker window opens with "Only this band" on, with a tooltip', bb and bb[0] and len(bb[1]) > 30, bb)
pg.locator('.abxw').first.screenshot(path=os.path.join(OUT, 'ni5b_ducker.png'))
u1 = R("UNDO.length"); R("document.querySelector('.abxw .nibd').click()"); pg.wait_for_timeout(300)
ck('"Only this band" turns off in one undo step', R("S.tracks.find(t=>t.name==='Bass').fx.find(x=>x.type==='duck').p.bd") is False and R("UNDO.length") == u1 + 1)
lo2, hi2 = bass_heard(); print('    whole duck: 100 Hz %.2f, 1 kHz %.2f' % (lo2, hi2))
ck('with the band mode off the Ducker ducks all of the bass (1 kHz drops too)', hi0 - hi2 > 2, round(hi0 - hi2, 2))
# the old path: a Ducker whose parameters have no bd at all renders the same as one with bd false
R("(()=>{const f=S.tracks.find(t=>t.name==='Bass').fx.find(x=>x.type==='duck');delete f.p.bd;delete f.p.bq;changed(true)})()")
h1 = md5(al.render(b0=0, b1=16, tracks=['Bass'])[0])
R("(()=>{const f=S.tracks.find(t=>t.name==='Bass').fx.find(x=>x.type==='duck');f.p.bd=false;changed(true)})()")
h2 = md5(al.render(b0=0, b1=16, tracks=['Bass'])[0])
ck('a Ducker without the new fields renders the same as with the band mode off', h1 == h2, (h1, h2))
R("undo();undo();0"); pg.wait_for_timeout(300)
ck('undo twice removes the Ducker again', not R("S.tracks.find(t=>t.name==='Bass').fx.some(x=>x.type==='duck')"))
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
blk = src[src.index('/* ===== lane D (task NI-5b)'):src.index('/* ===== end of lane D NI-5b')]
ck('no audio nodes or animation frames in the NI-5b block', not any(k in blk for k in ('createGain', 'createBiquad', '.connect(', 'requestAnimationFrame')), '')
ck('no em dashes in the NI-5b block', '—' not in blk, '')
ck('no console errors', not al.errors, al.errors)
al.stop()
print('%d/%d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
