/* Task UV-2 (lane O): the arrangement's frame cost in Electron on a real graphics path (the macOS runner), before and after the tiles.
     electron tools/ui-tests/uv_bench_electron.js out.json name=path/to/index.html [name=path ...]
   For every build: Fractals open, the window 1600 x 900 CSS px at 1.75 (2800 x 1575 device px; the runner's screen is smaller than the
   user's), frame-rate limit off. With the tiles off and (when the build has them) on:
     bench   one drawing of the arrangement after a 6 CSS px scroll, finished by a 1-pixel read-back so the drawing itself is counted (median of 60)
     scroll  4 s of a sideways scroll of 6 CSS px a frame through V.x / dirty (what a trackpad does): frames per second, the app's own frame
             time, main-thread time per frame (Chromium's TaskDuration)
     edit    4 s with the view still and a clip moved by a beat and back on every frame
   The runner is a virtual Mac with a paravirtual graphics device: its numbers compare before and after, not what the M4 does at 240 Hz. */
const { app, BrowserWindow } = require('electron');
const fs = require('fs'), path = require('path');
app.commandLine.appendSwitch('disable-frame-rate-limit'); app.commandLine.appendSwitch('disable-gpu-vsync');
app.commandLine.appendSwitch('force-device-scale-factor', '1.75'); app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
const argv = process.argv.slice(process.argv.findIndex(a => a.endsWith('uv_bench_electron.js')) + 1);
const OUT = argv[0], BUILDS = argv.slice(1).map(a => { const i = a.indexOf('='); return [a.slice(0, i), path.resolve(a.slice(i + 1))]; });
app.on('window-all-closed', () => { });   /* one window per build: closing one must not end the run */
process.on('uncaughtException', e => { console.log('uncaught', e && e.stack || e); });
console.log('uv bench: builds', JSON.stringify(BUILDS), 'electron', process.versions.electron);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function one(name, file) {
  console.log('build', name, file);
  const w = new BrowserWindow({ width: 1600, height: 900, show: true, enableLargerThanScreen: true, useContentSize: true, webPreferences: { backgroundThrottling: false } });
  const wc = w.webContents, run = c => wc.executeJavaScript('AudioLab.run(' + JSON.stringify(c) + ')');
  const until = async (c, ms) => { const t = Date.now(); while (Date.now() - t < ms) { try { if (await wc.executeJavaScript(c)) return true; } catch (e) { } await sleep(500); } return false; };
  await w.loadFile(file).catch(() => { }); await until('!!(window.AudioLab&&AudioLab.version)', 120000);
  await wc.executeJavaScript("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}));1"); await w.loadFile(file).catch(() => { });
  await until('!!(window.AudioLab&&AudioLab.version)', 120000); await sleep(4000);
  await wc.executeJavaScript("for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()};1");
  await wc.executeJavaScript('window.AL_TEST_SONGS=' + JSON.stringify(require(path.join(__dirname, '..', 'test-songs', 'alsong.js')).songs()) + ';1'); /* task WS-F: the test song from tools/test-songs */
  await run('openDemoFractals()'); await sleep(8000); await wc.executeJavaScript("{const s=document.getElementById('liteNote');if(s)s.remove()};1");
  await run('pmSetOn(false);UI.follow=false;if(play.on)stop();0'); await until("AudioLab.run('!MAP.busy&&!MAP.tm&&!MAP.et')", 90000); await sleep(1000);
  console.log('  Fractals open');
  const res = { name, meta: JSON.parse(await run("JSON.stringify({v:VERSION,arr:[arr.width,arr.height],dpr:devicePixelRatio,tiles:typeof UVT==='object',gpu:typeof uvGpu==='function'?[uvGpu(),UVT.gpuName]:null,tracks:S.tracks.length})")), rows: [] };
  await run("if(!window.__ub){window.__ub={t:0,n:0};const o=frame0;frame0=function(n){const t=performance.now();try{return o(n)}finally{__ub.t+=performance.now()-t;__ub.n++}}};0");
  wc.debugger.attach('1.3'); await wc.debugger.sendCommand('Performance.enable');
  const metric = async () => { const m = {}; for (const x of (await wc.debugger.sendCommand('Performance.getMetrics')).metrics) m[x.name] = x.value; return m; };
  for (const on of (res.meta.tiles ? [false, 'auto'] : [false])) {
    if (res.meta.tiles) await run('UVT.on=' + JSON.stringify(on) + ';UVT.force=1;dirty=true;0');
    await run('V.x=96;V.ppb=24;V.y=0;clampV();dirty=true;0'); await sleep(500);
    const b = JSON.parse(await run(`(()=>{const g=arr.getContext('2d'),r=[],why={};dirty=false;drawArr(false);g.getImageData(0,0,1,1);
      for(let i=0;i<60;i++){V.x+=(i%30<15?6:-6)/V.ppb;clampV();const t=performance.now();drawArr(false);g.getImageData(0,0,1,1);r.push(performance.now()-t);if(typeof UVT==='object'){const k=UVT.last.mode+(UVT.why?':'+UVT.why:'');why[k]=(why[k]||0)+1}}
      r.sort((a,b)=>a-b);return JSON.stringify({med:r[30],p90:r[54],min:r[0],modes:why})})()`));
    res.rows.push({ tiles: on, scene: 'bench', ...b });
    for (const sc of ['scroll', 'edit']) {
      const drv = sc === 'scroll'
        ? "window.__ud={on:true,k:0};(function f(){if(!__ud.on)return;__ud.k++;V.x+=(Math.floor(__ud.k/90)%2?-1:1)*6/V.ppb;clampV();dirty=true;requestAnimationFrame(f)})();0"
        : "window.__ud={on:true,k:0};V.x=160;clampV();{let c=null;S.tracks.forEach((t,i)=>{for(const q of t.clips){const G=clipGeom(i,q);if(!c&&G.x>X0+20&&G.x<arr.clientWidth-60&&G.y>AY+10&&G.y+G.h<arr.clientHeight-BY)c=q}});__ud.c=c}(function f(){if(!__ud.on)return;__ud.k++;if(__ud.c){__ud.c.start+=(__ud.k%2?1:-1);dirty=true}requestAnimationFrame(f)})();0";
      await run(drv); await sleep(600);
      const m0 = await metric();
      await run("window.__uw={};if(!window.__uwr&&typeof UVT==='object'){window.__uwr=1;const o=drawArr;drawArr=function(p){const r=o.apply(this,arguments);if(!p){const k=UVT.last.mode+(UVT.why?':'+UVT.why:'');__uw[k]=(__uw[k]||0)+1}return r}};0");
      const r = JSON.parse(await wc.executeJavaScript(`new Promise(res=>{const iv=[];let last=performance.now(),t0=last;const a0=__ub.t,n0=__ub.n;const f=()=>{const n=performance.now();iv.push(n-last);last=n;if(n-t0<4000)requestAnimationFrame(f);else res(JSON.stringify({iv,app:(__ub.t-a0)/Math.max(1,__ub.n-n0)}))};requestAnimationFrame(f)})`));
      const m1 = await metric();
      await run("__ud.on=false;if(__ud.c&&__ud.k%2)__ud.c.start-=1;dirty=true;0"); await sleep(400);
      const iv = r.iv.slice(2).sort((a, b) => a - b), n = iv.length, tot = iv.reduce((a, b) => a + b, 0);
      res.rows.push({ tiles: on, scene: sc, fps: +(n / (tot / 1000)).toFixed(1), med: +iv[n >> 1].toFixed(2), p95: +iv[Math.floor(n * .95)].toFixed(2), app: +r.app.toFixed(2),
        main: +(((m1.TaskDuration || 0) - (m0.TaskDuration || 0)) * 1000 / n).toFixed(2), modes: res.meta.tiles ? JSON.parse(await run('JSON.stringify(__uw)')) : null, edited: sc === 'edit' ? await run('!!__ud.c') : undefined });
    }
  }
  wc.debugger.detach(); w.destroy();
  return res;
}
app.whenReady().then(async () => {
  const all = [];
  for (const [n, f] of BUILDS) { try { all.push(await one(n, f)); } catch (e) { all.push({ name: n, error: String(e && e.stack || e) }); } }
  fs.writeFileSync(OUT, JSON.stringify(all, null, 1));
  for (const r of all) {
    console.log('==', r.name, JSON.stringify(r.meta || r.error));
    for (const x of r.rows || []) console.log(('tiles ' + (x.tiles ? x.tiles : 'off')).padEnd(11), x.scene.padEnd(7), (x.edited === false ? '(no clip found to edit) ' : '') + (x.scene === 'bench' ? 'one drawing median ' + x.med.toFixed(2) + ' ms, 90% ' + x.p90.toFixed(2) + ', best ' + x.min.toFixed(2) : 'fps ' + x.fps + '  interval median ' + x.med + ' ms, 95% ' + x.p95 + '  app ' + x.app + ' ms/f  main ' + x.main + ' ms/f'), x.modes ? JSON.stringify(x.modes) : '');
  }
  app.quit();
});
