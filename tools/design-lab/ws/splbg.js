var SPLBG=(function(){var W=window,D=document,PI=Math.PI,TAU=PI*2,S=null,
 SPEC_CHANCE=1/3,/* how often the spectrogram comes up, compared with each of the other four */
 KINDS=['moons','harm','dipole','chart','spec'],
 /* colours per picture. g, bg, e: the card from its centre to its edge. ink: "Audio". a, b: "Lab" and the bar. d: the bright end of the bar. p: PRO. m, n: the two small lines. L lines, T trails, O dots and the labels that ride on them (red, green, blue) */
 PAL={moons:{g:'#0f1830',bg:'#070910',e:'#040508',ink:'#eaf1ff',a:'#4cc9f0',b:'#6096ff',d:'#ffc43c',p:'#a8d8ff',m:'#8492b4',n:'#77839f',L:'96,150,255',T:'76,201,240',O:'255,196,60'},
  harm:{g:'#131738',bg:'#07080f',e:'#040407',ink:'#eef0ff',a:'#78aaff',b:'#a99bff',d:'#e6e9ff',p:'#c6ceff',m:'#8a90b8',n:'#7a7fa3',L:'128,160,255',T:'169,155,255',O:'230,233,255'},
  dipole:{g:'#0e1a34',bg:'#06080f',e:'#040508',ink:'#eaf0ff',a:'#6096ff',b:'#9fc2ff',d:'#ffc43c',p:'#b9d0ff',m:'#8190b2',n:'#75829f',L:'96,150,255',T:'96,150,255',O:'255,196,60'},
  chart:{g:'#15182a',bg:'#07080d',e:'#040406',ink:'#f5f1e8',a:'#ffb627',b:'#ffd27a',d:'#fff0cc',p:'#ffd98f',m:'#9296a8',n:'#7f8394',L:'140,170,255',T:'76,201,240',O:'255,182,39'},
  spec:{g:'#0a1226',bg:'#05070d',e:'#030409',ink:'#eaf6ff',a:'#3fb8e8',b:'#ffd23a',d:'#ffe894',p:'#bfe9ff',m:'#879cb0',n:'#788b9e',L:'63,184,232',T:'63,184,232',O:'255,210,58'}},
 SPC=[[5,7,13],[20,48,110],[63,184,232],[255,210,58]],BW=220;
 function K(w){return Math.max(1,Math.min(1.8,w/640))}
 function dot(c,x,y,r,col){c.fillStyle=col;c.beginPath();c.arc(x,y,r,0,TAU);c.fill()}
 function lab(c,w,tx,x,y,al,col){c.font='500 '+Math.max(8,Math.min(13,w/72)).toFixed(1)+'px ui-monospace,"SF Mono",Menlo,Consolas,monospace';if('letterSpacing'in c)c.letterSpacing='0.12em';c.textAlign=al;c.textBaseline='middle';c.fillStyle=col;c.fillText(tx,x,y);if('letterSpacing'in c)c.letterSpacing='0px'}
 var FN={
 /* Io, Europa and Ganymede: 4, 2 and 1 orbits in the same time. Orbits and Jupiter to scale (5.9, 9.4 and 15 Jupiter radii) */
 moons:function(c,w,h,t,P){var cx=w/2,cy=h*.345,ro=-.2,ca=Math.cos(ro),sa=Math.sin(ro),A0=Math.min(w*.37,h*.5),rp=A0/15,k=K(w),N=['IO  4','EUROPA  2','GANYMEDE  1'],i;
  c.lineWidth=1;c.strokeStyle='rgba('+P.L+',.2)';for(i=-1;i<=1;i++){var rr=rp*Math.cos(i*.5),of=rp*Math.sin(i*.5)*.93;c.beginPath();c.ellipse(cx+of*sa,cy-of*ca,rr,rr*.36,ro,0,PI);c.stroke()}
  c.strokeStyle='rgba('+P.L+',.55)';c.beginPath();c.arc(cx,cy,rp,0,TAU);c.stroke();
  for(i=0;i<3;i++){var A=A0*[5.9,9.4,15][i]/15,B=A*.36,ph=t*(TAU/(5*[1,2,4][i]))+i*2.1;c.lineWidth=1;c.strokeStyle='rgba('+P.L+',.2)';c.beginPath();c.ellipse(cx,cy,A,B,ro,0,TAU);c.stroke();
   c.lineWidth=1.5;c.strokeStyle='rgba('+P.T+',.7)';c.beginPath();c.ellipse(cx,cy,A,B,ro,ph-.8,ph);c.stroke();
   var x=A*Math.cos(ph),y=B*Math.sin(ph),X=cx+x*ca-y*sa,Y=cy+x*sa+y*ca,rt=X>w*.72;dot(c,X,Y,2.3*k,'rgb('+P.O+')');lab(c,w,N[i],X+(rt?-7:7)*k,Y-8*k,rt?'right':'left','rgba('+P.O+',.9)')}},
 /* a pen on two pendulums that slow down; another interval on each figure (3:2, 4:3, 5:4, 2:1) */
 harm:function(c,w,h,t,P,d){var T=13,q=Math.floor(t/T),u=t-q*T,cx=w/2,cy=h*.34,A=Math.min(w*.33,h*.5),B=h*.285,N=1500,p=d.p,i,x=0,y=0;
  if(d.q!==q||!p){d.q=q;if(d.r0==null)d.r0=Math.random()*4|0;var R=[[3,2],[4,3],[5,4],[2,1]][(q+d.r0)%4],s=q+d.r0;p=d.p||(d.p=new Float32Array(N*2+2));
   for(i=0;i<=N;i++){var tt=i*.035,e=Math.exp(-tt*.035);p[2*i]=(Math.sin(tt*R[0]*1.003+s)*.6+Math.sin(tt*R[1]+1.3)*.4)*e;p[2*i+1]=(Math.sin(tt*R[1]*.998+.6)*.6+Math.sin(tt*R[0]+s*.7)*.4)*e}}
  var n=Math.round((.3+.7*Math.min(1,u/4.5))*N),f=u>T-2?Math.max(0,(T-u)/2):1;c.beginPath();for(i=0;i<=n;i++){x=cx+A*p[2*i];y=cy+B*p[2*i+1];i?c.lineTo(x,y):c.moveTo(x,y)}
  c.strokeStyle='rgba('+P.L+','+(.5*f).toFixed(3)+')';c.lineWidth=1;c.lineJoin='round';c.stroke();if(n<N)dot(c,x,y,2*K(w),'rgba('+P.O+',.95)')},
 /* the field lines of a magnet, r = L sin^2(theta), tilted 10 degrees as at Jupiter; the charges bounce between their two mirror points */
 dipole:function(c,w,h,t,P){var R=w*.5,rp=R*.058,k=K(w),Ls=[.2,.3,.44,.62,.86,1.2,1.7,2.4],i,j,sg,th,s,r;c.save();c.translate(w/2,h*.345);c.rotate(.17+Math.sin(t*.15)*.03);c.lineWidth=1;
  for(i=0;i<8;i++){var L=Ls[i]*R,t0=Math.asin(Math.sqrt(rp/L)),sp=PI-2*t0;c.strokeStyle='rgba('+P.L+',.22)';c.beginPath();
   for(sg=-1;sg<=1;sg+=2)for(j=0;j<=40;j++){th=t0+sp*j/40;s=Math.sin(th);r=L*s*s;j?c.lineTo(sg*r*s,-r*Math.cos(th)):c.moveTo(sg*r*s,-r*Math.cos(th))}c.stroke();
   for(sg=-1;sg<=1;sg+=2){th=PI/2+sp*.46*Math.sin(t*(.9/(.5+Ls[i]))+i*1.7+(sg>0?0:2.1));s=Math.sin(th);r=L*s*s;dot(c,sg*r*s,-r*Math.cos(th),1.3*k,'rgba('+P.O+',.85)')}}
  c.strokeStyle='rgba('+P.L+',.2)';c.beginPath();for(i=-1;i<=1;i++){var yy=-rp*Math.sin(i*.55),hw=rp*Math.cos(i*.55);c.moveTo(-hw,yy);c.lineTo(hw,yy)}c.moveTo(0,-rp*1.5);c.lineTo(0,rp*1.5);c.stroke();
  c.strokeStyle='rgba('+P.L+',.55)';c.beginPath();c.arc(0,0,rp,0,TAU);c.stroke();c.restore();
  /* the lines fade out behind the name and the bar */c.save();c.globalCompositeOperation='destination-out';c.translate(w/2,h*.86);c.scale(w*.5,h*.35);var g=c.createRadialGradient(0,0,.78,0,0,1);g.addColorStop(0,'rgba(0,0,0,1)');g.addColorStop(1,'rgba(0,0,0,0)');c.fillStyle=g;c.fillRect(-1,-1,2,2);c.restore()},
 /* three bodies at 1, 2 and 3 times the same rate: the harmonic series drawn as an atom, on a faint grid */
 chart:function(c,w,h,t,P){var st=w/24,cx=w/2,cy=h*.345,k=K(w),ny=Math.ceil(h/st),RT=Math.min(w*.21,h*.285),i,a,x,y;
  for(i=-12;i<=12;i++){c.fillStyle='rgba('+P.L+','+(i%4?.022:.05)+')';c.fillRect(Math.round(cx+i*st),0,1,h)}
  for(i=-ny;i<=ny;i++){c.fillStyle='rgba('+P.L+','+(i%4?.022:.05)+')';c.fillRect(0,Math.round(cy+i*st),w,1)}
  c.lineWidth=1;c.setLineDash([3,5]);c.strokeStyle='rgba('+P.O+',.1)';c.beginPath();c.moveTo(0,cy+.5);c.lineTo(w,cy+.5);c.moveTo(cx+.5,0);c.lineTo(cx+.5,h*.655);c.stroke();c.setLineDash([]);
  c.strokeStyle='rgba('+P.L+',.17)';c.beginPath();for(i=0;i<72;i++){a=i/72*TAU;var l=(i%6?3:7)*k,ca=Math.cos(a),sa=Math.sin(a);c.moveTo(cx+ca*RT,cy+sa*RT);c.lineTo(cx+ca*(RT+l),cy+sa*(RT+l))}c.stroke();
  for(i=0;i<3;i++){var R=RT*[.43,.63,.83][i];a=-t*(TAU/14)*(i+1)+i*1.7;c.lineWidth=1;c.strokeStyle='rgba('+P.L+',.24)';c.beginPath();c.arc(cx,cy,R,0,TAU);c.stroke();
   c.lineWidth=1.5;c.strokeStyle='rgba('+P.T+',.75)';c.beginPath();c.arc(cx,cy,R,a,a+.7);c.stroke();
   x=cx+Math.cos(a)*R;y=cy+Math.sin(a)*R;dot(c,x,y,2.3*k,'rgb('+P.O+')');lab(c,w,'H'+(i+1),x+7*k,y-8*k,'left','rgba('+P.O+',.9)')}
  dot(c,cx,cy,2.6*k,'rgba('+P.O+',.9)')},
 /* frequency over time, rolling: a made-up 145 BPM pattern on a small picture (220 points wide) that the screen scales up; 30 new columns a second */
 spec:function(c,w,h,t,P,d){var bh=c.canvas.height,want=BW+Math.floor(t*30),n=0;
  if(!d.b||d.b.height!==bh){d.b=D.createElement('canvas');d.b.width=BW;d.b.height=bh;d.x=d.b.getContext('2d');d.x.fillStyle='rgb(5,7,13)';d.x.fillRect(0,0,BW,bh);d.col=d.x.createImageData(1,bh);d.m=new Float32Array(bh);d.n=Math.max(0,want-BW)}
  while(d.n<want&&n++<BW){col(d,bh);d.x.globalCompositeOperation='copy';d.x.drawImage(d.b,-1,0);d.x.globalCompositeOperation='source-over';d.x.putImageData(d.col,BW-1,0)}
  d.n=Math.max(d.n,want);if(!n&&d.dr)return;d.dr=1;c.globalCompositeOperation='copy';c.drawImage(d.b,0,0);c.globalCompositeOperation='source-over'}};
 /* one column of the spectrogram: kick, bass with eight overtones, a lead with five, hats, a little noise */
 function col(d,bh){var tt=(d.n++)/30,beat=(tt/.4138)%1,hb=(tt/.4138+.5)%1,fb=[55,55,65.4,49][Math.floor(tt/.8276)%4],fl=440*Math.pow(2,Math.round(Math.sin(tt*.6)*5)/12),m=d.m,o=d.col.data,ro=(bh-1)/9.966,y,k,ek=Math.exp(-beat*9),eh=Math.exp(-hb*14)*.7;
  for(y=0;y<bh;y++){var fy=1-y/(bh-1);m[y]=Math.random()*.05+(fy<.26?ek*(1-fy/.26):0)+(fy>.78?eh*Math.random():0)}
  function sp(f,a,s2){var yc=(bh-1)*(1-Math.log(f/20)/6.9078),y0=Math.max(0,Math.ceil(yc-3)),y1=Math.min(bh-1,Math.floor(yc+3)),y,x;for(y=y0;y<=y1;y++){x=(y-yc)/ro;m[y]+=a*Math.exp(-x*x/s2)}}
  for(k=1;k<=8;k++)sp(fb*k,.75/Math.sqrt(k)*(.35+.65*beat),.004);for(k=1;k<=5;k++)sp(fl*k,.6/k,.003);
  for(y=0;y<bh;y++){var v=Math.min(.999,m[y]*1.3)*3,i=v|0,q=v-i,a=SPC[i],b=SPC[i+1],p=y*4;o[p]=a[0]+(b[0]-a[0])*q;o[p+1]=a[1]+(b[1]-a[1])*q;o[p+2]=a[2]+(b[2]-a[2])*q;o[p+3]=255}}
 function pick(lk,tk){lk=lk||'audiolab-splash-last';var f=null,last=null,w=[],tot=0,i,r;try{f=localStorage.getItem(tk||'audiolab-splash-test');last=localStorage.getItem(lk)}catch(e){}
  if(KINDS.indexOf(f)>=0)return f;
  for(i=0;i<KINDS.length;i++){w[i]=KINDS[i]===last?0:KINDS[i]==='spec'?SPEC_CHANCE:1;tot+=w[i]}
  r=Math.random()*tot;for(i=0;i<KINDS.length;i++){if(w[i]>0){r-=w[i];if(r<0)break}}if(i>=KINDS.length)i=KINDS[0]===last?1:0;
  try{localStorage.setItem(lk,KINDS[i])}catch(e){}return KINDS[i]}
 function fit(){var cv=S.cv,w=cv.clientWidth,h=cv.clientHeight;if(!w||!h)return false;var z=cv.getBoundingClientRect().width/w,sc=Math.min((W.devicePixelRatio||1)*(z>.3&&z<4?z:1),2,Math.sqrt(2.2e6/(w*h))),pw=Math.round(w*sc),ph=Math.round(h*sc);
  if(S.k==='spec'){pw=BW;ph=Math.max(60,Math.round(BW*h/w));sc=1}if(cv.width!==pw||cv.height!==ph){cv.width=pw;cv.height=ph}S.d.dr=0;S.w=w;S.h=h;S.sc=sc;return true}
 function draw(ts){if(!S.w&&!fit())return;var c=S.c;c.setTransform(S.sc,0,0,S.sc,0,0);if(S.k!=='spec')c.clearRect(0,0,S.w,S.h);FN[S.k](c,S.w,S.h,S.still?(S.k==='harm'?8:40+S.off):Math.max(0,(ts-S.t0)/1000)+S.off,PAL[S.k],S.d);S.fr++}
 /* at most 60 pictures a second (30 in the lighter looks); the frames are asked for by name each time, so the app's background freeze (task AO) holds them too */
 function tick(ts){if(!S||!S.on)return;S.raf=0;if(!S.el.isConnected){stop();return}var b=D.body;if(b&&(b.classList.contains('lite')||b.classList.contains('lkstill'))){if(!S.lkS){S.lkS=1;var o0=S.still;S.still=true;draw(ts);S.still=o0}S.raf=W.requestAnimationFrame(tick);return}S.lkS=0;var lim=b&&(b.classList.contains('fxstill')||b.classList.contains('lite'))?32:15;if(ts-S.last>=lim){S.last=ts;draw(ts)}S.raf=W.requestAnimationFrame(tick)}
 function onRs(){if(S&&S.on){S.w=0;if(S.still)draw(0)}}
 function attach(el,k){var cv=el&&el.querySelector('canvas');if(!cv)return null;if(S&&S.on&&!k)k=S.k;
  if(!S||!S.on||S.k!==k){if(S&&S.on)stop();k=KINDS.indexOf(k)>=0?k:pick();S={k:k,t0:performance.now(),off:k==='harm'||k==='spec'?0:Math.random()*60,d:{},last:-1e9,fr:0,raf:0,still:false,on:true};try{S.still=W.matchMedia('(prefers-reduced-motion: reduce)').matches}catch(e){}W.addEventListener('resize',onRs)}
  S.el=el;S.cv=cv;S.c=cv.getContext('2d');S.w=0;var P=PAL[S.k],st=el.style,n;for(n in{g:1,bg:1,e:1,ink:1,a:1,b:1,d:1,p:1,m:1,n:1})st.setProperty('--sp'+n,P[n]);el.setAttribute('data-sp',S.k);
  draw(performance.now());if(!S.still&&!S.raf)S.raf=W.requestAnimationFrame(tick);return S.k}
 function stop(){if(!S)return;S.on=false;if(S.raf){try{W.cancelAnimationFrame(S.raf)}catch(e){}S.raf=0}W.removeEventListener('resize',onRs);S.d={}}
 return{attach:attach,stop:stop,pick:pick,KINDS:KINDS,PAL:PAL,FN:FN,BW:BW,SPEC_CHANCE:SPEC_CHANCE,kind:function(){return S&&S.on?S.k:null},frames:function(){return S?S.fr:0},running:function(){return!!(S&&S.on&&S.raf)}}})();
