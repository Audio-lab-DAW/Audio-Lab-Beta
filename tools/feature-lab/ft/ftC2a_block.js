/* v0.238 (task FT-C2a): Ableton Push 1, part 1: connect, display, pads. A profile for Push 1's Live port (its User port and other Pushes stay
   generic). Hello: Live mode, pressure mode and touch strip mode by SysEx, the 4-line display, the pads and the buttons it uses; goodbye (page
   hidden, device switched off or unplugged): display cleared, pads and buttons dark. The pads are a note grid in the project key (PR.root,
   PR.scale): in key or chromatic, rows in fourths, thirds or one after another, octave up and down; pad colours from the track's colour (root
   pads), white for notes in the key, dark out of key, green while held. Velocity curves, pressure off or per pad or for the whole pad grid
   (sent to FT_HOOKS.pressure for later steps), the touch strip as pitch bend or modulation. Scales button: the 8 encoders over the display
   change key, scale, layout, rows, velocity, pressure, strip and octave. Only changed display lines and pad colours are sent; nothing runs
   while the Push is still. Bytes: display, modes and pad notes as in the pushmod reverse-engineering notes; button numbers as in the
   open-source Push 1 scripts; to be confirmed on the real Push 1 (FT-C2a log). */
const P1={SX:[0xF0,0x47,0x7F,0x15],CC:{oct_dn:54,oct_up:55,scales:58,note:50,accent:57,shift:49,user:59},ENC:[71,72,73,74,75,76,77,78],
  /* palette indices (Push 1 uses Live's 128-colour pad palette: 0 off, 3 white; the hue row of full colours 5, 9, 13 ... 57) */
  HUE:[[0,5],[28,9],[52,13],[78,17],[118,21],[140,25],[162,29],[182,33],[196,37],[212,41],[234,45],[264,49],[298,53],[330,57]],
  ROWS:{'4th':[3,5],'3rd':[2,4],'seq':[8,8]},
  OPT:{lay:[['key','In key'],['chrom','Chromatic']],rows:[['4th','Fourths'],['3rd','Thirds'],['seq','In a row']],vc:[['lin','Linear'],['soft','Soft'],['hard','Hard'],['fixed','Fixed']],
    at:[['off','Off'],['poly','Per pad'],['chan','Whole grid']],strip:[['pb','Pitch bend'],['mod','Modulation']]},
  NN:['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']};
window.P1=P1;
const p1S=()=>{const d={lay:'key',rows:'4th',vc:'lin',at:'off',strip:'pb',oct:2};const u=UI.p1&&typeof UI.p1==='object'?UI.p1:{};for(const k in d)if(u[k]!==undefined)d[k]=u[k];return d};
const p1Set=(k,v)=>{UI.p1=Object.assign({},UI.p1||{},{[k]:v});saveUI()};
const p1Match=d=>{const n=String(d.name||'');return/ableton\s*push/i.test(n)&&!/push\s*[23]\b|push\s*[23]\s/i.test(n)&&!/user/i.test(n)&&!/^MIDIIN\d/i.test(n)};
const p1Track=()=>{const a=S.tracks.filter(t=>t.arm&&t.kind==='inst');if(a.length)return a;const t=curT();return t&&t.kind==='inst'?[t]:[]};
function p1Col(c){const m=/^#?([0-9a-f]{6})$/i.exec(String(c||'').trim());if(!m)return 3;const n=parseInt(m[1],16),r=(n>>16)/255,g=((n>>8)&255)/255,b=(n&255)/255,mx=Math.max(r,g,b),mn=Math.min(r,g,b),dl=mx-mn;
  if(mx<.12)return 1;if(dl<.15*mx||dl<.08)return 3;let h=mx===r?((g-b)/dl)%6:mx===g?(b-r)/dl+2:(r-g)/dl+4;h=(h*60+360)%360;let best=5,bd=999;for(const[hh,i]of P1.HUE){const x=Math.min(Math.abs(h-hh),360-Math.abs(h-hh));if(x<bd){bd=x;best=i}}return best}
