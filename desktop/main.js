// AudioLab Studio desktop wrapper (Electron).
// Loads the web app from a private secure scheme so it is cross-origin isolated
// (SharedArrayBuffer on), grants audio-device / MIDI / file permissions, and adds
// menus, window memory, .audiolab file opening and auto-update.
const { app, BrowserWindow, Menu, protocol, session, shell, dialog, ipcMain, systemPreferences } = require('electron');
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
    fs.writeFileSync(stateFile(), JSON.stringify({ ...b, max: win.isMaximized(), full: win.isFullScreen() }));
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
  win = new BrowserWindow({
    width: st.width || 1500,
    height: st.height || 920,
    x: st.x,
    y: st.y,
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
  win.on('close', saveState);
  win.on('closed', () => { win = null; appReady = false; });

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
    }).then((r) => { if (r.response === 0) autoUpdater.quitAndInstall(); });
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
    createWindow();
    setupUpdater();
    app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
  });

  app.on('window-all-closed', () => { if (!isMac) app.quit(); });
}
