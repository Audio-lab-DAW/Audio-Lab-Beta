
/* ===== lane D (task NI-10a): I7 draw the arc, part 1 =====
   Draw the energy you want over the song, in NI-6's energy lane, on its own scale (0 to 1). Stored with the song as S.ni_arc
   ({v:1, line:[one value per beat, or null]}); a project without it has no line. Where the measured energy sits clearly under the line
   (0.06 or more, for at least a bar, gaps of up to 2 beats joined) the stretch is marked: "bars 9 to 12 sit about 20 dB under your line".
   The dB is the loudness change that would close the gap if loudness alone moved (energy is 55 % loudness over a 30 dB scale).
   Drawing is one undo step per stroke; nothing is measured that NI-6 does not already measure; drawn only in drawArr's normal redraw. */
NI.al={draw:false,st:null,sh:null,shKey:'',strokes:0};
const NI_AL_MIN=.06,NI_AL_COL='#3ecf8e';
function NI_alLine(){const a=S.ni_arc;return a&&a.v===1&&Array.isArray(a.line)?a.line:null}
function NI_alHas(){const L=NI_alLine();return!!L&&L.some(v=>v!=null)}
/* set the line over [b0, b1) from v0 to v1 (a straight piece); v null erases */
function NI_alSet(b0,b1,v0,v1){if(!S.ni_arc||S.ni_arc.v!==1||!Array.isArray(S.ni_arc.line))S.ni_arc={v:1,line:[]};const L=S.ni_arc.line,a=Math.max(0,Math.floor(Math.min(b0,b1))),e=Math.max(a+1,Math.ceil(Math.max(b0,b1)));
  while(L.length<e)L.push(null);for(let b=a;b<e;b++){if(v0==null){L[b]=null;continue}const f=e-a>1?(b-a)/(e-a-1):0,v=b0<=b1?v0+(v1-v0)*f:v1+(v0-v1)*f;L[b]=Math.round(clamp(v,0,1)*1000)/1000}
  while(L.length&&L[L.length-1]==null)L.pop();if(!L.length)delete S.ni_arc;NI.al.shKey=''}
function NI_alClear(){if(!NI_alHas())return;pushUndo();delete S.ni_arc;NI.al.shKey='';changed(false);dirty=true;toast('Your energy line is cleared. Undo brings it back.')}
/* the stretches under the line: [{b0, b1, gap (energy), db, txt}] */
function NI_alShort(){const L=NI_alLine();if(!L)return[];const d=NI.arc.data(),k=NI_sig()+'|'+JSON.stringify(L).length+'|'+L.reduce((a,v,i)=>a+(v==null?0:v*(i+1)),0)+'|'+(d.all-d.left)+'|'+d.nb;
  if(NI.al.shKey===k&&NI.al.sh)return NI.al.sh;const out=[],n=Math.min(L.length,d.nb);let b=0;
  while(b<n){const s=i=>i<n&&L[i]!=null&&!d.unk[i]&&L[i]-d.E[i]>=NI_AL_MIN;if(!s(b)){b++;continue}let e=b+1,gap=0,last=b;
    for(;e<n;e++){if(s(e)){last=e;gap=0}else if(++gap>2)break}let a=b,z=last+1;const nx=z;
    /* the edges: NI-6 smooths over 4 beats, so trim the beats where the gap is under half of the stretch's middle gap */
    {const gs=[];for(let i=a;i<z;i++)if(L[i]!=null&&!d.unk[i])gs.push(L[i]-d.E[i]);gs.sort((p,q)=>p-q);const md=gs.length?gs[gs.length>>1]:0,gp=i=>L[i]==null||d.unk[i]?0:L[i]-d.E[i];
     while(a<z-1&&gp(a)<md/2)a++;while(z-1>a&&gp(z-1)<md/2)z--}
    let sum=0,c=0;for(let i=a;i<z;i++)if(L[i]!=null&&!d.unk[i]){sum+=Math.max(0,L[i]-d.E[i]);c++}
    if(z-a>=4&&c){const g=sum/c,db=Math.round(g/NI_ARC_W.l*30),A0=NI_bb(a),Z=NI_bb(z-1);out.push({b0:a,b1:z,gap:g,db,bar0:A0.bar,bar1:Z.bar,txt:`${A0.bar===Z.bar?'bar '+A0.bar:'bars '+A0.bar+' to '+Z.bar} ${A0.bar===Z.bar?'sits':'sit'} about ${db} dB under your line`})}
    b=nx}
  NI.al.sh=out;NI.al.shKey=k;return out}
