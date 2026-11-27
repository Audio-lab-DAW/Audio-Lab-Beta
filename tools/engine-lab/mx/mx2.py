#!/usr/bin/env python3
"""Task MX-2 (lane K, mixing engine): device automation in export, delay compensation for every path (X5), latency read-out (X6).
Needs MX-1 in the file. Re-runnable on a fresh index.html: every anchor is asserted unique; a file that already has MX-2 is left alone.
   python3 tools/engine-lab/mx/mx2.py [index.html]"""
import sys
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
if '/* ===== task MX-2 (lane K' in s:
    print('MX-2 already in', F); sys.exit(0)
assert '/* ===== task MX-1 (lane K' in s, 'MX-1 first'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:140])
    s = s.replace(old, new)

# the old pdcMap (tracks and groups only) goes; the new one is in mx2.js
a = s.index('function pdcMap(sr){const M=new Map();M.target=0;if(UI.pdc===false)return M;'); b = s.index('return M}', a) + len('return M}')
assert s[a:b].count('function ') == 1 and b - a < 800
s = s[:a] + '/* pdcMap: task MX-2, one solve over every path (see the MX-2 block) */' + s[b:]

# syncGraph: the live map is kept for busRoute and the trigger wiring; the track's delay moves under a short dip while playing
rep("PDC=pdcMap(ctx.sampleRate);CPU.pdc", "PDC=MXPML=pdcMap(ctx.sampleRate,true);CPU.pdc")
rep("{const d=(PDC.get(t.id)||0)/ctx.sampleRate;if(d!==N.pdcV){N.pdcV=d;N.pdc.delayTime.setValueAtTime(d,ctx.currentTime)}}",
    "{const dd=(PDC.get(t.id)||0)/ctx.sampleRate,pr=!!N.mxPdOn,d=pr?0:dd,dp=pr?dd:0;if(d!==N.pdcV){N.pdcV=d;if(play.on)mxDelaySet(N.pdc,N.ut.in.gain,d,1);else N.pdc.delayTime.setValueAtTime(d,ctx.currentTime)}"
    "if(N.mxPd&&dp!==N.mxPdV){N.mxPdV=dp;if(play.on)mxDelaySet(N.mxPd,N.ut.in.gain,dp,1);else N.mxPd.delayTime.setValueAtTime(dp,ctx.currentTime)}}")
# a track a trigger enters: the delay before its devices (live and export)
rep("if(sig!==N.sig){N.sig=sig;try{N.in.disconnect()}catch(e){}", "if(sig!==N.sig||!!N.mxPdOn!==!!(PDC.pre&&PDC.pre.has(t.id))){N.sig=sig;N.mxPdOn=!!(PDC.pre&&PDC.pre.has(t.id));try{N.in.disconnect()}catch(e){}if(N.mxPd)try{N.mxPd.disconnect()}catch(e){}")
rep("let prev=N.in;for(const f of t.fx){if(!f.on||(t.fxByp&&f.type!=='chord'&&f.type!=='arp'))continue;", "let prev=N.in;if(N.mxPdOn){if(!N.mxPd){N.mxPd=ctx.createDelay(1);N.mxPdV=0}prev.connect(N.mxPd);prev=N.mxPd}for(const f of t.fx){if(!f.on||(t.fxByp&&f.type!=='chord'&&f.type!=='arp'))continue;")
rep("pn=oc.createStereoPanner();vol.gain.value=_aud?t.vol:0;pn.pan.value=t.pan;let prev=tin;", "pn=oc.createStereoPanner();vol.gain.value=_aud?t.vol:0;pn.pan.value=t.pan;let prev=tin;if(PDC.pre&&PDC.pre.has(t.id)){const dl=oc.createDelay(1);dl.delayTime.value=Math.min(sr,PDC.get(t.id)||0)/sr;prev.connect(dl);prev=dl}")
rep("{const d=PDC.get(t.id)||0;if(d>0){const dl=oc.createDelay(1)", "{const d=PDC.pre&&PDC.pre.has(t.id)?0:PDC.get(t.id)||0;if(d>0){const dl=oc.createDelay(1)")

