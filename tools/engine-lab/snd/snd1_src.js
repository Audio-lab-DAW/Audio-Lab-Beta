/* ==SND1-js== v0.000 (task SND-1, lane L): Filter v2 (new device 'filter2') and the Auto Filter's Clean models (B37, N5)
   One worklet processor, al-snd-filter, runs the shared kit's filters (sndKitCore): Ladder 24 (Moog style, Huovilainen drive),
   Diode 24 (303 style), MS-20 12 (Sallen-Key), SVF 12 and SVF 24 (Butterworth at resonance 0), Comb and Formant, with the drive
   inside the filter, every value smoothed per sample (20 ms), 2x oversampling by the kit's halfbands (the dry part of the mix goes
   through the same up/down pair so a mix below 100 % does not comb), and a sleep after 1 s of silence in and out.
   The core (sndFltCore) is plain arithmetic for the native port (NB): Math.exp, Math.log, Math.tan, Math.tanh, Math.sqrt only,
   doubles, no FMA, no flush to zero (the kit's flush() zeroes states below 1e-30). The worklet and the main thread run the same core.
   Old projects: the Low-pass filter (filter) stays as it is; an Auto Filter without q (every saved one) has Hi-Fi off (q 'classic'), bit for
   bit; a new Auto Filter starts with Hi-Fi on (q 'clean'; the AE1 rule: new devices start on). Own implementation; no code copied. */
