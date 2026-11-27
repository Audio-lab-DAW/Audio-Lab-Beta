#!/usr/bin/env python3
"""Task MX-2 (lane K, mixing engine): X5 delay compensation for every path (outputs, sends, returns, Ducker triggers), X6 latency you can see
(a small read-out in the track's first device), and device automation (S.pauto) rendered in exports.
Needs MX-1. Re-runnable on a fresh index.html: every anchor is asserted unique; a file that already has MX-2 is left alone.
   python3 tools/engine-lab/mx/mx2.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
if '/* ===== task MX-2 (lane K' in s:
    print('MX-2 already in', F); sys.exit(0)
assert '/* ===== task MX-1 (lane K' in s, 'MX-2 needs MX-1'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:140])
    s = s.replace(old, new)

def func(head, nxt):
    """the text of one function from its head to the next anchor"""
    a = s.index(head); assert s.count(head) == 1, head
    b = s.index(nxt, a); return a, b

# 1. pdcMap: one plan for the whole graph (mxSolve); same signature plus lane J's live flag, same result for tracks
a, b = func('function pdcMap(sr){', '\n/* Level meter colours')
old = s[a:b]; assert old.count('function ') == 1 and 'grpAnc(t)' in old, old[:200]
s = s[:a] + "function pdcMap(sr,live){const M=new Map();M.target=0;const X=mxSolve(sr,!!live);if(live)MXSOL=X;M.mx=X;if(UI.pdc===false)return M;M.target=X.T;for(const[id,d] of X.d)if(d>0)M.set(id,d);return M}" + s[b:]

# 2. syncGraph: the live plan, the input delay (head) and the fading track delay
rep("const solo=S.tracks.some(t=>t.solo),PDC=pdcMap(ctx.sampleRate);CPU.pdc=PDC.target/ctx.sampleRate;",
    "const solo=S.tracks.some(t=>t.solo),PDC=pdcMap(ctx.sampleRate,true);CPU.pdc=PDC.target/ctx.sampleRate;")
rep("    const sig=(t.fxByp?'B|':'')+t.fx.map(f=>f.id+(f.on?'1':'0')).join(',');\n    if(sig!==N.sig){",
    "    try{mxHead(N,t,ctx.sampleRate)}catch(e){console.error('AudioLab delay compensation',e)}\n    const sig=(N.mxh?'H|':'')+(t.fxByp?'B|':'')+t.fx.map(f=>f.id+(f.on?'1':'0')).join(',');\n    if(sig!==N.sig){")
rep("      let prev=N.in;for(const f of t.fx){if(!f.on||(t.fxByp&&f.type!=='chord'&&f.type!=='arp'))continue;const x=N.fxm.get(f.id);prev.connect(x.in);prev=x.out}prev.connect(N.pdc)}",
    "      if(N.mxh){N.in.connect(N.mxcg);N.mxhIn=N.in}let prev=N.mxh||N.in;for(const f of t.fx){if(!f.on||(t.fxByp&&f.type!=='chord'&&f.type!=='arp'))continue;const x=N.fxm.get(f.id);prev.connect(x.in);prev=x.out}prev.connect(N.pdc)}")
rep("    {const d=(PDC.get(t.id)||0)/ctx.sampleRate;if(d!==N.pdcV){N.pdcV=d;N.pdc.delayTime.setValueAtTime(d,ctx.currentTime)}}",
    "    {const d=(PDC.get(t.id)||0)/ctx.sampleRate;if(d!==N.pdcV)mxPdcSet(N,d)}")
rep("  busRoute();spSync();\n}", "  busRoute();spSync();try{mxLatPaint()}catch(e){}\n}")

# 3. busRoute: outputs and sends get their own delay when the plan asks for one; inputs after a track's input delay
a, b = func('function busRoute(){if(!ctx)return;', '\nconst RETN=')
old = s[a:b]; assert 'MX-1: a send in t.sendPre' in old and old.count('function ') == 1
s = s[:a] + r"""function busRoute(){if(!ctx)return;const solo=S.tracks.some(t=>t.solo),X=MXSOL,sr=ctx.sampleRate;for(const t of S.tracks){const N=NODES.get(t.id);if(!N)continue;const d=mxDestT(t),D=d&&NODES.get(d.id),dest=D?mxInOf(D):master;
    {const e=X?(X.eo.get(t.id)||0)/sr:0;if(e>0&&!N.mxOE){const E=mxEdge();try{N.pan.disconnect(N.dest||master)}catch(err){}N.pan.connect(E.g);E.d.connect(N.dest||master);N.mxOE=E}/* MX-2: the output's own delay */
     const fr=N.mxOE?N.mxOE.d:N.pan;if(N.dest!==dest){try{fr.disconnect(N.dest||master)}catch(err){}fr.connect(dest);N.dest=dest}if(N.mxOE)mxDSet(N.mxOE.d,N.mxOE.g,e)}
    N.snd=N.snd||new Map();const want=t.kind==='return'?{}:(t.sends||{}),pre=t.sendPre||{};/* MX-1: a send in t.sendPre is taken before the fader (N.mxPre, after effects, compensation and the utility) */
    for(const[rid,sg] of N.snd){const R=NODES.get(rid);if(!(want[rid]>0)||!R||sg._to!==mxInOf(R)||!!sg._pre!==!!pre[rid]||!mxSendOk(t,rid)){try{(sg._from||N.pan).disconnect(sg)}catch(e){}try{sg.disconnect()}catch(e){}if(sg._E){try{sg._E.d.disconnect()}catch(e){}}N.snd.delete(rid)}}
    let np=false;for(const rid in want)if(pre[rid]&&want[rid]>0){np=true;break}
    if(np&&!N.mxPre){N.mxPre=ctx.createGain();N.mxPre.gain.value=0;N.mxPreC=false}
    if(N.mxPre){const on=!N.slp;if(!!N.mxPreC!==on){try{on?N.ut.out.connect(N.mxPre):N.ut.out.disconnect(N.mxPre)}catch(e){}N.mxPreC=on}N.mxPre.gain.setTargetAtTime(np&&trkAudible(t,solo)?1:0,ctx.currentTime,.01)}
    for(const rid in want){const R=NODES.get(rid),lv=want[rid];if(!R||rid===t.id||!(lv>0)||!mxSendOk(t,rid))continue;let sg=N.snd.get(rid);if(!sg){const pr=!!pre[rid],fr=pr?N.mxPre:N.pan,to=mxInOf(R);sg=ctx.createGain();sg.gain.value=0;fr.connect(sg);sg.connect(to);sg._to=to;sg._pre=pr;sg._from=fr;N.snd.set(rid,sg)}sg.gain.setTargetAtTime(lv,ctx.currentTime,.01)
      const e=X?(X.es.get(t.id+'>'+rid)||0)/sr:0;if(e>0&&!sg._E){const E=mxEdge();try{sg.disconnect(sg._to)}catch(err){}sg.connect(E.g);E.d.connect(sg._to);sg._E=E}if(sg._E)mxDSet(sg._E.d,sg._E.g,e)}}}""" + s[b:]

# 4. the Ducker's trigger: its own delay when the plan asks for one
a, b = func('function abxWire(){if(!ctx)return;', '\n{const _sg=syncGraph;syncGraph=function(){const r=_sg.apply(this,arguments);try{abxWire()}')
old = s[a:b]; assert old.count('function ') == 1 and 'X.ksrc=tap' in old
s = s[:a] + r"""function abxWire(){if(!ctx)return;const K=MXSOL,sr=ctx.sampleRate;for(const t of S.tracks){const N=NODES.get(t.id);if(!N)continue;for(const f of t.fx||[]){if(f.type!=='duck')continue;const X=N.fxm.get(f.id);if(!X||!X.key)continue;
   const s=abxSrc(f),SN=s&&s!==t?NODES.get(s.id):null,tap=SN&&!abxReach(t,s)?SN.ut.out:null,e=tap&&K?(K.ek.get(f.id)||0)/sr:0;/* MX-2: the trigger arrives with the sound it ducks */
   if(e>0&&!X.mxKE){const E=mxEdge();E.d.connect(X.key);if(X.ksrc){try{X.ksrc.disconnect(X.key)}catch(err){}X.ksrc.connect(E.g)}X.mxKE=E}
   const to=X.mxKE?X.mxKE.g:X.key;if(X.ksrc!==tap){if(X.ksrc){try{X.ksrc.disconnect(to)}catch(e){}}X.ksrc=tap;if(tap)tap.connect(to)}if(X.mxKE)mxDSet(X.mxKE.d,X.mxKE.g,e)}}}""" + s[b:]

# 5. renderMix: the same plan offline (input delays, link delays), automation, merged stops
rep("await wlLoad(oc);if(S.seed==null)S.seed=", "await wlLoad(oc);mxSuspWrap(oc);if(S.seed==null)S.seed=")
rep("const ABK=only||fast?new Set():abxKeys(),ABD=[];", "const ABK=only||fast?new Set():abxKeys(),ABD=[],FXN=new Map(),PX=PDC.mx||null;")
rep("pn.pan.value=t.pan;let prev=tin;", "pn.pan.value=t.pan;let prev=tin,hin=tin;{const cc=PX?PX.c.get(t.id)||0:0;if(cc>0){const dl=oc.createDelay(1);dl.delayTime.value=cc/sr;hin=oc.createGain();tin.connect(dl);dl.connect(hin);prev=hin}}")
rep("for(const f of fast?[]:t.fx){if(!f.on)continue;const x=mkFxNode(oc,f.type);x.set(f.p);prev.connect(x.in);prev=x.out;if(f.type==='duck'&&x.key)ABD.push([x,f.p&&f.p.src,t.id])}",
    "for(const f of fast?[]:t.fx){if(!f.on)continue;const x=mkFxNode(oc,f.type);x.set(f.p);prev.connect(x.in);prev=x.out;FXN.set(f.id,{x,f,t});if(f.type==='duck'&&x.key)ABD.push([x,f.p&&f.p.src,t.id,f.id])}")
rep("NN.set(t.id,{tin,pn,pre:prev,aud:_aud});", "NN.set(t.id,{tin,hin,pn,vol,pre:prev,aud:_aud});")
rep("if(!(gp&&!G&&mxOutT(t)))n.pn.connect(G?G.tin:mst);", "if(!(gp&&!G&&mxOutT(t)))mxOffD(oc,n.pn,G?G.hin:mst,PX?PX.eo.get(t.id):0);")
rep("(pr?n.pre:n.pn).connect(sg);sg.connect(R.tin)}", "(pr?n.pre:n.pn).connect(sg);mxOffD(oc,sg,R.hin,PX?PX.es.get(t.id+'>'+rid):0)}")
rep("for(const[x,sid,tid] of ABD){const n=NN.get(sid);if(n&&sid!==tid&&!abxReach(trkById(tid),trkById(sid)))n.pre.connect(x.key)}",
    "for(const[x,sid,tid,fid] of ABD){const n=NN.get(sid);if(n&&sid!==tid&&!abxReach(trkById(tid),trkById(sid)))mxOffD(oc,n.pre,x.key,PX?PX.ek.get(fid):0)}\n  try{mxPaPlan(oc,b0,NN,FXN,mst,fast)}catch(e){console.warn('AudioLab automation in export',e)}")

# 6. fxLat: the browser's compressor delays by 6 ms cut to whole samples (264 at 44.1 kHz, not 265): measured with an impulse
rep("case'comp':case'ott':return Math.round(.006*sr);", "case'comp':case'ott':return Math.floor(.006*sr+1e-6);")

# 7. new JS and CSS
JS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mx2.js'), encoding='utf-8').read()
rep("function askChoice(title,text,btns,icon){", JS + "function askChoice(title,text,btns,icon){")
CSS = (".tdev .devh .tdn .mxlat{flex:none;margin-left:2px;font:var(--fw5,500) 9.5px/1 var(--ffu);color:var(--mut);opacity:.85;cursor:help;font-variant-numeric:tabular-nums}"
       ".tdev .devh .tdn .mxlat .lku{color:inherit}.tdev .devh .tdn .mxlat.off{color:var(--unit);opacity:1}\n")
rep(".dacv{display:flex;", CSS + ".dacv{display:flex;")
open(F, 'w', encoding='utf-8').write(s)
print('MX-2 written to', F)
