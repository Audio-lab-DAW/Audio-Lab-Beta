/* --- v0.225 (task AB1): the About window. Earth with its radiation belts behind the text, drawn in code from the pick page of task SR7 (docs/about-round-2.md): one of two pictures at random each time About opens, "corner" (E2: large Earth low right, soft belts) or "sheet" (E7: Earth on the left edge, contour lines). Every dot sits on a drawn dipole field line and bounces between its two mirror points with the real speed profile. On top: the fine atom (FATOM) as the logo and the same facts as before in a quiet spec list. One canvas for the picture (at most 30 pictures a second), one small one for the atom; both run only while About is open, stand still at the Light level and with "reduce motion", and are held by the background freeze (task AO) because their frames are asked for through window.requestAnimationFrame. Nothing here runs before About is opened for the first time. --- */
/* The fine atom: the AudioLab mark (three orbits at 90, 30 and 150 degrees, seen so that each circle shows as an ellipse 0.42 wide, a small nucleus, one warm electron) as many fine particles. Each particle runs on its own circle around the nucleus; its speed follows Kepler's rule (a little faster closer in), particles behind the nucleus are hidden and the far side is dimmer and smaller. One small piece on purpose, so the same atom can be used elsewhere:
   FATOM.paint(g,cx,cy,size,t,o)  draws it into any 2D context (g in CSS pixels, already scaled for the screen), centred on cx, cy, size across, at time t in seconds
   FATOM.canvas(cv,size,t,o)      sizes the canvas cv for the screen (device pixel ratio and page zoom, at most 3) and draws it
   o (optional): alpha 0..1, scale (canvas pixels per CSS pixel, to skip the measuring), haze false to leave out the faint outer particles */
