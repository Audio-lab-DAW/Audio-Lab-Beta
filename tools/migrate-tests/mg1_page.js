/* ===== task MG1 (the path to the native app; window built on lane F's overlay tokens --ov-*, LOOK units in amber) =====
   The user's wish (27 Nov 2026, 19:36): people on the Electron app update from inside the app to the native AudioLab. A window in the centre
   explains the move and stays until the user clicks: Install now or Later (the close cross and Esc are Later, Enter is Install now).
   It shows when the desktop shell offers a native build for this computer (the "native" block of the update manifest, desktop/native-migrate.js)
   and Later was not chosen in the last 3 days; it waits while something plays, records or exports, and while the update window is open.
   The offer also stays in the Updates window, the app menu (Install the native AudioLab…) and the command list.
   Install now: download with progress and the checksum (desktop), then every project (open tabs and Saved projects, as .audiolab files with their
   audio), the settings, presets, controller mappings, the recent list and the icon choice are written to the folder the native app reads
   (docs/native-migration.md), then the shell installs and opens the native app and quits. Nothing of this app or its data is deleted. */
const MGS={st:null,open:false,ph:'offer',ret:null,wait:0,err:null,dl:null,exp:null,tgt:'',unsub:null,tick:0};
function mgD(){const D=window.audiolabDesktop;return D&&D.nativeMigrate||null}
function mgMB(b){const m=(+b||0)/1048576;return m>=100?Math.round(m)+'':m>=10?m.toFixed(0):m.toFixed(1)}
/* about how long: the download at 25 Mbit/s (fast) and 5 Mbit/s (slow), plus about half a minute to install */
function mgTime(b){const f=Math.max(1,Math.round(((+b||0)/3.1e6+30)/60)),s=Math.max(f+1,Math.round(((+b||0)/6.2e5+30)/60));return f>=s?`about ${f} minute${f>1?'s':''}`:`about ${f} minute${f>1?'s':''} on a fast connection, up to ${s} on a slow one`}
function mgCss(){if(document.getElementById('mgCss'))return;const s=document.createElement('style');s.id='mgCss';s.textContent=`
#mgM{position:fixed;inset:0;z-index:2147480500;display:grid;place-items:center;background:rgba(4,5,8,.5)}
@media (prefers-reduced-motion:no-preference){body:not(.lite):not(.lkm1) #mgM{animation:mgF calc(var(--ov-mo,1)*var(--ov-sheet,140ms)) var(--ov-ease,ease-out)}body:not(.lite):not(.lkm1) #mgM .mgw{animation:mgP calc(var(--ov-mo,1)*var(--ov-sheet,140ms)) var(--ov-ease,ease-out)}}
@keyframes mgF{from{opacity:0}to{opacity:1}}@keyframes mgP{from{opacity:0;transform:translateY(6px) scale(.985)}to{opacity:1;transform:none}}
#mgM .mgw{position:relative;box-sizing:border-box;width:min(520px,calc(100vw - 32px));max-height:calc(100vh - 40px);display:flex;flex-direction:column;padding:22px 24px 16px;border-radius:16px;background:rgba(var(--gtr,19,20,27),.97);border:1px solid rgba(255,255,255,.15);box-shadow:0 30px 90px rgba(0,0,0,.62),inset 0 1px 0 rgba(255,255,255,.07);color:#e8eaf0;font-size:var(--fs2,12px);line-height:1.5}
body.gls #mgM .mgw,body.lite #mgM .mgw{background:rgb(var(--gtr2,19,20,27))}
#mgM .mgx{position:absolute;top:12px;right:12px;width:30px;height:30px;padding:0!important;border-radius:9px;line-height:1;font-size:var(--fs3,13px)}
#mgM .mglab{font:var(--ov-lab);letter-spacing:var(--ov-labsp);text-transform:uppercase;color:var(--ov-mut,#8b8b97);margin:0 40px 8px 0}#mgM .mglab i{font-style:normal;color:var(--ov-amb,#ffb547)}
#mgM h3{margin:0 40px 4px 0;font:var(--fw6,600) var(--fs4,16px) var(--ffu,inherit);color:#f2f4f8}#mgM .mgsub{margin:0 0 12px;color:#9ba0ad}
#mgM .mgsc{flex:1 1 auto;min-height:40px;overflow:auto;overscroll-behavior:contain;margin:0 -6px 8px 0;padding-right:6px}
#mgM h5{margin:10px 0 4px;font:var(--fw6,600) var(--fs1,11px) var(--ffu,inherit);color:#9a9da9}#mgM ul{margin:0;padding:0 0 0 18px;display:grid;gap:3px;color:#d9dce4}
#mgM .mgnote{margin:10px 0 0;padding:8px 10px;border-radius:var(--ov-r-card,9px);color:#f6dfb4;background:rgba(245,160,76,.1);border:1px solid rgba(245,160,76,.4)}
#mgM .mgfacts{display:flex;flex-wrap:wrap;gap:6px 14px;margin:10px 0 0;padding:8px 10px;border-radius:var(--ov-r-card,9px);background:rgba(6,7,10,.45);border:1px solid var(--ov-ln,rgba(255,255,255,.09));font:var(--ov-key);color:#c9ccd6}#mgM .mgfacts u{text-decoration:none;color:var(--ov-amb,#ffb547)}
#mgM ol.mgst{list-style:none;margin:4px 0 0;padding:0;display:grid;gap:7px}#mgM ol.mgst li{display:grid;grid-template-columns:18px 1fr auto;gap:8px;align-items:center;color:#9ba0ad}
#mgM ol.mgst li b{font-weight:var(--fw5,500)}#mgM ol.mgst li.on{color:#eef0f5}#mgM ol.mgst li.ok{color:#bfe9d2}#mgM ol.mgst li.bad{color:#ffb4a8}
#mgM ol.mgst li>i{width:10px;height:10px;border-radius:50%;border:1.5px solid currentColor;justify-self:center}#mgM ol.mgst li.ok>i{background:#3ecf8e;border-color:#3ecf8e}#mgM ol.mgst li.on>i{border-color:var(--ov-amb,#ffb547);border-top-color:transparent;animation:mgSp calc(var(--ov-mo,1)*900ms) linear infinite}#mgM ol.mgst li.bad>i{background:#ff6b5a;border-color:#ff6b5a}
@keyframes mgSp{to{transform:rotate(360deg)}}#mgM ol.mgst li small{font:var(--ov-key);color:var(--ov-mut,#8b8b97)}
#mgM .mgbar{grid-column:2/4;height:6px;border-radius:3px;background:rgba(255,255,255,.08);overflow:hidden}#mgM .mgbar>span{display:block;height:100%;width:0;background:var(--ov-amb,#ffb547);transition:width .12s linear}
#mgM .mgerr{margin:10px 0 0;padding:8px 10px;border-radius:var(--ov-r-card,9px);color:#ffd2cb;background:rgba(255,107,90,.1);border:1px solid rgba(255,107,90,.45)}
#mgM .mgb{flex:none;display:flex;align-items:center;justify-content:flex-end;gap:8px;padding-top:10px;border-top:1px solid var(--ov-ln,rgba(255,255,255,.09))}#mgM .mgb .mgsp{flex:1}
#mgM .mgb{flex-wrap:wrap}#mgM .mgb button{min-width:96px;height:32px;padding:0 12px;white-space:nowrap;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;gap:8px}#mgM .mgb button.pri{background:#3ecf8e;color:#04140c;border-color:#3ecf8e;font-weight:var(--fw6,600)}
#mgM .mgb kbd{font:var(--ov-key);font-size:10px;opacity:.7;padding:0 4px;border-radius:4px;border:1px solid currentColor}
#mgM .mgb button:focus-visible{outline:2px solid var(--ov-hi,#4c8dff);outline-offset:2px}
#updDlg .mgur{display:flex;align-items:center;gap:10px;margin:10px 0 0;padding:9px 11px;border-radius:10px;background:rgba(62,207,142,.08);border:1px solid rgba(62,207,142,.4)}#updDlg .mgur div{flex:1;display:grid;line-height:1.4}#updDlg .mgur small{color:#9ba0ad}`;document.head.appendChild(s)}
async function mgRefresh(){const N=mgD();if(!N)return null;try{MGS.st=await N.status()}catch(e){MGS.st=null}try{mgUpdRow()}catch(e){}return MGS.st}
function mgBusy(){try{if(typeof uywBusy==='function'&&uywBusy())return true}catch(e){}try{if(typeof UYW!=='undefined'&&UYW.open)return true}catch(e){}return false}
/* shows the window when it is due; while something plays, records or exports (or the update window is open) it waits until that has been quiet for 1.5 s */
function mgMaybe(){const s=MGS.st;if(!s||!s.offer||!s.due||MGS.open)return;if(!mgBusy()){mgOpen(false);return}
  clearInterval(MGS.wait);let q=0;MGS.wait=setInterval(()=>{if(MGS.open||!MGS.st||!MGS.st.due){clearInterval(MGS.wait);return}if(mgBusy()){q=0;return}if(++q>=3){clearInterval(MGS.wait);mgOpen(false)}},500)}
