
/* ===== lane D (task NI-5c): X16 the clash measure that knows the beat (AE3 pick, improves I12 masking cables) =====
   NI-5a finds clash candidates from NI-3's per-beat cache, which averages a whole beat: in a rolling psytrance bass (KBBB) kick and bass
   share 40 to 120 Hz but take turns inside each beat, so the average flags them. Here each candidate is checked in time: both tracks are
   rendered offline on their own over the 8 beats around the playhead (NI-7's one-track render, after fader and pan, 22.05 kHz), split into
   the 1/3-octave bands with a band-pass and followed every 11.6 ms; a pair counts as a clash only for the share of moments when both are
   loud in that band at once. Kept per track and window under NI-3's piece key, so an edit measures again only what it touched. */
NI.cg={mem:new Map(),q:[],busy:false,ready:0,renders:0};
const NI_CG_W=8,NI_CG_SR=22050,NI_CG_HOP=256,NI_CG_TURN=.25;
function NI_cgKey(t,w){const p=Math.floor(w*NI_CG_W/NI_AN_SEG),k=NI_anKey(t,p);return k===''?'':k+'|cg'+w}
/* the band levels of one render: d[f*NB+m] in dB, a frame every 256 samples (11.6 ms), bands of NI-5a (1/3 octave) */
function NI_cgWork(L,R,sr){const NB=NI_CL_NB,H=NI_CG_HOP,n=Math.min(L.length,R.length),nf=Math.floor(n/H),d=new Float32Array(nf*NB).fill(-140),x=new Float32Array(n);
  for(let i=0;i<n;i++)x[i]=(L[i]+R[i])*.5;
  for(let m=0;m<NB;m++){const[fa,fb]=NI_clEdges(m);if(fb>=sr*.45)continue;const fc=Math.sqrt(fa*fb),Q=fc/(fb-fa),w0=2*Math.PI*fc/sr,al=Math.sin(w0)/(2*Q),a0=1+al,b0=al/a0,b2=-al/a0,a1=-2*Math.cos(w0)/a0,a2=(1-al)/a0;
    let x1=0,x2=0,y1=0,y2=0,u1=0,u2=0,v1=0,v2=0;
    for(let f=0;f<nf;f++){let s=0;const e=(f+1)*H;for(let i=f*H;i<e;i++){const xi=x[i],y=b0*xi+b2*x2-a1*y1-a2*y2;x2=x1;x1=xi;y2=y1;y1=y;const v=b0*y+b2*u2-a1*v1-a2*v2;u2=u1;u1=y;v2=v1;v1=v;s+=v*v}
      d[f*NB+m]=10*Math.log10(2*s/H+1e-14)}}
  return{nf,NB,d,sr,hop:H}}
/* the band levels of a track in window w (beats 8w to 8w+8): the result, '' if silent there, or null (queued) */
function NI_cgGet(t,w){const k=NI_cgKey(t,w);if(k==='')return'';const r=NI.cg.mem.get(k);if(r)return r;NI_cgQueue(t,w,k);return null}
function NI_cgQueue(t,w,k){const G=NI.cg;if(!G.q.some(x=>x.k===k))G.q.push({t,w,k,pj:PJ&&PJ.cur});if(!G.busy)NI_cgPump()}
async function NI_cgPump(){const G=NI.cg;if(G.busy)return;G.busy=true;
  try{while(G.q.length){const why=NI_anHold();if(why){await NI_anSleep(800);continue}
      const it=G.q.shift();if(it.pj!==(PJ&&PJ.cur)||!S.tracks.includes(it.t)||G.mem.has(it.k)||NI_cgKey(it.t,it.w)!==it.k)continue;
      let r;try{r=await NI_mlRender(it.t,it.w*NI_CG_W,(it.w+1)*NI_CG_W,NI_CG_SR)}catch(e){console.warn('NI clash timing render',e);continue}
      if(NI_cgKey(it.t,it.w)!==it.k){G.q.push(it);continue}/* the track changed while it rendered */
      G.mem.set(it.k,NI_cgWork(r.L,r.R,r.sr||NI_CG_SR));G.renders++;G.ready++;if(G.mem.size>300)G.mem.delete(G.mem.keys().next().value);
      try{if(NI_clOn()){NI.clash.drawn='';NI_clTick(true)}}catch(e){}
      await NI_anSleep(play.on?600:15)}}
  finally{G.busy=false}}
