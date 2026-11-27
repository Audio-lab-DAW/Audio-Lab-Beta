"""Task NI-3 (lane D): I1 frequency map, part 1: the analysis worker and the per-beat band cache (NF3).
Edit script with unique asserted anchors, so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_3.py [index.html]
Adds (no UI; the map view is NI-4):
  - NI_anWork: the analysis of one piece (a worker; the same function runs on the page if a worker cannot start):
    per beat, 61 bands of 1/6 octave (20 Hz to 20.5 kHz) for mid and for side, loudness (BS.1770 K-weighting, LUFS of the beat),
    spectral centroid, "is playing", the five strongest peaks (Hz and dB)
  - NI.an: pieces of 24 beats per track, rendered offline one at a time (renderMixChunked with only), keyed by a hash of what the
    piece's sound depends on (the track without its name and colour, the clips that reach the piece, tempo map, master chain), kept in
    memory and in IndexedDB ('audiolab-ni', capped), pieces with no clip skipped without a render, paused while an export runs and
    while the song plays unless the CPU read-out stayed under 45% for 2 s (then one piece every 600 ms at most), cancelled when the project changes
  - API: NI.an.get(track, beat) (sync, null and queued when missing), NI.an.ensure({tracks, b0, b1, prog}) (Promise),
    NI.an.status(), NI.an.cancel(), NI.an.bands (centre frequencies); NI_HOOKS.analysis = NI.an
"""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane D (task NI-3)'
if MARK in s:
    print('NI-3 already applied'); sys.exit(0)
assert 'NI_HOOKS.kickBass=NI_kickBass' in s, 'NI-2a must be in the file first'

def put(s, anchor, new, before=True):
    n = s.count(anchor)
    assert n == 1, (anchor[:60], n)
    return s.replace(anchor, new + anchor if before else anchor + new)

