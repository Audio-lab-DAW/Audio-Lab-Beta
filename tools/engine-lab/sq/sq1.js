/* ===== lane N (task SQ1): the Quality switch, Classic / Clean (the user's AE1 picks Q0a, Q0b and Q10; docs/quality-build.md) =====
   One switch for every sound-quality improvement, so that no loaded song changes its sound without the user's yes:
   - per device: the field q on an effect (f.q) and quality on an instrument (t.inst.quality: an instrument's own parameters sit on the
     same object and several already use q as a number: the Clap, Growl, Vector FM and Orbit), 'classic' or 'clean'; missing = follow the
     song; read it with sqOf(device) (SQ_HOOKS.of), never .q directly;
   - per song: S.sq, 'classic' or 'clean'; missing = 'classic' (every song saved before v0.294, the demos and the Fractals song);
     songs made in the New project window (empty, audio, instruments) start 'clean'; it is the default for devices without their own;
   - Classic is today's bits (the release gate's export check proves it); Clean is the improved sound of that device;
   - new devices (added after the song was opened: browser, paste, menus, the Assistant, lessons) get 'clean', except in a song the user
     set to Classic by hand (S.sq==='classic'), where they get 'classic';
   - "Use Clean everywhere" and "Use Classic everywhere" (Settings > Project > Sound quality, the chip's menu, the command list) set the song
     and every device in one undo step.
   The value reaches the audio code as p._sq: a non-enumerable mirror on each effect's parameter object (never saved, never in undo, never in
   Object.keys), refreshed before syncGraph and the offline renders. A node keeps the last value it saw, so a copied p without the mirror
   keeps the device's quality. Instruments: lane L reads sqOf(t.inst) (or SQ_HOOKS.of).
   The chip: a small Classic / Clean pill in the title strip of every device whose Clean sound differs (SQ.DEV; lane L adds its devices with
   SQ_HOOKS.reg). Lane I can place it in its own frame: set DV_HOOKS.placesQuality=true and call SQ_HOOKS.chip(deviceElement), which returns
   the button (or null); until then it is put after the device name here.
   Q10, the first Clean feature: the Soft Clipper with Asymmetry not 0 gets a one-pole DC blocker at 5 Hz after its output
   (y = x - x1 + R*y1, R = 1 - 2*pi*5/sr, in double, IIRFilterNode). Classic goes through a gain of exactly 1 (bit-identical). Biased
   shapers of lane L use SQ_HOOKS.dc(ctx) or the same formula in their worklets.
   Nothing here runs per frame: the scan runs in changed(), syncGraph and the offline renders, and is a loop over the devices. */
const SQ={v:'0.294',LV:1,S:null,known:new Set(),wr:false,
 DEV:{clip:'Clean: while Asymmetry is not 0, a DC blocker (5 Hz) after the clipper removes the slow offset that asymmetric clipping makes, so it no longer eats headroom or pushes the next limiter on one side.'},
 CL:'Classic: the sound this device had before the Quality switch, bit for bit.',
 n:{scan:0,stamp:0}};
const SQ_HOOKS=window.SQ_HOOKS=Object.assign(window.SQ_HOOKS||{},{
 of:d=>sqOf(d),proj:()=>sqProj(),
 reg(key,text){if(typeof key==='string'&&key)SQ.DEV[key]=String(text||'Clean: the improved sound of this device.');try{renderFx()}catch(e){}},
 dc:(c,hz)=>sqDcNode(c,hz),chip:D=>sqChipFor(D),useAll:q=>sqUseAll(q)});
function sqProj(s){s=s===undefined?(typeof S==='object'?S:null):s;return s&&(s.sq==='clean'||s.sq==='classic')?s.sq:'classic'}
function sqF(d){return d&&d.preset===undefined&&typeof d.type==='string'&&d.p&&typeof d.p==='object'?'q':'quality'}
function sqOwnQ(d){const v=d&&d[sqF(d)];return v==='clean'||v==='classic'?v:null}
function sqOf(d,s){return sqOwnQ(d)||sqProj(s)}
function sqNewQ(){return typeof S==='object'&&S&&S.sq==='classic'?'classic':'clean'}
/* every device of a song: [object, key, kind, track] */
function sqDevs(s){const out=[];if(!s||!Array.isArray(s.tracks))return out;
 for(const t of s.tracks){if(t.inst&&typeof t.inst==='object')out.push([t.inst,'i:'+t.id+':'+(t.inst.preset||''),'inst',t]);for(const f of t.fx||[])if(f&&f.id)out.push([f,f.id,'fx',t])}
 for(const f of s.mfx||[])if(f&&f.id)out.push([f,f.id,'fx',null]);return out}
