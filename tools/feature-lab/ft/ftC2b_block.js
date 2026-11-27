/* v0.239 (task FT-C2b): Ableton Push 1, part 2: control. Outside Scales the 8 encoders move the selected device's parameters (8 at a time,
   names and values on the display; < and > page through banks, the Left and Right arrows pick the device, Up and Down the track), or the
   volume or pan of 8 tracks (Volume, Pan & Send; Device goes back). The upper row under the display selects tracks, the lower row arms them
   (Mute and Solo switch it to mute or solo; press again for arm). Transport: Play (Shift+Play: loop on or off), Record, Stop, Metronome,
   Tap tempo, the tempo encoder (one undo step per turn), the master encoder on the master level. Undo (Shift: redo), New (instrument track),
   Duplicate (the selected clip, else the track), Delete (the selected clip; held with a drum pad: clears that pad in the step lane),
   Quantize. A drum kit track selected: the lower left 4x4 pads are its 16 pads (pressing one selects it), the top two rows are a 16-step
   lane of the selected pad over the bar under the playhead (one undo step a press). A mapping learned on a Push control wins over all this.
   Event driven: nothing runs while still; while the song plays and a drum kit is on the pads, the lane follows the bar 4 times a second. */
const P1B={CC:{play:85,rec:86,stop:29,metro:9,tap:3,undo:119,neu:87,dup:88,del:118,quant:116,dev:110,vol:114,pan:115,mute:60,solo:61,pgL:62,pgR:63,left:44,right:45,up:46,down:47,shift:49},
  ROW1:20,ROW2:102,TEMPO:14,MASTER:79,iv:0};
window.P1B=P1B;
const p1b=d=>d.p1.b||(d.p1.b={em:'dev',lr:'arm',tb:0,dev:{},bk:{},shift:false,del:0,delUsed:false,tap:[],acc:{},undoT:0,undoK:'',dh:new Set(),sel:null});
const p1bA=s=>String(s==null?'':s).replace(/∞/g,'inf').replace(/[·•]/g,'.').replace(/[–—−]/g,'-').replace(/[^\x20-\x7E]/g,'');
const p1b8=a=>{const r=a.slice(0,8);while(r.length<8)r.push('');return r};
const p1bDrum=t=>!!(t&&t.kind==='inst'&&t.inst&&t.inst.preset==='drums');
const p1bDT=()=>{const t=curT();return p1bDrum(t)&&S.tracks.includes(t)?t:null};
/* the devices in the device panel of the selected track, each with its controls in panel order */
function p1bDevs(){const out=[],fx=document.getElementById('fxin');if(!fx)return out;
  for(const D of fx.querySelectorAll('.dev')){const ids=[...new Set([...D.querySelectorAll('[data-c^="fx:"]')].filter(e=>e.closest('.dev')===D).map(e=>e.dataset.c))].filter(id=>{const C=CT.get(id);return C&&C.spec&&C.get&&C.set});
    if(!ids.length)continue;const h=D.querySelector(':scope>.devh>span'),tr=D.classList.contains('tdev');out.push({name:tr?'Track':(h&&h.textContent.trim())||'Device',ids,tr})}return out}
function p1bParams(d){const b=p1b(d),devs=p1bDevs();if(!devs.length)return{devs,i:-1,bank:0,nb:0,ids:[]};
  let i=b.dev[selT];if(i==null){i=devs.findIndex(x=>!x.tr);if(i<0)i=0}i=clamp(i,0,devs.length-1);const nb=Math.ceil(devs[i].ids.length/8),bank=clamp(b.bk[selT+':'+i]|0,0,nb-1);
  return{devs,i,bank,nb,ids:devs[i].ids.slice(bank*8,bank*8+8)}}
