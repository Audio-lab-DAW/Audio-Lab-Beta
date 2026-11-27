/* Task IC6 (27 Nov 2026): the user's round 4 icon picks, in the real desktop app (Electron with desktop/main.js).
   Run after `node desktop/scripts/sync-app.js`:   xvfb-run -a node tools/ui-tests/taskIC6_electron.js [desktop dir] [screenshot dir]
   Checks: J3 stays the default and its big pictures are the ones of v0.270 (icon.icns 128 pt and up, icon.ico 96 px and up, icon.png,
   dock-icon.png are byte for byte the v0.270 files kept in tools/icon-lab/ic6/ref-v0270.json as SHA-256); S1 at 32 px and below
   (icon.icns 16 and 32 pt at 1x and 2x, each 2x drawn for its point size; icon.ico 16 to 32; the favicons); icons.json (the Dipole field
   group with J3, J3 Chart paper, J4, M3 and M5 in P2 and P8, J6, J8 and J10, each with small pictures at 16, 32, 48; every older icon
   kept); a saved choice is kept; choosing a new icon works on the Mac and on Windows (the .ico the app writes has the icon's own small
   pictures); the picker in Settings shows the new icons with their thumbnails; no page or console errors. Uses taskAH_fake.js. */
const { _electron } = require('playwright');
const path = require('path'), os = require('os'), fs = require('fs'), crypto = require('crypto');
const DIR = path.resolve(process.argv[2] || path.join(__dirname, '..', '..', 'desktop'));
const SHOTS = process.argv[3] || null;
const fail = []; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const IA = path.join(DIR, 'icon-assets'), PK = path.join(IA, 'picker');
const sha = (b) => crypto.createHash('sha256').update(b).digest('hex');
function pngSize(b) { return b.slice(1, 4).toString() === 'PNG' ? [b.readUInt32BE(16), b.readUInt32BE(20)] : null; }
async function start(ud, platform) {
  const exe = process.env.ELECTRON || require(path.join(DIR, 'node_modules', 'electron'));
  const app = await _electron.launch({ executablePath: exe, args: ['--no-sandbox', '-r', path.join(__dirname, 'taskAH_fake.js'), DIR], env: { ...process.env, XDG_CONFIG_HOME: ud, AH_PLATFORM: platform || '' } });
  const page = await app.firstWindow(); const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 300)));
  page.on('console', (m) => { if (m.type() === 'error') errs.push('console: ' + m.text().slice(0, 300)); });
  await page.waitForFunction(() => window.AudioLab && window.AudioLab.version, null, { timeout: 90000 }); await sleep(4000);
  return { app, page, errs };
}
const GROUP = ['dipole-field', 'dipole-field-paper', 'field-orbits', 'field-edge', 'field-edge-paper', 'field-depth', 'field-depth-paper',
  'porthole-field', 'measured-field', 'measured-field-paper', 'field-dial', 'field-dial-paper'];
