/* v0.253 (task FT-C3c): Novation Launchpad (Mini MK3, X, Pro MK3) and Akai APC (APC40 MK2, APC mini, APC mini mk2) as section launchers.
   The grid shows 8 tracks across (one track bank shared by these controllers) and the song's sections down (8 rows; 5 on the APC40), as the
   Push's Session mode does: a pad is lit in the track's colour when that track plays something in the section, green in the section playing,
   white and pulsing in the one queued. Pads and the scene buttons on the right launch sections through the Push's launcher (FT_HOOKS.push1Launch,
   the Launch setting: next bar, end of the section, at once; Shift: at once), so no new audio path. Launchpads: programmer mode (hello) and
   back to Live mode (goodbye); the arrows move the grid; Session, and Keys or Note (the pads as a note grid in the project key, Push 1's
   layout settings) and Drums (a 4x4 drum kit) where the Launchpad has those buttons. APCs: faders on the levels of the 8 tracks shown (master
   fader on the master) with the takeover setting (pick up, scale, jump; they have no motors), track buttons select the track; Shift with the
   track buttons: arrows, faders on volume, pan or the selected device. APC40 MK2: Ableton mode, track buttons (arm, solo, activator as mute,
   select), device knobs on the selected device and track knobs on pan with their LED rings, Play, Stop, Record, Metronome, Stop all clips,
   the tempo knob. Clips come with the clip launcher (F8, step FT-C2d). Event driven: sent only on change, a check 4 times a second only
   while the song plays with one of these connected. Bytes: Novation's Launchpad Mini [MK3] programmer's reference and Akai's APC40 Mk2
   communications protocol v1.2; APC mini numbers as used by the open-source scripts; to be confirmed on real devices (FT-C3c log). */
const LPG={tb:0,iv:0,key:'',soonT:0,undoK:'',undoT:0,n:{pad:0,hello:0},
  M:{lpm3:{name:'Launchpad Mini MK3',lp:1,id:0x0D,re:/lpminimk3|launchpad\s*mini\s*mk\s*3/i,rows:8,top:{up:91,down:92,left:93,right:94,ses:95,drums:96,keys:97}},
     lpx:{name:'Launchpad X',lp:1,id:0x0C,re:/\blpx\b|launchpad\s*x\b/i,rows:8,top:{up:91,down:92,left:93,right:94,ses:95,keys:96}},
     lpp3:{name:'Launchpad Pro MK3',lp:1,id:0x0E,re:/lpprom?k3|launchpad\s*pro\s*mk\s*3/i,rows:8,top:{left:91,right:92,ses:93,keys:94},shift:90},
     apc40:{name:'APC40 MK2',apc:1,re:/apc\s*40\s*mk\s*(ii|2)/i,rows:5,scene:82,shift:98,solid:0,pulse:9,rgb:1},
     apcm2:{name:'APC mini mk2',apc:1,re:/apc\s*mini\s*mk\s*(ii|2)/i,rows:8,scene:112,trk:100,shift:122,fader:48,solid:6,pulse:9,rgb:1},
     apcm:{name:'APC mini',apc:1,re:/apc\s*mini(?!\s*mk\s*(ii|2))/i,rows:8,scene:82,trk:64,shift:98,fader:48,rgb:0}},
  AP:{play:91,stop:92,rec:93,click:90,up:94,down:95,right:96,left:97,stopAll:81}};
window.LPG=LPG;
const lpModel=d=>{const a=UI.ctlAs&&UI.ctlAs[d.name];if(a)return LPG.M[a]?a:null;const n=String(d.name||'');if(/\bDAW\b|\bDIN\b|notes|apc\s*key/i.test(n))return null;
  for(const k in LPG.M){const M=LPG.M[k];if(!M.re.test(n))continue;if(M.apc&&/^MIDIIN\d/i.test(n))return null;
    /* Windows names a Launchpad's second interface (the MIDI one, where programmer mode lives) "MIDIIN2 (...)": prefer it to its plain twin */
    if(M.lp&&!/^MIDIIN\d/i.test(n)&&[...CTL.devs.values()].some(x=>x!==d&&/^MIDIIN\d/i.test(x.name)&&x.base===d.base&&!/\bDAW\b/i.test(x.name)))return null;return k}return null};
