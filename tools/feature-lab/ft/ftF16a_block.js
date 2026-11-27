/* v0.289 (task FT-F16a): Volume shaper, part 1 (starred card F16). An effect that turns the volume down and up along a drawn curve, one cycle
   per 1/4 note, 1/2 note, 1 bar or 2 bars, locked to the song: the curve is worked out for every sample from the song's beat (tempo map
   included) in a small worklet of its own, so a point at 1/16 lands on the sample, live and in an export alike. The play start and every loop
   jump reach the worklet as an anchor (a context time and the beat there) that takes over at its exact frame; while stopped it runs on in
   tempo. The display shows the curve with the signal of the last cycle folded over it (input grey, output in colour) and where the song is.
   Presets in the style of Kickstart and LFOTool. The worklet only reports levels while there is sound; nothing runs while the song is silent.
   Part 2 (FT-F16b): triggered by notes of another track or by audio, up to three bands. */
const FTVS={NB:192,url:null,
  CYC:[['1/4','1/4 note',1],['1/2','1/2 note',2],['1','1 bar',4],['2','2 bars',8]],
  TIP:{cyc:'How long one cycle of the curve is. The cycles start on the bar lines of the song.',snap:'Where points land when you drag them sideways: on 16ths or 32nds of the song, or anywhere.'}};
const ftVsBeats=p=>{const c=FTVS.CYC.find(q=>q[0]===String(p&&p.cyc));return c?c[2]:1};
/* the worklet: gain from the song's beat, for every sample */
const FTVS_WL=`/* ===== AudioLab volume shaper (task FT-F16a) ===== */
(()=>{const NB=${FTVS.NB};
function sOf(T,b){if(T.length<2||b<=0)return b*60/T[0].bpm;let lo=0,hi=T.length-1;while(lo<hi){const m=(lo+hi+1)>>1;if(T[m].b<=b)lo=m;else hi=m-1}const p=T[lo],n=T[lo+1],d=b-p.b;if(!n||!p.ramp)return p.s+d*60/p.bpm;const k=(n.bpm-p.bpm)/(n.b-p.b);return Math.abs(k)<1e-9?p.s+d*60/p.bpm:p.s+60/k*Math.log((p.bpm+k*d)/p.bpm)}
function bOf(T,s){if(T.length<2||s<=0)return s*T[0].bpm/60;let lo=0,hi=T.length-1;while(lo<hi){const m=(lo+hi+1)>>1;if(T[m].s<=s)lo=m;else hi=m-1}const p=T[lo],n=T[lo+1],d=s-p.s;if(!n||!p.ramp)return p.b+d*p.bpm/60;const k=(n.bpm-p.bpm)/(n.b-p.b);return Math.abs(k)<1e-9?p.b+d*p.bpm/60:p.b+p.bpm*(Math.exp(k*d/60)-1)/k}
function ev(P,x,sm){let i=0;while(i<P.length-2&&P[i+1].x<=x)i++;const a=P[i],b=P[Math.min(P.length-1,i+1)],dx=Math.max(1e-6,b.x-a.x);let t=(x-a.x)/dx;t=t<0?0:t>1?1:t;if(sm)t=(1-Math.cos(Math.PI*t))/2;const c=a.c||0;t=c>=0?Math.pow(t,1+c*3):1-Math.pow(1-t,1-c*3);return a.y+(b.y-a.y)*t}
class FtVs extends AudioWorkletProcessor{
 constructor(o){super();const po=(o&&o.processorOptions)||{};this.p=null;this.T=[{b:0,s:0,bpm:120,ramp:0}];this.A=[{t:0,b:0,s:0}];this.g=-1;this.bi=new Float32Array(NB);this.bo=new Float32Array(NB);this.lb=-1;this.loud=0;this.left=0;
  this.apply(po);for(const m of(po.q||[]))this.apply(m);this.port.onmessage=e=>this.apply(e.data)}
 apply(d){if(!d)return;if(d.tm&&d.tm.length)this.T=d.tm;if(d.p){this.p=d.p}
  if(d.a){const a=d.a;this.A=this.A.filter(x=>x.t<a.t);this.A.push({t:a.t,b:a.b,s:sOf(this.T,a.b)})}
  if(d.tm)for(const a of this.A)a.s=sOf(this.T,a.b)}
 process(ins,outs){const I=ins[0]||[],O=outs[0],n=O[0].length,p=this.p;const i0=I[0],i1=I[1]||I[0];
  if(!p||!p.pts||p.pts.length<2){for(let c=0;c<O.length;c++){const s=c?i1:i0;if(s)O[c].set(s);else O[c].fill(0)}return true}
  const sr=sampleRate,F=currentFrame,T=this.T,A=this.A,P=p.pts,cy=p.cb,ph=p.ph||0,d=p.d,sm=!!p.sm,k=p.k,flat=T.length<2,bins=this.bi,bout=this.bo,o0=O[0],o1=O[1]||null;let g=this.g,lb=this.lb,loud=0,x=0;
  for(let i=0;i<n;i++){const tt=(F+i)/sr;while(A.length>1&&A[1].t<=tt)A.shift();const a=A[0];
   const beat=flat?a.b+(tt-a.t)*T[0].bpm/60:bOf(T,a.s+(tt-a.t));let q=beat/cy+ph;q-=Math.floor(q);x=q;
   const v=ev(P,q,sm),tg=1-d+d*v;if(g<0||k>=1)g=tg;else g+=(tg-g)*k;
   const l=i0?i0[i]:0,r=i1?i1[i]:0;o0[i]=l*g;if(o1)o1[i]=r*g;
   const bb=Math.floor(q*NB);if(bb!==lb){lb=bb;bins[bb]=0;bout[bb]=0}const m=Math.max(l<0?-l:l,r<0?-r:r);if(m>bins[bb])bins[bb]=m;const mo=m*g;if(mo>bout[bb])bout[bb]=mo;if(m>1e-5)loud=1}
  this.g=g;this.lb=lb;if(loud)this.loud=1;this.left-=n;
  if(this.left<=0){this.left=Math.round(sr/20);if(this.loud){this.loud=0;this.port.postMessage({bi:bins.slice(),bo:bout.slice(),x})}}
  return true}}
registerProcessor('al-ftvs',FtVs)})();`;
function ftVsLoad(c){if(c._ftvsP)return c._ftvsP;if(!c.audioWorklet)return c._ftvsP=Promise.resolve(false);
  if(!FTVS.url)FTVS.url=URL.createObjectURL(new Blob([FTVS_WL],{type:'application/javascript'}));
  return c._ftvsP=c.audioWorklet.addModule(FTVS.url).catch(()=>c.audioWorklet.addModule('data:application/javascript;base64,'+btoa(unescape(encodeURIComponent(FTVS_WL))))).then(()=>{c._ftvsOK=1;return true}).catch(e=>{console.warn('volume shaper worklet',e);return false})}
