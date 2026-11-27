/* ===================== CONTROL IDS, part 1 (v0.266, task XT-DL1) =====================
   The groundwork of the Workshop (docs/extensions-plan.md 9.4 rule 1, 9.7 DL1): one stable id per control, in one table.
   CONTROLS rows: [id, selector inside the area's root, plain name]. The area is the id's first word (CONTROL_AREAS gives its root).
   Repeated controls (one per track header or mixer strip) share one id, so a later rule covers every track at once.
   A released id is never renamed or reused: the list is docs/ids.md, checked by tools/ui-tests/taskXT_DL1.py; a retired id
   goes into CONTROL_ALIAS (old id: new id). xtTag(area) writes data-al="<id>" on the area's controls after the area is built
   (renderHeaders, renderMixer, trApply), once per task turn in a microtask, after every other wrapper has run.
   Nothing reads data-al yet and nothing looks or behaves differently; no work per frame. */
const CONTROL_AREAS={transport:'#tr',track:'#hdrin',mixer:'#mixWin'};
const CONTROLS=[
 ['transport.logo','#bLogo','AudioLab menu button'],['transport.assistant','#bAI','Assistant button'],
 ['transport.locatorLeft','.lcd.loc:has(>#locL)','left locator'],['transport.locatorRight','.lcd.loc:has(>#locR)','right locator'],
 ['transport.home','#bHome','Go to start button'],['transport.loop','#bLoop','Loop button'],['transport.stop','#bStop','Stop button'],
 ['transport.play','#bPlay','Play button'],['transport.record','#bRec','Record button'],['transport.capture','#bCap','Capture button'],
 ['transport.keyboard','#bKbd','Keyboard piano button'],['transport.tempo','#bpm','tempo box'],['transport.tempoUp','#bpmUp','tempo up arrow'],
 ['transport.tempoDown','#bpmDn','tempo down arrow'],['transport.signature','.lcd.tempo .sig','time signature'],['transport.tap','#bTap','Tap tempo button'],
 ['transport.metronome','#bClick','Metronome button'],['transport.countIn','#bCount','Count-in button'],['transport.clickPattern','#mpat','click pattern'],
 ['transport.position','.lcd:has(>#posBars)','position display'],['transport.clock','.lcd:has(>#posTime)','clock display'],
 ['transport.tutorial','#bTut','Tutorial mode button'],['transport.mixer','#mBtn','Mixer button'],['transport.masterMeter','#mtr','master meter'],
 ['transport.clipWarning','#niClipB','clip warning'],['transport.peak','#peakBox','peak level box'],['transport.loudness','#lufsB','loudness box'],
 ['transport.performance','#cpu','performance meter'],
 ['transport.extra.gap','.trx-gap','flexible gap'],['transport.extra.space','.trx-space','fixed space'],['transport.extra.line','.trx-line','divider line'],
 ['transport.extra.timeOfDay','.trx-tod','time of day'],['transport.extra.progress','.trx-prog','song progress'],['transport.extra.tap','.trx-tap','extra Tap tempo button'],
 ['transport.extra.loopLength','.trx-sel','loop length'],['transport.extra.workTimer','.trx-work','work timer'],['transport.extra.section','.trx-sect','current section'],
 ['transport.extra.sectionPrevious','.trx-nav [data-sn="-1"]','Previous section button'],['transport.extra.sectionNext','.trx-nav [data-sn="1"]','Next section button'],
 ['transport.extra.midi','.trx-midi','MIDI activity light'],['transport.extra.clip','.trx-clip','clip indicator'],
 ['track.name','.hdr .nm','track name'],['track.fold','.hdr [data-gfold]','group fold arrow'],['track.volume','.hdr [data-c^="hd:"]','track volume slider'],
 ['track.mute','.hdr [data-a=mute]','track Mute button'],['track.solo','.hdr [data-a=solo]','track Solo button'],
 ['track.arm','.hdr [data-a=arm],.hdr [data-z=arm]','track Record arm button'],['track.edit','.hdr [data-a=edit]','Edit channel button'],
 ['track.read','.hdr [data-a=read]','Read automation button'],['track.pan','.hdr [data-c^="hp:"]','track pan slider'],
 ['track.writeAutomation','.hdr [data-a=aar]','Write automation button'],['track.lanes','.hdr [data-a=lanes]','Automation lanes button'],
 ['track.freeze','.hdr [data-z=freeze]','Freeze button'],['track.effectsOff','.hdr [data-z=byp]','Effects off button'],
 ['track.output','.hdr [data-z=out]','track Output button'],['track.sends','.hdr [data-z=sends]','track Sends button'],['track.color','.hdr [data-z=color]','track colour button'],
 ['track.meter','.hdr .vm','track level meter'],['track.resize','.hdr .rsz','track height handle'],
 ['track.lane.write','.lhd [data-la=w]','lane Write button'],['track.lane.editor','.lhd [data-la=ed]','lane Envelope editor button'],
 ['track.lane.hide','.lhd [data-la=x]','lane Hide button'],['track.lane.resize','.lhd .lrz','lane height handle'],
 ['track.recordAutomation','#bAR','Record automation button'],['track.showAutomation','#bAut','Show all automation button'],
 ['track.add.audio','.addrow [data-add=audio]','Add audio track button'],['track.add.instrument','.addrow [data-add=inst]','Add instrument track button'],
 ['track.add.return','.addrow [data-add=return]','Add return track button'],
 ['track.master.volume','.mhdr [data-c="hp:master"]','master volume slider'],['track.master.effects','.mhdr [data-mact=fx]','master Effects button'],
 ['track.master.mixer','.mhdr [data-mact=mixer]','master Mixer button'],['track.master.view','.mhdr [data-mact=view]','master View button'],
 ['mixer.view','#mxVw','mixer View menu'],['mixer.spectrumOverlay','#mxDev','Spectrum overlay button'],['mixer.compact','#mxCmp','Compact channels button'],
 ['mixer.cables','#mxCab','Cables button'],['mixer.settings','#mxSetB','Mixer settings button'],['mixer.close','.fwh>.fwc','mixer Close button'],
 ['mixer.strip.name','.mx:not(.master)>.mxn','channel name'],['mixer.strip.instrument','.mxi .slot.inst','channel instrument slot'],
 ['mixer.strip.device','.mxi .slot:not(.inst)','channel device slot'],['mixer.strip.display','.mx:not(.master) canvas.mxv','channel picture'],
 ['mixer.strip.send','.mx:not(.master) .mxsnd [data-c]','channel send knob'],['mixer.strip.volume','.mx:not(.master) .fwrap>[data-c]','channel fader'],
 ['mixer.strip.pan','.mx:not(.master) .mxp [data-c]','channel pan knob'],['mixer.strip.mute','.mx:not(.master) .mxb [data-a=mute]','channel Mute button'],
 ['mixer.strip.solo','.mx:not(.master) .mxb [data-a=solo]','channel Solo button'],['mixer.strip.arm','.mx:not(.master) .mxb [data-a=arm]','channel Record arm button'],
 ['mixer.master.name','.mx.master>.mxn','master channel name'],['mixer.master.pin','.mx.master .mxpin','master Pin button'],
 ['mixer.master.display','.mx.master canvas.mxv','master picture'],['mixer.master.volume','.mx.master .fwrap>[data-c]','master fader'],
 ['mixer.master.mono','[data-mon=mono]','Mono button'],['mixer.master.dim','[data-mon=dim]','Dim button'],['mixer.master.swap','[data-mon=swap]','Swap left and right button'],
 ['mixer.ab.a','.abt [data-ab=a]','mix A button'],['mixer.ab.b','.abt [data-ab=b]','mix B button'],['mixer.ab.copy','[data-ab=copy]','Copy mix button'],
 ['mixer.cables.sends','.cablg [data-cl=send]','cable legend Sends switch'],['mixer.cables.outputs','.cablg [data-cl=out]','cable legend Outputs switch'],
 ['mixer.cables.sidechains','.cablg [data-cl=sc]','cable legend Sidechains switch'],['mixer.cables.selectedOnly','.cablg [data-cl=sel]','cable legend Selected only switch'],
 ['mixer.cables.style','.cablg [data-cl=sty]','cable legend Style switch'],['mixer.cables.clashes','.cablg [data-ni=clash]','cable legend Clashes switch']];