const lpDevs=()=>[...CTL.devs.values()].filter(d=>d.g&&d.prof&&d.prof.id==='grid'&&!ctlOff(d));
const lpRow=()=>S.tracks.slice(LPG.tb,LPG.tb+8);
const lpMaxTb=()=>Math.max(0,S.tracks.length-8);
/* pads: (x, r) with r the row from the top; and back */
function lpNote(M,x,r){if(M.lp)return 11+(M.rows-1-r)*10+x;return(M.rows-1-r)*8+x}
function lpXY(M,n){if(M.lp){const y=Math.floor(n/10)-1,x=n%10-1;if(x<0||x>7||y<0||y>7)return null;return[x,M.rows-1-y]}if(n<0||n>=M.rows*8)return null;return[n%8,M.rows-1-(n>>3)]}
const lpSceneCC=(M,r)=>M.lp?89-r*10:null;
/* out: every LED is a key; a message goes out only when its value changes */
function lpOut(d,k,bytes){const v=bytes.join(',');if(d.g.out.get(k)===v)return;d.g.out.set(k,v);if(ctlSend(d,bytes))LPG.n.pad++}
/* one lit pad or RGB button: c is a palette index (0 off, 3 white, 21 green, p1Col of a track colour), pulse for the queued */
function lpPadLed(d,n,c,pulse,cc){const M=d.g.M;if(M.lp){lpOut(d,(cc?'c':'n')+n,[(cc?0xB0:0x90)|(pulse&&c?2:0),n,c]);return}
  if(M.rgb){lpOut(d,'n'+n,[0x90|(pulse&&c?M.pulse:M.solid),n,c]);return}
  /* APC mini: green, red, yellow (1, 3, 5; one more blinks) */
  const v=!c?0:c===21?1:c===3?(pulse?6:5):3;lpOut(d,'n'+n,[0x90,n,pulse&&c&&v!==6?v+1:v])}
/* single colour buttons: 0 off, 1 on, 2 blink */
const lpBtn=(d,n,v,ch)=>lpOut(d,'b'+(ch|0)+':'+n,[0x90|(ch|0),n,v]);
/* ---- what the grid shows ---- */
function lpPaint(d){if(!d||!d.g||ctlOff(d))return;try{const g=d.g,M=g.M;if(g.mode==='keys'||g.mode==='drums')lpNotePads(d);else lpSesPads(d);lpSide(d)}catch(e){console.error('AudioLab grid '+d.name,e)}}
function lpSesPads(d){const g=d.g,M=g.M,row=lpRow(),ss=p1cSecs(),so=g.so|0,cur=p1cCur(),q=P1C.q;
  for(let r=0;r<M.rows;r++){const s=ss[so+r],isQ=!!(s&&q&&q.id===s.id),isC=!!(s&&play.on&&cur&&cur.id===s.id);
    for(let x=0;x<8;x++){const t=row[x];let c=0;if(s&&t&&p1cHas(t,s))c=isQ?3:isC?21:p1Col(t.color);lpPadLed(d,lpNote(M,x,r),c,isQ)}
    if(M.lp)lpPadLed(d,lpSceneCC(M,r),!s?0:isQ?3:isC?21:1,isQ,true);else lpBtn(d,M.scene+r,!s?0:isQ?2:isC?1:0)}}
function lpNotePads(d){const g=d.g,M=g.M,o=p1S(),t=p1Track()[0],tc=p1Col(t&&t.color);
  for(let r=0;r<8;r++)for(let x=0;x<8;x++){const y=7-r;let c;if(g.mode==='drums'){const k=y*4+x;c=x<4&&y<4?(g.held.has(60+k)?21:t?tc:1):0}else c=p1PadCol(x,y,o,g.held,tc);lpPadLed(d,lpNote(M,x,r),c,false)}
  for(let r=0;r<8;r++)lpPadLed(d,lpSceneCC(M,r),0,false,true)}
