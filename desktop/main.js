// AudioLab Pro desktop wrapper (Electron).
// Loads the web app from a private secure scheme so it is cross-origin isolated
// (SharedArrayBuffer on), grants audio-device / MIDI / file permissions, and adds
// menus, window memory, .audiolab file opening and auto-update.
const { app, BrowserWindow, Menu, protocol, session, shell, dialog, ipcMain, systemPreferences, screen, nativeImage, powerSaveBlocker } = require('electron');
const path = require('path');
const fs = require('fs');
/* The app was called AudioLab Studio before v0.167. Its settings, projects list and downloaded updates stay in the folder with the old name,
   so nothing is lost when the app is installed under the new name. */
if (process.env.AL_TEST_APPDATA) { try { app.setPath('appData', process.env.AL_TEST_APPDATA); } catch (e) {} }   // task MG1: tests only
try { app.setPath('userData', path.join(app.getPath('appData'), 'AudioLab Studio')); } catch (e) {}

const SCHEME = 'audiolab';
const HOST = 'app';
const RELEASES = 'https://github.com/Audio-lab-DAW/Audio-Lab-Beta/releases/latest';
const isMac = process.platform === 'darwin';
const isDev = process.argv.includes('--dev');

protocol.registerSchemesAsPrivileged([
  { scheme: SCHEME, privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true, stream: true } }
]);

// Audio must never be throttled when the window is hidden or covered.
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
app.commandLine.appendSwitch('disable-renderer-backgrounding');
app.commandLine.appendSwitch('disable-background-timer-throttling');
app.commandLine.appendSwitch('disable-backgrounding-occluded-windows');
// Draw on the GPU and hand frames straight to the screen: smoother at 120–240 Hz.
app.commandLine.appendSwitch('enable-gpu-rasterization');
app.commandLine.appendSwitch('enable-zero-copy');

let win = null;
/* task MG1: the path to the native AudioLab (desktop/native-migrate.js): the manifest's optional "native" block, the centred window in the page
   (mg* in index.html), the export of projects and settings, the download, the check and the install. Missing module: nothing is offered. */
let NM = null;
try { NM = require('./native-migrate'); } catch (e) { try { NM = require('./app/native-migrate.js'); } catch (e2) { NM = null; } }   // app/: the copy sync-app.js puts there, so a build made before package.json lists the module still has it
let pendingFile = null;   // a .audiolab path waiting for the app to finish loading
let appReady = false;     // the web app's global functions exist

/* ---------- window state ---------- */
const stateFile = () => path.join(app.getPath('userData'), 'window-state.json');
function loadState() {
  try { return JSON.parse(fs.readFileSync(stateFile(), 'utf8')); } catch (e) { return {}; }
}
function saveState() {
  if (!win || win.isDestroyed()) return;
  try {
    const b = win.getNormalBounds();
    fs.writeFileSync(stateFile(), JSON.stringify({ ...b, max: win.isMaximized(), full: win.isFullScreen(), v120: 1 }));
  } catch (e) { /* ignore */ }
}

/* ---------- local scheme with isolation headers ---------- */
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.woff2': 'font/woff2' };
/* ---------- the AudioLab program can be newer than this app ----------
   The whole DAW is one file (index.html). The app carries a copy, and can download a newer one into the user-data folder and run that instead,
   so updating never needs a new download-and-replace. A new app is only needed when the manifest says so (minShell). */
const cmpV = (a, b) => { const x = String(a).split('.').map(Number), y = String(b).split('.').map(Number); for (let i = 0; i < 3; i++) { const d = (x[i] || 0) - (y[i] || 0); if (d) return d > 0 ? 1 : -1; } return 0; };
const upDir = () => path.join(app.getPath('userData'), 'app-update');
const upMeta = () => path.join(upDir(), 'meta.json');
const upIndex = () => path.join(upDir(), 'index.html');
let liveIndex = null;                 // the downloaded index.html in use, or null = the copy inside the app
let liveVer = null;                   // version of the program that is running
let upState = {};                     // { version, sha256, ok, bad }
function readMeta() { try { return JSON.parse(fs.readFileSync(upMeta(), 'utf8')); } catch (e) { return {}; } }
function writeMeta(m) { try { fs.mkdirSync(upDir(), { recursive: true }); fs.writeFileSync(upMeta(), JSON.stringify(m)); } catch (e) { /* ignore */ } }
function pickContent() {
  liveIndex = null; liveVer = app.getVersion(); upState = readMeta();
  const m = upState;
  if (m.version && !m.reverted && fs.existsSync(upIndex()) && cmpV(m.version, app.getVersion()) > 0) { liveIndex = upIndex(); liveVer = m.version; }
  else if (m.version && cmpV(m.version, app.getVersion()) <= 0) { try { fs.rmSync(upDir(), { recursive: true, force: true }); } catch (e) { /* ignore */ } upState = {}; }   // the app itself is newer now
}
function registerScheme() {
  const root = path.join(__dirname, 'app');
  protocol.handle(SCHEME, async (req) => {
    try {
      const u = new URL(req.url);
      let p = decodeURIComponent(u.pathname);
      if (p === '/' || p === '') p = '/index.html';
      let file = path.normalize(path.join(root, p));
      if (p.startsWith('/app-icons/')) { file = path.normalize(path.join(ICON_DIR, p.slice(11))); if (!file.startsWith(ICON_DIR + path.sep)) return new Response('Forbidden', { status: 403 }); }   // the icon picker's pictures (v0.203)
      else if (!file.startsWith(root)) return new Response('Forbidden', { status: 403 });
      if (p === '/index.html' && liveIndex) file = liveIndex;
      const data = await fs.promises.readFile(file);
      return new Response(data, {
        status: 200,
        headers: {
          'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream',
          'Cross-Origin-Opener-Policy': 'same-origin',
          'Cross-Origin-Embedder-Policy': 'require-corp',
          'Cross-Origin-Resource-Policy': 'same-origin',
          'Cache-Control': 'no-store'
        }
      });
    } catch (e) {
      return new Response('Not found', { status: 404 });
    }
  });
}