function mgOpen(byUser){const N=mgD();if(!N){toast('The native AudioLab is installed from the desktop app.');return false}
  if(!MGS.st||!MGS.st.offer){if(byUser)mgRefresh().then(s=>{if(s&&s.offer)mgOpen(true);else toast('No native AudioLab is offered for this computer yet.')});return false}
  mgCss();clearInterval(MGS.wait);if(MGS.open){mgPaint();return true}
  if(MGS.ph==='done'||MGS.ph==='err'||MGS.ph==='blocked'){if(MGS.ph!=='blocked')MGS.ph='offer'}
  MGS.ret=document.activeElement;MGS.open=true;
  const m=document.createElement('div');m.id='mgM';m.innerHTML='<div class="mgw" role="dialog" aria-modal="true" aria-labelledby="mgT" aria-describedby="mgS"><button type="button" class="mgx" data-mg="later" aria-label="Later (Esc)" title="Later (Esc): ask again in 3 days. The offer stays in the Updates window and the app menu.">✕</button><div class="mgbody"></div></div>';
  document.body.appendChild(m);
  m.addEventListener('click',e=>{const b=e.target.closest('[data-mg]');if(b&&!b.disabled)mgAct(b.dataset.mg)});   /* a click beside the window does nothing: it stays until a button is clicked */
  document.addEventListener('keydown',mgKey,true);mgPaint();setTimeout(()=>mgFocus(),30);return true}
