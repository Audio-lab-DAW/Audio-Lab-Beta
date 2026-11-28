/* Task WS-0b (lane Q): round 2 drawings for the start screen's random set, and the corrected dipole flows.
   Same shape as SPLBG.FN in index.html: fn(c,w,h,t,P,d), drawn in a frame of w x h with the picture centred at (w/2, h*.345), the name below it.
   P is a palette like SPLBG.PAL (L lines, T trails, O dots and labels, as "r,g,b"), d a per-picture scratch object. Nothing here changes SPLBG. */
var R2=(function(){var PI=Math.PI,TAU=PI*2,D=document;
 function K(w){return Math.max(1,Math.min(1.8,w/640))}
 function dot(c,x,y,r,col){c.fillStyle=col;c.beginPath();c.arc(x,y,r,0,TAU);c.fill()}
 function lab(c,w,tx,x,y,al,col){c.font='500 '+Math.max(8,Math.min(13,w/72)).toFixed(1)+'px ui-monospace,"SF Mono",Menlo,Consolas,monospace';if('letterSpacing'in c)c.letterSpacing='0.12em';c.textAlign=al;c.textBaseline='middle';c.fillStyle=col;c.fillText(tx,x,y);if('letterSpacing'in c)c.letterSpacing='0px'}
 function rgba(s,a){return 'rgba('+s+','+(+a).toFixed(3)+')'}
 /* the lines fade out behind the name and the bar, as in the splash's dipole */
 function fadeName(c,w,h){c.save();c.globalCompositeOperation='destination-out';c.translate(w/2,h*.86);c.scale(w*.5,h*.35);var g=c.createRadialGradient(0,0,.78,0,0,1);g.addColorStop(0,'rgba(0,0,0,1)');g.addColorStop(1,'rgba(0,0,0,0)');c.fillStyle=g;c.fillRect(-1,-1,2,2);c.restore()}
 var PAL={
  chladni:{g:'#0c1f26',bg:'#06090c',e:'#030507',ink:'#e8fbf8',a:'#3fd0c9',b:'#8fe3d0',d:'#ffd27a',p:'#b7efe6',m:'#86a3a6',n:'#748f92',L:'63,208,201',T:'143,227,208',O:'255,210,122'},
  pend:{g:'#141a33',bg:'#07080f',e:'#040508',ink:'#eef1ff',a:'#7aa2ff',b:'#c3d2ff',d:'#ffc43c',p:'#c9d6ff',m:'#8a92b6',n:'#7980a2',L:'122,162,255',T:'195,210,255',O:'255,196,60'},
  twodip:{g:'#17143a',bg:'#08070f',e:'#040408',ink:'#f0eeff',a:'#8b7bff',b:'#c4b8ff',d:'#ffc43c',p:'#d2c9ff',m:'#9089b8',n:'#7e78a3',L:'139,123,255',T:'139,123,255',O:'255,196,60'},
  interf:{g:'#081a2a',bg:'#04080d',e:'#020408',ink:'#e6f8ff',a:'#4cc9f0',b:'#7bf0ff',d:'#ffd27a',p:'#b6ecff',m:'#7f9db0',n:'#708a9c',L:'76,201,240',T:'123,240,255',O:'255,182,39'},
  vdp:{g:'#0b2019',bg:'#050a08',e:'#030605',ink:'#e8fff3',a:'#3ecf8e',b:'#a3f7c9',d:'#ffd23a',p:'#b8f5d6',m:'#83a597',n:'#729184',L:'62,207,142',T:'163,247,201',O:'255,210,58'},
  liss:{g:'#1f1708',bg:'#0a0805',e:'#060403',ink:'#fff5e6',a:'#ffb627',b:'#ffd27a',d:'#fff0cc',p:'#ffd98f',m:'#a89a82',n:'#928672',L:'255,182,39',T:'255,210,122',O:'255,240,200'},
  trap:{g:'#28110e',bg:'#0b0606',e:'#060303',ink:'#fff0ea',a:'#ff7a59',b:'#ffb38a',d:'#ffd6a0',p:'#ffc7b0',m:'#ad9088',n:'#977d76',L:'255,140,110',T:'255,122,89',O:'255,214,160'},
  four:{g:'#1a1031',bg:'#08060f',e:'#040308',ink:'#f6eeff',a:'#ff7ac8',b:'#b583ff',d:'#ffd23a',p:'#e8c4ff',m:'#9a88b4',n:'#86789f',L:'181,131,255',T:'255,122,200',O:'255,210,58'}};
 var FN={};

 /* R1 Chladni plate: a square plate held at its centre and bowed. Where it does not move (the nodal lines) the sand stays; where it shakes, the sand is thrown off.
    Modes of a free square plate, approximated as cos(n pi x)cos(m pi y) -/+ cos(m pi x)cos(n pi y) (Ritz 1909; Paul Bourke). A new mode every 12 s. */
 var CM=[[1,4,-1],[2,5,1],[1,6,-1],[3,5,1],[2,7,-1],[3,7,1],[1,5,1],[4,6,-1]];
 function cf(n,m,sg,x,y){var a=PI*n,b=PI*m;return Math.cos(a*x)*Math.cos(b*y)+sg*Math.cos(b*x)*Math.cos(a*y)}
 function nodal(n,m,sg){var G=80,v=new Float32Array((G+1)*(G+1)),i,j,o=[];for(j=0;j<=G;j++)for(i=0;i<=G;i++)v[j*(G+1)+i]=cf(n,m,sg,i/G,j/G);
  for(j=0;j<G;j++)for(i=0;i<G;i++){var a=v[j*(G+1)+i],b=v[j*(G+1)+i+1],cc=v[(j+1)*(G+1)+i+1],dd=v[(j+1)*(G+1)+i],p=[];
   if((a>0)!==(b>0))p.push((i+a/(a-b))/G,j/G);if((b>0)!==(cc>0))p.push((i+1)/G,(j+b/(b-cc))/G);if((cc>0)!==(dd>0))p.push((i+1-cc/(cc-dd))/G,(j+1)/G);if((dd>0)!==(a>0))p.push(i/G,(j+1-dd/(dd-a))/G);
   if(p.length>=4)o.push(p[0],p[1],p[2],p[3]);if(p.length===8)o.push(p[4],p[5],p[6],p[7])}
  return new Float32Array(o)}
 FN.chladni=function(c,w,h,t,P,d){var S=Math.min(w*.44,h*.56),x0=w/2-S/2,y0=h*.345-S/2,k=K(w),T=12,q=Math.floor(t/T),u=t-q*T,M=CM[((q%CM.length)+CM.length)%CM.length],i,N=1300;
  if(d.q!==q){d.q=q;d.seg=nodal(M[0],M[1],M[2])}var sg=d.seg;
  c.lineWidth=1;c.strokeStyle=rgba(P.L,.32);c.strokeRect(Math.round(x0)+.5,Math.round(y0)+.5,Math.round(S),Math.round(S));
  c.strokeStyle=rgba(P.L,.22);c.beginPath();var cl=6*k;[[x0,y0,1,1],[x0+S,y0,-1,1],[x0,y0+S,1,-1],[x0+S,y0+S,-1,-1]].forEach(function(e){c.moveTo(e[0]-e[2]*cl*.0,e[1]-e[3]*cl);c.lineTo(e[0]-e[2]*cl*.0,e[1]-e[3]*cl*2.2);c.moveTo(e[0]-e[2]*cl,e[1]);c.lineTo(e[0]-e[2]*cl*2.2,e[1])});c.stroke();
  dot(c,w/2,h*.345,1.6*k,rgba(P.L,.6));
  var fa=Math.min(1,u/1.2)*(u>T-1.2?Math.max(0,(T-u)/1.2):1);c.strokeStyle=rgba(P.L,.17*fa);c.beginPath();for(i=0;i<sg.length;i+=4){c.moveTo(x0+sg[i]*S,y0+sg[i+1]*S);c.lineTo(x0+sg[i+2]*S,y0+sg[i+3]*S)}c.stroke();
  var g=d.g;if(!g||d.gs!==sg&&!d.live){g=d.g=new Float32Array(N*2);for(i=0;i<N;i++){var s=(Math.random()*(sg.length/4)|0)*4,f=Math.random();g[2*i]=sg[s]+(sg[s+2]-sg[s])*f+(Math.random()-.5)*.006;g[2*i+1]=sg[s+1]+(sg[s+3]-sg[s+1])*f+(Math.random()-.5)*.006}d.gs=sg}
  var dt=d.lt==null?0:Math.min(.05,Math.max(0,t-d.lt));if(dt>0)d.live=1;d.lt=t;
  if(dt>0){var n=M[0],m=M[1],sgn=M[2],an=PI*n,am=PI*m;for(i=0;i<N;i++){var x=g[2*i],y=g[2*i+1],cnx=Math.cos(an*x),cny=Math.cos(an*y),cmx=Math.cos(am*x),cmy=Math.cos(am*y),snx=Math.sin(an*x),sny=Math.sin(an*y),smx=Math.sin(am*x),smy=Math.sin(am*y),
    f=cnx*cmy+sgn*cmx*cny,fx=-an*snx*cmy-sgn*am*smx*cny,fy=-am*cnx*smy-sgn*an*cmx*sny,g2=fx*fx+fy*fy+1e-6,a=Math.abs(f),st=Math.min(1,dt*2.2);
    x+=-f*fx/g2*st*.5+(Math.random()-.5)*a*a*dt*.35;y+=-f*fy/g2*st*.5+(Math.random()-.5)*a*a*dt*.35;g[2*i]=x<0?0:x>1?1:x;g[2*i+1]=y<0?0:y>1?1:y}}
  c.fillStyle=rgba(P.O,.72);var z=Math.max(1,1.1*k);for(i=0;i<N;i++)c.fillRect(x0+g[2*i]*S-z/2,y0+g[2*i+1]*S-z/2,z,z);
  lab(c,w,'N '+M[0]+'  M '+M[1],x0+S,y0-11*k,'right',rgba(P.O,.85));lab(c,w,'NODAL LINES',x0,y0-11*k,'left',rgba(P.L,.6))};

 /* R2 Pendulum wave: 15 pendulums, the first swings 51 times in 60 s, each next one once more (Harvard Natural Sciences Lecture Demonstrations).
    Seen from above, the bobs make travelling waves, scatter, and line up again every 60 s. */
 FN.pend=function(c,w,h,t,P){var N=15,cx=w/2,cy=h*.345,k=K(w),span=Math.min(w*.62,h*1.05),A=Math.min(h*.2,w*.15),i,j,X=[],Y=[];
  c.lineWidth=1;c.setLineDash([3,5]);c.strokeStyle=rgba(P.L,.16);c.beginPath();c.moveTo(cx-span/2-14*k,cy+.5);c.lineTo(cx+span/2+14*k,cy+.5);c.stroke();c.setLineDash([]);
  for(i=0;i<N;i++){var x=cx-span/2+span*i/(N-1),n=51+i;X[i]=x;Y[i]=cy+A*Math.cos(TAU*n*t/60);
   c.strokeStyle=rgba(P.L,.13);c.beginPath();c.moveTo(Math.round(x)+.5,cy-A);c.lineTo(Math.round(x)+.5,cy+A);c.moveTo(x-3*k,cy-A);c.lineTo(x+3*k,cy-A);c.moveTo(x-3*k,cy+A);c.lineTo(x+3*k,cy+A);c.stroke();
   c.strokeStyle=rgba(P.T,.4);c.lineWidth=1.5;c.beginPath();for(j=0;j<=5;j++){var tt=t-j*.018,yy=cy+A*Math.cos(TAU*n*tt/60);j?c.lineTo(x,yy):c.moveTo(x,yy)}c.stroke();c.lineWidth=1}
  c.strokeStyle=rgba(P.L,.3);c.beginPath();c.moveTo(X[0],Y[0]);for(i=1;i<N-1;i++){c.quadraticCurveTo(X[i],Y[i],(X[i]+X[i+1])/2,(Y[i]+Y[i+1])/2)}c.lineTo(X[N-1],Y[N-1]);c.stroke();
  for(i=0;i<N;i++)dot(c,X[i],Y[i],2.4*k,'rgb('+P.O+')');
  var sec=((t%60)+60)%60;lab(c,w,'51',X[0],cy+A+14*k,'center',rgba(P.L,.7));lab(c,w,'65 SWINGS IN 60 S',X[N-1],cy+A+14*k,'right',rgba(P.O,.85));lab(c,w,'T '+(sec<10?'0':'')+Math.floor(sec)+' S',X[N-1],cy-A-14*k,'right',rgba(P.O,.85))};

 /* R3 Two magnets side by side: the field lines of two parallel dipoles, found by stepping along B = sum of (3(m.r)r - m)/r^3; the dots flow out of each north pole and back in at a south pole */
 function b2(x,y,C){var bx=0,by=0,i;for(i=0;i<C.length;i+=2){var rx=x-C[i],ry=y-C[i+1],r2=rx*rx+ry*ry,r=Math.sqrt(r2),r5=r2*r2*r,md=-ry;bx+=3*md*rx/r5;by+=(3*md*ry/r2+1)/(r2*r)}return[bx,by]}
 FN.twodip=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),rp=w*.034,Dd=w*.14,i,j;
  if(d.w!==w||d.h!==h){d.w=w;d.h=h;var C=[cx-Dd,cy,cx+Dd,cy],Lines=[],ang=[-70,-52,-36,-22,-10,10,22,36,52,70];
   for(var q=0;q<2;q++)for(j=0;j<ang.length;j++){var a=ang[j]*PI/180,x=C[2*q]+Math.sin(a)*rp*1.02,y=C[2*q+1]-Math.cos(a)*rp*1.02,pts=[x,y],T=[0],tm=0,ok=false,bp=Math.hypot.apply(null,b2(C[2*q],C[2*q+1]-rp,C));
    for(i=0;i<4000;i++){var B=b2(x,y,C),bm=Math.hypot(B[0],B[1]),st=1.6;x+=B[0]/bm*st;y+=B[1]/bm*st;tm+=st/(70*k*Math.pow(bm/bp,.2));pts.push(x,y);T.push(tm);
     if(Math.hypot(x-C[0],y-C[1])<rp||Math.hypot(x-C[2],y-C[3])<rp){ok=true;break}if(x<-w*.7||x>w*1.7||y<-h*.9||y>h*1.9)break}
    Lines.push({p:new Float32Array(pts),T:new Float32Array(T),tm:tm,ok:ok})}d.L=Lines;d.C=C}
  c.lineWidth=1;for(i=0;i<d.L.length;i++){var Ln=d.L[i],p=Ln.p;c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(p[0],p[1]);for(j=2;j<p.length;j+=6)c.lineTo(p[j],p[j+1]);c.lineTo(p[p.length-2],p[p.length-1]);c.stroke()}
  for(i=0;i<d.L.length;i++){var L2=d.L[i],n=Math.max(1,Math.floor(L2.tm/1.1));for(j=0;j<n;j++){var tau=((t+j*L2.tm/n)%L2.tm+L2.tm)%L2.tm,T2=L2.T,lo=0,hi=T2.length-1;while(hi-lo>1){var md=(lo+hi)>>1;if(T2[md]<tau)lo=md;else hi=md}var f=(tau-T2[lo])/((T2[hi]-T2[lo])||1),xx=L2.p[2*lo]+(L2.p[2*hi]-L2.p[2*lo])*f,yy=L2.p[2*lo+1]+(L2.p[2*hi+1]-L2.p[2*lo+1])*f;
   if(xx>-20&&xx<w+20&&yy>-20&&yy<h+20)dot(c,xx,yy,1.3*k,rgba(P.O,.85))}}
  for(i=0;i<2;i++){var X=d.C[2*i],Y=d.C[2*i+1];c.strokeStyle=rgba(P.L,.2);c.beginPath();for(j=-1;j<=1;j++){var yy2=Y-rp*Math.sin(j*.55),hw=rp*Math.cos(j*.55);c.moveTo(X-hw,yy2);c.lineTo(X+hw,yy2)}c.moveTo(X,Y-rp*1.5);c.lineTo(X,Y+rp*1.5);c.stroke();c.strokeStyle=rgba(P.L,.55);c.beginPath();c.arc(X,Y,rp,0,TAU);c.stroke();
   lab(c,w,'N',X,Y-rp*1.5-8*k,'center',rgba(P.O,.85))}
  fadeName(c,w,h)};

 /* R4 Two-source interference: two sources in step, each a circular wave falling off as 1/sqrt(r). Where crest meets trough the water stays still: the dark lines are hyperbolas */
 var IW=200;
 FN.interf=function(c,w,h,t,P,d){var bh=Math.max(40,Math.round(IW*h/w)),cx=w/2,cy=h*.345,k=K(w),sep=w*.075,lam=w*.05,i,x,y;
  if(!d.b||d.bh!==bh||d.w!==w){d.w=w;d.bh=bh;d.b=D.createElement('canvas');d.b.width=IW;d.b.height=bh;d.x=d.b.getContext('2d');d.im=d.x.createImageData(IW,bh);var n=IW*bh;d.r1=new Float32Array(n);d.r2=new Float32Array(n);d.mk=new Float32Array(n);var sx=w/IW,sy=h/bh;
   for(y=0;y<bh;y++)for(x=0;x<IW;x++){var X=(x+.5)*sx,Y=(y+.5)*sy,j=y*IW+x,a=Math.hypot(X-(cx-sep),Y-cy),b=Math.hypot(X-(cx+sep),Y-cy);d.r1[j]=a;d.r2[j]=b;
    var ex=Math.min(1,Math.min(X,w-X)/(w*.16)),ey=Math.min(1,Y/(h*.08)),eb=Math.max(0,Math.min(1,(h*.7-Y)/(h*.16))),rr=Math.hypot((X-cx)/(w*.5),(Y-cy)/(h*.5));d.mk[j]=ex*ey*eb*Math.max(0,1-rr*rr*.55)}}
  var L=P.L.split(',').map(Number),o=d.im.data,kk=TAU/lam,ph=t*TAU*.55,n2=IW*bh;
  for(i=0;i<n2;i++){var r1=d.r1[i],r2=d.r2[i],v=Math.cos(kk*r1-ph)/Math.sqrt(1+r1/lam)+Math.cos(kk*r2-ph)/Math.sqrt(1+r2/lam),q=i*4,al=Math.max(0,v)*.62*d.mk[i];o[q]=L[0];o[q+1]=L[1];o[q+2]=L[2];o[q+3]=Math.min(255,al*255)}
  d.x.putImageData(d.im,0,0);c.save();c.imageSmoothingEnabled=true;c.drawImage(d.b,0,0,w,h);c.restore();
  dot(c,cx-sep,cy,2.4*k,'rgb('+P.O+')');dot(c,cx+sep,cy,2.4*k,'rgb('+P.O+')');lab(c,w,'S1',cx-sep,cy-12*k,'center',rgba(P.O,.9));lab(c,w,'S2',cx+sep,cy-12*k,'center',rgba(P.O,.9))};

 /* R5 Phase portrait of the Van der Pol oscillator, x'' - mu(1 - x^2)x' + x = 0 with mu 1.2: every start, inside or outside, ends on the same loop, the limit cycle */
 var MU=1.2;function vf(x,y){return[y,MU*(1-x*x)*y-x]}
 function rk(s,h2){var a=vf(s[0],s[1]),b=vf(s[0]+a[0]*h2/2,s[1]+a[1]*h2/2),c2=vf(s[0]+b[0]*h2/2,s[1]+b[1]*h2/2),e=vf(s[0]+c2[0]*h2,s[1]+c2[1]*h2);s[0]+=h2/6*(a[0]+2*b[0]+2*c2[0]+e[0]);s[1]+=h2/6*(a[1]+2*b[1]+2*c2[1]+e[1])}
 function spawn(o){var a=Math.random()*TAU,r=Math.random()<.4?Math.random()*.6+.05:Math.random()*1.2+2.6;o.s=[Math.cos(a)*r,Math.sin(a)*r*1.4];o.age=0;o.tr=[]}
 FN.vdp=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),bw=Math.min(w*.62,h*1.2),bh=h*.58,sx=bw/6,sy=bh/9,i,j;
  if(!d.cyc){var s=[2,0];for(i=0;i<3000;i++)rk(s,.01);var pc=[];for(i=0;i<760;i++){rk(s,.01);pc.push(s[0],s[1])}d.cyc=pc;d.p=[];for(i=0;i<34;i++){var o={};spawn(o);var pre=Math.random()*9;for(j=0;j<pre/.02;j++)rk(o.s,.02);o.age=pre;d.p.push(o)}}
  function X(v){return cx+v*sx}function Y(v){return cy-v*sy}
  c.lineWidth=1;c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(cx-bw/2,cy+.5);c.lineTo(cx+bw/2,cy+.5);c.moveTo(cx+.5,cy-bh/2);c.lineTo(cx+.5,cy+bh/2);for(i=-2;i<=2;i++){c.moveTo(X(i),cy-3*k);c.lineTo(X(i),cy+3*k)}for(i=-4;i<=4;i++){c.moveTo(cx-3*k,Y(i));c.lineTo(cx+3*k,Y(i))}c.stroke();
  c.strokeStyle=rgba(P.L,.11);c.beginPath();for(i=-6;i<=6;i++)for(j=-4;j<=4;j++){var x=i*.45,y=j*1.0,v=vf(x,y),m=Math.hypot(v[0]*sx,-v[1]*sy)||1,l=5*k;c.moveTo(X(x),Y(y));c.lineTo(X(x)+v[0]*sx/m*l,Y(y)-v[1]*sy/m*l)}c.stroke();
  var pc2=d.cyc;c.strokeStyle=rgba(P.L,.48);c.lineWidth=1.2;c.beginPath();for(i=0;i<pc2.length;i+=2)i?c.lineTo(X(pc2[i]),Y(pc2[i+1])):c.moveTo(X(pc2[i]),Y(pc2[i+1]));c.closePath();c.stroke();c.lineWidth=1;
  var dt=d.lt==null?0:Math.min(.05,Math.max(0,t-d.lt));d.lt=t;
  for(i=0;i<d.p.length;i++){var o2=d.p[i];if(dt>0){var sub=4;for(j=0;j<sub;j++)rk(o2.s,dt*1.1/sub);o2.age+=dt*1.1;o2.tr.push(o2.s[0],o2.s[1]);if(o2.tr.length>44)o2.tr.splice(0,2);if(o2.age>22||Math.abs(o2.s[0])>4||Math.abs(o2.s[1])>6)spawn(o2)}
   var tr=o2.tr;if(tr.length>3){c.strokeStyle=rgba(P.T,.45);c.beginPath();for(j=0;j<tr.length;j+=2)j?c.lineTo(X(tr[j]),Y(tr[j+1])):c.moveTo(X(tr[j]),Y(tr[j+1]));c.stroke()}
   if(Math.abs(o2.s[0])<3.1&&Math.abs(o2.s[1])<4.6)dot(c,X(o2.s[0]),Y(o2.s[1]),1.6*k,rgba(P.O,.9))}
  lab(c,w,'X',cx+bw/2,cy-10*k,'right',rgba(P.L,.7));lab(c,w,'DX/DT',cx+8*k,cy-bh/2+4*k,'left',rgba(P.L,.7));lab(c,w,'LIMIT CYCLE  μ 1.2',cx-bw/2,cy-bh/2+4*k,'left',rgba(P.O,.85))};

 /* R6 Lissajous figure on an oscilloscope: X and Y fed two tones in a simple ratio; a slow phase drift turns the figure. A new ratio every 16 s */
 var LR=[[3,2],[5,4],[1,2],[3,4],[5,3],[2,3]];
 FN.liss=function(c,w,h,t,P){var cx=w/2,cy=h*.345,k=K(w),sw=Math.min(w*.46,h*.62*1.25),sh=sw*.8,x0=cx-sw/2,y0=cy-sh/2,T=16,q=Math.floor(t/T),u=t-q*T,R=LR[((q%LR.length)+LR.length)%LR.length],ph=t*.35,i;
  c.lineWidth=1;c.strokeStyle=rgba(P.L,.07);c.beginPath();for(i=1;i<10;i++){var gx=Math.round(x0+sw*i/10)+.5;c.moveTo(gx,y0);c.lineTo(gx,y0+sh)}for(i=1;i<8;i++){var gy=Math.round(y0+sh*i/8)+.5;c.moveTo(x0,gy);c.lineTo(x0+sw,gy)}c.stroke();
  c.strokeStyle=rgba(P.L,.16);c.beginPath();for(i=0;i<=50;i++){var tx=x0+sw*i/50,ty=y0+sh*i/40;c.moveTo(tx,cy-(i%5?2:4)*k);c.lineTo(tx,cy+(i%5?2:4)*k);if(i<=40){c.moveTo(cx-(i%5?2:4)*k,ty);c.lineTo(cx+(i%5?2:4)*k,ty)}}c.stroke();
  c.strokeStyle=rgba(P.L,.32);c.strokeRect(Math.round(x0)+.5,Math.round(y0)+.5,Math.round(sw),Math.round(sh));
  var f=Math.min(1,u/1)*(u>T-1?Math.max(0,T-u):1),ax=sw*.42,ay=sh*.42;c.strokeStyle=rgba(P.L,.38*f);c.beginPath();for(i=0;i<=600;i++){var s=i/600*TAU,x=cx+ax*Math.sin(R[0]*s+ph),y=cy-ay*Math.sin(R[1]*s);i?c.lineTo(x,y):c.moveTo(x,y)}c.stroke();
  var sb=t*1.6;c.lineWidth=1.6;for(i=0;i<24;i++){var s1=sb-i*.05,s2=sb-(i+1)*.05;c.strokeStyle=rgba(P.T,.8*(1-i/24)*f);c.beginPath();c.moveTo(cx+ax*Math.sin(R[0]*s1+ph),cy-ay*Math.sin(R[1]*s1));c.lineTo(cx+ax*Math.sin(R[0]*s2+ph),cy-ay*Math.sin(R[1]*s2));c.stroke()}c.lineWidth=1;
  dot(c,cx+ax*Math.sin(R[0]*sb+ph),cy-ay*Math.sin(R[1]*sb),2.2*k,rgba(P.O,f));
  var deg=Math.round(((ph*180/PI)%360+360)%360);lab(c,w,'X '+R[0]+' : Y '+R[1],x0,y0+sh+12*k,'left',rgba(P.O,.85));lab(c,w,'PHASE '+deg+'°',x0+sw,y0+sh+12*k,'right',rgba(P.L,.7))};

 /* R7 TRAPPIST-1: seven Earth-sized planets in a chain of resonances (periods 1.51, 2.42, 4.05, 6.10, 9.21, 12.35, 18.77 days; neighbours 8:5 5:3 3:2 3:2 4:3 3:2). Orbits to scale; 1 day = 0.9 s */
 var TP=[1.5109,2.4218,4.0496,6.0996,9.2067,12.3529,18.7673],TA=[.01154,.0158,.02227,.02925,.03849,.04683,.06189],TR=[1.12,1.1,.79,.92,1.05,1.13,.76],TN=['B','C','D','E','F','G','H'];
 FN.trap=function(c,w,h,t,P){var cx=w/2,cy=h*.345,ro=-.2,ca=Math.cos(ro),sa=Math.sin(ro),A0=Math.min(w*.4,h*.56),k=K(w),i;
  var g=c.createRadialGradient(cx,cy,0,cx,cy,14*k);g.addColorStop(0,rgba(P.O,.55));g.addColorStop(1,rgba(P.O,0));c.fillStyle=g;c.fillRect(cx-14*k,cy-14*k,28*k,28*k);dot(c,cx,cy,2.8*k,'rgb('+P.O+')');
  var XY=[];for(i=0;i<7;i++){var A=A0*TA[i]/TA[6],B=A*.36,phs=TAU*t/(TP[i]*.9)+i*1.9;c.lineWidth=1;c.strokeStyle=rgba(P.L,.18);c.beginPath();c.ellipse(cx,cy,A,B,ro,0,TAU);c.stroke();
   c.lineWidth=1.4;c.strokeStyle=rgba(P.T,.6);c.beginPath();c.ellipse(cx,cy,A,B,ro,phs-.7,phs);c.stroke();var x=A*Math.cos(phs),y=B*Math.sin(phs);XY.push([cx+x*ca-y*sa,cy+x*sa+y*ca])}
  c.lineWidth=1;c.strokeStyle=rgba(P.L,.12);c.beginPath();for(i=0;i<7;i++)i?c.lineTo(XY[i][0],XY[i][1]):c.moveTo(XY[i][0],XY[i][1]);c.stroke();
  for(i=0;i<7;i++){dot(c,XY[i][0],XY[i][1],1.5*TR[i]*k,'rgb('+P.O+')');if(i>=3){var rt=XY[i][0]>w*.72;lab(c,w,TN[i],XY[i][0]+(rt?-7:7)*k,XY[i][1]-8*k,rt?'right':'left',rgba(P.O,.9))}}
  lab(c,w,'TRAPPIST-1   8:5  5:3  3:2  3:2  4:3  3:2',cx,cy+A0*.36+18*k,'center',rgba(P.L,.62))};

 /* R8 Fourier series: rotating circles, each a harmonic, add up to a square, a sawtooth or a triangle wave (the shapes an oscillator makes). A new wave every 14 s */
 var FT=[['SQUARE',function(n){return n%2?4/(PI*n):0}],['SAWTOOTH',function(n){return(n%2?2:-2)/(PI*n)}],['TRIANGLE',function(n){return n%2?((n-1)/2%2?-1:1)*8/(PI*PI*n*n):0}]];
 FN.four=function(c,w,h,t,P){var cy=h*.345,k=K(w),T=14,q=Math.floor(t/T),u=t-q*T,F=FT[((q%3)+3)%3],R0=h*.14,x0=w*.3,om=TAU*.17,xw0=w*.5,xw1=w*.93,sp=(xw1-xw0)/(TAU/om),f=Math.min(1,u/1)*(u>T-1?Math.max(0,T-u):1),i,n,
   H=[];for(n=1;H.length<6&&n<20;n++){var a=F[1](n);if(a)H.push([n,a*R0])}
  var px=x0,py=cy;c.lineWidth=1;for(i=0;i<H.length;i++){var r=Math.abs(H[i][1]),an=H[i][0]*om*t,sg=H[i][1]<0?-1:1;c.strokeStyle=rgba(P.L,.2*f+.04);c.beginPath();c.arc(px,py,r,0,TAU);c.stroke();var nx=px+sg*r*Math.cos(an),ny=py-sg*r*Math.sin(an);c.strokeStyle=rgba(P.L,.42*f+.06);c.beginPath();c.moveTo(px,py);c.lineTo(nx,ny);c.stroke();px=nx;py=ny}
  dot(c,px,py,2.2*k,rgba(P.O,f));c.setLineDash([3,4]);c.strokeStyle=rgba(P.O,.25*f);c.beginPath();c.moveTo(px,py);c.lineTo(xw0,py);c.stroke();c.setLineDash([]);
  c.strokeStyle=rgba(P.L,.14);c.beginPath();c.moveTo(xw0,cy+.5);c.lineTo(xw1,cy+.5);c.moveTo(xw0+.5,cy-R0*1.35);c.lineTo(xw0+.5,cy+R0*1.35);c.stroke();
  c.strokeStyle=rgba(P.T,.75*f);c.lineWidth=1.4;c.beginPath();for(var x=xw0;x<=xw1;x+=2){var tt=t-(x-xw0)/sp,y=cy;for(i=0;i<H.length;i++)y-=H[i][1]*Math.sin(H[i][0]*om*tt);x===xw0?c.moveTo(x,y):c.lineTo(x,y)}c.stroke();c.lineWidth=1;
  lab(c,w,F[0],xw1,cy-R0*1.35,'right',rgba(P.O,.85*f+.1));lab(c,w,'HARMONICS '+H.map(function(e){return e[0]}).join(' '),x0,cy+R0*1.55+6*k,'center',rgba(P.L,.62))};

 /* ===== The dipole: today's drawing with three corrected flows. Field lines r = L sin^2(theta); |B| ~ sqrt(1 + 3 cos^2 theta) / r^3, 2 at the pole's surface, 1 at the equator's.
    The ball is drawn as a uniformly magnetised sphere: inside it the field is uniform, so each line closes through the ball as a straight chord (Griffiths, ex. 6.1).
    dir 1 = Jupiter (the field leaves the north half, as Jupiter's dipole points north), -1 = Earth (it leaves the south half). ===== */
 var Ls=[.2,.3,.44,.62,.86,1.2,1.7,2.4];
 function dipFrame(c,w,h,t,P,inner){var R=w*.5,rp=R*.058,i,j,sg,th,s,r;c.save();c.translate(w/2,h*.345);c.rotate(.17+Math.sin(t*.15)*.03);c.lineWidth=1;
  for(i=0;i<8;i++){var L=Ls[i]*R,t0=Math.asin(Math.sqrt(rp/L)),sp=PI-2*t0;c.strokeStyle='rgba('+P.L+',.22)';c.beginPath();for(sg=-1;sg<=1;sg+=2)for(j=0;j<=40;j++){th=t0+sp*j/40;s=Math.sin(th);r=L*s*s;j?c.lineTo(sg*r*s,-r*Math.cos(th)):c.moveTo(sg*r*s,-r*Math.cos(th))}c.stroke()}
  if(inner){c.strokeStyle='rgba('+P.L+',.12)';c.beginPath();for(i=0;i<8;i++){var x=rp*Math.sqrt(rp/(Ls[i]*R)),y=rp*Math.sqrt(1-rp/(Ls[i]*R));c.moveTo(x,-y);c.lineTo(x,y);c.moveTo(-x,-y);c.lineTo(-x,y)}c.stroke()}
  c.strokeStyle='rgba('+P.L+',.2)';c.beginPath();for(i=-1;i<=1;i++){var yy=-rp*Math.sin(i*.55),hw=rp*Math.cos(i*.55);c.moveTo(-hw,yy);c.lineTo(hw,yy)}c.moveTo(0,-rp*1.5);c.lineTo(0,rp*1.5);c.stroke();
  c.strokeStyle='rgba('+P.L+',.55)';c.beginPath();c.arc(0,0,rp,0,TAU);c.stroke();return{R:R,rp:rp}}
 function endFrame(c,w,h){c.restore();fadeName(c,w,h)}
 /* a table per line: points (x,y) from the top of the ball out along the line to the bottom, then (F1) up through the ball; t = travel time with speed V (B/2)^g */
 function tables(w,mode){var R=w*.5,rp=R*.058,k=K(w),out=[],i,j;for(i=0;i<8;i++){var L=Ls[i]*R,t0=Math.asin(Math.sqrt(rp/L)),N=260,X=[],Y=[],B=[],In=[];
   for(j=0;j<=N;j++){var th=t0+(PI-2*t0)*j/N,s=Math.sin(th),r=L*s*s,cth=Math.cos(th);X.push(r*s);Y.push(-r*cth);B.push(Math.sqrt(1+3*cth*cth)/Math.pow(r/rp,3));In.push(0)}
   if(mode===1){var xi=rp*Math.sqrt(rp/L),yi=rp*Math.sqrt(1-rp/L);for(j=1;j<24;j++){X.push(xi);Y.push(yi-2*yi*j/24);B.push(2);In.push(1)}X.push(X[0]);Y.push(Y[0]);B.push(B[0]);In.push(1)}
   var T=[0],tm=0,g=mode===1?.2:0,V=(mode===1?110:46)*k;for(j=1;j<X.length;j++){var ds=Math.hypot(X[j]-X[j-1],Y[j]-Y[j-1]),bm=(B[j]+B[j-1])/2;tm+=ds/(V*Math.pow(bm/2,g));T.push(tm)}
   out.push({X:X,Y:Y,In:In,T:T,tm:tm})}return out}
 function at(tb,tau){var T=tb.T,lo=0,hi=T.length-1;while(hi-lo>1){var m=(lo+hi)>>1;if(T[m]<tau)lo=m;else hi=m}var f=(tau-T[lo])/((T[hi]-T[lo])||1);return[tb.X[lo]+(tb.X[hi]-tb.X[lo])*f,tb.Y[lo]+(tb.Y[hi]-tb.Y[lo])*f,tb.In[lo]&&tb.In[hi]]}
 var api={dir:1};
 function flow(mode){return function(c,w,h,t,P,d){var k=K(w);if(d.w!==w||d.m!==mode){d.w=w;d.m=mode;d.tb=tables(w,mode)}dipFrame(c,w,h,t,P,mode===1);var dir=api.dir,i,j;
   for(i=0;i<8;i++){var tb=d.tb[i],gap=mode===1?1.1:Math.max(.5,34*k/(46*k)),n=Math.max(1,Math.floor(tb.tm/gap));for(var sg=-1;sg<=1;sg+=2)for(j=0;j<n;j++){var tau=((t+j*tb.tm/n+(sg>0?0:tb.tm/n/2))%tb.tm+tb.tm)%tb.tm;if(dir<0)tau=tb.tm-tau;var p=at(tb,tau);
    if(p[2])dot(c,sg*p[0],p[1],.95*k,'rgba('+P.O+',.3)');else dot(c,sg*p[0],p[1],1.3*k,'rgba('+P.O+',.88)')}}
   endFrame(c,w,h)}}
 /* F3: the real motion of a trapped charge: it spirals round its line (gyration) and slides along it, slowing where the field gets stronger, until it turns back at its mirror point,
    where B = B_eq / sin^2(pitch angle at the equator). Total speed stays the same; along the line v_par = v sqrt(1 - B/B_mirror). It also drifts round the planet, out of the page. */
 function rat(th){var s=Math.sin(th),c2=Math.cos(th);return Math.sqrt(1+3*c2*c2)/Math.pow(s,6)}
 function trapT(w){var R=w*.5,k=K(w),out=[],AL=[32,52,40,62,36],idx=[2,3,4,5,6],q,j;for(q=0;q<idx.length;q++){var L=Ls[idx[q]]*R,al=AL[q]*PI/180,bm=1/(Math.sin(al)*Math.sin(al)),lo=.02,hi=PI/2;
   for(j=0;j<60;j++){var m=(lo+hi)/2;if(rat(m)>bm)lo=m;else hi=m}var thm=hi,N=300,X=[],Y=[],T=[0],NX=[],NY=[],BB=[],tm=0;
   for(j=0;j<=N;j++){var th=thm+(PI-2*thm)*j/N,s=Math.sin(th),r=L*s*s,cth=Math.cos(th);X.push(r*s);Y.push(-r*cth);var tx=2*L*s*cth*s+r*cth,ty=-(2*L*s*cth*cth-r*s),tl=Math.hypot(tx,ty)||1;NX.push(-ty/tl);NY.push(tx/tl);BB.push(rat(th));
    if(j){var ds=Math.hypot(X[j]-X[j-1],Y[j]-Y[j-1]),vp=Math.sqrt(Math.max(.0016,1-(BB[j]+BB[j-1])/2/bm));tm+=ds/(64*k*vp);T.push(tm)}}
   out.push({X:X,Y:Y,NX:NX,NY:NY,B:BB,T:T,tm:tm,thm:thm,L:L,bm:bm})}return out}
 FN.dipF3=function(c,w,h,t,P,d){var k=K(w);if(d.w!==w||!d.tp){d.w=w;d.tp=trapT(w)}dipFrame(c,w,h,t,P,false);var i,j;
  for(var ii=0;ii<d.tp.length*2;ii++){i=ii>>1;var tb=d.tp[i],sg=ii%2?-1:1,ph0=i*1.37+(ii%2)*.41;
   c.strokeStyle='rgba('+P.O+',.45)';c.beginPath();[0,tb.X.length-1].forEach(function(e){var x=sg*tb.X[e],y=tb.Y[e],nx=sg*tb.NX[e],ny=tb.NY[e];c.moveTo(x-nx*4*k,y-ny*4*k);c.lineTo(x+nx*4*k,y+ny*4*k)});c.stroke();
   function pos(tt){var per=2*tb.tm,u=((tt+ph0*tb.tm)%per+per)%per,tau=u<tb.tm?u:per-u,T=tb.T,lo=0,hi=T.length-1;while(hi-lo>1){var m=(lo+hi)>>1;if(T[m]<tau)lo=m;else hi=m}var f=(tau-T[lo])/((T[hi]-T[lo])||1),
     x=tb.X[lo]+(tb.X[hi]-tb.X[lo])*f,y=tb.Y[lo]+(tb.Y[hi]-tb.Y[lo])*f,b=tb.B[lo]+(tb.B[hi]-tb.B[lo])*f,rho=3.2*k/Math.sqrt(b),off=rho*Math.sin(tt*15+ph0*5);return[sg*(x+tb.NX[lo]*off),y+tb.NY[lo]*off]}
   c.strokeStyle='rgba('+P.T+',.5)';c.beginPath();for(j=0;j<=16;j++){var p=pos(t-j*.022);j?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1])}c.stroke();var p0=pos(t);dot(c,p0[0],p0[1],1.4*k,'rgba('+P.O+',.92)')}
  c.restore();fadeName(c,w,h);var tb3=d.tp[1],a=.17+Math.sin(t*.15)*.03,lx=tb3.X[0],ly=tb3.Y[0];
  lab(c,w,'MIRROR POINT',w/2+lx*Math.cos(a)-ly*Math.sin(a)+8*k,h*.345+lx*Math.sin(a)+ly*Math.cos(a)-2*k,'left','rgba('+P.O+',.75)')};
 FN.dipF1=flow(1);FN.dipF2=flow(2);
 api.PAL=PAL;api.FN=FN;api.KINDS=['chladni','pend','twodip','interf','vdp','liss','trap','four'];
 return api})();