function sndFltCore(K){
  const LN2=0.6931471805599453,LN50=3.912023005428146,LN20=2.995732273553991,LN10_20=0.11512925464970229,CENT=LN2/1200;
  const Q24A=0.5411961001461969,Q24B=1.3065629648763766,BELL=2.9810717055349722; // Butterworth 4th order; 10^(12/20)-1
  // models: 0 ladder, 1 diode, 2 ms20, 3 svf12, 4 svf24, 5 comb, 6 formant, 7 bell (+12 dB, the Auto Filter's Peak)
  // level: the ladder keeps sqrt(1+k) of the bass it loses to resonance, the diode (1+k)^0.75: both about -3 dB at resonance 25 %, -6 dB at 80 %
  // modes (SVF, MS-20): 0 low-pass, 1 band-pass, 2 high-pass, 3 notch, 4 peak; comb: 3 (notch) = negative feedback
  class Ch{constructor(R,os){this.R=R;this.lad=new K.Ladder();this.dio=new K.Diode();this.sk=new K.SallenKey();this.a=new K.Svf();this.b=new K.Svf();
      this.cb=new K.Comb(Math.ceil(R/20)+8);this.cb.setDamp(12000,R);this.fm=new K.Formant();this.ov=os===2?new K.Os2():null}
    copy(o){cp(this,o)}
    reset(){this.lad.reset();this.dio.reset();this.sk.reset();this.a.reset();this.b.reset();this.cb.reset();this.fm.reset();if(this.ov)this.ov.reset()}
    flush(){this.lad.flush();this.dio.flush();this.sk.flush();this.a.flush();this.b.flush();this.cb.flush();this.fm.flush();if(this.ov)this.ov.flush()}}
  const sm=(sr,v)=>new K.Smooth(20,sr,v);
  // copies every state of a channel into another of the same shape (numbers and typed arrays, depth first, in key order)
  function cp(a,b){for(const k in b){const v=b[k];if(typeof v==='number')a[k]=v;else if(v&&typeof v==='object'){if(v.BYTES_PER_ELEMENT)a[k].set(v);else cp(a[k],v)}}}
  class Engine{
    constructor(sr,o){o=o||{};this.sr=sr;this.model=o.model|0;this.mode=o.mode|0;this.os=o.os===1?1:2;this.mk();
      this.lf=sm(sr,0);this.r=sm(sr,0);this.dr=sm(sr,0);this.mx=sm(sr,1);this.og=sm(sr,1);this.vw=sm(sr,0);
      this.first=true;this.pf=NaN;this.pr=NaN;this.pd=NaN;this.pm=NaN;this.po=NaN;this.pv=NaN;
      this.fc=-1;this.cr=-1;this.cv=-1;this.cd=-1;this.lastL=NaN;this.lastT=NaN;this.n=0;this.comp=1;this.cn=1;this.quiet=0;this.sleep=false}
    mk(){const R=this.sr*this.os;this.R=R;this.ch=[new Ch(R,this.os),new Ch(R,this.os)];this.fc=-1;this.cd=-1}
    msg(d){if(!d)return;if(d.os!=null&&(d.os===1?1:2)!==this.os){this.os=d.os===1?1:2;this.mk()}
      if(d.model!=null&&(d.model|0)!==this.model){this.model=d.model|0;this.ch[0].reset();this.ch[1].reset();this.fc=-1;this.cd=-1}
      if(d.mode!=null&&(d.mode|0)!==this.mode){this.mode=d.mode|0;this.fc=-1}}
    // the parameters' targets for this block (AudioParam values, float32); the first block jumps
    targets(P){const f=P.freq[0],r=P.res[0],dv=P.drive[0],m=P.mix[0],o=P.out[0],v=P.vowel[0],J=this.first||this.sleep;
      if(f!==this.pf){this.pf=f;const lf=Math.log(f<5?5:(f>24000?24000:f));if(J)this.lf.jump(lf);else this.lf.to(lf)}else if(J)this.lf.jump(this.lf.t);
      if(r!==this.pr){this.pr=r;const x=r<0?0:(r>1.2?1.2:r);if(J)this.r.jump(x);else this.r.to(x)}else if(J)this.r.jump(this.r.t);
      if(dv!==this.pd){this.pd=dv;const x=dv<0?0:(dv>1?1:dv);if(J)this.dr.jump(x);else this.dr.to(x)}else if(J)this.dr.jump(this.dr.t);
      if(m!==this.pm){this.pm=m;const x=m<0?0:(m>1?1:m);if(J)this.mx.jump(x);else this.mx.to(x)}else if(J)this.mx.jump(this.mx.t);
      if(o!==this.po){this.po=o;const x=Math.exp(o*LN10_20);if(J)this.og.jump(x);else this.og.to(x)}else if(J)this.og.jump(this.og.t);
      if(v!==this.pv){this.pv=v;const x=v<0?0:(v>4?4:v);if(J)this.vw.jump(x);else this.vw.to(x)}else if(J)this.vw.jump(this.vw.t);
      this.first=false}
    // coefficients for both channels (one tan per update; channel 1 copies channel 0)
    coef(fc,r){const R=this.R,c0=this.ch[0],c1=this.ch[1],md=this.model;
      switch(md){
        case 0:{const g=K.prewarp(fc,R),G=g/(1+g),k=4*r;c0.lad.G=G;c0.lad.k=k;c1.lad.G=G;c1.lad.k=k;this.comp=Math.sqrt(1+k);break}
        case 1:{const d=c0.dio;d.set(fc,r,R);const e=c1.dio;e.g=d.g;e.k=d.k;e.Mf.set(d.Mf);e.Mo.set(d.Mo);const q=Math.sqrt(1+d.k);this.comp=q*Math.sqrt(q);break}
        case 2:{const g=K.prewarp(fc,R),k=2*r;c0.sk.g=g;c0.sk.k=k;c1.sk.g=g;c1.sk.k=k;break}
        case 3:case 7:{const g=K.prewarp(fc,R),q=0.5*Math.exp(r*LN50);c0.a.setG(g,1/q);c1.a.setG(g,1/q);break}
        case 4:{const g=K.prewarp(fc,R),q=Q24B*Math.exp(r*LN20);c0.a.setG(g,1/Q24A);c1.a.setG(g,1/Q24A);c0.b.setG(g,1/q);c1.b.setG(g,1/q);break}
        case 5:{const fb=(this.mode===3?-0.98:0.98)*(r>1?1:r),D=R/fc;c0.cb.set(D,fb,false);c1.cb.set(D,fb,false);this.cn=1-(fb<0?-fb:fb);break}
        case 6:{const sh=fc/1000;c0.fm.set(this.cv,R,sh);c1.fm.set(this.cv,R,sh);break}}}
    drive(dv){const nl=dv>0,d=0.5+7.5*dv;this.dn=nl;this.dd=d;this.mu=nl?Math.sqrt(d+d):1;for(const c of this.ch){c.lad.setDrive(d,nl);c.dio.setDrive(d,nl);c.sk.setDrive(d,nl)}}
    run(c,x){const md=this.model;
      switch(md){
        case 0:return c.lad.tick(x)*this.comp;
        case 1:return c.dio.tick(x)*this.comp;
        case 2:{const y=c.sk.tick(this.dn?K.sat(x,this.dd):x);return this.mode===1?c.sk.bp:y}}
      const xs=this.dn?K.sat(x,this.dd):x;
      switch(md){
        case 3:return c.a.run(xs,this.mode);
        case 4:return c.b.run(c.a.run(xs,this.mode),this.mode);
        case 5:return c.cb.tick(xs)*this.cn;
        case 6:return c.fm.tick(xs);
        default:return xs+BELL*c.a.run(xs,1)}}
    // one block: inL/inR may be null (no input), outL/outR the outputs, P the AudioParam arrays (det a-rate)
    block(inL,inR,outL,outR,n,P){this.targets(P);
      let pk=0;if(inL)for(let k=0;k<n;k++){const a=inL[k]<0?-inL[k]:inL[k];if(a>pk)pk=a}
      if(inR&&inR!==inL)for(let k=0;k<n;k++){const a=inR[k]<0?-inR[k]:inR[k];if(a>pk)pk=a}
      if(this.sleep){if(pk===0){for(let k=0;k<n;k++){outL[k]=0;if(outR!==outL)outR[k]=0}return}this.sleep=false;this.quiet=0}
      let two=!!(inR&&inR!==inL&&outR!==outL);if(two){let same=true;for(let k=0;k<n;k++)if(inL[k]!==inR[k]){same=false;break}if(same)two=false}
      const det=P.det,dA=det.length>1,c0=this.ch[0],c1=this.ch[1],os2=this.os===2;let opk=0;if(two&&this.mono)c1.copy(c0);this.mono=!two;
      for(let k=0;k<n;k++){
        const l=this.lf.next(),r=this.r.next(),dv=this.dr.next(),m=this.mx.next(),og=this.og.next(),vw=this.vw.next(),dt=dA?det[k]:det[0];
        if(l!==this.lastL||dt!==this.lastT){this.lastL=l;this.lastT=dt;this.cf=Math.exp(l+dt*CENT)}
        let fc=this.cf;const R=this.R;if(fc>R*0.45)fc=R*0.45;if(fc<5)fc=5;
        if(dv!==this.cd){this.cd=dv;this.drive(dv)}
        if(fc!==this.fc||r!==this.cr||vw!==this.cv){if(this.model!==1||(this.n&3)===0||this.fc<0){this.fc=fc;this.cr=r;this.cv=vw;this.coef(fc,r)}}
        this.n=(this.n+1)|0;
        const xl=inL?inL[k]:0,xr=two?inR[k]:xl;let yl,yr;
        if(os2){const o=c0.ov.up(xl);o[0]=m*this.run(c0,o[0])+(1-m)*o[0];o[1]=m*this.run(c0,o[1])+(1-m)*o[1];yl=c0.ov.down(o);
          if(two){const p=c1.ov.up(xr);p[0]=m*this.run(c1,p[0])+(1-m)*p[0];p[1]=m*this.run(c1,p[1])+(1-m)*p[1];yr=c1.ov.down(p)}else yr=yl}
        else{yl=m*this.run(c0,xl)+(1-m)*xl;yr=two?m*this.run(c1,xr)+(1-m)*xr:yl}
        const gm=og*this.mu;yl*=gm;yr*=gm;outL[k]=yl;if(outR!==outL)outR[k]=yr;const a=yl<0?-yl:yl,b=yr<0?-yr:yr;if(a>opk)opk=a;if(b>opk)opk=b}
      c0.flush();c1.flush();
      if(pk===0&&opk<1e-6){this.quiet+=n;if(this.quiet>=this.sr){this.sleep=true;c0.reset();c1.reset();this.lf.jump(this.lf.t);this.r.jump(this.r.t);this.dr.jump(this.dr.t);this.mx.jump(this.mx.t);this.og.jump(this.og.t);this.vw.jump(this.vw.t)}}else this.quiet=0}}
  return{v:1,Engine,BELL,Q24A,Q24B}}