# busRoute (MX-1's): outputs and sends get the extra delay their path needs
rep("if(N.dest!==dest){try{N.pan.disconnect(N.dest||master)}catch(e){}N.pan.connect(dest);N.dest=dest}",
    "const PM=MXPML||pdcMap(ctx.sampleRate,true),op=(PM.edge.get('o:'+t.id)||0)/ctx.sampleRate,via=op>0;"
    "if(N.dest!==dest||!!N.mxOv!==via){try{N.pan.disconnect(N.mxOv?N.mxOd:(N.dest||master))}catch(e){}if(N.mxOg)try{N.mxOg.disconnect()}catch(e){}"
    "if(via){if(!N.mxOd){N.mxOd=ctx.createDelay(1);N.mxOg=ctx.createGain();N.mxOd.connect(N.mxOg)}N.mxOd.delayTime.value=op;N.mxOdV=op;N.pan.connect(N.mxOd);N.mxOg.connect(dest)}else N.pan.connect(dest);N.dest=dest;N.mxOv=via}"
    "else if(via&&N.mxOdV!==op){mxDelaySet(N.mxOd,N.mxOg.gain,op,1);N.mxOdV=op}")
rep("try{sg.disconnect()}catch(e){}N.snd.delete(rid)}}", "try{sg.disconnect()}catch(e){}if(sg._dl)try{sg._dl.disconnect()}catch(e){}N.snd.delete(rid)}}")
rep("let sg=N.snd.get(rid);if(!sg){const pr=!!pre[rid],fr=pr?N.mxPre:N.pan;sg=ctx.createGain();sg.gain.value=0;fr.connect(sg);sg.connect(R.in);sg._to=R.in;sg._pre=pr;sg._from=fr;N.snd.set(rid,sg)}sg.gain.setTargetAtTime(lv,ctx.currentTime,.01)}",
    "let sg=N.snd.get(rid);const sp=(PM.edge.get('s:'+t.id+':'+rid)||0)/ctx.sampleRate;"
    "if(sg&&!!sg._dl!==(sp>0)){try{sg._from.disconnect(sg)}catch(e){}try{sg.disconnect()}catch(e){}if(sg._dl)try{sg._dl.disconnect()}catch(e){}N.snd.delete(rid);sg=null}"
    "if(!sg){const pr=!!pre[rid],fr=pr?N.mxPre:N.pan;sg=ctx.createGain();sg.gain.value=0;fr.connect(sg);if(sp>0){sg._dl=ctx.createDelay(1);sg._dl.delayTime.value=sp;sg._dlV=sp;sg.connect(sg._dl);sg._dl.connect(R.in)}else sg.connect(R.in);sg._to=R.in;sg._pre=pr;sg._from=fr;N.snd.set(rid,sg)}"
    "if(sg._dl&&sg._dlV!==sp){mxDelaySet(sg._dl,sg.gain,sp,lv);sg._dlV=sp}else sg.gain.setTargetAtTime(lv,ctx.currentTime,.01)}")

# the Ducker's trigger: its extra delay
rep("const s=abxSrc(f),SN=s&&s!==t?NODES.get(s.id):null,tap=SN&&!abxReach(t,s)?SN.ut.out:null;if(X.ksrc===tap)continue;if(X.ksrc){try{X.ksrc.disconnect(X.key)}catch(e){}}X.ksrc=tap;if(tap)tap.connect(X.key)",
    "const s=abxSrc(f),SN=s&&s!==t?NODES.get(s.id):null,tap=SN&&!abxReach(t,s)?SN.ut.out:null,kp=tap&&MXPML?(MXPML.edge.get('k:'+f.id)||0)/ctx.sampleRate:0;"
    "if(X.ksrc===tap&&(X.kdV||0)===kp)continue;if(X.ksrc===tap&&X.kdl&&kp>0){X.kdl.delayTime.setValueAtTime(kp,ctx.currentTime);X.kdV=kp;continue}"
    "if(X.ksrc){try{X.ksrc.disconnect(X.kdl||X.key)}catch(e){}}if(X.kdl){try{X.kdl.disconnect()}catch(e){}X.kdl=null}X.ksrc=tap;X.kdV=kp;"
    "if(tap){if(kp>0){X.kdl=ctx.createDelay(1);X.kdl.delayTime.value=kp;tap.connect(X.kdl);X.kdl.connect(X.key)}else tap.connect(X.key)}")

