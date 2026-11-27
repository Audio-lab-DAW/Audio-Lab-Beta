"""Task NI-1b (lane D): I3 "Why is this clipping?", part 2: the card.
Edit script with unique asserted anchors (needs NI-1a in the file), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_1b.py [index.html]
Adds:
  - the card (#niClip, a .pop, so the glass engine draws it): bar and beat, the chain in words, readouts with units,
    a signed bar chart of each track's share of the peak, and the fixes: lower the top contributor (one undo step),
    a limiter at the end of the master chain (one undo step), play the moment (2-bar loop), clear
  - opening it: a click on the master peak read-out, the mixer's master clip dot, the master pop's clip dot
    (when the song has clip events), on a strip's peak read-out (when that strip has events); the command ni.clipExplain
  - a small "Clip" button next to the mixer button and a dot on the master peak read-out while the song has clip events
"""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane D (task NI-1b)'
if MARK in s:
    print('NI-1b already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-1a ===== */' in s, 'NI-1a must be in the file first'

def put(s, anchor, new, before=True):
    n = s.count(anchor)
    assert n == 1, (anchor[:60], n)
    return s.replace(anchor, new + anchor if before else anchor + new)

# 1. the 1a log tells the card's indicator about new events
A1 = "if(NI_HOOKS.clipEvent)try{NI_HOOKS.clipEvent(e)}catch(_){}}"
s = put(s, A1, "if(NI.clipUI)try{NI.clipUI(e)}catch(_){}", before=True)

# 2. the command
A2 = "\n {id:'tour',g:'help',"
s = put(s, A2, "\n {id:'ni.clipExplain',g:'view',l:'Why is this clipping? (explain the last clip)',d:'',ic:'M3 15l4-8 3 5 2-3 5 6M3 4h14',run:()=>NI_clipCard()},")

# 3. CSS
CSS = r"""/* lane D (task NI-1b): the "Why is this clipping?" card. Instrument look: units on every read-out, equal-width digits, one colour per track on its bar */
#niClip{width:330px;align-items:stretch;gap:8px;padding:10px 12px 12px;font-size:var(--fs2);z-index:60}
#niClip[hidden]{display:none}
#niClip .nich{display:flex;align-items:center;gap:6px}#niClip .nich b{font-size:var(--fs3);flex:1;white-space:nowrap}
#niClip>select{min-height:22px;width:100%;font-size:var(--fs1);padding:0 4px}#niClip>select[hidden]{display:none}
#niClip .nix{min-height:22px;width:24px;padding:0;display:grid;place-items:center}#niClip .nix svg{width:12px;height:12px}
#niClip .nist{font-size:var(--fs1);color:var(--mut)}#niClip .nist:empty{display:none}
#niClip .niw{margin:0;line-height:1.45;color:var(--ink)}
#niClip .nird{display:grid;grid-template-columns:repeat(3,1fr);gap:4px}
#niClip .nird span{display:flex;flex-direction:column;gap:1px;padding:4px 6px;border-radius:6px;background:rgba(0,0,0,.28);border:1px solid rgba(255,255,255,.07)}
#niClip .nird small{font-size:var(--fs1);color:var(--mut)}#niClip .nird b{font:var(--fw6) var(--fs2) var(--ffu);font-variant-numeric:tabular-nums;color:#cfe6ff;white-space:nowrap}
#niClip .nird b.ov{color:#ff6b6b}#niClip .nird b i{font-style:normal;font-weight:var(--fw4);color:var(--mut);margin-left:3px;font-size:var(--fs1)}
#niClip .nibars{display:flex;flex-direction:column;gap:3px}#niClip .nibars:empty{display:none}
#niClip .nibh{display:flex;justify-content:space-between;font-size:var(--fs1);color:var(--mut)}
#niClip .nibr{display:grid;grid-template-columns:86px minmax(0,1fr) 42px;align-items:center;gap:6px;font-size:var(--fs1)}
#niClip .nibr>span{display:flex;align-items:center;gap:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#d6d8de}
#niClip .nibr>span i{width:7px;height:7px;border-radius:2px;flex:none;background:var(--c)}
#niClip .nibr u{position:relative;height:10px;border-radius:2px;background:rgba(0,0,0,.35);text-decoration:none;overflow:hidden;
  background-image:linear-gradient(90deg,rgba(255,255,255,.09) 1px,transparent 1px);background-size:25% 100%}
#niClip .nibr u em{position:absolute;top:1px;bottom:1px;background:var(--c);border-radius:1px}
#niClip .nibr u s{position:absolute;top:0;bottom:0;width:1px;background:rgba(255,255,255,.55)}
#niClip .nibr b{text-align:right;font-weight:var(--fw6);font-variant-numeric:tabular-nums;color:#e9eaf0}
#niClip .nifix{display:flex;flex-wrap:wrap;gap:5px}#niClip .nifix button{min-height:24px;padding:0 9px;font-size:var(--fs1)}
#niClip .nifix button.pri{background:linear-gradient(#ff7a7a,#d94848);border-color:#5e1414;color:#fff}
#niClip .nifix button[hidden]{display:none}
#niClip .ninote{font-size:var(--fs1);color:var(--mut);line-height:1.4}#niClip .ninote:empty{display:none}
#niClipB{height:28px;min-height:28px;padding:0 8px;display:flex;align-items:center;gap:5px;font:var(--fw6) var(--fs1) var(--ffu);color:#ffd0b0}#niClipB[hidden]{display:none}
#niClipB i{width:7px;height:7px;border-radius:50%;background:#ff6b3d;box-shadow:0 0 5px #ff6b3d}
#peakBox.niev{position:relative}#peakBox.niev::after{content:'';position:absolute;left:4px;top:4px;width:5px;height:5px;border-radius:50%;background:#ff9a3c;box-shadow:0 0 4px #ff9a3c}
"""
A3 = ".dacv{display:flex;"
s = put(s, A3, CSS)

# 4. JS
JS = r"""/* ===== lane D (task NI-1b): I3 "Why is this clipping?", part 2: the card =====
   Opens from the master peak read-out, the mixer's and the master pop's clip dots (when the song has clip events), a strip's peak read-out
   (when that strip has events) and the command ni.clipExplain. Measures with NI_clipExplain (NI-1a, offline). Fixes are single undo steps. */
NI.card={el:null,ev:null,r:null,tok:0};
const NI_srcName=src=>src==='master'?'Master':((trkById(src)||{}).name||'a track');
function NI_evLabel(e){const w=NI_bb(Math.round(e.t*2)/2),d=(e.db>=0?'+':'')+e.db.toFixed(1)+' dB';return`bar ${w.bar} · ${NI_srcName(e.src)} · ${e.sat?'at least '+d+', limiter':d}`}
/* a small clip button next to the mixer button, shown only while the song has clip events (the peak read-out is hidden in the compact transport) */
{const mb=$('#mBtn');if(mb&&!$('#niClipB')){mb.insertAdjacentHTML('afterend','<button id="niClipB" hidden title="The mix went over while it played (or the safety limiter was at its ceiling). Click to see why it clipped and how to fix it."><i></i>Clip</button>');$('#niClipB').onclick=e=>{if(!NI_clipLog().length){e.currentTarget.hidden=true;return}NI_clipCard(null,e.currentTarget)}}}
NI.clipUI=e=>{const cb=$('#niClipB');if(cb)cb.hidden=false;if(e.src!=='master')return;const b=$('#peakBox');if(!b)return;b.classList.add('niev');b.dataset.niT=b.dataset.niT||b.title;b.title='The mix went over (or the safety limiter was at its ceiling) while it played. Click to see why. The orange dot stays until you clear it in that card.'};
function NI_cardEl(){let W=NI.card.el;if(W&&W.isConnected)return W;W=document.createElement('div');W.id='niClip';W.className='pop';W.hidden=true;W.setAttribute('role','dialog');W.setAttribute('aria-label','Why is this clipping?');
  W.innerHTML=`<div class="nich"><b>Why is this clipping?</b><button class="nix" data-ni="x" title="Close (Escape)" aria-label="Close"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M2 2l8 8M10 2l-8 8"/></svg></button></div><select data-ni="ev" title="The moments this song went over while it played (positions read live, to the nearest half beat), newest first. Pick one to measure it."></select>
  <div class="nist" aria-live="polite"></div><p class="niw"></p>
  <div class="nird"><span title="Where the highest sample of the mix is, in the song"><small>Where</small><b data-ni="at">–</b></span><span title="The highest sample of the mix, in dB relative to full scale (0 dBFS is the most a file can hold)"><small>Peak</small><b data-ni="pk">–</b></span><span title="The highest point between the samples (4x oversampled, like a true-peak meter). Players and converters can go over here even when the samples do not."><small>Inter-sample</small><b data-ni="tp">–</b></span></div>
  <div class="nibars"></div><div class="ninote"></div>
  <div class="nifix"><button class="pri" data-ni="low" hidden></button><button data-ni="lim" hidden title="Adds AudioLab's Limiter at the end of the master chain (Safety net: no gain, ceiling -1 dB, true peak), or turns it on if it is there. One undo step.">Limiter on the master</button><button data-ni="play" title="Loops the 2 bars around this moment and plays them, so you can hear it">Play the moment</button><button data-ni="clr" title="Forget the clip events of this song and reset the clip lights">Clear</button></div>`;
  document.body.appendChild(W);NI.card.el=W;
  W.addEventListener('click',ev=>{const b=ev.target.closest('[data-ni]');if(!b||b.tagName==='SELECT')return;const k=b.dataset.ni;
    if(k==='x')NI_cardClose();else if(k==='low')NI_clipFixLower();else if(k==='lim')NI_clipFixLimiter();else if(k==='play')NI_clipPlay();else if(k==='clr')NI_clipClearAll()});
  W.querySelector('[data-ni="ev"]').addEventListener('change',ev=>{const id=+ev.target.value,e=NI_clipLog().find(q=>q.id===id);if(e)NI_cardShow(e)});
  return W}
function NI_cardClose(){const W=NI.card.el;if(W)W.hidden=true;NI.card.tok++}
function NI_cardPlace(anchor){const W=NI.card.el,z=ZOOM,vw=innerWidth/z,vh=innerHeight/z,Wd=W.offsetWidth,H=W.offsetHeight;let L,T;
  if(anchor&&anchor.isConnected){const r=anchor.getBoundingClientRect();L=r.right/z-Wd;T=r.top/z-H-8;if(T<4)T=r.bottom/z+8}else{L=(vw-Wd)/2;T=(vh-H)/3}
  W.style.left=clamp(L,4,vw-Wd-4)+'px';W.style.top=clamp(T,4,Math.max(4,vh-H-4))+'px'}
/* open the card: for an event (default: the newest of the given source, else the newest of the song) */
function NI_clipCard(e,anchor,src){const L=NI_clipLog();if(!e)e=[...L].reverse().find(q=>!src||q.src===src)||null;
  if(!e){toast('No clips in this song yet. AudioLab notes them while the song plays.');return null}
  const W=NI_cardEl();W.hidden=false;NI.card.anchor=anchor||NI.card.anchor||null;NI_cardShow(e);NI_cardPlace(NI.card.anchor);return W}
async function NI_cardShow(e){const W=NI_cardEl(),C=NI.card,tok=++C.tok;C.ev=e;C.r=null;
  const sel=W.querySelector('[data-ni="ev"]'),L=[...NI_clipLog()].reverse().slice(0,30);sel.innerHTML=L.map(q=>`<option value="${q.id}"${q.id===e.id?' selected':''}>${esc(NI_evLabel(q))}</option>`).join('');sel.hidden=L.length<2;
  W.querySelector('.nist').textContent='Measuring this moment offline (the mix, then each track alone)…';W.querySelector('.niw').textContent='';W.querySelector('.nibars').innerHTML='';W.querySelector('.ninote').textContent='';
  for(const k of['at','pk','tp']){const b=W.querySelector(`[data-ni="${k}"]`);b.textContent='–';b.classList.remove('ov')}for(const k of['low','lim'])W.querySelector(`[data-ni="${k}"]`).hidden=true;
  const r=await NI_clipExplain(e);if(tok!==C.tok||W.hidden)return;C.r=r;NI_cardFill(r,e);NI_cardPlace(C.anchor)}
function NI_cardFill(r,e){const W=NI.card.el,st=W.querySelector('.nist'),f1=v=>(v>=0?'+':'')+v.toFixed(1);
  if(!r||r.busy||r.stale||r.error||r.empty){st.textContent=r?(r.why||('Could not measure: '+r.error)):'Nothing to measure.';return}
  st.textContent='';const strip=e.src!=='master'&&r.strip;
  const pl=strip&&r.strip.clips.length?' (playing: '+r.strip.clips.join(', ')+')':'';
  W.querySelector('.niw').textContent=strip?(r.strip.pkDb>0?`${r.strip.name} goes over on its own here: its peak is ${f1(r.strip.pkDb)} dB${pl}. In the mix: `:`${r.strip.name}'s strip went over while it played. Measured here on its own: ${r.strip.pkDb==null?'not measurable alone':f1(r.strip.pkDb)+' dB'}${pl}. In the mix: `)+r.words:r.words;
  const at=W.querySelector('[data-ni="at"]'),pk=W.querySelector('[data-ni="pk"]'),tp=W.querySelector('[data-ni="tp"]');
  at.innerHTML=`${r.where.bar}.${r.where.beat}<i>bar.beat</i>`;pk.innerHTML=`${f1(r.peakDb)}<i>dBFS</i>`;tp.innerHTML=`${f1(r.tpDb)}<i>dBTP</i>`;pk.classList.toggle('ov',r.peakDb>0);tp.classList.toggle('ov',r.tpDb>0);
  /* the bars: each track's signed part of the peak sample, zero line and quarter lines */
  const rows=r.tracks.filter(q=>Math.abs(q.share)>=.005).slice(0,8);if(Math.abs(r.rest.share)>=.02)rows.push({name:'Sends, groups, master',color:'#8b8b97',share:r.rest.share,rest:1});
  const lo=Math.min(0,...rows.map(q=>q.share)),hi=Math.max(1,...rows.map(q=>q.share)),X=v=>(v-lo)/(hi-lo)*100;
  W.querySelector('.nibars').innerHTML=rows.length?`<div class="nibh" title="Each track's part of the highest sample. They add up to 100%. A negative part pulls the peak down (opposite phase)."><span>Share of the peak</span><span>${lo<0?Math.round(lo*100)+'% to ':''}${Math.round(hi*100)}%</span></div>`+rows.map(q=>{const a=X(Math.min(0,q.share)),b=X(Math.max(0,q.share));
    return`<div class="nibr" style="--c:${q.color||'#8b8b97'}" title="${esc(q.name)}: ${Math.round(q.share*100)}% of the peak sample${q.rest?' (what sends, groups and master effects add)':q.pkDb!=null?', its own peak here '+f1(q.pkDb)+' dBFS':''}"><span><i></i>${esc(q.name)}</span><u><s style="left:${X(0)}%"></s><em style="left:${a}%;width:${Math.max(.6,b-a)}%"></em></u><b>${Math.round(q.share*100)}%</b></div>`}).join(''):'';
  const notes=[];if(e.lim)notes.push(e.sat?'Heard live through the safety limiter, which was at its ceiling here. The measurement is of the mix before it.':'Heard live through the safety limiter. The measurement is of the mix before it.');
  if(!r.clip&&!strip)notes.push(r.tpDb>0?'The samples stay under 0 dBFS, but the inter-sample peak does not: a limiter with true peak catches that.':'An export of this moment is not over 0 dBFS.');
  if(r.masterFx)notes.push('The master has effects, so shares are measured after them (each track alone through the master chain).');
  W.querySelector('.ninote').textContent=notes.join(' ');
  const lw=NI_lowerFor(r,e),lb=W.querySelector('[data-ni="low"]');lb.hidden=!lw;if(lw){lb.textContent=`Lower ${lw.name} by ${lw.db.toFixed(1)} dB`;lb.title=strip?`Turns ${lw.name}'s volume down so it stays under 0 dB on its own. One undo step.`:`Turns ${lw.name}'s volume down so this peak lands at -0.5 dBFS (it has the biggest share). One undo step. The card measures again afterwards.`}
  const ml=(S.mfx||[]).find(f=>f.type==='limit');W.querySelector('[data-ni="lim"]').hidden=!((r.clip||r.tpDb>0)&&!(ml&&ml.on));
  W.querySelector('[data-ni="lim"]').textContent=ml?'Turn the master limiter on':'Limiter on the master'}
/* which track to lower and by how much: so the peak sample lands at -0.5 dBFS, at least the overshoot plus 0.5 dB (a strip: its own overshoot plus 0.5 dB) */
function NI_lowerFor(r,e){if(!r)return null;
  if(e&&e.src!=='master'&&r.strip&&r.strip.pkDb>0){const t=trkById(r.strip.id);return t?{id:t.id,name:t.name,db:Math.ceil((r.strip.pkDb+.5)*10)/10}:null}
  if(!r.clip)return null;const top=r.tracks[0];if(!top||!(top.share>0))return null;const T=Math.pow(10,-.5/20),m=r.peak,v=top.share*m;
  let g=1-(m-T)/v;g=Math.max(.03,Math.min(1,g));const need=-20*Math.log10(g),db=Math.ceil(Math.max(need,r.overDb+.5)*10)/10;return{id:top.id,name:top.name,db}}
function NI_clipFixLower(){const C=NI.card,lw=NI_lowerFor(C.r,C.ev);if(!lw)return;const t=trkById(lw.id);if(!t)return;
  pushUndo();t.vol=t.vol*Math.pow(10,-lw.db/20);changed(true);toast(`${t.name} is ${lw.db.toFixed(1)} dB lower. Undo puts it back. Measuring again…`);NI_cardShow(C.ev)}
function NI_clipFixLimiter(){pushUndo();S.mfx=S.mfx||[];let f=S.mfx.find(q=>q.type==='limit');
  if(f)f.on=true;else{f=mkFx('limit');Object.assign(f.p,{gain:0,ceil:-1,rel:200,look:5,out:0,style:'transparent',tp:true});f.on=true;S.mfx.push(f)}
  changed(true);try{routeMaster()}catch(_){}toast('A limiter (ceiling -1 dB, true peak) is on the master now. Undo takes it away. Measuring again…');NI_cardShow(NI.card.ev)}
function NI_clipPlay(){const r=NI.card.r,e=NI.card.ev;const t=r&&r.t!=null?r.t:e&&e.t;if(t==null)return;const P=barPos(Math.max(0,t)+2e-3);let a=P.start-P.len,b=P.start+P.len;if(a<0){a=0;b=2*P.len}
  if(play.on)stop();S.loopRange={a,b};S.loop=true;pos=a;syncTransportUI();dirty=true;start();const w=NI_bb(a);toast(`Looping bars ${w.bar} to ${w.bar+1}. The loop button turns it off.`)}
function NI_clipClearAll(){NI_clipClear();{const cb=$('#niClipB');if(cb)cb.hidden=true}const b=$('#peakBox');if(b){b.classList.remove('niev');if(b.dataset.niT){b.title=b.dataset.niT;delete b.dataset.niT}b.click()}
  try{const h=MXH.get('master');if(h)h.max=-90}catch(_){}try{for(const h of MXH.values())h.pkm=0}catch(_){}NI_cardClose();toast('Clip events of this song cleared.')}
/* where it opens from: the master peak read-out and clip dots, a strip's peak read-out */
document.addEventListener('click',ev=>{const t=ev.target;if(!t||!t.closest)return;let a,src='master';
  if(!(a=t.closest('#peakBox,#mxClip,#mpClip'))){a=t.closest('.mxpkr');if(!a||ev.shiftKey)return;src=a.dataset.pk}
  if(!NI_clipLog().some(q=>q.src===src))return;const anc=a;setTimeout(()=>NI_clipCard(null,anc,src),0)},true);
document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&NI.card.el&&!NI.card.el.hidden){NI_cardClose();ev.stopPropagation()}},true);
document.addEventListener('pointerdown',ev=>{const W=NI.card.el;if(!W||W.hidden)return;if(W.contains(ev.target)||ev.target.closest('#peakBox,#mxClip,#mpClip,.mxpkr,#toast,#niClipB'))return;NI_cardClose()},true);
/* ===== end of lane D NI-1b ===== */
"""
A4 = "function askChoice(title,text,btns,icon){"
s = put(s, A4, JS)
open(P, 'w', encoding='utf-8').write(s)
print('NI-1b applied')
