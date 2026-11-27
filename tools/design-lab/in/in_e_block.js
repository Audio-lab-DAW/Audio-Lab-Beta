/* ===== lane E (task IN-E): the EQ displays, the user's pick E3 (bandwidth calipers) =====
   E3 is E1 (the calibrated EQ) with the area between the summed curve and 0 dB lightly filled, so boosts and cuts read as shapes; an amber
   caliper under each bell marking its bandwidth with the width in octaves (the M3 caliper style); shelves and cuts show their corner frequency.
   - Pro EQ (vizEQ2): the gain scale on the left in the gain colour (it was on the right in grey), the analyzer's dBFS scale on the right in the
     analyzer's colour with its 4.5 dB/oct tilt named (levels in dBFS as IN-S calibrated them: the analyser reads a sine 13.56 dB low), the fill,
     the calipers and corner marks; the band read-out adds the note (X8) and the width in octaves. The ±24 dB range stays: the hit test, the drag
     and the box select share it, so a zoom (E1's ±6 to ±30) would have to change them together (left for later, named in the log).
   - Bell widths are measured on the band's own response (getFrequencyResponse, what the band really does): the two frequencies where the bell
     is at half its gain in dB, which is how Q is defined for a bell (for a 6 dB bell, its -3 dB points). Band-pass: 3 dB under its top; notch:
     3 dB under 0. Nothing new in the audio path; drawn with the display, nothing extra when it is hidden.
   - Filter (vizFilter) and Auto Filter: the fill to 0 dB, the corner mark at the cutoff for low-pass and high-pass, the caliper for band-pass,
     notch and peak. */
const INSE={gain:'#c9b37a',ana:'rgba(120,200,255,.62)',fill:'rgba(255,210,122,.08)',bw:[],cal:[],corner:[]};
/* the bandwidth around index ic of a response (F ascending in Hz, D in dB) at the level lv: the two crossings, interpolated on the log axis */
function ineBW(F,D,n,ic,lv){const up=D[ic]>lv;let a=-1,b=-1;
  for(let k=ic;k>0;k--)if((D[k-1]>lv)!==up){const t=(lv-D[k])/((D[k-1]-D[k])||1e-9);a=Math.exp(Math.log(F[k])+(Math.log(F[k-1])-Math.log(F[k]))*t);break}
  for(let k=ic;k<n-1;k++)if((D[k+1]>lv)!==up){const t=(lv-D[k])/((D[k+1]-D[k])||1e-9);b=Math.exp(Math.log(F[k])+(Math.log(F[k+1])-Math.log(F[k]))*t);break}
  return a>0&&b>0?{f1:a,f2:b,oct:Math.log2(b/a)}:null}
/* an amber caliper from x1 to x2 at y with its label above (up) or below */
function ineCaliper(g,x1,x2,y,s,up,lo,hi){const L=INS.look(),yy=INS.px(g,Math.max(lo,Math.min(hi,y)));g.strokeStyle=L.unit;g.lineWidth=INS.hair(g,1);g.beginPath();
  g.moveTo(x1,yy-3);g.lineTo(x1,yy+3);g.moveTo(x2,yy-3);g.lineTo(x2,yy+3);g.moveTo(x1,yy);g.lineTo(x2,yy);g.stroke();
  g.font='7.5px '+L.mono;g.textAlign='center';g.textBaseline=up?'bottom':'top';const xm=(x1+x2)/2,tw=g.measureText(s).width;if(tw<Math.max(40,x2-x1+60)){g.fillStyle=L.unit;g.fillText(s,xm,up?yy-3:yy+3)}g.textAlign='left';g.textBaseline='alphabetic'}
/* corner marks along the bottom: an amber tick at each frequency, its value above it where there is room */
function ineCorners(g,list,yb){if(!list.length)return;const L=INS.look();list.sort((a,b)=>a[0]-b[0]);g.strokeStyle=L.unit;g.lineWidth=INS.hair(g,1);g.beginPath();for(const[x] of list){const xx=INS.px(g,x);g.moveTo(xx,yb);g.lineTo(xx,yb-8)}g.stroke();
  g.font='7.5px '+L.mono;g.textBaseline='bottom';g.textAlign='center';g.fillStyle=L.unit;let last=-1e9;for(const[x,s] of list){const tw=g.measureText(s).width;if(x-tw/2<last+4)continue;g.fillText(s,x,yb-10);last=x+tw/2}g.textAlign='left';g.textBaseline='alphabetic'}
