
/* ===== lane D (task NI-8): I4 mono-loss map =====
   Per track and per band, how much level it loses when the mix is folded to mono, read from NI-3's per-beat mid and side bands
   (loss = mid / (mid + side) in power: 0 dB holds, -3 dB is a wide or one-sided sound, more means parts of it cancel). Tracks that
   cancel each other in mono: the loudest tracks of the range rendered offline on their own (NI-7's one-track render, a tap after the
   fader and pan, at 22.05 kHz) and their spectra compared pair by pair in a worker. Nothing is added to the live path or to exports. */
NI.mono={w:null,tok:0,res:null,pairs:null,busy:false,tm:0,key:'',pend:null,runs:0,song:false,pairRuns:0};
const NI_ML_SR=22050,NI_ML_N=4096,NI_ML_MAXT=8;
/* the colour of a loss (dB lost, positive): cyan holds, grey one-sided, amber partly cancels, red cancels */
function NI_mlCol(L){const st=[[0,[76,201,240]],[3,[139,139,151]],[6,[255,181,71]],[12,[255,107,107]]];let a=st[0],b=st[st.length-1];
  if(L<=0)return st[0][1];if(L>=12)return st[3][1];for(let i=1;i<st.length;i++)if(L<=st[i][0]){a=st[i-1];b=st[i];break}const f=(L-a[0])/(b[0]-a[0]);return a[1].map((v,i)=>Math.round(v+(b[1][i]-v)*f))}
function NI_mlHz(f){return f>=1000?(Math.round(f/100)/10).toString().replace(/\.0$/,'')+' kHz':Math.round(f)+' Hz'}
function NI_mlRangeTxt(a,b){return a>=1000?(Math.round(a/100)/10).toString().replace(/\.0$/,'')+' to '+NI_mlHz(b):Math.round(a)+' to '+NI_mlHz(b)}
const NI_mlDb=v=>{const r=Math.round(v*10)/10;return(r<0?'−':r>0?'+':'')+INS.fmt(Math.abs(r),'dB')};
/* the range: NI-7's (the loop or the 8 bars around the playhead), or the whole song */
function NI_mlRange(){const M=NI.mono;if(M.song){const e=Math.ceil(NI_anEnd());return{b0:0,b1:Math.max(1,e),how:'the whole song'}}return NI_jourRange()}
/* per track over [b0, b1) from the cache: summed mid and side power per band. Resolves after NI.an.ensure; o.prog(done, total) */
async function NI_mlTracks(b0,b1,o){o=o||{};const L=NI_anTracks().filter(t=>!t.mute&&(t.clips||[]).some(c=>!c.mute&&c.start<b1&&c.start+c.len>b0-NI_AN_SEG));
  const r=await NI_anEnsure({tracks:L,b0,b1,prog:o.prog});if(r.cancelled&&r.done<r.total)return{cancelled:true};
  const NB=NI_AN_NB,bands=NI.an.bands,out=[];
  for(const t of L){const PM=new Float64Array(NB),PS=new Float64Array(NB);let n=0;
    for(let b=Math.floor(b0);b<Math.ceil(b1);b++){const g=NI_anGet(t,b,{noQueue:true});if(!g||g.silent||!g.mid||!g.play)continue;n++;for(let i=0;i<NB;i++){PM[i]+=Math.pow(10,g.mid[i]/10);PS[i]+=Math.pow(10,g.side[i]/10)}}
    if(!n)continue;let mx=0;for(let i=0;i<NB;i++)mx=Math.max(mx,PM[i]+PS[i]);if(mx<1e-11)continue;
    const loss=new Float32Array(NB),sig=new Float32Array(NB);let sm=0,sa=0;
    for(let i=0;i<NB;i++){const a=PM[i]+PS[i];loss[i]=a>0?Math.min(60,-10*Math.log10(Math.max(PM[i],a*1e-6)/a)):0;const rel=10*Math.log10(a/mx+1e-30);sig[i]=rel>=-12?1:rel<=-30?0:.15+.85*(rel+30)/18;if(rel>-30){sm+=PM[i];sa+=a}}
    const tot=sa>0?-10*Math.log10(Math.max(sm,sa*1e-6)/sa):0;
    /* the worst stretch: neighbouring bands (one quiet band may sit between) that lose 3.5 dB or more */
    let best=null;for(let i=0;i<NB;){if(!(sig[i]>.15&&loss[i]>=3.5)){i++;continue}let j=i,gap=0,k=i+1;for(;k<NB;k++){if(sig[k]>.15&&loss[k]>=3.5){j=k;gap=0}else if(++gap>1)break}
      let m=0,a=0;for(let q=i;q<=j;q++){if(sig[q]<=.15)continue;m+=PM[q];a+=PM[q]+PS[q]}const ls=-10*Math.log10(Math.max(m,a*1e-6)/a),lost=a-m;
      if(!best||lost>best.lost)best={i0:i,i1:j,loss:ls,lost,fa:bands[i]*Math.pow(2,-1/12),fb:bands[j]*Math.pow(2,1/12)};i=j+1}
    out.push({t,id:t.id,name:t.name,color:t.color||'#8b8b97',loss,sig,tot,worst:best,beats:n,PM,PS})}
  return{tracks:out}}
