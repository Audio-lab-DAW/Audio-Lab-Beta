
/* ===== lane D (task NI-31): X18 high-pass hints with a one-click cut (AE3 pick) =====
   From NI-3's per-beat bands on up to four stretches of 24 beats per track spread over the song: a track that has level under a line it does not need gets a
   hint with the frequency. The line: for a track with notes, 0.6 times the frequency of its lowest note (its fundamental keeps its level
   within about 0.5 dB once cut); for a track without notes (audio), 150 Hz. Never on a kick, a bass, a sub or a drum kit (NI-2a's scores
   and the names), never when the line falls under 40 Hz. Hint: at least 1 % of the track's level under the line; for audio at most 20 %
   (more means the low end is the sound itself). One click adds a gentle high-pass (12 dB per octave) at the line on the track's Pro EQ,
   one undo step: the EQ's own high-pass band when there is one (raised, never lowered), else a new Pro EQ first in the chain. A
   suggestion only, never automatic. Window #niHp: main menu, command ni.hpHints; NI_HOOKS.hpHints. Returns are not measured (NI-3
   measures tracks; a return's sound comes from the sends). */
NI.hp={w:null,tok:0,res:null,busy:false,tm:0,key:'',pend:null,runs:0,cuts:0};
const NI_HP_AUDIO=150,NI_HP_MIN=40,NI_HP_SHARE=.01,NI_HP_AMAX=.2;
/* why a track gets no hint at all: kick, bass, sub, drums */
function NI_hpSkip(t){const I=t.inst,pr=I&&I.preset,nm=String(t.name||'');
  if(pr==='kick'||/kick|\bbd\b/i.test(nm))return'a kick';if(pr==='drums'||/drum/i.test(nm))return'a drum kit, it may hold the kick';if(/\bsub\b|808/i.test(nm))return'a sub';if(/bass/i.test(nm))return'a bass';
  try{if(NI_kickScore(t)>=6)return'a kick';if(NI_bassScore(t)>=4)return'plays a bass line'}catch(e){}return''}
/* the line of a track: {hz, why} or null */
function NI_hpLine(t){const N=NI_allNotes(t);if(N.length){let m=1e9;for(const n of N)if(n.p<m)m=n.p;const f0=NI_hz(m),hz=Math.min(300,.6*f0);
    if(hz<NI_HP_MIN)return null;return{hz,why:`below its lowest note (${NI_noteTxt(m)}, ${NI_fmtHz(f0)})`,note:m,audio:false}}
  return{hz:NI_HP_AUDIO,why:'a usual line for a sound that is not a kick or a bass',audio:true}}
/* a nice frequency for the button: 5 Hz steps under 100, 10 Hz above */
const NI_hpRound=f=>f<100?Math.max(5,Math.round(f/5)*5):Math.round(f/10)*10;
/* the share of a track's level under hz (bands of 1/6 octave, a band counts in the part of it under hz, on the log scale) */
function NI_hpShare(x,hz){const B=NI.an.bands;let lo=0,all=0;for(let i=0;i<B.length;i++){const a=x.PM[i]+x.PS[i];all+=a;const e0=B[i]*Math.pow(2,-1/12),e1=B[i]*Math.pow(2,1/12);
    const fr=hz>=e1?1:hz<=e0?0:Math.log(hz/e0)/Math.log(e1/e0);lo+=a*fr}return all>0?lo/all:0}
/* up to NI_HP_PIECES stretches of 24 beats per track (NI-3's pieces) where it sounds, spread over the song: enough for the low end, and a
   long song is not rendered whole (on a 1152-beat song with 26 tracks the whole song is 1274 renders) */
const NI_HP_PIECES=4;
function NI_hpPieces(t){const e=Math.ceil(NI_anEnd()/NI_AN_SEG),P=[];for(let p=0;p<e;p++)if(NI_anKey(t,p)!=='')P.push(p);if(P.length<=NI_HP_PIECES)return P;
  const out=[];for(let i=0;i<NI_HP_PIECES;i++)out.push(P[Math.floor((i+.5)*P.length/NI_HP_PIECES)]);return[...new Set(out)]}
