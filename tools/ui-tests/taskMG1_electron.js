/* Task MG1: the path from the Electron app to the native AudioLab, in the real desktop app (desktop/main.js, preload.js, native-migrate.js),
   against a stand-in native build served by a local update server (tools/migrate-tests/fake_native.js, AL_UPDATE_BASE).
     node tools/ui-tests/taskMG1_electron.js [desktop dir]          (Linux: xvfb-run -a; the stand-in installs only with AL_NATIVE_TEST=1, set here)
   Every launch gets its own application-data folder (AL_TEST_APPDATA), so a run on a real computer never touches the user's AudioLab.
   Checks: the window appears by itself, centred, and stays until a button is clicked (a click beside it and 12 s of waiting do nothing);
   Enter is Install now, Esc and the close cross are Later; Later hides it for 3 days (a restart does not bring it back, 3 days later it does);
   the app menu and the command list offer it; a wrong checksum refuses (nothing exported, nothing installed, the app keeps running);
   Install now downloads, checks, exports, installs, opens the stand-in and quits; the projects read back from the export equal the app's;
   on the Mac the installed copy has no quarantine mark; a signature is checked when the shell has a key; the shell before MG1 ignores the block. */
const { _electron } = require('playwright');
const path = require('path'), os = require('os'), fs = require('fs'), zlib = require('zlib'), crypto = require('crypto'), { spawn, execFileSync } = require('child_process');
const ROOT = path.join(__dirname, '..', '..');
const DIR = path.resolve(process.argv[2] || path.join(ROOT, 'desktop'));
const fail = []; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) fail.push(m); return c; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const exe = process.env.ELECTRON || require(path.join(DIR, 'node_modules', 'electron'));
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'almg-'));
const plat = process.platform;
if (plat === 'linux') process.env.AL_NATIVE_TEST = '1';
if (!fs.existsSync(path.join(DIR, 'app', 'index.html'))) execFileSync('node', [path.join(DIR, 'scripts', 'sync-app.js')]);

function server(tag, flags) {
  return new Promise((res, rej) => {
    if (plat === 'darwin' && process.env.MG_DMG === '1') flags = [...flags, '--dmg'];   // MG_DMG=1: the Mac stand-in as a DMG (mounted with hdiutil) instead of a zip
    const p = spawn('node', [path.join(ROOT, 'tools', 'migrate-tests', 'fake_native.js'), path.join(TMP, 'srv-' + tag), '0', ...flags], { stdio: ['ignore', 'pipe', 'inherit'] });
    let out = '', key = '';
    p.stdout.on('data', (d) => { out += d; const k = /PUBKEY (\S+)/.exec(out); if (k) key = k[1]; const m = /READY (\d+)/.exec(out); if (m) res({ p, port: +m[1], key, line: out.trim().split('\n').pop() }); });
    p.on('exit', (c) => rej(new Error('fake_native exited ' + c + ': ' + out)));
    setTimeout(() => rej(new Error('fake_native did not start: ' + out)), 120000);
  });
}
async function launch(srv, tag, extra, dir) {
  const ad = path.join(TMP, 'appdata-' + tag); fs.mkdirSync(ad, { recursive: true });
  const env = { ...process.env, AL_UPDATE_BASE: `http://127.0.0.1:${srv.port}/`, AL_TEST_APPDATA: ad, XDG_CONFIG_HOME: ad, AL_NATIVE_DEST: path.join(TMP, 'dest-' + tag), AL_MG_QUIT_MS: '1500', ...(extra || {}) };
  const app = await _electron.launch({ executablePath: exe, args: ['--no-sandbox', dir || DIR], env, timeout: 120000 });
  const page = await app.firstWindow(); const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 300)));
  await page.waitForFunction(() => window.AudioLab && window.AudioLab.version, null, { timeout: 120000 });
  const R = (c) => page.evaluate((c) => window.AudioLab.run(c), c);
  let exited = false; app.process().on('exit', () => { exited = true; });
  return { app, page, R, errs, ad, dest: env.AL_NATIVE_DEST, mig: path.join(ad, 'AudioLab', 'migrate'), ud: path.join(ad, 'AudioLab Studio'), get exited() { return exited; } };
}
const shown = (A) => A.page.evaluate(() => { const m = document.querySelector('#mgM .mgw'); if (!m) return null; const r = m.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2, w: innerWidth, h: innerHeight, t: (document.getElementById('mgT') || {}).textContent || '', btn: [...m.querySelectorAll('.mgb button')].map((b) => b.textContent), focus: document.activeElement && document.activeElement.textContent || '', ph: document.querySelector('#mgM ol.mgst') ? 'steps' : 'offer' }; });
async function waitFor(fn, secs) { const t0 = Date.now(); while (Date.now() - t0 < secs * 1000) { const v = await fn().catch(() => null); if (v) return v; await sleep(250); } return null; }
async function close(A) { try { await A.app.evaluate(({ app }) => { app.exit(0); }); } catch (e) { /* gone */ } await sleep(500); }
function readAudiolab(f) {   // a .audiolab file: gzip, then "AUDIOLAB", version, json length, json, audio
  let u = fs.readFileSync(f); if (u[0] === 0x1f && u[1] === 0x8b) u = zlib.gunzipSync(u);
  if (u.subarray(0, 8).toString() !== 'AUDIOLAB') throw new Error('not an AudioLab file');
  const jl = u.readUInt32LE(12); const J = JSON.parse(u.subarray(16, 16 + jl).toString('utf8')); J._audioBytes = u.length - 16 - jl; return J;
}

