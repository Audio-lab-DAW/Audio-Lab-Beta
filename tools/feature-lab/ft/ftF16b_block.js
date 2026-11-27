/* v0.295 (task FT-F16b): Volume shaper, part 2 (starred card F16). The curve can start on the notes of another track (a ghost kick: a muted
   MIDI track whose notes only start the curve) or on the hits of another track's sound (the kick itself, after its effects and before its
   fader, so a muted track still works), and the sound can be split into two or three bands so only the lows follow the curve. Notes are read
   from the song (sample exact, the same live and in an export; notes played live on that track start it too); a sound trigger is found in the
   worklet. Old songs: no new fields, so the curve runs on the bar lines over the whole sound, as before (the same arithmetic, bit-identical).
   New optional fields in f.p: trig ('song', 'note', 'audio'), src (track id; kept in src0 while the curve runs on the bar lines, so the
   track stays free to sleep), nf (one note only, or all), thr (dB), bnd (1, 2, 3), x1 and x2 (Hz), bs ('100': which bands follow the curve). */
Object.assign(FTVS.TIP,{trig:'What starts the curve: the bar lines of the song, every note of another track (a ghost kick), or every hit of another track’s sound.',
  src:'Which track starts the curve. A muted track works too: its notes or its sound still start the curve.',nf:'Start only on one note of that track (the kick of a drum kit), or on every note.',
  thr:'How loud the other track must get to start the curve. Lower it if hits are missed, raise it if quiet sounds start it too.',
  bnd:'Split the sound into bands so only some of them follow the curve, for example only the lows duck under the kick.',
  x1:'Where the low band ends and the next one starts.',x2:'Where the middle band ends and the high band starts.',
  b0:'The low band follows the curve. Off: it passes unchanged.',b1:'The middle band follows the curve. Off: it passes unchanged.',b2:'The high band follows the curve. Off: it passes unchanged.'});
const FTVS_X1=[60,80,100,120,150,200,250,300,400,500],FTVS_X2=[800,1000,1500,2000,2500,3000,4000,5000,8000],FTVS_TH=[-48,-42,-36,-30,-24,-18,-12,-6];
const ftVsHz=f=>f>=1000?(f/1000).toFixed(f%1000?1:0)+' kHz':f+' Hz';
/* the note triggers of a track, in song beats (sorted, each once); cached until the track's clips change */
function ftVsTb(p){if(!p||p.trig!=='note'||!p.src)return[];const t=trkById(p.src);if(!t||!t.clips)return[];const nf=p.nf==null||p.nf===''?-1:+p.nf;
  let sg=nf+'|';for(const c of t.clips)sg+=c.start+','+c.len+','+(c.off||0)+','+(c.mute?1:0)+','+(c.notes?c.notes.length+':'+c.notes.reduce((a,n)=>a+n.s*7+n.p*3+(n.m?1:0),0):'-')+';';
  const C=FTVS_TBC.get(t);if(C&&C.sg===sg)return C.tb;const o=[];
  for(const c of t.clips){if(c.mute||!c.notes)continue;let ns=c.notes;try{ns=ccSus(c,mfxNotes(t,c.notes))}catch(e){}const off=c.off||0;
    for(const n of ns){if(n.m||n.s<off||n.s>=off+c.len)continue;if(nf>=0&&n.p!==nf)continue;o.push(+(c.start+n.s-off).toFixed(9))}}
  o.sort((a,b)=>a-b);const tb=o.filter((b,i)=>!i||b-o[i-1]>1e-6);FTVS_TBC.set(t,{sg,tb});return tb}
/* ---- the sound trigger: the other track after its effects, before its fader (the Ducker's tap) ---- */
const ftVsOwner=f=>{for(const t of S.tracks)if((t.fx||[]).includes(f))return t;return null};
const ftVsSrcOk=(t,s)=>!!(t&&s&&s!==t&&s.kind!=='group'&&!abxReach(t,s));
function ftVsWire(){if(!ctx)return;for(const t of S.tracks){const N=NODES.get(t.id);if(!N)continue;for(const f of t.fx||[]){if(f.type!=='ftvs')continue;const X=N.fxm.get(f.id);if(!X||!X.key)continue;
  const s=f.p&&f.p.trig==='audio'&&f.on?trkById(f.p.src):null,SN=ftVsSrcOk(t,s)?NODES.get(s.id):null,tap=SN&&SN.ut?SN.ut.out:null;if(X.ksrc===tap)continue;
  if(X.ksrc){try{X.ksrc.disconnect(X.key)}catch(e){}}X.ksrc=tap;if(tap)tap.connect(X.key)}}}
{const _sg=syncGraph;syncGraph=function(){const r=_sg.apply(this,arguments);try{ftVsWire()}catch(e){console.error('AudioLab volume shaper',e)}return r}}
/* offline renders: each track's tap is noted while renderMix builds it; the shapers are wired when rendering starts */
const FTVS_OFF=new WeakMap();
{const _mu=mxUtilOff;mxUtilOff=function(oc,t){const r=_mu.apply(this,arguments);try{if(t&&t.id){let m=FTVS_OFF.get(oc);if(!m)FTVS_OFF.set(oc,m=new Map());m.set(t.id,r)}}catch(e){}return r}}
function ftVsWireOff(c,X){try{const p=X.p;if(!p||p.trig!=='audio'||!p.src)return;let f=null,t=null;for(const u of S.tracks)for(const q of u.fx||[])if(q.p===p){f=q;t=u}
  const s=trkById(p.src),m=FTVS_OFF.get(c),tap=m&&m.get(p.src);if(tap&&ftVsSrcOk(t,s))tap.connect(X.key)}catch(e){console.warn('volume shaper trigger',e)}}