const CONTROL_ALIAS={};
const XTCI=new Map(CONTROLS.map(c=>[c[0],c]));
function xtTag(area){const r=document.querySelector(CONTROL_AREAS[area]);if(!r)return 0;let n=0;
  for(const c of CONTROLS){if(!c[0].startsWith(area+'.'))continue;for(const e of r.querySelectorAll(c[1]))if(e.dataset.al!==c[0]){e.dataset.al=c[0];n++}}return n}
const XTQ=new Set();
function xtTagSoon(area){if(!XTQ.size)queueMicrotask(()=>{for(const a of XTQ)try{xtTag(a)}catch(e){console.error('AudioLab control ids',e)}XTQ.clear()});XTQ.add(area)}
/* the control (its CONTROLS row) an element belongs to, or null; follows CONTROL_ALIAS for ids from an older file */
function xtControlOf(el){const e=el&&el.closest&&el.closest('[data-al]');if(!e)return null;let id=e.dataset.al;for(let i=0;i<8&&CONTROL_ALIAS[id];i++)id=CONTROL_ALIAS[id];return XTCI.get(id)||null}
{const _rhX=renderHeaders;renderHeaders=function(){const r=_rhX.apply(this,arguments);xtTagSoon('track');return r}}
{const _rmX=renderMixer;renderMixer=function(){const r=_rmX.apply(this,arguments);xtTagSoon('mixer');return r}}
/* parts of the mixer built outside renderMixer: the cable legend (cabLegend, called by the cable drawing) and the pan
   controls in the chosen style (s1PanBuild); one query per call, a tag pass only when something new has no id */
{const _clX=cabLegend;cabLegend=function(w){const r=_clX.apply(this,arguments);const lg=w&&w.querySelector('.cablg');if(lg&&lg.querySelector('button:not([data-al])'))xtTagSoon('mixer');return r}}
{const _pbX=s1PanBuild;s1PanBuild=function(){const r=_pbX.apply(this,arguments);xtTagSoon('mixer');return r}}
{const _taX=trApply;trApply=function(){const r=_taX.apply(this,arguments);xtTagSoon('transport');return r}}
setTimeout(()=>{for(const a in CONTROL_AREAS)xtTagSoon(a)},0);
