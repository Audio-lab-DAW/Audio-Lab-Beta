/* ===== v0.287 (task SC-A, lane G): the science look's shared drawing module (docs/science-look-round-2.md, step SC-A) =====
   One place for the science drawings that the later steps (SC-B to SC-K) put into the app:
   - SCI.D: the drawings as plain functions that paint into any canvas context: orbits (the orbit chart S7: rings, tick ring, dashed cross,
     bodies), corner (orbit corner B2), field (dipole field lines S1 and B3), lissa (Lissajous figure S4), harm (string harmonics B4),
     comb (harmonic comb with the amber bracket that measures the pitch), spec (a small spectrogram picture fed one column at a time, S6),
     lab (the small amber mono label) and dot. Each takes a strength k from 0 to 1 (faint 0.45, normal 1) and draws nothing at 0;
     labels only at normal, and they must carry true values. Ported from the pick page of round 2, colours as today (LB, AM, CY, OR).
   - SCI.view({cv, place, paint, move}): a canvas that the module sizes (device pixels, up to 2x) and paints with paint(g,w,h,t,k,view).
     move:false (working surfaces) = one picture, painted again only when its size, the level or the settings change.
     move:true (empty and waiting states) = painted by ONE shared timer at 30 pictures a second at most, only while the canvas is on screen;
     the timer stops by itself when no moving view is shown (an owner that shows its canvas again calls view.wake()).
     Frames are asked for through the app's frame gate, so the background freeze (task AO) holds them.
   - The rules: Motion other than Ambient (Appearance), "reduce motion" and Light mode make every view still; Light mode draws nothing at all
     (the user's pick W14 off); Interface > Science drawings off (UI.scOn false) draws nothing anywhere.
   - Strength per place: SCI_DEF holds the user's picks (W3 and W14 off); UI.scW (hidden, no control) can override one place: {W2:'off'}.
   No visible change in this step: no place uses a view yet. No cost while no view exists (no timer, no listener, no observer).
   Names start with SCI / sci (the prefix sc of lane G; SC is a local name in older code). */