function lpSide(d){const g=d.g,M=g.M,T=M.top,row=lpRow(),ss=p1cSecs();
  if(M.lp){const mv=(k,can)=>{if(T[k]!=null)lpPadLed(d,T[k],g.mode!=='ses'?0:can?3:1,false,true)};
    mv('up',(g.so|0)>0);mv('down',(g.so|0)+M.rows<ss.length);mv('left',LPG.tb>0);mv('right',LPG.tb<lpMaxTb());
    if(T.ses!=null)lpPadLed(d,T.ses,g.mode==='ses'?21:1,false,true);if(T.keys!=null)lpPadLed(d,T.keys,g.mode==='keys'?21:1,false,true);if(T.drums!=null)lpPadLed(d,T.drums,g.mode==='drums'?21:1,false,true);return}
  if(M.trk!=null)for(let i=0;i<8;i++){const t=row[i];lpBtn(d,M.trk+i,g.shift?(i<4?1:((i===4&&g.fm==='vol')||(i===5&&g.fm==='pan')||(i===7&&g.fm==='dev'))?1:0):t&&t.id===selT?1:0)}
  if(d.g.mk==='apc40'){const A=LPG.AP;for(let i=0;i<8;i++){const t=row[i];lpBtn(d,0x30,t&&t.arm?1:0,i);lpBtn(d,0x31,t&&t.solo?1:0,i);lpBtn(d,0x32,t&&!t.mute?1:0,i);lpBtn(d,0x33,t&&t.id===selT?1:0,i);lpBtn(d,0x34,0,i)}
    lpBtn(d,A.play,play.on?1:0);lpBtn(d,A.rec,REC.on?1:0);lpBtn(d,A.click,S.click?1:0);
    /* LED rings: device knobs show the selected device, track knobs the pans */
    const P=ctlTDev();for(let i=0;i<8;i++){const id=P.ids[i],tp=row[i]&&'hp:'+row[i].id;
      lpOut(d,'rt'+i,[0xB0,0x18+i,id?1:0]);lpOut(d,'rv'+i,[0xB0,0x10+i,id?Math.round(clamp(mcN(id)||0,0,1)*127):0]);
      lpOut(d,'pt'+i,[0xB0,0x38+i,tp&&CT.has(tp)?3:0]);lpOut(d,'pv'+i,[0xB0,0x30+i,tp&&CT.has(tp)?Math.round(clamp(mcN(tp)||0,0,1)*127):0])}}}
function lpAll(){for(const d of lpDevs())lpPaint(d)}
function lpSoon(){if(LPG.soonT||!lpDevs().length)return;LPG.soonT=setTimeout(()=>{LPG.soonT=0;lpAll()},33)}
/* while the song plays: follow the section under the playhead and the queue (4 times a second, only then) */
function lpFollow(){if(LPG.iv||!play.on||!lpDevs().length)return;LPG.key='';LPG.iv=setInterval(()=>{if(!play.on||!lpDevs().length){clearInterval(LPG.iv);LPG.iv=0;lpSoon();return}
  const c=p1cCur(),k=(c?c.id:'')+':'+(P1C.q?P1C.q.id:'');if(k!==LPG.key){LPG.key=k;lpAll()}},250)}
/* ---- faders and absolute knobs: no motors, so the takeover setting decides when they catch the value ---- */
function lpAbs(d,slot,id,v){if(!id||!CT.has(id))return;const g=d.g,tk=UI.ctlTake||'pickup',cur=mcN(id);let st=g.ft[slot];if(!st||st.id!==id)st=g.ft[slot]={id,ok:false,last:null,set:null};
  if(st.set!=null&&Math.abs(cur-st.set)>.004)st.ok=false;let n=null;
  if(tk==='jump'||st.ok)n=v;
  else if(tk==='scale'){if(st.last==null)n=null;else if(v>st.last)n=cur+(v-st.last)*(1-cur)/Math.max(1e-6,1-st.last);else if(v<st.last)n=cur-(st.last-v)*cur/Math.max(1e-6,st.last);if(n!=null&&Math.abs(n-v)<.01){st.ok=true;n=v}}
  else if(Math.abs(v-cur)<=1.5/127||(st.last!=null&&(st.last-cur)*(v-cur)<=0)){st.ok=true;n=v}
  st.last=v;if(n==null)return;n=clamp(n,0,1);mcSet(id,n,'g'+id);st.set=mcN(id);lpSoon()}
