// v0.207 (task Y): the centred update window in the real desktop app (today's main.js and preload.js), no system dialogs.
//   node desktop/scripts/sync-app.js; AL_UPDATE_BASE=http://127.0.0.1:18765/ MODE=ota xvfb-run -a desktop/node_modules/.bin/electron --no-sandbox tools/engine-tests/updater/test_window.js
// MODE: ota (a newer program is downloaded by the hourly check: window, Restart now, the new version runs) | app (the manifest asks for a newer app)
const {app,BrowserWindow,dialog}=require('electron');const fs=require('fs'),http=require('http'),path=require('path'),crypto=require('crypto'),os=require('os');
const R=path.join(__dirname,'..','..','..'),T=path.join(os.tmpdir(),'al-upd-window');fs.rmSync(T,{recursive:true,force:true});fs.mkdirSync(T,{recursive:true});
app.setPath('userData',path.join(T,'userdata'));const _sp=app.setPath.bind(app);app.setPath=(k,v)=>{if(k==='userData')return;return _sp(k,v)};
const mode=process.env.MODE||'ota',log=[];
const cur=fs.readFileSync(path.join(R,'index.html'),'utf8'),cv=cur.match(/const VERSION='([\d.]+)'/)[1];
const next=cur.replace(/const VERSION='0\.(\d+)'/,(m,n)=>"const VERSION='0."+(+n+1)+"'"),nv=next.match(/const VERSION='([\d.]+)'/)[1];
app.getVersion=()=>cv+'.0';
const man=JSON.stringify({version:nv,sha256:crypto.createHash('sha256').update(Buffer.from(next,'utf8')).digest('hex'),size:Buffer.byteLength(next),minShell:mode==='app'?'9.0.0':'0.147.0',notes:'Notes for '+nv});
http.createServer((q,r)=>{const u=q.url.split('?')[0];if(u.endsWith('app-version.json'))r.end(man);else if(u.endsWith('index.html'))r.end(next);else{r.statusCode=404;r.end()}}).listen(18765,'127.0.0.1');
dialog.showMessageBox=(w,o)=>{log.push('SYSTEM DIALOG '+(o.message||''));return Promise.resolve({response:1})};
require(path.join(R,'desktop','main.js'));
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const js=c=>BrowserWindow.getAllWindows()[0].webContents.executeJavaScript(c,true).catch(e=>'err '+e.message);
const W="(()=>{const m=document.getElementById('uywM');if(!m)return 'no window';return m.querySelector('h3').textContent+' | '+m.querySelector('.uywv').innerText.replace(/\\n/g,' ')+' | '+[...m.querySelectorAll('.uywb button')].map(b=>b.textContent).join('/')})()";
const shot=async n=>{try{const im=await BrowserWindow.getAllWindows()[0].webContents.capturePage();fs.writeFileSync(path.join(process.env.SHOTS||T,n+'.png'),im.toPNG())}catch(e){}};
(async()=>{await wait(16000);log.push('version '+await js("window.AudioLab.run('VERSION')"));log.push('window: '+await js(W));await shot('electron-'+mode);
  if(mode==='ota'){await js("document.querySelector('#uywM [data-uy=go]').click()");await wait(9000);log.push('after: version '+await js("window.AudioLab.run('VERSION')")+' window: '+await js(W)+' card: '+await js("(()=>{const c=document.getElementById('updCard');return !c||c.hidden?'none':c.innerText.replace(/\\n/g,' / ')})()"));await shot('electron-after')}
  console.log('RESULT '+JSON.stringify({mode,log},null,1));app.exit(0)})();
