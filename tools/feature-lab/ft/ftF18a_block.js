/* v0.315 (task FT-F18a): Kick and bass lab, part 1 (starred card F18). Lane D's lab (NI-2a analysis, NI-2b card) already shows the kick's
   note, the song key, the clash and the gap. This adds one row under its words through NI_HOOKS.kickBassView.addRow, with what the lab
   did not have yet:
   - Bass line: the key the bass line itself plays in (every note of the bass track, weighted by length) and whether it agrees with the song key;
   - Tail overlap: how long the bass sounds while the kick still rings (the kick's life after each hit), and how much shorter the tail would
     have to be to clear the next bass note (F18b's "shorten tail" uses this);
   - Low band: the kick and the bass each rendered offline for the bar, one track at a time (through its own effects and the master, as heard),
     both low-passed at 120 Hz (Butterworth, 4th order, the same filter on both, so it does not move one against the other), then correlated
     while the kick sounds and per 16th; with what that does to the level when the two add up. Drawn once as a strip under the read-outs.
   Nothing per frame: one measurement when the lab measures (two offline renders of one bar, cached), one small canvas drawn once.
   No audio nodes in the live graph; the project is not changed. FT_HOOKS.kickBassLab for F18b (phase rotation, shorten tail). */
const FTKB={cache:new Map(),fc:120,last:null,renders:0,draws:0,
  SC:[['minor',[0,2,3,5,7,8,10]],['phrygian',[0,1,3,5,7,8,10]],['harmonic minor',[0,2,3,5,7,8,11]],['dorian',[0,2,3,5,7,9,10]],['major',[0,2,4,5,7,9,11]]]};
/* the bass line's own key: duration-weighted pitch classes, the best scale and root (the root counts extra; ties go to the song key) */
function ftKbBassKey(bt,K){const ns=bt?NI_allNotes(bt):[];if(!ns.length)return null;const w=new Array(12).fill(0);let tot=0;
  for(const n of ns){const d=Math.max(.0625,+n.l||0),pc=((Math.round(n.p)%12)+12)%12;w[pc]+=d;tot+=d}
  const used=w.map((v,i)=>v>0?i:-1).filter(i=>i>=0),fitOf=pcs=>pcs.reduce((a,pc)=>a+w[pc],0)/tot;let best=null;
  for(let r=0;r<12;r++)for(const[nm,iv]of FTKB.SC){const pcs=iv.map(i=>(i+r)%12),fit=fitOf(pcs),sc=fit+.25*w[r]/tot+(K&&K.root===r&&K.scale===nm?.004:0)+(K&&K.root===r?.002:0);
    if(!best||sc>best.sc+1e-9)best={root:r,scale:nm,fit,sc,pcs}}
  const songFit=K&&K.pcs?fitOf(K.pcs):null,few=used.length<=2;
  const same=!!(K&&K.pcs&&(best.root===K.root&&(best.scale===K.scale||songFit>=best.fit-1e-9)||songFit>=.999&&few));
  return{root:best.root,scale:best.scale,name:NI_PCN[best.root]+' '+best.scale,fit:best.fit,pcs:best.pcs,songFit,same,few,used:used.map(i=>NI_PCN[i])}}
/* the tail overlap: per kick hit, how long a bass note sounds inside the kick's life (ms, overlaps merged), whether a bass note is still
   held when the kick hits, and "cut": how much shorter the kick would have to be to end before the first bass note after the hit */
function ftKbOverlap(r){const k=r&&r.kick,B=r&&r.bass?r.bass.notes:[];if(!k||!k.hits||!k.hits.length||!B.length||!(k.lifeMs>0))return null;
  const ms=(a,b)=>(secOf(b)-secOf(a))*1000,hits=[];
  for(const h of k.hits){const e=beatOf(secOf(h)+k.lifeMs/1000),iv=[];let held=false,first=null;
    for(const q of B){const s=Math.max(q.b,h),t=Math.min(q.b+q.l,e);if(t>s+1e-9)iv.push([s,t]);if(q.b<h-1e-6&&q.b+q.l>h+1e-6)held=true;if(q.b>=h-1e-6&&(first==null||q.b<first))first=q.b}
    iv.sort((a,b)=>a[0]-b[0]);let into=0,cs=null,ce=null;for(const[s,t]of iv){if(cs==null){cs=s;ce=t}else if(s<=ce)ce=Math.max(ce,t);else{into+=ms(cs,ce);cs=s;ce=t}}if(cs!=null)into+=ms(cs,ce);
    const cut=first!=null&&first<e?ms(first,e):0;hits.push({b:h,end:e,into:Math.round(into),held,cut:Math.round(cut),first})}
  const mx=hits.reduce((a,x)=>x.into>a.into?x:a,hits[0]);return{hits,max:mx.into,cut:Math.max(...hits.map(x=>x.cut)),held:hits.some(x=>x.held),lifeMs:Math.round(k.lifeMs)}}