function lpFaderId(d,i){const g=d.g;if(i===8)return'ms';if(g.fm==='dev')return ctlTDev().ids[i]||null;const t=lpRow()[i];return t?(g.fm==='pan'?'hp:':'hd:')+t.id:null}
/* ---- moving the grid ---- */
function lpMove(d,k,big){const g=d.g,M=g.M,st=big?M.rows:1,tst=big?8:1;
  if(k==='up'||k==='down')g.so=clamp((g.so|0)+(k==='down'?st:-st),0,Math.max(0,p1cSecs().length-M.rows));
  else{LPG.tb=clamp(LPG.tb+(k==='right'?tst:-tst),0,lpMaxTb());toast('Grid: tracks '+(LPG.tb+1)+' to '+Math.min(S.tracks.length,LPG.tb+8)+'.')}lpAll()}
function lpLaunchRow(d,r){const s=p1cSecs()[(d.g.so|0)+r];if(s)p1cLaunch(s,!!d.g.shift);lpSoon()}
const lpRun=id=>{const a=SCM.get(id);if(a)a.run();lpSoon()};
function lpTrackBtn(k,t){if(!t)return;if(k==='sel'){selectTrack(t.id);return}if(k==='arm'){if(t.kind!=='inst'&&t.kind!=='audio')return;armTrack(t).then(()=>lpSoon(),()=>{});return}pushUndo();t[k]=!t[k];changed(true)}
/* ---- messages ---- */
const lpMine=(d,type,ch,num)=>{const ms=ctlIndex().byM.get(ctlKey(type,ch,num));return!!(ms&&ms.some(m=>m.dev===d.name))};
function lpMsg(d,a){const g=d.g,s=a[0],c=s&0xf0,ch=s&15;if(!g||s>=0xF0)return;const M=g.M,on=(c===0x90||c===0xB0)&&a[2]>0,type=c===0xB0?'cc':c===0xE0?'pb':'note';
  if(c===0x90||c===0x80||c===0xB0||c===0xE0){if(ML.on||CTL.relearn||lpMine(d,type,ch,c===0xE0?0:a[1])){if(c===0x80||(c===0x90&&!a[2]))return;ctlIn(d,type,ch,c===0xE0?0:a[1],c===0xE0?(a[2]<<7)|a[1]:a[2]);return}}
  const n=a[1];
  if(M.shift!=null&&((M.lp&&c===0xB0&&n===M.shift)||(!M.lp&&(c===0x90||c===0x80)&&n===M.shift))){g.shift=on;if(M.trk!=null)lpSide(d);return}
  if(M.lp){
    if(c===0x90||c===0x80||c===0xA0){const xy=lpXY(M,n);if(!xy||c===0xA0)return;const[x,r]=xy,y=7-r;
      if(g.mode==='keys'||g.mode==='drums'){let m;if(g.mode==='drums'){if(x>3||y>3)return;m=60+y*4+x}else{const p=p1Pad(x,y,p1S());if(p.m<0||p.m>127)return;m=p.m}
        if(on){g.held.add(m);p1On(m,p1Vel(a[2],p1S()))}else{g.held.delete(m);noteOff('p1:'+m)}lpNotePads(d);return}
      if(!on)return;const t=lpRow()[x];if(t&&t.id!==selT)selectTrack(t.id);lpLaunchRow(d,r);return}
    if(c===0xB0){if(!on)return;const T=M.top;
      if(n%10===9&&n>=19&&n<=89){if(g.mode==='ses')lpLaunchRow(d,(89-n)/10);return}
      for(const k of['up','down','left','right'])if(T[k]===n){if(g.mode==='ses')lpMove(d,k,!!g.shift);return}
      for(const k of['ses','keys','drums'])if(T[k]===n){lpModeSet(d,k);return}}
    return}
  /* APC */
  if(c===0xB0){const v=a[2]/127;
    if(d.g.mk==='apc40'){if(n===7&&ch<8){lpAbs(d,'f'+ch,lpFaderId(d,ch),v);return}if(n===14){lpAbs(d,'f8','ms',v);return}
      if(n>=0x10&&n<0x18){lpAbs(d,'k'+(n-0x10),ctlTDev().ids[n-0x10]||null,v);return}
      if(n>=0x30&&n<0x38){const t=lpRow()[n-0x30];lpAbs(d,'p'+(n-0x30),t?'hp:'+t.id:null,v);return}
      if(n===13){const dl=a[2]<64?a[2]:a[2]-128;if(dl)p1bTempo(LPG,Math.round((S.bpm+Math.sign(dl)*(g.shift?.1:1))*10)/10);return}return}
    if(M.fader!=null&&n>=M.fader&&n<=M.fader+8){const i=n-M.fader;lpAbs(d,'f'+i,lpFaderId(d,i),v);return}return}
  if(c!==0x90&&c!==0x80)return;
  if(!on){return}
  if(n<M.rows*8&&!(d.g.mk==='apc40'&&ch)){const[x,r]=lpXY(M,n),t=lpRow()[x];if(t&&t.id!==selT)selectTrack(t.id);lpLaunchRow(d,r);return}
  if(M.scene!=null&&n>=M.scene&&n<M.scene+M.rows){lpLaunchRow(d,n-M.scene);return}
  if(M.trk!=null&&n>=M.trk&&n<M.trk+8){const i=n-M.trk;if(g.shift){if(i<4)lpMove(d,['up','down','left','right'][i],false);else if(i===4||i===5||i===7){g.fm=i===4?'vol':i===5?'pan':'dev';g.ft={};toast(g.fm==='dev'?'Faders: the selected device.':g.fm==='pan'?'Faders: pan.':'Faders: volume.');lpSide(d)}return}lpTrackBtn('sel',lpRow()[i]);return}
  if(d.g.mk==='apc40'){const A=LPG.AP,t=lpRow()[ch];
    if(n>=0x30&&n<=0x34){if(n===0x30)lpTrackBtn('arm',t);else if(n===0x31)lpTrackBtn('solo',t);else if(n===0x32)lpTrackBtn('mute',t);else if(n===0x33)lpTrackBtn('sel',t);return}
    if(n===A.play){lpRun('play');return}if(n===A.stop||n===A.stopAll){if(play.on)lpRun('stop');else{pos=0;dirty=true}return}if(n===A.rec){lpRun('rec');return}if(n===A.click){lpRun('click');return}
    if(n===A.up||n===A.down||n===A.left||n===A.right){lpMove(d,n===A.up?'up':n===A.down?'down':n===A.left?'left':'right',!!g.shift);return}}}
