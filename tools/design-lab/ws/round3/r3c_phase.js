/* ===== The phase portrait (R5, green) reworked: four pictures of a system's motion drawn in its state space. ===== */
(function(R3){var U=R3.U,PI=Math.PI,TAU=PI*2,K=U.K,dot=U.dot,lab=U.lab,rgba=U.rgba,mix=U.mix,step=U.step;
 R3.PAL.ph={g:'#0b2019',bg:'#050a08',e:'#030605',ink:'#e8fff3',a:'#3ecf8e',b:'#a3f7c9',d:'#ffd23a',p:'#b8f5d6',m:'#83a597',n:'#729184',L:'62,207,142',T:'163,247,201',O:'255,210,58'};
 R3.PAL.phLor=R3.PAL.phFlow=R3.PAL.phPoin=R3.PAL.phBif=R3.PAL.ph;

 /* PH1 the Lorenz attractor: dx = 10(y - x), dy = x(28 - z) - y, dz = xy - (8/3)z (Lorenz 1963). The faint curve is one long orbit; it never closes and never
    crosses itself. Nine tracers start 0.001 apart: they travel as one dot for a while, then part and end up anywhere on the butterfly (sensitive dependence).
    Shown swinging slowly about the z axis. Time 0.8 units a second; a new start every 24 s. */
 function lor(s,h){var x=s[0],y=s[1],z=s[2],B=8/3,a1=10*(y-x),b1=x*(28-z)-y,c1=x*y-B*z,x2=x+a1*h/2,y2=y+b1*h/2,z2=z+c1*h/2,a2=10*(y2-x2),b2=x2*(28-z2)-y2,c2=x2*y2-B*z2,
   x3=x+a2*h/2,y3=y+b2*h/2,z3=z+c2*h/2,a3=10*(y3-x3),b3=x3*(28-z3)-y3,c3=x3*y3-B*z3,x4=x+a3*h,y4=y+b3*h,z4=z+c3*h,a4=10*(y4-x4),b4=x4*(28-z4)-y4,c4=x4*y4-B*z4;
  s[0]=x+h/6*(a1+2*a2+2*a3+a4);s[1]=y+h/6*(b1+2*b2+2*b3+b4);s[2]=z+h/6*(c1+2*c2+2*c3+c4)}
 var LZ=null,LN=3800;
 function lzPath(){if(LZ)return LZ;var s=[1,1,1],i;for(i=0;i<1500;i++)lor(s,.008);LZ=new Float32Array(LN*3);for(i=0;i<LN;i++){lor(s,.008);LZ[3*i]=s[0];LZ[3*i+1]=s[1];LZ[3*i+2]=s[2]}return LZ}
 R3.FN.phLor=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),sc=Math.min(w*.0066,h*.0089),NTR=9,TL=64,Tc=24,rate=.8,q=Math.floor(t/Tc),u=t-q*Tc,p=lzPath(),i,j,dt=step(d,t);
  function init(){d.q=q;d.s=[];d.tr=[];d.hx=[];d.ht=[];var b=((q*977)%LN+LN)%LN;for(i=0;i<NTR;i++){d.s.push([p[3*b]+i*.001,p[3*b+1],p[3*b+2]]);d.tr.push([]);d.hx.push([])}d.sim=0}
  function adv(hh){for(i=0;i<NTR;i++){var s=d.s[i],tr=d.tr[i];lor(s,hh);tr.push(s[0],s[1],s[2]);if(tr.length>TL*3)tr.splice(0,3)}d.sim+=hh;if(d.sim>=d.ht.length*.04){d.ht.push(d.sim);for(i=0;i<NTR;i++)d.hx[i].push(d.s[i][0])}}
  if(d.q!==q||dt<0){init();var want=u*rate;while(d.sim<want-1e-9)adv(Math.min(.0125,want-d.sim))}else if(dt>0){var hh=dt*rate,n=Math.ceil(hh/.02);for(j=0;j<n;j++)adv(hh/n)}
  var a=.2+.8*Math.sin(t*.11),ca=Math.cos(a),sa=Math.sin(a),ce=Math.cos(.22),se=Math.sin(.22);
  function X(x,y){return cx+(x*ca+y*sa)*sc}function Y(x,y,z){return cy-((z-24)*ce+(-x*sa+y*ca)*se)*sc}
  c.lineWidth=1;c.lineJoin='round';c.strokeStyle=rgba(P.L,.25);c.beginPath();for(i=0;i<LN;i++){var x=p[3*i],y=p[3*i+1],z=p[3*i+2];i?c.lineTo(X(x,y),Y(x,y,z)):c.moveTo(X(x,y),Y(x,y,z))}c.stroke();
  /* the two fixed points the orbit circles */
  c.strokeStyle=rgba(P.L,.5);c.beginPath();for(i=-1;i<=1;i+=2){var fx=X(i*8.485,i*8.485),fy=Y(i*8.485,i*8.485,27);c.moveTo(fx-3*k,fy);c.lineTo(fx+3*k,fy);c.moveTo(fx,fy-3*k);c.lineTo(fx,fy+3*k)}c.stroke();
  var f=Math.min(1,u/.8)*Math.min(1,(Tc-u)/1.2),pa=new Path2D(),pb=new Path2D(),far=0;
  for(i=0;i<NTR;i++){var tr=d.tr[i],m=tr.length/3,hm=Math.max(0,m-TL/2|0);for(j=0;j<m;j++){var px=X(tr[3*j],tr[3*j+1]),py=Y(tr[3*j],tr[3*j+1],tr[3*j+2]);if(j<hm)j?pa.lineTo(px,py):pa.moveTo(px,py);else{if(j===hm){if(j)pa.lineTo(px,py);pb.moveTo(px,py)}else pb.lineTo(px,py)}}
   if(i){var s0=d.s[0],s1=d.s[i];far=Math.max(far,Math.hypot(s1[0]-s0[0],s1[1]-s0[1],s1[2]-s0[2]))}}
  c.strokeStyle=rgba(P.T,.3*f);c.stroke(pa);c.lineWidth=1.3;c.strokeStyle=rgba(P.T,.75*f);c.stroke(pb);c.lineWidth=1;
  for(i=0;i<NTR;i++){var s2=d.s[i];dot(c,X(s2[0],s2[1]),Y(s2[0],s2[1],s2[2]),1.7*k,rgba(P.O,.95*f))}
  var bw=Math.min(w*.3,h*.42);lab(c,w,'LORENZ  σ 10  ρ 28  β 8/3',cx-bw,cy-84*k,'left',rgba(P.L,.7));
  lab(c,w,'9 STARTS 0.001 APART',cx+bw,cy-84*k,'right',rgba(P.O,.85));lab(c,w,'NOW '+(far<.01?far.toFixed(3):far<1?far.toFixed(2):far.toFixed(1))+' APART',cx+bw,cy-70*k,'right',rgba(P.O,.85*f));
  /* in the wide band: x of each of the nine against time. One line at first, then they part */
  var E=d.ext||w*.5;if(E>w*.6){var xa=cx+bw+46*k,xb=cx+E-26*k,ln=xb-xa,hs=1.75*k,nh=d.ht.length;c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(xa,cy+.5);c.lineTo(xb,cy+.5);c.moveTo(Math.round(xa)+.5,cy-40*k);c.lineTo(Math.round(xa)+.5,cy+40*k);c.stroke();
   for(i=NTR-1;i>=0;i--){var hx=d.hx[i];c.strokeStyle=rgba(P.T,(i?.34:.8)*f);c.beginPath();for(j=0;j<nh;j++){var xx=xa+d.ht[j]/(Tc*rate)*ln,yy=cy-hx[j]*hs;j?c.lineTo(xx,yy):c.moveTo(xx,yy)}c.stroke();if(nh)dot(c,xa+d.ht[nh-1]/(Tc*rate)*ln,cy-d.s[i][0]*hs,1.4*k,rgba(P.O,.9*f))}
   lab(c,w,'X OF EACH START, OVER TIME',xa+6*k,cy-84*k,'left',rgba(P.L,.7))}};
 R3.BAND.phLor=.82;

 /* PH2 the flow of the Van der Pol oscillator, x'' - mu (1 - x^2) x' + x = 0, over the whole plane (x across, dx/dt up). Streaks follow the flow, coloured by its speed
    (dim and green where slow, bright where fast); every one of them is drawn onto the same closed loop, the limit cycle. mu breathes between 0.3 and 3:
    the loop goes from a near circle (a sine tone) to a sharp-cornered relaxation shape. Dashed: the curve where dx/dt stops changing (the nullcline). */
 function vdp(s,h,mu){var x=s[0],y=s[1],a1=y,b1=mu*(1-x*x)*y-x,x2=x+a1*h/2,y2=y+b1*h/2,a2=y2,b2=mu*(1-x2*x2)*y2-x2,x3=x+a2*h/2,y3=y+b2*h/2,a3=y3,b3=mu*(1-x3*x3)*y3-x3,x4=x+a3*h,y4=y+b3*h,a4=y4,b4=mu*(1-x4*x4)*y4-x4;
  s[0]=x+h/6*(a1+2*a2+2*a3+a4);s[1]=y+h/6*(b1+2*b2+2*b3+b4)}
 R3.FN.phFlow=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,sx=44,sy=16,HY=6.1,XM=3.75,mu=1.65+1.35*Math.sin(t*.12),dt=step(d,t),i,j,N=130,HV=6.5;
  function X(v){return cx+v*sx}function Y(v){return cy-v*sy}
  function spawn(o){o.x=(Math.random()*2-1)*XM;o.y=(Math.random()*2-1)*HY;o.tr=[X(o.x),Y(o.y)];o.life=1.6+Math.random()*2.6;o.age=0;o.sp=0}
  function adv(h2){for(i=0;i<d.p.length;i++){var o=d.p[i],tr=o.tr;o.age+=h2;if(o.age>o.life||Math.abs(o.x)>XM||Math.abs(o.y)>HY){tr.splice(0,4);if(tr.length<4)spawn(o);continue}
    var vx=o.y,vy=mu*(1-o.x*o.x)*o.y-o.x,ux=vx*sx,uy=-vy*sy,m=Math.hypot(ux,uy)||1,sp=Math.min(1,Math.log(1+Math.hypot(vx,vy))/3.6),ds=(22+46*sp)*h2;o.sp=sp;o.x+=ux/m*ds/sx;o.y-=uy/m*ds/sy;
    var px=X(o.x),py=Y(o.y),n=tr.length;if(n<4||Math.hypot(px-tr[n-4],py-tr[n-3])>3.2){tr.push(px,py);if(tr.length>30)tr.splice(0,2)}else{tr[n-2]=px;tr[n-1]=py}}}
  if(!d.p||d.n!==N||dt<0){d.n=N;d.p=[];for(i=0;i<N;i++){var o={};spawn(o);o.age=Math.random()*o.life*.6;d.p.push(o)}d.cs=[2,0];d.hv=[];d.hc=0;for(i=0;i<2500;i++)vdp(d.cs,.02,mu);for(j=0;j<HV*60;j++){vdp(d.cs,1/60,mu);d.hv.push(d.cs[1])}for(j=0;j<70;j++)adv(1/60)}
  else if(dt>0){adv(dt);var ns=Math.max(1,Math.ceil(dt/.02));for(j=0;j<ns;j++)vdp(d.cs,dt/ns,mu);d.hc+=dt*60;while(d.hc>=1){d.hc-=1;d.hv.push(d.cs[1]);if(d.hv.length>HV*60)d.hv.shift()}}
  /* axes and ticks */
  c.lineWidth=1;c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(X(-XM),cy+.5);c.lineTo(X(XM),cy+.5);c.moveTo(cx+.5,Y(HY));c.lineTo(cx+.5,Y(-HY));for(i=-Math.floor(XM);i<=XM;i++){c.moveTo(X(i),cy-3*k);c.lineTo(X(i),cy+3*k)}for(i=-6;i<=6;i+=2){c.moveTo(cx-3*k,Y(i));c.lineTo(cx+3*k,Y(i))}c.stroke();
  /* nullcline y = x / (mu (1 - x^2)) */
  c.setLineDash([3,5]);c.strokeStyle=rgba(P.L,.2);c.beginPath();var pen=0;for(var xv=-XM;xv<=XM;xv+=.04){var den=mu*(1-xv*xv),yv=Math.abs(den)<1e-3?99:xv/den;if(Math.abs(yv)>HY){pen=0;continue}pen?c.lineTo(X(xv),Y(yv)):c.moveTo(X(xv),Y(yv));pen=1}c.stroke();c.setLineDash([]);
  /* the streaks, in four speed classes */
  var B=[new Path2D(),new Path2D(),new Path2D(),new Path2D()];for(i=0;i<d.p.length;i++){var tr=d.p[i].tr,b=B[Math.min(3,d.p[i].sp*4|0)];if(tr.length<4)continue;b.moveTo(tr[0],tr[1]);for(j=2;j<tr.length;j+=2)b.lineTo(tr[j],tr[j+1])}
  var C=[rgba(P.L,.3),rgba(P.L,.55),rgba(P.T,.62),rgba(mix(P.T,P.O,.55),.8)];c.lineJoin='round';for(i=0;i<4;i++){c.strokeStyle=C[i];c.stroke(B[i])}
  /* the limit cycle at this mu, from the point that rides it */
  var s=[d.cs[0],d.cs[1]];c.strokeStyle=rgba(P.T,.85);c.lineWidth=1.4;c.beginPath();c.moveTo(X(s[0]),Y(s[1]));for(i=0;i<460;i++){vdp(s,.02,mu);c.lineTo(X(s[0]),Y(s[1]))}c.stroke();c.lineWidth=1;
  dot(c,X(d.cs[0]),Y(d.cs[1]),2.3*k,rgba(P.O,.95));
  lab(c,w,'VAN DER POL  μ '+mu.toFixed(2),X(-XM),cy-86*k,'left',rgba(P.O,.85));lab(c,w,'LIMIT CYCLE',X(XM),cy-86*k,'right',rgba(P.T,.8));lab(c,w,'X',X(XM),cy+10*k,'right',rgba(P.L,.7));lab(c,w,'DX/DT',cx+8*k,cy-72*k,'left',rgba(P.L,.7));
  /* in the wide band: the same motion against time (the newest at the left, level with the dot): a sine at small mu, a buzz at large mu */
  if(E>w*.6){var xa=X(XM)+34*k,xb=cx+E-26*k,hv=d.hv,nh=hv.length,pv=(xb-xa)/(HV*60);c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(xa,cy+.5);c.lineTo(xb,cy+.5);c.moveTo(Math.round(xa)+.5,Y(HY));c.lineTo(Math.round(xa)+.5,Y(-HY));c.stroke();
   c.setLineDash([3,4]);c.strokeStyle=rgba(P.O,.3);c.beginPath();c.moveTo(X(d.cs[0]),Y(d.cs[1]));c.lineTo(xa,Y(d.cs[1]));c.stroke();c.setLineDash([]);
   c.strokeStyle=rgba(P.T,.8);c.lineWidth=1.4;c.beginPath();for(i=0;i<nh;i++){var xx=xa+i*pv,yy=Y(hv[nh-1-i]);i?c.lineTo(xx,yy):c.moveTo(xx,yy)}c.stroke();c.lineWidth=1;dot(c,xa,Y(d.cs[1]),1.8*k,rgba(P.O,.95));
   lab(c,w,'DX/DT OVER TIME',xa+6*k,cy-86*k,'left',rgba(P.L,.7))}};
 R3.BAND.phFlow=.84;

 /* PH3 a Poincare section. The driven Duffing oscillator, x'' + 0.3 x' - x + x^3 = 0.5 cos(1.2 t), is chaotic. Photograph it once per turn of the drive, always at
    the same drive phase, and the points fall on a strange attractor: a sheet stretched and folded over itself. Here 1500 states are shown at one drive phase,
    and the phase is swept: the sheet stretches, folds and comes back onto itself once per turn (11.6 s). The amber dot is one state and its path. */
 var DF=null,DN=1500,DW=1.2,DTP=TAU/1.2,DH=DTP/100;
 function duf(xs,vs,n,tau,h2){var c0=.5*Math.cos(DW*tau),c1=.5*Math.cos(DW*(tau+h2/2)),c2=.5*Math.cos(DW*(tau+h2)),i;for(i=0;i<n;i++){var x=xs[i],v=vs[i],a1=v,b1=-.3*v+x-x*x*x+c0,x2=x+a1*h2/2,v2=v+b1*h2/2,a2=v2,b2=-.3*v2+x2-x2*x2*x2+c1,
    x3=x+a2*h2/2,v3=v+b2*h2/2,a3=v3,b3=-.3*v3+x3-x3*x3*x3+c1,x4=x+a3*h2,v4=v+b3*h2,a4=v4,b4=-.3*v4+x4-x4*x4*x4+c2;xs[i]=x+h2/6*(a1+2*a2+2*a3+a4);vs[i]=v+h2/6*(b1+2*b2+2*b3+b4)}}
 function dufSec(){if(DF)return DF;var x=new Float32Array([.1]),v=new Float32Array([.1]),i,j;DF=new Float32Array(DN*2);for(i=-40;i<DN;i++){for(j=0;j<100;j++)duf(x,v,1,j*DH,DH);if(i>=0){DF[2*i]=x[0];DF[2*i+1]=v[0]}}return DF}
 R3.FN.phPoin=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),sx=Math.min(w*.14,h*.19),sy=sx*1.12,rate=.45,dt=step(d,t),i,tau=(t*rate)%DTP;
  if(!d.xs||dt<0){var S=dufSec();d.xs=new Float32Array(DN);d.vs=new Float32Array(DN);for(i=0;i<DN;i++){d.xs[i]=S[2*i];d.vs[i]=S[2*i+1]}var n=Math.floor(tau/DH);d.tr=[];for(i=0;i<n;i++){duf(d.xs,d.vs,DN,i*DH,DH);d.tr.push(d.xs[0],d.vs[0])}d.tau=n*DH;if(d.tr.length>180)d.tr.splice(0,d.tr.length-180)}
  else if(dt>0){duf(d.xs,d.vs,DN,d.tau,dt*rate);d.tau+=dt*rate;d.tr.push(d.xs[0],d.vs[0]);if(d.tr.length>180)d.tr.splice(0,2)}
  function X(v){return cx+v*sx}function Y(v){return cy-v*sy}
  c.lineWidth=1;c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(X(-2),cy+.5);c.lineTo(X(2),cy+.5);c.moveTo(cx+.5,Y(1.15));c.lineTo(cx+.5,Y(-1.15));for(i=-1;i<=1;i+=2){c.moveTo(X(i),cy-3*k);c.lineTo(X(i),cy+3*k);c.moveTo(cx-3*k,Y(i));c.lineTo(cx+3*k,Y(i))}c.stroke();
  c.fillStyle=rgba(P.T,.8);var z=Math.max(1,1.25*k),xs=d.xs,vs=d.vs;for(i=0;i<DN;i++)c.fillRect(cx+xs[i]*sx-z/2,cy-vs[i]*sy-z/2,z,z);
  var tr=d.tr;if(tr.length>3){c.strokeStyle=rgba(P.O,.4);c.beginPath();for(i=0;i<tr.length;i+=2)i?c.lineTo(X(tr[i]),Y(tr[i+1])):c.moveTo(X(tr[i]),Y(tr[i+1]));c.stroke()}
  dot(c,X(xs[0]),Y(vs[0]),2.2*k,rgba(P.O,.95));
  /* the drive's phase as a small dial */
  var ph=DW*d.tau,dx=X(2)-10*k,dy=Y(1.15)+12*k,dr=9*k;c.strokeStyle=rgba(P.L,.45);c.beginPath();c.arc(dx,dy,dr,0,TAU);c.stroke();c.strokeStyle=rgba(P.O,.9);c.beginPath();c.moveTo(dx,dy);c.lineTo(dx+dr*Math.sin(ph),dy-dr*Math.cos(ph));c.stroke();
  var deg=Math.round(((ph*180/PI)%360+360)%360);lab(c,w,'DRIVE PHASE '+(deg<100?deg<10?'  ':' ':'')+deg+'°',dx-dr-8*k,dy,'right',rgba(P.O,.85));
  lab(c,w,'POINCARÉ SECTION  DUFFING',X(-2),Y(1.15)+12*k,'left',rgba(P.L,.7));lab(c,w,'X',X(2),cy+10*k,'right',rgba(P.L,.7));lab(c,w,'DX/DT',cx+8*k,Y(1.15)+26*k,'left',rgba(P.L,.7))};
 R3.BAND.phPoin=.78;

 /* PH4 the road to chaos: the logistic map x -> r x (1 - x). For each growth rate r the dots show where x ends up: one value, then 2, 4, 8 ... (period doubling,
    each step 4.669 times shorter: Feigenbaum), chaos from r = 3.5699, and inside the chaos a window of period 3 at 3.8284. The cursor draws the diagram in 14 s, then sweeps r to and fro and shows the orbit there; it starts again every 66 s. */
 var BW=760,BH=300,R0=2.85,R1=4;
 R3.FN.phBif=function(c,w,h,t,P,d){var cx=w/2+((d.ext||0)>w*.6?44:0),cy=h*.345,k=K(w),FH=Math.min(w*.74,h*1.02)*.39,FW=(d.ext||0)>w*.6?FH*3.5:FH/.39,x0=cx-FW/2,y0=cy-FH/2-2*k,i,j,T1=14,TP=T1+52,u=((t%TP)+TP)%TP,prog=Math.min(1,u/T1),
   tri=u<T1?prog:1-Math.abs(((u-T1)/26)%2-1),rc=R0+(R1-R0)*tri,want=Math.round(prog*BW),fo=Math.min(1,(TP-u)/1.2);
  if(!d.b||d.pc!==P.T||want<d.col){d.b=document.createElement('canvas');d.b.width=BW;d.b.height=BH;d.x=d.b.getContext('2d');d.col=0;d.pc=P.T}
  if(d.col<want){d.x.fillStyle=rgba(P.T,.42);for(i=d.col;i<want;i++){var r=R0+(R1-R0)*i/(BW-1),x=.5;for(j=0;j<160;j++)x=r*x*(1-x);for(j=0;j<70;j++){x=r*x*(1-x);d.x.fillRect(i,Math.round((1-x)*(BH-1)),1,1)}}d.col=want}
  c.imageSmoothingEnabled=true;c.globalAlpha=fo;c.drawImage(d.b,x0,y0,FW,FH);c.globalAlpha=1;
  c.lineWidth=1;c.strokeStyle=rgba(P.L,.3);c.beginPath();c.moveTo(Math.round(x0)-.5,y0);c.lineTo(Math.round(x0)-.5,y0+FH+4*k);c.moveTo(x0-4*k,Math.round(y0+FH)+.5);c.lineTo(x0+FW,Math.round(y0+FH)+.5);
  var M=[[3,'3.0'],[3.4495,''],[3.5699,'3.57'],[3.8284,'3.83'],[4,'4.0']];for(i=0;i<M.length;i++){var mx=x0+(M[i][0]-R0)/(R1-R0)*FW;c.moveTo(mx,y0+FH);c.lineTo(mx,y0+FH+4*k)}c.stroke();
  for(i=0;i<M.length;i++)if(M[i][1])lab(c,w,M[i][1],x0+(M[i][0]-R0)/(R1-R0)*FW,y0+FH+11*k,'center',rgba(P.L,.7));
  var X=x0+(rc-R0)/(R1-R0)*FW,xo=.5;c.strokeStyle=rgba(P.O,.4);c.beginPath();c.moveTo(X,y0);c.lineTo(X,y0+FH);c.stroke();for(j=0;j<400;j++)xo=rc*xo*(1-xo);for(j=0;j<32;j++){xo=rc*xo*(1-xo);dot(c,X,y0+(1-xo)*FH,1.5*k,rgba(P.O,.9))}
  var rt=X>x0+FW*.5;lab(c,w,'R '+rc.toFixed(3),X+(rt?-7:7)*k,y0+7*k,rt?'right':'left',rgba(P.O,.9));
  lab(c,w,'X → R · X (1 − X)',x0+6*k,y0-9*k,'left',rgba(P.L,.7));lab(c,w,rc<3?'ONE VALUE':rc<3.4495?'PERIOD 2':rc<3.5441?'PERIOD 4':rc<3.5699?'PERIOD 8, 16 …':rc>3.8284&&rc<3.8415?'PERIOD 3':'CHAOS',x0+FW,y0-9*k,'right',rgba(P.O,.85))};
 R3.BAND.phBif=.86;
})(R3);
