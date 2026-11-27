/* ===== lane N (task SQ1): the Quality switch, shown as one on/off switch "Hi-Fi" (the user's AE1 picks Q0a, Q0b and Q10; docs/quality-build.md) =====
   One switch for every sound-quality improvement, so that no loaded song changes its sound without the user's yes:
   - per device: the field q on an effect (f.q) and quality on an instrument (t.inst.quality: an instrument's own parameters sit on the
     same object and several already use q as a number: the Clap, Growl, Vector FM and Orbit), 'classic' or 'clean'; missing = follow the
     song; read it with sqOf(device) (SQ_HOOKS.of), never .q directly;
   - per song: S.sq, 'classic' or 'clean'; missing = 'classic' (every song saved before v0.294, the demos and the Fractals song);
     songs made in the New project window (empty, audio, instruments) start 'clean'; it is the default for devices without their own;
   - Classic is today's bits (the release gate's export check proves it); Clean is the improved sound of that device;
   - new devices (added after the song was opened: browser, paste, menus, the Assistant, lessons) get 'clean', except in a song the user
     set to Classic by hand (S.sq==='classic'), where they get 'classic';
   - "Hi-Fi everywhere" and "Hi-Fi off everywhere" (Settings > Project > Hi-Fi, the switch's menu, the command list) set the song
     and every device in one undo step.
   The value reaches the audio code as p._sq: a non-enumerable mirror on each effect's parameter object (never saved, never in undo, never in
   Object.keys), refreshed before syncGraph and the offline renders. A node keeps the last value it saw, so a copied p without the mirror
   keeps the device's quality. Instruments: lane L reads sqOf(t.inst) (or SQ_HOOKS.of).
   In the interface it is one switch named Hi-Fi (on = 'clean', off = 'classic'), with its short line next to it: a row at the bottom of
   the device's controls (the rail) on every device whose Hi-Fi sound differs (SQ.DEV; lane L adds its devices with SQ_HOOKS.reg), a chip in
   the title strip where a device has no rail. Lane I can place it in its own frame: set DV_HOOKS.placesQuality=true and call
   SQ_HOOKS.chip(deviceElement,true), which returns the row (switch and line) or null.
   Q10, the first Clean feature: the Soft Clipper with Asymmetry not 0 gets a one-pole DC blocker at 5 Hz after its output
   (y = x - x1 + R*y1, R = 1 - 2*pi*5/sr, in double, IIRFilterNode). Classic goes through a gain of exactly 1 (bit-identical). Biased
   shapers of lane L use SQ_HOOKS.dc(ctx) or the same formula in their worklets.
   Nothing here runs per frame: the scan runs in changed(), syncGraph and the offline renders, and is a loop over the devices. */
const SQ={v:'0.294',LV:1,S:null,known:new Set(),wr:false,
 DEV:{clip:'while Asymmetry is not 0, a DC blocker (5 Hz) after the clipper removes the slow offset that asymmetric clipping makes, so it no longer eats headroom or pushes the next limiter on one side.'},
 n:{scan:0,stamp:0}};
const SQ_HOOKS=window.SQ_HOOKS=Object.assign(window.SQ_HOOKS||{},{
 of:d=>sqOf(d),proj:()=>sqProj(),
 reg(key,text){if(typeof key==='string'&&key)SQ.DEV[key]=String(text||'a higher quality sound.');try{renderFx()}catch(e){}},
 dc:(c,hz)=>sqDcNode(c,hz),chip:(D,row)=>sqChipFor(D,row),useAll:q=>sqUseAll(q)});
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
/* the Hi-Fi switch in the device (the user's naming, 27 Nov 23:00 to 23:08 Brussels: one on/off switch "Hi-Fi", on = 'clean', off = 'classic',
   with its short line shown next to it, not only on hover). It sits as a row at the bottom of the device's controls (the rail, .dfs); a device
   without that rail gets a small Hi-Fi chip after its name in the title strip. */
