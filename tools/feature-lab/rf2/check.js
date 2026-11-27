// Headless check of the RF2 pick page: loads it, exercises each mock-up and the picks bar, reports errors.
// Usage: node check.js [shot-dir]
const {chromium}=require('playwright');const path=require('path');
(async()=>{const b=await chromium.launch();const errs=[];let ok=0,fail=0;const T=(n,c)=>{c?ok++:(fail++,console.log('FAIL',n))};
for(const vp of [{width:1280,height:900},{width:400,height:850}]){
const p=await b.newPage({viewport:vp});p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
const html='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+require('fs').readFileSync(path.join(__dirname,'ideas-no-daw-has.html'),'utf8')+'</body></html>';
await p.setContent(html,{waitUntil:'load'});await p.waitForTimeout(300);
T('34 cards',await p.locator('article.card').count()===34);
T('10 mocks',await p.locator('.mock canvas, .mock .mrow').count()>=10);
T('no mock failed',await p.evaluate(()=>![...document.querySelectorAll('.mock')].some(m=>m.textContent.includes('Mock-up failed'))));
const ov=await p.evaluate(()=>document.documentElement.scrollWidth-innerWidth);T('no h-scroll '+vp.width+' ('+ov+')',ov<=0);
await p.click('#takeStar');T('take star',(await p.textContent('#picks'))==='RF2 picks: I1 I2 I3 I12 I24 I30');
await p.check('#pk-I22');T('pick I22',(await p.textContent('#picks')).includes('I22'));
await p.click('#clr');T('clear',(await p.textContent('#picks')).includes('none'));
await p.click('[data-mock=I1] canvas',{position:{x:200,y:80}});T('I1 click',(await p.textContent('[data-mock=I1] .read')).startsWith('Bar'));
await p.fill('#i2t','2');await p.dispatchEvent('#i2t','input');T('I2 tune',(await p.textContent('[data-mock=I2] .read')).includes('Kick settles'));
await p.click('#i2r');T('I2 root',(await p.textContent('[data-mock=I2] .read')).includes('key root'));
await p.click('#i3l');T('I3 card',(await p.textContent('.clipcard')).includes('over 0 dBFS'));await p.click('#i3b');T('I3 fix',(await p.textContent('.clipcard')).includes('No clipping'));
await p.click('[data-mock=I6] .chip >> nth=3');
await p.fill('#i13d','18');await p.dispatchEvent('#i13d','input');T('I13',(await p.textContent('[data-mock=I13] .read')).includes('passes 0 dB'));
await p.click('#i22p');T('I22',(await p.textContent('[data-mock=I22] .read')).includes('Bass from v3'));
await p.click('#i24t');await p.click('#i24e');await p.click('#i24b');T('I24',(await p.textContent('[data-mock=I24] .read')).includes('Kept both'));
await p.locator('[data-mock=I26] canvas').scrollIntoViewIfNeeded();const bb=await p.locator('[data-mock=I26] canvas').boundingBox();await p.mouse.move(bb.x+bb.width*.5,bb.y+60);await p.mouse.down();await p.mouse.move(bb.x+bb.width*.4,bb.y+60);await p.mouse.up();T('I26',(await p.textContent('[data-mock=I26] .read')).startsWith('Kept'));
await p.click('#i30a');T('I30',(await p.textContent('#i30c')).startsWith('4 accepted'));
await p.click('.chip[data-f=star]');T('filter star',await p.locator('article.card:visible').count()===6);await p.click('.chip[data-f=all]');
if(process.argv[2]){await p.evaluate(()=>scrollTo(0,0));await p.screenshot({path:path.join(process.argv[2],'rf2-'+vp.width+'.png'),fullPage:vp.width>500?false:false})}
await p.close()}
await b.close();console.log('checks passed',ok,'failed',fail);if(errs.length)console.log('ERRORS',errs);process.exit(fail||errs.length?1:0)})();