/* per track: summed mid and side power per band over its chosen pieces (only the beats it plays) */
async function NI_hpTracks(L,o){o=o||{};const jobs=[];for(const t of L)for(const p of NI_hpPieces(t))jobs.push({t,p});let done=0;const tot=jobs.length;if(o.prog)o.prog(0,tot);
  const rs=await Promise.all(jobs.map(j=>NI_anEnsure({tracks:[j.t],b0:j.p*NI_AN_SEG,b1:(j.p+1)*NI_AN_SEG}).then(r=>{done++;if(o.prog)try{o.prog(done,tot)}catch(_){}return r})));
  if(rs.some(r=>r.cancelled&&r.done<r.total))return{cancelled:true};const NB=NI_AN_NB,out=[];
  for(const t of L){const PM=new Float64Array(NB),PS=new Float64Array(NB);let n=0;
    for(const j of jobs){if(j.t!==t)continue;for(let b=j.p*NI_AN_SEG;b<(j.p+1)*NI_AN_SEG;b++){const g=NI_anGet(t,b,{noQueue:true});if(!g||g.silent||!g.mid||!g.play)continue;n++;for(let i=0;i<NB;i++){PM[i]+=Math.pow(10,g.mid[i]/10);PS[i]+=Math.pow(10,g.side[i]/10)}}}
    if(n)out.push({t,PM,PS,beats:n})}
  return{tracks:out,pieces:tot}}
/* the hints of the song: resolves {hints: [{t, id, name, hz, cut, share, why, audio}], skipped: [{name, why}], pieces} */
async function NI_hpMeasure(o){o=o||{};const hints=[],skipped=[],cand=[];
  for(const t of NI_anTracks()){if(t.mute||!(t.clips||[]).some(c=>!c.mute))continue;const sk=NI_hpSkip(t);if(sk){skipped.push({name:t.name,why:sk});continue}
    const L=NI_hpLine(t);if(!L){skipped.push({name:t.name,why:'its notes reach the lowest octave'});continue}cand.push(t)}
  const r=await NI_hpTracks(cand,o);if(r.cancelled)return{cancelled:true};
  for(const x of r.tracks){const t=x.t,L=NI_hpLine(t),cut=NI_hpRound(L.hz),share=NI_hpShare(x,cut);if(share<NI_HP_SHARE)continue;
    if(L.audio&&share>NI_HP_AMAX){skipped.push({name:t.name,why:'much of its sound is low: probably needed'});continue}
    hints.push({t,id:t.id,name:t.name,color:t.color||'#8b8b97',hz:L.hz,cut,share,why:L.why,audio:L.audio,x})}
  hints.sort((a,b)=>b.share-a.share);return{hints,skipped,pieces:r.pieces}}
/* the cut: one undo step */
function NI_hpCut(id,hz){const t=trkById(id);if(!t||!(hz>0))return null;let f=(t.fx||[]).find(x=>x.type==='eq'&&x.on&&x.p&&Array.isArray(x.p.bands)&&x.p.bands.some(b=>b.t==='highpass')),made=false;
  {const o=f&&f.p.bands.find(q=>q.t==='highpass');if(o&&o.on&&o.f>=hz){toast(`${t.name} is already cut under ${NI_fmtHz(o.f)}.`);return{f,band:o,same:true}}}
  pushUndo();if(!f){f=mkFx('eq');t.fx=t.fx||[];t.fx.unshift(f);made=true}const b=f.p.bands.find(q=>q.t==='highpass');
  Object.assign(b,{on:true,f:Math.round(hz),q:.3,sl:12})/* the Pro EQ's lowest Q: the least rise above the cut */;NI.hp.cuts++;changed(true);try{renderFx()}catch(e){}try{renderMixer()}catch(e){}
  toast(`${t.name}: a gentle high-pass at ${NI_fmtHz(hz)} (12 dB per octave) on ${made?'a new Pro EQ':'its Pro EQ'}. Undo takes it back.`);return{f,band:b,made}}
const NI_hpPct=v=>v>=.095?Math.round(v*100)+' %':(Math.round(v*1000)/10).toString()+' %';
function NI_hpShow(res){const w=NI.hp.w,g=w.querySelector('.nhg'),sk=w.querySelector('.nhs');
  if(!res.hints.length)g.innerHTML=`<div class="nhempty" title="Tracks with notes: nothing under 0.6 times their lowest note; other tracks: nothing under 150 Hz (at least 1 % of their level would count)">No track has level under a line it does not need. Nothing to cut.</div>`;
  else g.innerHTML=res.hints.map(h=>{const tip=`${h.name}: ${NI_hpPct(h.share)} of its level is under ${NI_fmtHz(h.cut)}, ${h.why}. An estimate from up to four stretches of 24 beats where it plays, spread over the song.`;
    return`<div class="nhnm" data-nht="${esc(h.id)}" style="--c:${esc(h.color)}" title="${esc(h.name)}: click to select the track"><i></i>${esc(h.name)}</div>
      <div class="nhw" title="${esc(tip)}"><b>${NI_hpPct(h.share)}</b> under ${NI_fmtHz(h.cut)}, ${esc(h.why)}</div>
      <button type="button" data-nhc="${esc(h.id)}" data-hz="${h.cut}" title="Add a gentle high-pass (12 dB per octave) at ${NI_fmtHz(h.cut)} on ${esc(h.name)}'s Pro EQ. One undo step. Listen before and after: some sounds need their low end.">Cut under ${NI_fmtHz(h.cut)}</button>`}).join('');
  sk.textContent=res.skipped.length?'Not checked: '+res.skipped.map(s=>`${s.name} (${s.why})`).join(', ')+'.':'';sk.title='Tracks left alone and why'}
