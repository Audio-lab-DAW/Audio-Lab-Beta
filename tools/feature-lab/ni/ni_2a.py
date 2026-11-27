"""Task NI-2a (lane D): I2 kick and bass tuning lab, part 1: the analysis (shared with lane C's FT-F18).
Edit script with unique asserted anchors (needs NI-1a in the file), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_2a.py [index.html]
Adds (no UI, no audio nodes, nothing per frame; the view is NI-2b):
  - NI_kickBass(o): finds the kick and the bass tracks (or takes o.kick, o.bass), the bar under the playhead (or o.t),
    the song key (lane C's project key when FT_HOOKS.projectKey exists, else the piano roll's scale and root, S.prKey),
    the kick's pitch curve and the note it settles on:
      * Kick designer instrument and drum machine kick pads (Kick designer pad, kit kicks): read from the parameters
        with the same formula kickRender uses (exact)
      * anything else (audio kick, sampler): that track rendered offline for the bar, YIN on the hit with the most
        tail, reported as a range (wider under 40 Hz, where a short tail cannot be exact)
    the bass notes of the bar (MIDI), each against the kick: interval, beat rate, state (tuned, clash, apart),
    kick hits of the bar with the bass notes they overlap and the gap to the next bass note (for the rolling-bass strip),
    the suggestion "tune the kick to the root" (target note and semitones); cached, thrown away if the song changed
  - NI_HOOKS.kickBass (the analysis, for FT-F18 and NI-2b), NI.kickModel (parameters only, synchronous)
"""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane D (task NI-2a)'
if MARK in s:
    print('NI-2a already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-1a ===== */' in s, 'NI-1a must be in the file first'

def put(s, anchor, new, before=True):
    n = s.count(anchor)
    assert n == 1, (anchor[:60], n)
    return s.replace(anchor, new + anchor if before else anchor + new)

JS = r"""/* ===== lane D (task NI-2a): I2 kick and bass tuning lab, part 1: the analysis (shared with FT-F18 through NI_HOOKS.kickBass) =====
   Reads the kick's pitch from its parameters when it is a Kick designer or a drum machine kick (exact), else renders that one track
   offline for one bar and tracks the pitch of a hit (YIN). Bass notes come from the bass track's MIDI clips. No audio nodes, no
   work per frame, nothing in the audio thread; one offline render of one track for one bar at most, cached. */
NI.kb={cache:new Map()};
const NI_PCN=['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'];
const NI_hz=m=>440*Math.pow(2,(m-69)/12),NI_midi=f=>69+12*Math.log2(f/440);
/* a note with cents: "F♯1 +12 c" (MIDI 60 is C4, as everywhere in AudioLab) */
function NI_noteTxt(m){if(!(m>0))return'';const r=Math.round(m),c=Math.round((m-r)*100);return NI_PCN[((r%12)+12)%12]+(Math.floor(r/12)-1)+(c?' '+(c>0?'+':'')+c+' c':'')}
/* the song key: lane C's project key (FT-F11) when it exists, else the piano roll's scale and root (kept in the project, S.prKey) */
function NI_key(){let k=null,from='piano roll';try{const F=window.FT_HOOKS;if(F&&typeof F.projectKey==='function'){const q=F.projectKey();if(q&&Number.isInteger(q.root)){k=q;from='project key'}}}catch(_){}
  if(!k)k={root:PR.root,scale:PR.scale};const root=((k.root|0)%12+12)%12,sc=SCALES[k.scale]?k.scale:'none',iv=SCALES[sc];
  return{root,scale:sc,from,pcs:iv?iv.map(i=>(i+root)%12):null,name:NI_PCN[root]+(sc==='none'?'':' '+sc)}}
const NI_inKey=(m,K)=>!K.pcs||K.pcs.includes(((Math.round(m)%12)+12)%12);
/* the notes of a track that sound in [b0, b1) in song beats: {p, b, l, v, clip} (muted notes and clips left out) */
function NI_notesIn(t,b0,b1){const out=[];for(const c of t.clips||[]){if(c.mute||!c.notes||c.start>=b1||c.start+c.len<=b0)continue;const off=c.off||0;
  for(const n of c.notes){if(n.m||n.s<off||n.s>=off+c.len)continue;const b=c.start+n.s-off,l=Math.min(n.l,off+c.len-n.s);if(b<b1&&b+l>b0)out.push({p:n.p,b,l,v:n.v,clip:c})}}return out.sort((a,b)=>a.b-b.b||a.p-b.p)}
const NI_allNotes=t=>NI_notesIn(t,-1e9,1e9);
/* kick pads of a drum machine: the pad index of a note (36 to 51) when that pad is a kick or a Kick designer */
const NI_kickPad=(I,p)=>{const P=I&&Array.isArray(I.pads)?I.pads:null,i=p-36;if(!P||i<0||i>15)return-1;const d=P[i];return d&&!d.mute&&(d.type==='kick'||d.type==='kd')?i:-1};
/* how likely a track is the kick or the bass */
function NI_kickScore(t){if(!t||t.kind==='return'||t.kind==='group')return 0;const I=t.inst,pr=I&&I.preset,nm=String(t.name||'');let s=0;
  if(pr==='kick')s+=10;if(pr==='drums'&&NI_allNotes(t).some(n=>NI_kickPad(I,n.p)>=0))s+=6;if(/kick|\bbd\b|bass ?drum/i.test(nm))s+=6;if(!I&&t.clips&&t.clips.some(c=>!c.notes))s+=s?1:0;return s}
function NI_bassScore(t){if(!t||t.kind==='return'||t.kind==='group')return 0;const I=t.inst,pr=I&&I.preset,nm=String(t.name||'');if(!I||pr==='kick'||pr==='drums'||/kick|drum/i.test(nm))return 0;
  const N=NI_allNotes(t);if(!N.length)return 0;let s=0;if(/bass|sub\b|808/i.test(nm))s+=6;const P=typeof PRESETS==='object'&&PRESETS[pr];if(P&&P.cat==='Bass')s+=4;
  const avg=N.reduce((a,n)=>a+n.p,0)/N.length;if(avg<52)s+=3;else if(avg<60)s+=1;return s}
function NI_pick(fn,skip){let best=null,bs=0;for(const t of S.tracks){if(t.id===skip)continue;const v=fn(t);if(v>bs){bs=v;best=t}}return best}
/* the Kick designer's pitch curve and level, the same formula as kickRender (tr: semitones of key tracking) */
function NI_kdCurve(I,tr,label){tr=tr||0;const fE=NI_hz(I.tune+tr),fS=Math.max(fE*1.02,I.start*Math.pow(2,tr/12)),lE=Math.log(fE),lS=Math.log(fS),cp=1+I.bend/100*5,
  hold=I.len*(.04+.22*I.tail/100),tp=2.8-2.4*I.tail/100,curve=[],dt=.002;
  for(let t=0;t<=I.len+1e-9;t+=dt){const x=Math.min(1,t/I.sweep),f=Math.exp(lE+(lS-lE)*Math.pow(1-x,cp)),y=clamp((t-hold)/Math.max(1e-4,I.len-hold),0,1);curve.push({ms:t*1000,f,a:Math.pow(1-y,tp)})}
  const m=NI_midi(fE);return{src:'params',label,exact:true,curve,startHz:fS,endHz:fE,endNote:m,range:{lo:fE,hi:fE},lifeMs:I.len*1000}}
/* parameters only (no render): the kick model of a track, or null when the sound has to be measured. note: the note played (key tracking) */
function NI_kickModel(t,note){const I=t&&t.inst;if(!I)return null;
  if(I.preset==='kick'){const p=note!=null?note:36;return NI_kdCurve(I,I.kt?p-36:0,'Kick designer settings')}
  if(I.preset==='drums'&&Array.isArray(I.pads)){const N=NI_allNotes(t).filter(n=>NI_kickPad(I,n.p)>=0),cnt={};for(const n of N)cnt[n.p]=(cnt[n.p]||0)+1;
    const p=note!=null&&NI_kickPad(I,note)>=0?note:+(Object.keys(cnt).sort((a,b)=>cnt[b]-cnt[a])[0]||36),i=NI_kickPad(I,p);if(i<0)return null;const pd=I.pads[i];
    if(pd.type==='kd'){const k=pd.k||kickParams('psyzap'),q=pd.tune||pd.dec!==1?{...k,tune:k.tune+pd.tune,len:Math.min(2.5,k.len*pd.dec)}:k;return Object.assign(NI_kdCurve(q,0,'drum pad "'+(pd.name||'Kick')+'" (Kick designer) settings'),{pad:i})}
    const base=KPRE[pd.kp||'house']||KPRE.house;return Object.assign(NI_kdCurve({...base,tune:base.tune+pd.tune,len:Math.min(2.5,base.len*(pd.dec||1))},0,'drum pad "'+(pd.name||'Kick')+'" settings'),{pad:i})}
  return null}
/* YIN on x from i0 over W samples, periods between sr/fmax and sr/fmin; 0 when no pitch */
function NI_yin(x,i0,W,sr,fmin,fmax,thr){const tmin=Math.max(2,Math.floor(sr/fmax)),tmax=Math.min(Math.ceil(sr/fmin),x.length-i0-W-2);if(tmax<=tmin+2)return 0;
  const c=new Float64Array(tmax+2);let run=0;c[0]=1;
  for(let t=1;t<=tmax+1;t++){let s=0;for(let j=0;j<W;j++){const q=x[i0+j]-x[i0+j+t];s+=q*q}run+=s;c[t]=run>0?s*t/run:1}
  let T=-1;for(let t=tmin;t<=tmax;t++)if(c[t]<thr){while(t+1<=tmax&&c[t+1]<c[t])t++;T=t;break}
  if(T<0){let b=1e9;for(let t=tmin;t<=tmax;t++)if(c[t]<b){b=c[t];T=t}if(b>.3)return 0}
  const a=c[T-1],b=c[T],d=c[T+1],den=a-2*b+d,sh=den>1e-12?clamp(.5*(a-d)/den,-1,1):0;return sr/(T+sh)}
/* measure a rendered kick: mono, low-passed and taken down to about 12 kHz, the hits found from the level, YIN every 5 ms on the hit with the longest tail */
function NI_kickMeasure(buf,b0){const sr0=buf.sampleRate,L=buf.getChannelData(0),R=buf.numberOfChannels>1?buf.getChannelData(1):L,D=Math.max(1,Math.round(sr0/12000)),sr=sr0/D,n=Math.floor(L.length/D),x=new Float32Array(n);
  {const w=2*Math.PI*1200/sr0,al=Math.sin(w)/(2*.707),cw=Math.cos(w),a0=1+al,b0q=(1-cw)/2/a0,b1q=(1-cw)/a0,a1=-2*cw/a0,a2=(1-al)/a0;let x1=0,x2=0,y1=0,y2=0;
   for(let i=0,k=0;i<n*D;i++){const v=(L[i]+R[i])/2,y=b0q*v+b1q*x1+b0q*x2-a1*y1-a2*y2;x2=x1;x1=v;y2=y1;y1=y;if(i%D===0)x[k++]=y}}
  const B=Math.max(1,Math.round(sr*.0025)),nb=Math.floor(n/B),env=new Float32Array(nb);let pk=0;for(let j=0;j<nb;j++){let s=0;for(let i=j*B;i<(j+1)*B;i++)s+=x[i]*x[i];env[j]=Math.sqrt(s/B);if(env[j]>pk)pk=env[j]}
  if(pk<1e-4)return null;const hits=[];let last=-1e9;for(let j=0;j<nb;j++){const pv=j?Math.max(env[j-1],env[Math.max(0,j-2)]):0;if(env[j]>.2*pk&&env[j]>2.5*pv+1e-6&&(j-last)*B/sr>.08){hits.push(j);last=j}}
  if(!hits.length)return null;
  /* the hit that rings longest before the next one (or the end) */
  let bi=0,bl=0;hits.forEach((h,i)=>{const e=i+1<hits.length?hits[i+1]:nb,l=e-h;if(l>bl){bl=l;bi=i}});
  const h0=hits[bi]*B,h1=Math.min(n,(bi+1<hits.length?hits[bi+1]*B:n)),fmin=27,W=Math.round(sr*.035),hop=Math.round(sr*.005),curve=[];
  for(let i=h0;i+W+Math.ceil(sr/fmin)+2<h1;i+=hop){let s=0;for(let j=0;j<W;j++)s+=x[i+j]*x[i+j];const a=Math.sqrt(s/W)/pk;if(a<.02)break;const f=NI_yin(x,i,W,sr,fmin,500,.12);curve.push({ms:(i-h0)/sr*1000,f,a})}
  const ok=curve.filter(q=>q.f>0);if(ok.length<3)return{hits:hits.map(h=>b0+beatOfSec(h*B/sr,b0)),curve,why:'The kick is too short or too noisy to read a pitch.'};
  /* the tail: the second half of the frames that have a pitch, the median is the end note, the spread its range */
  const tail=ok.slice(Math.floor(ok.length/2)).map(q=>q.f).sort((a,b)=>a-b),pct=p=>tail[Math.min(tail.length-1,Math.max(0,Math.round(p*(tail.length-1))))],fE=pct(.5);
  let lo=pct(.1),hi=pct(.9);const wide=fE<40?.4:.1;lo=Math.min(lo,fE*Math.pow(2,-wide/12*1));hi=Math.max(hi,fE*Math.pow(2,wide/12));
  const life=curve.length?curve[curve.length-1].ms+35:0;
  return{src:'audio',label:'measured from the sound',exact:false,curve,startHz:ok[0].f,endHz:fE,endNote:NI_midi(fE),range:{lo,hi},lifeMs:life,low:fE<40,hits:hits.map(h=>b0+beatOfSec(h*B/sr,b0))}}
const beatOfSec=(s,b0)=>beatOf(secOf(b0)+s)-b0;
/* a bass note against the kick's end: the interval folded to the nearest octave, the beat rate between the kick's harmonic and the bass
   (or the bass harmonic and the kick, when the bass is lower) and the state: tuned (under 30 cents), clash (0.3 to 2.5 semitones), apart */
function NI_kbPair(fK,fB){const d=12*Math.log2(fB/fK),o=Math.round(d/12),dd=d-12*o,beat=o>=0?Math.abs(fB-fK*Math.pow(2,o)):Math.abs(fK-fB*Math.pow(2,-o)),a=Math.abs(dd);
  return{semis:d,oct:o,off:dd,beatHz:beat,state:a<.3?'tuned':a<=2.5?'clash':'apart'}}
/* the analysis. o: {t (song beat; default the playhead), kick (track id), bass (track id), sr}. Resolves to
   {key, bar:{n,b0,b1}, kick:{id,name,src,label,exact,curve:[{ms,f,a}],startHz,endHz,endNote,endTxt,range:{lo,hi,txt},lifeMs,inKey,hits:[beat]},
    bass:{id,name,notes:[{p,b,l,f,txt,inKey,pair:{semis,oct,off,beatHz,state}}],why}, overlap:[{b, notes:[i], gapMs}], suggest:{tuneTo}, words}
   or {empty, why} / {stale, why} / {busy, why}. */
async function NI_kickBass(o){o=Object.assign({},o||{});if(EXR)return{busy:true,why:'An export is running. Try again when it is done.'};
  const K=NI_key(),kt=o.kick!=null?trkById(o.kick):NI_pick(NI_kickScore),bt=o.bass!=null?trkById(o.bass):NI_pick(NI_bassScore,kt&&kt.id);
  if(!kt)return{empty:true,why:'No kick found. Name a track "Kick" or use the Kick designer.',key:K};
  let t=o.t!=null?o.t:curDisp();const hasK=b=>{const P=barPos(Math.max(0,b));return kt.clips.some(c=>!c.mute&&c.start<P.start+P.len&&c.start+c.len>P.start)};
  if(!hasK(t)){const c=kt.clips.filter(c=>!c.mute).sort((a,b)=>a.start-b.start)[0];if(c)t=c.start}
  const P=barPos(Math.max(0,t)),b0=P.start,b1=P.start+P.len,sr=o.sr||(ctx&&ctx.sampleRate)||48000;
  const key=NI_hash(JSON.stringify([kt,bt||null,b0,K,sr,tmapKey()]));if(NI.kb.cache.has(key))return NI.kb.cache.get(key);
  const sig=NI_sig(),T0=performance.now();
  /* the kick: from its settings, else measured */
  const kN=NI_notesIn(kt,b0,b1),I=kt.inst,kHit=kN.filter(n=>!I||I.preset!=='drums'||NI_kickPad(I,n.p)>=0);let k=NI_kickModel(kt,kHit.length?kHit[0].p:null);
  if(k)k.hits=kHit.map(n=>n.b);
  else{try{const span=Math.min(P.len+1,8),buf=await renderMixChunked(sr,b0,b0+span,0,false,kt.id,null,false);if(NI_sig()!==sig)return{stale:true,why:'The song changed while it was measured. Try again.'};
      k=NI_kickMeasure(buf,b0)}catch(e){if(e&&e.message==='cancelled')return{stale:true,why:'Cancelled.'};console.warn('NI_kickBass',e);return{error:String(e&&e.message||e)}}
    if(!k)return{empty:true,why:'The kick is silent in bar '+(P.bar+1)+'.',key:K,bar:{n:P.bar+1,b0,b1}};if(!k.endHz)return{empty:true,why:k.why,key:K,bar:{n:P.bar+1,b0,b1}}
    k.hits=k.hits.filter(b=>b<b1-.02)}
  const kk={id:kt.id,name:kt.name,...k,endTxt:NI_noteTxt(k.endNote),inKey:NI_inKey(k.endNote,K)};
  kk.range.txt=Math.abs(NI_midi(kk.range.hi)-NI_midi(kk.range.lo))<.02?NI_noteTxt(kk.endNote):NI_noteTxt(NI_midi(kk.range.lo))+' to '+NI_noteTxt(NI_midi(kk.range.hi));
  /* the bass notes of the bar */
  const bass={id:bt?bt.id:null,name:bt?bt.name:'',notes:[],why:''};
  if(!bt)bass.why='No bass found. Name a track "Bass" or give it notes under C3.';
  else{for(const n of NI_notesIn(bt,b0,b1)){const f=NI_hz(n.p);bass.notes.push({p:n.p,b:n.b,l:n.l,v:n.v,f,txt:NI_noteTxt(n.p),inKey:NI_inKey(n.p,K),pair:NI_kbPair(kk.endHz,f)})}
    if(!bass.notes.length)bass.why='The bass plays no notes in bar '+(P.bar+1)+'.'}
  /* each kick hit: the bass notes sounding during the kick's life, and the gap to the next bass note (the rolling bass leaves room for the kick) */
  const lifeB=b=>beatOf(secOf(b)+kk.lifeMs/1000)-b,overlap=kk.hits.map(h=>{const e=h+lifeB(h),on=[];bass.notes.forEach((q,i)=>{if(q.b<e-1e-6&&q.b+q.l>h+1e-6)on.push(i)});
    const nx=bass.notes.find(q=>q.b>=h-1e-6);return{b:h,end:e,notes:on,gapMs:nx?Math.round((secOf(nx.b)-secOf(h))*1000):null}});
  /* "tune the kick to the root": the root nearest to where the kick settles */
  let tuneTo=null;{const m=kk.endNote,r0=Math.round((m-K.root)/12)*12+K.root;tuneTo={note:r0,txt:NI_noteTxt(r0),semis:r0-m}}
  const r={key:K,bar:{n:P.bar+1,b0,b1},kick:kk,bass,overlap,suggest:{tuneTo},sr,ms:Math.round(performance.now()-T0)};r.words=NI_kbWords(r);
  NI.kb.cache.set(key,r);if(NI.kb.cache.size>24)NI.kb.cache.delete(NI.kb.cache.keys().next().value);return r}
/* in words: "The kick settles on F♯1 (46.2 Hz, from the Kick designer settings). Bar 9 bass: F♯2 in tune; G1 beating at 2.8 Hz." */
function NI_kbWords(r){const k=r.kick,f=v=>v.toFixed(1)+' Hz';let w=`The kick settles on ${k.exact?k.endTxt:'about '+k.range.txt} (${f(k.endHz)}, ${k.label})${k.low&&!k.exact?'; under 40 Hz this is a range, not exact':''}. Key: ${r.key.name}${k.inKey?'':', the kick is outside it'}.`;
  if(r.bass.notes.length){const seen=new Set(),parts=[];for(const q of r.bass.notes){if(seen.has(q.p))continue;seen.add(q.p);const s=q.pair.state;
      parts.push(q.txt+(s==='tuned'?' in tune with the kick':s==='clash'?` beating at ${q.pair.beatHz.toFixed(1)} Hz`:` ${Math.abs(q.pair.off).toFixed(1)} semitones from the kick`))}
    w+=` Bar ${r.bar.n} bass: ${parts.join('; ')}.`}else if(r.bass.why)w+=' '+r.bass.why;
  if(r.suggest.tuneTo&&Math.abs(r.suggest.tuneTo.semis)>=.3)w+=` Tuning the kick to the root: ${r.suggest.tuneTo.txt} (${r.suggest.tuneTo.semis>0?'+':''}${r.suggest.tuneTo.semis.toFixed(1)} semitones).`;return w}
NI.kickBass=NI_kickBass;NI.kickModel=NI_kickModel;NI.key=NI_key;NI_HOOKS.kickBass=NI_kickBass;
/* ===== end of lane D NI-2a ===== */
"""
A3 = "function askChoice(title,text,btns,icon){"
s = put(s, A3, JS)
open(P, 'w', encoding='utf-8').write(s)
print('NI-2a applied')