const FATOM=(()=>{const TAU=Math.PI*2,CI=.42,SI=Math.sqrt(1-CI*CI),NB=6,PER=128,HAZE=80,NUC=52,RN=.135,T0=11;
  let M=null;
  function make(){let sd=20261127;const rnd=()=>{sd|=0;sd=sd+0x6D2B79F5|0;let t=Math.imul(sd^sd>>>15,1|sd);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296},gs=()=>(rnd()+rnd()+rnd()+rnd()-2)*1.732;
    const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],orb=[30,90,150].map((d,i)=>{const f=d*Math.PI/180,u=[Math.cos(f),Math.sin(f),0],v=[-Math.sin(f)*CI,Math.cos(f)*CI,(i===1?-1:1)*SI];return{u,v,n:cross(u,v)}});
    /* a particle: two unit vectors a, b that span its own circle, start angle, turns per second (as an angle), radius, group (0 dot, 1 accent dot, 2 haze) */
    const P=[],add=(a,b,rho,grp)=>P.push(a[0],a[1],a[2],b[0],b[1],b[2],rnd()*TAU,TAU/T0*Math.pow(rho,-1.5),rho,grp);
    for(const o of orb)for(let i=0;i<PER;i++){const ps=rnd()*TAU,de=gs()*.032,c=Math.cos(ps),s=Math.sin(ps),cd=Math.cos(de),sdl=Math.sin(de),a=[0,1,2].map(j=>o.u[j]*c+o.v[j]*s),b=[0,1,2].map(j=>(-o.u[j]*s+o.v[j]*c)*cd+o.n[j]*sdl);add(a,b,1+gs()*.028,rnd()<.3?1:0)}
    for(let i=0;i<HAZE;i++){const z=rnd()*2-1,f=rnd()*TAU,q=Math.sqrt(1-z*z),a=[q*Math.cos(f),q*Math.sin(f),z],r0=Math.abs(a[2])<.9?[0,0,1]:[1,0,0];let b=cross(a,r0);const h=Math.hypot(b[0],b[1],b[2]);b=b.map(v=>v/h);add(a,b,.46+.5*Math.sqrt(rnd()),2)}
    /* the nucleus: a small tight ball of fine dots, half warm (protons) and half pale (neutrons) */
    const N=[];for(let i=0;i<NUC;i++){const z=rnd()*2-1,f=rnd()*TAU,q=Math.sqrt(1-z*z),k=.92*Math.cbrt(rnd());N.push([q*Math.cos(f)*k,q*Math.sin(f)*k,z*k,i%2])}
    return{orb,P:new Float32Array(P),n:P.length/10,N,el:[[0,.4,1],[1,2.9,0],[2,5.1,0]],B:Array.from({length:NB*3},()=>[]),NB:[[],[],[],[]]}}
  function paint(g,cx,cy,size,t,o){o=o||{};M=M||make();const R=size*.42,k=Math.max(.8,Math.min(1.7,size/116)),al=o.alpha==null?1:o.alpha,rn=R*RN;
    /* the whole atom sways a few degrees so the depth can be seen; the mark stays recognisable */
    const ya=.15*Math.sin(t*TAU/26),xa=.075*Math.sin(t*TAU/19+1),ca=Math.cos(ya),sa=Math.sin(ya),cb=Math.cos(xa),sb=Math.sin(xa);
    let X=0,Y=0,Z=0;const rot=(x,y,z)=>{const x1=x*ca+z*sa,z1=-x*sa+z*ca;X=x1;Y=y*cb-z1*sb;Z=y*sb+z1*cb};
    g.save();g.lineCap='round';g.lineJoin='round';
    const ring=front=>{g.lineWidth=.6*k;g.strokeStyle='rgba(122,170,255,'+((front?.3:.14)*al).toFixed(3)+')';g.beginPath();
      for(const q of M.orb){let pen=false;for(let j=0;j<=72;j++){const th=j/72*TAU,c=Math.cos(th),s=Math.sin(th);rot(q.u[0]*c+q.v[0]*s,q.u[1]*c+q.v[1]*s,q.u[2]*c+q.v[2]*s);const sx=cx+R*X,sy=cy-R*Y;if((Z>=0)===front){pen?g.lineTo(sx,sy):g.moveTo(sx,sy);pen=true}else{if(pen)g.lineTo(sx,sy);pen=false}}}g.stroke()};
    /* particles into depth buckets: 6 depths x (dot, accent, haze) behind and in front are filled as a few paths */
    const B=M.B;for(const b of B)b.length=0;const P=M.P;
    for(let i=0,p=0;i<M.n;i++,p+=10){const grp=P[p+9];if(grp===2&&o.haze===false)continue;const th=P[p+6]+t*P[p+7],c=Math.cos(th),s=Math.sin(th),r=P[p+8];rot((P[p]*c+P[p+3]*s)*r,(P[p+1]*c+P[p+4]*s)*r,(P[p+2]*c+P[p+5]*s)*r);
      if(Z<0&&X*X+Y*Y<RN*RN*1.1)continue;const d=Math.min(NB-1,Math.max(0,((Z+1.05)/2.1*NB)|0));B[grp*NB+d].push(cx+R*X,cy-R*Y)}
    const dots=front=>{for(let grp=0;grp<3;grp++)for(let d=front?NB/2:0;d<(front?NB:NB/2);d++){const a=B[grp*NB+d];if(!a.length)continue;const dd=(d+.5)/NB,rad=(grp===2?.28+.14*dd:.36+.26*dd)*k;
        g.fillStyle='rgba('+(grp===1?'110,208,238':grp===2?'150,190,255':'198,232,255')+','+((grp===2?.14+.3*dd:.24+.7*dd)*al).toFixed(3)+')';g.beginPath();for(let i=0;i<a.length;i+=2){g.moveTo(a[i]+rad,a[i+1]);g.arc(a[i],a[i+1],rad,0,TAU)}g.fill()}};
    /* the three electrons: one warm (as in the mark), two pale; each with a short fine tail along its orbit */
    const elec=front=>{for(const[oi,ph,warm]of M.el){const q=M.orb[oi],th=ph+t*TAU/T0,c=Math.cos(th),s=Math.sin(th);rot(q.u[0]*c+q.v[0]*s,q.u[1]*c+q.v[1]*s,q.u[2]*c+q.v[2]*s);if((Z>=0)!==front||(Z<0&&X*X+Y*Y<RN*RN*1.2))continue;
        const dd=(Z+1)/2,ex=cx+R*X,ey=cy-R*Y,col=warm?'240,168,120':'226,242,255';g.beginPath();g.moveTo(ex,ey);for(let j=1;j<=8;j++){const t2=th-j*.055,c2=Math.cos(t2),s2=Math.sin(t2);rot(q.u[0]*c2+q.v[0]*s2,q.u[1]*c2+q.v[1]*s2,q.u[2]*c2+q.v[2]*s2);g.lineTo(cx+R*X,cy-R*Y)}
        g.lineWidth=.8*k;g.strokeStyle='rgba('+col+','+((.16+.3*dd)*al).toFixed(3)+')';g.stroke();g.fillStyle='rgba('+col+','+((.5+.5*dd)*al).toFixed(3)+')';g.beginPath();g.arc(ex,ey,(.95+.45*dd)*k,0,TAU);g.fill()}};
    ring(false);dots(false);elec(false);
    /* nucleus: it hides what is behind it, a faint glow around it, then its dots, the far ones first and dimmer */
    g.fillStyle='rgba(6,10,18,'+(.9*al).toFixed(3)+')';g.beginPath();g.arc(cx,cy,rn,0,TAU);g.fill();
    const hg=g.createRadialGradient(cx,cy,0,cx,cy,R*.36);hg.addColorStop(0,'rgba(110,208,238,'+(.13*al).toFixed(3)+')');hg.addColorStop(1,'rgba(110,208,238,0)');g.fillStyle=hg;g.beginPath();g.arc(cx,cy,R*.36,0,TAU);g.fill();
    const na=t*.23,cn=Math.cos(na),sn=Math.sin(na),Q=M.NB;for(const a of Q)a.length=0;for(const m of M.N){rot(m[0]*cn+m[2]*sn,m[1],-m[0]*sn+m[2]*cn);Q[(Z<0?0:2)+m[3]].push(cx+rn*X,cy-rn*Y)}
    for(let i=0;i<4;i++){const a=Q[i],fr=i>1,rad=(fr?.62:.5)*k;g.fillStyle='rgba('+(i&1?'240,168,120':'176,206,248')+','+((fr?.95:.5)*al).toFixed(3)+')';g.beginPath();for(let j=0;j<a.length;j+=2){g.moveTo(a[j]+rad,a[j+1]);g.arc(a[j],a[j+1],rad,0,TAU)}g.fill()}
    ring(true);dots(true);elec(true);g.restore()}
  function canvas(cv,size,t,o){o=o||{};let sc=o.scale;if(!(sc>0)){const cw=cv.clientWidth,z=cw?cv.getBoundingClientRect().width/cw:1;sc=Math.min(3,(window.devicePixelRatio||1)*(z>.3&&z<4?z:1))}
    const px=Math.max(1,Math.round(size*sc));if(cv.width!==px||cv.height!==px){cv.width=px;cv.height=px}const g=cv.getContext('2d');g.setTransform(px/size,0,0,px/size,0,0);g.clearRect(0,0,size,size);paint(g,size/2,size/2,size,t,o);return sc}
  return{paint,canvas,count:()=>{M=M||make();return M.n+3+M.N.length}}})();
