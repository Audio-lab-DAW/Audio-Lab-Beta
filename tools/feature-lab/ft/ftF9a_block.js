/* v0.269 (task FT-F9a): step sequencer clips, part 1. A MIDI clip can carry a step pattern (clip.steps, optional; older projects have
   none): 16, 32 or 64 steps of 1/8, 1/16 or 1/32 over rows that are the drum kit's 16 pads or 8 notes of the key (the piano roll's key,
   or the project key once FT-F11 gives FT_HOOKS.projectKey). Each step has a level, accent, slide, chance and ratchet (1 to 4 hits).
   The pattern writes the clip's notes (repeated over the clip's length), so playback, export, bounce, linked copies and older AudioLab
   versions all play ordinary notes; only chance is decided while playing (a note with ch < 1 plays with that chance; the hits of one
   ratcheted step share the roll). Editor: a window of its own (double-click a step clip, clip menu Edit steps, command clip.editSteps);
   new clips from the track menu (Add step sequencer clip here) or the command clip.newSteps. If the notes were changed in the piano roll,
   the editor says so and only replaces them when a step is edited. Nothing runs while idle: the playing step is drawn only while the
   editor is open and the song plays. Part 2 (FT-F9b): the Roll preset, convert to and from a normal clip, slide into Acid and Psy Bass. */
const FTSQ={id:null,el:null,cv:null,row:0,drag:null,raf:0,iv:0,pr:0,menu:null,memo:new Map(),cur:-1,
  RES:[[.5,'1/8'],[.25,'1/16'],[.125,'1/32']],NS:[16,32,64],LV:.75,LW:112,RH:22,LH:24,
  LANES:[['lv','Level','How loud the step plays. Drag up or down.'],['ac','Accent','Accent: the step plays louder. Click to turn it on or off.'],
    ['sl','Slide','Slide: the note holds into the next step (legato). Click to turn it on or off.'],['ch','Chance','How often the step plays: 100 % always, 50 % every other time on average. Drag up or down.'],
    ['rt','Ratchet','Ratchet: the step plays 1 to 4 quick hits. Click to step through, or drag up or down.']]};
function ftSqKey(){try{if(FT_HOOKS.projectKey){const k=FT_HOOKS.projectKey();if(k&&SCALES[k.scale])return k}}catch(e){}
  return{root:PR.root==null?9:PR.root,scale:PR.scale&&PR.scale!=='none'&&SCALES[PR.scale]?PR.scale:'minor'}}
function ftSqRowsFor(st,t){if(st.mode==='drums'){const P=t&&t.inst&&t.inst.preset==='drums'?ensurePads(t.inst):null;return Array.from({length:16},(_,i)=>({p:36+i,nm:P&&P[i]?P[i].name:nname(36+i)}))}
  const k=ftSqKey(),sc=SCALES[k.scale]||SCALES.minor,L=sc.length,out=[];st.key=NN[k.root]+' '+k.scale;
  for(let i=0;i<8;i++){const p=12*st.oct+k.root+sc[i%L]+12*Math.floor(i/L);out.push({p,nm:nname(p)+(i%L===0?' (root)':'')})}return out.reverse()}
/* the grid always has one row of n steps per row; a longer pattern repeats what is there */
function ftSqFit(st){const R=st.rows.length;st.g=Array.isArray(st.g)?st.g:[];while(st.g.length<R)st.g.push([]);st.g.length=R;
  for(let r=0;r<R;r++){let a=st.g[r];if(!Array.isArray(a))a=st.g[r]=[];const old=a.length;for(let i=old;i<st.n;i++)a[i]=old&&a[i%old]?Object.assign({},a[i%old]):null;a.length=st.n;for(let i=0;i<st.n;i++)if(a[i]===undefined)a[i]=null}}