function sqMirror(d){const p=d&&d.p;if(!p||typeof p!=='object')return;const v=sqOf(d);if(p._sq===v)return;try{Object.defineProperty(p,'_sq',{value:v,enumerable:false,writable:true,configurable:true})}catch(e){}}
/* the scan: a new song object (opened, switched, undone, built by a script) is taken as it is; a device not seen before in the same song is new */
function sqScan(){if(typeof S!=='object'||!S)return;sqWrapClip();SQ.n.scan++;const base=SQ.S!==S;if(base){SQ.S=S;SQ.known.clear()}
 for(const[d,k,kind]of sqDevs(S)){const f=sqF(d);if(!base&&!SQ.known.has(k)&&d[f]===undefined){d[f]=sqNewQ();SQ.n.stamp++}SQ.known.add(k);if(kind==='fx')sqMirror(d)}}
/* Q10: the DC blocker */
function sqDcNode(c,hz){const R=1-2*Math.PI*(hz||5)/c.sampleRate;return c.createIIRFilter([1,-1],[1,-R])}
function sqWrapClip(){if(SQ.wr)return;let N;try{N=NDN}catch(e){return}if(!N||typeof N.clip!=='function')return;SQ.wr=true;const mk=N.clip;SQ.raw=mk;/* the device without the switch, for the tests */
 N.clip=function(c){const x=mk.apply(this,arguments);if(!x||!x.out||typeof x.set!=='function'||!c.createIIRFilter)return x;
  const o=x.out,sw=c.createGain(),dc=sqDcNode(c,5),st=x.set;let on=false,q=null;o.connect(sw);dc.connect(sw);x.out=sw;x.sqDc=()=>on;
  x.set=function(p){const r=st.apply(this,arguments);if(p&&(p._sq==='clean'||p._sq==='classic'))q=p._sq;const want=q==='clean'&&!!(p&&+p.bias);
   if(want!==on){on=want;try{o.disconnect(want?sw:dc)}catch(e){}o.connect(want?dc:sw)}return r};
  return x}}
/* the chip */
function sqKey(own,kind){return kind==='fx'?own.type:'inst:'+(own.preset||'')}
function sqOwn(D){if(!D||!D.dataset)return null;const t=typeof curT==='function'?curT():null;if(!t)return null;
 if(D.dataset.d==='fx'){const id=D.dataset.id;return(t.fx||[]).find(f=>f.id===id)||((typeof S==='object'&&S.mfx)||[]).find(f=>f.id===id)||null}
 return D.dataset.d==='inst'?t.inst||null:null}
function sqChipFor(D){const own=sqOwn(D);if(!own)return null;const kind=D.dataset.d==='fx'?'fx':'inst',txt=SQ.DEV[sqKey(own,kind)];if(!txt)return null;
 const q=sqOf(own),b=document.createElement('button');b.type='button';b.className='sqchip'+(q==='clean'?' on':'');b.dataset.q=q;b.textContent=q==='clean'?'Clean':'Classic';
 b.setAttribute('aria-label','Sound quality: '+b.textContent);b.setAttribute('aria-haspopup','menu');
 b.title='Sound quality of this device: '+b.textContent+(sqOwnQ(own)?'':' (as the song)')+'. '+(q==='clean'?txt:SQ.CL)+' Click to switch to '+(q==='clean'?'Classic':'Clean')+'; right-click for the whole song.';return b}
function sqChips(){if(typeof window.DV_HOOKS==='object'&&DV_HOOKS&&DV_HOOKS.placesQuality)return;const root=document.getElementById('fxin');if(!root)return;
 for(const D of root.querySelectorAll('.dev[data-d=fx],.dev[data-d=inst]')){const h=D.querySelector('.devh');if(!h)continue;const old=h.querySelector(':scope>.sqchip');const b=sqChipFor(D);
  if(!b){if(old)old.remove();continue}if(old){if(old.title===b.title&&old.dataset.q===b.dataset.q)continue;old.replaceWith(b);continue}
  const nm=h.querySelector(':scope>span');nm?nm.after(b):h.appendChild(b)}}
