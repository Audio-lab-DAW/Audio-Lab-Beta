/* v0.248 (task FT-C3b): Mackie Control and HUI control surfaces (motor faders, V-pots, buttons, displays). A device whose name says so
   (Mackie Control, MCU, X-Touch, QCon, Platform M or X; HUI) or that the user sets to "Mackie Control" or "HUI" on the Controllers page
   becomes a surface: 8 faders on the levels of 8 tracks (the master fader on the master; motors follow, not while touched; one undo step a
   touch), V-pots on pan (or, Mackie Plug-in, on the selected device's first 8 parameters), Rec, Solo, Mute and Select per strip, banks of 8
   and channel by 1, transport (Play, Stop, Record, Cycle, Click, Rewind and Fast forward by a bar), the jog wheel (16ths, Shift: bars),
   Undo, Save, arrows (tracks up and down, devices left and right), the 2 x 56 display (names and values), the time code display (bars,
   beats, 16ths, ticks) and the assignment display; HUI: 4-character strips, the 2 x 40 display, its time code, and the ping it needs
   (one message a second while a HUI is connected). An extender (name with "Ext" or "XT") shows the next 8 tracks. Everything is sent
   only when it changed; a check 15 times a second runs only while the song plays and a surface is connected. Bytes as in the Logic Pro
   Control Surfaces guide (Mackie Control) and the HUI MIDI protocol notes (theageman, 2010); to be confirmed on real surfaces. */
const MC={N:{rec:0,solo:8,mute:16,sel:24,vpp:32,trk:40,send:41,pan:42,plug:43,bankL:46,bankR:47,chL:48,chR:49,shift:70,save:80,undo:81,cycle:86,click:89,rew:91,ff:92,stop:93,play:94,record:95,up:96,down:97,left:98,right:99,touch:104},
  SX:[0xF0,0,0,0x66],tb:0,vm:'pan',acc:{},undoK:'',undoT:0,pollT:0,soonT:0,pingT:0,jogT:0,jogB:null,n:{fb:0,lcd:0,ping:0}};
window.MC=MC;
const mcAs=d=>UI.ctlAs&&UI.ctlAs[d.name];
const mcMatch=d=>{const a=mcAs(d);if(a)return a==='mcu';const n=String(d.name||'');return/mackie\s*control|\bmcu\b|x-?touch(?!\s*mini)|qcon|platform\s*[mx]/i.test(n)&&!/\bhui\b/i.test(n)};
const huiMatch=d=>{const a=mcAs(d);if(a)return a==='hui';return/\bhui\b/i.test(String(d.name||''))};
const mcDevs=()=>[...CTL.devs.values()].filter(d=>d.mc&&d.prof&&(d.prof.id==='mcu'||d.prof.id==='hui')&&!ctlOff(d));
const mcMax=()=>Math.max(0,S.tracks.length-1);
const mcStrip=(d,i)=>S.tracks[clamp(MC.tb|0,0,mcMax())+d.mc.off+i]||null;
function mcVid(d,i){if(MC.vm==='plug'&&!d.mc.off&&d.prof.id==='mcu')return ctlTDev().ids[i]||null;const t=mcStrip(d,i);return t&&CT.has('hp:'+t.id)?'hp:'+t.id:null}
const mcN=id=>{const C=id&&CT.get(id);return C?C.spec.n(C.get()):null};
const mcTxt=id=>{const C=id&&CT.get(id);if(!C)return'';try{return p1bA(C.spec.f(C.get()))}catch(e){return''}};
/* moving a control: one undo step per run of moves (a fader touch opens its own) */
function mcSet(id,n,key){const C=CT.get(id);if(!C)return;if(key)p1bUndo(MC,key);C.set(C.spec.v(clamp(n,0,1)));ctlPaintId(id);if(C.after&&!document.querySelector(`[data-c="${CSS.escape(id)}"]`))try{C.after(C.get())}catch(e){}}
function mcNudge(id,dn){const C=CT.get(id);if(!C)return;const cur=C.spec.n(C.get());let r=MC.acc[id];if(r==null||Math.abs(r-cur)>.02)r=cur;r=clamp(r+dn,0,1);MC.acc[id]=r;mcSet(id,r,id)}
function mcFader(d,i,n){const id=i===8?'ms':(t=>t?'hd:'+t.id:null)(mcStrip(d,i));if(!id||!CT.has(id))return;d.mc.fin[i]=n;mcSet(id,n,d.mc.touch.has(i)?null:'f'+id);d.mc.fo[i]=Math.round(clamp(mcN(id),0,1)*16383)}
function mcTouch(d,i,on){if(on){if(!d.mc.touch.has(i)){d.mc.touch.add(i);pushUndo()}}else{d.mc.touch.delete(i);d.mc.fo[i]=-1;mcSoon()}}
function mcBank(dn){const a=clamp((MC.tb|0)+dn,0,mcMax());if(a===(MC.tb|0))return;MC.tb=a;toast('Faders: tracks '+(a+1)+' to '+Math.min(S.tracks.length,a+8*Math.max(1,mcDevs().length))+'.');mcAll()}
function mcStripBtn(d,k,i){const t=mcStrip(d,i);if(!t)return;
  if(k==='sel'){selectTrack(t.id);return}if(k==='rec'){if(t.kind!=='inst'&&t.kind!=='audio')return;armTrack(t).then(()=>mcSoon(),()=>{});return}
  pushUndo();t[k]=!t[k];changed(true)}