const ftSqHash=N=>{let h=0;for(const n of N||[]){const s=n.p+','+n.s+','+n.l+','+n.v;for(let i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))|0}return h+':'+(N||[]).length};
const ftSqClean=c=>!!(c&&c.steps&&(c.steps.h==null||c.steps.h===ftSqHash(c.notes)));
/* the pattern writes the clip's notes */
function ftSqGen(c){const st=c&&c.steps;if(!st)return;ftSqFit(st);const d=st.res,P=st.n*d,cov=Math.max(P,(c.off||0)+c.len),reps=Math.max(1,Math.ceil(cov/P-1e-9)),out=[];let gi=0;
  for(let k0=0;k0<reps;k0++)for(let r=0;r<st.rows.length;r++){const p=st.rows[r].p,a=st.g[r];for(let i=0;i<st.n;i++){const q=a[i];if(!q)continue;
    const s0=k0*P+i*d,rt=Math.max(1,Math.min(4,q.rt|0||1)),lv=q.lv==null?FTSQ.LV:q.lv,v=+Math.min(1,lv+(q.ac?.25:0)).toFixed(4),ch=q.ch==null?1:q.ch,g=++gi;
    for(let k=0;k<rt;k++){const n={p,s:+(s0+k*d/rt).toFixed(6),l:+(rt>1?d/rt*.8:q.sl?d*1.05:d*(st.gate||.5)).toFixed(6),v};if(q.ac)n.ac=1;if(q.sl&&k===rt-1)n.sl=1;if(ch<1){n.ch=ch;n.cg=g}out.push(n)}}}
  out.sort((a,b)=>a.s-b.s||a.p-b.p);c.notes=out;st.cov=reps*P;st.h=ftSqHash(out)}
function ftSqNewSteps(t){const dr=!!(t&&t.inst&&t.inst.preset==='drums'),st={v:1,n:16,res:.25,mode:dr?'drums':'key',oct:3,gate:dr?.5:.85,rows:[],g:[]};st.rows=ftSqRowsFor(st,t);ftSqFit(st);return st}
function ftSqAdd(t,beat){if(!t||!t.inst){toast('Step sequencer clips go on instrument tracks. Select one first.');return null}if(t.frz){toast('This track is frozen. Unfreeze it to add clips.');return null}
  pushUndo();const st=ftSqNewSteps(t),b=Math.max(0,Math.floor((beat==null?pos:beat)/4)*4),c=mkClip({start:b,len:st.n*st.res,name:'Steps',notes:[],steps:st});ftSqGen(c);t.clips.push(c);selC=c.id;changed(false);ftSqOpen(c.id);return c}
/* chance is rolled while playing: a note with ch < 1 plays with that chance; the hits of one ratcheted step (same cg) share one roll */
{const _cs=ccSus;ccSus=function(c,notes){const r=_cs.apply(this,arguments);if(!c||!c.steps||!Array.isArray(r))return r;let any=false;for(const n of r)if(n.ch!=null&&n.ch<1){any=true;break}if(!any)return r;
  const now=performance.now(),M=FTSQ.memo;if(M.size>400)for(const[k,m]of M)if(now-m.t>2000)M.delete(k);
  return r.filter(n=>{if(n.ch==null||n.ch>=1)return true;if(n.cg){const k=c.id+':'+n.cg,m=M.get(k);if(m&&now-m.t<400)return m.keep;const keep=Math.random()<n.ch;M.set(k,{t:now,keep});return keep}return Math.random()<n.ch})}}
