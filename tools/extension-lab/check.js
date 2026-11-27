// Headless checks for the extension lab page. Run: node tools/extension-lab/check.js
// Also writes open.html (the page wrapped so it opens straight from disk) and the example files.
const fs=require('fs'),path=require('path'),{chromium}=require('playwright');
const dir=__dirname,src=fs.readFileSync(path.join(dir,'extensions-round-1.html'),'utf8');
const wrap='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style></head><body>'+src+'</body></html>';
fs.writeFileSync(path.join(dir,'open.html'),wrap);
let pass=0,fail=0;const ok=(c,m)=>{if(c)pass++;else{fail++;console.log('FAIL',m)}};
(async()=>{const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']}),pg=await b.newPage({viewport:{width:1280,height:900}});const errs=[];pg.on('pageerror',e=>errs.push(e.message));pg.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
 const srv=require('http').createServer((q,r)=>{r.setHeader('content-type','text/html');r.end(wrap)}).listen(0);await pg.goto('http://localhost:'+srv.address().port+'/');await pg.waitForTimeout(1500);
 // --- themes
 const th=await pg.evaluate(()=>{const X=EXLAB,o={};for(const k in X.THEME_EX){const r=X.normTheme(X.THEME_EX[k]);o[k]={w:r.warns,e:r.errs,ct:r.t&&r.t._c.cText,ca:r.t&&r.t._c.cAcc}}return o});
 for(const k of['audiolab','jupiter','webb','lab']){ok(!th[k].e.length&&!th[k].w.length,`theme ${k} clean: ${JSON.stringify(th[k])}`);ok(th[k].ct>=4.5&&th[k].ca>=3,`theme ${k} contrast`)}
 ok(th.broken.w.length>=6&&th.broken.ct>=4.5&&th.broken.ca>=3,'broken theme corrected: '+th.broken.w.length);ok(th.broken.w.some(w=>w.includes('onLoad')),'unknown key ignored');
 ok((await pg.evaluate(()=>EXLAB.normTheme({format:'x'}).errs.length))>0,'wrong format refused');
 // --- devices
 const dv=await pg.evaluate(()=>{const X=EXLAB,o={};for(const k in X.DEV_EX){const r=X.normDevice(X.DEV_EX[k]);o[k]={w:r.warns,e:r.errs}}return o});
 for(const k of['echo','phone','chorus','sweep'])ok(!dv[k].e.length,`device ${k} builds: ${dv[k].e}`);
 ok(dv.echo.w.length===1&&dv.echo.w[0].includes('capped'),'echo feedback capped');ok(dv.bad.w.some(w=>w.includes('capped')),'runaway capped');
 const nd=await pg.evaluate(()=>{const X=EXLAB,d=JSON.parse(JSON.stringify(X.DEV_EX.echo));d.wires=[['in','sat'],['sat','fb'],['fb','sat'],['sat','out']];return X.normDevice(d).errs});ok(nd.some(e=>e.includes('no delay')),'loop without delay refused');
 ok(await pg.evaluate(()=>{try{EXLAB.compileExpr('alert(1)',[]);return false}catch(e){return true}}),'expr: unknown function refused');
 ok(await pg.evaluate(()=>EXLAB.compileExpr('db($a) * 2 + max(1, 3)',['a'])({a:0})===5),'expr value');
 // --- scripts
 const sc=await pg.evaluate(()=>{const X=EXLAB,o={};for(const k in X.SC_EX){const c=X.compileScript(X.SC_EX[k]);o[k]={ok:c.ok,e:c.errs,ops:c.opsTotal,heavy:!!c.tooHeavy}}return o});
 for(const k of['clip','crush','comb','phaser','loud'])ok(sc[k].ok,`script ${k} compiles: ${sc[k].e}`);ok(!sc.heavy.ok&&sc.heavy.heavy,'heavy refused');ok(!sc.sandbox.ok&&sc.sandbox.e.length>=1,'sandbox refused: '+sc.sandbox.e);
 const esc=await pg.evaluate(()=>['sample:\n out0 = this;','sample:\n out0 = globalThis.x;','sample:\n out0 = constructor(1);','sample:\n x = "a";','sample:\n while (1) { }','sample:\n loop (1000) { x = 1; }','sample:\n loop (n) { x = 1; }','sample:\n out0 = in0\n','param p 0..1 = 0\nsample:\n p = 2;','sample:\n out0 = sin;','sample:\n process = 1;','sample:\n x = a => 1;','sample:\n x = `1`;','sample:\n x = mem;'].map(s=>EXLAB.compileScript(s).ok));
 ok(esc.every(x=>x===false),'escape attempts all refused: '+esc);
 const pre=await pg.evaluate(async()=>{const X=EXLAB,o={};for(const k of['clip','comb','phaser','loud']){const c=X.compileScript(X.SC_EX[k]);o[k]=await X.preflight(c.kernel,c.params.map(p=>p.default))}return o});
 for(const k in pre)ok(pre[k].ms>0&&pre[k].ms<250,`preflight ${k}: ${JSON.stringify(pre[k])}`);ok(pre.clip.nan===0&&pre.clip.peak<1.5,'clip sane');ok(pre.loud.peak>4||pre.loud.nan>0,'loud bug seen by the test run');
 // --- chat
 const ch=await pg.evaluate(()=>{const out=[];for(const q of['A warm tape echo with wobble','Add reverb','More feedback','Make it darker','Call it Moon echo','Remove the echo','A crunchy telephone voice','banana','Make the theme purple']){document.querySelector('#chIn').value=q;document.querySelector('#chForm').requestSubmit();out.push({q,name:EXLAB.CH.d&&EXLAB.CH.d.name,n:EXLAB.CH.d&&EXLAB.CH.d.params.length,mods:[...EXLAB.CH.mods].join(','),last:EXLAB.CH.msgs.at(-1).t})}return out});
 console.log(ch.map(c=>`${c.q} -> ${c.name} [${c.mods}] ${c.n} | ${c.last}`).join('\n'));
 ok(ch[0].name==='Tape echo'&&ch[1].mods.includes('reverb')&&ch[4].name==='Moon echo'&&!ch[5].mods.includes('echo')&&ch[6].name==='Crunchy telephone','chat flow');
 // --- audio: every device through the safety stage
 await pg.click('#rl-desc');await pg.waitForTimeout(900);const a1=await pg.evaluate(()=>({on:EXLAB.Rig.on,st:EXLAB.Rig.ctx.state,stat:EXLAB.Rig.stat,dev:!!EXLAB.DV.dev}));ok(a1.on&&a1.st==='running'&&a1.dev&&a1.stat.pin>0.001,'desc device plays: '+JSON.stringify(a1));
 await pg.click('[data-ex="bad"]');await pg.waitForTimeout(2500);const a2=await pg.evaluate(()=>EXLAB.Rig.stat);ok(a2.gr<0.9||a2.trips>0,'runaway device held by the safety stage: '+JSON.stringify(a2));
 await pg.click('#rl-script');await pg.waitForTimeout(1500);const a3=await pg.evaluate(()=>({live:EXLAB.SC.live,node:!!EXLAB.SC.node,key:EXLAB.Rig.key}));ok(a3.node&&a3.key==='script'&&a3.live!=null,'script device live with a cpu reading: '+JSON.stringify(a3));
 await pg.click('#scEx [data-ex="loud"]');await pg.waitForTimeout(2500);const a4=await pg.evaluate(()=>EXLAB.Rig.stat);ok(a4.trips>0||a4.gr<0.5,'loud script caught: '+JSON.stringify(a4));
 await pg.click('#scEx [data-ex="comb"]');await pg.waitForTimeout(1200);await pg.click('#rl-chat');await pg.waitForTimeout(800);ok(await pg.evaluate(()=>EXLAB.Rig.key==='chat'&&!!EXLAB.CH.S.dev),'chat device plays');await pg.click('#rl-chat');
 // --- picks
 await pg.click('#pkStar');ok((await pg.textContent('#pkLine'))==='EX1 picks: 1A 2B 3A 4A 5A 6A 7A 8A 9A','picks line: '+await pg.textContent('#pkLine'));
 // --- layout
 for(const w of[1280,400]){await pg.setViewportSize({width:w,height:900});await pg.waitForTimeout(200);const ov=await pg.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);ok(ov<=0,`no sideways scroll at ${w}: ${ov}`)}
 ok(!errs.length,'no page errors: '+errs.join(' | '));
 await pg.setViewportSize({width:1280,height:900});await pg.click('#thEx [data-ex="jupiter"]');await pg.click('#scEx [data-ex="clip"]');await pg.waitForTimeout(700);await pg.screenshot({path:process.env.SHOT||path.join(require('os').tmpdir(),'exlab.png'),fullPage:true});
 // example files
 const ex=await pg.evaluate(()=>({t:EXLAB.THEME_EX,d:Object.fromEntries(Object.entries(EXLAB.DEV_EX).map(([k,v])=>[k,EXLAB.fmtDev(v)])),s:EXLAB.SC_EX}));const ed=path.join(dir,'examples');fs.mkdirSync(ed,{recursive:true});
 for(const k in ex.t)if(k!=='broken')fs.writeFileSync(path.join(ed,k+'.audiolabtheme'),JSON.stringify(ex.t[k],null,2)+'\n');for(const k in ex.d)if(k!=='bad')fs.writeFileSync(path.join(ed,k+'.audiolabdevice'),ex.d[k]+'\n');for(const k of['clip','crush','comb','phaser'])fs.writeFileSync(path.join(ed,k+'.alscript'),ex.s[k]);
 await b.close();srv.close();console.log(`${pass} passed, ${fail} failed`);process.exit(fail?1:0)})();