/* a 4th-order Butterworth low-pass as two biquads (bilinear, the same on both signals), on the mono sum */
function ftKbLow(L,R,sr,fc){const n=L.length,x=new Float32Array(n);for(let i=0;i<n;i++)x[i]=(L[i]+(R?R[i]:L[i]))*.5;
  for(const Q of[.5411961,1.3065630]){const w0=2*Math.PI*fc/sr,c=Math.cos(w0),al=Math.sin(w0)/(2*Q),a0=1+al,b0=(1-c)/2/a0,b1=(1-c)/a0,b2=b0,a1=-2*c/a0,a2=(1-al)/a0;
    let x1=0,x2=0,y1=0,y2=0;for(let i=0;i<n;i++){const v=x[i],y=b0*v+b1*x1+b2*x2-a1*y1-a2*y2;x2=x1;x1=v;y2=y1;y1=y;x[i]=y}}return x}
/* correlation of two low-passed signals over sample ranges [[i0,i1],...] (null: all): r, the level change when they add (dB) and both energies */
function ftKbCorrOf(k,b,rg){let kb=0,kk=0,bb=0;const n=Math.min(k.length,b.length);for(const[i0,i1]of rg||[[0,n]]){for(let i=Math.max(0,i0|0),e=Math.min(n,i1|0);i<e;i++){const p=k[i],q=b[i];kb+=p*q;kk+=p*p;bb+=q*q}}
  const quiet=kk<1e-9||bb<1e-9||bb<kk*1e-4||kk<bb*1e-4;return{r:quiet?null:kb/Math.sqrt(kk*bb),db:quiet?0:10*Math.log10((kk+bb+2*kb)/(kk+bb)),ek:kk,eb:bb,quiet,silent:kk<1e-9?'kick':bb<1e-9||bb<kk*1e-4?'bass':kk<bb*1e-4?'kick':null}}
/* the low band of the bar: renders the kick and the bass alone (cached per tracks, bar, master, tempo map and rate), then correlates */
async function ftKbCorr(r,o){o=o||{};if(!r||!r.kick||!r.bass||r.bass.id==null||!r.bar)return null;if(EXR)return{busy:true,why:'An export is running.'};
  const kt=trkById(r.kick.id),bt=trkById(r.bass.id);if(!kt||!bt)return null;const sr=r.sr||(ctx&&ctx.sampleRate)||48000,b0=r.bar.b0,b1=r.bar.b1,fc=FTKB.fc;
  const key=NI_hash(JSON.stringify([kt,bt,b0,b1,sr,fc,S.mfx||null,masterGain(),tmapKey(),r.kick.hits,r.kick.lifeMs]));if(FTKB.cache.has(key)&&!o.keep)return FTKB.cache.get(key);
  const sig=NI_sig(),tail=Math.min(.5,(r.kick.lifeMs||300)/1000+.05);let K,Bf;
  try{FTKB.renders++;const bk=await renderMixChunked(sr,b0,b1,tail,false,kt.id,null,false);if(NI_sig()!==sig)return{stale:true};
    FTKB.renders++;const bb=await renderMixChunked(sr,b0,b1,tail,false,bt.id,null,false);if(NI_sig()!==sig)return{stale:true};
    K=ftKbLow(bk.getChannelData(0),bk.numberOfChannels>1?bk.getChannelData(1):null,sr,fc);Bf=ftKbLow(bb.getChannelData(0),bb.numberOfChannels>1?bb.getChannelData(1):null,sr,fc)}
  catch(e){if(e&&e.message==='cancelled')return{stale:true};console.warn('ftKbCorr',e);return{error:String(e&&e.message||e)}}
  const at=b=>Math.round((secOf(b)-secOf(b0))*sr),lives=r.kick.hits.filter(h=>h<b1-1e-6).map(h=>[at(h),at(h)+Math.round(r.kick.lifeMs/1000*sr)]);
  const life=ftKbCorrOf(K,Bf,lives),bar=ftKbCorrOf(K,Bf,[[0,at(b1)]]),steps=[],ns=Math.max(1,Math.round((b1-b0)*4));
  for(let i=0;i<ns;i++){const c=ftKbCorrOf(K,Bf,[[at(b0+i/4),at(b0+(i+1)/4)]]);steps.push({r:c.r,e:c.ek+c.eb,quiet:c.quiet})}
  const res={life,bar,steps,lives,fc,sr,b0,b1};if(o.keep)return Object.assign({k:K,b:Bf},res);
  FTKB.cache.set(key,res);if(FTKB.cache.size>16)FTKB.cache.delete(FTKB.cache.keys().next().value);return res}
