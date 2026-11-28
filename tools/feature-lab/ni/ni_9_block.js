
/* ===== lane D (task NI-9): I5 harmonic ruler =====
   A piano strip along the bottom of every spectrum view drawn by lane E's INS.spec (the Spectrum device, the spectrum overlay, the
   Visualizer), the five strongest peaks of the live trace labelled with note and cents ("A2 0 c"); peaks outside the song key in amber,
   peaks that keep ringing for more than a beat after the rest of the sound (at least as loud as the pitch
   within 12 dB when it started) faded by 6 dB more than the pitch did, while the pitch itself fades too (a held note that does not
   fade is a note, not a ringing resonance), in red. Drawn into the view's own canvas after lane E's
   drawer (INS.spec is wrapped once, its code is not changed); nothing is drawn or computed while the view is not live (stopped, closed),
   the peaks are found at most 8 times a second per view (3 at the Light level) from the bins the view has already read this frame.
   Switch: UI.niHr (on unless set to false), command ni.harmonicRuler, main menu, Settings row ni.harmonicRuler.
   NI_HOOKS.harmonicRuler(g, box, peaks, o) draws a ruler into any canvas, NI_HOOKS.harmonicPeaks(an, lo, hi, st) finds the peaks. */
NI.hr={v:1,runs:0,draws:0,wrapped:false};
const NI_HR_COL={ink:'#ececf1',key:'#ffb547',ring:'#ff6b6b'};
function NI_hrOn(){return!(typeof UI==='object'&&UI&&UI.niHr===false)}
/* a frequency as note and cents: {m, r, c, name: "A2", txt: "A2 0 c" / "A2 +12 c" / "A2 −8 c"} */
function NI_hrNote(f){const m=NI_midi(f),r=Math.round(m),c=Math.round((m-r)*100),name=NI_PCN[((r%12)+12)%12]+(Math.floor(r/12)-1);return{m,r,c,name,txt:name+' '+(c>0?'+'+c:c<0?'−'+(-c):'0')+' c'}}
/* the peaks of an analyser's bins (dB, as INS.fft returns them): local maxima standing 8 dB over the 1/6 octave around them, refined by a
   parabola through the top bin and its neighbours (with the analyser's Blackman window the frequency is within 0.01 bin of a steady
   tone); one per 70 cents, the strongest first. D: the bins; sr, fft: the analyser's rate and size. */
function NI_hrFind(D,sr,fft,lo,hi,n){n=n||5;const N=D.length,bh=sr/fft,k0=Math.max(3,Math.ceil(Math.max(lo,25)/bh)),k1=Math.min(N-3,Math.floor(Math.min(hi,sr/2*.95)/bh));let top=-1e9;
  for(let k=k0;k<=k1;k++)if(D[k]>top)top=D[k];if(!(top>-140))return[];const thr=Math.max(-130,top-54),c=[];
  for(let k=k0;k<=k1;k++){const v=D[k];if(!(v>thr&&v>D[k-1]&&v>=D[k+1]))continue;const w=Math.max(4,Math.round(k*(Math.pow(2,1/12)-1)));let mn=1e9;
    for(let i=Math.max(1,k-w);i<=Math.min(N-1,k+w);i++)if(D[i]<mn)mn=D[i];if(v-mn<8)continue;
    const a=D[k-1],e=D[k+1],dn=a-2*v+e;let p=0;if(isFinite(a)&&isFinite(e)&&dn<0)p=Math.max(-.5,Math.min(.5,.5*(a-e)/dn));c.push({hz:(k+p)*bh,db:v-.25*(a-e)*p,k})}
  c.sort((x,y)=>y.db-x.db);const out=[];for(const q of c){if(out.some(o=>Math.abs(1200*Math.log2(q.hz/o.hz))<70))continue;out.push(q);if(out.length>=n)break}return out}
/* the level of everything but the peaks (dB), for the ringing check */
function NI_hrRest(D,sr,fft,lo,hi,pk){const bh=sr/fft,k0=Math.max(1,Math.ceil(lo/bh)),k1=Math.min(D.length-1,Math.floor(hi/bh));let s=0;
  for(let k=k0;k<=k1;k++){let near=false;for(const q of pk)if(Math.abs(k-q.k)<=4){near=true;break}if(!near)s+=Math.pow(10,D[k]/10)}return 10*Math.log10(s+1e-20)}