// the worklet part: appended to the kit's module (SNDK must exist)
function sndFltWL(){return '\n/* ===== AudioLab Filter v2 processor (task SND-1) ===== */\nconst SNDF=('+sndFltCore.toString()+')(SNDK);\n'+
  "registerProcessor('al-snd-filter',class extends AudioWorkletProcessor{static get parameterDescriptors(){return[{name:'freq',defaultValue:1200,minValue:5,maxValue:24000,automationRate:'k-rate'},{name:'res',defaultValue:0.25,minValue:0,maxValue:1.2,automationRate:'k-rate'},{name:'drive',defaultValue:0,minValue:0,maxValue:1,automationRate:'k-rate'},{name:'mix',defaultValue:1,minValue:0,maxValue:1,automationRate:'k-rate'},{name:'out',defaultValue:0,minValue:-48,maxValue:48,automationRate:'k-rate'},{name:'vowel',defaultValue:0,minValue:0,maxValue:4,automationRate:'k-rate'},{name:'det',defaultValue:0,minValue:-24000,maxValue:24000,automationRate:'a-rate'}]}"+
  "constructor(o){super();const q=(o&&o.processorOptions)||{};this.e=new SNDF.Engine(sampleRate,q);this.port.onmessage=e=>this.e.msg(e.data)}"+
  "process(ins,outs,P){const i=ins[0]||[],o=outs[0];if(!o||!o[0])return true;this.e.block(i[0]||null,i[1]||i[0]||null,o[0],o[1]||o[0],o[0].length,P);return true}});\n"}
{const _w=sndWL;sndWL=function(){return _w()+sndFltWL()}}

