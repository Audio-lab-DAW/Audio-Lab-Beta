/* ---------- the six tools ---------- */
const TABS=[
 {k:'P1',n:'The everything list',d:'Every setting by its id in one searchable list, with its default, like about:config in Firefox. It also holds the options that have no normal control today (purple mark) and the locked safety values (red mark). Try: search "meter", set <b>mixer.meterFps</b> to 10 and press Play; set <b>ui.accentHue</b> to 30; type 999 into <b>mixer.stripWidth</b>.'},
 {k:'P2',n:'Pick and change any control',d:'Press "Pick an element", then click any button, read-out or strip part in the mock. Hide it, rename it or move it; choose whether that holds in every layout or only this one. The rules file on the right is the whole truth: edit it by hand and press Apply. Try to hide the limiter light.'},
 {k:'P3',n:'Commands and macros',d:'Every action is a named command. Give it a key, put it on the toolbar, or chain several into a macro that runs as one undo step. Scripts and the chat box call the same names. Keys work while the pointer is over the mock.'},
 {k:'P4',n:'Your own CSS',d:'A few lines of CSS change the look beyond what any setting offers. Guard rails: it only reaches AudioLab\'s own window, cannot load files or web addresses, and is switched off by itself if it hides a protected control.'},
 {k:'P5',n:'Your own scripts',d:'A small JavaScript API reads and changes the project. A script runs in a sandbox: no files, no network unless you allow it on a card, 2 seconds at most, and its changes arrive as one undo step. Examples 4 to 6 try to misbehave.'},
 {k:'P6',n:'Safe mode and reset',d:'The way back. Safe mode starts AudioLab as it came without deleting anything. The list shows every change from all five tools, each with its own remove button.'}];
const tool=$('#dlTool');
function renderTabs(){$('#dlTabs').innerHTML=TABS.map(t=>`<button data-tab="${t.k}" aria-pressed="${ST.tab==t.k}" class="${PK.P[t.k]=='yes'?'picked':''}"><span class="num">${t.k}</span>${t.n}${PK.P[t.k]?` <small>· ${PK.P[t.k]}</small>`:''}</button>`).join('');
 const t=TABS.find(t=>t.k==ST.tab);$('#dlInfo').innerHTML=`<p><b>${t.k} ${t.n}.</b> ${t.d}</p><span>Do you want this?</span><span class="segm" role="group" aria-label="Do you want ${t.n}">${['yes','later','no'].map(v=>`<button data-yn="${v}" aria-pressed="${PK.P[t.k]==v}">${v[0].toUpperCase()+v.slice(1)}${v=='yes'?' ★':''}</button>`).join('')}</span>`}
const j=o=>JSON.stringify(o,null,2);
const pane=(head,body,foot='')=>`<div class="dlpane"><header>${head}</header>${body}${foot}</div>`;
const fileHead=(name,extra='')=>`<b>${name}</b><span class="sp"></span>${extra}`;

/* P1 */
let ERR=null;
function setRows(){const q=ST.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
 const rows=SET.filter(e=>{if(ST.filter=='chg'&&layerOf(e.id)=='default')return false;if(ST.filter=='hid'&&!e.h)return false;if(ST.filter=='lock'&&!e.lock)return false;
  const hay=(e.id+' '+e.l+' '+e.k).toLowerCase();return q.every(w=>hay.includes(w))});
 if(!rows.length)return '<div class="dlhint">Nothing matches. Try "meter", "ms" or "safety".</div>';
 return rows.map(e=>{const v=eff(e.id),ly=layerOf(e.id),id=e.id,did='dls-'+id.replace(/\./g,'-');let ed;
  if(e.lock)ed=`<span class="c ro">${esc(fmtV(e,v))}</span>`;
  else if(e.t=='bool')ed=`<button class="sw" role="switch" id="${did}" aria-checked="${!!v}" data-set="${id}" aria-label="${esc(e.l)}"></button>`;
  else if(e.t=='enum')ed=`<select id="${did}" data-set="${id}" aria-label="${esc(e.l)}">${e.x.map(o=>`<option${o==v?' selected':''}>${esc(o)}</option>`).join('')}</select>`;
  else ed=`<input type="number" id="${did}" data-set="${id}" value="${v}" step="${e.x[2]}" aria-label="${esc(e.l)}">`;
  const tags=(e.h?'<i class="tag h" title="No normal control exists for this today">no control</i> ':'')+(e.lock?'<i class="tag l">locked</i> ':'')+(ly=='user'?'<i class="tag u">yours</i>':ly=='project'?'<i class="tag p">project</i>':'');
  return `<div class="dlrow${ly!='default'?' chg':''}"><span class="id">${esc(id)}<small>${esc(e.l)} · default ${esc(fmtV(e,e.def))}${e.t=='num'&&!e.lock?' · '+e.x[0]+' to '+e.x[1]:''}</small></span><span>${tags}</span>${ed}${ly!='default'?`<button class="rs" data-rst="${id}" title="Back to the default" aria-label="Reset ${id}">↺</button>`:'<span></span>'}${ERR&&ERR.id==id?`<span class="err">${esc(ERR.msg)}</span>`:''}</div>`}).join('')}
function p1(){const n=SET.length,h=SET.filter(e=>e.h).length,l=SET.filter(e=>e.lock).length;
 const F=[['all','All '+n],['chg','Changed'],['hid','No normal control '+h],['lock','Locked '+l]];
 return pane(`<input class="dlq" id="dlQ" type="search" placeholder="Search ${n} settings by id or words" value="${esc(ST.q)}" aria-label="Search settings"><span class="sg">${F.map(f=>`<button data-flt="${f[0]}" aria-pressed="${ST.filter==f[0]}">${f[1]}</button>`).join('')}</span><span class="sg" title="Where a change is written">${[['user','Write to: mine'],['project','this project']].map(f=>`<button data-tgt="${f[0]}" aria-pressed="${ST.target==f[0]}">${f[1]}</button>`).join('')}</span>`,`<div class="dlbody" id="dlSetList">${setRows()}</div>`)
 +pane(fileHead('The files this writes'),`<div class="dlbody" style="gap:0"><div class="dlgrp">settings.json · yours, on this computer</div><pre class="dlfile">${esc(j({audiolab:'settings',version:1,values:ST.safe?{}:CUST.settingsUser}))}</pre><div class="dlgrp">inside the project file · travels with the song</div><pre class="dlfile">${esc(j({settings:CUST.settingsProject}))}</pre></div>`,`<div class="dlmsg">Three layers, the later one wins: AudioLab's defaults, then yours, then the project's. Only what differs from the default is written, so an update that improves a default reaches you.</div>`)}

