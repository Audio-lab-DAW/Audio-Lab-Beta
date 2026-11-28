/* ===== The Fourier series (R8, pink) reworked: four pictures of a shape built from sines. ===== */
(function(R3){var U=R3.U,PI=Math.PI,TAU=PI*2,K=U.K,dot=U.dot,lab=U.lab,rgba=U.rgba,mix=U.mix,ease=U.ease;
 R3.PAL.fs={g:'#1a1031',bg:'#08060f',e:'#040308',ink:'#f6eeff',a:'#ff7ac8',b:'#b583ff',d:'#ffd23a',p:'#e8c4ff',m:'#9a88b4',n:'#86789f',L:'181,131,255',T:'255,122,200',O:'255,210,58'};
 R3.PAL.fsAtom=R3.PAL.fsStack=R3.PAL.fsGibbs=R3.PAL.fsUnc=R3.PAL.fs;

 /* FS1 epicycles draw the AudioLab atom. Any closed curve z(s) is a sum of turning circles, z(s) = sum of c_k e^(2 pi i k s) (the complex Fourier series; the c_k are
    found here by a discrete Fourier transform of 512 points on the curve). The curve is the atom's three rings in one stroke. Circles are added largest first:
    2, 5, 12, 30, then 60 of them, one lap each (7 s), and the atom sharpens. Right: the circles' radii, the ones in use in amber. */
 var AT=null,ST=[2,5,12,30,60];
 function atom(){if(AT)return AT;var b=.36,M=512,raw=[],i,j,k;
  function seg(phi,th0,th1){/* along the ring turned by phi, from polar angle th0 to th1 (anticlockwise) */var s0=Math.atan2(Math.sin(th0-phi)/b,Math.cos(th0-phi)),s1=Math.atan2(Math.sin(th1-phi)/b,Math.cos(th1-phi));while(s1<=s0+1e-9)s1+=TAU;var n=Math.max(8,Math.round((s1-s0)/TAU*360)),cp=Math.cos(phi),sp=Math.sin(phi);for(i=0;i<n;i++){var s=s0+(s1-s0)*i/n,x=Math.cos(s),y=b*Math.sin(s);raw.push(x*cp-y*sp,x*sp+y*cp)}}
  var D=PI/180;seg(0,30*D,30*D);seg(60*D,30*D,90*D);seg(120*D,90*D,90*D);seg(60*D,90*D,30*D);
  var n=raw.length/2,cum=[0];for(i=1;i<=n;i++){j=i%n;cum.push(cum[i-1]+Math.hypot(raw[2*j]-raw[2*i-2],raw[2*j+1]-raw[2*i-1]))}
  var pts=new Float32Array(M*2),q=0;for(i=0;i<M;i++){var tg=cum[n]*i/M;while(cum[q+1]<tg)q++;var f=(tg-cum[q])/((cum[q+1]-cum[q])||1),a=q%n,c2=(q+1)%n;pts[2*i]=raw[2*a]+(raw[2*c2]-raw[2*a])*f;pts[2*i+1]=raw[2*a+1]+(raw[2*c2+1]-raw[2*a+1])*f}
  var C=[];for(k=-64;k<=64;k++){var re=0,im=0;for(i=0;i<M;i++){var an=-TAU*k*i/M,cs=Math.cos(an),sn=Math.sin(an);re+=pts[2*i]*cs-pts[2*i+1]*sn;im+=pts[2*i]*sn+pts[2*i+1]*cs}C.push({k:k,re:re/M,im:im/M,r:Math.hypot(re,im)/M})}
  var c0=C[64];C.splice(64,1);C.sort(function(p,q2){return q2.r-p.r});
  var curves=ST.map(function(N){var o=new Float32Array(M*2+2);for(i=0;i<=M;i++){var x=c0.re,y=c0.im;for(j=0;j<N;j++){var an2=TAU*C[j].k*i/M,cs2=Math.cos(an2),sn2=Math.sin(an2);x+=C[j].re*cs2-C[j].im*sn2;y+=C[j].re*sn2+C[j].im*cs2}o[2*i]=x;o[2*i+1]=y}return o});
  return AT={pts:pts,C:C,c0:c0,cur:curves,M:M}}
 R3.FN.fsAtom=function(c,w,h,t,P){var A=atom(),cx=w/2,cy=h*.345,k=K(w),S=Math.min(w*.19,h*.255),TLp=7,q=Math.floor(t/TLp),u=t/TLp-q,st=((q%ST.length)+ST.length)%ST.length,N=ST[st],M=A.M,i,j;
  function X(v){return cx+v*S}function Y(v){return cy-v*S}
  /* the atom itself, faintly; then the lap before; then this lap up to the pen */
  c.lineWidth=1;c.lineJoin='round';c.strokeStyle=rgba(P.L,.13);c.beginPath();for(i=0;i<M;i++)i?c.lineTo(X(A.pts[2*i]),Y(A.pts[2*i+1])):c.moveTo(X(A.pts[0]),Y(A.pts[1]));c.closePath();c.stroke();
  var cur=A.cur[st],m=Math.floor(u*M),fo=1-ease((u-.9)/.1);
  c.lineWidth=1.4;c.strokeStyle=rgba(P.T,.85*fo);c.beginPath();c.moveTo(X(cur[0]),Y(cur[1]));for(i=1;i<=m;i++)c.lineTo(X(cur[2*i]),Y(cur[2*i+1]));c.stroke();c.lineWidth=1;
  /* the chain of circles */
  var x=A.c0.re,y=A.c0.im,pa=new Path2D(),pb=new Path2D();pb.moveTo(X(x),Y(y));for(j=0;j<N;j++){var o=A.C[j],an=TAU*o.k*u,cs=Math.cos(an),sn=Math.sin(an),r=o.r*S;if(r>.7){pa.moveTo(X(x)+r,Y(y));pa.arc(X(x),Y(y),r,0,TAU)}x+=o.re*cs-o.im*sn;y+=o.re*sn+o.im*cs;pb.lineTo(X(x),Y(y))}
  c.strokeStyle=rgba(P.L,.2);c.stroke(pa);c.strokeStyle=rgba(P.L,.6);c.stroke(pb);dot(c,X(A.c0.re),Y(A.c0.im),2.4*k,rgba(P.O,.9));dot(c,X(x),Y(y),2.2*k,rgba(P.O,1));
  /* the radii, largest first */
  var bx=cx+S+34*k,by=cy+S*.42,bh=S*.8,nb=22,r0=Math.sqrt(A.C[0].r);c.lineWidth=2;for(i=0;i<nb;i++){var hh=Math.sqrt(A.C[i].r)/r0*bh,xx=Math.round(bx+i*4.6*k)+1;c.strokeStyle=i<N?rgba(P.O,.85):rgba(P.L,.3);c.beginPath();c.moveTo(xx,by);c.lineTo(xx,by-hh);c.stroke()}c.lineWidth=1;
  c.strokeStyle=rgba(P.L,.3);c.beginPath();c.moveTo(bx-3*k,by+.5);c.lineTo(bx+nb*4.6*k,by+.5);c.stroke();lab(c,w,'RADII',bx,by+11*k,'left',rgba(P.L,.7));
  lab(c,w,(N<10?' ':'')+N+' CIRCLES',cx-S-34*k,cy-S*.42,'right',rgba(P.O,.9));lab(c,w,'ONE STROKE',cx-S-34*k,cy-S*.42+14*k,'right',rgba(P.L,.7))};
 R3.BAND.fsAtom=.78;

 /* FS2 one sound, two views. A square, a sawtooth or a triangle wave (front, bright) is the sum of the sine waves stacked behind it, harmonic 1 to 8;
    seen from the side, the same stack is the spectrum: one bar per harmonic (amber). b_n: square 4/(pi n) for odd n; sawtooth 2/(pi n), alternating sign;
    triangle 8/(pi n)^2 for odd n, alternating sign. The wave changes every 11 s and the bars glide to the new recipe. */
 var WV=[['SQUARE',function(n){return n%2?4/(PI*n):0}],['SAWTOOTH',function(n){return(n%2?2:-2)/(PI*n)}],['TRIANGLE',function(n){return n%2?((n-1)/2%2?-1:1)*8/(PI*PI*n*n):0}]];
 R3.FN.fsStack=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,wide=E>w*.6,NH=8,T=11,q=Math.floor(t/T),u=t-q*T,f=ease((u-(T-1.6))/1.6),Wa=WV[((q%3)+3)%3],Wb=WV[(((q+1)%3)+3)%3],
   xa=wide?cx-E*.5:w*.07,xb=wide?cx+E*.5:w*.76,dx=9.5,dy=-12.2,y0=cy+50,A=23,kap=TAU/176,om=TAU*.2,n,x,a=[];
  for(n=1;n<=NH;n++)a[n]=Wa[1](n)*(1-f)+Wb[1](n)*f;
  c.lineWidth=1;c.lineJoin='round';
  /* the floor: one base line per harmonic, and the two depth edges */
  c.strokeStyle=rgba(P.L,.1);c.beginPath();for(n=0;n<=NH;n++){c.moveTo(xa+n*dx,y0+n*dy+.5);c.lineTo(xb+n*dx,y0+n*dy+.5)}c.stroke();
  c.strokeStyle=rgba(P.L,.28);c.beginPath();c.moveTo(xa,y0);c.lineTo(xa+NH*dx,y0+NH*dy);c.moveTo(xb,y0);c.lineTo(xb+(NH+.6)*dx,y0+(NH+.6)*dy);c.stroke();
  for(n=NH;n>=1;n--){var am=a[n]*A,al=.16+.6*Math.min(1,Math.abs(a[n])/1.27);c.strokeStyle=rgba(P.L,al);c.beginPath();for(x=xa;x<=xb;x+=3){var yy=y0+n*dy-am*Math.sin(n*(kap*(x-cx)-om*t));x===xa?c.moveTo(x+n*dx,yy):c.lineTo(x+n*dx,yy)}c.stroke()}
  c.strokeStyle=rgba(P.T,.9);c.lineWidth=1.5;c.beginPath();for(x=xa;x<=xb;x+=2){var s=0,ph=kap*(x-cx)-om*t;for(n=1;n<=NH;n++)s+=a[n]*Math.sin(n*ph);x===xa?c.moveTo(x,y0-s*A):c.lineTo(x,y0-s*A)}c.stroke();
  /* the spectrum on the end wall */
  c.lineWidth=2;c.strokeStyle=rgba(P.O,.9);c.beginPath();for(n=1;n<=NH;n++){var bx=Math.round(xb+n*dx)+1,by=y0+n*dy;c.moveTo(bx,by);c.lineTo(bx,by-Math.abs(a[n])*A*1.35-.5)}c.stroke();c.lineWidth=1;
  for(n=1;n<=NH;n++)dot(c,Math.round(xb+n*dx)+1,y0+n*dy-Math.abs(a[n])*A*1.35-.5,1.6*k,rgba(P.O,.95));
  lab(c,w,'1',xb+dx+8*k,y0+dy+8*k,'left',rgba(P.O,.85));lab(c,w,'8',xb+8*dx+8*k,y0+8*dy+8*k,'left',rgba(P.O,.85));lab(c,w,'HARMONIC',xb+NH*dx+10*k,y0+NH*dy-A*1.35-10*k,'right',rgba(P.O,.85));
  lab(c,w,f>.5?Wb[0]:Wa[0],xa+NH*dx,y0+NH*dy-A*1.35-10*k,'left',rgba(P.T,.5+.4*Math.abs(1-2*f)));lab(c,w,'TIME →',xb-6*k,y0+A*1.2+11*k,'right',rgba(P.L,.7))};
 R3.BAND.fsStack=.86;

 /* FS3 the Gibbs effect. Add odd harmonics one at a time and the sum closes in on a square wave everywhere except at the jump: the overshoot beside it gets
    narrower but never lower. It stays at 8.95 % of the jump (the Wilbraham-Gibbs constant: peak 1.179 for a wave of +/-1). The earlier sums linger as ghosts.
    From 1 to 24 terms (harmonic 47) in 18 s, then a rest. */
 R3.FN.fsGibbs=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,Pp=264,A=44,ST2=.75,NT=24,Tc=NT*ST2+3.5,u=((t%Tc)+Tc)%Tc,nt=Math.min(NT,1+Math.floor(u/ST2)),f=nt>=NT&&u>=NT*ST2?1:ease((u/ST2-(nt-1))/.55),
   xa=cx-E-2,M=Math.ceil((2*E+4)/1.5)+1,i,j,n,fo=Math.min(1,(Tc-u)/.8)*Math.min(1,.25+u/.6);
  function sum(nn){var o=new Float32Array(M);for(i=0;i<M;i++){var ph=TAU*(xa+i*1.5-cx)/Pp,s=0;for(n=1;n<=nn;n++)s+=Math.sin((2*n-1)*ph)/(2*n-1);o[i]=s*4/PI}return o}
  if(d.M!==M||d.q!==Math.floor(t/Tc)||d.nt>nt){d.M=M;d.q=Math.floor(t/Tc);d.nt=0;d.g=[];d.base=null}
  if(d.nt!==nt){if(d.base&&d.nt===nt-1){var nb=new Float32Array(M),kk=2*d.nt-1;for(i=0;i<M;i++)nb[i]=d.base[i]+4/PI*Math.sin(kk*TAU*(xa+i*1.5-cx)/Pp)/kk;if(d.nt>0){d.g.unshift(nb);if(d.g.length>5)d.g.pop()}d.base=nb}else{d.base=sum(nt-1);d.g=[];for(j=1;j<=5&&nt-j>=1;j++)d.g.push(sum(nt-j))}d.nt=nt}
  c.lineWidth=1;c.lineJoin='round';
  /* the square wave aimed at, and the level the overshoot keeps */
  c.setLineDash([2,4]);c.strokeStyle=rgba(P.L,.22);c.beginPath();var j0=Math.floor((xa-cx)/(Pp/2))-1;for(j=j0;cx+j*Pp/2<cx+E+Pp;j++){var xs=cx+j*Pp/2,up=((j%2)+2)%2===0;c.moveTo(xs,cy+(up?A:-A));c.lineTo(xs,cy+(up?-A:A));c.lineTo(xs+Pp/2,cy+(up?-A:A))}c.stroke();
  c.strokeStyle=rgba(P.O,.34);c.beginPath();c.moveTo(cx-E,cy-1.179*A);c.lineTo(cx+E,cy-1.179*A);c.moveTo(cx-E,cy+1.179*A);c.lineTo(cx+E,cy+1.179*A);c.stroke();c.setLineDash([]);
  c.strokeStyle=rgba(P.L,.2);c.beginPath();c.moveTo(cx-E,cy+.5);c.lineTo(cx+E,cy+.5);c.stroke();
  var GA=[.24,.17,.12,.08,.05];for(j=d.g.length-1;j>=1;j--){var g=d.g[j];c.strokeStyle=rgba(P.L,GA[j]*fo);c.beginPath();for(i=0;i<M;i++)i?c.lineTo(xa+i*1.5,cy-g[i]*A):c.moveTo(xa,cy-g[0]*A);c.stroke()}
  var kk2=2*nt-1,am=f*4/PI/kk2,b=d.base;c.strokeStyle=rgba(P.T,.92*fo);c.lineWidth=1.5;c.beginPath();for(i=0;i<M;i++){var v=b[i]+am*Math.sin(kk2*TAU*(xa+i*1.5-cx)/Pp);i?c.lineTo(xa+i*1.5,cy-v*A):c.moveTo(xa,cy-v*A)}c.stroke();c.lineWidth=1;
  /* the first peak on each side of every jump: at a quarter period divided by the number of terms */
  var off=Pp/(4*nt),pv=0;for(n=1;n<=nt;n++)pv+=Math.sin((2*n-1)*TAU*off/Pp)/(2*n-1)*(n===nt?f:1);pv*=4/PI;
  for(j=j0;cx+j*Pp/2<cx+E+Pp;j++){var xj=cx+j*Pp/2,sg=((j%2)+2)%2===0?1:-1;dot(c,xj+off,cy-sg*pv*A,2*k,rgba(P.O,.95*fo));dot(c,xj-off,cy+sg*pv*A,2*k,rgba(P.O,.95*fo))}
  lab(c,w,'OVERSHOOT 8.95 %',cx+w*.45,cy-1.179*A-9*k,'right',rgba(P.O,.85));lab(c,w,(nt<10?' ':'')+nt+(nt===1?' TERM ':' TERMS')+'  UP TO HARMONIC '+kk2,cx-w*.45,cy-1.179*A-9*k,'left',rgba(P.L,.75))};
 R3.BAND.fsGibbs=1;

 /* FS4 short in time, wide in frequency. A train of pulses built from 30 harmonics with a bell-shaped spectrum, a_n = exp(-n^2 / 2 s^2). Narrow the spectrum and the
    pulse spreads out; widen it and the pulse sharpens to a click. The two widths (amber) always multiply to the same number: dt * df = 1 / (2 pi), the uncertainty
    relation of every sound. s breathes between 1.6 and 11 harmonics over 18 s. */
 R3.FN.fsUnc=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,wide=E>w*.6,NH=30,Pp=196,A=64,sg=Math.exp(Math.log(1.6)+(Math.log(11)-Math.log(1.6))*(.5-.5*Math.cos(TAU*t/18))),
   xa=wide?cx-E*.56:w*.05,xb=wide?cx+E*.16:w*.56,xs=wide?cx+E*.27:w*.64,bs=wide?7.2:6.2,xc=xa+(xb-xa)*.5,yb=cy+40,a=[],sa=0,n,x;
  for(n=1;n<=NH;n++){a[n]=Math.exp(-n*n/(2*sg*sg));sa+=a[n]}
  c.lineWidth=1;c.lineJoin='round';c.strokeStyle=rgba(P.L,.26);c.beginPath();c.moveTo(xa,yb+.5);c.lineTo(xb,yb+.5);c.moveTo(xs-4*k,yb+.5);c.lineTo(xs+(NH+1)*bs,yb+.5);c.moveTo(Math.round(xs)-.5,yb);c.lineTo(Math.round(xs)-.5,yb-A-4*k);c.stroke();
  /* the pulse train: the sum of the 30 harmonics */
  c.strokeStyle=rgba(P.T,.92);c.lineWidth=1.5;c.beginPath();for(x=xa;x<=xb;x+=2){var ph=TAU*(x-xc)/Pp,s=0;for(n=1;n<=NH;n++)s+=a[n]*Math.cos(n*ph);s/=sa;x===xa?c.moveTo(x,yb-s*A):c.lineTo(x,yb-s*A)}c.stroke();c.lineWidth=1;
  /* the spectrum and its bell */
  c.strokeStyle=rgba(P.L,.3);c.beginPath();for(x=0;x<=NH+.5;x+=.5){var v=Math.exp(-x*x/(2*sg*sg));x?c.lineTo(xs+x*bs,yb-v*A):c.moveTo(xs,yb-A)}c.stroke();
  c.lineWidth=2;c.strokeStyle=rgba(P.T,.85);c.beginPath();for(n=1;n<=NH;n++){var bx=Math.round(xs+n*bs),hh=a[n]*A;if(hh<.6)continue;c.moveTo(bx,yb);c.lineTo(bx,yb-hh)}c.stroke();c.lineWidth=1;
  /* the two widths: one standard deviation each way in time, one in frequency */
  var wt=Pp/(TAU*sg),wf=sg*bs,yk=yb+10*k;c.strokeStyle=rgba(P.O,.9);c.beginPath();c.moveTo(xc-wt,yk);c.lineTo(xc+wt,yk);c.moveTo(xc-wt,yk-3*k);c.lineTo(xc-wt,yk+3*k);c.moveTo(xc+wt,yk-3*k);c.lineTo(xc+wt,yk+3*k);
  c.moveTo(xs,yk);c.lineTo(xs+wf,yk);c.moveTo(xs,yk-3*k);c.lineTo(xs,yk+3*k);c.moveTo(xs+wf,yk-3*k);c.lineTo(xs+wf,yk+3*k);c.stroke();
  lab(c,w,'ΔT',xc+wt+7*k,yk,'left',rgba(P.O,.9));lab(c,w,'ΔF',xs+wf+7*k,yk,'left',rgba(P.O,.9));
  lab(c,w,'TIME',xa,yb-A-6*k,'left',rgba(P.L,.7));lab(c,w,'FREQUENCY',xs+(NH+1)*bs,yb-A-6*k,'right',rgba(P.L,.7));lab(c,w,'ΔT · ΔF = 1 / 2π',wide?(xb+xs)/2:xb,yb-A-6*k,wide?'center':'right',rgba(P.O,.85))};
 R3.BAND.fsUnc=.95;
})(R3);
