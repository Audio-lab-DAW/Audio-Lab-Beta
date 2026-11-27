// AudioLab: the path from this Electron app to the native AudioLab (task MG1, 27 November 2026).
// The user's wish (27 Nov, 19:36 Brussels): people on the Electron app update from inside the app to the native version; a centred
// window explains the move (Install now / Later); projects, settings, presets and the icon choice come along.
//
// What this module does (main process; the window itself is in index.html, functions mg*):
//  1. reads the optional "native" block of the update manifest (desktop/app-version.json, written only by the release gate) and decides
//     whether this computer can install it (platform and processor, minimum OS, a newer version than one already installed here);
//  2. remembers "Later" (3 days) and what was installed, in native-migrate.json in the user-data folder;
//  3. takes the export the page writes (every project as a .audiolab file, the settings, presets, mappings, recent list) and stores it,
//     with a manifest and sha256 checksums, in the folder the native app reads on its first start (docs/native-migration.md);
//  4. downloads the native build with progress, checks its size, sha256 and, when this shell has a public key, its Ed25519 signature;
//  5. installs it: Mac: unpack (.zip with ditto, or a .dmg mounted with hdiutil), copy to /Applications (or ~/Applications when
//     /Applications is not writable), remove the quarantine mark from the copy it wrote itself, open it, quit this app once it runs;
//     Windows: run the per-user installer, quit. The Electron app and its data are never deleted: the user can go back.
// Manifests without a "native" block (every manifest until the first native build is promoted) change nothing.
'use strict';
const path = require('path');
const fs = require('fs');
const os = require('os');
const crypto = require('crypto');
const { execFile, spawn } = require('child_process');

// The Ed25519 public key for native builds (task QL4 fills it, raw 32 bytes in base64). Empty: the sha256 from the manifest is the check.
// With a key, a native build without a valid signature is refused.
const NATIVE_PUBKEY = '';
const LATER_DAYS = 3;
const FORMAT = 'audiolab-migrate', FORMAT_VERSION = 1;

let H = null;              // what main.js hands over: { app, ipcMain, shell, getWin, quitNow, dockAll, isTest, cmpV, rebuildMenu }
let offer = null;          // the native build this computer can install, or null
let lastBlock = null;      // the manifest's native block as last seen (for the status)
let busy = null;           // a running install: { stage, abort }
let exp = null;            // the export being written: { dir, files: [] }

const env = (k) => process.env[k] || '';
const testMode = () => !!(env('AL_UPDATE_BASE') || env('AL_NATIVE_TEST') === '1');
const stateFile = () => path.join(H.app.getPath('userData'), 'native-migrate.json');
function readState() { try { return JSON.parse(fs.readFileSync(stateFile(), 'utf8')) || {}; } catch (e) { return {}; } }
function writeState(s) { try { fs.writeFileSync(stateFile(), JSON.stringify(s, null, 1)); } catch (e) { /* the window asks again next time */ } }
// ~/Library/Application Support/AudioLab/migrate (Mac), %APPDATA%\AudioLab\migrate (Windows), ~/.config/AudioLab/migrate (Linux)
function migrateDir() { return env('AL_MIGRATE_DIR') || path.join(H.app.getPath('appData'), 'AudioLab', 'migrate'); }
const cmpV = (a, b) => { const x = String(a).split('.').map((n) => parseInt(n, 10) || 0), y = String(b).split('.').map((n) => parseInt(n, 10) || 0); for (let i = 0; i < Math.max(x.length, y.length, 3); i++) { const d = (x[i] || 0) - (y[i] || 0); if (d) return d > 0 ? 1 : -1; } return 0; };
function osVersion() { try { return process.getSystemVersion(); } catch (e) { return os.release(); } }
// the keys this computer can use, most specific first. linux-x64 only in tests (there is no Linux native app).
function platformKeys() {
  const p = process.platform, a = process.arch;
  if (p === 'darwin') return ['darwin-' + a, 'darwin'];
  if (p === 'win32') return ['win32-' + a, 'win32'];
  if (p === 'linux' && env('AL_NATIVE_TEST') === '1') return ['linux-' + a, 'linux'];
  return [];
}
const HEX64 = /^[0-9a-f]{64}$/;
function urlOK(u) {
  try { const x = new URL(u); if (x.protocol === 'https:') return true; return testMode() && x.protocol === 'http:' && /^(127\.0\.0\.1|localhost)$/.test(x.hostname); } catch (e) { return false; }
}