/* the pad under (x, y), 0,0 bottom left: its MIDI note and whether it is the root or in the key */
function p1Pad(x,y,o){o=o||p1S();const sc=(SCALES[PR.scale]||null)||[0,1,2,3,4,5,6,7,8,9,10,11],root=PR.root|0,base=12*(o.oct+1)+root,R=P1.ROWS[o.rows]||P1.ROWS['4th'];
  if(o.lay==='key'){const n=sc.length,dg=y*R[0]+x,st=Math.floor(dg/n)*12+sc[dg%n];return{m:base+st,root:dg%n===0,in:true}}
  const st=y*R[1]+x,ss=((st%12)+12)%12;return{m:base+st,root:ss===0,in:sc.includes(ss)}}
function p1PadCol(x,y,o,held,tc){const p=p1Pad(x,y,o);if(p.m>127||p.m<0)return 0;if(held&&held.has(p.m))return tc===21?3:21;return p.root?tc:p.in?3:0}
const p1Send=(d,a)=>ctlSend(d,a);
function p1Line(d,i,txt){const s=String(txt||'').replace(/[^\x20-\x7E]/g,'?').padEnd(68).slice(0,68);const st=d.p1;if(st.disp[i]===s)return;
  if(!CTL.sysex)return;st.disp[i]=s;if(!s.trim()){p1Send(d,P1.SX.concat([0x1C+i,0,0,0xF7]));return}p1Send(d,P1.SX.concat([0x18+i,0,69,0],[...s].map(c=>c.charCodeAt(0)),[0xF7]))}
const p1Cell=a=>a.map(x=>String(x).slice(0,16).padEnd(17)).join(''),p1Cell8=a=>a.map((x,i)=>String(x).slice(0,8).padEnd(i%2?9:8)).join('');
function p1Disp(d){const o=p1S(),t=p1Track()[0],key=P1.NN[PR.root|0]+' '+PR.scale,st=d.p1;
  if(st.scales){p1Line(d,0,p1Cell8(['Root','Scale','Layout','Rows','Velocity','Pressure','Strip','Octave']));
    const lab=(k)=>(P1.OPT[k].find(x=>x[0]===o[k])||P1.OPT[k][0])[1];
    p1Line(d,1,p1Cell8([P1.NN[PR.root|0],PR.scale.replace('harmonic ','harm ').replace('pentatonic','pent'),lab('lay'),lab('rows'),lab('vc'),lab('at'),lab('strip'),String(o.oct)]));
    p1Line(d,2,'');p1Line(d,3,p1Cell(['Turn to change','','','Scales: back']));return}
  p1Line(d,0,p1Cell(['AudioLab',t?t.name:'No instrument','','Note mode']));
  p1Line(d,1,p1Cell(['Key '+key,(o.lay==='key'?'In key':'Chromatic')+', '+(P1.OPT.rows.find(x=>x[0]===o.rows)||['','Fourths'])[1],'Octave '+o.oct,'Vel '+(P1.OPT.vc.find(x=>x[0]===o.vc)||['','Linear'])[1]]));
  p1Line(d,2,t?'':p1Cell(['Select or arm an','instrument track','to play the pads','']));p1Line(d,3,p1Cell(['Scales: key and','layout','Octave up/down','']))}
function p1Pads(d){const o=p1S(),st=d.p1,t=p1Track()[0],tc=p1Col(t&&t.color);for(let y=0;y<8;y++)for(let x=0;x<8;x++){const n=36+y*8+x,c=p1PadCol(x,y,o,st.held,tc);if(st.led.get(n)!==c){st.led.set(n,c);p1Send(d,[0x90,n,c])}}}
function p1Btns(d){const o=p1S(),st=d.p1,set=(cc,v)=>{if(st.btn.get(cc)!==v){st.btn.set(cc,v);p1Send(d,[0xB0,cc,v])}};
  set(P1.CC.oct_up,12*(o.oct+2)+(PR.root|0)<=127?(st.scales?1:4):0);set(P1.CC.oct_dn,o.oct>0?(st.scales?1:4):0);set(P1.CC.scales,st.scales?4:1);set(P1.CC.note,4)}
