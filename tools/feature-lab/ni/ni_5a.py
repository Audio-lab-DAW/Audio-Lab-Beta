"""Task NI-5a (lane D): I12 masking cables, part 1: the clashes (NF5).
Edit script with unique asserted anchors (needs NI-3 and NI-4 in the file), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_5a.py [index.html]
Adds:
  - NI_clashAt(beat): the clashes at a beat, read from NI-3's per-beat cache (no live analysis): per track the energy (mid plus side) in
    1/3-octave bands (two of NI-3's 1/6-octave bands each); the 12 loudest tracks that play at that beat are compared in pairs (or, with the
    cable lane's "Selected only", the selected track against every other); a band clashes when both tracks are over the floor there (36 dB
    under the loudest band at that beat, between -80 and -50 dB) and within 12 dB of each other; the strength of a pair is its strongest band
    (how far the quieter one is over the floor, less for a bigger gap); the
    band range around it is given as "45 to 70 Hz"; at most 8 cables, the strongest first
  - a "Clashes" switch in the mixer's cable legend (UI.mxs.niClash); with it on, the clashes at the playhead are drawn in the cable lane as
    magenta cables between the two strips, thickness the strength, labelled "Bass vs Kick, 45 to 70 Hz", with a tooltip; click: a small card
    with the numbers (NI_clashPop, NI_HOOKS.clashPop for the fixes of NI-5b)
  - a 250 ms check only while the mixer is open with the cable lane and Clashes on: it works only when the beat, the project or the analysis
    changed, and draws only when the list of clashes changed; missing pieces are measured in the background (NI.an.ensure), the next piece
    ahead while playing; nothing per frame, nothing in the audio path; the normal cables, their legend and "Selected only" unchanged
  - command ni.clashes (opens the mixer, turns the cable lane and Clashes on); NI.clash (at, draw, list)
  - keeps NI-1b's clip note in the peak box's tooltip, which lane E's meters (v0.257) rewrite twice a second
"""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane D (task NI-5a)'
if MARK in s:
    print('NI-5a already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-4 ===== */' in s, 'NI-4 must be in the file first'

def put(s, anchor, new, before=True):
    n = s.count(anchor)
    assert n == 1, (anchor[:60], n)
    return s.replace(anchor, new + anchor if before else anchor + new)

# 1. the command, after ni.freqMap
A1 = "run:()=>NI_mapOpen()},"
s = put(s, A1, "\n {id:'ni.clashes',g:'view',l:'Show clashes between tracks in the mixer',d:'',ic:'M4 6c4 8 8 8 12 0M4 14c4-8 8-8 12 0',run:()=>NI_clashCmd()},", before=False)

# 2. CSS
CSS = r"""/* lane D (task NI-5a): clash cables in the mixer's cable lane (their own colour, magenta, never red against green) */
#mixWin svg.cabs .nicc{fill:none;stroke:#e86bff;stroke-linecap:round;opacity:.9}
#mixWin svg.cabs .nicb{fill:none;stroke:rgba(0,0,0,.6);stroke-linecap:round}
#mixWin svg.cabs .nicl{font:var(--fw6) var(--fs1) var(--ffu);fill:#f3c4ff;paint-order:stroke;stroke:#0c0d11;stroke-width:3px;stroke-linejoin:round;pointer-events:none;font-variant-numeric:tabular-nums}
#mixWin svg.cabs .nich{fill:none;stroke:transparent;stroke-width:12px;pointer-events:stroke;cursor:pointer}
#mixWin svg.cabs .nicg.hov .nicc{opacity:.35}#mixWin svg.cabs .nicg .nicc.hi{opacity:1;filter:drop-shadow(0 0 4px #e86bff)}
#mixWin .cablg em{overflow:hidden;text-overflow:ellipsis;min-width:0}#mixWin .cablg em[hidden]{display:none}#mixWin .cablg button.niclb{gap:5px}#mixWin .cablg button.niclb b{font-weight:var(--fw5);color:#f3c4ff;font-variant-numeric:tabular-nums}
#niClashPop{position:fixed;z-index:9795;min-width:220px;max-width:min(320px,calc(100vw - 16px));padding:10px 12px 12px;border-radius:var(--ov-r-card,9px);background:rgba(19,20,27,.98);border:1px solid rgba(232,107,255,.4);box-shadow:0 18px 50px rgba(0,0,0,.65);color:#d9dce6;font-size:var(--fs2);line-height:1.45}
#niClashPop h4{margin:0 0 4px;font-size:var(--fs2);font-weight:var(--fw6);color:#f3c4ff}
#niClashPop p{margin:0 0 6px;color:var(--mut)}#niClashPop .nicpr{display:flex;justify-content:space-between;gap:10px;font-variant-numeric:tabular-nums}
#niClashPop .nicpr i{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:5px;background:var(--c)}
#niClashPop .nicpb{display:flex;gap:6px;justify-content:flex-end;margin-top:8px}#niClashPop .nicpb button{min-height:24px;padding:0 9px}
"""
A2 = ".dacv{display:flex;"
s = put(s, A2, CSS)

# 3. JS after NI-4
JS = r"""
/* ===== lane D (task NI-5a): I12 masking cables, part 1: the clashes =====
   Read from NI-3's per-beat cache at the playhead (no live analysis, nothing in the audio path). Drawn into the cable lane's SVG as its
   own group after the normal cables; the normal cables, their legend and "Selected only" are not changed. A 250 ms check runs only while
   the mixer is open with the cable lane and Clashes on, and does work only when the beat, the project or the analysis changed. */
NI.clash={tm:0,beat:null,sig:'',rev:-1,list:[],drawn:'',want:'',meas:false};
const NI_CL_FLOOR=-50,NI_CL_GAP=12,NI_CL_MAX=8,NI_CL_TRK=12,NI_CL_COL='#e86bff';
const NI_CL_NB=Math.ceil(NI_AN_NB/2);/* 1/3-octave bands: two 1/6-octave bands each */
const NI_clOn=()=>!!mxsO().niClash&&cabOn();
/* the edges of a 1/3-octave band, in Hz */
function NI_clEdges(m){const k0=2*m,k1=Math.min(NI_AN_NB-1,2*m+1);return[20*Math.pow(2,(k0-.5)/6),20*Math.pow(2,(k1+.5)/6)]}
const NI_clHz=f=>f>=1000?(Math.round(f/100)/10).toString().replace(/\.0$/,'')+' kHz':Math.round(f)+' Hz';
function NI_clRange(m0,m1){const a=NI_clEdges(m0)[0],b=NI_clEdges(m1)[1],fa=f=>f>=1000?(Math.round(f/100)/10).toString().replace(/\.0$/,''):String(Math.round(f));return(b>=1000&&a>=1000?fa(a)+' to '+fa(b)+' kHz':fa(a)+(a>=1000?' kHz':'')+' to '+NI_clHz(b))}
/* per track at a beat: 1/3-octave levels in dB (Float32Array) and loudness; null when a piece is missing, '' when silent there */
function NI_clTrack(t,b){const p=Math.floor(b/NI_AN_SEG),r=NI_anPiece(t,p);if(r==='')return'';if(!r)return null;const j=b-p*NI_AN_SEG;if(j>=r.nb||!r.play[j])return'';
  const o=j*NI_AN_NB,L=new Float32Array(NI_CL_NB);for(let m=0;m<NI_CL_NB;m++){let v=0;for(let k=2*m;k<=2*m+1&&k<NI_AN_NB;k++)v+=NI_MAP_P[r.mid[o+k]]+NI_MAP_P[r.side[o+k]];L[m]=v>1e-14?10*Math.log10(v):-140}
  return{L,loud:r.loud[j]}}
/* the clashes at a beat: {list:[{a,b,m0,m1,mk,s,la,lb,gap}], missing:[tracks], beat} */
function NI_clashAt(beat){const b=Math.max(0,Math.floor(beat)),all=NI_anTracks(),D=[],missing=[];
  for(const t of all){const d=NI_clTrack(t,b);if(d===null){missing.push(t);continue}if(d)D.push({t,d})}
  const o=mxsO(),st=o.cabSel&&selT&&selT!=='__m'?trkById(selT):null,sel=st?D.find(x=>x.t===st):null;
  if(st&&!sel)return{list:[],missing,beat:b,tracks:0};/* Selected only, and the selected channel is silent here (or a group or return) */
  let A;if(sel)A=D;else{A=D.slice().sort((x,y)=>y.d.loud-x.d.loud).slice(0,NI_CL_TRK)}
  /* the floor follows the mix: 36 dB under the loudest band of the compared tracks at this beat, never above -50 dB nor below -80 dB */
  let top=-140;for(const x of A)for(let m=0;m<NI_CL_NB;m++)if(x.d.L[m]>top)top=x.d.L[m];const FL=clamp(top-36,-80,NI_CL_FLOOR);
  const out=[];
  for(let i=0;i<A.length;i++)for(let j=i+1;j<A.length;j++){const x=A[i],y=A[j];if(sel&&x!==sel&&y!==sel)continue;
    const S1=new Float32Array(NI_CL_NB);let best=0,mk=-1;
    for(let m=0;m<NI_CL_NB;m++){const la=x.d.L[m],lb=y.d.L[m],lo=Math.min(la,lb),g=Math.abs(la-lb);if(lo<FL||g>NI_CL_GAP){S1[m]=0;continue}const v=(lo-FL)*(1-g/(2*NI_CL_GAP));S1[m]=v;if(v>best){best=v;mk=m}}
    if(mk<0||best<4)continue;let m0=mk,m1=mk;while(m0>0&&S1[m0-1]>=best*.5)m0--;while(m1<NI_CL_NB-1&&S1[m1+1]>=best*.5)m1++;
    const la=x.d.L[mk],lb=y.d.L[mk],[a,c]=la>=lb?[x,y]:[y,x];
    out.push({a:a.t,b:c.t,m0,m1,mk,s:best,la:Math.max(la,lb),lb:Math.min(la,lb),gap:Math.abs(la-lb),range:NI_clRange(m0,m1)})}
  out.sort((p,q)=>q.s-p.s);return{list:out.slice(0,NI_CL_MAX),missing,beat:b,tracks:A.length,floor:FL}}
/* the beat the check reads: the playhead while playing, else where it stands */
const NI_clBeat=()=>Math.max(0,Math.floor(play.on?curDisp():pos));
function NI_clRun(){const C=NI.clash;clearInterval(C.tm);C.tm=0;if(!NI_clOn())return;const w=document.getElementById('mixWin');if(!w||w.hidden)return;C.tm=setInterval(NI_clTick,250);NI_clTick(true)}
function NI_clStop(){const C=NI.clash;clearInterval(C.tm);C.tm=0;C.beat=null;C.list=[];C.drawn='';const sv=document.querySelector('#mixWin .mxs>svg.cabs .nicg');if(sv)sv.remove();NI_clPopClose()}
function NI_clTick(force){const C=NI.clash,w=document.getElementById('mixWin');if(!w||w.hidden||!NI_clOn()){NI_clStop();return}
  const b=NI_clBeat(),sg=NI_sig()+'|'+(mxsO().cabSel?selT:''),rev=NI.an.stats.renders+NI.an.stats.idb;
  if(!force&&b===C.beat&&sg===C.sig&&rev===C.rev)return;C.beat=b;C.sig=sg;C.rev=rev;
  const R=NI_clashAt(b);C.list=R.list;C.meas=R.missing.length>0;
  /* missing pieces: measured in the background (once per piece), and the next piece ahead while playing */
  const p=Math.floor(b/NI_AN_SEG),wk=p+'|'+NI_sig();
  if(R.missing.length&&C.want!==wk){C.want=wk;NI_anEnsure({tracks:R.missing,b0:p*NI_AN_SEG,b1:(p+1)*NI_AN_SEG}).then(()=>{if(C.want===wk)C.want='';if(NI_clOn())NI_clTick(true)})}
  else if(play.on&&b-p*NI_AN_SEG>=12){const nk=(p+1)+'|'+NI_sig();if(C.ahead!==nk){C.ahead=nk;NI_anEnsure({b0:(p+1)*NI_AN_SEG,b1:(p+2)*NI_AN_SEG})}}
  NI_clDraw()}
/* the clash cables, as one group in the cable lane's SVG */
function NI_clDraw(){const C=NI.clash,w=document.getElementById('mixWin');const G=CAB.G,sv=w&&w.querySelector('.mxs>svg.cabs');if(!sv||!G){C.drawn='';return}
  const key=C.list.map(c=>c.a.id+c.b.id+c.m0+'-'+c.m1+':'+Math.round(c.s)).join('|')+'|'+(G.sy2??G.sy)+'|'+G.H+'|'+G.right;
  NI_clLegend();if(key===C.drawn&&sv.querySelector('.nicg'))return;C.drawn=key;
  let g=sv.querySelector('.nicg');if(!g){g=document.createElementNS(CABSVG,'g');g.setAttribute('class','nicg');
    g.addEventListener('pointerover',e=>{const p=e.target.closest('.nich');if(!p)return;g.classList.add('hov');const c=g.querySelector('.nicc[data-n="'+p.dataset.n+'"]');if(c)c.classList.add('hi')});
    g.addEventListener('pointerout',e=>{const p=e.target.closest('.nich');if(!p)return;g.classList.remove('hov');for(const c of g.querySelectorAll('.nicc.hi'))c.classList.remove('hi')});
    g.addEventListener('click',e=>{const p=e.target.closest('.nich');if(!p)return;e.stopPropagation();const c=C.list[+p.dataset.n];if(c)NI_clashPop(c,e.clientX,e.clientY)})}
  const hg=sv.querySelector(':scope>.chg');if(hg)sv.insertBefore(g,hg);else sv.appendChild(g);
  /* the curves stay above the legend row at the bottom of the lane */
  const P=G.P,sy=G.sy2??G.sy,lgE=w.querySelector('.cablg'),lgT=lgE&&lgE.offsetParent?(lgE.getBoundingClientRect().top-G.R.top)/G.k-G.ms.clientTop:G.H,room=Math.max(10,Math.min(G.H-6,lgT-3)-sy);let back='',front='',lab='',hit='';const n=C.list.length,occ=[];
  /* the normal cables' labels are taken room too */
  for(const t of sv.querySelectorAll(':scope>.clg .clab')){try{const q=t.getBBox();if(q.width)occ.push([q.x,q.x+q.width,q.y+q.height-2])}catch(_){}}
  /* the strongest clash hangs lowest, its label under its curve (over it in a short lane); a label that would cover another one is left to the tooltip */
  C.list.forEach((c,i)=>{const A=P.get(c.a.id),B=P.get(c.b.id);if(!A||!B)return;const x1=A.cx+3,x2=B.cx-3;
    const rm=room>=34?room-12:room,sag=clamp(rm*(n>1?.55+.45*(n-i)/n:1),10,rm),d=cabPath(x1,sy,x2,sy,sag),wd=(1.4+4.6*clamp(c.s/36,0,1)).toFixed(2);
    back+=`<path class="nicb" d="${d}" stroke-width="${(+wd+2.4).toFixed(2)}"/>`;front+=`<path class="nicc" data-n="${i}" d="${d}" stroke-width="${wd}"/>`;
    const tx=`${c.a.name} vs ${c.b.name}, ${c.range}`,tw=cs2Tw(tx),ly=room>=34?sy+sag+3+ +wd/2+8:sy+sag-3-+wd/2,lx=clamp((x1+x2)/2-tw/2,4,Math.max(4,G.right-tw));
    const free=y=>!occ.some(o=>Math.abs(o[2]-y)<11&&lx<o[1]+4&&lx+tw>o[0]-4),yy=[ly,ly-11,ly-22].find(y=>y>sy+14&&free(y));
    if(yy!=null){occ.push([lx,lx+tw,yy]);lab+=`<text class="nicl" x="${lx.toFixed(1)}" y="${yy.toFixed(1)}">${esc(tx)}</text>`}
    hit+=`<path class="nich" data-n="${i}" d="${d}"><title>${esc(NI_clWords(c))} Click for the numbers.</title></path>`});
  g.innerHTML=back+front+lab+hit}
function NI_clWords(c){return`${c.a.name} and ${c.b.name} both sit at ${c.range} here (${INS.fmt(c.la,'dB')} and ${INS.fmt(c.lb,'dB')}, ${c.gap.toFixed(1)} dB apart), so ${c.b.name} is hard to hear there.`}
/* the switch in the cable legend; with Clashes on it shows how many there are at the playhead */
function NI_clLegend(){const w=document.getElementById('mixWin'),lg=w&&w.querySelector('.cablg');if(!lg)return;let b=lg.querySelector('.niclb');
  if(!b){b=document.createElement('button');b.type='button';b.className='cl2 niclb';b.dataset.ni='clash';const em=lg.querySelector('em');lg.insertBefore(b,em||null);
    b.addEventListener('click',e=>{e.stopPropagation();mxsSet('niClash',mxsO().niClash?0:1);if(mxsO().niClash)NI_clRun();else NI_clStop();try{cabSoon()}catch(_){}})}
  const on=!!mxsO().niClash,C=NI.clash,cnt=on?(C.meas&&!C.list.length?'…':String(C.list.length)):'',h=`<svg viewBox="0 0 26 8" width="26" height="8"><path d="M1 2Q13 9 25 2" stroke="${NI_CL_COL}" stroke-width="2.4" fill="none" stroke-linecap="round"/></svg>Clashes${on?` <b>${cnt}</b>`:''}`;
  if(b._h!==h){b._h=h;b.innerHTML=h}b.classList.toggle('on',on);b.setAttribute('aria-pressed',String(on));
  /* the button takes its room from the hint at the end, so the legend keeps its width (the normal cables' labels keep their room) */
  const em=lg.querySelector('em');if(em&&em.offsetParent){em.style.maxWidth='';const nat=em.offsetWidth,bw=b.offsetWidth+10;em.style.maxWidth=Math.max(0,nat-bw)+'px';em.hidden=nat-bw<24}
  b.title=`Clashes: a magenta cable joins two channels that fight in the same frequency band at the playhead (both loud there, close in level). Thicker means a bigger clash. The 12 loudest channels are compared, or with Selected only the selected channel against all. Measured from the song in the background${on&&C.meas?', still measuring this part':''}. Click to ${on?'hide':'show'} them.`}
/* the card for one clash (NI-5b adds the fixes through NI_HOOKS.clashPop) */
function NI_clPopClose(){const p=document.getElementById('niClashPop');if(p)p.remove();document.removeEventListener('pointerdown',NI_clPopOut,true)}
function NI_clPopOut(e){const p=document.getElementById('niClashPop');if(p&&!p.contains(e.target))NI_clPopClose()}
function NI_clashPop(c,cx,cy){NI_clPopClose();const p=document.createElement('div');p.id='niClashPop';const w=NI_bb(NI.clash.beat||0);
  p.innerHTML=`<h4>${esc(c.a.name)} vs ${esc(c.b.name)}, ${esc(c.range)}</h4><p>At ${esc(w.txt)} both channels are loud in this band, ${c.gap.toFixed(1)} dB apart, so the quieter one gets covered.</p>
    <div class="nicpr"><span><i style="--c:${esc(c.a.color||'#cfd3db')}"></i>${esc(c.a.name)}</span><span>${INS.fmt(c.la,'dB')}</span></div>
    <div class="nicpr"><span><i style="--c:${esc(c.b.color||'#cfd3db')}"></i>${esc(c.b.name)}</span><span>${INS.fmt(c.lb,'dB')}</span></div>
    <div class="nicpb"><button type="button" data-nc="sel" title="Select ${esc(c.b.name)}, the channel that gets covered">Select ${esc(c.b.name)}</button><button type="button" data-nc="x" title="Close this card">Close</button></div>`;
  document.body.appendChild(p);const r=p.getBoundingClientRect();p.style.left=clamp(cx+8,4,innerWidth-r.width-4)+'px';p.style.top=clamp(cy+8,4,innerHeight-r.height-4)+'px';
  p.addEventListener('click',e=>{const b=e.target.closest('[data-nc]');if(!b)return;if(b.dataset.nc==='sel'){selectTrack(c.b.id);try{renderHeaders()}catch(_){}}NI_clPopClose()});
  try{if(NI_HOOKS.clashPop)NI_HOOKS.clashPop(c,p)}catch(e){console.warn('NI clash hook',e)}
  setTimeout(()=>document.addEventListener('pointerdown',NI_clPopOut,true),0);return p}
/* the command: open the mixer with the cable lane and Clashes on */
function NI_clashCmd(){let w=document.getElementById('mixWin');if(!w||w.hidden){openMixer();w=document.getElementById('mixWin')}if(!mxsO().cab)mxsSet('cab',1);if(!mxsO().niClash)mxsSet('niClash',1);cabSoon();setTimeout(NI_clRun,0);
  toast('Clashes on: magenta cables join channels that fight in the same band at the playhead.')}
/* after every redraw of the cable lane, the clash cables again (the lane's SVG is rebuilt) */
{const _cd=cabDraw;cabDraw=function(){const r=_cd.apply(this,arguments);try{if(NI_clOn()){NI.clash.drawn='';if(!NI.clash.tm)NI_clRun();else NI_clDraw()}else if(NI.clash.tm||NI.clash.list.length)NI_clStop();NI_clLegend()}catch(e){console.warn('NI clashes',e)}return r}}
/* with Clashes on the lane asks for two more rows of room (as tidy cables do, only out of the room the channels leave; a height set by hand wins) */
{const _t=cs2T;cs2T=function(){const v=_t.apply(this,arguments);try{const o=mxsO();if(!o.niClash||o.cabH||!cabOn())return v;const ms=cs2Ms(),mn=cs2Min(),room=ms?ms.clientHeight-cs2ChMin():150;
  const k=cs2K(),want=(Math.max(v/k,52)+32)*k,cap=Math.max(mn,Math.min(150*k,room));return Math.max(v,Math.round(Math.min(want,cap)))}catch(e){return v}}}
/* NI-1b's clip note on the transport's peak box: since v0.257 lane E's meters write that box's tooltip twice a second (RMS and crest), which
   wiped the note. While a clip event is flagged the note goes in front of their text; cleared, their text alone. Runs after every script
   has loaded so it wraps theirs; it compares one string per call and writes only when the text is wrong. */
const NI_CLIP_TIP='The mix went over (or the safety limiter was at its ceiling) while it played. Click to see why. The orange dot stays until you clear it in that card.';
function NI_clipTip(){const pb=document.getElementById('peakBox');if(!pb)return;const base=pb._tt||pb.dataset.niT||'',want=pb.classList.contains('niev')?NI_CLIP_TIP+(base?'\n'+base:''):(pb._tt||'');if(want&&pb.title!==want)pb.title=want}
setTimeout(()=>{const _m=meters;meters=function(){const r=_m.apply(this,arguments);try{NI_clipTip()}catch(e){}return r}},0);
{const _cu=NI.clipUI;NI.clipUI=function(e){const r=_cu.apply(this,arguments);try{NI_clipTip()}catch(_){}return r}}
NI.clash.at=NI_clashAt;NI.clash.draw=NI_clDraw;NI.clash.pop=NI_clashPop;
/* ===== end of lane D NI-5a ===== */"""
A3 = "/* ===== end of lane D NI-4 ===== */"
s = put(s, A3, JS, before=False)
open(P, 'w', encoding='utf-8').write(s)
print('NI-5a applied')