const SQL={on:'Hi-Fi on: higher quality sound.',off:'Hi-Fi off: lighter and faster, good for slower computers or big projects.',
 old:'This song was made before Hi-Fi mode was implemented, so it plays as you made it. Turn Hi-Fi on for higher quality.'};
function sqKey(own,kind){return kind==='fx'?own.type:'inst:'+(own.preset||'')}
function sqOwn(D){if(!D||!D.dataset)return null;const t=typeof curT==='function'?curT():null;if(!t)return null;
 if(D.dataset.d==='fx'){const id=D.dataset.id;return(t.fx||[]).find(f=>f.id===id)||((typeof S==='object'&&S.mfx)||[]).find(f=>f.id===id)||null}
 return D.dataset.d==='inst'?t.inst||null:null}
/* the switch for device element D (or null for a device without a Hi-Fi sound); row: with its short line under it */
function sqChipFor(D,row){const own=sqOwn(D);if(!own)return null;const kind=D.dataset.d==='fx'?'fx':'inst',txt=SQ.DEV[sqKey(own,kind)];if(!txt)return null;
 const on=sqOf(own)==='clean',b=document.createElement('button');b.type='button';b.className='sqchip'+(on?' on':'');b.dataset.q=on?'clean':'classic';
 b.setAttribute('role','switch');b.setAttribute('aria-checked',String(on));b.setAttribute('aria-haspopup','menu');b.innerHTML='<i aria-hidden="true"></i>Hi-Fi';
 b.title=SQL.on+' '+SQL.off+' On this device: '+txt+(sqOwnQ(own)?'':' (It follows the song.)')+' Right-click for the whole song.';
 if(!row)return b;const r=document.createElement('div');r.className='sqrow';const l=document.createElement('small');l.className='sqln';l.textContent=on?SQL.on:SQL.off;r.append(b,l);r.dataset.k=b.dataset.q+'|'+b.title;return r}
function sqChips(){if(typeof window.DV_HOOKS==='object'&&DV_HOOKS&&DV_HOOKS.placesQuality)return;const root=document.getElementById('fxin');if(!root)return;
 for(const D of root.querySelectorAll('.dev[data-d=fx],.dev[data-d=inst]')){const rail=D.querySelector(':scope>.devb>.dfs'),h=D.querySelector('.devh');
  const oldR=D.querySelector('.sqrow'),oldC=h&&h.querySelector(':scope>.sqchip');
  if(rail){if(oldC)oldC.remove();const r=sqChipFor(D,true);if(!r){if(oldR)oldR.remove();continue}if(oldR&&oldR.dataset.k===r.dataset.k&&oldR.parentNode===rail)continue;if(oldR)oldR.remove();rail.appendChild(r);continue}
  if(oldR)oldR.remove();if(!h)continue;const b=sqChipFor(D,false);if(!b){if(oldC)oldC.remove();continue}if(oldC){if(oldC.title===b.title&&oldC.dataset.q===b.dataset.q)continue;oldC.replaceWith(b);continue}
  const nm=h.querySelector(':scope>span');nm?nm.after(b):h.appendChild(b)}}
function sqSet(D,q){const own=sqOwn(D);if(!own||sqOwnQ(own)===q)return;pushUndo();own[sqF(own)]=q;sqScan();changed(true);
 try{toast(q==='clean'?'Hi-Fi on for this device: higher quality sound.':'Hi-Fi off for this device: lighter and faster.')}catch(e){}}
function sqUseAll(q){if(q!=='clean'&&q!=='classic')return;if(typeof S!=='object'||!S)return;pushUndo();S.sq=q;for(const[d]of sqDevs(S))d[sqF(d)]=q;sqScan();changed(true);
 try{toast(q==='clean'?'Hi-Fi everywhere in this song. One undo puts it back.':'Hi-Fi off everywhere in this song. One undo puts it back.')}catch(e){}try{sqSync()}catch(e){}}