/* the pair analysis of one set of renders. d: {T: [{L, R}], sr, N}. Pure: runs in the worker */
function NI_mlWork(d){const T=d.T,nT=T.length,sr=d.sr,N=d.N,H=N>>1,hop=N>>1;
  const win=new Float32Array(N);for(let i=0;i<N;i++)win[i]=.5-.5*Math.cos(2*Math.PI*i/N);
  const lv=Math.log2(N),rev=new Uint32Array(N);for(let i=0;i<N;i++){let r=0,x=i;for(let b=0;b<lv;b++){r=(r<<1)|(x&1);x>>=1}rev[i]=r}
  const cs=new Float64Array(H),sn=new Float64Array(H);for(let i=0;i<H;i++){cs[i]=Math.cos(2*Math.PI*i/N);sn[i]=-Math.sin(2*Math.PI*i/N)}
  const re=new Float64Array(N),im=new Float64Array(N);
  const fft=()=>{for(let i=0;i<N;i++){const j=rev[i];if(j>i){let t=re[i];re[i]=re[j];re[j]=t;t=im[i];im[i]=im[j];im[j]=t}}
    for(let s=2;s<=N;s<<=1){const h=s>>1,st=N/s;for(let i=0;i<N;i+=s)for(let k=0;k<h;k++){const c=cs[k*st],q=sn[k*st],a=i+k,b=a+h,xr=re[b]*c-im[b]*q,xi=re[b]*q+im[b]*c;re[b]=re[a]-xr;im[b]=im[a]-xi;re[a]+=xr;im[a]+=xi}}};
  /* 1/3 octave bands from 20 Hz up to the top of the render */
  const bw=sr/N,cen=[];for(let k=0;;k++){const c=20*Math.pow(2,k/3);if(c*Math.pow(2,1/6)>=sr/2)break;cen.push(c)}const NB=cen.length,bOf=new Int16Array(H+1).fill(-1);
  for(let k=0;k<NB;k++){const a=Math.ceil(cen[k]*Math.pow(2,-1/6)/bw),b=Math.floor(cen[k]*Math.pow(2,1/6)/bw);for(let i=Math.max(1,a);i<=Math.min(H,b);i++)bOf[i]=k}
  const len=T.reduce((m,x)=>Math.max(m,x.L.length),0),F=len<N?1:Math.floor((len-N)/hop)+1,nP=nT*(nT-1)/2;
  const PM=new Float64Array(nT*NB),PST=new Float64Array(nT*NB),CM=new Float64Array(nP*NB),CS=new Float64Array(nP*NB);
  const Lr=new Float64Array(nT*(H+1)),Li=new Float64Array(nT*(H+1)),Rr=new Float64Array(nT*(H+1)),Ri=new Float64Array(nT*(H+1)),on=new Uint8Array(nT);
  for(let f=0;f<F;f++){const i0=f*hop;
    for(let t=0;t<nT;t++){const L=T[t].L,R=T[t].R;let e=0;for(let i=0;i<N;i++){const k=i0+i,l=k<L.length?L[k]:0,r=k<R.length?R[k]:0;re[i]=l*win[i];im[i]=r*win[i];e+=l*l+r*r}on[t]=e>1e-12?1:0;if(!on[t])continue;fft();
      const o=t*(H+1);for(let k=0;k<=H;k++){const k2=(N-k)&(N-1),ar=re[k],ai=im[k],br=re[k2],bi=im[k2];Lr[o+k]=(ar+br)*.5;Li[o+k]=(ai-bi)*.5;Rr[o+k]=(ai+bi)*.5;Ri[o+k]=(br-ar)*.5}
      for(let k=1;k<=H;k++){const b=bOf[k];if(b<0)continue;const lr=Lr[o+k],li=Li[o+k],rr=Rr[o+k],ri=Ri[o+k],mr=(lr+rr)*.5,mi=(li+ri)*.5;PM[t*NB+b]+=mr*mr+mi*mi;PST[t*NB+b]+=lr*lr+li*li+rr*rr+ri*ri}}
    let p=0;for(let a=0;a<nT;a++)for(let b=a+1;b<nT;b++,p++){if(!on[a]||!on[b])continue;const oa=a*(H+1),ob=b*(H+1);
      for(let k=1;k<=H;k++){const q=bOf[k];if(q<0)continue;const mar=(Lr[oa+k]+Rr[oa+k])*.5,mai=(Li[oa+k]+Ri[oa+k])*.5,mbr=(Lr[ob+k]+Rr[ob+k])*.5,mbi=(Li[ob+k]+Ri[ob+k])*.5;
        CM[p*NB+q]+=mar*mbr+mai*mbi;CS[p*NB+q]+=Lr[oa+k]*Lr[ob+k]+Li[oa+k]*Li[ob+k]+Rr[oa+k]*Rr[ob+k]+Ri[oa+k]*Ri[ob+k]}}}
  return{NB,cen:Float64Array.from(cen),PM,PST,CM,CS,nT}}
