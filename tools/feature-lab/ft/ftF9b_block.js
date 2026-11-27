/* v0.278 (task FT-F9b): step sequencer clips, part 2. Ready-made patterns in the step editor (Pattern: Roll K B B B for the psytrance
   bass with the first hit lower, Gallop, Off-beat; on a drum kit Four on the floor and Psy drums). A step clip turns into a normal MIDI
   clip and back (clip menu, the editor's Normal clip button, commands clip.toNotes and clip.toSteps): back is exact when the notes were
   not changed in between, otherwise the notes are read into steps (step size, ratchets, slides, accents, chance, gate) and the editor
   says how many moved. Accented steps always reach Acid's accent (velocity over 0.88) and plain steps on an Acid track stay under it, so
   accent and slide (the note overlaps the next one, which Acid glides into) play as on a 303. A converted clip keeps its notes' chance
   (clip.nch). Push 1's drum step lane edits the pattern of a step clip under the playhead. Psy Bass's own slide is lane L's (hook). */
const FTSQP={key:[['roll','Roll (K B B B)','Psytrance roll on the root: the bass on the three 16ths after each kick, the first of them lower'],
    ['gallop','Gallop (K - B B)','The bass on the last two 16ths of each beat, the first of them lower'],['off','Off-beat (K - B -)','The bass on the off-beat 8th of each beat'],['clear','Clear all','Turn every step off']],
  drums:[['four','Four on the floor','The kick on every beat'],['psy','Psy drums','Kick on every beat, clap on 2 and 4, closed hat on the off-beats'],['clear','Clear all','Turn every step off']]};
Object.assign(FTSQ_TIP,{'Make normal MIDI clip':'Keep the notes as they are and drop the steps. Make step sequencer clip turns it back.',
  'Make step sequencer clip':'Read the notes into a step pattern you can edit step by step. Notes off the steps move to the nearest one.'});
/* velocity of a step: accent adds 25 %; on Acid an accent always crosses its accent line (0.88) and a plain step stays under it */
function ftSqV(lv,ac,acid){let v=Math.min(1,lv+(ac?.25:0));if(ac)v=Math.max(v,.9);else if(acid)v=Math.min(v,.88);return+v.toFixed(4)}
const ftSqAcid=c=>{const f=c&&findClip(c.id);return!!(f&&f.t.inst&&f.t.inst.preset==='acid')};
function ftSqPreset(f,id){const c=f.c,t=f.t,st=c.steps;if(!st||!FTSQP[st.mode].some(p=>p[0]===id))return false;pushUndo();
  if(st.res!==.25&&id!=='clear'){const P0=st.n*st.res;st.res=.25;if(Math.abs(c.len-P0)<1e-6)c.len=st.n*.25}
  ftSqFit(st);st.g=st.rows.map(()=>Array(st.n).fill(null));
  const put=(row,fn)=>{if(row<0||row>=st.rows.length)return;for(let i=0;i<st.n;i++){const q=fn(i%4,i);if(q)st.g[row][i]=q}};let sel=FTSQ.row;
  if(st.mode==='key'){const r=st.rows.length-1;sel=r;
    if(id==='roll')put(r,k=>k===0?null:k===1?{lv:.55}:{});else if(id==='gallop')put(r,k=>k===2?{lv:.6}:k===3?{}:null);else if(id==='off')put(r,k=>k===2?{}:null)}
  else{const P=t.inst&&t.inst.preset==='drums'?ensurePads(t.inst):[],row=(...ty)=>{for(const y of ty){const i=P.findIndex(p=>p&&p.type===y);if(i>=0)return st.rows.findIndex(r=>r.p===36+i)}return-1};
    let kick=row('kick','kd');if(kick<0)kick=0;sel=kick;
    if(id==='four'||id==='psy')put(kick,k=>k===0?{}:null);
    if(id==='psy'){put(row('clap','snare'),(k,i)=>k===0&&(i>>2)%2===1?{}:null);put(row('chat','shaker'),k=>k===2?{lv:.6}:null)}}
  FTSQ.row=sel;ftSqGen(c);changed(false);ftSqPaint();return true}