const mcCur=()=>play.on&&!play.counting?curDisp():pos;
function mcSeek(b){b=Math.max(0,b);if(play.on){MC.jogB=b;clearTimeout(MC.jogT);MC.jogT=setTimeout(()=>{MC.jogT=0;const x=MC.jogB;MC.jogB=null;if(x==null)return;pos=x;stop();start();dirty=true;mcSoon()},180);return}pos=b;dirty=true;mcSoon()}
function mcRew(fw){const c=MC.jogB!=null?MC.jogB:mcCur(),P=barPos(c);if(fw)mcSeek(P.start+P.len);else mcSeek(c-P.start>.1?P.start:barPos(Math.max(0,P.start-1e-3)).start)}
function mcJog(dl,sh){const c=MC.jogB!=null?MC.jogB:mcCur();if(sh){let b=c;for(let k=0;k<Math.abs(dl);k++){const P=barPos(dl>0?b:Math.max(0,b-1e-3));b=dl>0?P.start+P.len:(b-P.start>1e-3?P.start:P.start)}mcSeek(b);return}mcSeek(Math.round((c+dl*.25)*4)/4)}
const mcRun=id=>{const a=SCM.get(id);if(a)a.run();mcSoon()};
/* the buttons both surfaces share, by name */
function mcBtn(d,k,on,i){const st=d.mc;if(k==='shift'){st.shift=on;return}if(k==='touch'){mcTouch(d,i,on);return}if(!on)return;
  if(k==='rec'||k==='solo'||k==='mute'||k==='sel'){mcStripBtn(d,k,i);return}
  if(k==='vpp'){const id=mcVid(d,i),C=id&&CT.get(id);if(C){pushUndo();const z=C.spec.d!=null?C.spec.n(C.spec.d):.5;mcSet(id,z,null)}return}
  if(k==='pan'||k==='plug'){MC.vm=k;toast(k==='plug'?'V-pots: the selected device ('+((ctlTDev().devs[ctlTDev().i]||{}).name||'none')+').':'V-pots: pan.');mcAll();return}
  if(k==='bankL'||k==='bankR'){mcBank((k==='bankR'?8:-8)*Math.max(1,mcDevs().length));return}if(k==='chL'||k==='chR'){mcBank(k==='chR'?1:-1);return}
  if(k==='play'){if(!play.on)mcRun('play');return}if(k==='stop'){if(play.on)mcRun('stop');else mcSeek(0);return}if(k==='record'){mcRun('rec');return}
  if(k==='cycle'){mcRun('loop');return}if(k==='click'){mcRun('click');return}if(k==='rew'||k==='ff'){mcRew(k==='ff');return}
  if(k==='undo'){mcRun(st.shift?'redo':'undo');return}if(k==='save'){mcRun('save');return}
  if(k==='up'||k==='down'){ctlTNav(k==='up'?'trkPrev':'trkNext');mcAll();return}if(k==='left'||k==='right'){ctlTNav(k==='left'?'devPrev':'devNext');mcAll()}}