/* P2 */
const scopeKey=()=>ST.scopeAll?'all':ST.layout;
function ruleFor(id,make){const L=CUST.rules[scopeKey()];let r=L.find(r=>r.id==id);if(!r&&make){r={id};L.push(r)}return r}
function tidyRules(){for(const k in CUST.rules)CUST.rules[k]=CUST.rules[k].filter(r=>r.hide||r.rename||r.before||r.after)}
function ruleText(r){const p=[];if(r.hide)p.push('hidden');if(r.rename)p.push('renamed “'+r.rename+'”');if(r.before)p.push('moved before '+r.before);if(r.after)p.push('moved after '+r.after);return p.join(', ')}
let RMSG=null;
function p2(){const id=ST.picked,c=id&&CTL[id],r=id&&ruleFor(id);
 let acts;
 if(!c)acts=`<div class="dlhint">${ST.picking?'Now click a control in the mock above.':'Press “Pick an element”, then click any control in the mock.'}</div>`;
 else acts=`<div class="dlacts"><b style="font:500 12px var(--mono)">${esc(id)}</b><small style="color:var(--mut)">in ${BOXNAME[c.box]}</small></div>
  <div class="dlacts"><input type="text" id="dlRen" maxlength="24" placeholder="New name" value="${esc(r&&r.rename||'')}" aria-label="New name for ${esc(id)}"><button class="B" data-ract="rename">Rename</button>
  <button class="B" data-ract="hide" aria-pressed="${!!(r&&r.hide)}">${r&&r.hide?'Hidden: show again':'Hide'}</button><button class="B" data-ract="earlier">◀ Move earlier</button><button class="B" data-ract="later">Move later ▶</button><button class="B dng" data-ract="reset">Reset this control</button></div>`;
 const all=[];for(const k of ['all','arrange','mix','compact'])for(const r of CUST.rules[k])all.push({k,r});
 const list=all.length?all.map((x,i)=>`<div class="dlchg"><span>${esc(x.r.id)} <small>${esc(ruleText(x.r))} · ${x.k=='all'?'every layout':'only '+LAYOUTS[x.k]}</small></span><button class="rs" data-rdel="${x.k}|${esc(x.r.id)}" aria-label="Remove this rule">✕</button></div>`).join(''):'<div class="dlhint">No rules yet.</div>';
 const warn=checkRules(),msg=RMSG||(warn.length?{k:'bad',t:warn.join(' ')}:{k:'ok',t:'The file is valid. '+all.length+' rule'+(all.length==1?'':'s')+'.'});
 return pane(`<button class="B pri" data-act="pick" aria-pressed="${ST.picking}">${ST.picking?'Picking… (click to stop)':'Pick an element'}</button><button class="B" data-act="ghosts" aria-pressed="${ST.ghosts}">Show hidden ones faintly</button><span class="sp"></span><span class="sg">${[[1,'Every layout'],[0,'Only '+LAYOUTS[ST.layout]]].map(f=>`<button data-scope="${f[0]}" aria-pressed="${!!f[0]==ST.scopeAll}">${f[1]}</button>`).join('')}</span>`,
  acts+`<div class="dlex"><button class="B" data-chat="rules">Chat box: “hide the sends and the R button in the mixer”</button></div><div class="dlbody"><div class="dlgrp">Rules in use</div>${list}</div>`)
 +pane(fileHead('ui-rules.json','<button class="B" data-act="rapply">Apply what I typed</button>'),`<textarea class="dlfile" id="dlRules" spellcheck="false" aria-label="The rules file">${esc(j({audiolab:'ui-rules',version:1,layouts:CUST.rules}))}</textarea>`,`<div class="dlmsg ${msg.k}">${esc(msg.t)}</div>`)}
function ruleAct(a){const id=ST.picked,c=CTL[id];if(!c)return;RMSG=null;
 if(a=='reset'){for(const k in CUST.rules)CUST.rules[k]=CUST.rules[k].filter(r=>r.id!=id)}
 else if(a=='hide'){if(c.prot){RMSG={k:'bad',t:id+' cannot be hidden. '+c.prot};return}const r=ruleFor(id,1);r.hide?delete r.hide:r.hide=true}
 else if(a=='rename'){const v=$('#dlRen').value.trim();const r=ruleFor(id,1);v?r.rename=v:delete r.rename}
 else{const ids=layoutOf(c.box).map(x=>x.id),i=ids.indexOf(id),t=a=='earlier'?ids[i-1]:ids[i+1];if(!t){RMSG={k:'bad',t:'It is already at the '+(a=='earlier'?'start':'end')+' of '+BOXNAME[c.box]+'.'};return}
  const r=ruleFor(id,1);delete r.before;delete r.after;a=='earlier'?r.before=t:r.after=t}
 tidyRules()}
function applyRulesText(){let o;try{o=JSON.parse($('#dlRules').value)}catch(e){RMSG={k:'bad',t:'Not valid JSON, so nothing was changed: '+e.message};return}
 if(!o||o.audiolab!='ui-rules'||typeof o.layouts!='object'){RMSG={k:'bad',t:'This is not a ui-rules file ("audiolab": "ui-rules" and "layouts" are needed). Nothing was changed.'};return}
 if(o.version>1){RMSG={k:'bad',t:'This file is for a newer AudioLab (version '+o.version+'). Nothing was changed.'};return}
 const out={all:[],arrange:[],mix:[],compact:[]};let skipped=0;
 for(const k in out)for(const r of Array.isArray(o.layouts[k])?o.layouts[k]:[]){if(!r||typeof r.id!='string'){skipped++;continue}const n={id:r.id};if(r.hide===true)n.hide=true;if(typeof r.rename=='string')n.rename=r.rename.slice(0,24);if(typeof r.before=='string')n.before=r.before;else if(typeof r.after=='string')n.after=r.after;out[k].push(n)}
 CUST.rules=out;tidyRules();const w=checkRules();RMSG=w.length||skipped?{k:'bad',t:'Applied, with notes: '+w.join(' ')+(skipped?' '+skipped+' entries had no id and were left out.':'')}:{k:'ok',t:'Applied.'}}

/* P3 */
function allCmds(){const m=ST.safe?[]:Object.keys(CUST.macros).map(macroCmd);return [...m,...CMD]}
function cmdRows(){const q=ST.cq.trim().toLowerCase().split(/\s+/).filter(Boolean);let g='',h='';
 for(const c of allCmds()){if(!q.every(w=>(c.id+' '+c.name+' '+c.g).toLowerCase().includes(w)))continue;
  if(c.g!=g){g=c.g;h+=`<div class="dlgrp">${g}</div>`}const k=keyOf(c.id),on=CUST.toolbar.includes(c.id);
  h+=`<div class="dlcmd"><span class="id">${esc(c.id)}<small>${esc(c.name)}${c.macro?' · '+c.macro.steps.length+' steps':''}</small></span><button class="dlkey${ST.waitKey==c.id?' w':''}" data-key="${esc(c.id)}" title="Click, then press the new keys. Backspace removes the key.">${ST.waitKey==c.id?'press…':esc(k)||'no key'}</button><button class="B" data-run="${esc(c.id)}" title="Run it now">▶</button><button class="B" data-bar="${esc(c.id)}" aria-pressed="${on}" title="Show on the toolbar">bar</button>${ST.macroOpen?`<button class="B" data-step="${esc(c.id)}" title="Add as a step">＋step</button>`:c.macro?`<button class="rs" data-mdel="${esc(c.id.slice(6))}" aria-label="Delete this macro">✕</button>`:'<span></span>'}</div>`}
 return h||'<div class="dlhint">No command matches.</div>'}
