const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('audiolabDesktop', {
  isDesktop: true,
  platform: process.platform,
  version: () => ipcRenderer.invoke('al:version'),
  checkForUpdates: () => ipcRenderer.invoke('al:check-updates'),
  programVersion: () => ipcRenderer.invoke('al:program-version'),
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
  dac: process.platform === 'darwin' ? {
    list: () => ipcRenderer.invoke('al:dac-list'),
    get: (uid) => ipcRenderer.invoke('al:dac-get', uid),
    set: (uid, v) => ipcRenderer.invoke('al:dac-set', uid, v)
  } : null
});
