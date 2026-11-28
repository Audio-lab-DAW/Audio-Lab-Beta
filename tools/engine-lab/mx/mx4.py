#!/usr/bin/env python3
"""Task MX-4 (lane K, mixing engine): X3 the Ducker's Spectral focus (32 bands) and X19's Bass mono switch (tracks and master),
with MX_HOOKS.bandFilter for lane E's band listen (X17). Needs MX-3. Re-runnable on a fresh index.html: every anchor is asserted unique;
a file that already has MX-4 is left alone.
   python3 tools/engine-lab/mx/mx4.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
if '/* ===== task MX-4 (lane K' in s:
    print('MX-4 already in', F); sys.exit(0)
assert '/* ===== task MX-3 (lane K' in s, 'MX-4 needs MX-3'
D = os.path.dirname(os.path.abspath(__file__))

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:140])
    s = s.replace(old, new)

# 1. the Ducker's worklet: the Spectral path (focus 4) as its own methods; the other focus modes run exactly the code they ran before
WL = open(os.path.join(D, 'mx4_wl.js'), encoding='utf-8').read()
rep("  process(ins,outs){const o=outs[0];if(!o||!o[0])return true;const oL=o[0],oR=o[1]||o[0],n=oL.length,m=ins[0]||[],k=ins[1]||[],mL=m[0],mR=m[1]||m[0],kL=k[0],kR=k[1]||k[0],N=this.N,la=this.la,bL=this.bL,bR=this.bR;",
    WL + "  process(ins,outs){const o=outs[0];if(!o||!o[0])return true;if(this.fo===4)return this.mxSp(ins,outs);const oL=o[0],oR=o[1]||o[0],n=oL.length,m=ins[0]||[],k=ins[1]||[],mL=m[0],mR=m[1]||m[0],kL=k[0],kR=k[1]||k[0],N=this.N,la=this.la,bL=this.bL,bR=this.bR;")
# 2. the focus value, the menu entry, a preset, the band gains from the worklet, the latency
rep("const ABXFO={all:0,low:1,band:2,high:3};", "const ABXFO={all:0,low:1,band:2,high:3,spec:4};")
rep("[['all','Everything'],['low','Lows (kick, bass)'],['band','One band'],['high','Highs (hats, snare)']]]", "[['all','Everything'],['low','Lows (kick, bass)'],['band','One band'],['high','Highs (hats, snare)'],['spec','Spectral (32 bands)']]]")
rep("['bass','Bass under kick (fast)',{amt:90,th:-30,gain:0,at:0,hd:20,rl:120,cv:20,la:2,ff:100,fo:'low',ls:false}]]",
    "['bass','Bass under kick (fast)',{amt:90,th:-30,gain:0,at:0,hd:20,rl:120,cv:20,la:2,ff:100,fo:'low',ls:false}],['mxspec','Bass under kick (spectral)',{amt:90,th:-40,gain:0,at:1,hd:20,rl:120,cv:0,la:0,ff:100,fo:'spec',ls:false}]]")
rep("n.port.onmessage=e=>{const d=e.data;if(!d)return;X.m.k=d.k;X.m.g=d.g;", "n.port.onmessage=e=>{const d=e.data;if(!d)return;X.m.k=d.k;X.m.g=d.g;if(d.b)X.mxSB=d.b;")
rep("if(f&&f.on&&f.type==='duck')return Math.round((+(f.p&&f.p.la)||0)*sr/1000);",
    "if(f&&f.on&&f.type==='duck')return Math.round((+(f.p&&f.p.la)||0)*sr/1000)+(f.p&&f.p.fo==='spec'?mxSpecN(sr):0);")
# 2b. the sidechain window (both layouts) offers Spectral too; the Focus dial is only for Lows, One band and Highs
rep("['high','Highs','Listen only to the top of '+sn+' (hats, snare)']]", "['high','Highs','Listen only to the top of '+sn+' (hats, snare)'],['spec','Spectral','Spectral (32 bands): '+t.name+' goes down only in the frequencies where '+sn+' plays, so a kick takes the bass out under itself and leaves the rest alone. Adds about 20 ms of latency, which the other tracks wait for']]", 2)
rep("fo!=='all'?", "fo!=='all'&&fo!=='spec'?", 2)
# 3. Bass mono: the utility names its merger (nothing else changes), the master chain and the export start from MX-4's functions
rep("m.connect(o);\n  let k='';return{in:i,out:o,set(t){", "m.connect(o);\n  let k='';return{in:i,out:o,mxM:m,set(t){")
rep("for(const x of MFXM.values()){try{x.out.disconnect()}catch(e){}}let prev=master;for(const f of S.mfx||[]){", "for(const x of MFXM.values()){try{x.out.disconnect()}catch(e){}}let prev=mxBmMst(master);for(const f of S.mfx||[]){")
rep("const mst=oc.createGain();mst.gain.value=fast?1:masterGain();let out=mst;SPDEST.set(oc,mst);", "const mst=oc.createGain();mst.gain.value=fast?1:masterGain();let out=fast?mst:mxBmOff(oc,null,mst);SPDEST.set(oc,mst);")
rep("prev=mxUtilOff(oc,t,prev);prev.connect(vol);", "prev=mxBmOff(oc,t,mxUtilOff(oc,t,prev));prev.connect(vol);")
# 4. new JS and CSS
JS = open(os.path.join(D, 'mx4.js'), encoding='utf-8').read()
rep("function askChoice(title,text,btns,icon){", JS + "function askChoice(title,text,btns,icon){")
CSS = (".tdev2 .tdbs .mxbm{grid-column:span 3}"
       ".mxbm{display:flex;align-items:center;justify-content:space-between;gap:3px;box-sizing:border-box;min-width:0;height:20px;min-height:0;margin:0;padding:0 2px 0 6px;border-radius:6px;border:1px solid var(--ln);background:transparent;font:var(--fw5) var(--fs1)/12px var(--ffu);color:var(--mut);cursor:pointer;text-align:left;overflow:hidden}"
       ".mxbm>span{flex:0 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.mxbm b{flex:none;font-weight:400;opacity:.75;border-radius:4px;padding:1px 3px;white-space:nowrap}.mxbm b:hover{opacity:1;background:var(--ln)}"
       ".mxbm.on{color:var(--ink);border-color:#4cc9f0;background:rgba(76,201,240,.16)}.mxbm:hover{border-color:var(--mut)}.mxbm.on:hover{border-color:#8fe0fa}.mxbm:focus-visible{outline:2px solid var(--acc);outline-offset:1px}"
       "#fxin>.mxbmm{flex:none;align-self:flex-start;width:auto;margin:6px 4px 0 0}\n")
rep(".dacv{display:flex;", CSS + ".dacv{display:flex;")
open(F, 'w', encoding='utf-8').write(s)
print('MX-4 added to', F)
