const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('audiolabDesktop', {
  isDesktop: true,
  platform: process.platform,
  version: () => ipcRenderer.invoke('al:version'),
  checkForUpdates: () => ipcRenderer.invoke('al:check-updates'),
  dac: process.platform === 'darwin' ? {
    list: () => ipcRenderer.invoke('al:dac-list'),
    get: (uid) => ipcRenderer.invoke('al:dac-get', uid),
    set: (uid, v) => ipcRenderer.invoke('al:dac-set', uid, v)
  } : null
});