function p3(){const d=ST.macroDraft;
 const draft=ST.macroOpen?`<div class="dlacts"><input type="text" id="dlMName" placeholder="Name of the macro" maxlength="30" value="${esc(d.name)}" aria-label="Name of the macro"><button class="B pri" data-act="msave">Save macro</button><button class="B" data-act="mcancel">Cancel</button></div><div class="dlsteps">${d.steps.length?d.steps.map((s,i)=>`<div class="st"><b>${i+1}</b><span>${esc(s)}</span><button class="rs" data-sup="${i}" aria-label="Move step up" ${i?'':'disabled'}>↑</button><button class="rs" data-sdel="${i}" aria-label="Remove step">✕</button></div>`).join(''):'<span style="color:var(--mut)">Press ＋step on the commands below, in the order they should run.</span>'}</div>`:'';
 const file={audiolab:'commands',version:1,keys:CUST.keys,toolbar:CUST.toolbar,macros:CUST.macros};
 return pane(`<input class="dlq" id="dlCQ" type="search" placeholder="Search ${allCmds().length} commands" value="${esc(ST.cq)}" aria-label="Search commands"><button class="B${ST.macroOpen?'':' pri'}" data-act="mnew" aria-pressed="${ST.macroOpen}">New macro</button>`,draft+`<div class="dlbody" id="dlCmdList">${cmdRows()}</div>`)
 +pane(fileHead('commands.json'),`<pre class="dlfile">${esc(j(file))}</pre>`,`<div class="dlmsg" id="dlCmdMsg">Only your changes are in the file. A key that is not listed keeps AudioLab's default.</div>`)}

/* P4 */
const CSSX=[['Big mute and solo','/* Larger M and S buttons on every strip */\n[al="mixer.strip.mute"], [al="mixer.strip.solo"] {\n  height: 30px;\n  font-size: 14px;\n  font-weight: 700;\n}'],
 ['Amber meters, square strips','.al-meter { background: #e3b341; }\n.al-strip { border-radius: 0; }\n.al-clip  { border-top-width: 8px; }'],
 ['Tries to break things','/* Each line here is stopped by a guard rail */\n@import url("https://example.org/theme.css");\n[al="transport.play"] { background: url(https://example.org/x.png); color: #7be0ae; }\n[al="mixer.master.limiter"] { display: none; }']];
