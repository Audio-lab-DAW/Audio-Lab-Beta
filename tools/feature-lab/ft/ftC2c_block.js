/* v0.243 (task FT-C2c): Ableton Push 1, part 3: sections as scenes. Session (CC 51) turns the pads into a grid: 8 tracks across (the same
   track bank as the button rows), 8 sections down (the song's sections in time order); a pad is lit in the track's colour when that track
   plays something in that section, green in the section playing now, white in the section that is queued. The 8 scene buttons on the right
   (CC 36 to 43, top to bottom) and the pads launch a section: when the song is stopped it plays from the section's start; while it plays
   the jump waits for the next bar, for the end of the section playing (like a scene in Live), or happens at once (setting "Launch" on the
   Controllers page and Shift+a scene button: at once). Pressing the queued section again cancels it. The arrows scroll the grid (Shift: by
   8). The 8 encoders move the volume (Pan & Send: pan) of the 8 tracks shown. Note (CC 50) goes back to the note grid; Push's User mode is
   left alone. Clip launching waits for the clip launcher (F8, step FT-C2d). Event driven: a timer runs only while a section is queued, and
   while the song plays in Session a check 4 times a second follows the section under the playhead. */
const P1C={SC:36,SES:51,q:null,qT:0,firing:false,iv:0,cur:null,OPT:[['bar','Next bar'],['sec','End of the section'],['now','At once']]};
window.P1C=P1C;
const p1cSecs=()=>(S.sections||[]).filter(s=>s&&s.len>0).slice().sort((a,b)=>a.start-b.start);
const p1cNow=()=>play.on?curBeat():pos;
const p1cCur=()=>{const b=p1cNow();return p1cSecs().find(s=>b>=s.start-1e-6&&b<s.start+s.len-1e-6)||null};
const p1cMode=()=>{const v=UI.p1&&UI.p1.sq;return P1C.OPT.some(o=>o[0]===v)?v:'bar'};
const p1cOn=d=>!!(d&&d.p1&&d.p1.ses&&!d.p1.scales);
/* does the track play something in the section: a note starting inside it, or an audio clip over it (a group: any track in it) */
function p1cHas(t,s,dep){const a=s.start,e=s.start+s.len;for(const c of t.clips||[]){if(c.mute)continue;const c0=c.start,c1=c.start+c.len;if(c1<=a||c0>=e)continue;
    if(!c.notes)return true;const o=c.off||0;for(const n of c.notes){const b=c0+n.s-o;if(b>=a&&b<e&&b>=c0&&b<c1)return true}}
  if(t.kind==='group'&&(dep|0)<4)for(const m of S.tracks)if(m.grp===t.id&&p1cHas(m,s,(dep|0)+1))return true;return false}
/* launch: stopped, play from the section; playing, jump at the next bar, at the end of the section playing, or at once */
function p1cJump(s){P1C.firing=true;try{if(play.on)stop();pos=s.start;start()}finally{P1C.firing=false}P1C.q=null;p1All()}
function p1cLaunch(s,now){if(!s)return;clearTimeout(P1C.qT);P1C.qT=0;
  if(P1C.q&&P1C.q.id===s.id&&!now){P1C.q=null;p1All();return}
  if(!play.on){P1C.q=null;pos=s.start;start();p1All();return}
  const m=now?'now':p1cMode(),b=curBeat();if(m==='now'){p1cJump(s);return}
  let at=Math.ceil(b/4-1e-6)*4;if(at-b<.02)at+=4;if(m==='sec'){const c=p1cCur();if(c)at=c.start+c.len}
  P1C.q={id:s.id,at};p1cArm();p1All()}
function p1cArm(){clearTimeout(P1C.qT);P1C.qT=0;const q=P1C.q;if(!q||!play.on)return;const b=curBeat(),ms=Math.max(0,(secOf(q.at)-secOf(b))*1000);
  P1C.qT=setTimeout(()=>{P1C.qT=0;const q2=P1C.q;if(!q2||q2!==q||!play.on)return;if(q.at-curBeat()>.02){p1cArm();return}const s=p1cSecs().find(x=>x.id===q.id);if(s)p1cJump(s);else{P1C.q=null;p1All()}},ms)}