function sqMenu(D,x,y){const own=sqOwn(D);if(!own)return;const on=sqOf(own)==='clean',sp=sqProj()==='clean';
 openMenu(x,y,[{head:'Hi-Fi'},
  {label:'Hi-Fi on',check:on,sub:'Higher quality sound',act:()=>sqSet(D,'clean')},
  {label:'Hi-Fi off',check:!on,sub:'Lighter and faster',act:()=>sqSet(D,'classic')},'-',
  {head:'This song: Hi-Fi '+(sp?'on':'off')},
  {label:'Hi-Fi everywhere',sub:'Every device of this song, one undo step',act:()=>sqUseAll('clean')},
  {label:'Hi-Fi off everywhere',sub:'Every device of this song, one undo step',act:()=>sqUseAll('classic')}])}
addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('#fxin .sqchip');if(!b)return;e.stopImmediatePropagation();e.preventDefault();const D=b.closest('.dev');sqSet(D,b.dataset.q==='clean'?'classic':'clean')},true);
addEventListener('contextmenu',e=>{const b=e.target.closest&&e.target.closest('#fxin .sqchip');if(!b)return;e.preventDefault();e.stopImmediatePropagation();const r=b.getBoundingClientRect();sqMenu(b.closest('.dev'),e.clientX||r.left,e.clientY||r.bottom)},true);
addEventListener('keydown',e=>{const b=e.target.closest&&e.target.closest('#fxin .sqchip');if(!b)return;if(e.key==='ContextMenu'||(e.key==='F10'&&e.shiftKey)){e.preventDefault();e.stopImmediatePropagation();const r=b.getBoundingClientRect();sqMenu(b.closest('.dev'),r.left,r.bottom+2)}},true);
/* Settings > Project: Hi-Fi for the song (lane B's cards and table) */
const SQROW={id:'songHiFi',l:'Hi-Fi for this song',pg:'files',b:'Hi-Fi',sc:'project',k:'S.sq',c:'#sqProj',t:'check',
 h:SQL.on+' '+SQL.off+' Devices without their own choice follow the song; each device has its own Hi-Fi switch.',
 w:'hi-fi hifi high quality sound quality clean classic aliasing dc blocker oversampling resampling lighter faster song project'};
function sqCounts(){const n={clean:0,classic:0,own:0};if(typeof S!=='object'||!S)return n;for(const[d,,kind]of sqDevs(S)){if(!SQ.DEV[sqKey(d,kind)])continue;n[sqOf(d)]++;if(sqOwnQ(d))n.own++}return n}
function sqBuild(){if(document.getElementById('sqCard')||typeof ST5!=='object'||!ST5.done)return;const pg=ST5.sec('files');if(!pg)return;
 const c=ST5.card('sqCard','Hi-Fi','<p class="hint sqold" id="sqOld" hidden></p>'+
  '<label class="chk" title="'+esc(SQROW.h)+'"><input type="checkbox" id="sqProj" aria-label="'+esc(SQROW.l)+'"> Hi-Fi for this song</label>'+
  '<p class="hint" id="sqLine"></p><p class="hint" id="sqStat"></p><div class="st5btns"><button type="button" id="sqAllC" title="Turn Hi-Fi on for this song and every device in it. One undo step puts it back.">Hi-Fi everywhere</button><button type="button" id="sqAllK" title="Turn Hi-Fi off for this song and every device in it: lighter and faster. One undo step puts it back.">Hi-Fi off everywhere</button></div>');
 const ref=document.getElementById('st8New');ref&&ref.parentNode===pg?ref.after(c):pg.appendChild(c);
 document.getElementById('sqProj').addEventListener('change',e=>{const v=e.target.checked?'clean':'classic';if(typeof S!=='object'||!S||S.sq===v)return;pushUndo();S.sq=v;sqScan();changed(true);sqSync()});
 document.getElementById('sqAllC').addEventListener('click',()=>sqUseAll('clean'));document.getElementById('sqAllK').addEventListener('click',()=>sqUseAll('classic'));sqSync()}
/* the note for a song made before Hi-Fi: shown in one visit of the Settings window per song (S.sqSeen, no sound, no undo step) */
function sqOldNote(){const o=document.getElementById('sqOld');if(!o||typeof S!=='object'||!S)return;
 const show=S.sq===undefined&&(!S.sqSeen||(SQ.noteS===S&&SQ.noteO===SQ.opens));if(show&&!S.sqSeen){S.sqSeen=1;SQ.noteS=S;SQ.noteO=SQ.opens}
 if(o.hidden===show){o.hidden=!show;o.textContent=show?SQL.old:''}}
