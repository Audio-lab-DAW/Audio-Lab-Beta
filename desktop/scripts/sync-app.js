// Copies the web app (../index.html) into desktop/app/. The browser-only
// service-worker bootstrap is left in; it does nothing here because the app is already isolated.
const fs = require('fs'), path = require('path');
const src = path.join(__dirname, '..', '..', 'index.html');
const dstDir = path.join(__dirname, '..', 'app');
let html = fs.readFileSync(src, 'utf8');
const m = html.match(/const VERSION='([\d.]+)'/);
if (m) {
  const pj = path.join(__dirname, '..', 'package.json');
  const j = JSON.parse(fs.readFileSync(pj, 'utf8'));
  const v = m[1].split('.').concat(['0']).slice(0, 3).join('.');
  if (j.version !== v) { j.version = v; fs.writeFileSync(pj, JSON.stringify(j, null, 2) + '\n'); }
  console.log('AudioLab version', m[1], '-> app version', v);
}
fs.mkdirSync(dstDir, { recursive: true });
fs.writeFileSync(path.join(dstDir, 'index.html'), html);
// task MG1: the native-app migration module also goes into app/, which every desktop build packs (main.js loads it from there when the
// build's file list does not name desktop/native-migrate.js yet)
try { fs.copyFileSync(path.join(__dirname, '..', 'native-migrate.js'), path.join(dstDir, 'native-migrate.js')); } catch (e) { /* not there: nothing offered */ }
// Manifest for in-app updates: the installed app compares this with what it runs, downloads ../index.html and checks its fingerprint.
// MIN_SHELL = the oldest app (Electron wrapper) that can run this index.html. Raise it only when main.js, preload.js or Electron must be newer.
const MIN_SHELL = '0.147.0';
if (m) {
  const sha = require('crypto').createHash('sha256').update(Buffer.from(html, 'utf8')).digest('hex');
  let notes = '';
  try { notes = fs.readFileSync(path.join(__dirname, '..', 'update-notes.txt'), 'utf8').trim(); } catch (e) { /* optional */ }
  // RELEASE CHANNEL (the owner's rule, 27 Nov 2026): installed apps update from desktop/app-version.json on main.
  // An ordinary release writes only desktop/app-version-dev.json; the live manifest changes only when the release gate
  // promotes a build that passed the start-up checks (AL_PROMOTE=1 node desktop/scripts/sync-app.js). See CLAUDE.md.
  // task MG1: the optional "native" block (the native AudioLab offered to the Electron app, docs/native-migration.md). Only a promotion writes it:
  // the block already in the live manifest is kept, and the release gate passes a new, checked one in AL_NATIVE_BLOCK (tools/release-gate/native_block.py).
  let native = null;
  if (process.env.AL_PROMOTE === '1') {
    try { native = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'app-version.json'), 'utf8')).native || null; } catch (e) { native = null; }
    if (process.env.AL_NATIVE_BLOCK) native = JSON.parse(fs.readFileSync(process.env.AL_NATIVE_BLOCK, 'utf8'));
  }
  const manifest = JSON.stringify(Object.assign({ version: m[1], sha256: sha, size: Buffer.byteLength(html, 'utf8'), minShell: MIN_SHELL, notes }, native ? { native } : {}), null, 2) + '\n';
  fs.writeFileSync(path.join(__dirname, '..', process.env.AL_PROMOTE === '1' ? 'app-version.json' : 'app-version-dev.json'), manifest);
  if (process.env.AL_PROMOTE !== '1') console.log('Not promoted: installed apps keep their version until the release gate promotes one.');
}
console.log('Synced index.html (' + (html.length / 1048576).toFixed(2) + ' MB)');