/* drawn after NI-6's lane, on the same scale */
function NI_alDraw(g,w){const L=NI_alLine(),A=NI.al;if(!L&&!A.draw)return;const d=NI.arc.data(),y=NI_arcY(),h=NI_ARC_H,right=!!UI.tracksRight,xr=right?X0+arrW:w,top=y+5,bh=h-10,Y=v=>top+(1-v)*bh,bx=b=>X0+(b-V.x)*V.ppb;
  g.save();g.beginPath();g.rect(X0,y,xr-X0,h-1);g.clip();
  if(L){const b0=Math.max(0,Math.floor(V.x)-1),b1=Math.min(L.length,Math.ceil(V.x+(xr-X0)/V.ppb)+1),sh=NI_alShort();
    /* the shortfall: the band between the line and the energy, and its size */
    g.fillStyle='rgba(255,107,107,.32)';for(const r of sh){if(r.b1<b0||r.b0>b1)continue;g.beginPath();g.moveTo(bx(r.b0),Y(L[r.b0]));for(let b=r.b0;b<r.b1;b++)if(L[b]!=null)g.lineTo(bx(b+.5),Y(L[b]));g.lineTo(bx(r.b1),Y(L[r.b1-1]??0));
      for(let b=r.b1-1;b>=r.b0;b--)g.lineTo(bx(b+.5),Y(d.unk[b]?L[b]??0:Math.min(L[b]??0,d.E[b])));g.closePath();g.fill()}
    g.strokeStyle=NI_AL_COL;g.lineWidth=1.6;g.beginPath();let on=false;for(let b=b0;b<b1;b++){const v=L[b];if(v==null){on=false;continue}const x=bx(b+.5),yy=Y(v);if(on)g.lineTo(x,yy);else{g.moveTo(bx(b),yy);g.lineTo(x,yy);on=true}if(b+1>=L.length||L[b+1]==null)g.lineTo(bx(b+1),yy)}g.stroke();
    g.font='600 9px '+INS.look().mono;g.textBaseline='middle';for(const r of sh){const x0=Math.max(X0+4,bx(r.b0)+4),x1=bx(r.b1);if(x1<X0||x0>xr)continue;const t='−'+r.db+'\u2009dB',tw=g.measureText(t).width+8;if(x1-x0<tw)continue;
      const yy=Math.min(top+bh-7,Y(L[r.b0]??.5)+9);g.fillStyle='rgba(8,10,14,.85)';rr(g,x0,yy-6.5,tw,13,3);g.fill();g.fillStyle='#ff8f8f';g.fillText(t,x0+4,yy)}g.textBaseline='alphabetic'}
  if(A.draw){const t='Drawing your line: drag across the lane. Alt-drag erases. Esc or right-click ends.';g.font='9px Inter,system-ui,sans-serif';const tw=g.measureText(t).width+8;g.fillStyle='rgba(8,10,14,.8)';rr(g,X0+4,y+3,tw,13,3);g.fill();g.fillStyle=NI_AL_COL;g.fillText(t,X0+8,y+12.5)}
  g.restore()}
function NI_alMode(on){const A=NI.al;A.draw=!!on;A.st=null;if(on&&!UI.niArc)NI_arcShow(true);dirty=true;if(on)toast('Draw the energy you want: drag across the energy lane under the sections. Alt-drag erases; Esc ends.')}
/* the stretches as one sentence, for a toast and the menu */
function NI_alSay(){const sh=NI_alShort(),d=NI.arc.data();if(!NI_alHas())return'';if(!d.complete)return'Still measuring the song: the shortfall shows as it fills in.';
  if(!sh.length)return'The song reaches your line everywhere it is drawn.';return sh.slice(0,3).map(r=>r.txt).join('; ')+(sh.length>3?`; and ${sh.length-3} more`:'')+'.'}
{const lp=e=>{const{x,y}=arrPt(e),Y0=NI_arcY(),top=Y0+5,bh=NI_ARC_H-10;return{b:V.x+(x-X0)/V.ppb,v:clamp(1-(y-top)/bh,0,1),inLane:NI_arcH()&&y>=Y0&&y<Y0+NI_ARC_H&&x>=X0&&x<=X0+arrW}};
 document.addEventListener('pointerdown',e=>{const A=NI.al;if(!A.draw||e.target!==arr||e.button!==0)return;const p=lp(e);if(!p.inLane)return;e.stopImmediatePropagation();e.preventDefault();
   pushUndo();A.st={b:p.b,v:p.v,er:e.altKey};NI_alSet(p.b,p.b+1,e.altKey?null:p.v,p.v);dirty=true;try{arr.setPointerCapture(e.pointerId)}catch(_){}},true);
 document.addEventListener('pointermove',e=>{const A=NI.al;if(!A.st)return;const p=lp(e),s=A.st;if(Math.floor(p.b)!==Math.floor(s.b)||Math.abs(p.v-s.v)>.002){NI_alSet(s.b,p.b,s.er?null:s.v,p.v);A.st={b:p.b,v:p.v,er:s.er};dirty=true}},true);
 const end=e=>{const A=NI.al;if(!A.st)return;A.st=null;A.strokes++;changed(false);dirty=true;const t=NI_alSay();if(t)toast(t)};
 document.addEventListener('pointerup',end,true);document.addEventListener('pointercancel',end,true);
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&NI.al.draw){NI_alMode(false);e.stopPropagation()}},true);
 arr.addEventListener('contextmenu',e=>{if(!NI.al.draw)return;const p=lp(e);if(!p.inLane)return;e.preventDefault();e.stopImmediatePropagation();NI_alMode(false)},true)}
{const base=NI_arcDraw;NI_arcDraw=function(g,w){base.apply(this,arguments);try{NI_alDraw(g,w)}catch(e){console.warn('NI draw the arc',e)}}}
/* the energy lane's menu: draw, clear, and the stretches (click to go there) */
function NI_alMenuItems(){const it=[{label:NI.al.draw?'Stop drawing your line':'Draw your line…',sub:'the energy you want over the song; the parts under it are marked',act:()=>NI_alMode(!NI.al.draw)}];
  if(NI_alHas()){for(const r of NI_alShort().slice(0,6))it.push({label:r.txt.charAt(0).toUpperCase()+r.txt.slice(1),sub:'go there',act:()=>{if(play.on)stop();pos=r.b0;syncTransportUI();dirty=true}});
    it.push({label:'Clear your line',act:()=>NI_alClear()})}it.push('-');return it}
NI.al.set=NI_alSet;NI.al.clear=NI_alClear;NI.al.short=NI_alShort;NI.al.mode=NI_alMode;NI.al.line=NI_alLine;NI.al.say=NI_alSay;
NI_HOOKS.arcLine={line:NI_alLine,short:NI_alShort,set:NI_alSet,mode:NI_alMode};
/* ===== end of lane D NI-10a ===== */
