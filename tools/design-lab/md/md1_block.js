/* ====================== task MD1: the measurement details (science look M1, M2, M3) ======================
   M1 readouts with units: units are tiny capitals in amber (CSS .lku and .mdu, canvas lkVU), equal-width digits, fixed decimals
      in the transport (latency to 0.1 ms, peak to 0.1 dB), static labels BAR, T+, BPM and a fine tick scale under the position (CSS only).
   M2 the orbit loader: mdOrb(px,p,label) gives an SVG (16, 24 or 40 px): an electron orbiting the nucleus when the progress is not
      known, an orbit that fills when it is (mdOrbSet(root,p)); CSS animation only, so it costs nothing while hidden (display none).
      mdOrbDraw draws the same on a canvas (the bounce of a MIDI clip on an audio track). mdJob(key,text,p) is a small pill for jobs
      without a window of their own (the stem splitter).
   M3 the caliper while dragging: drawn on the arrangement canvas after the frame, only while a clip is moved or its edge dragged,
      a block of clips moved, a loop, section or selection range drawn; nothing is read from the page, nothing runs when idle.
      Setting UI.mdCal (Appearance, Density and motion: "Caliper while dragging"). */
const MD1={jobs:new Map(),lab:false};
const MD1_ORB={e:'M16,0A16,6.6 0 1,1 -16,0A16,6.6 0 1,1 16,0',c:'M0,-15A15,15 0 1,1 0,15A15,15 0 1,1 0,-15'};
function mdOrbPx(px){return px>=32?40:px>=20?24:16}
function mdOrb(px,p,lab){const s=mdOrbPx(px||16),k=p!=null,q=k?Math.max(0,Math.min(1,+p||0)):0,d=k?MD1_ORB.c:MD1_ORB.e,l=String(lab||'Working').replace(/[&<>"]/g,'');
  return `<svg class="mdorb mdo${s}${k?' mdp':''}" viewBox="-20 -20 40 40" role="${k?'progressbar':'img'}" aria-label="${l}"${k?` aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(q*100)}"`:''}><title>${l}</title><g${k?'':' transform="rotate(-30)"'}><path class="o0" d="${d}" pathLength="100"/><path class="o1" d="${d}" pathLength="100"${k?` style="stroke-dasharray:${(q*100).toFixed(1)} 100"`:''}/><path class="o2" d="${d}" pathLength="100"${k?` style="stroke-dashoffset:${(-q*100).toFixed(1)}"`:''}/></g><circle class="nu" r="3.6"/></svg>`}
/* set the progress of the orbit inside root (or root itself); an orbiting one becomes a filling one */
function mdOrbSet(root,p){if(!root)return;const el=root.classList&&root.classList.contains('mdorb')?root:root.querySelector&&root.querySelector('.mdorb');if(!el)return;
  const q=Math.max(0,Math.min(1,+p||0)),v=(q*100).toFixed(1);if(el.__p===v)return;el.__p=v;
  if(!el.classList.contains('mdp')){el.classList.add('mdp');el.setAttribute('role','progressbar');el.setAttribute('aria-valuemin','0');el.setAttribute('aria-valuemax','100');const g=el.querySelector('g');if(g)g.removeAttribute('transform');for(const ph of el.querySelectorAll('path'))ph.setAttribute('d',MD1_ORB.c)}
  const o1=el.querySelector('.o1'),o2=el.querySelector('.o2');if(o1)o1.style.strokeDasharray=v+' 100';if(o2)o2.style.strokeDashoffset=(-q*100).toFixed(1);el.setAttribute('aria-valuenow',String(Math.round(q*100)))}
/* the same on a canvas: circle orbit, filled arc, nucleus, electron at the head (p null: orbiting by time) */
function mdOrbDraw(g,cx,cy,px,p,t){const r=mdOrbPx(px)*.375,k=p!=null,q=k?Math.max(0,Math.min(1,p)):0,lw=Math.max(1,r/6.5);g.save();g.lineCap='round';g.lineWidth=lw;
  g.strokeStyle=k?'rgba(255,255,255,.16)':'rgba(159,194,255,.3)';g.beginPath();if(k)g.arc(cx,cy,r,0,6.2832);else g.ellipse(cx,cy,r,r*.41,-.52,0,6.2832);g.stroke();
  let a;if(k){a=-1.5708+q*6.2832;if(q>0){g.strokeStyle='#4cc9f0';g.beginPath();g.arc(cx,cy,r,-1.5708,a);g.stroke()}}else{a=((t||performance.now())/1300%1)*6.2832;g.strokeStyle='#4cc9f0';g.beginPath();g.ellipse(cx,cy,r,r*.41,-.52,a-1.4,a);g.stroke()}
  g.fillStyle='#ffd23a';g.beginPath();g.arc(cx,cy,Math.max(1.2,r*.22),0,6.2832);g.fill();
  let ex,ey;if(k){ex=cx+Math.cos(a)*r;ey=cy+Math.sin(a)*r}else{const x=r*Math.cos(a),y=r*.41*Math.sin(a),c=Math.cos(-.52),s=Math.sin(-.52);ex=cx+x*c-y*s;ey=cy+x*s+y*c}
  g.fillStyle='#fff';g.beginPath();g.arc(ex,ey,Math.max(1.1,r*.17),0,6.2832);g.fill();g.restore()}
/* a small pill for a job without a window of its own; p null: progress not known */
function mdJob(key,text,p){const J=MD1.jobs;J.set(key,{text,p,at:performance.now()});let b=document.getElementById('mdJob');if(!b){b=document.createElement('div');b.id='mdJob';b.setAttribute('role','status');document.body.appendChild(b)}
  const known=p!=null,cur=b.dataset.k===key&&b.dataset.m===(known?'p':'o');if(!cur){b.dataset.k=key;b.dataset.m=known?'p':'o';b.innerHTML=mdOrb(24,known?p:null,text)+'<span></span><b></b>'}
  if(known)mdOrbSet(b,p);b.querySelector('span').textContent=text;b.querySelector('b').textContent=known?Math.round(Math.max(0,Math.min(1,p))*100)+'%':'';b.hidden=false;
  clearTimeout(MD1.jt);MD1.jt=setTimeout(()=>{for(const[k,v] of J)if(performance.now()-v.at>60000)mdJobEnd(k)},61000)}
function mdJobEnd(key){MD1.jobs.delete(key);const b=document.getElementById('mdJob');if(!b)return;if(!MD1.jobs.size){b.hidden=true;b.dataset.k='';return}const[k,v]=[...MD1.jobs][MD1.jobs.size-1];b.dataset.k='';mdJob(k,v.text,v.p)}
/* export: the orbit with the real progress in the top pill, the export window and the full-screen render */
function mdExpSet(p){for(const[sel,px,lab] of[['#exTop',16,'Export progress'],['#exWave',16,'Export progress'],['#exFz .fzr',40,'Render progress']]){const h=document.querySelector(sel);if(!h)continue;if(!h.querySelector('.mdorb'))h.insertAdjacentHTML('afterbegin',mdOrb(px,0,lab));mdOrbSet(h,p)}}
/* M1: unit labels in the transport (static, nothing per frame) */
function mdTrLabels(){const mk=(t,tip)=>{const u=document.createElement('span');u.className='mdu';u.textContent=t;u.setAttribute('aria-hidden','true');if(tip)u.title=tip;return u};
  const pb=document.getElementById('posBars'),pt=document.getElementById('posTime'),bp=document.getElementById('bpm');
  if(pb&&!pb.previousElementSibling){pb.before(mk('bar','Bar . beat . sixteenth . tick'));pb.parentElement.classList.add('mdtk')}
  if(pt&&!(pt.previousElementSibling&&pt.previousElementSibling.classList.contains('mdu'))){pt.before(mk('t+','Time from the song start (hours:minutes:seconds.milliseconds)'));pt.parentElement.classList.add('mdtk','mdclk')}
  if(bp&&!(bp.nextElementSibling&&bp.nextElementSibling.classList.contains('mdu')))bp.after(mk('bpm','Beats per minute'));
  for(const id of['mBtnV','pkNow','latV','cpuV']){const e=document.getElementById(id);if(e&&!e.firstElementChild)lkOut(e,e.textContent)}
  MD1.lab=true}
/* ---- M3: the caliper ---- */
function mdCalOn(){return typeof UI!=='object'||UI.mdCal!==false}
function mdBarF(b){try{if(sigFlat())return b/4;const P=barPos(Math.max(0,b));return P.bar+P.inBar/P.len}catch(e){return b/4}}
function mdRowsY(r0,r1){const a=Math.max(0,Math.min(r0,r1)),z=Math.min(S.tracks.length-1,Math.max(r0,r1));return[AY+(TRY[a]??a*V.th)-V.y,AY+(TRY[z]??z*V.th)-V.y+V.th]}
function mdCalSpan(){if(!mdCalOn()||typeof S!=='object')return null;
  if(typeof ad!=='undefined'&&ad){const k=ad.k;
    if((k==='move'||k==='res'||k==='resl')&&ad.c&&ad.t&&ad.pushed){const i=S.tracks.indexOf(ad.t);if(i<0)return null;const G=clipGeom(i,ad.c),a=ad.c.start;return{a,b:a+ad.c.len,y0:G.y,y1:G.y+G.h,pos:true}}
    if(k==='block'&&ad.moved&&ad.items&&ad.items.length){let a=1e9,b=-1e9,r0=1e9,r1=-1;if(typeof SELR!=='undefined'&&SELR&&!ad.rip){a=SELR.b0;b=SELR.b1;r0=SELR.r0;r1=SELR.r1}else for(const it of ad.items){if(!it.c)continue;a=Math.min(a,it.c.start);b=Math.max(b,it.c.start+it.c.len);const ri=S.tracks.indexOf(it.t);if(ri>=0){r0=Math.min(r0,ri);r1=Math.max(r1,ri)}}
      if(ad.rip&&ad.dst!=null&&ad.R){a=ad.dst;b=ad.dst+(ad.R.b1-ad.R.b0);r0=ad.R.r0;r1=ad.R.r1}if(!(b>a)||r1<0)return null;const[y0,y1]=mdRowsY(r0,r1);return{a,b,y0,y1,pos:true}}
    if((k==='ruler'&&ad.lr)||(k==='loopmv'&&ad.moved)){const a=loopA(),b=loopB();if(!(b>a))return null;return{a,b,y0:AY,y1:AY+12,top:true,pos:true}}
    if((k==='sec'&&ad.moved&&ad.mode!=='move'||k==='secnew')&&ad.sc){return{a:ad.sc.start,b:ad.sc.start+ad.sc.len,y0:AY,y1:AY+12,top:true,pos:true}}
  }
  if(typeof RS!=='undefined'&&RS&&RS.moved&&typeof SELR!=='undefined'&&SELR&&SELR.b1>SELR.b0){const[y0,y1]=mdRowsY(SELR.r0,SELR.r1);return{a:SELR.b0,b:SELR.b1,y0,y1,pos:true}}
  return null}
function mdCalDraw(){const C=mdCalSpan();if(!C)return;if(typeof OVW==='object'&&(OVW.on||OVW.a))return;
  const d=(window.devicePixelRatio||1)*ZOOM,g=arr.getContext('2d'),w=arr.width/d,L=lkT(),hp=1/Math.max(1,d),px=v=>Math.round(v*d)/d+hp/2;
  const xa=X0+(C.a-V.x)*V.ppb,xb=X0+(C.b-V.x)*V.ppb;if(xb<X0||xa>w)return;
  const yl=C.top?AY+9:Math.max(AY+9,C.y0-8),ya=px(Math.min(Math.max(xa,X0),w)),yb=px(Math.min(xb,w)),y=px(yl);
  g.save();g.setTransform(d,0,0,d,0,0);g.beginPath();g.rect(X0,AY,w-X0,arr.height/d-AY);g.clip();
  g.strokeStyle=L.meas;g.fillStyle=L.meas;g.lineWidth=hp;g.beginPath();
  for(const x of[xa,xb])if(x>=X0-1&&x<=w+1){const xx=px(x);g.moveTo(xx,yl-4);g.lineTo(xx,C.top?yl+5:C.y0+5)}
  g.moveTo(ya,y);g.lineTo(yb,y);g.stroke();
  /* arrowheads, where the end is in view */
  const ah=(x,dir)=>{g.beginPath();g.moveTo(x,y);g.lineTo(x+dir*5,y-2.5);g.lineTo(x+dir*5,y+2.5);g.closePath();g.fill()};if(xb-xa>14){if(xa>=X0)ah(px(xa),1);if(xb<=w)ah(px(xb),-1)}
  /* a fine tick scale: one tick a beat while beats are 6 px apart or more, longer at the bars */
  if(V.ppb>=6&&C.b-C.a<=512){g.globalAlpha=.55;g.beginPath();for(let bt=Math.ceil(C.a-1e-6);bt<C.b-1e-6;bt++){const x=X0+(bt-V.x)*V.ppb;if(x<=xa+3||x>=xb-3||x<X0||x>w)continue;const bar=Math.abs(mdBarF(bt)-Math.round(mdBarF(bt)))<1e-6;g.moveTo(px(x),y-(bar?2.5:1.5));g.lineTo(px(x),y+(bar?2.5:1.5))}g.stroke();g.globalAlpha=1}
  /* the label: length in bars and seconds, and the position */
  const nb=mdBarF(C.b)-mdBarF(C.a),sec=secOf(C.b)-secOf(C.a),pos=C.pos?barsStr(C.a).replace(/\s+/g,'').replace(/\.0$/,'').split('.').slice(0,3).join('.'):'';
  const P=[['Δ ',L.meas,0],[nb.toFixed(3),L.ink,0],[' bars',L.unit,1],['   ',L.ink,0],[sec.toFixed(3),L.ink,0],[' s',L.unit,1]];if(pos)P.push(['   @ ',L.meas,0],[pos,L.ink,0]);
  g.font='500 11px '+L.ui;g.textBaseline='middle';const sc='fontVariantCaps' in g;let tw=0;for(const s of P){if(s[2]&&sc)g.fontVariantCaps='all-small-caps';s[3]=g.measureText(s[0]).width;tw+=s[3];if(sc)g.fontVariantCaps='normal'}
  let lx=Math.max(X0+4,Math.min(Math.max(xa,X0)+4,w-tw-10)),ly=yl-11;if(ly<AY+6)ly=yl+11;
  g.fillStyle='rgba(8,10,14,.84)';g.beginPath();if(g.roundRect)g.roundRect(lx-5,ly-8,tw+10,16,4);else g.rect(lx-5,ly-8,tw+10,16);g.fill();
  for(const s of P){g.fillStyle=s[1];if(s[2]&&sc)g.fontVariantCaps='all-small-caps';g.fillText(s[0],lx,ly+.5);if(sc)g.fontVariantCaps='normal';lx+=s[3]}
  g.restore()}
{const _dmd=drawArr;drawArr=function(ph){const r=_dmd.apply(this,arguments);if(typeof ad!=='undefined'&&ad||typeof RS!=='undefined'&&RS){try{mdCalDraw()}catch(e){}}return r}}
/* the setting: Appearance, in the Density and motion block (it moves with the block) */
const MD1_ROWS=[{"id":"caliper","l":"Caliper while dragging","pg":"layout","ap":"appearance","b":"Density and motion","sc":"app","k":"UI.mdCal","c":"#mdCalChk","t":"check","d":true,"h":"While you move a clip, drag its edge, or draw a loop, section or selection, a thin amber measuring line shows the length in bars and seconds and where it starts, like a dimension on a drawing.","w":"caliper measure measuring dimension length bars seconds drag dragging ruler interface"}];
{const m=document.getElementById('lkMotion'),row=m&&m.closest('.row');if(row&&!document.getElementById('mdCalChk')){const r=document.createElement('div');r.className='row';r.title=MD1_ROWS[0].h;r.innerHTML='<label class="chk" style="margin:0"><input type="checkbox" id="mdCalChk"> Caliper while dragging</label>';row.after(r);
  const c=r.querySelector('input');c.checked=UI.mdCal!==false;c.onchange=()=>{UI.mdCal=c.checked;saveUI();dirty=true}}}
try{for(const r of MD1_ROWS)if(!STX.has(r.id)){STT.push(r);STX.set(r.id,r)}}catch(e){}
const MD1_HOOKS=window.MD1_HOOKS=Object.assign(window.MD1_HOOKS||{},{orb:mdOrb,orbSet:mdOrbSet,orbDraw:mdOrbDraw,job:mdJob,jobEnd:mdJobEnd,calSpan:mdCalSpan});
mdTrLabels();