/* a step clip opens in the step editor; Open in piano roll from the clip menu still reaches the piano roll */
{const _o=openPR;openPR=function(t,c){if(c&&c.steps&&!FTSQ.pr){ftSqOpen(c.id);return}return _o.apply(this,arguments)}}
function ftSqPR(id){const f=findClip(id);if(!f)return;FTSQ.pr=1;try{openPR(f.t,f.c)}finally{FTSQ.pr=0}}
/* a step clip made longer keeps playing its pattern; the editor follows undo and every other change */
{const _c=changed;changed=function(){const r=_c.apply(this,arguments);try{ftSqWatch()}catch(e){console.error('AudioLab steps',e)}return r}}
function ftSqWatch(){for(const id of new Set([selC,FTSQ.id])){if(!id)continue;const f=findClip(id);if(f&&f.c.steps&&f.c.steps.cov!=null&&(f.c.off||0)+f.c.len>f.c.steps.cov+1e-6&&ftSqClean(f.c))ftSqGen(f.c)}if(FTSQ.id)ftSqPaint()}
/* ---- the editor ---- */
function ftSqClip(){const f=FTSQ.id&&findClip(FTSQ.id);return f&&f.c.steps?f:null}
function ftSqBuild(){if(FTSQ.el)return FTSQ.el;const st=document.createElement('style');st.textContent=`
.ftsq{position:fixed;z-index:44;display:flex;flex-direction:column;background:rgba(18,19,24,.97);border:1px solid rgba(255,255,255,.13);border-radius:12px;box-shadow:0 24px 70px rgba(0,0,0,.6);color:#ececf1;font:400 12px Inter,system-ui,sans-serif;max-width:96vw;max-height:92vh}
.ftsq[hidden]{display:none}.ftsqh{display:flex;align-items:center;gap:8px;padding:7px 10px;border-bottom:1px solid rgba(255,255,255,.08);cursor:move;touch-action:none}
.ftsqh b{font-size:13px;font-weight:600}.ftsqh .ftsqn{color:#8b8b97;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.ftsqh .sp{flex:1}
.ftsqh button{min-height:22px;min-width:26px;padding:0 6px}
.ftsqt{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;padding:6px 10px;border-bottom:1px solid rgba(255,255,255,.06)}
.ftsqt label{display:flex;align-items:center;gap:5px;color:#8b8b97}.ftsqt select{min-height:24px;font-size:12px}.ftsqt button{min-height:24px;padding:0 8px;font-size:12px}
.ftsqk{color:#f5c84c;font-weight:600}.ftsqw{margin:6px 10px 0;padding:6px 9px;border-radius:7px;background:rgba(245,200,76,.12);border:1px solid rgba(245,200,76,.35);color:#f3e2b0;display:flex;gap:8px;align-items:center}
.ftsqw[hidden]{display:none}.ftsqw button{min-height:22px;padding:0 8px;font-size:12px}
.ftsqs{overflow:auto;padding:6px 8px 4px}.ftsqs canvas{display:block;touch-action:none;cursor:pointer}
.ftsqhelp{padding:2px 10px 8px;color:#8b8b97;font-size:11px}`;document.head.appendChild(st);
  const el=document.createElement('div');el.id='ftSq';el.className='ftsq';el.hidden=true;el.setAttribute('role','dialog');el.setAttribute('aria-label','Step sequencer');el.tabIndex=-1;
  el.innerHTML=`<div class="ftsqh"><b>Steps</b><span class="ftsqn"></span><span class="sp"></span><button type="button" data-a="x" title="Close the step editor (Esc)" aria-label="Close">✕</button></div>
<div class="ftsqt"><label title="How many steps the pattern has">Steps <select data-a="n">${FTSQ.NS.map(n=>`<option value="${n}">${n}</option>`).join('')}</select></label>
<label title="How long one step is: 1/16 is a sixteenth note">Step <select data-a="res">${FTSQ.RES.map(([v,l])=>`<option value="${v}">${l}</option>`).join('')}</select></label>
<label title="What the rows play: the drum kit's 16 pads, or 8 notes of the key">Rows <select data-a="mode"><option value="drums">Drum pads</option><option value="key">Notes in key</option></select></label>
<span class="ftsqk" title="The key the note rows follow (the piano roll's key). Change the key there, then press Follow key."></span>
<button type="button" data-a="od" title="Note rows one octave lower">Oct −</button><button type="button" data-a="ou" title="Note rows one octave higher">Oct +</button>
<button type="button" data-a="fk" title="Rebuild the note rows from the current key (the steps stay where they are)">Follow key</button>
<button type="button" data-a="clr" title="Turn every step of the selected row off">Clear row</button>
<button type="button" data-a="pr" title="Open the notes in the piano roll. Editing steps here afterwards replaces changes made there.">Piano roll</button></div>
<div class="ftsqw" hidden><span>The notes were changed in the piano roll. Editing a step here writes the pattern again and replaces those changes.</span><button type="button" data-a="re" title="Write the notes from the steps now (Mod+Z undoes it)">Use the steps</button></div>
<div class="ftsqs"><canvas aria-label="Step grid"></canvas></div>
<div class="ftsqhelp">Click a step to turn it on or off, drag to paint. Click a row name to pick the row whose level, accent, slide, chance and ratchet show under the grid.</div>`;
  document.body.appendChild(el);FTSQ.el=el;FTSQ.cv=el.querySelector('canvas');
  el.addEventListener('click',e=>{const b=e.target.closest('button[data-a]');if(!b)return;ftSqAct(b.dataset.a)});
  el.addEventListener('change',e=>{const s=e.target.closest('select[data-a]');if(!s)return;ftSqAct(s.dataset.a,s.value)});
  el.addEventListener('keydown',e=>{if(e.key==='Escape'){e.stopPropagation();ftSqClose()}});
  /* move the window by its title bar */
  const hd=el.querySelector('.ftsqh');hd.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;const r=el.getBoundingClientRect(),z=ZOOM||1,o={x:e.clientX,y:e.clientY,l:r.left/z,t:r.top/z};hd.setPointerCapture(e.pointerId);
    const mv=ev=>{el.style.left=Math.max(0,o.l+(ev.clientX-o.x)/z)+'px';el.style.top=Math.max(0,o.t+(ev.clientY-o.y)/z)+'px'},up=()=>{hd.removeEventListener('pointermove',mv);hd.removeEventListener('pointerup',up)};hd.addEventListener('pointermove',mv);hd.addEventListener('pointerup',up)});
  const cv=FTSQ.cv;cv.addEventListener('pointerdown',ftSqDown);cv.addEventListener('pointermove',ftSqMove);cv.addEventListener('pointerup',ftSqUp);cv.addEventListener('pointercancel',ftSqUp);
  return el}
