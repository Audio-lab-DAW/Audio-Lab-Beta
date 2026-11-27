"""Task NI-2a (lane D): I2 kick and bass tuning lab, the analysis (NI_kickBass, NI_HOOKS.kickBass).
Checks:
  - synthetic audio kicks (sweep down to a known end note, drive, decay) are found within 20 cents, the range holds the
    true note, kicks under 40 Hz are flagged as a range
  - the Kick designer's end note is read from its settings (exact) and agrees within 20 cents with a measurement of
    its own render; drum machine kick pads (Kick designer pad, kit kick) read from their settings with the pad's tune
  - bass notes of the bar under the playhead: interval, beat rate and state match a direct calculation
    (tuned, clash with the beat rate, apart), notes outside the bar are left out
  - kick hits with the bass notes they overlap and the gap to the next bass note (rolling bass)
  - the key from the piano roll (S.prKey), in key or not, "tune the kick to the root" target
  - the analysis never changes the project; a second call is served from the cache; an edit gives a new result
  - the code adds no audio nodes; no em dashes; no console errors
  python3 tools/ui-tests/taskNI_2a.py [repo dir]"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
N = [0, 0]; FAIL = []
def ck(name, ok, info=''):
    N[0] += 1
    if ok: N[1] += 1; print('  ok  ', name, info if info != '' else '')
    else: FAIL.append(name); print('  FAIL', name, info)

SR = 48000; BPM = 120; SPB = 60 / BPM
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
cents = lambda a, b: 1200 * math.log2(a / b)

def synth_kick(f_end, f_start=260.0, sweep=0.045, life=0.38, drive=2.0, beats=16):
    n = int(beats * SPB * SR); x = np.zeros(n)
    m = int(life * SR); tt = np.arange(m) / SR
    xx = np.minimum(1, tt / sweep); f = np.exp(np.log(f_end) + (np.log(f_start) - np.log(f_end)) * (1 - xx) ** 3)
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.where(tt < 0.0005, tt / 0.0005, 1) * (1 - tt / life) ** 1.2
    hit = np.tanh(drive * np.sin(ph) * env) / np.tanh(drive) * 0.9
    for b in range(beats):
        s0 = int(b * SPB * SR); k = min(m, n - s0); x[s0:s0 + k] += hit[:k]
    return np.vstack([x, x]).astype(np.float32)

al = AudioLab(os.path.join(ROOT, 'index.html')); al.start()
print('version', al.version)
def kb(o=''):
    return al.page.evaluate("c=>AudioLab.run(c)", "(async()=>{const r=await NI_kickBass(%s);return JSON.parse(JSON.stringify(r))})()" % (o or '{}'))

# 1. synthetic audio kicks at known end notes
for f_end in (hz(31), hz(28), hz(33.4), hz(26), hz(24)):
    buf = al.add_audio(synth_kick(f_end), SR)
    al.build({'bpm': BPM, 'tracks': [{'kind': 'audio', 'name': 'Kick', 'vol': 1.0, 'clips': [{'start': 0, 'len': 16, 'name': 'k', 'buf': buf}]}]})
    r = kb('{t:4.5}')
    k = r.get('kick') or {}
    c = cents(k.get('endHz', 1), f_end) if k.get('endHz') else 999
    tag = 'audio kick ending at %.1f Hz' % f_end
    ck(tag + ': measured from the sound, within 20 cents', k.get('src') == 'audio' and abs(c) < 20, (round(k.get('endHz', 0), 2), round(c, 1), k.get('range', {}).get('txt')))
    ck(tag + ': the range holds the true note', k and k['range']['lo'] <= f_end * 1.003 and k['range']['hi'] >= f_end / 1.003, k and (round(k['range']['lo'], 2), round(k['range']['hi'], 2)))
    ck(tag + ': flagged as a range under 40 Hz (and only there)', bool(k.get('low')) == (f_end < 40), k.get('low'))
    ck(tag + ': hits of bar 2 found on the beats', k and len(k['hits']) == 4 and all(abs(h - (4 + i)) < 0.02 for i, h in enumerate(k['hits'])), k and k['hits'])
print('    words:', r.get('words'))
ck('words for a low kick say it is a range', 'range, not exact' in r.get('words', ''), r.get('words'))

# 2. the Kick designer from its settings, against a measurement of its own render
for tune in (30, 26, 34.5):
    al.build({'bpm': BPM, 'tracks': [{'name': 'Kick', 'preset': 'kick', 'vol': 1.0, 'inst': {'tune': tune},
              'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 36, 's': b, 'l': 0.25, 'v': 0.9} for b in range(16)]}]}]})
    r = kb('{t:4}'); k = r['kick']
    ck('Kick designer at tune %g: read from its settings, exact %.2f Hz' % (tune, hz(tune)), k['src'] == 'params' and k['exact'] and abs(k['endHz'] - hz(tune)) < 1e-6, (k['src'], k['endHz']))
    ck('Kick designer at tune %g: the curve falls from the punch to the end note' % tune, k['curve'][0]['f'] > k['curve'][-1]['f'] and abs(k['curve'][-1]['f'] - hz(tune)) < 1e-6, (round(k['curve'][0]['f']), round(k['curve'][-1]['f'], 2)))
    x, sr = al.render(b0=0, b1=16, sr=SR, only='Kick')
    buf = al.add_audio(x.astype(np.float32), SR)
    al.build({'bpm': BPM, 'tracks': [{'kind': 'audio', 'name': 'Kick render', 'vol': 1.0, 'clips': [{'start': 0, 'len': 16, 'name': 'k', 'buf': buf}]}]})
    m = kb('{t:4}')['kick']
    ck('Kick designer at tune %g: its render measured within 20 cents of its settings' % tune, abs(cents(m['endHz'], hz(tune))) < 20, (round(m['endHz'], 2), round(cents(m['endHz'], hz(tune)), 1)))
ck('NI.kickModel gives the same without a render (key tracking: note 48 is 12 semitones up when kt is on)',
   abs(al.run("NI.kickModel({inst:Object.assign({},PRESETS.kick,{preset:'kick',tune:30,kt:true}),clips:[]},48).endHz") - hz(42)) < 1e-6)

# 3. drum machine kick pads
al.build({'bpm': BPM, 'tracks': [{'name': 'Drums', 'preset': 'drums', 'vol': 1.0,
          'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 36, 's': b, 'l': 0.25, 'v': 0.9} for b in range(16)] + [{'p': 42, 's': b + .5, 'l': .25, 'v': .5} for b in range(16)]}]}]})
did = al.tracks['Drums']
base = al.run("KPRE.house.tune")
al.run("trkById(%s).inst.pads[0].tune=-2;0" % json.dumps(did))
r = kb(); k = r['kick']
ck('drum machine kit kick: found as the kick, read from its settings with the pad tune (-2)', k['src'] == 'params' and abs(k['endHz'] - hz(base - 2)) < 1e-6 and k.get('pad') == 0, (k['label'], k['endHz'], hz(base - 2)))
al.run("Object.assign(trkById(%s).inst.pads[0],{type:'kd',k:kickParams('psyroll'),tune:1,dec:1});changed(false);0" % json.dumps(did))
k = kb()['kick']; pr = al.run("KPRE.psyroll.tune")
ck('drum machine Kick designer pad: its settings plus the pad tune', abs(k['endHz'] - hz(pr + 1)) < 1e-6, (k['label'], k['endHz']))

# 4. bass notes against the kick, key, overlap
KT = 30  # kick F#1, 46.25 Hz
bass_notes = [(30, 8.25), (31, 8.5), (42, 8.75), (43, 9.25), (37, 9.5), (35, 10.25), (31.0, 13.25)]  # last one is in bar 4: left out
al.build({'bpm': BPM, 'tracks': [
    {'name': 'Kick', 'preset': 'kick', 'vol': 1.0, 'inst': {'tune': KT}, 'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 36, 's': b, 'l': 0.25, 'v': 0.9} for b in range(16)]}]},
    {'name': 'Lead', 'preset': 'saw', 'vol': .5, 'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 72, 's': 0, 'l': 4, 'v': .5}]}]},
    {'name': 'Bass', 'preset': 'saw', 'vol': 1.0, 'clips': [{'start': 0, 'len': 16, 'notes': [{'p': p, 's': s, 'l': 0.2, 'v': 0.8} for p, s in bass_notes]}]}]})
al.run("PR.root=6;PR.scale='minor';0")
before = al.run("JSON.stringify(S)")
r = kb('{t:9.6}')
ck('kick and bass found by name and pitch (not the Lead)', r['kick']['name'] == 'Kick' and r['bass']['name'] == 'Bass', (r['kick']['name'], r['bass']['name']))
ck('bar 3 (beats 8 to 12) is the bar under the playhead', r['bar'] == {'n': 3, 'b0': 8, 'b1': 12}, r['bar'])
ck('the six bass notes of bar 3, none from bar 4', [q['p'] for q in r['bass']['notes']] == [30, 31, 42, 43, 37, 35], [q['p'] for q in r['bass']['notes']])
fK = hz(KT); ok = True; info = []
for q in r['bass']['notes']:
    fB = hz(q['p']); d = 12 * math.log2(fB / fK); o = round(d / 12); dd = d - 12 * o
    beat = abs(fB - fK * 2 ** o) if o >= 0 else abs(fK - fB * 2 ** -o)
    st = 'tuned' if abs(dd) < .3 else 'clash' if abs(dd) <= 2.5 else 'apart'
    good = abs(q['pair']['beatHz'] - beat) < 1e-6 and q['pair']['state'] == st and abs(q['pair']['semis'] - d) < 1e-9
    ok &= good; info.append((q['txt'], q['pair']['state'], round(q['pair']['beatHz'], 2), st, round(beat, 2)))
ck('every pair: interval, beat rate and state match the direct calculation', ok, info)
st = {q['p']: q['pair'] for q in r['bass']['notes']}
ck('F#1 and F#2 in tune, G1 beating at 2.75 Hz, G2 at 5.51 Hz, C#2 and B1 apart',
   st[30]['state'] == st[42]['state'] == 'tuned' and st[31]['state'] == st[43]['state'] == 'clash' and abs(st[31]['beatHz'] - (hz(31) - hz(30))) < 1e-9 and abs(st[43]['beatHz'] - (hz(43) - 2 * hz(30))) < 1e-9 and st[37]['state'] == st[35]['state'] == 'apart',
   {p: (v['state'], round(v['beatHz'], 2)) for p, v in st.items()})
ck('key from the piano roll: F# minor, the kick in key, G not in key', r['key']['name'] == 'F♯ minor' and r['key']['from'] == 'piano roll' and r['kick']['inKey'] and not [q for q in r['bass']['notes'] if q['p'] == 31][0]['inKey'], (r['key'], r['kick']['inKey']))
ck('kick in tune with the root: "tune to root" is 0 semitones', abs(r['suggest']['tuneTo']['semis']) < 1e-9, r['suggest'])
ov = r['overlap']
ck('four kick hits in bar 3 at 8, 9, 10, 11', [round(o['b'], 3) for o in ov] == [8, 9, 10, 11], [o['b'] for o in ov])
ck('gap to the next bass note: 125 ms after the kick at 8 (bass at 8.25, 120 BPM)', ov[0]['gapMs'] == 125, [o['gapMs'] for o in ov])
ck('the kick at 8 (life 320 ms, 0.64 beat) overlaps the bass notes at 8.25 and 8.5, not 8.75', ov[0]['notes'] == [0, 1], ov[0]['notes'])
ck('the kick at 11 has no next bass note in the bar', ov[3]['gapMs'] is None and ov[3]['notes'] == [], ov[3])
print('    words:', r['words'])
ck('words name the kick note and a beating bass note', 'F♯1' in r['words'] and 'beating at 2.8 Hz' in r['words'] and '—' not in r['words'], r['words'])
al.run("PR.root=9;0")
r2 = kb('{t:9.6}')
ck('key A minor: "tune to root" says A1, +3 semitones', r2['suggest']['tuneTo']['txt'] == 'A1' and abs(r2['suggest']['tuneTo']['semis'] - 3) < 1e-9, r2['suggest'])
after_key = al.run("JSON.stringify(S)")
al.run("PR.root=6;0")
same = al.page.evaluate("c=>AudioLab.run(c)", "(async()=>{const a=await NI_kickBass({t:9.6}),t0=performance.now(),b=await NI_kickBass({t:9.6});return [a===b,performance.now()-t0]})()")
ck('a second call is served from the cache', same[0] and same[1] < 30, same)
ck('the analysis does not change the project', al.run("JSON.stringify(S)") == before, '')
al.run("trkById(%s).clips[0].notes[1].p=30;changed(false);0" % json.dumps(al.tracks['Bass']))
r3 = kb('{t:9.6}')
ck('an edit gives a new result (G1 moved to F#1: in tune)', r3['bass']['notes'][1]['pair']['state'] == 'tuned', r3['bass']['notes'][1]['pair'])
ck('NI_HOOKS.kickBass is the analysis (for FT-F18)', al.run("NI_HOOKS.kickBass===NI_kickBass"))
ck('lane C project key is used when it exists', al.page.evaluate("c=>AudioLab.run(c)", "(async()=>{window.FT_HOOKS=window.FT_HOOKS||{};const o=FT_HOOKS.projectKey;FT_HOOKS.projectKey=()=>({root:2,scale:'major'});const k=NI_key();FT_HOOKS.projectKey=o;return k.name==='D major'&&k.from==='project key'})()"))

# 5. edge cases
al.build({'bpm': BPM, 'tracks': [{'name': 'Pad', 'preset': 'saw', 'vol': .5, 'clips': [{'start': 0, 'len': 8, 'notes': [{'p': 72, 's': 0, 'l': 4, 'v': .5}]}]}]})
r = kb()
ck('no kick: says so, nothing else', r.get('empty') and 'No kick' in r['why'], r)
al.build({'bpm': BPM, 'tracks': [{'name': 'Kick', 'preset': 'kick', 'vol': 1.0, 'clips': [{'start': 16, 'len': 4, 'notes': [{'p': 36, 's': 0, 'l': .25, 'v': .9}]}]}]})
r = kb('{t:0}')
ck('no bass: the kick is still read (from the first bar it plays), the bass says why', r['kick']['src'] == 'params' and r['bar']['n'] == 5 and 'No bass' in r['bass']['why'], (r['bar'], r['bass']))

# 6. the code
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
blk = src[src.index('/* ===== lane D (task NI-2a)'):src.index('/* ===== end of lane D NI-2a')]
ck('no audio nodes or worklets made in the NI-2a block', not any(k in blk for k in ('createGain', 'createBiquad', 'AudioWorklet', 'audioWorklet', '.connect(', 'OfflineAudioContext')), '')
ck('no em dashes in the NI-2a block', '—' not in blk, '')
ck('no console errors', not al.errors, al.errors)
al.stop()
print('%d/%d checks pass' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