const PROT=Object.keys(CTL).filter(k=>CTL[k].prot);
function cleanCss(text){const rep=[];if(/@import/i.test(text))rep.push('Left out @import: a snippet cannot load other files.');
 let sh;try{sh=new CSSStyleSheet();sh.replaceSync(text.replace(/\[al([~^$*|]?=)/g,'[data-al$1'))}catch(e){return{css:'',rep:['Could not read the CSS: '+e.message]}}
 const out=[];for(const r of sh.cssRules){if(!(r instanceof CSSStyleRule)){rep.push('Left out '+r.cssText.split('{')[0].trim()+': only plain style rules are allowed.');continue}
  const d=[];for(let i=0;i<r.style.length;i++){const p=r.style[i],v=r.style.getPropertyValue(p);
   if(/url\(|image-set|expression/i.test(v)){rep.push('Left out '+p+' on '+r.selectorText.replace(/data-al/g,'al')+': no files or web addresses.');continue}
   if(p=='position'&&/fixed|sticky/.test(v)){rep.push('Left out position: '+v+': a snippet cannot cover the window.');continue}
   d.push(p+':'+v+(r.style.getPropertyPriority(p)?' !important':''))}
  if(d.length)out.push(r.selectorText.split(',').map(s=>'#dlRoot #dlApp:not(#x#y) '+s.trim().replace(/^(:root|html|body)\b/,'')).join(',')+'{'+d.join(';')+'}')}
 return{css:out.join('\n'),rep}}
let cssEl=null;
function applyCss(){if(!cssEl){cssEl=document.createElement('style');cssEl.id='dlUserCss';document.head.appendChild(cssEl)}
 const on=CUST.css.on&&!ST.safe&&CUST.css.clean;cssEl.textContent=on?CUST.css.clean:'';if(!on)return;
 for(const id of PROT){const el=$(`[data-al="${id}"]`,app);if(!el)continue;const cs=getComputedStyle(el),b=el.getBoundingClientRect();
  if(cs.display=='none'||cs.visibility=='hidden'||+cs.opacity<.4||b.width<6||b.height<6){cssEl.textContent='';CUST.css.on=false;CUST.css.rep=(CUST.css.rep||[]).concat('Switched off: it hid '+id+'. '+CTL[id].prot+' Remove that rule and switch it on again.');return}}}
function setCss(text,on){const r=cleanCss(text);CUST.css={on,text,clean:r.css,rep:r.rep}}
function p4(){const c=CUST.css,rep=c.rep||[];
 return pane(`<b>snippets/my-look.css</b><span class="sp"></span><button class="sw" role="switch" id="dlCssOn" aria-checked="${!!c.on}" data-act="csson" aria-label="Snippet on"></button><button class="B pri" data-act="cssapply">Apply</button>`,
  `<div class="dlex">${CSSX.map((x,i)=>`<button class="B" data-cssx="${i}">${i+1} ${x[0]}</button>`).join('')}</div><textarea class="dlfile" id="dlCss" spellcheck="false" placeholder="Type CSS here, or press an example. A control is addressed by its id: [al=&quot;transport.play&quot;]" aria-label="Your CSS">${esc(c.text)}</textarea>`)
 +pane(fileHead('What the guard rails did'),`<div class="dlbody">${rep.length?rep.map(r=>`<div class="dlchg"><span style="color:#ffb9b9;font-family:var(--f)">${esc(r)}</span></div>`).join(''):`<div class="dlhint">${c.text?(c.on?'Nothing was left out. The snippet is on.':'The snippet is off.'):'Nothing yet.'}</div>`}
  <div class="dlgrp">What a snippet can reach</div><div class="dlhint">Controls by id, <b>[al="mixer.strip.mute"]</b>, and a short list of named parts that stay the same between versions: <b>.al-strip</b>, <b>.al-track</b>, <b>.al-clip</b>, <b>.al-meter</b>. Use the picker in P2 to find an id. Anything else in AudioLab's inner markup may change with an update.</div></div>`,`<div class="dlmsg">${c.on?'On · '+c.clean.split('\n').length+' rule(s) in use':'Off · nothing from this snippet is in use'}</div>`)}

/* P5: scripts in a worker */
const SCR=[['Colour all tracks by type',"// Colour every track by what it is.\nconst colours = { drums:'#e5534b', bass:'#4c8dff', lead:'#e3b341', pad:'#b77bff', fx:'#3ecf8e', vocal:'#f0883e' };\nfor (const track of al.project.tracks) {\n  track.setColor(colours[track.type] || '#8b8b97');\n  console.log(track.name, 'is', track.type);\n}"],
 ['Humanise selected notes',"// Move each selected note a little in time and loudness.\nconst amount = 0.2;   // in sixteenth notes\nconst notes = al.selection.notes;\nfor (const note of notes) {\n  note.set({\n    start: Math.max(0, note.start + (Math.random() * 2 - 1) * amount),\n    velocity: Math.round(note.velocity - Math.random() * 35)\n  });\n}\nconsole.log('Humanised', notes.length, 'notes. Undo puts them back.');"],
 ['Add a toolbar button',"// Adds a button at the right end of the transport bar.\n// It stays until the script is stopped.\nal.ui.addToolbarButton({\n  id: 'octave-flip',\n  label: 'Octave flip',\n  onClick() {\n    for (const note of al.selection.notes) {\n      note.set({ pitch: note.pitch >= 69 ? note.pitch - 12 : note.pitch + 12 });\n    }\n    console.log('Flipped', al.selection.notes.length, 'notes');\n  }\n});\nconsole.log('Button added. Press it in the mock.');"],
 ['Never ends (time limit)',"// A script with a mistake: this loop never ends.\n// Press Play in the mock first: the music keeps going.\nlet n = 0;\nwhile (true) { n++; }"],
 ['Asks for the network',"// Scripts have no network of their own.\nconsole.log('fetch is', typeof fetch);\n// The only door is al.net.fetch, and it asks you first.\nconst reply = await al.net.fetch('https://presets.example.org/list.json');\nconsole.log('Got', reply.presets.length, 'preset names:', reply.presets.join(', '));"],
 ['Touches a safety value',"// One allowed change, one out of range, one locked.\nal.settings.set('mixer.stripWidth', 110);\nal.settings.set('mixer.stripWidth', 9999);\nal.settings.set('safety.limiter.ceilingDb', 6);\nal.project.tracks[0].setColor('not a colour');"],
 ['Chat box: “make every second note softer”',"// Written by the chat box. It explains each step:\n// 1. take the notes of the selected clip, in time order\nconst notes = al.project.notes.sort((a, b) => a.start - b.start);\n// 2. every second one gets 45 less velocity (never below 1)\nnotes.forEach((note, i) => {\n  if (i % 2 === 1) note.set({ velocity: Math.max(1, note.velocity - 45) });\n});\nconsole.log('Softened', Math.floor(notes.length / 2), 'notes');"]];
let CODE=SCR[0][1],PERM=null;
function workerMain(){'use strict';
 for(const k of ['fetch','XMLHttpRequest','WebSocket','EventSource','importScripts','indexedDB','caches','Worker','SharedWorker','BroadcastChannel','Notification','WebTransport','RTCPeerConnection','navigator','location']){for(let o=self;o;o=Object.getPrototypeOf(o)){try{Object.defineProperty(o,k,{value:undefined,configurable:false,writable:false})}catch(e){}}}
 const post=self.postMessage.bind(self);let snap=null,ops=[],handlers={},asks={},askN=0,nextH=0;
 const op=o=>{ops.push(o);if(ops.length>5000)throw new Error('Too many changes in one run (the limit is 5000).')};
 const trackW=t=>({get id(){return t.id},get name(){return t.name},get type(){return t.type},get color(){return t.color},get muted(){return !!t.mute},get soloed(){return !!t.solo},
  setColor(c){t.color=String(c);op({o:'track',id:t.id,k:'color',v:t.color})},setName(n){t.name=String(n);op({o:'track',id:t.id,k:'name',v:t.name})},
  setMuted(b){t.mute=b?1:0;op({o:'track',id:t.id,k:'mute',v:t.mute})},setSoloed(b){t.solo=b?1:0;op({o:'track',id:t.id,k:'solo',v:t.solo})}});
 const noteW=n=>({get id(){return n.id},get start(){return n.start},get length(){return n.length},get pitch(){return n.pitch},get velocity(){return n.velocity},get selected(){return !!n.selected},
  set(c){for(const k of ['start','length','pitch','velocity'])if(c&&k in c){n[k]=Number(c[k]);op({o:'note',id:n.id,k,v:n[k]})}}});
 const al={version:'0.1',
  project:{get tempo(){return snap.tempo},setTempo(v){snap.tempo=Number(v);op({o:'tempo',v:snap.tempo})},get tracks(){return snap.tracks.map(trackW)},get notes(){return snap.notes.map(noteW)}},
  selection:{get track(){const t=snap.tracks.find(t=>t.id==snap.sel);return t?trackW(t):null},get notes(){return snap.notes.filter(n=>n.selected).map(noteW)}},
  transport:{get playing(){return snap.playing},play(){op({o:'play',v:1})},stop(){op({o:'play',v:0})}},
  commands:{run(id){op({o:'cmd',id:String(id)})}},
  settings:{get(id){return snap.settings[id]},set(id,v){op({o:'setting',id:String(id),v})}},
  ui:{addToolbarButton(b){const h='h'+(++nextH);handlers[h]=b.onClick;op({o:'button',id:String(b.id),label:String(b.label),h})}},
  net:{fetch(url){return new Promise((res,rej)=>{const n=++askN;asks[n]={res,rej};post({t:'ask',n,perm:'network',url:String(url)})})}}};
 const fmt=a=>typeof a=='string'?a:(()=>{try{return JSON.stringify(a)}catch(e){return String(a)}})();
 const con={log:(...a)=>post({t:'log',k:'i',m:a.map(fmt).join(' ')}),warn:(...a)=>post({t:'log',k:'w',m:a.map(fmt).join(' ')}),error:(...a)=>post({t:'log',k:'e',m:a.map(fmt).join(' ')})};
 const AF=Object.getPrototypeOf(async function(){}).constructor;
 self.onmessage=async e=>{const d=e.data;
  if(d.t=='run'){snap=d.snap;ops=[];handlers={};const t0=performance.now();try{await new AF('al','console','"use strict";'+d.code)(al,con);post({t:'done',ops,ms:performance.now()-t0,keep:Object.keys(handlers).length>0})}catch(err){post({t:'fail',m:String(err&&err.message||err)})}}
  else if(d.t=='event'){snap=d.snap;ops=[];try{await handlers[d.h]();post({t:'done',ops,ev:1,keep:true})}catch(err){post({t:'fail',m:String(err&&err.message||err),keep:true})}}
  else if(d.t=='answer'){const a=asks[d.n];delete asks[d.n];if(a)d.ok?a.res(d.body):a.rej(new Error('The network was not allowed.'))}}}
let W=null,wTimer=null,wBusy=false;
function killWorker(why){if(W){W.terminate();W=null}clearTimeout(wTimer);wBusy=false;PERM=null;const had=CUST.scripts.buttons.length;CUST.scripts.buttons=[];if(why)say(why,'e');if(had||why)renderAll()}
function arm(ms,what){clearTimeout(wTimer);wTimer=setTimeout(()=>killWorker('Stopped by AudioLab: '+what+' took longer than '+(ms>=1000?ms/1000+' s':ms+' ms')+'. Nothing it did was applied. The music and the window never waited for it.'),ms)}
function snapForScript(){const s=clone(P);s.playing=!!T.playing;s.settings={};SET.forEach(e=>s.settings[e.id]=eff(e.id));return s}
function runScript(code){if(ST.safe){say('Safe mode is on: scripts do not run.','w');return}killWorker();let w;
 try{w=new Worker(URL.createObjectURL(new Blob(['('+workerMain+')()'],{type:'text/javascript'})))}catch(e){say('This page could not start the sandbox ('+e.message+').','e');return}
 W=w;w.onmessage=onW;w.onerror=e=>{say('Script error: '+e.message,'e');killWorker()};say('▶ Running in the sandbox…','i');wBusy=true;arm(eff('safety.script.runLimitMs'),'the script');w.postMessage({t:'run',code,snap:snapForScript()});renderTool()}
function onW(e){const d=e.data;if(e.target!==W)return;
 if(d.t=='log'){say(d.m,d.k);return}
 if(d.t=='ask'){clearTimeout(wTimer);PERM=d;renderTool();return}
 clearTimeout(wTimer);wBusy=false;
 if(d.t=='fail'){say('Error: '+d.m+' Nothing was applied.','e');if(!d.keep)killWorker();renderTool();return}
 const r=applyOps(d.ops,d.ev?'Script button':'Script');
 say((d.ev?'Button handler':'Finished'+(d.ms!=null?' in '+Math.max(1,Math.round(d.ms))+' ms':''))+': '+r.ok+' change'+(r.ok==1?'':'s')+' applied'+(r.ok?' as one undo step':'')+(r.bad.length?', '+r.bad.length+' refused.':'.'),r.bad.length?'w':'o');
 r.bad.forEach(b=>say('  refused: '+b,'w'));if(!d.keep){W.terminate();W=null}renderAll()}
function applyOps(ops,label){const bad=[];let ok=0;const n0=UNDO.length,before=JSON.stringify(P);
 for(const o of ops||[]){
  if(o.o=='track'){const t=P.tracks.find(t=>t.id==o.id);if(!t){bad.push('no track '+o.id);continue}
   if(o.k=='color'){if(!/^#[0-9a-f]{6}$/i.test(o.v)){bad.push('"'+o.v+'" is not a colour like #4c8dff');continue}t.color=o.v}
   else if(o.k=='name')t.name=String(o.v).slice(0,24);else if(o.k=='mute'||o.k=='solo')t[o.k]=o.v?1:0;else{bad.push('unknown track field '+o.k);continue}ok++}
  else if(o.o=='note'){const n=P.notes.find(n=>n.id==o.id);if(!n||!isFinite(o.v)){bad.push('bad note change');continue}
   n[o.k]=o.k=='start'?clamp(o.v,0,31.5):o.k=='length'?clamp(o.v,.25,8):o.k=='pitch'?clamp(Math.round(o.v),50,84):clamp(Math.round(o.v),1,127);ok++}
  else if(o.o=='tempo'){if(!isFinite(o.v)){bad.push('tempo must be a number');continue}P.tempo=clamp(Math.round(o.v),40,240);ok++}
  else if(o.o=='play'){setPlaying(!!o.v);ok++}
  else if(o.o=='cmd'){if(runCmd(o.id,'quiet')===false)bad.push('no command '+o.id);else ok++}
  else if(o.o=='setting'){const r=setSetting(o.id,o.v);if(r.bad)bad.push(o.id+' = '+o.v+': '+r.bad);else ok++}
  else if(o.o=='button'){const B=CUST.scripts.buttons;if(B.length>=8&&!B.some(b=>b.id==o.id)){bad.push('at most 8 script buttons');continue}CUST.scripts.buttons=B.filter(b=>b.id!=o.id).concat({id:o.id.slice(0,30),label:o.label.slice(0,24),h:o.h});ok++}
  else bad.push('unknown change')}
 UNDO.length=Math.min(UNDO.length,n0);if(JSON.stringify(P)!==before){UNDO.push({label,snap:before});REDO.length=0}return{ok,bad}}
function scriptButton(id){const b=CUST.scripts.buttons.find(b=>b.id==id);if(!b||!W)return;if(wBusy){say('The script is still busy.','w');return}wBusy=true;arm(Math.max(250,eff('workshop.scriptHandlerMs')),'the button handler');W.postMessage({t:'event',h:b.h,snap:snapForScript()})}
function answerPerm(ok){const d=PERM;PERM=null;if(!W||!d)return;say(ok?'You allowed the network once for '+permHost(d)+'.':'You did not allow the network.',ok?'o':'w');arm(eff('safety.script.runLimitMs'),'the script');
 W.postMessage({t:'answer',n:d.n,ok,body:{presets:['Acid Line 303','Rolling Bass','Night Pad','Forest Lead']}});renderTool()}
const permHost=d=>{try{return new URL(d.url).host}catch(e){return d.url}};
const API=`al.project.tracks        list of tracks: id, name, type, color, muted, soloed
  .setColor('#rrggbb') .setName(text) .setMuted(bool) .setSoloed(bool)
al.project.notes         notes of the selected clip: id, start, length, pitch, velocity
  .set({ start, length, pitch, velocity })
al.project.tempo  al.project.setTempo(bpm)
al.selection.track  al.selection.notes
al.transport.playing  al.transport.play()  .stop()
al.commands.run('clip.quantize16')     any command from P3, also macros
al.settings.get(id)  al.settings.set(id, value)     same checks as P1
al.ui.addToolbarButton({ id, label, onClick })
await al.net.fetch(url)                asks you on a card first
console.log(...)`;
function p5(){const perm=PERM?`<div class="dlperm"><b>This script asks for something</b><span>Network access to <b style="font:500 12px var(--mono)">${esc(permHost(PERM))}</b>. Scripts cannot reach the internet unless you allow it. The time limit is paused while you decide.</span><div><button class="B pri" data-perm="1">Allow once</button><button class="B" data-perm="0">Don't allow</button></div></div>`:'';
 return pane(`<b>scripts/my-script.js</b><span class="sp"></span><button class="B pri" data-act="srun">▶ Run</button><button class="B" data-act="sstop" ${W?'':'disabled'}>■ Stop${CUST.scripts.buttons.length?' (removes its button)':''}</button>`,
  `<div class="dlex">${SCR.map((x,i)=>`<button class="B" data-scr="${i}">${i<6?(i+1)+' ':''}${esc(x[0])}</button>`).join('')}</div>${perm}<textarea class="dlfile" id="dlCode" spellcheck="false" aria-label="Your script">${esc(CODE)}</textarea>`)
 +pane(fileHead('Console','<button class="B" data-act="cclear">Clear</button>'),`<div class="dlcon" id="dlCon" aria-live="polite"></div><div class="dlgrp" style="margin:8px 10px 0">The API on one page (made from the same lists as P1 and P3)</div><pre class="dlfile" style="font-size:11px">${esc(API)}</pre>`)}

/* P6 */
const EMPTY=()=>({settingsUser:{},settingsProject:{},rules:{all:[],arrange:[],mix:[],compact:[]},keys:{},toolbar:[],macros:{},css:{on:false,text:''},scripts:{buttons:[]}});
let BACKUP=null,ASKRESET=false;
function changes(){const L=[];
 for(const id in CUST.settingsUser)L.push({g:'Settings (yours)',t:id+' = '+CUST.settingsUser[id],s:'default '+SBY[id].def,del:()=>delete CUST.settingsUser[id]});
 for(const id in CUST.settingsProject)L.push({g:'Settings (this project)',t:id+' = '+CUST.settingsProject[id],s:'',del:()=>delete CUST.settingsProject[id]});
 for(const k in CUST.rules)CUST.rules[k].forEach(r=>L.push({g:'Controls',t:r.id,s:ruleText(r)+(k=='all'?'':' · only '+LAYOUTS[k]),del:()=>{CUST.rules[k]=CUST.rules[k].filter(x=>x!==r)}}));
 for(const id in CUST.keys)L.push({g:'Keys',t:id,s:(CUST.keys[id]||'no key')+(CBY[id]&&CBY[id].key?' · default '+CBY[id].key:''),del:()=>delete CUST.keys[id]});
 CUST.toolbar.forEach(id=>L.push({g:'Toolbar',t:id,s:'button added',del:()=>{CUST.toolbar=CUST.toolbar.filter(x=>x!=id)}}));
 for(const s in CUST.macros)L.push({g:'Macros',t:'macro.'+s,s:CUST.macros[s].steps.length+' steps',del:()=>{delete CUST.macros[s];delete CUST.keys['macro.'+s];CUST.toolbar=CUST.toolbar.filter(x=>x!='macro.'+s)}});
 if(CUST.css.text)L.push({g:'CSS',t:'snippets/my-look.css',s:CUST.css.on?'on':'off',del:()=>{CUST.css={on:false,text:''}}});
 CUST.scripts.buttons.forEach(b=>L.push({g:'Scripts',t:'button “'+b.label+'”',s:'from a running script',del:()=>killWorker()}));return L}
let CHG=[];
function p6(){CHG=changes();let g='',list='';CHG.forEach((c,i)=>{if(c.g!=g){g=c.g;list+=`<div class="dlgrp">${g}</div>`}list+=`<div class="dlchg"><span>${esc(c.t)} <small>${esc(c.s)}</small></span><button class="rs" data-cdel="${i}" aria-label="Remove this change">✕</button></div>`});
 const bundle=Object.assign({audiolab:'customisations',version:1,madeWith:'AudioLab 0.3'},{settings:CUST.settingsUser,uiRules:CUST.rules,commands:{keys:CUST.keys,toolbar:CUST.toolbar,macros:CUST.macros},css:CUST.css.text?{'my-look.css':{on:CUST.css.on,text:CUST.css.text}}:{},scripts:{}});
 return pane(`<b>Everything you changed: ${CHG.length}</b><span class="sp"></span><button class="B" data-act="safe" aria-pressed="${ST.safe}">Safe mode ${ST.safe?'is on':'is off'}</button>`,
  `<div class="dlacts">${ASKRESET?`<span style="flex:1 1 200px">Remove all ${CHG.length} changes? A backup is kept, so this can be put back.</span><button class="B dng" data-act="resetyes">Yes, reset</button><button class="B" data-act="resetno">Cancel</button>`:`<button class="B dng" data-act="reset" ${CHG.length?'':'disabled'}>Reset my customisations…</button>${BACKUP?'<button class="B" data-act="restore">Put the backup back</button>':''}`}</div>
  <div class="dlbody">${list||'<div class="dlhint">AudioLab is exactly as it came.</div>'}</div>`,
  `<div class="dlmsg">In the app, safe mode also starts by holding Shift while AudioLab opens, and it is offered by itself when the last start did not finish.</div>`)
 +pane(fileHead('audiolab-customisations.json','<button class="B" data-act="bcopy">Copy</button>'),`<pre class="dlfile" id="dlBundle">${esc(j(bundle))}</pre>`,`<div class="dlmsg">One file to back up or carry to another computer. Audio devices and anything locked are never in it.</div>`)}

let DRAWING=false;
function renderTool(){if(DRAWING)return;DRAWING=true;try{tool.innerHTML=({P1:p1,P2:p2,P3:p3,P4:p4,P5:p5,P6:p6})[ST.tab]();const c=$('#dlCon');if(c){c.innerHTML=LOG.map(l=>`<div class="${l.k}">${esc(l.t)}</div>`).join('')||'<div class="i">Press Run. What a script prints shows here.</div>';c.scrollTop=c.scrollHeight}}finally{DRAWING=false}}
function renderAll(){renderApp();renderTabs();renderTool();picksLine()}

/* ---------- events ---------- */
$('#dlTabs').onclick=e=>{const b=e.target.closest('[data-tab]');if(!b)return;ST.tab=b.dataset.tab;ST.picking=false;RMSG=null;ERR=null;renderAll()};
$('#dlInfo').onclick=e=>{const b=e.target.closest('[data-yn]');if(!b)return;PK.P[ST.tab]=PK.P[ST.tab]==b.dataset.yn?'':b.dataset.yn;save();renderTabs()};
$('#dlStat').onclick=e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.lay){ST.layout=b.dataset.lay;RMSG=null}else if(b.dataset.act=='undo'){runCmd('edit.undo','quiet');return}else if(b.dataset.act=='safe')ST.safe=!ST.safe;renderAll()};
app.addEventListener('click',e=>{const t=e.target;
 if(t.closest('[data-act=unsafe]')){ST.safe=false;renderAll();return}
 const a=t.closest('[data-al]');
 if(ST.picking&&ST.tab=='P2'){if(a){ST.picked=a.dataset.al;RMSG=null;renderAll()}e.preventDefault();return}
 const r=t.closest('[data-run]');if(r){runCmd(r.dataset.run);return}
 const sb=t.closest('[data-sbtn]');if(sb){scriptButton(sb.dataset.sbtn);return}
 if(a){const id=a.dataset.al,c=CTL[id],tr=a.dataset.tr;
  if(tr){P.sel=tr;if(id=='mixer.strip.mute')return mutate('Mute',()=>{const x=selTrack();x.mute=x.mute?0:1});if(id=='mixer.strip.solo')return mutate('Solo',()=>{const x=selTrack();x.solo=x.solo?0:1});renderApp();return}
  if(c.cmd)runCmd(c.cmd,'quiet');return}
 const s=t.closest('[data-sel]');if(s){P.sel=s.dataset.sel;renderApp()}});
app.addEventListener('mouseover',e=>{if(!(ST.picking&&ST.tab=='P2'))return;const a=e.target.closest('[data-al]'),p=$('#dlPoint');if(p)p.innerHTML=a?'Pointing at <b>'+esc(a.dataset.al)+'</b>':''});
tool.addEventListener('input',e=>{const t=e.target;
 if(t.id=='dlQ'){ST.q=t.value;$('#dlSetList').innerHTML=setRows()}
 else if(t.id=='dlCQ'){ST.cq=t.value;$('#dlCmdList').innerHTML=cmdRows()}
 else if(t.id=='dlCode')CODE=t.value;else if(t.id=='dlMName')ST.macroDraft.name=t.value});
tool.addEventListener('change',e=>{const t=e.target,id=t.dataset.set;if(!id||t.tagName=='BUTTON'||DRAWING)return;
 const r=setSetting(id,t.type=='number'?t.value:t.value,ST.target);ERR=r.bad?{id,msg:r.bad+' The value was not changed.'}:null;if(r.bad){DRAWING=true;try{$('#dlSetList').innerHTML=setRows()}finally{DRAWING=false}}});
tool.addEventListener('keydown',e=>{if(e.key=='Enter'&&e.target.id=='dlRen'){ruleAct('rename');renderAll()}});
tool.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;const d=b.dataset;
 if(d.set){const r=setSetting(d.set,!eff(d.set),ST.target);ERR=r.bad?{id:d.set,msg:r.bad}:null;if(r.bad)renderTool();return}
 if(d.rst){delete CUST.settingsUser[d.rst];delete CUST.settingsProject[d.rst];ERR=null}
 else if(d.flt)ST.filter=d.flt;else if(d.tgt)ST.target=d.tgt;
 else if(d.scope!=null)ST.scopeAll=d.scope=='1';
 else if(d.ract)ruleAct(d.ract);
 else if(d.rdel){const[k,id]=d.rdel.split('|');CUST.rules[k]=CUST.rules[k].filter(r=>r.id!=id);RMSG=null}
 else if(d.chat=='rules'){CUST.rules.mix=CUST.rules.mix.filter(r=>r.id!='mixer.strip.sends'&&r.id!='mixer.strip.rec').concat({id:'mixer.strip.sends',hide:true},{id:'mixer.strip.rec',hide:true});ST.layout='mix';RMSG={k:'ok',t:'The chat box wrote 2 rules for the Mix layout and showed them here before applying. In the app you press Accept first.'}}
 else if(d.key){ST.waitKey=ST.waitKey==d.key?null:d.key}
 else if(d.run){runCmd(d.run);renderTool();return}
 else if(d.bar){CUST.toolbar=CUST.toolbar.includes(d.bar)?CUST.toolbar.filter(x=>x!=d.bar):CUST.toolbar.concat(d.bar)}
 else if(d.step){ST.macroDraft.steps.push(d.step)}
 else if(d.sdel!=null)ST.macroDraft.steps.splice(+d.sdel,1);
 else if(d.sup!=null){const s=ST.macroDraft.steps,i=+d.sup;[s[i-1],s[i]]=[s[i],s[i-1]]}
 else if(d.mdel){delete CUST.macros[d.mdel];delete CUST.keys['macro.'+d.mdel];CUST.toolbar=CUST.toolbar.filter(x=>x!='macro.'+d.mdel)}
 else if(d.cssx!=null){setCss(CSSX[+d.cssx][1],true)}
 else if(d.scr!=null){CODE=SCR[+d.scr][1]}
 else if(d.perm!=null){answerPerm(d.perm=='1');return}
 else if(d.cdel!=null){CHG[+d.cdel].del()}
 else switch(d.act){
  case'pick':ST.picking=!ST.picking;break;case'ghosts':ST.ghosts=!ST.ghosts;break;case'rapply':applyRulesText();break;
  case'mnew':ST.macroOpen=!ST.macroOpen;break;case'mcancel':ST.macroOpen=false;ST.macroDraft={name:'',steps:[]};break;
  case'msave':{const m=ST.macroDraft,name=m.name.trim();if(!name||!m.steps.length){renderTool();say(!name?'Give the macro a name first.':'Add at least one step.','e');return}
   const slug=name.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||'macro';CUST.macros[slug]={name,steps:m.steps.slice()};ST.macroOpen=false;ST.macroDraft={name:'',steps:[]};renderAll();say('Saved as macro.'+slug+'. It is now a command like any other.','o');return}
  case'csson':setCss($('#dlCss').value,!CUST.css.on);break;case'cssapply':setCss($('#dlCss').value,true);break;
  case'srun':CODE=$('#dlCode').value;runScript(CODE);return;case'sstop':killWorker();say('Stopped.','i');renderAll();return;case'cclear':LOG.length=0;break;
  case'safe':ST.safe=!ST.safe;break;case'reset':ASKRESET=true;break;case'resetno':ASKRESET=false;break;
  case'resetyes':BACKUP=clone(CUST);killWorker();CUST=EMPTY();ASKRESET=false;break;case'restore':if(BACKUP){CUST=BACKUP;BACKUP=null;if(CUST.css.text)setCss(CUST.css.text,CUST.css.on)}break;
  case'bcopy':{const tx=$('#dlBundle').textContent;(navigator.clipboard?navigator.clipboard.writeText(tx):Promise.reject()).then(()=>{b.textContent='Copied'},()=>{const r=document.createRange();r.selectNodeContents($('#dlBundle'));const s=getSelection();s.removeAllRanges();s.addRange(r)});return}
  default:return}
 renderAll()});
