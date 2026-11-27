/* Task IC4 (27 Nov 2026): the J3 app icon and the new picker options, in the real desktop app (Electron with desktop/main.js).
   Run after `node desktop/scripts/sync-app.js`:   xvfb-run -a node tools/ui-tests/taskIC4_electron.js [desktop dir] [screenshot dir]
   Checks: the shipped files (icon.icns with the small master at 16 and 32 pt, icon.ico with 10 sizes, the small ones from the small
   master), icons.json (J3 the default, the seven Dipole field icons with their small pictures, the 49 older icons kept), the choice
   saved before IC4 (Ocean Yellow, the old default, means the default: J3; any other old choice is kept; a choice saved from IC4 on
   is kept even when it is Ocean Yellow), the picker in Settings with the new group first, and no page errors. Uses taskAH_fake.js. */
const { _electron } = require('playwright');
const path = require('path'), os = require('os'), fs = require('fs'), crypto = require('crypto');
const DIR = path.resolve(process.argv[2] || path.join(__dirname, '..', '..', 'desktop'));
const SHOTS = process.argv[3] || null;
const fail = []; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const IA = path.join(DIR, 'icon-assets'), PK = path.join(IA, 'picker');
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
(async () => {
  // --- files ---
  const icns = fs.readFileSync(path.join(DIR, 'build', 'icon.icns')), parts = {};
  for (let p = 8; p < icns.length;) { const t = icns.slice(p, p + 4).toString(), n = icns.readUInt32BE(p + 4); parts[t] = icns.slice(p + 8, p + n); p += n; }
  ok(['icp4', 'icp5', 'ic11', 'ic12', 'ic07', 'ic08', 'ic09', 'ic10', 'ic13', 'ic14'].every((t) => parts[t]), 'icon.icns has every size from 16 pt to 512 pt @2x (' + Object.keys(parts).join(' ') + ')');
  const want = { icp4: 16, icp5: 32, ic11: 32, ic12: 64, ic07: 128, ic13: 256, ic08: 256, ic14: 512, ic09: 512, ic10: 1024 };
  ok(Object.keys(want).every((t) => parts[t] && String(pngSize(parts[t])) === String([want[t], want[t]])), 'icon.icns: each entry has its own pixel size');
  // since IC6 the 16 pt @2x picture is drawn for its point size, so it no longer equals the 32 pt picture (taskIC6_electron.js checks it)
  ok(parts.icp5 && parts.ic11 && String(pngSize(parts.icp5)) === '32,32' && String(pngSize(parts.ic11)) === '32,32', 'icon.icns: 32 px (32 pt and 16 pt @2x) from the small master');
  const ico = fs.readFileSync(path.join(DIR, 'build', 'icon.ico')), nI = ico.readUInt16LE(4), sizes = [];
  for (let k = 0; k < nI; k++) { const w = ico.readUInt8(6 + 16 * k) || 256, len = ico.readUInt32LE(6 + 16 * k + 8), off = ico.readUInt32LE(6 + 16 * k + 12); const s = pngSize(ico.slice(off, off + len)); sizes.push(w); if (!s || s[0] !== w) ok(false, 'icon.ico entry ' + w + ' is a ' + w + ' px PNG'); }
  ok(String(sizes) === '16,20,24,32,40,48,64,96,128,256', 'icon.ico has 10 sizes, each its own PNG: ' + sizes.join(' '));
  const web16 = fs.readFileSync(path.join(DIR, '..', 'favicon-16.png')), web32 = fs.readFileSync(path.join(DIR, '..', 'favicon-32.png'));
  const icoEntry = (w) => { for (let k = 0; k < nI; k++) if ((ico.readUInt8(6 + 16 * k) || 256) === w) { const len = ico.readUInt32LE(6 + 16 * k + 8), off = ico.readUInt32LE(6 + 16 * k + 12); return ico.slice(off, off + len); } return null; };
  ok(web16.equals(icoEntry(16)) && web32.equals(icoEntry(32)), 'the website favicons at 16 and 32 are the small master, the same pictures as in icon.ico');
  const IJ = JSON.parse(fs.readFileSync(path.join(PK, 'icons.json'), 'utf8')), all = IJ.groups.flatMap((g) => g.icons);
  ok(IJ.default === 'dipole-field' && IJ.previous_default === 'ocean-yellow', 'icons.json: the default is dipole-field (J3), the one before was ocean-yellow');
  ok(IJ.groups[0].key === 'dipole' && ['dipole-field', 'field-orbits', 'porthole-field', 'measured-field', 'measured-field-paper', 'field-dial', 'field-dial-paper'].every((id) => IJ.groups[0].icons.some((i) => i.id === id)) && IJ.groups[0].icons[0].id === 'dipole-field', 'icons.json: the Dipole field group comes first with J3, J4, J6, J8, J8 paper, J10, J10 paper');
  ok(all.length >= 56 && new Set(all.map((i) => i.id)).size === all.length, 'icons.json: at least 56 icons (49 kept + 7 of IC4; IC6 adds 5), every id once');
  let bad = [];
  for (const ic of all) {
    if (!fs.existsSync(path.join(PK, ic.file)) || !fs.existsSync(path.join(PK, 'thumb', ic.id + '.png'))) bad.push(ic.id);
    for (const z in (ic.small || {})) { const b = fs.readFileSync(path.join(PK, ic.small[z])); if (String(pngSize(b)) !== String([+z, +z])) bad.push(ic.id + '@' + z); }
  }
  ok(!bad.length, 'every icon has its picture and thumb, every small picture its size' + (bad.length ? ': ' + bad.join(' ') : ''));
  ok(IJ.groups[0].icons.every((i) => i.small && i.small['16'] && i.small['32'] && i.small['48']), 'every new icon has small pictures at 16, 32 and 48 px');
  // --- the saved choice ---
  const cases = [[null, 'dipole-field', 'no choice saved: J3'], [{ id: 'ocean-yellow' }, 'dipole-field', 'Ocean Yellow saved before IC4 (the old default): J3'],
    [{ id: 'sputnik' }, 'sputnik', 'another choice saved before IC4 (Sputnik) is kept'], [{ id: 'ocean-yellow', v: 2 }, 'ocean-yellow', 'Ocean Yellow chosen from IC4 on is kept'],
    [{ id: 'no-such-icon' }, 'dipole-field', 'an unknown id falls back to J3']];
  for (const [saved, exp, label] of cases) {
    const ud = fs.mkdtempSync(path.join(os.tmpdir(), 'alic4-'));
    const t0 = await start(ud, 'darwin'); const udp = await t0.app.evaluate(({ app }) => app.getPath('userData')); await t0.app.close();
    if (saved) fs.writeFileSync(path.join(udp, 'app-icon.json'), JSON.stringify(saved));
    const t = await start(ud, 'darwin'); const info = await t.page.evaluate(() => window.audiolabDesktop.listAppIcons());
    ok(info.current === exp && info.default === 'dipole-field', 'saved choice: ' + label + ' (current ' + info.current + ')');
    if (!saved) {
      const r = await t.app.evaluate(() => global.__AH.dock.slice());
      const dock = await t.app.evaluate((_, f) => global.__AH.sig(global.__AH.nativeImage.createFromPath(f)), path.join(DIR, 'dock-icon.png'));
      ok(r.length >= 1 && r[r.length - 1].sha === dock.sha, 'Mac (macOS 15): at the start the Dock gets dock-icon.png, J3 on the Apple grid');
      const res = await t.page.evaluate(() => window.audiolabDesktop.setAppIcon('field-dial'));
      const pref = JSON.parse(fs.readFileSync(path.join(udp, 'app-icon.json'), 'utf8'));
      ok(res.ok && pref.id === 'field-dial' && pref.v === 2, 'choosing Field Dial is saved with v: 2');
      // the picker in Settings
      await t.page.evaluate(() => window.AudioLab.run("openSettings('colors')")); await sleep(400);
      await t.page.evaluate(() => document.getElementById('apicBox').scrollIntoView()); await sleep(2500);
      const st = await t.page.evaluate(() => ({ groups: [...document.querySelectorAll('#apicBox .apicg')].map((e) => e.textContent), tiles: document.querySelectorAll('#apicBox [data-apic]').length, on: [...document.querySelectorAll('#apicBox .apict.on')].map((b) => b.dataset.apic), def: [...document.querySelectorAll('#apicBox .apict em')].map((e) => e.closest('[data-apic]').dataset.apic), broken: [...document.querySelectorAll('#apicBox img')].filter((i) => i.complete && !i.naturalWidth).map((i) => i.src).slice(0, 5), first: [...document.querySelectorAll('#apicBox .apicgrid')][0] && [...document.querySelectorAll('#apicBox .apicgrid')][0].querySelectorAll('[data-apic]').length }));
      ok(st.groups[0] === 'Dipole field' && st.first >= 7 && st.tiles === all.length, 'picker: Dipole field first with the 7 icons of IC4 (and those of IC6), every icon of icons.json shown (' + st.groups.slice(0, 3).join(', ') + ')');
      ok(st.on.join() === 'field-dial' && st.def.join() === 'dipole-field', 'picker: Field Dial marked in use, Dipole Field marked Default');
      ok(!st.broken.length, 'picker: every thumbnail loads' + (st.broken.length ? ': ' + st.broken.join(' ') : ''));
      if (SHOTS) {
        fs.mkdirSync(SHOTS, { recursive: true });
        const box = await t.page.$('#apicBox'); await box.scrollIntoViewIfNeeded();
        await t.page.screenshot({ path: path.join(SHOTS, 'ic4-picker-window.png') });
        await box.screenshot({ path: path.join(SHOTS, 'ic4-picker.png') });
      }
    }
    ok(!t.errs.length, 'no page errors (' + label + ')' + (t.errs.length ? ': ' + t.errs.join(' | ') : ''));
    await t.app.close();
  }
  console.log(fail.length ? 'FAILED ' + fail.length : 'all pass'); process.exit(fail.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
