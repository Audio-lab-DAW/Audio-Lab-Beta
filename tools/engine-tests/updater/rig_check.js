// reproduce: what happens when the page calls checkForUpdates in the current app
const {app,BrowserWindow,dialog}=require('electron');const fs=require('fs'),http=require('http'),path=require('path'),crypto=require('crypto');
const R=require('path').join(__dirname,'..','..','..'),T=require('path').join(require('os').tmpdir(),'al-upd-rig');fs.mkdirSync(T,{recursive:true});
fs.rmSync(T+'/userdata',{recursive:true,force:true});
app.setPath('userData',T+'/userdata');const _sp=app.setPath.bind(app);app.setPath=(k,v)=>{if(k==='userData')return;return _sp(k,v)};
app.getVersion=()=>process.env.SHELLV||'0.170.0';
const mode=process.env.MODE||'same';const log=[];
const cur=fs.readFileSync(R+'/index.html','utf8');const next=cur.replace(/const VERSION='0\.(\d+)'/,(m,n)=>"const VERSION='0."+(+n+1)+"'");
const nv=next.match(/const VERSION='([\d.]+)'/)[1],cv=cur.match(/const VERSION='([\d.]+)'/)[1];
const man=(html,v)=>JSON.stringify({version:v,sha256:crypto.createHash('sha256').update(Buffer.from(html,'utf8')).digest('hex'),size:Buffer.byteLength(html),minShell:'0.147.0',notes:'Test notes for '+v});
const srv=http.createServer((q,r)=>{const u=q.url.split('?')[0];log.push('GET '+u);if(mode==='hang')return;if(mode==='down'){r.statusCode=503;return r.end()}
 if(u.endsWith('app-version.json'))r.end(mode==='new'?man(next,nv):man(cur,cv));else if(u.endsWith('index.html'))r.end(mode==='new'?next:cur);else{r.statusCode=404;r.end()}});
srv.listen(18765,'127.0.0.1');
dialog.showMessageBox=(w,o)=>{log.push('DIALOG '+(o.message||'')+' | '+(o.detail||'').slice(0,60)+' | '+(o.buttons||[]).join('/'));return Promise.resolve({response:1})};
process.argv.push('--no-sandbox');
require(R+'/desktop/main.js');
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const js=c=>BrowserWindow.getAllWindows()[0].webContents.executeJavaScript(c,true).catch(e=>'err '+e.message);
(async()=>{await wait(6000);log.push('ver '+await js("window.AudioLab.run('VERSION')"));
 const steps=(process.env.STEPS||'click').split(',');
 for(const s of steps){
  if(s==='click'){log.push('click genUpd: '+await js("(()=>{openSettings('general');const b=document.getElementById('genUpd');if(!b)return 'no button';if(b.hidden)return 'hidden';b.click();return 'clicked'})()"));await wait(3000)}
  if(s==='about'){log.push('about: '+await js("(()=>{const f=window.AudioLab.run('typeof openAbout');return f})()"))}
  if(s==='wait')await wait(9000);if(s==='wait20')await wait(20000);
  if(s==='card')log.push('card: '+await js("(()=>{const c=document.getElementById('updCard');return !c?'none':c.hidden?'hidden':c.innerText.replace(/\\n/g,' / ')})()"));
  if(s==='later')log.push('later: '+await js("(()=>{const c=document.getElementById('updCard');if(!c)return 'none';c.querySelector('[data-u=later]').click();return 'ok'})()"));
 }
 console.log('RESULT '+JSON.stringify({mode,log},null,1));app.exit(0)})();
