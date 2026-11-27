// Hands the page's message port to the main process (the page itself has no access to Node).
'use strict';
const { ipcRenderer } = require('electron');
window.addEventListener('message', e => {
  if (e.data === 'tap-port' && e.ports && e.ports[0]) ipcRenderer.postMessage('tap-port', null, [e.ports[0]]);
  else if (e.data && e.data.tapInfo) ipcRenderer.send('tap-info', e.data.tapInfo);
});
