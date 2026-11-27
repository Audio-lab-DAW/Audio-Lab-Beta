/* ===== lane E (task IN-O): stereo field and phase, the user's picks O0 (today's drawing kept), O1 and O4 =====
   O0 the stereo field box of every mixer strip and the master stays as it is (diamond grid, L R M, dots in the strip's colour scheme, its
      menu options, the phase, balance and width read-outs).
   O1 marks only (X5): amber ticks at 0, -6, -12 and -18 dB of a mono signal on the M axis and of a one-sided signal on the L and R diagonals
      (placed by the display's own mapping, so a tick is where such a sample lands), +S and -S at the sides; a short afterglow (a small layer
      per display that fades to 18 % in 1/6 s, by time, so the shape reads instead of flickering dots; none at the Light level), the newest
      sample as an amber dot. The phase bar gets a scale (ticks every 0.1, heavier at -1, -0.5, 0, +0.5, +1), the negative half hatched, the
      value with a real minus and the phase angle (arccos of the correlation). The master box's Stereo bar: the negative half hatched, the
      phase angle beside the value. The overlay's stereo module (it already fades) gets the same marks.
   O4 a polar view, chosen in the stereo field's right-click menu (Picture: Stereo field or Polar view), never instead of it: iZotope's
      polar sample, the angle is the stereo position (up = mono, 45 degrees = only left or only right), the distance the level (rings every
      12 dB from -48 to 0 dB); beyond 45 degrees is out of phase, on a hatched ground; the share of samples in phase in percent.
   The strip taps (N.aL, N.aR) stay at 256 samples: reading 512 doubled the dots and the other readers' work (2 ms more a mixer picture
   with 18 strips on screen, measured); the afterglow builds the shape from the frames instead. Dots are drawn in six level steps of the strip's
   colour scheme (one fill colour per step, not per dot). Drawn only for strips on screen, as before. */
const INSO={MK:'rgba(255,181,71,.6)',HAT:'rgba(255,77,109,.32)',RED:'rgba(255,77,109,.07)',st:new WeakMap(),NB:6,cnt:[0,0],ip:new WeakMap()};
/* O1 marks. K: pixels per unit of mid m=(l+r)/sqrt2 and side s=(r-l)/sqrt2 (how the display maps them), lim: the box's half size */
function inoMarks(g,cx,cy,K,lim,o={}){const L=INS.look();g.save();if(o.a!=null)g.globalAlpha=o.a;g.strokeStyle=INSO.MK;g.lineWidth=INS.hair(g,1);g.beginPath();const lab=[];
  for(const db of[0,-6,-12,-18]){const amp=Math.pow(10,db/20),dm=amp*Math.SQRT2*K,dd=amp*K/Math.SQRT2;
    if(dm<=lim-1){const y=INS.px(g,cy-dm);g.moveTo(cx-3,y);g.lineTo(cx+3,y);if(db>-18)lab.push([db,y])}
    if(dd<=lim-1){for(const sg of[-1,1]){const px=cx+sg*dd,py=cy-dd;g.moveTo(px-1.8,py-sg*1.8);g.lineTo(px+1.8,py+sg*1.8)}}}
  g.stroke();
  if(lim>=26&&o.lab!==false){g.font='6.5px '+L.mono;g.fillStyle=INSO.MK;g.textBaseline='middle';g.textAlign='left';for(const[db,y]of lab)g.fillText(db?INS.num(db,0):'0',cx+4,y);
    g.fillStyle=L.mut;g.textAlign='right';g.fillText('+S',cx+lim-2,cy-5);g.textAlign='left';g.fillText(INS.MIN+'S',cx-lim+2,cy-5);g.textBaseline='alphabetic'}
  g.restore()}