/* ---- main thread: the node, its parameters and the analog curve for displays ---- */
const SNDF_M={ladder:0,diode:1,ms20:2,svf12:3,svf24:4,comb:5,formant:6,bell:7},SNDF_MD={lp:0,bp:1,hp:2,notch:3,peak:4};
const SNDF_P=['freq','res','drive','mix','out','vowel'];
// o = {model, mode, os (1|2), freq Hz, res 0..1.2, drive 0..1, mix 0..1, out dB, vowel 0..4}
function sndFltNode(c,o){const i=c.createGain(),out=c.createGain(),X={in:i,out,node:null,o:Object.assign({model:0,mode:0,os:2,freq:1200,res:.25,drive:0,mix:1,out:0,vowel:0},o||{}),mods:[],
   set(v){const O=this.o,n=this.node,dm={};let any=false;for(const k of['model','mode','os'])if(v[k]!=null&&v[k]!==O[k]){O[k]=v[k];dm[k]=v[k];any=true}
     if(n&&any)n.port.postMessage(dm);for(const k of SNDF_P)if(v[k]!=null&&+v[k]===+v[k]){O[k]=+v[k];if(n){const a=n.parameters.get(k);try{a.setValueAtTime(O[k],c.currentTime)}catch(e){a.value=O[k]}}}},
   mod(src){this.mods.push(src);if(this.node)src.connect(this.node.parameters.get('det'))}};
 const mk=()=>{if(X.node)return;try{const O=X.o,pd={};for(const k of SNDF_P)pd[k]=O[k];
    const n=new AudioWorkletNode(c,'al-snd-filter',{numberOfInputs:1,numberOfOutputs:1,outputChannelCount:[2],channelCount:2,channelCountMode:'explicit',parameterData:pd,processorOptions:{model:O.model,mode:O.mode,os:O.os}});
    try{i.disconnect(out)}catch(e){}i.connect(n);n.connect(out);X.node=n;for(const s of X.mods)s.connect(n.parameters.get('det'))}catch(e){console.warn('AudioLab Filter v2',e)}};
 i.connect(out);if(typeof OfflineAudioContext!=='undefined'&&c instanceof OfflineAudioContext){(c._pre=c._pre||[]).push(mk);if(!c._wl)wlLoad(c)}else if(c._wl)mk();else{(c._wlq=c._wlq||[]).push(mk);wlLoad(c)}return X}
