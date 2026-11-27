/* ===== lane E (task IN-C and IN-D): the CPU graph (C1) and the scope preview in devices (D1) =====
   C1, load against budget (docs/design-round-4-instruments.md, family C): the top bar's CPU graph keeps today's filled history and gets a budget
   tick at 75 % (amber); the area is green below the budget and red only above it. The Performance pop-up gets the same graph large, with a 0, 50
   and 100 % scale, the dashed budget line and three read-outs: now, the highest of the last 4 s and the main thread's time per screen frame.
   Nothing new is measured: the load is cpuFrame's own (the audio thread's load, the interface, the voices), sampled every 100 ms as today.
   INC.btn is the one CPU graph drawer: DS-T2's TC1 (lane A) reuses it.
   D1, scope preview (family D): the Soft Clipper's waveform pane shows the last 300 ms as min and max columns (no aliasing), the input faint behind
   the output, a centre line and faint lines at +-0.5 with their numbers, a time scale bar (X11), the output's peak in dBFS (digital peak, held 2 s)
   and red marks at the edge where the output touched full scale. The Bitcrusher keeps its staircase (it shows what the device does) and gets the
   same scale, scale bar, peak read-out and full-scale marks. Analysers are only read (INS.td, once a frame; INS.fresh finds the new samples):
   no audio node is made, the sound does not change. */