/* the afterglow layer of one display: a canvas of the box's size in CSS pixels that fades by time; draw(lg) paints into it in box coordinates */
function inoLayer(cv,g,x0,y0,S0,draw){const d=1/* the soft afterglow at one pixel per CSS pixel: a third of the work at 1.75x */,W=Math.max(1,Math.round(S0*d));let st=INSO.st.get(cv);
  if(!st||st.cv.width!==W){const c=document.createElement('canvas');c.width=c.height=W;st={cv:c,g:c.getContext('2d'),t:0};st.g.setTransform(d,0,0,d,0,0);INSO.st.set(cv,st)}
  const now=performance.now(),dt=st.t?Math.min(.25,(now-st.t)/1000):1;st.t=now;const lg=st.g;
  lg.globalCompositeOperation='destination-out';lg.fillStyle='rgba(0,0,0,'+(1-Math.pow(.82,dt*60)).toFixed(3)+')';lg.fillRect(0,0,S0,S0);lg.globalCompositeOperation='source-over';
  draw(lg);g.drawImage(st.cv,x0,y0,S0,S0)}
/* the colour of each of the six level steps (today's per-dot colour, mxC, at the step's middle) */
function inoCols(cm,col,H0){const k=cm+'|'+col+(H0&&H0.b3?'|'+H0.b3[0]+','+H0.b3[1]+','+H0.b3[2]:'');if(H0._inoK===k)return H0._inoC;const c=[];for(let b=0;b<INSO.NB;b++)c.push(mxC(cm,(b+.5)/INSO.NB,col,H0.b3,0));H0._inoK=k;H0._inoC=c;return c}
/* the dots of a mixer strip's stereo field (O0's mapping: px = cx + s R, py = cy - m R, one 1.6 px dot per sample, alpha 0.6) or of the polar view (O4) */
function inoField(cv,g,sx,sy0,S0,cx,cy,R,bl,br,n,cm,col,H0){const pol=mxOpt('stereo','pol'),lite=INS.lite(),C=inoCols(cm,col,H0),NB=INSO.NB;INSO.cnt[0]++;
  const PX=INSO.PX||(INSO.PX=new Float32Array(2048)),PY=INSO.PY||(INSO.PY=new Float32Array(2048)),PB=INSO.PB||(INSO.PB=new Uint8Array(2048)),nn=Math.min(n,2048);
  /* one pass: each sample's place and level step; then one fill colour per step, fillRect per dot (the fast path) */
  const plot=(q,ox,oy)=>{let ip=0,tot=0;for(let i=0;i<nn;i++){const l=bl[i],r=br[i];if(pol){let m=(l+r)/2,s=(r-l)/2;if(m<0){m=-m;s=-s}const lev=Math.sqrt(m*m+s*s);if(lev<1e-5){PB[i]=255;continue}
        const th=Math.atan2(s,m);tot++;if(th<=.7854&&th>=-.7854)ip++;const P=inoPol(th,lev,R);PX[i]=ox+P[0]-.8;PY[i]=oy+P[1]-.8;PB[i]=Math.min(NB-1,Math.floor(Math.min(1,lev*1.98)*NB))}
      else{const s=(l+r)*.7071,d=(r-l)*.7071;PX[i]=ox+d*R;PY[i]=oy-s*R;PB[i]=Math.min(NB-1,Math.floor(Math.min(1,Math.sqrt(s*s+d*d)*1.4)*NB))}}
    q.globalAlpha=.6;for(let b=0;b<NB;b++){q.fillStyle=C[b];for(let i=0;i<nn;i++)if(PB[i]===b)q.fillRect(PX[i],PY[i],1.6,1.6)}q.globalAlpha=1;return tot?ip/tot:null};
  const box=pol?inoPolBox(sx,sy0,S0):null,ox=pol?box.cx-sx:cx-sx,oy=pol?box.cy-sy0:cy-sy0;let ipf=null;
  g.save();g.beginPath();g.rect(sx+1,sy0+1,S0-2,S0-2);g.clip();
  if(lite)ipf=plot(g,ox+sx,oy+sy0);else inoLayer(cv,g,sx,sy0,S0,lg=>{ipf=plot(lg,ox,oy)});
  /* the newest sample, amber */const l=bl[n-1],r=br[n-1];if(Math.abs(l)+Math.abs(r)>1e-5){let x,y;if(pol){let m=(l+r)/2,s=(r-l)/2;if(m<0){m=-m;s=-s}const P=inoPol(Math.atan2(s,m),Math.hypot(m,s),box.R);x=box.cx+P[0];y=box.cy+P[1]}else{x=cx+(r-l)*.7071*R;y=cy-(l+r)*.7071*R}
    g.fillStyle=INS.look().unit;g.beginPath();g.arc(x+.8,y+.8,1.8,0,7);g.fill()}
  g.restore();
  if(pol&&ipf!=null){const p=INSO.ip.get(cv),v=p==null?ipf:p+(ipf-p)*.1;INSO.ip.set(cv,v);const L=INS.look();g.font='6.5px '+L.mono;g.textAlign='right';g.fillStyle=v<.9?'#ff8a8a':L.ink;g.fillText(Math.round(v*100)+' %',sx+S0-3,sy0+S0-4);g.fillStyle=L.mut;g.textAlign='left';g.fillText('in phase',sx+3,sy0+S0-4)}}
