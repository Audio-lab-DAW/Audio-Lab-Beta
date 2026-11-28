"""Task LT-3a (lane J): fast MIDI notes in the desktop app (L5): notes read in a hidden window of the shell and posted straight
into the instrument's AudioWorklet through a MessagePort, past the page's main thread. One instrument kind in this step: the pooled
voice engine (al-poly: Plant, the basic synths, Wavetable; not Acid). docs/latency-build.md
Edit script with unique, asserted anchors; safe to re-run (does nothing when the step is in). Needs LT-1 and LT-2.
Run from the repository root: python3 tools/engine-lab/lt/lt_3a.py"""
import os,sys,json
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
def load(p):return open(os.path.join(ROOT,p),encoding='utf-8').read()
def save(p,s):open(os.path.join(ROOT,p),'w',encoding='utf-8').write(s)
def rep(s,a,b):
    n=s.count(a);assert n==1,(n,a[:90]);return s.replace(a,b)

# ---------- desktop shell: one hook each in main.js and preload.js, the module listed in the build ----------
m=load('desktop/main.js')
if 'lt-midi' not in m:
    a="    try { require('./native-engine').setup({ ipcMain, app }); } catch (e) { console.warn('native engine', e); }  // task NB-N2b: idle until the page asks (desktop/native-engine.js)\n"
    m=rep(m,a,a+"    try { require('./lt-midi').setup({ ipcMain, app, BrowserWindow, session, scheme: SCHEME }); } catch (e) { console.warn('fast MIDI notes', e); }  // task LT-3a: notes past the page's main thread (desktop/lt-midi.js)\n")
    save('desktop/main.js',m)
p=load('desktop/preload.js')
if 'ltMidiPort' not in p:
    p=p.rstrip('\n')+"\n// task LT-3a: fast MIDI notes (desktop/lt-midi.js): the page posts { ltMidiPort: true } with one end of a MessageChannel whose other end is in its AudioWorklet\ncontextBridge.exposeInMainWorld('audiolabLtMidi', true);\nwindow.addEventListener('message', (e) => {\n  if (e.data && e.data.ltMidiPort === true && e.ports && e.ports[0]) ipcRenderer.postMessage('al:lt-port', null, [e.ports[0]]);\n});\n"
    save('desktop/preload.js',p)
pk=load('desktop/package.json')
if '"lt-midi.js"' not in pk:
    pk=rep(pk,'      "native-feeder.js"\n    ],','      "native-feeder.js",\n      "lt-midi.js"\n    ],');json.loads(pk);save('desktop/package.json',pk)

# ---------- index.html ----------
s=load('index.html')
if 'task LT-3a (lane J)' in s:
    print('LT-3a already in index.html (desktop hooks checked)');sys.exit(0)
assert 'task LT-2 (lane J)' in s,'LT-2 first'
# the worklet bundle: lane J's piece goes first, so it can see the pooled voice engine being registered (empty outside the desktop app's need: it only wraps)
s=rep(s,"})();\\n'+WLSRC+(typeof VWL==='string'?VWL:'')+'\\n'+(typeof RWL","})();\\n'+(window.LT_WL||'')+WLSRC+(typeof VWL==='string'?VWL:'')+'\\n'+(typeof RWL")

# LT-1's switch between the playing and the mixing buffer restarts the engine; a context closed while its worklet module still loads
# makes Chromium reject the load ("worklet failed AbortError", seen 2 of 5 runs of taskLT_1.py on v0.297): the switch now waits for the
# load (at most about 6 s). Found in LT-3a's tests; LT-1 is lane J's own code.
s=rep(s,"if(held||performance.now()-LT.evT<400){ltBufEval.t=setTimeout(ltBufEval,450);return}",
  "if(held||performance.now()-LT.evT<400){ltBufEval.t=setTimeout(ltBufEval,450);return}\n if(ctx._wlp&&!ctx._wl&&(LT.wlW=(LT.wlW||0)+1)<20){ltBufEval.t=setTimeout(ltBufEval,300);return}LT.wlW=0;")