/* step clip to a normal MIDI clip: the notes stay; the steps are kept aside so turning it back is exact while the notes are unchanged */
function ftSqToNotes(t,c){if(!c||!c.steps)return false;pushUndo();const st=c.steps;if(ftSqClean(c))c.stepsOld=JSON.parse(JSON.stringify(st));else delete c.stepsOld;delete c.steps;
  if(c.notes.some(n=>n.ch!=null&&n.ch<1))c.nch=1;if(FTSQ.id===c.id)ftSqClose();changed(false);toast('This is a normal MIDI clip now. Make step sequencer clip in its menu turns it back.');return true}
/* a normal MIDI clip to a step clip: the notes are read into steps */
function ftSqRead(t,c){const N=(c.notes||[]).filter(n=>n&&isFinite(n.s)&&isFinite(n.p)),acid=!!(t.inst&&t.inst.preset==='acid'),ps=[...new Set(N.map(n=>n.p))].sort((a,b)=>b-a);
  const dr=!!(t.inst&&t.inst.preset==='drums')&&ps.every(p=>p>=36&&p<=51),st={v:1,n:16,res:.25,mode:dr?'drums':'key',oct:3,gate:dr?.5:.85,rows:[],g:[]};
  if(dr)st.rows=ftSqRowsFor(st,t);
  else{if(ps.length>16)return{err:'This clip has '+ps.length+' different notes; a step clip has up to 16 rows.'};let ok=!ps.length;if(ok)st.rows=ftSqRowsFor(st,t);
    for(let o=0;o<=8&&!ok;o++){st.oct=o;st.rows=ftSqRowsFor(st,t);ok=ps.every(p=>st.rows.some(r=>r.p===p))}
    if(!ok){st.oct=3;st.rows=ps.map(p=>({p,nm:nname(p)}));st.cust=1;st.key='Notes of the clip'}}
  /* the step size that fits the most notes: one note at the start of a step, or 2 to 4 hits spread evenly over it (a ratchet) */
  const groups=d=>{const G=new Map();for(const n of N){const i=Math.floor(n.s/d+.02),k=n.p+'|'+i;if(!G.has(k))G.set(k,{p:n.p,i,ns:[]});G.get(k).ns.push(n)}let bad=0;
    for(const g of G.values()){g.ns.sort((a,b)=>a.s-b.s);const m=g.ns.length;if(m>4){bad+=m-1;g.m=1;continue}g.m=m;let ok=true;for(let k=0;k<m;k++)if(Math.abs(g.ns[k].s-(g.i*d+k*d/m))>.01)ok=false;if(!ok){bad+=m;g.m=1}}return{G,bad}};
  let best=null;for(const d of[.25,.125,.5]){const r=groups(d);if(!best||r.bad<best.bad)best=Object.assign(r,{d})}
  const d=best.d,cl=Math.max(d,(c.off||0)+c.len);st.res=d;st.n=FTSQ.NS.find(n=>n*d>=cl-1e-6)||64;st.g=st.rows.map(()=>Array(st.n).fill(null));
  const gl=[];
  for(const g of[...best.G.values()].sort((a,b)=>a.i-b.i)){const r=st.rows.findIndex(x=>x.p===g.p);if(r<0)continue;const j=g.i%st.n;if(j<0||st.g[r][j])continue;const n=g.ns[0],last=g.ns[g.ns.length-1];
    const ac=!!n.ac||acid&&n.v>.88,q={},lv=Math.round(Math.max(.05,Math.min(1,(n.v==null?.8:n.v)-(ac?.25:0)))*100)/100;if(lv!==FTSQ.LV)q.lv=lv;if(ac)q.ac=1;
    if(g.m>1&&g.m===g.ns.length)q.rt=g.m;else if(last.sl||n.l>d*1.001)q.sl=1;else gl.push(n.l/d);if(n.ch!=null&&n.ch<1)q.ch=Math.max(.05,Math.round(n.ch*20)/20);st.g[r][j]=q}
  if(gl.length){gl.sort((a,b)=>a-b);st.gate=Math.round(clamp(gl[gl.length>>1],.05,1)*100)/100}
  return{st}}