document.addEventListener('keydown',e=>{const typing=/INPUT|TEXTAREA|SELECT/.test(e.target.tagName);
 if(ST.waitKey){e.preventDefault();const id=ST.waitKey;ST.waitKey=null;
  if(e.key=='Escape'){renderTool();return}
  if(e.key=='Backspace'){CUST.keys[id]='';renderAll();say('Removed the key of '+id+'.','i');return}
  const ch=chord(e);if(!ch){ST.waitKey=id;return}
  const other=allCmds().find(c=>c.id!=id&&keyOf(c.id)==ch);if(other)CUST.keys[other.id]='';
  if(CBY[id]&&CBY[id].key==ch)delete CUST.keys[id];else CUST.keys[id]=ch;renderAll();say(id+' is now on '+ch+(other?'. '+other.id+' had that key and now has none.':'.'),'o');return}
 if(typing||!(app.matches(':hover')||app.contains(document.activeElement)))return;
 const ch=chord(e);if(!ch)return;const c=allCmds().find(c=>keyOf(c.id)==ch);if(c){e.preventDefault();runCmd(c.id);if(ST.tab=='P3')renderTool()}});

/* ---------- K: decisions ---------- */
const DEC=[
 {k:'K1',t:'How deep',o:[['a','Rules only: the everything list, hide / move / rename, commands and macros (P1 to P3)'],['b','Rules and CSS (P1 to P4)'],['c','Everything including scripts (P1 to P5), built in that order']],r:'c',why:'Each stage is useful alone and prepares the next. Scripts come last because they need the most care, and by then they sit on lists that already exist.'},
 {k:'K2',t:'Where it lives',o:[['a','A page "Advanced" inside Settings'],['b','Its own window, opened from the logo menu and from a link at the foot of Settings'],['c','Both: the everything list inside Settings, the rest in its own window']],r:'b',why:'Settings stays calm for everyone else. A window of its own has room for a file beside each tool, as on this page.'},
 {k:'K3',t:'What it is called',o:[['a','Workshop'],['b','Developer'],['c','Advanced'],['d','Lab bench']],r:'a',why:'It says "make and change things" without sounding like it is only for programmers.'},
 {k:'K4',t:'Who sees it',o:[['a','Always in the menu'],['b','Hidden until one switch in Settings turns it on'],['c','Hidden; a right-click "Hide this" and "Customise…" still works for everyone']],r:'c',why:'Hiding a button is the wish most people have, so that part needs no switch. The files, CSS and scripts stay out of sight until asked for.'},
 {k:'K5',t:'Where the files are kept',o:[['a','Inside AudioLab only, edited in the Workshop'],['b','Real files in a folder you can open (desktop app), one export file in the browser version'],['c','Real files, and AudioLab reloads them the moment they are saved from another editor']],r:'b',why:'Real files can be backed up, compared and shared. Live reload (c) is a small step to add later.'},
 {k:'K6',t:'What a project may carry',o:[['a','Nothing: customisations are yours only'],['b','Settings and control rules, never CSS or code'],['c','Also scripts, each asking on a card when the project opens']],r:'b',why:'A song file from someone else must never run code by being opened.'},
 {k:'K7',t:'Sharing scripts and macros',o:[['a','No sharing: your own only'],['b','As a file; opening one shows what it is, what it asks for, and the code, before anything runs'],['c','b, and later a gallery inside AudioLab']],r:'b',why:'Follows whatever is picked for sharing in the main extensions plan. A gallery needs reviewing and is a later question.'},
 {k:'K8',t:'Network for scripts',o:[['a','Never'],['b','Per script and per site, asked on a card, off by default'],['c','On for scripts you wrote yourself']],r:'b',why:'The Figma and userscript model. A script that only tidies notes should not be able to send anything anywhere.'},
 {k:'K9',t:'When a script takes too long',o:[['a','Stopped at 2 seconds, always'],['b','At 2 seconds AudioLab asks: wait longer or stop'],['c','No limit for scripts you wrote yourself']],r:'b',why:'A long but honest job (rename 400 clips) can finish, and a stuck one is still one click from gone. The audio never waits either way.'},
 {k:'K10',t:'The chat box',o:[['a','Writes rules, macros and scripts, shows them, and you press Accept'],['b','Applies them at once and tells you'],['c','Only explains; you type everything']],r:'a',why:'You always see what will change before it does, and the result is a normal file you can edit or remove.'},
 {k:'K11',t:'How safe mode starts',multi:1,o:[['a','Hold Shift while AudioLab opens'],['b','A menu item "Restart in safe mode"'],['c','Offered by itself when the last start did not finish']],r:'abc',why:'Three doors, because the moment you need it is the moment the usual door may be the broken thing.'},
 {k:'K12',t:'Right-click on any control',o:[['a','Adds "Hide this" and "Customise…" to every right-click menu'],['b','Only through the picker in the Workshop'],['c','Hold a key and click (Alt+Shift) to pick, no menu entry']],r:'a',why:'The shortest route to the first thing you asked for. The menu entry appears only where no right-click menu is already full.'}];