/* ---------- app icon: J3 Dipole Field by default (task IC4; Ocean Yellow before), any picker icon by choice (v0.203) ----------
   The choice lives in app-icon.json in the user-data folder. macOS: the Dock icon while the app runs (Finder and Launchpad keep the
   bundle icon, which cannot change without breaking the app's signature). Windows: every window and the taskbar, plus the Start menu
   and desktop shortcuts (an .ico written to the user-data folder). */
const ICON_DIR = path.join(__dirname, 'icon-assets', 'picker');
let iconList = null;
function readIcons() {
  if (iconList) return iconList;
  try { iconList = JSON.parse(fs.readFileSync(path.join(ICON_DIR, 'icons.json'), 'utf8')); } catch (e) { iconList = { default: IC4_ICON.def, groups: [] }; }
  return iconList;
}
// IC4_ICON (task IC4, 27 Nov 2026): the default became J3 "Dipole Field". A choice saved before IC4 carries no version; if it is the
// old default (Ocean Yellow) it meant "the default", so it now gives J3. Choices saved from IC4 on carry v: 2 and are kept as they are.
const IC4_ICON = { def: 'dipole-field' };
function icDef() { return readIcons().default || IC4_ICON.def; }
function findIcon(id) { for (const g of readIcons().groups || []) for (const ic of g.icons || []) if (ic.id === id) return ic; return null; }
const iconPrefFile = () => path.join(app.getPath('userData'), 'app-icon.json');
function savedIcon() {
  try { const j = JSON.parse(fs.readFileSync(iconPrefFile(), 'utf8')), id = j.id; if (!j.v && id === readIcons().previous_default) return icDef(); if (findIcon(id)) return id; } catch (e) { /* none saved */ }
  return icDef();
}
let curIcon = null;
// The picker pictures are 512 px with the Apple margin (50 px). macOS wants the margin; Windows wants the tile edge to edge.
function iconImage(id, full) {
  const def = id === icDef();
  if (def && isMac) { const im = nativeImage.createFromPath(path.join(__dirname, 'dock-icon.png')); if (!im.isEmpty()) return im; }
  const ic = findIcon(id); if (!ic) return null;
  let im = nativeImage.createFromPath(path.join(ICON_DIR, ic.file));
  if (im.isEmpty()) return null;
  if (full) { const s = im.getSize(), m = Math.round(s.width * 50 / 512); im = im.crop({ x: m, y: m, width: s.width - 2 * m, height: s.height - 2 * m }); }
  return im;
}
// Off the Mac the default's picture is the program's own icon.ico (the W7 shortcut icon, v0.219), not the picker picture.
function defaultIcon() {
  for (const f of [path.join(process.resourcesPath || '', 'icon.ico'), path.join(__dirname, 'build', 'icon.ico')]) {
    try { if (fs.existsSync(f)) { const im = nativeImage.createFromPath(f); if (!im.isEmpty()) return im; } } catch (e) { /* try the next */ }
  }
  // Linux cannot read an .ico: the Dock picture without its Apple margin (100 of 1024 px).
  try { let im = nativeImage.createFromPath(path.join(__dirname, 'dock-icon.png')); if (!im.isEmpty()) { const s = im.getSize(), m = Math.round(s.width * 100 / 1024); return im.crop({ x: m, y: m, width: s.width - 2 * m, height: s.height - 2 * m }); } } catch (e) { /* fall through */ }
  return null;
}
// True on macOS 26 or later (Darwin 25+) when the app bundle holds the compiled Icon Composer icon.
function macBundleIcon() {
  try { return isMac && parseInt(require('os').release(), 10) >= 25 && fs.existsSync(path.join(process.resourcesPath || '', 'Assets.car')); } catch (e) { return false; }
}
function winIcon() { if (isMac || !curIcon || curIcon === icDef()) return null; return icoImage(curIcon) || iconImage(curIcon, true); }
// Windows: a picker choice as a multi-size .ico (its own small pictures at 16, 32 and 48 px, task IC4), so the title bar and the
// taskbar show the small versions drawn for those sizes instead of the 512 px picture shrunk. Written once per icon in user data.
function icoFor(id) {
  try {
    const im = iconImage(id, true); if (!im) return null;
    const f = path.join(app.getPath('userData'), 'app-icon-' + id + '.ico');
    if (!fs.existsSync(f)) fs.writeFileSync(f, makeIco(im, findIcon(id)));
    return f;
  } catch (e) { return null; }
}
function icoImage(id) {
  if (process.platform !== 'win32') return null;
  try { const f = icoFor(id); if (!f) return null; const im = nativeImage.createFromPath(f); return im.isEmpty() ? null : im; } catch (e) { return null; }
}
function applyIcon(id, startup) {
  curIcon = id;
  try {
    if (isMac) {
      if (!app.dock) return;
      // macOS 26 and later with the Icon Composer icon in the bundle (Assets.car, task IC1): the Dock draws the app's own icon, which is
      // blue in every icon style. A picture set here is a flat bitmap the system may treat on its own, so the default sets none:
      // nothing at the start, and null (back to the bundle icon) when coming back from another icon.
      if (id === icDef() && macBundleIcon()) {
        if (!startup) { try { app.dock.setIcon(null); } catch (e) { const im = iconImage(id, false); if (im) app.dock.setIcon(im); } }
        return;
      }
      const im = iconImage(id, false); if (im) app.dock.setIcon(im);
      return;
    }
    // Windows and Linux: the default is the program's own icon (from icon.ico), so at start nothing needs doing.
    if (startup && id === icDef()) return;
    const im = (id === icDef() && defaultIcon()) || icoImage(id) || iconImage(id, true);
    if (im) for (const w of BrowserWindow.getAllWindows()) { try { w.setIcon(im); } catch (e) { /* ignore */ } }
  } catch (e) { /* the icon is a nicety, never a reason to fail */ }
}
// A PNG-in-ICO file (Windows Vista and later read these): 256, 48, 32 and 16 px. The icon's own small pictures (icons.json 'small',
// task IC4) are used at 16, 32 and 48 px when it has them; otherwise the big picture is shrunk.
function smallPng(ic, n) {
  try { const f = ic && ic.small && ic.small[String(n)]; if (!f) return null; const im = nativeImage.createFromPath(path.join(ICON_DIR, f)); const s = im.getSize(); return !im.isEmpty() && s.width === n ? im.toPNG() : null; } catch (e) { return null; }
}
function makeIco(im, ic) {
  const pngs = [256, 48, 32, 16].map((n) => ({ n, b: smallPng(ic, n) || im.resize({ width: n, height: n, quality: 'best' }).toPNG() }));
  const head = Buffer.alloc(6 + 16 * pngs.length);
  head.writeUInt16LE(0, 0); head.writeUInt16LE(1, 2); head.writeUInt16LE(pngs.length, 4);
  let off = head.length;
  pngs.forEach((p, i) => { const o = 6 + 16 * i; head.writeUInt8(p.n >= 256 ? 0 : p.n, o); head.writeUInt8(p.n >= 256 ? 0 : p.n, o + 1); head.writeUInt8(0, o + 2); head.writeUInt8(0, o + 3); head.writeUInt16LE(1, o + 4); head.writeUInt16LE(32, o + 6); head.writeUInt32LE(p.b.length, o + 8); head.writeUInt32LE(off, o + 12); off += p.b.length; });
  return Buffer.concat([head, ...pngs.map((p) => p.b)]);
}
// Only the shortcuts the installer made for this very program are touched, and only their icon.
function updateShortcuts(id) {
  if (process.platform !== 'win32' || !app.isPackaged) return;
  try {
    const def = id === icDef();
    const ud = app.getPath('userData');
    let ico = process.execPath;
    if (!def) {
      ico = icoFor(id); if (!ico) return;   // a new name per icon, so Windows does not show a cached picture
    }
    for (const f of fs.readdirSync(ud)) if (/^app-icon-.*\.ico$/.test(f) && path.join(ud, f) !== ico) { try { fs.unlinkSync(path.join(ud, f)); } catch (e) { /* ignore */ } }
    const links = [path.join(app.getPath('appData'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'AudioLab Pro.lnk'), path.join(app.getPath('desktop'), 'AudioLab Pro.lnk')];
    for (const l of links) {
      if (!fs.existsSync(l)) continue;
      let sc; try { sc = shell.readShortcutLink(l); } catch (e) { continue; }
      if (!sc || String(sc.target || '').toLowerCase() !== process.execPath.toLowerCase()) continue;
      if (String(sc.icon || '').toLowerCase() === ico.toLowerCase()) continue;
      shell.writeShortcutLink(l, 'update', { icon: ico, iconIndex: 0 });
    }
  } catch (e) { /* shortcuts keep their icon */ }
}
ipcMain.handle('al:app-icons', () => {
  const L = readIcons();
  return { default: icDef(), current: curIcon || savedIcon(), base: `${SCHEME}://${HOST}/app-icons/`, platform: process.platform,
    groups: (L.groups || []).map((g) => ({ key: g.key, name: g.name, icons: (g.icons || []).map((ic) => ({ id: ic.id, name: ic.name, file: ic.file })) })) };
});
ipcMain.handle('al:set-app-icon', (e, id) => {
  id = String(id || '');
  if (!findIcon(id)) return { ok: false, current: curIcon || savedIcon() };
  try { fs.writeFileSync(iconPrefFile(), JSON.stringify({ id, v: 2 })); } catch (x) { /* still applied for this run */ }
  applyIcon(id, false);
  setTimeout(() => updateShortcuts(id), 50);
  return { ok: true, current: id };
});

/* ---------- permissions: audio devices, MIDI, files ---------- */
const ALLOWED = new Set(['media', 'audioCapture', 'speaker-selection', 'midi', 'midiSysex', 'fileSystem', 'clipboard-read', 'clipboard-sanitized-write', 'fullscreen', 'window-management', 'persistent-storage', 'storage-access', 'unlimited-storage']);
function setupPermissions() {
  const ses = session.defaultSession;
  ses.setPermissionRequestHandler((wc, permission, cb) => cb(ALLOWED.has(permission)));
  ses.setPermissionCheckHandler((wc, permission) => ALLOWED.has(permission));
  // Let device APIs (MIDI, HID, serial) through if the app ever asks.
  if (ses.setDevicePermissionHandler) ses.setDevicePermissionHandler(() => true);
}

/* ---------- main window ---------- */
function createWindow() {
  const st = loadState();
  // First start (or a window saved before v0.120): open at about 80% of the screen, centred.
  const wa = screen.getPrimaryDisplay().workAreaSize;
  const fresh = !st.v120;
  win = new BrowserWindow({
    width: fresh ? Math.round(wa.width * 0.8) : (st.width || Math.round(wa.width * 0.8)),
    height: fresh ? Math.round(wa.height * 0.8) : (st.height || Math.round(wa.height * 0.8)),
    x: fresh ? undefined : st.x,
    y: fresh ? undefined : st.y,
    center: fresh,
    minWidth: 900,
    minHeight: 560,
    backgroundColor: '#0c0e14',
    title: 'AudioLab Pro',
    ...(winIcon() ? { icon: winIcon() } : {}),
    show: false,
    autoHideMenuBar: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      backgroundThrottling: false,
      spellcheck: false
    }
  });
  if (st.max) win.maximize();
  if (st.full) win.setFullScreen(true);
  win.once('ready-to-show', () => win.show());
  win.on('close', (e) => {
    saveState();
    if (quitOK || !appReady) return;
    e.preventDefault();
    askQuit(() => { quitOK = true; if (quitting) app.quit(); else if (win) win.close(); });
  });
  win.on('closed', () => { win = null; appReady = false; if (!quitting) quitOK = false; });

  // Links open in the real browser, never inside the DAW window.
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });
  win.webContents.on('will-navigate', (e, url) => {
    if (!url.startsWith(SCHEME + '://')) { e.preventDefault(); if (/^https?:/i.test(url)) shell.openExternal(url); }
  });

  win.webContents.on('did-finish-load', () => waitForApp());
  win.loadURL(`${SCHEME}://${HOST}/index.html`);
  if (isDev) win.webContents.openDevTools({ mode: 'detach' });
}

