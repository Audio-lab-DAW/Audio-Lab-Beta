/* ===================== stem split lanes, step 3 (v0.000, task SG2-3, lane R; the user's pick S1) =====================
   S1: Keep working sends the split to a small card with the orbit (MD1's mdOrb, the real progress), the clip name, a 6 px strip per
   stem (the same columns, one putImageData per strip per chunk), the time left, Open (back to the sheet) and Stop. When it ends it
   says what was added and offers Undo. Lane F's notification stack (OV5's notify) does not exist yet, so the card is drawn here, in
   the job pill's place; when OV5 builds notify({kind,text,action,keep}) lane F puts SG_HOOKS.card(job) (the strips) into its card.
   Lane G: SG_HOOKS.pill(key) gives MD1's pill a 96 x 16 strip of the running split (key 'stem'), or null. */
function sgStrips(host,j,cls){const el=document.createElement('div');el.className=cls||'sgSts';el.innerHTML=j.stems.map(x=>`<div class="sgSs" title="${esc(x.name)}"><canvas></canvas></div>`).join('');host.appendChild(el);
  [...el.querySelectorAll('canvas')].forEach((cv,i)=>sgView(j,cv,i));return el}
function sgDoneText(j){const n=j.added||0;if(!n)return j.lv&&j.pickNull?'Nothing was changed.':'No stem had sound, so nothing was added.';return j.kind==='quick'?'Done. '+n+' stem track'+(n===1?'':'s')+' added below. The original clip is muted. Quick split is approximate: use it for sketching and remixing.':`Done: ${n} neural stem track${n===1?'':'s'} added below. The original clip is muted.`}
function sgCard(j){let c=document.getElementById('sgCard');if(c)c.remove();mdJobEnd('stem');c=document.createElement('div');c.id='sgCard';c.setAttribute('role','status');c.dataset.al='stem.card';j.card=c;
  c.innerHTML=`<div class="sgCt"><span class="sgCo"></span><b></b><button class="sgCx" data-al="stem.card.close" title="Close this card; the split goes on" aria-label="Close">✕</button></div><div class="sgCs"></div><div class="sgRo sgCr"></div>
   <div class="sgCa"><span></span><button data-al="stem.card.open" data-sg="open" title="Show the split's lanes again">Open</button><button data-al="stem.card.stop" data-sg="stop" title="Stop the split: nothing is changed">Stop</button><button data-al="stem.card.undo" data-sg="undo" hidden title="Take the new stem tracks out again">Undo</button></div>`;
  document.body.appendChild(c);sgStrips(c.querySelector('.sgCs'),j);const o=c.querySelector('.sgCo'),b=c.querySelector('b'),ro=c.querySelector('.sgCr'),op=c.querySelector('[data-sg=open]'),st=c.querySelector('[data-sg=stop]'),un=c.querySelector('[data-sg=undo]');let ok=null;
  const f=tickOnly=>{if(!c.isConnected){j.ui.delete(f);sgDrop(j,c);return}if(j.phase==='stop'||j.phase==='err'){sgCardClose(j);return}ro.innerHTML=sgRoHtml(j,true)||'<span class="ph">'+(j.phase==='dl'?'Downloading the model':j.phase==='init'?'Loading the model':'Starting')+'</span>';
    const pl=document.getElementById('mdJob');c.classList.toggle('up',!!(pl&&!pl.hidden));if(tickOnly)return;
    const p=j.phase==='dl'?(j.dl&&j.dl.p)||0:j.phase==='init'||j.phase==='wait'?null:j.phase==='done'?1:j.fin/j.total,k=p==null?'o':'p';if(ok!==k){ok=k;o.innerHTML=mdOrb(24,p,'Stem split progress')}else if(p!=null)mdOrbSet(o,p);
    b.textContent=j.phase==='dl'?'Downloading the stem model':'Splitting “'+j.name+'”';st.hidden=j.phase==='done';op.hidden=j.phase==='done'};
  j.ui.add(f);f();
  c.querySelector('.sgCx').onclick=()=>sgCardClose(j);st.onclick=()=>sgStop(j);
  op.onclick=()=>{sgCardClose(j);j.bg=false;let m=document.getElementById('stq');if(m)m.remove();m=document.createElement('div');m.id='stq';m.className='modal';document.body.appendChild(m);sgSheet(m,j)};
  un.onclick=()=>{if(UNDO.length&&UNDO[UNDO.length-1]===j.undo){undo();toast('The stem tracks were taken out again.')}else toast('Other changes came after the split: use Undo in the Edit menu.');sgCardClose(j)}}
function sgCardClose(j){const c=j.card;j.card=null;if(c){sgDrop(j,c);c.remove()}clearTimeout(j.cardT)}
/* the end of a split sent on with Keep working: the card says what was added (Undo), or the toast as before */
function sgAdded(j){if(!j.card||!j.card.isConnected){toast(sgDoneText(j));return}const c=j.card,n=j.added||0;
  c.querySelector('b').textContent=n?`${n} stem${n===1?'':'s'} added below “${j.under||j.name}”`:'No stem had sound';c.querySelector('.sgCr').innerHTML=n?'<span class="ph">The original clip is muted.</span>':'<span class="ph">Nothing was added.</span>';
  c.querySelector('[data-sg=undo]').hidden=!n;c.querySelector('[data-sg=stop]').hidden=true;c.querySelector('[data-sg=open]').hidden=true;mdOrbSet(c.querySelector('.sgCo'),1);clearTimeout(j.cardT);j.cardT=setTimeout(()=>sgCardClose(j),20000)}
SG_HOOKS.keep=j=>sgCard(j);SG_HOOKS.added=j=>sgAdded(j);
/* for lane F (OV5's notify) and lane G (MD1's pill) */
SG_HOOKS.card=j=>{const d=document.createElement('div');sgStrips(d,j);return d};
SG_HOOKS.pill=key=>{if(key!=='stem')return null;const j=[...SG2.jobs].find(x=>x.bg&&x.phase!=='done');if(!j)return null;const d=document.createElement('span');d.className='sgPs';sgStrips(d,j,'sgSts sgPst');return d};
