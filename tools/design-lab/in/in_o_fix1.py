"""Task IN-O follow-up (lane E): the phase angle from the value as shown. acos is steep near +1 and -1, so the angle of the unrounded
correlation could read "-1.00  175°" or "+1.00  6°"; the angle is now taken from the two-decimal value it sits beside (-1.00 is 180°).
Edits index.html and tools/design-lab/in/in_o_block.js (so in_o.py re-applies the same code). Unique asserted anchors.
  python3 tools/design-lab/in/in_o_fix1.py [index.html]"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
EDITS = [("const ang=Math.acos(c)*180/Math.PI,", "const ang=Math.acos(Math.round(c*100)/100)*180/Math.PI,/* IN-O fix: the angle of the value as shown */"),
         ("Math.round(Math.acos(Math.max(-1,Math.min(1,v)))*180/Math.PI)", "Math.round(Math.acos(Math.max(-1,Math.min(1,Math.round(v*100)/100)))*180/Math.PI)")]
for f in (P, os.path.join(HERE, 'in_o_block.js')):
    s = open(f, encoding='utf-8').read()
    if 'IN-O fix: the angle of the value as shown' in s:
        print(os.path.basename(f), 'already fixed'); continue
    for a, b in EDITS:
        assert s.count(a) == 1, (f, a, s.count(a))
        s = s.replace(a, b)
    open(f, 'w', encoding='utf-8').write(s); print(os.path.basename(f), 'fixed')