/* ---- what the surface should show; each driver sends only what changed ---- */
function mcModel(d){const m={f:[],v:[],nm:[],val:[],sel:[],mute:[],solo:[],rec:[]};const plug=MC.vm==='plug'&&!d.mc.off&&d.prof.id==='mcu',P=plug?ctlTDev():null;
  for(let i=0;i<8;i++){const t=mcStrip(d,i),vid=mcVid(d,i);m.f.push(t?mcN('hd:'+t.id):0);m.v.push(vid?mcN(vid):null);
    m.nm.push(plug?(vid?p1bA(CT.get(vid).label):''):(t?p1bA(t.name):''));m.val.push(vid?mcTxt(vid):'');m.sel.push(!!t&&t.id===selT);m.mute.push(!!(t&&t.mute));m.solo.push(!!(t&&t.solo));m.rec.push(!!(t&&t.arm))}
  m.ms=mcN('ms');m.plug=plug;m.dev=P&&P.devs[P.i]?P.devs[P.i].name:'';return m}
function mcClock(){const b=mcCur(),P=barPos(Math.max(0,b)),bl=4/P.sig.d,bi=Math.floor(P.inBar/bl+1e-9),r=P.inBar-bi*bl,s=Math.floor(r/.25+1e-9),tk=Math.floor((r-s*.25)/.25*240+1e-6)+1;return{bar:P.bar+1,beat:bi+1,six:s+1,tick:Math.min(240,tk)}}
/* Mackie Control */
function mcSend(d,a,k,v){const st=d.mc;if(k!=null){if(st.out.get(k)===v)return;st.out.set(k,v)}if(ctlSend(d,a))MC.n.fb++}
function mcLcd(d,line,txt){const s=String(txt).replace(/[^\x20-\x7E]/g,'?').padEnd(56).slice(0,56);if(d.mc.lcd[line]===s||!CTL.sysex)return;d.mc.lcd[line]=s;MC.n.lcd++;ctlSend(d,MC.SX.concat([d.mc.xt?0x15:0x14,0x12,line*56],[...s].map(c=>c.charCodeAt(0)),[0xF7]))}
const mcSeg=(c,dot)=>{const x=c.charCodeAt(0);return((x>=0x40?x-0x40:x)&0x3F)|(dot?0x40:0)};
function mcuPaint(d){const st=d.mc,m=mcModel(d),N=MC.N,led=(n,on)=>mcSend(d,[0x90,n,on?127:0],'n'+n,on?127:0);
  for(let i=0;i<9;i++){if(st.touch.has(i))continue;const n=i===8?m.ms:m.f[i];if(i===8&&st.off)continue;const v=Math.round(clamp(n||0,0,1)*16383);if(st.fo[i]===v)continue;st.fo[i]=v;mcSend(d,[0xE0|i,v&127,v>>7])}
  for(let i=0;i<8;i++){const v=m.v[i]==null?0:(m.plug?0x20:0x10)|(1+Math.round(clamp(m.v[i],0,1)*10));mcSend(d,[0xB0,0x30+i,v],'r'+i,v);
    led(N.rec+i,m.rec[i]);led(N.solo+i,m.solo[i]);led(N.mute+i,m.mute[i]);led(N.sel+i,m.sel[i])}
  if(!st.off){led(N.pan,!m.plug);led(N.plug,m.plug);led(N.play,play.on);led(N.record,!!REC.on);led(N.cycle,!!S.loop);led(N.click,!!S.click)}
  const cell=a=>a.map(x=>String(x).slice(0,6).padEnd(7)).join('');mcLcd(d,0,cell(m.nm));mcLcd(d,1,cell(m.val));
  if(st.off)return;const c=mcClock(),tc=String(c.bar).padStart(3,' ').slice(-3)+String(c.beat).padStart(2,' ').slice(-2)+String(c.six).padStart(2,'0').slice(-2)+String(c.tick).padStart(3,'0').slice(-3);
  for(let k=0;k<10;k++){const v=mcSeg(tc[k],k===2||k===4||k===6);mcSend(d,[0xB0,0x40+(9-k),v],'t'+k,v)}
  const as=m.plug?'PL':'PN';mcSend(d,[0xB0,0x4B,mcSeg(as[0])],'a0',mcSeg(as[0]));mcSend(d,[0xB0,0x4A,mcSeg(as[1])],'a1',mcSeg(as[1]))}
