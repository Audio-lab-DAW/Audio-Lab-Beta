
/* ===== lane D (task NI-7b): X23 the gain staging check for the whole mix (AE3 pick, folded into I13 level journey) =====
   Every track that plays in the range is measured with NI-7's one-track render (a tap after its clips or instrument and after each device
   that is on, and after its fader and pan; nothing in the live path). Problems, one line each with a jump to the track:
   - hot: a peak over -1 dBFS anywhere before the fader (into a device, or out of the last device into the fader)
   - quiet into a level-sensitive device (compressor, drive, OTT, limiter...): peaks under -30 dBFS going in
   - barely heard: peaks under -40 dBFS after the fader
   The master: its peak after its own chain over the same range (renderMixChunked without the safety limiter), as headroom; a problem
   when it is over -1 dBFS and no limiter on the master holds it. Groups and returns are not measured on their own (their sound comes from
   other tracks); what goes into them is in their tracks' lines. */
NI.gs={w:null,tok:0,res:null,busy:false,tm:0,key:'',pend:null,runs:0};
const NI_GS_HOT=-1,NI_GS_QIN=-30,NI_GS_QOUT=-40;
const NI_gsSens=f=>/comp|ott|drive|dist|satur|gate|limit|clip|crush|duck|tape|tube|glue|maxim|exciter|fold|amp|side|dynam|de-?ess|transient|expand/i.test(f.type+' '+((FXDEF[f.type]||{}).name||''));
const NI_gsLim=f=>/limit|maxim|clip/i.test(f.type+' '+((FXDEF[f.type]||{}).name||''));
const NI_gsDb=v=>v<=-140?'silent':(v<0?'−':'+')+INS.fmt(Math.abs(Math.round(v*10)/10),'dBFS');
/* the problems of one measured track: res = NI_jourMeasure(t, b0, b1) */
function NI_gsJudge(t,res){const st=res.steps,P=[],live=st.filter(s=>s.k==='src'||(s.k==='fx'&&!s.midi)),fd=st.find(s=>s.k==='fader');if(!fd||fd.peak==null)return P;
  if(fd.peak<=-140&&live.every(s=>!(s.peak>-140)))return P;/* silent here */
  /* the point after step s: into the next device that is on, or into the fader */
  const into=s=>{const i=st.indexOf(s);for(let j=i+1;j<st.length;j++){if(st[j].k==='fx'&&!st[j].midi)return{f:st[j].f,name:st[j].name};if(st[j].k==='fader')return{name:'the fader'}}return{name:'the fader'}};
  let hot=null;for(const s of live)if(s.peak>NI_GS_HOT&&(!hot||s.peak>hot.s.peak))hot={s,to:into(s)};
  if(hot){const by=Math.ceil((hot.s.peak-NI_GS_HOT+.5)*2)/2,from=hot.s.k==='src'?(t.inst?'its instrument':'its clips'):hot.s.name;
    P.push({kind:'hot',t,step:hot.s,to:hot.to,peak:hot.s.peak,by,txt:`hot into ${hot.to.name}: peaks at ${NI_gsDb(hot.s.peak)} after ${from}`,
      tip:`${t.name} peaks at ${NI_gsDb(hot.s.peak)} going into ${hot.to.name}, over ${NI_gsDb(NI_GS_HOT)} before the fader. Devices that react to level (compressors, drive) behave differently that hot. Turn ${hot.s.k==='src'?(t.inst?'the instrument\'s volume':'the clip gain'):'the output of '+hot.s.name} down by about ${INS.fmt(by,'dB')} and the fader up by the same.`})}
  const qd=[];for(const s of live){const to=into(s);if(to.f&&NI_gsSens(to.f)&&s.peak>-140&&s.peak<NI_GS_QIN)qd.push({s,to})}
  if(qd.length){const q=qd.reduce((a,b)=>b.s.peak<a.s.peak?b:a);P.push({kind:'quiet',t,step:q.s,to:q.to,peak:q.s.peak,txt:`quiet into ${q.to.name}: peaks at ${NI_gsDb(q.s.peak)}`,
    tip:`${t.name} reaches ${q.to.name} at only ${NI_gsDb(q.s.peak)} (peak). ${q.to.name} reacts to level, so its settings may not do what they say at this level. Raise what feeds it, or lower its threshold.`})}
  if(fd.peak>-140&&fd.peak<NI_GS_QOUT)P.push({kind:'low',t,step:fd,peak:fd.peak,txt:`barely heard: peaks at ${NI_gsDb(fd.peak)} after its fader`,
    tip:`${t.name} peaks at only ${NI_gsDb(fd.peak)} after its fader and pan, so it adds little to the mix here. Raise it, or mute it if it is not needed.`});
  return P}
