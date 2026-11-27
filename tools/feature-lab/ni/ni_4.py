"""Task NI-4 (lane D): I1 frequency map of the whole song, part 2: the view (NF4).
Edit script with unique asserted anchors (needs NI-3 in the file), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_4.py [index.html]
Adds:
  - a window "Frequency map" (#niMap, the app's fwin: moves, resizes, remembers its place): time left to right over the whole song,
    frequency bottom to top (log, 20 Hz to 20 kHz, the 61 bands of NI-3), each cell in the colour of the track that owns the most energy
    there, brightness by level; with more than 12 tracks the colours follow the groups (switchable); section names on top; a legend of the
    owners (most cells first); a one-track layer (the rest grey, that track glowing by its own level); hover read-out (bar and beat,
    frequency with INS.hz, the owner and the runner-up with their levels); click to move the playhead there and select the owner
  - drawn once per change of the analysis or of the window size (NI.an progress, throttled), never per frame; a thin playhead marker moved
    by a 250 ms check only while the window is open and the song plays; the analysis (NI.an.ensure) starts when the window opens and is
    cancelled when it closes; a project edit re-measures in the background
  - command ni.freqMap; NI.map (own(beat, band), draw(), open(), close())
"""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane D (task NI-4)'
if MARK in s:
    print('NI-4 already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-3 ===== */' in s, 'NI-3 must be in the file first'
assert 'const INS={' in s, 'lane E IN-A must be in the file first'

def put(s, anchor, new, before=True):
    n = s.count(anchor)
    assert n == 1, (anchor[:60], n)
    return s.replace(anchor, new + anchor if before else anchor + new)

# 1. the command, after ni.clipExplain
A1 = "run:()=>NI_clipCard()},"
s = put(s, A1, "\n {id:'ni.freqMap',g:'view',l:'Frequency map of the whole song',d:'',ic:'M3 17V3M3 17h14M6 14l3-5 3 3 4-7',run:()=>NI_mapOpen()},", before=False)

# 2. CSS
CSS = r"""/* lane D (task NI-4): the frequency map window. Instrument look: drafting grid, mono numbers, track colours carry the meaning */
#niMap .fwb{flex-direction:column;gap:6px;padding:6px 8px 8px}
#niMap .nimt{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:var(--fs1);color:var(--mut)}
#niMap .nimt select{min-height:22px;font-size:var(--fs1);padding:0 4px;max-width:180px}
#niMap .nimt button{min-height:22px;padding:0 8px;font-size:var(--fs1)}
#niMap .nimst{margin-left:auto;font-variant-numeric:tabular-nums;white-space:nowrap}
#niMap .nimcv{position:relative;flex:1;min-height:120px}
#niMap .nimcv canvas{position:absolute;inset:0;width:100%;height:100%;display:block;cursor:crosshair;border-radius:6px;background:#05070b}
#niMap .nimph{position:absolute;top:0;bottom:0;width:1px;background:#3ecf8e;box-shadow:0 0 4px #3ecf8e;pointer-events:none;left:0}
#niMap .nimph[hidden]{display:none}
#niMap .nimro{font:var(--fw5) var(--fs1)/1.3 var(--ffu);font-variant-numeric:tabular-nums;color:#cfe6ff;min-height:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#niMap .nimlg{display:flex;flex-wrap:wrap;gap:4px;max-height:48px;overflow:auto}
#niMap .nimlg button{display:flex;align-items:center;gap:4px;min-height:20px;height:20px;padding:0 7px;border-radius:10px;font-size:var(--fs1);background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);box-shadow:none}
#niMap .nimlg button i{width:8px;height:8px;border-radius:2px;background:var(--c);flex:none}
#niMap .nimlg button.on{background:rgba(255,255,255,.16);border-color:var(--c)}
"""
A2 = ".dacv{display:flex;"
s = put(s, A2, CSS)

# 2b. NI-3's key leaves out the group a track sits in (a render with only does not pass through the group), so grouping does not re-measure
A2b = "const NI_AN_TDROP=['id','name','color','col','mute','solo','sel','open','h','fold','arm','mon','clips']"
assert s.count(A2b) == 1, 'NI-3 key list'
s = s.replace(A2b, "const NI_AN_TDROP=['id','name','color','col','mute','solo','sel','open','h','fold','arm','mon','clips','grp']")

# 3. JS after NI-3
JS = r"""
/* ===== lane D (task NI-4): I1 frequency map of the whole song, part 2: the view =====
   Reads NI.an (NI-3). The grid of owners is worked out once per change of the analysis (a few ms for the whole song, from the stored bytes
   through a lookup table), the picture is drawn into the window's canvas once per change or resize. Nothing per frame; while the song plays
   a 250 ms check moves a thin playhead marker (a CSS position, no redraw). The look values, the frequency read-out and the number formatter
   come from lane E's INS. */
NI.map={w:null,g:null,tok:0,dirty:true,layer:'',col:'auto',raf:0,ph:0,last:'',busy:false,res:null,hover:null};
const NI_MAP_P=(()=>{const a=new Float64Array(256);for(let i=0;i<256;i++)a[i]=i?Math.pow(10,(i/2-127)/10):0;return a})();/* stored byte -> power */
/* the piece of a track (raw bytes), '' when silent there, null when not measured yet */
function NI_anPiece(t,p){const k=NI_anKey(t,p);if(k==='')return'';return NI.an.mem.get(k)||null}
/* colour of a track in the map: its own, or its group's (by bus) */
function NI_mapCol(t,byGrp){const g=byGrp&&grpOf(t);return(g&&g.color)||t.color||'#8b8b97'}
const NI_hex=c=>{const m=/^#?([0-9a-f]{6})$/i.exec(String(c||''));if(!m)return[139,139,151];const v=parseInt(m[1],16);return[v>>16&255,v>>8&255,v&255]};
/* the grid: per beat and band, the owner (index into tracks, -1 silent, -2 not measured) and the total level in dB */
function NI_mapGrid(){const L=NI_anTracks(),nb=Math.max(1,Math.ceil(NI_anEnd())),B=NI_AN_NB,own=new Int16Array(nb*B).fill(-1),lvl=new Float32Array(nb*B).fill(-140),best=new Float64Array(nb*B),tot=new Float64Array(nb*B),unk=new Uint8Array(nb),cnt=new Uint32Array(L.length);
  const np=Math.ceil(nb/NI_AN_SEG);let done=0,all=0;
  L.forEach((t,ti)=>{for(let p=0;p<np;p++){const r=NI_anPiece(t,p);all++;if(r==='')continue;if(!r){for(let j=0;j<NI_AN_SEG&&p*NI_AN_SEG+j<nb;j++)unk[p*NI_AN_SEG+j]=1;continue}done++;
    for(let j=0;j<r.nb;j++){const b=p*NI_AN_SEG+j;if(b>=nb)break;if(!r.play[j])continue;const o=b*B,q=j*B;for(let k=0;k<B;k++){const v=NI_MAP_P[r.mid[q+k]]+NI_MAP_P[r.side[q+k]];if(v<=1e-12)continue;tot[o+k]+=v;if(v>best[o+k]){best[o+k]=v;own[o+k]=ti}}}}});
  for(let i=0;i<own.length;i++){if(tot[i]>0){lvl[i]=10*Math.log10(tot[i]);if(lvl[i]<-90)own[i]=-1;else if(lvl[i]>-60)cnt[own[i]]++}else if(unk[Math.floor(i/B)])own[i]=-2}
  return{L,nb,B,own,lvl,best,cnt,done,all,complete:!unk.some(x=>x)}}
function NI_mapOpen(){const M=NI.map,z=ZOOM,vw=innerWidth/z,vh=innerHeight/z;
  const w=fwin('niMap','Frequency map',{x:Math.round(vw*.08),y:Math.round(vh*.12),w:Math.round(Math.min(1100,vw*.84)),h:Math.round(Math.min(440,vh*.6))},()=>NI_mapClose(true));
  if(!M.w||M.w!==w){M.w=w;w.querySelector('.fwt').title='The whole song: time left to right, frequency bottom to top. Each spot shows the track that is loudest there';
    const fwc=w.querySelector('.fwc');if(fwc)fwc.title='Close the frequency map (the measuring stops)';
    w.querySelector('.fwb').innerHTML=`<div class="nimt"><label title="Show every track, or one track glowing over the rest">Layer <select data-nm="layer"></select></label>
      <label title="Colour each spot by its track, or by the group (bus) the track is in. Auto: by group when the song has more than 12 tracks">Colours <select data-nm="col"><option value="auto">Auto</option><option value="trk">By track</option><option value="grp">By group</option></select></label>
      <span class="nimst" aria-live="polite"></span></div>
      <div class="nimcv"><canvas title="Point at a spot to read its time, frequency and owner. Click to move the playhead there and select that track"></canvas><i class="nimph" hidden></i></div>
      <div class="nimro"></div><div class="nimlg"></div>`;
    const q=s=>w.querySelector(s);q('[data-nm="layer"]').onchange=e=>{M.layer=e.target.value;NI_mapDraw()};q('[data-nm="col"]').onchange=e=>{M.col=e.target.value;M.dirty=true;NI_mapDraw()};
    const cv=q('canvas');cv.addEventListener('pointermove',e=>NI_mapHover(e));cv.addEventListener('pointerleave',()=>{q('.nimro').textContent='';M.hover=null});cv.addEventListener('click',e=>NI_mapClick(e));
    q('.nimlg').addEventListener('click',e=>{const b=e.target.closest('[data-id]');if(!b)return;M.layer=M.layer===b.dataset.id?'':b.dataset.id;NI_mapDraw()});
    if(window.ResizeObserver)new ResizeObserver(()=>{if(!w.hidden)NI_mapDraw()}).observe(cv)}
  M.dirty=true;NI_mapRun();NI_mapDraw();clearInterval(M.ph);M.ph=setInterval(NI_mapTick,250);return w}
function NI_mapClose(fromWin){const M=NI.map;clearInterval(M.ph);M.ph=0;M.tok++;if(NI.an.q.length)NI_anCancel();if(!fromWin&&M.w)M.w.hidden=true}
/* measure the whole song (or what changed); redraw at most every 600 ms while it fills */
function NI_mapRun(){const M=NI.map,tok=++M.tok;M.last=NI_sig();let t0=0;
  NI_anEnsure({prog:()=>{M.dirty=true;const n=performance.now();if(n-t0>600){t0=n;if(tok===M.tok)NI_mapDraw()}}}).then(r=>{if(tok!==M.tok)return;M.res=r;M.dirty=true;NI_mapDraw()})}
/* while open: follow edits (measure again after 1 s of quiet) and move the playhead marker while playing */
function NI_mapTick(){const M=NI.map,w=M.w;if(!w||w.hidden){clearInterval(M.ph);M.ph=0;return}
  const sg=NI_sig();if(sg!==M.last){if(!M.edit||M.edit.sg!==sg)M.edit={sg,t:performance.now()};else if(performance.now()-M.edit.t>1000){M.edit=null;M.dirty=true;NI_mapRun();NI_mapDraw()}}
  const ph=w.querySelector('.nimph'),G=M.geo;if(!G||!play.on){ph.hidden=true;return}const b=curDisp();ph.hidden=!(b>=0&&b<=G.nb);ph.style.left=(G.x0+b/G.nb*G.pw).toFixed(1)+'px'}
function NI_mapDraw(){const M=NI.map,w=M.w;if(!w||w.hidden)return;const cv=w.querySelector('canvas');if(!cv.clientWidth)return;
  if(M.dirty||!M.g){M.g=NI_mapGrid();M.dirty=false;M.img=null}const G=M.g,{g,w:W,h:H}=fit(cv),L=INS.look(),byGrp=M.col==='grp'||(M.col==='auto'&&G.L.length>12);
  const st=w.querySelector('.nimst'),run=NI.an.status();st.textContent=G.complete?`${G.L.length} tracks · ${Math.round(G.nb)} beats`+(M.res&&M.res.cancelled?' · stopped':''):`Measuring: ${G.all-NI_mapLeft(G)} of ${G.all} pieces done…`+(run.paused?' (waiting: '+run.paused+')':'');
  st.title='The map is measured in the background, piece by piece, and remembered for next time. Pieces where a track is silent are not measured';
  /* the layer select and the legend */
  const grs=S.tracks.filter(t=>t.kind==='group'&&G.L.some(x=>grpOf(x)===t)),ls=w.querySelector('[data-nm="layer"]'),opts='<option value="">All tracks</option>'+(grs.length?'<optgroup label="Groups">'+grs.map(t=>`<option value="${esc(t.id)}">${esc(t.name)} (group)</option>`).join('')+'</optgroup><optgroup label="Tracks">':'')+G.L.map(t=>`<option value="${esc(t.id)}">${esc(t.name)}</option>`).join('')+(grs.length?'</optgroup>':'');if(ls._o!==opts){ls.innerHTML=opts;ls._o=opts}ls.value=M.layer||'';
  w.querySelector('[data-nm="col"]').value=M.col;
  const lg=w.querySelector('.nimlg'),agg=new Map();G.L.forEach((t,i)=>{if(!G.cnt[i])return;const g=byGrp&&grpOf(t),k=g||t,e=agg.get(k)||{t:k,n:0,grp:!!g};e.n+=G.cnt[i];agg.set(k,e)});
  const ord=[...agg.values()].sort((a,b)=>b.n-a.n),tot=ord.reduce((a,x)=>a+x.n,0)||1;
  lg.innerHTML=ord.map(e=>`<button data-id="${esc(e.t.id)}" class="${e.t.id===M.layer?'on':''}" style="--c:${e.grp?(e.t.color||'#8b8b97'):NI_mapCol(e.t,byGrp)}" title="${esc(e.t.name)}${e.grp?' (group)':''} owns ${Math.round(100*e.n/tot)}% of the sounding spots. Click to show it alone, click again for all"><i></i>${esc(e.t.name)}</button>`).join('');
  /* geometry: frequency axis on the left, sections on top, beats under the map */
  const x0=34,y0=16,pw=Math.max(10,W-x0-6),ph=Math.max(10,H-y0-14);M.geo={x0,y0,pw,ph,nb:G.nb,W,H};
  g.clearRect(0,0,W,H);g.fillStyle='#05070b';g.fillRect(0,0,W,H);
  /* the cells, once into an image of nb x 61, then scaled */
  const key=M.layer+'|'+byGrp;if(!M.img||M.img.key!==key){const c=document.createElement('canvas');c.width=G.nb;c.height=G.B;const cg=c.getContext('2d'),im=cg.createImageData(G.nb,G.B),d=im.data,cols=G.L.map(t=>NI_hex(NI_mapCol(t,byGrp))),LS=M.layer?G.L.map((t,i)=>t.id===M.layer||(grpOf(t)||{}).id===M.layer?i:-1).filter(i=>i>=0):[],li=LS.length?LS[0]:-1,lgc=li>=0?NI_hex((trkById(M.layer)||{}).color||NI_mapCol(G.L[li],byGrp)):null;
    for(let b=0;b<G.nb;b++)for(let k=0;k<G.B;k++){const i=b*G.B+k,o=((G.B-1-k)*G.nb+b)*4,ow=G.own[i];let r=0,gg=0,bb=0,a=255;
      if(ow===-2){const h=(b+k)%4<2;r=gg=bb=h?16:10}else if(ow>=0||li>=0){const lv=G.lvl[i],br=clamp((lv+84)/66,0,1);
        if(li<0){const c=cols[ow],f=.12+.88*Math.pow(br,1.15);r=c[0]*f;gg=c[1]*f;bb=c[2]*f}
        else{/* one track: its own level glows in its colour, the rest is dim grey */let own=0;const j=b%NI_AN_SEG;for(const ti of LS){const r0=NI_anPiece(G.L[ti],Math.floor(b/NI_AN_SEG));if(r0&&r0.play[j])own+=NI_MAP_P[r0.mid[j*G.B+k]]+NI_MAP_P[r0.side[j*G.B+k]]}
          const ol=own>1e-12?10*Math.log10(own):-140,ob=clamp((ol+84)/66,0,1),grey=ow>=0?18+40*br:0,c=lgc;
          if(ob>0){const f=.15+.85*Math.pow(ob,1.1);r=Math.max(grey,c[0]*f);gg=Math.max(grey,c[1]*f);bb=Math.max(grey,c[2]*f)}else{r=gg=bb=grey}}}
      d[o]=r;d[o+1]=gg;d[o+2]=bb;d[o+3]=a}
    cg.putImageData(im,0,0);M.img={key,c}}
  g.imageSmoothingEnabled=false;g.drawImage(M.img.c,x0,y0,pw,ph);g.imageSmoothingEnabled=true;
  /* frequency grid and labels (log, decades long, 2 and 5 mid); the 61 bands run from 20 Hz to 20.5 kHz */
  const lo=NI.an.bands[0]*Math.pow(2,-1/12),hi=NI.an.bands[NI_AN_NB-1]*Math.pow(2,1/12),FY=f=>y0+ph*(1-Math.log(f/lo)/Math.log(hi/lo));M.geo.FY=FY;M.geo.lo=lo;M.geo.hi=hi;
  g.lineWidth=1;g.font='8px '+L.mono;g.textBaseline='middle';g.textAlign='right';
  for(const f of[20,50,100,200,500,1000,2000,5000,10000,20000]){const y=Math.round(FY(f))+.5,dec=[100,1000,10000].includes(f);g.strokeStyle=dec?'rgba(255,255,255,.16)':'rgba(255,255,255,.07)';g.beginPath();g.moveTo(x0,y);g.lineTo(x0+pw,y);g.stroke();
    g.fillStyle=dec?L.lab:L.mut;g.fillText(f>=1000?f/1000+'k':String(f),x0-4,y)}
  g.save();g.translate(8,y0+ph/2);g.rotate(-Math.PI/2);g.textAlign='center';g.fillStyle=L.mut;g.fillText('Hz',0,0);g.restore();
  /* bars under the map, sections on top */
  const X=b=>x0+b/G.nb*pw;M.geo.step=[1,2,4,8,16,32,64,128].find(k=>k*4/G.nb*pw>=34)||256;g.textAlign='center';g.textBaseline='top';g.fillStyle=L.mut;let lastX=-1e9;
  for(let b=0;b<G.nb;b+=4){const P=barPos(b+1e-3);if(Math.abs(P.start-b)>1e-6)continue;const bar=P.bar+1,x=X(b);if((bar-1)%M.geo.step)continue;if(x-lastX<24)continue;lastX=x;
    g.strokeStyle='rgba(255,255,255,.12)';g.beginPath();g.moveTo(Math.round(x)+.5,y0+ph);g.lineTo(Math.round(x)+.5,y0+ph+3);g.stroke();g.fillText(String(bar),x,y0+ph+4)}
  g.textBaseline='middle';g.textAlign='left';g.font='600 9px '+(getComputedStyle(document.body).getPropertyValue('--ffu').trim()||'sans-serif');
  for(const sc of S.sections||[]){const xa=X(sc.start),xb=X(sc.start+sc.len);if(xb<x0||xa>x0+pw)continue;g.fillStyle=sc.color||'#888';g.globalAlpha=.85;g.fillRect(xa,2,Math.max(1,xb-xa-1),3);g.globalAlpha=1;
    g.strokeStyle='rgba(255,255,255,.18)';g.beginPath();g.moveTo(Math.round(xa)+.5,y0);g.lineTo(Math.round(xa)+.5,y0+ph);g.stroke();
    const nm=String(sc.name||''),tw=g.measureText(nm).width;if(tw<xb-xa-4){g.fillStyle='rgba(230,236,245,.85)';g.fillText(nm,xa+3,10)}}
  if(!G.L.length){g.fillStyle=L.mut;g.textAlign='center';g.fillText('No tracks to measure.',x0+pw/2,y0+ph/2)}}
function NI_mapLeft(G){let n=0;for(const t of G.L){const np=Math.ceil(G.nb/NI_AN_SEG);for(let p=0;p<np;p++)if(NI_anPiece(t,p)===null)n++}return n}
/* where the pointer is: beat, band, owner */
function NI_mapAt(e){const M=NI.map,G=M.geo,cv=M.w.querySelector('canvas'),r=cv.getBoundingClientRect();if(!G)return null;const x=(e.clientX-r.left)/r.width*G.W,y=(e.clientY-r.top)/r.height*G.H;
  if(x<G.x0||x>G.x0+G.pw||y<G.y0||y>G.y0+G.ph)return null;const b=Math.min(G.nb-1,Math.max(0,Math.floor((x-G.x0)/G.pw*G.nb))),f=G.lo*Math.pow(G.hi/G.lo,1-(y-G.y0)/G.ph),k=clamp(Math.round(6*Math.log2(f/20)),0,NI_AN_NB-1);
  return{b,bt:(x-G.x0)/G.pw*G.nb,f,k}}
/* the owner and the runner-up at a beat and band, with levels */
function NI_mapOwn(b,k){const G=NI.map.g||NI_mapGrid(),out=[];G.L.forEach(t=>{const r=NI_anPiece(t,Math.floor(b/NI_AN_SEG)),j=b%NI_AN_SEG;if(!r||!r.play[j])return;const v=NI_MAP_P[r.mid[j*NI_AN_NB+k]]+NI_MAP_P[r.side[j*NI_AN_NB+k]];if(v>1e-12)out.push({t,id:t.id,name:t.name,db:10*Math.log10(v)})});
  out.sort((a,c)=>c.db-a.db);return out.filter(x=>x.db>-90)}
function NI_mapHover(e){const M=NI.map,a=NI_mapAt(e),ro=M.w.querySelector('.nimro');if(!a){ro.textContent='';return}const o=NI_mapOwn(a.b,a.k),w=NI_bb(a.b),bd=NI.an.bands[a.k];
  const f=INS.hz(bd,{note:true}).replace('  ',' · ');let s=`bar ${w.bar}.${w.beat} · ${f}`;if(M.g&&M.g.own[a.b*NI_AN_NB+a.k]===-2)s+=' · not measured yet';else if(!o.length)s+=' · silent';else{s+=` · ${o[0].name} ${INS.fmt(o[0].db,'dB')}`;if(o[1])s+=`, then ${o[1].name} ${INS.fmt(o[1].db,'dB')}`}ro.textContent=s;M.hover=a}
function NI_mapClick(e){const a=NI_mapAt(e);if(!a)return;const o=NI_mapOwn(a.b,a.k),M=NI.map,lt=M.layer&&trkById(M.layer),inL=lt&&lt.kind==='group'?o.find(x=>grpOf(x.t)===lt):null,tid=lt?(lt.kind==='group'?(inL&&inL.id):lt.id):(o[0]&&o[0].id);
  if(play.on){stop();pos=a.b;start()}else{pos=a.b}syncTransportUI();dirty=true;if(tid&&trkById(tid)){selectTrack(tid);try{renderHeaders()}catch(_){}}
  const w=NI_bb(a.b);toast(tid?`Bar ${w.bar}.${w.beat}: ${trkById(tid).name} selected.`:`Bar ${w.bar}.${w.beat}.`)}
NI.map.open=NI_mapOpen;NI.map.close=()=>NI_mapClose(false);NI.map.draw=NI_mapDraw;NI.map.own=NI_mapOwn;NI.map.grid=()=>NI.map.g||NI_mapGrid();
/* ===== end of lane D NI-4 ===== */"""
A3 = "/* ===== end of lane D NI-3 ===== */"
s = put(s, A3, JS, before=False)
open(P, 'w', encoding='utf-8').write(s)
print('NI-4 applied')
