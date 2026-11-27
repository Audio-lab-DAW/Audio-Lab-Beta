#!/usr/bin/env node
/* Task EX2: headless checks of the deep layer, alone and inside EX1's pick page.
   node tools/extension-lab/deep_check.js [folder for screenshots] */
const {chromium}=require('playwright'),path=require('path'),fs=require('fs');
const dir=__dirname,shots=process.argv[2];let pass=0,fail=0;
const ok=(c,n)=>{c?pass++:fail++;console.log((c?'ok   ':'FAIL ')+n)};
const wrap=f=>{const o=path.join(dir,'open-'+f);fs.writeFileSync(o,'<!doctype html><html><head><meta charset="utf8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0}[hidden]{display:none!important}</style></head><body>'+fs.readFileSync(path.join(dir,f),'utf8')+'</body></html>');return 'file://'+o};
(async()=>{const b=await chromium.launch();
for(const f of ['deep-layer.html','extensions-with-deep-layer.html']){const host=f.startsWith('ext');console.log('\n== '+f);
 const p=await b.newPage({viewport:{width:1280,height:1000}});const errs=[];p.on('console',m=>{if(m.type()=='error')errs.push(m.text())});p.on('pageerror',e=>errs.push(e.message));
 await p.goto(wrap(f));await p.waitForTimeout(700);
 const txt=s=>p.$eval(s,e=>e.innerText||e.value||''),click=s=>p.click(s),tab=t=>click(`[data-tab=${t}]`);
 const line=()=>txt(host?'#pkLine':'#picks');
 ok((await line()).includes('Deep layer | P1 ?')&&(await line()).includes('K1c K2b'),'picks line starts on the recommendations');
 if(host)ok((await line()).startsWith('EX1 picks: 1?'),'EX1 picks stay at the front of the same line');
 // P1
 await p.fill('#dlQ','meter');ok((await p.$$('#dlSetList .dlrow')).length>=3&&(await p.$$('#dlSetList .dlrow')).length<10,'P1 search narrows the list');
 await p.fill('#dlQ','mixer.stripWidth');await p.fill('#dls-mixer-stripWidth','999');await p.dispatchEvent('#dls-mixer-stripWidth','change');
 ok((await txt('#dlSetList')).includes('Must be from 64 to 170'),'P1 refuses a value out of range');
 await p.fill('#dls-mixer-stripWidth','120');await p.dispatchEvent('#dls-mixer-stripWidth','change');
 ok(await p.$eval('#dlApp',e=>e.style.getPropertyValue('--sw'))=='120px'&&(await txt('#dlTool')).includes('"mixer.stripWidth": 120'),'P1 a valid value changes the mock and the file');
 await click('[data-flt=lock]');ok((await p.$$('#dlSetList input, #dlSetList select, #dlSetList .sw')).length==0,'P1 locked safety values have no editor');
 // P2
 await tab('P2');await click('[data-act=pick]');await click('#dlApp [data-al="mixer.strip.sends"]');await click('[data-ract=hide]');
 ok((await p.$$('#dlApp [data-al="mixer.strip.sends"]')).length==0,'P2 hide removes the control from every strip');
 await click('#dlApp [data-al="transport.loop"]');const before=await p.$$eval('#dlApp .dlbar [data-al]',a=>a.map(e=>e.dataset.al).indexOf('transport.loop'));await click('[data-ract=earlier]');
 ok(await p.$$eval('#dlApp .dlbar [data-al]',a=>a.map(e=>e.dataset.al).indexOf('transport.loop'))==before-1,'P2 move earlier moves it one place');
 await click('#dlApp [data-al="transport.stop"]');await p.fill('#dlRen','Halt');await click('[data-ract=rename]');ok((await txt('#dlApp [data-al="transport.stop"]')).includes('Halt'),'P2 rename shows in the mock');
 await click('#dlApp [data-al="mixer.master.limiter"]');await click('[data-ract=hide]');ok((await txt('#dlTool')).includes('cannot be hidden')&&(await p.$$('#dlApp [data-al="mixer.master.limiter"]')).length==1,'P2 the limiter light cannot be hidden');
 await p.fill('#dlRules','{"audiolab":"ui-rules","version":1,"layouts":{"all":[{"id":"transport.capture","hide":true},{"id":"no.such.thing","hide":true}]}}');await click('[data-act=rapply]');
 ok((await p.$$('#dlApp [data-al="transport.capture"]')).length==0&&(await txt('#dlTool')).includes('no control has this id'),'P2 a hand-written file applies and an unknown id is reported');
 await p.fill('#dlRules','{broken');await click('[data-act=rapply]');ok((await txt('#dlTool')).includes('Not valid JSON')&&(await p.$$('#dlApp [data-al="transport.capture"]')).length==0,'P2 a broken file changes nothing');
 // P3
 await tab('P3');await click('[data-act=mnew]');await p.fill('#dlMName','Loud octave');await click('[data-step="note.octaveUp"]');await click('[data-step="note.velocityUp"]');await click('[data-act=msave]');
 ok((await txt('#dlTool')).includes('macro.loud-octave'),'P3 a saved macro becomes a command');
 const u0=await txt('#dlStat');await click('[data-run="macro.loud-octave"]');ok((await txt('#dlStat')).includes('Undo “Loud octave”')&&!u0.includes('Loud octave'),'P3 a macro is one undo step');
 await click('[data-key="transport.loop"]');await p.keyboard.press('Shift+K');ok((await txt('#dlTool')).includes('"transport.loop": "Shift+K"'),'P3 a new key is written to the file');
 await p.hover('#dlApp');const lp=await p.$eval('#dlApp [data-al="transport.loop"]',e=>e.classList.contains('on'));await p.keyboard.press('Shift+K');ok(await p.$eval('#dlApp [data-al="transport.loop"]',e=>e.classList.contains('on'))!=lp,'P3 the new key runs the command over the mock');
 await click('[data-bar="track.mute"]');ok((await p.$$('#dlApp [data-run="track.mute"]')).length==1,'P3 a command can be put on the toolbar');
 // P4
 await tab('P4');await click('[data-cssx="0"]');ok(await p.$eval('#dlApp [data-al="mixer.strip.mute"]',e=>getComputedStyle(e).height)=='30px','P4 a snippet restyles a control by id');
 await click('[data-cssx="2"]');const t4=await txt('#dlTool');ok(t4.includes('Left out @import')&&t4.includes('no files or web addresses')&&t4.includes('Switched off: it hid mixer.master.limiter'),'P4 guard rails: no import, no url, protected control stays');
 ok(await p.$eval('#dlApp [data-al="mixer.master.limiter"]',e=>getComputedStyle(e).display)!='none','P4 the limiter light is still visible');
 // P5
 await tab('P5');const run=async i=>{await click(`[data-scr="${i}"]`);await click('[data-act=srun]');await p.waitForTimeout(450)};
 await run(0);ok(await p.$$eval('#dlApp .dltr',a=>new Set(a.map(e=>e.style.getPropertyValue('--c'))).size)==6,'P5 example 1 colours the six tracks by type');
 await run(1);ok(await p.$$eval('#dlApp .dlpr i',a=>a.some(e=>parseFloat(e.style.opacity)<.99)),'P5 example 2 humanises the notes');
 await run(5);const t5=await txt('#dlCon');ok(t5.includes('Locked. A safety value')&&t5.includes('Must be from 64 to 170'),'P5 a script cannot set a locked or out-of-range value');
 await run(2);await click('#dlApp [data-sbtn]');await p.waitForTimeout(350);ok((await txt('#dlCon')).includes('Button handler: 16 changes'),'P5 example 3 adds a toolbar button that works');
 await run(4);ok((await txt('#dlCon')).includes('fetch is undefined')&&(await p.$$('.dlperm')).length==1,'P5 no network; al.net.fetch shows a permission card');
 await click('[data-perm="0"]');await p.waitForTimeout(300);ok((await txt('#dlCon')).includes('The network was not allowed'),'P5 saying no ends the script with a clear error');
 await click('#dlApp [data-al="transport.play"]');const pos0=await p.$eval('#dlPh',e=>e.style.left);await run(3);await p.waitForTimeout(2100);
 ok((await txt('#dlCon')).includes('Stopped by AudioLab: the script took longer than 2 s')&&await p.$eval('#dlPh',e=>e.style.left)!=pos0,'P5 a script that never ends is stopped at 2 s while the mock keeps playing');
 // P6
 await tab('P6');const n6=(await p.$$('#dlTool [data-cdel]')).length;ok(n6>=8,'P6 lists every change ('+n6+')');
 await click('#dlTool [data-act=safe]');ok((await p.$$('#dlApp [data-al="transport.capture"]')).length==1&&(await p.$eval('#dlApp',e=>e.style.getPropertyValue('--sw')))=='76px'&&(await p.$$('#dlApp .usr')).length==0,'P6 safe mode shows AudioLab as it came');
 await click('#dlApp [data-act=unsafe]');ok((await p.$$('#dlApp [data-al="transport.capture"]')).length==0,'P6 leaving safe mode brings the changes back');
 await click('[data-act=reset]');await click('[data-act=resetyes]');ok((await p.$$('#dlTool [data-cdel]')).length==0,'P6 reset removes every change');
 await click('[data-act=restore]');ok((await p.$$('#dlTool [data-cdel]')).length>=8,'P6 the backup can be put back');
 // picks
 await click('[data-yn=yes]');await click('#dl-K1-a');ok((await line()).includes('P6 yes')&&(await line()).includes('K1a'),'picks follow the clicks');
 if(host){await click('#pkStar');ok(/EX1 picks: 1A 2B .*P1 yes.*K1c/.test(await line()),'"Use the starred picks" fills both parts');
  ok(await p.evaluate(()=>!!window.EXLAB&&document.querySelectorAll('#p1,#p2,#p3,#p4,#plan,#pick,#deep').length==7),'EX1\'s prototypes are still on the page')}
 ok(errs.length==0,'no console errors'+(errs.length?': '+errs.join(' | '):''));
 if(shots){await tab('P5');await p.screenshot({path:path.join(shots,(host?'host':'alone')+'.png'),fullPage:host?false:true});if(host){await p.$eval('#deep',e=>e.scrollIntoView());await p.screenshot({path:path.join(shots,'host-deep.png')})}}
 for(const w of [1280,400]){const m=await b.newPage({viewport:{width:w,height:900}});await m.goto(wrap(f));await m.waitForTimeout(500);ok(await m.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'no sideways scroll at '+w+' px');
  if(shots&&w==400&&host){await m.$eval('#deep',e=>e.scrollIntoView());await m.screenshot({path:path.join(shots,'host-400.png')})}await m.close()}
 await p.close()}
await b.close();for(const f of fs.readdirSync(dir))if(f.startsWith('open-'))fs.unlinkSync(path.join(dir,f));
console.log('\n'+pass+' passed, '+fail+' failed');process.exit(fail?1:0)})();
