/* ===== v0.315 (task ST-S11, lane B): settings step S11, audio devices in the picked design B2 =====
   Settings › Audio opens with a Devices card: two role cards, "Listen through" (the output) and "Record from" (the input), and two setups,
   Listening and Recording, chosen with one switch. The Recording setup fills itself: the input that looks most like an audio interface
   (the device profiles, the kind AudioLab reads from the label, the same groupId or name on an output), and that same device's output when it
   has one, so input and output share one clock; anything can be changed by hand and "Fill automatically again" forgets the hand choice.
   Arming an audio track (or any track, or never: a setting) switches to Recording by itself without asking (the user's answer 1), with a
   short quiet notice and "Back to Listening"; when no such track is armed any more AudioLab goes back to Listening, but only when it was
   AudioLab that switched. Switching between setups and devices used before is instant (answer 4): the output is ramped down for 25 ms, the
   device is switched, and it is ramped up again over 30 ms, so it does not click (no ramp when nothing is running). The 1.5 s fade for a new or
   returning device and the safe volume are step S13. Armed audio tracks are opened again on the new input. The same code on macOS and Windows:
   Windows' "Communications" and the system's "Default" entries are left out, names like "Microphone (Zoom AMS-24)" and "Speakers (Zoom
   AMS-24)" are matched by the part in brackets, USB ids "(1235:8210)" by Chromium on a Mac are ignored. Stored keys: UI.st11 (the setups) and
   UI.st11arm; UI.sink and UI.inDev stay the live output and input as before, and an older profile's input becomes the Recording input. */