/* from the menu, the command list or the Updates window: the window, or, once the native app is installed, open it */
async function mgGo(byUser){const N=mgD(),s=MGS.st;if(N&&s&&s.offer&&s.installed&&updCmp(s.installed.version,s.offer.version)>=0&&!MGS.open){let ok=false;try{ok=await N.open()}catch(e){}if(ok)return true;MGS.tgt=s.installed.path||'';MGS.ph=mgPlat()==='darwin'?'blocked':'offer'}return mgOpen(byUser)}
function mgFocus(){const m=document.getElementById('mgM');if(!m)return;const f=m.querySelector('.mgb button.pri:not([disabled])')||m.querySelector('.mgb button:not([disabled])')||m.querySelector('.mgx');if(f)f.focus()}
function mgKey(e){if(!MGS.open)return;const m=document.getElementById('mgM');if(!m)return;
  if(e.key==='Escape'){e.preventDefault();e.stopPropagation();if(MGS.ph==='offer'||MGS.ph==='err'||MGS.ph==='blocked')mgAct('later');else if(MGS.ph==='dl')mgAct('cancel');return}
  if(e.key==='Enter'&&!e.isComposing){const t=e.target&&e.target.closest&&e.target.closest('#mgM button');e.preventDefault();e.stopPropagation();if(t&&!t.disabled){t.click();return}const p=m.querySelector('.mgb button.pri:not([disabled])');if(p)p.click();return}
  if(e.key==='Tab'){const L=[...m.querySelectorAll('button:not([disabled])')];if(!L.length)return;const i=L.indexOf(document.activeElement);e.preventDefault();e.stopPropagation();L[(i+(e.shiftKey?-1:1)+L.length)%L.length].focus();return}
  if(!(e.target&&e.target.closest&&e.target.closest('#mgM'))){e.stopPropagation()}}   /* the app's own shortcuts wait while the window is open */
