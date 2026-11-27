/* W7 shortcut icon (task AH, v0.219) in the real desktop app: Electron with desktop/main.js, driven by Playwright.
   Run after `node desktop/scripts/sync-app.js`:
     xvfb-run -a node tools/ui-tests/taskAH_electron.js [desktop dir]
   Two starts. As a Mac (the platform name is faked and the Dock only records): the Dock picture at the start and after choosing
   Ocean Yellow is desktop/dock-icon.png, the W7 picture, and another choice still gives its picker picture.
   As it is (Linux, the Windows code path): choosing Ocean Yellow after another icon sets the program's own icon on every window, not the
   picker picture. Linux cannot decode an .ico, so there the W7 Dock picture without its margin stands in; the .ico itself is checked in the build.
   Since task IC4 (27 Nov 2026) the default is J3 "Dipole Field" and the shipped files are desktop/icon-assets/ (W7 stays in shortcut/ as a
   record): the test reads the default and the count from icons.json, so it follows the icon that ships. */
const { _electron } = require('playwright');
const path = require('path'), os = require('os'), fs = require('fs'), crypto = require('crypto');
const DIR = path.resolve(process.argv[2] || path.join(__dirname, '..', '..', 'desktop'));
const fail = []; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const fsha = (f) => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
async function start(platform, rel) {
  const ud = fs.mkdtempSync(path.join(os.tmpdir(), 'alah-'));
  const exe = process.env.ELECTRON || require(path.join(DIR, 'node_modules', 'electron'));
  const app = await _electron.launch({ executablePath: exe, args: ['--no-sandbox', '-r', path.join(__dirname, 'taskAH_fake.js'), DIR], env: { ...process.env, XDG_CONFIG_HOME: ud, AH_PLATFORM: platform || '', AH_DARWIN_REL: rel || '' } });
  const page = await app.firstWindow(); const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 300)));
  await page.waitForFunction(() => window.AudioLab && window.AudioLab.version, null, { timeout: 90000 }); await sleep(6000);
  const rec = () => app.evaluate(() => ({ dock: global.__AH.dock.slice(), win: global.__AH.win.slice() }));
  const img = (f, crop) => app.evaluate((_, a) => { let im = global.__AH.nativeImage.createFromPath(a.f); if (im.isEmpty()) return null; if (a.crop) { const s = im.getSize(), m = Math.round(s.width * a.crop); im = im.crop({ x: m, y: m, width: s.width - 2 * m, height: s.height - 2 * m }); } return global.__AH.sig(im); }, { f, crop: crop || 0 });
  const pick = (id) => page.evaluate((id) => window.audiolabDesktop.setAppIcon(id), id);
  return { app, page, errs, rec, img, pick };
}
(async () => {
  const dockFile = path.join(DIR, 'dock-icon.png'), W7 = path.join(DIR, 'icon-assets');
  const IJ = JSON.parse(fs.readFileSync(path.join(DIR, 'icon-assets', 'picker', 'icons.json'), 'utf8')), DEF = IJ.default, DEFN = IJ.groups.flatMap((g) => g.icons).find((i) => i.id === DEF).name, COUNT = IJ.groups.reduce((n, g) => n + g.icons.length, 0);
  ok(fsha(dockFile) === fsha(path.join(W7, 'dock-icon.png')), 'desktop/dock-icon.png is the shipped file (icon-assets)');
  ok(fsha(path.join(DIR, 'build', 'icon.icns')) === fsha(path.join(W7, 'icon.icns')), 'desktop/build/icon.icns is the shipped file');
  ok(fsha(path.join(DIR, 'build', 'icon.ico')) === fsha(path.join(W7, 'icon.ico')), 'desktop/build/icon.ico is the shipped file');
  const pj = JSON.parse(fs.readFileSync(path.join(DIR, 'package.json'), 'utf8')).build;
  ok(pj.win.icon === 'build/icon.ico' && (pj.win.extraResources || []).some((r) => r.from === 'build/icon.ico' && r.to === 'icon.ico'), 'the Windows build takes build/icon.ico for the program and ships it as resources/icon.ico');
  ok(pj.files.includes('dock-icon.png'), 'dock-icon.png is packed into the app');
  // --- as a Mac ---
  { const t = await start('darwin');
    const info = await t.page.evaluate(() => window.audiolabDesktop.listAppIcons());
    ok(info.default === DEF && info.current === DEF && info.platform === 'darwin', 'Mac: ' + DEFN + ' is the default and the choice (' + info.platform + ')');
    ok(info.groups.reduce((n, g) => n + g.icons.length, 0) === COUNT, 'Mac: ' + COUNT + ' choices');
    const dock = await t.img(dockFile), pickOY = await t.img(path.join(DIR, 'icon-assets', 'picker', DEF + '.png')), other = info.groups[0].icons[1], pickOther = await t.img(path.join(DIR, 'icon-assets', 'picker', other.file));
    let r = await t.rec();
    ok(r.dock.length >= 1 && r.dock[r.dock.length - 1].sha === dock.sha, 'Mac: at the start the Dock gets dock-icon.png (' + r.dock.length + ' call, ' + dock.w + ' px)');
    await t.pick(other.id); await sleep(300); r = await t.rec();
    ok(r.dock[r.dock.length - 1].sha === pickOther.sha, 'Mac: ' + other.name + ' gives its picker picture, as before');
    const n = r.dock.length; const res = await t.pick(DEF); await sleep(300); r = await t.rec();
    ok(res.ok && r.dock.length === n + 1 && r.dock[n].sha === dock.sha, 'Mac: choosing ' + DEFN + ' sets the new Dock picture (dock-icon.png)');
    ok(dock.sha !== pickOY.sha, 'Mac: that is not the picker picture of ' + DEFN);
    ok(!t.errs.length, 'Mac: no page errors' + (t.errs.length ? ': ' + t.errs.join(' | ') : ''));
    await t.app.close(); }
  // --- as a Mac with macOS 26 and the Icon Composer icon in the bundle (task IC1) ---
  { const t = await start('darwin', '25');
    const info = await t.page.evaluate(() => window.audiolabDesktop.listAppIcons());
    const other = info.groups[0].icons[1], pickOther = await t.img(path.join(DIR, 'icon-assets', 'picker', other.file));
    let r = await t.rec();
    ok(r.dock.length === 0, 'macOS 26: at the start with ' + DEFN + ' no Dock picture is set, the bundle icon stays (' + r.dock.length + ' calls)');
    await t.pick(other.id); await sleep(300); r = await t.rec();
    ok(r.dock.length === 1 && r.dock[0].sha === pickOther.sha, 'macOS 26: ' + other.name + ' gives its picker picture, as before');
    const res = await t.pick(DEF); await sleep(300); r = await t.rec();
    ok(res.ok && r.dock.length === 2 && r.dock[1].reset === true, 'macOS 26: back to ' + DEFN + ' hands the Dock back to the bundle icon (null), no bitmap');
    ok(!t.errs.length, 'macOS 26: no page errors' + (t.errs.length ? ': ' + t.errs.join(' | ') : ''));
    await t.app.close(); }
  // --- as it is: the Windows and Linux code path ---
  { const t = await start('');
    const info = await t.page.evaluate(() => window.audiolabDesktop.listAppIcons());
    const other = info.groups[0].icons[1], pickOther = await t.img(path.join(DIR, 'icon-assets', 'picker', other.file), 50 / 512), pickOY = await t.img(path.join(DIR, 'icon-assets', 'picker', DEF + '.png'), 50 / 512);
    const ico = await t.img(path.join(DIR, 'build', 'icon.ico')), want = ico || await t.img(dockFile, 100 / 1024);
    console.log('     this computer ' + (ico ? 'reads' : 'cannot read') + ' an .ico; expected picture: ' + (ico ? 'build/icon.ico' : 'dock-icon.png without its margin') + ' ' + want.w + ' px');
    let r = await t.rec();
    ok(r.win.length === 0, 'Windows path: at the start with ' + DEFN + ' no window icon is set (the program keeps its own icon)');
    await t.pick(other.id); await sleep(300); r = await t.rec();
    ok(r.win.length >= 1 && r.win[r.win.length - 1].sha === pickOther.sha, 'Windows path: ' + other.name + ' gives its picker picture edge to edge, as before');
    const n = r.win.length; await t.pick(DEF); await sleep(300); r = await t.rec();
    ok(r.win.length > n && r.win[r.win.length - 1].sha === want.sha, 'Windows path: back to ' + DEFN + ' sets the program\'s own picture on the window');
    ok(r.win[r.win.length - 1].sha !== pickOY.sha, 'Windows path: that is not the picker picture of ' + DEFN);
    ok(!t.errs.length, 'Windows path: no page errors' + (t.errs.length ? ': ' + t.errs.join(' | ') : ''));
    await t.app.close(); }
  console.log(fail.length ? 'FAILED ' + fail.length : 'all pass'); process.exit(fail.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