/* the master's peak after its own chain over [b0, b1) */
async function NI_gsMaster(b0,b1){const buf=await renderMixChunked(44100,b0,b1,0,false,null,null,false);const L=buf.getChannelData?buf.getChannelData(0):buf.L,R=buf.getChannelData?buf.getChannelData(Math.min(1,buf.numberOfChannels-1)):buf.R;
  let pk=0;for(let i=0;i<L.length;i++){const a=Math.abs(L[i]),b=Math.abs(R[i]);if(a>pk)pk=a;if(b>pk)pk=b}const peak=pk>0?20*Math.log10(pk):-150,lim=(S.mfx||[]).find(f=>f.on&&NI_gsLim(f));
  return{peak,head:-peak,lim:lim?((FXDEF[lim.type]||{}).name||lim.type):null}}
/* the check over the range (NI-7's: the loop or the 8 bars around the playhead). o: {prog(done, total), isOk()} */
async function NI_gsMeasure(o){o=o||{};const r=NI_jourRange(),b0=r.b0,b1=r.b1;
  const L=S.tracks.filter(t=>t.kind!=='group'&&t.kind!=='return'&&!t.mute&&(t.clips||[]).some(c=>!c.mute&&c.start<b1&&c.start+c.len>b0));
  const tracks=[],probs=[];let k=0;
  for(const t of L){if(o.isOk&&!o.isOk())return{cancelled:true};if(o.prog)try{o.prog(k,L.length+1)}catch(_){}k++;
    let m;try{m=await NI_jourMeasure(t,b0,b1)}catch(e){console.warn('NI gain staging',t.name,e);continue}
    const fd=m.steps.find(s=>s.k==='fader'),src=m.steps.find(s=>s.k==='src');tracks.push({t,id:t.id,name:t.name,inPeak:src&&src.peak,outPeak:fd&&fd.peak,outRms:fd&&fd.rms});probs.push(...NI_gsJudge(t,m))}
  if(o.isOk&&!o.isOk())return{cancelled:true};if(o.prog)try{o.prog(L.length,L.length+1)}catch(_){}
  const master=await NI_gsMaster(b0,b1);
  if(master.peak>NI_GS_HOT&&!master.lim)probs.push({kind:'master',t:null,peak:master.peak,txt:`peaks at ${NI_gsDb(master.peak)}: ${master.peak>=0?'it clips':'under 1 dB of headroom'}`,
    tip:`The master peaks at ${NI_gsDb(master.peak)} after its own effects, with no limiter on it. Lower the loudest tracks (or all faders a little) so it peaks around −6 dBFS while you mix.`});
  const ord={master:0,hot:1,quiet:2,low:3};probs.sort((a,b)=>ord[a.kind]-ord[b.kind]||b.peak-a.peak);
  return{b0,b1,how:r.how,tracks,probs,master}}
function NI_gsOpen(){const G=NI.gs,z=ZOOM,vw=innerWidth/z,vh=innerHeight/z;
  const w=fwin('niGain','Gain staging',{x:Math.round(vw*.2),y:Math.round(vh*.17),w:Math.round(Math.min(560,vw*.46)),h:Math.round(Math.min(420,vh*.62))},()=>NI_gsClose(true));
  if(!G.w||G.w!==w){G.w=w;w.querySelector('.fwt').title='Tracks too hot going into their devices or too quiet, and the master\'s headroom';{const c=w.querySelector('.fwc');if(c)c.title='Close the gain staging check'}
    w.querySelector('.fwb').innerHTML=`<div class="ngt"><span title="What this window checks">Levels into each device and out of each fader</span><button data-ng="again" title="Measure again">Measure again</button><span class="ngst" aria-live="polite"></span></div>
      <div class="ngl"></div><div class="ngm"></div>
      <div class="ngnote" title="How it is measured">Each track on its own, offline: peaks after its clips or instrument, after each device and after its fader. Hot means over −1 dBFS before the fader; quiet means under −30 dBFS into a compressor, drive or limiter, or under −40 dBFS after the fader. Nothing is added to what you hear.</div>`;
    w.querySelector('[data-ng="again"]').onclick=()=>{G.key='';NI_gsRun()};
    w.querySelector('.ngl').addEventListener('click',e=>{const j=e.target.closest('[data-ngj]');if(j){e.stopPropagation();if(trkById(j.dataset.ngj)){selectTrack(j.dataset.ngj);try{NI_jourOpen(j.dataset.ngj)}catch(_){}}return}
      const r=e.target.closest('[data-ngt]');if(r&&trkById(r.dataset.ngt))selectTrack(r.dataset.ngt)})}
  clearInterval(G.tm);G.tm=setInterval(NI_gsTick,300);NI_gsRun();return w}