const ftKbSg=v=>(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(2),ftKbDb=v=>(v>=0?'+':'−')+Math.abs(v).toFixed(1)+' dB';
function ftKbCorrWords(c){if(!c)return'';if(c.busy||c.stale||c.error)return'';const L=c.life;
  if(L.silent==='bass')return'Low band: the bass is silent while the kick sounds, so the two cannot cancel there.';if(L.silent==='kick')return'Low band: the kick has nothing under 120 Hz here.';
  const v=L.r;return v>=.3?`Low band (under 120 Hz) while the kick sounds: in phase (${ftKbSg(v)}), so together they are ${ftKbDb(L.db)} louder than apart.`
    :v<=-.3?`Low band (under 120 Hz) while the kick sounds: out of phase (${ftKbSg(v)}), so together they are ${ftKbDb(L.db)} quieter than apart; the low end thins out where they meet.`
    :`Low band (under 120 Hz) while the kick sounds: mostly unrelated (${ftKbSg(v)}), they neither add up nor cancel much (${ftKbDb(L.db)}).`}
/* the strip: one bar per 16th, up when the two are in phase (green), down and hatched when they cancel (red), faded by how loud the low band is there; the kick's lives shaded */
function ftKbDraw(cv,c,r){if(!cv)return;FTKB.draws++;const dpr=Math.min(2,window.devicePixelRatio||1),w=516,h=46;if(cv.width!==w*dpr){cv.width=w*dpr;cv.height=h*dpr}
  const g=cv.getContext('2d');g.setTransform(dpr,0,0,dpr,0,0);vbg(g,w,h);const x0=64,x1=w-8,mid=h/2,amp=mid-5;
  txt(g,'in phase',6,12,'rgba(126,226,176,.85)',9);txt(g,'cancel',6,h-6,'rgba(255,138,138,.85)',9);
  g.fillStyle='rgba(255,255,255,.12)';g.fillRect(x0,mid,x1-x0,1);
  if(!c||!c.steps){txt(g,c&&c.why?c.why:'Measuring the low band…',(x0+x1)/2,mid+4,NI_KBC.lab,10,'center');return}
  const n=c.steps.length,bw=(x1-x0)/n,tot=c.b1-c.b0,X=b=>x0+(b-c.b0)/tot*(x1-x0),emax=Math.max(1e-12,...c.steps.map(s=>s.e));
  if(r&&r.kick){g.fillStyle='rgba(255,107,107,.13)';for(const h0 of r.kick.hits){const e=beatOf(secOf(h0)+r.kick.lifeMs/1000);g.fillRect(X(h0),3,Math.max(1,Math.min(X(e),x1)-X(h0)),h-6)}}
  g.fillStyle='rgba(255,255,255,.08)';for(let b=Math.ceil(c.b0);b<c.b1;b++)g.fillRect(Math.round(X(b)),3,1,h-6);
  c.steps.forEach((s,i)=>{if(s.r==null)return;const a=.25+.75*Math.sqrt(s.e/emax),x=x0+i*bw+1,bwi=Math.max(1,bw-2),hh=Math.max(1,Math.abs(s.r)*amp);
    if(s.r>=0){g.fillStyle=`rgba(62,207,142,${a.toFixed(3)})`;g.fillRect(x,mid-hh,bwi,hh)}
    else{g.fillStyle=`rgba(255,90,90,${a.toFixed(3)})`;g.fillRect(x,mid+1,bwi,hh);g.save();g.beginPath();g.rect(x,mid+1,bwi,hh);g.clip();g.strokeStyle='rgba(0,0,0,.45)';g.lineWidth=1;
      for(let k=-hh;k<bwi+hh;k+=4){g.moveTo(x+k,mid+1);g.lineTo(x+k+hh,mid+1+hh)}g.stroke();g.restore()}})}
const FTKB_TIP={bk:'The key the bass line itself plays in, from all its notes (longer notes count more), and how much of it fits. When it differs from the song key, either may be wrong.',
  ov:'How long the bass sounds while the kick still rings (its life after each hit), at the worst hit of this bar. The second number: how much shorter the kick would have to be to end before the next bass note.',
  lb:'How the kick and the bass line up under 120 Hz while the kick sounds: +1 in phase (they add up), 0 unrelated, −1 out of phase (they cancel and the low end thins out). The dB value is the level change when the two add up.',
  cv:'The low band per 16th of this bar: up and green where the kick and the bass are in phase, down, red and hatched where they cancel, faint where the low band is quiet. The kick\'s lives are shaded.'};
function ftKbRow(r,el){FTKB.last={r};if(!r||!r.kick||r.empty||r.busy||r.stale||r.error){el.hidden=true;return}el.className='ftkb';
  const bk=r.bass&&r.bass.id!=null?ftKbBassKey(trkById(r.bass.id),r.key):null,ov=ftKbOverlap(r);FTKB.last.bk=bk;FTKB.last.ov=ov;
  const pc=v=>Math.round(v*100)+' %';
  const bkH=bk?(bk.few?`${esc(bk.used.join(', '))}<i>${bk.same?'in the key':'outside the key'}</i>`:`${esc(bk.name)}<i>${pc(bk.fit)}</i>`):'–';
  const ovH=ov?(ov.max>0?`${ov.max}<i>ms${ov.cut>0?', '+ov.cut+' ms too long':''}</i>`:`none<i>ms</i>`):'–';
  el.innerHTML=`<div class="nird"><span title="${esc(FTKB_TIP.bk)}"><small>Bass line</small><b data-fk="bk" class="${bk?bk.same?'ok':'cl':''}">${bkH}</b></span>`+
    `<span title="${esc(FTKB_TIP.ov)}"><small>Tail overlap</small><b data-fk="ov" class="${ov?ov.max>0?'cl':'ok':''}">${ovH}</b></span>`+
    `<span title="${esc(FTKB_TIP.lb)}"><small>Low band</small><b data-fk="lb">…</b></span></div><canvas data-fk="cv" title="${esc(FTKB_TIP.cv)}"></canvas><p class="ftkbw"></p>`;
  const W=[];if(bk){if(bk.few)W.push(`The bass line plays only ${bk.used.join(' and ')}${bk.same?', inside the song key':', outside the song key '+r.key.name}.`);
    else W.push(bk.same?`The bass line plays in ${bk.name}, the song key.`:`The bass line fits ${bk.name} best (${pc(bk.fit)} of its notes)${r.key.pcs?', the song key '+r.key.name+' only '+pc(bk.songFit):''}.`)}
  if(ov){if(ov.held)W.push('A bass note is still held when the kick hits.');if(ov.max>0)W.push(`The kick rings ${ov.lifeMs} ms; the bass sounds for ${ov.max} ms of it${ov.cut>0?`, and the tail would have to be ${ov.cut} ms shorter to end before the next bass note`:''}.`);else W.push('The bass stays out of the kick\'s tail.')}
  const wl=el.querySelector('.ftkbw'),cv=el.querySelector('canvas'),lb=el.querySelector('[data-fk="lb"]');wl.textContent=W.join(' ');ftKbDraw(cv,null,r);
  const tok=FTKB.tok=(FTKB.tok|0)+1;ftKbCorr(r).then(c=>{if(tok!==FTKB.tok||!el.isConnected)return;FTKB.last.c=c;
    if(!c||c.busy||c.stale||c.error){lb.textContent='–';ftKbDraw(cv,{why:c?c.why||(c.stale?'The song changed. Measure again.':'Could not measure.'):'No bass to compare.'},r);return}
    const L=c.life;if(L.r==null){lb.innerHTML='–<i>'+(L.silent==='bass'?'no bass':'no kick')+'</i>';lb.className=''}else{lb.innerHTML=`${ftKbSg(L.r)}<i>${ftKbDb(L.db)}</i>`;lb.className=L.r<=-.3?'cl':L.r>=.3?'ok':''}
    ftKbDraw(cv,c,r);const t=ftKbCorrWords(c);if(t)wl.textContent=(W.length?W.join(' ')+' ':'')+t})}
if(window.NI_HOOKS&&NI_HOOKS.kickBassView)NI_HOOKS.kickBassView.addRow(ftKbRow);
FT_HOOKS.kickBassLab={bassKey:ftKbBassKey,overlap:ftKbOverlap,corr:ftKbCorr,corrOf:ftKbCorrOf,low:ftKbLow,last:()=>FTKB.last,stats:()=>({renders:FTKB.renders,draws:FTKB.draws,cache:FTKB.cache.size})};
document.head.insertAdjacentHTML('beforeend','<style id="ftkbCss">#niKB .ftkb{display:flex;flex-direction:column;gap:5px}#niKB .ftkb[hidden]{display:none}#niKB .ftkb .nird{grid-template-columns:repeat(3,1fr)}#niKB .ftkb canvas{width:516px;height:46px}#niKB .ftkbw{margin:0;font-size:var(--fs1);line-height:1.45;color:var(--mut)}#niKB .ftkbw:empty{display:none}</style>');
