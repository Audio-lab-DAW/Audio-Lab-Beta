"""Task LT-1 (lane J): the output check (L1) and the playing buffer (L2).
Edit script with unique, asserted anchors; safe to re-run on a fresh index.html (it does nothing when the step is already in).
Run from the repository root: python3 tools/engine-lab/lt/lt_1.py"""
import os,sys
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
P=os.path.join(ROOT,'index.html')
s=open(P,encoding='utf-8').read()
if 'task LT-1 (lane J)' in s:
    print('LT-1 already in index.html');sys.exit(0)
def rep(a,b):
    global s
    n=s.count(a);assert n==1,(n,a[:80]);s=s.replace(a,b)

# 1. ensureCtx: one hook after the render block is chosen (the playing buffer sets the latency hint and a 64-frame block)
rep("{const rq=rqWant(bsz);if(rq>128)o.renderSizeHint=rq}",
    "{const rq=rqWant(bsz);if(rq>128)o.renderSizeHint=rq}try{LT_HOOKS.ctxOpts(o)}catch(e){}")
# 2. Auto's step up while playing ignores dropouts heard at the playing buffer (lane J switches that to the mixing buffer itself)
rep("setInterval(()=>{if(!ctx||!play.on||UI.buf!==-1)return;const now=performance.now();let add=0;",
    "setInterval(()=>{if(!ctx||!play.on||UI.buf!==-1||ltIsPlay())return;const now=performance.now();let add=0;")
# 3. the step up at Stop likewise
rep("function autoBufCheck(){if(UI.buf!==-1||URS.n<2)return;",
    "function autoBufCheck(){if(UI.buf!==-1||URS.n<2)return;if(ltIsPlay()){URS.n=0;return}")