function NI_hpKey(){return NI_sig()+'|'+Math.ceil(NI_anEnd())}
async function NI_hpRun(){const H=NI.hp,w=H.w;if(!w||w.hidden)return;const tok=++H.tok,st=w.querySelector('.nhst'),ok=()=>tok===H.tok&&!w.hidden;H.key=NI_hpKey();H.busy=true;H.runs++;st.textContent='Measuring…';
  try{const res=await NI_hpMeasure({prog:(d,n)=>{if(ok())st.textContent=`Analysing ${d} of ${n} pieces…`}});if(!ok())return;if(res.cancelled){st.textContent='Stopped: the song changed.';return}
    H.res=res;NI_hpShow(res);st.textContent=res.hints.length?res.hints.length+(res.hints.length>1?' hints':' hint'):'all clean';st.title='Measured on up to four stretches of 24 beats per track, spread over the song'}
  catch(e){if(!ok())return;console.warn('NI high-pass hints',e);st.textContent='Could not measure: '+(e&&e.message||e)}finally{if(tok===H.tok)H.busy=false}}
function NI_hpTick(){const H=NI.hp,w=H.w;if(!w||w.hidden){clearInterval(H.tm);H.tm=0;return}if(play.on||H.busy)return;const k=NI_hpKey();if(k===H.key){H.pend=null;return}
  if(!H.pend||H.pend.k!==k)H.pend={k,t:performance.now()};else if(performance.now()-H.pend.t>800){H.pend=null;NI_hpRun()}}
function NI_hpOpen(){const H=NI.hp,z=ZOOM,vw=innerWidth/z,vh=innerHeight/z;
  const w=fwin('niHp','High-pass hints',{x:Math.round(vw*.22),y:Math.round(vh*.18),w:Math.round(Math.min(560,vw*.46)),h:Math.round(Math.min(380,vh*.6))},()=>NI_hpClose(true));
  if(!H.w||H.w!==w){H.w=w;w.querySelector('.fwt').title='Tracks with level under a line they do not need, and a one-click gentle cut';{const c=w.querySelector('.fwc');if(c)c.title='Close the high-pass hints'}
    w.querySelector('.fwb').innerHTML=`<div class="nht"><span title="Suggestions only: nothing is cut until you click">Suggestions: click to cut, Undo takes it back.</span><button data-nh="again" title="Measure again">Measure again</button><span class="nhst" aria-live="polite"></span></div>
      <div class="nhg"></div><div class="nhs"></div>
      <div class="nhnote">From each track on its own, offline, on up to four stretches of 24 beats spread over the song. Never on kicks, basses, subs or drum kits. Returns are not checked.</div>`;
    w.querySelector('[data-nh="again"]').onclick=()=>NI_hpRun();
    w.querySelector('.nhg').addEventListener('click',e=>{const b=e.target.closest('[data-nhc]');if(b){e.stopPropagation();NI_hpCut(b.dataset.nhc,+b.dataset.hz);return}const r=e.target.closest('[data-nht]');if(r&&trkById(r.dataset.nht))selectTrack(r.dataset.nht)})}
  clearInterval(H.tm);H.tm=setInterval(NI_hpTick,300);NI_hpRun();return w}
function NI_hpClose(fromWin){const H=NI.hp;clearInterval(H.tm);H.tm=0;H.tok++;H.busy=false;if(!fromWin&&H.w)H.w.hidden=true}
NI_HOOKS.hpHints={open:NI_hpOpen,measure:o=>NI_hpMeasure(o),cut:(id,hz)=>NI_hpCut(id,hz),line:t=>NI_hpLine(t)};
/* ===== end of lane D NI-31 ===== */