// the analog curve of a setting (magnitude, linear) at the frequencies fr, written into mg; drive is not shown
let SNDF_K=null;
function sndFltResp(o,fr,mg){const K=SNDF_K||(SNDF_K=sndKitCore()),N=fr.length,md=o.model|0,mo=o.mode|0,fc=Math.max(5,o.freq),r=Math.max(0,Math.min(1.2,o.res)),m=Math.max(0,Math.min(1,o.mix)),og=Math.pow(10,(o.out||0)/20);
  const cdiv=(ar,ai,br,bi)=>{const d=br*br+bi*bi;return[(ar*br+ai*bi)/d,(ai*br-ar*bi)/d]},cmul=(ar,ai,br,bi)=>[ar*br-ai*bi,ar*bi+ai*br];
  const svf=(w,q,mode)=>{const sr=0,si=w,s2r=-w*w,dr=s2r+1,di=w/q;let nr,ni;switch(mode){case 1:nr=0;ni=w/q;break;case 2:nr=s2r;ni=0;break;case 3:nr=s2r+1;ni=0;break;case 4:nr=1-s2r;ni=0;break;default:nr=1;ni=0}return cdiv(nr,ni,dr,di)};
  for(let j=0;j<N;j++){const f=fr[j],w=f/fc;let h=[1,0];
    if(md===0){const k=4*r;let p=[1,w];p=cmul(p[0],p[1],p[0],p[1]);p=cmul(p[0],p[1],p[0],p[1]);h=cdiv(Math.sqrt(1+k),0,p[0]+k,p[1])}
    else if(md===1){const k=K.DK*r,s=w*K.DW;// (sI - A) y = B u, A the diode ladder, u = x - k y4: tridiagonal, solved by elimination
      const a=[[2,0],[2,0],[2,0],[1,0]];for(const q of a)q[1]=s;let c=[-1,-1,-1],dI=[[1,0],[0,0],[0,0],[0,0]];// Thomas algorithm, complex
      const cp=[],dp=[];let den=a[0];cp[0]=cdiv(c[0],0,den[0],den[1]);dp[0]=cdiv(1,0,den[0],den[1]);
      for(let t=1;t<4;t++){const mr=cmul(-1,0,cp[t-1][0],cp[t-1][1]),dd=[a[t][0]-mr[0],a[t][1]-mr[1]];if(t<3)cp[t]=cdiv(c[t],0,dd[0],dd[1]);const nn=cmul(1,0,dp[t-1][0],dp[t-1][1]);dp[t]=cdiv(nn[0],nn[1],dd[0],dd[1])}
      const T=dp[3];// y4 for u = 1 (back substitution not needed for the last unknown)
      const q=Math.sqrt(1+k),cg=q*Math.sqrt(q);h=cdiv(T[0]*cg,T[1]*cg,1+k*T[0],k*T[1])}
    else if(md===2){const k=2*r,dr=1-w*w,di=(2-k)*w;h=mo===1?cdiv(0,w,dr,di):cdiv(1,0,dr,di)}
    else if(md===3)h=svf(w,0.5*Math.exp(r*Math.log(50)),mo);
    else if(md===4){const a=svf(w,0.5411961001461969,mo),b=svf(w,1.3065629648763766*Math.exp(r*Math.log(20)),mo);h=cmul(a[0],a[1],b[0],b[1])}
    else if(md===5){const fb=(mo===3?-0.98:0.98)*Math.min(1,r),ph=2*Math.PI*f/fc;h=cdiv(1-Math.abs(fb),0,1-fb*Math.cos(ph),fb*Math.sin(ph))}
    else if(md===6){const v=Math.max(0,Math.min(4,o.vowel||0)),sh=fc/1000;let i0=Math.floor(v);if(i0>3)i0=3;const t=v-i0,A=K.VOW[i0],B=K.VOW[i0+1];h=[0,0];
      for(let q=0;q<5;q++){const fq=(A[q]+(B[q]-A[q])*t)*sh,db=A[q+5]+(B[q+5]-A[q+5])*t,bw=(A[q+10]+(B[q+10]-A[q+10])*t)*sh,g=Math.pow(10,db/20),b=svf(f/fq,fq/bw,1);h[0]+=g*b[0];h[1]+=g*b[1]}}
    else{const b=svf(w,0.5*Math.exp(r*Math.log(50)),1);h=[1+2.9810717055349722*b[0],2.9810717055349722*b[1]]}
    const yr=m*h[0]+(1-m),yi=m*h[1];mg[j]=Math.hypot(yr,yi)*og}
  return mg}
SND_HOOKS.filterResp=sndFltResp;/* lane E: the analog curve of a Filter v2 or Auto Filter Clean setting, for drawing */

/* ---- the Auto Filter's Clean mode: the same processor in place of the biquads; LFO and envelope move its cutoff (det, cents) ---- */
const SNDF_AF={lp12:[3,0],lp24:[4,0],hp12:[3,2],hp24:[4,2],bp:[3,1],notch:[3,3],peak:[7,0],formant:[6,0],comb:[5,0],ladder:[0,0],diode:[1,0],ms20:[2,0]};
function sndAfMap(p){const T=SNDF_AF[p.type]||SNDF_AF.lp24,o={model:T[0],mode:T[1],os:2,freq:p.freq,drive:(p.drive||0)/100,mix:(p.mix??100)/100,out:0,vowel:p.vowel??1};
  if(p.type==='comb'){const g=Math.max(-.95,Math.min(.95,p.res));o.res=Math.abs(g)/.98;o.mode=g<0?3:0}
  else o.res=Math.max(0,Math.min(1,Math.log(Math.max(.5,p.res)/.5)/Math.log(50)));
  if(p.type==='formant')o.freq=p.freq*1000/1200;return o}
