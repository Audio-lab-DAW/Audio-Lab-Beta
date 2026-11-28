/* ===== task MX-5 (lane K, mixing engine): Dual Path Latency (the user's play-through idea, X7 replaced; docs/mixing-build.md) =====
   Off by default, turned on in Settings, Audio (UI.mxDpl). While you play a track (lane J's rule: armed, or the selected instrument while the
   computer keyboard plays, and lane J's played-track exception on), that track keeps its slow devices but does not wait for them:
   - look-ahead devices run a quick stand-in: the Limiter with 1 sample of look-ahead, the Gate without look-ahead, the Soft Clipper without
     oversampling;
   - a latent device with a Mix knob (Drive, Vocoder) plays its dry part at once and its wet part when it is ready (two paths: the device at full
     wet, scaled by Mix, and the dry part around it, scaled by 1 - Mix).
   Every other track, playback of tracks you are not playing, and every export (renderMix builds its own nodes from f.p) use the exact version.
   Nothing is built while it is off: the set() wrapper passes f.p through untouched and syncGraph wires exactly as before. */
const MXDPL={sig:'',split:new Set(['drive','vocoder']),name:'Dual Path Latency',tag:'AudioLab Pro Technology',
 tagLine:'AudioLab Pro Technology. Other DAWs turn slow devices off to cut latency; Dual Path Latency keeps them and brings them back in sync.',
 help:'While you play a track (armed, or with the computer keyboard), its slow devices keep running and nothing waits for them: the part that is ready sounds at once and the slow part joins a moment later, in time. Look-ahead devices use a quick stand-in while you play. Tracks you are not playing, playback and every export use the exact version. Off unless you turn it on.'};
const MX_ATOM='<svg class="mxatom" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="1"/><path d="M20.2 20.2c2.04-2.03.02-7.36-4.5-11.9-4.54-4.52-9.87-6.54-11.9-4.5-2.04 2.03-.02 7.36 4.5 11.9 4.54 4.52 9.87 6.54 11.9 4.5Z"/><path d="M15.7 15.7c4.52-4.54 6.54-9.87 4.5-11.9-2.03-2.04-7.36-.02-11.9 4.5-4.52 4.54-6.54 9.87-4.5 11.9 2.03 2.04 7.36.02 11.9-4.5Z"/></svg>';
function mxDplLive(){if(UI.mxDpl!==true||UI.ltPdc===false)return[];try{return liveTracks()}catch(e){return[]}}
function mxDplOn(t){if(!t||UI.mxDpl!==true||UI.ltPdc===false)return false;return mxDplLive().includes(t)}
/* the stand-in parameters while you play (a copy; f.p itself is never changed) */
function mxDplStand(type,p){if(!p)return p;switch(type){
  case'limit':return Object.assign({},p,{look:.02});
  case'gate':return p.look>0?Object.assign({},p,{look:0}):p;
  case'clip':return p.os!=='none'?Object.assign({},p,{os:'none'}):p}
 return MXDPL.split.has(type)?Object.assign({},p,{mix:100}):p}
/* the device's own set(): one wrapper per node, the track looked up at call time */
function mxDplWrap(N,t){for(const f of t.fx){const x=N.fxm.get(f.id);if(!x||typeof x.set!=='function')continue;x._mxT=t.id;x._mxFid=f.id;x._mxTy=f.type;
  if(!x._mxSet){const o=x.set;x._mxSet=o;x.set=function(p){let q=p;try{const T=trkById(this._mxT);if(mxDplOn(T)){q=mxDplStand(this._mxTy,p);const NN=NODES.get(this._mxT),D=NN&&NN.mxDS&&NN.mxDS.get(this._mxFid);if(D)mxDplMix(D,p)}}catch(e){q=p}return o.call(this,q)}}}}
