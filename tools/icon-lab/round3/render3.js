/* Renders round-3 icons and mock-ups to PNG with rsvg-convert.
   node render3.js [Jn]  -> renders/Jn/ for P2 and P8:
     Jn-Pp-{1024,512,128,64,32,16}.png (full tile), Jn-Pp-mac-1024.png (Apple grid), Jn-Pp-dock-dark.png,
     Jn-Pp-dock-light.png, Jn-Pp-styles.png (macOS 26 styles; for P8 with the Dark proposal P8N),
     Jn-Pp-taskbar-dark.png (150 %), Jn-Pp-taskbar-light.png (100 %)
   and renders/sheet-all.png (every design in P2 and P8 at 1024 and the small masters), renders/small-check.png */
const A = require('./icons3.js'), fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const OUT = path.join(__dirname, 'renders'), TMP = path.join(require('os').tmpdir(), 'al3.svg');
function png(svgStr, file, w) { fs.writeFileSync(TMP, svgStr); const a = [TMP, '-o', file]; if (w) a.unshift('-w', String(w), '-h', String(w)); execFileSync('rsvg-convert', a); }
const only = process.argv[2], PS = ['P2', 'P8'];
const quick = process.argv.includes('--quick');
for (const D of A.DESIGNS) {
  if (only && only !== '--quick' && D.id !== only) continue;
  const dir = path.join(OUT, D.id); fs.mkdirSync(dir, { recursive: true });
  for (const P of PS) {
    for (const z of [1024, 512, 128, 64, 32, 16]) png(A.svg(D.id, P, z, { frame: 'full' }), path.join(dir, `${D.id}-${P}-${z}.png`), z);
    if (quick) continue;
    png(A.svg(D.id, P, 1024, { frame: 'mac' }), path.join(dir, `${D.id}-${P}-mac-1024.png`), 1024);
    png(A.dock(D.id, P, 'dark'), path.join(dir, `${D.id}-${P}-dock-dark.png`));
    png(A.dock(D.id, P, 'light'), path.join(dir, `${D.id}-${P}-dock-light.png`));
    png(A.styles(D.id, P), path.join(dir, `${D.id}-${P}-styles.png`));
    png(A.taskbar(D.id, P, 'dark', 1.5), path.join(dir, `${D.id}-${P}-taskbar-dark.png`));
    png(A.taskbar(D.id, P, 'light', 1), path.join(dir, `${D.id}-${P}-taskbar-light.png`));
  }
  console.log(D.id, 'done');
}
/* overview sheet: each design, P2 then P8, at 256 (full detail) and at 64, 32, 16 drawn at their real size and magnified x4 */
if (!only || only === '--quick') {
  const S = 256, G = 14, rows = A.DESIGNS.length, colW = S + 3 * 4 * 32 + 64 + 4 * G;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${2 * colW + G}" height="${rows * (S + 2 * G) + G}"><rect width="100%" height="100%" fill="#2B2D35"/>`;
  A.DESIGNS.forEach((d, r) => PS.forEach((p, c) => {
    const x = G + c * colW, y = G + r * (S + 2 * G);
    s += A.svg(d.id, p, 256, { frame: 'full' }).replace(/^<svg[^>]*>/, `<svg x="${x}" y="${y}" width="${S}" height="${S}" viewBox="0 0 1024 1024">`);
    let xx = x + S + G;
    for (const z of [64, 32, 16]) { const w = z === 64 ? 128 : z * 4; s += A.svg(d.id, p, z, { frame: 'full' }).replace(/^<svg[^>]*>/, `<svg x="${xx}" y="${y}" width="${w}" height="${w}" viewBox="0 0 1024 1024">`); xx += w + G; }
    s += `<text x="${x}" y="${y + S + 12}" font-family="Helvetica" font-size="12" fill="#CCD">${d.id} ${p} ${d.name}</text>`;
  }));
  png(s + '</svg>', path.join(OUT, 'sheet-all.png'));
}
