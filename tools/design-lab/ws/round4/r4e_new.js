/* ===== Six new drawings N1 to N6, each with its own palette. ===== */
(function(R4){var U=R4.U,PI=Math.PI,TAU=PI*2,K=U.K,dot=U.dot,lab=U.lab,rgba=U.rgba,mix=U.mix,ease=U.ease,step=U.step;
 R4.PAL.drum={g:'#18220a',bg:'#080a05',e:'#040503',ink:'#f6ffe8',a:'#aadc50',b:'#d6f596',d:'#ffd23a',p:'#d9f2a8',m:'#93a57f',n:'#80916e',L:'170,220,80',T:'214,245,150',O:'255,210,58'};
 R4.PAL.string={g:'#151b2a',bg:'#07080c',e:'#040407',ink:'#f1f4fb',a:'#9fb6dc',b:'#e0e8f6',d:'#ffc43c',p:'#ccd8ee',m:'#8c93a6',n:'#7b8193',L:'150,175,215',T:'224,232,246',O:'255,196,60'};
 R4.PAL.mach={g:'#2a0c1a',bg:'#0b0508',e:'#060305',ink:'#ffeef4',a:'#ff5a96',b:'#ff9ac0',d:'#ffd23a',p:'#ffc0d6',m:'#ad8a98',n:'#977885',L:'255,90,150',T:'255,150,190',O:'255,210,58'};
 R4.PAL.hydro={g:'#14123a',bg:'#07070f',e:'#040408',ink:'#f0eeff',a:'#786eff',b:'#b4a8ff',d:'#ffc43c',p:'#cfc8ff',m:'#8d89b8',n:'#7b77a3',L:'120,110,255',T:'180,170,255',O:'255,196,60'};
 R4.PAL.chirp={g:'#0c1f26',bg:'#06090c',e:'#030507',ink:'#e8fbf8',a:'#3fd0c9',b:'#8fe3d0',d:'#ffd27a',p:'#b7efe6',m:'#86a3a6',n:'#748f92',L:'63,208,201',T:'143,227,208',O:'255,210,122'};
 R4.PAL.light={g:'#101a2e',bg:'#06080e',e:'#040508',ink:'#eef4ff',a:'#5ac8ff',b:'#ff6e8c',d:'#ffc43c',p:'#bfe6ff',m:'#8794ad',n:'#76829a',L:'255,110,140',T:'90,200,255',O:'255,196,60'};

 /* N1 a drum head, struck. A round membrane held at its rim moves in modes J_m(j_mn r) cos(m angle) cos(2 pi f t): m still lines across the middle and n - 1 still
    circles (amber, dashed). Each mode is struck (the amber flash), swings at its own pitch and dies away, as on a real drum. The pitches are not harmonics:
    1, 1.59, 2.14, 2.30, 2.65, 2.92 times the lowest (the zeros of the Bessel functions), which is why a drum has no clear note. The lowest is shown at 1.25 swings
    a second and the others at their true ratios. Bright mesh: above the resting plane; dim: below. The faint second mesh is the opposite end of the swing. */
 var DM=[[0,1,2.4048],[1,1,3.8317],[2,1,5.1356],[0,2,5.5201],[3,1,6.3802],[1,2,7.0156]],DZ={0:[2.4048,5.5201],1:[3.8317,7.0156],2:[5.1356],3:[6.3802]};
 function bj(m,x){var s=0,i,n=40;for(i=0;i<n;i++){var ta=(i+.5)*PI/n;s+=Math.cos(m*ta-x*Math.sin(ta))}return s/n}
 R4.FN.drum=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345+2,k=K(w),rho=Math.min(w*.265,h*.36),sq=.4,NR=12,NS=60,T=8,q=Math.floor(t/T),u=t-q*T,mi=((q%6)+6)%6,M=DM[mi],m=M[0],i,j,Hs=24*k;
  if(d.mi!==mi){d.mi=mi;d.J=[];var mx=0,ia=0;for(i=0;i<=NR;i++)d.J.push(bj(m,M[2]*i/NR));for(i=0;i<=200;i++){var v=Math.abs(bj(m,M[2]*i/200));if(v>mx+1e-9){mx=v;ia=i/200}}for(i=0;i<=NR;i++)d.J[i]/=mx;d.J[NR]=0;d.ra=ia}
  if(!d.ct){d.ct=[];d.sn=[];for(j=0;j<=NS;j++){d.ct.push(Math.cos(TAU*j/NS));d.sn.push(Math.sin(TAU*j/NS))}}
  var env=Math.exp(-u/3)*ease((T-u)/.9),A0=46*k*env,A=A0*Math.sin(TAU*1.25*M[2]/2.4048*u),ct=d.ct,sn=d.sn,cm=[],J=d.J;for(j=0;j<=NS;j++)cm.push(Math.cos(m*TAU*j/NS));
  /* the shell under the hoop */
  c.lineWidth=1;c.lineJoin='round';c.strokeStyle=rgba(P.L,.3);c.beginPath();c.moveTo(cx-rho,cy);c.lineTo(cx-rho,cy+Hs);c.ellipse(cx,cy+Hs,rho,rho*sq,0,PI,0,true);c.lineTo(cx+rho,cy);c.stroke();
  c.strokeStyle=rgba(P.L,.16);c.beginPath();for(i=-3;i<=3;i++){var lx=cx+rho*Math.sin(i*.44),ly=cy+rho*sq*Math.cos(i*.44);c.moveTo(lx,ly+3*k);c.lineTo(lx,ly+Hs-3*k)}c.stroke();
  /* the opposite end of the swing, faintly */
  var g=new Path2D(),Ag=-A0*(A<0?-1:1);for(i=3;i<NR;i+=3){g.moveTo(cx+rho*i/NR,cy-Ag*J[i]*cm[0]);for(j=1;j<=NS;j++)g.lineTo(cx+rho*i/NR*ct[j],cy+rho*i/NR*sn[j]*sq-Ag*J[i]*cm[j])}
  for(j=0;j<NS;j+=5){g.moveTo(cx,cy-Ag*J[0]*cm[j]);for(i=1;i<=NR;i++)g.lineTo(cx+rho*i/NR*ct[j],cy+rho*i/NR*sn[j]*sq-Ag*J[i]*cm[j])}c.strokeStyle=rgba(P.L,.13*Math.min(1,env*3));c.stroke(g);
  /* the mesh: far half first; each piece bright when above the resting plane, dim when below */
  var B=[new Path2D(),new Path2D(),new Path2D(),new Path2D()];
  function seg(i1,j1,i2,j2){var z1=A*J[i1]*cm[j1],z2=A*J[i2]*cm[j2],far=sn[j1]+sn[j2]<-1e-9||(i1!==i2&&sn[j1]<0),b=B[(far?0:2)+(z1+z2>0?1:0)];b.moveTo(cx+rho*i1/NR*ct[j1],cy+rho*i1/NR*sn[j1]*sq-z1);b.lineTo(cx+rho*i2/NR*ct[j2],cy+rho*i2/NR*sn[j2]*sq-z2)}
  for(i=1;i<NR;i++)for(j=0;j<NS;j++)seg(i,j,i,j+1);for(j=0;j<NS;j+=2)for(i=0;i<NR;i++)seg(i,j,i+1,j);
  c.strokeStyle=rgba(P.L,.2);c.stroke(B[0]);c.strokeStyle=rgba(P.T,.34);c.stroke(B[1]);c.strokeStyle=rgba(P.L,.5);c.stroke(B[2]);c.strokeStyle=rgba(P.T,.85);c.stroke(B[3]);
  c.strokeStyle=rgba(P.L,.8);c.lineWidth=1.5;c.beginPath();c.ellipse(cx,cy,rho,rho*sq,0,0,TAU);c.stroke();c.lineWidth=1;
  /* the still lines of this mode, on the resting plane */
  c.setLineDash([2,3]);c.strokeStyle=rgba(P.O,.25+.45*Math.min(1,env*2.5));c.beginPath();for(j=0;j<m;j++){var a=(PI/2+j*PI)/m;c.moveTo(cx-rho*Math.cos(a),cy-rho*Math.sin(a)*sq);c.lineTo(cx+rho*Math.cos(a),cy+rho*Math.sin(a)*sq)}
  if(M[1]===2){var rn=DZ[m][0]/M[2]*rho;c.moveTo(cx+rn,cy);c.ellipse(cx,cy,rn,rn*sq,0,0,TAU)}c.stroke();c.setLineDash([]);
  /* the strike */
  if(u<.45){var sf=1-u/.45,sx=cx+rho*d.ra,rr=(3+26*(1-sf))*k;c.strokeStyle=rgba(P.O,.9*sf);c.beginPath();c.ellipse(sx,cy,rr,rr*sq,0,0,TAU);c.stroke();dot(c,sx,cy,2.4*k,rgba(P.O,sf))}
  lab(c,w,'MODE ('+m+','+M[1]+')',cx-rho,cy-rho*sq-24*k,'left',rgba(P.O,.9));lab(c,w,(M[2]/2.4048).toFixed(2)+' × LOWEST',cx+rho,cy-rho*sq-24*k,'right',rgba(P.O,.9))};
 R4.BAND.drum=.84;R4.STILL.drum=40.72;

 /* N2 a plucked string. Pull a string aside at one point and let go: the corner splits in two and the two run to and fro (d'Alembert), which is the same as the sum
    of the string's harmonics with b_n = 2 sin(n pi p) / (n^2 pi^2 p (1 - p)) for a pluck at the fraction p. Pluck at 1/3 and every third harmonic is missing; at 1/2
    all the even ones. The string swings 1.8 times a second here; the fan behind it is where it was over the last 0.09 s, so the shape stays readable while
    it moves. The high harmonics die first, so the corners round off into the fundamental. Bars: the harmonics 1 to 16 as they ring. A new pluck every 9 s. */
 var PL=[[1/5,'1/5'],[1/2,'1/2'],[1/3,'1/3'],[1/8,'1/8']],SNH=24,SNJ=160,SF0=1.8,SNG=8;
 R4.FN.string=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345-6,k=K(w),E=d.ext||w*.5,wide=E>w*.6,xl=wide?cx-E*.8:w*.07,xr=wide?cx+E*.8:w*.93,Ln=xr-xl,H=44,T=9,q=Math.floor(t/T),u=t-q*T,pi=((q%4)+4)%4,p=PL[pi][0],pp=PL[((pi+3)%4)][0],n,j,g,PRE=.9;
  if(!d.S){d.S=new Float32Array((SNH+1)*(SNJ+1));for(n=1;n<=SNH;n++)for(j=0;j<=SNJ;j++)d.S[n*(SNJ+1)+j]=Math.sin(n*PI*j/SNJ);d.y=new Float32Array(SNJ+1)}
  function bn(n,pv){return 2*Math.sin(n*PI*pv)/(n*n*PI*PI*pv*(1-pv))}
  function dec(n,tau){return Math.exp(-tau*(.07+.0035*n*n))}
  /* the shape at the time uu of this pluck's cycle. While the finger pulls (0.9 s) the old ringing fades and the string is drawn aside; then it is let go */
  function shape(uu){var y=d.y,e=ease(uu/PRE),tau=uu-PRE;y.fill(0);for(n=1;n<=SNH;n++){var a=uu<PRE?bn(n,pp)*Math.cos(n*TAU*SF0*(T-PRE+uu))*dec(n,T-PRE+uu)*(1-e)+bn(n,p)*e:bn(n,p)*Math.cos(n*TAU*SF0*tau)*dec(n,tau);if(Math.abs(a)<1e-4)continue;var o=n*(SNJ+1);for(j=0;j<=SNJ;j++)y[j]+=a*d.S[o+j]}return y}
  c.lineWidth=1;c.lineJoin='round';
  /* the two extreme shapes of the ideal motion, faintly: the pluck and its mirror image half a period later */
  var xp=xl+Ln*p;c.setLineDash([2,4]);c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(xl,cy);c.lineTo(xp,cy-H);c.lineTo(xr,cy);c.lineTo(xr-Ln*p,cy+H);c.closePath();c.stroke();c.setLineDash([]);
  c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(xl-10*k,cy+.5);c.lineTo(xr+10*k,cy+.5);c.stroke();
  /* where the string was: eight earlier shapes, 1/90 s apart */
  if(u>PRE)for(g=SNG;g>=1;g--){var ug=u-g/90;if(ug<PRE)continue;var yg=shape(ug);c.strokeStyle=rgba(P.L,.46*(1-g/(SNG+1)));c.beginPath();for(j=0;j<=SNJ;j++){var xg=xl+Ln*j/SNJ;j?c.lineTo(xg,cy-yg[j]*H):c.moveTo(xg,cy)}c.stroke()}
  var y=shape(u);c.strokeStyle=rgba(P.T,.96);c.lineWidth=1.7;c.beginPath();for(j=0;j<=SNJ;j++){var x=xl+Ln*j/SNJ;j?c.lineTo(x,cy-y[j]*H):c.moveTo(x,cy)}c.stroke();c.lineWidth=1;
  c.strokeStyle=rgba(P.L,.7);c.beginPath();c.moveTo(xl,cy-9*k);c.lineTo(xl,cy+9*k);c.moveTo(xr,cy-9*k);c.lineTo(xr,cy+9*k);c.stroke();dot(c,xl,cy,2*k,rgba(P.L,.9));dot(c,xr,cy,2*k,rgba(P.L,.9));
  /* the finger */
  var fy=cy-y[Math.round(p*SNJ)]*H;if(u<PRE){dot(c,xp,fy,2.6*k,rgba(P.O,.95));c.strokeStyle=rgba(P.O,.6);c.beginPath();c.moveTo(xp,fy-5*k);c.lineTo(xp,fy-15*k);c.stroke()}
  lab(c,w,'PLUCKED AT '+PL[pi][1],xp,cy-H-12*k,p>.4?'center':'left',rgba(P.O,.85));
  /* the harmonics as they ring */
  var e2=ease(u/PRE),tau2=u-PRE,bx=cx-8*9.5*k,by=cy+H+36*k;c.strokeStyle=rgba(P.L,.3);c.beginPath();c.moveTo(bx,by+.5);c.lineTo(bx+17*9.5*k,by+.5);c.stroke();c.lineWidth=2;c.strokeStyle=rgba(P.O,.9);c.beginPath();
  for(n=1;n<=16;n++){var en=u<PRE?Math.abs(bn(n,pp))*dec(n,T-PRE+u)*(1-e2)+Math.abs(bn(n,p))*e2:Math.abs(bn(n,p))*dec(n,tau2),hh=Math.sqrt(en/1.3)*26*k,xx=Math.round(bx+n*9.5*k);if(hh>.7){c.moveTo(xx,by);c.lineTo(xx,by-hh)}}c.stroke();c.lineWidth=1;
  lab(c,w,'HARMONICS 1 TO 16',bx-8*k,by-8*k,'right',rgba(P.L,.7))};
 R4.BAND.string=.9;R4.STILL.string=37.04;

 /* N3 Doppler and the Mach cone. A source sends out a wave every 0.14 s; each one spreads at the speed of sound. As the source speeds up the waves bunch ahead
    of it (a higher pitch) and stretch behind; past Mach 1 it outruns them and they pile into a cone with sin(half angle) = 1 / Mach. The amber line is the true
    envelope of the circles drawn. The speed swings between Mach 0.4 and 1.6 over 22 s. */
 R4.FN.mach=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,cs=58,te=.14,life=2.5,NF=Math.ceil(life/te),span=2*E+330,W=TAU/22,i;
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
 R4.BAND.mach=1;

 /* N4 the hydrogen atom. Where the electron is likely to be found: 2600 points drawn from |psi|^2 in space for the states 2p, 3d, 3p, 4d, 4f, 4p (m = 0), turning
    slowly about the atom's axis, which leans towards you; near points are brighter than far ones. These are the atom's standing waves, with still surfaces like a
    drum's; the two tints are the two signs of psi. One state fades into the next every 10 s. The bar gives the scale in Bohr radii (0.0529 nm). */
 var HS=[[2,1,'2P',10,5],[3,2,'3D',21,10],[3,1,'3P',24,10],[4,2,'4D',36,20],[4,3,'4F',33,20],[4,1,'4P',40,20]],HC=[],HNP=2600;
 function psi(s,x,z){var r=Math.sqrt(x*x+z*z)+1e-9,ct=z/r,n=s[0],l=s[1],R=n===2?r*Math.exp(-r/2):n===3?(l===2?r*r:r*(6-r))*Math.exp(-r/3):(l===3?r*r*r:l===2?r*r*(12-r):r*(80-20*r+r*r))*Math.exp(-r/4);return R*(l===1?ct:l===2?3*ct*ct-1:ct*(5*ct*ct-3))}
 /* points of one state: distance from the axis, height, angle about the axis, sign. The weight is |psi|^2 times the distance from the axis (the ring's size) */
 function hcloud(si){if(HC[si])return HC[si];var S=HS[si],Rm=S[3],sd=si*7919+13,rnd=function(){sd=(sd*48271)%2147483647;return sd/2147483647},mx=0,a,b,i,o={rho:new Float32Array(HNP),z:new Float32Array(HNP),ph:new Float32Array(HNP),sg:new Int8Array(HNP)};
  for(a=1;a<=70;a++)for(b=0;b<=70;b++){var v=psi(S,a/70*Rm,(b/35-1)*Rm);mx=Math.max(mx,v*v*a/70*Rm)}
  for(i=0;i<HNP;){var x=rnd()*Rm,z=(rnd()*2-1)*Rm,pv=psi(S,x,z);if(pv*pv*x>rnd()*mx*1.1){o.rho[i]=x;o.z[i]=z;o.ph[i]=rnd()*TAU;o.sg[i]=pv<0?-1:1;i++}}return HC[si]=o}
 R4.FN.hydro=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),RP=Math.min(w*.148,h*.2),T=10,q=Math.floor(t/T),u=t-q*T,si=((q%6)+6)%6,sp=(si+5)%6,S=HS[si],Sp=HS[sp],e=ease(u/1.8),rv=Sp[3]+(S[3]-Sp[3])*e,sc=RP/rv,
   ang=t*.2,tl=.36,cT=Math.cos(tl),sT=Math.sin(tl),z1=Math.max(1,1.05*k),z2=Math.max(1.2,1.5*k),i,pass;
  c.lineWidth=1;c.setLineDash([3,5]);c.strokeStyle=rgba(P.L,.22);c.beginPath();c.moveTo(cx+.5,cy-RP*1.1);c.lineTo(cx+.5,cy+RP*1.1);c.stroke();c.setLineDash([]);
  var CA=rgba(P.T,1),CB=rgba(P.B||mix(P.L,'255,120,200',.45),1);
  function cloud(o,al){if(al<=.004)return;var rho=o.rho,zz=o.z,ph=o.ph,sg=o.sg,n=HNP,X=d.X||(d.X=new Float32Array(HNP)),Y=d.Y||(d.Y=new Float32Array(HNP)),D=d.D||(d.D=new Float32Array(HNP));
   for(i=0;i<n;i++){var a=ph[i]+ang,dy=rho[i]*Math.sin(a);X[i]=cx+rho[i]*Math.cos(a)*sc;Y[i]=cy-(zz[i]*cT-dy*sT)*sc;D[i]=dy}
   for(pass=0;pass<4;pass++){var near=pass>1,pos=pass%2===0,zs=near?z2:z1;c.fillStyle=pos?CA:CB;c.globalAlpha=al*(near?.95:.3);for(i=0;i<n;i++)if((D[i]>0)===near&&(sg[i]>0)===pos)c.fillRect(X[i]-zs/2,Y[i]-zs/2,zs,zs)}c.globalAlpha=1}
  cloud(hcloud(sp),1-e);cloud(hcloud(si),e);
  dot(c,cx,cy,2.4*k,rgba(P.O,.95));
  var bl=S[4]*sc,bx=cx+RP*1.3,by=cy+RP*.9;c.strokeStyle=rgba(P.O,.85);c.beginPath();c.moveTo(bx,by);c.lineTo(bx+bl,by);c.moveTo(bx,by-3*k);c.lineTo(bx,by+3*k);c.moveTo(bx+bl,by-3*k);c.lineTo(bx+bl,by+3*k);c.stroke();lab(c,w,S[4]+' BOHR RADII',bx,by-10*k,'left',rgba(P.O,.85));
  lab(c,w,'HYDROGEN  '+S[2],cx-RP*1.3,cy-RP*.9,'right',rgba(P.O,.9));lab(c,w,'N '+S[0]+'  L '+S[1]+'  M 0',cx-RP*1.3,cy-RP*.9+14*k,'right',rgba(P.L,.75));lab(c,w,'AXIS',cx+8*k,cy-RP*1.04,'left',rgba(P.L,.7));
  dot(c,bx+4*k,by-RP*.5,2.2*k,CA);lab(c,w,'ψ +',bx+12*k,by-RP*.5,'left',rgba(P.L,.75));dot(c,bx+4*k,by-RP*.5+13*k,2.2*k,CB);lab(c,w,'ψ −',bx+12*k,by-RP*.5+13*k,'left',rgba(P.L,.75))};
 R4.BAND.hydro=.9;R4.STILL.hydro=15;

 /* N5 the first gravitational wave heard on Earth, GW150914 (LIGO, 14 September 2015): two black holes of 36 and 29 suns circling ever faster and merging.
    The wave's frequency follows f = 35 Hz (tau / 0.17 s)^(-3/8) and its size f^(2/3), with tau the time left to the merger: a chirp from 35 to about 250 Hz in 0.2 s,
    inside the range of hearing, then the ring-down. Shown 47 times slower. The orbit turns once for every two waves, its size as tau^(1/4). */
 R4.FN.chirp=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,wide=E>w*.6,T0=8,Tc=11.5,TM=.12,NC=9.52,u=((t%Tc)+Tc)%Tc,A=44,v=52,
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
 R4.BAND.chirp=.9;

 /* N6 light. A plane electromagnetic wave: the electric field E (up and down) and the magnetic field B (towards and away from you) swing in step, at right angles
    to each other and to the direction of travel, E x B pointing along it; in vacuum E = c B. One wavelength is marked. */
 R4.FN.light=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,lam=168,AE=46,bx=-.52*56,by=.36*56,xa=cx-E-8,xb=cx+E+8,x,ph,pe=new Path2D(),pb=new Path2D(),ee=new Path2D(),eb=new Path2D(),v=.33,n=0;
  for(x=xa-((xa-cx)%8+8)%8;x<=xb;x+=8){ph=TAU*((x-cx)/lam-v*t);var s=Math.sin(ph);pb.moveTo(x,cy);pb.lineTo(x+bx*s,cy+by*s);pe.moveTo(x,cy);pe.lineTo(x,cy-AE*s)}
  for(x=xa;x<=xb;x+=3){ph=TAU*((x-cx)/lam-v*t);var s2=Math.sin(ph);n?ee.lineTo(x,cy-AE*s2):ee.moveTo(x,cy-AE*s2);n?eb.lineTo(x+bx*s2,cy+by*s2):eb.moveTo(x+bx*s2,cy+by*s2);n=1}
  c.lineWidth=1;c.lineJoin='round';c.strokeStyle=rgba(P.L,.3);c.stroke(pb);c.strokeStyle=rgba(P.L,.85);c.lineWidth=1.4;c.stroke(eb);c.lineWidth=1;
  c.strokeStyle=rgba(P.O,.4);c.beginPath();c.moveTo(xa,cy+.5);c.lineTo(xb,cy+.5);c.stroke();
  c.strokeStyle=rgba(P.T,.34);c.stroke(pe);c.strokeStyle=rgba(P.T,.92);c.lineWidth=1.4;c.stroke(ee);c.lineWidth=1;
  /* one wavelength, riding on two crests of E */
  var xc=cx-lam*.75+((lam*(.25+v*t))%lam+lam)%lam,yk=cy-AE-10*k;c.strokeStyle=rgba(P.O,.9);c.beginPath();c.moveTo(xc,yk);c.lineTo(xc+lam,yk);c.moveTo(xc,yk-3*k);c.lineTo(xc,yk+3*k);c.moveTo(xc+lam,yk-3*k);c.lineTo(xc+lam,yk+3*k);c.stroke();lab(c,w,'λ',xc+lam/2,yk-9*k,'center',rgba(P.O,.9));
  var ax=cx+w*.44;c.strokeStyle=rgba(P.O,.9);c.beginPath();c.moveTo(ax-7*k,cy-4*k);c.lineTo(ax,cy);c.lineTo(ax-7*k,cy+4*k);c.stroke();lab(c,w,'C',ax+9*k,cy,'left',rgba(P.O,.9));
  lab(c,w,'E  ELECTRIC',cx-w*.45,cy-AE-22*k,'left',rgba(P.T,.9));lab(c,w,'B  MAGNETIC',cx-w*.45+104*k,cy-AE-22*k,'left',rgba(P.L,.9))};
 R4.BAND.light=1;
 /* the drawings that run the full width of the band: the host puts a soft shade of the card's colour behind the name for these */
 R4.WIDE={fsStack:1,fsGibbs:1,fsUnc:1,string:1,mach:1,light:1};
 R4.NAME={dipP2:'Dipole field, density',dipP3:'Dipole field, energy',dipP4:'Dipole field, radiation belt',dipP5:'Dipole field, aurora',phLor:'Lorenz attractor',phFlow:'Phase flow',phPoin:'Poincaré section',phFrac:'Fractal road to chaos',
  fsWind:'Winding a wave',fsStack:'Harmonic stack',fsGibbs:'Gibbs effect',fsUnc:'Time and frequency',drum:'Drum head',string:'Plucked string',mach:'Mach cone',hydro:'Hydrogen atom',chirp:'Gravitational wave',light:'Light wave'};
 /* the final random set of the start screen, in the order of the Settings list. moons is SPLBG's; interf, liss and trap are WSR2's (round 2), unchanged */
 R4.SET=['dipP5','dipP3','dipP2','dipP4','moons','interf','liss','trap','phLor','phFlow','phPoin','phFrac','fsWind','fsStack','fsGibbs','fsUnc','drum','string','mach','hydro','chirp','light'];
})(R4);
