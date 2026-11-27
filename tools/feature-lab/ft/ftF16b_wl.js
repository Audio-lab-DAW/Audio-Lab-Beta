const FTVS_WL=`/* ===== AudioLab volume shaper (tasks FT-F16a and FT-F16b) ===== */
(()=>{const NB=${FTVS.NB};
function sOf(T,b){if(T.length<2||b<=0)return b*60/T[0].bpm;let lo=0,hi=T.length-1;while(lo<hi){const m=(lo+hi+1)>>1;if(T[m].b<=b)lo=m;else hi=m-1}const p=T[lo],n=T[lo+1],d=b-p.b;if(!n||!p.ramp)return p.s+d*60/p.bpm;const k=(n.bpm-p.bpm)/(n.b-p.b);return Math.abs(k)<1e-9?p.s+d*60/p.bpm:p.s+60/k*Math.log((p.bpm+k*d)/p.bpm)}
function bOf(T,s){if(T.length<2||s<=0)return s*T[0].bpm/60;let lo=0,hi=T.length-1;while(lo<hi){const m=(lo+hi+1)>>1;if(T[m].s<=s)lo=m;else hi=m-1}const p=T[lo],n=T[lo+1],d=s-p.s;if(!n||!p.ramp)return p.b+d*p.bpm/60;const k=(n.bpm-p.bpm)/(n.b-p.b);return Math.abs(k)<1e-9?p.b+d*p.bpm/60:p.b+p.bpm*(Math.exp(k*d/60)-1)/k}
function bpmAt(T,b){if(T.length<2)return T[0].bpm;let lo=0,hi=T.length-1;while(lo<hi){const m=(lo+hi+1)>>1;if(T[m].b<=b)lo=m;else hi=m-1}const p=T[lo],n=T[lo+1];if(!n||!p.ramp)return p.bpm;return p.bpm+(n.bpm-p.bpm)*Math.max(0,Math.min(1,(b-p.b)/(n.b-p.b)))}
function ev(P,x,sm){let i=0;while(i<P.length-2&&P[i+1].x<=x)i++;const a=P[i],b=P[Math.min(P.length-1,i+1)],dx=Math.max(1e-6,b.x-a.x);let t=(x-a.x)/dx;t=t<0?0:t>1?1:t;if(sm)t=(1-Math.cos(Math.PI*t))/2;const c=a.c||0;t=c>=0?Math.pow(t,1+c*3):1-Math.pow(1-t,1-c*3);return a.y+(b.y-a.y)*t}
/* FT-F16b: RBJ biquads; a Linkwitz-Riley crossover is two Butterworth stages, its low and high add up to a 2nd-order all-pass */
function bq(k,f,sr){const w=2*Math.PI*Math.min(f,sr*.45)/sr,cs=Math.cos(w),al=Math.sin(w)/(2*Math.SQRT1_2);let b0,b1,b2;
 if(k===0){b0=(1-cs)/2;b1=1-cs;b2=b0}else if(k===1){b0=(1+cs)/2;b1=-(1+cs);b2=b0}else{b0=1-al;b1=-2*cs;b2=1+al}const a0=1+al;return[b0/a0,b1/a0,b2/a0,-2*cs/a0,(1-al)/a0]}
class FtVs extends AudioWorkletProcessor{
 constructor(o){super();const po=(o&&o.processorOptions)||{};this.p=null;this.T=[{b:0,s:0,bpm:120,ramp:0}];this.A=[{t:0,b:0,s:0,on:1}];this.on=1;this.g=-1;this.bi=new Float32Array(NB);this.bo=new Float32Array(NB);this.lb=-1;this.loud=0;this.left=0;
  this.tb=[];this.ti=-1;this.lt=-1;this.es=Infinity;this.pk=0;this.arm=1;this.kl=0;this.trg=0;this.C=null;this.st=new Float64Array(36);
  this.apply(po);for(const m of(po.q||[]))this.apply(m);this.port.onmessage=e=>this.apply(e.data)}
 apply(d){if(!d)return;if(d.tm&&d.tm.length)this.T=d.tm;if(d.p){const o=this.p;this.p=d.p;if(!o||o.bn!==d.p.bn||o.f1!==d.p.f1||o.f2!==d.p.f2){const sr=sampleRate,f1=d.p.f1||150,f2=d.p.f2||2500;this.C=[bq(0,f1,sr),bq(1,f1,sr),bq(0,f2,sr),bq(1,f2,sr),bq(2,f2,sr)];this.st.fill(0)}}
  if(d.tb){this.tb=d.tb;this.ti=-1}if(typeof d.lt==='number')this.lt=d.lt;if(typeof d.on==='number'){this.on=d.on;if(!d.on){const t=currentTime;this.A=this.A.filter((x,i)=>!i||x.t<=t);while(this.A.length>1&&this.A[1].t<=t)this.A.shift()}}
  if(d.a){const a=d.a;this.A=this.A.filter(x=>x.t<a.t);this.A.push({t:a.t,b:a.b,s:sOf(this.T,a.b),on:a.on==null?1:a.on})}
  if(d.tm)for(const a of this.A)a.s=sOf(this.T,a.b)}
 /* one biquad, transposed direct form II; st holds two values per filter and channel */
 f(c,o,x){const s=this.st,y=c[0]*x+s[o];s[o]=c[1]*x-c[3]*y+s[o+1];s[o+1]=c[2]*x-c[4]*y;return y}
 split(x,ch,g,bs,bn){const C=this.C,o=ch*18;let lo=this.f(C[0],o,this.f(C[0],o+2,x)),hi=this.f(C[1],o+4,this.f(C[1],o+6,x));
  if(bn<3)return lo*(bs[0]?g:1)+hi*(bs[1]?g:1);
  const md=this.f(C[2],o+8,this.f(C[2],o+10,hi)),hh=this.f(C[3],o+12,this.f(C[3],o+14,hi));lo=this.f(C[4],o+16,lo);return lo*(bs[0]?g:1)+md*(bs[1]?g:1)+hh*(bs[2]?g:1)}
 process(ins,outs){const I=ins[0]||[],O=outs[0],n=O[0].length,p=this.p;const i0=I[0],i1=I[1]||I[0];
  if(!p||!p.pts||p.pts.length<2){for(let c=0;c<O.length;c++){const s=c?i1:i0;if(s)O[c].set(s);else O[c].fill(0)}return true}
  const sr=sampleRate,F=currentFrame,T=this.T,A=this.A,P=p.pts,cy=p.cb,ph=p.ph||0,d=p.d,sm=!!p.sm,k=p.k,flat=T.length<2,bins=this.bi,bout=this.bo,o0=O[0],o1=O[1]||null;let g=this.g,lb=this.lb,loud=0,x=0;
  const tg=p.tg|0,bn=p.bn|0,bs=p.bs||[1,1,1],sh=bn>1&&!p.all,K=ins[1]||[],k0=K[0],k1=K[1]||K[0],TB=this.tb,nT=TB.length;let ti=this.ti,es=this.es,pk=this.pk,arm=this.arm,kl=this.kl,trg=0;
  const th=p.th||.063,pkR=Math.exp(-1/(.04*sr)),gap=Math.round(.06*sr),lt=this.lt;let bpm=0;
  for(let i=0;i<n;i++){const tt=(F+i)/sr;while(A.length>1&&A[1].t<=tt){A.shift();this.on=A[0].on}const a=A[0];
   const beat=flat?a.b+(tt-a.t)*T[0].bpm/60:bOf(T,a.s+(tt-a.t));let q;
   if(tg===0){q=beat/cy+ph;q-=Math.floor(q)}
   else{if(!bpm)bpm=bpmAt(T,beat);let e=Infinity;
    if(tg===1){if(this.on&&nT){if(ti>=nT||(ti>=0&&TB[ti]>beat)){let lo=0,hi=nT-1;ti=-1;while(lo<=hi){const m=(lo+hi)>>1;if(TB[m]<=beat){ti=m;lo=m+1}else hi=m-1}}while(ti+1<nT&&TB[ti+1]<=beat){ti++;trg=1}if(ti>=0)e=beat-TB[ti]}
     if(lt>=0&&tt>=lt){const el=(tt-lt)*bpm/60;if(el<e)e=el}}
    else{const kx=k0?Math.max(k0[i]<0?-k0[i]:k0[i],k1[i]<0?-k1[i]:k1[i]):0;pk=kx>pk?kx:pk*pkR;if(pk<1e-9)pk=0;if(pk>kl)kl=pk;if(es<Infinity)es++;
     if(arm&&pk>th&&es>=gap){es=0;arm=0;trg=1}else if(!arm&&pk<th*.5)arm=1;if(es<Infinity)e=es/sr*bpm/60}
    q=e===Infinity?1:Math.min(1,e/cy+ph)}
   x=q;const v=ev(P,q,sm),tg2=1-d+d*v;if(g<0||k>=1)g=tg2;else g+=(tg2-g)*k;
   const l=i0?i0[i]:0,r=i1?i1[i]:0;if(sh){o0[i]=this.split(l,0,g,bs,bn);if(o1)o1[i]=this.split(r,1,g,bs,bn)}else{o0[i]=l*g;if(o1)o1[i]=r*g}
   const bb=Math.min(NB-1,Math.floor(q*NB));if(bb!==lb){lb=bb;bins[bb]=0;bout[bb]=0}const m=Math.max(l<0?-l:l,r<0?-r:r);if(m>bins[bb])bins[bb]=m;const mo=m*g;if(mo>bout[bb])bout[bb]=mo;if(m>1e-5)loud=1}
  this.g=g;this.lb=lb;this.ti=ti;this.es=es;this.pk=pk;this.arm=arm;this.kl=kl;if(trg)this.trg=1;if(loud||(tg===2&&kl>1e-5))this.loud=1;this.left-=n;
  if(this.left<=0){this.left=Math.round(sr/20);if(this.loud){this.loud=0;this.port.postMessage({bi:bins.slice(),bo:bout.slice(),x,kl:this.kl,tr:this.trg});this.kl=0;this.trg=0}}
  return true}}
registerProcessor('al-ftvs',FtVs)})();`;