function sndAfClean(c,X){const v=X._v1;if(!v)return X;const s0=X.set,B={b1:X.b1,b2:X.b2,fm:X.fm};let S=null,on=false,cur=null;
  const one={getFrequencyResponse(fr,mg){mg.fill(1)}},zero={getFrequencyResponse(fr,mg){mg.fill(0)}},
   pr={getFrequencyResponse(fr,mg){if(cur)sndFltResp(Object.assign({},cur,{mix:1}),fr,mg);else mg.fill(1)}},
   pf={getFrequencyResponse(fr,mg){if(cur)sndFltResp(Object.assign({},cur,{mix:1}),fr,mg);const g=X.fg[0].gain.value||1;for(let j=0;j<mg.length;j++)mg[j]/=g}};
  X.set=function(p){s0.call(X,p);const cl=p.q==='clean';
   if(cl){cur=sndAfMap(p);if(!S){S=sndFltNode(c,cur);S.out.connect(v.post);S.mod(v.lg);S.mod(v.eg)}else S.set(cur);v.dry.gain.value=0;v.wet.gain.value=0;
     if(!on){try{v.i.disconnect(v.drv)}catch(e){}v.i.connect(S.in);on=true}X.b1=pr;X.b2=one;X.fm=[pf,zero,zero];X.snd=S}
   else{if(on){try{v.i.disconnect(S.in)}catch(e){}v.i.connect(v.drv);on=false}X.b1=B.b1;X.b2=B.b2;X.fm=B.fm;X.snd=null;cur=null}};
  return X}

/* ---- Filter v2: the new device ---- */
const SNDF_TYPES=[['ladder','Ladder 24 (Moog style)'],['diode','Diode 24 (303 style)'],['ms20','MS-20 12 (Sallen-Key)'],['svf12','SVF 12'],['svf24','SVF 24'],['comb','Comb'],['formant','Formant (vowels)']];
const sndF2p=(model,mode,freq,res,drive,mix,vowel,out)=>({model,mode:mode||'lp',os:'2x',freq,res,drive:drive||0,mix:mix??100,vowel:vowel||0,out:out||0});
function sndF2Map(p){return{model:SNDF_M[p.model]??0,mode:SNDF_MD[p.mode]??0,os:p.os==='1x'?1:2,freq:p.freq,res:(p.res??25)/100,drive:(p.drive||0)/100,mix:(p.mix??100)/100,out:p.out||0,vowel:p.vowel||0}}
const SNDF_TIP={model:'Model|Which filter circuit: Ladder 24 and Diode 24 are the warm 4-pole low-passes (Moog and 303 style), MS-20 12 screams at high resonance, SVF 12 and 24 are clean and can also be band-pass, high-pass, notch or peak, Comb rings at the cutoff pitch, Formant makes vowels.',
 mode:'Shape|Low-pass, band-pass, high-pass, notch or peak. Used by SVF 12 and SVF 24; MS-20 has low-pass and band-pass; on Comb, Notch gives the hollow (negative) comb. The ladders are always low-pass.',
 os:'Oversampling|2x runs the filter at twice the sample rate, so drive and high resonance stay clean (no whistling fold-back tones). Off uses less CPU.',
 q:'Hi-Fi|Hi-Fi on: higher quality sound (the new filter models at 2x, smoother sweeps, drive inside the filter, and Ladder, Diode and MS-20 in the Type list). Hi-Fi off: lighter and faster, good for slower computers or big projects.',
 freq:'Cutoff|Where the filter starts to cut (for Comb: the pitch it rings at; for Formant: shifts the vowel up or down).',res:'Resonance|How much the filter rings at the cutoff. At 100 % the ladders, Diode and MS-20 start to whistle on their own.',
 drive:'Drive|Saturation inside the filter: louder parts get rounder and the resonance gets grittier. 0 % is clean.',vowel:'Vowel|For the Formant model: a, e, i, o, u and the shades in between.',
 mix:'Mix|How much of the filtered sound you hear against the dry sound.',out:'Output|Level after the filter, in dB.'};