/* the timing of one clash: how often both are loud in its band at the same moment over the window around the beat */
function NI_cgGate(c,beat){const w=Math.floor(Math.max(0,beat)/NI_CG_W),ea=NI_cgGet(c.a,w),eb=NI_cgGet(c.b,w);c.gate=null;c.turns=false;if(!ea||!eb)return null;
  const NB=NI_CL_NB,n=Math.min(ea.nf,eb.nf),pa=new Float32Array(n),pb=new Float32Array(n),co=new Uint8Array(n);let ma=-140,mb=-140;
  for(let f=0;f<n;f++){let sa=0,sb=0;for(let m=c.m0;m<=c.m1;m++){sa+=Math.pow(10,ea.d[f*NB+m]/10);sb+=Math.pow(10,eb.d[f*NB+m]/10)}pa[f]=10*Math.log10(sa+1e-14);pb[f]=10*Math.log10(sb+1e-14);if(pa[f]>ma)ma=pa[f];if(pb[f]>mb)mb=pb[f]}
  /* loud: within 10 dB of its own top in this window; a clash moment: both loud and within 12 dB of each other */
  let both=0,either=0;for(let f=0;f<n;f++){const A=pa[f]>=ma-10&&pa[f]>-100,B=pb[f]>=mb-10&&pb[f]>-100;if(A||B)either++;if(A&&B&&Math.abs(pa[f]-pb[f])<=NI_CL_GAP){both++;co[f]=1}}
  const share=either?both/either:0;c.gate={share,w,b0:w*NI_CG_W,b1:(w+1)*NI_CG_W,pa,pb,co,ma,mb,hop:ea.hop,sr:ea.sr};c.turns=share<NI_CG_TURN;return c.gate}
{const _at=NI_clashAt;NI_clashAt=function(beat){const R=_at.apply(this,arguments);for(const c of R.list)NI_cgGate(c,R.beat);
  R.list.sort((p,q)=>(p.turns-q.turns)||(q.s*(q.gate?q.gate.share:1)-p.s*(p.gate?p.gate.share:1)));R.timing=R.list.some(c=>!c.gate);return R};NI.clash.at=NI_clashAt}
const NI_cgPct=v=>Math.round(v*100)+'%';
{const _w=NI_clWords;NI_clWords=function(c){const g=c.gate;if(!g)return _w(c)+' (When each one plays inside the beat is still being measured.)';const a=NI_bb(g.b0),b=NI_bb(g.b1);
  if(c.turns)return`${c.a.name} and ${c.b.name} both use ${c.range}, but they take turns: both are loud there at the same moment only ${NI_cgPct(g.share)} of the time (bars ${a.bar} to ${b.bar-1}), so this is not a real clash. An estimate.`;
  return _w(c)+` Both are loud there at the same moment ${NI_cgPct(g.share)} of the time (bars ${a.bar} to ${b.bar-1}). An estimate.`}}