function NI_mlRun2(d){const M=NI.mono;if(M.wk===undefined){try{const code='const NI_mlWork='+NI_mlWork.toString()+';onmessage=e=>{const r=NI_mlWork(e.data);postMessage({id:e.data.id,r})}';
    M.wk=new Worker(URL.createObjectURL(new Blob([code],{type:'text/javascript'})));M.wkq=new Map();M.wkid=0;M.wk.onmessage=e=>{const f=M.wkq.get(e.data.id);if(f){M.wkq.delete(e.data.id);f(e.data.r)}};
    M.wk.onerror=e=>{console.warn('NI mono-loss worker',e&&e.message);for(const f of M.wkq.values())f(null,new Error('the analysis worker stopped'));M.wkq.clear();try{M.wk.terminate()}catch(_){}M.wk=null}}catch(e){M.wk=null}}
  if(!M.wk)return new Promise(r=>setTimeout(()=>r(NI_mlWork(d)),0));const id=++M.wkid;d.id=id;
  return new Promise((res,rej)=>{M.wkq.set(id,(r,e)=>r?res(r):rej(e));M.wk.postMessage(d,d.T.flatMap(x=>[x.L.buffer,x.R.buffer]))})}
/* render one track after its fader and pan (NI-7's one-track render), at 22.05 kHz */
async function NI_mlRender(t,b0,b1){const taps=[1+(t.fx||[]).filter(f=>f.on).length];taps.raw=true;taps.sr=NI_ML_SR;return NI_jourRender(t,b0,b1,NI_jourSteps(t),taps)}
/* the pairs that cancel each other in mono over [b0, b1) (at most 8 bars), among the loudest tracks (at most 8) */
async function NI_mlPairs(list,b0,b1,isOk){const bEnd=Math.min(b1,barStart(barPos(b0+1e-6).bar+8)),c=list.slice().sort((a,b)=>{const s=x=>{let v=0;for(let i=0;i<x.PM.length;i++)v+=x.PM[i]+x.PS[i];return v};return s(b)-s(a)}).slice(0,NI_ML_MAXT);
  if(c.length<2)return{pairs:[],b0,b1:bEnd,n:c.length};const T=[];for(const x of c){if(isOk&&!isOk())return null;const r=await NI_mlRender(x.t,b0,bEnd);T.push({L:r.L,R:r.R})}if(isOk&&!isOk())return null;
  const w=await NI_mlRun2({T,sr:NI_ML_SR,N:NI_ML_N});if(!w||(isOk&&!isOk()))return null;const NB=w.NB,pairs=[];let p=0;
  for(let a=0;a<c.length;a++)for(let b=a+1;b<c.length;b++,p++){let mx=0;for(let k=0;k<NB;k++)mx=Math.max(mx,w.PM[a*NB+k]+w.PM[b*NB+k]);if(mx<1e-10)continue;
    const bad=new Uint8Array(NB);for(let k=0;k<NB;k++){const pa=w.PM[a*NB+k],pb=w.PM[b*NB+k],s=pa+pb;if(s<mx*1e-3||Math.min(pa,pb)<Math.max(pa,pb)*.0316)continue;/* both in the band, within 15 dB */
      if((s+2*w.CM[p*NB+k])/s<=.5)bad[k]=1}
    let best=null;for(let i=0;i<NB;){if(!bad[i]){i++;continue}let j=i;while(j+1<NB&&bad[j+1])j++;let s=0,m=0,st=0,sm=0;for(let k=i;k<=j;k++){const pa=w.PM[a*NB+k],pb=w.PM[b*NB+k];s+=pa+pb;m+=pa+pb+2*w.CM[p*NB+k];st+=w.PST[a*NB+k]+w.PST[b*NB+k];sm+=w.PST[a*NB+k]+w.PST[b*NB+k]+2*w.CS[p*NB+k]}
      const lm=10*Math.log10(Math.max(m,s*1e-6)/s),ls=10*Math.log10(Math.max(sm,st*1e-6)/st),lost=s-Math.max(0,m);if(!best||lost>best.lost)best={fa:w.cen[i]*Math.pow(2,-1/6),fb:w.cen[j]*Math.pow(2,1/6),mono:lm,stereo:ls,lost};i=j+1}
    if(best)pairs.push(Object.assign({a:c[a].t,b:c[b].t},best))}
  pairs.sort((x,y)=>x.mono-y.mono);return{pairs,b0,b1:bEnd,n:c.length}}
