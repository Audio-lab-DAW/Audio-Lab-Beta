/* ===================== stem split lanes, step 2 (v0.000, task SG2-2, lane R; the user's picks G1, P1, F1) =====================
   G1: the Split sheet stays open after Split and becomes the loading bar: the mix's spectrogram faint on top (drawn at once, no model
   needed), then one lane per stem in viridis (INS.cmap, lane E), filled at the true song position as each chunk lands. An amber
   hairline edge (--unit, --lk-hair) marks the last final sample; the read-out row uses L2 (values in ink, units in amber small caps).
   P1: the draft stretch of a chunk (its last 1.95 s, cross-faded with the next chunk) is drawn at half strength and repainted.
   F1: a soft CSS scan over the chunk being worked on; a still hatch under Reduce motion, Motion "Signal only" or Light mode.
   Nothing runs per frame: one putImageData dirty rectangle per lane per chunk, the edge moves by a 120 ms CSS transition (0 with
   Reduce motion), the read-out changes once a second while a split runs. When it ends each lane shows its level and a tick
   (silent stems unticked) and "Add N tracks" makes them. Keep working closes the sheet; the split goes on (card in SG2-3).
   Jobs: sgJob(o) -> job {kind, name, of, stems:[{name,col,k}], ns, cw, total, phase, n, done, fin, pe, work, mix, cols, st, runs};
   sgLanes(host, job) draws the layout into host and returns its element; sgJobCols(job,msg) takes a {t:'cols'} message. */
function sgReduce(){const B=document.body.classList;return B.contains('lite')||B.contains('lkm1')||B.contains('fxstill')||matchMedia('(prefers-reduced-motion: reduce)').matches}
function sgFmt(s){s=Math.max(0,s);const m=Math.floor(s/60),r=s-m*60;return m+':'+(r<10?'0':'')+r.toFixed(1)}
function sgFmt0(s){s=Math.max(0,Math.round(s));return Math.floor(s/60)+':'+String(s%60).padStart(2,'0')}
function sgJob(o){const quick=o.kind==='quick',sr=quick?o.sr:44100,total=quick?o.len:Math.ceil(o.len*44100/o.sr),N=343980,ST=N-Math.floor(N/4);
  const j=Object.assign({phase:'wait',done:0,fin:0,pe:0,work:null,mix:null,cols:null,st:null,cw:0,runs:[],t0:performance.now(),lastAt:performance.now(),views:new Set(),ui:new Set(),dl:null,tick:0,bg:false},o);
  j.sr=sr;j.total=total;j.ns=j.stems.length;j.n=quick?Math.ceil(total/(1<<18)):Math.max(1,Math.ceil(total/ST));j.ST=quick?(1<<18):ST;j.N=quick?(1<<18):N;j.mb=quick?0:NEUM[o.kind].mb;
  SG2.jobs.add(j);return j}
function sgSetCw(j,cw){j.cw=Math.max(64,Math.min(2048,Math.round(cw)||512));j.cols=new Uint8Array(j.ns*96*j.cw);j.st=new Uint8Array(j.cw)}
function sgLut(){return SG2.lut||(SG2.lut=INS.cmap('viridis'))}
/* alpha per level, as on the pick page: quiet bins fade into the lane's dark background (the stems in viridis, the mix a faint grey) */
function sgAlpha(){if(!SG2.al){const a=new Uint8Array(256),m=new Uint8Array(256);for(let v=0;v<256;v++){a[v]=Math.round(Math.min(1,v/255*1.7)*255);m[v]=Math.round(Math.pow(v/255,1.2)*.5*255)}SG2.al=[a,m]}return SG2.al}
/* one dirty rectangle: columns c0..c1 of lane si (-1 = the mix) into the view's canvas */
function sgPaint(j,v,c0,c1){c0=Math.max(0,c0);c1=Math.min(j.cw,c1);const w=c1-c0;if(w<=0||!v.g)return;const im=v.g.createImageData(w,96),o=im.data,L=sgLut(),cw=j.cw,mix=v.si<0,src=mix?j.mix:j.cols,base=mix?0:v.si*96*cw,draft=!document.body.classList.contains('lite');
  if(!src)return;const[AS,AM]=sgAlpha();for(let c=0;c<w;c++){const cc=c0+c,s=mix?2:j.st[cc];if(!s||(s===1&&!draft))continue;for(let r=0;r<96;r++){const v=src[base+r*cw+cc],p=(r*w+c)*4;
    if(mix){o[p]=o[p+1]=o[p+2]=215;o[p+3]=AM[v]}else{const q=v*3;o[p]=L[q];o[p+1]=L[q+1];o[p+2]=L[q+2];o[p+3]=s===2?AS[v]:AS[v]>>1}}}
  v.g.putImageData(im,c0,0)}