function NI_gsClose(fromWin){const G=NI.gs;clearInterval(G.tm);G.tm=0;G.tok++;G.busy=false;if(!fromWin&&G.w)G.w.hidden=true}
function NI_gsKey(){const r=NI_jourRange();return r.b0+'|'+r.b1+'|'+NI_sig()+'|'+JSON.stringify(S.mfx||[])}
function NI_gsTick(){const G=NI.gs,w=G.w;if(!w||w.hidden){clearInterval(G.tm);G.tm=0;return}if(play.on||G.busy)return;const k=NI_gsKey();if(k===G.key){G.pend=null;return}
  if(!G.pend||G.pend.k!==k)G.pend={k,t:performance.now()};else if(performance.now()-G.pend.t>800){G.pend=null;NI_gsRun()}}
async function NI_gsRun(){const G=NI.gs,w=G.w;if(!w||w.hidden)return;const tok=++G.tok,st=w.querySelector('.ngst'),ok=()=>tok===G.tok&&!w.hidden,pj=PJ&&PJ.cur;G.key=NI_gsKey();G.busy=true;G.runs++;st.textContent='Measuring…';
  try{const res=await NI_gsMeasure({prog:(d,n)=>{if(ok())st.textContent=d<n-1?`Measuring track ${d+1} of ${n-1}…`:'Measuring the master…'},isOk:()=>ok()&&(PJ&&PJ.cur)===pj});
    if(!ok())return;if(res.cancelled){st.textContent='Stopped: the song changed.';return}G.res=res;NI_gsShow(res);const a=NI_bb(res.b0),b=NI_bb(res.b1),n=res.probs.length;
    st.textContent=(n?`${n} to look at`:'nothing to fix')+`, bars ${a.bar} to ${b.bar-1} (${res.how})`;st.title='What was found, and the range measured'}
  catch(e){if(!ok())return;console.warn('NI gain staging',e);st.textContent='Could not measure: '+(e&&e.message||e)}finally{if(tok===G.tok)G.busy=false}}
function NI_gsShow(res){const w=NI.gs.w,l=w.querySelector('.ngl'),m=w.querySelector('.ngm'),cls={master:'bad',hot:'bad',quiet:'warn',low:'warn'};
  let h='';if(!res.tracks.length)h='<div class="ngempty" title="Move the playhead or set a loop over a part that plays">No track plays in this range.</div>';
  else if(!res.probs.length)h=`<div class="ngok" title="${res.tracks.length} tracks measured">Nothing to fix: every track enters its devices under −1 dBFS and comes out of its fader at a usable level.</div>`;
  for(const p of res.probs){if(p.kind==='master'){h+=`<div class="ngr ${cls[p.kind]}" title="${esc(p.tip)}"><span class="ngn"><i style="--c:#ececf1"></i>Master</span><span class="ngw">${esc(p.txt)}</span><span></span></div>`;continue}
    h+=`<div class="ngr ${cls[p.kind]}" data-ngt="${esc(p.t.id)}" title="${esc(p.tip)}"><span class="ngn"><i style="--c:${esc(p.t.color||'#8b8b97')}"></i>${esc(p.t.name)}</span><span class="ngw">${esc(p.txt)}</span>`+
      `<button type="button" data-ngj="${esc(p.t.id)}" title="Select ${esc(p.t.name)} and open its level journey (the level after each of its devices)">Journey</button></div>`}
  l.innerHTML=h;const M=res.master;
  m.innerHTML=`<span title="The master's peak over this range, after its own effects, without the safety limiter. Headroom is how far that peak sits under 0 dBFS">Master: peaks at ${NI_gsDb(M.peak)}${M.peak<0?`, ${INS.fmt(Math.round(-M.peak*10)/10,'dB')} of headroom`:', no headroom'}${M.lim?` (after its ${esc(M.lim)})`:''}</span>`}
NI.gs.open=NI_gsOpen;NI.gs.close=()=>NI_gsClose(false);NI.gs.measure=NI_gsMeasure;NI.gs.judge=NI_gsJudge;
NI_HOOKS.gainStaging={open:NI_gsOpen,measure:o=>NI_gsMeasure(o)};
/* ===== end of lane D NI-7b ===== */