/* measure everything for the window; resolves {tracks, pairs, b0, b1, how} */
async function NI_mlMeasure(o){o=o||{};const r=NI_mlRange(),t=await NI_mlTracks(r.b0,r.b1,{prog:o.prog});if(t.cancelled)return{cancelled:true};
  const res={tracks:t.tracks,b0:r.b0,b1:r.b1,how:r.how,pairs:null};if(o.noPairs)return res;
  const pr=NI.mono.song?NI_jourRange():r,pl=pr===r?t.tracks:(await NI_mlTracks(pr.b0,pr.b1)).tracks||[];if(o.step)o.step(res);
  const P=await NI_mlPairs(pl,pr.b0,pr.b1,o.isOk);if(!P)return{cancelled:true};res.pairs=P;NI.mono.pairRuns++;return res}
function NI_mlOpen(){const M=NI.mono,z=ZOOM,vw=innerWidth/z,vh=innerHeight/z;
  const w=fwin('niMono','Mono loss',{x:Math.round(vw*.18),y:Math.round(vh*.16),w:Math.round(Math.min(640,vw*.5)),h:Math.round(Math.min(460,vh*.66))},()=>NI_mlClose(true));
  if(!M.w||M.w!==w){M.w=w;w.querySelector('.fwt').title='How much level each track loses when the mix is heard in mono, band by band';{const c=w.querySelector('.fwc');if(c)c.title='Close the mono-loss map'}
    w.querySelector('.fwb').innerHTML=`<div class="nmt"><button data-nm="mono" title="Hear the mix in mono, as on a phone or a club system (the Mono switch of the master strip). Does not change the export.">Hear in mono</button>
      <label title="Measure the whole song instead of the loop or the 8 bars around the playhead. Tracks that cancel each other are still checked around the playhead."><input type="checkbox" data-nm="song"> Whole song</label>
      <button data-nm="again" title="Measure again">Measure again</button><span class="nmst" aria-live="polite"></span></div>
      <div class="nmk" title="The colour of each band: how much of that track's level is lost in mono there"><i style="--k:${NI_mlCol(0).join(',')}"></i>holds<i style="--k:${NI_mlCol(3).join(',')}"></i>−3 dB, wide or one-sided<i style="--k:${NI_mlCol(6).join(',')}"></i>−6 dB, partly cancels<i style="--k:${NI_mlCol(12).join(',')}"></i>−12 dB and more, cancels<span>faint: a quiet band of that track</span></div>
      <div class="nmg"></div><div class="nmp"></div>
      <div class="nmnote">From each track on its own, offline: its clips, devices, fader and pan (the master chain is in the per-band numbers). Nothing is added to what you hear.</div>`;
    w.querySelector('[data-nm="song"]').onchange=e=>{M.song=e.target.checked;NI_mlRun()};w.querySelector('[data-nm="again"]').onclick=()=>NI_mlRun();
    w.querySelector('[data-nm="mono"]').onclick=()=>NI_mlMonoSw();
    w.querySelector('.nmg').addEventListener('click',e=>{const r=e.target.closest('[data-nmt]');if(r&&trkById(r.dataset.nmt))selectTrack(r.dataset.nmt)})}
  w.querySelector('[data-nm="song"]').checked=M.song;NI_mlMonoPaint();clearInterval(M.tm);M.tm=setInterval(NI_mlTick,300);NI_mlRun();return w}
