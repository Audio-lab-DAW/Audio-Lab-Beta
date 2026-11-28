  /* task MX-4 (lane K): the Spectral focus. 32 bands from 20 Hz to 20 kHz; in each band this track goes down only as much as the trigger is there,
     and only while it sounds (Duck amount, Trigger level, Trigger gain, Attack, Hold, Release and Curve as in the other focus modes).
     A short-time Fourier transform: Hann in and out, 75 % overlap, the two channels packed in one transform; unity when nothing ducks.
     Latency: one frame (1024 samples, 2048 above 64 kHz) plus the look-ahead, reported by fxLat. Hear the trigger plays the trigger with the same delay. */
  mxSp(ins,outs){const o=outs[0],oL=o[0],oR=o[1]||o[0],n=oL.length,m=ins[0]||[],k=ins[1]||[],mL=m[0],mR=m[1]||m[0],kL=k[0],kR=k[1]||k[0],N=this.N,la=this.la,bL=this.bL,bR=this.bR,gk=this.gk,ls=this.ls;
   const NF=sampleRate>64000?2048:1024;let Z=this.Z;
   if(!Z||Z.N!==NF){const lg=Math.round(Math.log2(NF)),w=new Float64Array(NF),br=new Uint32Array(NF),cs=new Float64Array(NF>>1),sn=new Float64Array(NF>>1),B=new Uint8Array((NF>>1)+1);
    for(let j=0;j<NF;j++){w[j]=.5-.5*Math.cos(2*Math.PI*j/NF);let r=0;for(let b=0;b<lg;b++)r|=((j>>b)&1)<<(lg-1-b);br[j]=r}
    for(let j=0;j<NF>>1;j++){cs[j]=Math.cos(2*Math.PI*j/NF);sn[j]=-Math.sin(2*Math.PI*j/NF)}
    for(let j=0;j<=NF>>1;j++){const f=Math.max(1,j)*sampleRate/NF;B[j]=Math.max(0,Math.min(31,Math.floor(32*Math.log(f/20)/Math.log(1000))))}
    Z=this.Z={N:NF,H:NF>>2,w,br,cs,sn,B,iL:new Float64Array(NF),iR:new Float64Array(NF),iK:new Float64Array(NF),oL:new Float64Array(NF),oR:new Float64Array(NF),re:new Float64Array(NF),im:new Float64Array(NF),kr:new Float64Array(NF),ki:new Float64Array(NF),E:new Float64Array(32),e:new Float64Array(32),hc:new Float64Array(32),g:new Float64Array(32).fill(1),p:0,c:0}}
   let w0=this.w,mk=this.mk,mg=this.mg,p=Z.p,c=Z.c;const M=NF-1,ZL=Z.oL,ZR=Z.oR,IL=Z.iL,IR=Z.iR,IK=Z.iK;
   for(let i=0;i<n;i++){bL[w0]=mL?mL[i]:0;bR[w0]=mR?mR[i]:0;const r=(w0-la+N)%N;w0=(w0+1)%N;
    oL[i]=ZL[p];oR[i]=ZR[p];ZL[p]=0;ZR[p]=0;
    const xl=kL?kL[i]*gk:0,xr=kL?kR[i]*gk:0,kv=(xl+xr)*.5,ka=kv<0?-kv:kv;if(ka>mk)mk=ka;
    if(ls){IL[p]=kv;IR[p]=kv}else{IL[p]=bL[r];IR[p]=bR[r]}IK[p]=kv;
    p=(p+1)&M;if(++c>=Z.H){c=0;Z.p=p;const gm=this.mxFr(Z,ls);if(gm<mg)mg=gm}}
   Z.p=p;Z.c=c;this.w=w0;
   if(this.live){this.mt+=n;if(this.mt>=512){this.port.postMessage({k:mk,g:mg,b:Float32Array.from(Z.g)});mk=0;mg=1;this.mt=0}}this.mk=mk;this.mg=mg;return true}
  mxFFT(Z,re,im,inv){const n=Z.N,br=Z.br,cs=Z.cs,sn=Z.sn;for(let i=0;i<n;i++){const j=br[i];if(j>i){let t=re[i];re[i]=re[j];re[j]=t;t=im[i];im[i]=im[j];im[j]=t}}
   for(let s=2;s<=n;s<<=1){const h=s>>1,st=n/s;for(let i=0;i<n;i+=s)for(let j=0;j<h;j++){const c=cs[j*st],q=inv?-sn[j*st]:sn[j*st],a=i+j,b=a+h,xr=re[b]*c-im[b]*q,xi=re[b]*q+im[b]*c;re[b]=re[a]-xr;im[b]=im[a]-xi;re[a]+=xr;im[a]+=xi}}}
  mxFr(Z,ls){const n=Z.N,M=n-1,p=Z.p,w=Z.w,re=Z.re,im=Z.im,kr=Z.kr,ki=Z.ki,B=Z.B,E=Z.E,e=Z.e,hc=Z.hc,g=Z.g,H=Z.H,h=n>>1;
   for(let j=0;j<n;j++){const q=(p+j)&M,ww=w[j];re[j]=Z.iL[q]*ww;im[j]=Z.iR[q]*ww;kr[j]=Z.iK[q]*ww;ki[j]=0}
   this.mxFFT(Z,re,im,false);let gm=1;
   if(!ls){this.mxFFT(Z,kr,ki,false);E.fill(0);for(let j=1;j<h;j++)E[B[j]]+=kr[j]*kr[j]+ki[j]*ki[j];
    const sc=32/(3*n*n),thL=this.thL,amt=this.amt,pw=this.pw,atS=this.atS,hdS=this.hdS,rlS=this.rlS;
    for(let b=0;b<32;b++){const A=Math.sqrt(E[b]*sc),tr=A>thL?Math.min(1,8.6858896*Math.log(A/thL)/6):0;let v=e[b];
     if(tr>v){v=Math.min(tr,v+H/atS);hc[b]=hdS}else if(hc[b]>0)hc[b]-=H;else if(v>tr)v=Math.max(tr,v-H/rlS);e[b]=v;const gb=v>0?1-amt*Math.pow(v,pw):1;g[b]=gb;if(gb<gm)gm=gb}
    for(let j=0;j<=h;j++){const gb=g[B[j]];if(gb===1)continue;re[j]*=gb;im[j]*=gb;if(j>0&&j<h){re[n-j]*=gb;im[n-j]*=gb}}}
   this.mxFFT(Z,re,im,true);const s=1/(1.5*n),ZL=Z.oL,ZR=Z.oR;
   for(let j=0;j<n;j++){const q=(p+j)&M,ww=w[j]*s;ZL[q]+=re[j]*ww;ZR[q]+=im[j]*ww}
   return gm}