/* a render builds a trigger track even when it is not heard */
{const _ak=abxKeys;abxKeys=function(){const s=_ak.apply(this,arguments);try{for(const t of S.tracks)for(const f of t.fx||[])if(f.type==='ftvs'&&f.on&&f.p&&f.p.trig==='audio'&&typeof f.p.src==='string')s.add(f.p.src)}catch(e){}return s}}
/* ---- the transport: the note triggers stop with the song (the curve rests at its end) and come back with it ---- */
function ftVsEach(fn){if(!ctx)return;for(const N of NODES.values())for(const x of N.fxm.values())if(x&&x.tbs!==undefined&&x.resync)fn(x)}
{const _s=start;start=function(){const r=_s.apply(this,arguments);try{setTimeout(()=>ftVsEach(x=>x.resync()),0)}catch(e){}return r}}
{const _t=stop;stop=function(){const r=_t.apply(this,arguments);try{ftVsEach(x=>x.send({on:0}))}catch(e){}return r}}
/* notes played live on the trigger track start the curve at once */
{const _n=noteOn;noteOn=function(pp){const r=_n.apply(this,arguments);try{if(ctx){const ts=liveTracks();if(ts.length)for(const t of S.tracks)for(const f of t.fx||[]){if(f.type!=='ftvs'||!f.on||!f.p||f.p.trig!=='note')continue;
  const nf=f.p.nf==null||f.p.nf===''?-1:+f.p.nf;if(nf>=0&&nf!==pp)continue;if(!ts.some(u=>u.id===f.p.src))continue;const N=NODES.get(t.id),X=N&&N.fxm.get(f.id);if(X&&X.send)X.send({lt:ctx.currentTime})}}}catch(e){}return r}}
/* ---- the device's controls (first in its bar): Start, Track, Notes or Level, Bands, Split, band switches ---- */
function ftVsRow(f){const p=f.p,tg=p.trig||'song',s=p.src?trkById(p.src):null,bn=Math.max(1,Math.min(3,+p.bnd||1)),bs=ftVsBs(p),T=FTVS.TIP,E=esc;
  const sel=(k,lab,opts,cur,tip)=>`<label title="${E(tip)}">${lab} <select data-x="${k}">${opts.map(([v,n])=>`<option value="${v}"${String(cur)===String(v)?' selected':''}>${E(n)}</option>`).join('')}</select></label>`;
  let h=sel('trig','Start',[['song','On the bar lines'],['note','On notes of a track'],['audio','On hits of a track']],tg,T.trig);
  if(tg!=='song'){h+=`<button class="nbtn ftvsrc${s?'':' ftvnone'}" data-nact="src" title="${E(T.src)}">${s?`<i class="ftvd" style="background:${E(s.color||'#888')}"></i>${E(s.name)}`:'Choose a track'}</button>`;
    if(tg==='note'){const nf=p.nf==null||p.nf===''?-1:+p.nf;h+=`<button class="nbtn" data-nact="nf" title="${E(T.nf)}">${nf<0?'Every note':'Only '+E(ftVsNoteName(s,nf))}</button>`}
    else h+=sel('thr','Level',FTVS_TH.map(v=>[v,v+' dB']),isFinite(+p.thr)&&p.thr!=null&&p.thr!==''?+p.thr:-24,T.thr)}
  h+=sel('bnd','Bands',[[1,'Whole sound'],[2,'Two bands'],[3,'Three bands']],bn,T.bnd);
  if(bn>1){h+=sel('x1','Split',FTVS_X1.map(v=>[v,ftVsHz(v)]),+p.x1||150,T.x1);if(bn>2)h+=sel('x2','and',FTVS_X2.map(v=>[v,ftVsHz(v)]),+p.x2||2500,T.x2);
    const nm=bn>2?['Low','Mid','High']:['Low','High'];nm.forEach((n,i)=>{const k=bn>2?i:i*2;h+=`<button class="nbtn ftvb${bs[i]?' on':''}" data-nact="b${i}" aria-pressed="${bs[i]?'true':'false'}" title="${E(T['b'+k]||T.b0)}">${n}</button>`})}
  return`<span class="ftvs2">${h}</span>`}