(async () => {
  console.log('platform', plat, process.arch, '| desktop', DIR);
  // ---------- 1. the offer: the window, centred, persistent, Later ----------
  const good = await server('good', []); console.log('     server:', good.line);
  let A = await launch(good, 'a');
  console.log('     app', await A.app.evaluate(({ app }) => app.getVersion()), 'program', await A.R('VERSION'));
  let w = await waitFor(() => shown(A), 40);
  ok(!!w, 'the window opens by itself when the manifest offers a native build (' + (w ? w.t : 'not shown in 40 s') + ')');
  if (w) {
    ok(w.t === 'AudioLab is becoming a native app', 'title: ' + w.t);
    ok(Math.abs(w.x - w.w / 2) <= 2 && Math.abs(w.y - w.h / 2) <= 2, `centred: middle at ${w.x.toFixed(0)},${w.y.toFixed(0)} in a ${w.w}x${w.h} window`);
    ok(/Later/.test(w.btn.join('|')) && /Install now/.test(w.btn.join('|')), 'buttons: ' + w.btn.join(' | '));
    ok(/Install now/.test(w.focus), 'Install now has the focus (Enter): ' + w.focus);
    const txt = await A.page.evaluate(() => document.querySelector('#mgM').innerText);
    ok(/sound engine/.test(txt) && /VST3/.test(txt) && /same look/i.test(txt) && /projects/i.test(txt) && /presets/.test(txt) && /icon/.test(txt) && /MB/.test(txt) && /minute/.test(txt), 'it says what changes, what comes along, size and time');
    await A.page.mouse.click(8, 8); await A.page.keyboard.press('Space'); await sleep(12000);
    ok(!!(await shown(A)), 'still there after a click beside it, a key and 12 s');
    const menu = await A.app.evaluate(({ Menu }) => { const L = []; const walk = (m) => { for (const i of m.items) { L.push(i.label); if (i.submenu) walk(i.submenu); } }; walk(Menu.getApplicationMenu()); return L; });
    ok(menu.includes('Install the native AudioLab…'), 'the app menu has "Install the native AudioLab…"');
    ok(await A.R("SCM.has('mg.native')?1:0") === 1, 'the command list has "Install the native AudioLab"');
    await A.page.keyboard.press('Escape'); await sleep(600);
    ok(!(await shown(A)), 'Esc closes it (Later)');
    const st = JSON.parse(fs.readFileSync(path.join(A.ud, 'native-migrate.json'), 'utf8'));
    ok(st.laterAt && Date.now() - st.laterAt < 60000, 'Later is remembered (native-migrate.json)');
    // the Updates window keeps the offer
    await A.R('(()=>{updOpen();return 1})()'); await sleep(1500);
    ok(await A.page.evaluate(() => !!document.querySelector('#updDlg .mgur button')), 'the Updates window shows "Install the native AudioLab…"');
    await A.page.evaluate(() => document.querySelector('#updDlg .mgur button').click()); await sleep(800);
    ok(!!(await shown(A)), 'which opens the window again');
    await A.page.evaluate(() => document.querySelector('#mgM .mgx').click()); await sleep(600);
    ok(!(await shown(A)), 'the close cross closes it (Later)');
    await A.R("(()=>{const d=document.getElementById('updDlg');if(d)d.remove();return 1})()");
  }
  // a restart within 3 days: not shown
  await close(A);
  A = await launch(good, 'a');
  await sleep(20000);
  ok(!(await shown(A)), 'after a restart within 3 days it does not open by itself');
  await close(A);
  const sf = path.join(A.ud, 'native-migrate.json'); const st2 = JSON.parse(fs.readFileSync(sf, 'utf8')); st2.laterAt = Date.now() - 3 * 86400000 - 60000; fs.writeFileSync(sf, JSON.stringify(st2));
  A = await launch(good, 'a');
  ok(!!(await waitFor(() => shown(A), 40)), '3 days after Later it opens again');
  await close(A);

  // ---------- 2. a wrong checksum refuses ----------
  const bad = await server('bad', ['--bad-sha']);
  A = await launch(bad, 'b');
  w = await waitFor(() => shown(A), 40);
  if (ok(!!w, 'the window opens (wrong checksum build)')) {
    await A.page.keyboard.press('Enter');
    const e = await waitFor(() => A.page.evaluate(() => { const t = document.getElementById('mgT'); return t && /not installed/.test(t.textContent) ? document.querySelector('#mgM').innerText : null; }), 60);
    ok(!!e && /checksum/.test(e), 'Enter = Install now; a wrong checksum: "' + (e ? e.split('\n').slice(0, 3).join(' / ') : 'no error shown') + '"');
    ok(!fs.existsSync(A.mig) && !fs.existsSync(A.dest), 'nothing exported, nothing installed');
    await sleep(3000); ok(!A.exited, 'the app keeps running');
    ok(/Try again/.test((await shown(A) || { btn: [] }).btn.join('|')), 'it offers Try again and Later');
  }
  await close(A); bad.p.kill();

  // ---------- 3. a signature: wrong one refused when the shell has the key ----------
  const sigbad = await server('sigbad', ['--bad-sig']);
  A = await launch(sigbad, 's', { AL_NATIVE_PUBKEY: sigbad.key });
  if (ok(!!(await waitFor(() => shown(A), 40)), 'the window opens (signed build, wrong signature)')) {
    await A.page.keyboard.press('Enter');
    const e = await waitFor(() => A.page.evaluate(() => { const t = document.getElementById('mgT'); return t && /not installed/.test(t.textContent) ? document.querySelector('#mgM').innerText : null; }), 60);
    ok(!!e && /signed/.test(e), 'a wrong Ed25519 signature is refused');
  }
  await close(A); sigbad.p.kill();

  // ---------- 4. Install now: download, check, export, install, open, quit ----------
  const signed = await server('signed', ['--sign']);
  const real = plat === 'darwin' && process.env.MG_REAL_DEST === '1';   // MG_REAL_DEST=1 (throw-away CI Macs only): into /Applications as for a user
  A = await launch(signed, 'c', Object.assign({ AL_NATIVE_PUBKEY: signed.key }, real ? { AL_NATIVE_DEST: '' } : {}));
  if (real) A.dest = '/Applications';   // or ~/Applications when /Applications is not writable (checked below)
  if (ok(!!(await waitFor(() => shown(A), 40)), 'the window opens (good signed build)')) {
    // some work to bring along: a second tab with notes, a saved project, a setting, a controller setting
    await A.R("(()=>{const keep=S;demo();const ps=S;S=keep;PJ.list.push({id:'pmg1',name:'MG1 test song',S:ps,dirty:true});saveProjects();const L=savedList();L.unshift({name:'MG1 saved',t:Date.now(),S:JSON.parse(JSON.stringify(ps))});savedPut(L);UI.mgTestSetting=42;UI.ctlStop=false;saveUINow();return 1})()");
    await sleep(500);
    const before = JSON.parse(await A.R("JSON.stringify({open:[...PJ.list,...(PJ.win||[])].map(p=>({name:p.name,S:p.id===PJ.cur?S:p.S})),saved:savedList().filter(q=>q&&q.S).map(q=>({name:q.name,S:q.S})),ui:UI})"));
    const t0 = Date.now();
    await A.page.evaluate(() => document.querySelector('#mgM .mgb button.pri').click());
    let sawBar = false; const tt = Date.now();
    while (!A.exited && Date.now() - tt < 180000) { if (!sawBar) sawBar = await A.page.evaluate(() => !!document.querySelector('#mgM .mgbar')).catch(() => false); await sleep(100); }
    ok(sawBar, 'the download shows its progress');
    ok(A.exited, 'the app quit after opening the native app (' + ((Date.now() - t0) / 1000).toFixed(1) + ' s)');
    // the stand-in started, with the migrate folder
    const mk = path.join(A.mig, 'stand-in-started.json');
    const started = await waitFor(async () => fs.existsSync(mk) && JSON.parse(fs.readFileSync(mk, 'utf8')), 20);
    ok(!!started && started.args.includes('--migrated-from-electron'), 'the stand-in native app started with --migrated-from-electron and the folder: ' + (started ? started.args : 'no marker'));
    if (plat === 'darwin') {
      let app = path.join(A.dest, 'AudioLab.app'); if (real && !fs.existsSync(app)) app = path.join(os.homedir(), 'Applications', 'AudioLab.app');
      ok(fs.existsSync(path.join(app, 'Contents', 'MacOS', 'AudioLab')), 'installed: ' + app);
      let q = ''; try { q = execFileSync('/usr/bin/xattr', ['-p', 'com.apple.quarantine', app], { stdio: ['ignore', 'pipe', 'ignore'] }).toString(); } catch (e) { q = ''; }
      ok(!q, 'the installed copy has no quarantine mark (the stand-in carried one)');
      let sig = ''; try { execFileSync('/usr/bin/codesign', ['--verify', '--deep', app]); sig = 'valid'; } catch (e) { sig = 'not valid'; }
      console.log('     ad hoc signature of the installed copy: ' + sig);
    } else if (plat === 'linux') ok(fs.existsSync(path.join(A.dest, 'AudioLab', 'AudioLab')), 'installed (Linux test install): ' + A.dest);
    // the export: manifest, checksums, projects read back equal
    let M = null; try { M = JSON.parse(fs.readFileSync(path.join(A.mig, 'manifest.json'), 'utf8')); } catch (e) { M = null; }
    ok(!!M && M.format === 'audiolab-migrate' && M.formatVersion === 1 && fs.existsSync(path.join(A.mig, 'READY')), 'migrate folder with manifest.json (format 1) and READY: ' + A.mig);
    if (M) {
      let bad = 0; for (const f of M.files) { const b = fs.readFileSync(path.join(A.mig, ...f.path.split('/'))); if (b.length !== f.size || crypto.createHash('sha256').update(b).digest('hex') !== f.sha256) bad++; }
      ok(!bad && M.files.length >= 8, `every file matches its checksum (${M.files.length} files, ${M.counts.projects} projects, audio missing ${M.counts.audioMissing})`);
      const I = JSON.parse(fs.readFileSync(path.join(A.mig, 'projects', 'index.json'), 'utf8')).projects;
      const eq = (a, b) => JSON.stringify(a, nw) === JSON.stringify(b, nw), nw = (k, v) => (k === 'work' && v && typeof v === 'object' && 'o' in v ? undefined : v);   // S.work counts minutes the song is open: it may tick between the snapshot and the export
      const where = (a, b, p) => { if (eq(a, b)) return ''; if (!a || !b || typeof a !== 'object' || typeof b !== 'object') return (p || '.') + ': ' + JSON.stringify(a).slice(0, 60) + ' vs ' + JSON.stringify(b).slice(0, 60); for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) { const w = where(a[k], b[k], (p || '') + '.' + k); if (w) return w; } return p; };
      let same = 0, diff = [];
      before.open.forEach((p, i) => { const x = I.find((q) => q.origin === 'open' && q.order === i + 1); const J = x && readAudiolab(path.join(A.mig, ...x.file.split('/'))); if (J && J.name === p.name && eq(J.project, p.S)) same++; else diff.push(p.name + (J ? ' at ' + where(J.project, p.S) : '')); });
      before.saved.forEach((p, i) => { const x = I.find((q) => q.origin === 'saved' && q.order === i + 1); const J = x && readAudiolab(path.join(A.mig, ...x.file.split('/'))); if (J && J.name === p.name && eq(J.project, p.S)) same++; else diff.push(p.name + ' (saved)'); });
      ok(!diff.length && same === before.open.length + before.saved.length, `projects read back equal: ${same} of ${before.open.length} open and ${before.saved.length} saved` + (diff.length ? '; differ: ' + diff.join(', ') : ''));
      const withAudio = I.map((x) => readAudiolab(path.join(A.mig, ...x.file.split('/')))).filter((J) => (J.audio || []).length);
      ok(withAudio.every((J) => J._audioBytes === J.audio.reduce((s, a) => s + a.ch * a.len * 4, 0)), `audio inside the project files is complete (${withAudio.length} projects with audio)`);
      const ui = JSON.parse(fs.readFileSync(path.join(A.mig, 'settings', 'ui.json'), 'utf8')), ls = JSON.parse(fs.readFileSync(path.join(A.mig, 'settings', 'local-storage.json'), 'utf8'));
      ok(ui.mgTestSetting === 42 && eq(ui, before.ui) && JSON.parse(ls['audiolab-ui']).mgTestSetting === 42, 'settings read back equal (ui.json and the whole storage)');
      ok(fs.existsSync(path.join(A.mig, 'settings', 'presets.json')) && fs.existsSync(path.join(A.mig, 'settings', 'controllers.json')) && JSON.parse(fs.readFileSync(path.join(A.mig, 'settings', 'controllers.json'), 'utf8')).ctlStop === false, 'presets and controller mappings');
      const ic = JSON.parse(fs.readFileSync(path.join(A.mig, 'settings', 'app-icon.json'), 'utf8')); ok(!!ic.id, 'icon choice: ' + ic.id);
      const rc = JSON.parse(fs.readFileSync(path.join(A.mig, 'recent.json'), 'utf8')); ok(rc.open.length === before.open.length && rc.saved.length === before.saved.length, 'recent list');
    }
    ok(fs.existsSync(path.join(A.ud, 'Local Storage')) || fs.existsSync(path.join(A.ud, 'native-migrate.json')), 'the Electron app\'s data is still there');
    ok(!A.errs.length, 'no page errors' + (A.errs.length ? ': ' + A.errs.join(' | ') : ''));
  }
  try { await close(A); } catch (e) { /* already gone */ }
  signed.p.kill();

  // ---------- 5. the shell before MG1 ignores the block ----------
  try {
    const old = path.join(TMP, 'oldshell'); fs.mkdirSync(old, { recursive: true });
    for (const f of fs.readdirSync(DIR)) if (!['node_modules', 'dist', 'app'].includes(f)) fs.cpSync(path.join(DIR, f), path.join(old, f), { recursive: true });
    fs.cpSync(path.join(DIR, 'app'), path.join(old, 'app'), { recursive: true });
    fs.symlinkSync(path.join(DIR, 'node_modules'), path.join(old, 'node_modules'), plat === 'win32' ? 'junction' : 'dir');
    const rev = process.env.MG_OLD_REV || 'cecd2d6';
    for (const f of ['main.js', 'preload.js']) fs.writeFileSync(path.join(old, f), execFileSync('git', ['show', rev + ':desktop/' + f], { cwd: ROOT }));
    fs.rmSync(path.join(old, 'native-migrate.js'), { force: true });
    A = await launch(good, 'old', {}, old);
    const r = await A.page.evaluate(() => window.audiolabDesktop.updateCheck({}));
    await sleep(15000);
    ok(r && r.status === 'current' && !(await shown(A)) && !A.errs.length, 'old shell: manifest with the native block read as before (' + (r && r.status) + '), no window, no error');
    await close(A);
  } catch (e) { ok(false, 'old shell check: ' + e.message); }
  good.p.kill();
  console.log(fail.length ? `\n${fail.length} FAILED` : '\nall checks passed');
  process.exit(fail.length ? 1 : 0);
})().catch((e) => { console.log('FAIL harness: ' + (e && e.stack || e)); process.exit(1); });