/* an offline render (export, bounce, freeze) gets its shapers when rendering starts: messages do not reach a worklet while it renders */
if(typeof OfflineAudioContext!=='undefined'&&!OfflineAudioContext.prototype._ftvs){const sr0=OfflineAudioContext.prototype.startRendering;OfflineAudioContext.prototype._ftvs=1;
  OfflineAudioContext.prototype.startRendering=function(){const q=this._ftvsQ;if(q&&q.length){this._ftvsQ=null;const me=this,args=arguments;return Promise.resolve(this._ftvsP).then(()=>{for(const f of q){try{f()}catch(e){console.warn('volume shaper',e)}}return sr0.apply(me,args)})}return sr0.apply(this,arguments)}}
const ftVsTm=()=>tmapSegs().map(q=>({b:q.b,s:q.s,bpm:q.bpm,ramp:q.ramp?1:0}));
/* where the song is: the live context follows the transport (the start and loop jumps lie ahead, the worklet takes them over at their frame); an
   offline render starts at its first beat */
function ftVsAnchor(c){if(c===ctx)return play.on?{t:play.t0,b:play.b0}:{t:0,b:0};return{t:0,b:(typeof VMOF!=='undefined'&&VMOF.has(c)?VMOF.get(c).b0:SIDE_B0)||0}}
const ftVsP=(p,sr)=>{const ms=+p.soft||0;return{pts:(p.pts||[]).map(q=>({x:+q.x,y:+q.y,c:+q.c||0})),cb:ftVsBeats(p),ph:(+p.phase||0)/100,d:clamp((p.depth??100)/100,0,1),sm:!!p.smooth,k:ms>0?1-Math.exp(-1/(ms*sr/1000)):1}};
function ftVsNode(c){const i=c.createGain(),out=c.createGain();i.connect(out);
  const off=typeof OfflineAudioContext!=='undefined'&&c instanceof OfflineAudioContext,a0=ftVsAnchor(c);
  const X={in:i,out,node:null,p:null,q:[],bin:null,bout:null,x:0,tm:0,
    send(m){if(X.node)X.node.port.postMessage(m);else X.q.push(m)},
    set(p){X.p=p;X.send({p:ftVsP(p,c.sampleRate)})},
    resync(){X.send({tm:ftVsTm(),a:ftVsAnchor(c)})}};
  const mk=()=>{if(X.node||!c._ftvsOK)return;try{const P=X.p?ftVsP(X.p,c.sampleRate):null;
    const n=new AudioWorkletNode(c,'al-ftvs',{numberOfInputs:1,numberOfOutputs:1,outputChannelCount:[2],channelCount:2,channelCountMode:'explicit',processorOptions:{p:P,tm:ftVsTm(),a:off?a0:ftVsAnchor(c),q:off?[]:X.q.filter(m=>!m.p)}});
    X.q=[];n.port.onmessage=e=>{const d=e.data;if(d&&d.bi){X.bin=d.bi;X.bout=d.bo;X.x=d.x;X.tm=performance.now()}};try{i.disconnect(out)}catch(e){}i.connect(n);n.connect(out);X.node=n}catch(e){console.warn('volume shaper node',e)}};
  if(off){(c._ftvsQ=c._ftvsQ||[]).push(mk);ftVsLoad(c)}else ftVsLoad(c).then(mk);
  return X}
