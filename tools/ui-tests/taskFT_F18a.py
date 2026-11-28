"""Task FT-F18a (lane C): Kick and bass lab, part 1: the bass line's key, the tail overlap and the low-band correlation, as a row of
lane D's Kick and bass lab (NI_HOOKS.kickBassView.addRow).
Checks:
  - the row shows under the lab's words: Bass line, Tail overlap, Low band, a strip canvas, the words; tooltips; no em dashes
  - bass key: a rolling F#1 bass in F# minor reads "in the key"; a bass line in A minor in an F# minor song reads A minor, flagged
  - tail overlap: equal to a calculation from the lab's own kick life and bass notes (merged), the cut to clear the next bass note
  - low band: the pure correlation on known signals (same: +1 and +3.01 dB, inverted: -1, 90 degrees apart: about 0);
    the lab's reading equals an independent offline calculation (both tracks rendered alone, scipy Butterworth 4th order at 120 Hz,
    correlated over the kick's lives) within 0.01, also on a second song and on the bar after
  - cached: opening again renders nothing new; nothing drawn while idle; the project is unchanged by measuring
  - a muted bass (silent): the row says the bass is silent
  - screenshots (normal and the Light level) to the out dir; no console errors
  python3 tools/ui-tests/taskFT_F18a.py [repo dir] [out dir]"""
import sys, os, json, math
import numpy as np
from scipy.signal import butter, sosfilt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
OUT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, '..', 'ft-shots'))
os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ck(name, ok, info=''):
    N[0] += 1
    if ok: N[1] += 1; print('  ok  ', name, info if info != '' else '')
    else: FAIL.append(name); print('  FAIL', name, info)

BPM = 120
al = AudioLab(os.path.join(ROOT, 'index.html')); al.start(); pg = al.page; R = al.run
errs = []
pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
pg.on('pageerror', lambda e: errs.append(str(e)))
print('version', al.version)

def wait_row():
    pg.wait_for_function("""()=>{const W=document.getElementById('niKB');if(!W||W.hidden||!NI.kbv.r)return false;const l=FT_HOOKS.kickBassLab.last();
        const b=W.querySelector('[data-fk="lb"]');return !!(l&&l.r===NI.kbv.r&&(l.c||NI.kbv.r.why)&&(!b||b.textContent!=='…'))}""", timeout=30000)
    pg.wait_for_timeout(150)
def row():
    return R("""(()=>{const W=document.getElementById('niKB'),E=W.querySelector('.ftkb'),q=k=>E&&E.querySelector('[data-fk="'+k+'"]');if(!E)return null;
      return{hidden:E.hidden,bk:q('bk')&&q('bk').textContent,bkc:q('bk')&&q('bk').className,ov:q('ov')&&q('ov').textContent,lb:q('lb')&&q('lb').textContent,lbc:q('lb')&&q('lb').className,
        w:(E.querySelector('.ftkbw')||{}).textContent,tips:[...E.querySelectorAll('.nird span,canvas')].every(e=>e.title&&e.title.length>8),cv:!!q('cv')}})()""")