const MCU_IN=(()=>{const N=MC.N,r={};for(const k of['rec','solo','mute','sel','vpp','touch'])for(let i=0;i<(k==='touch'?9:8);i++)r[N[k]+i]=[k,i];for(const k in N)if(!['rec','solo','mute','sel','vpp','touch'].includes(k))r[N[k]]=[k,0];return r})();
const mcMine=(d,type,ch,num)=>{const ms=ctlIndex().byM.get(ctlKey(type,ch,num));return!!(ms&&ms.some(m=>m.dev===d.name))};
function mcuMsg(d,a){const s=a[0],c=s&0xf0,ch=s&15;if(s>=0xF0)return;const type=c===0xB0?'cc':c===0xE0?'pb':'note',num=c===0xE0?0:a[1],raw=c===0xE0?(a[2]<<7)|a[1]:a[2];
  if(c===0x90||c===0x80||c===0xB0||c===0xE0){if(ML.on||CTL.relearn||mcMine(d,type,ch,num)){if(c===0x80||(c===0x90&&!a[2]))return;ctlIn(d,type,ch,num,raw);return}}
  if(c===0xE0){if(ch<=8)mcFader(d,ch,raw/16383);return}
  if(c===0x90||c===0x80){const x=MCU_IN[a[1]];if(x)mcBtn(d,x[0],c===0x90&&a[2]>0,x[1]);mcSoon();return}
  if(c===0xB0){const n=a[1],v=a[2],dl=v&0x40?-(v&0x3F):(v&0x3F);if(n>=16&&n<=23){const id=mcVid(d,n-16);if(id)mcNudge(id,dl/(d.mc.shift?1000:100));mcSoon();return}if(n===60){mcJog(dl,d.mc.shift);return}}}
function mcuBye(d){if(!d.mc)return;const raw=a=>{if(!d.out||(a[0]===0xF0&&!CTL.sysex))return;try{d.out.send(a);CTL.n.out++}catch(e){}};
  for(let l=0;l<2;l++)raw(MC.SX.concat([d.mc.xt?0x15:0x14,0x12,l*56],Array(56).fill(32),[0xF7]));for(const k of d.mc.out.keys()){if(k[0]==='n')raw([0x90,+k.slice(1),0]);else if(k[0]==='r')raw([0xB0,0x30+(+k.slice(1)),0]);else if(k[0]==='t')raw([0xB0,0x40+(9-(+k.slice(1))),0x20]);else if(k[0]==='a')raw([0xB0,k==='a0'?0x4B:0x4A,0x20])}
  d.mc.out.clear();d.mc.lcd=['',''];d.mc.fo=[]}
