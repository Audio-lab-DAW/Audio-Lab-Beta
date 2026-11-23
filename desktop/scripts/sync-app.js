// Copies the web app (../index.html) into desktop/app/. The browser-only
// service-worker bootstrap is left in; it does nothing here because the app is already isolated.
const fs = require('fs'), path = require('path');
const src = path.join(__dirname, '..', '..', 'index.html');
const dstDir = path.join(__dirname, '..', 'app');
let html = fs.readFileSync(src, 'utf8');
const m = html.match(/const VERSION='([\d.]+)'/);
if (m) {
  const pj = path.join(__dirname, '..', 'package.json');
  const j = JSON.parse(fs.readFileSync(pj, 'utf8'));
  const v = m[1].split('.').concat(['0']).slice(0, 3).join('.');
  if (j.version !== v) { j.version = v; fs.writeFileSync(pj, JSON.stringify(j, null, 2) + '\n'); }
  console.log('AudioLab version', m[1], '-> app version', v);
}
fs.mkdirSync(dstDir, { recursive: true });
fs.writeFileSync(path.join(dstDir, 'index.html'), html);
console.log('Synced index.html (' + (html.length / 1048576).toFixed(2) + ' MB)');
