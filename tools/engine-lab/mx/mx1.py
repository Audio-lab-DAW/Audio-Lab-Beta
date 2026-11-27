#!/usr/bin/env python3
"""Task MX-1 (lane K, mixing engine): X12 pre or post per send, X13 output to any group, return or track.
Re-runnable on a fresh index.html: every anchor is asserted unique; a file that already has MX-1 is left alone.
   python3 tools/engine-lab/mx/mx1.py [index.html]"""
import sys
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
if '/* ===== task MX-1 (lane K' in s:
    print('MX-1 already in', F); sys.exit(0)

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:120])
    s = s.replace(old, new)

# 1. busRoute: outputs from t.out, pre sends from the track before its fader, one loop check
a = s.index('function busRoute(){if(!ctx)return;'); b = s.index('\nconst RETN=', a)
old = s[a:b]
assert old.count('function ') == 1 and 'N.snd' in old
s = s[:a] + r"""function busRoute(){if(!ctx)return;const solo=S.tracks.some(t=>t.solo);for(const t of S.tracks){const N=NODES.get(t.id);if(!N)continue;const d=mxDestT(t),D=d&&NODES.get(d.id),dest=D?D.in:master;
    if(N.dest!==dest){try{N.pan.disconnect(N.dest||master)}catch(e){}N.pan.connect(dest);N.dest=dest}
    N.snd=N.snd||new Map();const want=t.kind==='return'?{}:(t.sends||{}),pre=t.sendPre||{};/* MX-1: a send in t.sendPre is taken before the fader (N.mxPre, after effects, compensation and the utility) */
    for(const[rid,sg] of N.snd){const R=NODES.get(rid);if(!(want[rid]>0)||!R||sg._to!==R.in||!!sg._pre!==!!pre[rid]||!mxSendOk(t,rid)){try{(sg._from||N.pan).disconnect(sg)}catch(e){}try{sg.disconnect()}catch(e){}N.snd.delete(rid)}}
    let np=false;for(const rid in want)if(pre[rid]&&want[rid]>0){np=true;break}
    if(np&&!N.mxPre){N.mxPre=ctx.createGain();N.mxPre.gain.value=0;N.mxPreC=false}
    if(N.mxPre){const on=!N.slp;if(!!N.mxPreC!==on){try{on?N.ut.out.connect(N.mxPre):N.ut.out.disconnect(N.mxPre)}catch(e){}N.mxPreC=on}N.mxPre.gain.setTargetAtTime(np&&trkAudible(t,solo)?1:0,ctx.currentTime,.01)}
    for(const rid in want){const R=NODES.get(rid),lv=want[rid];if(!R||rid===t.id||!(lv>0)||!mxSendOk(t,rid))continue;let sg=N.snd.get(rid);if(!sg){const pr=!!pre[rid],fr=pr?N.mxPre:N.pan;sg=ctx.createGain();sg.gain.value=0;fr.connect(sg);sg.connect(R.in);sg._to=R.in;sg._pre=pr;sg._from=fr;N.snd.set(rid,sg)}sg.gain.setTargetAtTime(lv,ctx.currentTime,.01)}}}""" + s[b:]

# 2. the loop check follows outputs too (abxReach is used by the Ducker, outputs and sends)
rep("if(x===a)return true;const g=grpOf(x);if(g)st.push(g);", "if(x===a)return true;const g=mxRawDest(x);if(g)st.push(g);")

# 3. renderMix: the utility (width, phase, trim) when not neutral, outputs, pre sends
rep("prev.connect(vol);vol.connect(pn);NN.set(t.id,{tin,pn,pre:prev});", "prev=mxUtilOff(oc,t,prev);prev.connect(vol);vol.connect(pn);NN.set(t.id,{tin,pn,pre:prev,aud:_aud});")
rep("const gp=only?null:grpOf(t),G=gp&&NN.get(gp.id);n.pn.connect(G?G.tin:mst);", "const gp=only?null:mxDestT(t),G=gp&&NN.get(gp.id);if(!(gp&&!G&&mxOutT(t)))n.pn.connect(G?G.tin:mst);")
rep("const sg=oc.createGain();sg.gain.value=lv;n.pn.connect(sg);sg.connect(R.tin)}", "if(!mxSendOk(t,rid))continue;const pr=!!(t.sendPre&&t.sendPre[rid]),sg=oc.createGain();sg.gain.value=pr?(n.aud?lv:0):lv;(pr?n.pre:n.pn).connect(sg);sg.connect(R.tin)}")