const AB1=(()=>{const TAU=Math.PI*2,D=Math.PI/180,ATOM=116,KINDS=['corner','sheet'];
  /* where the Earth sits in a 780 x 720 window (it follows the real window), its size, the lean of its axis on screen (roll), how far we look from above (elev), and the belt style */
  const KIND={corner:{R:140,elev:22,roll:26,lon:-20,b:'glow',pos:(w,h,k)=>[w-66*k,h-74*k]},sheet:{R:104,elev:9,roll:-12,lon:60,b:'fine',pos:(w,h)=>[-6,h*.425]}};
  /* the Earth as picked (S3, drafted): heavier outline, graticule every 15 degrees, coastlines, the night side shaded, axis ticks */
  const SE={out:.8,ow:1.2,grat:15,ga:.13,coast:.6,cw:.9};
  const COL={p:'232,160,126',e:'104,200,236',n:'122,164,238',pd:'255,208,176',ed:'190,236,255',nd:'200,214,240',earth:'166,198,255'};
  const POLE={lat:80.8,lon:-72.8};/* geomagnetic north pole, NOAA NCEI WMM2025; the dipole axis leans 9.2 degrees */
  const BELT={inner:[1.2,3],outer:[4,7]};/* Earth radii from the centre, NASA */
  /* belts. Each shell: L (Earth radii at the equator), lines around the Earth, kind (p inner belt, e outer belt, n neither), dots per line */
  const BS={glow:{glow:1,lw:.8,la:.46,dot:1.35,sh:[[1.5,6,'p',3],[2.1,6,'p',2],[2.7,6,'p',1],[3.5,6,'n',0],[4.4,8,'e',2],[5.2,8,'e',2],[6,8,'e',2],[6.8,8,'e',1],[9,8,'n',0]]},
    fine:{glow:0,lw:.6,la:.46,dot:1.2,sh:[[1.3,4,'p',2],[1.6,4,'p',3],[1.9,4,'p',2],[2.2,4,'p',2],[2.5,4,'p',1],[2.8,4,'p',1],[3.5,4,'n',0],[4,4,'e',2],[4.5,4,'e',3],[5,4,'e',3],[5.5,4,'e',2],[6,4,'e',2],[6.5,4,'e',1],[7,4,'e',1],[8.5,4,'n',0]]}};
  /* the six features shown, in the short wording of the pick page (the full list keeps the app's own wording, AHF) */
  const SHORT={pool:'32 voices a track, up to 14 oscillators',block:'moved 293 samples: difference 0',swap:'old sound gone in 13 to 19 ms',freeze:'audio thread 59 % to 7 %',stems:'4 or 6 stems, offline',ai:'held notes within about 4 cents'};
  const n={bg:0,atom:0,open:0,corner:0,sheet:0};let G=null,S=null,force=null;
  const rng=s=>()=>{s|=0;s=s+0x6D2B79F5|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296};
  const sm=(x,a,b)=>{const u=clamp((x-a)/(b-a),0,1);return u*u*(3-2*u)},mul=(a,b)=>{const o=new Array(9);for(let i=0;i<3;i++)for(let j=0;j<3;j++)o[i*3+j]=a[i*3]*b[j]+a[i*3+1]*b[3+j]+a[i*3+2]*b[6+j];return o};
  /* everything that is worked out once, at the first opening: the bounce tables, the coastlines, the lines and the dots */
  function prep(){if(G)return G;
    const MB=(()=>{const m=[Math.cos(POLE.lat*D)*Math.cos(POLE.lon*D),Math.cos(POLE.lat*D)*Math.sin(POLE.lon*D),Math.sin(POLE.lat*D)];let e1=[-m[1],m[0],0];const h=Math.hypot(e1[0],e1[1]);e1=e1.map(v=>v/h);const e2=[m[1]*e1[2]-m[2]*e1[1],m[2]*e1[0]-m[0]*e1[2],m[0]*e1[1]-m[1]*e1[0]];return[e1,e2,m]})();
    /* bounce on a dipole line. Speed along the line is v*sqrt(1-B/Bm), B/Beq = sqrt(1+3sin^2)/cos^6, ds = L cos sqrt(1+3sin^2) dlat. Gives latitude / mirror latitude at 33 equal time steps of a quarter bounce (equator to mirror point) */
    const quarter=lm=>{const b=l=>Math.sqrt(1+3*Math.sin(l)**2)/Math.cos(l)**6,bm=b(lm),N=600,ts=new Float64Array(N+1),ls=new Float64Array(N+1);let t=0;
      for(let i=0;i<N;i++){const w=1-(i+.5)/N,l=lm*(1-w*w),dl=lm*2*w/N;t+=Math.cos(l)*Math.sqrt(1+3*Math.sin(l)**2)/Math.sqrt(Math.max(1e-9,1-b(l)/bm))*dl;const w1=1-(i+1)/N;ts[i+1]=t;ls[i+1]=1-w1*w1}
      const out=new Float32Array(33);let j=0;for(let k=0;k<=32;k++){const tt=t*k/32;while(j<N-1&&ts[j+1]<tt)j++;out[k]=ls[j]+(ls[j+1]-ls[j])*(tt-ts[j])/(ts[j+1]-ts[j]||1)}out[32]=1;return out};
    const MIR=[10,17,24,31,38,46].map(d=>{const lm=d*D,sa=Math.sqrt(Math.cos(lm)**6/Math.sqrt(1+3*Math.sin(lm)**2));return{lm,q:quarter(lm),f:(1.30-.56*sa)/.74}});/* f: bounce period factor, Hamlin 1961 */
    /* coastlines: longitude, latitude pairs, drawn as strokes */
    const LAND=[
 [-168,66,-162,70,-141,70,-128,70,-110,68,-95,69,-82,68,-80,63,-94,59,-88,56,-80,52,-78,58,-70,62,-62,58,-56,52,-66,48,-60,46,-70,43,-74,40,-76,35,-81,31,-80,26,-83,29,-90,30,-97,27,-97,21,-91,19,-87,21,-88,16,-83,15,-83,10,-78,9,-80,7,-86,12,-94,16,-105,20,-110,24,-113,30,-117,33,-122,37,-124,43,-124,48,-131,54,-140,60,-152,59,-158,57,-164,60,-168,66],
 [-78,9,-72,12,-62,11,-52,5,-50,0,-37,-5,-35,-9,-39,-17,-42,-23,-48,-27,-53,-34,-58,-38,-65,-42,-66,-47,-69,-52,-72,-53,-75,-47,-73,-38,-71,-30,-70,-19,-76,-14,-81,-6,-80,-1,-77,4,-78,9],
 [-17,15,-16,22,-10,29,-6,36,3,37,10,37,11,33,20,31,25,32,32,31,35,25,37,19,43,12,51,12,48,5,41,-2,39,-9,40,-16,35,-24,32,-29,27,-34,19,-35,17,-29,13,-20,12,-8,9,-1,9,4,4,6,-4,5,-8,4,-13,8,-17,15],
 [-9,37,-9,43,-2,44,-4,48,2,51,8,54,9,57,12,56,11,59,5,59,6,62,14,68,25,71,30,70,41,67,44,66,40,64,45,68,60,69,68,69,73,72,81,74,100,77,112,74,130,71,141,73,160,70,170,69,179,66,178,62,170,60,163,58,162,55,156,51,157,57,152,59,143,59,137,54,141,52,140,48,133,43,130,42,128,39,126,35,122,39,118,39,122,37,120,34,122,30,119,25,114,22,108,21,106,18,109,12,105,9,101,13,100,8,103,2,100,5,98,9,97,16,92,22,87,21,80,15,80,10,77,8,73,17,72,21,67,25,58,25,56,27,50,30,48,30,52,24,56,24,59,22,55,17,45,13,43,13,39,21,35,28,33,31,36,36,30,36,27,37,26,40,23,38,22,37,20,40,19,42,14,45,12,44,16,41,18,40,16,38,12,42,9,44,3,43,0,39,-2,37,-5,36,-9,37],
 [-5,50,1,51,0,53,-2,56,-3,58,-6,57,-3,54,-5,52,-5,50],
 [130,32,135,34,140,35,141,39,142,43,145,44,141,45,140,41,137,37,132,35,130,32],
 [-45,60,-52,65,-54,70,-60,76,-68,77,-60,82,-35,83,-20,81,-20,75,-25,70,-35,66,-42,62,-45,60],
 [114,-22,114,-34,118,-35,124,-33,131,-31,136,-35,140,-38,146,-39,150,-37,153,-28,146,-19,142,-11,141,-17,136,-12,130,-12,125,-14,121,-19,114,-22],
 [0,-70,30,-69,60,-67,90,-66,120,-66,150,-68,170,-72,190,-78,210,-76,240,-74,260,-73,285,-72,298,-65,302,-70,320,-78,340,-74,360,-70],
 [44,-25,47,-25,50,-16,49,-12,44,-17,44,-25],[109,1,117,7,119,1,116,-4,110,-3,109,1],[95,5,104,-5,106,-6,103,0,98,4,95,5],[131,-1,141,-3,147,-6,150,-10,141,-9,138,-8,133,-4,131,-1]
].map(a=>{const p=[];for(let i=0;i+3<a.length;i+=2){const m=Math.max(1,Math.ceil(Math.max(Math.abs(a[i+2]-a[i]),Math.abs(a[i+3]-a[i+1]))/5));for(let k=0;k<m;k++){const lo=(a[i]+(a[i+2]-a[i])*k/m)*D,la=(a[i+1]+(a[i+3]-a[i+1])*k/m)*D;p.push(Math.cos(la)*Math.cos(lo),Math.cos(la)*Math.sin(lo),Math.sin(la))}}return new Float32Array(p)});
    for(const key in BS){const b=BS[key],r=rng(31);b.shells=b.sh.map(([L,nm,kind])=>{const ls=Math.acos(Math.sqrt(1/L)),m=L>3?80:40,rho=new Float32Array(m+1),zz=new Float32Array(m+1);
        for(let k=0;k<=m;k++){const la=-ls+2*ls*k/m,c2=Math.cos(la)**2;rho[k]=L*c2*Math.cos(la);zz[k]=L*c2*Math.sin(la)}return{L,nm,kind,rho,zz,ph0:r()*TAU}});
      b.parts=[];b.sh.forEach(([L,nm,kind,np],si)=>{const lmax=Math.acos(Math.sqrt(1.08/L));for(let j=0;j<nm;j++)for(let q=0;q<np;q++){const ok=MIR.filter(m=>m.lm<lmax),m=ok[Math.min(ok.length-1,(r()*r()*ok.length*1.6)|0)];
          b.parts.push({si,j,m,L,kind,ph:r(),T:(kind==='e'?1.5:4.4)*L*m.f*(.85+.3*r())})}});
      if(b.glow){r();b.parts.push({si:b.sh.findIndex(s=>s[2]==='n'),j:2,m:MIR[2],L:3.5,kind:'n',ph:.3,T:9})}}
    return G={MB,MIR,LAND}}
  const latAt=(m,u)=>{u-=Math.floor(u);const s=u<.25?4*u:u<.5?4*(.5-u):u<.75?4*(u-.5):4*(1-u),x=s*32,i=Math.min(31,x|0),v=m.q[i]+(m.q[i+1]-m.q[i])*(x-i);return(u<.5?1:-1)*v*m.lm};
  function viewMatrix(p,spin){const e=p.elev*D,r=p.roll*D,ce=Math.cos(e),se=Math.sin(e),cr=Math.cos(r),sr=Math.sin(r),ct=Math.cos(spin),st=Math.sin(spin);
    return mul([cr,-sr,0,sr,cr,0,0,0,1],mul([1,0,0,0,ce,-se,0,se,ce],mul([0,1,0,0,0,1,1,0,0],[ct,-st,0,st,ct,0,0,0,1])))}
  /* how strongly the dark veil covers a point: the text column, the name, and a soft round patch behind the atom. M is measured from the page (fit) */
  function mask(M,x,y){const c=M.c,a=M.n,t=M.a;let v=sm(x,c[0]-46,c[0]-6)*sm(x,c[2]+46,c[2]+6)*sm(y,c[1]-44,c[1]-6)*sm(y,c[3]+42,c[3]+4);
    if(!M.exp){v=Math.max(v,sm(x,a[0]-110,a[0]-34)*sm(x,a[2]+110,a[2]+34)*sm(y,a[1]-58,a[1]-2)*sm(y,a[3]+40,a[3]+4));const d=Math.hypot(x-t[0],y-t[1]);v=Math.max(v,.8*sm(d,t[2]*1.25,t[2]*.55))}return v}
  /* one picture. c is in window pixels (w x h), t in seconds */
  function scene(c,w,h,t,kind,M){const g=prep(),p=KIND[kind],b=BS[p.b],k=clamp(Math.min(w/780,h/720),.7,1.1),R=p.R*k,[cx,cy]=p.pos(w,h,k);
    const gr=c.createRadialGradient(w/2,h*.417,0,w/2,h*.417,560*Math.max(w/780,h/720));gr.addColorStop(0,'#0b1322');gr.addColorStop(.6,'#060910');gr.addColorStop(1,'#04060a');c.fillStyle=gr;c.fillRect(0,0,w,h);
    const spin=p.lon*D+t*TAU/240,V=viewMatrix(p,spin),MB=g.MB;/* the Earth turns eastward, once in 240 s here */
    const A=mul(V,[MB[0][0],MB[1][0],MB[2][0],MB[0][1],MB[1][1],MB[2][1],MB[0][2],MB[1][2],MB[2][2]]);/* magnetic frame to view */
    const drift=s=>s.kind==='e'?t*TAU*s.L/540:s.kind==='p'?-t*TAU*s.L/160:0;/* electrons eastward, protons westward, faster further out */
    /* belts as a glow: cross-sections of the two shells at 24 meridians, each very faint */
    if(b.glow){for(const[bl,col,a,lam]of[[BELT.inner,COL.p,.03,34],[BELT.outer,COL.e,.022,40]]){c.fillStyle='rgba('+col+','+a+')';for(let j=0;j<24;j++){const ph=j*TAU/24,cp=Math.cos(ph),sp=Math.sin(ph);c.beginPath();
        for(let pass=0;pass<2;pass++){const L=bl[1-pass],lm=Math.min(lam*D,Math.acos(Math.sqrt(1/L)));for(let q=0;q<=14;q++){const la=(pass?1:-1)*(-lm+2*lm*q/14),c2=Math.cos(la)**2,rh=L*c2*Math.cos(la),z=L*c2*Math.sin(la),x=rh*cp,y=rh*sp;
            c.lineTo(cx+R*(A[0]*x+A[1]*y+A[2]*z),cy-R*(A[3]*x+A[4]*y+A[5]*z))}}c.closePath();c.fill()}}}
    /* field lines: the far half first, then the Earth, then the near half */
    const lines=pass=>{c.lineWidth=b.lw;for(const s of b.shells){const psi=s.ph0+drift(s),m=s.rho.length;c.beginPath();
        for(let j=0;j<s.nm;j++){const ph=psi+j*TAU/s.nm,cp=Math.cos(ph),sp=Math.sin(ph);let pb=-2,px=0,py=0;
          for(let q=0;q<m;q++){const x=s.rho[q]*cp,y=s.rho[q]*sp,z=s.zz[q],X=A[0]*x+A[1]*y+A[2]*z,Y=A[3]*x+A[4]*y+A[5]*z,Z=A[6]*x+A[7]*y+A[8]*z,bk=Z<0&&X*X+Y*Y<1?-1:Z<0?0:1,sx=cx+R*X,sy=cy-R*Y;
            if(bk===pass){if(pb===pass)c.lineTo(sx,sy);else if(pb>=0){c.moveTo(px,py);c.lineTo(sx,sy)}else c.moveTo(sx,sy)}else if(pb===pass&&bk>=0)c.lineTo(sx,sy);
            pb=bk;px=sx;py=sy}}
        c.strokeStyle='rgba('+COL[s.kind]+','+b.la*(s.kind==='n'?.6:1)*(pass?1:.5)+')';c.stroke()}};
    lines(0);earth(c,V,cx,cy,R,g.LAND);lines(1);
    /* trapped particles: on the lines, bouncing between their mirror points; the short tail is where the dot was a moment before */
    const buf={p0:[],p1:[],e0:[],e1:[],n0:[],n1:[],p0c:[],p1c:[],e0c:[],e1c:[],n0c:[],n1c:[]};
    for(const q of b.parts){const s=b.shells[q.si],ph=s.ph0+drift(s)+q.j*TAU/s.nm,cp=Math.cos(ph),sp=Math.sin(ph),u=q.ph+t/q.T;
      let hid=0;const pts=[];for(const du of[0,.012]){const la=latAt(q.m,u-du),c2=Math.cos(la)**2,rh=q.L*c2*Math.cos(la),z=q.L*c2*Math.sin(la),x=rh*cp,y=rh*sp,X=A[0]*x+A[1]*y+A[2]*z,Y=A[3]*x+A[4]*y+A[5]*z,Z=A[6]*x+A[7]*y+A[8]*z;
        if(!du){if(Z<0&&X*X+Y*Y<1){hid=1;break}pts.push(Z)}pts.push(cx+R*X,cy-R*Y)}
      if(hid)continue;const sx=pts[1],sy=pts[2];if(sx<-4||sx>w+4||sy<-4||sy>h+4)continue;buf[q.kind+(pts[0]<0?0:1)+(M&&mask(M,sx,sy)>.5?'c':'')].push(sx,sy,pts[3],pts[4])}
    c.lineCap='round';for(const key in buf){const a=buf[key],col=COL[key[0]+'d'],al=(key[1]==='1'?.9:.42)*(key[2]?.22:1);if(!a.length)continue;
      c.strokeStyle='rgba('+col+','+al*.5+')';c.lineWidth=b.dot*1.1;c.beginPath();for(let i=0;i<a.length;i+=4){c.moveTo(a[i+2],a[i+3]);c.lineTo(a[i],a[i+1])}c.stroke();
      c.fillStyle='rgba('+col+','+al+')';c.beginPath();for(let i=0;i<a.length;i+=4){c.moveTo(a[i]+b.dot,a[i+1]);c.arc(a[i],a[i+1],b.dot,0,TAU)}c.fill()}
    c.lineCap='butt';if(M&&M.veil){c.imageSmoothingEnabled=true;c.drawImage(M.veil,0,0,w,h)}}
  function earth(c,V,cx,cy,R,LAND){const se=SE,pr=(x,y,z)=>[cx+R*(V[0]*x+V[1]*y+V[2]*z),cy-R*(V[3]*x+V[4]*y+V[5]*z),V[6]*x+V[7]*y+V[8]*z];
    c.beginPath();c.arc(cx,cy,R,0,TAU);c.fillStyle='rgba(6,10,18,.86)';c.fill();
    c.save();c.beginPath();c.arc(cx,cy,R,0,TAU);c.clip();
    const arc=(f,m)=>{let pen=0;for(let q=0;q<=m;q++){const v=f(q/m),o=pr(v[0],v[1],v[2]);if(o[2]>0){pen?c.lineTo(o[0],o[1]):c.moveTo(o[0],o[1]);pen=1}else pen=0}};
    c.beginPath();for(let lo=0;lo<360;lo+=se.grat)arc(u=>{const la=(-90+180*u)*D;return[Math.cos(la)*Math.cos(lo*D),Math.cos(la)*Math.sin(lo*D),Math.sin(la)]},30);
    for(let la=-90+se.grat;la<90;la+=se.grat)arc(u=>[Math.cos(la*D)*Math.cos(u*TAU),Math.cos(la*D)*Math.sin(u*TAU),Math.sin(la*D)],60);c.strokeStyle='rgba('+COL.earth+','+se.ga+')';c.lineWidth=.5;c.stroke();
    c.beginPath();for(const L of LAND){let pen=0;for(let i=0;i<L.length;i+=3){const o=pr(L[i],L[i+1],L[i+2]);if(o[2]>.02){pen?c.lineTo(o[0],o[1]):c.moveTo(o[0],o[1]);pen=1}else pen=0}}
    c.strokeStyle='rgba('+COL.earth+','+se.coast+')';c.lineWidth=se.cw;c.lineJoin='round';c.stroke();
    const ng=c.createLinearGradient(cx-R,cy-R*.4,cx+R,cy+R*.4);ng.addColorStop(0,'rgba(3,5,10,0)');ng.addColorStop(.5,'rgba(3,5,10,.1)');ng.addColorStop(.72,'rgba(3,5,10,.7)');ng.addColorStop(1,'rgba(3,5,10,.85)');c.fillStyle=ng;c.fillRect(cx-R,cy-R,2*R,2*R);
    c.restore();
    c.beginPath();c.arc(cx,cy,R,0,TAU);c.strokeStyle='rgba('+COL.earth+','+se.out+')';c.lineWidth=se.ow;c.stroke();
    const np=pr(0,0,1),ux=(np[0]-cx)/R,uy=(np[1]-cy)/R,hh=Math.hypot(ux,uy)||1;c.beginPath();for(const sg of[-1,1]){c.moveTo(cx+sg*ux/hh*(R+4),cy+sg*uy/hh*(R+4));c.lineTo(cx+sg*ux/hh*(R+16),cy+sg*uy/hh*(R+16))}c.strokeStyle='rgba('+COL.earth+',.6)';c.lineWidth=1;c.stroke()}
  /* which picture: one or the other, an even chance at every opening. Test hook: AB1.force('corner' or 'sheet'), or the same word in localStorage 'audiolab-about-test' */
  function pick(){let f=force;try{f=f||localStorage.getItem('audiolab-about-test')}catch(e){}return KINDS.includes(f)?f:KINDS[Math.random()<.5?0:1]}
  const still=()=>AT.reduce||document.body.classList.contains('lite');
  function html(){const sr=ctx?ctx.sampleRate:0,bl=ctx&&ctx.baseLatency?Math.round(ctx.baseLatency*sr):0,ua=navigator.userAgent,br=/Chrome\/(\d+)/.exec(ua),sf=/Version\/([\d.]+).*Safari/.exec(ua);
    const info=[['Version',VERSION],['Build',BUILD],['Audio engine','Web Audio · 32-bit float'],['Running at',(sr?(sr/1000)+' kHz':'not started')+(bl?' · '+bl+' samples':'')],['Instruments',Object.keys(PRESETS).length],['Effects',Object.keys(FXDEF).length],['Platform',(/Mac/.test(ua)?'macOS':'Desktop')+' · '+(br?'Chrome '+br[1]:sf?'Safari '+sf[1]:'Browser')],['CPU cores',navigator.hardwareConcurrency||'?']];
    const all=AHF.reduce((m,x)=>m+x[2].length,0),hl=AHF.flatMap(x=>x[2].filter(y=>y[4]));
    const grp=([name,,L])=>'<div class="abG"><div class="abGh">'+esc(name)+'<span>'+L.length+'</span></div>'+L.map(([k,nm,d,v])=>'<div class="abR"><span class="n">'+esc(nm)+'</span>'+(v?'<span class="v">'+esc(v)+'</span>':'')+'<span class="d">'+esc(d)+'</span></div>').join('')+'</div>';
    return'<div class="abC"><canvas class="abAtom" role="img" aria-label="AudioLab logo"></canvas><div class="abW"><span class="wm"><span class="wmA">Audio</span><span class="wmL">Lab</span><span class="wmP">PRO</span></span></div>'
      +'<div class="abS">Digital audio workstation · Version '+VERSION+'</div><div class="abBy">Designed by<span>Ilja V. Jakovliev</span></div>'
      +'<div class="abI">'+info.map(([a,b])=>'<div><span>'+a+'</span><span class="v">'+esc(String(b))+'</span></div>').join('')+'</div><div class="abH">Under the hood</div>'
      +'<div class="abF">'+hl.map(([k,nm,d,v])=>'<div class="abT" title="'+esc(d)+'"><span class="n">'+esc(nm)+'</span><span class="v">'+esc(SHORT[k]||v)+'</span></div>').join('')+'</div>'
      +'<div class="abB"><button type="button" id="abMore" aria-expanded="false" aria-controls="abAll" data-n="'+all+'">All '+all+' features</button><button type="button" id="abUpd" title="'+(window.audiolabDesktop?'Looks for a newer AudioLab, shows what is new and installs it inside the app':'Shows which version this is. The web version is always current.')+'">Check for updates</button></div>'
      +'<div class="abAll" id="abAll" hidden>'+[[0,3,5],[1,2,4]].map(col=>'<div class="abCol">'+col.map(i=>grp(AHF[i])).join('')+'</div>').join('')+'<div class="abNote">Measured in AudioLab\'s own tests on a test computer. Your computer may give other numbers. AI voices need the desktop app.</div></div>'
      +'<div class="abCr">© 2026 Ilja V. Jakovliev. All rights reserved.</div></div>'}
  /* measure the window and the text, size the picture's canvas (at most 2 canvas pixels per point), build the veil once as a small picture */
  function fit(){const A=S;if(!A)return false;const el=A.el;el.style.setProperty('--abh',el.clientHeight+'px');const w=el.clientWidth,h=el.clientHeight;if(!w||!h)return false;
    const er=el.getBoundingClientRect(),z=er.width/(el.offsetWidth||w)||1,zz=z>.3&&z<4?z:1,sc=Math.min((window.devicePixelRatio||1)*zz,2),pw=Math.round(w*sc),ph=Math.round(h*sc);if(A.bg.width!==pw||A.bg.height!==ph){A.bg.width=pw;A.bg.height=ph}
    const br=A.bg.getBoundingClientRect(),rc=q=>{const e=el.querySelector(q),r=e.getBoundingClientRect();return[(r.left-br.left)/zz,(r.top-br.top)/zz,(r.right-br.left)/zz,(r.bottom-br.top)/zz]};
    const wm=rc('.abW .wm'),by=rc('.abBy'),inf=rc('.abI'),cr=rc('.abCr'),at=rc('.abAtom'),M={exp:A.exp,n:[wm[0],wm[1],wm[2],by[3]],a:[(at[0]+at[2])/2,(at[1]+at[3])/2,(at[2]-at[0])/2]};
    if(A.exp){const al=rc('#abAll');M.c=[al[0],-400,al[2],h+400]}else M.c=[inf[0],inf[1],inf[2],cr[3]];
    const vw=Math.ceil(w/4),vh=Math.ceil(h/4),v=A.veil||(A.veil=document.createElement('canvas'));v.width=vw;v.height=vh;const x=v.getContext('2d'),im=x.createImageData(vw,vh),dt=im.data;
    for(let j=0;j<vh;j++)for(let i=0;i<vw;i++){const q=(j*vw+i)*4;dt[q]=5;dt[q+1]=8;dt[q+2]=14;dt[q+3]=255*.86*mask(M,i*4+2,j*4+2)}x.putImageData(im,0,0);M.veil=v;
    A.M=M;A.w=w;A.h=h;A.sc=sc;A.asc=Math.min(3,(window.devicePixelRatio||1)*zz);return true}
  function drawBg(ts){const A=S;if(!A.w&&!fit())return;const c=A.c;c.setTransform(A.sc,0,0,A.sc,0,0);scene(c,A.w,A.h,A.st?47:(ts-A.t0)/1000+A.off,A.k,A.M);n.bg++}
  function drawAtom(ts){const A=S;if(!A.w)return;FATOM.canvas(A.at,ATOM,A.st?7.4:(ts-A.t0)/1000+A.off,{scale:A.asc});n.atom++}
  /* the picture at most 30 times a second, the atom at most 60; both from the one frame that the page asks for */
  function tick(ts){const A=S;if(!A||!A.on)return;A.raf=0;if(!A.el.isConnected||!SPL||SPL.el!==A.el){stop();return}if(A.st)return;
    if(ts-A.lastB>=32){A.lastB=ts;drawBg(ts)}if(ts-A.lastA>=15){A.lastA=ts;drawAtom(ts)}A.raf=window.requestAnimationFrame(tick)}
  /* (again) after opening, a new window size, the full list opening, or the Light level switching: one picture now, and the frames if it moves */
  function kick(refit){const A=S;if(!A||!A.on)return;const st=still();if(refit)A.w=0;if(!refit&&st===A.st&&(st||A.raf))return;A.st=st;const now=performance.now();A.lastB=A.lastA=now;drawBg(now);drawAtom(now);if(!st&&!A.raf)A.raf=window.requestAnimationFrame(tick)}
  function open(){if(SPL)return;prep();const k=pick(),el=document.createElement('div');el.id='splash';el.className='ab ab2';el.dataset.abp=k;el.setAttribute('role','dialog');el.setAttribute('aria-label','About AudioLab Pro');
    el.innerHTML='<canvas class="abBg" aria-hidden="true"></canvas>'+html()+'<button class="abx" aria-label="Close" title="Close (Esc)">✕</button>';document.body.appendChild(el);
    const t0=performance.now();SPL={el,t0};n.open++;n[k]++;
    const A=S={el,k,bg:el.querySelector('.abBg'),at:el.querySelector('.abAtom'),t0,off:Math.random()*240,lastB:-1e9,lastA:-1e9,raf:0,on:true,w:0,exp:false,st:null,veil:null,M:null};A.c=A.bg.getContext('2d');
    el.addEventListener('click',e=>{if(e.target===el||e.target.closest('.abx')){hideSplash();return}const b=e.target.closest('#abMore');if(!b)return;const a=el.querySelector('#abAll'),op=a.hidden;a.hidden=!op;A.exp=op;el.classList.toggle('exp',op);b.setAttribute('aria-expanded',String(op));b.textContent=op?'Show less':'All '+b.dataset.n+' features';
      kick(true);if(op)el.scrollTo({top:Math.max(0,el.querySelector('.abH').offsetTop-22),behavior:still()?'auto':'smooth'});else el.scrollTop=0});
    A.rs=()=>kick(true);window.addEventListener('resize',A.rs);try{A.mo=new MutationObserver(()=>kick(false));A.mo.observe(document.body,{attributes:true,attributeFilter:['class']})}catch(e){}
    kick(true);if(document.fonts&&document.fonts.ready)document.fonts.ready.then(()=>{if(S===A&&A.on)kick(true)})}
  function stop(){const A=S;if(!A)return;A.on=false;if(A.raf){try{window.cancelAnimationFrame(A.raf)}catch(e){}A.raf=0}window.removeEventListener('resize',A.rs);if(A.mo)A.mo.disconnect();S=null}
  return{open,stop,pick,KINDS,force:k=>{force=k||null},n,state:()=>S,kind:()=>S?S.k:null,running:()=>!!(S&&S.on&&S.raf),
    /* for tests: milliseconds per picture, drawn n times off screen at w x h and 2 canvas pixels per point */
    bench:(kind,w,h,m)=>{const cv=document.createElement('canvas');cv.width=w*2;cv.height=h*2;const x=cv.getContext('2d');x.scale(2,2);for(let i=0;i<10;i++)scene(x,w,h,i,kind,null);const a=performance.now();for(let i=0;i<m;i++)scene(x,w,h,10+i/30,kind,null);return(performance.now()-a)/m},
    benchAtom:m=>{const cv=document.createElement('canvas');for(let i=0;i<10;i++)FATOM.canvas(cv,ATOM,i,{scale:2});const a=performance.now();for(let i=0;i<m;i++)FATOM.canvas(cv,ATOM,10+i/60,{scale:2});return(performance.now()-a)/m}}})();
/* About opens the new window; the loading splash and its preview are untouched. Closing stops the drawing at once */
{const _ss=showSplash;showSplash=function(about){if(about!==true)return _ss.apply(this,arguments);return AB1.open()}}
{const _hs=hideSplash;hideSplash=function(){const a=AB1.state(),r=_hs.apply(this,arguments);if(a&&(!SPL||SPL.el!==a.el))AB1.stop();return r}}