function ftSqOpen(id){const f=findClip(id);if(!f||!f.c.steps)return false;const el=ftSqBuild(),was=!el.hidden&&FTSQ.id===id;FTSQ.id=id;FTSQ.row=Math.min(FTSQ.row,f.c.steps.rows.length-1);if(!was)FTSQ.row=f.c.steps.mode==='drums'?0:f.c.steps.rows.length-1;
  el.hidden=false;ftSqPaint();if(!was){const r=el.getBoundingClientRect(),z=ZOOM||1;el.style.left=Math.max(8,(innerWidth/z-r.width/z)/2)+'px';el.style.top=Math.max(8,innerHeight/z*.16)+'px'}
  try{el.focus({preventScroll:true})}catch(e){}clearInterval(FTSQ.iv);FTSQ.iv=setInterval(ftSqPlayCheck,250);return true}
function ftSqClose(){if(FTSQ.el)FTSQ.el.hidden=true;FTSQ.id=null;clearInterval(FTSQ.iv);FTSQ.iv=0;cancelAnimationFrame(FTSQ.raf);FTSQ.raf=0;FTSQ.drag=null}
/* the playing step: drawn only while the editor is open and the song plays (30 times a second at most) */
function ftSqPlayCheck(){if(!FTSQ.id||!play.on||FTSQ.raf)return;let last=0;const loop=now=>{if(!FTSQ.id||!play.on){FTSQ.raf=0;FTSQ.cur=-1;ftSqPaint();return}FTSQ.raf=requestAnimationFrame(loop);if(now-last<33)return;last=now;const s=ftSqStepNow();if(s!==FTSQ.cur){FTSQ.cur=s;ftSqPaint()}};FTSQ.raf=requestAnimationFrame(loop)}
function ftSqStepNow(){const f=ftSqClip();if(!f)return-1;const c=f.c,st=c.steps,b=curDisp();if(b<c.start||b>=c.start+c.len)return-1;const P=st.n*st.res,x=((c.off||0)+b-c.start)%P;return Math.floor(x/st.res+1e-9)}
function ftSqGeo(st){const cw=st.n<=16?30:st.n<=32?20:13,R=st.rows.length,gh=R*FTSQ.RH,ly=gh+12;return{cw,R,gh,ly,w:FTSQ.LW+st.n*cw+6,h:ly+FTSQ.LANES.length*FTSQ.LH+4}}
function ftSqPaint(){const el=FTSQ.el;if(!el||el.hidden)return;const f=ftSqClip();if(!f){ftSqClose();return}const c=f.c,t=f.t,st=c.steps;ftSqFit(st);
  el.querySelector('.ftsqn').textContent=t.name+' · '+c.name;const q=a=>el.querySelector(`[data-a="${a}"]`);q('n').value=String(st.n);q('res').value=String(st.res);q('mode').value=st.mode;
  const km=st.mode==='key';for(const a of['od','ou','fk'])q(a).hidden=!km;el.querySelector('.ftsqk').hidden=!km;el.querySelector('.ftsqk').textContent=km?(st.key||''):'';
  el.querySelector('.ftsqw').hidden=ftSqClean(c);
  const G=ftSqGeo(st),cv=FTSQ.cv,dpr=(devicePixelRatio||1)*(ZOOM||1);if(cv.width!==Math.round(G.w*dpr)||cv.height!==Math.round(G.h*dpr)){cv.width=Math.round(G.w*dpr);cv.height=Math.round(G.h*dpr);cv.style.width=G.w+'px';cv.style.height=G.h+'px'}
  const g=cv.getContext('2d');g.setTransform(dpr,0,0,dpr,0,0);g.clearRect(0,0,G.w,G.h);const col=t.color||'#4cc9f0',LW=FTSQ.LW,RH=FTSQ.RH,cw=G.cw;
  g.font='500 11px Inter,system-ui,sans-serif';g.textBaseline='middle';
  for(let r=0;r<G.R;r++){const y=r*RH,sel=r===FTSQ.row,row=st.rows[r];g.fillStyle=sel?'rgba(76,141,255,.22)':r%2?'rgba(255,255,255,.025)':'rgba(255,255,255,.045)';g.fillRect(0,y,LW-4,RH-2);
    if(st.mode==='drums'&&t.inst&&t.inst.preset==='drums'){const P=ensurePads(t.inst)[row.p-36];if(P&&DTYPE[P.type]){g.fillStyle=DTYPE[P.type][1];g.fillRect(0,y,3,RH-2)}}
    g.fillStyle=sel?'#fff':/root/.test(row.nm)?'#f5c84c':'#c9ccd4';g.save();g.beginPath();g.rect(0,y,LW-8,RH);g.clip();g.fillText(row.nm,8,y+RH/2);g.restore();
    for(let i=0;i<st.n;i++){const x=LW+i*cw,on=st.g[r][i],beat=Math.floor(i/4)%2;g.fillStyle=i===FTSQ.cur?'rgba(62,207,142,.28)':beat?'#1a1b21':'#202128';g.fillRect(x+1,y+1,cw-2,RH-4);
      if(on){const lv=on.lv==null?FTSQ.LV:on.lv,ch=on.ch==null?1:on.ch;g.globalAlpha=.35+.65*lv;g.fillStyle=col;const hh=(RH-4)*ch;g.fillRect(x+1,y+1+(RH-4-hh),cw-2,hh);g.globalAlpha=1;
        if(ch<1){g.strokeStyle=col;g.lineWidth=1;g.strokeRect(x+1.5,y+1.5,cw-3,RH-5)}
        if(on.ac){g.fillStyle='#fff';g.fillRect(x+2,y+2,cw-4,2)}
        if(on.sl){g.fillStyle='#fff';g.beginPath();g.moveTo(x+cw-1,y+RH/2-1);g.lineTo(x+cw-6,y+RH/2-5);g.lineTo(x+cw-6,y+RH/2+3);g.closePath();g.fill()}
        const rt=on.rt|0;if(rt>1){g.fillStyle='rgba(0,0,0,.55)';for(let k=1;k<rt;k++)g.fillRect(x+1+(cw-2)*k/rt-.5,y+3,1,RH-8)}}}}
  /* the lanes of the selected row */
  const a=st.g[FTSQ.row]||[],rn=st.rows[FTSQ.row];g.fillStyle='#8b8b97';g.font='600 10px Inter,system-ui,sans-serif';
  FTSQ.LANES.forEach(([k,label],j)=>{const y=G.ly+j*FTSQ.LH;g.fillStyle='rgba(255,255,255,.04)';g.fillRect(0,y,LW-4,FTSQ.LH-3);g.fillStyle='#9a9daa';g.fillText(label+(j===0&&rn?'  ·  '+rn.nm.replace(' (root)',''):''),8,y+FTSQ.LH/2-1);
    for(let i=0;i<st.n;i++){const x=LW+i*cw,on=a[i],H=FTSQ.LH-5;g.fillStyle=i%4?'#17181d':'#1c1d23';g.fillRect(x+1,y,cw-2,H);if(!on)continue;g.fillStyle=col;
      if(k==='lv'||k==='ch'){const v=on[k]==null?(k==='lv'?FTSQ.LV:1):on[k];g.globalAlpha=.85;g.fillRect(x+2,y+H-H*v,cw-4,H*v);g.globalAlpha=1}
      else if(k==='ac'||k==='sl'){g.globalAlpha=on[k]?1:.25;g.beginPath();g.arc(x+cw/2,y+H/2,Math.min(4,cw/3),0,7);g.fill();g.globalAlpha=1}
      else{const rt=on.rt|0||1;g.fillStyle=rt>1?'#fff':'#8b8b97';g.textAlign='center';g.fillText(String(rt),x+cw/2,y+H/2+1);g.textAlign='left'}}})}