const SCI_DEF={W1:'normal',W2:'faint',W3:'off',W4:'faint',W5:'normal',W6:'normal',W7:'normal',W8:'normal',W9:'faint',W10:'faint',W11:'faint',W12:'faint',W13:'faint',W14:'off'};
const SCI=(()=>{const TAU=Math.PI*2,D=document,V=new Set(),MONO='"JetBrains Mono",ui-monospace,Menlo,monospace';
 const C={LB:'110,160,255',AM:'255,182,39',CY:'76,201,240',OR:'255,196,60',WH:'255,255,255'};
 const A=(v,a)=>'rgba('+v+','+Math.max(0,Math.min(1,a)).toFixed(3)+')';
 const st={raf:0,last:-1e9,fr:0,ticks:0,mo:null,rs:null,lite:null,still:null};
 const body=()=>D.body;
 const lite=()=>{const b=body();return!!(b&&b.classList.contains('lite'))};
 function on(){return typeof UI!=='object'||!UI||UI.scOn!==false}
 function strength(p){const u=typeof UI==='object'&&UI&&UI.scW||null,w=(u&&u[p])||SCI_DEF[p]||'off';return w==='normal'?1:w==='faint'?.45:0}
 /* the strength a place draws at now; 0 = nothing at all */
 function level(p){if(!on())return 0;let k=strength(p);if(k&&lite()){const l=strength('W14');if(!l)return 0;k=Math.min(k,l)}return k}
 /* true: every view is one still picture */
 function still(){try{if(typeof AT==='object'&&AT&&AT.reduce)return true}catch(e){}const b=body();return lite()||!!(b&&b.classList.contains('lkstill'))}

 /* ---------- the drawings ---------- */
 function dot(g,x,y,r,f){g.fillStyle=f;g.beginPath();g.arc(x,y,r,0,TAU);g.fill()}
 /* the small amber mono label; only at normal strength */
 function lab(g,s,x,y,k,al,px){if(k<1)return;g.font='500 '+(px||9)+'px '+MONO;g.textAlign=al||'left';g.textBaseline='middle';g.fillStyle=A(C.AM,.88);if('letterSpacing' in g)g.letterSpacing='0.1em';g.fillText(s,x,y);if('letterSpacing' in g)g.letterSpacing='0px'}
 /* orbit chart: o.n rings (3), o.ticks a tick ring, o.cross a dashed cross, o.rate turns per second scaled by o.rates[i] (or i+1),
    o.ang[i] a fixed angle per body (a tempo-locked caller sets them), o.names labels at normal */
 function orbits(g,cx,cy,R,t,k,o){if(!(k>0))return;o=o||{};const n=o.n||3;g.lineWidth=1;
  if(o.cross){g.setLineDash([3,4]);g.strokeStyle=A(C.AM,.25*k);g.beginPath();g.moveTo(cx-R*1.5,cy+.5);g.lineTo(cx+R*1.5,cy+.5);g.moveTo(cx+.5,cy-R*1.5);g.lineTo(cx+.5,cy+R*1.5);g.stroke();g.setLineDash([])}
  if(o.ticks){const RT=R*1.16;g.strokeStyle=A(C.LB,.4*k);g.beginPath();for(let i=0;i<72;i++){const a=i/72*TAU,l=i%6?2.5:6,ca=Math.cos(a),sa=Math.sin(a);g.moveTo(cx+ca*RT,cy+sa*RT);g.lineTo(cx+ca*(RT+l),cy+sa*(RT+l))}g.stroke()}
  for(let i=0;i<n;i++){const r=R*(n>1?.42+.58*i/(n-1):1),a=o.ang&&o.ang[i]!=null?o.ang[i]:-t*(o.rate||.45)*(o.rates?o.rates[i]:i+1)+i*1.7;
   g.lineWidth=1;g.strokeStyle=A(C.LB,.38*k);g.beginPath();g.arc(cx,cy,r,0,TAU);g.stroke();
   g.strokeStyle=A(C.CY,.8*k);g.lineWidth=1.4;g.beginPath();g.arc(cx,cy,r,a-.6,a);g.stroke();g.lineWidth=1;
   const x=cx+Math.cos(a)*r,y=cy+Math.sin(a)*r;dot(g,x,y,2,A(C.OR,k));if(o.names&&o.names[i])lab(g,o.names[i],x+5,y-7,k,'left',o.px)}
  if(o.core)dot(g,cx,cy,2.4,A(C.OR,.9*k))}
 /* orbit corner (B2): tick rings centred at (cx,cy), usually a corner just outside the box */
 function corner(g,cx,cy,W,k,t){if(!(k>0))return;g.lineWidth=1;const RR=[.34,.5,.66,.82,.98];
  for(let i=0;i<RR.length;i++){const R=RR[i]*W;g.strokeStyle=A(C.LB,.22*k);g.beginPath();g.arc(cx,cy,R,0,TAU);g.stroke();
   const a=Math.PI*1.25+Math.sin((t||0)*.08*(1+i*.3)+i*2)*.38;dot(g,cx+Math.cos(a)*R,cy+Math.sin(a)*R,1.6,A(C.OR,.75*k))}
  g.strokeStyle=A(C.LB,.28*k);g.beginPath();const R=W*.66;for(let i=0;i<180;i++){const a=i/180*TAU,l=i%5?2.5:5,ca=Math.cos(a),sa=Math.sin(a);g.moveTo(cx+ca*R,cy+sa*R);g.lineTo(cx+ca*(R+l),cy+sa*(R+l))}g.stroke()}
 /* dipole field lines r = L sin^2(theta) around (cx,cy), turned by rot; o.L the shells, o.r0 a surface they start from, o.a line strength,
    o.still no moving charges */
 function field(g,cx,cy,R,rot,t,k,o){if(!(k>0))return;o=o||{};const r0=o.r0||0,Ls=o.L||[.16,.25,.37,.52,.72,1,1.4,2],al=o.a||.3;g.save();g.translate(cx,cy);g.rotate(rot||0);g.lineWidth=1;
  for(let i=0;i<Ls.length;i++){const L=Ls[i],th0=r0?Math.asin(Math.sqrt(Math.min(1,r0/(L*R)))):0,sp=Math.PI-2*th0;
   for(const sg of[-1,1]){g.beginPath();for(let j=0;j<=40;j++){const th=th0+j/40*sp,s=Math.sin(th),r=L*R*s*s,x=sg*r*s,y=-r*Math.cos(th);j?g.lineTo(x,y):g.moveTo(x,y)}
    g.strokeStyle=A(C.LB,al*k);g.stroke();
    if(!o.still){const th=th0+(((t*(.1/(.5+L))+i*.37+(sg>0?0:.5))%1+1)%1)*sp,s=Math.sin(th),r=L*R*s*s;dot(g,sg*r*s,-r*Math.cos(th),1.2,A(C.OR,Math.min(1,al*3)*k))}}}
  g.restore()}
 /* Lissajous figure x = sin(a u + d), y = sin(b u); o.dot the phase u of a moving dot */
 function lissa(g,cx,cy,Ax,By,a,b,d,k,o){if(!(k>0))return;o=o||{};g.beginPath();for(let i=0;i<=240;i++){const u=i/240*TAU,x=cx+Ax*Math.sin(a*u+d),y=cy+By*Math.sin(b*u);i?g.lineTo(x,y):g.moveTo(x,y)}
  g.strokeStyle=A(C.CY,.5*k);g.lineWidth=1;g.stroke();if(o.dot!=null)dot(g,cx+Ax*Math.sin(a*o.dot+d),cy+By*Math.sin(b*o.dot),1.8,A(C.OR,k))}
 /* string harmonics (B4): the first o.n standing waves of a string from x to x+w, swinging slowly */
 function harm(g,x,y,w,h,t,k,o){if(!(k>0))return;o=o||{};const n=o.n||3;g.strokeStyle=A(C.LB,.3*k);g.lineWidth=1;
  for(let m=1;m<=n;m++){g.beginPath();for(let i=0;i<=60;i++){const xx=x+w*i/60,yy=y+h/2+Math.sin(m*Math.PI*i/60)*h*.42/m*Math.cos(t*(2+m));i?g.lineTo(xx,yy):g.moveTo(xx,yy)}g.stroke()}}
 /* harmonic comb: a line per harmonic of f0 on a linear axis to fmax, the first amber; the bracket measures f0 to 2 f0 (the pitch) */
 function comb(g,x,y,w,h,f0,fmax,k,o){if(!(k>0)||!(f0>0))return;o=o||{};const xf=f=>x+w*f/fmax,u=o.grow==null?1:o.grow;
  for(let m=1;m*f0<fmax;m++){const xx=Math.round(xf(m*f0))+.5,hh=h*.8/Math.sqrt(m)*u;g.strokeStyle=m===1?A(C.AM,.95*k):A(C.CY,.85*k);g.lineWidth=1.5;g.beginPath();g.moveTo(xx,y+h);g.lineTo(xx,y+h-hh);g.stroke()}
  if(o.bracket!==false&&2*f0<fmax){const a=xf(f0),b=xf(2*f0),by=y+4;g.strokeStyle=A(C.AM,.9*Math.max(.45,k));g.lineWidth=1;g.beginPath();g.moveTo(a,by-2.5);g.lineTo(a,by+2.5);g.moveTo(b,by-2.5);g.lineTo(b,by+2.5);g.moveTo(a,by+.5);g.lineTo(b,by+.5);g.stroke();
   if(o.label)lab(g,o.label,b+6,by,k,'left',o.px)}}
 /* spectrogram (S6): a small picture (bw x bh) that scrolls left by one column per push(m); m = magnitudes 0 to 1, low frequencies first.
    draw() scales it into a box, revealing frac of its width (an export that grows left to right) with the amber line at the front */
 const SPC=[[5,7,13],[20,48,110],[63,184,232],[255,210,58]];
 function spec(bw,bh){const c=D.createElement('canvas');c.width=bw;c.height=bh;const x=c.getContext('2d');x.fillStyle='rgb(5,7,13)';x.fillRect(0,0,bw,bh);const col=x.createImageData(1,bh),o=col.data;
  const S={c,n:0,push(m){const L=m.length;for(let yy=0;yy<bh;yy++){const q=L?m[Math.min(L-1,Math.floor((bh-1-yy)/bh*L))]:0,v=Math.max(0,Math.min(.999,q||0))*3,i=v|0,f=v-i,a=SPC[i],b=SPC[i+1],p=yy*4;o[p]=a[0]+(b[0]-a[0])*f;o[p+1]=a[1]+(b[1]-a[1])*f;o[p+2]=a[2]+(b[2]-a[2])*f;o[p+3]=255}
    x.globalCompositeOperation='copy';x.drawImage(c,-1,0);x.globalCompositeOperation='source-over';x.putImageData(col,bw-1,0);S.n++},
   /* at a fixed position (an export: column i of n) instead of scrolling */
   put(i,m){const L=m.length;for(let yy=0;yy<bh;yy++){const q=L?m[Math.min(L-1,Math.floor((bh-1-yy)/bh*L))]:0,v=Math.max(0,Math.min(.999,q||0))*3,j=v|0,f=v-j,a=SPC[j],b=SPC[j+1],p=yy*4;o[p]=a[0]+(b[0]-a[0])*f;o[p+1]=a[1]+(b[1]-a[1])*f;o[p+2]=a[2]+(b[2]-a[2])*f;o[p+3]=255}x.putImageData(col,Math.max(0,Math.min(bw-1,i|0)),0);S.n++},
   draw(g,X,Y,W,H,k,frac){if(!(k>0))return;const fr=frac==null?1:Math.max(0,Math.min(1,frac));g.save();g.beginPath();g.rect(X,Y,W*fr,H);g.clip();g.globalAlpha=.3+.6*k;g.imageSmoothingEnabled=true;g.drawImage(c,X,Y,W,H);g.restore();
    if(frac!=null&&fr<1){const lx=Math.round(X+W*fr)+.5;g.strokeStyle=A(C.AM,.9);g.lineWidth=1;g.beginPath();g.moveTo(lx,Y);g.lineTo(lx,Y+H);g.stroke()}}};
  return S}

 /* ---------- views and the one timer ---------- */
 function shown(h){const c=h.cv;return c.isConnected&&D.visibilityState==='visible'&&c.getClientRects().length>0}
 function fit(h){const c=h.cv,w=c.clientWidth,hh=c.clientHeight;if(!w||!hh)return false;const r=c.getBoundingClientRect(),z=r.width/w,sc=Math.min((window.devicePixelRatio||1)*(z>.3&&z<4?z:1),2),pw=Math.max(1,Math.round(w*sc)),ph=Math.max(1,Math.round(hh*sc));
  if(c.width!==pw||c.height!==ph){c.width=pw;c.height=ph}h.w=w;h.h=hh;h.sc=sc;return true}
 const moving=h=>h.move&&!still()&&level(h.place)>0;
 /* paint one view; force: also when nothing changed (a moving view's next picture) */
 function paint(h,ts,force){if(!h.on)return false;const k=level(h.place);
  /* hidden: nothing is drawn; a picture that is switched off is cleared once, so it cannot come back stale */
  if(!shown(h)){if(!k&&h.k){h.g.setTransform(1,0,0,1,0,0);h.g.clearRect(0,0,h.cv.width,h.cv.height);h.k=0}h.drawn=false;return false}if(!force&&h.drawn&&k===h.k&&h.w)return false;if(!h.w&&!fit(h))return false;
  const g=h.g,mv=moving(h);g.setTransform(h.sc,0,0,h.sc,0,0);g.clearRect(0,0,h.w,h.h);
  if(k>0){try{h.paint(g,h.w,h.h,mv?(ts-h.t0)/1000:h.tStill,k,h)}catch(e){console.error('AudioLab science drawing',e);h.on=false;V.delete(h)}}
  g.setTransform(1,0,0,1,0,0);h.k=k;h.drawn=true;h.fr++;st.fr++;return true}
 function tick(ts){st.raf=0;if(!V.size)return;let any=false;const due=ts-st.last>=32;if(due){st.last=ts;st.ticks++}
  for(const h of[...V]){if(!h.cv.isConnected){h.stop();continue}if(moving(h)){if(!shown(h)){h.drawn=false;continue}any=true;if(due)paint(h,ts,true)}else if(!h.drawn)paint(h,ts,false)}
  if(any)st.raf=requestAnimationFrame(tick)}
 function wake(){if(!st.raf&&V.size)st.raf=requestAnimationFrame(tick)}
 /* every view again on its next frame (a setting, the size of the window, Light mode or Motion changed) */
 function refresh(){for(const h of V){h.drawn=false;h.w=0}wake()}
 function onRs(){if(st.rsT)return;st.rsT=setTimeout(()=>{st.rsT=0;refresh()},120)}
 /* Light mode and Motion arrive as classes on the body: watched only while a view exists */
 function onCls(){const l=lite(),s=still();if(l!==st.lite||s!==st.still){st.lite=l;st.still=s;refresh()}}
 function listen(onOff){if(onOff&&!st.mo){st.lite=lite();st.still=still();st.mo=new MutationObserver(onCls);if(body())st.mo.observe(body(),{attributes:true,attributeFilter:['class']});addEventListener('resize',onRs)}
  else if(!onOff&&st.mo){st.mo.disconnect();st.mo=null;removeEventListener('resize',onRs)}}
 function view(o){if(!o||!o.cv||typeof o.paint!=='function')return null;
  const h={cv:o.cv,g:o.cv.getContext('2d'),place:o.place||'',paint:o.paint,move:!!o.move,tStill:o.tStill==null?40:o.tStill,t0:performance.now(),k:-1,w:0,h:0,sc:1,fr:0,on:true,drawn:false,data:o.data||{}};
  h.redraw=()=>{if(!h.on)return;h.drawn=false;h.w=0;wake()};
  h.wake=()=>{if(h.on){if(!h.drawn)h.w=0;wake()}};
  h.setMove=m=>{h.move=!!m;h.drawn=false;wake()};
  h.stop=()=>{if(!h.on)return;h.on=false;V.delete(h);if(!V.size){listen(false);if(st.raf){cancelAnimationFrame(st.raf);st.raf=0}}};
  V.add(h);listen(true);paint(h,performance.now(),true);wake();return h}
 return{DEF:SCI_DEF,C,A,D:{dot,lab,orbits,corner,field,lissa,harm,comb,spec},level,strength,still,on,view,wake,refresh,
  frames:()=>st.fr,ticks:()=>st.ticks,running:()=>!!st.raf,views:()=>V.size,watching:()=>!!st.mo}})();