/* ---------- 1. the offer ---------- */
// Called by main.js with every manifest it reads. Returns the offer (or null) and tells the page when it changed.
function seen(m) {
  const b = m && typeof m === 'object' ? m.native : null;
  lastBlock = b && typeof b === 'object' ? b : null;
  const was = offer ? offer.version + '|' + offer.sha256 : '';
  offer = pick(lastBlock);
  const now = offer ? offer.version + '|' + offer.sha256 : '';
  if (now !== was) { try { H.rebuildMenu && H.rebuildMenu(); } catch (e) { /* ignore */ } send({ type: 'offer', offer: pub() }); }
  return offer;
}
function pick(b) {
  if (!b || !b.version || !b.platforms || typeof b.platforms !== 'object') return null;
  let key = null, e = null;
  for (const k of platformKeys()) if (b.platforms[k]) { key = k; e = b.platforms[k]; break; }
  if (!e || !urlOK(e.url) || !HEX64.test(String(e.sha256 || '').toLowerCase()) || !(+e.size > 0)) return null;
  if (e.minOS && cmpV(osVersion(), e.minOS) < 0) return null;
  const kind = String(e.kind || (/\.dmg$/i.test(e.url) ? 'dmg' : /\.zip$/i.test(e.url) ? 'zip' : /\.exe$/i.test(e.url) ? 'exe' : '')).toLowerCase();
  if (process.platform === 'win32' ? kind !== 'exe' : !['zip', 'dmg'].includes(kind)) return null;
  if (process.platform !== 'darwin' && kind === 'dmg') return null;
  return { version: String(b.version), notes: String(b.notes || ''), released: String(b.released || ''), platform: key, url: e.url, size: +e.size,
    sha256: String(e.sha256).toLowerCase(), signature: String(e.signature || ''), minOS: String(e.minOS || ''), kind,
    app: String(e.app || (process.platform === 'darwin' ? 'AudioLab.app' : 'AudioLab')), exec: String(e.exec || ''), args: Array.isArray(e.args) ? e.args.map(String) : [] };
}
// what the page may see
function pub() {
  if (!offer) return null;
  const { version, notes, released, platform, size, kind, minOS } = offer;
  return { version, notes, released, platform, size, kind, minOS, signed: !!offer.signature, keyed: !!pubKey() };
}
function status() {
  const st = readState();
  const inst = st.installed && st.installed.path && fs.existsSync(st.installed.path) ? st.installed : null;
  const later = +st.laterAt || 0;
  const due = !!offer && !(inst && cmpV(inst.version, offer.version) >= 0) && (!later || Date.now() - later >= LATER_DAYS * 86400000);
  return { offer: pub(), laterAt: later, laterDays: LATER_DAYS, due, installed: inst, busy: busy ? busy.stage : null, platform: process.platform, migrateDir: migrateDir(), block: !!lastBlock };
}

/* ---------- 2. the events to the page ---------- */
function send(o) { try { const w = H.getWin(); if (w && !w.isDestroyed()) w.webContents.send('al:mg-ev', o); } catch (e) { /* ignore */ } }
let progT = 0;
function progress(o, force) { const t = Date.now(); if (!force && t - progT < 120) return; progT = t; send(Object.assign({ type: 'progress' }, o)); }