function ftSqHit(e){const f=ftSqClip();if(!f)return null;const st=f.c.steps,G=ftSqGeo(st),r=FTSQ.cv.getBoundingClientRect(),z=ZOOM||1,x=(e.clientX-r.left)/z,y=(e.clientY-r.top)/z;
  const i=Math.floor((x-FTSQ.LW)/G.cw);if(y<G.gh){const row=Math.floor(y/FTSQ.RH);if(row<0||row>=G.R)return null;return x<FTSQ.LW?{k:'label',row}:i>=0&&i<st.n?{k:'cell',row,i}:null}
  if(y>=G.ly){const j=Math.floor((y-G.ly)/FTSQ.LH);if(j<0||j>=FTSQ.LANES.length)return null;const fr=1-((y-G.ly-j*FTSQ.LH)/(FTSQ.LH-5));return x>=FTSQ.LW&&i>=0&&i<st.n?{k:'lane',lane:FTSQ.LANES[j][0],j,i,v:clamp(fr,0,1)}:{k:'lanelabel',j}}return null}
function ftSqEdit(fn){const f=ftSqClip();if(!f)return;if(!FTSQ.drag||!FTSQ.drag.pushed){pushUndo();if(FTSQ.drag)FTSQ.drag.pushed=1}fn(f.c.steps,f.c);ftSqGen(f.c);if(!FTSQ.drag)changed(false);else dirty=true;ftSqPaint()}
function ftSqDown(e){const H=ftSqHit(e);if(!H)return;e.preventDefault();FTSQ.cv.setPointerCapture(e.pointerId);
  if(H.k==='label'){FTSQ.row=H.row;ftSqPaint();return}if(H.k!=='cell'&&H.k!=='lane')return;
  const f=ftSqClip(),st=f.c.steps;FTSQ.drag={k:H.k,pushed:0};
  if(H.k==='cell'){FTSQ.row=H.row;FTSQ.drag.on=!st.g[H.row][H.i];ftSqCell(H)}
  else{const on=st.g[FTSQ.row]&&st.g[FTSQ.row][H.i];if(!on){FTSQ.drag=null;return}FTSQ.drag.lane=H.lane;FTSQ.drag.y0=e.clientY;FTSQ.drag.rt0=on.rt|0||1;
    if(H.lane==='ac'||H.lane==='sl')FTSQ.drag.on=!on[H.lane];ftSqLane(H,e,true)}}
