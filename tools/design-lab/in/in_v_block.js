/* ===== lane E (task IN-V): the Visualizer, the user's pick V1 (one frequency axis) with the viridis colour map =====
   - The spectrogram and the spectrum share one frequency axis: the spectrum lies sideways beside the spectrogram, on the same log rows from
     20 Hz (bottom) to 20 kHz (top), with the axis between them (long marks at decades, mid at 2 and 5, numbers where they fit, HZ in amber), so
     a line in one is a peak in the other at the same height. In All the two old panes become this one module; Spectrogram shows it alone.
   - The spectrogram in the chosen colour map (viridis by default; magma, inferno, today's heat) with its colour bar in dBFS; levels in true
     dBFS (IN-S's calibration: a sine reads its peak level); below the range floor and while stopped, the background. The columns are kept as
     levels, so a new map or range repaints the history instead of clearing it.
   - The sideways spectrum: the same rows, tilt around 1 kHz, a line every range/3 dB with numbers, max hold falling 3 dB/s (none at the
     Light level), the settings in its top corner.
   - Spectrum (alone): IN-S's analyzer front panel (S2) with the menu's tilt and hold; its 10 dB/div stays.
   - Waveform: today's scrolling picture with an amplitude scale (0 and -6 dBFS) and a time scale bar (X11) measured from the real column rate.
   - Levels as M2: the RMS core in the bar with the peak part faint above it on the fader taper and its scale, the peak hold line, read-outs
     short-term LUFS, peak, RMS and crest with amber units.
   - The right-click menu (pvMenu) gets Colour map, Range (60, 90, 120 dB), Spectrum tilt (off, 3, 4.5 dB per octave), Max hold and Speed
     (slow, normal, fast), kept in UI.vzO.
   Draws only inside the Visualizer's own frame (vizFrame: screen rate, half at the Light level, nothing while hidden); no audio nodes. */
