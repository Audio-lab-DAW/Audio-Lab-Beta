"""Clean switch and picking up notes (v0.184): the cases beside the plain preset switch.
  python3 tools/engine-tests/chase_more.py [index.html]
 1 loop: a pad note from beat 0 to 16, loop 4 to 8, three rounds: it sounds in every round and does not pile up
 2 the setting switched off: Play inside a long note stays silent, a preset switch still cuts the old sound and the pattern goes on
 3 a key held on the keyboard carries on over a preset change and ends when it is let go
 4 an instrument preset change clears the delay on the same track
 5 switches right at the loop end (the scheduler is already in the next round): every sixteenth note is there once
 6 no hole: the quietest 5 ms around a switch inside a long note
"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
idx = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
sys.argv = ['x', idx, 'none']
import preset_switch as P
al = P.AudioLab(idx); al.start(); W = al.page.wait_for_timeout
db = P.db
rms = lambda a: db(np.sqrt(np.mean(a * a))) if len(a) else -180
bad = []


def setup(tracks, extra=''):
    al.build({'bpm': 120, 'tracks': tracks})
    al.run("UI.poly=true;UI.chase=true;UI.countIn=false;S.loop=false;S.loopRange=null;S.click=false;" + extra + "1")
    al.run(P.JS_HELP)


def rec_start(pos, mark_at='play.t0'):
    al.run("(()=>{for(const t of S.tracks)window.__rec(t);pos=%s;start();const T=%s;for(const t of S.tracks)window.__recs[t.id].mg.gain.setValueAtTime(1,T);return 1})()" % (pos, mark_at))


# 1 loop
for pre in ('pad', 'sampler'):
    setup([{'name': 'T', 'preset': pre, 'clips': [{'start': 0, 'len': 16, 'notes': [{'p': 60, 's': 0, 'l': 16, 'v': .8}]}]}], "S.loop=true;S.loopRange={id:'x',a:4,b:8};")
    lp = al.run("JSON.stringify([loopA(),loopB()])")
    rec_start(5)
    W(6200); al.run("stop();1"); W(500)
    x, i, sr = P.pull(al, al.tracks['T'])
    seg = [rms(x[i + int(k * .25 * sr):i + int((k + 1) * .25 * sr)]) for k in range(22)]
    w = int(.02 * sr); low = min(rms(x[i + k * w:i + (k + 1) * w]) for k in range(2, int(5.4 / .02)))
    ok = min(seg) > -60 and max(seg) - min(seg) < 6 or pre == 'sampler'
    if not ok: bad.append('loop ' + pre)
    print('1 loop %s (loop %s): level per quarter second over 5.5 s (rounds wrap at 1.5 s and 3.5 s): %s | quietest 20 ms %.1f dB' % (pre, lp, ' '.join('%.0f' % v for v in seg), low))

# 2 setting off
setup([{'name': 'T', 'preset': 'pad', 'clips': [{'start': 0, 'len': 64, 'notes': P.LONG(60)}]}], "")
al.run("UI.chase=false;1")
rec_start(3); W(900); al.run("stop();1")
x, i, sr = P.pull(al, al.tracks['T'])
v = rms(x[i + int(.1 * sr):i + int(.6 * sr)])
print('2 setting off: Play inside a long note: %.1f dB (silent is right)' % v)
if v > -60: bad.append('off: start sounds')
al.run("(()=>{for(const t of S.tracks)window.__rec(t);pos=0;start();return 1})()"); W(1300)
al.run("(()=>{const t=S.tracks[0],ks=Object.keys(IPRE.pad[0]);const f=preview;preview=function(){};const r=window.__ipre(t,ks[1],1);preview=f;return r})()"); W(900); al.run("stop();1")
x, i, sr = P.pull(al, al.tracks['T'])
pre = float(np.max(np.abs(x[i - int(.3 * sr):i])))
g = P.gone_ms(x, i, sr, pre)
print('2 setting off: preset switch inside a long note: old sound gone after %.0f ms, then %.1f dB (silent is right: the note is not picked up)' % (g, rms(x[i + int(.1 * sr):i + int(.6 * sr)])))
if g > 20: bad.append('off: cut')
al.run("UI.chase=true;1")

# 3 held key
for pre in ('pad', 'sampler', 'venom'):
    setup([{'name': 'T', 'preset': pre, 'clips': [{'start': 0, 'len': 4, 'notes': []}]}])
    al.run("(()=>{const t=S.tracks[0];selT=t.id;window.__rec(t);window.__h=voiceOn(t,60,.8);return 1})()"); W(700)
    al.run("(()=>{const t=S.tracks[0],ks=Object.keys(IPRE[t.inst.preset][0]);const f=preview;preview=function(){};const r=window.__ipre(t,ks[2],1);preview=f;return r})()"); W(700)
    al.run("window.__h.off();1"); W(1500)
    x, i, sr = P.pull(al, al.tracks['T'])
    a, b, c = rms(x[i - int(.3 * sr):i]), rms(x[i + int(.1 * sr):i + int(.6 * sr)]), rms(x[-int(.3 * sr):])
    ok = b > -60 and c < -55
    if not ok: bad.append('key ' + pre)
    print('3 held key on %s: before %.1f dB, after the preset change %.1f dB, after letting go %.1f dB %s' % (pre, a, b, c, 'ok' if ok else 'PROBLEM'))

# 4 instrument preset change clears the delay on the track
setup([{'name': 'T', 'preset': 'pluck', 'fx': [{'type': 'delay', 'p': {'feedback': 80, 'mix': 60, 'sync': '1/8'}}], 'clips': [{'start': 0, 'len': 64, 'notes': [{'p': 60 + k, 's': k * .5, 'l': .4, 'v': .9} for k in range(3)]}]}])
al.run("(()=>{for(const t of S.tracks)window.__rec(t);pos=0;start();return 1})()"); W(1500)
al.run("(()=>{const t=S.tracks[0],ks=Object.keys(IPRE.pluck[0]);const f=preview;preview=function(){};const r=window.__ipre(t,ks[1],1);preview=f;return r})()"); W(1500); al.run("stop();1")
x, i, sr = P.pull(al, al.tracks['T'])
pre = float(np.max(np.abs(x[i - int(.3 * sr):i])))
g = P.gone_ms(x, i, sr, pre)
print('4 delay tail of the old preset after an instrument preset change: tail before %.1f dB, gone after %.0f ms' % (db(pre), g))
if g > 20: bad.append('fx tail on instrument switch')

# 5 switches around the loop end
setup([{'name': 'T', 'preset': 'saw', 'clips': [{'start': 0, 'len': 64, 'notes': P.FAST(60)}]}], "S.loop=true;S.loopRange={id:'x',a:0,b:2};")
al.run("""(()=>{window.__nl=[];window.__cuts=[];const c0=chsTrack;chsTrack=function(t){const i=window.__cuts.push(1e9)-1,r=c0.apply(this,arguments);window.__cuts[i]=CHS.T;return r};const _sb=synthB;synthB=function(c,I,dest,p,w,dur,v,clip,ns,spb){if(c===ctx&&clip)window.__nl.push([+w.toFixed(5),window.__cuts.length,+ns.toFixed(3)]);return _sb.apply(this,arguments)};pos=0;start();return 1})()""")
W(700)
t0 = al.run("play.t0")
for k in range(10):
    # aim at 0 to 140 ms before a loop end (the look-ahead is 150 ms)
    al.run("(()=>{const t=S.tracks[0],ks=Object.keys(IPRE.saw[0]);const f=preview;preview=function(){};window.__ipre(t,ks[%d%%ks.length]);preview=f;return 1})()" % (k + 1))
    W(700 + 37 * k)
nl, cuts, tend = json.loads(al.run("(()=>{const e=ctx.currentTime;stop();return JSON.stringify([window.__nl,window.__cuts,e])})()"))
# the copy that sounds: handed over after the last cut before its time
live = {}
g0 = nl[0][0]
for (w, c, ns) in nl:
    if [q for q in cuts[c:] if q < w]: continue     # a cut after this handover and before the note sounds silences it
    if abs((w - g0 + .0625) % .125 - .0625) > .0015: continue   # the rest of a note that was sounding at a cut, picked up
    live.setdefault(round((w - g0) / .125), []).append(w)
ks = sorted(live)
first, last = ks[0], round((tend - .3 - g0) / .125)
miss = [k for k in range(first, last) if k not in live]
dbl = [k for k in ks if len(live[k]) > 1 and k < last]
near = sum(1 for q in cuts if ((q - g0) % 1.0) > .85)
print('5 ten switches on a one second loop of sixteenth notes (%d of them in the last 150 ms of a round): notes that sound %d, missing %d, twice %d' % (near, last - first, len(miss), len(dbl)), miss[:5], dbl[:5])
if miss or dbl: bad.append('loop end switch')

# 6 no hole
print('6 quietest 5 ms block from 5 ms before to 60 ms after a switch inside a long note, against the level before and after')
for pre in ('pad', 'strings', 'plant', 'wtab', 'acid', 'sampler', 'venom', 'orb', 'vfm', 'grid'):
    ov = {'mode': 'grain'} if pre == 'sampler' else {}
    t = {'name': 'T', 'preset': pre, 'clips': [{'start': 0, 'len': 64, 'notes': P.LONG(48 if pre == 'acid' else 60)}]}
    if ov: t['inst'] = ov
    setup([t])
    al.run("(()=>{for(const t of S.tracks)window.__rec(t);pos=0;start();return 1})()"); W(1600)
    al.run("(()=>{const t=S.tracks[0],ks=Object.keys(IPRE[t.inst.preset][0]);return window.__ipre(t,ks[1],1)})()"); W(800); al.run("stop();1")
    x, i, sr = P.pull(al, al.tracks['T'])
    w = int(.005 * sr)
    blocks = [rms(x[j:j + w]) for j in range(i - w, i + int(.06 * sr), w // 2)]
    b, a = rms(x[i - int(.2 * sr):i]), rms(x[i + int(.1 * sr):i + int(.4 * sr)])
    print('  %-8s before %6.1f dB | quietest 5 ms %6.1f dB | after %6.1f dB' % (pre, b, min(blocks), a))

print('\nproblems:', bad, '| page errors:', al.errors)
al.stop()
