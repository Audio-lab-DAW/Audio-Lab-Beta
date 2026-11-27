/* ===================== COMMANDS REGISTRY (v0.273, task XT-DL2) =====================
   The groundwork of macros, toolbars, scripts and the Assistant (docs/extensions-plan.md 9.6 c, 9.7 DL2): every action has one namespaced
   command id, and runCommand(id) is the one door that runs it. Built over the shortcut list SCA, which stays as it is: its ids remain the keys
   of UI.keys, the key presets (SCPRE) and SCM, so nobody's shortcuts change and every existing caller (SCM.get('play').run()) keeps working.
   - XT_CMD_NS gives each old SCA id its namespaced id; ids that already have a namespace (ctl.*, ni.*, clip.*, added by lanes C and D) are kept.
     A new SCA row without a namespace still works (group.id) but must get a row here and in docs/commands.md (tools/ui-tests/taskXT_DL2.py).
   - COMMAND_ALIAS: old id (and retired ids) to the namespaced id. A released command id is never renamed or reused (9.4 rules 1 and 2).
   - Gestures (rows that only describe a mouse or edit gesture, such as Copy or Shift-drag) are listed but cannot be run.
   - XT_CMD_EXTRA: commands that have a button but no row in the shortcut list (so the Settings list does not change).
   - XT_CMD_LOG: the last 50 commands run through runCommand, for the Workshop console (DL10).
   The registry is built on first use and again only when SCA grows; nothing runs at start, per frame or per key. */
const XT_CMD_NS={play:'transport.play',stop:'transport.stop',home:'transport.home',rec:'transport.record',loop:'transport.loop',click:'transport.metronome',
 save:'project.save',saveas:'project.saveAs',open:'project.open','new':'project.new','export':'project.export',tm:'project.timeMachine',midiexp:'project.exportMidi',
 undo:'edit.undo',redo:'edit.redo',redo2:'edit.redoAlt',del:'edit.delete',copy:'edit.copy',cut:'edit.cut',paste:'edit.paste',
 dup:'clip.duplicate',split:'clip.split',quant:'clip.quantize16',clipmute:'clip.mute',rename:'clip.rename',
 ajdup:'clip.dragCopy',ajnudge:'clip.nudge',ajtrack:'clip.moveToTrack',akmarq:'clip.marquee',akbounce:'clip.dropToAudio',ajbig:'clip.nudgeBig',ajfine:'clip.nudgeFine',
 newaudio:'track.newAudio',newmidi:'track.newInstrument',mute:'track.mute',solo:'track.solo',group:'track.group',ungroup:'track.ungroup',
 mixer:'view.mixer',devs:'view.devices',lite:'view.lightMode',settings:'view.settings',browser:'view.instrumentBrowser',fxbrowser:'view.effectsBrowser',
 pianoroll:'view.pianoRoll',kbd:'view.keyboard',follow:'view.follow',zoomin:'view.zoomIn',zoomout:'view.zoomOut',overview:'view.overview',aut:'view.automation',
 closewins:'view.closeWindows',keys:'help.shortcuts',ai:'help.assistant',tour:'help.tour'};
const XT_CMD_GESTURE=new Set(['del','copy','cut','paste','ajdup','ajnudge','ajtrack','akmarq','akbounce','ajbig','ajfine']);
const COMMAND_ALIAS=Object.assign({learn:'ctl.learn'},XT_CMD_NS);
const XT_CMD_EXTRA=[
 {id:'transport.countIn',g:'transport',l:'Count-in on / off',run:()=>{const b=document.getElementById('bCount');if(b)b.click()}},
 {id:'transport.tapTempo',g:'transport',l:'Tap tempo',run:()=>{const b=document.getElementById('bTap');if(b)b.click()}},
 {id:'transport.capture',g:'transport',l:'Capture what you just played',run:()=>{const b=document.getElementById('bCap');if(b)b.click()}}];
const XT_CMD={map:null,n:-1},XT_CMD_LOG=[];
/* the registry: Map of namespaced id to {id, name, group, defaultKey, key, legacy, gesture, when, run} */
function xtCommands(){const L=typeof SCA!=='undefined'?SCA:[];if(XT_CMD.map&&XT_CMD.n===L.length)return XT_CMD.map;const M=new Map();
  for(const a of L){const id=XT_CMD_NS[a.id]||(a.id.includes('.')?a.id:a.g+'.'+a.id);if(M.has(id))continue;
    M.set(id,{id,name:a.l,group:a.g,defaultKey:a.d||'',get key(){return typeof scBind==='function'?scBind(a)||'':a.d||''},legacy:a.id,gesture:XT_CMD_GESTURE.has(a.id),when:'global',run:a.run})}
  for(const x of XT_CMD_EXTRA)if(!M.has(x.id))M.set(x.id,{id:x.id,name:x.l,group:x.g,defaultKey:'',key:'',legacy:null,gesture:false,when:'global',run:x.run});
  XT_CMD.map=M;XT_CMD.n=L.length;return M}
/* the namespaced id of any id (namespaced, old, or retired), or null */
function xtCommandId(id){id=String(id||'');const M=xtCommands();for(let i=0;i<8&&!M.has(id)&&COMMAND_ALIAS[id];i++)id=COMMAND_ALIAS[id];
  if(M.has(id))return id;for(const c of M.values())if(c.legacy===id)return c.id;return null}
/* the one door: runs a command by any of its ids; false (with the reason in XT_CMD_LOG) when it is unknown, a gesture or fails */
function runCommand(id,src){const cid=xtCommandId(id),c=cid&&xtCommands().get(cid),e={id:cid||String(id),t:Date.now(),src:src||'',ok:false};
  if(!c)e.why='unknown';else if(c.gesture)e.why='gesture';else try{c.run();e.ok=true}catch(err){e.why='error';console.error('AudioLab command '+cid,err)}
  XT_CMD_LOG.push(e);if(XT_CMD_LOG.length>50)XT_CMD_LOG.shift();return e.ok}