// The web app defines its functions in one big script; wait until it is ready.
function waitForApp(tries = 0) {
  if (!win || win.isDestroyed()) return;
  win.webContents.executeJavaScript("!!(window.audiolabHost&&window.audiolabHost.ready())", true)
    .then((ok) => {
      if (ok) { appReady = true; if (liveIndex && !upState.ok) { upState.ok = true; writeMeta(upState); } flushPending(); }
      else if (tries < 80) setTimeout(() => waitForApp(tries + 1), 250);
      else revertContent();
    })
    .catch(() => { if (tries < 80) setTimeout(() => waitForApp(tries + 1), 250); else revertContent(); });
}
// A downloaded version that never starts must not lock the user out: go back to the copy inside the app.
function revertContent() {
  if (!liveIndex || upState.ok) return;
  const bad = upState.version;
  upState = { version: bad, reverted: true }; writeMeta(upState); liveIndex = null; liveVer = app.getVersion();
  if (win && !win.isDestroyed()) { win.reload(); dialog.showMessageBox(win, { type: 'warning', message: `Version ${bad} did not start`, detail: `AudioLab went back to version ${app.getVersion()}. Nothing was lost. The update will be offered again when a newer one is published.` }); }
}

/* ---------- opening .audiolab files ---------- */
function findAudiolabArg(argv) {
  return argv.find((a) => /\.audiolab$/i.test(a) && fs.existsSync(a));
}
function openFileInApp(file) {
  if (!win || win.isDestroyed() || !appReady) { pendingFile = file; return; }
  try {
    const b64 = fs.readFileSync(file).toString('base64');
    const name = JSON.stringify(path.basename(file));
    const js = `(async()=>{const b=atob("${b64}"),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);await window.audiolabHost.open(${name},u)})()`;
    win.webContents.executeJavaScript(js, true).catch((e) => dialog.showErrorBox('Could not open project', String(e)));
    if (win.isMinimized()) win.restore();
    win.focus();
  } catch (e) {
    dialog.showErrorBox('Could not open project', String(e));
  }
}
function flushPending() {
  if (pendingFile) { const f = pendingFile; pendingFile = null; openFileInApp(f); }
}
app.on('open-file', (e, file) => { e.preventDefault(); openFileInApp(file); });   // macOS