/* O4: the polar geometry in a square box: the centre at the bottom middle of a half disc that fills the box's width */
function inoPolBox(sx,sy0,S0){const R=S0/2-3;return{cx:sx+S0/2,cy:sy0+S0/2+R/2+2,R}}
function inoPol(th,lev,R){const rad=R*Math.max(0,1+20*Math.log10(Math.max(1e-9,lev))/48),t=th-Math.PI/2;return[Math.cos(t)*rad,Math.sin(t)*rad]}
/* O4 background (instead of the diamond): out-of-phase sectors hatched, rings every 12 dB, the 45 degree guides amber, MONO, L and R */
function inoPolBg(g,sx,sy0,S0){const L=INS.look(),{cx,cy,R}=inoPolBox(sx,sy0,S0),lw=INS.hair(g,L.lwGrid);g.fillStyle='#0c0e13';g.fillRect(sx+1,sy0+1,S0-2,S0-2);
  g.save();g.beginPath();g.rect(sx+1,sy0+1,S0-2,S0-2);g.clip();
  for(const[a0,a1]of[[Math.PI,Math.PI*1.25],[Math.PI*1.75,Math.PI*2]]){g.beginPath();g.moveTo(cx,cy);g.arc(cx,cy,R,a0,a1);g.closePath();g.fillStyle=INSO.RED;g.fill();g.save();g.clip();g.strokeStyle=INSO.HAT;g.lineWidth=lw;g.beginPath();for(let k=-R*2;k<R*2;k+=4){g.moveTo(cx+k,cy);g.lineTo(cx+k+R,cy-R)}g.stroke();g.restore()}
  g.lineWidth=lw;g.strokeStyle=L.gMid;for(let i=1;i<=4;i++){g.beginPath();g.arc(cx,cy,R*i/4,Math.PI,Math.PI*2);g.stroke()}
  for(const a of[-90,-45,0,45,90]){const t=(a-90)*Math.PI/180;g.strokeStyle=a===0?L.gMaj:Math.abs(a)===45?INSO.MK:L.gMid;g.beginPath();g.moveTo(cx,cy);g.lineTo(cx+Math.cos(t)*R,cy+Math.sin(t)*R);g.stroke()}
  g.restore();g.font='6.5px '+L.mono;g.fillStyle=L.mut;g.textBaseline='alphabetic';g.textAlign='center';if(S0>=40){g.fillText('MONO',cx,sy0+8);g.fillText('L',cx-R*.72-3,cy-R*.72+2);g.fillText('R',cx+R*.72+3,cy-R*.72+2)}
  if(S0>=70){g.textAlign='left';g.fillText(INS.MIN+'12',cx+2,cy-R*.75+7)}g.textAlign='left'}
