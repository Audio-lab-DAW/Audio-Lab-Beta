"""Task LM-4a (lane M, Learn): the lesson runner and the four psytrance lessons as LM_LESSONS data.
Run on a fresh index.html (after git pull --rebase):  python3 tools/design-lab/lm/lm4a.py [index.html]
Unique, asserted anchors: new JS before `function askChoice(title,text,btns,icon){`, new CSS before `.dacv{display:flex;`.
Re-running on a file that already has the block replaces it (between the markers), so a rebase never doubles it."""
import sys, re
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()

JS_A = 'function askChoice(title,text,btns,icon){'
CSS_A = '.dacv{display:flex;'
JM0, JM1 = '/* ==LM4a-js== */', '/* ==/LM4a-js== */'
CM0, CM1 = '/* ==LM4a-css== */', '/* ==/LM4a-css== */'

CSS = CM0 + r'''
/* task LM-4a (lane M, Learn): the stand-in pointer used until lane F's guide engine (ovGuide, task LM1) exists: one card, one ring,
   one leader. Only the card takes the pointer; the ring and the leader let every click through. Drawn with the overlay tokens. */
#lmg{position:fixed;left:0;top:0;width:0;height:0;z-index:9700;pointer-events:none}
#lmg .lmgR{position:fixed;border:1px solid var(--ov-amb,#ffb547);border-radius:6px;pointer-events:none;box-shadow:0 0 0 3px rgba(255,181,71,.13)}
#lmg svg{position:fixed;left:0;top:0;overflow:visible;pointer-events:none}
#lmg svg line{stroke:var(--ov-amb,#ffb547);stroke-width:1}#lmg svg circle{fill:var(--ov-amb,#ffb547)}
.lmgC{position:fixed;pointer-events:auto;width:318px;max-width:calc(100vw - 24px);box-sizing:border-box;padding:10px 12px 9px;border-radius:var(--ov-r-tip,8px);
  background:#15161c;border:1px solid rgba(255,181,71,.34);color:#d9dce6;font:var(--fw4,400) var(--fs2,12px)/1.45 var(--ffu,Inter,system-ui,sans-serif);box-shadow:0 14px 40px rgba(0,0,0,.55)}
.lmgK{display:flex;gap:8px;font:var(--ov-lab);letter-spacing:var(--ov-labsp,.12em);text-transform:uppercase;color:var(--ov-amb,#ffb547)}.lmgK span{margin-left:auto;color:var(--ov-mut,#8b8b97)}
.lmgC h4{margin:5px 0 3px;font-size:13px;font-weight:var(--fw6,600);color:#f1f3f8}.lmgC p{margin:0 0 6px;color:#b8bcc8}
.lmgL{font-variant-numeric:tabular-nums;color:#e8ebf2;padding:4px 7px;border-radius:5px;background:rgba(255,255,255,.045);margin-bottom:7px}.lmgL.ok{color:#7ee0a8}.lmgL.no{color:#ffcf8a}
.lmgB{display:flex;gap:6px;align-items:center;flex-wrap:wrap}.lmgB i{flex:1}
.lmgC button{height:22px;min-height:22px;padding:0 8px;border-radius:var(--ov-r-item,6px);border:1px solid var(--ov-ln,rgba(255,255,255,.09));background:rgba(255,255,255,.06);color:#dfe2ea;font:inherit;font-size:var(--fs1,11px);cursor:pointer}
.lmgC button:hover{background:rgba(255,255,255,.12)}.lmgC button.pri{border-color:rgba(255,181,71,.5);color:#ffd9a0}
.lmgD{display:flex;gap:4px;margin-top:8px}.lmgD i{width:14px;height:3px;border-radius:2px;background:rgba(255,255,255,.14)}.lmgD i.c{background:rgba(255,181,71,.5)}.lmgD i.d{background:var(--ov-amb,#ffb547)}
#lmgO{position:fixed;left:16px;bottom:96px;z-index:9700;width:300px}
#lmgO .lmgRow{display:flex;align-items:center;gap:8px;width:100%;height:auto;min-height:30px;padding:4px 8px;margin:0 0 4px;text-align:left}
#lmgO .lmgRow small{display:block;color:var(--ov-mut,#8b8b97)}#lmgO .lmgRow b{font-weight:var(--fw5,500)}#lmgO .lmgRow em{margin-left:auto;font-style:normal;color:#7ee0a8}
body.lite .lmgC{box-shadow:none;background:#16171d}
''' + CM1 + '\n'