const NEW = ['dipole-field-paper', 'field-edge', 'field-edge-paper', 'field-depth', 'field-depth-paper'];
(async () => {
  const REF = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'icon-lab', 'ic6', 'ref-v0270.json'), 'utf8'));
  // --- icon.icns ---
  const icns = fs.readFileSync(path.join(DIR, 'build', 'icon.icns')), parts = {};
  for (let p = 8; p < icns.length;) { const t = icns.slice(p, p + 4).toString(), n = icns.readUInt32BE(p + 4); parts[t] = icns.slice(p + 8, p + n); p += n; }
  const want = { icp4: 16, ic11: 32, icp5: 32, ic12: 64, ic07: 128, ic13: 256, ic08: 256, ic14: 512, ic09: 512, ic10: 1024 };
  ok(Object.keys(want).every((t) => parts[t] && String(pngSize(parts[t])) === String([want[t], want[t]])), 'icon.icns: every entry from 16 pt to 512 pt @2x with its own pixel size');
  ok(['ic07', 'ic13', 'ic08', 'ic14', 'ic09', 'ic10'].every((t) => sha(parts[t]) === REF.icns[t]), 'icon.icns: 128 pt and up are J3 as shipped in v0.270, byte for byte');
  ok(['icp4', 'ic11', 'icp5', 'ic12'].every((t) => sha(parts[t]) !== REF.icns[t]), 'icon.icns: 16 and 32 pt at 1x and 2x are new (S1)');
  ok(!parts.ic11.equals(parts.icp5), 'icon.icns: 16 pt @2x is drawn for its point size, not the 32 pt picture again');
  // --- icon.ico ---
  const ico = fs.readFileSync(path.join(DIR, 'build', 'icon.ico')), nI = ico.readUInt16LE(4), ent = {};
  for (let k = 0; k < nI; k++) { const w = ico.readUInt8(6 + 16 * k) || 256, len = ico.readUInt32LE(6 + 16 * k + 8), off = ico.readUInt32LE(6 + 16 * k + 12); ent[w] = ico.slice(off, off + len); }
  ok(Object.keys(ent).join() === '16,20,24,32,40,48,64,96,128,256' && Object.keys(ent).every((w) => String(pngSize(ent[w])) === String([+w, +w])), 'icon.ico: 10 sizes, each its own PNG');
  ok([96, 128, 256].every((w) => sha(ent[w]) === REF.ico[w]), 'icon.ico: 96 px and up are J3 as shipped in v0.270');
  ok([16, 20, 24, 32].every((w) => sha(ent[w]) !== REF.ico[w]), 'icon.ico: 16 to 32 px are new (S1)');
  ok(sha(fs.readFileSync(path.join(DIR, 'build', 'icon.png'))) === REF.png && sha(fs.readFileSync(path.join(DIR, 'dock-icon.png'))) === REF.dock, 'icon.png and dock-icon.png: J3 as shipped in v0.270');
  const fav = (z) => fs.readFileSync(path.join(DIR, '..', 'favicon-' + z + '.png'));
  ok(fav(16).equals(ent[16]) && fav(32).equals(ent[32]), 'the website favicons at 16 and 32 are S1, the same pictures as in icon.ico');
  // --- icons.json ---
  const IJ = JSON.parse(fs.readFileSync(path.join(PK, 'icons.json'), 'utf8')), all = IJ.groups.flatMap((g) => g.icons);
  ok(IJ.default === 'dipole-field' && IJ.previous_default === 'ocean-yellow', 'icons.json: the default stays dipole-field (J3 P2)');
  ok(IJ.groups[0].key === 'dipole' && IJ.groups[0].icons.map((i) => i.id).join() === GROUP.join(), 'icons.json: the Dipole field group has J3, J3 Chart paper, J4, M3 and M5 (P2, P8), J6, J8 (P2, P8), J10 (P2, P8)');
  const codes = Object.fromEntries(IJ.groups[0].icons.map((i) => [i.id, i.design_code]));
  ok(codes['dipole-field-paper'] === 'J3 P8' && codes['field-edge'] === 'M3 P2' && codes['field-edge-paper'] === 'M3 P8' && codes['field-depth'] === 'M5 P2' && codes['field-depth-paper'] === 'M5 P8', 'icons.json: the new icons carry their design codes (J3 P8, M3 P2/P8, M5 P2/P8)');
  ok(all.length === 61 && new Set(all.map((i) => i.id)).size === 61, 'icons.json: 61 icons (56 kept + 5 new), every id once');
  let bad = [];
  for (const ic of all) {
    if (!fs.existsSync(path.join(PK, ic.file)) || !fs.existsSync(path.join(PK, 'thumb', ic.id + '.png'))) bad.push(ic.id);
    for (const z in (ic.small || {})) { const b = fs.readFileSync(path.join(PK, ic.small[z])); if (String(pngSize(b)) !== String([+z, +z])) bad.push(ic.id + '@' + z); }
  }
  ok(!bad.length, 'every icon has its picture and thumb, every small picture its size' + (bad.length ? ': ' + bad.join(' ') : ''));
  ok(IJ.groups[0].icons.every((i) => i.small && ['16', '32', '48'].every((z) => i.small[z])), 'every Dipole field icon has its own small pictures at 16, 32 and 48 px');
  ok(fs.readFileSync(path.join(PK, 'small', 'dipole-field-16.png')).equals(ent[16]) && fs.readFileSync(path.join(PK, 'small', 'dipole-field-32.png')).equals(ent[32]), 'the default\'s small pictures in the picker are the S1 pictures of icon.ico');
  // --- the app ---
  const cases = [[null, 'dipole-field', 'no choice saved: J3'], [{ id: 'field-dial', v: 2 }, 'field-dial', 'a choice saved in v0.270 (Field Dial) is kept'],
    [{ id: 'sputnik' }, 'sputnik', 'an older choice (Sputnik) is kept']];
  for (const [saved, exp, label] of cases) {
    const ud = fs.mkdtempSync(path.join(os.tmpdir(), 'alic6-'));
    const t0 = await start(ud, 'darwin'); const udp = await t0.app.evaluate(({ app }) => app.getPath('userData')); await t0.app.close();
    if (saved) fs.writeFileSync(path.join(udp, 'app-icon.json'), JSON.stringify(saved));
    const t = await start(ud, 'darwin'); const info = await t.page.evaluate(() => window.audiolabDesktop.listAppIcons());
    ok(info.current === exp && info.default === 'dipole-field', 'saved choice: ' + label + ' (current ' + info.current + ')');
    if (!saved) {
      const r = await t.app.evaluate(() => global.__AH.dock.slice());
      const dock = await t.app.evaluate((_, f) => global.__AH.sig(global.__AH.nativeImage.createFromPath(f)), path.join(DIR, 'dock-icon.png'));
      ok(r.length >= 1 && r[r.length - 1].sha === dock.sha, 'Mac (macOS 15): at the start the Dock gets dock-icon.png, J3');
      const n0 = r.length, res = await t.page.evaluate(() => window.audiolabDesktop.setAppIcon('field-edge-paper'));
      const pref = JSON.parse(fs.readFileSync(path.join(udp, 'app-icon.json'), 'utf8'));
      const r2 = await t.app.evaluate(() => global.__AH.dock.slice());
      ok(res.ok && pref.id === 'field-edge-paper' && pref.v === 2 && r2.length > n0 && r2[r2.length - 1].w > 0, 'Mac: choosing Field to the Edge, Chart Paper (M3 P8) sets the Dock and is saved');
      await t.page.evaluate(() => window.AudioLab.run("openSettings('colors')")); await sleep(400);
      await t.page.evaluate(() => document.getElementById('apicBox').scrollIntoView()); await sleep(2500);
      const st = await t.page.evaluate(() => ({ groups: [...document.querySelectorAll('#apicBox .apicg')].map((e) => e.textContent),
        first: [...document.querySelectorAll('#apicBox .apicgrid')][0] ? [...[...document.querySelectorAll('#apicBox .apicgrid')][0].querySelectorAll('[data-apic]')].map((b) => b.dataset.apic) : [],
        tiles: document.querySelectorAll('#apicBox [data-apic]').length, on: [...document.querySelectorAll('#apicBox .apict.on')].map((b) => b.dataset.apic),
        def: [...document.querySelectorAll('#apicBox .apict em')].map((e) => e.closest('[data-apic]').dataset.apic),
        loaded: [...document.querySelectorAll('#apicBox .apicgrid')][0] ? [...[...document.querySelectorAll('#apicBox .apicgrid')][0].querySelectorAll('img')].filter((i) => i.complete && i.naturalWidth === 128).length : 0 }));
      ok(st.groups[0] === 'Dipole field' && st.first.join() === GROUP.join() && st.tiles === 61, 'picker: Dipole field first with its 12 icons in order, 61 in all');
      ok(st.on.join() === 'field-edge-paper' && st.def.join() === 'dipole-field', 'picker: the new choice marked in use, Dipole Field marked Default');
      ok(st.loaded === 12, 'picker: all 12 Dipole field thumbnails load (' + st.loaded + ')');
      if (SHOTS) {
        fs.mkdirSync(SHOTS, { recursive: true });
        const box = await t.page.$('#apicBox'); await box.scrollIntoViewIfNeeded();
        await t.page.screenshot({ path: path.join(SHOTS, 'ic6-picker-window.png') });
        const g = await t.page.$('#apicBox .apicgrid'); await g.screenshot({ path: path.join(SHOTS, 'ic6-picker-group.png') });
      }
    }
    ok(!t.errs.length, 'no page errors (' + label + ')' + (t.errs.length ? ': ' + t.errs.join(' | ') : ''));
    await t.app.close();
  }
  // --- Windows: a new icon becomes an .ico with its own small pictures ---
  {
    const ud = fs.mkdtempSync(path.join(os.tmpdir(), 'alic6w-'));
    const t = await start(ud, 'win32'); const udp = await t.app.evaluate(({ app }) => app.getPath('userData'));
    const res = await t.page.evaluate(() => window.audiolabDesktop.setAppIcon('field-depth'));
    await sleep(600);
    const f = path.join(udp, 'app-icon-field-depth.ico'), has = fs.existsSync(f);
    let sizes = [], same = false;
    if (has) {
      const b = fs.readFileSync(f), n = b.readUInt16LE(4), e = {};
      for (let k = 0; k < n; k++) { const w = b.readUInt8(6 + 16 * k) || 256, len = b.readUInt32LE(6 + 16 * k + 8), off = b.readUInt32LE(6 + 16 * k + 12); e[w] = b.slice(off, off + len); sizes.push(w); }
      const px = (buf) => t.app.evaluate((_, b64) => global.__AH.sig(global.__AH.nativeImage.createFromBuffer(Buffer.from(b64, 'base64'))).sha, buf.toString('base64'));
      same = e[16] && (await px(e[16])) === (await px(fs.readFileSync(path.join(PK, 'small', 'field-depth-16.png'))));
    }
    ok(res.ok && has && sizes.sort((a, b) => a - b).join() === '16,32,48,256', 'Windows: choosing Field Depth (M5) writes an .ico with 16, 32, 48 and 256 px (' + sizes.join(' ') + ')');
    ok(same, 'Windows: its 16 px picture is the S1-style small version drawn for M5');
    ok(!t.errs.length, 'no page errors (Windows)' + (t.errs.length ? ': ' + t.errs.join(' | ') : ''));
    await t.app.close();
  }
  console.log(fail.length ? 'FAILED ' + fail.length : 'all pass'); process.exit(fail.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