/* HUI */
const HUI={HD:[0xF0,0,0,0x66,5,0],STRIP:['touch','sel','mute','solo','auto','vsel','ins','rec'],Z:{0x0A:['chL','bankL','chR','bankR'],0x0E:['talk','rew','ff','stop','play','record'],0x0F:['rtz','end','online','cycle'],0x0D:['down','left','mode','right','up'],0x08:['ctrl','shift','emode','undo','alt','opt','etool','save']}};
function huiLed(d,z,p,on){const k='z'+z+':'+p,v=on?1:0;if(d.mc.out.get(k)===v)return;d.mc.out.set(k,v);ctlSend(d,[0xB0,0x0C,z]);ctlSend(d,[0xB0,0x2C,p|(on?0x40:0)])}
function huiPaint(d){const st=d.mc,m=mcModel(d);
  for(let i=0;i<8;i++){if(!st.touch.has(i)){const v=Math.round(clamp(m.f[i]||0,0,1)*16383);if(st.fo[i]!==v){st.fo[i]=v;ctlSend(d,[0xB0,i,v>>7]);ctlSend(d,[0xB0,0x20+i,v&127]);MC.n.fb++}}
    const r=m.v[i]==null?0:0x11+Math.round(clamp(m.v[i],0,1)*10);if(st.out.get('r'+i)!==r){st.out.set('r'+i,r);ctlSend(d,[0xB0,0x10+i,r])}
    huiLed(d,i,1,m.sel[i]);huiLed(d,i,2,m.mute[i]);huiLed(d,i,3,m.solo[i]);huiLed(d,i,7,m.rec[i]);
    const s4=String(m.nm[i]).slice(0,4).padEnd(4);if(st.lcd['s'+i]!==s4&&CTL.sysex){st.lcd['s'+i]=s4;MC.n.lcd++;ctlSend(d,HUI.HD.concat([0x10,i],[...s4].map(c=>c.charCodeAt(0)),[0xF7]))}}
  huiLed(d,0x0E,4,play.on);huiLed(d,0x0E,5,!!REC.on);huiLed(d,0x0F,3,!!S.loop);
  const t=curT(),a=clamp(MC.tb|0,0,mcMax())+st.off,top=('AudioLab').padEnd(10)+('Tracks '+(a+1)+'-'+Math.min(S.tracks.length,a+8)).padEnd(15)+(t?p1bA(t.name):'').slice(0,15).padEnd(15),bot=m.val.map(x=>String(x).slice(0,4).padEnd(5)).join('');
  for(let z=0;z<8;z++){const s=(z<4?top:bot).slice((z%4)*10,(z%4)*10+10).replace(/[^\x20-\x7E]/g,'?').padEnd(10);if(st.lcd['m'+z]!==s&&CTL.sysex){st.lcd['m'+z]=s;MC.n.lcd++;ctlSend(d,HUI.HD.concat([0x12,z],[...s].map(c=>c.charCodeAt(0)),[0xF7]))}}
  const c=mcClock(),dg=(String(c.bar).padStart(3,'0').slice(-3)+String(c.beat).padStart(2,'0').slice(-2)+String(c.six).padStart(2,'0').slice(-2)).split('').map(Number),dots=[2,4];
  const y=dg.map((x,k)=>x+(dots.includes(k)?0x10:0)).reverse(),tk=y.join(',');if(st.lcd.tc!==tk&&CTL.sysex){st.lcd.tc=tk;ctlSend(d,HUI.HD.concat([0x11],y,[0xF7]))}}
