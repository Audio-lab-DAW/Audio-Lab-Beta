/* Renders round 5c to PNG with rsvg-convert.  node render5c.js [id|small|sheets]
     renders/<id>/<id>-<P>-{1024,512,128,64}.png, -mac-1024.png, -dock-dark.png, -dock-light.png, -styles.png   (E1..E8)
     renders/small/<id>-<P>-{16,20,24,32,48}.png, -32-at16.png (16 pt at 2x), -64-at32.png (32 pt at 2x), -mac-{16,32}.png   (ES1..ES4)
     renders/sheet-big-<P>.png, renders/sheet-small-<P>.png */
'use strict';
const A = require('./icons5c.js'), S = require('./small5c.js'), fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const OUT = path.join(__dirname, 'renders'), TMP = path.join(require('os').tmpdir(), 'al5c.svg');
function png(svgStr, file, w) { fs.writeFileSync(TMP, svgStr); const a = [TMP, '-o', file]; if (w) a.unshift('-w', String(w), '-h', String(w)); execFileSync('rsvg-convert', a); }
const only = process.argv[2], PS = ['P2', 'P8'];
for (const D of A.DESIGNS) {
  if (only && D.id !== only) continue;
  const dir = path.join(OUT, D.id); fs.mkdirSync(dir, { recursive: true });
  for (const P of PS) {
    for (const z of [1024, 512, 128, 64]) png(A.svg(D.id, P, z, { frame: 'full' }), path.join(dir, `${D.id}-${P}-${z}.png`), z);
    png(A.svg(D.id, P, 1024, { frame: 'mac' }), path.join(dir, `${D.id}-${P}-mac-1024.png`), 1024);
    png(A.dock((z) => A.svg(D.id, P, z, { frame: 'mac' }), 'dark'), path.join(dir, `${D.id}-${P}-dock-dark.png`));
    png(A.dock((z) => A.svg(D.id, P, z, { frame: 'mac' }), 'light'), path.join(dir, `${D.id}-${P}-dock-light.png`));
    png(A.styles((z, st) => A.svg(D.id, P, z, { frame: 'mac', style: st }), P), path.join(dir, `${D.id}-${P}-styles.png`));
  }
  console.log(D.id);
}
if (!only || only === 'small') {
  const dir = path.join(OUT, 'small'); fs.mkdirSync(dir, { recursive: true });
  for (const sid of S.IDS) for (const P of PS) {
    for (const z of [16, 20, 24, 32, 48]) png(S.smallSvg(sid, P, z, 'full'), path.join(dir, `${sid}-${P}-${z}.png`));
    png(S.smallSvg(sid, P, 32, 'full', { pt: 16 }), path.join(dir, `${sid}-${P}-32-at16.png`));
    png(S.smallSvg(sid, P, 64, 'full', { pt: 32 }), path.join(dir, `${sid}-${P}-64-at32.png`));
    for (const z of [16, 32]) png(S.smallSvg(sid, P, z, 'mac'), path.join(dir, `${sid}-${P}-mac-${z}.png`));
  }
  console.log('small');
}
if (!only || only === 'sheets') for (const P of PS) {
  execFileSync('node', [path.join(__dirname, 'sheet5c.js'), path.join(OUT, `sheet-big-${P}.png`), P]);
  execFileSync('python3', [path.join(__dirname, 'sheet_small5c.py'), path.join(OUT, `sheet-small-${P}.png`), P]);
}