/* the setting: Interface (Layout page), in the Density and motion block, under Caliper while dragging */
const SCI_ROWS=[{"id":"scOn","l":"Science drawings","pg":"layout","ap":"appearance","b":"Density and motion","sc":"app","k":"UI.scOn","c":"#scOnChk","t":"check","d":true,"h":"Faint science drawings (orbits, field lines, harmonics, a spectrogram) on empty and waiting screens. They never move where you work, stand still unless Motion is Ambient, and Light mode never shows them. Off: none anywhere.","w":"science drawings orbits orbit field lines harmonics spectrogram background decoration ambient look interface"}];
{const a=document.getElementById('mdCalChk'),m=document.getElementById('lkMotion'),row=(a||m)&&(a||m).closest('.row');if(row&&!document.getElementById('scOnChk')){const r=document.createElement('div');r.className='row';r.title=SCI_ROWS[0].h;r.innerHTML='<label class="chk" style="margin:0"><input type="checkbox" id="scOnChk"> Science drawings</label>';row.after(r);
  const c=r.querySelector('input');c.checked=UI.scOn!==false;c.onchange=()=>{UI.scOn=c.checked;saveUI();SCI.refresh()}}}
try{for(const r of SCI_ROWS)if(!STX.has(r.id)){STT.push(r);STX.set(r.id,r)}}catch(e){}
const SCI_HOOKS=window.SCI_HOOKS=Object.assign(window.SCI_HOOKS||{},{view:SCI.view,level:SCI.level,draw:SCI.D,refresh:SCI.refresh});