/* the pair view in the clash card: both tracks in the clash's band over the window, the moments they are loud together shaded */
function NI_cgDraw(cv,c){const g=c.gate,dpr=Math.min(2,(window.devicePixelRatio||1)*(typeof ZOOM==='number'?ZOOM:1)),W=cv.clientWidth||296,H=cv.clientHeight||64,L=lkT();
  cv.width=Math.round(W*dpr);cv.height=Math.round(H*dpr);const x=cv.getContext('2d');x.setTransform(dpr,0,0,dpr,0,0);x.fillStyle='#05070b';x.fillRect(0,0,W,H);if(!g)return;
  const n=g.pa.length,top=Math.max(g.ma,g.mb)+4,lo=top-40,X=f=>f/Math.max(1,n-1)*W,Y=v=>H-2-clamp((v-lo)/40,0,1)*(H-4);
  x.fillStyle='rgba(232,107,255,.28)';for(let f=0;f<n;f++)if(g.co[f])x.fillRect(X(f),0,Math.max(1,W/n+.5),H);
  /* beats (and the bar line) from the song's tempo */
  for(let i=0;i<=NI_CG_W;i++){const fx=secSpan(g.b0,g.b0+i)*g.sr/g.hop,xx=Math.round(X(fx))+.5,bar=barPos(g.b0+i+1e-6).inBar<1e-3;x.strokeStyle=bar?L.gMaj:L.gMid;x.lineWidth=L.hair(dpr);x.beginPath();x.moveTo(xx,0);x.lineTo(xx,H);x.stroke()}
  const line=(p,col)=>{x.strokeStyle=col;x.lineWidth=1.25;x.beginPath();for(let f=0;f<n;f++){const yy=Y(p[f]);if(f)x.lineTo(X(f),yy);else x.moveTo(X(f),yy)}x.stroke()};
  line(g.pa,c.a.color||'#cfd3db');line(g.pb,c.b.color||'#9aa3b5')}
{const _p=NI_HOOKS.clashPop;NI_HOOKS.clashPop=function(c,p){const g=c.gate,box=document.createElement('div');box.className='nicgv';
  if(g){const a=NI_bb(g.b0),b=NI_bb(g.b1);box.innerHTML=`<canvas title="${esc(c.a.name)} and ${esc(c.b.name)} in ${esc(c.range)} over bars ${a.bar} to ${b.bar-1}, beat by beat. Shaded: the moments both are loud there at once."></canvas>
      <div class="nicgt${c.turns?' tn':''}" title="The share of the moments either one is loud in this band when both are loud at once (within 12 dB of each other). Under ${NI_cgPct(NI_CG_TURN)} they take turns. An estimate from the song, every 11.6 ms.">Loud together <b>${NI_cgPct(g.share)}</b> of the time${c.turns?': they take turns':''}</div>`}
  else box.innerHTML=`<div class="nicgt" title="Each track is rendered on its own over these bars in the background">When each one plays inside the beat: still measuring…</div>`;
  const first=p.querySelector('.nicpr');p.insertBefore(box,first||p.querySelector('.nicpb'));if(c.turns){const h=p.querySelector('p');if(h)h.textContent=`Both use this band, but they take turns inside the beat, so the quieter one is not covered for long.`}
  const cv=box.querySelector('canvas');if(cv)NI_cgDraw(cv,c);const r=_p?_p(c,p):undefined;
  /* they take turns: nothing to fix in this band; the kick and bass lab for the low end */
  if(c.turns){const f=p.querySelector('.nicpf');if(f){f.innerHTML=`<p>Nothing to fix here: they already take turns.${c.mk<=6?' If the low end still sounds muddy, the kick and bass lab shows the tuning and the gaps.':''}</p>`+(c.mk<=6&&typeof NI_kbOpen==='function'?`<button type="button" data-ncg="kb" title="Open the kick and bass lab: the kick's pitch, the bass notes and the gaps between them">Open the kick and bass lab<small>Tuning, beating and the gap after each kick</small></button>`:'');
    const b=f.querySelector('[data-ncg]');if(b)b.onclick=e=>{e.stopPropagation();NI_clPopClose();NI_kbOpen()}}}
  return r}}
NI.cg.get=NI_cgGet;NI.cg.gate=NI_cgGate;NI.cg.work=NI_cgWork;NI_HOOKS.clashTiming={gate:(c,beat)=>NI_cgGate(c,beat),get:NI_cgGet};
/* ===== end of lane D NI-5c ===== */
