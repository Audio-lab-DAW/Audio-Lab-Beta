"""Task NI-31 (lane D): X18 high-pass hints with a one-click cut (AE3 pick).
Edit script with unique asserted anchors (needs NI-9 in the file), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_31.py [index.html]
Adds (JS from ni_31_block.js, after the NI-9 block): a window "High-pass hints" (#niHp) from the main menu and the command ni.hpHints;
per track over the whole song (NI-8's per-track sums of NI-3's bands) the share of level under a line it does not need (0.6 times its
lowest note, or 150 Hz without notes; never kicks, basses, subs, drum kits); a button per hint adds a gentle high-pass (12 dB/oct) on the
track's Pro EQ, one undo step; NI_HOOKS.hpHints.
"""
import sys, os
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* ===== lane D (task NI-31)' in s:
    print('NI-31 already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-9 ===== */' in s, 'NI-9 must be in the file first'
def rep(s, old, new):
    n = s.count(old)
    assert n == 1, (old[:70], n)
    return s.replace(old, new)
A1 = "{id:'ni.harmonicRuler',g:'view',"
s = rep(s, A1, "{id:'ni.hpHints',g:'view',l:'High-pass hints (tracks with low end they do not need, one-click gentle cut)',d:'',ic:'M2 15c3 0 4-9 7-9h9',run:()=>NI_hpOpen()},\n " + A1)
A2 = "   {label:NI_hrOn()?'Harmonic ruler: on'"
s = rep(s, A2, "   {label:'High-pass hints…',sub:'low end a track does not need, with a one-click gentle cut',ic:I('M2 15c3 0 4-9 7-9h9','#3ecf8e'),act:()=>NI_hpOpen()},\n" + A2)
CSS = r"""/* lane D (task NI-31): high-pass hints */
#niHp .fwb{flex-direction:column;gap:6px;padding:6px 10px 10px;overflow:auto}
#niHp .nht{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:var(--fs1);color:var(--mut)}#niHp .nht button{min-height:22px;padding:0 8px;font-size:var(--fs1)}
#niHp .nhst{margin-left:auto;font-variant-numeric:tabular-nums;white-space:nowrap}
#niHp .nhg{display:grid;grid-template-columns:minmax(80px,1fr) minmax(160px,2.6fr) auto;gap:4px 10px;align-items:center;font-size:var(--fs1)}
#niHp .nhnm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#d9dce3;display:flex;align-items:center;gap:5px;cursor:pointer}#niHp .nhnm i{flex:none;width:9px;height:9px;border-radius:2px;background:var(--c)}
#niHp .nhw{color:var(--mut);font-variant-numeric:tabular-nums}#niHp .nhw b{color:#ffb547;font-weight:var(--fw6)}
#niHp .nhg button{min-height:22px;padding:0 8px;font-size:var(--fs1);white-space:nowrap}
#niHp .nhempty{grid-column:1/-1;color:#4cc9f0}#niHp .nhs,#niHp .nhnote{font-size:var(--fs1);color:var(--mut);line-height:1.35}
"""
s = rep(s, ".dacv{display:flex;", CSS + ".dacv{display:flex;")
JS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ni_31_block.js'), encoding='utf-8').read()
A3 = '/* ===== end of lane D NI-9 ===== */'
s = rep(s, A3, A3 + JS.rstrip('\n'))
open(P, 'w', encoding='utf-8').write(s)
print('NI-31 applied')
