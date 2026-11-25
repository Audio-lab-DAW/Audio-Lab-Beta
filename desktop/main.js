// AudioLab Pro desktop wrapper (Electron).
// Loads the web app from a private secure scheme so it is cross-origin isolated
// (SharedArrayBuffer on), grants audio-device / MIDI / file permissions, and adds
// menus, window memory, .audiolab file opening and auto-update.
const { app, BrowserWindow, Menu, protocol, session, shell, dialog, ipcMain, systemPreferences, screen } = require('electron');
const path = require('path');
const fs = require('fs');
/* The app was called AudioLab Studio before v0.167. Its settings, projects list and downloaded updates stay in the folder with the old name,
   so nothing is lost when the app is installed under the new name. */
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
      if (!file.startsWith(root)) return new Response('Forbidden', { status: 403 });
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
function buildMenu() {
  const tpl = [
    ...(isMac ? [{
      label: 'AudioLab Pro',
      submenu: [
        { role: 'about' },
        { label: 'Check for Updates…', click: () => checkUpdates(true) },
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
        ...(!isMac ? [{ label: 'Check for Updates…', click: () => checkUpdates(true) }] : []),
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
let manualCheck = false;
let updBusy = false;
let updReady = null;   // a downloaded version waiting for a restart
async function updFetch(file) {
  const { net } = require('electron');
  const tries = UPD_BASE ? [[UPD_BASE + file, {}]] : [[UPD_API + file + '?ref=main', { Accept: 'application/vnd.github.raw+json' }], [UPD_RAW + file + '?t=' + Date.now(), {}]];
  let err = null;
  for (const [url, headers] of tries) {
    try { const r = await net.fetch(url, { headers, cache: 'no-store' }); if (r.ok) return Buffer.from(await r.arrayBuffer()); err = new Error('HTTP ' + r.status); } catch (e) { err = e; }
  }
  throw err || new Error('download failed');
}
function setupUpdater() {
  if (!isMac && app.isPackaged) {
    try { ({ autoUpdater } = require('electron-updater')); autoUpdater.logger = null; autoUpdater.autoDownload = true; autoUpdater.autoInstallOnAppQuit = true;
      autoUpdater.on('update-downloaded', (info) => {
        dialog.showMessageBox(win, { type: 'info', buttons: ['Restart and update', 'Later'], defaultId: 0, cancelId: 1, message: `AudioLab Pro ${info.version} is ready`, detail: 'Save your project first, then restart to finish updating.' })
          .then((r) => { if (r.response === 0) { quitOK = true; autoUpdater.quitAndInstall(); } });
      });
      autoUpdater.on('error', () => {});
    } catch (e) { autoUpdater = null; }
  }
  if (!app.isPackaged && !UPD_BASE) return;
  setTimeout(() => checkUpdates(false), 8000);
  setInterval(() => checkUpdates(false), 3600 * 1000);   // once an hour
  setInterval(() => { if (updReady) offerRestart(); }, 6 * 3600 * 1000);   // a dismissed notice comes back after 6 hours
}
let shellAsked = null;
function needNewApp(m) {
  if (!manualCheck && shellAsked === m.version) return;   // ask once per version, not at every check
  shellAsked = m.version;
  if (autoUpdater) { autoUpdater.checkForUpdates().catch(() => {}); if (manualCheck) dialog.showMessageBox(win, { type: 'info', message: `Version ${m.version} needs a newer app`, detail: 'It is being downloaded. You will be asked to restart when it is ready.' }); return; }
  dialog.showMessageBox(win, { type: 'info', buttons: ['Open download page', 'Later'], defaultId: 0, cancelId: 1, message: `Version ${m.version} needs a newer app`, detail: 'This one time, download the new app and replace this one. After that, updates install by themselves again.' })
    .then((r) => { if (r.response === 0) shell.openExternal(RELEASES); });
}
function offerRestart() {
  if (!updReady || !win || win.isDestroyed()) return;
  const v = updReady.version;
  // Preferred: a card inside the window (top right) that stays until accepted or dismissed. Older program versions don't have it: then a dialog.
  if (!manualCheck) {
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
  if (!updReady) return;
  updReady = null; pickContent();
  if (win && !win.isDestroyed()) { appReady = false; win.webContents.executeJavaScript('try{window.audiolabHost&&window.audiolabHost.beforeReload&&window.audiolabHost.beforeReload()}catch(e){}', true).catch(() => {}).then(() => setTimeout(() => { if (win && !win.isDestroyed()) win.reload(); }, 300)); }
}
async function checkUpdates(manual) {
  manualCheck = !!manual;
  if (updBusy) return;
  if (updReady) { if (manual) offerDialog(); return; }
  updBusy = true;
  const say = (message, detail, type) => { if (manual && win && !win.isDestroyed()) dialog.showMessageBox(win, { type: type || 'info', message, detail }); };
  try {
    const m = JSON.parse((await updFetch('desktop/app-version.json')).toString('utf8'));
    if (!m || !m.version || !m.sha256) throw new Error('bad manifest');
    if (cmpV(m.version, liveVer || app.getVersion()) <= 0) { say('AudioLab is up to date.', 'Version ' + (liveVer || app.getVersion())); return; }
    if (m.minShell && cmpV(m.minShell, app.getVersion()) > 0) { needNewApp(m); return; }
    if (upState.reverted && upState.version === m.version) { say(`Version ${m.version} did not start on this computer`, 'AudioLab stays on version ' + (liveVer || app.getVersion()) + ' until a newer one is published.', 'warning'); return; }
    const data = await updFetch('index.html');
    const sha = require('crypto').createHash('sha256').update(data).digest('hex');
    if (sha !== m.sha256) { say('The update is still being published.', 'Try again in a few minutes.'); return; }
    fs.mkdirSync(upDir(), { recursive: true });
    const tmp = upIndex() + '.part'; fs.writeFileSync(tmp, data); fs.renameSync(tmp, upIndex());
    writeMeta({ version: m.version, sha256: sha, at: Date.now() });
    updReady = { version: m.version, notes: m.notes || '' };
    offerRestart();
  } catch (e) {
    say('Could not check for updates.', String(e && e.message || e), 'warning');
  } finally { updBusy = false; manualCheck = false; }
}
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
    execFile(alvolPath(), args, { timeout: 4000 }, (err, stdout) => {
      try { resolve(JSON.parse(String(stdout).trim() || '{}')); } catch (e) { resolve({ error: String(err || e) }); }
    });
  });
}
ipcMain.handle('al:dac-list', () => alvol(['list']));
ipcMain.handle('al:dac-get', (e, uid) => alvol(['get', String(uid || 'default')]));
ipcMain.handle('al:dac-set', (e, uid, v) => alvol(['set', String(uid || 'default'), String(Math.max(0, Math.min(1, +v || 0)))]));
ipcMain.handle('al:check-updates', () => checkUpdates(true));
ipcMain.handle('al:apply-update', () => applyContent());

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
ipcMain.handle('al:tear', (e, d) => {
  const disp = screen.getDisplayNearestPoint(screen.getCursorScreenPoint()).workArea;
  const w = Math.round(disp.width * 0.7), h = Math.round(disp.height * 0.75);
  let x = Number.isFinite(d.x) ? d.x : undefined, y = Number.isFinite(d.y) ? d.y : undefined;
  if (x != null) x = Math.max(disp.x, Math.min(disp.x + disp.width - 200, x));
  if (y != null) y = Math.max(disp.y, Math.min(disp.y + disp.height - 100, y));
  const kw = new BrowserWindow({ width: w, height: h, x, y, minWidth: 700, minHeight: 420, backgroundColor: '#0c0e14', title: (d.name || 'Project') + ' · AudioLab Pro', webPreferences: kidPrefs() });
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
    // Show the current icon in the Dock even if macOS cached an older one from a previous version.
    if (isMac && app.dock) { try { const { nativeImage } = require('electron'); const im = nativeImage.createFromPath(path.join(__dirname, 'dock-icon.png')); if (!im.isEmpty()) app.dock.setIcon(im); } catch (e) { /* ignore */ } }
    createWindow();
    setupUpdater();
    app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
  });

  app.on('window-all-closed', () => { if (!isMac) app.quit(); });
}