function NI_mlClose(fromWin){const M=NI.mono;clearInterval(M.tm);M.tm=0;M.tok++;M.busy=false;if(!fromWin&&M.w)M.w.hidden=true}
/* the Mono switch of the master strip, from here */
function NI_mlMonoSw(){if(UI.bitPerfect)return;UI.monoChk=!UI.monoChk;if(UI.monoChk)UI.swapChk=false;saveUI();ensureCtx();monSet();try{monPaint()}catch(e){}try{syncSettings()}catch(e){}NI_mlMonoPaint()}
function NI_mlMonoPaint(){const b=NI.mono.w&&NI.mono.w.querySelector('[data-nm="mono"]');if(!b)return;b.classList.toggle('on',!!UI.monoChk);b.disabled=!!UI.bitPerfect;if(UI.bitPerfect)b.title='Off while bit-perfect output is on (Settings › Audio)'}
function NI_mlKey(){const r=NI_mlRange();return r.b0+'|'+r.b1+'|'+NI.mono.song+'|'+NI_sig()}
function NI_mlTick(){const M=NI.mono,w=M.w;if(!w||w.hidden){clearInterval(M.tm);M.tm=0;return}NI_mlMonoPaint();if(play.on||M.busy)return;const k=NI_mlKey();if(k===M.key){M.pend=null;return}
  if(!M.pend||M.pend.k!==k)M.pend={k,t:performance.now()};else if(performance.now()-M.pend.t>800){M.pend=null;NI_mlRun()}}