function ftSqCell(H){const D=FTSQ.drag;ftSqEdit(st=>{const a=st.g[H.row];if(D.on){if(!a[H.i])a[H.i]={}}else a[H.i]=null})}
function ftSqLane(H,e,first){const D=FTSQ.drag,L=D.lane;const st=ftSqClip().c.steps,on=st.g[FTSQ.row][H.i];if(!on)return;
  ftSqEdit(()=>{if(L==='lv'){on.lv=Math.round(Math.max(.05,H.v)*100)/100;if(on.lv===FTSQ.LV)delete on.lv}else if(L==='ch'){on.ch=Math.round(Math.max(.05,H.v)*20)/20;if(on.ch>=1)delete on.ch}
    else if(L==='ac'||L==='sl'){if(D.on)on[L]=1;else delete on[L]}else if(L==='rt'){const v=first?(D.rt0%4)+1:clamp(Math.round(D.rt0+(D.y0-e.clientY)/12),1,4);D.cyc=first?v:D.cyc;if(v>1)on.rt=v;else delete on.rt}})}
function ftSqMove(e){const H=ftSqHit(e),D=FTSQ.drag;
  if(!D){FTSQ.cv.title=ftSqTip(H);return}
  if(D.k==='cell'&&H&&H.k==='cell'){const st=ftSqClip().c.steps;if(!!st.g[H.row][H.i]!==D.on)ftSqCell(H)}
  else if(D.k==='lane'&&H&&H.k==='lane'){if(D.lane==='rt'){if(Math.abs(e.clientY-D.y0)>6)ftSqLane(H,e,false)}else ftSqLane(H,e,false)}}