/* ---------- menu ---------- */
function runInApp(code) {
  if (win && !win.isDestroyed()) win.webContents.executeJavaScript(code, true).catch(() => {});
}
// task MG1: "Install the native AudioLab…" opens the page's centred window; once installed, "Open the native AudioLab"
function mgMenu() {
  let st = null; try { st = NM && NM.status(); } catch (e) { st = null; }
  if (!st || !st.offer) return [];
  if (st.installed && cmpV(st.installed.version, st.offer.version) >= 0) return [{ label: 'Open the native AudioLab', click: () => runInApp("window.audiolabHost&&window.audiolabHost.mgOpen&&window.audiolabHost.mgOpen(true)") }];
  return [{ label: 'Install the native AudioLab…', click: () => runInApp("window.audiolabHost&&window.audiolabHost.mgOpen&&window.audiolabHost.mgOpen(true)") }];
}
function buildMenu() {
  const tpl = [
    ...(isMac ? [{
      label: 'AudioLab Pro',
      submenu: [
        { role: 'about' },
        { label: 'Check for Updates…', click: () => checkUpdates(true) },
        ...mgMenu(),
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' }, { role: 'hideOthers' }, { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    }] : []),
    {
      label: 'File',
      submenu: [
        { label: 'Open Project…', accelerator: 'CmdOrCtrl+O', click: () => runInApp('window.audiolabHost&&window.audiolabHost.openDialog()') },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit' }
      ]
    },
    { label: 'Edit', submenu: [{ role: 'undo' }, { role: 'redo' }, { type: 'separator' }, { role: 'cut' }, { role: 'copy' }, { role: 'paste' }, { role: 'selectAll' }] },
    {
      label: 'View',
      submenu: [
        { role: 'togglefullscreen' },
        { label: 'Song Overview', click: () => runInApp("window.AudioLab&&window.AudioLab.run('ovwToggle()')") },
        { type: 'separator' },
        { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'reload' }, { role: 'forceReload' }, { role: 'toggleDevTools' }
      ]
    },
    { role: 'windowMenu' },
    {
      label: 'Help',
      submenu: [
        ...(!isMac ? [{ label: 'Check for Updates…', click: () => checkUpdates(true) }, ...mgMenu()] : []),
        { label: 'AudioLab Pro on GitHub', click: () => shell.openExternal('https://github.com/Audio-lab-DAW/Audio-Lab-Beta') },
        { label: 'Releases', click: () => shell.openExternal(RELEASES) }
      ]
    }
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(tpl));
}

/* ---------- updates ---------- */
// 1. The program (index.html): downloaded in the background, checked against its fingerprint, used after a restart of the window.
// 2. The app around it (Electron): only when the manifest asks for a newer one. Windows installs it by itself; the Mac app is not signed, so there the download page opens.
const UPD_BASE = process.env.AL_UPDATE_BASE || '';   // tests point this at a local server
const UPD_API = 'https://api.github.com/repos/Audio-lab-DAW/Audio-Lab-Beta/contents/';
const UPD_RAW = 'https://raw.githubusercontent.com/Audio-lab-DAW/Audio-Lab-Beta/main/';
let autoUpdater = null;
let updReady = null;   // a downloaded version waiting for a restart: { version, notes, size }
let updLast = { status: 'never', at: 0 };   // result of the last check, for the page's update window
let updChain = Promise.resolve();   // checks run one after another, never two at once
/* Every request has a time limit. Before v0.172 a request that never answered (after sleep, on a network that drops packets) left the updater
   "busy" for good, and "Check for updates" then did nothing at all until the app was restarted. */
async function updFetch(file, ms) {
  const { net } = require('electron');
  const tries = UPD_BASE ? [[UPD_BASE + file, {}]] : [[UPD_API + file + '?ref=main', { Accept: 'application/vnd.github.raw+json' }], [UPD_RAW + file + '?t=' + Date.now(), {}]];
  let err = null;
  for (const [url, headers] of tries) {
    const ac = new AbortController(); let tm = null;
    const limit = new Promise((_, rej) => { tm = setTimeout(() => { try { ac.abort(); } catch (e) { /* ignore */ } rej(Object.assign(new Error('no answer in time'), { timeout: true })); }, ms || 20000); });
    try {
      const got = await Promise.race([limit, (async () => { const r = await net.fetch(url, { headers, cache: 'no-store', signal: ac.signal }); if (!r.ok) throw new Error('HTTP ' + r.status); return Buffer.from(await r.arrayBuffer()); })()]);
      clearTimeout(tm); return got;
    } catch (e) { clearTimeout(tm); err = e; }
  }
  throw err || new Error('download failed');
}
function updWhy(e) {
  try { const { net } = require('electron'); if (net.isOnline && !net.isOnline()) return 'offline'; } catch (x) { /* ignore */ }
  if (e && e.timeout) return 'timeout';
  const s = String(e && e.message || e);
  if (/^HTTP /.test(s)) return 'http';
  if (/manifest|JSON|Unexpected/i.test(s)) return 'bad';
  return 'unreachable';
}
// One check. download=false only looks; download=true also fetches the new version and keeps it ready for a restart. Always answers, never hangs.
async function updDo(download) {
  const inst = liveVer || app.getVersion();
  const fin = (o) => { updLast = Object.assign({ installed: inst, app: app.getVersion(), at: Date.now() }, o); return updLast; };
  let m;
  try {
    m = JSON.parse((await updFetch('desktop/app-version.json', 15000)).toString('utf8'));
    if (!m || !m.version || !m.sha256) throw new Error('bad manifest');
    try { if (NM) NM.seen(m); } catch (x) { /* task MG1: a bad native block never stops the program's own update */ }
  } catch (e) {
    if (updReady) return fin({ status: 'ready', latest: updReady.version, notes: updReady.notes || '', size: updReady.size || 0 });
    return fin({ status: 'error', reason: updWhy(e), error: String(e && e.message || e) });
  }
  const base = { latest: m.version, notes: m.notes || '', size: m.size || 0 };
  if (updReady && updReady.version === m.version) return fin(Object.assign({ status: 'ready' }, base));
  if (cmpV(m.version, inst) <= 0) return fin(Object.assign({ status: 'current' }, base));
  if (m.minShell && cmpV(m.minShell, app.getVersion()) > 0) return fin(Object.assign({ status: 'needs-app', minShell: m.minShell, autoApp: !!autoUpdater }, base));
  if (upState.reverted && upState.version === m.version) return fin(Object.assign({ status: 'reverted' }, base));
  if (!download) return fin(Object.assign({ status: 'available' }, base));
  let data;
  try { data = await updFetch('index.html', 120000); } catch (e) { return fin(Object.assign({ status: 'error', reason: updWhy(e), error: String(e && e.message || e) }, base)); }
  const sha = require('crypto').createHash('sha256').update(data).digest('hex');
  if (sha !== m.sha256) return fin(Object.assign({ status: 'publishing' }, base));
  try {
    fs.mkdirSync(upDir(), { recursive: true });
    const tmp = upIndex() + '.part'; fs.writeFileSync(tmp, data); fs.renameSync(tmp, upIndex());
    writeMeta({ version: m.version, sha256: sha, at: Date.now() });
  } catch (e) { return fin(Object.assign({ status: 'error', reason: 'disk', error: String(e && e.message || e) }, base)); }
  updReady = { version: m.version, notes: m.notes || '', size: m.size || data.length };
  return fin(Object.assign({ status: 'ready' }, base));
}
function updCheck(download) { const p = updChain.then(() => updDo(download)); updChain = p.catch(() => {}); return p; }
function setupUpdater() {
  if (!isMac && app.isPackaged) {
    try { ({ autoUpdater } = require('electron-updater')); autoUpdater.logger = null; autoUpdater.autoDownload = true; autoUpdater.autoInstallOnAppQuit = true;
      autoUpdater.on('update-downloaded', (info) => {
        // v0.207 (task Y): the page's own update window first ("Restart and install" calls al:install-app); a system dialog for older programs
        appUpdateToPage({ version: info.version, stage: 'ready', auto: true }).then((ok) => { if (!ok) appReadyDialog(info); });
      });
      autoUpdater.on('error', () => {});
    } catch (e) { autoUpdater = null; }
  }
  if (!app.isPackaged && !UPD_BASE) return;
  setTimeout(() => checkUpdates(false), 8000);
  setInterval(() => checkUpdates(false), 3600 * 1000);   // once an hour
  setInterval(() => { if (updReady) offerRestart(false); }, 6 * 3600 * 1000);   // a dismissed notice comes back after 6 hours
}
// v0.207 (task Y): a new desktop app is shown in the page's centred update window (audiolabHost.appUpdate); false when the program is older
function appUpdateToPage(o) {
  if (!win || win.isDestroyed() || !appReady) return Promise.resolve(false);
  const arg = JSON.stringify(Object.assign({ app: app.getVersion(), notes: (updLast && updLast.notes) || '' }, o));
  return win.webContents.executeJavaScript(`!!(window.audiolabHost&&window.audiolabHost.appUpdate&&window.audiolabHost.appUpdate(${arg}))`, true).catch(() => false);
}
function appReadyDialog(info) {
        dialog.showMessageBox(win, { type: 'info', buttons: ['Restart and update', 'Later'], defaultId: 0, cancelId: 1, message: `AudioLab Pro ${info.version} is ready`, detail: 'Save your project first, then restart to finish updating.' })
          .then((r) => { if (r.response === 0) { quitOK = true; autoUpdater.quitAndInstall(); } });
}
let shellAsked = null;
function needNewApp(m, manual) {
  if (!manual && shellAsked === m.version) return;   // ask once per version, not at every check
  shellAsked = m.version;
  if (!manual) {   // v0.207 (task Y): the page's window, a system dialog only for older programs
    if (autoUpdater) autoUpdater.checkForUpdates().catch(() => {});
    appUpdateToPage({ version: m.version, notes: m.notes || '', stage: 'needed', auto: !!autoUpdater }).then((ok) => { if (!ok) { shellAsked = null; needNewAppDialog(m, false, true); } });
    return;
  }
  needNewAppDialog(m, manual, false);
}
function needNewAppDialog(m, manual, checked) {
  shellAsked = m.version;
  if (autoUpdater) { if (!checked) autoUpdater.checkForUpdates().catch(() => {}); if (manual) dialog.showMessageBox(win, { type: 'info', message: `Version ${m.version} needs a newer app`, detail: 'It is being downloaded. You will be asked to restart when it is ready.' }); return; }
  dialog.showMessageBox(win, { type: 'info', buttons: ['Open download page', 'Later'], defaultId: 0, cancelId: 1, message: `Version ${m.version} needs a newer app`, detail: 'This one time, download the new app and replace this one. After that, updates install by themselves again.' })
    .then((r) => { if (r.response === 0) shell.openExternal(RELEASES); });
}
function offerRestart(manual) {
  if (!updReady || !win || win.isDestroyed()) return;
  const v = updReady.version;
  // Preferred: the page's own notice (since v0.207 a centred update window, before that a card at the top right). Older program versions don't have it: then a dialog.
  if (!manual) {
    win.webContents.executeJavaScript(`!!(window.audiolabHost&&window.audiolabHost.updateReady&&window.audiolabHost.updateReady(${JSON.stringify(v)},${JSON.stringify(updReady.notes || '')}))`, true)
      .then((ok) => { if (!ok) offerDialog(); }).catch(() => offerDialog());
    return;
  }
  offerDialog();
}
function offerDialog() {
  if (!updReady || !win || win.isDestroyed()) return;
  const v = updReady.version;
  dialog.showMessageBox(win, { type: 'info', buttons: ['Restart now', 'Later'], defaultId: 0, cancelId: 1, message: `AudioLab ${v} is ready`, detail: (updReady.notes ? updReady.notes + '\n\n' : '') + 'Restarting takes a second and keeps your open projects. With "Later" it is used the next time you start AudioLab.' })
    .then((r) => { if (r.response === 0) applyContent(); });
}
function applyContent() {
  if (!updReady) return false;
  updReady = null; pickContent();
  if (win && !win.isDestroyed()) { appReady = false; win.webContents.executeJavaScript('try{window.audiolabHost&&window.audiolabHost.beforeReload&&window.audiolabHost.beforeReload()}catch(e){}', true).catch(() => {}).then(() => setTimeout(() => { if (win && !win.isDestroyed()) win.reload(); }, 300)); }
  return true;
}
// From the menu, the hourly timer, and program versions older than v0.172 (their button calls this). Newer program versions show their own update window.
async function checkUpdates(manual) {
  if (manual && win && !win.isDestroyed() && appReady) {
    try { if (await win.webContents.executeJavaScript('!!(window.audiolabHost&&window.audiolabHost.updOpen&&(window.audiolabHost.updOpen(),true))', true)) return; } catch (e) { /* older program: dialogs below */ }
  }
  const say = (message, detail, type) => { if (manual && win && !win.isDestroyed()) dialog.showMessageBox(win, { type: type || 'info', message, detail }); };
  const r = await updCheck(true);
  if (r.status === 'ready') offerRestart(manual);
  else if (r.status === 'needs-app') needNewApp({ version: r.latest, notes: r.notes }, manual);
  else if (r.status === 'current') say('AudioLab is up to date.', 'Version ' + r.installed);
  else if (r.status === 'reverted') say(`Version ${r.latest} did not start on this computer`, 'AudioLab stays on version ' + r.installed + ' until a newer one is published.', 'warning');
  else if (r.status === 'publishing') say('The update is still being published.', 'Try again in a few minutes.');
  else say('Could not check for updates.', r.reason === 'offline' ? 'This computer is not connected to the internet.' : r.reason === 'timeout' ? 'GitHub did not answer in time. Try again in a moment.' : 'GitHub could not be reached (' + (r.error || 'unknown reason') + ').', 'warning');
}
ipcMain.handle('al:update-check', (e, o) => updCheck(!!(o && o.download)));
ipcMain.handle('al:update-status', () => { let nat = null; try { nat = NM ? NM.status().offer : null; } catch (e) { nat = null; } return Object.assign({}, updLast, { installed: liveVer || app.getVersion(), app: app.getVersion(), ready: updReady ? updReady.version : null, platform: process.platform, native: nat }); });   // task MG1: native = the native build offered here, or null
ipcMain.handle('al:install-app', () => { if (!autoUpdater) return false; askQuit(() => { quitOK = true; autoUpdater.quitAndInstall(); }); return true; });   // v0.207: "Restart and install" in the page's update window
ipcMain.handle('al:update-app', () => { if (autoUpdater) { autoUpdater.checkForUpdates().catch(() => {}); return 'auto'; } shell.openExternal(RELEASES); return 'page'; });
ipcMain.handle('al:version', () => app.getVersion());
ipcMain.handle('al:program-version', () => liveVer || app.getVersion());

/* ---------- DAC hardware volume (macOS Core Audio helper) ---------- */
const { execFile } = require('child_process');
function alvolPath() {
  return app.isPackaged ? path.join(process.resourcesPath, 'bin', 'alvol') : path.join(__dirname, 'bin', 'alvol');
}
function alvol(args) {
  return new Promise((resolve) => {
    if (!isMac || !fs.existsSync(alvolPath())) return resolve({ error: 'unavailable' });
    execFile(alvolPath(), args, { timeout: 6000 }, (err, stdout) => {
      try { resolve(JSON.parse(String(stdout).trim() || '{}')); } catch (e) { resolve({ error: String(err || e) }); }
    });
  });
}
ipcMain.handle('al:dac-list', () => alvol(['list']));
ipcMain.handle('al:dac-get', (e, uid) => alvol(['get', String(uid || 'default')]));
ipcMain.handle('al:dac-set', (e, uid, v) => alvol(['set', String(uid || 'default'), String(Math.max(0, Math.min(1, +v || 0)))]));
ipcMain.handle('al:check-updates', () => checkUpdates(true));
ipcMain.handle('al:apply-update', () => applyContent());
/* every device with its kind, channels, rate and the rates it offers; setting the device's own sample rate (v0.172) */
ipcMain.handle('al:dac-info', () => alvol(['info']));
ipcMain.handle('al:dac-rate', (e, uid, hz) => alvol(['rate', String(uid || 'default'), String(Math.round(+hz || 0))]));

/* ---------- torn-off projects: each one gets a real window of its own ---------- */
const kids = new Map();   // webContents id -> { win, data }
function kidPrefs() {
  return { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false, sandbox: true, backgroundThrottling: false, spellcheck: false };
}
// is the window over the main window's tab bar? (top ~44 px of its content area)
function overTabs(kw) {
  if (!win || win.isDestroyed() || kw.isDestroyed()) return null;
  const cb = win.getContentBounds(), kb = kw.getBounds(), p = screen.getCursorScreenPoint();
  const inX = p.x >= cb.x && p.x <= cb.x + cb.width;
  const nearTop = kb.y <= cb.y + 44 && kb.y >= cb.y - 60;
  return inX && nearTop ? { x: p.x - cb.x } : null;
}
ipcMain.handle('al:display-hz', () => { try { const d = win && !win.isDestroyed() ? screen.getDisplayMatching(win.getBounds()) : screen.getPrimaryDisplay(); return d.displayFrequency || 0; } catch (e) { return 0; } });
ipcMain.handle('al:is-fullscreen', () => !!(win && !win.isDestroyed() && win.isFullScreen()));
/* ---------- app activity (v0.218, task AO): tell every window whether AudioLab is in front, and save power while it is not ----------
   The page cannot see everything itself: which of the app's windows has the focus, hide (Cmd+H) and minimise. Every change is sent to all windows as
   { focused: one of AudioLab's windows has the focus, visible: this window is shown and not minimised, minimized }. The page answers with
   { playing, frozen }: while something plays the computer is kept from suspending the app (powerSaveBlocker, only then); while a window is frozen
   Chromium may throttle it (backgroundThrottling on), and it runs at full speed again the moment it is not frozen. */
function actState(w) {
  let focused = false, visible = true, minimized = false;
  try { focused = !!BrowserWindow.getFocusedWindow(); } catch (e) { /* ignore */ }
  try { minimized = w.isMinimized(); visible = w.isVisible() && !minimized; } catch (e) { /* ignore */ }
  return { focused, visible, minimized };
}
let actT = null;
function actSend() {
  actT = null;
  for (const w of BrowserWindow.getAllWindows()) { try { if (!w.isDestroyed()) w.webContents.send('al:activity', actState(w)); } catch (e) { /* ignore */ } }
}
// the focus moving from one AudioLab window to another gives a blur and then a focus: wait a moment so the page sees one change
function actSoon() { if (!actT) actT = setTimeout(actSend, 60); }
app.on('browser-window-created', (e, w) => { for (const ev of ['blur', 'focus', 'hide', 'show', 'minimize', 'restore']) w.on(ev, actSoon); });
app.on('did-become-active', actSoon);
app.on('did-resign-active', actSoon);
const actBy = new Map();   // webContents id -> { playing, frozen }
let actPsb = null;
function actPower() {
  let playing = false;
  for (const s of actBy.values()) if (s.playing) playing = true;
  try {
    if (playing && actPsb == null) actPsb = powerSaveBlocker.start('prevent-app-suspension');
    else if (!playing && actPsb != null) { powerSaveBlocker.stop(actPsb); actPsb = null; }
  } catch (e) { /* ignore */ }
}
ipcMain.handle('al:activity-get', (e) => { const w = BrowserWindow.fromWebContents(e.sender); return w ? actState(w) : { focused: true, visible: true, minimized: false }; });
ipcMain.on('al:activity-set', (e, s) => {
  const wc = e.sender, id = wc.id, st = { playing: !!(s && s.playing), frozen: !!(s && s.frozen) };
  if (!actBy.has(id)) wc.once('destroyed', () => { actBy.delete(id); actPower(); });
  actBy.set(id, st);
  try { wc.setBackgroundThrottling(st.frozen); } catch (e2) { /* ignore */ }
  actPower();
});
// processor use of every process of the app, as Electron measures it (for the freeze test and for looking into slowness)
ipcMain.handle('al:metrics', () => {
  try { return { power: actPsb != null, procs: app.getAppMetrics().map((m) => ({ pid: m.pid, type: m.type, name: m.name || m.serviceName || '', cpu: m.cpu ? m.cpu.percentCPUUsage : 0, wakeups: m.cpu ? m.cpu.idleWakeupsPerSecond : 0 })) }; }
  catch (e) { return { power: false, procs: [] }; }
});

ipcMain.handle('al:tear', (e, d) => {
  const disp = screen.getDisplayNearestPoint(screen.getCursorScreenPoint()).workArea;
  const w = Math.round(disp.width * 0.7), h = Math.round(disp.height * 0.75);
  let x = Number.isFinite(d.x) ? d.x : undefined, y = Number.isFinite(d.y) ? d.y : undefined;
  if (x != null) x = Math.max(disp.x, Math.min(disp.x + disp.width - 200, x));
  if (y != null) y = Math.max(disp.y, Math.min(disp.y + disp.height - 100, y));
  const kw = new BrowserWindow({ width: w, height: h, x, y, minWidth: 700, minHeight: 420, backgroundColor: '#0c0e14', title: (d.name || 'Project') + ' · AudioLab Pro', ...(winIcon() ? { icon: winIcon() } : {}), webPreferences: kidPrefs() });
  const id = kw.webContents.id;
  kids.set(id, { win: kw, data: d });
  kw.webContents.setWindowOpenHandler(({ url }) => { if (/^https?:/i.test(url)) shell.openExternal(url); return { action: 'deny' }; });
  kw.loadURL(`${SCHEME}://${HOST}/index.html#alchild-native`);
  let hovering = false;
  kw.on('move', () => {
    const h = overTabs(kw);
    if (h) { if (!hovering) kw.setOpacity(0.35); hovering = true; win.webContents.send('al:dock-hover', { x: h.x, name: d.name }); }
    else if (hovering) { hovering = false; kw.setOpacity(1); win.webContents.send('al:dock-hover', null); }
  });
  kw.on('moved', () => {   // the drag ended: over the tab bar means "put it back"
    const h = overTabs(kw);
    if (hovering && win) win.webContents.send('al:dock-hover', null);
    hovering = false; kw.setOpacity(1);
    if (h) kw.webContents.executeJavaScript(`window.audiolabHost&&window.audiolabHost.dockOut&&window.audiolabHost.dockOut(${JSON.stringify(null)})`).catch(() => {});
  });
  kw.on('close', (ev) => {   // closing the window puts the project back in the tabs, so nothing is lost
    const k = kids.get(id);
    if (!k || k.docked || !win || win.isDestroyed()) return;
    ev.preventDefault();
    kw.webContents.executeJavaScript('window.audiolabHost&&window.audiolabHost.dockOut?window.audiolabHost.dockOut(null):null')
      .catch(() => { k.docked = true; kw.close(); });
    setTimeout(() => { if (!kw.isDestroyed()) { k.docked = true; kw.close(); } }, 6000);
  });
  kw.on('closed', () => kids.delete(id));
  return true;
});
ipcMain.handle('al:child-data', (e) => { const k = kids.get(e.sender.id); return k ? k.data : null; });
ipcMain.handle('al:dock', (e, d) => {
  const k = kids.get(e.sender.id);
  if (d && win && !win.isDestroyed()) { win.webContents.send('al:dock', d); win.show(); win.focus(); }
  if (k) { k.docked = true; setTimeout(() => { if (!k.win.isDestroyed()) k.win.close(); }, 30); }
  return true;
});
ipcMain.on('al:to-main', (e, m) => { if (win && !win.isDestroyed()) win.webContents.send('al:from-child', m); });
async function dockAll() {   // before quitting: every torn-off project comes home first
  const list = [...kids.values()].filter(k => !k.docked && !k.win.isDestroyed());
  await Promise.all(list.map(k => Promise.race([
    k.win.webContents.executeJavaScript('window.audiolabHost&&window.audiolabHost.dockOut?window.audiolabHost.dockOut(null):null').catch(() => {}),
    new Promise(r => setTimeout(r, 4000))
  ])));
  await new Promise(r => setTimeout(r, 300));
}

/* ---------- quit: ask the app to save first ---------- */
let quitOK = false, quitting = false, asking = false;
function askQuit(go) {
  if (asking || !win || win.isDestroyed()) return;
  asking = true;
  win.show(); win.focus();
  dockAll().then(() => win.webContents.executeJavaScript('window.audiolabHost&&window.audiolabHost.quitCheck?window.audiolabHost.quitCheck():true', true))
    .then((ok) => { asking = false; if (ok) go(); else quitting = false; })
    .catch(() => { asking = false; go(); });
}
app.on('before-quit', (e) => {
  if (quitOK || !win || win.isDestroyed() || !appReady) return;
  e.preventDefault(); quitting = true;
  askQuit(() => { quitOK = true; app.quit(); });
});

/* ---------- lifecycle ---------- */
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', (e, argv) => {
    const f = findAudiolabArg(argv);
    if (win) { if (win.isMinimized()) win.restore(); win.focus(); }
    if (f) openFileInApp(f);
  });

  app.whenReady().then(async () => {
    pickContent();
    registerScheme();
    setupPermissions();
    buildMenu();
    const f = findAudiolabArg(process.argv.slice(1));
    if (f) pendingFile = f;
    // macOS only reveals audio-device names after microphone permission; ask once, quietly.
    if (isMac) { try { if (systemPreferences.getMediaAccessStatus('microphone') === 'not-determined') systemPreferences.askForMediaAccess('microphone'); } catch (e) { /* ignore */ } }
    // The chosen icon (J3 Dipole Field unless another was picked, task IC4) in the Dock, also when macOS cached an older one from a previous version.
    applyIcon(savedIcon(), true);
    if (curIcon !== icDef()) setTimeout(() => updateShortcuts(curIcon), 4000);   // an app update puts the installer's shortcuts back
    createWindow();
    setupUpdater();
    try { require('./voice-ai').setup({ ipcMain, app }); } catch (e) { console.warn('AI voices', e); }  // task Z2: AI voices (desktop/voice-ai.js)
    try { require('./native-engine').setup({ ipcMain, app }); } catch (e) { console.warn('native engine', e); }  // task NB-N2b: idle until the page asks (desktop/native-engine.js)
    try { require('./lt-midi').setup({ ipcMain, app, BrowserWindow, session, scheme: SCHEME }); } catch (e) { console.warn('fast MIDI notes', e); }  // task LT-3a: notes past the page's main thread (desktop/lt-midi.js)
    try { if (NM) NM.setup({ app, ipcMain, shell, getWin: () => win, dockAll, rebuildMenu: buildMenu, quitNow: () => { quitOK = true; quitting = true; app.quit(); } }); } catch (e) { console.warn('native migrate', e); }  // task MG1
    app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
  });

  app.on('window-all-closed', () => { if (!isMac) app.quit(); });
}
