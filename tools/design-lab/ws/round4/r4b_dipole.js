/* ===== The dipole (S1) with the F1 field flow kept exactly as built in WS-1: out of the north half, along the line, in at the south, up through the ball
   (Jupiter). Field lines r = L sin^2(theta); |B| ~ sqrt(1 + 3 cos^2 theta) / r^3; speed V (B/2)^0.2; the ball a uniformly magnetised sphere (straight chords inside).
   Only what a particle looks like changes: the four readings the user picked (P2 density, P3 energy, P4 radiation belt, P5 aurora), which the start screen
   treats as four drawings of its random set. R4.cnt (0, 1, 2) is the particle count; 1 is the build's. ===== */
(function(R4){var U=R4.U,PI=Math.PI,TAU=PI*2,K=U.K,dot=U.dot,lab=U.lab,rgba=U.rgba,mix=U.mix,hash=U.hash;
 var Ls=[.2,.3,.44,.62,.86,1.2,1.7,2.4],GAP=[2.3,1.55,1.05];
 R4.PAL.dip={g:'#0e1a34',bg:'#06080f',e:'#040508',ink:'#eaf0ff',a:'#6096ff',b:'#9fc2ff',d:'#ffc43c',p:'#b9d0ff',m:'#8190b2',n:'#75829f',L:'96,150,255',T:'96,150,255',O:'255,196,60',A:'120,255,214'};
 /* the frame: field lines, the chords through the ball, the ball. sub: more lines drawn faintly (P2). Leaves the context rotated; end() restores it */
 function frame(c,w,h,t,P,sub){var R=w*.5,rp=R*.058,i,j,sg,th,s,r;c.save();c.translate(w/2,h*.345);c.rotate(.17+Math.sin(t*.15)*.03);c.lineWidth=1;
  if(sub){c.strokeStyle='rgba('+P.L+',.085)';c.beginPath();for(i=0;i<sub.length;i++){var L0=sub[i],a0=Math.asin(Math.sqrt(rp/L0)),s0=PI-2*a0;for(sg=-1;sg<=1;sg+=2)for(j=0;j<=30;j++){th=a0+s0*j/30;s=Math.sin(th);r=L0*s*s;j?c.lineTo(sg*r*s,-r*Math.cos(th)):c.moveTo(sg*r*s,-r*Math.cos(th))}}c.stroke()}
  for(i=0;i<8;i++){var L=Ls[i]*R,t0=Math.asin(Math.sqrt(rp/L)),sp=PI-2*t0;c.strokeStyle='rgba('+P.L+',.22)';c.beginPath();for(sg=-1;sg<=1;sg+=2)for(j=0;j<=40;j++){th=t0+sp*j/40;s=Math.sin(th);r=L*s*s;j?c.lineTo(sg*r*s,-r*Math.cos(th)):c.moveTo(sg*r*s,-r*Math.cos(th))}c.stroke()}
  c.strokeStyle='rgba('+P.L+',.12)';c.beginPath();for(i=0;i<8;i++){var x=rp*Math.sqrt(rp/(Ls[i]*R)),y=rp*Math.sqrt(1-rp/(Ls[i]*R));c.moveTo(x,-y);c.lineTo(x,y);c.moveTo(-x,-y);c.lineTo(-x,y)}c.stroke();
  c.strokeStyle='rgba('+P.L+',.2)';c.beginPath();for(i=-1;i<=1;i++){var yy=-rp*Math.sin(i*.55),hw=rp*Math.cos(i*.55);c.moveTo(-hw,yy);c.lineTo(hw,yy)}c.moveTo(0,-rp*1.5);c.lineTo(0,rp*1.5);c.stroke();
  c.strokeStyle='rgba('+P.L+',.55)';c.beginPath();c.arc(0,0,rp,0,TAU);c.stroke()}
 function end(c,w,h){c.restore();U.fadeName(c,w,h)}
 /* one line as a table (the F1 table of round 2): from the top of the ball out along the line to the bottom, then up through the ball; T = travel time */
 function mkLine(L,rp,k){var t0=Math.asin(Math.sqrt(rp/L)),N=260,X=[],Y=[],B=[],In=[],j;
  for(j=0;j<=N;j++){var th=t0+(PI-2*t0)*j/N,s=Math.sin(th),r=L*s*s,cth=Math.cos(th);X.push(r*s);Y.push(-r*cth);B.push(Math.sqrt(1+3*cth*cth)/Math.pow(r/rp,3));In.push(0)}
  var xi=rp*Math.sqrt(rp/L),yi=rp*Math.sqrt(1-rp/L);for(j=1;j<24;j++){X.push(xi);Y.push(yi-2*yi*j/24);B.push(2);In.push(1)}X.push(X[0]);Y.push(Y[0]);B.push(B[0]);In.push(1);
  var T=[0],tm=0,V=110*k;for(j=1;j<X.length;j++){var ds=Math.hypot(X[j]-X[j-1],Y[j]-Y[j-1]),bm=(B[j]+B[j-1])/2;tm+=ds/(V*Math.pow(bm/2,.2));T.push(tm)}
  return{X:X,Y:Y,B:B,In:In,T:T,tm:tm,N:N,L:L}}
 var O={x:0,y:0,i:0,f:0,inn:0};
 function at(tb,tau){var T=tb.T,lo=0,hi=T.length-1,m;while(hi-lo>1){m=(lo+hi)>>1;if(T[m]<tau)lo=m;else hi=m}var f=(tau-T[lo])/((T[hi]-T[lo])||1);O.x=tb.X[lo]+(tb.X[hi]-tb.X[lo])*f;O.y=tb.Y[lo]+(tb.Y[hi]-tb.Y[lo])*f;O.i=lo;O.f=f;O.inn=tb.In[lo]&&tb.In[hi];return O}
 function prep(d,w){if(d.w!==w){d.w=w;var R=w*.5,k=K(w);d.tb=Ls.map(function(l){return mkLine(l*R,R*.058,k)});d.x=null}return d.tb}
 function wrap(u,tm){return((u%tm)+tm)%tm}
 /* the F1 schedule: on each line dots evenly spaced in travel time, the two sides half a gap apart. fn(tb, line, side, j, table time, gap between dots) */
 function each(tbs,t,gap,fn){var dir=R4.dir,n0=0,i,j,sg;for(i=0;i<tbs.length;i++){var tb=tbs[i],n=Math.max(1,Math.floor(tb.tm/gap));n0+=2*n;for(sg=-1;sg<=1;sg+=2)for(j=0;j<n;j++){var tau=wrap(t+j*tb.tm/n+(sg>0?0:tb.tm/n/2),tb.tm);fn(tb,i,sg,j,dir<0?tb.tm-tau:tau,tb.tm/n)}}R4.np=n0;return n0}

 /* P2 field strength as density. Field lines are drawn so that their spacing shows the field's strength (Faraday's picture). Forty more lines, evenly spaced where they
    leave the ball, are drawn faintly, and every line carries the same flow: the dots crowd exactly where the lines crowd, that is, where the field is strong.
    A dot dims as it slows down far out (alpha as its speed), so the light per length of line is even and what is left is the crowding of the lines. */
 var GAP2=[3.7,2.5,1.65];
 R4.FN.dipP2=function(c,w,h,t,P,d){var k=K(w),R=w*.5,rp=R*.058,i;prep(d,w);if(!d.x){d.x=1;var ta=Math.asin(Math.sqrt(.058/2.4)),tb0=Math.asin(Math.sqrt(.058/.2)),M=40;d.sub=[];for(i=0;i<M;i++){var th=ta+(tb0-ta)*(i+.5)/M,s=Math.sin(th);d.sub.push(rp/(s*s))}d.st=d.sub.map(function(L){return mkLine(L,rp,k)})}
  frame(c,w,h,t,P,d.sub);var gap=GAP2[R4.cnt],dir=R4.dir,n0=0,j,sg,pi=new Path2D(),po=[new Path2D(),new Path2D(),new Path2D(),new Path2D()],ro=.9*k,ri=.6*k;
  for(i=0;i<d.st.length;i++){var tb=d.st[i],n=Math.max(1,Math.round(tb.tm/gap));n0+=2*n;for(sg=-1;sg<=1;sg+=2)for(j=0;j<n;j++){var tau=wrap(t+(j+hash(i*7+sg))*tb.tm/n,tb.tm),p=at(tb,dir<0?tb.tm-tau:tau),x=sg*p.x;if(p.inn){pi.moveTo(x+ri,p.y);pi.arc(x,p.y,ri,0,TAU)}else{var v=Math.pow(tb.B[p.i]/2,.2),b=po[v>.62?3:v>.36?2:v>.2?1:0];b.moveTo(x+ro,p.y);b.arc(x,p.y,ro,0,TAU)}}}
  c.fillStyle='rgba('+P.O+',.3)';c.fill(pi);[.45,.62,.8,.95].forEach(function(a,q){c.fillStyle='rgba('+P.O+','+a+')';c.fill(po[q])});d.np=R4.np=n0;end(c,w,h)};

 /* P3 energy. Belt particles come with a steep spectrum of energies: many slow ones, few fast ones. Size, brightness and colour show a particle's energy
    (cool and small to hot and large, the hottest with a ring). Above about 1 MeV electrons all move at nearly the speed of light, so they keep the same pace. */
 R4.FN.dipP3=function(c,w,h,t,P,d){var k=K(w),tbs=prep(d,w),B=[new Path2D(),new Path2D(),new Path2D(),new Path2D()],pi=new Path2D(),pr=new Path2D();frame(c,w,h,t,P);
  d.np=each(tbs,t,GAP[R4.cnt],function(tb,i,sg,j,tau){var p=at(tb,tau),x=sg*p.x,e=Math.pow(hash(i*31+j*7+sg*3),2.3),r=(.62+1.35*e)*k,b=e<.12?0:e<.34?1:e<.62?2:3;
   if(p.inn){pi.moveTo(x+r*.7,p.y);pi.arc(x,p.y,r*.7,0,TAU);return}B[b].moveTo(x+r,p.y);B[b].arc(x,p.y,r,0,TAU);if(b===3){pr.moveTo(x+r+2.4*k,p.y);pr.arc(x,p.y,r+2.4*k,0,TAU)}});
  var C=[rgba(mix(P.T,P.O,.25),.7),rgba(mix(P.T,P.O,.7),.82),rgba(P.O,.92),rgba(P.O,1)],n;c.fillStyle='rgba('+P.O+',.28)';c.fill(pi);for(n=0;n<4;n++){c.fillStyle=C[n];c.fill(B[n])}c.strokeStyle='rgba('+P.O+',.38)';c.lineWidth=1;c.stroke(pr);
  end(c,w,h);var lx=w*.5+w*.37,ly=h*.345-66*k;lab(c,w,'ENERGY',lx-44*k,ly,'right','rgba('+P.L+',.75)');for(n=0;n<4;n++)dot(c,lx-34*k+n*11*k,ly,(.7+.5*n)*k,C[n]);c.strokeStyle='rgba('+P.O+',.38)';c.beginPath();c.arc(lx-34*k+33*k,ly,4.6*k,0,TAU);c.stroke()};

 /* P4 radiation belt. The flow stays; added are the particles that do not reach the ball: charges trapped on the inner lines, each circling its line and bouncing
    between two mirror points set by its pitch angle at the equator (B_mirror = B_eq / sin^2 alpha). Together they fill a belt, as at Jupiter and in Earth's Van Allen belts. */
 function rat(th){var s=Math.sin(th),c2=Math.cos(th);return Math.sqrt(1+3*c2*c2)/Math.pow(s,6)}
 var NT=[34,60,96];
 R4.FN.dipP4=function(c,w,h,t,P,d){var k=K(w),R=w*.5,tbs=prep(d,w),i,j,q,sg;if(!d.x){d.x=1;d.tr=[];for(i=0;i<NT[2];i++){var al=(36+44*hash(i*5+1))*PI/180,bm=1/(Math.sin(al)*Math.sin(al)),lo=.05,hi=PI/2;for(j=0;j<40;j++){var m=(lo+hi)/2;if(rat(m)>bm)lo=m;else hi=m}
    var Lr=.2+.33*hash(i*11+3);d.tr.push({L:Lr*R,lm:PI/2-hi,om:1.9/(.35+Lr*1.6),ph:hash(i*3+7)*TAU,sg:i%2?1:-1,rho:(1.1+5.5*(Lr-.2))*k,wg:15/(.6+Lr*3),g0:hash(i*13)*TAU})}}
  frame(c,w,h,t,P);var La=.2*R,Lb=.535*R,rp=R*.058;c.fillStyle='rgba('+P.T+',.055)';
  for(sg=-1;sg<=1;sg+=2){c.beginPath();for(q=0;q<2;q++){var L=q?La:Lb,a0=Math.asin(Math.sqrt(rp/L)),th;for(j=0;j<=30;j++){th=q?PI-a0-(PI-2*a0)*j/30:a0+(PI-2*a0)*j/30;var s=Math.sin(th),r=L*s*s;(j||q)?c.lineTo(sg*r*s,-r*Math.cos(th)):c.moveTo(sg*r*s,-r*Math.cos(th))}}c.closePath();c.fill()}
  d.np=each(tbs,t,GAP[R4.cnt],function(tb,i,sg,j,tau){var p=at(tb,tau);if(p.inn)dot(c,sg*p.x,p.y,.72*k,'rgba('+P.O+',.3)');else dot(c,sg*p.x,p.y,k,'rgba('+P.O+',.88)')});
  var n=NT[R4.cnt],pt=new Path2D(),pd=new Path2D(),rd=.95*k;for(i=0;i<n;i++){var o=d.tr[i],pen=0;for(q=5;q>=0;q--){var tt=t-q*.035,th2=PI/2+o.lm*Math.sin(o.om*tt+o.ph),s2=Math.sin(th2),c2=Math.cos(th2),r2=o.L*s2*s2,dr=2*o.L*s2*c2,tx=dr*s2+r2*c2,ty=-dr*c2+r2*s2,tl=Math.hypot(tx,ty)||1,
     off=o.rho*s2*s2*s2*Math.sin(o.wg*tt+o.g0),x=o.sg*(r2*s2-ty/tl*off),y=-r2*c2+tx/tl*off;pen?pt.lineTo(x,y):pt.moveTo(x,y);pen=1;if(!q){pd.moveTo(x+rd,y);pd.arc(x,y,rd,0,TAU)}}}
  c.lineWidth=k;c.strokeStyle='rgba('+P.T+',.5)';c.stroke(pt);c.fillStyle=rgba(mix(P.T,'255,255,255',P.A?.45:0),.95);c.fill(pd);c.lineWidth=1;d.np+=n;R4.np=d.np;end(c,w,h);
  lab(c,w,'RADIATION BELT',w*.5+w*.37,h*.345-66*k,'right','rgba('+P.T+',.8)')};

 /* P5 aurora. Where the lines meet the ball near its poles, the flow runs into the planet's upper air, which glows: the auroral ovals. Each dot is drawn as a streak
    (its path over the last 70 ms, so fast dots are long), and the foot of its line flashes as it passes through; the two ovals are seen edge-on as short bars. */
 R4.FN.dipP5=function(c,w,h,t,P,d){var k=K(w),R=w*.5,rp=R*.058,tbs=prep(d,w),dir=R4.dir,A=P.A||P.T,ps=new Path2D(),ph=new Path2D(),pi=new Path2D(),gap=GAP[R4.cnt],i,sg,j;frame(c,w,h,t,P);
  d.np=each(tbs,t,gap,function(tb,i,sg,j,tau){var p=at(tb,tau),x=sg*p.x,y=p.y;if(p.inn){pi.moveTo(x+.72*k,y);pi.arc(x,y,.72*k,0,TAU);return}ph.moveTo(x+.95*k,y);ph.arc(x,y,.95*k,0,TAU);
   var u=tau-dir*.07;if(u>0&&u<tb.T[tb.N]){p=at(tb,u);ps.moveTo(x,y);ps.lineTo(sg*p.x,p.y)}});
  c.lineCap='round';c.lineWidth=1.25*k;c.strokeStyle='rgba('+P.O+',.5)';c.stroke(ps);c.lineCap='butt';c.fillStyle='rgba('+P.O+',.3)';c.fill(pi);c.fillStyle='rgba('+P.O+',.95)';c.fill(ph);
  /* the feet: a ray up each line and a glow, flashing when a dot goes through (out at the north, in at the south) */
  for(i=0;i<8;i++){var tb=tbs[i],n=Math.max(1,Math.floor(tb.tm/gap)),per=tb.tm/n;for(sg=-1;sg<=1;sg+=2)for(j=0;j<2;j++){var age=wrap(t+(sg>0?0:per/2)+(dir<0?1:-1)*(j?tb.T[tb.N]:0),per),f=Math.exp(-age/.32),e=j?tb.N:0,stp=j?-1:1,x0=sg*tb.X[e],y0=tb.Y[e],q=e,len=0;
    c.strokeStyle=rgba(A,.16+.7*f);c.lineWidth=1.3*k;c.beginPath();c.moveTo(x0,y0);while(len<(5+7*f)*k&&q+stp>=0&&q+stp<=tb.N){q+=stp;len=Math.hypot(tb.X[q]-tb.X[e],tb.Y[q]-tb.Y[e]);c.lineTo(sg*tb.X[q],tb.Y[q])}c.stroke();
    dot(c,x0,y0,(2.2+2.6*f)*k,rgba(A,.07+.2*f));dot(c,x0,y0,1.1*k,rgba(A,.35+.6*f))}}
  c.lineWidth=1.2*k;c.strokeStyle=rgba(A,.55);c.beginPath();for(j=-1;j<=1;j+=2){[.2,.44].forEach(function(th){c.moveTo(-rp*Math.sin(th),j*rp*Math.cos(th));c.lineTo(rp*Math.sin(th),j*rp*Math.cos(th))})}c.stroke();c.lineWidth=1;
  end(c,w,h);lab(c,w,'AURORAL OVALS',w*.5+w*.37,h*.345-66*k,'right',rgba(A,.8))};
 R4.BAND.dipP2=R4.BAND.dipP3=R4.BAND.dipP4=R4.BAND.dipP5=1;
})(R4);
