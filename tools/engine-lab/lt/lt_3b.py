"""Task LT-3b (lane J): fast MIDI notes in the desktop app (L5), second part. docs/latency-build.md
LT-3a posted notes from the shell's listening window straight into one worklet kind (the pooled voice engine). This step:
  - every worklet instrument whose notes are plain held voices: the pooled engine (Plant, basic synths, Wavetable), Sampler grains,
    Emit, Vector grains, Vector FM, Orbit, Sub bass, Psy bass, Crackle. The page works out each played track's note message once
    (the instrument's own play function, captured, never sent) for all 128 keys; the worklet only puts in the time, the tag and the
    velocity. Left to the page: Acid (slide and accent), Venom (its own engine per note), Bouncing ball (its display), the classic
    Sampler, a track with a MIDI effect (chord, arpeggiator), a locked instrument.
  - the Drum kit: a small worklet player of lane J's own (al-lt-drum) plays the kit's pads from the same rendered pad buffers the page
    uses (PADBUF, kickRender), with level, pan, the hat and kick chokes and the key-up fade of the page's path.
  - recording placed by the MIDI time stamp: a note from a MIDI keyboard is placed by its Web MIDI event's time stamp (when it arrived),
    not by when the page got to it (LT-2's placement used the page's time for MIDI notes). Browser and desktop.
  - the Settings row "Fast MIDI notes" (desktop only) through LT_HOOKS.audioRows.
Edit script with unique, asserted anchors; safe to re-run. Needs LT-1, LT-2, LT-3a.
Run from the repository root: python3 tools/engine-lab/lt/lt_3b.py"""
import os,sys
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
def load(p):return open(os.path.join(ROOT,p),encoding='utf-8').read()
def save(p,s):open(os.path.join(ROOT,p),'w',encoding='utf-8').write(s)
def rep(s,a,b):
    n=s.count(a);assert n==1,(n,a[:90]);return s.replace(a,b)

s=load('index.html')
if 'task LT-3b (lane J)' in s:
    print('LT-3b already in index.html');sys.exit(0)
assert 'task LT-3a (lane J)' in s,'LT-3a first'

# ---- LT-2's placement: a MIDI note is placed by its Web MIDI event's time stamp (LT.miT, set in the ctlMsg wrapper below) ----
s=rep(s,"pn=LT.kdT&&now-LT.kdT<40&&LT.kdT<=now?LT.kdT:now,spk=o.contextTime+(pn-o.performanceTime)/1000,b=beatOf(secOf(L.b)+(spk-T0));\n    if(isFinite(b)&&Math.abs(secOf(b)-secOf(L.b))<.25)L.b=b}}catch(e){}return r}}",
  "mi=typeof LT.miT==='number'&&LT.miT<=now&&now-LT.miT<1000,pn=mi?LT.miT:LT.kdT&&now-LT.kdT<40&&LT.kdT<=now?LT.kdT:now,spk=o.contextTime+(pn-o.performanceTime)/1000,b=beatOf(secOf(L.b)+(spk-T0));\n    if(isFinite(b)&&Math.abs(secOf(b)-secOf(L.b))<(mi?1.05:.25))L.b=b}}catch(e){}return r}}")

# ---- the LT-3a block is replaced by LT-3a + LT-3b (lane J's own code) ----
a=s.index('/* ===== lane J, task LT-3a (lane J): fast MIDI notes in the desktop app (L5).')
e0='/* ===== end of lane J LT-3a ===== */\n';b=s.index(e0)+len(e0)
assert s.count(e0)==1 and a<b

