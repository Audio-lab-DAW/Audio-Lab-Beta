"""Task IN-L fix 1 (lane E, 28 Nov, for task RG): the loudness history (INL) missed a Reset about 1 time in 3.
INL cleared itself only when the new LM.hist was still empty at its 100 ms tick, but the master meter pushes into LM.hist every 250 ms,
so a push landing first kept the old history (the gate's taskIN_L.py flake: 120/122 after Reset, stray cyan in the EBU check).
LM.hist is only ever reassigned by a Reset, so a new array always means a reset.
  python3 tools/design-lab/in/in_l_fix1.py [index.html]"""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
NEW = "if(LM.hist!==INL.ref){INL.ref=LM.hist;INL.n=0;INL.i=0/* IN-L fix 1: a new LM.hist is always a reset */}"
if NEW in s: print('IN-L fix 1 already applied'); sys.exit(0)
OLD = "if(LM.hist!==INL.ref){INL.ref=LM.hist;if(!LM.hist.length){INL.n=0;INL.i=0}}"
assert s.count(OLD) == 1, s.count(OLD)
assert s.count("LM.hist=") == 2, s.count("LM.hist=")  # both are resets (the pop-up's Reset, the analyser menu's)
s = s.replace(OLD, NEW); open(P, 'w', encoding='utf-8').write(s); print('IN-L fix 1 applied')