JS=r"""/* ===== lane J, task LT-1 (lane J): the output check (L1) and the playing buffer (L2). docs/latency-build.md =====
   L1: when the audio engine starts, when devices change and when the output is changed (events only, no timer), AudioLab looks at the output
   in use and warns when it is Bluetooth, a virtual device (eqMac, Background Music, BlackHole, an aggregate such as Cubase System Sound Link),
   a device in call mode (16 kHz) or one that reports a long delay; one button plays through the wired output (remembered as UI.ltWired).
   L2: while a track is armed or the computer keyboard plays and the song is stopped, the engine runs at the playing buffer (128 frames with
   64-frame render blocks where Chromium allows it); the mixing buffer (Auto or the fixed one) comes back at Play only when the playing buffer
   crackled there (a restart costs about 0.13 s, too long to add to every Play). Auto now also comes back down one step after a clean minute
   of playing, applied at Stop. LT_HOOKS: notify (lane F's notice, when it exists), audioRows (lane B's Settings rows), ctxOpts (ensureCtx). */
const LT={v:'0.278',cur:'mix',rq:128,pbUsed:0,heavy:false,forceMix:false,rsPlay:false,keys:new Set(),evT:0,iv:0,tot:0,dropT:0,abuf:0,clean:0,need:60000,down:false,stepT:0,downT:-1e9,shown:new Set(),later:new Set(),ocBusy:false,ocT:0,log:[]};
function ltIsPlay(){try{return LT.cur==='play'}catch(e){return false}}
function ltPB(){const v=UI.ltPlayBuf==null?128:+UI.ltPlayBuf;return UI.lat4&&(v===128||v===256)?v:0}
/* which buffer the engine should run at now */
function ltWant(){if(LT.forceMix)return'mix';if(play.on||LT.rsPlay)return LT.heavy?'mix':LT.cur;const pb=ltPB();if(!pb)return'mix';let n=0;try{n=liveTracks().length}catch(e){}return n?'play':'mix'}
const LT_HOOKS={notify:null,audioRows:null,
 ctxOpts(o){const m=ltWant(),pb=ltPB();LT.cur=m;LT.pbUsed=m==='play'?pb:0;if(m!=='play')return;o.latencyHint=pb/(UI.sr||48000);if(RQOK&&pb===128)o.renderSizeHint=64;else delete o.renderSizeHint}};
{const _e=ensureCtx;ensureCtx=function(){const had=!!ctx,r=_e.apply(this,arguments);if(!had&&ctx){LT.rq=ctx.renderQuantumSize||128;if(!LT.ocT){LT.ocT=1;setTimeout(()=>ltOutCheck('start'),1200)}}return r}}
{const _r=restartAudio;restartAudio=function(){LT.rsPlay=!!play.on;try{return _r.apply(this,arguments)}finally{LT.rsPlay=false}}}
/* switch between the playing and the mixing buffer: only while stopped, after 0.45 s of quiet, never while a key or a note is held */
function ltBufEval(){clearTimeout(ltBufEval.t);if(!ctx||play.on)return;let held=LT.keys.size>0;try{held=held||LIVE.size>0||(REC&&REC.on)}catch(e){}
 if(held||performance.now()-LT.evT<400){ltBufEval.t=setTimeout(ltBufEval,450);return}
 const w=ltWant();if(w===LT.cur&&(w!=='play'||LT.pbUsed===ltPB()))return;LT.log.unshift({t:Date.now(),from:LT.cur,to:w});LT.log.length=Math.min(LT.log.length,12);restartAudio(true)}
function ltSoon(ms){LT.evT=performance.now();clearTimeout(ltBufEval.t);ltBufEval.t=setTimeout(ltBufEval,ms||450)}
document.addEventListener('keydown',e=>{if(!e.repeat)LT.keys.add(e.code||e.key)},true);
document.addEventListener('keyup',e=>{LT.keys.delete(e.code||e.key);if(ctx&&!play.on)ltSoon()},true);
addEventListener('blur',()=>LT.keys.clear());
document.addEventListener('pointerup',()=>{if(ctx&&!play.on)ltSoon()},true);
/* while playing: a clean minute marks Auto one step down; dropouts at the playing buffer switch to the mixing buffer at once */
function ltTick(){if(!play.on||!ctx)return;const now=performance.now(),tot=URS.total,dt=CPU.dropT,drop=tot!==LT.tot||dt!==LT.dropT;LT.tot=tot;LT.dropT=dt;
 const ab=UI.abuf||256;if(ab!==LT.abuf){if(ab>LT.abuf&&LT.abuf){LT.stepT=now;LT.down=false;LT.clean=0;if(now-LT.downT<120000)LT.need=Math.min(480000,LT.need*2)}LT.abuf=ab}
 if(LT.cur==='play'){if(drop&&!LT.heavy){LT.heavy=true;URS.n=0;try{DBUF.ev=[]}catch(e){}setTimeout(()=>{if(!play.on||LT.cur!=='play')return;LT.forceMix=true;try{restartAudio(true)}finally{LT.forceMix=false}URS.n=0;
   toast('The playing buffer crackled with the whole song, so AudioLab went back to the mixing buffer while it plays. Your notes still use the small buffer when the song is stopped.')},0)}return}
 if(drop){LT.clean=0;return}LT.clean+=1000;if(UI.buf===-1&&ab>256&&LT.clean>=LT.need&&now-LT.stepT>=60000)LT.down=true}
function ltStepDown(){if(!LT.down||play.on||UI.buf!==-1)return;const ab=UI.abuf||256,i=ABUF.indexOf(ab);if(ab!==LT.abuf){LT.down=false;return}/* Auto went up at this Stop: no step down */
 if(i<1)return;const now=performance.now();UI.abuf=ABUF[i-1];LT.abuf=UI.abuf;LT.down=false;LT.clean=0;LT.stepT=LT.downT=now;try{saveUI()}catch(e){}
 restartAudio(true);toast(`A clean minute of playing, so the automatic buffer came back down to ${UI.abuf} samples (${(UI.abuf/(ctx?ctx.sampleRate:48000)*1000).toFixed(1)} ms).`)}
{const _s=start;start=function(){if(LT.cur==='play'&&LT.heavy&&ctx){LT.forceMix=true;try{restartAudio(true)}finally{LT.forceMix=false}}const r=_s.apply(this,arguments);
  LT.tot=URS.total;LT.dropT=CPU.dropT;if(!LT.abuf)LT.abuf=UI.abuf||256;clearInterval(LT.iv);LT.iv=setInterval(ltTick,1000);return r}}
{const _t=stop;stop=function(){const was=play.on,r=_t.apply(this,arguments);if(was){clearInterval(LT.iv);LT.iv=0;setTimeout(ltStepDown,320);ltSoon(600)}return r}}
/* the latency read-out says when the playing buffer is in use */
{const _l=latency;latency=function(){const r=_l.apply(this,arguments);try{if(ctx&&LT.cur==='play'){const e=$('#latO');if(e)e.textContent+=' · playing buffer '+LT.pbUsed+' samples, blocks of '+(ctx.renderQuantumSize||128)}}catch(e){}return r}}

/* ---- L1: the output check ---- */
const LT_WIRED=/\bifi\b|gryphon|ams-?24|zoom ams|focusrite|scarlett|\brme\b|babyface|fireface|motu|apogee|audient|\bssl\b|universal audio|apollo|\bvolt\b|\bdac\b/i;
function ltOutWhy(o){const l=String(o&&o.label||''),hw=o&&o.hw||null,t=hw&&hw.transport,R=[];
 const eq=/\(eqmac\)|\beqmac\b/i.test(l),vir=!eq&&(o.type==='virtual'||t==='virtual'||t==='aggregate'||/background music|blackhole|soundflower|loopback|sound link|aggregate|multi-output|krisp|zoom ?audio|teams audio|vb-audio|voicemeeter/i.test(l));
 const bt=t==='bluetooth'||o.type==='bt'||/airpods|bluetooth|soundlink|\bbose\b|beats |\bjbl\b|hands-?free|wh-1000|wf-1000|\bbuds\b|jabra|marshall/i.test(l);
 if(eq)R.push('it goes through eqMac, an app that processes the sound on its way and adds delay');
 if(vir)R.push('it is a virtual device that passes the sound through other software before it reaches a speaker');
 if(bt)R.push('it is Bluetooth, which adds about 150 ms or more');
 const rate=(o.full&&o.rate)||(o.use&&ctx&&!UI.sr?ctx.sampleRate:0);if(rate&&rate<=16000)R.push(`it runs at ${rate/1000} kHz, the call mode a headset uses when an app has its microphone open, so music loses everything above ${rate/2000} kHz`);
 if(o.full&&o.use&&ctx){const ms=((ctx.outputLatency||0)+(ctx.baseLatency||0))*1000;if(ms>40&&!eq&&!vir&&!bt)R.push(`it reports ${Math.round(ms)} ms of delay`)}
 return R}
function ltWired(outs,cur){const ok=outs.filter(o=>o.kind==='out'&&o!==cur&&o.id&&o.id!=='default'&&!ltOutWhy(Object.assign({},o,{use:false})).length);
 return(UI.ltWired&&ok.find(o=>adNorm(o.label)===UI.ltWired))||ok.find(o=>LT_WIRED.test(o.label))||ok.find(o=>o.type==='dac'||o.type==='int'||o.type==='usb')||null}
async function ltUseOut(o){UI.ltWired=adNorm(o.label);try{saveUI()}catch(e){}try{await listOuts()}catch(e){}
 const os=document.getElementById('outSel');if(!os||![...os.options].some(x=>x.value===o.id)){toast(o.label.trim()+' is not in the list of outputs any more. Pick it in Settings, Audio.');return false}
 os.value=o.id;os.dispatchEvent(new Event('change'));return true}
const LT_ICO='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4 4 0 0 1 0 6"/><path d="M18.5 6.5a7.5 7.5 0 0 1 0 11"/></svg>';
function ltNotify(n){return askChoice(n.title,n.text,n.buttons,LT_ICO)}
async function ltOutCheck(why){if(UI.ltOutChk===false||!ctx||LT.ocBusy)return null;LT.ocBusy=true;try{
  let A=null;try{A=await adScan(true)}catch(e){}const cur=A&&adCur();
  if(!cur||!A.named){if(ctx.sampleRate<=16000&&!LT.shown.has('#rate')){LT.shown.add('#rate');toast(`Your output runs at ${ctx.sampleRate/1000} kHz, the call mode of a headset with its microphone in use: music loses its highs and plays late. Pick a wired output in Settings, Audio.`)}return null}
  const key=adNorm(cur.label);if((UI.ltOkOut||[]).includes(key)||LT.shown.has(key)||LT.later.has(key))return null;
  const R=ltOutWhy(cur);if(!R.length){if(['dac','int','usb'].includes(cur.type)&&cur.id!=='default'){UI.ltWired=key;try{saveUI()}catch(e){}}return null}
  LT.shown.add(key);const w=ltWired(A.outs,cur),nm=cur.label.trim();
  const text=`AudioLab is playing through ${nm}: ${R.join('; ')}. The notes you play will sound late${w?', and '+w.label.trim()+' is connected':''}.`;
  const btns=(w?[{label:'Play through '+w.label.trim(),v:'wired',cls:'pri'}]:[]).concat([{label:'Keep this output',v:'keep'},{label:'Not now',v:'later'}]);
  let v=null;try{v=await (LT_HOOKS.notify||ltNotify)({kind:'output',why,title:'This output makes notes late',text,buttons:btns,device:nm,wired:w&&w.label})}catch(e){}
  if(v==='wired'&&w)await ltUseOut(w);
  else if(v==='keep'){UI.ltOkOut=(UI.ltOkOut||[]).filter(x=>x!==key).concat([key]).slice(-12);try{saveUI()}catch(e){}toast(`AudioLab will not warn about ${nm} again. Settings, Audio, Check the output device turns the check off.`)}
  else LT.later.add(key);
  return v||'later'}finally{LT.ocBusy=false}}
try{navigator.mediaDevices.addEventListener('devicechange',()=>{clearTimeout(ltOutCheck.t);ltOutCheck.t=setTimeout(()=>ltOutCheck('change'),1500)})}catch(e){}
try{document.getElementById('outSel').addEventListener('change',()=>{clearTimeout(ltOutCheck.t);ltOutCheck.t=setTimeout(()=>ltOutCheck('pick'),900)})}catch(e){}

/* ---- the two Settings rows (lane B places them for good through LT_HOOKS.audioRows; until then they sit under Render blocks) ---- */
const LT_ROWS=[
{"id":"playBuf","l":"Playing buffer","pg":"audio","b":"Audio driver","sc":"app","k":"UI.ltPlayBuf","c":"#ltPbSel","t":"select","d":"128","h":"While a track is armed or the computer keyboard plays, and the song is stopped, AudioLab uses this smaller buffer so notes sound sooner.","w":"playing buffer latency live armed keyboard midi notes small buffer fast monitor"},
{"id":"outCheck","l":"Check the output device","pg":"audio","b":"Audio driver","sc":"app","k":"UI.ltOutChk","c":"#ltOcChk","t":"check","d":true,"h":"Warns when the sound goes through Bluetooth, a virtual device such as eqMac or BlackHole, or a device in call mode, and offers your wired output instead.","w":"output check bluetooth eqmac blackhole background music virtual call mode 16 khz warning wired dac late"}];
LT_HOOKS.audioRows=LT_ROWS;
{const rq=document.getElementById('rqSel'),row=rq&&rq.closest('.cprow');if(row&&!document.getElementById('ltPbSel')){
  const a=document.createElement('div');a.className='cprow';a.title=LT_ROWS[0].h;a.innerHTML='<span>Playing buffer</span><select id="ltPbSel"><option value="128">128 samples while you play (recommended)</option><option value="256">256 samples while you play</option><option value="0">Off: always the buffer above</option></select>';
  const b=document.createElement('label');b.className='chk';b.title=LT_ROWS[1].h;b.innerHTML='<input type="checkbox" id="ltOcChk"> Check the output device (warns about Bluetooth, eqMac and call mode)';
  row.after(a,b);const s=a.querySelector('select'),c=b.querySelector('input');s.value=String(ltPB()||(UI.ltPlayBuf==null?128:0));c.checked=UI.ltOutChk!==false;
  s.onchange=()=>{UI.ltPlayBuf=+s.value||0;try{saveUI()}catch(e){}if(ctx&&!play.on)ltSoon(50)};
  c.onchange=()=>{UI.ltOutChk=c.checked;if(c.checked){UI.ltOkOut=[];LT.shown.clear();LT.later.clear()}try{saveUI()}catch(e){}if(c.checked&&ctx)ltOutCheck('setting')}}}
try{for(const r of LT_ROWS)if(!STX.has(r.id)){STT.push(r);STX.set(r.id,r)}}catch(e){}
{const o=document.querySelector('#bufSel option[value="-1"]');if(o)o.textContent='Auto (recommended): goes up when it hears dropouts, back down after a clean minute'}
/* ===== end of lane J LT-1 ===== */
"""
rep("function askChoice(title,text,btns,icon){",JS+"function askChoice(title,text,btns,icon){")
open(P,'w',encoding='utf-8').write(s)
print('LT-1 applied')