# fxLat: what the browser's compressor really delays by (measured: floor of 6 ms; the Multiband's impulse peaks there too)
rep("case'comp':case'ott':return Math.round(.006*sr);case'mband':return Math.round(.0062*sr);", "case'comp':case'ott':case'mband':return Math.floor(.006*sr+1e-6);/* MX-2: measured, the browser compressor's pre-delay */")
# renderMix: the same delays, and the automation plan
rep("const ABK=only||fast?new Set():abxKeys(),ABD=[];", "const ABK=only||fast?new Set():abxKeys(),ABD=[],MXRG={fx:new Map(),trk:new Map(),mst};")
rep("const x=mkFxNode(oc,f.type);x.set(f.p);prev.connect(x.in);prev=x.out;if(f.type==='duck'&&x.key)ABD.push([x,f.p&&f.p.src,t.id])",
    "const x=mkFxNode(oc,f.type);x.set(f.p);prev.connect(x.in);prev=x.out;MXRG.fx.set(f.id,{x,f});if(f.type==='duck'&&x.key)ABD.push([x,f.p&&f.p.src,t.id,f.id])")
rep("NN.set(t.id,{tin,pn,pre:prev,aud:_aud});", "NN.set(t.id,{tin,pn,pre:prev,aud:_aud});MXRG.trk.set(t.id,{vol,pn,aud:_aud});")
rep("if(!(gp&&!G&&mxOutT(t)))n.pn.connect(G?G.tin:mst);", "if(!(gp&&!G&&mxOutT(t)))mxOffCon(oc,n.pn,G?G.tin:mst,PDC.edge?PDC.edge.get('o:'+t.id):0);")
rep("(pr?n.pre:n.pn).connect(sg);sg.connect(R.tin)}", "(pr?n.pre:n.pn).connect(sg);mxOffCon(oc,sg,R.tin,PDC.edge?PDC.edge.get('s:'+t.id+':'+rid):0)}")
rep("for(const[x,sid,tid] of ABD){const n=NN.get(sid);if(n&&sid!==tid&&!abxReach(trkById(tid),trkById(sid)))n.pre.connect(x.key)}",
    "for(const[x,sid,tid,fid] of ABD){const n=NN.get(sid);if(n&&sid!==tid&&!abxReach(trkById(tid),trkById(sid)))mxOffCon(oc,n.pre,x.key,PDC.edge?PDC.edge.get('k:'+fid):0)}"
    "try{mxPaPlan(oc,b0,MXRG,fast)}catch(e){console.warn('AudioLab automation export',e)}")

JS = open(__file__.replace('mx2.py', 'mx2.js'), encoding='utf-8').read()
rep("function askChoice(title,text,btns,icon){", JS + "{const _sg2=syncGraph;syncGraph=function(){const r=_sg2.apply(this,arguments);try{mxLatShow()}catch(e){}return r}}\nfunction askChoice(title,text,btns,icon){")
rep(".dacv{display:flex;", "#fxin .tdev2 .devh .mxlat{flex:none;margin-left:-2px;font:var(--fw5) 9px/12px var(--ffu);color:#7d8292;font-variant-numeric:tabular-nums;white-space:nowrap;cursor:help}\n.dacv{display:flex;")
open(F, 'w', encoding='utf-8').write(s)
print('MX-2 written to', F)