function ftSqToSteps(t,c){if(!c||!c.notes||c.steps)return false;if(!t||!t.inst){toast('Step sequencer clips go on instrument tracks.');return false}
  if(c.stepsOld&&c.stepsOld.h===ftSqHash(c.notes)){pushUndo();c.steps=c.stepsOld;delete c.stepsOld;delete c.nch;changed(false);ftSqOpen(c.id);toast('Back to a step sequencer clip, as it was.');return true}
  const R=ftSqRead(t,c);if(R.err){toast(R.err);return false}
  const old=c.notes.map(n=>({p:n.p,s:n.s,l:n.l}));pushUndo();c.steps=R.st;delete c.stepsOld;delete c.nch;ftSqGen(c);
  const key=n=>n.p+'|'+Math.round(n.s*1e4),nw=new Map(c.notes.map(n=>[key(n),n]));let moved=0,len=0;
  for(const n of old){const m=nw.get(key(n));if(!m)moved++;else if(Math.abs(m.l-n.l)>1e-3)len++}
  FTSQ.lastRead={moved,len,before:old.length,after:c.notes.length};changed(false);ftSqOpen(c.id);
  toast(moved||len?'Made a step sequencer clip: '+(moved?moved+' note'+(moved>1?'s':'')+' moved to the steps':'')+(moved&&len?', ':'')+(len?len+' length'+(len>1?'s':'')+' changed':'')+'. Mod+Z undoes it.':'Made a step sequencer clip. The notes are the same.');return true}
function ftSqCmdConv(dir){const f=selC&&findClip(selC);if(!f||!f.c.notes){toast('Select a MIDI clip first.');return}
  if(dir==='notes'){if(!f.c.steps){toast('This clip is already a normal MIDI clip.');return}ftSqToNotes(f.t,f.c)}else{if(f.c.steps){ftSqOpen(f.c.id);return}ftSqToSteps(f.t,f.c)}}
/* the editor: a Pattern menu and a Normal clip button */
{const _b=ftSqBuild;ftSqBuild=function(){const had=!!FTSQ.el,el=_b.apply(this,arguments);try{if(!had&&el){const pr=el.querySelector('.ftsqt [data-a="pr"]');
  if(pr){pr.insertAdjacentHTML('beforebegin','<label title="Write a ready-made pattern over the whole clip (Mod+Z undoes it)">Pattern <select data-a="pat"></select></label>');
    pr.insertAdjacentHTML('afterend','<button type="button" data-a="norm" title="Make this a normal MIDI clip: the notes stay, the steps go. Make step sequencer clip in the clip menu turns it back.">Normal clip</button>')}}}catch(e){console.error('AudioLab steps',e)}return el}}
{const _p=ftSqPaint;ftSqPaint=function(){const r=_p.apply(this,arguments);try{const el=FTSQ.el,f=el&&!el.hidden&&ftSqClip();if(f){const s=el.querySelector('[data-a="pat"]'),m=f.c.steps.mode;
  if(s&&s.dataset.m!==m){s.dataset.m=m;s.innerHTML='<option value="">Choose…</option>'+FTSQP[m].map(([v,l,tp])=>`<option value="${v}" title="${tp}">${l}</option>`).join('')}if(s)s.value='';
  if(f.c.steps.cust){const k=el.querySelector('.ftsqk');if(k){k.textContent='Notes of the clip';k.title='The rows are the notes this clip had. Follow key gives the rows of the key instead.'}}}}catch(e){console.error('AudioLab steps',e)}return r}}
{const _a=ftSqAct;ftSqAct=function(a,val){const f=ftSqClip();if(f){const c=f.c,st=c.steps;
  if(a==='pat'){if(val)ftSqPreset(f,val);return}
  if(a==='norm'){ftSqToNotes(f.t,c);return}
  if(st.cust&&(a==='od'||a==='ou')){const dx=a==='ou'?12:-12;if(!st.rows.every(r=>r.p+dx>=0&&r.p+dx<=127))return;pushUndo();st.rows=st.rows.map(r=>({p:r.p+dx,nm:nname(r.p+dx)}));ftSqGen(c);changed(false);ftSqPaint();return}
  if(a==='fk'&&st.cust){delete st.cust;st.oct=st.oct==null?3:st.oct}
  if(a==='mode'&&st.cust){delete st.cust;st.custK=1}}
  const r=_a.apply(this,arguments);try{const g=ftSqClip();if(g&&a==='mode'&&g.c.steps.custK&&g.c.steps.mode==='key'){g.c.steps.cust=1;delete g.c.steps.custK;ftSqPaint()}}catch(e){}return r}}