JS=r"""/* ===== lane J, task LT-3a (lane J): fast MIDI notes in the desktop app (L5). docs/latency-build.md =====
   (extended by task LT-3b (lane J): every worklet instrument, the Drum kit, recording by the MIDI time stamp, the Settings row)
   A note from a MIDI keyboard went Web MIDI, controller layer, noteOn, then a message to the instrument's worklet: all on this page's main
   thread, so a busy moment (drawing, a long task, a project loading) held the note back. In the desktop app the shell reads notes in a
   small hidden window that does nothing else (desktop/lt-midi.js) and posts them straight into the played track's worklet through a
   MessagePort; the voice starts at the next audio block. This page still gets every note through its own Web MIDI (piano display, recording,
   meters) and does not play again what the worklet played. Only plain note inputs (the controller layer's generic profile, not a
   surface, not off, not an IAC or "to Cubase" kind of port), only notes and the sustain pedal; controllers, MIDI learn and surfaces stay
   with lane C's code. Nothing runs without a MIDI keyboard and a played track. UI.ltFast=false (Settings, "Fast MIDI notes") turns it off.
   LT-3b: the page works out each played track's note message once for all 128 keys with the instrument's own play function (captured,
   never sent); the worklet only puts in the time, the tag and the velocity, so the sound is the engine's own. The Drum kit's pads play in
   al-lt-drum (lane J's), from the page's own pad buffers. Left to the page: Acid, Venom, Bouncing ball, the classic Sampler, MIDI effects. */
window.LT_WL=`/* lane J, tasks LT-3a and LT-3b: fast MIDI notes into the worklet instruments */
(()=>{if(typeof registerProcessor!=='function'||globalThis.LTW)return;
const NM=new Set(['al-poly','al-grain','al-emit','al-vgrain','al-vfm','al-orb','al-sbs','al-psb','al-crki']);
const W=globalThis.LTW={P:new Map(),port:null,ret:null,held:new Map(),sus:0,tg:-1,blk:new Set(),learn:0,cfg:null,n:0};
const rp=registerProcessor;globalThis.registerProcessor=function(name,C){if(!NM.has(name))return rp(name,C);class L extends C{constructor(o){super(o);W.add(this)}}return rp(name,L)};
W.add=p=>{const f=p.port.onmessage;p.ltF=f;p.port.onmessage=e=>{const d=e.data;if(d&&d.lt){try{W.msg(p,d.lt,e)}catch(x){}return}if(d&&d.die)W.drop(p);if(f)f.call(p.port,e)}};
W.send=(p,m)=>{if(p.ltF)p.ltF.call(p.port,{data:m})};
W.drop=p=>{W.P.delete(p);if(W.ret===p)W.ret=W.P.size?W.P.keys().next().value:null};
W.msg=(p,m,e)=>{if(m.port&&e.ports&&e.ports[0]){if(W.port)try{W.port.close()}catch(x){}W.port=e.ports[0];W.port.onmessage=W.midi;W.ret=p;if(W.cfg)W.port.postMessage({ports:W.cfg})}
 if(m.cfg){W.cfg=m.cfg.ports||[];W.blk=new Set(m.cfg.blk||[]);W.learn=m.cfg.learn?1:0;if(W.port)W.port.postMessage({ports:W.cfg})}
 if(m.ping){W.ret=p;if(W.port)W.port.postMessage({ping:m.ping})}
 if('on' in m){if(m.on){if(m.kit){p.K=m.kit;W.P.set(p,{kit:1})}else W.P.set(p,{T:m.T,iw:m.iw,it:m.it,iv:m.iv});if(!W.ret)W.ret=p;p.port.postMessage({lt:{ack:m.id}})}
  else{for(const h of W.held.values())W.rel(p,W.P.get(p),h.tg);W.drop(p);if(p.K)p.live=0}}};
W.rel=(p,o,tg)=>{if(!o)return;if(o.kit)p.rel(tg);else W.send(p,{off:[tg,0]})};
W.off=k=>{const h=W.held.get(k);if(!h)return;W.held.delete(k);for(const[p,o] of W.P)W.rel(p,o,h.tg)};
W.midi=e=>{const d=e.data;if(!d)return;if(d.pong!=null){if(W.ret)W.ret.port.postMessage({lt:{pong:d.pong,ins:d.ins||[]}});return}
 const a=d.m;if(!a)return;const s=a[0]&0xf0,nt=a[1];
 if(s===0xB0){if(a[1]!==64)return;W.sus=a[2]>=64?1:0;if(!W.sus)for(const[k,h] of[...W.held])if(h.up)W.off(k);return}
 if(s===0x90&&a[2]>0){if(W.learn||W.blk.has(nt)||!W.P.size)return;const h=W.held.get(nt);if(h){if(!h.up)return;W.off(nt)}
  const tg=W.tg--,v=a[2]/127,t0=currentTime;let any=0;
  for(const[p,o] of W.P){if(o.kit){if(p.hit(nt,v,tg))any=1;continue}const b=o.T&&o.T[nt];if(!b)continue;const x=b.slice();x[o.iw]=t0;x[o.it]=tg;if(o.iv>=0)x[o.iv]=v;W.send(p,{n:[x]});any=1}
  if(!any)return;W.held.set(nt,{tg,up:0});W.n++;
  if(W.ret)W.ret.port.postMessage({lt:{ltn:[nt,a[2],t0,d.t||0]}});return}
 if(s===0x80||s===0x90){const h=W.held.get(nt);if(!h)return;if(W.sus){h.up=1;return}W.off(nt)}};
/* the Drum kit's pads (LT-3b): one-shots from the page's own pad buffers; level, pan (the StereoPanner's equal-power law), the open hat
   choked by the next hat (6 ms), a kick choked by the next kick (4 ms), the key-up fade of the page's path */
class LtDrum extends AudioWorkletProcessor{constructor(){super();this.V=[];this.K=null;this.live=1;this.oh=null;this.kk=null;W.add(this)}
 hit(nt,v,tg){const K=this.K,P=K&&K.pads[nt-60];if(!P||!P.b.length)return 0;
  if(P.grp===1&&this.oh&&!this.oh.dc)this.oh.dc=Math.exp(-1/(.006*sampleRate));if(P.grp===2&&this.kk&&!this.kk.ln)this.kk.ln=Math.max(1,Math.round(.004*sampleRate));
  const b=P.b[(Math.random()*P.b.length)|0],H=Math.PI/2,st=b.length>1,pn=P.pan||0,x=st?(pn<=0?pn+1:pn):(pn+1)/2;
  const o={b,i:0,n:b[0].length,g:P.g*v*K.G,st,pl:pn<=0,c:Math.cos(x*H),s:Math.sin(x*H),e:1,dk:0,dc:0,cf:1,ln:0,lk:0,tg};
  this.V.push(o);if(P.grp===1&&P.op)this.oh=o;if(P.grp===2)this.kk=o;if(this.V.length>64)this.V.shift();return 1}
 rel(tg){if(!this.K)return;for(const o of this.V)if(o.tg===tg&&!o.dk)o.dk=Math.exp(-1/(this.K.tau*sampleRate))}
 process(i,outs){const O=outs[0],L=O[0],R=O[1]||O[0],m=L.length;if(!this.V.length)return this.live===1;
  for(let k=this.V.length-1;k>=0;k--){const o=this.V[k],l=o.b[0],r=o.st?o.b[1]:l;let j=0;
   for(;j<m&&o.i<o.n;j++,o.i++){let a=o.g*o.e*o.cf;if(o.dk)o.e*=o.dk;if(o.dc)o.cf*=o.dc;if(o.ln){a*=Math.max(0,1-o.lk/o.ln);o.lk++}
    if(!o.st){const y=l[o.i]*a;L[j]+=y*o.c;R[j]+=y*o.s}else if(o.pl){L[j]+=(l[o.i]+r[o.i]*o.c)*a;R[j]+=r[o.i]*o.s*a}else{L[j]+=l[o.i]*o.c*a;R[j]+=(r[o.i]+l[o.i]*o.s)*a}}
   if(o.i>=o.n||o.e*o.cf<1e-6||(o.ln&&o.lk>=o.ln)){this.V.splice(k,1);if(this.oh===o)this.oh=null;if(this.kk===o)this.kk=null}}
  return true}}
rp('al-lt-drum',LtDrum);
})();
`;
const LTF={ctx:null,chan:0,tgt:new Map(),cfg:'',ins:null,allow:new Set(),blk:new Set(),skip:0,n:0,rep:[],from:null,pong:0,id:1,why:new Map()};
const ltFastOK=()=>!!(window.audiolabLtMidi&&UI.ltFast!==false&&UI.poly!==false);
/* the engines whose live notes are held voices of the same shape: [is it, processor, its states, its play function] */
const LTE=[[I=>pvOK(I)&&I.preset!=='acid','al-poly',()=>PVS,(...a)=>pvPlay(...a)],[I=>gvOK(I),'al-grain',()=>GVS,(...a)=>gvPlay(...a)],
 [I=>emOK(I),'al-emit',()=>EMS,(...a)=>emPlay(...a)],[I=>vgOK(I),'al-vgrain',()=>VGS,(...a)=>vgPlay(...a)],[I=>vfmOK(I),'al-vfm',()=>VFMS,(...a)=>vfmPlay(...a)],
 [I=>orbOK(I),'al-orb',()=>ORBS,(...a)=>orbPlay(...a)],[I=>sbsOK(I),'al-sbs',()=>SBSM,(...a)=>sbsPlay(...a)],[I=>psbOK(I),'al-psb',()=>PSBM,(...a)=>psbPlay(...a)],
 [I=>crkOK(I),'al-crki',()=>CRKM,(...a)=>crkPlay(...a)]];
const ltMfx=t=>{try{return!!(t&&t.fx&&t.fx.some(f=>f.on&&(f.type==='chord'||MIDIFX.has(f.type))))}catch(e){return true}};
/* what the fast path plays a track with: 'kit', an engine row, or null (the page plays it). Takes a track (or, as in LT-3a, an instrument). */
function ltFastKind(x){const t=x&&x.inst?x:null,I=t?t.inst:x;if(!I||I.lock||(t&&ltMfx(t)))return null;if(I.preset==='drums')return'kit';for(const E of LTE)try{if(E[0](I))return E}catch(e){}return null}
function ltFastSig(t){const I=t.inst;try{return I.preset==='drums'?JSON.stringify([I.pads,I.gain,I.og,I.r]):JSON.stringify(I)}catch(e){return String(Math.random())}}
/* the note message of every key, made by the instrument's own play function into a batch that is taken back before it is sent */
function ltCapT(E,I,N,st){const W0=-4321.0625,TG=-987654,ch={triv:true,dest:N.in,in:N.in,end:0};
 const run=(p,v)=>{const sv=st.nb;st.nb=[];let r=null;try{E[3](ctx,I,ch,p,W0,3600,v,TG);r=st.nb}catch(e){r=null}finally{st.nb=sv}return r&&r.length===1&&Array.isArray(r[0])?r[0]:null};
 const T=[];for(let m=0;m<128;m++){const x=run(m-24,.5);if(!x)return null;T.push(x)}
 const a=T[84],b=run(60,1);if(!b||b.length!==a.length)return null;const iw=a.indexOf(W0),it=a.indexOf(TG);if(iw<0||it<0)return null;
 let iv=-1;for(let k=0;k<a.length;k++)if(a[k]!==b[k]){if(iv>=0||a[k]!==.5||b[k]!==1)return null;iv=k}
 for(const x of T){if(x.length!==a.length||x[iw]!==W0||x[it]!==TG)return null;for(let k=0;k<x.length;k++)if(k!==iw&&k!==it&&typeof x[k]==='number'&&(x[k]<-1000||x[k]===TG))return null}
 return{T,iw,it,iv}}
/* the Drum kit's pads, from the page's own buffers: what padPlay plays for a hit, without the nodes */
function ltKitT(I){ensurePads(I);const sr=ctx.sampleRate,G=(I.gain!=null?I.gain:1)*(+I.og?Math.pow(10,I.og/20):1),r=I.r!=null?Math.min(I.r,.6):.2,pads=[],set=new Set();let wait=false;
 for(let i=0;i<16;i++){const pd=I.pads[i];pads.push(null);if(!pd||pd.type==='off'||pd.mute)continue;const ty=pd.type,D=pd.dec,tn=pd.tone;let P=null;
  try{if(ty==='kd'||ty==='kick'){let k;if(ty==='kd'){if(!pd.k)pd.k=kickParams('psyzap');k=pd.tune||pd.dec!==1?{...pd.k,tune:pd.k.tune+pd.tune,len:Math.min(2.5,pd.k.len*pd.dec)}:pd.k}
    else{const base=KPRE[pd.kp||'house']||KPRE.house;k={...base,tune:base.tune+pd.tune,len:Math.min(2.5,base.len*D),click:clamp(base.click*(.3+tn*1.4),0,100)}}
    const B=kickRender(k,sr,0),c=[];for(let q=0;q<Math.min(2,B.numberOfChannels);q++)c.push(B.getChannelData(q).slice());P={b:[c],g:pd.lvl*1.1,pan:pd.pan,grp:2}}
   else{const key=ty+'|'+pd.tune+'|'+D+'|'+tn+'|'+sr,V3=PADBUF.get(key);
    if(Array.isArray(V3))P={b:V3.map(x=>[x.getChannelData(0).slice()]),g:pd.lvl,pan:pd.pan,grp:ty==='chat'||ty==='ohat'?1:0,op:ty==='ohat'};
    else{wait=true;if(!V3){PADBUF.set(key,'busy');Promise.all([0,1,2].map(()=>padRender(pd,sr))).then(b=>{PADBUF.set(key,b);ltFastSoon()}).catch(()=>PADBUF.delete(key))}}}}catch(e){P=null}
  if(P){pads[i]=P;set.add(i)}}
 return{kit:{pads,G,tau:Math.max(.008,r/3)},set,wait}}
function ltFastBack(e){const d=e.data&&e.data.lt;if(!d)return;if(d.ack!=null){for(const o of LTF.tgt.values())if(o.id===d.ack&&o.node&&o.node.port===e.target)o.ack=1}
 if(d.pong!=null){LTF.pong=d.pong;LTF.ins=new Set(d.ins)}if(d.ltn){LTF.n++;LTF.rep.push(d.ltn);if(LTF.rep.length>64)LTF.rep.shift()}}
function ltFastDrop(o){try{o.node.port.postMessage({lt:{on:0}})}catch(e){}if(o.kit){const n=o.node;setTimeout(()=>{try{n.disconnect()}catch(e){}},1500)}}
function ltFastClear(){for(const o of LTF.tgt.values())ltFastDrop(o);LTF.tgt.clear()}
function ltFastEval(){clearTimeout(ltFastEval.t);ltFastEval.t=null;
 if(!ltFastOK()||!ctx||ctx.state==='closed'){ltFastClear();return}
 if(LTF.ctx!==ctx){LTF.tgt.clear();LTF.ctx=ctx;LTF.chan=0;LTF.cfg='';LTF.ins=null}
 const ports=ltFastPorts();let L=[];if(ports.length)try{L=liveTracks().filter(t=>t.kind==='inst')}catch(e){}
 const want=new Map();let wait=false;LTF.why.clear();
 for(const t of L){const k=ltFastKind(t);if(!k){LTF.why.set(t.id,'page');continue}const N=NODES.get(t.id);if(!N||!N.in){wait=true;continue}
  const sig=ltFastSig(t),o=LTF.tgt.get(t.id);
  if(o&&o.sig===sig&&o.din===N.in&&(k==='kit'?o.kit:o.st&&o.st.node&&!o.st.fin&&o.E===k)){want.set(t.id,o);continue}
  if(k==='kit'){if(!ctx._wl){wait=true;continue}const K=ltKitT(t.inst);if(K.wait)wait=true;if(!K.set.size)continue;
   let node=o&&o.kit&&o.din===N.in?o.node:null;if(!node){try{node=new AudioWorkletNode(ctx,'al-lt-drum',{numberOfInputs:0,numberOfOutputs:1,outputChannelCount:[2]});node.connect(N.in)}catch(e){LTF.why.set(t.id,'no drum player');continue}}
   want.set(t.id,{kit:1,node,din:N.in,sig:K.wait?sig+'~wait':sig,pads:K.set,msg:{kit:K.kit},id:LTF.id++,ack:0,fresh:1})}
  else{let st;try{st=pvState(ctx,N.in,k[1],k[2]())}catch(e){continue}if(!st.node){wait=true;continue}const C=ltCapT(k,t.inst,N,st);if(!C){LTF.why.set(t.id,'not one voice per note');continue}
   want.set(t.id,{E:k,st,node:st.node,din:N.in,sig,msg:{T:C.T,iw:C.iw,it:C.it,iv:C.iv},id:LTF.id++,ack:0,fresh:1})}}
 for(const[k,o] of LTF.tgt){const w=want.get(k);if(w===o)continue;if(!w||w.node!==o.node)ltFastDrop(o);LTF.tgt.delete(k)}
 if(want.size&&!LTF.chan){const o=[...want.values()][0];try{const mc=new MessageChannel();o.node.port.postMessage({lt:{port:1}},[mc.port1]);window.postMessage({ltMidiPort:true},'*',[mc.port2]);LTF.chan=1}catch(e){console.warn('fast MIDI notes',e);return}}
 if(LTF.chan){const blk=ltFastBlk(),learn=!!(typeof ML!=='undefined'&&ML.on&&ML.sel),cs=JSON.stringify([ports,blk,learn]);const o=[...want.values()][0];
  if(o&&cs!==LTF.cfg){LTF.cfg=cs;LTF.allow=new Set(ports);LTF.blk=new Set(blk);LTF.learn=learn;o.node.port.postMessage({lt:{cfg:{ports,blk,learn}}});o.node.port.postMessage({lt:{ping:Date.now()}})}}
 if(want.size)ltFastWrap();
 for(const[k,w] of want){if(!w.fresh)continue;w.fresh=0;if(!w.node.ltB){w.node.ltB=1;try{w.node.port.addEventListener('message',ltFastBack);w.node.port.start()}catch(e){}}
  LTF.tgt.set(k,w);w.node.port.postMessage({lt:{on:1,id:w.id,...w.msg}});w.msg=null}
 if(wait)ltFastEval.t=setTimeout(ltFastEval,300)}
function ltFastPorts(){const r=[];try{if(UI.ctlStop)return r;for(const d of CTL.devs.values()){if(!d.prof||d.prof.id!=='generic'||ctlOff(d))continue;if(/\bIAC\b|Cubase|Network Session|loopMIDI/i.test(d.name))continue;if(!r.includes(d.name))r.push(d.name)}}catch(e){}return r}
function ltFastBlk(){const b=[];try{for(const k of ctlIndex().byM.keys()){const m=/^note[^0-9]*\d+[^0-9]+(\d+)$/.exec(String(k));if(m)b.push(+m[1])}}catch(e){}return b}
const ltFastSoon=()=>{if(!ltFastOK())return;if(!ltFastEval.t)ltFastEval.t=setTimeout(ltFastEval,120)};
document.addEventListener('pointerup',ltFastSoon,true);document.addEventListener('keyup',ltFastSoon,true);
/* which device a note came from, and its Web MIDI time stamp (lane C's ctlMsg, wrapped the way other lanes wrap noteOn); a controller
   message on a fast-played track may change its sound: the note messages are worked out again soon */
{const _m=ctlMsg;ctlMsg=function(d,a){const o=LTF.from,mt=LT.miT;LTF.from=d;let ev=null;try{ev=window.event}catch(e){}
  LT.miT=ev&&ev.type==='midimessage'&&typeof ev.timeStamp==='number'&&ev.timeStamp>0?ev.timeStamp:null;
  try{if(LTF.tgt.size&&a&&(a[0]&0xf0)===0xB0&&a[1]!==64)ltFastSoon()}catch(e){}
  try{return _m.apply(this,arguments)}finally{LTF.from=o;LT.miT=mt}}}
/* the page does not start a voice the worklet already started: a note from a port the shell reads, on a track the worklet plays; the
   instrument's display and the pad still light up.
   The check sits outside every other voiceOn wrapper: several instruments add theirs while the app starts (after this script), and one of
   those that answers a key itself would play it again; ltFastWrap puts it back on the outside when a fast track is set up. */
function ltFastWrap(){if(voiceOn.__lt)return;const _v=voiceOn;voiceOn=function(t,p,v){const d=LTF.from;if(d&&t&&LTF.ins&&LTF.ins.has(d.name)&&LTF.allow.has(d.name)&&!LTF.blk.has(p+24)&&ctx===LTF.ctx){const o=LTF.tgt.get(t.id);
  if(o&&o.ack&&(!o.kit||o.pads.has(p-36))){LTF.skip++;if(ltFastSig(t)!==o.sig)ltFastSoon();
   try{slzWake(t)}catch(e){}try{if(o.kit){let h=PADHIT.get(t.inst);if(!h){h=new Float64Array(16).fill(-9);PADHIT.set(t.inst,h)}h[p-36]=ctx.currentTime}else hitMark(ctx,t.inst,ctx.currentTime,p,.3)}catch(e){}return null}}return _v.apply(this,arguments)};
 voiceOn.__lt=1;if(_v.__e)voiceOn.__e=1}
ltFastWrap();
{const _n=noteOn;noteOn=function(){const r=_n.apply(this,arguments);if(LTF.from&&!LTF.tgt.size)ltFastSoon();return r}}
LT_HOOKS.fastNotes=()=>({on:ltFastOK(),tracks:[...LTF.tgt].map(([id,o])=>({id,ready:!!o.ack,kind:o.kit?'kit':o.E[1],pads:o.kit?[...o.pads]:undefined})),page:[...LTF.why].map(([id,w])=>({id,why:w})),ports:[...LTF.allow],seen:LTF.ins?[...LTF.ins]:[],played:LTF.n,skipped:LTF.skip});
/* the Settings row (desktop only; lane B places it for good through LT_HOOKS.audioRows) */
if(window.audiolabLtMidi){const R={"id":"fastMidi","l":"Fast MIDI notes","pg":"audio","b":"Audio driver","sc":"app","k":"UI.ltFast","c":"#ltFmChk","t":"check","d":true,"h":"Notes from a MIDI keyboard go straight to the armed track's instrument, so they sound on time even while the screen is busy. Desktop app only.","w":"fast midi notes keyboard latency late busy worklet desktop push nanokey"};
 try{LT_ROWS.push(R);if(!STX.has(R.id)){STT.push(R);STX.set(R.id,R)}}catch(e){}
 {const oc=document.getElementById('ltOcChk'),row=oc&&oc.closest('label');if(row&&!document.getElementById('ltFmChk')){const l=document.createElement('label');l.className='chk';l.title=R.h;
   l.innerHTML='<input type="checkbox" id="ltFmChk"> Fast MIDI notes (a MIDI keyboard plays the armed track straight away, even while the screen is busy)';row.after(l);const c=l.querySelector('input');c.checked=UI.ltFast!==false;
   c.onchange=()=>{UI.ltFast=c.checked;try{saveUI()}catch(e){}ltFastEval()}}}}
/* ===== end of lane J LT-3a ===== */
"""
s=s[:a]+JS+s[b:]
assert s.count('task LT-3b (lane J)')==1
save('index.html',s)
print('LT-3b applied')