const p1bRow=d=>{const b=p1b(d);return S.tracks.slice(b.tb,b.tb+8)};
/* one undo step for a run of turns of the same control (a pause of 1.5 s starts a new one) */
function p1bUndo(b,key){const now=performance.now();if(b.undoK!==key||now-b.undoT>1500)pushUndo();b.undoK=key;b.undoT=now}
function p1bNudge(d,id,dn){const C=CT.get(id);if(!C)return;const b=p1b(d),cur=C.spec.n(C.get());let r=b.acc[id];if(r==null||Math.abs(r-cur)>.02)r=cur;r=clamp(r+dn,0,1);b.acc[id]=r;
  p1bUndo(b,id);C.set(C.spec.v(r));ctlPaintId(id);if(C.after&&!document.querySelector(`[data-c="${CSS.escape(id)}"]`))try{C.after(C.get())}catch(e){}}
function p1bTempo(b,bpm){const n=UNDO.length,now=performance.now(),again=b.undoK==='bpm'&&now-b.undoT<1500;setBpm(bpm);if(again&&UNDO.length>n)UNDO.pop();b.undoK='bpm';b.undoT=now}
function p1bEnc(d,i,raw){const b=p1b(d),dl=raw<64?raw:raw-128,dn=dl/127*(b.shift?.1:1);
  if(b.em==='dev'){const id=p1bParams(d).ids[i];if(id)p1bNudge(d,id,dn)}else{const t=p1bRow(d)[i],id=t&&(b.em==='vol'?'hd:':'hp:')+t.id;if(id&&CT.has(id))p1bNudge(d,id,dn)}p1Disp(d)}
function p1bTap(b){const now=performance.now();if(b.tap.length&&now-b.tap[b.tap.length-1]>2000)b.tap=[];b.tap.push(now);if(b.tap.length>5)b.tap.shift();
  if(b.tap.length<2)return;const T=b.tap,avg=(T[T.length-1]-T[0])/(T.length-1);if(avg>0)p1bTempo(b,60000/avg)}
function p1bDelClip(){const f=selC&&findClip(selC);if(!f){toast('Select a clip, then press Delete on the Push to delete it.');return}pushUndo();f.t.clips=f.t.clips.filter(c=>c!==f.c);selC=null;changed(false);toast('Clip deleted. Undo on the Push, or Mod+Z.')}
function p1bDup(){const f=selC&&findClip(selC);if(f){SCM.get('dup').run();return}const t=curT();if(t&&S.tracks.includes(t)){dupTrack(t);toast('Track duplicated (no clip was selected).')}}
function p1bLower(b,t){if(b.lr==='arm'){if(t.kind!=='inst'&&t.kind!=='audio')return;armTrack(t).then(()=>p1All(),()=>{});return}pushUndo();t[b.lr]=!t[b.lr];changed(true)}
/* the drum kit's step lane: 16 steps of the selected pad over the bar under the playhead */
function p1bLane(t){const pd=36+(t.inst.psel|0),B=Math.floor(Math.max(0,play.on?curDisp():pos)/4)*4,c=t.clips.find(c=>c.notes&&c.start<=B+1e-6&&B<c.start+c.len-1e-6)||null,on=Array(16).fill(false);
  if(c)for(const n of c.notes){if(n.p!==pd)continue;const x=(c.start+n.s-(c.off||0)-B)*4,k=Math.round(x);if(k>=0&&k<16&&Math.abs(x-k)<.26)on[k]=true}return{B,c,pd,on}}
function p1bStep(t,k){const L=p1bLane(t);pushUndo();let c=L.c;if(!c){c=mkClip({start:L.B,len:4,name:t.name,notes:[]});t.clips.push(c)}const rel=L.B+k/4-c.start+(c.off||0);
  if(L.on[k])c.notes=c.notes.filter(n=>!(n.p===L.pd&&Math.abs(n.s-rel)<.13));else{c.notes.push({p:L.pd,s:rel,l:.25,v:.8});c.notes.sort((a,b)=>a.s-b.s);if(L.B+4>c.start+c.len)c.len=L.B+4-c.start}changed(false)}