function p1Paint(d){if(!d||!d.p1||ctlOff(d))return;p1Disp(d);p1Pads(d);p1Btns(d)}
const p1All=()=>{for(const d of CTL.devs.values())if(d.prof&&d.prof.id==='push1')p1Paint(d)};
function p1Modes(d){const o=p1S();if(!CTL.sysex)return;p1Send(d,P1.SX.concat([0x62,0,1,0,0xF7]));/* Live mode */
  p1Send(d,P1.SX.concat([0x5C,0,1,o.at==='chan'?1:0,0xF7]));/* pressure: per pad or whole grid */p1Send(d,P1.SX.concat([0x63,0,1,o.strip==='mod'?10:6,0xF7]))/* strip: pitch bend or mod wheel */}
const p1Vel=(v,o)=>{const x=v/127;return o.vc==='fixed'?100/127:o.vc==='soft'?Math.pow(x,.6):o.vc==='hard'?Math.pow(x,1.6):x};
/* plays like a keyboard on the armed tracks, or the selected instrument track when none is armed (as Live's Push does) */
function p1On(m,v){const key='p1:'+m;if(LIVE.has(key))return;const ts=p1Track();if(!ts.length)return;const hs=ts.map(t=>({t,h:voiceOn(t,m-24,v)}));const b=play.on&&!play.counting?curDisp():null;LIVE.set(key,{p:m-24,v,hs,b});flashArm()}
function p1Enc(d,i,raw){const st=d.p1,dl=raw<64?raw:raw-128;st.acc[i]=(st.acc[i]||0)+dl;if(Math.abs(st.acc[i])<3)return;const dir=Math.sign(st.acc[i]);st.acc[i]=0;const o=p1S();
  const cyc=(k)=>{const L=P1.OPT[k],j=L.findIndex(x=>x[0]===o[k]);p1Set(k,L[(j+dir+L.length)%L.length][0])};
  if(i===0){PR.root=((PR.root|0)+dir+12)%12;changed(false)}else if(i===1){const K=Object.keys(SCALES),j=K.indexOf(PR.scale);PR.scale=K[(j+dir+K.length)%K.length];changed(false)}
  else if(i===2)cyc('lay');else if(i===3)cyc('rows');else if(i===4)cyc('vc');else if(i===5){cyc('at');p1Modes(d)}else if(i===6){cyc('strip');p1Modes(d)}
  else if(i===7){const n=clamp(o.oct+dir,0,8);if(12*(n+1)+(PR.root|0)<=127)p1Set('oct',n)}p1All();ctlPagePaint()}
/* goodbye goes out also when the device was just switched off (ctlSend refuses a switched-off device) */
const p1Raw=(d,a)=>{if(!d||!d.out||(a[0]===0xF0&&!CTL.sysex))return;try{d.out.send(a);CTL.n.out++}catch(e){}};
function p1Bye(d){if(!d.p1)return;for(let i=0;i<4;i++)p1Raw(d,P1.SX.concat([0x1C+i,0,0,0xF7]));for(let n=36;n<100;n++)p1Raw(d,[0x90,n,0]);for(const cc of d.p1.btn.keys())p1Raw(d,[0xB0,cc,0]);
  for(const k of[...LIVE.keys()])if(typeof k==='string'&&k.startsWith('p1:'))noteOff(k);d.p1.disp=['','','',''];d.p1.led.clear();d.p1.btn.clear()}