const ineOct=o=>INS.num(o,2)+' oct',ineHz=f=>INS.fmt(f,'Hz');
/* Pro EQ: the analyzer's scale (dBFS at 1 kHz, with the tilt) on the right */
function ineAnaScale(g,w,h){const L=INS.look();g.font='7.5px '+L.mono;g.textAlign='right';g.textBaseline='middle';g.fillStyle=INSE.ana;
  for(const t of[-20,-40,-60]){const raw=t-INS.SPCAL,y=h-(raw+90)/84*h;if(y<44||y>h-26)continue;g.fillText(INS.num(t,0)+' dBFS',w-4,y)}
  g.textBaseline='top';g.fillText('analyzer, tilt 4.5 dB/oct',w-4,4);g.textAlign='left';g.textBaseline='alphabetic'}
/* Pro EQ: one band's mark from its own response (M2 over FQ); called in the band loop */
function ineBand(i,b,M2,n,w,dy){if(!b||!b.on)return;const F=FQ,D=INSE.D&&INSE.D.length>=n?INSE.D:(INSE.D=new Float32Array(n));for(let k=0;k<n;k++)D[k]=20*Math.log10(Math.max(1e-9,M2[k]));
  const t=b.t;if(t==='peaking'||t==='bandpass'||t==='notch'){let ic=0,ext=0;for(let k=0;k<n;k++){const v=t==='bandpass'?D[k]:Math.abs(D[k]);if(k===0||v>ext){ext=v;ic=k}}
      const top=D[ic];if(t==='peaking'&&Math.abs(top)<.5)return;const lv=t==='peaking'?top/2:t==='bandpass'?top-3:-3,r=ineBW(F,D,n,ic,lv);if(!r)return;INSE.bw[i]=r.oct;
      INSE.cal.push([fX(r.f1,w),fX(r.f2,w),dy(top)+(top>0?-14:14),ineOct(r.oct),top>0])}
  else if(/shelf|pass|tilt/.test(t))INSE.corner.push([fX(b.f,w),ineHz(b.f)])}
/* Pro EQ: the fill between the summed curve and 0 dB (before the curve is drawn) */
function ineFill(g,p,n,dy){const og=Math.pow(10,(p.out||0)/20),y0=dy(0);g.beginPath();g.moveTo(0,y0);for(let k=0;k<n;k++)g.lineTo(k*2,dy(clamp(20*Math.log10(Math.max(1e-9,MT[k]*og)),-30,30)));g.lineTo((n-1)*2,y0);g.closePath();g.fillStyle=INSE.fill;g.fill()}
/* Pro EQ: the calipers and corner marks (after the curve), then clear for the next draw */
function ineMarks(g,w,h){for(const[a,b,y,s,up] of INSE.cal)ineCaliper(g,a,b,y,s,up,12,h-30);ineCorners(g,INSE.corner,h-14);INSE.cal=[];INSE.corner=[]}
/* Filter and Auto Filter: marks from a response (F Hz, lin magnitudes), x and y mappings */
function ineFiltMarks(g,kind,f0,F,mag,n,X,Y,yb,lo,hi){const D=new Float32Array(n);for(let k=0;k<n;k++)D[k]=20*Math.log10(Math.max(1e-9,mag[k]));
  if(kind==='lp'||kind==='hp'){ineCorners(g,[[X(f0),ineHz(f0)]],yb);return}
  let ic=0,ext=-1e9;for(let k=0;k<n;k++){const v=kind==='notch'?-D[k]:D[k];if(v>ext){ext=v;ic=k}}const top=D[ic],lv=kind==='notch'?-3:kind==='peak'?top/2:top-3;if(kind==='peak'&&Math.abs(top)<.5)return;
  const r=ineBW(F,D,n,ic,lv);if(r)ineCaliper(g,X(r.f1),X(r.f2),Y(top)+(top>0?-14:14),ineOct(r.oct),top>0,lo,hi)}
function ineVizFilter(g,w,h,p){const n=120,F=new Float32Array(n),M=new Float32Array(n);for(let k=0;k<n;k++){const fr=20*Math.pow(1000,k/(n-1)),r=fr/p.freq;F[k]=fr;M[k]=1/Math.sqrt(Math.pow(1-r*r,2)+Math.pow(r/Math.max(.1,p.q),2))}
  ineFiltMarks(g,'lp',p.freq,F,M,n,f=>fX(f,w),db=>h*.5-db/24*h*.4,h-14,10,h-24)}
function ineAfilt(g,p,fr,mg,N,w,Yd,Bm,m){const t=p.type,kind=/^lp/.test(t)?'lp':/^hp/.test(t)?'hp':t==='bp'?'bp':t==='notch'?'notch':t==='peak'?'peak':null;if(!kind)return;
  const M=new Float32Array(N);for(let k=0;k<N;k++)M[k]=m*mg[k]+(1-m);ineFiltMarks(g,kind,p.freq,fr,M,N,f=>Math.log(f/20)/Math.log(1000)*w,Yd,Bm-2,12,Bm-16)}
/* ===== end of lane E IN-E ===== */