function ftSqUp(){const D=FTSQ.drag;FTSQ.drag=null;if(D&&D.pushed)changed(false)}
function ftSqTip(H){const f=ftSqClip();if(!H||!f)return'';const st=f.c.steps;
  if(H.k==='label')return st.rows[H.row].nm+': click to show its level, accent, slide, chance and ratchet under the grid';
  if(H.k==='cell'){const on=st.g[H.row][H.i];return st.rows[H.row].nm+', step '+(H.i+1)+': '+(on?'on. Click to turn it off.':'off. Click to turn it on, drag to paint.')}
  if(H.k==='lane'||H.k==='lanelabel'){const L=FTSQ.LANES[H.j];return L[1]+(H.k==='lane'?', step '+(H.i+1):'')+': '+L[2]}return''}
function ftSqAct(a,val){const f=ftSqClip();if(a==='x'){ftSqClose();return}if(!f)return;const c=f.c,t=f.t,st=c.steps;
  if(a==='pr'){ftSqPR(c.id);return}
  if(a==='re'){pushUndo();ftSqGen(c);changed(false);toast('The notes come from the steps again.');return}
  pushUndo();
  if(a==='n'){const n=+val,P0=st.n*st.res;if(!FTSQ.NS.includes(n))return;st.n=n;ftSqFit(st);if(Math.abs(c.len-P0)<1e-6)c.len=st.n*st.res}
  else if(a==='res'){const v=+val,P0=st.n*st.res;if(!FTSQ.RES.some(r=>r[0]===v))return;st.res=v;if(Math.abs(c.len-P0)<1e-6)c.len=st.n*st.res}
  else if(a==='mode'){if(val!=='drums'&&val!=='key')return;st.keep=st.keep||{};st.keep[st.mode]={rows:st.rows,g:st.g};st.mode=val;const k=st.keep[val];st.gate=val==='drums'?.5:.85;
    if(k){st.rows=k.rows;st.g=k.g}else{st.rows=ftSqRowsFor(st,t);st.g=[]}delete st.keep[val];FTSQ.row=val==='drums'?0:st.rows.length-1}
  else if(a==='od'||a==='ou'){st.oct=clamp((st.oct==null?3:st.oct)+(a==='ou'?1:-1),0,8);st.rows=ftSqRowsFor(st,t)}
  else if(a==='fk'){st.rows=ftSqRowsFor(st,t)}
  else if(a==='clr'){const r=st.g[FTSQ.row];if(r)r.fill(null)}
  ftSqFit(st);FTSQ.row=Math.min(FTSQ.row,st.rows.length-1);ftSqGen(c);changed(false);ftSqPaint()}