const INV={n:0,BG:[7,8,11],
  O(){const o=(typeof UI==='object'&&UI&&UI.vzO)||{};return{map:o.map||'viridis',range:o.range||90,tilt:o.tilt!=null?+o.tilt:4.5,hold:o.hold!==false,speed:o.speed||'normal'}},
  set(k,v){UI.vzO=Object.assign({},UI.vzO||{},{[k]:v});saveUI()},
  MAPS:[['viridis','Viridis'],['magma','Magma'],['inferno','Inferno'],['today','Today’s heat']],
  lut(k){return k==='today'&&typeof VZRGB!=='undefined'?VZRGB:INS.cmap(INS.cmapNames.includes(k)?k:'viridis')},
  _cb:{},
  cbar(g,x,y,w,h,k){let c=INV._cb[k];if(!c){c=INV._cb[k]=document.createElement('canvas');c.width=256;c.height=1;const q=c.getContext('2d'),im=q.createImageData(256,1),L=INV.lut(k);for(let i=0;i<256;i++){im.data[i*4]=L[i*3];im.data[i*4+1]=L[i*3+1];im.data[i*4+2]=L[i*3+2];im.data[i*4+3]=255}q.putImageData(im,0,0)}
    const sm=g.imageSmoothingEnabled;g.imageSmoothingEnabled=true;g.drawImage(c,x,y,w,h);g.imageSmoothingEnabled=sm},
  rows(H){/* per row (top = 20 kHz): the bin range (fractional) and log2 of the row's centre over 1 kHz, made once per size */
    const sr=ctx.sampleRate,n=VZ.f.length,k=H+'|'+n+'|'+sr;if(INV._rk===k)return INV._rb;const rb=new Float32Array(H*3);
    for(let y=0;y<H;y++){const f0=20*Math.pow(1000,1-(y+1)/H),f1=20*Math.pow(1000,1-y/H);rb[y*3]=Math.min(n-1.001,f0/(sr/2)*n);rb[y*3+1]=Math.min(n-1.001,f1/(sr/2)*n);rb[y*3+2]=Math.log2(Math.sqrt(f0*f1)/1000)}
    INV._rk=k;INV._rb=rb;return rb},
  colv(H){/* dBFS per row from this frame's analyser read (VZ.f, read once in vizFrame): a row narrower than a bin is read between the two nearest bins, a wider one takes its highest bin */
    const rb=INV.rows(H),B=VZ.f,v=INV._cv&&INV._cv.length===H?INV._cv:(INV._cv=new Float32Array(H)),cal=INS.SPCAL||0;
    for(let y=0;y<H;y++){const b0=rb[y*3],b1=rb[y*3+1];let d;if(b1-b0<1){const m=(b0+b1)/2,i=m|0,fr=m-i;d=B[i]*(1-fr)+B[i+1]*fr}else{d=-1e9;for(let i=Math.round(b0),e=Math.round(b1);i<=e;i++)if(B[i]>d)d=B[i]}v[y]=isFinite(d)?d+cal:-240}return v},
  /* the spectrogram: a ring of columns kept as levels (0 = no data, else -0.6 dB steps), painted with the map; two columns of a CSS pixel each */
  rgbOf(q,O,L){if(!q)return INV.BG;const db=-q*.6,v=(db+O.range)/O.range;if(v<=0)return INV.BG;const k=Math.min(255,Math.round(v*255))*3;return[L[k],L[k+1],L[k+2]]},
  repaint(S,O){const L=INV.lut(O.map),im=S.x.createImageData(S.W,S.H),d=im.data;for(let i=0;i<S.W*S.H;i++){const c=INV.rgbOf(S.q[i],O,L);d[i*4]=c[0];d[i*4+1]=c[1];d[i*4+2]=c[2];d[i*4+3]=255}S.x.putImageData(im,0,0)},
  sg(g,x,y,w,h,vals,O){const Wb=Math.max(2,Math.ceil(w/2)),Hb=vals?vals.length:Math.max(2,Math.round(h));let S=VZ.isg;
    if(!S||S.W!==Wb||S.H!==Hb){S=VZ.isg={W:Wb,H:Hb,c:document.createElement('canvas'),q:new Uint8Array(Wb*Hb),p:0,acc:0,k:''};S.c.width=Wb;S.c.height=Hb;S.x=S.c.getContext('2d');S.x.fillStyle='rgb('+INV.BG+')';S.x.fillRect(0,0,Wb,Hb);S.col=S.x.createImageData(1,Hb)}
    const key=O.map+'|'+O.range;if(S.k&&S.k!==key)INV.repaint(S,O);S.k=key;
    S.acc=Math.min(4,S.acc+(O.speed==='slow'?.5:O.speed==='fast'?2:1));const L=INV.lut(O.map),D=S.col.data;
    while(S.acc>=1){S.acc-=1;for(let r=0;r<Hb;r++){const q=vals?Math.max(1,Math.min(255,Math.round(-vals[r]/.6))):0;S.q[r*Wb+S.p]=q;const c=INV.rgbOf(q,O,L);D[r*4]=c[0];D[r*4+1]=c[1];D[r*4+2]=c[2];D[r*4+3]=255}S.x.putImageData(S.col,S.p,0);S.p=(S.p+1)%Wb;INV.n++}
    const p=S.p,sw=w/Wb,sm=g.imageSmoothingEnabled;g.imageSmoothingEnabled=false;if(Wb-p>0)g.drawImage(S.c,p,0,Wb-p,Hb,x,y,(Wb-p)*sw,h);if(p>0)g.drawImage(S.c,0,0,p,Hb,x+(Wb-p)*sw,y,p*sw,h);g.imageSmoothingEnabled=sm},
  /* the shared frequency axis, upright: f -> y */
  fy(f,y0,h){return y0+h-h*Math.log(f/20)/Math.log(1000)},
  fAxisV(g,x,y0,h,o={}){const L=INS.look(),lw=INS.hair(g,L.lwLine);g.lineWidth=lw;
    for(const lv of[0,1,2]){g.strokeStyle=lv?L.tick:L.tickHi;g.beginPath();for(let d=10;d<=10000;d*=10)for(let m=1;m<10;m++){const f=d*m;if(f<20||f>20000)continue;const k=m===1?0:m===2||m===5?1:2;if(k!==lv)continue;const yy=INS.px(g,INV.fy(f,y0,h)),tl=[5,3.5,2][k];g.moveTo(x,yy);g.lineTo(x+tl,yy)}g.stroke()}
    g.font='7px '+L.mono;g.textAlign='left';g.textBaseline='middle';let last=-1e9;for(const f of[20000,10000,5000,2000,1000,500,200,100,50,20]){const yy=INV.fy(f,y0,h);if(yy-last<9||yy<y0+10||yy>y0+h-3)continue;last=yy;g.fillStyle=f===100||f===1000||f===10000?L.lab:L.mut;g.fillText(f>=1000?f/1000+'k':String(f),x+7,yy)}
    if(o.unit!==false){g.fillStyle=L.unit;g.textBaseline='top';g.fillText('HZ',x+7,y0+1)}g.textBaseline='alphabetic'},
  side(g,x,y0,w,h,vals,O,dt){/* the spectrum laid sideways on the spectrogram's rows */const L=INS.look(),R=O.range,X=d=>x+w*Math.max(0,Math.min(1,(d+R)/R)),hold=O.hold&&!INS.lite();let S=VZ.iside;
    g.lineWidth=INS.hair(g,L.lwGrid);g.strokeStyle=L.gMid;g.beginPath();for(let d=0;d>=-R+1e-9;d-=R/3){const xx=INS.px(g,X(d));g.moveTo(xx,y0);g.lineTo(xx,y0+h)}g.stroke();
    g.strokeStyle=L.gMin;g.beginPath();for(const f of[100,1000,10000]){const yy=INS.px(g,INV.fy(f,y0,h));g.moveTo(x,yy);g.lineTo(x+w,yy)}g.stroke();
    if(vals){const n=vals.length,rb=INV.rows(n);if(!S||S.sv.length!==n){S=VZ.iside={sv:new Float32Array(n).fill(-240),mh:new Float32Array(n).fill(-240)}}const a=1-Math.exp(-dt/.25),fall=3*dt;
      for(let r=0;r<n;r++){const v=vals[r]+O.tilt*rb[r*3+2];S.sv[r]=S.sv[r]<-200?v:S.sv[r]+(v-S.sv[r])*a;S.mh[r]=Math.max(S.sv[r],S.mh[r]-fall)}
      const yr=r=>y0+h*(r+.5)/n;if(hold){g.strokeStyle='rgba(255,255,255,.3)';g.lineWidth=1;g.beginPath();for(let r=0;r<n;r+=2){const xx=X(S.mh[r]),yy=yr(r);r?g.lineTo(xx,yy):g.moveTo(xx,yy)}g.stroke()}
      g.fillStyle='rgba(76,201,240,.12)';g.beginPath();g.moveTo(x,y0);for(let r=0;r<n;r+=2)g.lineTo(X(S.sv[r]),yr(r));g.lineTo(x,y0+h);g.closePath();g.fill();
      g.strokeStyle='#4cc9f0';g.lineWidth=INS.hair(g,L.lwCurve);g.beginPath();for(let r=0;r<n;r+=2){const xx=X(S.sv[r]),yy=yr(r);r?g.lineTo(xx,yy):g.moveTo(xx,yy)}g.stroke()}
    g.strokeStyle=L.gMaj;g.lineWidth=INS.hair(g,L.lwLine);g.strokeRect(INS.px(g,x),INS.px(g,y0),w,h);
    INS.corner(g,'TILT '+INS.num(O.tilt,O.tilt%1?1:0)+(hold?' · MAX':''),x+w-3,y0+3,'right');
    return X},
  /* the module: spectrogram | axis | spectrum, colour bar and dB numbers under them */
  mod(g,w,h,live){const O=INV.O(),L=INS.look(),bot=h>=70?13:0,ph=Math.max(10,h-bot),sideW=w>=220?Math.max(70,Math.min(170,Math.round(w*.26))):0,axW=sideW?30:0,sgW=Math.max(20,w-sideW-axW),now=performance.now(),dt=Math.min(.5,Math.max(.001,(now-(VZ.itv||now-16))/1000));VZ.itv=now;
    const vals=live&&play.on&&VZ.f?INV.colv(Math.max(2,Math.round(ph))):null;
    INV.sg(g,0,0,sgW,ph,vals,O);g.lineWidth=INS.hair(g,L.lwLine);g.strokeStyle=L.gMaj;g.strokeRect(INS.px(g,0),INS.px(g,0),sgW,ph);
    if(sideW){INV.fAxisV(g,sgW+1,0,ph);INV.side(g,sgW+axW,0,sideW-2,ph,vals,O,dt)}else{/* narrow: the numbers inside the left edge, as before */g.font='7px '+L.mono;g.fillStyle='rgba(255,255,255,.55)';g.textBaseline='middle';for(const f of[100,1000,10000]){g.fillText(f>=1000?f/1000+'k':String(f),4,INV.fy(f,0,ph))}g.textBaseline='alphabetic'}
    INS.corner(g,'SPECTROGRAM · '+(INV.MAPS.find(m=>m[0]===O.map)||['', 'Viridis'])[1].toUpperCase(),4,3);
    if(bot){const yb=ph+3,lab=INS.MIN+O.range;g.font='7px '+L.mono;g.textBaseline='middle';g.textAlign='left';g.fillStyle=L.mut;g.fillText(lab,3,yb+3);const tw=g.measureText(lab).width,bx=6+tw,bw=Math.max(30,Math.min(120,sgW*.4));INV.cbar(g,bx,yb+1.5,bw,3,O.map);
      g.fillStyle=L.lab;g.fillText('0',bx+bw+3,yb+3);g.fillStyle=L.unit;g.fillText('DBFS',bx+bw+3+g.measureText('0 ').width,yb+3);
      if(sideW){const x0=sgW+axW,sw=sideW-2;g.textAlign='center';g.fillStyle=L.mut;for(let d=0;d>=-O.range+1e-9;d-=O.range/3){const xx=x0+sw*(d+O.range)/O.range;g.textAlign=d===0?'right':Math.abs(d+O.range)<1e-9?'left':'center';g.fillText(INS.num(d,0),xx,yb+3)}g.textAlign='left'}
      g.textBaseline='alphabetic'}},
  /* Spectrum alone: IN-S's front panel with the menu's tilt and hold (its 10 dB/div stays) */
  fft(g,w,h,live){const O=INV.O(),st=VZ.ins||(VZ.ins={tr:{}});INS.spec(g,0,0,w,h,{tr:[{an:VZ.an,col:INS.SPC.c1,hold:O.hold&&!INS.lite(),fall:3,anAvg:true,st:st.tr}],lo:20,hi:20000,top:0,bot:-100,tilt:O.tilt||0,live:!!(live&&VZ.an),st})},
  /* Waveform: an amplitude scale and a time scale bar measured from the columns really written */
  waveScale(g,w,h,live){const L=INS.look(),mid=h/2,a=mid*.95;if(live&&play.on){const t=INV.wt||(INV.wt=[]);t.push(performance.now());if(t.length>90)t.shift()}else if(INV.wt&&INV.wt.length&&performance.now()-INV.wt[INV.wt.length-1]>1500)INV.wt=[];
    g.lineWidth=INS.hair(g,L.lwLine);g.strokeStyle=L.tick;g.beginPath();for(const k of[1,.5]){for(const sg of[-1,1]){const yy=INS.px(g,mid+sg*a*k);g.moveTo(0,yy);g.lineTo(k===1?5:3,yy)}}g.stroke();
    g.font='7px '+L.mono;g.textBaseline='middle';g.textAlign='left';g.fillStyle=L.lab;g.fillText('0',7,mid-a+4);g.fillStyle=L.unit;g.fillText('DBFS',7+g.measureText('0 ').width,mid-a+4);g.fillStyle=L.mut;g.fillText(INS.MIN+'6',7,mid-a*.5);
    const t=INV.wt;if(t&&t.length>20){const rate=(t.length-1)/((t[t.length-1]-t[0])/1000);let d=null;for(const s of[.25,.5,1,2,5,10]){if(rate*s>=40){d=s;break}}if(d&&rate*d<=Math.min(160,w*.5)){const len=rate*d,x1=w-6,x0=x1-len,yy=INS.px(g,h-14);
      g.strokeStyle=L.unit;g.lineWidth=1;g.beginPath();g.moveTo(x0,yy);g.lineTo(x1,yy);g.moveTo(x0,yy-2.5);g.lineTo(x0,yy+2.5);g.moveTo(x1,yy-2.5);g.lineTo(x1,yy+2.5);g.stroke();
      const un=d>=1?'s':'ms';g.textAlign='right';g.fillStyle=L.unit;const uw=g.measureText(' '+INS.ucap(un)).width;g.fillText(INS.ucap(un),x1,yy-7);g.fillStyle=L.ink;g.fillText(d>=1?String(d):String(d*1000),x1-uw,yy-7);INV.sb=d}}
    g.textAlign='left';g.textBaseline='alphabetic'},
  /* Levels as M2 */
  lev(g,w,h,live){const L=INS.look(),ch=[anL,anR],nm=['L','R'],bw=Math.max(8,Math.min(22,(w-40)/3)),top=14,bot=h-16,H=Math.max(10,bot-top),Y=d=>top+H-H*dbN(d);
    INS.scaleTaper(g,28,top,H,{fs:7,gap:9});
    ch.forEach((an,i)=>{const x=34+i*(bw+6);g.fillStyle='#121318';g.fillRect(x,top,bw,H);if(!live||!an)return;const pk=peakOf(an),d=pk>1e-6?20*Math.log10(pk):-90;VZ.hold[i]=Math.max((VZ.hold[i]??-90)-.35,d);
      const gr=g.createLinearGradient(0,bot,0,top);gr.addColorStop(0,'#3ecf8e');gr.addColorStop(.7,'#f5c84c');gr.addColorStop(.92,'#ff9a3c');gr.addColorStop(1,'#ff2d55');
      INS.mbar(g,x,top,bw,H,dbN(d),INM.rfr(an,dbN),gr);if(VZ.hold[i]>-59){g.fillStyle=VZ.hold[i]>-.1?'#ff3b3b':'#fff';g.fillRect(x,Y(VZ.hold[i]),bw,1.5)}if(d>-.1){g.fillStyle='#ff2d55';g.fillRect(x,top-6,bw,4)}
      g.fillStyle='rgba(255,255,255,.5)';g.font='600 9px Inter,system-ui,sans-serif';g.fillText(nm[i],x+bw/2-3,h-4)});
    const lx=34+2*(bw+6)+4;if(lx+44<w){const m=live&&typeof INM==='object'&&INM.read?INM.read(anL,anR):null,hp=Math.max(VZ.hold[0]??-90,VZ.hold[1]??-90),rows=[['SHORT-TERM',LM.S>-69?LM.S:null,'LUFS'],['PEAK',hp>-89?hp:null,'dBFS'],['RMS',m&&m.rms>-100?m.rms:null,'dBFS'],['CREST',m&&m.cf>-100&&m.rms>-100?m.cf:null,'dB']];
      let yy=top+8;for(const[k,v,u] of rows){if(yy+16>bot+8)break;g.fillStyle=L.mut;g.font='7px '+L.mono;g.fillText(k,lx,yy);g.font='600 12px '+L.mono;g.fillStyle=L.ink;const s=v==null?'–':INS.num(v,1);g.fillText(s,lx,yy+14);g.font='7px '+L.mono;g.fillStyle=L.unit;g.fillText(INS.ucap(u),lx+INV.tw(g,s)+3,yy+14);yy+=27}}},
  tw(g,s){const f=g.font;g.font='600 12px '+INS.look().mono;const w=g.measureText(s).width;g.font=f;return w},
  /* All: the spectrogram and spectrum panes become one module over both rectangles */
  merge(P){const a=P.findIndex(p=>p[0]==='spec'),b=P.findIndex(p=>p[0]==='fft');if(a<0||b<0)return P;const A=P[a],B=P[b],x=Math.min(A[1],B[1]),y=Math.min(A[2],B[2]),x2=Math.max(A[1]+A[3],B[1]+B[3]),y2=Math.max(A[2]+A[4],B[2]+B[4]);
    P[a]=['spec',x,y,x2-x,y2-y];P.splice(b,1);return P},
  /* the menu entries (pvMenu) */
  menu(){if(!UI.viz)return[];const O=INV.O(),s=(k,v)=>()=>{INV.set(k,v)};
    return['-',{head:'Visualizer pictures'},
      {label:'Colour map',sub:(INV.MAPS.find(m=>m[0]===O.map)||[0,''])[1],kids:INV.MAPS.map(([k,l])=>({label:l,check:O.map===k,act:s('map',k)}))},
      {label:'Range',sub:O.range+' dB',kids:[60,90,120].map(r=>({label:r+' dB',check:O.range===r,act:s('range',r)}))},
      {label:'Spectrum tilt',sub:O.tilt?INS.num(O.tilt,O.tilt%1?1:0)+' dB per octave':'Off',kids:[[0,'Off (flat)'],[3,'3 dB per octave'],[4.5,'4.5 dB per octave']].map(([t,l])=>({label:l,check:O.tilt===t,act:s('tilt',t)}))},
      {label:'Max hold',sub:'a faint line at the highest level, falling 3 dB a second',sw:true,check:O.hold,act:s('hold',!O.hold)},
      {label:'Speed',sub:({slow:'Slow',normal:'Normal',fast:'Fast'})[O.speed],kids:[['slow','Slow'],['normal','Normal'],['fast','Fast']].map(([k,l])=>({label:l,check:O.speed===k,act:s('speed',k)}))}]}
};
if(typeof VZD==='object'&&VZD){VZD.spec=INV.mod;VZD.fft=INV.fft;VZD.lev=INV.lev;{const _w=VZD.wave;VZD.wave=function(g,w,h,live){_w.apply(this,arguments);INV.waveScale(g,w,h,live)}}}
/* ===== end of lane E IN-V ===== */
