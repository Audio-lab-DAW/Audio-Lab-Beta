"""Task NI-6 (lane D): I6 energy arc.
Edit script with unique asserted anchors (needs NI-3, NI-4 and NI-5b in the file), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_6.py [index.html]
Adds:
  - a thin lane under the section row (under the tempo lane when that is shown), off by default (UI.niArc): the song's energy over time,
    from three ingredients read from NI-3's per-beat cache of every track (nothing measured live, nothing in the audio path):
    loudness (the tracks' K-weighted power added up, as LUFS), density (how many of the song's tracks play) and brightness (the spectral
    centroid of all tracks together), each smoothed over 4 beats. Energy = 55% loudness + 25% density + 20% brightness, each scaled 0 to 1
    (loudness -36 to -6 LUFS, density 0 to all tracks, brightness 150 Hz to 6 kHz on a log scale)
  - the curve filled with a magma ramp (brighter = more energy); pointing at it draws the three ingredients apart (cyan, violet, amber)
    with a read-out; "Always show the three ingredients" keeps them; section starts as hairlines; not-yet-measured beats hatched
  - a dashed comparison curve: a typical psytrance arc (from the section names when every section has a known name: intro, build, drop,
    break, outro...; otherwise a generic arc over the song length), scaled to the song's own range; a reference's arc when another lane
    gives one (NI.arc.setRef, for lane C's FT-F25a reference slots)
  - click moves the playhead; right-click: compare with, ingredients, hide. Switch: the section row's menu ("Show the energy arc") and
    the command ni.energyArc. Settings rows in NI_SETTINGS (S4 shape)
  - drawn only inside the arrangement's normal redraw (no timer, no per-frame work while idle); the analysis starts 0.3 s after the lane
    is shown, again 1.2 s after an edit settles, and is cancelled when the lane is hidden (unless the frequency map or the clashes need it)
"""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane D (task NI-6)'
if MARK in s:
    print('NI-6 already applied'); sys.exit(0)
for m in ('/* ===== end of lane D NI-3 ===== */', '/* ===== end of lane D NI-4 ===== */', '/* ===== end of lane D NI-5b ===== */'):
    assert m in s, m + ' must be in the file first'

def rep(s, old, new):
    n = s.count(old)
    assert n == 1, (old[:70], n)
    return s.replace(old, new)

# 1. the lanes' height above the tracks: the tempo lane plus the energy arc; the tempo lane keeps its own 44 px
s = rep(s, "const TMPH=()=>UI.tempoLane?44:0;", "const TMPH=()=>(UI.tempoLane?44:0)+NI_arcH();/* the tempo lane and (lane D, NI-6) the energy arc under it */")
s = rep(s, "function tmpGeo(){const y=TY+RUL+SECH,h=TMPH(),", "function tmpGeo(){const y=TY+RUL+SECH,h=UI.tempoLane?44:0,")
s = rep(s, "  if(TMPH())drawTempoLane(g,w);\n", "  if(UI.tempoLane)drawTempoLane(g,w);if(NI_arcH())NI_arcDraw(g,w);\n")

# 2. the switch in the section row's menu, next to the tempo lane's
A2 = "{label:(UI.tempoLane?'Hide':'Show')+' the tempo and time signature lane',act:()=>tempoLaneShow(!UI.tempoLane)}"
assert s.count(A2) == 2, ('tempo lane menu items', s.count(A2))  # the section row's menu and the empty-arrangement menu
s = s.replace(A2, A2 + ",{label:(UI.niArc?'Hide':'Show')+' the energy arc',sub:'loudness, tracks playing and brightness over the song',act:()=>NI_arcShow(!UI.niArc)}")

# 3. the command, after ni.kickBass
A3 = "run:()=>NI_kbOpen()},"
s = rep(s, A3, A3 + "\n {id:'ni.energyArc',g:'view',l:'Energy arc on / off (loudness, tracks playing and brightness over the song)',d:'',ic:'M2 15c3 0 3-8 6-8s3 5 5 5 3-7 5-7',run:()=>NI_arcShow(!UI.niArc)},")