function sgView(j,cv,si){cv.width=j.cw;cv.height=96;const v={cv,si,g:cv.getContext('2d')};j.views.add(v);sgPaint(j,v,0,j.cw);return v}
function sgDrop(j,root){for(const v of[...j.views])if(!v.cv.isConnected||(root&&root.contains(v.cv)))j.views.delete(v)}
function sgJobCols(j,m){const c0=m.fin[0],c2=m.prov[1],n=c2-c0;if(n>0&&j.cols)for(let s=0;s<j.ns;s++)for(let r=0;r<96;r++)j.cols.set(m.cols.subarray((s*96+r)*n,(s*96+r+1)*n),(s*96+r)*j.cw+c0);
  if(j.st){j.st.fill(2,m.fin[0],m.fin[1]);j.st.fill(1,m.prov[0],m.prov[1])}
  const now=performance.now();if(j.phase==='run')j.runs.push(now-j.lastAt);j.lastAt=now;j.phase=m.i+1>=m.n?'fin':'run';j.done=m.i+1;j.n=m.n;j.fin=m.s1;j.pe=m.pe;
  j.work=m.i+1>=m.n?null:[m.s1,Math.min(j.total,m.s1+j.ST)];
  sgDrop(j);for(const v of j.views)if(v.si>=0)sgPaint(j,v,c0,c2);try{SG_HOOKS.onChunk(j,m)}catch(e){console.warn('SG_HOOKS.onChunk',e)}sgUpd(j)}
function sgPhase(j,ph,x){if(ph==='dl'){j.phase='dl';j.dl=x}else if((ph==='init'||ph==='cached')&&j.phase!=='init'){j.phase='init'}else if(ph==='run'&&j.phase!=='run'&&j.phase!=='fin'){j.phase='run';j.lastAt=performance.now();if(!j.work)j.work=[0,Math.min(j.total,j.ST)]}else return;sgUpd(j)}
function sgUpd(j){for(const f of[...j.ui])try{f()}catch(e){console.warn('stem split view',e)}
  const run=j.phase!=='done'&&j.phase!=='err'&&j.phase!=='stop';if(run&&!j.tick)j.tick=setInterval(()=>{if(!j.ui.size)return;for(const f of j.ui)try{f(1)}catch(e){}},1000);if(!run&&j.tick){clearInterval(j.tick);j.tick=0}}
function sgEnd(j,ph){j.phase=ph;sgUpd(j);if(ph!=='done')SG2.jobs.delete(j);if(j.tick){clearInterval(j.tick);j.tick=0}
  if(ph==='done'&&j.runs.length){const m=j.runs.slice(-3).reduce((a,b)=>a+b,0)/Math.min(3,j.runs.length)/1000;UI.sgRate=Object.assign({},UI.sgRate,{[j.kind]:+m.toFixed(3)});saveUI()}}
/* remaining time: the mean of the last three chunks times the chunks left; before the first chunk this computer's last speed for the model */
function sgEta(j){if(j.phase==='done'||j.phase==='fin'||j.phase==='err'||j.phase==='stop')return null;const now=performance.now(),left=j.n-j.done;
  let m=j.runs.length?j.runs.slice(-3).reduce((a,b)=>a+b,0)/Math.min(3,j.runs.length):null,from='';if(m==null){const r=UI.sgRate&&UI.sgRate[j.kind];if(!r)return{ms:null};m=r*1000;from='last'}
  let rem=left*m;if(j.phase==='run')rem-=Math.min(m*.9,now-j.lastAt);return{ms:Math.max(0,rem),from}}