/* clip menu: Make normal MIDI clip on a step clip, Make step sequencer clip on a MIDI clip of an instrument track */
{const _om=openMenu;openMenu=function(cx,cy,items){const M=FTSQ.menu;if(M&&M.k==='c'&&M.c&&M.c.notes&&Array.isArray(items)){try{const i=items.findIndex(o=>o&&o.label==='Open in piano roll');if(i>=0){const t=M.t,c=M.c;
    const it=c.steps?{label:'Make normal MIDI clip',sub:'the notes stay, the steps go',act:()=>ftSqToNotes(t,c)}:{label:'Make step sequencer clip',sub:'edit the notes as steps',dis:!t.inst||!!t.frz,act:()=>ftSqToSteps(t,c)};
    items=items.slice(0,i+1).concat([it],items.slice(i+1))}}catch(e){console.error('AudioLab steps',e)}}return _om.call(this,cx,cy,items)}}
/* Push 1's drum step lane: on a step clip it shows and edits the pattern (the steps of the bar under the playhead) */
{const _l=p1bLane;p1bLane=function(t){const L=_l.apply(this,arguments);try{const c=L.c;if(c&&c.steps&&c.steps.mode==='drums'){const st=c.steps;ftSqFit(st);const row=st.rows.findIndex(r=>r.p===L.pd),base=L.B-c.start+(c.off||0),idx=[];
  for(let k=0;k<16;k++){const x=base+k/4,y=x/st.res,i=Math.round(y);let j=-1;if(Math.abs(y-i)<1e-6&&L.B+k/4<c.start+c.len-1e-6)j=((i%st.n)+st.n)%st.n;idx.push(j);L.on[k]=row>=0&&j>=0&&!!st.g[row][j]}
  L.sq={c,row,idx}}}catch(e){console.error('AudioLab steps',e)}return L}}
{const _s=p1bStep;p1bStep=function(t,k){const L=p1bLane(t);if(!L.sq)return _s.apply(this,arguments);const{c,row,idx}=L.sq,j=idx[k];if(row<0||j==null||j<0)return;
  pushUndo();const a=c.steps.g[row];a[j]=a[j]?null:{};ftSqGen(c);changed(false)}}
{const _x=p1bClear;p1bClear=function(t,i){const L=p1bLane({inst:{psel:i},clips:t.clips});if(!L.sq)return _x.apply(this,arguments);const{c,row,idx}=L.sq;if(row<0)return;const a=c.steps.g[row];
  if(!idx.some(j=>j>=0&&a[j]))return;pushUndo();for(const j of idx)if(j>=0)a[j]=null;ftSqGen(c);changed(false)}}
try{for(const k of['nch','stepsOld'])if(Array.isArray(LK.MIDI)&&!LK.MIDI.includes(k))LK.MIDI.push(k)}catch(e){}
FT_HOOKS.stepConvert={toSteps:id=>{const f=findClip(id);return f?ftSqToSteps(f.t,f.c):false},toNotes:id=>{const f=findClip(id);return f?ftSqToNotes(f.t,f.c):false},
  preset:(id,p)=>{const f=findClip(id);return f&&f.c.steps?ftSqPreset(f,p):false},presets:mode=>(FTSQP[mode]||[]).map(p=>({id:p[0],name:p[1],tip:p[2]}))};
