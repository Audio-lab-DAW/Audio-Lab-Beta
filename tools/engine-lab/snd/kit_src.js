/* ===== AudioLab shared DSP kit (task SND-0, lane L, v1) =====
   One plain-arithmetic core used by the worklet devices of lane L (Filter v2, Acid v2, Psy Bass v2, Saturate, ...).
   It runs in the worklet module (wlLoad appends sndWL(): the name there is SNDK) and on the main thread for tests.
   Rules so the native engine (task NB) can port it bit for bit:
   - only + - * /, Math.sqrt, Math.abs, Math.floor, comparisons, and Math.exp, Math.log, Math.log1p, Math.tan, Math.tanh,
     Math.sin, Math.cos, which V8 computes with fdlibm (native: native/third_party/fdlibm, ieee754::exp and so on);
   - no Math.pow, no Math.random, no fused multiply-add (native: -ffp-contract=off), evaluation order exactly as written;
   - denormals are kept, as the worklet keeps them; flush() zeroes states below 1e-30 and is called by the device.
   Everything is my own implementation from the papers:
   - TPT (zero-delay feedback) one-pole, SVF, ladder: V. Zavalishin, The Art of VA Filter Design, rev. 2.1.0 (2018);
   - nonlinear ladder (saturation of the solved stage inputs): after A. Huovilainen, DAFx-04;
   - first-order ADAA: J. Parker, V. Zavalishin, E. Le Bivic, DAFx-16; S. Bilbao, F. Esqueda, J. Parker, V. Valimaki, IEEE SPL 2017;
   - polyphase IIR halfband: R. Valenzuela, A. Constantinides, IEE Proc. 1983; the design formulas as in HIIR by
     Laurent de Soras (WTFPL licence; no HIIR code copied), coefficients computed by tools/engine-lab/snd/halfband_design.py;
   - formant table: the Csound manual's formant values, bass voice (data);
   - the diode ladder and Sallen-Key models are written out as state-space systems below and solved by the trapezoidal rule. */