/* ---------- 3. the export: projects and settings to the folder the native app reads ---------- */
function safeRel(rel) {
  const r = String(rel || '').replace(/\\/g, '/');
  if (!r || r.startsWith('/') || r.split('/').some((s) => !s || s === '.' || s === '..') || /[<>:"|?*\u0000-\u001f]/.test(r)) throw new Error('bad file name ' + r);
  return r;
}
function exportBegin(o) {
  const base = migrateDir(), parent = path.dirname(base);
  fs.mkdirSync(parent, { recursive: true });
  const dir = base + '.incoming';
  fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
  exp = { dir, files: [], from: o || {} };
  return { ok: true, dir: base };
}
function exportFile(rel, data, kind) {
  if (!exp) throw new Error('no export started');
  const r = safeRel(rel), f = path.join(exp.dir, ...r.split('/'));
  const buf = typeof data === 'string' ? Buffer.from(data, 'utf8') : Buffer.from(data.buffer ? new Uint8Array(data.buffer, data.byteOffset || 0, data.byteLength) : data);
  fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, buf);
  const sha = crypto.createHash('sha256').update(buf).digest('hex');
  exp.files = exp.files.filter((x) => x.path !== r); exp.files.push({ path: r, size: buf.length, sha256: sha, kind: String(kind || '') });
  return { ok: true, sha256: sha, size: buf.length };
}
// the page's part is done: add the shell's own files (icon choice, window size), check every file read back, write the manifest, then swap
// the folder in (the previous export is kept as migrate.previous until the next one), and write READY last.
function exportEnd(meta) {
  if (!exp) throw new Error('no export started');
  const ud = H.app.getPath('userData');
  let icon = null; try { icon = JSON.parse(fs.readFileSync(path.join(ud, 'app-icon.json'), 'utf8')); } catch (e) { /* the default icon */ }
  exportFile('settings/app-icon.json', JSON.stringify({ id: (icon && icon.id) || 'ocean-yellow', chosen: !!(icon && icon.id) }, null, 1), 'icon');
  try { exportFile('settings/window-state.json', fs.readFileSync(path.join(ud, 'window-state.json')), 'window'); } catch (e) { /* none saved */ }
  for (const f of exp.files) {   // read back: what is on disk is what was sent
    const b = fs.readFileSync(path.join(exp.dir, ...f.path.split('/')));
    if (b.length !== f.size || crypto.createHash('sha256').update(b).digest('hex') !== f.sha256) throw new Error('the copy of ' + f.path + ' does not read back the same');
  }
  const m = Object.assign({}, meta && typeof meta === 'object' ? meta : {}, {
    format: FORMAT, formatVersion: FORMAT_VERSION, created: new Date().toISOString(),
    from: Object.assign({ app: 'AudioLab Pro (Electron)', shell: H.app.getVersion(), platform: process.platform, arch: process.arch, os: osVersion(), userData: ud }, (meta && meta.from) || {}),
    to: offer ? { version: offer.version } : null,
    files: exp.files.slice().sort((a, b) => (a.path < b.path ? -1 : 1))
  });
  fs.writeFileSync(path.join(exp.dir, 'manifest.json'), JSON.stringify(m, null, 1));
  const base = migrateDir(), prev = base + '.previous';
  if (fs.existsSync(base)) { fs.rmSync(prev, { recursive: true, force: true }); fs.renameSync(base, prev); }
  fs.renameSync(exp.dir, base);
  fs.writeFileSync(path.join(base, 'READY'), String(m.created) + '\n');
  const n = exp.files.length, projects = exp.files.filter((f) => f.kind === 'project').length;
  exp = null;
  const st = readState(); st.exported = { at: Date.now(), dir: base, files: n, projects }; writeState(st);
  return { ok: true, dir: base, files: n, projects };
}

/* ---------- 4. download and check ---------- */
function pubKey() { return env('AL_NATIVE_PUBKEY') || NATIVE_PUBKEY; }
function verifySig(file, sigB64) {
  const raw = Buffer.from(pubKey(), 'base64');
  if (raw.length !== 32) throw new Error('the public key is not 32 bytes');
  const key = crypto.createPublicKey({ key: Buffer.concat([Buffer.from('302a300506032b6570032100', 'hex'), raw]), format: 'der', type: 'spki' });
  return crypto.verify(null, fs.readFileSync(file), key, Buffer.from(sigB64, 'base64'));
}
const dlDir = () => path.join(H.app.getPath('userData'), 'native-download');
async function download(o, signal) {
  const { net } = require('electron');
  fs.mkdirSync(dlDir(), { recursive: true });
  const name = (path.basename(new URL(o.url).pathname) || 'AudioLab-native').replace(/[^\w.+-]/g, '_');
  const file = path.join(dlDir(), name), part = file + '.part';
  // a file already downloaded and checked is used again
  if (fs.existsSync(file) && fs.statSync(file).size === o.size && (await shaFile(file)) === o.sha256) { progress({ stage: 'download', got: o.size, size: o.size }, true); return file; }
  const r = await net.fetch(o.url, { cache: 'no-store', signal });
  if (!r.ok) throw Object.assign(new Error('the server answered HTTP ' + r.status), { why: 'http' });
  const h = crypto.createHash('sha256'), out = fs.createWriteStream(part);
  let got = 0, stall = null;
  const reader = r.body.getReader();
  const kick = () => { clearTimeout(stall); stall = setTimeout(() => { try { reader.cancel(); } catch (e) { /* ignore */ } }, 60000); };
  try {
    kick();
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      kick(); got += value.length;
      if (got > o.size) throw Object.assign(new Error('the download is larger than the release says'), { why: 'size' });
      h.update(value);
      if (!out.write(Buffer.from(value.buffer, value.byteOffset, value.byteLength))) await new Promise((res) => out.once('drain', res));
      progress({ stage: 'download', got, size: o.size });
    }
  } finally { clearTimeout(stall); await new Promise((res) => out.end(res)); }
  progress({ stage: 'download', got, size: o.size }, true);
  if (got !== o.size) { fs.rmSync(part, { force: true }); throw Object.assign(new Error('the download stopped at ' + got + ' of ' + o.size + ' bytes'), { why: 'size' }); }
  const sha = h.digest('hex');
  if (sha !== o.sha256) { fs.rmSync(part, { force: true }); throw Object.assign(new Error('the checksum does not match: got ' + sha.slice(0, 12) + '…, expected ' + o.sha256.slice(0, 12) + '…'), { why: 'checksum' }); }
  fs.renameSync(part, file);
  return file;
}
function shaFile(f) { return new Promise((res) => { const h = crypto.createHash('sha256'); fs.createReadStream(f).on('data', (d) => h.update(d)).on('end', () => res(h.digest('hex'))).on('error', () => res('')); }); }
function check(file, o) {
  if (pubKey()) {
    if (!o.signature) throw Object.assign(new Error('the release has no signature'), { why: 'signature' });
    let ok = false; try { ok = verifySig(file, o.signature); } catch (e) { ok = false; }
    if (!ok) throw Object.assign(new Error('the signature does not match'), { why: 'signature' });
    return 'sha256 and Ed25519 signature';
  }
  return 'sha256';
}