const INC={h:new Float32Array(120),i:0,n:0,li:-1,pk:0,BUD:.75,cv:null,
  GREEN:'rgba(62,207,142,.35)',RED:'rgba(255,77,77,.5)',
  /* every 100 ms from cpuFrame: the highest load of the frames since the last call goes into a 12 s history (120 points) */
  tick(now,load){let m=load;if(INC.li>=0){for(let k=INC.li;k!==CPU.i;k=(k+1)%120){const v=CPU.hist[(k+1)%120];if(v>m)m=v}}INC.li=CPU.i;
    INC.i=(INC.i+1)%120;INC.h[INC.i]=m;INC.n=Math.min(120,INC.n+1);let p=0;for(let k=0;k<Math.min(40,INC.n);k++){const v=INC.h[(INC.i-k+120)%120];if(v>p)p=v}INC.pk=p;
    const P=$('#cpuPop');if(P&&!P.hidden&&INC.cv&&INC.cv.isConnected)INC.big()},
  /* the filled area, green below the budget and red above it (clipped twice, one path) */
  area(g,x,y,w,h,get,n,bud){const Y=v=>y+h-Math.min(1,Math.max(0,v))*h,path=()=>{g.beginPath();g.moveTo(x,y+h);for(let k=0;k<n;k++)g.lineTo(x+(n>1?k/(n-1):0)*w,Y(get(k)));g.lineTo(x+w,y+h);g.closePath()},yb=Y(bud);
    g.save();path();g.clip();g.fillStyle=INC.GREEN;g.fillRect(x,yb,w,y+h-yb);g.fillStyle=INC.RED;g.fillRect(x,y,w,yb-y);g.restore();return Y},
  /* the button's graph (the one drawer; DS-T2's TC1 uses it too): today's history of the last 120 frames, the budget tick */
  btn(g,w,h){const L=INS.look();g.fillStyle='#050608';g.fillRect(0,0,w,h);const Y=INC.area(g,0,1,w,h-2,k=>CPU.hist[(CPU.i+1+k)%120],120,INC.BUD);
    const yb=INS.px(g,Y(INC.BUD));g.strokeStyle=L.unit;g.globalAlpha=.8;g.lineWidth=INS.hair(g,L.lwLine);g.beginPath();g.moveTo(0,yb);g.lineTo(w,yb);g.stroke();g.globalAlpha=1},
  /* the pop-up: kept across the pop-up's rebuilds (its HTML is replaced when a value changes) */
  pop(P){if(!P)return;let c=INC.cv;if(!c){c=INC.cv=document.createElement('canvas');c.className='incC';c.title='Load against the budget: below the amber line at 75 % the computer keeps up; above it dropouts become likely. The last 12 seconds.'}
    if(c.parentNode!==P||c.previousElementSibling!==P.firstElementChild){const b=P.firstElementChild;if(b&&b.nextSibling)P.insertBefore(c,b.nextSibling);else P.appendChild(c)}INC.big()},
  big(){const c=INC.cv;if(!c||!c.isConnected||!c.clientWidth)return;const{g,w,h}=fit(c),L=INS.look();g.clearRect(0,0,w,h);
    const x0=24,y0=6,gw=w-x0-2,gh=h-36,Y=v=>y0+gh-gh*Math.min(1,v),n=Math.max(2,INC.n);g.fillStyle='#050608';g.fillRect(x0,y0,gw,gh);
    g.lineWidth=INS.hair(g,L.lwGrid);g.font='7px '+L.mono;g.textAlign='right';g.textBaseline='middle';
    for(const v of[0,.25,.5,1]){const yy=INS.px(g,Y(v));g.strokeStyle=v===.5||v===1||v===0?L.gMaj:L.gMid;g.beginPath();g.moveTo(x0,yy);g.lineTo(x0+gw,yy);g.stroke();if(v!==.25){g.fillStyle=L.mut;g.fillText(Math.round(v*100)+'%',x0-3,Y(v))}}
    INC.area(g,x0,y0,gw,gh,k=>INC.h[(INC.i-(n-1-k)+1200)%120],n,INC.BUD);
    const yb=INS.px(g,Y(INC.BUD));g.strokeStyle=L.unit;g.globalAlpha=.85;g.setLineDash([4,3]);g.beginPath();g.moveTo(x0,yb);g.lineTo(x0+gw,yb);g.stroke();g.setLineDash([]);g.globalAlpha=1;
    g.textBaseline='bottom';g.textAlign='right';g.fillStyle=L.unit;g.font='6.5px '+L.mono;g.fillText('BUDGET 75 %',x0+gw-3,yb-2);g.textAlign='left';g.fillStyle=L.mut;g.fillText('12 S',x0+3,y0+gh-2);
    const ms=(typeof FPS==='object'&&FPS.js)||0,fr=typeof FPS==='object'&&FPS.hz>0?1000/FPS.hz:16.7,now=INC.h[INC.i]||0,ry=y0+gh+15,cw=gw/3;
    const rd=(x,num,unit,lab,hot)=>{g.textBaseline='alphabetic';g.textAlign='left';g.font='600 11px '+L.mono;g.fillStyle=hot?'#ff6b6b':L.ink;g.fillText(num,x,ry);const tw=g.measureText(num).width;g.font='7px '+L.mono;g.fillStyle=L.unit;g.fillText(unit,x+tw+2,ry);g.fillStyle=L.mut;g.font='6.5px '+L.mono;g.fillText(lab,x,ry+11)};
    rd(x0,String(Math.round(now*100)),'%','NOW',now>INC.BUD);rd(x0+cw,String(Math.round(INC.pk*100)),'%','PEAK 4 S',INC.pk>INC.BUD);rd(x0+2*cw,ms.toFixed(2),'MS','PER FRAME OF '+fr.toFixed(1),ms>fr)},
};
const IND={st:new Map(),FS:.9999,
  /* 300 ms as min and max columns from an analyser's new samples; k scales the samples (the Soft Clipper's input tap is at a quarter) */
  feed(key,an,cols,k,keep){const sr=(typeof ctx!=='undefined'&&ctx&&ctx.sampleRate)||48000;let st=IND.st.get(key);
    if(!st||st.cols!==cols||st.sr!==sr){st={cols,sr,per:.3*sr/cols,mn:new Float32Array(cols),mx:new Float32Array(cols),fs:new Uint8Array(cols),i:0,c:0,cmn:1e9,cmx:-1e9,cfs:0,t:0,pk:{}};IND.st.set(key,st)}
    if(!keep&&an.fftSize<4096)an.fftSize=4096;/* an analyser is a tap: a longer buffer only lets a late frame find all its new samples */
    const a=INS.td(an),now=performance.now(),dt=st.t?(now-st.t)/1000:0;st.t=now;const exp=dt*sr,s0=INS.fresh(a,st,exp);let m=0;
    const put=(lo,hi,f)=>{st.cmn=Math.min(st.cmn,lo);st.cmx=Math.max(st.cmx,hi);if(f)st.cfs=1;if(++st.c>=st.per){st.c-=st.per;st.mn[st.i]=st.cmn;st.mx[st.i]=st.cmx;st.fs[st.i]=st.cfs;st.i=(st.i+1)%cols;st.cmn=1e9;st.cmx=-1e9;st.cfs=0}};
    if(dt>.5){st.mn.fill(0);st.mx.fill(0);st.fs.fill(0)}else if(s0===0){/* the last samples seen were not found: more arrived than the buffer holds */const gap=Math.min(Math.round(.3*sr),Math.round(exp)-a.length);if(gap>256)for(let j=0;j<gap;j++)put(1e9,-1e9,0)}/* a gap longer than the buffer (a long frame): those columns stay empty, so the time across stays true */
    for(let j=s0;j<a.length;j++){const v=a[j]*k,av=v<0?-v:v;if(av>m)m=av;put(v,v,av>=IND.FS)}
    st.now=m;INS.peak(st.pk,m>1e-9?20*Math.log10(m):-240,dt||1/60);return st},
  /* the columns, the newest at the right */
  cols(g,st,x,y,w,h,col){const n=st.cols,c=h/2,yc=y+c,cw=Math.max(w/n,.75);g.fillStyle=col;g.beginPath();for(let q=0;q<n;q++){const j=(st.i+q)%n;let lo=st.mn[j],hi=st.mx[j];if(hi<lo)continue;lo=Math.max(-1,lo);hi=Math.min(1,hi);const y1=yc-hi*c,y2=yc-lo*c;g.rect(x+q*w/n,y1,cw,Math.max(.75,y2-y1))}g.fill()},
  /* red marks at the top and bottom edge where the signal touched full scale */
  over(g,st,x,y,w,h){const n=st.cols;g.fillStyle='#ff4d4d';for(let q=0;q<n;q++){const j=(st.i+q)%n;if(!st.fs[j])continue;const xx=x+q*w/n;if(st.mx[j]>=IND.FS)g.fillRect(xx,y,Math.max(w/n,1),2);if(st.mn[j]<=-IND.FS)g.fillRect(xx,y+h-2,Math.max(w/n,1),2)}},
  /* the scale: a centre line, faint lines at +-0.5, the numbers inside the right edge */
  scale(g,x,y,w,h,lab){const L=INS.look(),lw=INS.hair(g,L.lwGrid);g.lineWidth=lw;g.strokeStyle=L.gMaj;g.beginPath();const yc=INS.px(g,y+h/2);g.moveTo(x,yc);g.lineTo(x+w,yc);g.stroke();
    g.strokeStyle=L.gMid;g.beginPath();for(const q of[.25,.75]){const yy=INS.px(g,y+h*q);g.moveTo(x,yy);g.lineTo(x+w,yy)}g.stroke()},
  labels(g,x,y,w,h){/* drawn after the trace, so they stay readable over a full band */const L=INS.look();
    g.font='6.5px '+L.mono;g.fillStyle=L.mut;g.textAlign='right';const M=INS.MIN;[['+1',y+5],['+0.5',y+h*.25],['0',y+h/2],[M+'0.5',y+h*.75],[M+'1',y+h-5]].forEach(([s,yy])=>{g.textBaseline='middle';const tw=g.measureText(s).width;g.fillStyle='rgba(0,0,0,.6)';g.fillRect(x+w-tw-4,yy-4,tw+3,8);g.fillStyle=L.mut;g.fillText(s,x+w-2,yy)});g.textAlign='left'},
  /* X11: a time scale bar, the shortest of 1, 2, 5, 10, 20, 50, 100 ms that is 40 px or more */
  bar(g,x,y,w,ms){const L=INS.look(),pp=w/ms,len=[1,2,5,10,20,50,100].find(v=>v*pp>=40)||100,bw=len*pp;g.strokeStyle=L.unit;g.lineWidth=1;const yy=INS.px(g,y);
    g.beginPath();g.moveTo(x,yy);g.lineTo(x+bw,yy);g.moveTo(INS.px(g,x),y-3);g.lineTo(INS.px(g,x),y+3);g.moveTo(INS.px(g,x+bw),y-3);g.lineTo(INS.px(g,x+bw),y+3);g.stroke();
    g.font='6.5px '+L.mono;g.fillStyle=L.unit;g.textAlign='left';g.textBaseline='middle';g.fillText(len+' MS',x+bw+4,y);return len},
  /* a read-out: the number in ink (red at full scale), the unit amber (L2) */
  ro(g,x,y,lab,db,unit,al){const L=INS.look(),num=db>-200?INS.num(db,1,db>0):INS.MIN+'∞';g.textBaseline='alphabetic';g.font='6.5px '+L.mono;const lw=g.measureText(lab+' ').width;g.font='600 9px '+L.mono;const nw=g.measureText(num).width;g.font='6.5px '+L.mono;const uw=g.measureText(' '+unit).width,W=lw+nw+uw;
    let xx=al==='right'?x-W:x;g.fillStyle=L.mut;g.fillText(lab+' ',xx,y);xx+=lw;g.font='600 9px '+L.mono;g.fillStyle=db>-.1?'#ff6b6b':L.ink;g.fillText(num,xx,y);xx+=nw;g.font='6.5px '+L.mono;g.fillStyle=L.unit;g.fillText(' '+unit,xx,y);return W},
  /* the Soft Clipper: the transfer dot (at the real input level) and the D1 scope pane */
  clip(g,w,h,f,X,o){const p=f.p,{ox,oy,S2,R,sx,sy,b}=o,wx=ox+S2+16,ww=Math.max(40,w-wx-8),cols=Math.max(20,Math.min(400,Math.round(ww)));
    const sI=IND.feed(f.id+'|i',X.anI,cols,4),sO=IND.feed(f.id+'|o',X.anO,cols,1);
    const ai=INS.td(X.anI),xs=ai[ai.length-1]*4,v=xs+b,yv=v>=0?clipF(v,p):-clipF(-v,p);g.fillStyle='#fff';glow(g,'#fff',10);g.beginPath();g.arc(sx(clamp(xs,-R,R)),sy(clamp(yv,-R,R)),4,0,7);g.fill();g.shadowBlur=0;
    g.fillStyle='#000';g.fillRect(wx,oy,ww,S2);IND.scale(g,wx,oy,ww,S2);IND.cols(g,sI,wx,oy,ww,S2,'rgba(255,255,255,.16)');IND.cols(g,sO,wx,oy,ww,S2,'rgba(255,154,60,.9)');IND.over(g,sO,wx,oy,ww,S2);IND.labels(g,wx,oy,ww,S2);
    const L=INS.look();g.font='6.5px '+L.mono;g.textBaseline='top';g.fillStyle='rgba(0,0,0,.6)';g.fillRect(wx+1,oy+1,32,10);g.fillStyle=L.mut;g.fillText('IN',wx+3,oy+3);g.fillStyle='#ff9a3c';g.fillText('OUT',wx+17,oy+3);
    const yb=oy+S2+8;IND.bar(g,wx,yb,ww,300);const pk=sO.pk.h;IND.ro(g,wx+ww,yb+3,'PEAK',pk,'dBFS','right');
    const inPk=sI.pk.h,red=Math.max(0,inPk-p.thr);txt(g,red>.1?'clipping '+INS.num(red,1)+' dB':'below threshold',wx+ww/2-8,yb+3,red>.1?'#ff9a3c':'rgba(255,255,255,.35)',8,'center');return sO},
  /* the Bitcrusher: its staircase stays; the scale, the scale bar for its window, the input peak and the full-scale marks */
  crush(g,w,h,f,X,T,Bm,N,dr){const sr=(typeof ctx!=='undefined'&&ctx&&ctx.sampleRate)||48000,cols=Math.max(20,Math.min(400,Math.round(w))),st=IND.feed(f.id+'|c',X.an,cols,dr,1);/* its own buffer size kept: its staircase reads the first 512 samples */
    IND.scale(g,0,T,w,Bm-T);const a=INS.td(X.an),n=Math.min(a.length,N);g.fillStyle='#ff4d4d';for(let x=0;x<w;x++){const v=a[Math.floor(x/w*n)]*dr;if(v>=IND.FS)g.fillRect(x,T,1.2,2);else if(v<=-IND.FS)g.fillRect(x,Bm-2,1.2,2)}
    IND.bar(g,6,Bm+9,w-120,n/sr*1000);IND.ro(g,w-6,Bm+12,'IN PEAK',st.pk.h,'dBFS','right');return st},
};
/* ===== end of lane E IN-C and IN-D ===== */
