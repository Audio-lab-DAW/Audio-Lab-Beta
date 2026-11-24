// AudioLab Studio desktop wrapper (Electron).
// Loads the web app from a private secure scheme so it is cross-origin isolated
// (SharedArrayBuffer on), grants audio-device / MIDI / file permissions, and adds
// menus, window memory, .audiolab file opening and auto-update.
const { app, BrowserWindow, Menu, protocol, session, shell, dialog, ipcMain, systemPreferences, screen } = require('electron');
const path = require('path');
const fs = require('fs');

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
function registerScheme() {
  const root = path.join(__dirname, 'app');
  protocol.handle(SCHEME, async (req) => {
    try {
      const u = new URL(req.url);
      let p = decodeURIComponent(u.pathname);
      if (p === '/' || p === '') p = '/index.html';
      const file = path.normalize(path.join(root, p));
      if (!file.startsWith(root)) return new Response('Forbidden', { status: 403 });
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
    title: 'AudioLab Studio',
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
      if (ok) { appReady = true; flushPending(); }
      else if (tries < 80) setTimeout(() => waitForApp(tries + 1), 250);
    })
    .catch(() => { if (tries < 80) setTimeout(() => waitForApp(tries + 1), 250); });
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
      label: 'AudioLab Studio',
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
        { label: 'AudioLab Studio on GitHub', click: () => shell.openExternal('https://github.com/Audio-lab-DAW/Audio-Lab-Beta') },
        { label: 'Releases', click: () => shell.openExternal(RELEASES) }
      ]
    }
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(tpl));
}

/* ---------- auto-update ---------- */
let autoUpdater = null;
let manualCheck = false;
function setupUpdater() {
  if (!app.isPackaged) return;
  try { ({ autoUpdater } = require('electron-updater')); } catch (e) { return; }
  autoUpdater.logger = null;
  // Windows: download and install by itself. Mac (unsigned): only tell the user and open the download page.
  autoUpdater.autoDownload = !isMac;
  autoUpdater.autoInstallOnAppQuit = !isMac;
  autoUpdater.on('update-available', (info) => {
    if (isMac) {
      dialog.showMessageBox(win, {
        type: 'info', buttons: ['Open download page', 'Later'], defaultId: 0, cancelId: 1,
        message: `AudioLab Studio ${info.version} is available`,
        detail: 'Download the new .dmg and drag it into Applications to replace this version.'
      }).then((r) => { if (r.response === 0) shell.openExternal(RELEASES); });
    } else if (manualCheck) {
      dialog.showMessageBox(win, { type: 'info', message: `Downloading AudioLab Studio ${info.version}…`, detail: 'You will be asked to restart when it is ready.' });
    }
  });
  autoUpdater.on('update-not-available', () => {
    if (manualCheck) dialog.showMessageBox(win, { type: 'info', message: 'AudioLab Studio is up to date.', detail: 'Version ' + app.getVersion() });
    manualCheck = false;
  });
  autoUpdater.on('update-downloaded', (info) => {
    dialog.showMessageBox(win, {
      type: 'info', buttons: ['Restart and update', 'Later'], defaultId: 0, cancelId: 1,
      message: `AudioLab Studio ${info.version} is ready`,
      detail: 'Save your project first, then restart to finish updating.'
    }).then((r) => { if (r.response === 0) { quitOK = true; autoUpdater.quitAndInstall(); } });
  });
  autoUpdater.on('error', (e) => {
    if (manualCheck) dialog.showMessageBox(win, { type: 'warning', message: 'Could not check for updates.', detail: String(e && e.message || e) });
    manualCheck = false;
  });
  setTimeout(() => checkUpdates(false), 8000);
}
function checkUpdates(manual) {
  manualCheck = !!manual;
  if (!autoUpdater) {
    if (manual) dialog.showMessageBox(win, { type: 'info', message: 'Updates are checked in the installed app only.', detail: 'Version ' + app.getVersion() });
    return;
  }
  autoUpdater.checkForUpdates().catch(() => {});
}
ipcMain.handle('al:version', () => app.getVersion());

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
  const kw = new BrowserWindow({ width: w, height: h, x, y, minWidth: 700, minHeight: 420, backgroundColor: '#0c0e14', title: (d.name || 'Project') + ' · AudioLab Studio', webPreferences: kidPrefs() });
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
