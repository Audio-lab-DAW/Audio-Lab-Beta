const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('audiolabDesktop', {
  isDesktop: true,
  platform: process.platform,
  version: () => ipcRenderer.invoke('al:version'),
  checkForUpdates: () => ipcRenderer.invoke('al:check-updates'),
  applyUpdate: () => ipcRenderer.invoke('al:apply-update'),
  programVersion: () => ipcRenderer.invoke('al:program-version'),
  // v0.172: the page shows its own update window and asks for plain results (no system dialogs)
  updateCheck: (o) => ipcRenderer.invoke('al:update-check', o || {}),
  updateStatus: () => ipcRenderer.invoke('al:update-status'),
  updateApp: () => ipcRenderer.invoke('al:update-app'),
  // torn-off projects in their own windows
  isFullScreen: () => ipcRenderer.invoke('al:is-fullscreen'),
  displayHz: () => ipcRenderer.invoke('al:display-hz'),
  tear: (d) => ipcRenderer.invoke('al:tear', d),
  childData: () => ipcRenderer.invoke('al:child-data'),
  dock: (d) => ipcRenderer.invoke('al:dock', d),
  toMain: (m) => ipcRenderer.send('al:to-main', m),
  onDock: (cb) => ipcRenderer.on('al:dock', (e, d) => cb(d)),
  onFromChild: (cb) => ipcRenderer.on('al:from-child', (e, m) => cb(m)),
  onDockHover: (cb) => ipcRenderer.on('al:dock-hover', (e, h) => cb(h)),
  // v0.203: the app icon picker in Settings (Ocean Yellow by default)
  listAppIcons: () => ipcRenderer.invoke('al:app-icons'),
  setAppIcon: (id) => ipcRenderer.invoke('al:set-app-icon', id),
  // task Z2: AI voices (desktop/voice-ai.js); the page checks for this object and asks for a new app when it is missing
  voiceAI: {
    status: () => ipcRenderer.invoke('al:vai-status'),
    download: () => ipcRenderer.invoke('al:vai-download'),
    embed: (x, ep, sh) => ipcRenderer.invoke('al:vai-embed', x, ep, sh),
    convert: (m) => ipcRenderer.invoke('al:vai-convert', m),
    voices: () => ipcRenderer.invoke('al:vai-voices'),
    saveVoice: (v) => ipcRenderer.invoke('al:vai-voice-save', v),
    getVoice: (id) => ipcRenderer.invoke('al:vai-voice-get', id),
    setVoice: (id, p) => ipcRenderer.invoke('al:vai-voice-set', id, p),
    delVoice: (id) => ipcRenderer.invoke('al:vai-voice-del', id),
    free: () => ipcRenderer.invoke('al:vai-free'),
    onProgress: (cb) => { const f = (e, d) => cb(d); ipcRenderer.on('al:vai-progress', f); return () => ipcRenderer.removeListener('al:vai-progress', f); }
  },
  dac: process.platform === 'darwin' ? {
    list: () => ipcRenderer.invoke('al:dac-list'),
    get: (uid) => ipcRenderer.invoke('al:dac-get', uid),
    set: (uid, v) => ipcRenderer.invoke('al:dac-set', uid, v),
    info: () => ipcRenderer.invoke('al:dac-info'),
    rate: (uid, hz) => ipcRenderer.invoke('al:dac-rate', uid, hz)
  } : null
});