const sgU=t=>`<span class="lku">${t}</span>`;
function sgRoHtml(j,short){const pos=j.fin/j.total*(j.total/j.sr),len=j.total/j.sr,E=sgEta(j),q=j.kind==='quick';let ph='';
  if(j.phase==='dl')ph=`<span class="ph">Downloading the model (first time only)</span><span>${Math.round((j.dl&&j.dl.mb)||0)} / ${j.mb}${sgU('MB')}</span>`;
  else if(j.phase==='init')ph=`<span class="ph">Loading the model</span>`;else if(j.phase==='wait')ph=`<span class="ph">Starting</span>`;
  else if(j.phase==='done'||j.phase==='fin')ph=`<span class="ph">Done</span>`;else if(j.phase==='stop')ph=`<span class="ph">Stopped</span>`;
  const ch=j.phase==='dl'||j.phase==='init'||j.phase==='wait'?'':`<span>${j.done} / ${j.n}${sgU(q?'blocks':'chunks')}</span>`,cl=j.of?`<span>clip ${j.of.i} of ${j.of.n}</span>`:'';
  const e=!E?'':E.ms==null?`<span class="ph">estimating…</span>`:`<span>≈ ${sgFmt0(E.ms/1000)}${sgU('left')}</span>${E.from==='last'&&!short?'<span class="ph">from your last split</span>':''}`;
  if(short)return`${cl}${ch}${e}`;return`${cl}${ph}${ch}<span>${sgFmt(pos)} / ${sgFmt(len)}${sgU('s')}</span>${j.phase==='done'||j.phase==='fin'?`<span>${j.ns}${sgU(j.ns===1?'stem':'stems')}</span>`:e}`}
/* the layout G1: read-out, mix lane, stem lanes, the edge and the chunk at work over the lane column, the time axis */
function sgLanes(host,j,o){o=o||{};const el=document.createElement('div');el.className='sgL'+(j.ns>4?' n6':'')+(sgReduce()?' still':'');el.dataset.al='stem.lanes';
  const len=j.total/j.sr,ax=[0,.25,.5,.75,1].map(f=>`<span>${sgFmt0(f*len)}</span>`).join('');
  el.innerHTML=`<div class="sgRo" aria-live="off"></div><div class="sgCol"><div class="sgLn mix"><div class="sgNm"><em>MIX</em></div><div class="sgCv"><canvas></canvas></div></div>
   ${j.stems.map((x,i)=>`<div class="sgLn" data-s="${i}"><div class="sgNm" title="${esc(x.name)}"><i style="background:${x.col}"></i>${esc(x.name)}</div><div class="sgCv"><canvas></canvas><span class="sgLv" hidden></span></div></div>`).join('')}
   <div class="sgOv"><div class="sgWork" hidden></div><div class="sgEdge" hidden><b></b></div></div></div><div class="sgAx">${ax}</div>
   <div class="sgSub">${o.sub||(j.kind==='quick'?'Quick split, built in. Each block is final when it is done.':'HTDemucs v4 by Meta on this computer. You can keep working; Stop changes nothing.')}</div>`;
  host.appendChild(el);if(!j.cw){const r=el.querySelector('.sgLn[data-s] .sgCv').getBoundingClientRect();sgSetCw(j,(r.width||440)*(window.devicePixelRatio||1))}
  const cvs=[...el.querySelectorAll('.sgCv canvas')];sgView(j,cvs[0],-1);cvs.slice(1).forEach((cv,i)=>sgView(j,cv,i));
  const ro=el.querySelector('.sgRo'),ed=el.querySelector('.sgEdge'),wk=el.querySelector('.sgWork'),lv=[...el.querySelectorAll('.sgLv')];
  const f=tickOnly=>{if(!el.isConnected){j.ui.delete(f);sgDrop(j,el);return}ro.innerHTML=sgRoHtml(j,false);if(tickOnly)return;
    const fin=j.phase==='done'||j.phase==='fin',fr=j.fin/j.total;ed.hidden=fin||(!j.done&&j.phase!=='run');ed.style.left=(fr*100)+'%';ed.firstElementChild.textContent=sgFmt(j.fin/j.sr);
    wk.hidden=!j.work||fin||j.phase==='err'||j.phase==='stop';if(j.work){wk.style.left=(j.work[0]/j.total*100)+'%';wk.style.width=Math.max(0,(j.work[1]-j.work[0])/j.total*100)+'%'}
    el.classList.toggle('still',sgReduce());if(j.phase==='done'&&j.lv)j.lv.forEach((d,i)=>{const s=lv[i];if(!s)return;s.hidden=false;s.textContent=d<-60?'silent':d.toFixed(1)+' dB'})};
  j.ui.add(f);f();return el}