async function NI_mlRun(){const M=NI.mono,w=M.w;if(!w||w.hidden)return;const tok=++M.tok,st=w.querySelector('.nmst'),ok=()=>tok===M.tok&&!w.hidden;M.key=NI_mlKey();M.busy=true;M.runs++;st.textContent='Measuring…';
  try{const res=await NI_mlMeasure({prog:(d,n)=>{if(ok())st.textContent=`Analysing ${d} of ${n} pieces…`},step:r=>{if(!ok())return;M.res=r;NI_mlShow(r);st.textContent='Checking which tracks cancel each other…'},isOk:ok});
    if(!ok())return;if(res.cancelled){st.textContent='Stopped: the song changed.';return}M.res=res;NI_mlShow(res);const a=NI_bb(res.b0),b=NI_bb(res.b1);st.textContent=res.how==='the whole song'?'the whole song':`bars ${a.bar} to ${b.bar-1} (${res.how})`;st.title='The range measured'}
  catch(e){if(!ok())return;console.warn('NI mono loss',e);st.textContent='Could not measure: '+(e&&e.message||e)}finally{if(tok===M.tok)M.busy=false}}
function NI_mlWords(x){if(x.worst&&x.worst.loss>=3.5)return{t:`${NI_mlDb(-x.worst.loss)} at ${NI_mlRangeTxt(x.worst.fa,x.worst.fb)}`,c:x.worst.loss>=6?'bad':'warn'};
  if(x.tot>=2)return{t:'wide, nothing cancels',c:''};return{t:'holds up in mono',c:'ok'}}