# 4. JS after NI-5b
JS = r"""
/* ===== lane D (task NI-6): I6 energy arc =====
   A lane under the section row. Everything comes from NI-3's per-beat cache (NI.an), worked out once per change of the analysis into
   per-beat arrays (a few ms for a whole song), drawn inside drawArr's normal redraw: no timer, nothing per frame while idle. */
NI.arc={d:null,stale:true,run:'',pend:'',tok:0,et:0,hov:-1,hx:0,res:null,draws:0,calcs:0,ref:null,tt:0,retry:0};
const NI_ARC_H=40,NI_ARC_W={l:.55,d:.25,b:.2},NI_ARC_COL={e:'#ececf1',l:'#4cc9f0',d:'#b583ff',b:'#ffb547',cmp:'rgba(236,236,241,.6)'};
/* a typical psytrance arc over the song (fraction, level 0 to 1): intro, build, drop, break, build, second drop, outro */
const NI_ARC_TYP=[[0,.25],[.1,.5],[.17,.8],[.18,.95],[.42,.95],[.44,.4],[.55,.45],[.62,.85],[.63,1],[.88,1],[.9,.6],[1,.2]];
/* section names it knows (the first match wins), with the level at the start and the end of the section */
const NI_ARC_SEC=[[/build|rise|riser|pre.?drop|lift|tension/i,.45,.85],[/drop|main|climax|chorus|peak|hook/i,.95,.95],[/break|bridge|calm|ambient|interlude/i,.4,.4],[/intro|start/i,.25,.55],[/outro|ending|end\b/i,.6,.2],[/verse|groove/i,.65,.65]];
function NI_arcH(){return typeof UI!=='undefined'&&UI&&UI.niArc?NI_ARC_H:0}
function NI_arcY(){return TY+RUL+SECH+(UI.tempoLane?44:0)}
/* per beat: loudness (LUFS), share of tracks playing, brightness (Hz), energy 0 to 1, each smoothed over 4 beats */
function NI_arcCalc(){const A=NI.arc;A.calcs++;const L=NI_anTracks().filter(t=>(t.clips||[]).length),nb=Math.max(0,Math.ceil(NI_anEnd())),B=NI_AN_NB,F=NI.an.bands,np=Math.ceil(nb/NI_AN_SEG);
  const pw=new Float64Array(nb),cnt=new Float32Array(nb),num=new Float64Array(nb),den=new Float64Array(nb),unk=new Uint8Array(nb);let all=0,left=0;
  for(const t of L)for(let p=0;p<np;p++){const r=NI_anPiece(t,p);all++;if(r==='')continue;if(!r){left++;for(let j=0;j<NI_AN_SEG&&p*NI_AN_SEG+j<nb;j++)unk[p*NI_AN_SEG+j]=1;continue}
    for(let j=0;j<r.nb;j++){const b=p*NI_AN_SEG+j;if(b>=nb)break;if(!r.play[j])continue;cnt[b]++;pw[b]+=Math.pow(10,(r.loud[j]+.691)/10);const q=j*B;
      for(let k=0;k<B;k++){const v=NI_MAP_P[r.mid[q+k]]+NI_MAP_P[r.side[q+k]];if(v>0){num[b]+=v*F[k];den[b]+=v}}}}
  const nT=Math.max(1,L.length),lu=new Float32Array(nb),dn=new Float32Array(nb),br=new Float32Array(nb),ln=new Float32Array(nb),bn=new Float32Array(nb),E=new Float32Array(nb),snd=new Uint8Array(nb);
  for(let b=0;b<nb;b++){let a=0,c=0,n=0,d=0,m=0;for(let i=b-2;i<=b+1;i++){if(i<0||i>=nb)continue;m++;a+=pw[i];c+=cnt[i];n+=num[i];d+=den[i]}
    lu[b]=a>0?10*Math.log10(a/m)-.691:-120;dn[b]=Math.min(1,c/m/nT);br[b]=d>0?n/d:0;snd[b]=a>0?1:0;
    ln[b]=clamp((lu[b]+36)/30,0,1);bn[b]=br[b]>0?clamp(Math.log2(br[b]/150)/Math.log2(40),0,1):0;E[b]=a>0?NI_ARC_W.l*ln[b]+NI_ARC_W.d*dn[b]+NI_ARC_W.b*bn[b]:0}
  /* the song's own range (5th to 95th percentile of the sounding, measured beats), for the comparison curve */
  const v=[];for(let b=0;b<nb;b++)if(snd[b]&&!unk[b])v.push(E[b]);v.sort((a,b)=>a-b);const pc=q=>v.length?v[Math.min(v.length-1,Math.floor(q*(v.length-1)))]:0;
  return{nb,nT,lu,dn,br,ln,bn,E,snd,unk,lo:pc(.05),hi:pc(.95),all,left,complete:!left,cmp:NI_arcCmpCurve(nb)}}
/* the comparison curve per beat, 0 to 1 (the shape; drawn scaled into the song's range), or null */
function NI_arcCmpCurve(nb){const c=UI.niArcCmp||'typ';if(!nb||c==='none')return null;const out=new Float32Array(nb);
  if(c==='ref'){const R=NI.arc.ref;if(!R)return null;for(let b=0;b<nb;b++)out[b]=clamp(+R.at((b+.5)/nb,b)||0,0,1);return out}
  const sec=(S.sections||[]).filter(x=>x&&x.len>0).slice().sort((a,b)=>a.start-b.start),lv=sc=>NI_ARC_SEC.find(q=>q[0].test(String(sc.name||'')));
  if(sec.length>=2&&sec.every(lv)){out.fill(NaN);for(const sc of sec){const q=lv(sc),a=Math.max(0,Math.floor(sc.start)),e=Math.min(nb,Math.ceil(sc.start+sc.len));for(let b=a;b<e;b++)out[b]=q[1]+(q[2]-q[1])*((b+.5-sc.start)/sc.len)}
    /* gaps: a straight line between the neighbours */let pv=-1;for(let b=0;b<=nb;b++){if(b<nb&&isNaN(out[b]))continue;const a=pv<0?(b<nb?out[b]:.5):out[pv],z=b<nb?out[b]:a;for(let i=pv+1;i<b;i++)out[i]=a+(z-a)*((i-pv)/(b-pv));pv=b}
    out.how='sections';return out}
  const P=NI_ARC_TYP;for(let b=0;b<nb;b++){const f=(b+.5)/nb;let i=1;while(i<P.length-1&&P[i][0]<f)i++;const[a0,v0]=P[i-1],[a1,v1]=P[i];out[b]=v0+(v1-v0)*clamp((f-a0)/Math.max(1e-6,a1-a0),0,1)}out.how='length';return out}
/* measure what is missing (NI-3 keeps what it measured before) and redraw as it fills, at most every 0.7 s */
function NI_arcRun(){const A=NI.arc,tok=++A.tok;A.run=NI_sig();A.pend='';A.stale=true;dirty=true;let t0=0;
  NI_anEnsure({prog:()=>{if(tok!==A.tok)return;const n=performance.now();if(n-t0>700){t0=n;A.stale=true;dirty=true}}}).then(r=>{if(tok!==A.tok)return;A.res=r;A.stale=true;dirty=true})}
function NI_arcShow(on){const A=NI.arc;UI.niArc=!!on;saveUI();dirty=true;try{renderHeaders()}catch(e){}
  if(on){A.retry=0;clearTimeout(A.et);A.et=0;NI_arcRun();toast('Energy arc: loudness, tracks playing and brightness over the song. Point at it to see the three apart.')}
  else{A.tok++;clearTimeout(A.et);A.et=0;A.pend='';A.hov=-1;NI_arcTitle('');const mw=document.getElementById('mixWin'),cl=typeof mxsO==='function'&&mxsO().niClash&&mw&&!mw.hidden;if(!(NI.map.w&&!NI.map.w.hidden)&&!cl&&NI.an.q.length)NI_anCancel()}}
function NI_arcCmp(c){UI.niArcCmp=c;saveUI();NI.arc.stale=true;dirty=true}
function NI_arcTitle(t){const A=NI.arc;if(t){if(arr.title!==t)arr.title=t;A.tt=1}else if(A.tt){arr.removeAttribute('title');A.tt=0}}
const NI_ARC_TIP='Energy arc: how much is going on over the song, from three things measured on every track: loudness (cyan), how many tracks play (violet) and brightness (amber). Energy is a made-up blend of them: 55% loudness, 25% tracks playing, 20% brightness. Point at it to see the three apart, click to move the playhead there, right-click to compare with a typical arc.';
function NI_arcDraw(g,w){const A=NI.arc;A.draws++;const sg=NI_sig();
  /* after an edit (or a new project) measure again once it has settled; cancelled measuring (another view closed) is picked up again, 3 times at most */
  if(A.run!==sg&&A.pend!==sg){A.pend=sg;A.retry=0;clearTimeout(A.et);A.et=setTimeout(()=>{A.et=0;if(UI.niArc&&NI_sig()!==A.run)NI_arcRun()},A.run?1200:300)}
  if(A.stale||!A.d){A.d=NI_arcCalc();A.stale=false}const d=A.d;
  if(A.run===sg&&!d.complete&&!NI.an.busy&&!NI.an.q.length&&!A.et&&A.res&&A.retry<3){A.retry++;A.et=setTimeout(()=>{A.et=0;if(UI.niArc)NI_arcRun()},1500)}
  const y=NI_arcY(),h=NI_ARC_H,LK=INS.look(),right=!!UI.tracksRight,xr=right?X0+arrW:w;
  g.fillStyle='#0d0f14';g.fillRect(0,y,w,h);g.fillStyle='rgba(255,255,255,.07)';g.fillRect(0,y+h-1,w,1);
  g.save();g.beginPath();g.rect(X0,y,xr-X0,h-1);g.clip();
  const top=y+5,bh=h-10,Y=v=>top+(1-v)*bh,bx=b=>X0+(b-V.x)*V.ppb,b0=Math.max(0,Math.floor(V.x)-2),b1=Math.min(d.nb,Math.ceil(V.x+(xr-X0)/V.ppb)+2),st=Math.max(1,Math.floor(1/Math.max(V.ppb,1e-6)));
  /* graticule: the middle line, section starts */
  g.fillStyle=LK.gMid;g.fillRect(X0,Math.round(Y(.5)),xr-X0,1);g.fillStyle=LK.gMaj;for(const sc of S.sections||[]){const x=bx(sc.start);if(x>=X0&&x<=xr)g.fillRect(Math.round(x),y,1,h-1)}
  /* not measured yet: hatched */
  for(let b=b0;b<b1;b++){if(!d.unk[b])continue;let e=b;while(e<b1&&d.unk[e])e++;const xa=bx(b),xe=bx(e);g.fillStyle='rgba(255,255,255,.04)';g.fillRect(xa,y+1,xe-xa,h-3);g.strokeStyle='rgba(255,255,255,.1)';g.lineWidth=1;g.beginPath();for(let x=Math.floor(xa/8)*8;x<xe+h;x+=8){g.moveTo(x,y+h-2);g.lineTo(x-h+4,y+2)}g.stroke();b=e}
  /* one value per step (the largest when zoomed out, so a short peak stays visible) */
  const pts=(a,f)=>{const o=[];for(let b=b0;b<b1;b+=st){let m=-1,u=false;for(let i=b;i<Math.min(b1,b+st);i++){if(d.unk[i]){u=true;break}const v=f?f(i):a[i];if(v>m)m=v}o.push(u?null:[bx(b+st/2),m])}return o};
  const stroke=(o,col,lw,dash)=>{g.strokeStyle=col;g.lineWidth=lw;g.setLineDash(dash||[]);g.beginPath();let on=false;for(const p of o){if(!p){on=false;continue}const yy=Y(p[1]);if(on)g.lineTo(p[0],yy);else{g.moveTo(p[0],yy);on=true}}g.stroke();g.setLineDash([])};
  if(!d.nb){g.fillStyle=LK.mut;g.font='10px Inter,system-ui,sans-serif';g.fillText('Nothing to measure yet: add clips and the energy arc follows the song.',X0+10,y+h/2+3)}
  else{const eo=pts(d.E);
    /* energy: filled with a magma ramp from the bottom (dim) to the top (bright), the line on top */
    const gr=g.createLinearGradient(0,top+bh,0,top);gr.addColorStop(0,'rgba(59,15,112,.55)');gr.addColorStop(.35,'rgba(140,41,129,.6)');gr.addColorStop(.6,'rgba(222,73,104,.65)');gr.addColorStop(.82,'rgba(254,159,109,.7)');gr.addColorStop(1,'rgba(252,253,191,.75)');
    g.fillStyle=gr;let run=[];const flush=()=>{if(run.length>1){g.beginPath();g.moveTo(run[0][0],top+bh);for(const p of run)g.lineTo(p[0],Y(p[1]));g.lineTo(run[run.length-1][0],top+bh);g.closePath();g.fill()}run=[]};for(const p of eo){if(!p)flush();else run.push(p)}flush();
    if(d.cmp){const lo=d.lo,hi=Math.max(d.hi,lo+.05);stroke(pts(null,i=>lo+(hi-lo)*d.cmp[i]),NI_ARC_COL.cmp,1,[4,3])}
    stroke(eo,NI_ARC_COL.e,1.2);
    const ing=UI.niArcIng||A.hov>=0;if(ing){stroke(pts(d.ln),NI_ARC_COL.l,1);stroke(pts(d.dn),NI_ARC_COL.d,1);stroke(pts(d.bn),NI_ARC_COL.b,1)}
    /* the read-out where the pointer is */
    if(A.hov>=0&&A.hov<d.nb){const b=A.hov,x=bx(b+.5);g.fillStyle='rgba(255,255,255,.5)';g.fillRect(Math.round(x),y,1,h-1);const w0=NI_bb(b),parts=[[`bar ${w0.bar}.${w0.beat}`,LK.lab]];
      if(d.unk[b])parts.push(['not measured yet',LK.mut]);else if(!d.snd[b])parts.push(['silent',LK.mut]);
      else{parts.push([`energy ${Math.round(100*d.E[b])}`,NI_ARC_COL.e],[INS.fmt(Math.round(d.lu[b]*10)/10,'LUFS'),NI_ARC_COL.l],[`${Math.round(d.dn[b]*d.nT)} of ${d.nT} tracks play`,NI_ARC_COL.d],[`brightness ${INS.hz(d.br[b])}`,NI_ARC_COL.b]);
        if(d.cmp)parts.push([`${UI.niArcCmp==='ref'&&A.ref?A.ref.name:'typical'} ${Math.round(100*(d.lo+(Math.max(d.hi,d.lo+.05)-d.lo)*d.cmp[b]))}`,LK.mut])}
      g.font='500 9.5px '+LK.mono;g.textBaseline='middle';const sep=' · ',sw=g.measureText(sep).width,tw=parts.reduce((a,p)=>a+g.measureText(p[0]).width,0)+sw*(parts.length-1)+10;
      let bxL=x+8;if(bxL+tw>xr-4)bxL=Math.max(X0+2,x-8-tw);g.fillStyle='rgba(8,10,14,.88)';rr(g,bxL,y+3,tw,15,3);g.fill();let tx=bxL+5;
      parts.forEach((p,i)=>{if(i){g.fillStyle=LK.mut;g.fillText(sep,tx,y+11);tx+=sw}g.fillStyle=p[1];g.fillText(p[0],tx,y+11);tx+=g.measureText(p[0]).width});g.textBaseline='alphabetic'}}
  /* top right in the lane: still measuring, or what the dashed line is */
  {const t=d.nb&&!d.complete?`measuring ${Math.round(100*(d.all-d.left)/Math.max(1,d.all))}%`+(NI.an.paused?' (waiting)':''):d.cmp?'- - '+(UI.niArcCmp==='ref'&&A.ref?A.ref.name:'typical arc'):'';
    if(t&&A.hov<0){g.font='9px Inter,system-ui,sans-serif';const tw=g.measureText(t).width+8;g.fillStyle='rgba(8,10,14,.75)';rr(g,xr-tw-4,y+3,tw,13,3);g.fill();g.fillStyle=LK.mut;g.fillText(t,xr-tw,y+12.5)}}
  g.restore();
  /* the label under the track headers, like the tempo lane's, on one line (the header column's caption sits under it) */
  g.fillStyle='#14161c';g.fillRect(right?X0+arrW:0,y,right?HDRW:X0,h-1);const L0=right?X0+arrW+10:10;
  g.fillStyle='#9aa0ae';g.font='600 9px Inter,system-ui,sans-serif';g.fillText('ENERGY',L0,y+14);
  g.font='9px Inter,system-ui,sans-serif';let lx=L0+g.measureText('ENERGY').width+42;for(const[k,t] of[['l','loud'],['d','tracks'],['b','bright']]){g.fillStyle=NI_ARC_COL[k];g.fillRect(lx,y+10,7,2);g.fillStyle=LK.mut;g.fillText(t,lx+10,y+14);lx+=10+g.measureText(t).width+8}}
function NI_arcIn(x,y){if(!NI_arcH())return'';const Y0=NI_arcY();if(y<Y0||y>=Y0+NI_ARC_H)return'';return x>=X0&&x<=X0+arrW?'lane':'label'}
function NI_arcMenu(cx,cy){const A=NI.arc,c=UI.niArcCmp||'typ';openMenu(cx,cy,[{head:'Energy arc: compare with'},
  {chips:[{label:'Nothing',on:c==='none',tip:'No comparison curve',act:()=>NI_arcCmp('none')},
    {label:'Typical psytrance arc',on:c==='typ',tip:'Intro, build, drop, break, build, second drop, outro. Lined up with your sections when they have names like Intro, Build, Drop, Break and Outro, otherwise spread over the song. Drawn within your song\'s own range: compare the shape, not the height',act:()=>NI_arcCmp('typ')},
    {label:A.ref?'Reference: '+A.ref.name:'A reference track',on:c==='ref',dis:!A.ref,tip:A.ref?'The energy arc of this reference, spread over your song':'Reference tracks are not in AudioLab yet. Once they are, their arc can be shown here',act:()=>NI_arcCmp('ref')}]},'-',
  {label:'Always show the three ingredients',sub:'loudness, tracks playing and brightness, not only while pointing',check:!!UI.niArcIng,act:()=>{UI.niArcIng=!UI.niArcIng;saveUI();dirty=true}},
  {label:'Hide the energy arc',act:()=>NI_arcShow(false)}])}
arr.addEventListener('pointermove',e=>{if(!NI_arcH())return;const A=NI.arc,{x,y}=arrPt(e),w=NI_arcIn(x,y);
  if(w==='lane'){const b=Math.floor(V.x+(x-X0)/V.ppb);if(b!==A.hov){A.hov=b;dirty=true}NI_arcTitle(NI_ARC_TIP)}
  else{if(A.hov>=0){A.hov=-1;dirty=true}if(w==='label')NI_arcTitle(NI_ARC_TIP);else NI_arcTitle('')}},true);
arr.addEventListener('pointerleave',()=>{const A=NI.arc;if(A.hov>=0){A.hov=-1;dirty=true}NI_arcTitle('')});
arr.addEventListener('pointerdown',e=>{if(!NI_arcH()||e.button!==0)return;const{x,y}=arrPt(e),w=NI_arcIn(x,y);if(!w)return;e.stopImmediatePropagation();e.preventDefault();if(w!=='lane')return;
  const b=Math.max(0,Math.floor(V.x+(x-X0)/V.ppb));if(play.on){stop();pos=b;start()}else pos=b;syncTransportUI();dirty=true},true);
arr.addEventListener('contextmenu',e=>{if(!NI_arcH())return;const{x,y}=arrPt(e);if(!NI_arcIn(x,y))return;e.preventDefault();e.stopImmediatePropagation();NI_arcMenu(e.clientX,e.clientY)},true);
/* for other lanes: a reference's arc ({name, at(fraction, beat) -> 0 to 1}, or null), and the numbers (for I7 draw the arc, I31 Ask the mix) */
NI.arc.setRef=r=>{NI.arc.ref=r&&typeof r.at==='function'?{name:String(r.name||'Reference'),at:r.at}:null;if(!NI.arc.ref&&UI.niArcCmp==='ref')UI.niArcCmp='typ';NI.arc.stale=true;dirty=true};
NI.arc.data=()=>{if(NI.arc.stale||!NI.arc.d){NI.arc.d=NI_arcCalc();NI.arc.stale=false}return NI.arc.d};NI.arc.show=NI_arcShow;NI.arc.run=NI_arcRun;
NI_HOOKS.energyArc=NI.arc;
window.NI_SETTINGS=window.NI_SETTINGS||[];
NI_SETTINGS.push({id:'ni.energyArc',label:'Energy arc under the sections',page:'Arrangement',block:'View',scope:'app',key:'niArc',default:false,help:'A thin curve of loudness, tracks playing and brightness over the song, measured in the background.',search:['energy','arc','curve','loudness','density','brightness','shape','song']},
  {id:'ni.energyArcCompare',label:'Energy arc: compare with',page:'Arrangement',block:'View',scope:'app',key:'niArcCmp',default:'typ',values:['none','typ','ref'],help:'A dashed curve: a typical psytrance arc, or a reference track\'s arc once reference tracks exist.',search:['energy','arc','reference','typical','psytrance','compare']},
  {id:'ni.energyArcIngredients',label:'Energy arc: always show the three ingredients',page:'Arrangement',block:'View',scope:'app',key:'niArcIng',default:false,help:'Loudness, tracks playing and brightness as three thin lines, not only while pointing at the arc.',search:['energy','arc','ingredients','loudness','density','brightness']});
/* ===== end of lane D NI-6 ===== */
"""
A4 = "/* ===== end of lane D NI-5b ===== */\n"
s = rep(s, A4, A4 + JS.lstrip('\n'))
open(P, 'w', encoding='utf-8').write(s)
print('NI-6 applied')
