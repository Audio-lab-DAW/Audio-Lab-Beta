// v0.172: the update window in the real desktop app. Run from the repo root after `cd desktop && npm ci` and `node desktop/scripts/sync-app.js`:
//   MODE=flow xvfb-run -a desktop/node_modules/.bin/electron --no-sandbox tools/engine-tests/updater/test_popup.js
// MODE: flow (update found, Update now, restarts into it) | same | hang | down | auto (installs by itself) | menu
// OLD=<git ref>: use main.js and preload.js of an older app build (for example f8371a1 = v0.170) with today's page.
const {app,BrowserWindow,dialog,Menu}=require('electron');const fs=require('fs'),http=require('http'),path=require('path'),crypto=require('crypto'),os=require('os'),cp=require('child_process');
const R=path.join(__dirname,'..','..','..'),T=path.join(os.tmpdir(),'al-upd-popup');fs.rmSync(T,{recursive:true,force:true});fs.mkdirSync(T,{recursive:true});
app.setPath('userData',path.join(T,'userdata'));const _sp=app.setPath.bind(app);app.setPath=(k,v)=>{if(k==='userData')return;return _sp(k,v)};
const mode=process.env.MODE||'flow',OLD=process.env.OLD||'',log=[];
const cur=fs.readFileSync(path.join(R,'index.html'),'utf8'),cv=cur.match(/const VERSION='([\d.]+)'/)[1];
const next=cur.replace(/const VERSION='0\.(\d+)'/,(m,n)=>"const VERSION='0."+(+n+1)+"'"),nv=next.match(/const VERSION='([\d.]+)'/)[1];
app.getVersion=()=>cv+'.0';
const man=(html,v)=>JSON.stringify({version:v,sha256:crypto.createHash('sha256').update(Buffer.from(html,'utf8')).digest('hex'),size:Buffer.byteLength(html),minShell:'0.147.0',notes:'Notes for '+v});
const isNew=()=>mode==='flow'||mode==='auto'||mode==='menu';
http.createServer((q,r)=>{const u=q.url.split('?')[0];if(mode==='hang')return;if(mode==='down'){r.statusCode=503;return r.end()}
  if(u.endsWith('app-version.json'))r.end(isNew()?man(next,nv):man(cur,cv));else if(u.endsWith('index.html'))r.end(isNew()?next:cur);else{r.statusCode=404;r.end()}}).listen(18765,'127.0.0.1');
dialog.showMessageBox=(w,o)=>{log.push('SYSTEM DIALOG '+(o.message||'')+' | '+(o.buttons||[]).join('/'));return Promise.resolve({response:0})};
process.argv.push('--no-sandbox');
let mainDir=path.join(R,'desktop');
if(OLD){mainDir=path.join(T,'old');fs.mkdirSync(mainDir);for(const f of['main.js','preload.js'])fs.writeFileSync(path.join(mainDir,f),cp.execSync(`git -C ${JSON.stringify(R)} show ${OLD}:desktop/${f}`));
  fs.cpSync(path.join(R,'desktop','app'),path.join(mainDir,'app'),{recursive:true});fs.symlinkSync(path.join(R,'desktop','node_modules'),path.join(mainDir,'node_modules'));
  fs.writeFileSync(path.join(mainDir,'app','_man.json'),isNew()?man(next,nv):man(cur,cv))}
require(path.join(mainDir,'main.js'));
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const js=c=>BrowserWindow.getAllWindows()[0].webContents.executeJavaScript(c,true).catch(e=>'err '+e.message);
const dlg="(()=>{const d=document.getElementById('updDlg');if(!d)return 'no window';return d.querySelector('.upds').textContent+' || '+d.querySelector('.updg').innerText.replace(/\\n/g,' ')+' || '+[...d.querySelectorAll('.cdb button')].map(b=>b.textContent).join('/')})()";
const card="(()=>{const c=document.getElementById('updCard');return !c?'none':c.hidden?'hidden':c.innerText.replace(/\\n/g,' / ')})()";
const shot=async n=>{try{const im=await BrowserWindow.getAllWindows()[0].webContents.capturePage();fs.writeFileSync(path.join(process.env.SHOTS||T,n+'.png'),im.toPNG())}catch(e){}};
(async()=>{await wait(6000);log.push('version '+await js("window.AudioLab.run('VERSION')")+' has updateCheck:'+await js("!!window.audiolabDesktop.updateCheck"));
  if(OLD)await js("window.AudioLab.run(\"UPDU.man='audiolab://app/_man.json'\")");
  const open="(()=>{window.AudioLab.run(\"openSettings('general')\");document.getElementById('genUpd').click();return 'clicked'})()";
  if(mode==='auto'){await js("window.AudioLab.run('UI.updAuto=true;saveUINow()')");await wait(4500);log.push('card: '+await js(card));await shot('auto-card');await js("window.AudioLab.run('LACT=0')");await wait(20000);log.push('after: version '+await js("window.AudioLab.run('VERSION')")+' card: '+await js(card));await shot('auto-done')}
  else if(mode==='menu'){const find=(items)=>{for(const i of items){if(/Check for Updates/.test(i.label||''))return i;if(i.submenu){const f=find(i.submenu.items);if(f)return f}}};find(Menu.getApplicationMenu().items).click();await wait(2500);log.push('menu -> '+await js(dlg))}
  else{await js(open);await wait(mode==='hang'?(OLD?14000:17000):2500);log.push('window: '+await js(dlg));await shot('popup-'+mode+(OLD?'-old':''));
    if(mode==='hang'||mode==='down'){await js("document.querySelector('#updDlg [data-up=again]').click()");await wait(mode==='hang'?(OLD?14000:17000):2500);log.push('again: '+await js(dlg))}
    if(mode==='flow'){if(process.env.CARDFIRST){await js("document.querySelector('#updDlg [data-up=x]').click()");await wait(6000);log.push('card: '+await js(card));await js(open);await wait(2500)}
      await js("document.querySelector('#updDlg [data-up=go]').click()");await wait(1200);log.push('during: '+await js(dlg));await wait(8000);log.push('after: version '+await js("window.AudioLab.run('VERSION')")+' card: '+await js(card)+' window: '+await js("!!document.getElementById('updDlg')"));await shot('after-flow'+(OLD?'-old':''))}}
  log.push('page errors: '+await js("JSON.stringify((window.__errs||[]))"));
  console.log('RESULT '+JSON.stringify({mode,old:OLD,log},null,1));app.exit(0)})();