function mgClose(){const m=document.getElementById('mgM');if(m)m.remove();document.removeEventListener('keydown',mgKey,true);MGS.open=false;const r=MGS.ret;MGS.ret=null;try{if(r&&r.focus&&r.isConnected)r.focus()}catch(e){}}
function mgPlat(){const D=window.audiolabDesktop;return(D&&D.platform)||''}
function mgPaint(){const m=document.getElementById('mgM');if(!m)return;const s=MGS.st||{},o=s.offer||{},mac=mgPlat()==='darwin',win=mgPlat()==='win32';
  const B=(k,t,tip,pri,kb)=>`<button type="button" data-mg="${k}"${pri?' class="pri"':''} title="${esc(tip)}">${esc(t)}${kb?`<kbd>${kb}</kbd>`:''}</button>`;
  const lab=`<p class="mglab">Native app · ${esc(o.version||'')} · ${mgMB(o.size)} <i>MB</i></p>`;let body='',btn='';
  m.querySelector('.mgx').hidden=!(MGS.ph==='offer'||MGS.ph==='err'||MGS.ph==='blocked');
  if(MGS.ph==='offer'){
    body=`${lab}<h3 id="mgT">AudioLab is becoming a native app</h3><p class="mgsub" id="mgS">A new AudioLab, built for ${mac?'the Mac':win?'Windows':'this computer'} itself instead of running in a browser engine.</p><div class="mgsc">
      <h5>What changes</h5><ul><li>Its own sound engine: lower latency and steadier playback.</li><li>VST3 plug-ins open inside AudioLab, next to its own devices.</li><li>The same look: the same screens, colours and controls.</li></ul>
      <h5>What comes along</h5><ul><li>Every project: the open tabs and your Saved projects, with their audio.</li><li>Your settings, presets, controller mappings, the app icon you picked and the recent list.</li><li>This app stays on your computer with everything in it, so you can go back.</li></ul>
      <div class="mgfacts"><span>Download <u>${mgMB(o.size)} MB</u></span><span>${esc(mgTime(o.size))}</span>${o.minOS?`<span>Needs ${mac?'macOS':win?'Windows':'OS'} ${esc(o.minOS)} or later</span>`:''}</div>
      ${o.notes?`<h5>About this version</h5><ul>${String(o.notes).split(/\n+/).filter(Boolean).slice(0,4).map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:''}
      <p class="mgnote">${mac?'It goes into Applications (or your own Applications folder if that one is locked). It is not signed by Apple yet: AudioLab removes the download mark from the copy it installs itself, so macOS normally opens it straight away. If macOS still asks, this window shows where to click (Open Anyway).':win?'It installs for your user account only, no administrator password. If Windows shows “Windows protected your PC”, click More info, then Run anyway: the installer is not signed yet.':'The native app is installed next to this one.'}</p></div>`;
    btn=`<span class="mgsp"></span>${B('later','Later','Keep working with this app. Asked again in 3 days; the offer stays in the Updates window and the app menu.',0,'Esc')}${B('go','Install now','Download, check and install the native AudioLab, bring your projects and settings along, then open it',1,'↵')}`}
  else if(MGS.ph==='err'){const E=MGS.err||{};
    const why=E.why==='checksum'?'The download did not match its checksum, so nothing was installed. It may have been damaged on the way, or the release is still being published.':E.why==='signature'?'The download is not signed with AudioLab’s key, so nothing was installed.':E.why==='size'?'The download was incomplete, so nothing was installed.':E.why==='cancelled'?'The download was stopped. Nothing was installed.':E.stage==='export'?'Your projects and settings could not be written for the native app, so nothing was installed. They are all still here.':E.stage==='install'?'The native app could not be put in place. This app and your projects are unchanged.':'The native AudioLab could not be downloaded. Nothing was installed.';
    body=`${lab}<h3 id="mgT">The native AudioLab was not installed</h3><p class="mgsub" id="mgS">${esc(why)}</p><div class="mgsc">${mgSteps()}${E.error?`<p class="mgerr">${esc(E.error)}</p>`:''}</div>`;
    btn=`<span class="mgsp"></span>${B('later','Later','Keep working with this app. Asked again in 3 days.',0,'Esc')}${B('go','Try again','Download and check it again',1,'↵')}`}
  else if(MGS.ph==='blocked'){
    body=`${lab}<h3 id="mgT">One more step on this Mac</h3><p class="mgsub" id="mgS">The native AudioLab is installed${MGS.tgt?' in '+esc(MGS.tgt.replace(/\/[^/]+$/,'')):''}, but macOS did not let it start yet.</p><div class="mgsc">${mgSteps()}
      <h5>Let it open</h5><ul><li>Open System Settings › Privacy &amp; Security.</li><li>Scroll down to “AudioLab was blocked” and click Open Anyway, then confirm with your password.</li><li>Come back here and click Open it again.</li></ul><p class="mgnote">This is needed once, because the app is not signed by Apple yet. Your projects and settings are already in place for it.</p></div>`;
    btn=`${B('reveal','Show in Finder','Show the native AudioLab in the Finder')}<span class="mgsp"></span>${B('later','Later','Keep working with this app',0,'Esc')}${B('sec','Privacy & Security','Open System Settings › Privacy & Security, where the Open Anyway button is')}${B('again','Open it again','Start the native AudioLab',1,'↵')}`}
  else{const done=MGS.ph==='done';
    body=`${lab}<h3 id="mgT">${done?(win?'The installer is running':'The native AudioLab is opening'):'Installing the native AudioLab'}</h3><p class="mgsub" id="mgS">${done?'This app closes in a moment. Your projects and settings are waiting in the native app.':'Keep this window open. Your work is saved first; nothing is deleted.'}</p><div class="mgsc">${mgSteps()}</div>`;
    btn=MGS.ph==='dl'?`<span class="mgsp"></span>${B('cancel','Cancel','Stop the download. Nothing is installed.',0,'Esc')}`:''}
  m.querySelector('.mgbody').innerHTML=body+`<div class="mgb">${btn}</div>`;m.querySelector('.mgbody').style.cssText='display:flex;flex-direction:column;min-height:0;flex:1 1 auto';
  if(!m.contains(document.activeElement)||document.activeElement===document.body)mgFocus()}
/* the steps with their state: wait, on (running), ok, bad */
function mgSteps(){const st=MGS.ph,E=MGS.err||{},order=['dl','check','exp','inst','open'],at={dl:0,check:1,exp:2,inst:3,open:4,done:5,blocked:4}[st];
  const failAt=st==='err'?{download:0,check:1,export:2,install:3}[E.stage]??0:-1;
  const cls=i=>failAt>=0?(i<failAt?'ok':i===failAt?'bad':''):at==null?'':i<at?'ok':i===at?(st==='blocked'?'bad':'on'):'';
  const d=MGS.dl,x=MGS.exp,mac=mgPlat()==='darwin',win=mgPlat()==='win32';
  const L=[['Download',d?`${mgMB(d.got)} of ${mgMB(d.size)} MB`:'',d&&d.size?Math.min(100,d.got/d.size*100):null],['Check',MGS.how||'sha256',null],['Projects and settings',x?`${x.n} of ${x.of}`:'',null],['Install',win?'run the installer':mac?'copy to Applications':'',null],['Open the native app','',null]];
  return`<ol class="mgst">${L.map((l,i)=>`<li class="${cls(i)}"><i></i><b>${esc(l[0])}</b><small>${esc(l[1])}</small>${i===0&&cls(0)==='on'&&l[2]!=null?`<div class="mgbar"><span style="width:${l[2].toFixed(1)}%"></span></div>`:''}</li>`).join('')}</ol>`}
async function mgAct(k){const N=mgD();if(!N)return;
  if(k==='later'){try{MGS.st=await N.later()}catch(e){}MGS.ph='offer';MGS.err=null;mgClose();try{mgUpdRow()}catch(e){}return}
  if(k==='cancel'){try{await N.cancel()}catch(e){}return}
  if(k==='reveal'){N.reveal('app');return}
  if(k==='sec'){N.reveal('security');return}
  if(k==='again'){const b=document.querySelector('#mgM [data-mg="again"]');if(b){b.disabled=true;b.textContent='Opening…'}let ok=false;try{ok=await N.open()}catch(e){}if(!ok){toast('macOS did not start it yet. Use Open Anyway in Privacy & Security first.');mgPaint()}return}
  if(k==='go')mgInstall()}
async function mgInstall(){const N=mgD();if(!N||MGS.ph==='dl'||MGS.ph==='check'||MGS.ph==='exp'||MGS.ph==='inst')return;
  if(mgBusy()&&!(typeof UYW!=='undefined'&&UYW.open)){toast('Stop playback, recording or the export first.');return}
  MGS.err=null;MGS.dl=null;MGS.exp=null;MGS.how='';MGS.ph='dl';mgPaint();
  const fail=(stage,r)=>{MGS.err={stage,why:r&&r.why||'',error:r&&r.error||String(r||'')};MGS.ph='err';mgPaint();try{N.cancel()}catch(e){}};
  let r;try{r=await N.install()}catch(e){r={ok:false,stage:'download',error:String(e&&e.message||e)}}
  if(!r||!r.ok){fail(r&&r.stage==='check'?'check':'download',r);return}
  MGS.how=r.how||'sha256';MGS.ph='exp';mgPaint();
  let x;try{x=await mgExport(N)}catch(e){fail('export',{error:String(e&&e.message||e)});return}
  MGS.ph='inst';mgPaint();
  let f;try{f=await N.finish()}catch(e){f={ok:false,error:String(e&&e.message||e)}}
  if(!f||!f.ok){fail('install',f);return}
  MGS.tgt=f.target||'';if(f.opened){MGS.ph='done';mgPaint()}else{MGS.ph='blocked';mgPaint()}}
/* every project and setting, into the folder the native app reads (docs/native-migration.md). Returns { files, projects }. */
async function mgExport(N){try{stop()}catch(e){}try{saveProjects()}catch(e){}try{saveUINow()}catch(e){}
  try{await N.prepare()}catch(e){}await new Promise(r=>setTimeout(r,400));try{saveProjects()}catch(e){}   /* torn-off projects come home first */
  const b=await N.exportBegin({program:VERSION});if(!b||!b.ok)throw new Error(b&&b.error||'the migrate folder could not be made');
  const put=async(rel,data,kind)=>{const q=await N.exportFile(rel,data,kind);if(!q||!q.ok)throw new Error((q&&q.error)||('could not write '+rel));return q};
  const open=[...(PJ&&PJ.list||[]),...(PJ&&PJ.win||[])],saved=typeof savedList==='function'?savedList().filter(q=>q&&q.S):[];
  /* audio the projects use that is not loaded yet comes from the app's storage first */
  const need=new Set();const walk=o=>{if(!o||typeof o!=='object')return;if(Array.isArray(o)){for(const v of o)walk(v);return}for(const k in o){const v=o[k];if(k==='buf'&&typeof v==='string')need.add(v);else if(v&&typeof v==='object')walk(v)}};
  for(const p of open)walk(p.id===PJ.cur?S:p.S);for(const q of saved)walk(q.S);
  if([...need].some(id=>!BUFS.has(id))){try{await bufRestore()}catch(e){}}
  const missing=[...need].filter(id=>!BUFS.has(id)).length;
  const tot=open.length+saved.length+1;MGS.exp={n:0,of:tot};mgPaint();const tick=()=>{MGS.exp.n++;mgPaint()};
  const idx=[],used=new Set(),nm=(pre,n,i)=>{let f=`projects/${pre}-${String(i).padStart(3,'0')}-${fileSafe(n).replace(/[^\w .()+,-]/g,'_').replace(/[. ]+$/,'')}.audiolab`;while(used.has(f))f=f.replace(/\.audiolab$/,'_.audiolab');used.add(f);return f};
  let i=0;for(const p of open){i++;const blob=await packProject(p),u=new Uint8Array(await blob.arrayBuffer()),f=nm('open',p.name,i);const q=await put(f,u,'project');
    idx.push({file:f,origin:'open',order:i,id:p.id,name:p.name,current:p.id===PJ.cur,tornOff:(PJ.win||[]).includes(p),savedAs:p.file||null,savedAt:p.savedAt||0,unsaved:!!p.dirty,sha256:q.sha256,size:q.size});tick()}
  i=0;for(const q0 of saved){i++;const p={id:'mgsv'+i,name:q0.name,S:q0.S,view:q0.view};const blob=await packProject(p),u=new Uint8Array(await blob.arrayBuffer()),f=nm('saved',q0.name,i);const q=await put(f,u,'project');
    idx.push({file:f,origin:'saved',order:i,name:q0.name,savedAt:q0.t||0,sha256:q.sha256,size:q.size});tick()}
  await put('projects/index.json',JSON.stringify({format:'audiolab-migrate-projects',formatVersion:1,projects:idx},null,1),'index');
  /* settings: every key of the app's storage as it is, and readable copies of the parts the native app needs first */
  const ls={};try{for(let k=0;k<localStorage.length;k++){const key=localStorage.key(k);if(key!=null)ls[key]=localStorage.getItem(key)}}catch(e){}
  await put('settings/local-storage.json',JSON.stringify(ls),'storage');
  const U=typeof UI==='object'&&UI?UI:{},pickK=re=>{const o={};for(const k of Object.keys(U))if(re.test(k))o[k]=U[k];return o};
  await put('settings/ui.json',JSON.stringify(U),'settings');
  await put('settings/presets.json',JSON.stringify(pickK(/^(fxUser|scPre)|[Pp]reset|Tpl$/)),'presets');
  await put('settings/controllers.json',JSON.stringify(Object.assign(pickK(/^(ctl|ml|midi)/i),{midiLearn:typeof ML==='object'&&ML&&ML.maps?ML.maps:undefined})),'controllers');
  await put('recent.json',JSON.stringify({format:'audiolab-migrate-recent',formatVersion:1,current:PJ&&PJ.cur,open:idx.filter(x=>x.origin==='open').map(x=>({name:x.name,file:x.file,savedAs:x.savedAs,current:x.current})),saved:idx.filter(x=>x.origin==='saved').map(x=>({name:x.name,file:x.file,savedAt:x.savedAt}))},null,1),'recent');tick();
  const e=await N.exportEnd({from:{program:VERSION,build:typeof BUILD==='string'?BUILD:''},counts:{projects:idx.length,open:open.length,saved:saved.length,audioMissing:missing}});
  if(!e||!e.ok)throw new Error(e&&e.error||'the export could not be finished');return e}
/* the Updates window keeps the offer */
function mgUpdRow(){const d=document.getElementById('updDlg');if(!d)return;let r=d.querySelector('.mgur');const s=MGS.st,o=s&&s.offer;
  if(!o){if(r)r.remove();return}
  if(!r){const at=d.querySelector('.cdb');if(!at)return;mgCss();r=document.createElement('div');r.className='mgur';at.parentNode.insertBefore(r,at);r.addEventListener('click',e=>{if(e.target.closest('button'))mgGo(true)})}
  const inst=s.installed&&updCmp(s.installed.version,o.version)>=0;
  r.innerHTML=`<div><b>The native AudioLab ${esc(o.version)}</b><small>${inst?'Installed. Your projects came along.':'Its own sound engine, VST3 plug-ins inside, your projects come along. '+mgMB(o.size)+' MB.'}</small></div><button type="button">${inst?'Open it':'Install the native AudioLab…'}</button>`}
if(mgD()){const N=mgD();
  MGS.unsub=N.on(ev=>{if(!ev)return;
    if(ev.type==='offer'){mgRefresh().then(()=>{if(MGS.open&&MGS.ph==='offer'){if(MGS.st&&MGS.st.offer)mgPaint();else mgClose()}else mgMaybe()});return}
    if(ev.type==='progress'){if(ev.stage==='download'){MGS.dl={got:ev.got||0,size:ev.size||0};if(MGS.ph==='dl'&&MGS.open){const bar=document.querySelector('#mgM .mgbar>span'),sm=document.querySelector('#mgM ol.mgst li small');if(bar&&sm){bar.style.width=Math.min(100,(MGS.dl.got/(MGS.dl.size||1))*100).toFixed(1)+'%';sm.textContent=`${mgMB(MGS.dl.got)} of ${mgMB(MGS.dl.size)} MB`}else mgPaint()}}
      else if(ev.stage==='check'&&MGS.open&&MGS.ph==='dl'){MGS.how=ev.how||MGS.how;MGS.ph='check';mgPaint()}
      else if(ev.stage==='open'&&MGS.open&&MGS.ph==='inst'){MGS.ph='open';MGS.tgt=ev.target||MGS.tgt;mgPaint()}return}
    if(ev.type==='opened'){MGS.tgt=ev.target||MGS.tgt;MGS.ph='done';if(MGS.open)mgPaint();return}
    if(ev.type==='blocked'){MGS.tgt=ev.target||MGS.tgt;MGS.ph='blocked';if(!MGS.open)mgOpen(true);else mgPaint()}});
  window.audiolabHost.mgOpen=u=>mgGo(u!==false);
  setTimeout(()=>{mgRefresh().then(mgMaybe)},4000);setInterval(()=>{if(!MGS.open)mgRefresh().then(mgMaybe)},3600000);   /* Later ends after 3 days, also without a restart */
  {const _mo=updOpen;updOpen=function(){const x=_mo.apply(this,arguments);try{if(MGS.st&&MGS.st.offer)mgUpdRow();else mgRefresh()}catch(e){}return x}}
  try{if(typeof SCA!=='undefined'&&typeof SCM!=='undefined'&&!SCM.has('mg.native')){SCA.push({id:'mg.native',g:'help',l:'Install the native AudioLab',d:'the native app: own sound engine, VST3 plug-ins, your projects come along',ic:'M4 4h12v9H4zM8 16h4M10 13v3',run:()=>mgGo(true)});SCM.set('mg.native',SCA[SCA.length-1])}}catch(e){}}
/* ===== end of task MG1 ===== */
