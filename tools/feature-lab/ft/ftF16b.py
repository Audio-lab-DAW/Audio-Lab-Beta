#!/usr/bin/env python3
"""Task FT-F16b (lane C): Volume shaper, part 2 (note and sound triggers, up to three bands). Anchored edit of lane C's own F16a block plus
   a new block after it; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftF16b.py [index.html] [version]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
VER = sys.argv[2] if len(sys.argv) > 2 else None
H = os.path.dirname(os.path.abspath(__file__))
rd = lambda n: open(os.path.join(H, n), encoding='utf-8').read().rstrip('\n')
s = open(F, encoding='utf-8').read()
if 'task FT-F16b)' in s: sys.exit('already applied')
assert 'task FT-F16a)' in s, 'FT-F16a is not in this file'
def one(a):
    assert s.count(a) == 1, (a[:80], s.count(a)); return s.index(a)
# 1. the worklet (whole string constant)
a = "const FTVS_WL=`/* ===== AudioLab volume shaper (task FT-F16a) ===== */"; e = "registerProcessor('al-ftvs',FtVs)})();`;"
i = one(a); j = s.index(e, i) + len(e); assert j - i < 8000
s = s[:i] + rd('ftF16b_wl.js') + s[j:]
# 2. anchor, parameters and the node (one stretch from ftVsAnchor to the end of ftVsNode)
a = "function ftVsAnchor(c){"; e = "  if(off){(c._ftvsQ=c._ftvsQ||[]).push(mk);ftVsLoad(c)}else ftVsLoad(c).then(mk);\n  return X}"
i = one(a); j = one(e) + len(e); assert 0 < j - i < 4000
mid = s[i:j]
for k in ["const ftVsTm=", "const ftVsP=(p,sr)=>", "function ftVsNode(c){"]: assert k in mid or k == "const ftVsTm=", k
# ftVsTm sits between the worklet loader and ftVsAnchor in F16a; keep anything in the stretch that is not ours to replace
keep = mid[mid.index("\n", mid.index("function ftVsAnchor(c){")) + 1: mid.index("const ftVsP=(p,sr)=>")]
assert keep.strip() == '', keep[:200]
s = s[:i] + rd('ftF16b_node.js') + s[j:]
# 3. the display: caption, where the curve is, the trigger meter
a = "txt(g,cn+' per cycle, from the bar line',x0+52,T-5,L.mut,9);"; one(a)
s = s.replace(a, "ftVsDrawX(g,w,h,p,X,T,B,x1);txt(g,ftVsCap(p,cn),x0+52,T-5,L.mut,9);")
a = "let ph=null;if(X&&performance.now()-X.tm<300)ph=X.x;else if(play.on&&ctx){let q=curDisp()/cb+(+p.phase||0)/100;ph=q-Math.floor(q)}"; one(a)
s = s.replace(a, "let ph=ftVsPh(p,X,cb);")
# 4. the new block after the F16a hook line
a = "FT_HOOKS.volumeShaper={type:'ftvs',beats:ftVsBeats,"
i = one(a); j = s.index("\n", i) + 1
blk = rd('ftF16b_block.js')
if VER: blk = blk.replace('/* v0.295 (task FT-F16b)', '/* v%s (task FT-F16b)' % VER, 1)
s = s[:j] + blk + "\n" + s[j:]
open(F, 'w', encoding='utf-8').write(s); print('FT-F16b applied')