JS = r"""/* ===== lane D (task NI-3): I1 frequency map, part 1: the analysis worker and the per-beat band cache =====
   Each track is rendered offline on its own in pieces of 24 beats (never in the audio thread), one piece at a time, and a worker turns a piece
   into per-beat numbers: 61 bands of 1/6 octave for mid and side, loudness, centroid, playing, five peaks. Kept in memory and in IndexedDB under
   a hash of what the piece's sound depends on, so an edit re-analyses only the pieces it touches. Nothing runs until a view asks (NI-4 and on). */
const NI_AN_V=1,NI_AN_SEG=24,NI_AN_SR=44100,NI_AN_NB=61,NI_AN_N=8192;
/* the analysis of one piece. d: {L, R (Float32Array), sr, edges (sample index of each beat start, and the end), N}. Pure: runs in the worker. */
function NI_anWork(d){const L=d.L,R=d.R,sr=d.sr,N=d.N,ed=d.edges,nb=ed.length-1,NB=61,H=N>>1,hop=N>>1;
  const win=new Float32Array(N);let w2=0;for(let i=0;i<N;i++){win[i]=.5-.5*Math.cos(2*Math.PI*i/N);w2+=win[i]*win[i]}
  const lv=Math.log2(N),rev=new Uint32Array(N);for(let i=0;i<N;i++){let r=0,x=i;for(let b=0;b<lv;b++){r=(r<<1)|(x&1);x>>=1}rev[i]=r}
  const cs=new Float64Array(H),sn=new Float64Array(H);for(let i=0;i<H;i++){cs[i]=Math.cos(2*Math.PI*i/N);sn[i]=-Math.sin(2*Math.PI*i/N)}
  const re=new Float64Array(N),im=new Float64Array(N);
  const fft=()=>{for(let i=0;i<N;i++){const j=rev[i];if(j>i){let t=re[i];re[i]=re[j];re[j]=t;t=im[i];im[i]=im[j];im[j]=t}}
    for(let s=2;s<=N;s<<=1){const h=s>>1,st=N/s;for(let i=0;i<N;i+=s)for(let k=0;k<h;k++){const c=cs[k*st],q=sn[k*st],a=i+k,b=a+h,xr=re[b]*c-im[b]*q,xi=re[b]*q+im[b]*c;re[b]=re[a]-xr;im[b]=im[a]-xi;re[a]+=xr;im[a]+=xi}}};
  /* band edges in bins: centre 20 Hz x 2^(k/6), edges a twelfth of an octave each side */
  const bw=sr/N,lo=new Float64Array(NB),hi=new Float64Array(NB),cen=new Float64Array(NB);for(let k=0;k<NB;k++){cen[k]=20*Math.pow(2,k/6);lo[k]=cen[k]*Math.pow(2,-1/12)/bw;hi[k]=cen[k]*Math.pow(2,1/12)/bw}
  /* K-weighting (BS.1770): a high shelf and a high pass, coefficients for this sample rate */
  const kw=(()=>{const sh=(G,Q,fc)=>{const A=Math.pow(10,G/40),w=2*Math.PI*fc/sr,c=Math.cos(w),al=Math.sin(w)/(2*Q),sA=2*Math.sqrt(A)*al,a0=(A+1)-(A-1)*c+sA;
      return[A*((A+1)+(A-1)*c+sA)/a0,-2*A*((A-1)+(A+1)*c)/a0,A*((A+1)+(A-1)*c-sA)/a0,2*((A-1)-(A+1)*c)/a0,((A+1)-(A-1)*c-sA)/a0]},
    hp=(Q,fc)=>{const w=2*Math.PI*fc/sr,c=Math.cos(w),al=Math.sin(w)/(2*Q),a0=1+al;return[(1+c)/2/a0,-(1+c)/a0,(1+c)/2/a0,-2*c/a0,(1-al)/a0]};
    return[sh(3.99984385397,.7071752369554193,1681.9744509555319),hp(.5003270373253953,38.13547087613982)]})();
  const kst=[[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]];/* per channel: x1 x2 y1 y2 of each stage */
  const kOne=(ch,x)=>{const S=kst[ch];let v=x;for(let s=0;s<2;s++){const c=kw[s],o=s*4,y=c[0]*v+c[1]*S[o]+c[2]*S[o+1]-c[3]*S[o+2]-c[4]*S[o+3];S[o+1]=S[o];S[o]=v;S[o+3]=S[o+2];S[o+2]=y;v=y}return v};
  const qd=v=>{const x=Math.round((v+127)*2);return x<0?0:x>255?255:x};
  const mid=new Uint8Array(nb*NB),side=new Uint8Array(nb*NB),loud=new Float32Array(nb),cent=new Float32Array(nb),play=new Uint8Array(nb),pk=new Float32Array(nb*10),rms=new Float32Array(nb);
  const PM=new Float64Array(H+1),PS=new Float64Array(H+1),nrm=2/(N*w2);
  const band=(P,k)=>{const a=lo[k],b=hi[k],i0=Math.ceil(a),i1=Math.floor(b);if(i1-i0>=1){let s=0;for(let i=i0;i<=i1&&i<=H;i++)s+=P[i];return s}
    const x=cen[k]/bw,i=Math.floor(x),f=x-i,v=i+1<=H?P[i]*(1-f)+P[i+1]*f:0;return v*(b-a)};
  for(let j=0;j<nb;j++){const s0=ed[j],s1=ed[j+1],len=s1-s0;PM.fill(0);PS.fill(0);
    const F=len<N?1:Math.floor((len-N)/hop)+1;
    for(let f=0;f<F;f++){const i0=s0+f*hop;
      for(let i=0;i<N;i++){const k=i0+i,l=k<L.length?L[k]:0,r=k<R.length?R[k]:0;re[i]=(l+r)*.5*win[i];im[i]=(l-r)*.5*win[i]}fft();
      /* two real signals in one transform: mid in re, side in im */
      for(let k=0;k<=H;k++){const k2=(N-k)&(N-1),ar=re[k],ai=im[k],br=re[k2],bi=im[k2],mr=(ar+br)*.5,mi=(ai-bi)*.5,sr_=(ai+bi)*.5,si=(br-ar)*.5;PM[k]+=mr*mr+mi*mi;PS[k]+=sr_*sr_+si*si}}
    for(let k=0;k<=H;k++){PM[k]*=nrm/F;PS[k]*=nrm/F}
    for(let k=0;k<NB;k++){mid[j*NB+k]=qd(10*Math.log10(band(PM,k)+1e-14));side[j*NB+k]=qd(10*Math.log10(band(PS,k)+1e-14))}
    /* centroid of the mid spectrum, 20 Hz to 20 kHz */
    {let a=0,b=0;const k0=Math.ceil(20/bw),k1=Math.min(H,Math.floor(20000/bw));for(let k=k0;k<=k1;k++){a+=k*bw*PM[k];b+=PM[k]}cent[j]=b>1e-14?a/b:0}
    /* loudness of the beat and its level */
    {let sl=0,sr2=0,pl=0;for(let i=s0;i<s1;i++){const l=L[i]||0,r=R[i]||0,a=kOne(0,l),b=kOne(1,r);sl+=a*a;sr2+=b*b;pl+=l*l+r*r}
      const n=Math.max(1,len);loud[j]=-.691+10*Math.log10((sl+sr2)/n+1e-14);rms[j]=10*Math.log10(pl/(2*n)+1e-14);play[j]=rms[j]>-60?1:0}
    /* the five strongest peaks of the mid spectrum (20 Hz to 16 kHz), with the frequency refined by a parabola on the dB values */
    {const k0=Math.max(2,Math.ceil(20/bw)),k1=Math.min(H-2,Math.floor(16000/bw)),c=[];for(let k=k0;k<=k1;k++){const v=PM[k];if(v>PM[k-1]&&v>=PM[k+1]&&v>1e-12)c.push(k)}
      c.sort((a,b)=>PM[b]-PM[a]);for(let q=0;q<5;q++){const k=c[q];if(k==null){pk[j*10+q*2]=0;pk[j*10+q*2+1]=-127;continue}const a=10*Math.log10(PM[k-1]+1e-14),b=10*Math.log10(PM[k]),g=10*Math.log10(PM[k+1]+1e-14),den=a-2*b+g,p=den<0?.5*(a-g)/den:0;
        pk[j*10+q*2]=(k+Math.max(-.5,Math.min(.5,p)))*bw;pk[j*10+q*2+1]=10*Math.log10(PM[k-1]+PM[k]+PM[k+1]+1e-14)}}}
  return{nb,mid,side,loud,cent,play,pk,rms}}
NI.an={mem:new Map(),q:[],busy:false,w:null,wq:new Map(),wid:0,waits:[],keys:{sig:'',m:new Map()},stats:{renders:0,idb:0,skipped:0,mem:0,ms:0},
  db:null,cap:3000,bands:Array.from({length:NI_AN_NB},(_,k)=>20*Math.pow(2,k/6)),paused:'',last:[]};
function NI_anWorker(){const A=NI.an;if(A.w===false)return null;if(A.w)return A.w;
  try{const code='const NI_anWork='+NI_anWork.toString()+';onmessage=e=>{const r=NI_anWork(e.data);postMessage({id:e.data.id,r},[r.mid.buffer,r.side.buffer,r.loud.buffer,r.cent.buffer,r.play.buffer,r.pk.buffer,r.rms.buffer])}';
    A.w=new Worker(URL.createObjectURL(new Blob([code],{type:'text/javascript'})));A.w.onmessage=e=>{const f=A.wq.get(e.data.id);if(f){A.wq.delete(e.data.id);f.res(e.data.r)}};
    A.w.onerror=e=>{console.warn('NI analysis worker',e&&e.message);for(const f of A.wq.values())f.rej(new Error('worker'));A.wq.clear();try{A.w.terminate()}catch(_){}A.w=false}}catch(e){A.w=false}return A.w||null}
function NI_anRun(d){const w=NI_anWorker();if(!w)return new Promise(r=>setTimeout(()=>r(NI_anWork(d)),0));const A=NI.an,id=++A.wid;d.id=id;
  return new Promise((res,rej)=>{A.wq.set(id,{res,rej});w.postMessage(d,[d.L.buffer,d.R.buffer])})}
/* IndexedDB: one store, entries {k, t, r}; capped by count, the oldest go first */
function NI_anDB(){const A=NI.an;if(A.db)return A.db;A.db=new Promise(res=>{try{const r=indexedDB.open('audiolab-ni',1);r.onupgradeneeded=()=>{const d=r.result;if(!d.objectStoreNames.contains('an')){const s=d.createObjectStore('an',{keyPath:'k'});s.createIndex('t','t')}};
  r.onsuccess=()=>res(r.result);r.onerror=()=>res(null);r.onblocked=()=>res(null)}catch(e){res(null)}});return A.db}
async function NI_anDBGet(k){const d=await NI_anDB();if(!d)return null;return new Promise(res=>{try{const q=d.transaction('an').objectStore('an').get(k);q.onsuccess=()=>res(q.result?q.result.r:null);q.onerror=()=>res(null)}catch(e){res(null)}})}
async function NI_anDBPut(k,r){const d=await NI_anDB();if(!d)return;try{const tx=d.transaction('an','readwrite'),st=tx.objectStore('an');st.put({k,t:Date.now(),r});
  if(Math.random()<.05){const c=st.count();c.onsuccess=()=>{let over=c.result-NI.an.cap;if(over<=0)return;const cur=st.index('t').openCursor();cur.onsuccess=()=>{const x=cur.result;if(!x||over--<=0)return;x.delete();x.continue()}}}}catch(e){}}
/* what a piece's sound depends on: the track (without name, colour, mute, solo, selection and ids), the clips that reach the piece (from 24 beats
   before it, for tails and the render's pre-roll), the tempo map, the master chain (the render goes through it), the version of this code */
const NI_AN_TDROP=['id','name','color','col','mute','solo','sel','open','h','fold','arm','mon','clips'],NI_AN_CDROP=['id','name','color','col','sel'];
const NI_anStrip=(o,ks)=>{const x=Object.assign({},o);for(const k of ks)delete x[k];return x};
function NI_anTracks(){return S.tracks.filter(t=>t.kind!=='group'&&t.kind!=='return')}
function NI_anEnd(){let e=0;for(const t of S.tracks)for(const c of t.clips||[])e=Math.max(e,c.start+c.len);return e}
function NI_anKey(t,p){const A=NI.an,sig=NI_sig()+'|'+(PJ&&PJ.cur);if(A.keys.sig!==sig){A.keys.sig=sig;A.keys.m.clear();A.keys.base=null}const mk=t.id+'|'+p;let k=A.keys.m.get(mk);if(k!==undefined)return k;
  const b0=p*NI_AN_SEG,b1=b0+NI_AN_SEG,cl=(t.clips||[]).filter(c=>!c.mute&&c.start<b1&&c.start+c.len>b0-NI_AN_SEG);
  if(!cl.length)k='';/* nothing sounds here: no render */
  else{if(!A.keys.base)A.keys.base=JSON.stringify([NI_AN_V,NI_AN_SR,NI_AN_N,typeof tmapKey==='function'?tmapKey():S.bpm,S.bpm,S.master,(S.mfx||[]).filter(f=>f.on),UI.headroom??-6]);
    const tt=JSON.stringify(NI_anStrip(t,NI_AN_TDROP)),cc=JSON.stringify(cl.map(c=>Object.assign(NI_anStrip(c,NI_AN_CDROP),{start:c.start-b0})));
    k=NI_hash(A.keys.base+'|'+b1+'|'+tt+'|'+cc)+'.'+p}
  A.keys.m.set(mk,k);return k}
/* the numbers of one beat of one track, or null (and the piece is queued). Bands in dB (a full-scale sine reads -3 dB in its band) */
function NI_anGet(tr,beat,o){const t=typeof tr==='object'?tr:trkById(tr);if(!t||beat<0)return null;const p=Math.floor(beat/NI_AN_SEG),k=NI_anKey(t,p),A=NI.an;
  const j=Math.floor(beat)-p*NI_AN_SEG;if(k===''){A.stats.mem++;return{silent:true,play:0,loud:-120,cent:0,mid:null,side:null,peaks:[]}}
  const r=A.mem.get(k);if(!r){if(!(o&&o.noQueue))NI_anQueue([{t,p}]);return null}A.stats.mem++;if(j>=r.nb)return null;
  const B=NI_AN_NB,f=(u,i)=>u[i]/2-127,mid=new Float32Array(B),side=new Float32Array(B);for(let i=0;i<B;i++){mid[i]=f(r.mid,j*B+i);side[i]=f(r.side,j*B+i)}
  const peaks=[];for(let q=0;q<5;q++){const hz=r.pk[j*10+q*2];if(hz>0)peaks.push({hz,db:r.pk[j*10+q*2+1]})}
  return{mid,side,loud:r.loud[j],cent:r.cent[j],play:r.play[j],rms:r.rms[j],peaks}}
function NI_anQueue(L){const A=NI.an,pj=PJ&&PJ.cur;for(const x of L){if(A.q.some(y=>y.t===x.t&&y.p===x.p&&y.pj===pj))continue;A.q.push({t:x.t,p:x.p,pj})}if(!A.busy)NI_anPump()}
const NI_anSleep=ms=>new Promise(r=>setTimeout(r,ms));
/* why it waits now, or '' */
function NI_anHold(){if(typeof EXR!=='undefined'&&EXR)return'an export is running';if(play.on){let m=0;for(let i=0;i<CPU.hist.length;i++)if(CPU.hist[i]>m)m=CPU.hist[i];if(m>.45)return'the song is playing and the CPU is busy'}return''}/* while playing: only when the CPU read-out stayed under 45% for the last 2 s */
async function NI_anPump(){const A=NI.an;if(A.busy)return;A.busy=true;
  try{while(A.q.length){      const why=NI_anHold();A.paused=why;if(why){await NI_anSleep(800);continue}
      const{t,p,pj}=A.q.shift();if(pj!==(PJ&&PJ.cur)||!S.tracks.includes(t)){NI_anDone();continue}/* another project, or the track is gone */const k=NI_anKey(t,p);if(k===''||A.mem.has(k)){NI_anDone();continue}
      let r=await NI_anDBGet(k);if(r){A.stats.idb++;A.mem.set(k,r);NI_anDone();continue}
      const b0=p*NI_AN_SEG,b1=Math.min(b0+NI_AN_SEG,Math.max(b0+1,Math.ceil(NI_anEnd()))),sig=NI_sig(),T0=performance.now();let buf;
      try{buf=await renderMixChunked(NI_AN_SR,b0,b1,0,false,t.id,null,false)}catch(e){if(e&&e.message==='cancelled'){A.q.unshift({t,p,pj});await NI_anSleep(1000);continue}console.warn('NI analysis render',e);NI_anDone();continue}
      if(NI_sig()!==sig&&NI_anKey(t,p)!==k){A.q.push({t,p,pj});continue}/* this track changed while it rendered: again, later */
      const edges=new Int32Array(b1-b0+1);for(let i=0;i<=b1-b0;i++)edges[i]=Math.min(buf.length,Math.round(secSpan(b0,b0+i)*NI_AN_SR));
      r=await NI_anRun({L:buf.getChannelData(0).slice(),R:buf.getChannelData(Math.min(1,buf.numberOfChannels-1)).slice(),sr:NI_AN_SR,edges,N:NI_AN_N});
      A.stats.renders++;A.stats.ms+=performance.now()-T0;A.last.push(t.name+' '+b0);if(A.last.length>64)A.last.shift();A.mem.set(k,r);NI_anDBPut(k,r);NI_anDone();
      if(A.mem.size>4000)A.mem.delete(A.mem.keys().next().value);
      await NI_anSleep(play.on?600:20)}}
  finally{A.busy=false;A.paused='';NI_anDone(true)}}
function NI_anDone(end){const A=NI.an;for(const w of A.waits.slice())w.tick(end)}
/* analyse tracks (default all but groups and returns) over [b0, b1) (default the song); o.prog(done, total). Resolves {done, total, renders, cancelled} */
function NI_anEnsure(o){o=o||{};const A=NI.an,L=(o.tracks?o.tracks.map(x=>typeof x==='object'?x:trkById(x)).filter(Boolean):NI_anTracks()),e=o.b1!=null?o.b1:NI_anEnd(),p0=Math.floor((o.b0||0)/NI_AN_SEG),p1=Math.ceil(e/NI_AN_SEG);
  const jobs=[];for(const t of L)for(let p=p0;p<p1;p++)jobs.push({t,p});const total=jobs.length,r0=A.stats.renders,proj=PJ&&PJ.cur;
  return new Promise(res=>{const w={tick(end){const gone=(PJ&&PJ.cur)!==proj,left=jobs.filter(j=>{if(!gone&&!S.tracks.includes(j.t))return false;const k=NI_anKey(j.t,j.p);return k!==''&&!A.mem.has(k)}).length;if(o.prog)try{o.prog(total-left,total)}catch(_){}
      if(!left||gone||(end&&!A.q.length&&left)){A.waits=A.waits.filter(x=>x!==w);res({done:total-left,total,renders:A.stats.renders-r0,cancelled:gone||(!!left&&!gone)})}}};
    A.waits.push(w);let sk=0;for(const j of jobs)if(NI_anKey(j.t,j.p)==='')sk++;A.stats.skipped+=sk;NI_anQueue(jobs.filter(j=>{const k=NI_anKey(j.t,j.p);return k!==''&&!A.mem.has(k)}));w.tick(!A.busy&&!A.q.length)})}
function NI_anCancel(){const A=NI.an;A.q.length=0;NI_anDone(true)}
NI.an.get=NI_anGet;NI.an.ensure=NI_anEnsure;NI.an.cancel=NI_anCancel;NI.an.key=NI_anKey;
NI.an.status=()=>{const A=NI.an;return{queued:A.q.length,busy:A.busy,paused:A.paused,renders:A.stats.renders,idb:A.stats.idb,skipped:A.stats.skipped,inMemory:A.mem.size,msPerPiece:A.stats.renders?Math.round(A.stats.ms/A.stats.renders):0}};
NI_HOOKS.analysis=NI.an;
/* ===== end of lane D NI-3 ===== */
"""
A = "function askChoice(title,text,btns,icon){"
s = put(s, A, JS)
open(P, 'w', encoding='utf-8').write(s)
print('NI-3 applied')