function p1bClear(t,i){const L=p1bLane({inst:{psel:i},clips:t.clips});if(!L.c||!L.on.some(Boolean))return;pushUndo();const c=L.c,a=L.B-c.start+(c.off||0);c.notes=c.notes.filter(n=>!(n.p===L.pd&&n.s>=a-.13&&n.s<a+4-.13));changed(false)}
function p1bDOn(t,p,v){const key='p1d:'+p;if(LIVE.has(key))return;const hs=[{t,h:voiceOn(t,p,v)}],b=play.on&&!play.counting?curDisp():null;LIVE.set(key,{p,v,hs,b});flashArm()}
function p1bPads(d,t){const st=d.p1,b=p1b(d),I=t.inst;ensurePads(I);const tc=p1Col(t.color),L=p1bLane(t),ps=I.psel|0;
  for(let y=0;y<8;y++)for(let x=0;x<8;x++){const n=36+y*8+x;let c=0;
    if(x<4&&y<4){const i=y*4+x,pd=I.pads[i];c=b.dh.has(i)?21:i===ps?3:pd&&pd.mute?1:tc}else if(y>=6){const k=(7-y)*8+x;c=L.on[k]?tc:k%4===0?2:1}
    if(st.led.get(n)!==c){st.led.set(n,c);p1Send(d,[0x90,n,c])}}}
function p1bPad(d,a){const st=d.p1,b=p1b(d),t=p1bDT(),c=a[0]&0xf0,x=(a[1]-36)%8,y=(a[1]-36)>>3,o=p1S();if(!t)return;
  if(c===0x90&&a[2]>0){if(x<4&&y<4){const i=y*4+x;if(b.del){p1bClear(t,i);b.delUsed=true}else{if((t.inst.psel|0)!==i){t.inst.psel=i;renderFx()}b.dh.add(i);p1bDOn(t,36+i,p1Vel(a[2],o))}}
    else if(y>=6)p1bStep(t,(7-y)*8+x)}
  else if(x<4&&y<4){const i=y*4+x;b.dh.delete(i);noteOff('p1d:'+(36+i))}
  p1Pads(d);p1Disp(d)}
/* the display outside Scales */
function p1bDisp(d){const b=p1b(d),T=S.tracks;if(selT!==b.sel){b.sel=selT;const k=T.findIndex(t=>t.id===selT);if(k>=0&&(k<b.tb||k>=b.tb+8))b.tb=Math.floor(k/8)*8}
  const row=p1bRow(d),t=curT(),nm=(x,m)=>(m&&x.id===selT?'>':'')+p1bA(x.name),o=p1S(),dt=p1bDT();
  if(b.em==='dev'){const P=p1bParams(d);
    if(P.i<0){p1Line(d,0,p1Cell(['No devices shown','','','']));p1Line(d,1,p1Cell(['Show the devices','panel in AudioLab','','']))}
    else{p1Line(d,0,p1Cell8(p1b8(P.ids.map(id=>p1bA(CT.get(id).label)))));p1Line(d,1,p1Cell8(p1b8(P.ids.map(id=>{const C=CT.get(id);return p1bA(C.spec.f(C.get()))}))))}
    const dv=P.devs[P.i],info=dt?'Pad '+((dt.inst.psel|0)+1)+' '+p1bA((dt.inst.pads||[])[dt.inst.psel|0]&&dt.inst.pads[dt.inst.psel|0].name):P1.NN[PR.root|0]+' '+PR.scale.replace('harmonic ','harm ').replace('pentatonic','pent')+', Oct '+o.oct;
    p1Line(d,2,p1Cell([t?p1bA(t.name):'No track',dv?(x=>p1bA(dv.name).slice(0,15-x.length)+' '+x)((P.i+1)+'/'+P.devs.length):'',P.nb>1?'Bank '+(P.bank+1)+' of '+P.nb:'',info]));
    p1Line(d,3,p1Cell8(p1b8(row.map(x=>nm(x,1)))));return}
  p1Line(d,0,p1Cell8(p1b8(row.map(x=>nm(x,0)))));
  p1Line(d,1,p1Cell8(p1b8(row.map(x=>{const C=CT.get((b.em==='vol'?'hd:':'hp:')+x.id);return C?p1bA(C.spec.f(C.get())):''}))));
  p1Line(d,2,p1Cell([b.em==='vol'?'Volume':'Pan','Tracks '+(b.tb+1)+'-'+(b.tb+row.length)+' of '+T.length,'Lower row: '+({arm:'Arm',mute:'Mute',solo:'Solo'})[b.lr],'Device: back']));
  p1Line(d,3,p1Cell8(p1b8(row.map(x=>nm(x,1)))))}