function sqSet(D,q){const own=sqOwn(D);if(!own||sqOwnQ(own)===q)return;pushUndo();own[sqF(own)]=q;sqScan();changed(true);
 try{toast((q==='clean'?'Clean':'Classic')+' sound on this device.'+(q==='clean'?'':' It sounds as it did before the Quality switch.'))}catch(e){}}
function sqUseAll(q){if(q!=='clean'&&q!=='classic')return;if(typeof S!=='object'||!S)return;pushUndo();S.sq=q;for(const[d]of sqDevs(S))d[sqF(d)]=q;sqScan();changed(true);
 try{toast(q==='clean'?'Clean sound everywhere in this song. One undo puts it back.':'Classic sound everywhere in this song: as before the Quality switch. One undo puts it back.')}catch(e){}try{sqSync()}catch(e){}}
function sqMenu(D,x,y){const own=sqOwn(D);if(!own)return;const q=sqOf(own),sp=sqProj();
 openMenu(x,y,[{head:'Sound quality'},
  {label:'Clean',check:q==='clean',sub:'The improved sound of this device',act:()=>sqSet(D,'clean')},
  {label:'Classic',check:q==='classic',sub:'As before the Quality switch, bit for bit',act:()=>sqSet(D,'classic')},'-',
  {head:'This song ('+(sp==='clean'?'Clean':'Classic')+')'},
  {label:'Use Clean everywhere',sub:'Every device of this song, one undo step',act:()=>sqUseAll('clean')},
  {label:'Use Classic everywhere',sub:'Every device of this song, one undo step',act:()=>sqUseAll('classic')}])}
addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('#fxin .sqchip');if(!b)return;e.stopImmediatePropagation();e.preventDefault();const D=b.closest('.dev');sqSet(D,b.dataset.q==='clean'?'classic':'clean')},true);
addEventListener('contextmenu',e=>{const b=e.target.closest&&e.target.closest('#fxin .sqchip');if(!b)return;e.preventDefault();e.stopImmediatePropagation();const r=b.getBoundingClientRect();sqMenu(b.closest('.dev'),e.clientX||r.left,e.clientY||r.bottom)},true);
addEventListener('keydown',e=>{const b=e.target.closest&&e.target.closest('#fxin .sqchip');if(!b)return;if(e.key==='ContextMenu'||(e.key==='F10'&&e.shiftKey)){e.preventDefault();e.stopImmediatePropagation();const r=b.getBoundingClientRect();sqMenu(b.closest('.dev'),r.left,r.bottom+2)}},true);
/* Settings > Project: the song's quality (lane B's cards and table) */
const SQROW={id:'songQuality',l:'Sound quality of this song',pg:'files',b:'Sound quality',sc:'project',k:'S.sq',c:'#sqProj',t:'select',
 h:'Classic keeps the sound AudioLab had before the Quality switch, bit for bit. Clean uses the improved sound where a device has one. Devices without their own choice follow the song; each device can still differ (its Classic / Clean chip).',
 w:'sound quality classic clean aliasing dc blocker oversampling resampling hi quality high quality improved song project'};
function sqCounts(){const n={clean:0,classic:0,own:0};if(typeof S!=='object'||!S)return n;for(const[d,,kind]of sqDevs(S)){if(!SQ.DEV[sqKey(d,kind)])continue;n[sqOf(d)]++;if(sqOwnQ(d))n.own++}return n}
function sqBuild(){if(document.getElementById('sqCard')||typeof ST5!=='object'||!ST5.done)return;const pg=ST5.sec('files');if(!pg)return;
 const c=ST5.card('sqCard','Sound quality','<p class="hint">Classic keeps the sound AudioLab had before, bit for bit: every song you made opens in Classic. Clean uses the improved sound where a device has one. New devices start Clean.</p>'+
  '<div class="cprow st8r" title="'+esc(SQROW.h)+'"><span>This song</span><select id="sqProj" aria-label="'+esc(SQROW.l)+'"><option value="classic">Classic (as before)</option><option value="clean">Clean</option></select></div>'+
  '<p class="hint" id="sqStat"></p><div class="st5btns"><button type="button" id="sqAllC" title="Set this song and every device in it to Clean. One undo step puts it back.">Use Clean everywhere</button><button type="button" id="sqAllK" title="Set this song and every device in it to Classic, the sound before the Quality switch. One undo step puts it back.">Use Classic everywhere</button></div>');
 const ref=document.getElementById('st8New');ref&&ref.parentNode===pg?ref.after(c):pg.appendChild(c);
 document.getElementById('sqProj').addEventListener('change',e=>{const v=e.target.value;if(v!=='clean'&&v!=='classic'||typeof S!=='object'||!S||S.sq===v)return;pushUndo();S.sq=v;sqScan();changed(true);sqSync()});
 document.getElementById('sqAllC').addEventListener('click',()=>sqUseAll('clean'));document.getElementById('sqAllK').addEventListener('click',()=>sqUseAll('classic'));sqSync()}