def song(bass_notes, kick_tune=30, mute_bass=False):
    tr = [{'name': 'Kick', 'preset': 'kick', 'vol': 1.0, 'inst': {'tune': kick_tune}, 'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 36, 's': b, 'l': .25, 'v': .9} for b in range(16)]}]},
          {'name': 'Bass', 'preset': 'saw', 'vol': .8, 'clips': [{'start': 0, 'len': 16, 'notes': bass_notes}]},
          {'name': 'Lead', 'preset': 'saw', 'vol': .4, 'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 66, 's': 0, 'l': 4, 'v': .5}]}]}]
    al.build({'bpm': BPM, 'tracks': tr})
    R("PR.root=6;PR.scale='minor';pos=9;0")
    if mute_bass: R("S.tracks.find(t=>t.name==='Bass').vol=0;0")
ROLL = [{'p': 30, 's': b + q, 'l': 0.2, 'v': 0.8} for b in range(16) for q in (.25, .5, .75)]

def offline(c):
    """independent: both tracks alone (the same render call), mono, scipy Butterworth, correlation over the lab's kick lives"""
    d = json.loads(R("""(async()=>{const r=NI.kbv.r,sr=r.sr,b0=r.bar.b0,b1=r.bar.b1,tail=Math.min(.5,(r.kick.lifeMs||300)/1000+.05),
        m=b=>{const L=b.getChannelData(0),Rr=b.numberOfChannels>1?b.getChannelData(1):L;return Array.from(L,(v,i)=>(v+Rr[i])*.5)};
        const k=await renderMixChunked(sr,b0,b1,tail,false,r.kick.id,null,false),b=await renderMixChunked(sr,b0,b1,tail,false,r.bass.id,null,false);
        return JSON.stringify({sr,k:m(k),b:m(b)})})()"""))
    sos = butter(4, 120, 'low', fs=d['sr'], output='sos')
    k = sosfilt(sos, np.array(d['k'])); b = sosfilt(sos, np.array(d['b']))
    idx = np.concatenate([np.arange(max(0, i0), min(len(k), i1)) for i0, i1 in c['lives']])
    kk, bb = k[idx], b[idx]
    r = float(np.sum(kk * bb) / math.sqrt(np.sum(kk * kk) * np.sum(bb * bb)))
    db = 10 * math.log10(np.sum((kk + bb) ** 2) / (np.sum(kk * kk) + np.sum(bb * bb)))
    return r, db
def lab_c():
    return json.loads(R("JSON.stringify((()=>{const c=FT_HOOKS.kickBassLab.last().c;return{life:c.life,lives:c.lives,steps:c.steps.length}})())"))

# 0. the pure correlation on known signals
pure = json.loads(R("""JSON.stringify((()=>{const sr=48000,n=48000,a=new Float32Array(n),b=new Float32Array(n),c=new Float32Array(n),z=new Float32Array(n);
   for(let i=0;i<n;i++){a[i]=Math.sin(2*Math.PI*50*i/sr);b[i]=-a[i];c[i]=Math.cos(2*Math.PI*50*i/sr)}const H=FT_HOOKS.kickBassLab;
   return{same:H.corrOf(a,a),inv:H.corrOf(a,b),q:H.corrOf(a,c),sil:H.corrOf(a,z)}})())"""))
ck('correlation of a signal with itself is +1, +3.01 dB', abs(pure['same']['r'] - 1) < 1e-6 and abs(pure['same']['db'] - 10 * math.log10(4 / 2)) < 1e-3, pure['same'])
ck('inverted: -1 (they cancel)', abs(pure['inv']['r'] + 1) < 1e-6, pure['inv']['r'])
ck('90 degrees apart: about 0 and about 0 dB', abs(pure['q']['r']) < .01 and abs(pure['q']['db']) < .05, pure['q'])
ck('one side silent: no correlation, named', pure['sil']['r'] is None and pure['sil']['silent'] == 'bass', pure['sil'])
low = json.loads(R("""JSON.stringify((()=>{const sr=48000,n=48000,f=hz=>{const x=new Float32Array(n);for(let i=0;i<n;i++)x[i]=Math.sin(2*Math.PI*hz*i/sr);return x};
   const rms=x=>{let s=0;for(let i=n/2;i<n;i++)s+=x[i]*x[i];return Math.sqrt(s/(n/2))*Math.SQRT2};const L=FT_HOOKS.kickBassLab.low;return[rms(L(f(40),null,sr,120)),rms(L(f(120),null,sr,120)),rms(L(f(480),null,sr,120))]})())"""))
ck('the low-pass: 40 Hz passes, 120 Hz at -3 dB, 480 Hz down more than 40 dB', abs(low[0] - 1) < .02 and abs(20 * math.log10(low[1]) + 3.01) < .1 and 20 * math.log10(low[2]) < -40, [round(20 * math.log10(v), 2) for v in low])

# 1. rolling bass in F# minor, kick on F#1
song(ROLL)
st0 = R("JSON.stringify(S.tracks)")
R("SCM.get('ni.kickBass').run();0"); wait_row(); c = row(); print('   ', c)
ck('the row shows under the lab: Bass line, Tail overlap, Low band and the strip', c and not c['hidden'] and c['cv'] and c['bk'] and c['ov'] and c['lb'], c)
ck('bass line: plays only F♯, in the key', c['bk'].startswith('F♯') and 'in the key' in c['bk'] and c['bkc'] == 'ok', c['bk'])
ck('every read-out and the strip has a tooltip', c['tips'])
ck('no em dashes in the row', '—' not in R("document.querySelector('#niKB .ftkb').textContent+[...document.querySelectorAll('#niKB .ftkb [title]')].map(e=>e.title).join(' ')"))
# overlap against a calculation from the lab's data
lr = json.loads(R("JSON.stringify(NI.kbv.r)")); life = lr['kick']['lifeMs']; spb = 60 / BPM * 1000
exp_into, exp_cut = 0, 0
for h in lr['kick']['hits']:
    iv = sorted([(max(q['b'], h), min(q['b'] + q['l'], h + life / spb)) for q in lr['bass']['notes'] if min(q['b'] + q['l'], h + life / spb) > max(q['b'], h) + 1e-9])
    tot, cs, ce = 0, None, None
    for s_, t_ in iv:
        if cs is None: cs, ce = s_, t_
        elif s_ <= ce: ce = max(ce, t_)
        else: tot += (ce - cs) * spb; cs, ce = s_, t_
    if cs is not None: tot += (ce - cs) * spb
    nx = [q['b'] for q in lr['bass']['notes'] if q['b'] >= h - 1e-6]
    cut = (h + life / spb - min(nx)) * spb if nx and min(nx) < h + life / spb else 0
    exp_into = max(exp_into, round(tot)); exp_cut = max(exp_cut, round(cut))
ov = json.loads(R("JSON.stringify(FT_HOOKS.kickBassLab.last().ov)"))
ck('tail overlap equals the calculation from the kick life (%d ms) and the notes' % round(life), ov['max'] == exp_into and ov['cut'] == exp_cut, (ov['max'], ov['cut'], exp_into, exp_cut))
ck('the read-out shows it: "%d ms, %d ms too long"' % (exp_into, exp_cut), c['ov'] == '%dms, %d ms too long' % (exp_into, exp_cut), c['ov'])
L = lab_c(); r_off, db_off = offline(L)
ck('low band equals the offline calculation within 0.01 (lab %+.3f, offline %+.3f)' % (L['life']['r'], r_off), abs(L['life']['r'] - r_off) < .01, (L['life']['r'], r_off))
ck('the level change equals it within 0.1 dB (lab %+.2f, offline %+.2f dB)' % (L['life']['db'], db_off), abs(L['life']['db'] - db_off) < .1)
ck('one strip value per 16th of the bar (16)', L['steps'] == 16, L['steps'])
sgn = '+' if L['life']['r'] > 0 else '−'
ck('the read-out shows the value with a sign and dB', c['lb'].startswith(sgn) and 'dB' in c['lb'], c['lb'])
ck('the words name the low band', 'Low band (under 120 Hz)' in c['w'], c['w'])
px = R("""(()=>{const cv=document.querySelector('#niKB .ftkb canvas'),d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;let g=0,r=0;
   for(let i=0;i<d.length;i+=4){if(d[i+1]>150&&d[i]<120)g++;if(d[i]>180&&d[i+1]<110)r++}return{g,r}})()""")
ck('the strip is drawn (coloured bars)', px['g'] + px['r'] > 100, px)
pg.locator('#niKB').screenshot(path=os.path.join(OUT, 'ftF18a_card.png'))
st1 = R("JSON.stringify(FT_HOOKS.kickBassLab.stats())")
pg.wait_for_timeout(1200)
ck('nothing drawn while idle', R("JSON.stringify(FT_HOOKS.kickBassLab.stats())") == st1)
ck('measuring leaves the project unchanged', R("JSON.stringify(S.tracks)") == st0)
# cached: close and open again
n0 = R("FT_HOOKS.kickBassLab.stats().renders")
R("NI_HOOKS.kickBassView.close();NI_HOOKS.kickBassView.open({});0"); wait_row()
ck('opening again uses the cache (no new render)', R("FT_HOOKS.kickBassLab.stats().renders") == n0, R("FT_HOOKS.kickBassLab.stats().renders") - n0)
# the next bar
pg.click('#niKB [data-nk="next"]'); pg.wait_for_timeout(100); wait_row(); L2 = lab_c(); r2, _ = offline(L2)
ck('bar 4: equals the offline calculation too (lab %+.3f, offline %+.3f)' % (L2['life']['r'], r2), abs(L2['life']['r'] - r2) < .01)
# tune the kick (lane D's fix) and the row follows
pg.click('#niKB [data-nk="here"]'); pg.wait_for_timeout(100); wait_row()

# 2. a bass line in A minor in an F# minor song, notes clear of the kick tail
AM = []
for b in range(16):
    for q, p in ((.5, 33), (.75, 36)): AM.append({'p': p if b % 4 != 3 else [40, 38, 43, 45][b // 4 % 4], 's': b + q, 'l': 0.2, 'v': 0.8})
AM += [{'p': 33, 's': b + .5, 'l': .2, 'v': .8} for b in range(0, 16, 2)]
song(AM, kick_tune=33)
R("NI_HOOKS.kickBassView.close();NI_HOOKS.kickBassView.open({});0"); wait_row(); c2 = row(); print('   ', c2)
bkk = json.loads(R("JSON.stringify(FT_HOOKS.kickBassLab.last().bk)"))
ck('bass line in A minor read as A minor and flagged against F♯ minor', c2['bk'].startswith('A minor') and c2['bkc'] == 'cl' and not bkk['same'], (c2['bk'], bkk))
ck('the words say the bass fits A minor and how little of it is in F♯ minor', 'fits A minor best' in c2['w'] and 'F♯ minor only' in c2['w'], c2['w'])
L3 = lab_c(); r3, db3 = offline(L3)
ck('second song: equals the offline calculation (lab %+.3f, offline %+.3f)' % (L3['life']['r'], r3), abs(L3['life']['r'] - r3) < .01 and abs(L3['life']['db'] - db3) < .1)
pg.locator('#niKB').screenshot(path=os.path.join(OUT, 'ftF18a_card_aminor.png'))

# 3. a bass at fader 0: silent
song(ROLL, mute_bass=True)
R("NI_HOOKS.kickBassView.close();NI_HOOKS.kickBassView.open({});0"); wait_row(); c3 = row(); print('   ', c3)
ck('a silent bass (fader at 0): the low band says so', 'no bass' in (c3['lb'] or '') and 'silent while the kick sounds' in c3['w'], (c3['lb'], c3['w']))

# 4. Light level
song(ROLL)
R("NI_HOOKS.kickBassView.close();0")
R("UI.lite=true;UI.liteMan=true;applyLite();0"); pg.wait_for_timeout(300)
R("NI_HOOKS.kickBassView.open({});0"); wait_row()
pg.locator('#niKB').screenshot(path=os.path.join(OUT, 'ftF18a_card_light.png'))
ck('no console errors', not [e for e in errs if 'coi-serviceworker' not in e and 'favicon' not in e], errs[:5])
al.stop()
print('%d of %d' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
