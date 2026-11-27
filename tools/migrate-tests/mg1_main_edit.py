#!/usr/bin/env python3
"""Task MG1: the shell side of the path to the native app, in desktop/main.js and desktop/preload.js.
Anchored edits (each anchor must occur exactly once); refuses a second run."""
import sys, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'desktop')
def edit(fn, pairs):
    p = os.path.join(D, fn); s = open(p, encoding='utf-8').read()
    if 'task MG1' in s: sys.exit(fn + ': already edited (task MG1)')
    for a, b in pairs:
        assert s.count(a) == 1, (fn, a[:80], s.count(a)); s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s); print('edited', fn)

edit('main.js', [
 # tests only: a throw-away application-data folder, so a test on a real computer never touches the user's AudioLab data
 ("try { app.setPath('userData', path.join(app.getPath('appData'), 'AudioLab Studio')); } catch (e) {}\n",
  "if (process.env.AL_TEST_APPDATA) { try { app.setPath('appData', process.env.AL_TEST_APPDATA); } catch (e) {} }   // task MG1: tests only\ntry { app.setPath('userData', path.join(app.getPath('appData'), 'AudioLab Studio')); } catch (e) {}\n"),
 # the module, loaded quietly (a shell without it simply never offers the native app)
 ("let win = null;\n",
  "let win = null;\n/* task MG1: the path to the native AudioLab (desktop/native-migrate.js): the manifest's optional \"native\" block, the centred window in the page\n   (mg* in index.html), the export of projects and settings, the download, the check and the install. Missing module: nothing is offered. */\nlet NM = null;\ntry { NM = require('./native-migrate'); } catch (e) { try { NM = require('./app/native-migrate.js'); } catch (e2) { NM = null; } }   // app/: the copy sync-app.js puts there, so a build made before package.json lists the module still has it\n"),
 # every manifest read: the native block
 ("    if (!m || !m.version || !m.sha256) throw new Error('bad manifest');\n  } catch (e) {",
  "    if (!m || !m.version || !m.sha256) throw new Error('bad manifest');\n    try { if (NM) NM.seen(m); } catch (x) { /* task MG1: a bad native block never stops the program's own update */ }\n  } catch (e) {"),
 # the menu: Install the native AudioLab (only while one is offered)
 ("        { label: 'Check for Updates…', click: () => checkUpdates(true) },\n        { type: 'separator' },\n        { role: 'services' },",
  "        { label: 'Check for Updates…', click: () => checkUpdates(true) },\n        ...mgMenu(),\n        { type: 'separator' },\n        { role: 'services' },"),
 ("        ...(!isMac ? [{ label: 'Check for Updates…', click: () => checkUpdates(true) }] : []),",
  "        ...(!isMac ? [{ label: 'Check for Updates…', click: () => checkUpdates(true) }, ...mgMenu()] : []),"),
 ("function buildMenu() {",
  "// task MG1: \"Install the native AudioLab…\" opens the page's centred window; once installed, \"Open the native AudioLab\"\nfunction mgMenu() {\n  let st = null; try { st = NM && NM.status(); } catch (e) { st = null; }\n  if (!st || !st.offer) return [];\n  if (st.installed && cmpV(st.installed.version, st.offer.version) >= 0) return [{ label: 'Open the native AudioLab', click: () => runInApp(\"window.audiolabHost&&window.audiolabHost.mgOpen&&window.audiolabHost.mgOpen(true)\") }];\n  return [{ label: 'Install the native AudioLab…', click: () => runInApp(\"window.audiolabHost&&window.audiolabHost.mgOpen&&window.audiolabHost.mgOpen(true)\") }];\n}\nfunction buildMenu() {"),
 # the status the page's update window reads
 ("ipcMain.handle('al:update-status', () => Object.assign({}, updLast, { installed: liveVer || app.getVersion(), app: app.getVersion(), ready: updReady ? updReady.version : null, platform: process.platform }));",
  "ipcMain.handle('al:update-status', () => { let nat = null; try { nat = NM ? NM.status().offer : null; } catch (e) { nat = null; } return Object.assign({}, updLast, { installed: liveVer || app.getVersion(), app: app.getVersion(), ready: updReady ? updReady.version : null, platform: process.platform, native: nat }); });   // task MG1: native = the native build offered here, or null"),
 # set up with the window, the quit and the torn-off windows
 ("    try { require('./native-engine').setup({ ipcMain, app }); } catch (e) { console.warn('native engine', e); }  // task NB-N2b: idle until the page asks (desktop/native-engine.js)\n",
  "    try { require('./native-engine').setup({ ipcMain, app }); } catch (e) { console.warn('native engine', e); }  // task NB-N2b: idle until the page asks (desktop/native-engine.js)\n    try { if (NM) NM.setup({ app, ipcMain, shell, getWin: () => win, dockAll, rebuildMenu: buildMenu, quitNow: () => { quitOK = true; quitting = true; app.quit(); } }); } catch (e) { console.warn('native migrate', e); }  // task MG1\n"),
])
edit('preload.js', [
 ("  metrics: () => ipcRenderer.invoke('al:metrics'),\n",
  "  metrics: () => ipcRenderer.invoke('al:metrics'),\n"
  "  // task MG1: the path to the native AudioLab (desktop/native-migrate.js). status(): { offer, due, laterAt, installed, busy, migrateDir };\n"
  "  // export*: the page writes every project and setting into the folder the native app reads; install() downloads and checks; finish() installs and opens it.\n"
  "  nativeMigrate: {\n"
  "    status: () => ipcRenderer.invoke('al:mg-status'),\n"
  "    later: () => ipcRenderer.invoke('al:mg-later'),\n"
  "    prepare: () => ipcRenderer.invoke('al:mg-prepare'),\n"
  "    exportBegin: (o) => ipcRenderer.invoke('al:mg-export-begin', o || {}),\n"
  "    exportFile: (rel, data, kind) => ipcRenderer.invoke('al:mg-export-file', String(rel), data, String(kind || '')),\n"
  "    exportEnd: (m) => ipcRenderer.invoke('al:mg-export-end', m || {}),\n"
  "    install: () => ipcRenderer.invoke('al:mg-install'),\n"
  "    finish: () => ipcRenderer.invoke('al:mg-finish'),\n"
  "    cancel: () => ipcRenderer.invoke('al:mg-cancel'),\n"
  "    open: () => ipcRenderer.invoke('al:mg-open'),\n"
  "    reveal: (what) => ipcRenderer.invoke('al:mg-reveal', String(what || '')),\n"
  "    on: (cb) => { const f = (e, d) => cb(d); ipcRenderer.on('al:mg-ev', f); return () => ipcRenderer.removeListener('al:mg-ev', f); }\n"
  "  },\n"),
])