const ftVsNoteName=(t,n)=>{try{const I=t&&t.inst;if(I&&I.preset==='drums'&&I.pads){const pd=I.pads[n-36];if(pd&&pd.name)return pd.name}}catch(e){}return noteName(n)};
{const _tb=ndTb;ndTb=function(f){let s=_tb.apply(this,arguments);try{if(f&&f.type==='ftvs'){const i=s.indexOf('<div class="ndtb">');if(i>=0)s=s.slice(0,i+18)+ftVsRow(f)+s.slice(i+18);else s+='<div class="ndtb">'+ftVsRow(f)+'</div>'}}catch(e){console.warn('volume shaper row',e)}return s}}
/* the start mode chooses the track: a track is kept in src only while it starts the curve (src makes it keep playing when muted) */
function ftVsNorm(f){const p=f.p,tg=p.trig||'song';if(tg==='song'){if(p.src){p.src0=p.src;delete p.src}return}
  if(!p.src&&p.src0&&trkById(p.src0))p.src=p.src0;const me=ftVsOwner(f);if(p.src&&!ftVsSrcOk(me,trkById(p.src)))delete p.src;
  if(!p.src){const c=S.tracks.filter(q=>ftVsSrcOk(me,q)&&q.kind!=='return'),k=c.find(q=>/ghost/i.test(q.name))||c.find(q=>/kick|\bbd\b/i.test(q.name));if(k)p.src=k.id}}
fxin.addEventListener('change',e=>{const el=e.target;if(!el||!el.dataset||!['trig','bnd','pre'].includes(el.dataset.x))return;const dv=el.closest('.dev'),t=curT(),f=dv&&t&&t.fx.find(q=>q.id===dv.dataset.id);if(!f||f.type!=='ftvs')return;
  setTimeout(()=>{ftVsNorm(f);ftVsApply(f);changed(true)},0)});
function ftVsBtnXY(f,a){const b=fxin.querySelector(`.dev[data-id="${f.id}"] [data-nact="${a}"]`),r=b?b.getBoundingClientRect():{left:200,bottom:200};return[r.left,r.bottom+4]}
Object.assign(NACT.ftvs,{
  src:f=>{const me=ftVsOwner(f),[x,y]=ftVsBtnXY(f,'src'),c=S.tracks.filter(q=>q!==me&&q.kind!=='group');
    openMenu(x,y,[{head:'Which track starts the curve?'},...c.map(q=>{const ok=ftVsSrcOk(me,q);return{label:q.name,dot:q.color,check:f.p.src===q.id,dis:!ok,
      sub:ok?(f.p.trig==='audio'?'Each hit of its sound starts the curve':'Each of its notes starts the curve'):(me?me.name:'This track')+' already plays into '+q.name+', so this would make a loop',
      act:()=>{if(!ok)return;pushUndo();f.p.src=q.id;if(f.p.nf!=null&&f.p.nf!==''&&f.p.trig==='note'){const tb=(q.clips||[]).some(c=>(c.notes||[]).some(n=>n.p===+f.p.nf));if(!tb)delete f.p.nf}ftVsApply(f);changed(true)}}})])},
  nf:f=>{const s=trkById(f.p.src),[x,y]=ftVsBtnXY(f,'nf'),ps=new Set();for(const c of(s&&s.clips)||[])for(const n of c.notes||[])ps.add(n.p);const L=[...ps].sort((a,b)=>a-b);
    openMenu(x,y,[{head:'Which notes start the curve?'},{label:'Every note',check:f.p.nf==null||f.p.nf==='',act:()=>{pushUndo();delete f.p.nf;ftVsApply(f);changed(true)}},
      ...L.map(n=>({label:'Only '+ftVsNoteName(s,n),sub:ftVsNoteName(s,n)!==noteName(n)?noteName(n):'Only this note starts the curve',check:+f.p.nf===n&&f.p.nf!=null&&f.p.nf!=='',act:()=>{pushUndo();f.p.nf=n;ftVsApply(f);changed(true)}}))])},
  b0:f=>ftVsBand(f,0),b1:f=>ftVsBand(f,1),b2:f=>ftVsBand(f,2)});