/* buttons: what they do and how they are lit (Push 1 button LEDs: 0 off, 1 dim, 4 lit; the two rows under the display take colours) */
function p1bCc(d,n,v){const b=p1b(d),C=P1B.CC,on=v>0;
  if(n===C.shift){b.shift=on;p1Btns(d);return true}
  if(P1.ENC.includes(n)){p1bEnc(d,P1.ENC.indexOf(n),v);return true}
  if(n===P1B.TEMPO){const dl=v<64?v:v-128;if(dl)p1bTempo(b,S.bpm+Math.sign(dl));p1Disp(d);return true}
  if(n===P1B.MASTER){const dl=v<64?v:v-128;p1bNudge(d,'ms',dl/127*(b.shift?.1:1));return true}
  if(n>=P1B.ROW1&&n<P1B.ROW1+8){if(on){const t=S.tracks[b.tb+n-P1B.ROW1];if(t)selectTrack(t.id)}return true}
  if(n>=P1B.ROW2&&n<P1B.ROW2+8){if(on){const t=S.tracks[b.tb+n-P1B.ROW2];if(t)p1bLower(b,t)}return true}
  if(n===C.del){if(on){b.del=1;b.delUsed=false}else{b.del=0;if(!b.delUsed)p1bDelClip()}return true}
  if(!Object.values(C).includes(n))return false;if(!on)return true;
  const run=id=>{const a=SCM.get(id);if(a)a.run()},sh=b.shift,devs=()=>p1bParams(d);
  if(n===C.play){if(sh)run('loop');else toggle()}else if(n===C.rec)run('rec');else if(n===C.stop)run('stop');else if(n===C.metro)run('click');else if(n===C.tap)p1bTap(b);
  else if(n===C.undo){if(sh)redo();else undo()}else if(n===C.neu)run('newmidi');else if(n===C.dup)p1bDup();else if(n===C.quant)run('quant');
  else if(n===C.dev)b.em='dev';else if(n===C.vol)b.em='vol';else if(n===C.pan)b.em='pan';else if(n===C.mute||n===C.solo){const k=n===C.mute?'mute':'solo';b.lr=b.lr===k?'arm':k}
  else if(n===C.pgL||n===C.pgR){const dir=n===C.pgR?1:-1;if(b.em==='dev'){const P=devs();if(P.i>=0)b.bk[selT+':'+P.i]=clamp(P.bank+dir,0,P.nb-1)}else b.tb=clamp(b.tb+8*dir,0,Math.max(0,Math.floor((S.tracks.length-1)/8)*8))}
  else if(n===C.left||n===C.right){const P=devs();if(P.i>=0)b.dev[selT]=clamp(P.i+(n===C.right?1:-1),0,P.devs.length-1)}
  else if(n===C.up||n===C.down){const k=S.tracks.findIndex(t=>t.id===selT),t=S.tracks[clamp(k+(n===C.down?1:-1),0,S.tracks.length-1)];if(t&&t.id!==selT)selectTrack(t.id)}
  p1All();return true}
function p1bBtns(d){const st=d.p1,b=p1b(d),C=P1B.CC,set=(cc,v)=>{if(st.btn.get(cc)!==v){st.btn.set(cc,v);p1Send(d,[0xB0,cc,v])}};
  set(C.play,play.on?4:1);set(C.rec,REC.on?4:1);set(C.metro,S.click?4:1);for(const k of['stop','tap','undo','neu','dup','del','quant','up','down','left','right'])set(C[k],1);set(C.shift,b.shift?4:1);
  set(C.dev,b.em==='dev'?4:1);set(C.vol,b.em==='vol'?4:1);set(C.pan,b.em==='pan'?4:1);set(C.mute,b.lr==='mute'?4:1);set(C.solo,b.lr==='solo'?4:1);
  if(b.em==='dev'){const P=p1bParams(d);set(C.pgL,P.bank>0?4:0);set(C.pgR,P.bank<P.nb-1?4:0)}else{set(C.pgL,b.tb>0?4:0);set(C.pgR,b.tb+8<S.tracks.length?4:0)}
  const row=p1bRow(d);for(let i=0;i<8;i++){const t=row[i];set(P1B.ROW1+i,!t?0:t.id===selT?10:7);
    set(P1B.ROW2+i,!t?0:b.lr==='arm'?(t.kind==='inst'||t.kind==='audio'?(t.arm?5:7):0):b.lr==='mute'?(t.mute?13:15):(t.solo?45:47))}}