JS = JM0 + r'''
/* ===================== task LM-4a (lane M, Learn: lessons) =====================
   The user's picks N5 H1 P1 W1 L1 G1 (docs/research-learn-mode.md 4.5 to 4.7). A lesson is data (LM_LESSONS): each step names a
   control id (data-al, lane H's CONTROLS) and, when the control repeats per track, the track it means (kick or bass); a check by name
   (LM_CHECK), a live line (LM_LIVE), a "Do it for me" fix (LM_FIX, one undo step each) or a command id (runCommand). Steps wait for a
   state of the song, never for a click: a key, a MIDI controller or the Assistant count the same. A step that is already true passes
   with "Already done"; a mustAct step always waits for a fresh move. Back, Skip step and End (Esc) on every step.
   Pointing: LM_HOOKS.point(id, card) goes to lane F's guide engine ovGuide(id, card) when it exists (task LM1), else to the stand-in
   lmLsPoint: one card, one amber ring and one leader; only the card takes the pointer, so nothing is ever blocked or covered.
   Cost: no lesson, no work (no timer, no listener, nothing in the DOM). While a lesson runs, one 150 ms timer runs the step's check
   (a few reads of the song) and re-places the card only when the text or the target's place changed.
   Progress (G1, quiet): UI.lm = {p: {lessonId: steps passed or 'done'}, o: 1 once the first-run offer was shown}.
   Getters (LM_G) read the song (S); the master peak reads the master meter's numbers without changing anything. Task LM5 moves the
   sidechain, automation-write and peak getters onto MX_HOOKS, FT_HOOKS and INS once their lanes publish them. */
const LM_HOOKS=window.LM_HOOKS||(window.LM_HOOKS={});
const LM_PK={decay:['d','decay','dec'],cutoff:['cut','cutoff','fc']};
const LM_G={
  trk(k){if(!S||!S.tracks)return null;const L=S.tracks.filter(t=>t.kind==='inst'),re=k==='kick'?/kick/i:/bass/i;
    return L.find(t=>String(t.name).trim().toLowerCase()===k)||L.find(t=>re.test(t.name)&&!(k==='bass'&&/kick/i.test(t.name)))||L.find(t=>t.inst&&re.test(t.inst.preset||''))||null},
  six:()=>60000/S.bpm/4,
  sec(re){return(S.sections||[]).find(x=>re.test(x.name||''))||null},
  build:()=>LM_G.sec(/build|rise/i),
  drop:()=>LM_G.sec(/drop/i)||LM_G.sec(/peak|climax|full/i),
  loops(sc){const R=S.loopRange;return!!(sc&&S.loop&&R&&Math.abs(R.a-sc.start)<.51&&Math.abs(R.b-sc.start-sc.len)<.51)},
  at:()=>play.on?curDisp():pos,
  clip(t){if(!t)return null;const M=t.clips.filter(c=>c.notes&&c.notes.length),b=LM_G.at(),R=S.loop&&S.loopRange;
    return M.find(c=>b>=c.start&&b<c.start+c.len)||(R&&M.find(c=>R.a>=c.start&&R.a<c.start+c.len))||M.slice().sort((a,z)=>z.notes.length-a.notes.length)[0]||null},
  /* the first bar of a clip in 16ths: notes on the three 16ths after each beat (off) and on the beats (on) */
  roll(c){const r={off:0,on:0};if(!c||!c.notes)return r;const b0=Math.floor(c.off||0),seen=new Set();
    for(const n of c.notes){const x=(n.s-b0)*4,k=Math.round(x);if(k<0||k>15||Math.abs(x-k)>.12||seen.has(k))continue;seen.add(k);if(k%4)r.off++;else r.on++}return r},
  par(t,n){const I=t&&t.inst;if(!I)return null;for(const k of LM_PK[n])if(typeof I[k]==='number')return{k,v:I[k],I};return null},
  decMs(t){const p=LM_G.par(t,'decay');return p?(p.v<20?p.v*1000:p.v):null},
  pump(t){const f=t&&(t.fx||[]).find(m=>m.type==='side'||m.type==='duck');if(!f)return null;const P=f.p||{};
    if(f.type==='side'){const per=(SYNCS[P.sync]||1)*60000/S.bpm;return{f,on:f.on!==false,depth:+P.depth||0,rel:(+P.shape||0)/100*per,per}}
    return{f,on:f.on!==false,depth:+P.amt||0,rel:+P.rl||0}},
  db:t=>t?20*Math.log10(Math.max(1e-6,t.vol)):-90,
  soloOnly:t=>!!(t&&t.solo&&S.tracks.every(x=>x===t||!x.solo)),
  noSolo:()=>S.tracks.every(x=>!x.solo),
  autoW:t=>!!(UI.autoRec||(t&&t.autoArm)),
  /* the best written line of a track inside a section: how much of the section it covers and how far it moves (0 to 1) */
  lane(t,sc){if(!t||!sc||!S.pauto)return null;let best=null;const lab=S.pautoL||{};
    const ids=Object.keys(S.pauto).filter(id=>id.includes(t.id)&&!/:(pan|vol)$/.test(id)),pref=ids.filter(id=>/cut|filt|freq/i.test(id+' '+(lab[id]||'')));
    for(const id of(pref.length?pref:ids)){const P=S.pauto[id].filter(q=>q.b>=sc.start-1e-6&&q.b<=sc.start+sc.len+1e-6);if(P.length<2)continue;
      let lo=1,hi=0,b0=1e9,b1=-1e9;for(const q of P){lo=Math.min(lo,q.v);hi=Math.max(hi,q.v);b0=Math.min(b0,q.b);b1=Math.max(b1,q.b)}
      const L={id,cover:(b1-b0)/sc.len,span:hi-lo,n:P.length};if(!best||L.cover+L.span>best.cover+best.span)best=L}
    return best},
  any:t=>!!(t&&S.pauto&&Object.keys(S.pauto).some(id=>id.includes(t.id)&&!/:(pan|vol)$/.test(id)&&S.pauto[id].length>1)),
  peakNow(){try{if(typeof INS==='object'&&INS&&typeof INS.masterPeak==='function')return+INS.masterPeak()}catch(e){}return typeof MT2==='object'?Math.max(MT2.l,MT2.r):-90},
  peak(){let m=-90;for(const x of LM_RUN.pk)m=Math.max(m,x[1]);return m}};
const lmU=u=>`<span class="lku">${u}</span>`,lmF=(v,d)=>v<=-89?'-∞':v.toFixed(d==null?1:d);
const LM_CHECK={
  tempo:()=>S.bpm>=143&&S.bpm<=147,
  playing:()=>!!play.on,
  roll:s0=>{const r=LM_G.roll(lmLsClip(s0));return r.off===12&&r.on===0},
  decay:()=>{const d=LM_G.decMs(LM_G.trk('bass'));return d!=null&&d<LM_G.six()},
  cutoff:s0=>{const p=LM_G.par(LM_G.trk('bass'),'cutoff');return!!(p&&s0.cut>0&&Math.abs(Math.log2(p.v/s0.cut))>.4&&p.v>=300&&p.v<=2000)},
  pumpOn:()=>{const p=LM_G.pump(LM_G.trk('bass'));return!!(p&&p.on)},
  depth:()=>{const p=LM_G.pump(LM_G.trk('bass'));return!!(p&&p.on&&p.depth>=50&&p.depth<=85)},
  release:()=>{const p=LM_G.pump(LM_G.trk('bass'));if(!p||!p.on)return false;const r=p.rel/LM_G.six();return r>=.6&&r<=1.5},
  compare:s0=>LM_RUN.tog-s0.tog>=2&&LM_CHECK.pumpOn(),
  loopBuild:()=>LM_G.loops(LM_G.build()),
  dark:()=>{const p=LM_G.par(LM_G.trk('bass'),'cutoff');return!!(p&&p.v<200)},
  writeOn:()=>LM_G.autoW(LM_G.trk('bass')),
  sweep:()=>{const L=LM_G.lane(LM_G.trk('bass'),LM_G.build());return!!(L&&L.cover>=.4&&L.span>=.35)},
  writeOff:()=>!LM_G.autoW(LM_G.trk('bass'))&&LM_G.any(LM_G.trk('bass')),
  loopDrop:()=>LM_G.loops(LM_G.drop())&&!!play.on,
  soloKick:()=>LM_G.soloOnly(LM_G.trk('kick')),
  kickLevel:()=>{const p=LM_G.peak();return LM_G.soloOnly(LM_G.trk('kick'))&&!!play.on&&p>=-8&&p<=-4},
  unsolo:()=>LM_G.noSolo(),
  bassFit:()=>{const p=LM_G.peak(),k=LM_G.trk('kick'),b=LM_G.trk('bass');return!!(play.on&&k&&b&&p<-1&&p>-16&&LM_G.db(b)<=LM_G.db(k)-2)},
  pumpCheck:()=>{const p=LM_G.pump(LM_G.trk('bass'));return!!(p&&p.on&&p.depth>=30)}};
const LM_LIVE={
  tempo:()=>`Now ${S.bpm} ${lmU('bpm')} · target 143 to 147`,
  roll:s0=>{const c=lmLsClip(s0);if(!c)return'No MIDI clip on the Bass track yet: draw one first, or use Do it for me.';const r=LM_G.roll(c);return`${r.off} of 12 placed in the first bar of “${esc(c.name||'Bass')}”${r.on?` · ${r.on} on a kick step: clear ${r.on>1?'those':'it'}`:''}`},
  decay:()=>{const d=LM_G.decMs(LM_G.trk('bass')),x=LM_G.six();if(d==null)return'This instrument has no Decay the lesson knows. Skip step.';return`Decay ${Math.round(d)} ${lmU('ms')} · 1/16 at ${S.bpm} ${lmU('bpm')} = ${Math.round(x)} ${lmU('ms')} · ${d<x?'fits ✓':'still overlaps'}`},
  cutoff:s0=>{const p=LM_G.par(LM_G.trk('bass'),'cutoff');if(!p)return'This instrument has no Cutoff the lesson knows. Skip step.';return`Cutoff ${Math.round(p.v)} ${lmU('Hz')} · moved ${s0.cut>0?Math.abs(Math.log2(p.v/s0.cut)).toFixed(1):'0.0'} ${lmU('oct')} · aim for 300 to 2000 ${lmU('Hz')}`},
  pumpOn:()=>LM_G.pump(LM_G.trk('bass'))?'':'No pump on the Bass yet: Do it for me adds a Sidechain device.',
  depth:()=>{const p=LM_G.pump(LM_G.trk('bass'));return p?`Depth ${Math.round(p.depth)} ${lmU('%')} · target 50 to 80`:'Turn the pump on first.'},
  release:()=>{const p=LM_G.pump(LM_G.trk('bass'));if(!p)return'Turn the pump on first.';const r=p.rel/LM_G.six();return`Release ${Math.round(p.rel)} ${lmU('ms')} · 1/16 = ${Math.round(LM_G.six())} ${lmU('ms')} · ratio ${r.toFixed(2)}${r>=.6&&r<=1.5?' ✓':''}`},
  compare:s0=>`${Math.min(2,LM_RUN.tog-s0.tog)} of 2 switches`,
  loopBuild:()=>{const b=LM_G.build();return b?`The Build: bar ${b.start/4+1} to ${(b.start+b.len)/4}`:'This song has no section named Build. Add one, or Skip step.'},
  dark:()=>{const p=LM_G.par(LM_G.trk('bass'),'cutoff');return p?`Cutoff ${Math.round(p.v)} ${lmU('Hz')} · under 200`:'This instrument has no Cutoff the lesson knows. Skip step.'},
  sweep:()=>{const L=LM_G.lane(LM_G.trk('bass'),LM_G.build());return L?`Written over ${Math.round(L.cover*100)} ${lmU('%')} of the Build · moves ${Math.round(L.span*100)} ${lmU('%')} of the knob`:'Nothing written yet'},
  loopDrop:()=>{const d=LM_G.drop();return d?`The ${esc(d.name)}: bar ${d.start/4+1} to ${(d.start+d.len)/4}${play.on?'':' · then press Play'}`:'This song has no section named Drop. Add one, or Skip step.'},
  kickLevel:()=>`Master peak ${lmF(LM_G.peak())} ${lmU('dBFS')} · target -8 to -4`,
  bassFit:()=>{const k=LM_G.trk('kick'),b=LM_G.trk('bass');return`Master peak ${lmF(LM_G.peak())} ${lmU('dBFS')} · bass ${k&&b?(LM_G.db(b)-LM_G.db(k)).toFixed(1):'?'} ${lmU('dB')} against the kick`},
  pumpCheck:()=>{const p=LM_G.pump(LM_G.trk('bass'));return p?`Pump ${p.on?'on':'off'} · Depth ${Math.round(p.depth)} ${lmU('%')}`:'No pump on the Bass.'}};
/* "Do it for me": each is one undo step (a loop range or automation write is not part of undo, as by hand) */
function lmLsRoll(c){const b0=c.off||0,N=c.notes,cnt={};for(const n of N)cnt[n.p]=(cnt[n.p]||0)+1;const pk=+Object.keys(cnt).sort((a,z)=>cnt[z]-cnt[a])[0]||33;
  const L=N.filter(n=>{const x=(n.s-b0)*4,k=Math.round(x);return!(Math.abs(x-k)<.12&&k%4===0)});
  for(let q=Math.ceil(b0*4-1e-6)/4;q<b0+c.len-1e-6;q+=.25){if(Math.abs(q-Math.round(q))<1e-6)continue;if(!L.some(n=>Math.abs(n.s-q)<.03))L.push({p:pk,s:q,l:.145,v:Math.abs(q%1-.25)<1e-6?.8:1})}
  L.sort((a,z)=>a.s-z.s);c.notes=L}
function lmLsFxSet(f){pushUndo();f();changed(true);try{renderMixer()}catch(e){}}
const LM_FIX={
  tempo:()=>setBpm(145),
  roll:s0=>{const c=lmLsClip(s0);if(!c)return;if(c.steps){toast('This is a step sequencer clip: set its steps in the step editor (double-click the clip).');return}pushUndo();lmLsRoll(c);if(c.link)for(const t of S.tracks)for(const k of t.clips)if(k!==c&&k.link===c.link&&k.notes)k.notes=JSON.parse(JSON.stringify(c.notes));changed(false)},
  decay:()=>{const p=LM_G.par(LM_G.trk('bass'),'decay');if(!p)return;const ms=LM_G.six()*.7;pushUndo();p.I[p.k]=p.v<20?+(ms/1000).toFixed(3):Math.round(ms);changed(false);renderFx()},
  pumpOn:()=>{const t=LM_G.trk('bass');if(!t)return;const p=LM_G.pump(t);lmLsFxSet(()=>{if(p)p.f.on=true;else t.fx.push(mkFx('side'))})},
  depth:()=>{const p=LM_G.pump(LM_G.trk('bass'));if(!p)return;lmLsFxSet(()=>{p.f.on=true;p.f.p[p.f.type==='side'?'depth':'amt']=70})},
  release:()=>{const p=LM_G.pump(LM_G.trk('bass'));if(!p)return;lmLsFxSet(()=>{p.f.on=true;if(p.f.type==='side')p.f.p.shape=Math.round(clamp(100*LM_G.six()/p.per,5,100));else p.f.p.rl=Math.round(LM_G.six())})},
  loopBuild:()=>lmLsLoop(LM_G.build(),false),
  dark:()=>{const p=LM_G.par(LM_G.trk('bass'),'cutoff');if(!p)return;pushUndo();p.I[p.k]=150;changed(false);renderFx()},
  writeOn:()=>{const t=LM_G.trk('bass'),b=t&&document.querySelector(`#hdrin .hdr[data-id="${t.id}"] [data-a=aar]`);if(t&&!LM_G.autoW(t)){if(b)b.click();else{t.autoArm=true;renderHeaders()}}},
  writeOff:()=>{const t=LM_G.trk('bass'),b=t&&document.querySelector(`#hdrin .hdr[data-id="${t.id}"] [data-a=aar]`);if(t&&t.autoArm){if(b)b.click();else{t.autoArm=false;renderHeaders()}}if(UI.autoRec){const r=document.getElementById('bAR');if(r)r.click()}},
  loopDrop:()=>lmLsLoop(LM_G.drop(),true),
  soloKick:()=>{const k=LM_G.trk('kick');if(!k)return;pushUndo();for(const t of S.tracks)t.solo=t===k;changed(true);try{renderMixer()}catch(e){}},
  unsolo:()=>{pushUndo();for(const t of S.tracks)t.solo=false;changed(true);try{renderMixer()}catch(e){}},
  pumpCheck:()=>{const t=LM_G.trk('bass');if(!t)return;const p=LM_G.pump(t);lmLsFxSet(()=>{if(!p)t.fx.push(mkFx('side'));else{p.f.on=true;const k=p.f.type==='side'?'depth':'amt';if(p.f.p[k]<30)p.f.p[k]=50}})}};
function lmLsLoop(sc,go){if(!sc)return;if(!LM_G.loops(sc)){S.loopRange={id:sc.id,a:sc.start,b:sc.start+sc.len};S.loop=true;pos=sc.start;syncTransportUI();dirty=true;if(play.on){stop();start()}}if(go&&!play.on)start()}
function lmLsClip(s0){const f=s0&&s0.clip&&findClip(s0.clip);return f?f.c:null}
/* the lessons: text is plain language; al = control id (data-al), track = which track's copy of a repeated control,
   want = the device control id the step will point at once lane H gives device knobs ids (DL7); until then it points at al */
const LM_LESSONS=[
 {id:'lm.rollingBass',title:'A rolling bass',minutes:3,skill:'Bass',steps:[
  {al:'transport.tempo',t:'Set a psytrance tempo',b:'Drag the tempo, scroll on it, or click it and use the arrow keys. Psytrance usually sits between 138 and 148 BPM; this lesson uses 143 to 147.',check:'tempo',live:'tempo',fix:'tempo'},
  {al:'transport.play',command:'transport.play',t:'Press Play and keep it playing',b:'Space works too. From here on every step reacts while you listen.',check:'playing'},
  {al:'track.name',track:'bass',t:'Fill the three 16ths after each kick',b:'Double-click the Bass clip to open it in the piano roll. The kick plays on every beat; a rolling bass plays the three 16ths in between, and none on the beat.',check:'roll',live:'roll',fix:'roll'},
  {al:'track.edit',track:'bass',want:'device.instrument.decay',t:'Make each note shorter than a 16th',b:'Open the Bass synth and turn Decay down while it plays. A note longer than a 16th blurs into the next one and smears the roll.',check:'decay',live:'decay',fix:'decay'},
  {al:'track.edit',track:'bass',want:'device.instrument.cutoff',t:'Shape the tone with Cutoff',b:'Move Cutoff on the Bass synth while it plays. Lower is rounder, higher brings out the bite. Between 300 Hz and 2 kHz suits a rolling bass.',check:'cutoff',live:'cutoff',mustAct:true}]},
 {id:'lm.sidechain',title:'Sidechain kick and bass',minutes:2,skill:'Groove',steps:[
  {al:'transport.play',command:'transport.play',t:'Press Play',b:'Listen to the kick and the bass sharing the low end.',check:'playing'},
  {al:'track.edit',track:'bass',want:'device.sidechain.power',t:'Turn the pump on',b:'On the Bass track, switch on its Sidechain device (or add one). The pump lowers the bass each time the kick hits.',check:'pumpOn',live:'pumpOn',fix:'pumpOn'},
  {al:'track.edit',track:'bass',want:'device.sidechain.depth',t:'Duck the bass under the kick',b:'Set Depth between 50 and 80 %. The dip in its picture is the room the kick gets.',check:'depth',live:'depth',fix:'depth'},
  {al:'track.edit',track:'bass',want:'device.sidechain.release',t:'Let it come back in time',b:'The release (Shape on the Sidechain device) sets how fast the bass returns. Near one 16th, the bass breathes with the groove.',check:'release',live:'release',fix:'release'},
  {al:'track.edit',track:'bass',want:'device.sidechain.power',t:'Compare: off, then on',b:'Switch the pump off and on again. Hearing it without the pump is the quickest way to judge it.',check:'compare',live:'compare',mustAct:true}]},
 {id:'lm.filterBuild',title:'A build with a filter sweep',minutes:3,skill:'Arrangement',steps:[
  {al:'transport.loop',t:'Loop the Build',b:'Click the Build section above the tracks (or right-click it and loop it). The loop plays it again and again while you work.',check:'loopBuild',live:'loopBuild',fix:'loopBuild'},
  {al:'track.edit',track:'bass',want:'device.instrument.cutoff',t:'Start dark',b:'Turn the Bass Cutoff all the way down, under 200 Hz. The sweep starts from here.',check:'dark',live:'dark',fix:'dark'},
  {al:'track.writeAutomation',alt:['track.recordAutomation','track.name'],track:'bass',t:'Turn on automation write',b:'Click the round write button on the Bass track (taller tracks show it; Record automation at the end of the track list works too). While it glows red, every knob you move during playback is recorded as a line.',check:'writeOn',fix:'writeOn'},
  {al:'transport.play',command:'transport.play',t:'Press Play',b:'Recording starts when you move the knob, not when you press Play.',check:'playing'},
  {al:'track.edit',track:'bass',want:'device.instrument.cutoff',t:'Sweep Cutoff up across the Build',b:'Turn Cutoff slowly from low to high while the Build plays. AudioLab writes the movement as a line on the Bass track.',check:'sweep',live:'sweep'},
  {al:'track.writeAutomation',alt:['track.recordAutomation','track.name'],track:'bass',t:'Turn write off and listen',b:'Click the write button again. Now the line plays the knob for you: watch Cutoff move on its own.',check:'writeOff',fix:'writeOff'}]},
 {id:'lm.mixDrop',title:'Mixing a drop',minutes:4,skill:'Mixing',steps:[
  {al:'transport.loop',t:'Loop the Drop and play it',b:'Click the Drop section above the tracks, then press Play.',check:'loopDrop',live:'loopDrop',fix:'loopDrop'},
  {al:'track.solo',track:'kick',t:'Solo the kick',b:'Mix from the kick up: on its own it sets the level everything else fits under.',check:'soloKick',fix:'soloKick'},
  {al:'track.volume',track:'kick',watch:['transport.peak','transport.masterMeter'],t:'Kick peaks near -6 dBFS',b:'Drag the Kick level until the master peak sits between -8 and -4 dBFS. That leaves room for the bass and the master.',check:'kickLevel',live:'kickLevel'},
  {al:'track.solo',track:'kick',t:'Unsolo the kick',b:'Bring the whole drop back.',check:'unsolo',fix:'unsolo'},
  {al:'track.volume',track:'bass',watch:['transport.peak','transport.masterMeter'],t:'Fit the bass under the kick',b:'Set the Bass level so the master peak stays under -1 dBFS and the bass sits at least 2 dB under the kick. These are starting points that leave room, not rules.',check:'bassFit',live:'bassFit'},
  {al:'track.edit',track:'bass',want:'device.sidechain.depth',t:'Check the pump',b:'With the pump on and at least 30 % Depth, the kick cuts through without turning it up.',check:'pumpCheck',live:'pumpCheck',fix:'pumpCheck'}]}];
const LM_RUN={les:null,i:0,s0:null,ok:false,already:false,tm:0,adv:0,pk:[],tog:0,pon:null,h:null,hk:'',html:''};
function lmLsUI(){let u=UI.lm;if(!u||typeof u!=='object')u=UI.lm={p:{},o:0};if(!u.p||typeof u.p!=='object')u.p={};return u}
function lmLsProg(id){const L=LM_LESSONS.find(l=>l.id===id),v=lmLsUI().p[id];return!L?0:v==='done'?L.steps.length:Math.min(L.steps.length,+v||0)}
function lmLsDone(){return LM_LESSONS.filter(l=>lmLsUI().p[l.id]==='done').length}
function lmLsStart(id,at){const les=LM_LESSONS.find(l=>l.id===id||l.id==='lm.'+id);if(!les||!S)return false;if(LM_RUN.les)lmLsEnd();lmLsOfferClose();
  Object.assign(LM_RUN,{les,i:Math.max(0,Math.min(les.steps.length-1,at|0)),pk:[],tog:0,pon:null});const u=lmLsUI();if(!u.o){u.o=1;saveUI()}
  LM_RUN.tm=setInterval(lmLsTick,150);addEventListener('keydown',lmLsKey);addEventListener('resize',lmLsResize);lmLsStep();return true}
function lmLsEnd(fin){const l=LM_RUN.les;if(!l)return;clearInterval(LM_RUN.tm);clearTimeout(LM_RUN.adv);LM_RUN.tm=0;LM_RUN.les=null;LM_RUN.pk=[];
  removeEventListener('keydown',lmLsKey);removeEventListener('resize',lmLsResize);if(LM_RUN.h&&LM_RUN.h.close)LM_RUN.h.close();LM_RUN.h=null;LM_RUN.hk='';LM_RUN.html='';
  if(fin)toast(`${l.title}: done ✓ (${lmLsDone()} of ${LM_LESSONS.length} lessons done)`)}
function lmLsSnap(){const t=LM_G.trk('bass'),p=LM_G.par(t,'cutoff'),c=LM_G.clip(t);return{cut:p?p.v:0,tog:LM_RUN.tog,clip:c?c.id:null}}
function lmLsCheck(st){try{return!!LM_CHECK[st.check](LM_RUN.s0)}catch(e){return false}}
function lmLsStep(){const l=LM_RUN.les,st=l.steps[LM_RUN.i];LM_RUN.s0=lmLsSnap();LM_RUN.ok=LM_RUN.already=false;clearTimeout(LM_RUN.adv);
  if(!st.mustAct&&lmLsCheck(st)){LM_RUN.ok=LM_RUN.already=true;LM_RUN.adv=setTimeout(()=>{if(LM_RUN.les===l&&LM_RUN.ok)lmLsNext()},1300)}lmLsShow()}
function lmLsTick(){const l=LM_RUN.les;if(!l)return;const now=performance.now(),st=l.steps[LM_RUN.i];
  LM_RUN.pk.push([now,LM_G.peakNow()]);while(LM_RUN.pk.length&&now-LM_RUN.pk[0][0]>1500)LM_RUN.pk.shift();
  {const p=LM_G.pump(LM_G.trk('bass')),on=!!(p&&p.on);if(LM_RUN.pon!==null&&on!==LM_RUN.pon)LM_RUN.tog++;LM_RUN.pon=on}
  if(!LM_RUN.already){const ok=lmLsCheck(st);if(ok&&!LM_RUN.ok){LM_RUN.ok=true;clearTimeout(LM_RUN.adv);const rm=matchMedia('(prefers-reduced-motion: reduce)').matches;LM_RUN.adv=setTimeout(()=>{if(LM_RUN.les===l&&LM_RUN.ok)lmLsNext()},rm?1400:1000)}
    else if(!ok&&LM_RUN.ok){LM_RUN.ok=false;clearTimeout(LM_RUN.adv)}}
  lmLsShow()}
function lmLsNext(){const l=LM_RUN.les;if(!l)return;const u=lmLsUI();if(u.p[l.id]!=='done')u.p[l.id]=Math.max(+u.p[l.id]||0,LM_RUN.i+1);
  if(LM_RUN.i+1>=l.steps.length){u.p[l.id]='done';saveUI();lmLsEnd(true);return}saveUI();LM_RUN.i++;lmLsStep()}
function lmLsAct(a){const l=LM_RUN.les;if(!l)return;const st=l.steps[LM_RUN.i];
  if(a==='end')lmLsEnd();else if(a==='skip')lmLsNext();else if(a==='back'){LM_RUN.i=Math.max(0,LM_RUN.i-1);lmLsStep()}
  else if(a==='doit'){if(st.fix&&LM_FIX[st.fix])LM_FIX[st.fix](LM_RUN.s0);else if(st.command&&!lmLsCheck(st))runCommand(st.command,'lesson');lmLsTick()}
  else if(a==='reveal'&&st.reveal){runCommand(st.reveal,'lesson');lmLsShow()}}
function lmLsKey(e){if(e.key!=='Escape'||e.defaultPrevented||!LM_RUN.les)return;if(document.querySelector('#ctxm:not([hidden])'))return;
  const t=e.target;if(t&&t.closest&&t.closest('input,textarea,select,[contenteditable=true]'))return;lmLsEnd()}
function lmLsResize(){if(LM_RUN.h&&LM_RUN.h.place)LM_RUN.h.place(lmLsFind(LM_RUN.les.steps[LM_RUN.i]),true)}
/* the control a step points at: the device control once it has an id, else the step's own id, inside the right track's header */
function lmLsFind(st){const vis=e=>{if(!e||!e.isConnected)return false;const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.bottom>0&&r.right>0&&r.top<innerHeight&&r.left<innerWidth};
  const q=(id,root)=>[...(root||document).querySelectorAll(`[data-al="${id}"]`)].find(vis)||null;
  const t=st.track&&LM_G.trk(st.track),h=t&&document.querySelector(`#hdrin .hdr[data-id="${t.id}"]`);if(st.track&&!h)return null;
  for(const id of[st.want,st.al,...(st.alt||[])]){if(!id)continue;const e=(h&&q(id,h))||[...document.querySelectorAll(`[data-al="${id}"]`)].find(x=>vis(x)&&(!x.closest('.hdr')||x.closest('.hdr')===h&&!!h));if(e)return e}return null}
function lmLsHTML(st,missing){const l=LM_RUN.les,n=l.steps.length,i=LM_RUN.i,ok=LM_RUN.ok,s0=LM_RUN.s0;
  let live='';if(LM_RUN.already)live='<div class="lmgL ok">Already done ✓ · moving on</div>';
  else{let x='';try{x=st.live&&LM_LIVE[st.live]?LM_LIVE[st.live](s0):''}catch(e){x=''}
    if(st.track&&!LM_G.trk(st.track))x=`This lesson looks for a track named ${st.track==='kick'?'Kick':'Bass'}. Rename yours, or Skip step.`;
    if(x)live=`<div class="lmgL${ok?' ok':''}" aria-live="polite">${x}${ok&&!/✓/.test(x)?' ✓':''}</div>`;else if(ok)live='<div class="lmgL ok" aria-live="polite">Done ✓</div>'}
  const rev=missing?`<div class="lmgL no">Not on screen.${st.reveal?' <button data-lg="reveal">Show it</button>':''}</div>`:'';
  const doit=!ok&&((st.fix&&LM_FIX[st.fix])||st.command)?'<button data-lg="doit" class="pri">Do it for me</button>':'';
  return`<div class="lmgK">Lesson · ${esc(l.title)}<span>${i+1} / ${n}</span></div><h4 id="lmgH">${ok?'✓ ':''}${esc(st.t)}</h4><p>${esc(st.b)}</p>${rev}${live}`+
    `<div class="lmgB">${i?'<button data-lg="back" aria-label="Back">Back</button>':''}<button data-lg="skip">Skip step</button>${doit}<i></i><button data-lg="end">End · Esc</button></div>`+
    `<div class="lmgD">${l.steps.map((_,j)=>`<i class="${j<i||(j===i&&ok)?'d':j===i?'c':''}"></i>`).join('')}</div>`}
function lmLsShow(){const l=LM_RUN.les;if(!l)return;const st=l.steps[LM_RUN.i],el=lmLsFind(st),html=lmLsHTML(st,!el),k=l.id+'|'+LM_RUN.i;
  if(!LM_RUN.h||LM_RUN.hk!==k){if(LM_RUN.h&&LM_RUN.h.close)LM_RUN.h.close();LM_RUN.hk=k;LM_RUN.html=html;
    LM_RUN.h=LM_HOOKS.point(el?el.dataset.al:st.al,{html,el,avoid:st.watch||[],track:st.track||null,onAct:lmLsAct,label:l.title})||null;return}
  if(html!==LM_RUN.html){LM_RUN.html=html;if(LM_RUN.h.update)LM_RUN.h.update(html)}if(LM_RUN.h.place)LM_RUN.h.place(el)}
/* the hook other lanes use: lane F's guide engine (task LM1) when released, else the stand-in */
if(typeof LM_HOOKS.point!=='function')LM_HOOKS.point=(id,card)=>typeof ovGuide==='function'?ovGuide(id,card):lmLsPoint(id,card);
function lmLsPoint(id,card){let L=document.getElementById('lmg');if(L)L.remove();L=document.createElement('div');L.id='lmg';
  L.innerHTML='<div class="lmgR" hidden></div><svg hidden><line/><circle r="2"/><circle r="2"/></svg><div class="lmgC" role="dialog" aria-labelledby="lmgH"></div>';document.body.appendChild(L);
  const C=L.querySelector('.lmgC'),R=L.querySelector('.lmgR'),G=L.querySelector('svg');let key='',cur=card.el||null;C.innerHTML=card.html;
  C.addEventListener('click',e=>{const b=e.target.closest('[data-lg]');if(b&&card.onAct)card.onAct(b.dataset.lg)});
  const place=(el,force)=>{if(el!==undefined)cur=el;const z=ZOOM||1,W=innerWidth/z,H=innerHeight/z,cw=C.offsetWidth,ch=C.offsetHeight,rz=r=>({l:r.left/z,t:r.top/z,r:r.right/z,b:r.bottom/z});
    const T=cur&&cur.isConnected?rz(cur.getBoundingClientRect()):null,A=[];if(T)A.push(T);for(const w of card.avoid||[]){const e=document.querySelector(`[data-al="${w}"]`);if(e&&e.offsetParent)A.push(rz(e.getBoundingClientRect()))}
    const k=(T?[T.l,T.t,T.r,T.b].map(Math.round).join():'-')+'|'+cw+'|'+ch+'|'+W+'|'+H;if(k===key&&!force)return;key=k;
    let x=W-cw-16,y=56;
    if(T){const g=16,cx=(T.l+T.r)/2-cw/2,cy=(T.t+T.b)/2-ch/2,cl=(a,lo,hi)=>Math.max(lo,Math.min(hi,a)),hit=(a,b)=>!(a.r<=b.l||a.l>=b.r||a.b<=b.t||a.t>=b.b);
      const cs=[[cx,T.b+g],[cx,T.t-g-ch],[T.r+g,cy],[T.l-g-cw,cy]].map(([a,b])=>[cl(a,8,W-cw-8),cl(b,8,H-ch-8)]);
      const f=cs.find(([a,b])=>!A.some(r=>hit({l:a-4,t:b-4,r:a+cw+4,b:b+ch+4},r)))||cs[0];x=f[0];y=f[1]}
    C.style.left=x+'px';C.style.top=y+'px';R.hidden=G.hidden=!T;if(!T)return;
    R.style.left=(T.l-3)+'px';R.style.top=(T.t-3)+'px';R.style.width=(T.r-T.l+6)+'px';R.style.height=(T.b-T.t+6)+'px';
    const px=Math.max(x,Math.min(x+cw,(T.l+T.r)/2)),py=Math.max(y,Math.min(y+ch,(T.t+T.b)/2)),qx=Math.max(T.l-3,Math.min(T.r+3,px)),qy=Math.max(T.t-3,Math.min(T.b+3,py));
    G.setAttribute('width',W);G.setAttribute('height',H);const ln=G.querySelector('line'),[c1,c2]=G.querySelectorAll('circle');
    ln.setAttribute('x1',px);ln.setAttribute('y1',py);ln.setAttribute('x2',qx);ln.setAttribute('y2',qy);c1.setAttribute('cx',px);c1.setAttribute('cy',py);c2.setAttribute('cx',qx);c2.setAttribute('cy',qy)};
  place(cur,true);
  return{update(h){C.innerHTML=h;place(undefined,true)},place,close(){L.remove()},el:()=>C}}
/* the first-run offer (one quiet card, once; never under automation, so no test or the smoke test ever sees it unasked) */
function lmLsOfferClose(){const o=document.getElementById('lmgO');if(o)o.remove()}
function lmLsOffer(force){const u=lmLsUI();if(!force&&(u.o||navigator.webdriver||LM_RUN.les||!S||document.getElementById('lmgO')))return false;
  if(!force&&[...document.querySelectorAll('#cdlg,#set,#mixWin')].some(e=>!e.hidden&&e.offsetParent))return false;
  u.o=1;saveUI();const o=document.createElement('div');o.id='lmgO';o.className='lmgC';o.setAttribute('role','dialog');o.setAttribute('aria-label','Learn');
  o.innerHTML=`<div class="lmgK">Learn<span>${lmLsDone()} of ${LM_LESSONS.length} done</span></div><p style="margin:6px 0 8px">Short lessons on your own song. Nothing is locked: the guide points at the real control and moves on when your song gets there.</p>`+
    LM_LESSONS.map(l=>`<button class="lmgRow" data-lo="${l.id}"><span><b>${esc(l.title)}</b><small>${l.steps.length} steps · about ${l.minutes} min</small></span>${u.p[l.id]==='done'?'<em>✓</em>':''}</button>`).join('')+
    '<div class="lmgB"><i></i><button data-lo="x">Not now</button></div>';
  o.addEventListener('click',e=>{const b=e.target.closest('[data-lo]');if(!b)return;if(b.dataset.lo==='x')lmLsOfferClose();else lmLsStart(b.dataset.lo)});
  document.body.appendChild(o);return true}
setTimeout(()=>{try{lmLsOffer(false)}catch(e){console.error('AudioLab Learn',e)}},12000);
/* for lane F's Help menu (LM2) and the Assistant (LM6) */
Object.assign(LM_HOOKS,{lessons:()=>LM_LESSONS.map(l=>({id:l.id,title:l.title,minutes:l.minutes,skill:l.skill,steps:l.steps.length,passed:lmLsProg(l.id),done:lmLsUI().p[l.id]==='done'})),
  start:(id,at)=>lmLsStart(id,at),end:()=>lmLsEnd(),active:()=>LM_RUN.les?{id:LM_RUN.les.id,step:LM_RUN.i}:null,
  progress:()=>`${lmLsDone()} of ${LM_LESSONS.length} done`,offer:()=>lmLsOffer(true)});
''' + JM1 + '\n'

def put(s, a, m0, m1, block):
    if m0 in s:
        i, j = s.index(m0), s.index(m1) + len(m1) + 1
        return s[:i] + block + s[j:]
    assert s.count(a) == 1, ('anchor not unique', a, s.count(a))
    return s.replace(a, block + a)

s = put(s, JS_A, JM0, JM1, JS)
s = put(s, CSS_A, CM0, CM1, CSS)
# no top-level name of this block may exist twice in the file
for n in re.findall(r'\nfunction (lm[A-Z]\w*)\(', JS) + ['LM_HOOKS', 'LM_LESSONS', 'LM_RUN', 'LM_G', 'LM_CHECK', 'LM_LIVE', 'LM_FIX', 'LM_PK']:
    c = len(re.findall(r'(?:function |const |let |var )' + n + r'\b', s))
    assert c == 1, (n, c)
assert '—' not in JS.split('LM_LESSONS=[')[1].split('const LM_RUN')[0], 'no em dash in lesson text'
open(P, 'w', encoding='utf-8').write(s)
print('ok', P)
