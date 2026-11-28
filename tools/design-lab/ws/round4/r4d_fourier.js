/* ===== The Fourier series (R8, pink) reworked: four pictures of a shape built from sines. ===== */
(function(R4){var U=R4.U,PI=Math.PI,TAU=PI*2,K=U.K,dot=U.dot,lab=U.lab,rgba=U.rgba,mix=U.mix,ease=U.ease;
 R4.PAL.fs={g:'#1a1031',bg:'#08060f',e:'#040308',ink:'#f6eeff',a:'#ff7ac8',b:'#b583ff',d:'#ffd23a',p:'#e8c4ff',m:'#9a88b4',n:'#86789f',L:'181,131,255',T:'255,122,200',O:'255,210,58'};
 R4.PAL.fsWind=R4.PAL.fsStack=R4.PAL.fsGibbs=R4.PAL.fsUnc=R4.PAL.fs;

 /* FS1 how a harmonic is found. Take two periods of a wave f and wind them round a circle, k turns to a period: z = f(angle) e^(-i k angle). For most k the curve balances about the
    centre. When k is a whole number n, the centre of mass of the curve is exactly the wave's nth Fourier coefficient, c_n = (1/2 pi) integral of f e^(-i n angle):
    it leaps out to half the amplitude of harmonic n, or sits at the centre when the wave has no such harmonic, and the curve closes on itself. The winding number runs from 0.5 to 6.5 (lingering on
    the whole numbers) and the distance of the centre of mass is plotted as it goes: the spectrum appears, with peaks at the wave's harmonics 2, 3 and 5. */
 var WA=[0,0,1,.55,0,.8,0],WS=2.35,WN=480,WF=null,WSP=null,WT=20,WHD=2.6;
 function wf(){if(WF)return WF;WF=new Float32Array(WN+1);for(var i=0;i<=WN;i++){var s=0,n;for(n=1;n<7;n++)s+=WA[n]*Math.cos(n*2*TAU*i/WN);WF[i]=s/WS}return WF}
 function wcm(kk,o){var F=wf(),re=0,im=0,i;for(i=0;i<WN;i++){var a=kk*2*TAU*i/WN;re+=F[i]*Math.cos(a);im-=F[i]*Math.sin(a)}o[0]=re/WN;o[1]=im/WN;return o}
 function wsp(){if(WSP)return WSP;WSP=new Float32Array(351);var o=[0,0];for(var i=0;i<=350;i++){wcm(i*.02,o);WSP[i]=Math.hypot(o[0],o[1])}return WSP}
 R4.FN.fsWind=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,wide=E>w*.6,F=wf(),SP=wsp(),Tc=WT+WHD,u=((t%Tc)+Tc)%Tc,s=Math.min(1,u/WT),uu=.5+6*s,kk=uu-.13*Math.sin(TAU*uu),fo=Math.min(1,(Tc-u)/.7)*Math.min(1,.3+u/.5),
   Rw=wide?66:70,ccx=wide?cx-76:cx-128,xs0=wide?cx+56:cx-18,xs1=wide?cx+E*.6:cx+252,ys=cy+(wide?52:58),hs=(wide?86:64)/.213,wx0=wide?cx-E*.6:xs0,wx1=wide?cx-186:xs1,wy=wide?cy-38:cy-56,wa=wide?30:17,i,o=[0,0];
  function XK(v){return xs0+(xs1-xs0)*v/7}
  c.lineWidth=1;c.lineJoin='round';
  /* the wave, one period, with a tick at every full turn of the winding */
  c.strokeStyle=rgba(P.L,.22);c.beginPath();c.moveTo(wx0,wy+.5);c.lineTo(wx1,wy+.5);c.stroke();
  c.strokeStyle=rgba(P.O,.6);c.beginPath();for(i=0;i<=2*kk+1e-6;i++){var tx=wx0+(wx1-wx0)*i/(2*kk);c.moveTo(tx,wy-wa-3*k);c.lineTo(tx,wy+wa+3*k)}c.stroke();
  c.strokeStyle=rgba(P.L,.85);c.lineWidth=1.3;c.beginPath();for(i=0;i<=WN;i+=2){var x=wx0+(wx1-wx0)*i/WN;i?c.lineTo(x,wy-F[i]*wa):c.moveTo(x,wy-F[0]*wa)}c.stroke();c.lineWidth=1;
  lab(c,w,'TWO PERIODS OF A WAVE',wx0,wy-wa-11*k,'left',rgba(P.L,.7));lab(c,w,'1 TURN',wx0+(wx1-wx0)/(2*kk)+5*k,wy+wa+2*k,'left',rgba(P.O,.8));
  /* the wave wound round the circle */
  c.strokeStyle=rgba(P.L,.2);c.beginPath();c.arc(ccx,cy,Rw,0,TAU);c.moveTo(ccx-Rw-5*k,cy+.5);c.lineTo(ccx+Rw+5*k,cy+.5);c.moveTo(ccx+.5,cy-Rw-5*k);c.lineTo(ccx+.5,cy+Rw+5*k);c.stroke();
  c.strokeStyle=rgba(P.T,.9*fo);c.lineWidth=1.4;c.beginPath();for(i=0;i<=WN;i++){var a=kk*2*TAU*i/WN,zx=ccx+F[i]*Rw*Math.cos(a),zy=cy+F[i]*Rw*Math.sin(a);i?c.lineTo(zx,zy):c.moveTo(zx,zy)}c.stroke();c.lineWidth=1;
  wcm(kk,o);var mx=ccx+o[0]*Rw,my=cy-o[1]*Rw,mag=Math.hypot(o[0],o[1]);c.strokeStyle=rgba(P.O,.8);c.beginPath();c.moveTo(ccx,cy);c.lineTo(mx,my);c.stroke();dot(c,mx,my,2.6*k,rgba(P.O,1));
  lab(c,w,kk.toFixed(2)+' TURNS A PERIOD',ccx,cy-Rw-13*k,'center',rgba(P.T,.9));
  /* the centre of mass against the winding number: the spectrum, as far as it has been measured */
  c.strokeStyle=rgba(P.L,.28);c.beginPath();c.moveTo(xs0-4*k,ys+.5);c.lineTo(xs1,ys+.5);c.moveTo(Math.round(xs0)-.5,ys);c.lineTo(Math.round(xs0)-.5,ys-.213*hs-6*k);for(i=1;i<=6;i++){c.moveTo(XK(i),ys);c.lineTo(XK(i),ys+4*k)}c.stroke();
  for(i=1;i<=6;i++)lab(c,w,''+i,XK(i),ys+11*k,'center',WA[i]&&kk>i-.02?rgba(P.O,.9):rgba(P.L,.7));
  var ne=Math.min(350,Math.floor(kk/.02));c.strokeStyle=rgba(P.T,.92*fo);c.lineWidth=1.5;c.beginPath();for(i=25;i<=ne;i++){i>25?c.lineTo(XK(i*.02),ys-SP[i]*hs):c.moveTo(XK(.5),ys-SP[25]*hs)}c.lineTo(XK(kk),ys-mag*hs);c.stroke();c.lineWidth=1;
  for(i=1;i<=6;i++)if(WA[i]&&kk>=i)dot(c,XK(i),ys-WA[i]/WS/2*hs,2*k,rgba(P.O,.95*fo));
  c.setLineDash([2,3]);c.strokeStyle=rgba(P.O,.4);c.beginPath();c.moveTo(XK(kk),ys);c.lineTo(XK(kk),ys-mag*hs);c.stroke();c.setLineDash([]);dot(c,XK(kk),ys-mag*hs,2.3*k,rgba(P.O,1));
  var near=Math.round(kk),hit=Math.abs(kk-near)<.06&&near>=1&&near<=6;
  lab(c,w,hit?(WA[near]?'HARMONIC '+near+' FOUND':'NO HARMONIC '+near):'CENTRE OF MASS',xs1,ys-.213*hs-(wide?2:6)*k,'right',rgba(P.O,hit?.95:.75));lab(c,w,'TURNS',xs1,ys+11*k,'right',rgba(P.L,.7))};
 R4.BAND.fsWind=.86;R4.STILL.fsWind=15;

 /* FS2 one sound, two views. A square, a sawtooth or a triangle wave (front, bright) is the sum of the sine waves stacked behind it, harmonic 1 to 8;
    seen from the side, the same stack is the spectrum: one bar per harmonic (amber). b_n: square 4/(pi n) for odd n; sawtooth 2/(pi n), alternating sign;
    triangle 8/(pi n)^2 for odd n, alternating sign. The wave changes every 11 s and the bars glide to the new recipe. */
 var WV=[['SQUARE',function(n){return n%2?4/(PI*n):0}],['SAWTOOTH',function(n){return(n%2?2:-2)/(PI*n)}],['TRIANGLE',function(n){return n%2?((n-1)/2%2?-1:1)*8/(PI*PI*n*n):0}]];
 R4.FN.fsStack=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,wide=E>w*.6,NH=8,T=11,q=Math.floor(t/T),u=t-q*T,f=ease((u-(T-1.6))/1.6),Wa=WV[((q%3)+3)%3],Wb=WV[(((q+1)%3)+3)%3],
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
 R4.BAND.fsStack=.86;

 /* FS3 the Gibbs effect. Add odd harmonics one at a time and the sum closes in on a square wave everywhere except at the jump: the overshoot beside it gets
    narrower but never lower. It stays at 8.95 % of the jump (the Wilbraham-Gibbs constant: peak 1.179 for a wave of +/-1). The earlier sums linger as ghosts.
    From 1 to 24 terms (harmonic 47) in 18 s, then a rest. */
 R4.FN.fsGibbs=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,Pp=264,A=44,ST2=.75,NT=24,Tc=NT*ST2+3.5,u=((t%Tc)+Tc)%Tc,nt=Math.min(NT,1+Math.floor(u/ST2)),f=nt>=NT&&u>=NT*ST2?1:ease((u/ST2-(nt-1))/.55),
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
 R4.BAND.fsGibbs=1;

 /* FS4 short in time, wide in frequency. A train of pulses built from 30 harmonics with a bell-shaped spectrum, a_n = exp(-n^2 / 2 s^2). Narrow the spectrum and the
    pulse spreads out; widen it and the pulse sharpens to a click. The two widths (amber) always multiply to the same number: dt * df = 1 / (2 pi), the uncertainty
    relation of every sound. s breathes between 1.6 and 11 harmonics over 18 s. */
 R4.FN.fsUnc=function(c,w,h,t,P,d){var cx=w/2,cy=h*.345,k=K(w),E=d.ext||w*.5,wide=E>w*.6,NH=30,Pp=196,A=64,sg=Math.exp(Math.log(1.6)+(Math.log(11)-Math.log(1.6))*(.5-.5*Math.cos(TAU*t/18))),
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
 R4.BAND.fsUnc=.95;
})(R4);
