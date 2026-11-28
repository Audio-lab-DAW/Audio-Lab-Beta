/* Task XT-DL12, the script sandbox in the real desktop app: Electron with desktop/main.js (the audiolab:// scheme, cross-origin isolated,
   contextIsolation and sandbox on, the preload bridge in the page). Run after `node desktop/scripts/sync-app.js`:
     xvfb-run -a node tools/ui-tests/taskXT_DL12_electron.js [desktop dir] [--quick]   (--quick leaves out the memory bomb)
   Checks that xtSandboxRun works there, that the sandbox frame runs in its own process (so a script that eats memory cannot take the
   window down), that the network, eval, the desktop bridge and the page's globals are out of reach (a local server counts requests),
   that an endless loop is stopped while the window keeps drawing, and that a memory bomb dies alone. */
// for: task XT-DL12 (lane H)
const { _electron } = require('playwright');
const path = require('path'), os = require('os'), fs = require('fs'), http = require('http');
const DIR = path.resolve(process.argv.slice(2).find((a) => !a.startsWith('--')) || path.join(__dirname, '..', '..', 'desktop'));
const fail = []; const ok = (c, m, i) => { console.log((c ? 'ok   ' : 'FAIL ') + m + (i !== undefined ? ' ' + JSON.stringify(i) : '')); if (!c) fail.push(m); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const hits = []; const srv = http.createServer((q, s) => { hits.push(q.url); s.writeHead(200, { 'Access-Control-Allow-Origin': '*' }); s.end('self.leak=1'); });
  await new Promise((r) => srv.listen(0, '127.0.0.1', r)); const U = 'http://127.0.0.1:' + srv.address().port;
  const ud = fs.mkdtempSync(path.join(os.tmpdir(), 'alxt12-'));
  const exe = process.env.ELECTRON || require(path.join(DIR, 'node_modules', 'electron'));
  const app = await _electron.launch({ executablePath: exe, args: ['--no-sandbox', DIR], env: { ...process.env, XDG_CONFIG_HOME: ud } });
  const page = await app.firstWindow(); const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 300)));
  page.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource|fetching the script/.test(m.text())) errs.push('console: ' + m.text().slice(0, 300)); });
  await page.waitForFunction(() => window.AudioLab && window.AudioLab.version, null, { timeout: 90000 }); await sleep(4000);
  const SB = (code, o) => page.evaluate(([c, o]) => xtSandboxRun(c, o || {}), [code, o || {}]);
  const v = await page.evaluate(() => AudioLab.run('VERSION'));
  ok(v.split('.').map(Number)[1] >= 291, 'the desktop app runs v0.291 or later', v);
  ok(await page.evaluate(() => crossOriginIsolated && location.protocol === 'audiolab:' && !!window.audiolabDesktop), 'the page is the real shell: audiolab://, cross-origin isolated, the desktop bridge present');
  ok(await page.evaluate(() => AudioLab.run('XT_SBX.n') === 0 && !document.querySelector('iframe[data-xt-sbx]')), 'at start no sandbox frame exists');
  let r = await SB("console.log('hi');al.change({n:al.input.n+1});return 'ran'", { input: { n: 1 } });
  ok(r.ok && r.value === 'ran' && r.changes[0].n === 2 && r.logs[0].v === 'hi', 'a script runs in the desktop app', [r.value, r.ms + ' ms']);
  // own process: hold a run open and ask the main process where its frame lives
  const hold = page.evaluate(() => xtSandboxRun('await new Promise(r=>setTimeout(r,1500));return 1', {}));
  await sleep(600);
  const pr = await app.evaluate(({ BrowserWindow }) => { const w = BrowserWindow.getAllWindows().find((x) => /index\.html/.test(x.webContents.getURL()) && !/#alchild/.test(x.webContents.getURL())) || BrowserWindow.getAllWindows()[0];
    const m = w.webContents.mainFrame; return { main: m.osProcessId, frames: m.framesInSubtree.filter((f) => f !== m).map((f) => ({ url: f.url, pid: f.osProcessId, origin: f.origin })) }; });
  await hold;
  const sf = pr.frames.find((f) => /srcdoc/.test(f.url));
  ok(sf && sf.pid !== pr.main, 'the sandbox frame runs in its own process (site isolation of sandboxed frames)', pr);
  ok(sf && sf.origin === 'null', 'the sandbox frame has an opaque origin', sf && sf.origin);
  const esc = {
    fetch: `try{await fetch('${U}/f',{mode:'no-cors'});return 'LEAK'}catch(e){return 'blocked'}`,
    xhr: `try{const x=new XMLHttpRequest();x.open('GET','${U}/x',false);x.send();return 'LEAK'}catch(e){return 'blocked'}`,
    ws: `return await new Promise(r=>{let s;try{s=new WebSocket('${U.replace('http', 'ws')}/w')}catch(e){return r('blocked')}s.onopen=()=>r('LEAK');s.onerror=()=>r('blocked');setTimeout(()=>r('blocked'),1500)})`,
    importScripts: `try{importScripts('${U}/i.js');return 'LEAK'}catch(e){return 'blocked'}`,
    'import()': `try{await import('${U}/d.js');return 'LEAK'}catch(e){return 'blocked'}`,
    eval: "try{eval('1');return 'LEAK'}catch(e){return 'blocked'}",
    'the bridge and the page': "return ['audiolabDesktop','window','document','parent','UI','AudioLab','require','process','localStorage','SharedArrayBuffer'].filter(n=>typeof self[n]!=='undefined').length?'LEAK':'blocked'",
    'the audiolab: scheme': "try{await fetch('audiolab://app/index.html');return 'LEAK'}catch(e){return 'blocked'}",
  };
  for (const [k, c] of Object.entries(esc)) { r = await SB(c, { limit: 4000 }); ok(r.ok && r.value === 'blocked', 'escape refused in the desktop app: ' + k, r.value || r.error); }
  await sleep(400);
  ok(hits.length === 0, 'the local server saw no request from the sandbox', hits);
  await page.evaluate(() => { window.__tk = 0; (function f() { __tk++; requestAnimationFrame(f); })(); });
  r = await SB('for(;;){}', { limit: 1000 });
  const tk = await page.evaluate(() => __tk);
  ok(r.stopped === 'time' && r.ms < 1700, 'an endless loop is stopped at the limit', [r.stopped, r.ms]);
  ok(tk >= 20, 'and the window kept drawing meanwhile', tk);
  if (!process.argv.includes('--quick')) {
    await page.evaluate(() => { window.__tk = 0; });
    r = await SB('const a=[];for(;;)a.push(new Array(2e5).fill(a.length))', { limit: 90000 });
    ok(r.stopped === 'memory' || /memory|allocation/i.test(r.error || ''), 'a memory bomb dies in its own process and the run is stopped', [r.stopped, r.ms, r.error]);
    ok(await page.evaluate(() => __tk) > 30 && (await SB('return 7')).value === 7, 'the window lived on, and the next script runs');
  }
  ok(await page.evaluate(() => !document.querySelector('iframe[data-xt-sbx]') && AudioLab.run('XT_SBX.runs.size') === 0), 'nothing is left behind');
  ok(!errs.length, 'no page errors', errs.slice(0, 4));
  await app.close(); srv.close();
  console.log(fail.length ? fail.length + ' FAILED' : 'all passed');
  process.exit(fail.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