/* the grid: 8 tracks across from the track bank, 8 sections down from the section offset */
function p1cPads(d){const st=d.p1,b=p1b(d),row=p1bRow(d),ss=p1cSecs(),so=st.so|0,cur=p1cCur(),q=P1C.q;
  for(let r=0;r<8;r++){const s=ss[so+r];for(let x=0;x<8;x++){const n=36+(7-r)*8+x,t=row[x];let c=0;
    if(s&&t&&p1cHas(t,s))c=q&&q.id===s.id?3:play.on&&cur&&cur.id===s.id?21:p1Col(t.color);
    if(st.led.get(n)!==c){st.led.set(n,c);p1Send(d,[0x90,n,c])}}}}
function p1cDisp(d){const st=d.p1,b=p1b(d),row=p1bRow(d),ss=p1cSecs(),so=st.so|0,cur=p1cCur(),q=P1C.q,qs=q&&ss.find(s=>s.id===q.id),k=b.em==='pan'?'hp:':'hd:';
  p1Line(d,0,p1Cell8(p1b8(row.map(x=>(x.id===selT?'>':'')+p1bA(x.name)))));
  p1Line(d,1,p1Cell8(p1b8(row.map(x=>{const C=CT.get(k+x.id);return C?p1bA(C.spec.f(C.get())):''}))));
  const bars=qs&&play.on?Math.max(0,Math.ceil((q.at-curBeat())/4)):0;
  p1Line(d,2,p1Cell([cur?'Now: '+p1bA(cur.name):ss.length?'Now: no section':'No sections yet',qs?'Next: '+p1bA(qs.name):'',qs&&play.on?'in '+bars+' bar'+(bars===1?'':'s'):'Launch: '+(P1C.OPT.find(o=>o[0]===p1cMode())||P1C.OPT[0])[1],'Note: back']));
  p1Line(d,3,ss.length?p1Cell8(p1b8(ss.slice(so,so+8).map(s=>p1bA(s.name)))):p1Cell(['Add sections in','the ruler to','launch them here','']))}
function p1cBtns(d){const st=d.p1,set=(cc,v)=>{if(st.btn.get(cc)!==v){st.btn.set(cc,v);p1Send(d,[0xB0,cc,v])}};set(P1C.SES,p1cOn(d)?4:1);
  const ss=p1cSecs(),so=st.so|0,cur=p1cCur(),q=P1C.q,on=p1cOn(d);
  for(let r=0;r<8;r++){const s=ss[so+r];set(P1C.SC+r,!on||!s?0:q&&q.id===s.id?16:play.on&&cur&&cur.id===s.id?22:7)}}