function huiMsg(d,a){const s=a[0],c=s&0xf0,st=d.mc;if(s>=0xF0)return;if(c===0x90&&a[1]===0)return;/* the ping's answer */
  if(c!==0xB0)return;const n=a[1],v=a[2];
  if(ML.on||CTL.relearn||mcMine(d,'cc',s&15,n)){if(n!==0x0F&&n!==0x2F){ctlIn(d,'cc',s&15,n,v);return}}
  if(n===0x0F){st.zone=v;return}
  if(n===0x2F){const z=st.zone,p=v&0x0F,on=!!(v&0x40);let k=null,i=0;if(z<8){k=HUI.STRIP[p];i=z}else if(HUI.Z[z])k=HUI.Z[z][p];if(k==='vsel'||k==='auto'||k==='ins')k=null;if(k)mcBtn(d,k,on,i);mcSoon();return}
  if(n<8){st.hi[n]=v;return}if(n>=0x20&&n<0x28){const i=n-0x20;mcFader(d,i,((st.hi[i]|0)<<7|v)/16383);return}
  const dl=v>0x40?v-0x40:-v;if(n>=0x40&&n<0x48){const id=mcVid(d,n-0x40);if(id)mcNudge(id,dl/(st.shift?1000:100));mcSoon();return}if(n===0x0D){mcJog(dl,st.shift);return}}
function huiBye(d){if(!d.mc)return;const raw=a=>{if(!d.out||(a[0]===0xF0&&!CTL.sysex))return;try{d.out.send(a);CTL.n.out++}catch(e){}};
  for(const k of d.mc.out.keys())if(k[0]==='z'){const[z,p]=k.slice(1).split(':').map(Number);raw([0xB0,0x0C,z]);raw([0xB0,0x2C,p])}else if(k[0]==='r')raw([0xB0,0x10+(+k.slice(1)),0]);
  for(let i=0;i<8;i++)raw(HUI.HD.concat([0x10,i,32,32,32,32,0xF7]));for(let z=0;z<8;z++)raw(HUI.HD.concat([0x12,z],Array(10).fill(32),[0xF7]));d.mc.out.clear();d.mc.lcd={};d.mc.fo=[]}
