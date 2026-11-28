/* Task LT-3a (lane J): fast MIDI notes in the real desktop app (Electron with desktop/main.js, preload.js and lt-midi.js).
   Run after `node desktop/scripts/sync-app.js` (or with desktop/app/index.html copied):
     xvfb-run -a node tools/ui-tests/taskLT_3a_electron.js [desktop dir] [--json out.json]
   A note is injected in the shell's listening window (AL_LT_TEST=1) as if a MIDI keyboard sent it. Measured: the note to the voice's
   first sample (on the output clock, getOutputTimestamp) on the armed Lead of the Fractals song, idle and while the page runs a 200 ms
   long task; before = the page's own path (Web MIDI, controller layer, noteOn), after = the fast path. Checks: the listening window is
   its own process, the Lead sounds, the page does not play the same note again, controller messages still reach lane C's layer, the
   sustain pedal holds, a learned note is not played by the fast path, a new audio engine gets a new channel, no page errors. */
const { _electron, chromium } = require('playwright');
const path = require('path'), os = require('os'), fs = require('fs');
const argv = process.argv.slice(2);
const DIR = path.resolve(argv.find((a) => !a.startsWith('--') && argv[argv.indexOf(a) - 1] !== '--json') || path.join(__dirname, '..', '..', 'desktop'));
const JS = argv.includes('--json') ? argv[argv.indexOf('--json') + 1] : null;
const fail = []; const ok = (c, m, i) => { console.log((c ? 'ok   ' : 'FAIL ') + m + (i !== undefined ? ' ' + JSON.stringify(i) : '')); if (!c) fail.push(m); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const med = (a) => { const b = [...a].sort((x, y) => x - y); return b.length ? +b[Math.floor(b.length / 2)].toFixed(1) : null; };
(async () => {
  const ud = fs.mkdtempSync(path.join(os.tmpdir(), 'allt3a-'));
  const exe = process.env.ELECTRON || require(path.join(DIR, 'node_modules', 'electron'));
  const app = await _electron.launch({ executablePath: exe, args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required', DIR], env: { ...process.env, XDG_CONFIG_HOME: ud, AL_LT_TEST: '1' } });
  const page = await app.firstWindow(); const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 300)));
  page.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource|fetching the script/.test(m.text())) errs.push('console: ' + m.text().slice(0, 300)); });
  await page.waitForFunction(() => window.AudioLab && window.AudioLab.version, null, { timeout: 90000 }); await sleep(3000);
  const R = (c) => page.evaluate((c) => AudioLab.run(c), c);
  const LTM = path.join(DIR, 'lt-midi.js'); const inject = (b) => app.evaluate((x, [f, b]) => process.mainModule.require(f).inject(b), [LTM, b]);
  ok(await page.evaluate(() => window.audiolabLtMidi === true && !!window.audiolabDesktop), 'the shell offers fast MIDI notes (preload hook)');
  ok(await R("typeof LT_HOOKS.fastNotes==='function'&&!LTF.chan"), 'nothing is made at start (no channel, no listening window)', await R('JSON.stringify(LT_HOOKS.fastNotes())'));
  ok((await app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows().length)) === 1, 'one window at start');
  /* the Fractals song, the Lead armed, a plain MIDI keyboard in the controller layer (named as the listening window reports it) */
  await R(`(async()=>{const r=document.getElementById('liteNote');if(r)r.remove();await openDemoFractals();return 1})()`); await sleep(2500);
  const setup = await R(`(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));ensureCtx();await ctx.resume();UI.kbPiano=false;CAPS=false;for(const t of S.tracks)t.arm=false;const lead=S.tracks.find(t=>t.name==='Lead');lead.arm=true;changed(true);syncGraph();
    ctlStart();await w(300);const g=CTL.profs.find(p=>p.id==='generic');window.__D={id:'lt-test',name:'LT Test Keys',man:'',inp:{name:'LT Test Keys'},out:null,prof:g,base:'LT Test Keys'};CTL.devs.set('lt-test',window.__D);
    voiceOn(lead,48,.01).off(true);await w(600);ltFastEval();await w(900);ltFastEval();await w(300);
    return JSON.stringify({preset:lead.inst.preset,kind:ltFastKind(lead.inst),fast:LT_HOOKS.fastNotes(),pdc:CPU.pdc})})()`);
  const S0 = JSON.parse(setup); console.log('setup', S0);
  ok(S0.kind && S0.fast.tracks.length === 1 && S0.fast.tracks[0].ready, 'the armed Lead (' + S0.preset + ') is played by the worklet', S0.fast);
  const wins = await app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows().map((w) => ({ url: w.webContents.getURL(), pid: w.webContents.getOSProcessId(), shown: w.isVisible() })));
  const lw = wins.find((w) => /lt-midi/.test(w.url)), mw = wins.find((w) => /index\.html/.test(w.url));
  ok(lw && mw && lw.pid !== mw.pid && !lw.shown, 'the listening window is hidden and runs in its own process', wins);
  /* the listening window reports what it reads: here nobody plugged a keyboard in, so the test names its own */
  await R("LTF.ins=new Set(['LT Test Keys']);1");
  /* sound: a tap on the Lead's engine output */
  await R(`(()=>{const o=[...LTF.tgt.values()][0];window.__A=ctx.createAnalyser();window.__A.fftSize=2048;o.st.out.connect(window.__A);window.__pk=()=>{const b=new Float32Array(2048);__A.getFloatTimeDomainData(b);let m=0;for(const x of b)m=Math.max(m,Math.abs(x));return m};
    window.__OT=()=>{const o=ctx.getOutputTimestamp();return{ct:o.contextTime,pt:o.performanceTime,to:performance.timeOrigin}};window.__VS=[];
    const _v=voiceOn;voiceOn=function(t,p,v){const r=_v.apply(this,arguments);if(r)__VS.push(ctx.currentTime+.002);return r};return 1})()`);
  const quiet = await R('__pk()');
  const n0 = await R('LTF.n'); const tI = Date.now(); await inject([0x90, 72, 100]); await sleep(150);
  const loud = await R('__pk()'); const rep = await R('JSON.stringify(LTF.rep[LTF.rep.length-1])');
  ok((await R('LTF.n')) === n0 + 1 && loud > 0.01 && quiet < 0.001, 'an injected note sounds on the Lead through the fast path', { quiet, loud, rep });
  /* the page gets the same note through its own Web MIDI: it does not start a second voice */
  const sk0 = await R('LTF.skip'), pv0 = await R('PVN.n');
  await R("ctlMsg(__D,new Uint8Array([0x90,72,100]));1");
  ok((await R('LTF.skip')) === sk0 + 1 && (await R('PVN.n')) === pv0 && (await R("LIVE.has('m72')")), 'the page shows and records the note but does not play it again', { skip: await R('LTF.skip') });
  await inject([0x80, 72, 0]); await R("ctlMsg(__D,new Uint8Array([0x80,72,0]));1"); await sleep(1500);
  ok((await R('__pk()')) < 0.002 && !(await R("LIVE.has('m72')")), 'note off lets the voice go', await R('__pk()'));
  /* controller messages are lane C's */
  const cin = await R('CTL.n.in'); await R("ctlMsg(__D,new Uint8Array([0xB0,1,64]));1");
  ok((await R('CTL.n.in')) === cin + 1 && (await R("CTL.last&&CTL.last.type")) === 'cc', 'a controller message still reaches the controller layer');
  /* the sustain pedal */
  await inject([0xB0, 64, 127]); await inject([0x90, 67, 100]); await sleep(60); await inject([0x80, 67, 0]); await sleep(500);
  const held = await R('__pk()'); await inject([0xB0, 64, 0]); await sleep(1500); const rel = await R('__pk()');
  ok(held > 0.01 && rel < 0.002, 'the sustain pedal holds a fast note and lets it go', { held, rel });
  /* a note learned to a control is not played by the fast path */
  await R(`(()=>{const st=ctlG();st.maps.push({id:'mlt',dev:'*',type:'note',ch:0,num:70,target:'master.vol',min:0,max:1,take:'jump',enc:'abs',fb:false});ctlDirty();ltFastEval();return 1})()`); await sleep(300);
  const nb = await R('LTF.n'); await inject([0x90, 70, 100]); await sleep(150);
  ok((await R('LTF.n')) === nb, 'a note learned to a control is left to the controller layer');
  await inject([0x80, 70, 0]); await R(`(()=>{const st=ctlG();st.maps=st.maps.filter(m=>m.id!=='mlt');ctlDirty();ltFastEval();return 1})()`); await sleep(1500);
  /* the measurement: note to first sample, before (the page's path) and after (fast), idle and during a 200 ms long task */
  const conv = `((ct)=>{const o=__OT();return o.to+o.pt+(ct-o.ct)*1000})`;
  const one = async (fast, busy, note) => {
    await R(`UI.ltFast=${fast ? 'undefined' : 'false'};ltFastEval();1`); await sleep(300);
    await R('__VS.length=0;1'); const nr = await R('LTF.rep.length');
    if (busy) await page.evaluate(() => { setTimeout(() => { const e = performance.now() + 200; while (performance.now() < e); }, 0); }); await sleep(busy ? 60 : 5);
    const t0 = Date.now();
    if (fast) await inject([0x90, note, 100]); else page.evaluate((n) => AudioLab.run('ctlMsg(__D,new Uint8Array([0x90,' + n + ',100]))'), note);
    await sleep(400);
    let ct = null;
    if (fast) { const r = JSON.parse(await R('JSON.stringify(LTF.rep.slice(' + nr + '))')); if (r.length) ct = r[0][2]; }
    else { const v = await R('__VS[0]||null'); ct = v; }
    const ms = ct == null ? null : (await R(conv + '(' + ct + ')')) - t0;
    if (fast) await inject([0x80, note, 0]); await R(`ctlMsg(__D,new Uint8Array([0x80,${note},0]));1`); await sleep(250);
    return ms;
  };
  const res = { before: { idle: [], busy: [] }, after: { idle: [], busy: [] } };
  for (let i = 0; i < 8; i++) for (const fast of [false, true]) for (const busy of [false, true]) res[fast ? 'after' : 'before'][busy ? 'busy' : 'idle'].push(await one(fast, busy, 60 + (i % 5)));
  await R('UI.ltFast=undefined;ltFastEval();1');
  const M = { before: { idle: med(res.before.idle.filter((x) => x != null)), busy: med(res.before.busy.filter((x) => x != null)) }, after: { idle: med(res.after.idle.filter((x) => x != null)), busy: med(res.after.busy.filter((x) => x != null)) } };
  console.log('note to first sample (ms, median of 8, on the output clock):', JSON.stringify(M)); console.log('all:', JSON.stringify(res));
  ok(res.after.busy.every((x) => x != null) && res.before.busy.every((x) => x != null), 'every measured note sounded');
  ok(M.before.busy - M.after.busy > 100, 'during a 200 ms long task the fast note does not wait for the page (' + M.before.busy + ' to ' + M.after.busy + ' ms)');
  ok(M.after.idle <= M.before.idle + 3, 'idle, the fast path is no slower (' + M.before.idle + ' to ' + M.after.idle + ' ms)');
  /* a new audio engine (a device change restarts it): a new channel */
  await R(`(async()=>{restartAudio();await new Promise(r=>setTimeout(r,2500));ensureCtx();await ctx.resume();syncGraph();const lead=S.tracks.find(t=>t.name==='Lead');voiceOn(lead,48,.01).off(true);await new Promise(r=>setTimeout(r,800));ltFastEval();await new Promise(r=>setTimeout(r,900));ltFastEval();return 1})()`);
  await sleep(600);
  const n2 = await R('LTF.n'); await inject([0x90, 62, 100]); await sleep(200); await inject([0x80, 62, 0]);
  ok((await R('LTF.n')) === n2 + 1 && (await R('LTF.ctx===ctx')), 'after the engine restarts the fast path plays again', await R('JSON.stringify(LT_HOOKS.fastNotes())'));
  /* disarming: the worklet stops playing the Lead */
  await R("S.tracks.find(t=>t.name==='Lead').arm=false;changed(true);ltFastEval();1"); await sleep(400);
  const n3 = await R('LTF.n'); await inject([0x90, 64, 100]); await sleep(200); await inject([0x80, 64, 0]);
  ok((await R('LTF.n')) === n3 && (await R('LTF.tgt.size')) === 0, 'a disarmed track is not played by the fast path');
  await sleep(500);
  ok(errs.length === 0, 'no page errors', errs);
  /* closing the app window also closes the listening window (it never keeps the app open) */
  const gone = await app.evaluate(async ({ BrowserWindow }) => { const m = BrowserWindow.getAllWindows().find((w) => /index\.html/.test(w.webContents.getURL())); m.destroy(); await new Promise((r) => setTimeout(r, 500)); return BrowserWindow.getAllWindows().length; }).catch(() => 0);
  ok(gone === 0, 'closing the app window leaves no hidden window behind', gone);
  try { await app.evaluate(({ app }) => app.exit(0)); } catch (e) { /* gone */ }
  /* the web page (no desktop shell): nothing changes */
  const b = await chromium.launch(); const pg = await b.newPage(); const we = []; pg.on('pageerror', (e) => we.push(String(e)));
  await pg.goto('file://' + path.join(DIR, 'app', 'index.html')); await pg.waitForFunction(() => window.AudioLab && window.AudioLab.version, null, { timeout: 90000 }); await sleep(1500);
  ok(await pg.evaluate(() => AudioLab.run("!LT_HOOKS.fastNotes().on&&!LTF.chan&&!window.LT_WL.includes('al-poly')===false")), 'in the browser the fast path is off (no shell)');
  await b.close();
  if (JS) fs.writeFileSync(JS, JSON.stringify({ M, res, fail }, null, 1));
  console.log(fail.length ? 'FAILED ' + fail.length : 'all passed'); process.exit(fail.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
