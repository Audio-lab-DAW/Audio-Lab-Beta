/* ============ DEEP LAYER PART: script. One closure; the only globals are window.DeepLayer and the element ids that start with dl. ============ */
(function(){
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=t=>String(t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const clone=o=>JSON.parse(JSON.stringify(o));
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));

/* ---------- the mock project ---------- */
const GREY='#8b8b97';
const TYPECOL={drums:'#e5534b',bass:'#4c8dff',lead:'#e3b341',pad:'#b77bff',fx:'#3ecf8e',vocal:'#f0883e'};
function freshProject(){return{tempo:138,sel:'t3',tracks:[
 {id:'t1',name:'Kick',type:'drums',color:GREY,mute:0,solo:0,clips:[[0,100]]},
 {id:'t2',name:'Bass',type:'bass',color:GREY,mute:0,solo:0,clips:[[0,50],[50,50]]},
 {id:'t3',name:'Lead',type:'lead',color:GREY,mute:0,solo:0,clips:[[25,25],[62.5,37.5]]},
 {id:'t4',name:'Pad',type:'pad',color:GREY,mute:0,solo:0,clips:[[50,50]]},
 {id:'t5',name:'Riser',type:'fx',color:GREY,mute:0,solo:0,clips:[[37.5,12.5],[87.5,12.5]]},
 {id:'t6',name:'Vox chop',type:'vocal',color:GREY,mute:0,solo:0,clips:[[62.5,25]]}],
 notes:[0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30].map((s,i)=>({id:'n'+(i+1),start:s,length:1.5,pitch:[57,60,64,67,69,67,64,60,57,62,65,69,72,69,65,62][i],velocity:100,selected:true}))}}
let P=freshProject();
const T={playing:0,rec:0,loop:1,click:0,count:0,pos:0};           // transport, not part of undo
const UNDO=[],REDO=[];
function mutate(label,fn){const before=JSON.stringify(P);fn();if(JSON.stringify(P)!==before){UNDO.push({label,snap:before});if(UNDO.length>60)UNDO.shift();REDO.length=0}renderApp()}

/* ---------- customisations: everything a user can change lives here, and only here ---------- */
const CUST0=()=>({settingsUser:{'mixer.meterFps':30},settingsProject:{},
 rules:{all:[{id:'transport.tap',rename:'Tap tempo'}],arrange:[],mix:[],compact:[]},
 keys:{'transport.metronome':'C','macro.tidy-clip':'Shift+T'},toolbar:['macro.tidy-clip'],
 macros:{'tidy-clip':{name:'Tidy clip',steps:['note.selectAll','clip.quantize16','note.velocityDown']}},
 css:{on:false,text:''},scripts:{buttons:[]}});
let CUST=CUST0();
const ST={tab:'P1',layout:'arrange',safe:false,picking:false,picked:null,ghosts:false,scopeAll:true,target:'user',filter:'all',q:'',cq:'',macroOpen:false,macroDraft:{name:'',steps:[]},waitKey:null};

/* ---------- P1: the settings table. S(id, type, default, extra, label, flags, search words). Flags: h = no normal control today, l = locked safety value, c = belongs to this computer (cannot go into a project) ---------- */
const SET=[],SBY={};
function S(id,t,def,x,l,f='',k=''){const e={id,t,def,x,l,h:f.includes('h'),lock:f.includes('l'),comp:f.includes('c'),k};SET.push(e);SBY[id]=e}
S('ui.accentHue','num',217,[0,360,1,'°'],'Accent colour of selected things','','colour blue tint');
S('ui.scale','num',100,[75,150,5,'%'],'Interface size','c','zoom bigger smaller');
S('ui.tooltips','bool',true,0,'Tooltips');
S('ui.tooltipDelayMs','num',500,[0,2000,50,' ms'],'How long before a tooltip shows','h','hover help');
S('ui.animationMs','num',80,[0,300,10,' ms'],'Length of button and panel animations','h','speed snappy');
S('ui.doubleClickMs','num',350,[150,700,10,' ms'],'Longest gap that counts as a double click','h');
S('ui.dragStartPx','num',4,[1,12,1,' px'],'Pointer travel before a drag starts','h');
S('ui.splash','bool',true,0,'Splash screen at start');
S('ui.splash.minMs','num',1000,[0,4000,100,' ms'],'Shortest time the splash stays','h','start loading');
S('ui.toast.ms','num',2600,[800,8000,200,' ms'],'How long a message stays on screen','h','notification');
S('ui.focusRing','enum','Keyboard only',['Keyboard only','Always','Never'],'Focus outline','h','accessibility');
S('glass.level','enum','Glass',['Glass','Light','Solid'],'Glass level','c','performance light mode');
S('glass.lens','enum','Wide',['Off','Fine','Apple','Wide'],'Glass lens');
S('glass.lensPx','num',45,[0,80,1,' px'],'Lens width in pixels (the presets set this)','h','refraction');
S('glass.backdropFps','num',60,[10,240,5,' fps'],'How often the picture behind glass is redrawn','hc','frame rate cost');
S('transport.clockFormat','enum','Bars',['Bars','Time','Samples'],'Clock shows','','timecode');
S('transport.playFlash','bool',true,0,'Play button flashes on the beat','','blink');
S('transport.tapWindowMs','num',2000,[800,5000,100,' ms'],'Tap tempo forgets taps older than','h');
S('transport.returnOnStop','bool',false,0,'Stop jumps back to where play started','h','cursor');
S('transport.preRollBars','num',0,[0,4,1,' bars'],'Pre-roll before recording','h','count in');
S('arrange.trackHeight','num',30,[22,56,2,' px'],'Track height','','zoom rows');
S('arrange.clipCornerPx','num',2,[0,8,1,' px'],'Clip corner radius','h','round look');
S('arrange.snapStrengthPx','num',8,[0,24,1,' px'],'How close before a clip snaps','h','magnet grid');
S('arrange.autoScrollEdgePx','num',40,[10,160,5,' px'],'Edge zone that scrolls while dragging','h');
S('arrange.wheelZoomStep','num',12,[2,40,1,'%'],'Zoom per wheel notch','h','scroll');
S('pianoroll.defaultVelocity','num',100,[1,127,1,''],'Velocity of a drawn note','h');
S('pianoroll.noteNameMinPx','num',28,[10,80,2,' px'],'Narrowest note that still shows its name','h');
S('pianoroll.previewNotes','bool',true,0,'Hear a note when it is clicked','h','audition');
S('pianoroll.ghostOpacity','num',35,[5,90,5,'%'],'Ghost notes opacity','h');
S('edit.nudgeFine','enum','1/64',['1/32','1/64','1/128'],'Finest nudge step','h','move');
S('edit.undoSteps','num',200,[50,2000,50,''],'Undo steps kept','h','history memory');
S('edit.pasteAt','enum','Playhead',['Playhead','Original time','Pointer'],'Paste lands at','h');
S('mixer.stripWidth','num',76,[64,170,2,' px'],'Strip width','','narrow wide channel');
S('mixer.meterFps','num',60,[10,120,5,' fps'],'How often level meters redraw','h','frame rate cpu');
S('mixer.peakHoldMs','num',1000,[0,10000,100,' ms'],'Peak hold time','','meter');
S('mixer.meterFloorDb','num',-60,[-96,-36,6,' dB'],'Lowest level a meter shows','h','range');
S('mixer.faderFineRatio','num',10,[2,50,1,'×'],'How much finer a fader moves with Shift','h','precision');
S('mixer.doubleClickReset','bool',true,0,'Double click puts a control back to its default','h');
S('mixer.soloMode','enum','Latch',['Latch','Exclusive','Momentary'],'Solo behaviour','h');
S('devices.paramSmoothMs','num',20,[0,200,5,' ms'],'Smoothing of knob moves (zipper noise)','h','automation');
S('devices.newStart','enum','As each device prefers',['As each device prefers','Shown','Hidden'],'New devices start with their parameters');
S('devices.presetPreview','bool',true,0,'Hear a preset while pointing at it','h');
S('audio.bufferSize','enum','Auto',['Auto','64','128','256','512','1024','2048'],'Buffer size','c','latency');
S('audio.sampleRate','enum','Automatic (device)',['Automatic (device)','44.1 kHz','48 kHz','96 kHz'],'Sample rate','c');
S('engine.voiceLimit','num',64,[16,256,8,''],'Most voices sounding at once','hc','polyphony cpu');
S('engine.sleepAfterMs','num',1500,[200,10000,100,' ms'],'A silent track goes to sleep after','h','cpu saver');
S('engine.lookaheadMs','num',120,[40,400,10,' ms'],'How far ahead notes are scheduled','hc','timing');
S('engine.freezeIdleS','num',20,[5,300,5,' s'],'Unchanged tracks are frozen after','h','background freeze');
S('project.autosaveMin','num',2,[1,30,1,' min'],'Autosave every');
S('project.backupCount','num',20,[1,200,1,''],'Earlier versions kept per project','h','time machine');
S('export.tailS','num',2,[0,16,1,' s'],'Export tail');
S('export.ditherSeedFixed','bool',true,0,'Same seed gives the same export','h');
S('chat.canWriteFiles','bool',true,0,'The chat box may write rules, macros and scripts (it always shows them first)','h','assistant ai');
S('workshop.enabled','bool',false,0,'Show the Workshop in the menu','','developer advanced');
S('workshop.scriptHandlerMs','num',50,[10,200,10,' ms'],'Longest a script may take to answer one event','h','time limit');
S('safety.limiter.ceilingDb','num',-1,[-10,-1,1,' dBFS'],'Master safety limiter ceiling','l','protect loud');
S('safety.output.maxGainDb','num',0,[0,0,1,' dB'],'Most gain the output stage may add','l','volume');
S('safety.startup.rampMs','num',30,[30,30,1,' ms'],'Fade-in when the engine starts','l','click pop');
S('safety.script.runLimitMs','num',2000,[2000,2000,1,' ms'],'Longest a script may run before it is stopped','l','time limit freeze');
const eff=id=>{const e=SBY[id];if(ST.safe||e.lock)return e.def;const p=CUST.settingsProject,u=CUST.settingsUser;return id in p?p[id]:id in u?u[id]:e.def};
const layerOf=id=>ST.safe?'default':id in CUST.settingsProject?'project':id in CUST.settingsUser?'user':'default';
const fmtV=(e,v)=>e.t=='num'?v+e.x[3]:e.t=='bool'?(v?'on':'off'):v;
/* validation: the same function guards the list, the files and scripts */
function validate(id,v){const e=SBY[id];if(!e)return{bad:'No setting is called "'+id+'". It is kept in the file but not used.'};
 if(e.lock)return{bad:'Locked. A safety value: no file, rule or script can change it.'};
 if(e.t=='bool'){if(typeof v!='boolean')return{bad:'Must be true or false.'};return{v}}
 if(e.t=='enum'){if(!e.x.includes(v))return{bad:'Must be one of: '+e.x.join(', ')+'.'};return{v}}
 const n=Number(v);if(v===''||!isFinite(n))return{bad:'Must be a number.'};
 if(n<e.x[0]||n>e.x[1])return{bad:'Must be from '+e.x[0]+' to '+e.x[1]+e.x[3]+'.'};return{v:n}}

/* ---------- the controls of the mock, each with a stable id ---------- */
const CTL={},ORDER={transport:[],strip:[],master:[]};
function C(id,box,label,o={}){CTL[id]=Object.assign({id,box,label},o);ORDER[box].push(id)}
C('transport.play','transport','Play',{cmd:'transport.play'});C('transport.stop','transport','Stop',{cmd:'transport.stop'});
C('transport.record','transport','Rec',{cmd:'transport.record',prot:'The record light must always be visible.'});
C('transport.loop','transport','Loop',{cmd:'transport.loop'});C('transport.metronome','transport','Click',{cmd:'transport.metronome'});
C('transport.countIn','transport','Count-in',{cmd:'transport.countIn'});C('transport.tap','transport','Tap',{cmd:'transport.tap'});
C('transport.clock','transport','Clock',{ro:1});C('transport.tempo','transport','Tempo',{ro:1});
C('transport.capture','transport','Capture',{});C('transport.undo','transport','Undo',{cmd:'edit.undo'});C('transport.redo','transport','Redo',{cmd:'edit.redo'});
C('transport.cpu','transport','CPU',{ro:1});
C('mixer.strip.name','strip','Name');C('mixer.strip.fx','strip','FX');C('mixer.strip.sends','strip','Sends');C('mixer.strip.pan','strip','Pan');
C('mixer.strip.fader','strip','Fader and meter');C('mixer.strip.peak','strip','Peak number');C('mixer.strip.mute','strip','M');C('mixer.strip.solo','strip','S');C('mixer.strip.rec','strip','R');
C('mixer.master.name','master','Master');C('mixer.master.lufs','master','Loudness');C('mixer.master.truePeak','master','True peak');
C('mixer.master.limiter','master','Limiter',{prot:'The limiter light shows that your ears and speakers are protected.'});
C('mixer.master.fader','master','Master meter',{prot:'The master meter must always be visible.'});C('mixer.master.mono','master','Mono');C('mixer.master.dim','master','Dim');
const BOXNAME={transport:'the transport bar',strip:'every channel strip',master:'the master strip'};
const LAYOUTS={arrange:'Arrange',mix:'Mix',compact:'Compact'};
function activeRules(){return ST.safe?[]:[...CUST.rules.all,...CUST.rules[ST.layout]]}
/* apply the rules to one box: returns [{id,label,hidden}] in display order, and collects problems */
let RULEWARN=[];
function layoutOf(box){const rules=activeRules();let order=ORDER[box].slice();const lab={},hid={};
 for(const r of rules){const c=CTL[r.id];if(!c||c.box!==box)continue;
  if(r.hide){if(c.prot)RULEWARN.push(r.id+': cannot be hidden. '+c.prot);else hid[r.id]=1}
  if(typeof r.rename=='string'&&r.rename.trim())lab[r.id]=r.rename.trim().slice(0,24);
  const rel=r.before||r.after;if(rel){const t=CTL[rel];if(!t||t.box!==box){RULEWARN.push(r.id+': can only move inside '+BOXNAME[box]+'.');continue}
   order=order.filter(x=>x!==r.id);const i=order.indexOf(rel);order.splice(r.before?i:i+1,0,r.id)}}
 return order.map(id=>({id,label:lab[id]||CTL[id].label,hidden:!!hid[id]}))}
function checkRules(){RULEWARN=[];for(const r of activeRules())if(!CTL[r.id])RULEWARN.push('"'+r.id+'": no control has this id. The rule is kept but not used.');['transport','strip','master'].forEach(layoutOf);return RULEWARN}

/* ---------- drawing the mock ---------- */
const app=$('#dlApp');
function clockText(){const beats=T.pos/100*16,f=eff('transport.clockFormat');
 if(f=='Bars')return (1+Math.floor(beats/4))+'.'+(1+Math.floor(beats%4))+'.'+(1+Math.floor(beats*4%4));
 const s=beats*60/P.tempo;return f=='Time'?'0:'+s.toFixed(2).padStart(5,'0'):Math.round(s*48000).toLocaleString('en')+' smp'}
function ctlHTML(it,tr){const id=it.id,c=CTL[id],g=it.hidden?' ghost':'',a=`data-al="${id}"${tr?` data-tr="${tr.id}"`:''}`,L=esc(it.label);
 const pk=ST.picked===id?' pkd':'';
 switch(id){
 case'transport.play':return `<button ${a} class="c${T.playing?' on':''}${g}${pk}">▶ ${L}</button>`;
 case'transport.stop':return `<button ${a} class="c${g}${pk}">■ ${L}</button>`;
 case'transport.record':return `<button ${a} class="c rec${T.rec?' on':''}${g}${pk}">● ${L}</button>`;
 case'transport.loop':return `<button ${a} class="c${T.loop?' on':''}${g}${pk}">${L}</button>`;
 case'transport.metronome':return `<button ${a} class="c${T.click?' on':''}${g}${pk}">${L}</button>`;
 case'transport.countIn':return `<button ${a} class="c${T.count?' on':''}${g}${pk}">${L}</button>`;
 case'transport.clock':return `<span ${a} class="c ro${g}${pk}" id="dlClock">${clockText()}</span>`;
 case'transport.tempo':return `<span ${a} class="c ro${g}${pk}">${P.tempo} BPM</span>`;
 case'transport.cpu':return `<span ${a} class="c ro${g}${pk}">${L} 7%</span>`;
 case'mixer.strip.name':return `<button ${a} class="c nm${g}${pk}">${esc(tr.name)}</button>`;
 case'mixer.strip.fx':return `<button ${a} class="c${g}${pk}">${L} 2</button>`;
 case'mixer.strip.pan':return `<button ${a} class="c dlpan${g}${pk}" aria-label="${L}"></button>`;
 case'mixer.strip.fader':return `<button ${a} class="c dlfd${g}${pk}" aria-label="${L}"><span class="fx" style="--v:${tr.id=='t1'?22:34}%"></span><span><i class="al-meter" data-mt="${tr.id}"></i></span><span><i class="al-meter" data-mt="${tr.id}"></i></span></button>`;
 case'mixer.strip.peak':return `<span ${a} class="c ro${g}${pk}" style="justify-content:center">${tr.mute?'-inf':'-6.2'}</span>`;
 case'mixer.strip.mute':return `<button ${a} class="c m1${tr.mute?' on':''}${g}${pk}">${L}</button>`;
 case'mixer.strip.solo':return `<button ${a} class="c s1${tr.solo?' on':''}${g}${pk}">${L}</button>`;
 case'mixer.master.name':return `<span ${a} class="c nm${g}${pk}">${L}</span>`;
 case'mixer.master.lufs':return `<span ${a} class="c ro${g}${pk}">${L=='Loudness'?'':L+' '}-14.2 LUFS</span>`;
 case'mixer.master.truePeak':return `<span ${a} class="c ro${g}${pk}">${L=='True peak'?'TP':L} -1.3</span>`;
 case'mixer.master.limiter':return `<span ${a} class="c ro dllamp${pk}" title="Safety limiter, ceiling ${eff('safety.limiter.ceilingDb')} dBFS">${L} on</span>`;
 case'mixer.master.fader':return `<button ${a} class="c dlfd${pk}" aria-label="${L}"><span class="fx" style="--v:26%"></span><span><i class="al-meter" data-mt="M"></i></span><span><i class="al-meter" data-mt="M"></i></span></button>`;
 default:return `<button ${a} class="c${g}${pk}">${L}</button>`}}
function boxHTML(box,tr){return layoutOf(box).filter(it=>!it.hidden||(ST.ghosts&&ST.tab=='P2')).map(it=>ctlHTML(it,tr)).join('')}
function renderApp(){
 RULEWARN=[];
 app.style.setProperty('--hue',eff('ui.accentHue'));app.style.setProperty('--scale',eff('ui.scale')/100);
 app.style.setProperty('--th',eff('arrange.trackHeight')+'px');app.style.setProperty('--cr',eff('arrange.clipCornerPx')+'px');
 app.style.setProperty('--sw',eff('mixer.stripWidth')+'px');app.style.setProperty('--anim',eff('ui.animationMs')+'ms');
 app.classList.toggle('picking',ST.picking&&ST.tab=='P2');
 const lay=ST.layout,tb=ST.safe?[]:CUST.toolbar,sb=ST.safe?[]:CUST.scripts.buttons;
 let h='';
 if(ST.safe)h+=`<div class="dlsafe"><span><b>Safe mode.</b> Your changes are all kept, but none of them is used: this is AudioLab as it came.</span><button data-act="unsafe">Leave safe mode</button></div>`;
 h+=`<div class="dlbar" data-box="transport">${boxHTML('transport')}<span class="sp"></span>${tb.map(id=>`<button class="c usr" data-run="${esc(id)}" title="${esc(id)}">${esc(cmdName(id))}</button>`).join('')}${sb.map(b=>`<button class="c usr" data-sbtn="${esc(b.id)}" title="Added by a script">${esc(b.label)}</button>`).join('')}</div>`;
 if(lay!='mix'){h+=`<div class="dlarr">${P.tracks.map(t=>`<div class="dltr al-track${t.id==P.sel?' sel':''}${t.mute?' mu':''}" data-sel="${t.id}" style="--c:${t.color}"><div class="dlth"><i></i>${esc(t.name)}<small>${t.type}</small></div><div class="dltl">${t.clips.map(c=>`<b class="al-clip" style="left:${c[0]}%;width:${c[1]}%"></b>`).join('')}</div></div>`).join('')}<div class="dlph" id="dlPh"></div></div>`;
  h+=`<div class="dlpr">${P.notes.map(n=>`<i class="${n.selected?'s':''}" style="left:${n.start/32*100}%;width:${n.length/32*100}%;bottom:${(n.pitch-50)/36*72+6}px;opacity:${.25+.75*n.velocity/127}"></i>`).join('')}</div>`}
 if(lay!='compact'){h+=`<div class="dlmix">${P.tracks.map(t=>`<div class="dlst al-strip${t.id==P.sel?' sel':''}" style="--c:${t.color}" data-box="strip">${boxHTML('strip',t)}</div>`).join('')}<div class="dlst al-strip dlmaster" style="--c:#fff" data-box="master">${boxHTML('master')}</div></div>`}
 app.innerHTML=h;placeHead();drawMeters(true);applyCss();
 const st=[`Layout <span class="sg" id="dlLay">${Object.keys(LAYOUTS).map(k=>`<button data-lay="${k}" aria-pressed="${k==lay}">${LAYOUTS[k]}</button>`).join('')}</span>`,
  `<button class="B" data-act="undo" ${UNDO.length?'':'disabled'}>↶ Undo${UNDO.length?' “'+esc(UNDO[UNDO.length-1].label)+'”':''}</button>`,
  `<button class="B" data-act="safe" aria-pressed="${ST.safe}">Safe mode</button>`,`<span id="dlPoint"></span>`];
 $('#dlStat').innerHTML=st.join('')}
function placeHead(){const ph=$('#dlPh');if(ph){const w=ph.parentNode.clientWidth-112;ph.style.left=112+w*T.pos/100+'px'}const c=$('#dlClock');if(c)c.textContent=clockText()}
const anySolo=()=>P.tracks.some(t=>t.solo);
function drawMeters(still){const so=anySolo();let mx=0;const lv={};
 for(const t of P.tracks){const on=T.playing&&!t.mute&&(!so||t.solo)&&t.clips.some(c=>T.pos>=c[0]&&T.pos<c[0]+c[1]);lv[t.id]=on?45+Math.random()*40:0;mx=Math.max(mx,lv[t.id])}
 lv.M=mx?Math.min(96,mx+6):0;for(const i of $$('[data-mt]',app))i.style.height=(still&&!T.playing?0:lv[i.dataset.mt]*(.9+Math.random()*.1))+'%'}
/* one timer while playing, none when stopped: the mock costs nothing at rest */
let tick=null,meterAt=0;
function setPlaying(on){T.playing=on?1:0;clearInterval(tick);tick=null;
 if(on){let last=performance.now();tick=setInterval(()=>{const now=performance.now(),dt=now-last;last=now;T.pos+=dt/1000*P.tempo/60/16*100;if(T.pos>=100){if(T.loop)T.pos=0;else{T.pos=100;setPlaying(0);renderApp();return}}
   placeHead();if(now-meterAt>=1000/eff('mixer.meterFps')){meterAt=now;drawMeters()}},16)}}

/* ---------- commands: every action of the mock as a named command ---------- */
const CMD=[],CBY={};
function K(id,g,name,key,run){const c={id,g,name,key:key||'',run};CMD.push(c);CBY[id]=c}
const selTrack=()=>P.tracks.find(t=>t.id==P.sel);
const selNotes=()=>{const s=P.notes.filter(n=>n.selected);return s.length?s:P.notes};
K('transport.play','Transport','Play / pause','Space',()=>{setPlaying(!T.playing);renderApp()});
K('transport.stop','Transport','Stop','Shift+Space',()=>{setPlaying(0);T.pos=0;T.rec=0;renderApp()});
K('transport.home','Transport','Go to start','Home',()=>{T.pos=0;renderApp()});
K('transport.record','Transport','Record','Shift+R',()=>{T.rec=T.rec?0:1;renderApp()});
K('transport.loop','Transport','Loop on / off','Shift+L',()=>{T.loop=T.loop?0:1;renderApp()});
K('transport.metronome','Transport','Metronome','',()=>{T.click=T.click?0:1;renderApp()});
K('transport.countIn','Transport','Count-in on / off','',()=>{T.count=T.count?0:1;renderApp()});
K('transport.tap','Transport','Tap tempo','',()=>mutate('Tap tempo',()=>{P.tempo=P.tempo>=150?120:P.tempo+2}));
K('transport.tempoUp','Transport','Tempo up 1 BPM','',()=>mutate('Tempo',()=>{P.tempo=clamp(P.tempo+1,40,240)}));
K('transport.tempoDown','Transport','Tempo down 1 BPM','',()=>mutate('Tempo',()=>{P.tempo=clamp(P.tempo-1,40,240)}));
K('edit.undo','Edit','Undo','Mod+Z',()=>{const u=UNDO.pop();if(u){REDO.push({label:u.label,snap:JSON.stringify(P)});P=JSON.parse(u.snap)}renderApp()});
K('edit.redo','Edit','Redo','Mod+Shift+Z',()=>{const u=REDO.pop();if(u){UNDO.push({label:u.label,snap:JSON.stringify(P)});P=JSON.parse(u.snap)}renderApp()});
K('track.selectNext','Track','Select the next track','ArrowDown',()=>{const i=P.tracks.findIndex(t=>t.id==P.sel);P.sel=P.tracks[(i+1)%P.tracks.length].id;renderApp()});
K('track.selectPrevious','Track','Select the track above','ArrowUp',()=>{const i=P.tracks.findIndex(t=>t.id==P.sel);P.sel=P.tracks[(i+P.tracks.length-1)%P.tracks.length].id;renderApp()});
K('track.mute','Track','Mute the selected track','M',()=>mutate('Mute',()=>{const t=selTrack();t.mute=t.mute?0:1}));
K('track.solo','Track','Solo the selected track','S',()=>mutate('Solo',()=>{const t=selTrack();t.solo=t.solo?0:1}));
K('track.unmuteAll','Track','Unmute and unsolo every track','',()=>mutate('Unmute all',()=>P.tracks.forEach(t=>{t.mute=0;t.solo=0})));
K('track.newInstrument','Track','New instrument track','Mod+Shift+I',()=>mutate('New track',()=>{if(P.tracks.length<9)P.tracks.push({id:'t'+Date.now()%100000,name:'Synth '+(P.tracks.length+1),type:'lead',color:GREY,mute:0,solo:0,clips:[]})}));
K('track.delete','Track','Delete the selected track','',()=>mutate('Delete track',()=>{if(P.tracks.length>1){const i=P.tracks.findIndex(t=>t.id==P.sel);P.tracks.splice(i,1);P.sel=P.tracks[Math.min(i,P.tracks.length-1)].id}}));
K('clip.duplicate','Clip','Duplicate the last clip of the selected track','Mod+D',()=>mutate('Duplicate clip',()=>{const t=selTrack(),c=t.clips[t.clips.length-1];if(c&&c[0]+c[1]*2<=100)t.clips.push([c[0]+c[1],c[1]])}));
K('clip.quantize16','Clip','Quantize the selected notes to 1/16','Q',()=>mutate('Quantize',()=>selNotes().forEach(n=>{n.start=clamp(Math.round(n.start),0,31)})));
K('note.selectAll','Notes','Select every note','Mod+A',()=>mutate('Select all',()=>P.notes.forEach(n=>n.selected=true)));
K('note.selectEveryOther','Notes','Select every second note','',()=>mutate('Select',()=>P.notes.forEach((n,i)=>n.selected=i%2==0)));
K('note.octaveUp','Notes','Selected notes one octave up','Shift+ArrowUp',()=>mutate('Octave up',()=>selNotes().forEach(n=>n.pitch=clamp(n.pitch+12,50,84))));
K('note.octaveDown','Notes','Selected notes one octave down','Shift+ArrowDown',()=>mutate('Octave down',()=>selNotes().forEach(n=>n.pitch=clamp(n.pitch-12,50,84))));
K('note.velocityUp','Notes','Selected notes louder','',()=>mutate('Velocity',()=>selNotes().forEach(n=>n.velocity=clamp(n.velocity+12,1,127))));
K('note.velocityDown','Notes','Selected notes softer','',()=>mutate('Velocity',()=>selNotes().forEach(n=>n.velocity=clamp(n.velocity-12,1,127))));
K('note.legato','Notes','Stretch each selected note to the next','',()=>mutate('Legato',()=>selNotes().forEach(n=>n.length=2)));
K('view.layoutArrange','View','Layout: Arrange','',()=>{ST.layout='arrange';renderAll()});
K('view.layoutMix','View','Layout: Mix','Shift+M',()=>{ST.layout='mix';renderAll()});
K('view.layoutCompact','View','Layout: Compact','',()=>{ST.layout='compact';renderAll()});
K('view.zoomIn','View','Taller tracks','',()=>setSetting('arrange.trackHeight',clamp(eff('arrange.trackHeight')+4,22,56)));
K('view.zoomOut','View','Lower tracks','',()=>setSetting('arrange.trackHeight',clamp(eff('arrange.trackHeight')-4,22,56)));
K('app.safeMode','App','Safe mode on / off','',()=>{ST.safe=!ST.safe;renderAll()});
K('project.new','Project','Start the mock project again','',()=>{mutate('New project',()=>{P=freshProject()})});
function macroCmd(slug){const m=CUST.macros[slug];return m&&{id:'macro.'+slug,g:'My macros',name:m.name,key:'',macro:m}}
function getCmd(id){if(id.startsWith('macro.'))return ST.safe?null:macroCmd(id.slice(6));return CBY[id]}
function cmdName(id){const c=getCmd(id);return c?c.name:id+' (missing)'}
let depth=0;
function runCmd(id,from){const c=getCmd(id);if(!c){say('No command is called '+id+'.','e');return false}
 if(c.macro){if(depth>4){say('Macro '+id+' calls itself: stopped.','e');return false}depth++;const n0=UNDO.length,before=JSON.stringify(P);
  for(const s of c.macro.steps)if(runCmd(s,'macro')===false)break;depth--;
  if(UNDO.length>n0){UNDO.length=n0;UNDO.push({label:c.name,snap:before})}renderApp();if(from!='macro')say('Macro “'+c.name+'” ran '+c.macro.steps.length+' steps as one undo step.','o');return true}
 c.run();if(from!='macro'&&from!='quiet')say('Ran '+id,'i');return true}
const keyOf=id=>ST.safe?(CBY[id]?CBY[id].key:''):(id in CUST.keys?CUST.keys[id]:(CBY[id]?CBY[id].key:''));
function chord(e){const p=[];if(e.metaKey||e.ctrlKey)p.push('Mod');if(e.altKey)p.push('Alt');if(e.shiftKey)p.push('Shift');let k=e.key;if(k==' ')k='Space';if(['Shift','Control','Alt','Meta'].includes(k))return'';if(k.length==1)k=k.toUpperCase();p.push(k);return p.join('+')}
function setSetting(id,v,layer){const r=validate(id,v);if(r.bad)return r;const e=SBY[id];layer=layer||'user';
 if(layer=='project'&&e.comp)return{bad:'This one belongs to the computer, so it cannot travel inside a project.'};
 const box=layer=='project'?CUST.settingsProject:CUST.settingsUser;if(layer=='user'&&r.v===e.def)delete box[id];else box[id]=r.v;renderAll();return r}
/* the console line under the tools (also used by commands) */
const LOG=[];function say(t,k='i'){LOG.push({t:String(t),k});if(LOG.length>200)LOG.shift();const c=$('#dlCon');if(c){c.innerHTML=LOG.map(l=>`<div class="${l.k}">${esc(l.t)}</div>`).join('');c.scrollTop=c.scrollHeight}const m=$('#dlCmdMsg');if(m){m.textContent=t;m.className='dlmsg '+(k=='e'?'bad':k=='o'?'ok':'')}}