JS=r"""/* ===== lane J, task LT-3a (lane J): fast MIDI notes in the desktop app (L5). docs/latency-build.md =====
   A note from a MIDI keyboard went Web MIDI, controller layer, noteOn, then a message to the instrument's worklet: all on this page's main
   thread, so a busy moment (drawing, a long task, a project loading) held the note back. In the desktop app the shell now reads notes in a
   small hidden window that does nothing else (desktop/lt-midi.js) and posts them straight into the played track's worklet through a
   MessagePort; the voice starts at the next audio block. This page still gets every note through its own Web MIDI (piano display, recording,
   meters) and does not play again what the worklet played. Only plain note inputs (the controller layer's generic profile, not a
   surface, not off, not an IAC or "to Cubase" kind of port), only notes and the sustain pedal; controllers, MIDI learn and surfaces stay
   with lane C's code. Nothing runs without a MIDI keyboard and a played track. UI.ltFast=false turns it off.
   LT-3a: the pooled voice engine (Plant, the basic synths, Wavetable; not Acid). LT-3b: every worklet instrument, drums, recording times. */
window.LT_WL=`/* lane J, task LT-3a: fast MIDI notes into the pooled voice engine */
(()=>{if(typeof registerProcessor!=='function'||globalThis.LTW)return;
const W=globalThis.LTW={P:new Set(),port:null,ret:null,held:new Map(),sus:0,tg:-1,blk:new Set(),learn:0,cfg:null,n:0};
const rp=registerProcessor;globalThis.registerProcessor=function(name,C){if(name!=='al-poly')return rp(name,C);class L extends C{constructor(o){super(o);W.add(this)}}return rp(name,L)};
W.add=p=>{const f=p.port.onmessage;p.port.onmessage=e=>{const d=e.data;if(d&&d.lt){try{W.msg(p,d.lt,e)}catch(x){}return}if(d&&d.die)W.P.delete(p);if(f)f.call(p.port,e)}};
W.msg=(p,m,e)=>{if(m.port&&e.ports&&e.ports[0]){if(W.port)try{W.port.close()}catch(x){}W.port=e.ports[0];W.port.onmessage=W.midi;W.ret=p;if(W.cfg)W.port.postMessage({ports:W.cfg})}
 if(m.cfg){W.cfg=m.cfg.ports||[];W.blk=new Set(m.cfg.blk||[]);W.learn=m.cfg.learn?1:0;if(W.port)W.port.postMessage({ports:W.cfg})}
 if(m.ping){W.ret=p;if(W.port)W.port.postMessage({ping:m.ping})}
 if('on' in m){if(m.on){p.ltId=m.id;W.P.add(p);p.port.postMessage({lt:{ack:m.id}})}else{for(const h of W.held.values())p.apply({off:[h.tg,0]});W.P.delete(p);p.ltId=0}}};
W.off=k=>{const h=W.held.get(k);if(!h)return;W.held.delete(k);for(const p of W.P)p.apply({off:[h.tg,0]})};
W.midi=e=>{const d=e.data;if(!d)return;if(d.pong!=null){if(W.ret)W.ret.port.postMessage({lt:{pong:d.pong,ins:d.ins||[]}});return}
 const a=d.m;if(!a)return;const s=a[0]&0xf0,nt=a[1];
 if(s===0xB0){if(a[1]!==64)return;W.sus=a[2]>=64?1:0;if(!W.sus)for(const[k,h] of[...W.held])if(h.up)W.off(k);return}
 if(s===0x90&&a[2]>0){if(W.learn||W.blk.has(nt)||!W.P.size)return;const h=W.held.get(nt);if(h){if(!h.up)return;W.off(nt)}
  const tg=W.tg--,v=a[2]/127,t0=currentTime;for(const p of W.P)p.apply({n:[[t0,3600,nt-24,v,p.ltId,tg,0,0,0]]});W.held.set(nt,{tg,up:0});W.n++;
  if(W.ret)W.ret.port.postMessage({lt:{ltn:[nt,a[2],t0,d.t||0]}});return}
 if(s===0x80||s===0x90){const h=W.held.get(nt);if(!h)return;if(W.sus){h.up=1;return}W.off(nt)}};
})();
`;
const LTF={ctx:null,chan:0,tgt:new Map(),cfg:'',ins:null,allow:new Set(),blk:new Set(),skip:0,n:0,rep:[],from:null,pong:0};
const ltFastOK=()=>!!(window.audiolabLtMidi&&UI.ltFast!==false&&UI.poly!==false);
const ltFastKind=I=>!!I&&pvOK(I)&&I.preset!=='acid';
function ltFastPorts(){const r=[];try{if(UI.ctlStop)return r;for(const d of CTL.devs.values()){if(!d.prof||d.prof.id!=='generic'||ctlOff(d))continue;if(/\bIAC\b|Cubase|Network Session|loopMIDI/i.test(d.name))continue;if(!r.includes(d.name))r.push(d.name)}}catch(e){}return r}
function ltFastBlk(){const b=[];try{for(const k of ctlIndex().byM.keys()){const m=/^note[^0-9]*\d+[^0-9]+(\d+)$/.exec(String(k));if(m)b.push(+m[1])}}catch(e){}return b}
function ltFastBack(e){const d=e.data&&e.data.lt;if(!d)return;if(d.ack!=null){for(const o of LTF.tgt.values())if(o.id===d.ack&&o.st.node&&o.st.node.port===e.target)o.ack=1}
 if(d.pong!=null){LTF.pong=d.pong;LTF.ins=new Set(d.ins)}if(d.ltn){LTF.n++;LTF.rep.push(d.ltn);if(LTF.rep.length>64)LTF.rep.shift()}}
function ltFastClear(){for(const o of LTF.tgt.values())try{pvSend(o.st,{lt:{on:0}})}catch(e){}LTF.tgt.clear()}
function ltFastEval(){clearTimeout(ltFastEval.t);ltFastEval.t=null;
 if(!ltFastOK()||!ctx||ctx.state==='closed'){ltFastClear();return}
 if(LTF.ctx!==ctx){LTF.tgt.clear();LTF.ctx=ctx;LTF.chan=0;LTF.cfg='';LTF.ins=null}
 const ports=ltFastPorts();let L=[];if(ports.length)try{L=liveTracks().filter(t=>t.kind==='inst'&&ltFastKind(t.inst))}catch(e){}
 const want=new Map();let wait=false;
 for(const t of L){const N=NODES.get(t.id);if(!N||!N.in)continue;const st=pvState(ctx,N.in);if(!st.node){wait=true;continue}const I=t.inst,sig=pvKey(I,ctx,false);
  if(I.preset==='wtab'){const nm=I.wt||'basic';if(!st.wts)st.wts=new Set();if(!st.wts.has(nm)){st.wts.add(nm);pvSend(st,{wt:nm,T:wtMips(nm)})}}
  let id=st.ids.get(sig);if(!id){if(st.ids.size>80)st.ids.clear();id=st.nid++;st.ids.set(sig,id);pvSend(st,{P:pvParams(I,ctx,false),id})}want.set(t.id,{st,id,sig,ack:0})}
 for(const[k,o] of LTF.tgt){const w=want.get(k);if(!w||w.st!==o.st||w.id!==o.id){try{pvSend(o.st,{lt:{on:0}})}catch(e){}LTF.tgt.delete(k)}}
 if(want.size&&!LTF.chan){const o=[...want.values()][0];try{const mc=new MessageChannel();o.st.node.port.postMessage({lt:{port:1}},[mc.port1]);window.postMessage({ltMidiPort:true},'*',[mc.port2]);LTF.chan=1}catch(e){console.warn('fast MIDI notes',e);return}}
 if(LTF.chan){const blk=ltFastBlk(),learn=!!(typeof ML!=='undefined'&&ML.on&&ML.sel),cs=JSON.stringify([ports,blk,learn]);const o=[...want.values()][0]||[...LTF.tgt.values()][0];
  if(o&&cs!==LTF.cfg){LTF.cfg=cs;LTF.allow=new Set(ports);LTF.blk=new Set(blk);LTF.learn=learn;pvSend(o.st,{lt:{cfg:{ports,blk,learn}}});pvSend(o.st,{lt:{ping:Date.now()}})}}
 for(const[k,w] of want){const o=LTF.tgt.get(k);if(o){o.sig=w.sig;continue}if(!w.st.ltB){w.st.ltB=1;try{w.st.node.port.addEventListener('message',ltFastBack);w.st.node.port.start()}catch(e){}}LTF.tgt.set(k,w);pvSend(w.st,{lt:{on:1,id:w.id}})}
 if(wait)ltFastEval.t=setTimeout(ltFastEval,300)}
const ltFastSoon=()=>{if(!ltFastOK())return;if(!ltFastEval.t)ltFastEval.t=setTimeout(ltFastEval,120)};
document.addEventListener('pointerup',ltFastSoon,true);document.addEventListener('keyup',ltFastSoon,true);
/* which device a note came from (lane C's ctlMsg, wrapped the way other lanes wrap noteOn) */
{const _m=ctlMsg;ctlMsg=function(d){const o=LTF.from;LTF.from=d;try{return _m.apply(this,arguments)}finally{LTF.from=o}}}
/* the page does not start a voice the worklet already started: a note from a port the shell reads, on a track the worklet plays */
{const _v=voiceOn;voiceOn=function(t,p,v){const d=LTF.from;if(d&&t&&LTF.ins&&LTF.ins.has(d.name)&&LTF.allow.has(d.name)&&!LTF.blk.has(p+24)&&ctx===LTF.ctx){const o=LTF.tgt.get(t.id);if(o&&o.ack){LTF.skip++;if(pvKey(t.inst,ctx,false)!==o.sig)ltFastSoon();return null}}return _v.apply(this,arguments)}}
{const _n=noteOn;noteOn=function(){const r=_n.apply(this,arguments);if(LTF.from&&!LTF.tgt.size)ltFastSoon();return r}}
LT_HOOKS.fastNotes=()=>({on:ltFastOK(),tracks:[...LTF.tgt].map(([id,o])=>({id,ready:!!o.ack})),ports:[...LTF.allow],seen:LTF.ins?[...LTF.ins]:[],played:LTF.n,skipped:LTF.skip});
/* ===== end of lane J LT-3a ===== */
"""
s=rep(s,"/* ===== end of lane J LT-2 ===== */\n","/* ===== end of lane J LT-2 ===== */\n"+JS)
save('index.html',s)
print('LT-3a applied')