function sndTips(){const fx=document.getElementById('fxin');if(!fx)return;const t=typeof curT==='function'&&curT();if(!t||!t.fx)return;
  for(const f of t.fx){if(f.type!=='filter2'&&f.type!=='afilt')continue;const D=fx.querySelector(`.dev[data-id="${f.id}"]`);if(!D)continue;
   for(const k of(f.type==='afilt'?['q']:['model','mode','os'])){const s=D.querySelector(`select[data-x="${k}"]`);if(s&&!s.title&&!s.dataset.tip){const p=SNDF_TIP[k].split('|');s.title=p[1];s.setAttribute('aria-label',p[0])}}
   if(f.type==='filter2')for(const k of['freq','res','drive','vowel','mix','out']){const e=D.querySelector(`[data-c="fx:${f.id}:${k}"]`);if(e&&!e.title&&!e.dataset.tip)e.title=SNDF_TIP[k].split('|')[1]}}}
function sndDefFilter2(){
 ND('filter2',{name:'Filter',vw:540,grp:['Tone & colour','#f5c84c'],desc:'Filter v2: Ladder, Diode, MS-20, SVF 12 and 24, Comb and Formant models with drive inside, smooth sweeps and 2x oversampling',
  hint:'Drag the dot: sideways for cutoff, up and down for resonance',
  logo:['#f5c84c','#ff9a3c','<path d="M4 16h18c6 0 8 4 10 10s4 10 12 10" stroke-width="2.8"/><path d="M22 16c3-6 6-6 8 0" stroke-width="2.4" opacity=".7"/>','FILTER'],
  p:{freq:[20,20000,1200,'Hz',1],res:[0,100,25,'%'],drive:[0,100,0,'%'],vowel:[0,4,0,'f1'],mix:[0,100,100,'%'],out:[-24,24,0,'dB']},dial:['freq','res','drive','vowel','mix','out'],
  lab:{freq:'Cutoff',res:'Resonance',drive:'Drive',vowel:'Vowel',out:'Output'},init:{model:'ladder',mode:'lp',os:'2x'},
  sel:[['model','Model',SNDF_TYPES],['mode','Shape',[['lp','Low-pass'],['bp','Band-pass'],['hp','High-pass'],['notch','Notch'],['peak','Peak']]],['os','Oversampling',[['2x','2x'],['1x','Off']]]],
  pre:mergePre(PRS('Low-pass',[['init','Ladder low-pass',sndF2p('ladder','lp',1200,25)],['warm','Warm ladder, driven',sndF2p('ladder','lp',800,45,40)],['acid','Diode acid squelch',sndF2p('diode','lp',600,80,35)],
     ['ms20','MS-20 scream',sndF2p('ms20','lp',1500,90,50)],['butter','Clean 24 dB low-pass',sndF2p('svf24','lp',2000,0)],['soft','Soft 12 dB low-pass',sndF2p('svf12','lp',3000,15)]]),
   PRS('Other shapes',[['hp24','Clean 24 dB high-pass',sndF2p('svf24','hp',150,0)],['bp','Resonant band-pass',sndF2p('svf12','bp',1200,55)],['msbp','MS-20 band-pass',sndF2p('ms20','bp',900,70,20)],['notch','Notch',sndF2p('svf12','notch',1000,20)]]),
   PRS('Comb and vowels',[['comb','Comb tone',sndF2p('comb','lp',220,85)],['hollow','Hollow comb',sndF2p('comb','notch',400,70)],['vowa','Vowel a',sndF2p('formant','lp',1000,0,0,100,0)],['vowo','Vowel o, driven',sndF2p('formant','lp',1000,0,30,100,3)]])),
  node:c=>{const S=sndFltNode(c,sndF2Map(sndF2p('ladder','lp',1200,25))),an=c.createAnalyser();an.fftSize=2048;an.smoothingTimeConstant=.7;S.out.connect(an);
   return{in:S.in,out:S.out,an,snd:S,cur:{},set(p){S.set(sndF2Map(p));this.cur=p}}},
  draw:(g,w,h,f,X)=>{const p=f.p,T=8,Bm=h-16,Yd=db=>T+(1-clamp((db+48)/72,0,1))*(Bm-T);vbg(g,w,h);gridF(g,w,h);
   for(const db of[-36,-24,-12,0,12]){lineH(g,Yd(db),w,db===0?'rgba(255,255,255,.12)':'rgba(255,255,255,.05)');txt(g,db+'',3,Yd(db)-2,'rgba(255,255,255,.28)',8)}
   if(X&&X.an)drawSpec(g,w,h,X.an,{lo:20,hi:20000,top:-10,floor:-90,slope:3,smooth:.75,y0:T,h:Bm-T,st:X.st||(X.st={}),c0:'rgba(245,200,76,.22)',c1:'rgba(245,200,76,.02)',line:'rgba(245,200,76,.35)'});
   const N=Math.min(220,Math.floor(w/2)),fr=X&&X.fr&&X.fr.length===N?X.fr:new Float32Array(N),mg=new Float32Array(N);if(X)X.fr=fr;for(let k=0;k<N;k++)fr[k]=20*Math.pow(1000,k/(N-1));sndFltResp(sndF2Map(p),fr,mg);
   g.beginPath();for(let k=0;k<N;k++){const x=k/(N-1)*w,y=Yd(toDb(mg[k]));k?g.lineTo(x,y):g.moveTo(x,y)}g.lineTo(w,Yd(0));g.lineTo(0,Yd(0));g.closePath();g.fillStyle='rgba(245,200,76,.16)';g.fill();
   g.beginPath();for(let k=0;k<N;k++){const x=k/(N-1)*w,y=Yd(toDb(mg[k]));k?g.lineTo(x,y):g.moveTo(x,y)}glow(g,'#f5c84c',7);g.strokeStyle='#f5c84c';g.lineWidth=2.2;g.stroke();g.shadowBlur=0;
   txt(g,(SNDF_TYPES.find(a=>a[0]===p.model)||['',''])[1]+(p.drive>0?' · drive '+Math.round(p.drive)+'%':'')+(p.os==='1x'?'':' · 2x'),w-6,T+10,'rgba(255,255,255,.4)',8,'right')},
  hnd:(p,w,h)=>{const T=8,Bm=h-16,Yd=db=>T+(1-clamp((db+48)/72,0,1))*(Bm-T),fx=f0=>Math.log(f0/20)/Math.log(1000)*w,pk=(p.res||0)/100*30;
   return[{x:fx(clamp(p.freq,20,20000)),y:Yd(clamp(pk,-30,22)),c:'#f5c84c',l:'Cutoff · resonance',v:fmtHz(p.freq)+' · '+Math.round(p.res)+'%',drag:(x,y)=>{p.freq=clamp(20*Math.pow(1000,x/w),20,20000);p.res=clamp(((1-(y-T)/(Bm-T))*72-48)/30*100,0,100)}}]}});
 try{const c=FXCAT.find(x=>x[0]==='EQ & filter');if(c&&!c[1].includes('filter2'))c[1].push('filter2')}catch(e){}
 try{if(typeof FXIC==='object'&&!FXIC.filter2)FXIC.filter2='<path d="M3 8h8c4 0 5 2 7 6s2 7 3 7"/><path d="M11 8c2-3 4-3 5 0" opacity=".6"/>'}catch(e){}}
