"""Task NI-1a (lane D): I3 "Why is this clipping?", part 1: the engine.
Edit script with unique asserted anchors, so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_1a.py [index.html]
Adds:
  - the lane D block (NI, NI_HOOKS) before `function askChoice(title,text,btns,icon){`
  - a clip event log fed from the readings the meters already make (master in meters(), each strip in trackMeters()):
    one call, only when a reading is over 0 dB while the song plays; nothing is added to the audio path
  - NI_clipExplain(t,o): offline render of the moment (the mix, then each track alone), the master's peak sample,
    each track's signed contribution at that sample, the overshoot, the inter-sample peak (4x oversampling); cached
"""
import sys, re
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane D (task NI-1a)'
if MARK in s:
    print('NI-1a already applied'); sys.exit(0)

def put(s, anchor, new, before=True):
    n = s.count(anchor)
    assert n == 1, (anchor[:60], n)
    return s.replace(anchor, new + anchor if before else anchor + new)

# 1. master clip events: right after the master meter decides it is over 0 dB
A1 = "if(pk>0){MT2.over=Math.max(MT2.over,pk);$('#peakBox').classList.add('clip')}"
s = put(s, A1, "if(pk>-6&&typeof NI_clipSeen==='function')NI_clipSeen('master',pk);", before=False)

# 2. strip clip events: each track's reading in trackMeters()
A2 = "const db=pk>1e-6?20*Math.log10(pk):-90,key=id+ci,v=db;"
s = put(s, A2, "if(db>0&&typeof NI_clipSeen==='function')NI_clipSeen(id,db);", before=False)

