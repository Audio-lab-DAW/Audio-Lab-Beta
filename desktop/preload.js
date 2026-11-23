const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('audiolabDesktop', {
  isDesktop: true,
  platform: process.platform,
  version: () => ipcRenderer.invoke('al:version'),
  checkForUpdates: () => ipcRenderer.invoke('al:check-updates')
});