/* a tempo edit while playing moves the song's anchor: the shapers follow (the transport's own resync covers start and loop jumps) */
{const _t=tmpEdit;tmpEdit=function(){const r=_t.apply(this,arguments);try{setTimeout(ndResync,0)}catch(e){}return r}}
const ftVsPre=(cyc,a,o)=>Object.assign({cyc,depth:100,soft:1,phase:0,smooth:false,snap:'16',pts:sp0(a)},o||{});
function ftVsApply(f){try{const X=vizInst(f);if(X)X.set(f.p)}catch(e){}}
function ftVsEdit(f,fn){pushUndo();fn(f.p);ftVsApply(f);changed(false)}
ND('ftvs',{name:'Volume Shaper',vw:560,grp:['Modulation','#3ecf8e'],desc:'Draw how the volume dips and comes back, locked to the song: kick ducking without a sidechain, gates and swells',
  hint:'Drag the white dots to draw the curve, the small yellow dots to bend a segment. Points snap to the song’s 16ths. Two points at the same place make a hard step.',
  logo:['#3ecf8e','#f5c84c','<path d="M4 36V12c4 0 6 24 12 24V12c4 0 6 24 12 24V12c4 0 6 24 12 24" stroke-width="2.4"/>','VSHAPE'],
  p:{depth:[0,100,100,'%'],soft:[0,20,1,'ms'],phase:[0,100,0,'%']},dial:['depth','soft','phase'],lab:{depth:'Depth',soft:'Smooth',phase:'Offset'},
  init:ftVsPre('1/4',[0,0,-.35,.5,1,0,1,1,0]),
  sel:[['cyc','Length',FTVS.CYC.map(q=>[q[0],q[1]])],['snap','Snap',[['16','1/16'],['32','1/32'],['0','Off']]],['smooth','Smooth segments',null,'chk']],
  btn:[['add','Add point','Add a point in the widest gap of the curve'],['rem','Remove point','Remove the last point inside the curve'],['flip','Invert','Turn the curve upside down'],['rev','Reverse','Mirror the curve in time'],['dbl','Double','The same curve twice in one cycle'],['flat','Flat','A flat line: the sound passes unchanged']],
  act:{add:f=>ftVsEdit(f,p=>{const P=p.pts;let bi=0,bw=0;for(let i=0;i<P.length-1;i++){const w=P[i+1].x-P[i].x;if(w>bw){bw=w;bi=i}}if(bw<=0)return;const x=P[bi].x+bw/2;P.splice(bi+1,0,{x,y:shEval(P,x,p.smooth),c:0})}),
    rem:f=>ftVsEdit(f,p=>{if(p.pts.length>2)p.pts.splice(p.pts.length-2,1)}),flip:f=>ftVsEdit(f,p=>p.pts.forEach(q=>q.y=1-q.y)),
    rev:f=>ftVsEdit(f,p=>{const P=p.pts;p.pts=P.slice().reverse().map((q,i,a)=>({x:+(1-q.x).toFixed(6),y:q.y,c:-(a[i+1]?a[i+1].c||0:0)}))}),
    dbl:f=>ftVsEdit(f,p=>{const P=p.pts,o=[];for(let r=0;r<2;r++)P.forEach((q,i)=>{if(r&&!i)return;o.push({x:(q.x+r)/2,y:q.y,c:q.c||0})});p.pts=o}),
    flat:f=>ftVsEdit(f,p=>{p.pts=[{x:0,y:1,c:0},{x:1,y:1,c:0}]})},
  pre:mergePre(
    PRS('Sidechain (Kickstart style)',[['k4','Kick duck 1/4',ftVsPre('1/4',[0,0,-.35,.5,1,0,1,1,0])],['kshort','Short duck',ftVsPre('1/4',[0,0,-.5,.28,1,0,1,1,0])],
      ['klong','Long pump',ftVsPre('1/4',[0,0,.25,.85,1,0,1,1,0])],['kgentle','Gentle pump',ftVsPre('1/4',[0,0,-.35,.5,1,0,1,1,0],{depth:55})],
      ['khalf','Half-time pump',ftVsPre('1/2',[0,0,-.35,.4,1,0,1,1,0])],['kroll','Psy roll gap (first 16th off)',ftVsPre('1/4',[0,0,0,.25,0,0,.25,1,0,1,1,0],{soft:.5})]]),
    PRS('Gates (LFOTool style)',[['g8','Gate 1/8',ftVsPre('1',shPulse(8,.5,1,0).flatMap(q=>[q.x,q.y,q.c]))],['g16','Gate 1/16',ftVsPre('1',shPulse(16,.5,1,0).flatMap(q=>[q.x,q.y,q.c]))],
      ['off8','Off-beat 1/8',ftVsPre('1/4',[0,0,0,.5,0,0,.5,1,0,1,1,0])],['t332','Trance 3-3-2',ftVsPre('1/2',[0,1,0,.125,1,0,.125,0,0,.1875,0,0,.1875,1,0,.3125,1,0,.3125,0,0,.375,0,0,.375,1,0,.5,1,0,.5,0,0,.5625,0,0,.5625,1,0,.6875,1,0,.6875,0,0,.75,0,0,.75,1,0,.875,1,0,.875,0,0,1,0,0])]]),
    PRS('Swells',[['sw1','Swell 1 bar',ftVsPre('1',[0,0,.4,.97,1,0,1,0,0],{soft:3})],['sw2','Swell 2 bars',ftVsPre('2',[0,0,.4,.97,1,0,1,0,0],{soft:3})],['tremo','Tremolo 1/8',ftVsPre('1/4',shSine(2).flatMap(q=>[q.x,q.y,q.c]),{depth:60,smooth:true})]])),
  node:(c)=>ftVsNode(c),
  draw:(g,w,h,f,X)=>{const p=f.p,P=p.pts||[],L=lkT(),x0=8,x1=w-8,T=16,B=h-16,W=x1-x0,H=B-T,X0=x=>x0+x*W,Y0=v=>T+(1-v)*H,cb=ftVsBeats(p),col=L.ok;vbg(g,w,h);
    /* grid: beats and 16ths of the song inside the cycle */
    const n16=Math.round(cb*4);for(let k=0;k<=n16;k++){const x=Math.round(X0(k/n16))+.5;g.strokeStyle=k%4===0?L.gMaj:L.gMin;g.lineWidth=1;g.beginPath();g.moveTo(x,T);g.lineTo(x,B);g.stroke()}
    for(let k=0;k<=4;k++){const y=Math.round(T+k/4*H)+.5;g.strokeStyle=k%2?L.gMin:L.gMid;g.beginPath();g.moveTo(x0,y);g.lineTo(x1,y);g.stroke()}
    /* the curve behind, as a gain (depth applied) */
    const d=clamp((p.depth??100)/100,0,1),gy=x=>1-d+d*shEval(P,x,p.smooth),SS=Math.max(64,Math.min(600,Math.floor(W)));
    g.beginPath();g.moveTo(X0(0),B);for(let k=0;k<=SS;k++)g.lineTo(X0(k/SS),Y0(gy(k/SS)));g.lineTo(X0(1),B);g.closePath();g.fillStyle='rgba(62,207,142,.12)';g.fill();
    /* the signal of the last cycle over it: input grey, output in colour (from the worklet, only while there is sound) */
    if(X&&X.bin){const NB=X.bin.length,bw=W/NB,age=(performance.now()-X.tm)/1000,fa=age<1.5?1:Math.max(0,1-(age-1.5));if(fa>0){g.globalAlpha=fa;
      for(let k=0;k<NB;k++){const a=Math.min(1,X.bin[k]),o=Math.min(1,X.bout[k]),xx=X0(k/NB);if(a>0){g.fillStyle='rgba(183,183,194,.22)';g.fillRect(xx,B-a*H,Math.max(1,bw-.5),a*H)}if(o>0){g.fillStyle='rgba(62,207,142,.55)';g.fillRect(xx,B-o*H,Math.max(1,bw-.5),o*H)}}g.globalAlpha=1}}
    g.beginPath();for(let k=0;k<=SS;k++){const x=X0(k/SS),y=Y0(gy(k/SS));k?g.lineTo(x,y):g.moveTo(x,y)}g.strokeStyle=col;g.lineWidth=1.6;g.stroke();
    /* where the song is */
    let ph=null;if(X&&performance.now()-X.tm<300)ph=X.x;else if(play.on&&ctx){let q=curDisp()/cb+(+p.phase||0)/100;ph=q-Math.floor(q)}
    if(ph!=null){const x=Math.round(X0(ph))+.5;g.strokeStyle='rgba(255,255,255,.55)';g.lineWidth=1;g.beginPath();g.moveTo(x,T);g.lineTo(x,B);g.stroke();g.fillStyle='#fff';g.beginPath();g.arc(x,Y0(gy(ph)),3.5,0,7);g.fill()}
    const cn=(FTVS.CYC.find(q=>q[0]===String(p.cyc))||FTVS.CYC[0])[1];txt(g,'VOLUME',x0,T-5,col,9);txt(g,cn+' per cycle, from the bar line',x0+52,T-5,L.mut,9);
    txt(g,'0 dB',x0+12,T+10,L.mut,8);txt(g,d<1?Math.round(20*Math.log10(Math.max(1e-6,1-d)))+' dB':'-∞ dB',x0+12,B-3,L.mut,8)},
  hnd:(p,w,h)=>{const x0=8,x1=w-8,T=16,B=h-16,W=x1-x0,H=B-T,P=p.pts||[],o=[],cb=ftVsBeats(p),sn=+p.snap||0,step=sn?(4/sn)/cb:0,snap=x=>step?Math.round(x/step)*step:x;
    P.forEach((q,i)=>{const first=i===0,last=i===P.length-1;o.push({x:x0+q.x*W,y:T+(1-q.y)*H,c:'#fff',l:'Point '+(i+1),v:Math.round(q.y*100)+'%',sm:P.length>24?1:0,drag:(x,y)=>{q.y=clamp(1-(y-T)/H,0,1);if(first)P[P.length-1].y=q.y;if(last)P[0].y=q.y;if(!first&&!last){const lo=P[i-1].x,hi=P[i+1].x;q.x=+clamp(snap((x-x0)/W),lo,hi).toFixed(6)}}});
      if(!last&&(P[i+1].x-q.x)>.02){const mx=(q.x+P[i+1].x)/2,my=shEval(P,mx,p.smooth);o.push({x:x0+mx*W,y:T+(1-my)*H,c:'#f5c84c',l:'Bend',v:(q.c||0).toFixed(2),sm:1,drag:(x,y,w2,h2,dy,p0)=>{const c0=(p0&&p0.pts&&p0.pts[i]?p0.pts[i].c:0)||0;q.c=clamp(c0+(dy||0)/60*(P[i+1].y>q.y?1:-1),-1,1)}})}});return o}});
/* tooltips on the Length, Snap and Smooth segments controls of the device's bar */
{const _tb=ndTb;ndTb=function(f){let s=_tb.apply(this,arguments);try{if(f&&f.type==='ftvs'){s=s.replace('<label>Length <','<label title="'+FTVS.TIP.cyc+'">Length <').replace('<label>Snap <','<label title="'+FTVS.TIP.snap+'">Snap <').replace('<label><input type="checkbox" data-x="smooth"','<label title="Round every segment off (an S shape) instead of straight lines"><input type="checkbox" data-x="smooth"')}}catch(e){}return s}}
FT_HOOKS.volumeShaper={type:'ftvs',beats:ftVsBeats,gainAt:(p,beat)=>{const q0=beat/ftVsBeats(p)+(+p.phase||0)/100,q=q0-Math.floor(q0),d=clamp((p.depth??100)/100,0,1);return 1-d+d*shEval(p.pts||[],q,p.smooth)}};
