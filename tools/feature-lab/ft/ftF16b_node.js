const FTVS_TBC=new WeakMap();
const ftVsBs=p=>{const s=String(p&&p.bs!=null?p.bs:'100');return[0,1,2].map(i=>s[i]==='1'?1:0)};
const FTVS_TG={song:0,note:1,audio:2};
function ftVsAnchor(c){if(c===ctx)return play.on?{t:play.t0,b:play.b0,on:1}:{t:0,b:0,on:0};return{t:0,b:(typeof VMOF!=='undefined'&&VMOF.has(c)?VMOF.get(c).b0:SIDE_B0)||0,on:1}}
/* FT-F16b: what the worklet needs: the curve as before, plus how it starts (tg 0 the bar lines, 1 notes of a track, 2 a track's sound over a level)
   and the bands (bn 1, 2 or 3; bs which of them follow the curve; all of them shaped is the same as one band, without the crossover) */
const ftVsP=(p,sr)=>{const ms=+p.soft||0,tg=FTVS_TG[p.trig]||0,bn=Math.max(1,Math.min(3,+p.bnd||1)),bs=ftVsBs(p),all=bs.slice(0,bn).every(Boolean);
  return{pts:(p.pts||[]).map(q=>({x:+q.x,y:+q.y,c:+q.c||0})),cb:ftVsBeats(p),ph:(+p.phase||0)/100,d:clamp((p.depth??100)/100,0,1),sm:!!p.smooth,k:ms>0?1-Math.exp(-1/(ms*sr/1000)):1,
    tg,th:Math.pow(10,(isFinite(+p.thr)&&p.thr!==''&&p.thr!=null?+p.thr:-24)/20),bn,bs,all,f1:+p.x1||150,f2:+p.x2||2500}};
function ftVsNode(c){const i=c.createGain(),out=c.createGain(),key=c.createGain();i.connect(out);
  const off=typeof OfflineAudioContext!=='undefined'&&c instanceof OfflineAudioContext,a0=ftVsAnchor(c);
  const X={in:i,out,key,ksrc:null,node:null,p:null,q:[],bin:null,bout:null,x:0,tm:0,kl:0,tr:0,tbs:'',ctx:c,
    send(m){if(X.node)X.node.port.postMessage(m);else X.q.push(m)},
    set(p){X.p=p;X.send({p:ftVsP(p,c.sampleRate)});const tb=ftVsTb(p),s=tb.length+':'+(tb.length?tb[0]+','+tb[tb.length-1]+','+tb.reduce((a,b)=>a+b,0):'');if(s!==X.tbs){X.tbs=s;X.send({tb})}},
    resync(){X.send({tm:ftVsTm(),a:ftVsAnchor(c)})}};
  const mk=()=>{if(X.node||!c._ftvsOK)return;try{const P=X.p?ftVsP(X.p,c.sampleRate):null;
    const n=new AudioWorkletNode(c,'al-ftvs',{numberOfInputs:2,numberOfOutputs:1,outputChannelCount:[2],channelCount:2,channelCountMode:'explicit',processorOptions:{p:P,tm:ftVsTm(),a:off?a0:ftVsAnchor(c),q:off?[]:X.q.filter(m=>!m.p&&!m.tb),tb:X.p?ftVsTb(X.p):[]}});
    X.q=[];n.port.onmessage=e=>{const d=e.data;if(d&&d.bi){X.bin=d.bi;X.bout=d.bo;X.x=d.x;X.kl=d.kl||0;if(d.tr)X.tr=performance.now();X.tm=performance.now()}};try{i.disconnect(out)}catch(e){}i.connect(n,0,0);key.connect(n,0,1);n.connect(out);X.node=n}catch(e){console.warn('volume shaper node',e)}};
  if(off){(c._ftvsQ=c._ftvsQ||[]).push(()=>{mk();ftVsWireOff(c,X)})}
  else ftVsLoad(c).then(mk);
  if(off)ftVsLoad(c);
  return X}