let PK={P:{},K:{}};
try{const s=JSON.parse(localStorage.getItem('al-ex2')||'null');if(s&&s.P&&s.K)PK=s}catch(e){}
DEC.forEach(d=>{if(!PK.K[d.k])PK.K[d.k]=d.r});
function save(){try{localStorage.setItem('al-ex2',JSON.stringify(PK))}catch(e){}picksLine()}
function renderDecs(){$('#decs').innerHTML=DEC.map(d=>`<div class="dec"><h3><span class="num">${d.k}</span>${d.t}</h3>${d.o.map(o=>{const rec=d.multi?d.r.includes(o[0]):d.r==o[0],on=d.multi?PK.K[d.k].includes(o[0]):PK.K[d.k]==o[0];
  return `<label><input type="${d.multi?'checkbox':'radio'}" name="dl-${d.k}" id="dl-${d.k}-${o[0]}" value="${o[0]}"${on?' checked':''}><span><b>${o[0]}</b> ${o[1]}</span>${rec?'<span class="star">★</span>':''}</label>`}).join('')}<p class="why">${d.why}</p></div>`).join('')}
$('#decs').onchange=e=>{const t=e.target,k=t.name.slice(3),d=DEC.find(d=>d.k==k);if(!d)return;PK.K[k]=d.multi?$$('input:checked',t.closest('.dec')).map(i=>i.value).join('')||'none':t.value;save()};
function picksText(){const p=TABS.map(t=>t.k+' '+(PK.P[t.k]||'?')).join(', ');return 'Deep layer | '+p+' | '+DEC.map(d=>d.k+PK.K[d.k]).join(' ')}
function picksLine(){const el=$('#picks');if(el&&!window.DeepLayerHost)el.textContent=picksText();document.dispatchEvent(new CustomEvent('deeplayer-picks',{detail:picksText()}))}
function takeAll(){TABS.forEach(t=>PK.P[t.k]='yes');DEC.forEach(d=>PK.K[d.k]=d.r);save();renderDecs();renderTabs()}
function startAgain(){PK={P:{},K:{}};DEC.forEach(d=>PK.K[d.k]=d.r);save();renderDecs();renderTabs()}
window.DeepLayer={picks:picksText,takeAll,startAgain};
if($('#useRec')&&!window.DeepLayerHost){$('#useRec').onclick=takeAll;$('#clr').onclick=startAgain;
 $('#copy').onclick=()=>{const tx=picksText(),b=$('#copy');(navigator.clipboard?navigator.clipboard.writeText(tx):Promise.reject()).then(()=>{b.textContent='Copied';setTimeout(()=>b.textContent='Copy my picks',1500)},()=>{const r=document.createRange();r.selectNodeContents($('#picks'));const s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Selected: press copy'})}}
renderDecs();renderAll();
})();