/* the peaks of a view, kept in the view's own state: found at most every 125 ms (333 ms at the Light level); each peak remembers since when
   it sounds at that pitch (within 35 cents), its loudest level and the loudest level of the rest since then */
NI.hr.peaks=function(an,lo,hi,st){if(!an||!st)return[];const now=performance.now(),H=st.niHr||(st.niHr={t:0,pk:[],tr:[]}),iv=INS.lite()?333:125;
  if(now-H.t<iv)return H.pk;H.t=now;NI.hr.runs++;const D=INS.fft(an),sr=an.context&&an.context.sampleRate||(typeof ctx==='object'&&ctx&&ctx.sampleRate)||48000,fft=an.fftSize||D.length*2,pk=NI_hrFind(D,sr,fft,lo,hi,5),rest=NI_hrRest(D,sr,fft,lo,hi,pk),
    beat=60/Math.max(20,(typeof S==='object'&&S&&S.bpm)||120)*1000,K=NI_hrKey(),tr=[];
  for(const q of pk){const nt=NI_hrNote(q.hz);let o=H.tr.find(x=>Math.abs(1200*Math.log2(q.hz/x.hz))<35);
    if(o){o.hz=q.hz;o.vMax=Math.max(o.vMax,q.db);o.rMax=Math.max(o.rMax,rest)}else o={hz:q.hz,t0:now,vMax:q.db,rMax:rest};tr.push(o);
    const age=(now-o.t0)/beat,fade=(o.rMax-rest)-(o.vMax-q.db);q.note=nt;q.out=!!(K&&K.pcs&&!K.pcs.includes(((nt.r%12)+12)%12));q.beats=age;q.ring=age>1&&fade>=6&&o.vMax-q.db>=1&&o.rMax>-125&&o.rMax>=o.vMax-12}
  H.tr=tr;H.pk=pk;return pk};
NI_HOOKS.harmonicPeaks=NI.hr.peaks;
/* the song key, read at most once a second */
function NI_hrKey(){const now=performance.now(),H=NI.hr;if(!H.kt||now-H.kt>1000){H.kt=now;try{H.key=NI_key()}catch(e){H.key=null}}return H.key}
/* the ruler: a piano strip across the box (x, y, w, h: the strip itself) on the view's log axis lo..hi, octave cells with C named where
   there is room, black keys where a semitone is at least 1.6 px wide, the key's notes lit, the peaks marked on the strip and named above it.
   o: {size: 'full' | 'mid', top (the highest y a label may use)} */
