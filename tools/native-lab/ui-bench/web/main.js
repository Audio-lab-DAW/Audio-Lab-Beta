// AudioLab UI bench (task RN4): runs bench.html in Electron and writes the result.
// Usage: electron main.js <out.json> [seconds]
const { app, BrowserWindow } = require('electron');
const fs = require('fs'), path = require('path');
const [outFile, secs] = process.argv.slice(2).filter(a => !a.startsWith('--') && !a.endsWith('main.js') && a !== '.');
app.whenReady().then(async () => {
  const win = new BrowserWindow({ x: 40, y: 40, width: 1600, height: 1000, show: true, backgroundColor: '#111111',
    webPreferences: { backgroundThrottling: false } });
  await win.loadFile(path.join(__dirname, 'bench.html'));
  let res;
  try { res = await win.webContents.executeJavaScript(`runBench(${Number(secs) || 10})`, true); }
  catch (e) { res = { error: String(e) }; }
  res.electron = process.versions.electron; res.chrome = process.versions.chrome;
  try { res.gpu = await app.getGPUInfo('basic'); } catch (e) { res.gpu = String(e); }
  try { res.gpuFeatures = app.getGPUFeatureStatus(); } catch (e) {}
  fs.writeFileSync(outFile || 'web.json', JSON.stringify(res, null, 2));
  app.exit(0);
});