function sqSync(){const s=document.getElementById('sqProj');if(!s)return;const v=sqProj();if(s.value!==v&&document.activeElement!==s)s.value=v;const n=sqCounts(),T=n.clean+n.classic,st=document.getElementById('sqStat');
 if(st){const h=!T?'No device in this song has a Clean sound of its own yet.':T+' device'+(T===1?'':'s')+' with a Clean sound: '+n.clean+' Clean, '+n.classic+' Classic.';if(st.textContent!==h)st.textContent=h}}
{if(typeof STT==='object'&&typeof STX==='object'&&!STX.has(SQROW.id)){const x=Object.assign({},SQROW);STT.push(x);STX.set(x.id,x)}
 const _s=ST5.show;ST5.show=function(){const x=_s.apply(this,arguments);try{sqBuild();sqSync()}catch(e){console.warn('sound quality (SQ1)',e)}return x};
 const _o=openSettings;openSettings=function(){const x=_o.apply(this,arguments);setTimeout(()=>{try{sqBuild();sqSync()}catch(e){console.warn('sound quality (SQ1)',e)}},0);return x};
 /* the scan before the audio code reads the devices, and the chips after the devices panel is drawn */
 const _c=changed;changed=function(){try{sqScan()}catch(e){console.warn('sound quality (SQ1)',e)}const r=_c.apply(this,arguments);try{sqSync()}catch(e){}return r};
 const _g=syncGraph;syncGraph=function(){try{sqScan()}catch(e){}return _g.apply(this,arguments)};
 const _m=renderMix;renderMix=function(){try{sqScan()}catch(e){}return _m.apply(this,arguments)};
 const _k=renderMixChunked;renderMixChunked=function(){try{sqScan()}catch(e){}return _k.apply(this,arguments)};
 const _f=renderFx;renderFx=function(){const r=_f.apply(this,arguments);try{sqChips()}catch(e){console.warn('sound quality (SQ1)',e)}return r};
 /* songs made in the New project window start Clean (the demo and the beat are the demos: they stay Classic) */
 const _n=npGo0;npGo0=function(){const k=typeof npT==='string'?npT:'',n0=PJ.list.length,r=_n.apply(this,arguments);try{if(k!=='demo'&&k!=='beat'&&PJ.list.length>n0){const p=PJ.list[PJ.list.length-1];if(p&&p.S&&!p.S.sq){p.S.sq='clean';if(p.S===S)sqScan()}}}catch(e){}return r};
 setTimeout(()=>{try{sqWrapClip();sqScan()}catch(e){}},0)}
/* the command list (SCA, read by lane H's registry) */
setTimeout(()=>{try{if(typeof SCA!=='undefined'&&typeof SCM!=='undefined'&&!SCM.has('sq.cleanAll')){
 SCA.push({id:'sq.cleanAll',g:'edit',l:'Use Clean sound everywhere in this song',d:'sound quality: every device and the song, one undo step',ic:'M4 10h12M10 4v12',run:()=>sqUseAll('clean')});SCM.set('sq.cleanAll',SCA[SCA.length-1]);
 SCA.push({id:'sq.classicAll',g:'edit',l:'Use Classic sound everywhere in this song',d:'sound quality: as before the Quality switch, one undo step',ic:'M4 10h12',run:()=>sqUseAll('classic')});SCM.set('sq.classicAll',SCA[SCA.length-1])}}catch(e){}},0);
/* ===== end of lane N SQ1 ===== */