function NI_hrDraw(g,b,pk,o){o=o||{};const L=INS.look(),K=Math.log(b.hi/b.lo),X=f=>b.x+b.w*Math.log(f/b.lo)/K,sw=b.w*Math.log(2)/12/K,key=NI_hrKey();NI.hr.draws++;
  g.save();g.beginPath();g.rect(b.x,b.y-60,b.w,b.h+60);g.clip();
  g.fillStyle='rgba(5,7,12,.82)';g.fillRect(b.x,b.y,b.w,b.h);
  const m0=Math.floor(NI_midi(b.lo)),m1=Math.ceil(NI_midi(b.hi));
  for(let m=m0;m<=m1;m++){const pc=((m%12)+12)%12,xa=X(NI_hz(m-.5)),xb=X(NI_hz(m+.5));
    if(sw>=1.6){const blk=[1,3,6,8,10].includes(pc);if(blk){g.fillStyle='rgba(0,0,0,.75)';g.fillRect(xa,b.y,xb-xa,b.h*.58)}else{g.fillStyle='rgba(255,255,255,.07)';g.fillRect(xa,b.y,xb-xa,b.h)}}
    if(key&&key.pcs&&key.pcs.includes(pc)&&sw>=1.6){g.fillStyle='rgba(245,200,76,.28)';g.fillRect(xa,b.y+b.h-2,Math.max(1,xb-xa-.5),2)}
    if(pc===0){const x=X(NI_hz(m-.5));g.fillStyle=L.tick;g.fillRect(Math.round(x),b.y,1,b.h);const oc=Math.floor(m/12)-1,ow=sw*12;
      if(ow>=18&&oc>=0){g.font='7px '+L.mono;g.textBaseline='middle';g.textAlign='left';g.fillStyle=L.mut;g.fillText('C'+oc,x+2,b.y+b.h/2+.5)}}}
  g.strokeStyle='rgba(255,255,255,.14)';g.lineWidth=1;g.strokeRect(b.x+.5,b.y+.5,b.w-1,b.h-1);
  /* the peaks: a mark on the strip, the name above it (two rows when names would touch) */
  const list=pk.filter(q=>q.hz>=b.lo&&q.hz<=b.hi).map(q=>({q,x:X(q.hz),c:q.ring?NI_HR_COL.ring:q.out?NI_HR_COL.key:NI_HR_COL.ink})).sort((a,c)=>a.x-c.x);
  g.font=(o.size==='full'?8:7)+'px '+L.mono;g.textBaseline='bottom';g.textAlign='center';const rowH=o.size==='full'?10:9,ends=[-1e9,-1e9];
  for(const it of list){const t=it.q.note.txt+(it.q.ring?' rings':''),tw=g.measureText(t).width+6;let r=it.x-tw/2>ends[0]+2?0:1;if(r===1&&it.x-tw/2<=ends[1]+2)r=0;ends[r]=it.x+tw/2;
    const ly=b.y-2-r*rowH,lx=Math.max(b.x+tw/2,Math.min(b.x+b.w-tw/2,it.x));
    if(o.top!=null&&ly-rowH<o.top)continue;
    g.fillStyle='rgba(5,7,12,.78)';g.fillRect(lx-tw/2,ly-rowH+1,tw,rowH-1);g.fillStyle=it.c;g.fillText(t,lx,ly);
    g.fillRect(Math.round(it.x)-.5,b.y,1.5,b.h);g.beginPath();g.moveTo(it.x,b.y+b.h-1);g.lineTo(it.x-3,b.y+b.h+3);g.lineTo(it.x+3,b.y+b.h+3);g.closePath();g.fill()}
  g.restore();NI.hr.last=list.map(it=>({t:it.q.note.txt+(it.q.ring?' rings':''),c:it.c,hz:it.q.hz}));return list.length}
NI_HOOKS.harmonicRuler=(g,box,peaks,o)=>NI_hrDraw(g,box,peaks||[],o);
/* lane E's drawer, wrapped once: after it drew a live view of size 'full' or 'mid', the ruler goes along the bottom of its graticule */
function NI_hrWrap(){if(NI.hr.wrapped||typeof INS!=='object'||typeof INS.spec!=='function')return false;const base=INS.spec;
  INS.spec=function(g,x,y,w,h,o){const r=base.apply(this,arguments);try{NI_hrAfter(g,w,h,o,r)}catch(e){if(!NI.hr.err){NI.hr.err=1;console.warn('harmonic ruler',e)}}return r};INS.spec.niBase=base;NI.hr.wrapped=true;return true}
function NI_hrAfter(g,w,h,o,r){if(!o||!r||!NI_hrOn())return;const T=o.tr&&o.tr[0];if(o.live===false||!T||!T.an)return;const sz=o.size||(h>=150&&w>=320?'full':h>=96&&w>=200?'mid':'mini');if(sz==='mini')return;
  const lo=o.lo||20,hi=o.hi||20000,st=o.st||T.st;if(!st)return;const pk=NI.hr.peaks(T.an,lo,hi,st),sh=sz==='full'?12:10;if(r.gw<120||r.gh<60)return;
  NI_hrDraw(g,{x:r.gx,y:r.gy+r.gh-sh,w:r.gw,h:sh,lo,hi},pk,{size:sz,top:r.gy+2})}
if(!NI_hrWrap())setTimeout(NI_hrWrap,0);
function NI_hrShow(on){UI.niHr=!!on;try{saveUI()}catch(e){}if(typeof toast==='function')toast(on?'Harmonic ruler on: the strongest notes of the sound under every spectrum view':'Harmonic ruler off')}
window.NI_SETTINGS=window.NI_SETTINGS||[];
NI_SETTINGS.push({id:'ni.harmonicRuler',label:'Harmonic ruler under spectrum views',page:'Display',block:'Analysis',scope:'app',key:'niHr',default:true,help:'A piano strip along the bottom of every spectrum view: the five strongest peaks named with note and cents, amber outside the song key, red when a pitch keeps ringing for more than a beat.',search:['harmonic','ruler','note','cents','pitch','peak','spectrum','key','resonance','ring']});
/* ===== end of lane D NI-9 ===== */