// hook into ND: the Auto Filter gets its Clean mode and its new types; Filter v2 is defined right after it
{const _nd=ND;ND=function(type,d){if(type==='afilt'&&d&&!d._snd){d._snd=1;
   for(const t of[['ladder','Ladder 24 (Hi-Fi)'],['diode','Diode 24 (Hi-Fi)'],['ms20','MS-20 12 (Hi-Fi)']])if(!AFT.some(a=>a[0]===t[0]))AFT.push(t);
   d.sel=[...(d.sel||[]),['q','Hi-Fi',[['classic','Off'],['clean','On']]]];/* the user's one switch (27 Nov, 23:00): q stays 'classic'|'clean' */d.init=Object.assign({},d.init||{},{q:'clean'});
   const n0=d.node;d.node=(c,t)=>sndAfClean(c,n0(c,t))}
  const r=_nd.apply(this,arguments);if(type==='afilt'&&!FXDEF.filter2)sndDefFilter2();return r}}
// presets carry no Quality: picking a preset on a Classic Auto Filter keeps it Classic (fxLib builds presets from a new device's settings)
{const _fl=fxLib;fxLib=function(){const r=_fl.apply(this,arguments);try{for(const k in FXPRE.afilt||{}){const v=FXPRE.afilt[k][1];if(v)delete v.q}}catch(e){}return r}}
{const _rf=renderFx;renderFx=function(){const r=_rf.apply(this,arguments);try{sndTips()}catch(e){}return r}}
/* ==SND1-js-end== */