/* ---------- 5. install ---------- */
function run(cmd, args, opt) {
  return new Promise((res, rej) => execFile(cmd, args, Object.assign({ timeout: 300000, maxBuffer: 8 << 20 }, opt || {}), (err, so, se) => (err ? rej(Object.assign(err, { out: String(se || so || '') })) : res(String(so || '')))));
}
function writable(dir) { try { fs.mkdirSync(dir, { recursive: true }); fs.accessSync(dir, fs.constants.W_OK); return true; } catch (e) { return false; } }
function findApp(dir, want, depth) {
  let L = []; try { L = fs.readdirSync(dir, { withFileTypes: true }); } catch (e) { return null; }
  const hit = L.find((d) => d.isDirectory() && d.name === want) || L.find((d) => d.isDirectory() && /\.app$/i.test(d.name));
  if (hit) return path.join(dir, hit.name);
  if ((depth || 0) < 2) for (const d of L) if (d.isDirectory() && !d.name.startsWith('.') && d.name !== '__MACOSX') { const r = findApp(path.join(dir, d.name), want, (depth || 0) + 1); if (r) return r; }
  return null;
}
// the bundle of the app that is running now (never replaced, never deleted)
function ownBundle() { const m = /^(.*?\.app)(\/|$)/.exec(process.execPath); return m ? m[1] : ''; }
// where the native app goes: /Applications when this user may write there, else ~/Applications (no password asked; nothing the app cannot do)
function macTarget(appName) {
  if (env('AL_NATIVE_DEST')) return path.join(env('AL_NATIVE_DEST'), appName);
  const sys = '/Applications', usr = path.join(os.homedir(), 'Applications');
  const t = path.join(sys, appName);
  if (writable(sys) && (!fs.existsSync(t) || writable(t))) return t;
  return path.join(usr, appName);
}
async function stageMac(file, o, work) {
  const unpacked = path.join(work, 'unpacked');
  fs.rmSync(unpacked, { recursive: true, force: true }); fs.mkdirSync(unpacked, { recursive: true });
  if (o.kind === 'zip') { await run('/usr/bin/ditto', ['-x', '-k', file, unpacked]); return findApp(unpacked, o.app); }
  // a DMG: mounted read-only and out of sight, the app copied out, unmounted again
  const mnt = path.join(work, 'mnt'); fs.mkdirSync(mnt, { recursive: true });
  await run('/usr/bin/hdiutil', ['attach', '-nobrowse', '-readonly', '-noautoopen', '-mountpoint', mnt, file]);
  try {
    const a = findApp(mnt, o.app);
    if (!a) return null;
    const to = path.join(unpacked, path.basename(a));
    await run('/usr/bin/ditto', [a, to]);
    return to;
  } finally { try { await run('/usr/bin/hdiutil', ['detach', mnt, '-force']); } catch (e) { /* ignore */ } }
}
async function installMac(file, o) {
  const work = path.join(dlDir(), 'work');
  progress({ stage: 'install', what: 'unpack' }, true);
  const src = await stageMac(file, o, work);
  if (!src) throw Object.assign(new Error('no .app in the download'), { why: 'bundle' });
  const name = path.basename(src);
  let target = macTarget(name);
  const own = ownBundle();
  if (own && path.resolve(target) === path.resolve(own)) throw Object.assign(new Error('the native app would replace this app'), { why: 'same' });
  progress({ stage: 'install', what: 'copy', to: target }, true);
  const put = async (t) => {
    fs.mkdirSync(path.dirname(t), { recursive: true });
    const tmp = t + '.installing'; fs.rmSync(tmp, { recursive: true, force: true });
    await run('/usr/bin/ditto', [src, tmp]);
    if (fs.existsSync(t)) { const old = t + '.old'; fs.rmSync(old, { recursive: true, force: true }); fs.renameSync(t, old); try { fs.renameSync(tmp, t); } catch (e) { fs.renameSync(old, t); throw e; } fs.rmSync(old, { recursive: true, force: true }); }
    else fs.renameSync(tmp, t);
  };
  try { await put(target); }
  catch (e) {   // /Applications refused after all (an older copy owned by another user): the user's own Applications folder
    const usr = path.join(os.homedir(), 'Applications', name);
    if (env('AL_NATIVE_DEST') || target === usr) throw e;
    target = usr; await put(target);
  }
  // only the copy written here: the quarantine mark, so Gatekeeper does not stop an app this app checked itself
  try { await run('/usr/bin/xattr', ['-dr', 'com.apple.quarantine', target]); } catch (e) { /* not marked */ }
  fs.rmSync(work, { recursive: true, force: true });
  return target;
}
// is the native app running? (its own executable inside the bundle)
async function macRunning(target) {
  try { const out = await run('/usr/bin/pgrep', ['-f', path.join(target, 'Contents', 'MacOS') + '/']); return !!out.trim(); } catch (e) { return false; }
}
async function openMac(target) {
  const a = ['-n', target, '--args', '--migrated-from-electron', migrateDir()];
  try { await run('/usr/bin/open', a, { timeout: 30000 }); } catch (e) { /* Gatekeeper said no, or open failed: the window shows Open Anyway */ }
  for (let i = 0; i < 40; i++) { if (await macRunning(target)) return true; await new Promise((r) => setTimeout(r, 250)); }
  return false;
}
async function installWin(file, o) {
  progress({ stage: 'install', what: 'installer' }, true);
  const args = o.args.length ? o.args : ['--migrated-from-electron', migrateDir()];
  await new Promise((res, rej) => {
    let done = false;
    const p = spawn(file, args, { detached: true, stdio: 'ignore', windowsHide: false });
    p.once('error', (e) => { if (!done) { done = true; rej(Object.assign(e, { why: 'launch' })); } });
    p.once('spawn', () => { if (!done) { done = true; p.unref(); res(); } });
  });
  return file;
}
// tests on Linux only (AL_NATIVE_TEST=1): a zip with a folder and an executable, unpacked into AL_NATIVE_DEST and started
async function installLinux(file, o) {
  const dest = env('AL_NATIVE_DEST') || path.join(os.homedir(), '.local', 'share', 'AudioLab-native');
  progress({ stage: 'install', what: 'unpack' }, true);
  fs.rmSync(dest, { recursive: true, force: true }); fs.mkdirSync(dest, { recursive: true });
  await run('unzip', ['-q', '-o', file, '-d', dest]);
  const exe = path.join(dest, o.exec || o.app);
  if (!fs.existsSync(exe)) throw Object.assign(new Error('no ' + (o.exec || o.app) + ' in the download'), { why: 'bundle' });
  fs.chmodSync(exe, 0o755);
  return exe;
}
function startLinux(exe) {
  return new Promise((res) => { const p = spawn(exe, ['--migrated-from-electron', migrateDir()], { detached: true, stdio: 'ignore' }); p.once('error', () => res(false)); p.once('spawn', () => { p.unref(); res(true); }); });
}