const mxDplSplitOk=(t,f)=>MXDPL.split.has(f.type)&&f.on&&!t.fxByp&&fxLat(f,ctx?ctx.sampleRate:48000)>0;
function mxDplSig(t){if(!mxDplOn(t))return'';return'P'+t.fx.filter(f=>mxDplSplitOk(t,f)).map(f=>f.id).join('.')+'|'}
function mxDplMix(D,p){const m=Math.max(0,Math.min(1,(p&&p.mix!=null?p.mix:100)/100)),now=ctx.currentTime;D.dg.gain.setTargetAtTime(1-m,now,.005);D.wg.gain.setTargetAtTime(m,now,.005)}
/* the two paths are taken down whenever the chain is wired again */
function mxDplCut(N){if(!N.mxDS)return;for(const[id,D] of N.mxDS){for(const n of[D.dg,D.wg,D.sum])try{n.disconnect()}catch(e){}}}
/* one link of the chain: the device, or the device and its dry path around it */
function mxDplLink(N,t,f,x,prev){if(!(mxDplOn(t)&&mxDplSplitOk(t,f))){prev.connect(x.in);return x.out}
 N.mxDS=N.mxDS||new Map();let D=N.mxDS.get(f.id);if(!D){D={dg:ctx.createGain(),wg:ctx.createGain(),sum:ctx.createGain()};D.dg.gain.value=0;D.wg.gain.value=1;N.mxDS.set(f.id,D)}
 prev.connect(x.in);prev.connect(D.dg);x.out.connect(D.wg);D.dg.connect(D.sum);D.wg.connect(D.sum);mxDplMix(D,f.p);return D.sum}
/* what the track's devices delay while you play with Dual Path Latency (the dry part of a split device is at once) */
function mxDplLat(t,sr){sr=sr||(ctx?ctx.sampleRate:48000);if(!t||t.fxByp)return 0;let n=0;for(const f of t.fx){if(!f.on)continue;if(MXDPL.split.has(f.type)&&(f.p&&f.p.mix!=null?f.p.mix:100)<100)continue;n+=fxLat({on:true,type:f.type,p:mxDplStand(f.type,f.p||{})},sr)}return n}
/* who plays changes after a click or a key: the graph is brought up to date only when Dual Path Latency is on and the played tracks changed */
function mxDplEval(){if(UI.mxDpl!==true)return;clearTimeout(mxDplEval.t);mxDplEval.t=setTimeout(()=>{if(!ctx)return;const s=mxDplLive().map(t=>t.id).join(',');if(s!==MXDPL.sig){MXDPL.sig=s;syncGraph()}},130)}
document.addEventListener('pointerup',mxDplEval,true);document.addEventListener('keyup',mxDplEval,true);
function mxDplSet(on){on=!!on;if((UI.mxDpl===true)===on)return;if(on)UI.mxDpl=true;else delete UI.mxDpl;try{saveUI()}catch(e){}MXDPL.sig=mxDplLive().map(t=>t.id).join(',');if(ctx)syncGraph();mxDplSync();if(on&&!UI.mxDplSeen)mxDplFirst()}
/* ---- Settings, Audio: the card (lane B's cards and table: an STT row with its control) ---- */
const MXDPL_ROW={id:'mxDpl',l:'Dual Path Latency',pg:'audio',b:'Dual Path Latency',sc:'app',k:'UI.mxDpl',c:'#mxDplChk',t:'check',d:false,h:MXDPL.help,
 w:'dual path latency play through monitoring slow devices look-ahead lookahead stand-in live armed keyboard low latency delay audiolab pro technology'};
const mxDplTag=()=>'<span class="mxtag" title="'+esc(MXDPL.tagLine)+'">'+MX_ATOM+esc(MXDPL.tag)+'</span>';
const MXDPL_PIC='<svg class="mxdplpic" viewBox="0 0 240 62" aria-hidden="true"><path class="ax" d="M30 4v40M8 44h226"/><text x="34" y="11">you play</text>'+
 '<rect class="fa" x="30" y="16" width="96" height="9" rx="2"/><text x="132" y="24">fast part: at once</text>'+
 '<rect class="sl" x="52" y="30" width="74" height="9" rx="2"/><text x="132" y="38">slow part: joins in time</text><path class="ar" d="M32 34.5h17m-4-3 4 3-4 3"/>'+
 '<text x="8" y="58" class="lo">playback and export: exact</text></svg>';
function mxDplBuild(){if(document.getElementById('mxDplCard')||typeof ST5!=='object'||!ST5.done)return;const pg=ST5.sec('audio');if(!pg)return;
 const c=ST5.card('mxDplCard',esc(MXDPL.name)+mxDplTag(),'<label class="chk" title="'+esc(MXDPL.help)+'"><input type="checkbox" id="mxDplChk" data-al="settings.dualPath" aria-label="'+esc(MXDPL.name)+'"> Dual Path Latency while you play</label>'+
  '<p class="hint" id="mxDplLine"></p><div class="mxdplfirst" id="mxDplFirst" hidden>'+MXDPL_PIC+'<p>'+esc(MXDPL.tagLine)+'</p><p class="hint">'+esc('While you play, the part that is ready sounds at once and slow devices join a moment later, in time. Look-ahead devices use a quick stand-in. Playback and exports stay exact.')+'</p><button type="button" id="mxDplOk" data-al="settings.dualPathOk" title="Hide this note. It does not come back.">Got it</button></div>');
 pg.appendChild(c);
 document.getElementById('mxDplChk').addEventListener('change',e=>mxDplSet(e.target.checked));
 document.getElementById('mxDplOk').addEventListener('click',()=>{UI.mxDplSeen=1;try{saveUI()}catch(e){}const f=document.getElementById('mxDplFirst');if(f)f.hidden=true});mxDplSync()}
