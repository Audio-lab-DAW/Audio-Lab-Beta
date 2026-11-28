#!/usr/bin/env python3
"""Task MX-3 (lane K, mixing engine): X1 sidechain from anything (Compressor, Gate, Multiband, OTT, the EQ's dynamic bands; tap points; one loop
check) and X4 "Duck under the kick", tuned for tails (a switch on each return, the Output menu of its mixer strip, and the cable menu).
Needs MX-1 and MX-2. Re-runnable on a fresh index.html: every anchor is asserted unique; a file that already has MX-3 is left alone.
   python3 tools/engine-lab/mx/mx3.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
if '/* ===== task MX-3 (lane K' in s:
    print('MX-3 already in', F); sys.exit(0)
assert '/* ===== task MX-2 (lane K' in s, 'MX-3 needs MX-2'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:140])
    s = s.replace(old, new)

# 1. the loop check, the sources a render needs and the links list count every key (Ducker and sidechain)
rep("if(f.type==='duck'&&f.on&&f.p&&f.p.src===x.id)st.push(t)", "if(f.on&&mxKeySrcId(f)===x.id)st.push(t)")
rep("if(f.type==='duck'&&f.on&&f.p&&typeof f.p.src==='string')s.add(f.p.src)", "{const k=f.on&&mxKeySrcId(f);if(k)s.add(k)}")
rep("for(const f of t.fx||[])if(f&&f.type==='duck'&&f.p&&typeof f.p.src==='string'){const s=trkById(f.p.src);if(s&&s!==t)L.push({k:'sc',a:s,b:t,fx:f,pre:true,tap:'fx',lat:null})}",
    "for(const f of t.fx||[])if(f&&mxKeySrcId(f)){const s=trkById(mxKeySrcId(f));if(s&&s!==t)L.push({k:'sc',a:s,b:t,fx:f,pre:true,tap:mxTapOf(f),lat:null})}")

# 2. MX-2's plan: every key edge (with its tap point: a key taken before the source's effects is ready earlier)
rep("if(f.type==='duck'&&f.p&&typeof f.p.src==='string'){const s=byId.get(f.p.src);if(s&&s!==t&&!abxReach(t,s))add('key',s,t,{fx:f,pos})}",
    "{const sid=mxKeySrcId(f),s=sid&&byId.get(sid);if(s&&s!==t&&!abxReach(t,s))add('key',s,t,{fx:f,pos,tl:mxTapLat(s,f,sr)})}")
rep("const need=E.k==='key'?a-E.pos:a;", "const need=E.k==='key'?(E.tl==null?a:a-R.L.get(E.a.id)+E.tl)-E.pos:a;")
rep("let ro=Infinity;for(const E of ed){const v=req(E);if(v<ro)ro=v}", "let ro=Infinity;for(const E of ed){if(E.tl!=null)continue;const v=req(E);if(v<ro)ro=v}")
rep("const e=Math.max(0,Math.min(sr,req(E)-(ii+L+dd)));", "const e=Math.max(0,Math.min(sr,req(E)-(E.tl!=null?ii+E.tl:ii+L+dd)));")

# 3. renderMix: keyed devices get their key from the chosen tap, with the plan's delay
rep("FXN.set(f.id,{x,f,t});if(f.type==='duck'&&x.key)ABD.push([x,f.p&&f.p.src,t.id,f.id])}",
    "FXN.set(f.id,{x,f,t});if(f.type==='duck'&&x.key)ABD.push([x,f.p&&f.p.src,t.id,f.id]);else if(mxScOk(f)){const M=mxKeyUp(oc,x,f);if(M)ABD.push([M,f.p.sc.src,t.id,f.id,f])}}")
rep("for(const[x,sid,tid,fid] of ABD){const n=NN.get(sid);if(n&&sid!==tid&&!abxReach(trkById(tid),trkById(sid)))mxOffD(oc,n.pre,x.key,PX?PX.ek.get(fid):0)}",
    "for(const[x,sid,tid,fid,ff] of ABD){const n=NN.get(sid);if(n&&sid!==tid&&!abxReach(trkById(tid),trkById(sid)))mxOffD(oc,ff?mxTapOff(n,ff,FXN):n.pre,x.key,PX?PX.ek.get(fid):0)}")

# 4. OTT: its band compressors and gains, for the keyed stage (a named field, nothing else changes)
rep("return{in:i,out,an:oan,bands:an,comps:bands.map(b=>b.k),set:p=>{", "return{in:i,out,an:oan,bands:an,comps:bands.map(b=>b.k),mxB:bands,set:p=>{")

# 4b. the Compressor's inner output and a worklet effect's inner output (the generic Gain stage replaces .out): named fields for the keyed stage
rep("return{in:i,out:g,an,k,set:p=>{k.threshold.value=p.threshold;", "return{in:i,out:g,mxG:g,an,k,set:p=>{k.threshold.value=p.threshold;")
rep("const i=c.createGain(),out=c.createGain(),w={in:i,out,node:null,", "const i=c.createGain(),out=c.createGain(),w={in:i,out,mxO:out,node:null,")

# 5. new JS and CSS
JS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mx3.js'), encoding='utf-8').read()
rep("function askChoice(title,text,btns,icon){", JS + "function askChoice(title,text,btns,icon){")
CSS = (".mxscr{display:flex;margin:3px 0 0}"
       ".mxscb{display:flex;align-items:center;gap:4px;box-sizing:border-box;width:100%;min-width:0;min-height:0;margin:0;padding:2px 5px;border-radius:5px;border:1px solid var(--ln);background:transparent;font:var(--fw5) var(--fs1)/12px var(--ffu);color:var(--mut);cursor:pointer;text-align:left}"
       ".mxscb .mxscl{flex:none;opacity:.8}.mxscb i{flex:none;width:6px;height:6px;border-radius:50%;background:var(--sc);box-shadow:inset 0 0 0 1px var(--mut)}.mxscb.set i{box-shadow:none}"
       ".mxscb .mxscn{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.mxscb b{flex:none;font-weight:400;opacity:.6}"
       ".mxscb:hover,.mxscb.set{color:var(--ink)}.mxscb:hover{border-color:var(--mut)}.mxscb.bad{border-color:#ff6b6b}.mxscb:focus-visible{outline:2px solid var(--acc);outline-offset:1px}"
       ".mxtail{display:flex;align-items:center;gap:5px;box-sizing:border-box;width:100%;min-height:0;margin:4px 0 0;padding:2px 6px;border-radius:5px;border:1px solid var(--ln);background:transparent;font:var(--fw5) var(--fs1)/12px var(--ffu);color:var(--mut);cursor:pointer;text-align:left}"
       ".mxtail i{flex:none;width:14px;height:8px;border-radius:4px;background:var(--ln);position:relative}.mxtail i:after{content:'';position:absolute;left:1px;top:1px;width:6px;height:6px;border-radius:50%;background:var(--mut)}"
       ".mxtail.on{color:var(--ink)}.mxtail.on i{background:#ff7a7a}.mxtail.on i:after{left:7px;background:#fff}.mxtail span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}"
       ".mxtail:focus-visible{outline:2px solid var(--acc);outline-offset:1px}\n")
rep(".dacv{display:flex;", CSS + ".dacv{display:flex;")
open(F, 'w', encoding='utf-8').write(s)
print('MX-3 added to', F)