# 3. the engine
JS = r"""/* ===== lane D (task NI-1a): the picked ideas (docs/ideas-build.md). I3 "Why is this clipping?", part 1: the engine =====
   Clip events come from the readings the meters already make: nothing is added to the audio path. An explanation renders the moment
   offline (the mix, then each track alone, through renderMixChunked) and finds which tracks made the peak. Nothing runs in the audio thread. */
const NI=window.NI=window.NI||{},NI_HOOKS=window.NI_HOOKS=window.NI_HOOKS||{};
NI.clips={log:[],n:0,last:null,cache:new Map(),max:200};
/* called by meters() (master, readings above -6 dB) and trackMeters() (strips, readings over 0 dB): one entry per over, repeats within 1.5 s and 2 beats merge.
   lim: the safety limiter was in the path (the level going in is read back from its curve); sat: the limiter was at its ceiling, db is then a lower bound */
/* the master meter reads after the safety limiter, a soft curve up to its ceiling whose table spans twice the input range (limSet: x from -2 to 2 for input -1 to 1).
   The level going into it (the same level an offline render of the mix has) is read back through the inverse of the curve. Near the ceiling the curve is flat,
   so there only a lower bound is known (sat): the limiter is squashing peaks there, and the offline explanation measures them exactly. */
function NI_preLim(db){if(UI.limiter===false||UI.bitPerfect)return{db,lim:false};const c=Math.pow(10,(UI.ceil??-1)/20),k=.82*c,y=Math.pow(10,db/20);if(y<=k)return{db:NI_db(y/2),lim:true};const r=(y-k)/(c-k);
  if(r>=.9995)return{db:NI_db((k+(c-k)*Math.atanh(.9995))/2),lim:true,sat:true};return{db:NI_db((k+(c-k)*Math.atanh(r))/2),lim:true}}
function NI_clipSeen(src,db){if(!play.on)return;let lim=false,sat=false;if(src==='master'){const q=NI_preLim(db);db=q.db;lim=q.lim;sat=!!q.sat}if(!(db>0)&&!sat)return;const C=NI.clips,b=curDisp(),now=performance.now(),pj=PJ&&PJ.cur;
  for(let i=C.log.length-1;i>=0&&i>=C.log.length-12;i--){const e=C.log[i];if(e.src===src&&e.proj===pj&&now-e.w<1500&&Math.abs(b-e.lb)<2){if(db>e.db||(sat&&!e.sat)){e.db=db;e.t=b;e.sat=sat}e.lb=b;e.w=now;return}}
  const e={id:++C.n,src,t:b,lb:b,db,lim,sat,w:now,at:Date.now(),proj:pj};C.log.push(e);if(C.log.length>C.max)C.log.shift();C.last=e;
  if(NI_HOOKS.clipEvent)try{NI_HOOKS.clipEvent(e)}catch(_){}}
/* the open project's clip events, oldest first */
function NI_clipLog(){const pj=PJ&&PJ.cur;return NI.clips.log.filter(e=>e.proj===pj)}
function NI_clipClear(){const pj=PJ&&PJ.cur;NI.clips.log=NI.clips.log.filter(e=>e.proj!==pj);NI.clips.last=null}
function NI_hash(s){let h=2166136261>>>0;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return(h>>>0).toString(36)+'.'+s.length.toString(36)}
const NI_sig=()=>(PJ&&PJ.cur)+'|'+((curP()||{}).chg|0)+'|'+UNDO.length;
/* bar and beat for a song position, 1-based, with the time signature (a peak a sample or two before a beat, as resampling can put it, counts as that beat: 2/1000 beat) */
function NI_bb(b){const P=barPos(Math.max(0,b)+2e-3),d=(P.sig&&P.sig.d)||4,bt=Math.floor(P.inBar*d/4+1e-6)+1;return{bar:P.bar+1,beat:bt,txt:'bar '+(P.bar+1)+', beat '+bt}}
/* 4x oversampling (windowed sinc, 16 zero crossings each side, Blackman window) for the inter-sample peak */
const NI_OS4=(()=>{const L=4,Z=16,N=L*Z,h=new Float32Array(2*N+1);for(let n=-N;n<=N;n++){const x=n/L,sn=n===0?1:Math.sin(Math.PI*x)/(Math.PI*x),w=.42+.5*Math.cos(Math.PI*n/N)+.08*Math.cos(2*Math.PI*n/N);h[n+N]=sn*w}return{L,N,h}})();
function NI_truePeak(a,i0,i1){const{L,N,h}=NI_OS4;i0=Math.max(0,i0|0);i1=Math.min(a.length,i1|0);let m=0;
  for(let n=i0;n<i1;n++){const v0=Math.abs(a[n]);if(v0>m)m=v0;for(let p=1;p<L;p++){const q=n*L+p;let y=0;const k0=Math.max(0,Math.ceil((q-N)/L)),k1=Math.min(a.length-1,Math.floor((q+N)/L));for(let k=k0;k<=k1;k++)y+=a[k]*h[q-k*L+N];const v=Math.abs(y);if(v>m)m=v}}return m}
const NI_db=v=>v>1e-9?20*Math.log10(v):-180;
/* the cache key leaves out the work timer (S.work counts minutes, it is not the sound)
   Why is this clipping? t: song position in beats (or a clip event; nothing: the last event). o: {src, sr, half (seconds searched each side), db}.
   Returns {clip, where, t, ch, peak, peakDb, overDb, tpDb, tracks:[{id,name,color,v,share,pkDb}], rest:{v,share}, words, ...};
   share is the signed part of the master's peak sample (cancelling tracks are negative), rest is what sends, groups and master effects add. */
async function NI_clipExplain(t,o){o=Object.assign({},o||{});if(t&&typeof t==='object'){o=Object.assign({src:t.src,db:t.db},o);t=t.t}
  if(t==null){const e=NI.clips.last;if(!e)return null;t=e.t;if(!o.src)o.src=e.src;if(o.db==null)o.db=e.db}
  if(EXR)return{busy:true,why:'An export is running. Try again when it is done.'};
  if(!songEnd())return{empty:true,why:'The song is empty.'};
  const sr=o.sr||(ctx&&ctx.sampleRate)||48000,half=o.half||.25,bp=half*bpmAt(Math.max(0,t))/60,b0=Math.max(0,t-bp),b1=Math.max(b0+.01,t+bp),src=o.src||'master';
  if(S.seed==null)S.seed=(Math.random()*1e9)|0;const key=NI_hash(JSON.stringify(S,function(k,v){return this===S&&k==='work'?undefined:v}))+'|'+sr+'|'+b0.toFixed(5)+'|'+b1.toFixed(5)+'|'+src+'|'+(UI.headroom??-6)+'|'+(UI.bitPerfect?1:0),C=NI.clips;
  if(C.cache.has(key))return C.cache.get(key);
  const sig=NI_sig(),T0=performance.now(),stale={stale:true,why:'The song changed while it was measured. Try again.'};
  try{
    const mix=await renderMixChunked(sr,b0,b1,0,false,null,null,false);if(NI_sig()!==sig)return stale;
    const ML=mix.getChannelData(0),MR=mix.getChannelData(1),n=ML.length;let pi=0,pc=0,pv=0;
    for(let i=0;i<n;i++){const a=Math.abs(ML[i]),b=Math.abs(MR[i]);if(a>pv){pv=a;pi=i;pc=0}if(b>pv){pv=b;pi=i;pc=1}}
    const M=pc?MR:ML,m=M[pi],w50=Math.round(.05*sr),Z=NI_OS4.N/NI_OS4.L,i0=Math.max(Math.min(Z,n>>1),pi-w50),i1=Math.min(Math.max(n-Z,(n>>1)+1),pi+w50+1);/* the inter-sample peak keeps 16 samples away from the ends of the render (no ringing from the cut) */
    const tp=Math.max(NI_truePeak(ML,i0,i1),NI_truePeak(MR,i0,i1)),pkBeat=beatOf(secOf(b0)+pi/sr);
    const solo=S.tracks.some(x=>x.solo),list=S.tracks.filter(x=>x.kind!=='return'&&x.kind!=='group'&&trkAudible(x,solo)&&x.clips.some(c=>!c.mute&&c.start<b1&&c.start+c.len>b0-64));
    const rows=[];let k=0;
    const one=async()=>{while(k<list.length){const x=list[k++],tb=await renderMixChunked(sr,b0,b1,0,false,x.id,null,false);if(NI_sig()!==sig)throw stale;
      const A=tb.getChannelData(pc),v=A[pi]||0;let lp=0;for(let ch=0;ch<2;ch++){const B=tb.getChannelData(ch);for(let i=i0;i<i1&&i<B.length;i++){const q=Math.abs(B[i]);if(q>lp)lp=q}}
      let wp=0;if(x.id===src)for(let ch=0;ch<2;ch++){const B=tb.getChannelData(ch);for(let i=0;i<B.length;i++){const q=Math.abs(B[i]);if(q>wp)wp=q}}
      rows.push({id:x.id,name:x.name,color:x.color,v,share:m?v/m:0,pkDb:NI_db(lp),_wp:wp})}};
    await Promise.all([one(),one()]);
    rows.sort((a,b)=>S.tracks.indexOf(trkById(a.id))-S.tracks.indexOf(trkById(b.id)));rows.sort((a,b)=>b.share-a.share);
    const sum=rows.reduce((a,r)=>a+r.v,0),rest=m-sum,mg=masterGain(),fxOn=(S.mfx||[]).some(f=>f.on);
    const peakDb=NI_db(pv),r={clip:peakDb>0,t:pkBeat,where:NI_bb(pkBeat),ch:pc?'right':'left',peak:pv,peakDb,overDb:Math.max(0,peakDb),tpDb:NI_db(tp),
      tracks:rows.map(({_wp,...q})=>q),rest:{v:rest,share:m?rest/m:0},sum,src,sr,b0,b1,i:pi,eventDb:o.db,masterFx:fxOn,ms:Math.round(performance.now()-T0)};
    if(src!=='master'){const x=trkById(src),q=rows.find(z=>z.id===src);r.strip=x?{id:x.id,name:x.name,pkDb:q&&mg>0?NI_db(q._wp/mg):null,approx:fxOn,
      clips:x.clips.filter(c=>!c.mute&&c.start<=pkBeat&&c.start+c.len>pkBeat).map(c=>c.name||'clip'),why:q?'':'This track is not heard on its own here (a return, a group or muted).'}:null}
    r.words=NI_clipWords(r);
    C.cache.set(key,r);if(C.cache.size>40)C.cache.delete(C.cache.keys().next().value);return r
  }catch(e){if(e===stale)return stale;if(e&&e.message==='cancelled')return{stale:true,why:'Cancelled.'};console.warn('NI_clipExplain',e);return{error:String(e&&e.message||e)}}}
/* the chain in words: "Kick + Bass add up here: +2.1 dB over 0 dBFS" */
function NI_clipWords(r){if(!r||r.peakDb==null)return'';const f=v=>(v>=0?'+':'')+v.toFixed(1)+' dB',top=r.tracks.filter(q=>q.share>=.1).slice(0,4),names=top.map(q=>q.name);
  const head=!r.clip?`No clip here: the peak is ${f(r.peakDb)}`:(names.length>1?`${names.join(' + ')} add up here: ${f(r.peakDb)} over 0 dBFS`:names.length?`${names[0]} goes over here: ${f(r.peakDb)} over 0 dBFS`:`The mix goes over here: ${f(r.peakDb)} over 0 dBFS`);
  const big=top.length?'Biggest share: '+top.map(q=>`${q.name} (${Math.round(q.share*100)}%)`).join(', ')+'.':'';
  const neg=r.tracks.filter(q=>q.share<=-.05).map(q=>`${q.name} (${Math.round(q.share*100)}%)`),rest=Math.abs(r.rest.share)>=.05?` Sends, groups and master effects: ${Math.round(r.rest.share*100)}%.`:'';
  return head+(r.where?' at '+r.where.txt:'')+'. '+big+(neg.length?' Pulling the other way: '+neg.join(', ')+'.':'')+rest+` Inter-sample peak: ${f(r.tpDb)}.`}
NI.clipExplain=NI_clipExplain;NI.clipLog=NI_clipLog;
/* ===== end of lane D NI-1a ===== */
"""
A3 = "function askChoice(title,text,btns,icon){"
s = put(s, A3, JS)
open(P, 'w', encoding='utf-8').write(s)
print('NI-1a applied')