// Install now: the page has exported first (al:mg-export-*). Answers { ok, stage, why, error, target, opened }.
async function install() {
  if (busy) return { ok: false, why: 'busy', stage: busy.stage };
  const o = offer;
  if (!o) return { ok: false, why: 'none', error: 'no native build is offered to this computer' };
  const ac = new AbortController();
  busy = { stage: 'download', abort: () => ac.abort() };
  const fail = (e, stage) => { busy = null; const r = { ok: false, stage, why: (e && e.why) || (ac.signal.aborted ? 'cancelled' : 'error'), error: String((e && e.message) || e) }; send(Object.assign({ type: 'failed' }, r)); return r; };
  let file;
  try { file = await download(o, ac.signal); } catch (e) { return fail(e, 'download'); }
  let how;
  busy.stage = 'check';
  try { how = check(file, o); } catch (e) { fs.rmSync(file, { force: true }); return fail(e, 'check'); }
  progress({ stage: 'check', ok: true, how }, true);
  busy.stage = 'checked';
  return { ok: true, stage: 'checked', how, file: path.basename(file) };
}
// after the export: put it in place and open it. Mac: quit once it runs; Windows: quit once the installer started.
async function finish() {
  const o = offer;
  if (!o || !busy) return { ok: false, why: 'none' };
  const file = path.join(dlDir(), (path.basename(new URL(o.url).pathname) || 'AudioLab-native').replace(/[^\w.+-]/g, '_'));
  busy.stage = 'install';
  let target, opened = false;
  try {
    if (process.platform === 'darwin') target = await installMac(file, o);
    else if (process.platform === 'win32') target = await installWin(file, o);
    else target = await installLinux(file, o);
  } catch (e) { busy = null; const r = { ok: false, stage: 'install', why: e.why || 'install', error: String(e.message || e) + (e.out ? ' (' + e.out.trim().slice(0, 200) + ')' : '') }; send(Object.assign({ type: 'failed' }, r)); return r; }
  const st = readState(); st.installed = { version: o.version, path: target, at: Date.now() }; delete st.laterAt; writeState(st);
  progress({ stage: 'open', target }, true);
  if (process.platform === 'darwin') opened = await openMac(target);
  else if (process.platform === 'win32') opened = true;
  else opened = await startLinux(target);
  busy = null;
  if (opened) { send({ type: 'opened', target }); setTimeout(() => { try { H.quitNow(); } catch (e) { /* ignore */ } }, env('AL_MG_QUIT_MS') ? +env('AL_MG_QUIT_MS') : 1800); }
  else send({ type: 'blocked', target });
  return { ok: true, target, opened };
}