ctlProf({id:'push1',name:'Ableton Push 1',match:p1Match,
  attach(d){d.p1={disp:['','','',''],led:new Map(),btn:new Map(),held:new Set(),acc:[],scales:false};p1Modes(d);p1Paint(d)},
  detach(d){p1Bye(d)},bye(d){p1Bye(d)},
  msg(d,a){const s=a[0],c=s&0xf0,ch=s&15,st=d.p1;if(!st||s>=0xF0)return;const o=p1S();
    if((c===0x90||c===0x80)&&a[1]>=36&&a[1]<=99){const x=(a[1]-36)%8,y=(a[1]-36)>>3,p=p1Pad(x,y,o);if(p.m<0||p.m>127)return;
      if(c===0x90&&a[2]>0){if(ML.on&&ML.sel&&ctlIn(d,'note',ch,a[1],a[2]))return;st.held.add(p.m);p1On(p.m,p1Vel(a[2],o))}else{st.held.delete(p.m);noteOff('p1:'+p.m)}p1Pads(d);return}
    if(c===0x90||c===0x80)return;/* encoder and strip touches (notes 0 to 12) never play */
    if(c===0xA0||c===0xD0){if(o.at==='off')return;if(FT_HOOKS.pressure)try{FT_HOOKS.pressure(c===0xA0?(a[1]>=36&&a[1]<=99?p1Pad((a[1]-36)%8,(a[1]-36)>>3,o).m:null):null,(c===0xA0?a[2]:a[1])/127)}catch(e){}return}
    if(c===0xE0){const v=(a[2]<<7)|a[1];if(ctlIn(d,'pb',ch,0,v))return;ccLive(o.strip==='mod'?'1':'pb',v/16383);return}
    if(c===0xB0){const n=a[1],v=a[2];
      if(st.scales&&P1.ENC.includes(n)&&!ML.on){p1Enc(d,P1.ENC.indexOf(n),v);return}
      if(n===P1.CC.scales){if(v>0){st.scales=!st.scales;p1Paint(d)}return}
      if(n===P1.CC.oct_up||n===P1.CC.oct_dn){if(v>0){const k=n===P1.CC.oct_up?1:-1,nx=clamp(o.oct+k,0,8);if(nx!==o.oct&&12*(nx+1)+(PR.root|0)<=127){p1Set('oct',nx);p1All();ctlPagePaint()}}return}
      if(n===P1.CC.note)return;
      midiCC(ch,n,v,d)}}});/* Push's buttons and encoders are not recorded into controller lanes; they can be learned */
/* the pads follow the selected track, its colour and the project key */
{const _s=selectTrack;selectTrack=function(){const r=_s.apply(this,arguments);try{if(CTL.devs.size)p1All()}catch(e){}return r}}
{const _c=changed;changed=function(){const r=_c.apply(this,arguments);try{if(CTL.devs.size){clearTimeout(P1.chT);P1.chT=setTimeout(p1All,60)}}catch(e){}return r}}
/* the Push's own settings on the Controllers page, while a Push 1 is connected (and in lane B's Settings through FT_HOOKS.controllersPage) */
{const _p=ctlPagePaint;ctlPagePaint=function(){const r=_p.apply(this,arguments);const b=CTL.host;if(!b||!b.isConnected||b.closest('[hidden]'))return r;
  if(![...CTL.devs.values()].some(d=>d.prof&&d.prof.id==='push1'))return r;const o=p1S(),sel=(k,tip)=>`<label title="${tip}">${{lay:'Layout',rows:'Rows',vc:'Velocity',at:'Pressure',strip:'Touch strip'}[k]} <select data-p1="${k}" title="${tip}">${P1.OPT[k].map(([v,l])=>`<option value="${v}"${o[k]===v?' selected':''}>${l}</option>`).join('')}</select></label>`;
  const w=document.createElement('div');w.className='p1set';w.innerHTML=`<h4>Ableton Push 1</h4><div class="cbar">${sel('lay','In key: every pad is a note of the project key. Chromatic: every note, the ones in the key lit white.')}${sel('rows','How far each row of pads is above the one below it')}${sel('vc','How hard you hit a pad turns into how loud the note plays. Fixed: always the same.')}${sel('at','Pressing harder on a held pad: off, per pad, or one value for the whole grid')}${sel('strip','What the touch strip on the left does')}
   <label title="The lowest pad's octave (also the Octave buttons on the Push)">Octave <select data-p1="oct" title="The lowest pad's octave (also the Octave buttons on the Push)">${[0,1,2,3,4,5,6,7].map(v=>`<option value="${v}"${o.oct===v?' selected':''}>${v}</option>`).join('')}</select></label></div>
   <div class="cnone" title="The key is the project's, as in the piano roll">Key: ${P1.NN[PR.root|0]} ${esc(PR.scale)} (the project key; Scales on the Push changes it too)</div>`;
  let at=[...b.querySelectorAll('h4')].find(h=>/mapping/i.test(h.textContent))||null;while(at&&at.parentElement!==b)at=at.parentElement;b.insertBefore(w,at);
  w.addEventListener('change',e=>{const x=e.target.closest('[data-p1]');if(!x)return;const k=x.dataset.p1;p1Set(k,k==='oct'?+x.value:x.value);if(k==='at'||k==='strip')for(const d of CTL.devs.values())if(d.prof&&d.prof.id==='push1')p1Modes(d);p1All()});return r}}
FT_HOOKS.push1Paint=()=>p1All();