/* the Split sheet after Split: lanes, Keep working / Stop / Add N tracks */
function sgSheet(m,j){m.dataset.sg='1';const eng=j.kind==='quick'?'Quick split':'HTDemucs · '+j.ns+(j.ns===1?' stem':' stems');
  m.innerHTML=`<div class="sheet sgSh" role="dialog" aria-label="Split into stems" style="width:min(580px,94vw)"><div class="sh"><b>Split “${esc(j.name)}”</b><span class="sgEn">${esc(j.kind==='quick'?eng:(j.kind==='n6'?'HTDemucs 6 stems':'HTDemucs 4 stems'))}</span></div><div class="impb sgB"></div>
   <div class="sf"><button id="sgKeep" data-al="stem.keepWorking" title="Close this window and go on working; the split goes on and tells you when it is done">Keep working</button><span></span><button id="sgStop" data-al="stem.stop" title="Stop the split: nothing is changed">Stop</button><button id="sgDiscard" data-al="stem.discard" hidden title="Close without adding the stems: nothing is changed">Discard</button><button id="sgAdd" class="pri" data-al="stem.add" disabled title="Add the ticked stems as new tracks below the clip (one undo step)">Add stems</button></div></div>`;
  j.sheet=m;sgLanes(m.querySelector('.sgB'),j);const add=m.querySelector('#sgAdd'),stop=m.querySelector('#sgStop'),keep=m.querySelector('#sgKeep'),dis=m.querySelector('#sgDiscard');
  const f=()=>{if(!m.isConnected){j.ui.delete(f);return}const d=j.phase==='done';add.disabled=!d;stop.hidden=d;dis.hidden=!d;keep.hidden=d;const n=j.on?j.on.filter(Boolean).length:0;add.textContent=d?`Add ${n} track${n===1?'':'s'}`:'Add stems';add.disabled=!d||!n;
    if(d&&!m.querySelector('.sgCk'))m.querySelectorAll('.sgLn[data-s]').forEach(r=>{const i=+r.dataset.s,c=document.createElement('input');c.type='checkbox';c.className='sgCk';c.dataset.al='stem.lane.keep';c.checked=!!j.on[i];c.title='Add '+j.stems[i].name+' as a track';c.setAttribute('aria-label','Add '+j.stems[i].name);
      c.onchange=()=>{j.on[i]=c.checked;r.classList.toggle('off',!c.checked);f()};r.classList.toggle('off',!c.checked);r.querySelector('.sgCv').appendChild(c)})};
  j.ui.add(f);f();
  keep.onclick=()=>sgKeep(j);stop.onclick=()=>sgStop(j);dis.onclick=()=>{if(j.pick)j.pick(null)};add.onclick=()=>{if(j.pick&&j.on)j.pick(j.on.map((v,i)=>v?i:-1).filter(i=>i>=0))};
  m.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();if(j.phase!=='done')sgKeep(j)}});setTimeout(()=>{if(m.isConnected)keep.focus()},30)}
function sgStop(j){if(j.kind==='quick')sgStopQuick();else sgStopNeural()}
/* Keep working: the sheet goes away, the split goes on; SG_HOOKS.keep(job) shows it elsewhere (S1, step 3), else the job pill */
function sgKeep(j){if(j.bg)return;j.bg=true;if(j.sheet){sgDrop(j,j.sheet);j.sheet.remove();j.sheet=null}if(SG_HOOKS.keep)SG_HOOKS.keep(j);else sgPill(j)}
function sgPill(j){const f=()=>{if(!j.bg||j.card){j.ui.delete(f);return}if(j.phase==='dl')mdJob('stem',`Downloading the stem model, ${j.mb} MB (only the first time)`,j.dl?j.dl.p:0);else if(j.phase==='init')mdJob('stem','Loading the stem model',null);
    else if(j.phase==='run'||j.phase==='fin')mdJob('stem',j.kind==='quick'?'Splitting into stems':'Separating with HTDemucs',j.done/j.n);else{mdJobEnd('stem');j.ui.delete(f)}};j.ui.add(f);f()}
function sgLevels(bufs){return bufs.map(b=>{let pk=0;for(let ch=0;ch<b.numberOfChannels;ch++){const d=b.getChannelData(ch);for(let k=0;k<d.length;k+=3){const v=Math.abs(d[k]);if(v>pk)pk=v}}return 20*Math.log10(Math.max(pk,1e-6))})}
/* several clips dropped with "the same for the other files": the read-out says clip 2 of 3 */
{const f=importFiles;importFiles=async function(files){const n=[...(files||[])].filter(x=>/^audio\//.test(x.type)||/\.(wav|mp3|aif|aiff|flac|m4a|ogg)$/i.test(x.name)).length;SG2.batch=n>1?{n,k:0}:null;try{return await f.apply(this,arguments)}finally{SG2.batch=null}}}