function setup(h) {
  H = h;
  const { ipcMain } = h;
  ipcMain.handle('al:mg-status', () => status());
  ipcMain.handle('al:mg-later', () => { const st = readState(); st.laterAt = Date.now(); writeState(st); return status(); });
  ipcMain.handle('al:mg-prepare', async () => { try { if (H.dockAll) await H.dockAll(); } catch (e) { /* ignore */ } return true; });
  ipcMain.handle('al:mg-export-begin', (e, o) => { try { return exportBegin(o); } catch (x) { return { ok: false, error: String(x.message || x) }; } });
  ipcMain.handle('al:mg-export-file', (e, rel, data, kind) => { try { return exportFile(rel, data, kind); } catch (x) { return { ok: false, error: String(x.message || x) }; } });
  ipcMain.handle('al:mg-export-end', (e, m) => { try { return exportEnd(m); } catch (x) { exp = null; return { ok: false, error: String(x.message || x) }; } });
  ipcMain.handle('al:mg-install', () => install());
  ipcMain.handle('al:mg-finish', () => finish());
  ipcMain.handle('al:mg-cancel', () => { if (busy && busy.stage === 'download') { busy.abort(); return true; } if (busy && busy.stage === 'checked') { busy = null; return true; } return false; });   // checked: the export failed or the user stopped before installing
  ipcMain.handle('al:mg-open', async () => {   // "Open it again" after macOS stopped it, or the menu once installed
    const st = readState(), t = st.installed && st.installed.path;
    if (!t || !fs.existsSync(t)) return false;
    if (process.platform === 'darwin') { const ok = await openMac(t); if (ok) { send({ type: 'opened', target: t }); setTimeout(() => { try { H.quitNow(); } catch (e) { /* ignore */ } }, 1800); } return ok; }
    H.shell.openPath(t); return true;
  });
  ipcMain.handle('al:mg-reveal', (e, what) => {
    if (what === 'security' && process.platform === 'darwin') { H.shell.openExternal('x-apple.systempreferences:com.apple.preference.security?General'); return true; }
    const st = readState(), t = what === 'export' ? migrateDir() : st.installed && st.installed.path;
    if (t && fs.existsSync(t)) { H.shell.showItemInFolder(t); return true; }
    return false;
  });
}

module.exports = { setup, seen, status, offerNow: () => pub(), migrateDir, _test: { pick, cmpV, safeRel } };
