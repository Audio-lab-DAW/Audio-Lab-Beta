/* Renders round-4 icons and mock-ups to PNG with rsvg-convert.
   node render4.js [id]  ->
     renders/<id>/<id>-<P>-{1024,512,128,64}.png (full tile), <id>-<P>-mac-1024.png (Apple grid),
       <id>-<P>-dock-dark.png, <id>-<P>-dock-light.png, <id>-<P>-styles.png (macOS 26 Default and Dark)   for K1..M5, H1, H2
     renders/small/<S>-<P>-<px>[-at<pt>].png for S1..S4 and IC4: 16, 20, 24, 32, 48 at 1x; 32 (16 pt at 2x), 64 (32 pt at 2x);
       <S>-<P>-mac-<px>.png (Apple grid), <S>-template-<px>-{black,white}.png (menu bar / tray)
     renders/sheet-big.png (every design in P2 and P8 at 256 and 64), renders/sheet-small.png (magnified 6 times) */
'use strict';
const A = require('./icons4.js'), S = require('./small4.js'), fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const OUT = path.join(__dirname, 'renders'), TMP = path.join(require('os').tmpdir(), 'al4.svg');
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
  console.log(D.id, 'done');
}
if (!only || only === 'small') {
  const dir = path.join(OUT, 'small'); fs.mkdirSync(dir, { recursive: true });
  for (const sid of S.IDS.concat(['IC4'])) {
    for (const P of PS) {
      for (const z of [16, 20, 24, 32, 48]) png(S.smallSvg(sid, P, z, 'full'), path.join(dir, `${sid}-${P}-${z}.png`));
      png(S.smallSvg(sid, P, 32, 'full', { pt: 16 }), path.join(dir, `${sid}-${P}-32-at16.png`));
      png(S.smallSvg(sid, P, 64, 'full', { pt: 32 }), path.join(dir, `${sid}-${P}-64-at32.png`));
      for (const z of [16, 32]) png(S.smallSvg(sid, P, z, 'mac'), path.join(dir, `${sid}-${P}-mac-${z}.png`));
    }
    for (const z of [16, 32]) for (const [nm, ink] of [['black', '#000000'], ['white', '#FFFFFF']]) png(S.template(sid, z, ink), path.join(dir, `${sid}-template-${z}-${nm}.png`));
  }
  console.log('small done');
}
if (!only) {
  const G = 14, SZ = 256, colW = SZ + 128 + 3 * G;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${2 * colW + G}" height="${A.DESIGNS.length * (SZ + 2 * G) + G}"><rect width="100%" height="100%" fill="#2B2D35"/>`;
  A.DESIGNS.forEach((d, r) => PS.forEach((p, c) => {
    const x = G + c * colW, y = G + r * (SZ + 2 * G);
    s += A.svg(d.id, p, 256, { frame: 'full' }).replace(/^<svg[^>]*>/, `<svg x="${x}" y="${y}" width="${SZ}" height="${SZ}" viewBox="0 0 1024 1024">`);
    s += A.svg(d.id, p, 64, { frame: 'full' }).replace(/^<svg[^>]*>/, `<svg x="${x + SZ + G}" y="${y}" width="128" height="128" viewBox="0 0 1024 1024">`);
    s += `<text x="${x}" y="${y + SZ + 12}" font-family="Helvetica" font-size="12" fill="#CCD">${d.id} ${p} ${d.name}</text>`;
  }));
  png(s + '</svg>', path.join(OUT, 'sheet-big.png'));
  execFileSync('python3', [path.join(__dirname, 'sheet_small.py')]);
}