function mxDplSync(){const c=document.getElementById('mxDplChk');if(!c)return;const on=UI.mxDpl===true;if(c.checked!==on)c.checked=on;
 const l=document.getElementById('mxDplLine');if(l){const L=on?mxDplLive():[],t=L[0],a=t?trkLat(t,ctx?ctx.sampleRate:48000):0,b=t?mxDplLat(t):0,sr=ctx?ctx.sampleRate:48000,ms=n=>(n/sr*1000).toFixed(1)+' ms';
  const s=!on?'Off: a track you play waits for its slow devices, as in other studios.':t?'On. '+t.name+' plays through its devices in '+ms(b)+' instead of '+ms(a)+'.':'On. It works on the track you play: arm a track or play with the computer keyboard.';if(l.textContent!==s)l.textContent=s}}
/* the first time it is turned on: one card inside the Settings card (not a pop-up) */
function mxDplFirst(){const f=document.getElementById('mxDplFirst');if(!f)return;f.hidden=false;UI.mxDplSeen=1;try{saveUI()}catch(e){}}
{if(typeof STT==='object'&&typeof STX==='object'&&!STX.has(MXDPL_ROW.id)){const x=Object.assign({},MXDPL_ROW);STT.push(x);STX.set(x.id,x)}
 const _s=ST5.show;ST5.show=function(){const x=_s.apply(this,arguments);try{mxDplBuild();mxDplSync()}catch(e){console.warn('Dual Path Latency (MX-5)',e)}return x};
 const _o=openSettings;openSettings=function(){const x=_o.apply(this,arguments);setTimeout(()=>{try{mxDplBuild();mxDplSync()}catch(e){console.warn('Dual Path Latency (MX-5)',e)}},0);return x};
 setTimeout(()=>{try{if(typeof XT_SET_NS==='object'&&XT_SET_NS&&!XT_SET_NS.mxDpl)XT_SET_NS.mxDpl='audio.dualPath'}catch(e){}},0)}
/* the command list (SCA, read by lane H's registry) */
setTimeout(()=>{try{if(typeof SCA!=='undefined'&&typeof SCM!=='undefined'&&!SCM.has('mx.dualPath')){
 SCA.push({id:'mx.dualPath',g:'edit',l:'Dual Path Latency on or off',d:'the track you play sounds at once, slow devices join in time; exports stay exact',ic:'M4 7h9M4 13h5M13 13h3M15 4l3 3-3 3',run:()=>{mxDplSet(UI.mxDpl!==true);toast(UI.mxDpl===true?'Dual Path Latency is on: the track you play sounds at once, slow devices join in time.':'Dual Path Latency is off.')}});SCM.set('mx.dualPath',SCA[SCA.length-1])}}catch(e){}},0);
/* ---- About: a small "AudioLab Pro Technology" section before "Under the hood" ---- */
function mxDplAbout(){return'<div class="mxab" id="mxAbout"><div class="mxabH">'+MX_ATOM+'<span>'+esc(MXDPL.tag)+'</span></div><div class="mxabR" title="'+esc(MXDPL.tagLine)+'"><b>'+esc(MXDPL.name)+'</b><span>While you play, the fast part sounds at once and slow devices join in time; exports stay exact.</span><span class="mxabBy">Designed by Ilja V. Jakovliev</span></div></div>'}
{const _a=ahfHtml;ahfHtml=function(){let h='';try{h=mxDplAbout()}catch(e){}return h+_a.apply(this,arguments)}}
/* hooks: lane E's meters or lane I's title strip may show the live number */
window.MX_HOOKS=window.MX_HOOKS||{};MX_HOOKS.dpl={on:t=>mxDplOn(t),lat:t=>mxDplLat(t),name:MXDPL.name,tag:MXDPL.tag};
/* ===== end of task MX-5 ===== */