/* menus: Add step sequencer clip here (instrument tracks), Edit steps on a step clip */
{const _tm=trackMenu;trackMenu=function(x,y,t,beat){FTSQ.menu={k:'t',t,beat};try{return _tm.apply(this,arguments)}finally{FTSQ.menu=null}}}
{const _cm=clipMenu;clipMenu=function(x,y,t,c){FTSQ.menu={k:'c',t,c};try{return _cm.apply(this,arguments)}finally{FTSQ.menu=null}}}
const FTSQ_TIP={'Add step sequencer clip here':'A new clip with a 16-step pattern: drum pads on a drum kit, notes of the key on other instruments.',
  'Edit steps…':'Open the step editor of this clip.','Open in piano roll':'Edit the notes themselves. Editing steps afterwards writes the pattern again and replaces changes made there.'};
{const _om=openMenu;openMenu=function(cx,cy,items){const M=FTSQ.menu;if(M&&Array.isArray(items)){FTSQ.menu=null;try{
    if(M.k==='t'&&M.t.inst){const i=items.findIndex(o=>o&&o.label==='Add MIDI clip here');if(i>=0)items=items.slice(0,i+1).concat([{label:'Add step sequencer clip here',sub:'16 steps of drums or notes',dis:!!M.t.frz,act:()=>ftSqAdd(M.t,M.beat)}],items.slice(i+1))}
    if(M.k==='c'&&M.c.steps){const i=items.findIndex(o=>o&&o.label==='Open in piano roll');if(i>=0){const id=M.c.id;items=items.slice(0,i).concat([{label:'Edit steps…',act:()=>ftSqOpen(id)},Object.assign({},items[i],{sub:'edit the notes; steps edited later replace them',act:()=>ftSqPR(id)})],items.slice(i+1))}}
  }catch(e){console.error('AudioLab steps',e)}}const r=_om.call(this,cx,cy,items);try{if(M){const m=document.getElementById('ctxm');if(m)for(const bt of m.querySelectorAll('button')){const l=bt.querySelector('.mlab'),tx=(l&&l.childNodes[0]?l.childNodes[0].textContent:bt.textContent).trim();if(FTSQ_TIP[tx]&&(tx!=='Open in piano roll'||M.k==='c'&&M.c.steps))bt.title=FTSQ_TIP[tx]}}}catch(e){}return r}}
function ftSqCmdNew(){const t=S.tracks.find(q=>q.id===selT);if(!t||!t.inst){toast('Select an instrument track first: step sequencer clips go on instrument tracks.');return}ftSqAdd(t,play.on?curDisp():pos)}
function ftSqCmdEdit(){const f=selC&&findClip(selC);if(!f||!f.c.steps){toast('Select a step sequencer clip first (add one from a track’s right-click menu).');return}ftSqOpen(f.c.id)}
/* linked copies of a step clip share the pattern too */
try{if(Array.isArray(LK.MIDI)&&!LK.MIDI.includes('steps'))LK.MIDI.push('steps')}catch(e){}
FT_HOOKS.stepClip=c=>c&&c.steps?{n:c.steps.n,res:c.steps.res,mode:c.steps.mode,edited:!ftSqClean(c)}:null;
FT_HOOKS.stepEditor={open:id=>ftSqOpen(id),close:()=>ftSqClose(),paint:()=>ftSqPaint(),add:(trackId,beat)=>ftSqAdd(S.tracks.find(t=>t.id===trackId),beat),gen:id=>{const f=findClip(id);if(f)ftSqGen(f.c)}};
