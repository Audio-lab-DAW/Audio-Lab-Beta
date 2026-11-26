/* App activity in the real desktop app (task AO, v0.218): Electron with desktop/main.js and desktop/preload.js, driven by Playwright.
   Run after `node desktop/scripts/sync-app.js`:
     xvfb-run -a node tools/ui-tests/taskAO_electron.js [desktop dir] [seconds per measurement] [seconds to settle after the start]
   The window events are the real BrowserWindow calls (blur, hide, minimize, show, focus); where the virtual screen has no window manager to send
   blur and focus, the test emits those two events on the window itself, so main.js, preload.js and the page still do all their work.
   Prints the processor use of every process as Electron measures it (app.getAppMetrics) in front, with another app in front, hidden, and back. */
const { _electron } = require('playwright');
const path = require('path'), os = require('os'), fs = require('fs');
const DIR = path.resolve(process.argv[2] || path.join(__dirname, '..', '..', 'desktop')), SECS = +(process.argv[3] || 20), SETTLE = +(process.argv[4] || 45);
const fail = []; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const ud = fs.mkdtempSync(path.join(os.tmpdir(), 'alao-'));
  const exe = process.env.ELECTRON || require(path.join(__dirname, '..', '..', 'desktop', 'node_modules', 'electron'));
  const app = await _electron.launch({ executablePath: exe, args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required', DIR], env: { ...process.env, XDG_CONFIG_HOME: ud } });
  const page = await app.firstWindow(); const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 300)));
  await page.waitForFunction(() => window.AudioLab && window.AudioLab.version, null, { timeout: 90000 }); await sleep(9000);
  const R = (c) => page.evaluate((c) => window.AudioLab.run(c), c);
  const newPage = await R("typeof AOS!=='undefined'?1:0").catch(() => 0), bridge = await page.evaluate(() => !!(window.audiolabDesktop && window.audiolabDesktop.activity));
  console.log('desktop app', await app.evaluate(({ app }) => app.getVersion()), 'page', await R('VERSION'), '| page has the freeze:', !!newPage, '| shell sends activity events:', bridge);
  await R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();pmSetOn(false);if(typeof AOG!=='undefined')AOG.boot=0;return 1})()");
  await page.mouse.click(700, 20); await sleep(SETTLE * 1000);   // the app renders clips ahead after it starts (background freeze of tracks): let that finish, it is not what is measured here
  // processor use: Electron's own numbers when the shell has them, else read from the main process
  const metrics = async () => app.evaluate(({ app }) => app.getAppMetrics().map((m) => ({ type: m.type, name: m.name || m.serviceName || '', cpu: m.cpu.percentCPUUsage, wk: m.cpu.idleWakeupsPerSecond })));
  const measure = async (label) => { await metrics(); await sleep(SECS * 1000); const M = await metrics(); const by = {}; let tot = 0;
    for (const m of M) { const k = m.type === 'Tab' ? 'page' : m.type === 'Browser' ? 'main' : m.type === 'GPU' ? 'GPU' : 'other'; by[k] = (by[k] || 0) + m.cpu; tot += m.cpu; }
    const st = newPage ? JSON.parse(await R("JSON.stringify({lv:AOS.lv,ctx:ctx?ctx.state:'none',why:AOS.why})")) : { lv: '-', ctx: await R("ctx?ctx.state:'none'"), why: '' };
    console.log(`     ${label}: page ${(by.page || 0).toFixed(2)} %, main process ${(by.main || 0).toFixed(2)} %, GPU process ${(by.GPU || 0).toFixed(2)} %, other ${(by.other || 0).toFixed(2)} %, all ${tot.toFixed(2)} % of one core (level ${st.lv}, audio ${st.ctx}${st.why ? ', ' + st.why : ''})`); return { by, tot, st }; };
  const win = (code) => app.evaluate(({ BrowserWindow }, code) => { const w = BrowserWindow.getAllWindows()[0]; return new Function('w', 'BrowserWindow', code)(w, BrowserWindow); }, code);
  const state = async () => (newPage ? JSON.parse(await R("JSON.stringify({lv:AOS.lv,fg:AOS.fg,ctx:ctx?ctx.state:'none',host:AOS.host,gate:AO.gate})")) : null);
  const waitLv = async (lv, lim = 30) => { const t0 = Date.now(); while (Date.now() - t0 < lim * 1000) { const s = await state(); if (s && s.lv === lv) return (Date.now() - t0) / 1000; await sleep(100); } return null; };
  await win("w.show();w.focus();return 1"); await sleep(500);
  const front = await measure('in front, nothing playing');
  // another app in front: blur. Without a window manager the focus cannot really move, so say what a real blur says.
  const realBlur = await win("w.blur();return BrowserWindow.getFocusedWindow()?0:1");
  if (!realBlur) await win("w.isFocused=()=>false;BrowserWindow.getFocusedWindow=()=>null;w.emit('blur');return 1");
  await page.evaluate(() => { try { window.dispatchEvent(new Event('blur')); } catch (e) {} });
  if (newPage) { await page.evaluate(() => { Document.prototype.hasFocus = function () { return !!window.__foc; }; }); await R("(()=>{aoEval('test');return 1})()"); }
  await sleep(600);
  if (newPage && bridge) { const s = await state(); ok(s.host && s.host.focused === false && s.host.visible === true, 'blur: main.js told the page (focused false, window still visible): ' + JSON.stringify(s.host));
    const t = await waitLv(2); ok(t != null, 'blur: the page froze ' + (t != null ? (t + 0.6).toFixed(1) : '?') + ' s later'); await sleep(400);
    await sleep(8000); }
  else await sleep(11000);
  const blur = await measure('another app in front (window visible)');
  await win("w.hide();return 1"); await sleep(6000);
  if (newPage && bridge) { const s = await state(); ok(s.host && s.host.visible === false, 'hide: main.js told the page the window is hidden: ' + JSON.stringify(s.host)); }
  const hid = await measure('hidden');
  if (newPage && bridge) { const m = await page.evaluate(() => window.audiolabDesktop.metrics()); ok(m && m.procs && m.procs.length >= 2 && m.power === false, 'the shell reports its own processor use (' + m.procs.length + ' processes) and holds no power blocker while nothing plays'); }
  // playing while hidden: the power blocker is on only then
  if (newPage && bridge) { await R("(()=>{pos=64;start();return 1})()"); await sleep(1500); const s = await state(); const pw = await page.evaluate(() => window.audiolabDesktop.metrics().then((m) => m.power));
    ok(s.lv === 1 && s.ctx === 'running' && s.gate && pw === true, 'Play while hidden: sound on, drawing off, the power blocker is on');
    const pl = await measure('hidden and playing (drawing off)'); await R("(()=>{stop();return 1})()"); const t = await waitLv(2); await sleep(500);
    const pw2 = await page.evaluate(() => window.audiolabDesktop.metrics().then((m) => m.power)); ok(t != null && pw2 === false, 'Stop: frozen again after ' + (t || 0).toFixed(1) + ' s, the power blocker is off'); }
  await win("w.show();w.focus();return 1"); if (!realBlur) await win("delete w.isFocused;BrowserWindow.getFocusedWindow=()=>w;w.emit('focus');return 1");
  if (newPage) await page.evaluate(() => { window.__foc = true; window.dispatchEvent(new Event('focus')); });
  await sleep(800);
  if (newPage) { const s = await state(); ok(s.lv === 0 && s.ctx === 'running' && !s.gate, 'shown and focused again: in front (level ' + s.lv + ', audio ' + s.ctx + ')'); }
  await sleep(SETTLE * 500); const back = await measure('back in front');
  if (newPage) console.log(`     page + main process: in front ${(front.by.page + front.by.main).toFixed(2)} %, another app in front ${(blur.by.page + blur.by.main).toFixed(2)} %, hidden ${(hid.by.page + hid.by.main).toFixed(2)} %`);
  ok(!errs.length, 'no page errors ' + errs.join('; '));
  await app.evaluate(({ app }) => app.exit(0)).catch(() => {});
  console.log(fail.length ? '\n' + fail.length + ' failed' : '\nall passed'); process.exit(fail.length ? 1 : 0);
})().catch((e) => { console.error('test error', e); process.exit(2); });