/* the painters and the message handler grow Session (wrapped once, outside FT-C2b's wrappers) */
{const _d=p1Disp;p1Disp=function(d){if(p1cOn(d))return p1cDisp(d);return _d.apply(this,arguments)}}
{const _p=p1Pads;p1Pads=function(d){if(p1cOn(d))return p1cPads(d);return _p.apply(this,arguments)}}
{const _b=p1Btns;p1Btns=function(d){const r=_b.apply(this,arguments);if(d&&d.p1)p1cBtns(d);return r}}
{const pf=CTL.profs.find(p=>p.id==='push1'),_m=pf.msg;pf.msg=function(d,a){const st=d.p1,s=a[0],c=s&0xf0;if(!st||s>=0xF0||ML.on)return _m.apply(this,arguments);
  if(c===0xB0){const n=a[1],v=a[2],on=v>0;
    if(n===P1C.SES){if(on){st.ses=!st.ses;if(st.ses)st.scales=false;p1Paint(d);p1cFollow()}return}
    if(n===P1.CC.note){if(on&&st.ses){st.ses=false;p1Paint(d)}return _m.apply(this,arguments)}
    if(!p1cOn(d))return _m.apply(this,arguments);
    const ms=ctlIndex().byM.get(ctlKey('cc',s&15,n));if(ms&&ms.some(m=>m.dev==='*'||m.dev===d.name))return _m.apply(this,arguments);/* a learned mapping wins */
    const b=p1b(d),C=P1B.CC;
    if(n>=P1C.SC&&n<P1C.SC+8){if(on)p1cLaunch(p1cSecs()[(st.so|0)+n-P1C.SC],b.shift);return}
    if(P1.ENC.includes(n)){const i=P1.ENC.indexOf(n),t=p1bRow(d)[i],dl=v<64?v:v-128,id=t&&(b.em==='pan'?'hp:':'hd:')+t.id;if(id&&CT.has(id))p1bNudge(d,id,dl/127*(b.shift?.1:1));p1Disp(d);return}
    if(n===C.up||n===C.down||n===C.left||n===C.right){if(on){const k=b.shift?8:1;
        if(n===C.up||n===C.down)st.so=clamp((st.so|0)+(n===C.down?k:-k),0,Math.max(0,p1cSecs().length-8));else b.tb=clamp(b.tb+(n===C.right?k:-k),0,Math.max(0,S.tracks.length-8));p1All()}return}
    return _m.apply(this,arguments)}
  if((c===0x90||c===0x80)&&a[1]>=36&&a[1]<=99&&p1cOn(d)){if(c===0x90&&a[2]>0){const x=(a[1]-36)%8,r=7-((a[1]-36)>>3),t=p1bRow(d)[x],sc=p1cSecs()[(st.so|0)+r];
      if(t&&t.id!==selT)selectTrack(t.id);if(sc)p1cLaunch(sc,p1b(d).shift)}return}
  return _m.apply(this,arguments)}}
/* while the song plays in Session: follow the section under the playhead (4 times a second, only then); a user's stop clears the queue */
const p1cAny=()=>{for(const d of CTL.devs.values())if(d.prof&&d.prof.id==='push1'&&!ctlOff(d)&&p1cOn(d))return true;return false};
function p1cFollow(){if(P1C.iv||!play.on||!p1cAny())return;P1C.cur=null;P1C.iv=setInterval(()=>{if(!play.on||!p1cAny()){clearInterval(P1C.iv);P1C.iv=0;return}const c=p1cCur(),k=(c?c.id:'')+':'+(P1C.q?Math.ceil((P1C.q.at-curBeat())/4):'');if(k!==P1C.cur){P1C.cur=k;p1All()}},250)}
{const _s=start;start=function(){const r=_s.apply(this,arguments);try{p1cFollow();if(P1C.q&&!P1C.firing)p1cArm()}catch(e){}return r}}
{const _t=stop;stop=function(){if(!P1C.firing&&(P1C.q||P1C.qT)){clearTimeout(P1C.qT);P1C.qT=0;P1C.q=null}return _t.apply(this,arguments)}}
/* the Launch setting on the Controllers page, beside the other Push 1 settings */
{const _p=ctlPagePaint;ctlPagePaint=function(){const r=_p.apply(this,arguments);const w=CTL.host&&CTL.host.querySelector('.p1set .cbar');if(w&&!w.querySelector('[data-p1c]')){const tip='Session mode on the Push: when a section you launch starts while the song plays';
  const l=document.createElement('label');l.title=tip;l.innerHTML=`Launch <select data-p1c="sq" title="${tip}">${P1C.OPT.map(([v,t])=>`<option value="${v}"${p1cMode()===v?' selected':''}>${t}</option>`).join('')}</select>`;w.appendChild(l);
  l.querySelector('select').addEventListener('change',e=>{e.stopPropagation();p1Set('sq',e.target.value);p1All()})}
  const h=CTL.host&&CTL.host.querySelector('.p1set .p1help');if(h&&!h.dataset.c2c){h.dataset.c2c=1;h.textContent+=' Session: the pads and the buttons on the right launch the song’s sections (8 tracks across, 8 sections down); Note goes back.'}return r}}
FT_HOOKS.push1Launch=(id,now)=>p1cLaunch(p1cSecs().find(s=>s.id===id),!!now);