# 4. mixer strips: the output button and the blue and yellow rings on the sends
rep("mx.classList.toggle('gm',!!grpOf(t));\n    if(t.kind==='return'||!R.length)continue;", "mx.classList.toggle('gm',!!grpOf(t));try{mxOutBtn(mx,t)}catch(e){console.error(e)}\n    if(t.kind==='return'||!R.length)continue;")
rep("const after=mx.querySelector('.mxi')||mx.querySelector('.mxn');after.after(box);paintAll(box)}}", "const after=mx.querySelector('.mxi')||mx.querySelector('.mxn');after.after(box);paintAll(box);try{mxRings(box,t)}catch(e){console.error(e)}}}")

# 5. the cable menu: Play straight into the Master undoes an output; Play into a return or a track
rep("if(b==='master'){const g=grpOf(a);if(g)it.push({ic:'mst'", "if(b==='master'){if(mxOutT(a)){it.push({ic:'mst',col:'#cfd3db',main:true,t:'Play straight into the Master',d:a.name+' stops playing into '+mxOutT(a).name+' and plays straight into the Master.',act:()=>mxSetOut(a,'master')});return it}const g=grpOf(a);if(g)it.push({ic:'mst'")
rep(" if(b.kind==='group'&&a.kind!=='return'){if(grpOf(a)===b)it.push({ic:'grp'", " mxOptsOut(a,b,it);\n if(b.kind==='group'&&a.kind!=='return'){if(grpOf(a)===b)it.push({ic:'grp'")

# 6. new JS and CSS
JS = open(__file__.replace('mx1.py', 'mx1.js'), encoding='utf-8').read()
rep("function askChoice(title,text,btns,icon){", JS + "function askChoice(title,text,btns,icon){")
CSS = (".mxsr{display:flex;align-items:center;gap:4px}.mxsr>.hb{flex:1;min-width:0}"
       ".mxpp{flex:none;box-sizing:border-box;width:11px;height:11px;min-width:0;min-height:0;padding:0;margin:0;border-radius:50%;border:2px solid #f5c84c;background:transparent;cursor:pointer}"
       ".mxpp.pre{border-color:#4cc9f0;background:rgba(76,201,240,.18)}.mxpp:hover{box-shadow:0 0 0 2px rgba(255,255,255,.16)}.mxpp:focus-visible{outline:2px solid #fff;outline-offset:1px}"
       ".hb.mxlp{opacity:.45}"
       ".mxout{display:flex;align-items:center;gap:4px;box-sizing:border-box;width:100%;min-height:0;margin:3px 0 0;padding:2px 5px;border-radius:5px;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.03);font:var(--fw6) var(--fs1)/12px var(--ffu);color:#9aa0ad;cursor:pointer;text-align:left}"
       ".mxout i{flex:none;width:6px;height:6px;border-radius:50%;background:var(--oc,#cfd3db)}.mxout span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.mxout b{flex:none;font-weight:400;opacity:.6}"
       ".mxout:hover{color:#eef1f6;border-color:rgba(255,255,255,.2)}.mxout.set{color:#eef1f6;border-color:rgba(255,255,255,.18)}.mxout.bad{border-color:#ff6b6b}"
       "#mixWin.mxcmp .mx .mxout{display:none}\n")
rep(".dacv{display:flex;", CSS + ".dacv{display:flex;")
open(F, 'w', encoding='utf-8').write(s)
print('MX-1 written to', F)