function ftVsBand(f,i){pushUndo();const bn=Math.max(1,Math.min(3,+f.p.bnd||1)),b=ftVsBs(f.p);/* in two bands the buttons are Low (0) and High (1) */b[i]=b[i]?0:1;f.p.bs=b.join('');void bn;ftVsApply(f);changed(true)}
/* ---- the display: what starts the curve and which band follows it; in Start on hits, the other track's level and the trigger level ---- */
function ftVsCap(p,cn){const tg=p.trig||'song',s=p.src?trkById(p.src):null,bn=Math.max(1,Math.min(3,+p.bnd||1)),bs=ftVsBs(p),x1=+p.x1||150,x2=+p.x2||2500;
  let c=tg==='song'?cn+' per cycle, from the bar line':tg==='note'?cn+' from each note of '+(s?s.name:'(choose a track)'):cn+' from each hit of '+(s?s.name:'(choose a track)');
  if(bn>1){const R=bn>2?['below '+ftVsHz(x1),ftVsHz(x1)+' to '+ftVsHz(x2),'above '+ftVsHz(x2)]:['below '+ftVsHz(x1),'above '+ftVsHz(x1)],on=R.filter((r,i)=>bs[i]);
    c+=on.length===R.length?'':on.length?', only '+on.join(' and '):', no band shaped'}return c}
function ftVsPh(p,X,cb){if(X&&performance.now()-X.tm<300)return X.x>=1?null:X.x;if(!play.on||!ctx)return null;const tg=p.trig||'song',b=curDisp();
  if(tg==='song'){const q=b/cb+(+p.phase||0)/100;return q-Math.floor(q)}
  if(tg==='note'){const tb=ftVsTb(p);let lo=0,hi=tb.length-1,k=-1;while(lo<=hi){const m=(lo+hi)>>1;if(tb[m]<=b){k=m;lo=m+1}else hi=m-1}if(k<0)return null;const q=(b-tb[k])/cb+(+p.phase||0)/100;return q>=1?null:q}
  return null}
function ftVsDrawX(g,w,h,p,X,T,B,x1){if((p.trig||'song')!=='audio')return;const L=lkT(),H=B-T,yv=db=>B-clamp((db+60)/60,0,1)*H,xm=x1-5,live=X&&performance.now()-X.tm<400;
  g.fillStyle='rgba(255,255,255,.06)';g.fillRect(xm,T,4,H);if(live&&X.kl>0){const y=yv(20*Math.log10(Math.max(1e-6,X.kl)));const s=p.src?trkById(p.src):null;g.fillStyle=s&&s.color||L.ok;g.fillRect(xm,y,4,B-y)}
  const th=isFinite(+p.thr)&&p.thr!=null&&p.thr!==''?+p.thr:-24,y=Math.round(yv(th))+.5;g.strokeStyle='#f5c84c';g.lineWidth=1;g.beginPath();g.moveTo(xm-3,y);g.lineTo(x1,y);g.stroke();
  if(X&&X.tr&&performance.now()-X.tr<150){g.fillStyle='rgba(245,200,76,.9)';g.beginPath();g.arc(xm+2,T-8,3,0,7);g.fill()}}
/* the hook: gainAt knows the note triggers too; audio triggers depend on the sound, so gainAt gives null there */
FT_HOOKS.volumeShaper={type:'ftvs',beats:ftVsBeats,triggers:p=>ftVsTb(p).slice(),gainAt:(p,beat)=>{const cb=ftVsBeats(p),ph=(+p.phase||0)/100,d=clamp((p.depth??100)/100,0,1),tg=p.trig||'song',P=p.pts||[];let q;
  if(tg==='audio')return null;if(tg==='note'){const tb=ftVsTb(p);let lo=0,hi=tb.length-1,k=-1;while(lo<=hi){const m=(lo+hi)>>1;if(tb[m]<=beat){k=m;lo=m+1}else hi=m-1}q=k<0?1:Math.min(1,(beat-tb[k])/cb+ph)}
  else{const q0=beat/cb+ph;q=q0-Math.floor(q0)}return 1-d+d*(q>=1&&P.length?+P[P.length-1].y:shEval(P,q,p.smooth))}};
document.head.insertAdjacentHTML('beforeend','<style id="ftvsCss">.ndtb .ftvs2{display:contents}.ndtb .nbtn.ftvb.on{background:var(--c,#3ecf8e);color:#0b0c10;border-color:transparent}.ftvs2 .ftvd{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px;vertical-align:1px}.ftvs2 .ftvnone{color:var(--warn,#f5c84c)}</style>');