function lpModeSet(d,k){const g=d.g;if(g.mode===k&&k!=='ses')k='ses';for(const m of[...g.held])noteOff('p1:'+m);g.held.clear();g.mode=k;
  if(k!=='ses'&&!p1Track().length)toast('Select or arm an instrument track to play the pads.');lpPaint(d)}
/* ---- hello and goodbye ---- */
function lpPair(d){if(!CTL.acc)return;const want=String(d.name).replace(/^MIDIIN(\d*)/i,'MIDIOUT$1').replace(/\bIn\b/,'Out'),outs=[...CTL.acc.outputs.values()].filter(o=>o.state!=='disconnected');
  const o=outs.find(o=>o.name===want)||outs.find(o=>o.name===d.name);if(o)d.out=o}
function lpHello(d){const M=d.g.M;LPG.n.hello++;if(M.lp){if(CTL.sysex)ctlSend(d,[0xF0,0,0x20,0x29,2,M.id,0x0E,1,0xF7]);else toast(M.name+': allow SysEx (full MIDI access) so AudioLab can put it in programmer mode.')}
  else if(d.g.mk==='apc40'&&CTL.sysex)ctlSend(d,[0xF0,0x47,0x7F,0x29,0x60,0,4,0x41,0,0,0,0xF7]);/* Ableton Live mode: the host lights everything */}
function lpBye(d,gone){if(!d.g)return;const raw=a=>{if(!d.out||(a[0]===0xF0&&!CTL.sysex))return;try{d.out.send(a);CTL.n.out++}catch(e){}};const M=d.g.M;
  for(const m of[...d.g.held])noteOff('p1:'+m);d.g.held.clear();
  if(!gone){for(const[k,v]of d.g.out){const b=v.split(',').map(Number);if(k[0]==='r'||k[0]==='p'){raw([b[0],b[1],0]);continue}raw([b[0]&0xF0,b[1],0])}
    if(M.lp)raw([0xF0,0,0x20,0x29,2,M.id,0x0E,0,0xF7])}d.g.out.clear()}
