"""Task NI-7 (lane D): I13 level journey.
Edit script with unique asserted anchors (needs NI-6 in the file), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_7.py [index.html]
Adds:
  - a window "Level journey" (#niJour, the app's fwin) for the selected track: one row per step of its path, top to bottom: the clip
    (or the instrument), each switched-on device, the fader and pan, and where it goes (its group or the master). Each row: a level
    bar on a dBFS scale (RMS as the bar, the peak as a tick), RMS and peak in dB, and the change from the step before; the biggest rise
    and the biggest drop (3 dB or more) are marked; a peak above 0 dBFS is marked
  - measured on its own offline render of that one track (the same steps as renderMix's one-track path: clips, instrument, devices,
    fader, pan, Vector Map), with every step's output also sent to its own pair of output channels, so the live path and the export
    path get no taps and do not change; the master chain, sends and sidechains are not in it (said in the window)
  - over the loop when it is on, otherwise the 8 bars around the playhead (at most 16 bars), with 2 bars of pre-roll for tails
  - follows the selected track (switchable), measures again 0.8 s after an edit settles; nothing runs while it is closed; a 300 ms
    check while open does work only when the track, the range or the project changed and the song is stopped
  - command ni.levelJourney, an entry in the main menu, NI_HOOKS.levelJourney ({open(id), measure(id, b0, b1)}) for the mixer
    strip or the device frame (lanes A, I)
"""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane D (task NI-7)'
if MARK in s:
    print('NI-7 already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-6 ===== */' in s, 'NI-6 must be in the file first'

def rep(s, old, new):
    n = s.count(old)
    assert n == 1, (old[:70], n)
    return s.replace(old, new)

# 1. the command, after ni.energyArc
A1 = "run:()=>NI_arcShow(!UI.niArc)},"
s = rep(s, A1, A1 + "\n {id:'ni.levelJourney',g:'view',l:'Level journey of the selected track (level after each device)',d:'',ic:'M6 3v14M6 6h8M6 10h5M6 14h9',run:()=>NI_jourOpen()},")

# 2. the main menu, after the kick and bass lab
A2 = "act:()=>NI_kbOpen()},"
s = rep(s, A2, A2 + "\n   {label:'Level journey…',sub:'the level after each device of the selected track',ic:I('M6 3v14M6 6h8M6 10h5M6 14h9','#4cc9f0'),act:()=>NI_jourOpen()},")

# 3. CSS
CSS = r"""/* lane D (task NI-7): the level journey window. Instrument look: drafting grid, dB on every number, the track colour on the bars */
#niJour .fwb{flex-direction:column;gap:6px;padding:6px 10px 10px;overflow:auto}
#niJour .njt{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:var(--fs1);color:var(--mut)}
#niJour .njt b{color:var(--ink);font-size:var(--fs2);display:flex;align-items:center;gap:6px}#niJour .njt b i{width:9px;height:9px;border-radius:2px;background:var(--c)}
#niJour .njt button{min-height:22px;padding:0 8px;font-size:var(--fs1)}#niJour .njt label{display:flex;align-items:center;gap:4px;cursor:pointer}
#niJour .njst{margin-left:auto;font-variant-numeric:tabular-nums;white-space:nowrap}
#niJour .njg{display:grid;grid-template-columns:minmax(90px,1.1fr) minmax(140px,2.4fr) 62px 62px 74px;gap:3px 8px;align-items:center;font-size:var(--fs1)}
#niJour .njh{color:var(--mut);font-size:var(--fs1)}#niJour .njh.r,#niJour .njn{text-align:right}
#niJour .njsc{position:relative;height:13px}#niJour .njsc span{position:absolute;top:0;transform:translateX(-50%);font:var(--fw5) 9px/13px var(--ffu);color:var(--mut);font-variant-numeric:tabular-nums}
#niJour .njnm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#d9dce3;display:flex;align-items:center;gap:5px}
#niJour .njnm small{color:var(--mut)}#niJour .njnm.njoff{color:var(--mut);text-decoration:line-through}
#niJour .njb{position:relative;height:14px;border-radius:2px;background:#05070b;background-image:repeating-linear-gradient(90deg,rgba(255,255,255,.07) 0 1px,transparent 1px calc(100%/11));overflow:hidden}
#niJour .njb i{position:absolute;left:0;top:3px;bottom:3px;background:var(--c);opacity:.85;border-radius:1px}
#niJour .njb u{position:absolute;top:1px;bottom:1px;width:2px;margin-left:-1px;background:#ececf1}
#niJour .njb s{position:absolute;top:0;bottom:0;width:1px;background:rgba(255,255,255,.35)}
#niJour .njn{font-variant-numeric:tabular-nums;color:#cfe6ff;white-space:nowrap}#niJour .njn.over{color:#ffb547}
#niJour .njd{font-variant-numeric:tabular-nums;white-space:nowrap;text-align:right;color:var(--mut)}
#niJour .njd.up{color:#ffb547;font-weight:var(--fw6)}#niJour .njd.dn{color:#4cc9f0;font-weight:var(--fw6)}
#niJour .njnote{font-size:var(--fs1);color:var(--mut);line-height:1.35}
"""
s = rep(s, ".dacv{display:flex;", CSS + ".dacv{display:flex;")

# 4. JS after NI-6
JS = r"""
/* ===== lane D (task NI-7): I13 level journey =====
   One track's path measured on its own offline render: the same steps as renderMix's one-track path (clips, instrument, devices, fader,
   pan, Vector Map), and every step's output also goes to its own two output channels. Nothing is added to the live path or to exports. */
NI.jour={w:null,tid:null,follow:true,tok:0,res:null,busy:false,tm:0,key:'',pend:null,runs:0};
const NI_JOUR_SR=44100,NI_JOUR_LO=-60,NI_JOUR_HI=6;
/* the beats it measures: the loop when it is on, else the 8 bars around the playhead; at most 16 bars */
function NI_jourRange(){const L=S.loop&&S.loopRange&&S.loopRange.b>S.loopRange.a?S.loopRange:null;
  if(L){const b1=Math.min(L.b,barStart(barPos(L.a+1e-6).bar+16));return{b0:L.a,b1,how:L.b>b1?'the first 16 bars of the loop':'the loop'}}
  const p=play.on?curDisp():pos,bar=barPos(Math.max(0,p)+1e-6).bar,a=Math.max(0,bar-4);return{b0:barStart(a),b1:barStart(a+8),how:'8 bars around the playhead'}}
/* render one track with a tap after every step; o.taps: the steps to tap (indices into the step list), at most 15 per render */
async function NI_jourRender(t,b0,b1,steps,taps){const sr=NI_JOUR_SR,pre=Math.min(b0,8),bs=b0-pre,len=secSpan(bs,b1)+.02,nT=taps.length;
  const oc=quietMeters(new OfflineAudioContext(2*nT,Math.ceil(len*sr),sr));await wlLoad(oc);SIDE_B0=bs;if(S.seed==null)S.seed=(Math.random()*1e9)|0;
  SEEDR=UI.exSeed===false?null:seedRng(S.seed+'|'+bs.toFixed(6)+'|'+b1.toFixed(6)+'|'+t.id+'|'+sr);
  try{const D=oc.destination;D.channelCount=2*nT;D.channelCountMode='explicit';D.channelInterpretation='discrete';const mg=oc.createChannelMerger(2*nT);mg.connect(D);
    const tapAt=new Map(taps.map((k,i)=>[k,i])),tap=(node,k)=>{const i=tapAt.get(k);if(i==null)return;const up=oc.createGain();up.channelCount=2;up.channelCountMode='explicit';up.channelInterpretation='speakers';
      const sp=oc.createChannelSplitter(2);node.connect(up);up.connect(sp);sp.connect(mg,0,2*i);sp.connect(mg,1,2*i+1)};
    const tin=oc.createGain(),vol=oc.createGain(),pn=oc.createStereoPanner();vol.gain.value=t.vol;pn.pan.value=t.pan;let prev=tin,k=0;tap(tin,k++);
    for(const f of t.fx||[]){if(!f.on)continue;const x=mkFxNode(oc,f.type);x.set(f.p);prev.connect(x.in);prev=x.out;tap(prev,k++)}
    prev.connect(vol);vol.connect(pn);tap(pn,k++);if(typeof vmOffTrk==='function')vmOffTrk(oc,t,vol,pn);
    /* the clips, as renderMix schedules them */
    for(const c of t.clips||[]){if(c.mute)continue;const cs=c.start,ce=cs+c.len;if(ce<=bs||cs>=b1)continue;
      const bFrom=Math.max(0,bs-cs),t0=secSpan(bs,cs+bFrom),ch=clipChain(oc,c,bFrom,t0,tin,60/bpmAt(cs+bFrom),t.read!==false);
      if(c.notes){if(t.inst&&!(BGF.tst&&BGF.tst(oc,t,c,tin,bs)))for(const n of ccSus(c,mfxNotes(t,c.notes))){if(n.m||n.s<c.off||n.s>=c.off+c.len)continue;const nb=cs+n.s-c.off;if(nb<bs||nb>=b1)continue;PVCH=ch;try{synthB(oc,t.inst,ch.in,n.p,secSpan(bs,nb),secSpan(nb,nb+Math.min(n.l,c.off+c.len-n.s)),n.v,c,n.s,60/bpmAt(nb))}finally{PVCH=null}}}
      else{const B=srcView(c);if(B){const x=oc.createBufferSource();x.buffer=B.buf;x.connect(ch.in);const[o1,d1]=clipAudioSpan(c,bFrom);x.start(t0,o1,d1)}}}}
  finally{SEEDR=null}
  const buf=await oc.startRendering(),skip=Math.round(secSpan(bs,b0)*sr),out=[];
  for(let i=0;i<nT;i++){const L=buf.getChannelData(2*i),R=buf.getChannelData(2*i+1);let pk=0,ss=0;for(let j=skip;j<L.length;j++){const a=L[j],b=R[j];ss+=a*a+b*b;const m=Math.max(Math.abs(a),Math.abs(b));if(m>pk)pk=m}
    const n=Math.max(1,L.length-skip);out.push({rms:ss>0?10*Math.log10(ss/(2*n)):-150,peak:pk>0?20*Math.log10(pk):-150})}
  return out}
/* the steps of a track's path, in order */
function NI_jourSteps(t){const st=[{k:'src',name:t.inst?'Instrument'+(t.inst.name||t.inst.type?': '+(t.inst.name||t.inst.type):''):'Clips',tip:t.inst?'The instrument playing the clips, before any device':'The audio clips with their gain and fades, before any device'}];
  for(const f of t.fx||[]){const d=FXDEF[f.type]||{},nm=d.name||f.type;st.push(f.on?{k:'fx',f,name:nm,tip:nm+': the level after it',midi:!!d.midi}:{k:'off',f,name:nm,tip:nm+' is switched off, so the sound goes past it unchanged'})}
  const g=grpOf(t);st.push({k:'fader',name:'Fader and pan',tip:'After the track\'s fader ('+INS.fmt(Math.round(20*Math.log10(Math.max(1e-6,t.vol))*10)/10,'dB')+') and pan: what goes on to '+(g?'the group '+g.name:'the master')});
  st.push({k:'dest',name:'Into '+(g?g.name:'Master'),tip:'What arrives at '+(g?'the group '+g.name:'the master')+'. The master\'s own fader and effects are not in this picture'});return st}
/* measure a track over [b0, b1): {t, b0, b1, steps (with rms, peak, delta), rise, drop} */
async function NI_jourMeasure(tr,b0,b1){const t=typeof tr==='object'?tr:trkById(tr);if(!t)throw new Error('no track');const steps=NI_jourSteps(t),live=[];steps.forEach((s,i)=>{if(s.k==='src'||s.k==='fx'||s.k==='fader')live.push(i)});
  const res=[];for(let i=0;i<live.length;i+=15){const part=live.slice(i,i+15),loc=part.map((_,j)=>i+j);const r=await NI_jourRender(t,b0,b1,steps,loc);res.push(...r)}
  live.forEach((si,j)=>Object.assign(steps[si],res[j]));const fd=steps.find(s=>s.k==='fader');Object.assign(steps[steps.length-1],{rms:fd.rms,peak:fd.peak});
  let last=null,rise=null,drop=null;for(const s of steps){if(s.rms==null||s.k==='dest')continue;if(last!=null&&s.rms>-140&&last>-140){s.delta=s.rms-last;if(s.delta>=3&&(!rise||s.delta>rise.delta))rise=s;if(s.delta<=-3&&(!drop||s.delta<drop.delta))drop=s}if(s.rms!=null)last=s.rms}
  if(rise)rise.big='up';if(drop)drop.big='dn';return{t,id:t.id,b0,b1,steps,rise,drop}}
function NI_jourOpen(tid){const J=NI.jour,z=ZOOM,vw=innerWidth/z,vh=innerHeight/z;if(tid){J.tid=tid;J.follow=false}
  const w=fwin('niJour','Level journey',{x:Math.round(vw*.55),y:Math.round(vh*.14),w:Math.round(Math.min(560,vw*.42)),h:Math.round(Math.min(420,vh*.62))},()=>NI_jourClose(true));
  if(!J.w||J.w!==w){J.w=w;w.querySelector('.fwt').title='The level of one track after each step of its path, from the clip to where it goes';{const c=w.querySelector('.fwc');if(c)c.title='Close the level journey'}
    w.querySelector('.fwb').innerHTML=`<div class="njt"><b class="njtn"></b><label title="Follow the selected track: pick another track and the journey measures it"><input type="checkbox" data-nj="follow"> Follow the selection</label>
      <button data-nj="again" title="Measure this track again">Measure again</button><span class="njst" aria-live="polite"></span></div><div class="njg"></div>
      <div class="njnote">Measured on this track alone, offline: its clips, devices, fader and pan. Sends, sidechains and the master are not in it, and nothing is added to what you hear.</div>`;
    w.querySelector('[data-nj="follow"]').onchange=e=>{J.follow=e.target.checked;if(J.follow&&selT)J.tid=selT;NI_jourRun()};w.querySelector('[data-nj="again"]').onclick=()=>NI_jourRun()}
  if(!tid&&(J.follow||!J.tid))J.tid=selT;w.querySelector('[data-nj="follow"]').checked=J.follow;clearInterval(J.tm);J.tm=setInterval(NI_jourTick,300);NI_jourRun();return w}
function NI_jourClose(fromWin){const J=NI.jour;clearInterval(J.tm);J.tm=0;J.tok++;J.busy=false;if(!fromWin&&J.w)J.w.hidden=true}
function NI_jourKey(){const J=NI.jour,r=NI_jourRange();return J.tid+'|'+r.b0+'|'+r.b1+'|'+NI_sig()}
/* while open: another track selected, the range or the project changed, and the song is stopped: measure again after 0.8 s of quiet */
function NI_jourTick(){const J=NI.jour,w=J.w;if(!w||w.hidden){clearInterval(J.tm);J.tm=0;return}if(J.follow&&selT&&selT!==J.tid){J.tid=selT;J.pend=null;NI_jourRun();return}
  if(play.on||J.busy)return;const k=NI_jourKey();if(k===J.key){J.pend=null;return}if(!J.pend||J.pend.k!==k)J.pend={k,t:performance.now()};else if(performance.now()-J.pend.t>800){J.pend=null;NI_jourRun()}}
async function NI_jourRun(){const J=NI.jour,w=J.w;if(!w||w.hidden)return;const tok=++J.tok,t=J.tid&&trkById(J.tid),st=w.querySelector('.njst'),g=w.querySelector('.njg'),tn=w.querySelector('.njtn');J.key=NI_jourKey();
  if(!t){tn.innerHTML='';g.innerHTML='';st.textContent='Select a track to see its level journey.';J.res=null;return}
  tn.style.setProperty('--c',t.color||'#8b8b97');tn.innerHTML=`<i></i>${esc(t.name)}`;tn.title='The track being measured';
  if(t.kind==='group'||t.kind==='return'){g.innerHTML='';st.textContent=(t.kind==='group'?'A group':'A return')+' gets its sound from other tracks: select one of them.';J.res=null;return}
  if(!(t.clips||[]).some(c=>!c.mute)){g.innerHTML='';st.textContent='This track has no clips to measure.';J.res=null;return}
  const r=NI_jourRange(),a=NI_bb(r.b0),b=NI_bb(r.b1);st.textContent='Measuring…';J.busy=true;J.runs++;
  try{const res=await NI_jourMeasure(t,r.b0,r.b1);if(tok!==J.tok)return;res.how=r.how;J.res=res;NI_jourShow(res);st.textContent=`bars ${a.bar} to ${b.bar-1} (${r.how})`;st.title='The level is the RMS (average power) over these bars; the peak is the highest sample'}
  catch(e){if(tok!==J.tok)return;console.warn('NI level journey',e);st.textContent='Could not measure this track: '+(e&&e.message||e)}finally{if(tok===J.tok)J.busy=false}}
function NI_jourShow(res){const w=NI.jour.w,g=w.querySelector('.njg'),c=res.t.color||'#8b8b97',X=v=>clamp((v-NI_JOUR_LO)/(NI_JOUR_HI-NI_JOUR_LO),0,1)*100,f=v=>v<=-140?'silent':INS.fmt(Math.round(v*10)/10,'dB'),sd=v=>(v>0?'+':v<0?'−':'±')+INS.fmt(Math.abs(Math.round(v*10)/10),'dB');
  let h=`<span class="njh" title="The path from the clip to where the track goes, top to bottom">Step</span><div class="njsc" title="Level in dBFS: 0 is full scale">${[-60,-48,-36,-24,-12,0].map(v=>`<span style="left:${X(v)}%">${v}</span>`).join('')}</div><span class="njh r" title="Average level (RMS) over the bars measured">Level</span><span class="njh r" title="The highest sample">Peak</span><span class="njh r" title="How much this step changed the level">Change</span>`;
  for(const s of res.steps){const off=s.k==='off',has=s.rms!=null;
    h+=`<div class="njnm${off?' njoff':''}" title="${esc(s.tip)}">${esc(s.name)}${s.midi?' <small>MIDI</small>':''}${off?' <small>off</small>':''}</div>`;
    h+=`<div class="njb" style="--c:${c}" title="${has?esc(s.name+': level '+f(s.rms)+', peak '+f(s.peak)):esc(s.tip)}"><s style="left:${X(0)}%"></s>${has&&s.rms>-140?`<i style="width:${X(s.rms)}%"></i><u style="left:${X(s.peak)}%"></u>`:''}</div>`;
    h+=`<span class="njn">${has?f(s.rms):''}</span><span class="njn${has&&s.peak>0?' over':''}"${has&&s.peak>0?' title="Peak above 0 dBFS: fine inside the track, but it clips if it reaches the output this loud"':''}>${has?f(s.peak):''}</span>`;
    h+=`<span class="njd${s.big?' '+s.big:''}"${s.big?` title="${s.big==='up'?'The biggest rise on this path':'The biggest drop on this path'}"`:''}>${s.delta!=null?(s.big==='up'?'▲ ':s.big==='dn'?'▼ ':'')+sd(s.delta):''}</span>`}
  g.innerHTML=h}
NI.jour.open=NI_jourOpen;NI.jour.close=()=>NI_jourClose(false);NI.jour.measure=(id,b0,b1)=>NI_jourMeasure(id,b0,b1);NI.jour.range=NI_jourRange;
NI_HOOKS.levelJourney={open:id=>NI_jourOpen(id),measure:(id,b0,b1)=>NI_jourMeasure(id,b0,b1)};
/* ===== end of lane D NI-7 ===== */
"""
A4 = "/* ===== end of lane D NI-6 ===== */\n"
s = rep(s, A4, A4 + JS.lstrip('\n'))
open(P, 'w', encoding='utf-8').write(s)
print('NI-7 applied')