/* the box: O1 marks on today's diamond, or the polar background */
function inoBox(g,sx,sy0,S0,cx,cy,R){if(mxOpt('stereo','pol')){inoPolBg(g,sx,sy0,S0);return}
  /* the marks of a box size drawn once into an image, then copied (one copy a frame instead of a path and five texts) */
  const d=INS.dpr(g),k=S0+'|'+d+'|'+(cx-sx)+'|'+(cy-sy0)+'|'+R,C=INSO.mc||(INSO.mc=new Map());let im=C.get(k);
  if(!im){if(C.size>16)C.clear();im=document.createElement('canvas');im.width=im.height=Math.max(1,Math.ceil(S0*d));const q=im.getContext('2d');q.setTransform(d,0,0,d,0,0);inoMarks(q,cx-sx,cy-sy0,R,S0/2-1);C.set(k,im)}
  g.drawImage(im,sx,sy0,im.width/d,im.height/d)}
/* O1: the phase (correlation) bar, -1 to +1: hatched negative half, ticks, the value with a real minus and the phase angle */
function inoCorr(g,bx,yb,bw2,corr,fill){const L=INS.look(),lw=INS.hair(g,1),c=Math.max(-1,Math.min(1,corr));g.save();g.fillStyle='#14161c';g.fillRect(bx,yb,bw2,6);
  g.save();g.beginPath();g.rect(bx,yb,bw2/2,6);g.clip();g.strokeStyle=INSO.HAT;g.lineWidth=lw;g.beginPath();for(let k=-8;k<bw2/2+8;k+=3){g.moveTo(bx+k,yb+6);g.lineTo(bx+k+6,yb)}g.stroke();g.restore();
  const cpos=bx+(c+1)/2*bw2;g.fillStyle=fill;g.fillRect(Math.min(cpos,bx+bw2/2),yb,Math.abs(cpos-(bx+bw2/2)),6);g.fillStyle='#fff';g.fillRect(cpos-1,yb-1,2,8);g.fillStyle='rgba(255,255,255,.25)';g.fillRect(bx+bw2/2,yb,1,6);
  g.strokeStyle=L.tick;g.lineWidth=lw;g.beginPath();const st=bw2>=60?20:4;for(let i=0;i<=st;i++){const x=INS.px(g,bx+bw2*i/st),maj=st===4||i%5===0;g.moveTo(x,yb+7);g.lineTo(x,yb+(maj?10:8.5))}g.stroke();
  g.font='6.5px '+L.mono;g.textAlign='right';g.textBaseline='alphabetic';const ang=Math.acos(c)*180/Math.PI,s=INS.num(c,2,true)+(bw2>=56?'  '+Math.round(ang)+'°':'');g.fillStyle=c<0?'#ff8a8a':L.ink;g.fillText(s,bx+bw2,yb-5);g.restore()}
/* O1 on the balance bar: ticks at L, the quarters, C and R */
function inoBalTicks(g,bx,yb2,bw2){const L=INS.look();g.save();g.strokeStyle=L.tick;g.lineWidth=INS.hair(g,1);g.beginPath();for(let i=0;i<=4;i++){const x=INS.px(g,bx+bw2*i/4);g.moveTo(x,yb2+7);g.lineTo(x,yb2+(i%2?8.5:10))}g.stroke();g.restore()}
/* the master box's Stereo read-out: a real minus, the phase angle */
function inoMaster(me,v){const b=me.querySelector('b');if(!b)return;if(v==null){b.textContent='–';return}const t=INS.num(v,2,true)+' '+Math.round(Math.acos(Math.max(-1,Math.min(1,v)))*180/Math.PI)+'°';if(b.textContent!==t)b.textContent=t}
/* O4 in the stereo field's right-click menu: the picture */
{const o=mxMenuItems;mxMenuItems=function(v){const it=o.apply(this,arguments);if(v!=='stereo')return it;const p=!!mxOpt('stereo','pol');
  it.push('-',{head:'Picture'},{label:'Stereo field',sub:'mono is an upright line, left and right on the diagonals',check:!p,act:()=>mxSet('stereo','pol',false)},{label:'Polar view',sub:'up is mono, 45° is only left or only right, outside that is out of phase; rings every 12 dB',check:p,act:()=>mxSet('stereo','pol',true)});return it}}
/* ===== end of lane E IN-O ===== */