function NI_mlShow(res){const w=NI.mono.w,g=w.querySelector('.nmg'),pp=w.querySelector('.nmp'),bands=NI.an.bands,X=f=>clamp(Math.log2(f/20)/Math.log2(1000),0,1)*100;
  if(!res.tracks.length){g.innerHTML='<div class="nmempty">No track plays in this range.</div>';pp.innerHTML='';return}
  let h=`<span></span><span class="nmh" title="The track">Track</span><div class="nmsc" title="Frequency, 20 Hz to 20 kHz">${[50,100,200,500,1000,2000,5000,10000].map(f=>`<span style="left:${X(f)}%">${f>=1000?f/1000+'k':f}</span>`).join('')}</div><span class="nmh r" title="The track's whole level in mono, against stereo">Mono</span><span class="nmh" title="Where it loses most">Where</span>`;
  const step=100/bands.length;
  for(const x of res.tracks){const stops=[];for(let i=0;i<bands.length;i++){const c=NI_mlCol(x.loss[i]),a=(x.sig[i]*.95).toFixed(2),p0=(X(bands[i]*Math.pow(2,-1/12))).toFixed(2),p1=(X(bands[i]*Math.pow(2,1/12))).toFixed(2);stops.push(`rgba(${c},${a}) ${p0}%`,`rgba(${c},${a}) ${p1}%`)}
    const W=NI_mlWords(x),tip=`${x.name}: ${W.t}. In mono the whole track is ${NI_mlDb(-x.tot)} against stereo.`;
    h+=`<i class="nmj" data-nmj="${esc(x.id)}"></i><div class="nmnm" data-nmt="${esc(x.id)}" style="--c:${esc(x.color)}" title="${esc(x.name)}: click to select the track"><i></i>${esc(x.name)}</div>`;
    h+=`<div class="nmb" data-nmt="${esc(x.id)}" title="${esc(tip)}" style="background-image:linear-gradient(90deg,${stops.join(',')})"></div>`;
    h+=`<span class="nmn${x.tot>=6?' bad':x.tot>=3.5?' warn':''}" title="The whole track in mono against stereo (power over its bands)">${NI_mlDb(-x.tot)}</span><span class="nmw ${W.c}" title="${esc(tip)}">${esc(W.t)}</span>`}
  g.innerHTML=h;
  /* the lines between tracks that cancel each other */
  const P=res.pairs;let ph='';
  if(!P)ph='<div class="nmpn">Checking which tracks cancel each other…</div>';
  else{const a=NI_bb(P.b0),b=NI_bb(P.b1),rng=`bars ${a.bar} to ${b.bar-1}`;
    if(!P.pairs.length)ph=`<div class="nmpn" title="The ${P.n} loudest tracks compared pair by pair, ${rng}">No tracks cancel each other in mono (${P.n} loudest tracks compared, ${rng}).</div>`;
    else{ph=`<div class="nmpn" title="The ${P.n} loudest tracks compared pair by pair, ${rng}">Tracks that cancel each other in mono (${rng}):</div>`;
      for(const q of P.pairs){const full=q.mono<=-30,s=`${q.a.name} and ${q.b.name} cancel at ${NI_mlRangeTxt(q.fa,q.fb)}: ${full?'they cancel out':NI_mlDb(q.mono)+' together'} in mono`+(q.stereo<=-3?', in stereo too ('+NI_mlDb(q.stereo)+')':', fine in stereo');
        ph+=`<div class="nmpr" data-a="${esc(q.a.id)}" data-b="${esc(q.b.id)}" title="${esc(s+'. Often one of them has its polarity flipped or is a copy delayed by a few milliseconds. Click to select '+q.a.name)}">${esc(s)}</div>`}}}
  pp.innerHTML=ph;pp.querySelectorAll('.nmpr').forEach(e=>e.onclick=()=>{if(trkById(e.dataset.a))selectTrack(e.dataset.a)});
  g.querySelectorAll('.nmline').forEach(e=>e.remove());if(P&&P.pairs.length){const rows=new Map();g.querySelectorAll('.nmj').forEach(e=>rows.set(e.dataset.nmj,e));const used=[];
    P.pairs.forEach((q,i)=>{const ea=rows.get(q.a.id),eb=rows.get(q.b.id);if(!ea||!eb)return;const y0=ea.offsetTop+ea.offsetHeight/2,y1=eb.offsetTop+eb.offsetHeight/2,top=Math.min(y0,y1),bot=Math.max(y0,y1);
      let lane=0;while(used.some(u=>u.l===lane&&u.t<bot&&u.b>top))lane++;used.push({l:lane,t:top,b:bot});const d=document.createElement('div');d.className='nmline'+(q.mono<=-6?' bad':'');
      d.style.cssText=`top:${top}px;height:${Math.max(2,bot-top)}px;left:${2+lane*4}px`;d.title=`${q.a.name} and ${q.b.name} cancel each other in mono at ${NI_mlRangeTxt(q.fa,q.fb)}`;g.appendChild(d)})}}
/* a small button next to Mono on the master strip (the mixer's render calls this hook) */
function NI_mlMxBtn(w){const m=w&&w.querySelector('.mx.master .mxmon');if(!m||m.querySelector('[data-niml]'))return;const b=document.createElement('button');b.dataset.niml='1';b.textContent='Loss';
  b.title='Mono loss map: which track loses level in mono, band by band, and which tracks cancel each other';b.onclick=e=>{e.stopPropagation();NI_mlOpen()};m.appendChild(b)}
NI.mono.open=NI_mlOpen;NI.mono.close=()=>NI_mlClose(false);NI.mono.measure=NI_mlMeasure;NI.mono.tracks=NI_mlTracks;NI.mono.pairsOf=NI_mlPairs;
NI_HOOKS.mxMon=NI_mlMxBtn;NI_HOOKS.monoLoss={open:NI_mlOpen,measure:o=>NI_mlMeasure(o),tracks:(b0,b1)=>NI_mlTracks(b0,b1)};
/* ===== end of lane D NI-8 ===== */
