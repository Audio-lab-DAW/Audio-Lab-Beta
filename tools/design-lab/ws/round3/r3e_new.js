/* ===== Six new drawings N1 to N6, each with its own palette. ===== */
(function(R3){var U=R3.U,PI=Math.PI,TAU=PI*2,K=U.K,dot=U.dot,lab=U.lab,rgba=U.rgba,mix=U.mix,ease=U.ease,step=U.step;
 R3.PAL.drum={g:'#18220a',bg:'#080a05',e:'#040503',ink:'#f6ffe8',a:'#aadc50',b:'#d6f596',d:'#ffd23a',p:'#d9f2a8',m:'#93a57f',n:'#80916e',L:'170,220,80',T:'214,245,150',O:'255,210,58'};
 R3.PAL.string={g:'#151b2a',bg:'#07080c',e:'#040407',ink:'#f1f4fb',a:'#9fb6dc',b:'#e0e8f6',d:'#ffc43c',p:'#ccd8ee',m:'#8c93a6',n:'#7b8193',L:'150,175,215',T:'224,232,246',O:'255,196,60'};
 R3.PAL.mach={g:'#2a0c1a',bg:'#0b0508',e:'#060305',ink:'#ffeef4',a:'#ff5a96',b:'#ff9ac0',d:'#ffd23a',p:'#ffc0d6',m:'#ad8a98',n:'#977885',L:'255,90,150',T:'255,150,190',O:'255,210,58'};
 R3.PAL.hydro={g:'#14123a',bg:'#07070f',e:'#040408',ink:'#f0eeff',a:'#786eff',b:'#b4a8ff',d:'#ffc43c',p:'#cfc8ff',m:'#8d89b8',n:'#7b77a3',L:'120,110,255',T:'180,170,255',O:'255,196,60'};
 R3.PAL.chirp={g:'#0c1f26',bg:'#06090c',e:'#030507',ink:'#e8fbf8',a:'#3fd0c9',b:'#8fe3d0',d:'#ffd27a',p:'#b7efe6',m:'#86a3a6',n:'#748f92',L:'63,208,201',T:'143,227,208',O:'255,210,122'};
 R3.PAL.light={g:'#101a2e',bg:'#06080e',e:'#040508',ink:'#eef4ff',a:'#5ac8ff',b:'#ff6e8c',d:'#ffc43c',p:'#bfe6ff',m:'#8794ad',n:'#76829a',L:'255,110,140',T:'90,200,255',O:'255,196,60'};

 /* N1 a drum head. A round membrane held at its rim moves in modes J_m(j_mn r) cos(m theta): m still lines across the middle and n still circles (amber, dashed).
    Their pitches are not harmonics: 1, 1.59, 2.14, 2.30, 2.65, 2.92 times the lowest (the zeros of the Bessel functions), which is why a drum has no clear note.
    Six modes, 9 s each, moving at their true ratios. */
 var DM=[[0,1,2.4048],[1,1,3.8317],[2,1,5.1356],[0,2,5.5201],[3,1,6.3802],[1,2,7.0156]],DZ={0:[2.4048,5.5201],1:[3.8317,7.0156],2:[5.1356],3:[6.3802]};
 function bj(m,x){var s=0,i,n=40;for(i=0;i<n;i++){var ta=(i+.5)*PI/n;s+=Math.cos(m*ta-x*Math.sin(ta))}return s/n}
 R3.FN.drum=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345+6,k=K(w),rho=Math.min(w*.28,h*.38),sq=.42,NR=10,NS=48,T=9,q=Math.floor(t/T),u=t-q*T,mi=((q%6)+6)%6,M=DM[mi],m=M[0],i,j;
  if(d.mi!==mi){d.mi=mi;d.J=[];var mx=0;for(i=0;i<=NR;i++){var v=bj(m,M[2]*i/NR);d.J.push(v)}for(i=0;i<=200;i++)mx=Math.max(mx,Math.abs(bj(m,M[2]*i/200)));for(i=0;i<=NR;i++)d.J[i]/=mx;d.J[NR]=0}
  var env=ease(u/1)*ease((T-u)/1),A=40*k*env*Math.cos(TAU*.42*M[2]/2.4048*t),cm=[],ct=[],sn=[];for(j=0;j<=NS;j++){var th=TAU*j/NS;cm.push(Math.cos(m*th));ct.push(Math.cos(th));sn.push(Math.sin(th))}
  function PX(i,j){return cx+rho*i/NR*ct[j]}function PY(i,j){return cy+rho*i/NR*sn[j]*sq-A*d.J[i]*cm[j]}
  var far=new Path2D(),near=new Path2D();for(i=1;i<NR;i++){near.moveTo(PX(i,0),PY(i,0));for(j=1;j<=NS/2;j++)near.lineTo(PX(i,j),PY(i,j));far.moveTo(PX(i,NS/2),PY(i,NS/2));for(j=NS/2+1;j<=NS;j++)far.lineTo(PX(i,j),PY(i,j))}
  for(j=0;j<NS;j+=2){var pp=j>0&&j<NS/2?near:far;pp.moveTo(PX(0,j),PY(0,j));for(i=1;i<=NR;i++)pp.lineTo(PX(i,j),PY(i,j))}
  c.lineWidth=1;c.lineJoin='round';c.strokeStyle=rgba(P.L,.2);c.stroke(far);c.strokeStyle=rgba(P.L,.5);c.stroke(near);
  c.strokeStyle=rgba(P.L,.7);c.lineWidth=1.3;c.beginPath();c.ellipse(cx,cy,rho,rho*sq,0,0,TAU);c.stroke();c.lineWidth=1;
  /* the still lines of this mode, on the resting plane */
  c.setLineDash([2,3]);c.strokeStyle=rgba(P.O,.6*env);c.beginPath();for(j=0;j<m;j++){var a=(PI/2+j*PI)/m;c.moveTo(cx-rho*Math.cos(a),cy-rho*Math.sin(a)*sq);c.lineTo(cx+rho*Math.cos(a),cy+rho*Math.sin(a)*sq)}
  if(M[1]===2){var rn=DZ[m][0]/M[2]*rho;c.moveTo(cx+rn,cy);c.ellipse(cx,cy,rn,rn*sq,0,0,TAU)}c.stroke();c.setLineDash([]);
  lab(c,w,'MODE ('+m+','+M[1]+')',cx-rho,cy-rho*sq-22*k,'left',rgba(P.O,.6+.3*env));lab(c,w,(M[2]/2.4048).toFixed(2)+' × LOWEST',cx+rho,cy-rho*sq-22*k,'right',rgba(P.O,.6+.3*env))};
 R3.BAND.drum=.82;

 /* N2 a plucked string. Pull a string aside at one point and let go: the corner splits in two and runs both ways (d'Alembert), which is the same as the sum of the
    string's harmonics with b_n = 2 sin(n pi p) / (n^2 pi^2 p (1 - p)) for a pluck at the fraction p. Pluck at 1/3 and every third harmonic is missing; at 1/2 all the
    even ones. The high harmonics die first, so the corners round off into the fundamental. Bars: the harmonics 1 to 16 as they ring. A new pluck every 9 s. */
 var PL=[[1/5,'1/5'],[1/2,'1/2'],[1/3,'1/3'],[1/8,'1/8']],SNH=24,SNJ=200;
 R3.FN.string=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345-6,k=K(w),E=d.ext||w*.5,wide=E>w*.6,xl=wide?cx-E*.8:w*.07,xr=wide?cx+E*.8:w*.93,Ln=xr-xl,H=36,T=9,q=Math.floor(t/T),u=t-q*T,pi=((q%4)+4)%4,p=PL[pi][0],pp=PL[((pi+3)%4)][0],n,j,PRE=.9;
  if(!d.S){d.S=new Float32Array((SNH+1)*(SNJ+1));for(n=1;n<=SNH;n++)for(j=0;j<=SNJ;j++)d.S[n*(SNJ+1)+j]=Math.sin(n*PI*j/SNJ)}
  function bn(n,pv){return 2*Math.sin(n*PI*pv)/(n*n*PI*PI*pv*(1-pv))}
  function amp(n,pv,tau){return bn(n,pv)*Math.cos(n*TAU*.55*tau)*Math.exp(-tau*(.1+.022*n*n))}
  var e=ease(u/PRE),tau=Math.max(0,u-PRE),y=new Float32Array(SNJ+1),cf=[];
  /* while the finger pulls (0.9 s) the old ringing fades and the string is drawn aside; then it is let go */
  for(n=1;n<=SNH;n++){var a=u<PRE?amp(n,pp,T-PRE+u)*(1-e)+bn(n,p)*e:amp(n,p,tau);cf[n]=a;var o=n*(SNJ+1);for(j=0;j<=SNJ;j++)y[j]+=a*d.S[o+j]}
  c.lineWidth=1;c.lineJoin='round';
  /* the two extreme shapes of the ideal motion, faintly: the pluck and its mirror image half a period later */
  var xp=xl+Ln*p;c.setLineDash([2,4]);c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(xl,cy);c.lineTo(xp,cy-H);c.lineTo(xr,cy);c.lineTo(xr-Ln*p,cy+H);c.closePath();c.stroke();c.setLineDash([]);
  c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(xl-10*k,cy+.5);c.lineTo(xr+10*k,cy+.5);c.stroke();
  c.strokeStyle=rgba(P.T,.95);c.lineWidth=1.6;c.beginPath();for(j=0;j<=SNJ;j++){var x=xl+Ln*j/SNJ;j?c.lineTo(x,cy-y[j]*H):c.moveTo(x,cy)}c.stroke();c.lineWidth=1;
  c.strokeStyle=rgba(P.L,.7);c.beginPath();c.moveTo(xl,cy-9*k);c.lineTo(xl,cy+9*k);c.moveTo(xr,cy-9*k);c.lineTo(xr,cy+9*k);c.stroke();dot(c,xl,cy,2*k,rgba(P.L,.9));dot(c,xr,cy,2*k,rgba(P.L,.9));
  /* the finger */
  var fy=cy-y[Math.round(p*SNJ)]*H;if(u<PRE){dot(c,xp,fy,2.6*k,rgba(P.O,.95));c.strokeStyle=rgba(P.O,.6);c.beginPath();c.moveTo(xp,fy-5*k);c.lineTo(xp,fy-15*k);c.stroke()}
  lab(c,w,'PLUCKED AT '+PL[pi][1],xp,cy-H-12*k,p>.4?'center':'left',rgba(P.O,.85));
  /* the harmonics as they ring */
  var bx=cx-8*9.5*k,by=cy+H+34*k;c.strokeStyle=rgba(P.L,.3);c.beginPath();c.moveTo(bx,by+.5);c.lineTo(bx+17*9.5*k,by+.5);c.stroke();c.lineWidth=2;c.strokeStyle=rgba(P.O,.9);c.beginPath();
  for(n=1;n<=16;n++){var en=u<PRE?Math.abs(bn(n,pp))*Math.exp(-(T-PRE+u)*(.1+.022*n*n))*(1-e)+Math.abs(bn(n,p))*e:Math.abs(bn(n,p))*Math.exp(-tau*(.1+.022*n*n)),hh=Math.sqrt(en/1.3)*26*k,xx=Math.round(bx+n*9.5*k);if(hh>.7){c.moveTo(xx,by);c.lineTo(xx,by-hh)}}c.stroke();c.lineWidth=1;
  lab(c,w,'HARMONICS 1 TO 16',bx-8*k,by-8*k,'right',rgba(P.L,.7))};
 R3.BAND.string=.9;

 /* N3 Doppler and the Mach cone. A source sends out a wave every 0.14 s; each one spreads at the speed of sound. As the source speeds up the waves bunch ahead
    of it (a higher pitch) and stretch behind; past Mach 1 it outruns them and they pile into a cone with sin(half angle) = 1 / Mach. The amber line is the true
    envelope of the circles drawn. The speed swings between Mach 0.4 and 1.6 over 22 s. */
 R3.FN.mach=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,cs=58,te=.14,life=2.5,NF=Math.ceil(life/te),span=2*E+330,W=TAU/22,i;
  function Mn(tt){return 1+.6*Math.sin(W*tt)}function Xu(tt){return cs*(tt+.6/W*(1-Math.cos(W*tt)))}function wr(xu){return cx-E-165+((xu%span)+span)%span}
  var xs=wr(Xu(t)),M=Mn(t),tk=Math.floor(t/te)*te,env=[];
  c.lineWidth=1;c.setLineDash([3,5]);c.strokeStyle=rgba(P.L,.16);c.beginPath();c.moveTo(cx-E,cy+.5);c.lineTo(cx+E,cy+.5);c.stroke();c.setLineDash([]);
  for(i=0;i<=NF;i++){var t0=tk-i*te,age=t-t0,r=cs*age,xe=wr(Xu(t0)),al=Math.pow(Math.max(0,1-age/life),1.3);if(al<=0)continue;c.strokeStyle=rgba(P.L,.62*al);c.beginPath();c.arc(xe,cy,Math.max(.1,r),0,TAU);c.stroke();
   var Me=Mn(t0);if(Me>1.001&&xe<=xs+1)env.push(xe+r/Me,r*Math.sqrt(1-1/(Me*Me)),al)}
  if(M>1.001&&env.length>3){for(var sg=-1;sg<=1;sg+=2){c.strokeStyle=rgba(P.O,.7);c.beginPath();c.moveTo(xs,cy);for(i=0;i<env.length;i+=3)c.lineTo(env[i],cy+sg*env[i+1]);c.stroke()}}
  dot(c,xs,cy,2.6*k,rgba(P.O,1));
  var lx=Math.max(cx-E+70*k,Math.min(cx+E-70*k,xs));lab(c,w,'MACH '+M.toFixed(2),lx,cy-16*k,'center',rgba(P.O,.9));
  lab(c,w,M>1.001?'CONE HALF ANGLE '+Math.round(Math.asin(1/M)*180/PI)+'°':'WAVES BUNCH AHEAD',cx+w*.45,cy-78*k,'right',rgba(P.O,.85));lab(c,w,M>1.001?'FASTER THAN ITS SOUND':'SLOWER THAN ITS SOUND',cx-w*.45,cy-78*k,'left',rgba(P.L,.75));
  U.fadeName(c,w,h)};
 R3.BAND.mach=1;

 /* N4 the hydrogen atom. Where the electron is likely to be found: 1400 dots drawn from |psi|^2 in a plane through the nucleus, for the states 2p, 3d, 3p, 4d, 4f, 4p
    (m = 0). These are the atom's standing waves, with still surfaces like a drum's; the two tints are the two signs of psi. The dots wander by a Metropolis random
    walk, so they re-settle when the state changes (every 9 s). The bar shows the scale in Bohr radii (0.0529 nm). */
 var HS=[[2,1,'2P',10,5],[3,2,'3D',21,10],[3,1,'3P',24,10],[4,2,'4D',36,20],[4,3,'4F',33,20],[4,1,'4P',40,20]];
 function psi(s,x,z){var r=Math.sqrt(x*x+z*z)+1e-9,ct=z/r,n=s[0],l=s[1],R=n===2?r*Math.exp(-r/2):n===3?(l===2?r*r:r*(6-r))*Math.exp(-r/3):(l===3?r*r*r:l===2?r*r*(12-r):r*(80-20*r+r*r))*Math.exp(-r/4);return R*(l===1?ct:l===2?3*ct*ct-1:ct*(5*ct*ct-3))}
 R3.FN.hydro=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),RP=Math.min(w*.17,h*.225),NP=1400,T=9,q=Math.floor(t/T),u=t-q*T,si=((q%6)+6)%6,S=HS[si],Sp=HS[(si+5)%6],dt=step(d,t),i,rv=Sp[3]+(S[3]-Sp[3])*ease(u/1.6);
  if(!d.x||dt<0){d.x=new Float32Array(NP);d.z=new Float32Array(NP);d.p=new Float32Array(NP);d.sg=new Int8Array(NP);d.si=si;var mx=0,a,b;for(a=0;a<60;a++)for(b=0;b<60;b++){var v=psi(S,(a/30-1)*S[3],(b/30-1)*S[3]);mx=Math.max(mx,v*v)}
   for(i=0;i<NP;){var x=(Math.random()*2-1)*S[3],z=(Math.random()*2-1)*S[3],pv=psi(S,x,z);if(pv*pv>Math.random()*mx*1.15){d.x[i]=x;d.z[i]=z;d.p[i]=pv*pv;d.sg[i]=pv<0?-1:1;i++}}d.k=0;rv=S[3]}
  else if(dt>0){if(d.si!==si){d.si=si;for(i=0;i<NP;i++){var p0=psi(S,d.x[i],d.z[i]);d.p[i]=p0*p0;d.sg[i]=p0<0?-1:1}}
   /* Metropolis: a few hundred walkers try a step each frame; right after a change all of them, with longer steps */
   var hot=u<2.6,sgm=S[3]*(hot?.085:.04),n=hot?NP:NP/5|0;for(var m=0;m<n;m++){i=d.k=(d.k+1)%NP;var x2=d.x[i]+(Math.random()*2-1)*sgm,z2=d.z[i]+(Math.random()*2-1)*sgm,p2=psi(S,x2,z2),pq=p2*p2;if(pq>=d.p[i]||pq>Math.random()*d.p[i]){d.x[i]=x2;d.z[i]=z2;d.p[i]=pq;d.sg[i]=p2<0?-1:1}}}
  var sc=RP/rv,zz=Math.max(1,1.3*k);
  c.lineWidth=1;c.setLineDash([3,5]);c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(cx+.5,cy-RP*1.08);c.lineTo(cx+.5,cy+RP*1.08);c.stroke();c.setLineDash([]);
  c.fillStyle=rgba(P.T,.85);for(i=0;i<NP;i++)if(d.sg[i]>0)c.fillRect(cx+d.x[i]*sc-zz/2,cy-d.z[i]*sc-zz/2,zz,zz);
  c.fillStyle=rgba(mix(P.L,P.T,.15),.85);for(i=0;i<NP;i++)if(d.sg[i]<0)c.fillRect(cx+d.x[i]*sc-zz/2,cy-d.z[i]*sc-zz/2,zz,zz);
  dot(c,cx,cy,2.2*k,rgba(P.O,.95));
  var bl=S[4]*sc,bx=cx+RP*1.25,by=cy+RP*.9;c.strokeStyle=rgba(P.O,.85);c.beginPath();c.moveTo(bx,by);c.lineTo(bx+bl,by);c.moveTo(bx,by-3*k);c.lineTo(bx,by+3*k);c.moveTo(bx+bl,by-3*k);c.lineTo(bx+bl,by+3*k);c.stroke();lab(c,w,S[4]+' BOHR RADII',bx,by-10*k,'left',rgba(P.O,.85));
  lab(c,w,'HYDROGEN  '+S[2],cx-RP*1.25,cy-RP*.9,'right',rgba(P.O,.9));lab(c,w,'N '+S[0]+'  L '+S[1]+'  M 0',cx-RP*1.25,cy-RP*.9+14*k,'right',rgba(P.L,.75));lab(c,w,'Z',cx+8*k,cy-RP*1.02,'left',rgba(P.L,.7))};
 R3.BAND.hydro=.9;

 /* N5 the first gravitational wave heard on Earth, GW150914 (LIGO, 14 September 2015): two black holes of 36 and 29 suns circling ever faster and merging.
    The wave's frequency follows f = 35 Hz (tau / 0.17 s)^(-3/8) and its size f^(2/3), with tau the time left to the merger: a chirp from 35 to about 250 Hz in 0.2 s,
    inside the range of hearing, then the ring-down. Shown 47 times slower. The orbit turns once for every two waves, its size as tau^(1/4). */
 R3.FN.chirp=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,wide=E>w*.6,T0=8,Tc=11.5,TM=.12,NC=9.52,u=((t%Tc)+Tc)%Tc,A=44,v=52,
   ox=wide?cx-E*.34:w*.17,xa=wide?cx-E*.19:w*.34,xn=wide?cx+E*.62:w*.9,i,x;
  function phi(tau){return TAU*NC*(1-Math.pow(Math.max(tau,TM)/T0,.625))}
  var PM=phi(TM),FR=TAU*5.3;
  function hOf(uu){uu=((uu%Tc)+Tc)%Tc;var tau=T0-uu;if(tau>TM)return Math.min(1,uu/.7)*Math.pow(tau/T0,-.25)/2.857*Math.cos(phi(tau));var s=TM-tau;return Math.exp(-s/.2)*Math.cos(PM+FR*s)}
  c.lineWidth=1;c.lineJoin='round';c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(xa,cy+.5);c.lineTo(xn+14*k,cy+.5);c.stroke();
  c.strokeStyle=rgba(P.T,.92);c.lineWidth=1.5;c.beginPath();for(x=xa;x<=xn;x+=1.5){var y=cy-A*hOf(u-(xn-x)/v)*Math.min(1,(x-xa)/40);x===xa?c.moveTo(x,y):c.lineTo(x,y)}c.stroke();c.lineWidth=1;
  var hn=hOf(u);c.setLineDash([2,3]);c.strokeStyle=rgba(P.O,.45);c.beginPath();c.moveTo(xn,cy-A*1.25);c.lineTo(xn,cy+A*1.25);c.stroke();c.setLineDash([]);dot(c,xn,cy-A*hn,2.3*k,rgba(P.O,1));
  /* the two black holes about their centre of mass */
  var tau=T0-u,am=44*k;function body(uu,j){var ta=Math.max(TM,T0-uu),a=am*Math.pow(ta/T0,.25),ph=phi(ta)/2+(j?PI:0),r=a*(j?36/65:29/65);return[ox+r*Math.cos(ph),cy-r*Math.sin(ph)*.72]}
  c.strokeStyle=rgba(P.L,.16);c.beginPath();c.ellipse(ox,cy,am*.5,am*.5*.72,0,0,TAU);c.stroke();
  if(tau>TM){for(var j=0;j<2;j++){c.strokeStyle=rgba(P.T,.5);c.beginPath();for(i=0;i<=26;i++){var b=body(Math.max(0,u-i*.035),j);i?c.lineTo(b[0],b[1]):c.moveTo(b[0],b[1])}c.stroke();var b0=body(u,j);dot(c,b0[0],b0[1],(j?2.6:3.1)*k,rgba(P.O,1))}}
  else{var s=TM-tau,f=Math.max(0,1-s/1.6);dot(c,ox,cy,3.9*k,rgba(P.O,1));for(i=0;i<3;i++){var rr=(s-i*.22)*70*k;if(rr>0&&rr<am*1.5){c.strokeStyle=rgba(P.T,.6*f*(1-rr/(am*1.5)));c.beginPath();c.ellipse(ox,cy,rr,rr*.72,0,0,TAU);c.stroke()}}}
  var fr=tau>TM?35*Math.pow(tau/T0,-.375):250;lab(c,w,tau>TM?'F '+(fr<100?' ':'')+Math.round(fr)+' HZ':s<1.2?'MERGED  250 HZ':'RING-DOWN',xn,cy-A*1.25-9*k,'right',rgba(P.O,.9));
  lab(c,w,'GW150914  STRAIN',xa,cy-A*1.25-9*k,'left',rgba(P.L,.75));lab(c,w,'36 + 29 SUNS',ox,cy+am*.72+10*k,'center',rgba(P.L,.75));
  /* 20 ms of real time */
  var bl=.02*47*v,bx=xn-bl-8*k,by=cy+A*1.25;c.strokeStyle=rgba(P.O,.8);c.beginPath();c.moveTo(bx,by);c.lineTo(bx+bl,by);c.moveTo(bx,by-3*k);c.lineTo(bx,by+3*k);c.moveTo(bx+bl,by-3*k);c.lineTo(bx+bl,by+3*k);c.stroke();lab(c,w,'20 MS',bx-7*k,by,'right',rgba(P.O,.85))};
 R3.BAND.chirp=.9;

 /* N6 light. A plane electromagnetic wave: the electric field E (up and down) and the magnetic field B (towards and away from you) swing in step, at right angles
    to each other and to the direction of travel, E x B pointing along it; in vacuum E = c B. One wavelength is marked. */
 R3.FN.light=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,lam=168,AE=46,bx=-.52*56,by=.36*56,xa=cx-E-8,xb=cx+E+8,x,ph,pe=new Path2D(),pb=new Path2D(),ee=new Path2D(),eb=new Path2D(),v=.33,n=0;
  for(x=xa-((xa-cx)%8+8)%8;x<=xb;x+=8){ph=TAU*((x-cx)/lam-v*t);var s=Math.sin(ph);pb.moveTo(x,cy);pb.lineTo(x+bx*s,cy+by*s);pe.moveTo(x,cy);pe.lineTo(x,cy-AE*s)}
  for(x=xa;x<=xb;x+=3){ph=TAU*((x-cx)/lam-v*t);var s2=Math.sin(ph);n?ee.lineTo(x,cy-AE*s2):ee.moveTo(x,cy-AE*s2);n?eb.lineTo(x+bx*s2,cy+by*s2):eb.moveTo(x+bx*s2,cy+by*s2);n=1}
  c.lineWidth=1;c.lineJoin='round';c.strokeStyle=rgba(P.L,.3);c.stroke(pb);c.strokeStyle=rgba(P.L,.85);c.lineWidth=1.4;c.stroke(eb);c.lineWidth=1;
  c.strokeStyle=rgba(P.O,.4);c.beginPath();c.moveTo(xa,cy+.5);c.lineTo(xb,cy+.5);c.stroke();
  c.strokeStyle=rgba(P.T,.34);c.stroke(pe);c.strokeStyle=rgba(P.T,.92);c.lineWidth=1.4;c.stroke(ee);c.lineWidth=1;
  /* one wavelength, riding on two crests of E */
  var xc=cx-lam*.75+((lam*(.25+v*t))%lam+lam)%lam,yk=cy-AE-10*k;c.strokeStyle=rgba(P.O,.9);c.beginPath();c.moveTo(xc,yk);c.lineTo(xc+lam,yk);c.moveTo(xc,yk-3*k);c.lineTo(xc,yk+3*k);c.moveTo(xc+lam,yk-3*k);c.lineTo(xc+lam,yk+3*k);c.stroke();lab(c,w,'λ',xc+lam/2,yk-9*k,'center',rgba(P.O,.9));
  var ax=cx+w*.44;c.strokeStyle=rgba(P.O,.9);c.beginPath();c.moveTo(ax-7*k,cy-4*k);c.lineTo(ax,cy);c.lineTo(ax-7*k,cy+4*k);c.stroke();lab(c,w,'C',ax+9*k,cy,'left',rgba(P.O,.9));
  lab(c,w,'E  ELECTRIC',cx-w*.45,cy-AE-22*k,'left',rgba(P.T,.9));lab(c,w,'B  MAGNETIC',cx-w*.45+104*k,cy-AE-22*k,'left',rgba(P.L,.9))};
 R3.BAND.light=1;
 /* the drawings that run the full width of the band: the host puts a soft shade of the card's colour behind the name for these */
 R3.WIDE={fsStack:1,fsGibbs:1,fsUnc:1,string:1,mach:1,light:1};
 R3.NAME={dipP0:'Dipole field',dipP1:'Dipole field',dipP2:'Dipole field',dipP3:'Dipole field',dipP4:'Dipole field',dipP5:'Dipole field',phLor:'Lorenz attractor',phFlow:'Phase flow',phPoin:'Poincaré section',phBif:'Road to chaos',
  fsAtom:'Fourier atom',fsStack:'Harmonic stack',fsGibbs:'Gibbs effect',fsUnc:'Time and frequency',drum:'Drum head',string:'Plucked string',mach:'Mach cone',hydro:'Hydrogen atom',chirp:'Gravitational wave',light:'Light wave'};
})(R3);
