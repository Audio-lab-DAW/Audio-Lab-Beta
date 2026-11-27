"""Task NI-2b (lane D): I2 kick and bass tuning lab, part 2: the view and the two fixes.
Edit script with unique asserted anchors (needs NI-1a and NI-2a in the file), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_2b.py [index.html]
Adds:
  - the card #niKB (a .pop, so the glass engine draws it): kick and bass track pickers, the bar (previous, next, at the playhead),
    read-outs (kick note, key, clash, gap), the result in words, and one canvas drawn once per measurement (never per frame):
    a note ruler C0 to C3 with the key lit, the kick's falling pitch curve over its life with its end note, the bass notes of the bar
    as bars on the same ruler (tuned, clash with the beat rate and a hatch, apart), the kick's life on each hit, and the rolling-bass
    gap strip
  - the fixes, one undo step each: "Tune the kick to the root" (Kick designer: its Pitch; drum machine pad: the pad's Tune),
    "Bass down an octave" (the notes of the bass clips that play in this bar); "Play this bar" loops it
  - the command ni.kickBass, an entry in the main menu, NI_HOOKS.kickBassView for lane C's FT-F18 rows
"""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane D (task NI-2b)'
if MARK in s:
    print('NI-2b already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-2a ===== */' in s, 'NI-2a must be in the file first'

def put(s, anchor, new, before=True):
    n = s.count(anchor)
    assert n == 1, (anchor[:60], n)
    return s.replace(anchor, new + anchor if before else anchor + new)

# 1. the command
A1 = "\n {id:'tour',g:'help',"
s = put(s, A1, "\n {id:'ni.kickBass',g:'view',l:'Kick and bass lab (is the kick in tune with the bass?)',d:'',ic:'M3 15h14M6 15V9M10 15V5M14 15v-4',run:()=>NI_kbOpen()},")

# 2. the main menu entry, next to Undo
A2 = "{label:'Undo',key:'⌘Z',dis:!UNDO.length,"
s = put(s, A2, "{label:'Kick and bass lab…',sub:'is the kick in tune with the bass?',ic:I('M3 15h14M6 15V9M10 15V5M14 15v-4','#ff6b6b'),act:()=>NI_kbOpen()},\n   ")

# 3. CSS
CSS = r"""/* lane D (task NI-2b): the kick and bass lab. Instrument look: units on every read-out, equal-width digits, the canvas drawn once per measurement */
#niKB{width:540px;align-items:stretch;gap:7px;padding:10px 12px 12px;font-size:var(--fs2);z-index:60}
#niKB[hidden]{display:none}
#niKB .nich{display:flex;align-items:center;gap:6px}#niKB .nich b{font-size:var(--fs3);flex:1;white-space:nowrap}
#niKB .nix{min-height:22px;width:24px;padding:0;display:grid;place-items:center}#niKB .nix svg{width:12px;height:12px}
#niKB .nisel{display:flex;align-items:center;gap:6px;font-size:var(--fs1);color:var(--mut)}
#niKB .nisel select{min-height:22px;flex:1;min-width:0;font-size:var(--fs1);padding:0 4px}
#niKB .nisel button{min-height:22px;padding:0 7px;font-size:var(--fs1)}#niKB .nisel b{color:var(--ink);font-weight:var(--fw6);font-variant-numeric:tabular-nums;min-width:44px;text-align:center}
#niKB .nist{font-size:var(--fs1);color:var(--mut)}#niKB .nist:empty{display:none}
#niKB .niw{margin:0;line-height:1.45;color:var(--ink)}#niKB .niw:empty{display:none}
#niKB .nird{display:grid;grid-template-columns:repeat(4,1fr);gap:4px}
#niKB .nird span{display:flex;flex-direction:column;gap:1px;padding:4px 6px;border-radius:6px;background:rgba(0,0,0,.28);border:1px solid rgba(255,255,255,.07);min-width:0}
#niKB .nird small{font-size:var(--fs1);color:var(--mut)}#niKB .nird b{font:var(--fw6) var(--fs2) var(--ffu);font-variant-numeric:tabular-nums;color:#cfe6ff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#niKB .nird b.cl{color:#ff8a8a}#niKB .nird b.ok{color:#7ee2b0}#niKB .nird b i{font-style:normal;font-weight:var(--fw4);color:var(--mut);margin-left:3px;font-size:var(--fs1)}
#niKB canvas{width:516px;height:268px;border-radius:6px;display:block}
#niKB .nifix{display:flex;flex-wrap:wrap;gap:5px}#niKB .nifix button{min-height:24px;padding:0 9px;font-size:var(--fs1)}
#niKB .nifix button.pri{background:linear-gradient(#ff7a7a,#d94848);border-color:#5e1414;color:#fff}#niKB .nifix button[hidden]{display:none}
#niKB .ninote{font-size:var(--fs1);color:var(--mut);line-height:1.4}#niKB .ninote:empty{display:none}
#niKB .nikbx:empty{display:none}
"""
A3 = ".dacv{display:flex;"
s = put(s, A3, CSS)

# 4. JS
JS = r"""/* ===== lane D (task NI-2b): I2 kick and bass tuning lab, part 2: the view and the two fixes =====
   Measures with NI_kickBass (NI-2a) and draws one canvas per measurement: nothing runs per frame, nothing while the card is closed.
   Fixes are single undo steps and measure again. Lane E's shared scale drawers replace the local ones here once IN-A lands. */
NI.kbv={el:null,r:null,tok:0,t:null,kick:null,bass:null,rows:[]};
const NI_mn=v=>(v<0?'−':'')+Math.abs(v).toFixed(1);/* the instrument rule: a real minus sign, one decimal */
const NI_KBC={kick:'#ff6b6b',tuned:'#3ecf8e',clash:'#ff5a5a',apart:'#8fb7ff',grid:'rgba(255,255,255,.07)',lab:'rgba(255,255,255,.5)'};
function NI_kbEl(){let W=NI.kbv.el;if(W&&W.isConnected)return W;W=document.createElement('div');W.id='niKB';W.className='pop';W.hidden=true;W.setAttribute('role','dialog');W.setAttribute('aria-label','Kick and bass lab');
  W.innerHTML=`<div class="nich"><b>Kick and bass lab</b><button class="nix" data-nk="x" title="Close (Escape)" aria-label="Close"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M2 2l8 8M10 2l-8 8"/></svg></button></div>
  <div class="nisel"><span>Kick</span><select data-nk="kick" title="The track that plays the kick. Found by itself (Kick designer, a drum machine kick, or a track named Kick); pick another here."></select><span>Bass</span><select data-nk="bass" title="The track that plays the bass line (its MIDI notes are read). Found by itself (a track named Bass, or the lowest notes); pick another here."></select></div>
  <div class="nisel"><button data-nk="prev" title="Measure the bar before">‹</button><b data-nk="bar" title="The bar that is measured">–</b><button data-nk="next" title="Measure the next bar">›</button><button data-nk="here" title="Measure the bar under the playhead">At the playhead</button><span style="flex:1"></span></div>
  <div class="nird"><span title="The note the kick settles on at the end of its pitch drop. Exact when read from the Kick designer or a drum machine kick; a range when measured from a sample."><small>Kick note</small><b data-nk="kn">–</b></span><span title="The song key: the piano roll's scale and root (or the project key when there is one)"><small>Key</small><b data-nk="key">–</b></span><span title="The fastest beating between the kick's note and a bass note of this bar, one or two semitones apart. Slow beating (under about 10 Hz) is heard as a wobble or a hole in the low end."><small>Clash</small><b data-nk="cl">–</b></span><span title="The shortest time from a kick hit to the next bass note in this bar: the room the bass leaves for the kick"><small>Gap</small><b data-nk="gap">–</b></span></div>
  <div class="nist" aria-live="polite"></div>
  <canvas data-nk="cv" title="Left: the note ruler, C0 at the bottom to C3 at the top, the song key lit. Kick: its pitch falling over its life (milliseconds), the note it settles on as a dashed line. Bar: the bass notes as bars on the same ruler, green in tune with the kick, red and hatched where they beat against it, blue further apart; the kick's life on each hit. Bottom strip: kick and bass in time, the gaps between them."></canvas>
  <p class="niw"></p><div class="nikbx"></div><div class="ninote"></div>
  <div class="nifix"><button class="pri" data-nk="tune" hidden></button><button data-nk="oct" hidden title="Moves every note of the bass clips that play in this bar down 12 semitones, so the bass sits under the kick instead of on it. The note names stay the same, so a clash stays at the same rate, but it moves to the bass's weaker overtone. One undo step.">Bass down an octave</button><button data-nk="play" title="Loops this bar and plays it, so you can hear the kick and the bass together">Play this bar</button></div>`;
  document.body.appendChild(W);NI.kbv.el=W;
  W.addEventListener('click',ev=>{const b=ev.target.closest('button[data-nk]');if(!b)return;const k=b.dataset.nk,V=NI.kbv,r=V.r;
    if(k==='x')NI_kbClose();else if(k==='prev'||k==='next'){const b0=r&&r.bar?r.bar.b0:barPos(Math.max(0,curDisp())).start,P=barPos(Math.max(0,b0+(k==='prev'?-.01:barPos(b0).len+.01)));V.t=Math.max(0,P.start);NI_kbShow()}
    else if(k==='here'){V.t=null;NI_kbShow()}else if(k==='tune')NI_kbFixTune();else if(k==='oct')NI_kbFixOct();else if(k==='play')NI_kbPlay()});
  for(const k of['kick','bass'])W.querySelector(`[data-nk="${k}"]`).addEventListener('change',ev=>{NI.kbv[k]=ev.target.value?+ev.target.value||ev.target.value:null;NI_kbShow()});
  return W}
function NI_kbClose(){const W=NI.kbv.el;if(W)W.hidden=true;NI.kbv.tok++}
function NI_kbPlace(){const W=NI.kbv.el,z=ZOOM,vw=innerWidth/z,vh=innerHeight/z,Wd=W.offsetWidth,H=W.offsetHeight;W.style.left=clamp((vw-Wd)/2,4,Math.max(4,vw-Wd-4))+'px';W.style.top=clamp((vh-H)/3,4,Math.max(4,vh-H-4))+'px'}
/* open the lab: o {t, kick, bass} (all optional) */
function NI_kbOpen(o){o=o||{};const V=NI.kbv,W=NI_kbEl();if('t'in o)V.t=o.t;else V.t=null;if(o.kick!=null)V.kick=o.kick;if(o.bass!=null)V.bass=o.bass;
  if(V.kick!=null&&!trkById(V.kick))V.kick=null;if(V.bass!=null&&!trkById(V.bass))V.bass=null;W.hidden=false;NI_kbShow();NI_kbPlace();return W}
function NI_kbOpts(sel,cur,fn,none){const L=S.tracks.filter(t=>t.kind!=='return'&&t.kind!=='group'&&(t.clips||[]).length);
  sel.innerHTML=`<option value="">${none}</option>`+L.map(t=>`<option value="${esc(String(t.id))}"${t.id===cur?' selected':''}>${esc(t.name||'Track')}</option>`).join('')}
async function NI_kbShow(){const W=NI_kbEl(),V=NI.kbv,tok=++V.tok,st=W.querySelector('.nist');st.textContent='Measuring…';
  const o={};if(V.t!=null)o.t=V.t;if(V.kick!=null)o.kick=V.kick;if(V.bass!=null)o.bass=V.bass;
  const r=await NI_kickBass(o);if(tok!==V.tok||W.hidden)return;V.r=r;NI_kbFill(r)}
function NI_kbFill(r){const W=NI.kbv.el,st=W.querySelector('.nist'),q=k=>W.querySelector(`[data-nk="${k}"]`);
  NI_kbOpts(q('kick'),r&&r.kick?r.kick.id:null,0,'No kick');NI_kbOpts(q('bass'),r&&r.bass?r.bass.id:null,0,'No bass');
  for(const k of['kn','key','cl','gap']){q(k).textContent='–';q(k).className=''}q('bar').textContent=r&&r.bar?'bar '+r.bar.n:'–';q('tune').hidden=true;q('oct').hidden=true;
  W.querySelector('.niw').textContent='';W.querySelector('.ninote').textContent='';
  if(r&&r.key)q('key').textContent=r.key.name;
  if(!r||r.busy||r.stale||r.error||r.empty||!r.kick){st.textContent=r?(r.why||('Could not measure: '+r.error)):'Nothing to measure.';NI_kbDraw(q('cv'),null);NI_kbRows(r);return}
  st.textContent='';const k=r.kick;q('kn').innerHTML=`${esc(k.exact?k.endTxt:'≈ '+NI_noteTxt(Math.round(k.endNote)))}<i>${k.endHz.toFixed(1)} Hz</i>`;q('kn').title=k.exact?'Exact, from the settings':'Measured from the sound: '+k.range.txt.replace(/-(\d)/g,'−$1')+' ('+k.range.lo.toFixed(1)+' to '+k.range.hi.toFixed(1)+' Hz)';
  const cl=r.bass.notes.filter(n=>n.pair.state==='clash').sort((a,b)=>a.pair.beatHz-b.pair.beatHz);
  if(r.bass.notes.length){const c=q('cl');if(cl.length){c.innerHTML=`${cl[0].pair.beatHz.toFixed(1)} Hz<i>${esc(cl[0].txt)}${cl[0].pair.oct?', overtone':''}</i>`;c.className='cl'}else{c.textContent='none';c.className='ok'}}
  const gaps=r.overlap.map(o=>o.gapMs).filter(v=>v!=null);if(gaps.length)q('gap').innerHTML=`${Math.min(...gaps)}<i>ms</i>`;
  W.querySelector('.niw').textContent=r.words;
  /* the fixes */
  const tf=NI_kbTuneTarget(r),tb=q('tune');if(tf){tb.hidden=false;tb.textContent=`Tune the kick to ${tf.txt}`;tb.title=`Sets ${tf.what} so the kick settles on ${tf.txt}, the root of ${r.key.name} (${tf.semis>0?'+':''}${NI_mn(tf.semis)} semitones). One undo step. The lab measures again afterwards.`}
  const oc=NI_kbOctClips(r);q('oct').hidden=!oc.length;
  const notes=[];if(!k.exact)notes.push('This kick is measured from its sound, so its note is a range'+(k.low?' (under 40 Hz a short tail cannot be exact)':'')+'. A sample is tuned with its own pitch, so the lab does not change it.');
  if(r.key.from==='piano roll')notes.push('The key is the piano roll\'s scale and root.');W.querySelector('.ninote').textContent=notes.join(' ');
  NI_kbDraw(q('cv'),r);NI_kbRows(r)}
/* lane C's FT-F18 rows (low-band correlation, phase rotation, shorten tail) go under the words: NI_HOOKS.kickBassView.addRow(fn), fn(r, el) */
function NI_kbRows(r){const box=NI.kbv.el&&NI.kbv.el.querySelector('.nikbx');if(!box)return;box.innerHTML='';for(const fn of NI.kbv.rows){const d=document.createElement('div');box.appendChild(d);try{fn(r,d)}catch(e){console.warn('kickBassView row',e)}}}
NI_HOOKS.kickBassView={open:o=>NI_kbOpen(o),close:()=>NI_kbClose(),refresh:()=>{if(NI.kbv.el&&!NI.kbv.el.hidden)NI_kbShow()},addRow:fn=>{if(typeof fn==='function'&&!NI.kbv.rows.includes(fn))NI.kbv.rows.push(fn)},result:()=>NI.kbv.r};
/* the root to tune the kick to, inside what the kick can reach (Kick designer Pitch 21 to 45, a pad's Tune -24 to +24 semitones) */
function NI_kbTuneTarget(r){if(!r||!r.kick||!r.kick.exact)return null;const t=trkById(r.kick.id),I=t&&t.inst;if(!I)return null;const m=r.kick.endNote,R=r.key.root;
  let lo,hi,what,cur;if(I.preset==='kick'){cur=I.tune;lo=21;hi=45;what='the Kick designer\'s Pitch'}else if(I.preset==='drums'&&r.kick.pad!=null){const pd=I.pads[r.kick.pad];cur=pd.tune||0;lo=-24;hi=24;what=`the Tune of the drum pad "${pd.name||'Kick'}"`}else return null;
  let best=null;for(let n=R;n<=60;n+=12){const sm=n-m,v=cur+sm;if(v<lo-1e-9||v>hi+1e-9)continue;if(!best||Math.abs(sm)<Math.abs(best.semis))best={note:n,semis:sm}}
  if(!best||Math.abs(best.semis)<.005)return null;return{...best,txt:NI_noteTxt(best.note),what,value:Math.round((cur+best.semis)*100)/100}}
function NI_kbFixTune(){const r=NI.kbv.r,tf=NI_kbTuneTarget(r);if(!tf)return;const t=trkById(r.kick.id),I=t.inst;pushUndo();
  if(I.preset==='kick')I.tune=tf.value;else I.pads[r.kick.pad].tune=tf.value;try{if(typeof KCACHE!=='undefined')KCACHE.clear()}catch(_){}
  changed(true);toast(`The kick settles on ${tf.txt} now. Undo puts it back. Measuring again…`);NI_kbShow()}
/* the bass clips that play in the measured bar, if every note stays at C0 or above after moving down */
function NI_kbOctClips(r){if(!r||!r.bass||!r.bass.id||!r.bass.notes.length)return[];const t=trkById(r.bass.id);if(!t)return[];const{b0,b1}=r.bar;
  const L=t.clips.filter(c=>!c.mute&&c.notes&&c.start<b1&&c.start+c.len>b0);return L.every(c=>c.notes.every(n=>n.p-12>=12))?L:[]}
function NI_kbFixOct(){const r=NI.kbv.r,L=NI_kbOctClips(r);if(!L.length)return;pushUndo();const seen=new Set();for(const c of L)for(const n of c.notes){if(seen.has(n))continue;seen.add(n);n.p-=12}
  changed(true);toast(`The bass is an octave lower in ${L.length===1?'its clip':L.length+' clips'}. Undo puts it back. Measuring again…`);NI_kbShow()}
function NI_kbPlay(){const r=NI.kbv.r;if(!r||!r.bar)return;if(play.on)stop();S.loopRange={a:r.bar.b0,b:r.bar.b1};S.loop=true;pos=r.bar.b0;syncTransportUI();dirty=true;start();toast(`Looping bar ${r.bar.n}. The loop button turns it off.`)}
/* the picture: drawn once per measurement */
function NI_kbDraw(cv,r){if(!cv)return;const dpr=Math.min(2,window.devicePixelRatio||1),w=516,h=268;if(cv.width!==w*dpr){cv.width=w*dpr;cv.height=h*dpr}
  const g=cv.getContext('2d');g.setTransform(dpr,0,0,dpr,0,0);vbg(g,w,h);if(!r||!r.kick){txt(g,'Nothing measured',w/2,h/2,NI_KBC.lab,11,'center');return}
  const M0=12,M1=48,top=16,bot=h-44,y=m=>bot-(clamp(m,M0,M1)-M0)/(M1-M0)*(bot-top),rh=(bot-top)/(M1-M0),K=r.key,kx0=34,kx1=150,bx0=164,bx1=w-8,k=r.kick,kc=NI_KBC.kick;
  /* the ruler: one row per semitone, black keys darker, the key's notes lit, the root brightest, C labelled */
  for(let m=M0;m<M1;m++){const pc=((m%12)+12)%12,blk=[1,3,6,8,10].includes(pc),inK=K.pcs&&K.pcs.includes(pc),y1=y(m+1),hh=y(m)-y1;
    g.fillStyle=blk?'#15171d':'#2a2d36';g.fillRect(17,y1+.5,13,hh-1);if(inK){g.fillStyle=pc===K.root?'rgba(76,201,240,.6)':'rgba(76,201,240,.22)';g.fillRect(17,y1+.5,13,hh-1)}
    if(inK){g.fillStyle=pc===K.root?'rgba(76,201,240,.09)':'rgba(76,201,240,.035)';g.fillRect(kx0,y1,bx1-kx0,hh)}
    if(pc===0){g.fillStyle=NI_KBC.grid;g.fillRect(kx0,y(m),bx1-kx0,1);txt(g,'C'+(m/12-1),2,y(m)+3,'rgba(255,255,255,.75)',8)}}
  txt(g,'Kick, ms after the hit',kx0,11,NI_KBC.lab,9);txt(g,'Bar '+r.bar.n,bx0,11,NI_KBC.lab,9);
  /* the kick: its pitch over its life; above C3 it runs along the top edge */
  const life=Math.max(60,k.lifeMs),X=ms=>kx0+ms/life*(kx1-kx0);g.strokeStyle='rgba(255,255,255,.1)';g.strokeRect(kx0+.5,top+.5,kx1-kx0,bot-top);
  for(const ms of[0,100,200,300,400,500,600,800,1000,1500,2000])if(ms<=life){const x=X(ms);g.fillStyle=NI_KBC.grid;g.fillRect(x,top,1,bot-top);txt(g,String(ms),x,bot+10,NI_KBC.lab,8,ms?'center':'left')}
  if(!k.exact){g.fillStyle='rgba(255,107,107,.14)';const a=y(NI_midi(k.range.hi)),b=y(NI_midi(k.range.lo));g.fillRect(kx0,a-rh/2,bx1-kx0,Math.max(2,b-a+rh))}
  g.lineWidth=2;g.lineJoin='round';let prev=null;for(const p of k.curve){if(!(p.f>0)){prev=null;continue}const x=X(p.ms),yy=y(NI_midi(p.f));g.strokeStyle=`rgba(255,107,107,${clamp(.25+p.a*.75,0,1)})`;if(prev){g.beginPath();g.moveTo(prev[0],prev[1]);g.lineTo(x,yy);g.stroke()}prev=[x,yy]}
  const ye=y(k.endNote);g.setLineDash([4,3]);g.strokeStyle='rgba(255,107,107,.8)';g.lineWidth=1;g.beginPath();g.moveTo(kx0,ye+.5);g.lineTo(bx1,ye+.5);g.stroke();g.setLineDash([]);
  {const s=`${k.exact?k.endTxt:'about '+NI_noteTxt(k.endNote)}  ${k.endHz.toFixed(1)} Hz`;g.font='600 9px Inter,system-ui,sans-serif';const tw=g.measureText(s).width;const ty=ye<top+14?ye+11:ye-4;g.fillStyle='rgba(7,8,12,.75)';g.fillRect(kx1-tw-6,ty-9,tw+4,12);txt(g,s,kx1-4,ty,kc,9,'right')}
  /* the bar: beat lines, the kick's life on each hit, the bass notes */
  const{b0,b1}=r.bar,BX=b=>bx0+(b-b0)/(b1-b0)*(bx1-bx0);g.strokeStyle='rgba(255,255,255,.1)';g.strokeRect(bx0+.5,top+.5,bx1-bx0,bot-top);
  for(let b=Math.ceil(b0-1e-9);b<b1-1e-9;b++){const x=BX(b);g.fillStyle=b===b0?'rgba(255,255,255,.16)':NI_KBC.grid;g.fillRect(x,top,1,bot-top);txt(g,r.bar.n+'.'+(b-b0+1),x+2,bot+10,NI_KBC.lab,8)}
  for(const o of r.overlap){const x=BX(o.b),x2=BX(Math.min(b1,o.end));g.fillStyle='rgba(255,107,107,.45)';g.fillRect(x,ye-1,Math.max(2,x2-x),2);g.fillStyle=kc;g.fillRect(x,ye-rh*.5,2,rh)}
  const hatch=(x,yy,ww,hh)=>{g.save();g.beginPath();g.rect(x,yy,ww,hh);g.clip();g.strokeStyle='rgba(255,255,255,.55)';g.lineWidth=1;for(let i=-hh;i<ww;i+=4){g.beginPath();g.moveTo(x+i,yy+hh);g.lineTo(x+i+hh,yy);g.stroke()}g.restore()};
  const lab=new Set();for(const n of r.bass.notes){const s=n.pair.state,col=NI_KBC[s],x=BX(n.b),x2=BX(Math.min(b1,n.b+n.l)),yy=y(n.p)-rh*.45,ww=Math.max(3,x2-x-1),hh=rh*.9;
    if(n.p>M1||n.p<M0){txt(g,(n.p>M1?'↑ ':'↓ ')+n.txt,x,n.p>M1?top+9:bot-3,col,8);continue}
    if(s==='clash'){g.shadowColor=col;g.shadowBlur=8}g.fillStyle=col;g.fillRect(x,yy,ww,hh);g.shadowBlur=0;if(s==='clash')hatch(x,yy,ww,hh);
    const key=n.p+'|'+s;if(!lab.has(key)){lab.add(key);const t=s==='clash'?`${n.txt} beating at ${n.pair.beatHz.toFixed(1)} Hz`:s==='tuned'?n.txt+' in tune':n.txt;const ty=n.p<k.endNote?yy+hh+10:yy-4,tx=Math.min(x,bx1-100);g.font='8px Inter,system-ui,sans-serif';g.fillStyle='rgba(7,8,12,.8)';g.fillRect(tx-2,ty-8,g.measureText(t).width+4,11);txt(g,t,tx,ty,s==='clash'?'#ffb3b3':'rgba(255,255,255,.75)',8)}}
  if(!r.bass.notes.length)txt(g,r.bass.why||'No bass notes',(bx0+bx1)/2,(top+bot)/2,NI_KBC.lab,9,'center');
  /* the gap strip: kick lives and bass notes in time, the gap after each hit in ms */
  const gy=h-22,gh=12;g.fillStyle='rgba(255,255,255,.04)';g.fillRect(bx0,gy,bx1-bx0,gh);txt(g,'In time',kx1,gy+9,NI_KBC.lab,8,'right');
  for(const n of r.bass.notes){const x=BX(n.b),x2=BX(Math.min(b1,n.b+n.l));g.fillStyle='rgba(143,183,255,.75)';g.fillRect(x,gy+gh/2,Math.max(2,x2-x-1),gh/2)}
  for(const o of r.overlap){const x=BX(o.b),x2=BX(Math.min(b1,o.end));g.fillStyle='rgba(255,107,107,.8)';g.fillRect(x,gy,Math.max(2,x2-x),gh/2);
    if(o.gapMs!=null){const nx=r.bass.notes.find(q=>q.b>=o.b-1e-6);if(nx){const xa=BX(o.b),xb=BX(nx.b);if(xb-xa>26)txt(g,o.gapMs+' ms',(xa+xb)/2,gy+gh+9,NI_KBC.lab,8,'center')}}}
  txt(g,'kick',bx1,gy-2,'rgba(255,107,107,.9)',8,'right');txt(g,'bass',bx1-26,gy-2,'rgba(143,183,255,.9)',8,'right')}
document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&NI.kbv.el&&!NI.kbv.el.hidden){NI_kbClose();ev.stopPropagation()}},true);
document.addEventListener('pointerdown',ev=>{const W=NI.kbv.el;if(!W||W.hidden)return;if(W.contains(ev.target)||ev.target.closest('#toast,.menu,.ctx,#cmdk'))return;NI_kbClose()},true);
NI.kbOpen=NI_kbOpen;
/* ===== end of lane D NI-2b ===== */
"""
A4 = "function askChoice(title,text,btns,icon){"
s = put(s, A4, JS)
open(P, 'w', encoding='utf-8').write(s)
print('NI-2b applied')