/* the C2a painters and the Push's message handler grow the new parts (a re-run after a rebase wraps them once) */
{const _d=p1Disp;p1Disp=function(d){if(!d||!d.p1)return;if(d.p1.scales)return _d.apply(this,arguments);p1bDisp(d)}}
{const _p=p1Pads;p1Pads=function(d){if(!d||!d.p1)return;const t=p1bDT();if(t&&!d.p1.scales)return p1bPads(d,t);return _p.apply(this,arguments)}}
{const _b=p1Btns;p1Btns=function(d){const r=_b.apply(this,arguments);if(d&&d.p1)p1bBtns(d);return r}}
{const pf=CTL.profs.find(p=>p.id==='push1'),_m=pf.msg;pf.msg=function(d,a){const st=d.p1,s=a[0],c=s&0xf0;if(!st||s>=0xF0||ML.on)return _m.apply(this,arguments);
  if(c===0xB0){const n=a[1];if(st.scales&&P1.ENC.includes(n))return _m.apply(this,arguments);if([P1.CC.scales,P1.CC.oct_up,P1.CC.oct_dn,P1.CC.note].includes(n))return _m.apply(this,arguments);
    const ms=ctlIndex().byM.get(ctlKey('cc',s&15,n));if(ms&&ms.some(m=>m.dev==='*'||m.dev===d.name))return _m.apply(this,arguments);/* a learned mapping wins */
    if(p1bCc(d,n,a[2]))return;return _m.apply(this,arguments)}
  if((c===0x90||c===0x80)&&a[1]>=36&&a[1]<=99&&!st.scales&&p1bDT())return p1bPad(d,a);
  return _m.apply(this,arguments)}}
/* transport changes light Play and Record; while the song plays the drum lane follows the bar (4 times a second, only then) */
const p1bAny=()=>{for(const d of CTL.devs.values())if(d.prof&&d.prof.id==='push1'&&d.p1&&!ctlOff(d))return true;return false};
{const _s=start;start=function(){const r=_s.apply(this,arguments);try{if(p1bAny()){p1All();if(!P1B.iv)P1B.iv=setInterval(()=>{if(!play.on||!p1bAny()){clearInterval(P1B.iv);P1B.iv=0;return}if(p1bDT())p1All()},250)}}catch(e){}return r}}
{const _t=stop;stop=function(){const r=_t.apply(this,arguments);try{if(p1bAny())p1All()}catch(e){}return r}}
{const _u=undo,_r=redo;undo=function(){const r=_u.apply(this,arguments);try{if(p1bAny())p1All()}catch(e){}return r};redo=function(){const r=_r.apply(this,arguments);try{if(p1bAny())p1All()}catch(e){}return r}}
/* a short guide under the Push 1 settings on the Controllers page */
{const _p=ctlPagePaint;ctlPagePaint=function(){const r=_p.apply(this,arguments);const w=CTL.host&&CTL.host.querySelector('.p1set');if(w&&!w.querySelector('.p1help')){const h=document.createElement('div');h.className='cnone p1help';
  h.title='What the buttons on your Push 1 do in AudioLab';h.textContent='On the Push: Device, Volume and Pan & Send pick what the 8 knobs move; < and > page through them; the arrows pick the device and the track. Upper row: select a track; lower row: arm (Mute and Solo switch it). Shift+Play: loop. Shift+Undo: redo. A drum kit track: the lower left pads play its 16 pads, the top two rows are 16 steps of the chosen pad.';w.appendChild(h)}return r}}