const STS11={v:'0.315'};
const ST11={done:false,busy:0,q:Promise.resolve(),nt:0,tk:0,
 $:id=>document.getElementById(id),
 S(){let s=UI.st11;if(!s||typeof s!=='object'){s=UI.st11={on:'listen',L:{o:UI.sink||'',i:UI.inDev||''},R:{o:null,i:UI.inDev?UI.inDev:null},auto:0};try{saveUI()}catch(e){}}
  if(!s.L)s.L={o:UI.sink||'',i:UI.inDev||''};if(!s.R)s.R={o:null,i:null};if(s.on!=='rec')s.on='listen';return s},
 arm(){const v=UI.st11arm;return v==='any'||v==='off'?v:'audio'},
 trig(t){const a=ST11.arm();return !!t&&a!=='off'&&(t.kind==='audio'||(a==='any'&&t.kind==='inst'))},
 /* the name a device has on both systems: "Speakers (Zoom AMS-24)" on Windows and "Zoom AMS-24 (1686:0428)" on a Mac both give "zoom ams 24" */
 core(l){l=String(l||'').toLowerCase().replace(/^(default|communications) - /,'').replace(/\([0-9a-f]{4}:[0-9a-f]{4}\)/g,'').trim();const m=/\(([^()]+)\)\s*$/.exec(l);if(m&&m[1].trim())l=m[1];return l.replace(/[^a-z0-9]+/g,' ').trim()},
 /* "Speakers (Zoom AMS-24)" says "Zoom AMS-24" when one device both records and plays (Windows names each side of a device) */
 short(l){const m=/^(speakers|headphones|line|line out|line in|microphone|mic|digital audio[^(]*|in [0-9][^(]*|out [0-9][^(]*)\s*\((.+)\)$/i.exec(String(l||'').trim());return m?m[2]:l},
 real:id=>!!id&&id!=='default'&&id!=='communications',
 ins:()=>(typeof ADV==='object'&&ADV.ins)||[],outs:()=>(typeof ADV==='object'&&ADV.outs)||[],
 pairOut(inId){const d=ST11.ins().find(x=>x.id===inId);if(!d||!ST11.real(inId))return null;const outs=ST11.outs().filter(o=>ST11.real(o.id));
  let o=d.gid?outs.find(x=>x.gid&&x.gid===d.gid):null;if(!o){const c=ST11.core(d.label);if(c)o=outs.find(x=>ST11.core(x.label)===c)}return o?o.id:null},
 score(d){if(!ST11.real(d.id))return -9;const l=d.label||'';let s=0;if(d.type==='int')s+=4;if(d.prof&&d.prof.k==='int')s+=3;if(ST11.pairOut(d.id))s+=2;
  if(/\busb\b|\([0-9a-f]{4}:[0-9a-f]{4}\)/i.test(l))s+=1;if(/built-?in|macbook|imac|internal|realtek|webcam|camera|facetime|array|headset/i.test(l))s-=3;if(['virtual','bt','display'].includes(d.type))s-=6;return s},
 bestIn(){let b=null,bs=0;for(const d of ST11.ins()){const s=ST11.score(d);if(s>bs){bs=s;b=d}}return b?b.id:null},
 /* the Recording setup as it is now: what was chosen by hand, the rest filled automatically */
 rec(){const s=ST11.S();let i=s.R.i,ia=false,o=s.R.o,oa=false;
  if(i==null){ia=true;const b=ST11.bestIn();i=b!=null?b:(s.L.i||'')}
  if(o==null){oa=true;const p=ST11.pairOut(i);o=p!=null?p:(s.L.o||'')}return{o,i,oa,ia}},
 name(id,kind){const L=kind==='out'?ST11.outs():ST11.ins();let d=ST11.real(id)?L.find(x=>x.id===id):null;if(d)return d.label;
  if(id&&ST11.real(id))return kind==='out'?'an output that is not connected':'an input that is not connected';const df=L.find(x=>x.def);return df?'System default ('+df.label+')':'System default'},
 dev(id,kind){const L=kind==='out'?ST11.outs():ST11.ins();return(ST11.real(id)?L.find(x=>x.id===id):L.find(x=>x.def))||null},
 /* the live output and input belong to the setup in use: a change made by hand anywhere (this card, the Audio devices window, Keep?'s Go back) is kept in it */
 take(){if(ST11.busy)return;const s=ST11.S(),o=UI.sink||'',i=UI.inDev||'';
  if(s.on==='listen'){if(s.L.o!==o||s.L.i!==i){s.L.o=o;s.L.i=i;try{saveUI()}catch(e){}}return}
  const ap=s.ap||{};let ch=false;if(ap.o!==undefined&&o!==ap.o){s.R.o=o;s.ap.o=o;ch=true}if(ap.i!==undefined&&i!==ap.i){s.R.i=i;s.ap.i=i;ch=true}if(ch)try{saveUI()}catch(e){}},
 go(mode,opt){const p=ST11.q.then(()=>ST11._go(mode,opt||{}),()=>ST11._go(mode,opt||{}));ST11.q=p.catch(()=>{});return p},
 async _go(mode,opt){ST11.take();const s=ST11.S();try{await adScan()}catch(e){}
  const tg=mode==='rec'?ST11.rec():{o:s.L.o||'',i:s.L.i||''},pO=UI.sink||'',pI=UI.inDev||'';s.on=mode;s.auto=mode==='rec'&&opt.auto?1:0;
  const r={changedO:tg.o!==pO,changedI:tg.i!==pI,pO,pI,o:tg.o,i:tg.i,ok:true,msg:''};ST11.busy++;
  try{if(r.changedI){UI.inDev=tg.i;ADV.at=0;try{saveUI()}catch(e){}await ST11.reopen()}
   if(r.changedO){const k=await ST11.sink(tg.o);r.ok=k.ok;r.msg=k.msg}}finally{ST11.busy--}
  s.ap=mode==='rec'?{o:UI.sink||'',i:UI.inDev||''}:{};if(mode==='listen'){s.L.o=UI.sink||'';s.L.i=UI.inDev||''}try{saveUI()}catch(e){}
  try{if(typeof ifdSync==='function')ifdSync()}catch(e){}ST11.paint();return r},
 /* a device switch with a click-free ramp of a few tens of milliseconds; no question (setups are chosen on purpose) */
 async sink(o){const c=typeof ctx!=='undefined'&&ctx?ctx:null;
  if(!c){UI.sink=o;try{saveUI()}catch(e){}try{const e=ST11.$('outSel');if(e)e.value=o}catch(e){}try{ST10.seen(o,true)}catch(e){}return{ok:true,msg:''}}
  const g=typeof MON==='object'&&MON&&MON.out&&MON.out.gain,run=c.state==='running'&&!!g;
  if(run){try{const t=c.currentTime;g.cancelScheduledValues(t);g.setValueAtTime(g.value,t);g.linearRampToValueAtTime(0,t+.025)}catch(e){}await new Promise(f=>setTimeout(f,35))}
  const T=toast;let msg='';toast=m=>{msg=m};let q0=false;try{q0=ST10.quiet;ST10.quiet=true}catch(e){}
  try{await adUseOut(o||'default')}catch(e){}finally{toast=T;try{ST10.quiet=q0}catch(e){}}
  const ok=(UI.sink||'')===(o||'');if(ok)try{ST10.seen(o,true)}catch(e){}
  if(run){try{const t=c.currentTime,to=MONDIM&&!UI.bitPerfect?.178:1;g.cancelScheduledValues(t);g.setValueAtTime(0,t);g.linearRampToValueAtTime(to,t+.03)}catch(e){}}
  return{ok,msg:ok?'':(msg||'The output could not be switched here.')}},
 /* armed audio tracks listen to the new input at once (not while recording) */
 async reopen(){if(typeof REC==='object'&&REC.on)return;for(const t of S.tracks){if(!t.arm||t.kind!=='audio')continue;const old=t._micRaw||t._mic;if(!old)continue;
  try{const st=await navigator.mediaDevices.getUserMedia(inCons());t._micRaw=st;t._mic=st;try{inWire(t)}catch(e){}try{old.getTracks().forEach(x=>x.stop())}catch(e){}}catch(e){}}},
 /* the short, quiet notice after an automatic switch, with the way back */
 note(kind,r){let n=ST11.$('st11Note');if(!n){n=document.createElement('div');n.id='st11Note';n.className='lg';n.setAttribute('role','status');n.hidden=true;
   n.innerHTML='<span class="st11nt"></span><button type="button" class="mini" data-st11n="back" title="Goes back to the Listening setup now. Your armed tracks stay armed.">Back to Listening</button><button type="button" class="mini st11nx" data-st11n="x" title="Hides this notice" aria-label="Hide">✕</button>';
   document.body.appendChild(n);n.addEventListener('click',e=>{const b=e.target.closest('[data-st11n]');if(!b)return;n.hidden=true;if(b.dataset.st11n==='back')ST11.go('listen',{})});
   n.addEventListener('mouseenter',()=>clearTimeout(ST11.nt));n.addEventListener('mouseleave',()=>{clearTimeout(ST11.nt);ST11.nt=setTimeout(()=>{n.hidden=true},2500)})}
  const out=ST11.name(r.o,'out'),inp=ST11.name(r.i,'in'),same=ST11.real(r.o)&&ST11.pairOut(r.i)===r.o;
  let t=kind==='rec'?'Switched to the Recording setup: '+(same?ST11.short(out)+' records and plays.':'recording from '+inp+', listening through '+out+'.'):'Back on the Listening setup: '+out+'.';
  if(!r.ok)t=(kind==='rec'?'Recording setup: ':'Listening setup: ')+r.msg;
  n.querySelector('.st11nt').textContent=t;n.querySelector('[data-st11n="back"]').hidden=kind!=='rec';n.hidden=false;clearTimeout(ST11.nt);ST11.nt=setTimeout(()=>{n.hidden=true},7000)},
 why(){const s=ST11.S(),a=ST11.arm();
  if(s.on==='listen')return 'Listening: AudioLab plays through '+ST11.name(UI.sink||'','out')+'. '+(a==='off'?'Switch to Recording yourself when you record.':'Arming '+(a==='any'?'a track':'an audio track')+' switches to the Recording setup by itself, and back when no track is armed.');
  const o=UI.sink||'',i=UI.inDev||'';
  if(!ST11.real(i)&&ST11.bestIn()==null&&s.R.i==null)return 'No audio interface was found, so recording uses the system input and plays through '+ST11.name(o,'out')+'.';
  if(ST11.real(o)&&ST11.pairOut(i)===o)return 'Recording: '+ST11.short(ST11.name(o,'out'))+' records and plays, so input and output share one clock and stay in step.';
  return 'Recording from '+ST11.name(i,'in')+', listening through '+ST11.name(o,'out')+'. These are two devices with their own clocks: the browser matches them, but one device for both is steadier.'},
 build(){if(ST11.done)return;const $=ST11.$;if(typeof ST10!=='object'||!ST10.done)return;const sec=ST5.sec('audio'),o=$('outSel'),orow=o&&o.closest('.cprow'),inp=$('ifdIn'),irow=inp&&inp.closest('.cprow');
  if(!sec||!orow||!irow)return;ST11.done=true;ST11.S();
  const tip={listen:'The Listening setup: the device you listen through, for example your DAC. Switches at once.',rec:'The Recording setup: the device you record from, and where you hear yourself. Filled automatically, changeable by hand. Switches at once.'};
  const c=document.createElement('div');c.className='sbox st11c';c.id='st11Dev';
  c.innerHTML='<h4>Devices</h4><div class="st11top"><div class="st11seg" id="st11Seg" role="group" aria-label="Setup in use"><button type="button" data-st11m="listen" title="'+tip.listen+'">Listening</button><button type="button" data-st11m="rec" title="'+tip.rec+'">Recording</button></div><p class="st11why" id="st11Why" aria-live="polite"></p></div>'
   +'<div class="st11roles"><div class="st11r" id="st11L"><div class="st11rh"><span class="adi" id="st11LI"></span><div class="adt"><span class="st11k">Listen through</span><b id="st11LN">–</b><small id="st11LC"></small></div><em class="st11by" id="st11LB"></em></div><div class="st11rb"></div></div>'
   +'<div class="st11r" id="st11R"><div class="st11rh"><span class="adi" id="st11RI"></span><div class="adt"><span class="st11k">Record from</span><b id="st11RN">–</b><small id="st11RC"></small></div><em class="st11by" id="st11RB"></em></div><div class="st11rb"></div></div></div>'
   +'<p class="hint st11oth" id="st11Oth"></p>'
   +'<div class="cprow"><span>Switch to Recording when I arm</span><select id="st11Arm" title="When you arm a track, AudioLab switches to the Recording setup by itself and shows a short notice with a way back. It goes back to Listening when no such track is armed."><option value="audio">an audio track (recommended)</option><option value="any">any track, also instruments</option><option value="off">never: I switch myself</option></select></div>'
   +'<div class="st11act"><button type="button" class="mini" id="st11Auto" title="Forgets the devices you chose by hand for the Recording setup and fills it automatically again">Fill Recording automatically again</button><button type="button" class="mini" id="st11Names" hidden title="Device names stay hidden until you allow audio input once. Nothing is recorded.">Show device names</button></div>';
  const drv=orow.closest('.sbox');sec.insertBefore(c,drv&&drv.parentNode===sec?drv:sec.firstChild);
  /* the one output select and the one input select move into their role cards (same elements, ids and handlers) */
  c.querySelector('#st11L .st11rb').appendChild(orow);if(!o.title)o.title='The device you listen through in the setup in use. A device used before switches at once; a new one asks Keep?';{const oc=ST10.row('ltOcChk');if(oc)c.querySelector('#st11L .st11rb').appendChild(oc)}
  {const d=document.createElement('div');d.className='cprow st10ro';d.innerHTML='<span>Record from</span><div class="cpin"><b id="st11DIn">–</b><button type="button" class="mini" data-st10go="#ifdIn" title="The input is chosen once, on Audio, in its Record from card. Opens it.">Change on Audio</button></div>';irow.before(d)}
  irow.classList.add('st11in');c.querySelector('#st11R .st11rb').appendChild(irow);
  {const sp=irow.querySelector('span');if(sp)sp.textContent='Input device'}inp.title='The device armed audio tracks record from, in the setup in use. Armed tracks switch to it at once.';
  /* the input's own handler runs as before; then the armed tracks follow and the setup keeps the choice */
  {const f=inp.onchange;if(f&&!f.__st11){const g=function(ev){const r=f.call(this,ev);ST11.take();ST11.reopen().then(()=>{try{if(S.tracks.some(t=>t.arm&&t.kind==='audio'))toast('Input chosen. Armed audio tracks record from it now.')}catch(e){}});ST11.paint();return r};g.__st11=f;inp.onchange=g}}
  const a=$('st11Arm');a.value=ST11.arm();a.onchange=()=>{UI.st11arm=a.value;try{saveUI()}catch(e){}ST11.paint()};
  c.addEventListener('click',e=>{const m=e.target.closest('[data-st11m]');if(m){ST11.go(m.dataset.st11m,{}).then(r=>{if(r&&!r.ok)toast(r.msg)});return}
   if(e.target.closest('#st11Auto')){const s=ST11.S();s.R.o=null;s.R.i=null;try{saveUI()}catch(e){}if(s.on==='rec')ST11.go('rec',{});else ST11.paint();toast('The Recording setup is filled automatically again.');return}
   if(e.target.closest('#st11Names')){(async()=>{try{const st=await navigator.mediaDevices.getUserMedia({audio:true});st.getTracks().forEach(t=>t.stop())}catch(err){toast('The audio input permission was not given, so names stay hidden.')}try{await listOuts()}catch(err){}if(typeof ADV==='object')ADV.at=0;ST11.paint()})()}});
  /* a change of the output made anywhere is kept in the setup in use */
  if(!ST10.outChanged.__st11){const f=ST10.outChanged;ST10.outChanged=function(){const r=f.apply(this,arguments);try{ST11.take();ST11.paint()}catch(e){}return r};ST10.outChanged.__st11=f}
  try{navigator.mediaDevices.addEventListener('devicechange',()=>{clearTimeout(ST11.dc);ST11.dc=setTimeout(()=>{if(typeof ADV==='object')ADV.at=0;ST11.paint()},500)})}catch(e){}
  /* the table: the input moves to Audio, two new rows; old names stay search words */
  {const r=STX.get('inDev');if(r){r.l='Input device';r.pg='audio';r.b='Devices';r.h='The device armed audio tracks record from, in the setup in use. The Recording setup fills it automatically; you can change it here.';r.w=((r.w||'')+' record from input device role card recording setup inputs').trim()}}
  {const r=STX.get('outDev');if(r){r.b='Devices';r.w=((r.w||'')+' listen through role card listening setup dac').trim()}}
  ST11.paint()},
 ROWS:[{"id":"setupNow","l":"Setup in use","pg":"audio","b":"Devices","sc":"app","k":"UI.st11.on","c":"#st11Seg","t":"cards","d":"listen","h":"Listening plays through the device you listen with; Recording records from your interface and plays where you hear yourself. Switching is instant.","w":"listening setup recording setup listen through record from role cards dac interface mode switch b2"},
  {"id":"armSwitch","l":"Switch to Recording when I arm","pg":"audio","b":"Devices","sc":"app","k":"UI.st11arm","c":"#st11Arm","t":"select","d":"audio","h":"Arming a track switches to the Recording setup by itself, with a short notice and a way back, and goes back to Listening when no such track is armed.","w":"arm armed automatic switch recording setup interface record enable"}],
 put(id,v,html){const e=ST11.$(id);if(!e)return;if(html){if(e.innerHTML!==v)e.innerHTML=v}else if(e.textContent!==v)e.textContent=v},
 async paint(){if(!ST11.done)return;const st=ST11.$('set');if(!st||st.hidden)return;try{await adScan()}catch(e){}const $=ST11.$,s=ST11.S(),put=ST11.put;
  for(const b of document.querySelectorAll('#st11Seg [data-st11m]')){const on=b.dataset.st11m===s.on;b.classList.toggle('on',on);b.setAttribute('aria-pressed',on?'true':'false')}
  put('st11Why',ST11.why());
  const role=(k,kind,id)=>{const d=ST11.dev(id,kind),K=(typeof ADK==='object'&&d&&ADK[d.type])||(typeof ADK==='object'&&ADK.other)||['','#9aa3b5'],ic=$('st11'+k+'I');
   put('st11'+k+'N',d?d.label:ST11.name(id,kind));put('st11'+k+'C',d&&typeof adChips==='function'?adChips(d):'',true);
   if(ic){ic.style.setProperty('--kc',K[1]);ic.title=K[0]||'';put('st11'+k+'I',typeof adIc==='function'?adIc(d?d.type:(kind==='out'?'other':'mic')):'',true)}};
  role('L','out',UI.sink||'');role('R','in',UI.inDev||'');
  const R=ST11.rec(),by=(a)=>s.on!=='rec'?'':a?'filled automatically':'chosen by you';
  put('st11LB',by(s.R.o==null));put('st11RB',by(s.R.i==null));
  for(const[k,v]of[['st11LB',s.R.o==null],['st11RB',s.R.i==null]]){const e=$(k);if(e)e.title=s.on!=='rec'?'':v?'AudioLab chose this device for the Recording setup. Choose another in the list to change it.':'You chose this device for the Recording setup. Fill Recording automatically again forgets the choice.'}
  put('st11Oth',s.on==='listen'?'Recording setup: '+(ST11.real(R.o)&&ST11.pairOut(R.i)===R.o?ST11.short(ST11.name(R.o,'out'))+' records and plays':'records from '+ST11.name(R.i,'in')+' and plays through '+ST11.name(R.o,'out'))+(R.ia&&R.oa?' (filled automatically).':'.'):'Listening setup: plays through '+ST11.name(s.L.o||'','out')+'.');
  {const a=$('st11Arm');if(a&&a.value!==ST11.arm()&&document.activeElement!==a)a.value=ST11.arm()}
  {const n=$('st11Names');if(n)n.hidden=!!(typeof ADV==='object'&&ADV.named)}
  {const o=$('outSel'),w=UI.sink||'';if(o&&document.activeElement!==o&&o.value!==w){/* the list is otherwise filled only when it is opened, so it showed System default while another device played */
    if(![...o.options].some(x=>x.value===w)){try{await listOuts()}catch(e){}}if([...o.options].some(x=>x.value===w))o.value=w}}
  {const i=$('ifdIn');if(i&&document.activeElement!==i){const L=ST11.ins().filter(x=>ST11.real(x.id)),h='<option value="">System default</option>'+L.map(x=>'<option value="'+esc(x.id)+'">'+esc(x.label)+'</option>').join('');if(i.innerHTML!==h)i.innerHTML=h;i.value=L.some(x=>x.id===UI.inDev)?UI.inDev:''}}
  put('st11DIn',ST11.name(UI.inDev||'','in'))},
 tick(){if(!ST11.done||typeof ST5!=='object'||(ST5.cur!=='audio'&&ST5.cur!=='dac'))return;if(++ST11.tk%4)return;ST11.take();ST11.paint()}};
/* arming: switch to Recording before the input is opened, so the track listens to the right device; back to Listening when the last one is disarmed */
{const _a11=armTrack;armTrack=async function(t){let sw=null;
  try{if(t&&!t.arm&&ST11.trig(t)&&!(typeof REC==='object'&&REC.on)){const s=ST11.S();if(s.on!=='rec'&&!S.tracks.some(q=>q!==t&&q.arm&&ST11.trig(q)))sw=await ST11.go('rec',{auto:true})}}catch(e){console.warn('recording setup (ST-S11)',e)}
  const x=await _a11.apply(this,arguments);
  try{if(sw&&(sw.changedO||sw.changedI||!sw.ok))ST11.note('rec',sw);
   if(t&&!t.arm){const s=ST11.S();if(s.on==='rec'&&s.auto&&!(typeof REC==='object'&&REC.on)&&!S.tracks.some(q=>q.arm&&ST11.trig(q))){const r=await ST11.go('listen',{auto:true});if(r.changedO||r.changedI||!r.ok)ST11.note('listen',r)}}}catch(e){console.warn('listening setup (ST-S11)',e)}
  return x}}
/* the two new rows join the table at once (search, reset, the Workshop's list), with their stable ids (task XT-DL3, docs/settings-ids.md) */
try{for(const r of ST11.ROWS)if(!STX.has(r.id)){const x=Object.assign({},r);STT.push(x);STX.set(x.id,x)}if(typeof XT_SET_NS==='object'&&XT_SET_NS){XT_SET_NS.setupNow='audio.setupNow';XT_SET_NS.armSwitch='audio.armSwitch'}}catch(e){}
try{ST11.S()}catch(e){}
/* a Recording setup AudioLab chose by itself, left over from the last session with nothing armed now, goes back to Listening quietly */
setTimeout(()=>{try{const s=ST11.S();if(s.on==='rec'&&s.auto&&!S.tracks.some(q=>q.arm&&ST11.trig(q)))ST11.go('listen',{auto:true})}catch(e){}},3000);
{const _o11=openSettings;openSettings=function(){const x=_o11.apply(this,arguments);try{ST11.build();ST11.paint()}catch(e){console.warn('settings devices (ST-S11)',e)}return x}}
{const _t11=ST5.tick;ST5.tick=function(){const x=_t11.apply(this,arguments);try{ST11.tick()}catch(e){}return x}}
/* ===== end of settings step S11 ===== */
