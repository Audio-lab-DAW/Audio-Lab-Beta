#!/usr/bin/env python3
"""Task MX-5 (lane K, mixing engine): Dual Path Latency (the user's play-through idea; docs/mixing-build.md, last sections).
Needs MX-2, MX-3 and MX-4. Re-runnable on a fresh index.html: every anchor is asserted unique; a file that already has MX-5 is left alone.
   python3 tools/engine-lab/mx/mx5.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
if '/* ===== task MX-5 (lane K' in s:
    print('MX-5 already in', F); sys.exit(0)
for k in ('MX-2', 'MX-3', 'MX-4'):
    assert '/* ===== task %s (lane K' % k in s, 'MX-5 needs ' + k

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:140])
    s = s.replace(old, new)

# syncGraph: the set() wrapper on every device node, the chain's signature, the two paths taken down and wired
rep("for(const f of t.fx)if(!N.fxm.has(f.id))N.fxm.set(f.id,mkFxNode(ctx,f.type));",
    "for(const f of t.fx)if(!N.fxm.has(f.id))N.fxm.set(f.id,mkFxNode(ctx,f.type));try{mxDplWrap(N,t)}catch(e){}")
rep("const sig=(N.mxh?'H|':'')+", "const sig=mxDplSig(t)+(N.mxh?'H|':'')+")
rep("if(sig!==N.sig){N.sig=sig;", "if(sig!==N.sig){N.sig=sig;mxDplCut(N);")
rep("const x=N.fxm.get(f.id);prev.connect(x.in);prev=x.out}prev.connect(N.pdc)}",
    "const x=N.fxm.get(f.id);prev=mxDplLink(N,t,f,x,prev)}prev.connect(N.pdc)}")
JS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mx5.js'), encoding='utf-8').read()
rep("function askChoice(title,text,btns,icon){", JS + "function askChoice(title,text,btns,icon){")
CSS = (".mxtag{display:inline-flex;align-items:center;gap:3px;margin-left:8px;vertical-align:1px;font:var(--fw5,500) 9.5px/1 var(--ffu);letter-spacing:.02em;color:var(--mut);opacity:.85;cursor:help;text-transform:none}"
       ".mxatom{width:11px;height:11px;flex:none}"
       ".mxdplfirst{margin:8px 0 2px;padding:8px 10px;border:1px solid var(--line,rgba(127,127,127,.25));border-radius:8px}.mxdplfirst p{margin:4px 0}"
       ".mxdplpic{display:block;width:100%;max-width:300px;height:auto;margin:0 0 4px}.mxdplpic text{font:9px var(--ffu);fill:var(--mut)}.mxdplpic text.lo{fill:var(--unit,var(--mut))}"
       ".mxdplpic .ax{stroke:var(--mut);stroke-width:1;fill:none;opacity:.5}.mxdplpic .fa{fill:var(--acc,#5aa9ff);opacity:.85}.mxdplpic .sl{fill:var(--mut);opacity:.55}.mxdplpic .ar{stroke:var(--mut);stroke-width:1.2;fill:none}"
       ".mxab{margin:12px 0 6px;color:var(--mut)}.mxabH{display:flex;align-items:center;gap:5px;font:var(--fw5,500) 10px/1 var(--ffu);letter-spacing:.04em}.mxab .mxatom{width:12px;height:12px}"
       ".mxabR{display:flex;flex-wrap:wrap;gap:2px 8px;align-items:baseline;margin-top:5px;font-size:var(--fs1,11px)}.mxabR b{color:var(--txt,inherit);font-weight:600}.mxabBy{opacity:.8}\n")
rep(".dacv{display:flex;", CSS + ".dacv{display:flex;")
open(F, 'w', encoding='utf-8').write(s)
print('MX-5 added to', F)