function sndKitCore(){
  const PI=3.141592653589793,TINY=1e-30,LN2=0.6931471805599453,LN10_20=0.11512925464970229;
  const fl=v=>(v<TINY&&v>-TINY)?0:v;
  // g = tan(pi fc / sr), the prewarped integrator gain; fc kept inside 1 mHz .. 0.49 sr
  function prewarp(fc,sr){let f=fc;const mx=sr*0.49;if(!(f<mx))f=mx;if(!(f>1e-3))f=1e-3;return Math.tan(PI*f/sr)}
  function dbToGain(db){return Math.exp(db*LN10_20)}

  // ---- parameter smoothing ----
  // one-pole towards the target; time = time constant in ms; snaps to the target within 1e-9
  class Smooth{constructor(ms,sr,v){this.y=v||0;this.t=this.y;this.set(ms,sr)}
    set(ms,sr){this.a=ms>0?1-Math.exp(-1000/(ms*sr)):1}
    to(v){this.t=v} jump(v){this.y=v;this.t=v}
    next(){const d=this.t-this.y;if(d<1e-9&&d>-1e-9){this.y=this.t;return this.y}this.y+=this.a*d;return this.y}
    busy(){return this.y!==this.t}}
  // linear ramp over n samples, lands exactly on the target
  class Ramp{constructor(n,v){this.n=n>0?n|0:1;this.y=v||0;this.t=this.y;this.k=0;this.d=0}
    to(v){if(v===this.t)return;this.t=v;this.k=this.n;this.d=(v-this.y)/this.n}
    jump(v){this.y=v;this.t=v;this.k=0}
    next(){if(this.k>0){if(--this.k===0)this.y=this.t;else this.y+=this.d}return this.y}
    busy(){return this.k>0}}

  // ---- TPT one-pole (Zavalishin ch. 3): lp, hp, ap ----
  class OnePole{constructor(){this.s=0;this.G=0}
    setG(g){this.G=g/(1+g)} set(fc,sr){this.setG(prewarp(fc,sr))}
    lp(x){const v=(x-this.s)*this.G,y=v+this.s;this.s=y+v;return y}
    hp(x){return x-this.lp(x)}
    ap(x){const y=this.lp(x);return y+y-x}
    reset(){this.s=0} flush(){this.s=fl(this.s)}}

  // ---- state-variable filter (Zavalishin ch. 4, TPT): analog prototype LP 1/(s^2+ks+1), k=1/Q ----
  // modes: 0 low-pass, 1 band-pass (k*bp: 0 dB peak), 2 high-pass, 3 notch, 4 peak (lp-hp), 5 all-pass, 6 band-pass (bp, peak Q)
  class Svf{constructor(){this.s1=0;this.s2=0;this.g=0;this.k=1.4142135623730951;this.h=1;this.lp=0;this.bp=0;this.hp=0}
    setG(g,k){this.g=g;this.k=k;this.h=1/(1+g*(g+k))}
    set(fc,q,sr){this.setG(prewarp(fc,sr),1/(q>1e-3?q:1e-3))}
    tick(x){const g=this.g,hp=(x-(g+this.k)*this.s1-this.s2)*this.h,v1=g*hp,bp=v1+this.s1;this.s1=bp+v1;
      const v2=g*bp,lp=v2+this.s2;this.s2=lp+v2;this.hp=hp;this.bp=bp;this.lp=lp;return lp}
    run(x,m){this.tick(x);switch(m){case 1:return this.k*this.bp;case 2:return this.hp;case 3:return x-this.k*this.bp;
      case 4:return this.lp-this.hp;case 5:return x-2*this.k*this.bp;case 6:return this.bp;default:return this.lp}}
    reset(){this.s1=0;this.s2=0} flush(){this.s1=fl(this.s1);this.s2=fl(this.s2)}}

  // ---- saturator used inside filters: tanh(d*x)/d (d = drive >= 0.01); identity when lin ----
  const sat=(x,d)=>Math.tanh(d*x)/d;

  // ---- 4-pole ladder (Zavalishin ch. 5, TPT cascade with a solved feedback) ----
  // analog: H(s) = 1/((1+s)^4 + k), k = 4*res (res 1 = self-oscillation at fc). Outputs y[0..3] = 1 to 4 poles.
  // nl: the solved input and each stage input go through tanh(d x)/d (Huovilainen-style); quiet signals give the linear filter.
  class Ladder{constructor(){this.s=new Float64Array(4);this.y=new Float64Array(4);this.G=0;this.k=0;this.d=1;this.nl=false}
    set(fc,res,sr){const g=prewarp(fc,sr);this.G=g/(1+g);this.k=4*res}
    setDrive(d,nl){this.d=d>0.01?d:0.01;this.nl=!!nl}
    tick(x){const G=this.G,b=1-G,s=this.s,y=this.y,k=this.k;
      const S=b*(G*(G*(G*s[0]+s[1])+s[2])+s[3]),G4=G*G*G*G;
      let u=(x-k*S)/(1+k*G4);
      if(this.nl){const d=this.d;u=sat(u,d);
        let v=(u-s[0])*G,o=v+s[0];s[0]=o+v;y[0]=o;
        v=(sat(o,d)-s[1])*G;o=v+s[1];s[1]=o+v;y[1]=o;
        v=(sat(o,d)-s[2])*G;o=v+s[2];s[2]=o+v;y[2]=o;
        v=(sat(o,d)-s[3])*G;o=v+s[3];s[3]=o+v;y[3]=o;return o}
      let v=(u-s[0])*G,o=v+s[0];s[0]=o+v;y[0]=o;
      v=(o-s[1])*G;o=v+s[1];s[1]=o+v;y[1]=o;
      v=(o-s[2])*G;o=v+s[2];s[2]=o+v;y[2]=o;
      v=(o-s[3])*G;o=v+s[3];s[3]=o+v;y[3]=o;return o}
    reset(){this.s.fill(0)} flush(){const s=this.s;for(let i=0;i<4;i++)s[i]=fl(s[i])}}

  // ---- linear state-space system, trapezoidal (TPT) solve: dy/dt = wc (A y + B u), integrator states s ----
  // y = M^-1 (s + g B u) with M = I - g A; then s = 2y - s. M^-1 by Gauss-Jordan with partial pivoting when g or A change.
  function invert(M,n,out){const a=new Float64Array(n*2*n);
    for(let r=0;r<n;r++){for(let c=0;c<n;c++)a[r*2*n+c]=M[r*n+c];a[r*2*n+n+r]=1}
    for(let c=0;c<n;c++){let p=c,best=Math.abs(a[c*2*n+c]);for(let r=c+1;r<n;r++){const v=Math.abs(a[r*2*n+c]);if(v>best){best=v;p=r}}
      if(p!==c)for(let j=0;j<2*n;j++){const t=a[c*2*n+j];a[c*2*n+j]=a[p*2*n+j];a[p*2*n+j]=t}
      const iv=1/a[c*2*n+c];for(let j=0;j<2*n;j++)a[c*2*n+j]*=iv;
      for(let r=0;r<n;r++){if(r===c)continue;const f=a[r*2*n+c];if(f!==0)for(let j=0;j<2*n;j++)a[r*2*n+j]-=f*a[c*2*n+j]}}
    for(let r=0;r<n;r++)for(let c=0;c<n;c++)out[r*n+c]=a[r*2*n+n+c];return out}
  function ssPrep(A,n,g,Mi){const M=new Float64Array(n*n);for(let r=0;r<n;r++)for(let c=0;c<n;c++)M[r*n+c]=(r===c?1:0)-g*A[r*n+c];return invert(M,n,Mi)}

  // ---- diode ladder (4 poles), the linearised equal-capacitor diode (RC) ladder with feedback from the last stage ----
  // dy1 = wc(u - 2y1 + y2), dy2 = wc(y1 - 2y2 + y3), dy3 = wc(y2 - 2y3 + y4), dy4 = wc(y3 - y4), u = x - k y4. DC gain 1.
  // The cutoff knob sets the frequency where the feedback is at -180 degrees (the resonance pitch): wc = 2 pi fc / DW;
  // self-oscillation at k = DK (res 1). DW and DK from tools/engine-lab/snd/kit_test.py (the analog model).
  const DW=1.1952286093343936,DK=18.387755102040813; // DW = sqrt(10/7), DK = 901/49
  class Diode{constructor(){this.s=new Float64Array(4);this.y=new Float64Array(4);this.Mf=new Float64Array(16);this.Mo=new Float64Array(16);
      this.g=-1;this.k=-1;this.d=1;this.nl=false}
    set(fc,res,sr){const g=prewarp(fc,sr)/DW,k=DK*res;if(g===this.g&&k===this.k)return;this.g=g;this.k=k;
      ssPrep([-2,1,0,-k, 1,-2,1,0, 0,1,-2,1, 0,0,1,-1],4,g,this.Mf);ssPrep([-2,1,0,0, 1,-2,1,0, 0,1,-2,1, 0,0,1,-1],4,g,this.Mo)}
    setDrive(d,nl){this.d=d>0.01?d:0.01;this.nl=!!nl}
    tick(x){const s=this.s,y=this.y,g=this.g;let M=this.Mf,u=x;
      if(this.nl){const p=M[12]*(s[0]+g*x)+M[13]*s[1]+M[14]*s[2]+M[15]*s[3];u=sat(x-this.k*p,this.d);M=this.Mo}
      const a0=s[0]+g*u,a1=s[1],a2=s[2],a3=s[3];
      for(let r=0;r<4;r++)y[r]=M[r*4]*a0+M[r*4+1]*a1+M[r*4+2]*a2+M[r*4+3]*a3;
      for(let r=0;r<4;r++)s[r]=y[r]+y[r]-s[r];return y[3]}
    reset(){this.s.fill(0)} flush(){const s=this.s;for(let i=0;i<4;i++)s[i]=fl(s[i])}}

  // ---- Sallen-Key 2-pole (MS-20 style): dy1 = wc(x - y1 + k(y1 - y2)), dy2 = wc(y1 - y2) ----
  // analog: LP = y2 = 1/(s^2 + (2-k)s + 1); k = 2*res (res 1 = self-oscillation at fc); bp = y1 - y2.
  // nl: the feedback k(y1 - y2) goes through tanh(d x)/d (the MS-20's screaming resonance).
  class SallenKey{constructor(){this.s1=0;this.s2=0;this.g=0;this.k=0;this.d=1;this.nl=false;this.lp=0;this.bp=0}
    set(fc,res,sr){this.g=prewarp(fc,sr);this.k=2*res}
    setDrive(d,nl){this.d=d>0.01?d:0.01;this.nl=!!nl}
    tick(x){const g=this.g,k=this.k,s1=this.s1,s2=this.s2;let y1,y2;
      // linear solve of [1-g(k-1), gk; -g, 1+g] [y1;y2] = [s1 + g x; s2]
      const m11=1-g*(k-1),m12=g*k,m21=-g,m22=1+g,det=m11*m22-m12*m21,r1=s1+g*x;
      y1=(r1*m22-m12*s2)/det;y2=(m11*s2-m21*r1)/det;
      if(this.nl){const f=sat(k*(y1-y2),this.d),q=1+g;y1=(s1+g*(x+f))/q;y2=(s2+g*y1)/q}
      this.s1=y1+y1-s1;this.s2=y2+y2-s2;this.lp=y2;this.bp=y1-y2;return y2}
    reset(){this.s1=0;this.s2=0} flush(){this.s1=fl(this.s1);this.s2=fl(this.s2)}}

  // ---- 4-point Hermite (Catmull-Rom) read of a circular buffer, frac in [0,1) between i and i+1 ----
  function hermite(xm1,x0,x1,x2,f){const c1=0.5*(x1-xm1),c2=xm1-2.5*x0+2*x1-0.5*x2,c3=0.5*(x2-xm1)+1.5*(x0-x1);return((c3*f+c2)*f+c1)*f+x0}

  // ---- comb: feedback (y = x + fb * LP(y[n-D])) or feed-forward (y = x + fb * x[n-D]); D fractional, at least 2 ----
  class Comb{constructor(maxD){let n=8;while(n<maxD+8)n*=2;this.b=new Float64Array(n);this.m=n-1;this.w=0;this.D=2;this.fb=0;this.ff=false;this.lp=new OnePole();this.damp=false}
    set(D,fb,ff){this.D=D<2?2:(D>this.m-4?this.m-4:D);this.fb=fb;this.ff=!!ff}
    setDamp(fc,sr){this.damp=fc<sr*0.49;if(this.damp)this.lp.set(fc,sr)}
    read(){const p=this.w-this.D,i=Math.floor(p),f=p-i,b=this.b,m=this.m;return hermite(b[(i-1)&m],b[i&m],b[(i+1)&m],b[(i+2)&m],f)}
    tick(x){let r=this.read();if(this.damp)r=this.lp.lp(r);const y=x+this.fb*r;this.b[this.w&this.m]=this.ff?x:y;this.w=(this.w+1)&this.m;return y}
    reset(){this.b.fill(0);this.lp.reset()} flush(){this.lp.flush()}}

  // ---- formant filter: five band-passes (SVF, 0 dB peak) per vowel, morph 0..4 = a e i o u ----
  // Csound manual, formant values, bass voice: frequency (Hz), level (dB), bandwidth (Hz)
  const VOW=[[600,1040,2250,2450,2750, 0,-7,-9,-9,-20, 60,70,110,120,130],
    [400,1620,2400,2800,3100, 0,-12,-9,-12,-18, 40,80,100,120,120],
    [250,1750,2600,3050,3340, 0,-30,-16,-22,-28, 60,90,100,120,120],
    [400,750,2400,2600,2900, 0,-11,-21,-20,-40, 40,80,100,120,120],
    [350,600,2400,2675,2950, 0,-20,-32,-28,-36, 40,80,100,120,120]];
  class Formant{constructor(){this.f=[new Svf(),new Svf(),new Svf(),new Svf(),new Svf()];this.a=new Float64Array(5);this.v=-1;this.sh=1}
    set(v,sr,shift){let m=v<0?0:(v>4?4:v);const sh=shift>0?shift:1;if(m===this.v&&sh===this.sh)return;this.v=m;this.sh=sh;
      let i=Math.floor(m);if(i>3)i=3;const t=m-i,A=VOW[i],B=VOW[i+1];
      for(let j=0;j<5;j++){const fq=(A[j]+(B[j]-A[j])*t)*sh,db=A[j+5]+(B[j+5]-A[j+5])*t,bw=(A[j+10]+(B[j+10]-A[j+10])*t)*sh;
        this.f[j].set(fq,fq/bw,sr);this.a[j]=dbToGain(db)}}
    tick(x){let y=0;for(let j=0;j<5;j++)y+=this.a[j]*this.f[j].run(x,1);return y}
    reset(){for(const f of this.f)f.reset()} flush(){for(const f of this.f)f.flush()}}

  // ---- first-order ADAA waveshapers: y = (F(x) - F(x1)) / (x - x1), f at the midpoint when |x - x1| < 1e-5 ----
  // half a sample of delay. type 0 tanh (F = log cosh), 1 hard clip at +-1, 2 triangle fold (unity slope, folds at +-1)
  function fTanh(x){return Math.tanh(x)}
  function FTanh(x){const a=x<0?-x:x;return a+Math.log1p(Math.exp(-2*a))-LN2}
  function fClip(x){return x>1?1:(x<-1?-1:x)}
  function FClip(x){const a=x<0?-x:x;return a<=1?0.5*x*x:a-0.5}
  function fFold(x){const p=x+1,t=p-4*Math.floor(p*0.25);return t<2?t-1:3-t}
  function FFold(x){const p=x+1,t=p-4*Math.floor(p*0.25);if(t<2){const u=t-1;return 0.5*u*u}const u=3-t;return 1-0.5*u*u}
  const SH=[[fTanh,FTanh],[fClip,FClip],[fFold,FFold]];
  class Adaa{constructor(type){const s=SH[type|0]||SH[0];this.f=s[0];this.F=s[1];this.x1=0;this.F1=this.F(0)}
    tick(x){const d=x-this.x1,Fx=this.F(x);let y;
      if(d>1e-5||d<-1e-5)y=(Fx-this.F1)/d;else y=this.f(0.5*(x+this.x1));this.x1=x;this.F1=Fx;return y}
    reset(){this.x1=0;this.F1=this.F(0)}}
  // the plain shapers, for v1 paths and comparisons
  const shape=(type,x)=>(SH[type|0]||SH[0])[0](x);

  // ---- polyphase IIR halfband (two all-pass chains); 2x and 4x up and down ----
  // HB2: 12 coefficients, transition 0.0245: flat to 20 kHz at 44.1 kHz (19.9 kHz at 44.1, 21.6 kHz at 48), stop band -129.6 dB.
  // HB4: 6 coefficients, transition 0.13: the 2x to 4x stage, stop band -116.8 dB above the images.
  const HB2=[0.024632766055914156,0.0939079931803703,0.19572860180114765,0.3147561373767702,0.43678913138537423,0.5515004677868941,
    0.6531485656966076,0.7399029427099999,0.8126528761623639,0.873903643889726,0.9270206247169374,0.9758592958305158];
  const HB4=[0.03262941871683486,0.12509227548391386,0.26416656094596896,0.4360438734971898,0.6339747877375774,0.8647170642539785];
  // one chain of first-order all-pass sections (c + z^-1)/(1 + c z^-1) at the low rate: y = c (x - y1) + x1
  class APChain{constructor(c){this.c=Float64Array.from(c);this.x=new Float64Array(c.length);this.y=new Float64Array(c.length)}
    tick(v){const c=this.c,X=this.x,Y=this.y;for(let i=0;i<c.length;i++){const y=c[i]*(v-Y[i])+X[i];X[i]=v;Y[i]=y;v=y}return v}
    reset(){this.x.fill(0);this.y.fill(0)}
    flush(){const X=this.x,Y=this.y;for(let i=0;i<X.length;i++){X[i]=fl(X[i]);Y[i]=fl(Y[i])}}}
  class Half{constructor(co){const e=[],o=[];for(let i=0;i<co.length;i++)(i&1?o:e).push(co[i]);this.a0=new APChain(e);this.a1=new APChain(o);this.o0=0;this.o1=0}
    up(x){this.o0=this.a0.tick(x);this.o1=this.a1.tick(x)}        // two output samples: o0 then o1
    down(a,b){return 0.5*(this.a0.tick(b)+this.a1.tick(a))}       // a = the earlier sample of the pair
    reset(){this.a0.reset();this.a1.reset()} flush(){this.a0.flush();this.a1.flush()}}
  // 2x: up(x) fills o[0..1]; down(o) returns one sample. 4x: o[0..3].
  class Os2{constructor(co){this.u=new Half(co||HB2);this.d=new Half(co||HB2);this.o=new Float64Array(2)}
    up(x){this.u.up(x);this.o[0]=this.u.o0;this.o[1]=this.u.o1;return this.o}
    down(o){return this.d.down(o[0],o[1])}
    reset(){this.u.reset();this.d.reset()} flush(){this.u.flush();this.d.flush()}}
  class Os4{constructor(){this.u1=new Half(HB2);this.u2=new Half(HB4);this.d2=new Half(HB4);this.d1=new Half(HB2);this.o=new Float64Array(4)}
    up(x){const u1=this.u1,u2=this.u2,o=this.o;u1.up(x);const b=u1.o1;u2.up(u1.o0);o[0]=u2.o0;o[1]=u2.o1;u2.up(b);o[2]=u2.o0;o[3]=u2.o1;return o}
    down(o){const a=this.d2.down(o[0],o[1]),b=this.d2.down(o[2],o[3]);return this.d1.down(a,b)}
    reset(){this.u1.reset();this.u2.reset();this.d2.reset();this.d1.reset()} flush(){this.u1.flush();this.u2.flush();this.d2.flush();this.d1.flush()}}
  // a shaper run at 1x, 2x or 4x, with or without ADAA: the building block for B12, B19, B28, B36 and Saturate (N2)
  class Shaper{constructor(type,os,adaa){this.t=type|0;this.n=os===4?4:(os===2?2:1);this.os=this.n===4?new Os4():(this.n===2?new Os2():null);this.a=adaa?new Adaa(this.t):null}
    one(x){return this.a?this.a.tick(x):shape(this.t,x)}
    tick(x){if(!this.os)return this.one(x);const o=this.os.up(x);for(let i=0;i<this.n;i++)o[i]=this.one(o[i]);return this.os.down(o)}
    reset(){if(this.os)this.os.reset();if(this.a)this.a.reset()} flush(){if(this.os)this.os.flush()}}

  // ---- one factory for the probe processor and the tests: p = parameter list ----
  function make(name,p,sr){let o,f;switch(name){
    case 'onepole':o=new OnePole();o.set(p[0],sr);f=p[1]===1?x=>o.hp(x):(p[1]===2?x=>o.ap(x):x=>o.lp(x));break;
    case 'svf':o=new Svf();o.set(p[0],p[1],sr);f=x=>o.run(x,p[2]|0);break;
    case 'ladder':o=new Ladder();o.set(p[0],p[1],sr);o.setDrive(p[2],p[3]);f=x=>o.tick(x);break;
    case 'diode':o=new Diode();o.set(p[0],p[1],sr);o.setDrive(p[2],p[3]);f=x=>o.tick(x);break;
    case 'sk':o=new SallenKey();o.set(p[0],p[1],sr);o.setDrive(p[2],p[3]);f=x=>o.tick(x);break;
    case 'comb':o=new Comb(p[0]+8);o.set(p[0],p[1],p[3]);o.setDamp(p[2],sr);f=x=>o.tick(x);break;
    case 'formant':o=new Formant();o.set(p[0],sr,p[1]);f=x=>o.tick(x);break;
    case 'shaper':o=new Shaper(p[0],p[2],p[3]);f=x=>o.tick(p[1]*x);break;
    case 'os2':o=new Os2();f=x=>o.down(o.up(x));break;
    case 'os4':o=new Os4();f=x=>o.down(o.up(x));break;
    default:return null}
    let n=0;return{o,tick(x){const y=f(x);if((++n&2047)===0&&o.flush)o.flush();return y}}}

  return{v:1,PI,prewarp,dbToGain,Smooth,Ramp,OnePole,Svf,Ladder,Diode,SallenKey,Comb,Formant,Adaa,shape,APChain,Half,Os2,Os4,Shaper,hermite,invert,HB2,HB4,DW,DK,VOW,make,sat};
}
// the worklet part: the kit as SNDK, and a probe processor (al-snd-kit) that runs one kit block on its input, for tests only
function sndWL(){return '/* ===== AudioLab shared DSP kit (task SND-0) ===== */\nconst SNDK=('+sndKitCore.toString()+')();\n'+
  "registerProcessor('al-snd-kit',class extends AudioWorkletProcessor{constructor(o){super();const q=(o&&o.processorOptions)||{};this.b=SNDK.make(q.name,q.p||[],sampleRate)}"+
  "process(ins,outs){const i=ins[0]&&ins[0][0],o=outs[0];if(!o||!o[0])return true;const n=o[0].length,b=this.b;for(let k=0;k<n;k++){const y=b?b.tick(i?i[k]:0):0;for(let c=0;c<o.length;c++)o[c][k]=y}return true}});\n"}
const SND_HOOKS={kit:1};
