"""Fractals export flake (scheduling chat, 28 Nov; task RG's entries): 'Fractals Bass, master put back to 0 dB' gave -26.74483 dB
(a6774faed0a9) instead of -25.48699 dB (09e0415bec5e) now and then.
Cause: renderMix sets the global SIDE_B0 (the beat an offline render starts at) and then awaits wlLoad(oc); the Sidechain effect
('side') reads SIDE_B0 when it is built, after that await. Any other renderMix that starts meanwhile (the overview map's background
render after load, the pieces of renderMixChunked that run side by side) overwrites SIDE_B0, so the pump is built with another
render's start beat: the Bass ducks on the wrong phase. Fix: set SIDE_B0 again right after the await (from there to
startRendering() the build is synchronous). NI-7's own render (lane D) sets it before its context is made too, so the Volume
Shaper's offline origin (VMOF, read when the context is made) is its own.
  python3 tools/feature-lab/ni/ni_sideb0.py [index.html]"""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* SIDE_B0 again after the await' in s:
    print('already applied'); sys.exit(0)
def rep(s, old, new):
    n = s.count(old); assert n == 1, (old[:80], n); return s.replace(old, new)
s = rep(s, "new OfflineAudioContext(2,Math.ceil(len*sr),sr));await wlLoad(oc);if(S.seed==null)S.seed=(Math.random()*1e9)|0;SEEDR=UI.exSeed===false?null:seedRng(S.seed+'|'+b0.toFixed(6)",
           "new OfflineAudioContext(2,Math.ceil(len*sr),sr));await wlLoad(oc);SIDE_B0=b0;/* SIDE_B0 again after the await: another render may have set it meanwhile (fix of the Fractals export flake, 28 Nov) */if(S.seed==null)S.seed=(Math.random()*1e9)|0;SEEDR=UI.exSeed===false?null:seedRng(S.seed+'|'+b0.toFixed(6)")
s = rep(s, "const oc=quietMeters(new OfflineAudioContext(2*nT,Math.ceil(len*sr),sr));await wlLoad(oc);SIDE_B0=bs;",
           "SIDE_B0=bs;const oc=quietMeters(new OfflineAudioContext(2*nT,Math.ceil(len*sr),sr));await wlLoad(oc);SIDE_B0=bs;")
open(P, 'w', encoding='utf-8').write(s); print('SIDE_B0 fix applied')
