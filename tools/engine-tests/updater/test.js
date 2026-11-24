const {app,BrowserWindow,dialog}=require('electron');const fs=require('fs'),http=require('http'),path=require('path');
app.setPath('userData','/tmp/upd/userdata');app.getVersion=()=>'0.147.0';
let mode=process.env.MODE||'good';const log=[];
const srv=http.createServer((q,r)=>{const u=q.url.split('?')[0];if(u.endsWith('app-version.json')){r.end(fs.readFileSync('/tmp/upd/man_'+mode+'.json'))}else if(u.endsWith('index.html')){r.end(fs.readFileSync('/tmp/upd/'+(mode==='bad'?'bad':'good')+'.html'))}else{r.statusCode=404;r.end()}});
srv.listen(18765,'127.0.0.1');
dialog.showMessageBox=(w,o)=>{log.push((o.message||'')+' | '+(o.buttons||[]).join('/'));return Promise.resolve({response:0})};
process.argv.push('--no-sandbox');
require('/home/claude/audio-lab-beta/desktop/main.js');
const ver=async()=>{const w=BrowserWindow.getAllWindows()[0];try{return await w.webContents.executeJavaScript("window.AudioLab?window.AudioLab.run('VERSION'):document.body.innerText.slice(0,20)")}catch(e){return 'err '+e.message}};
const wait=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{await wait(7000);const v0=await ver();await wait(Number(process.env.WAIT||9000));const v1=await ver();
 let meta={};try{meta=JSON.parse(fs.readFileSync('/tmp/upd/userdata/app-update/meta.json','utf8'))}catch(e){}
 console.log('RESULT '+JSON.stringify({mode,shell:app.getVersion(),before:v0,after:v1,log,meta:{version:meta.version,ok:meta.ok,reverted:meta.reverted}}));app.exit(0)})();