ctlProf({id:'grid',name:'Launchpad or APC',match:d=>!!lpModel(d),
  attach(d){const mk=lpModel(d),M=LPG.M[mk];lpPair(d);d.g={mk,M,so:0,mode:'ses',shift:false,fm:'vol',held:new Set(),ft:{},out:new Map()};lpHello(d);lpPaint(d);if(play.on)lpFollow()},
  detach(d,gone){lpBye(d,gone)},bye(d){lpBye(d)},msg:lpMsg});
/* a Launchpad's twin port on Windows: look again once every port is known */
{const _s=ctlScan;ctlScan=function(){const r=_s.apply(this,arguments);try{for(const d of CTL.devs.values())if(Object.values(LPG.M).some(M=>M.lp&&M.re.test(d.name)))ctlAttach(d,true)}catch(e){}return r}}
/* repaint when the song, the selection, the queue or a control changes */
{const _l=p1cLaunch;p1cLaunch=function(){const r=_l.apply(this,arguments);try{lpSoon()}catch(e){}return r}}
{const _j=p1cJump;p1cJump=function(){const r=_j.apply(this,arguments);try{lpSoon()}catch(e){}return r}}
{const _s=start;start=function(){const r=_s.apply(this,arguments);try{if(lpDevs().length){lpFollow();lpSoon()}}catch(e){}return r}}
{const _t=stop;stop=function(){const r=_t.apply(this,arguments);try{lpSoon()}catch(e){}return r}}
{const _s=selectTrack;selectTrack=function(){const r=_s.apply(this,arguments);try{lpSoon()}catch(e){}return r}}
{const _c=changed;changed=function(){const r=_c.apply(this,arguments);try{lpSoon()}catch(e){}return r}}
{const _p=paintCtl;paintCtl=function(el){const r=_p.apply(this,arguments);try{if(!LPG.soonT&&el&&el.dataset&&CTL.devs.size&&/^(hd:|hp:|ms$|fx:)/.test(el.dataset.c||'')&&lpDevs().length)lpSoon()}catch(e){}return r}}
/* the Controllers page: these models under Works as, and a line on what the grid does */
{const _p=ctlPagePaint;ctlPagePaint=function(){const r=_p.apply(this,arguments);const b=CTL.host;if(!b||!b.isConnected||b.closest('[hidden]'))return r;
  for(const sel of b.querySelectorAll('select[data-mc="as"]')){if(sel.querySelector('[data-lp]'))continue;const dn=sel.closest('[data-d]').dataset.d,a=UI.ctlAs&&UI.ctlAs[dn]||'';
    for(const k in LPG.M){const o=document.createElement('option');o.value=k;o.dataset.lp=1;o.textContent=LPG.M[k].name;if(a===k)o.selected=true;sel.appendChild(o)}
    sel.title+=' Launchpad and APC: a grid that launches the song’s sections.'}
  if(lpDevs().length&&!b.querySelector('.lpinfo')){const at=b.querySelector('.mcset .cmtpi')||null,w=document.createElement('div');w.className='cmtpi lpinfo';w.title='What a Launchpad or APC does in AudioLab';
    w.textContent='Launchpad and APC: 8 tracks across, the song’s sections down. A lit pad: that track plays in that section (green: playing, white: queued). Pads and the buttons on the right launch a section (Launch setting under Push 1, or Shift: at once); arrows move the grid. Launchpad: Keys or Note plays the pads in key, Drums a 4x4 drum kit, Session goes back. APC: faders on the levels of the 8 tracks (Shift and track buttons 5, 6, 8: volume, pan, the selected device), track buttons select (Shift: arrows). APC40: knobs on the selected device and on pan, transport and tempo.';
    const set=b.querySelector('.mcset');if(set)set.appendChild(w);else b.insertBefore(w,b.querySelector(':scope>.cmtpl'))}return r}}
FT_HOOKS.gridPaint=()=>lpAll();