function huiPing(){const hs=mcDevs().filter(d=>d.prof.id==='hui');if(!hs.length){clearInterval(MC.pingT);MC.pingT=0;return}for(const d of hs){ctlSend(d,[0x90,0,0]);MC.n.ping++}}
/* ---- painting: on change, and 15 times a second only while playing ---- */
function mcPaintDev(d){if(!d||!d.mc||ctlOff(d))return;try{if(d.prof.id==='hui')huiPaint(d);else mcuPaint(d)}catch(e){console.error('AudioLab surface '+d.name,e)}}
function mcAll(){for(const d of mcDevs())mcPaintDev(d)}
function mcSoon(){if(MC.soonT||!mcDevs().length)return;MC.soonT=setTimeout(()=>{MC.soonT=0;mcAll()},33)}
function mcPoll(){if(MC.pollT||!mcDevs().length)return;const tick=()=>{MC.pollT=0;mcAll();if(play.on&&mcDevs().length)MC.pollT=setTimeout(tick,66)};MC.pollT=setTimeout(tick,66)}
function mcNew(d){d.mc={off:/\b(ext|xt)\b|extender/i.test(d.name)?8:0,xt:/\b(ext|xt)\b|extender/i.test(d.name),touch:new Set(),fo:[],fin:[],out:new Map(),lcd:d.prof.id==='hui'?{}:['',''],hi:[],zone:0,shift:false}}
ctlProf({id:'mcu',name:'Mackie Control',match:mcMatch,attach(d){mcNew(d);mcPaintDev(d);if(play.on)mcPoll()},detach(d){mcuBye(d)},bye(d){mcuBye(d)},msg:mcuMsg});
ctlProf({id:'hui',name:'HUI',match:huiMatch,attach(d){mcNew(d);ctlSend(d,[0x90,0,0]);mcPaintDev(d);if(!MC.pingT)MC.pingT=setInterval(huiPing,1000);if(play.on)mcPoll()},detach(d){huiBye(d)},bye(d){huiBye(d)},msg:huiMsg});
{const _s=start;start=function(){const r=_s.apply(this,arguments);try{if(mcDevs().length)mcPoll()}catch(e){}return r}}
{const _s=selectTrack;selectTrack=function(){const r=_s.apply(this,arguments);try{if(mcDevs().length)mcSoon()}catch(e){}return r}}
{const _c=changed;changed=function(){const r=_c.apply(this,arguments);try{if(mcDevs().length)mcSoon()}catch(e){}return r}}
{const _p=paintCtl;paintCtl=function(el){const r=_p.apply(this,arguments);try{if(!MC.soonT&&el&&el.dataset&&CTL.devs.size&&/^(hd:|hp:|ms$|fx:)/.test(el.dataset.c||'')&&mcDevs().length)mcSoon()}catch(e){}return r}}
/* ---- the Controllers page: what each device works as ---- */
function mcAsSet(name,v){UI.ctlAs=Object.assign({},UI.ctlAs||{});if(v)UI.ctlAs[name]=v;else delete UI.ctlAs[name];saveUI();for(const d of CTL.devs.values())if(d.name===name){const p=CTL.profs.find(x=>x.match(d));if(p!==d.prof)ctlAttach(d)}ctlPagePaint()}
{const _p=ctlPagePaint;ctlPagePaint=function(){const r=_p.apply(this,arguments);const b=CTL.host;if(!b||!b.isConnected||b.closest('[hidden]'))return r;const devs=[...CTL.devs.values()];if(!devs.length)return r;if(!document.getElementById('ctlCss4')){const st=document.createElement('style');st.id='ctlCss4';st.textContent='.ctlpg .mcrow{display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center;padding:4px;flex-shrink:0}.ctlpg .mcrow b{font-weight:var(--fw5);min-width:120px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}';document.head.appendChild(st)}
  const tip='What this device is to AudioLab. Mackie Control and HUI: a mixing surface with motor faders, knobs and a display (Behringer X-Touch, Icon, Mackie and many more in their Mackie or HUI mode). Automatic: by its name.';
  const o=(v,cur,l)=>`<option value="${v}"${cur===v?' selected':''}>${l}</option>`,w=document.createElement('div');w.className='mcset';w.style.display='contents';
  w.innerHTML=`<h4>Works as</h4>${devs.map(d=>{const a=mcAs(d)||'';return`<div class="mcrow" data-d="${esc(d.name)}"><b title="${esc(d.name)}">${esc(d.name)}</b><select data-mc="as" title="${tip}">${o('',a,'Automatic ('+esc(d.prof?d.prof.name:'')+')')+o('generic',a,'Keyboard or controller')+o('mcu',a,'Mackie Control')+o('hui',a,'HUI')}</select></div>`}).join('')}
  ${mcDevs().length?`<div class="cmtpi" title="What the buttons of a Mackie Control or HUI surface do in AudioLab">Faders: levels of 8 tracks (master fader: master). Knobs: pan; Plug-in: the selected device. Rec, Solo, Mute, Select per track; Bank and Channel move the 8 tracks; Play, Stop, Record, Cycle, Click, Rewind and Forward (a bar), the jog wheel (Shift: bars), Undo (Shift: redo), Save; Up and Down pick the track, Left and Right the device.</div>`:''}`;
  let at=b.querySelector(':scope>.cmtpl')||[...b.querySelectorAll(':scope>h4')].find(x=>x.textContent==='Mappings')||null;b.insertBefore(w,at);
  w.querySelector('select')&&w.addEventListener('change',e=>{const x=e.target.closest('[data-mc="as"]');if(!x)return;e.stopPropagation();mcAsSet(x.closest('[data-d]').dataset.d,x.value)});return r}}
FT_HOOKS.surfacePaint=()=>mcAll();FT_HOOKS.surfaceAs=(name,kind)=>mcAsSet(name,kind||'');