function sqSync(){const s=document.getElementById('sqProj');if(!s)return;const on=sqProj()==='clean';if(s.checked!==on)s.checked=on;
 const l=document.getElementById('sqLine'),lt=on?SQL.on:SQL.off;if(l&&l.textContent!==lt)l.textContent=lt;
 const n=sqCounts(),T=n.clean+n.classic,st=document.getElementById('sqStat');
 if(st){const h=!T?'No device in this song has a Hi-Fi sound of its own yet.':T+' device'+(T===1?'':'s')+' with Hi-Fi: '+n.clean+' on, '+n.classic+' off.';if(st.textContent!==h)st.textContent=h}
 const set=document.getElementById('set');if(set&&!set.hidden)sqOldNote()}
{if(typeof STT==='object'&&typeof STX==='object'&&!STX.has(SQROW.id)){const x=Object.assign({},SQROW);STT.push(x);STX.set(x.id,x)}
 const _s=ST5.show;ST5.show=function(){const x=_s.apply(this,arguments);try{sqBuild();sqSync()}catch(e){console.warn('Hi-Fi (SQ1)',e)}return x};
 const _o=openSettings;openSettings=function(){SQ.opens=(SQ.opens||0)+1;const x=_o.apply(this,arguments);setTimeout(()=>{try{sqBuild();sqSync()}catch(e){console.warn('Hi-Fi (SQ1)',e)}},0);return x};
 /* the scan before the audio code reads the devices, and the switches after the devices panel is drawn */
 const _c=changed;changed=function(){try{sqScan()}catch(e){console.warn('Hi-Fi (SQ1)',e)}const r=_c.apply(this,arguments);try{sqSync()}catch(e){}return r};
 const _g=syncGraph;syncGraph=function(){try{sqScan()}catch(e){}return _g.apply(this,arguments)};
 const _m=renderMix;renderMix=function(){try{sqScan()}catch(e){}return _m.apply(this,arguments)};
 const _k=renderMixChunked;renderMixChunked=function(){try{sqScan()}catch(e){}return _k.apply(this,arguments)};
 const _f=renderFx;renderFx=function(){const r=_f.apply(this,arguments);try{sqChips()}catch(e){console.warn('Hi-Fi (SQ1)',e)}return r};
 /* songs made in the New project window start with Hi-Fi on (the demo and the beat are the demos: they stay off) */
 const _n=npGo0;npGo0=function(){const k=typeof npT==='string'?npT:'',n0=PJ.list.length,r=_n.apply(this,arguments);try{if(k!=='demo'&&k!=='beat'&&PJ.list.length>n0){const p=PJ.list[PJ.list.length-1];if(p&&p.S&&!p.S.sq){p.S.sq='clean';if(p.S===S)sqScan()}}}catch(e){}return r};
 setTimeout(()=>{try{sqWrapClip();sqScan()}catch(e){}},0)}
/* the command list (SCA, read by lane H's registry) */
setTimeout(()=>{try{if(typeof SCA!=='undefined'&&typeof SCM!=='undefined'&&!SCM.has('sq.cleanAll')){
 SCA.push({id:'sq.cleanAll',g:'edit',l:'Hi-Fi everywhere in this song',d:'higher quality sound on every device of this song, one undo step',ic:'M4 10h12M10 4v12',run:()=>sqUseAll('clean')});SCM.set('sq.cleanAll',SCA[SCA.length-1]);
 SCA.push({id:'sq.classicAll',g:'edit',l:'Hi-Fi off everywhere in this song',d:'lighter and faster on every device of this song, one undo step',ic:'M4 10h12',run:()=>sqUseAll('classic')});SCM.set('sq.classicAll',SCA[SCA.length-1])}}catch(e){}},0);
/* ===== end of lane N SQ1 ===== */
