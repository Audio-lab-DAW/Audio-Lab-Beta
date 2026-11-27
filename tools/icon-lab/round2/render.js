/* Renders round-2 icons and mock-ups to PNG with rsvg-convert.
   node render.js            -> renders/ (each design in its own best palette and in every palette)
   Output per design Ix: renders/Ix/Ix-Pn-{1024,512,128,64,32,16}.png (best palette, full tile),
   Ix-mac-1024.png (Apple grid), Ix-palettes.png (every palette, 160 px), Ix-dock-dark.png,
   Ix-dock-light.png, Ix-styles.png (macOS 26 styles), Ix-taskbar-dark.png, Ix-taskbar-light.png. */
const A = require('./icons.js'), fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const OUT = path.join(__dirname, 'renders'), TMP = path.join(require('os').tmpdir(), 'al2.svg');
function png(svgStr, file, w) { fs.writeFileSync(TMP, svgStr); const a = [TMP, '-o', file]; if (w) a.unshift('-w', String(w), '-h', String(w)); execFileSync('rsvg-convert', a); }
const only = process.argv[2];
for (const D of A.DESIGNS) {
  if (only && D.id !== only) continue;
  const dir = path.join(OUT, D.id); fs.mkdirSync(dir, { recursive: true });
  const P = D.best;
  for (const z of [1024, 512, 128, 64, 32, 16]) png(A.svg(D.id, P, z, { frame: 'full' }), path.join(dir, `${D.id}-${P}-${z}.png`), z);
  png(A.svg(D.id, P, 1024, { frame: 'mac' }), path.join(dir, `${D.id}-${P}-mac-1024.png`), 1024);
  const S = 160, G = 12, n = A.PALETTES.length;
  let sheet = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${n * (S + G) + G}" height="${S + 2 * G + 22}"><rect width="100%" height="100%" fill="#2B2D35"/>`;
  A.PALETTES.forEach((p, i) => { sheet += A.svg(D.id, p.id, S, { frame: 'full' }).replace(/^<svg[^>]*>/, `<svg x="${G + i * (S + G)}" y="${G}" width="${S}" height="${S}" viewBox="0 0 1024 1024">`); sheet += `<text x="${G + i * (S + G) + S / 2}" y="${S + G + 18}" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-size="13" fill="#CCD">${p.id} ${p.name}</text>`; });
  png(sheet + '</svg>', path.join(dir, `${D.id}-palettes.png`));
  png(A.dock(D.id, P, 'dark'), path.join(dir, `${D.id}-dock-dark.png`));
  png(A.dock(D.id, P, 'light'), path.join(dir, `${D.id}-dock-light.png`));
  png(A.styles(D.id, P), path.join(dir, `${D.id}-styles.png`));
  png(A.taskbar(D.id, P, 'dark', 1.5), path.join(dir, `${D.id}-taskbar-dark.png`));
  png(A.taskbar(D.id, P, 'light', 1), path.join(dir, `${D.id}-taskbar-light.png`));
  console.log(D.id, 'done');
}
/* the palette family as one sheet: every design x every palette at 96 px */
if (!only) {
  const S = 96, G = 8, rows = A.DESIGNS.length, cols = A.PALETTES.length;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${cols * (S + G) + G}" height="${rows * (S + G) + G}"><rect width="100%" height="100%" fill="#2B2D35"/>`;
  A.DESIGNS.forEach((d, r) => A.PALETTES.forEach((p, c) => { s += A.svg(d.id, p.id, 128, { frame: 'full' }).replace(/^<svg[^>]*>/, `<svg x="${G + c * (S + G)}" y="${G + r * (S + G)}" width="${S}" height="${S}" viewBox="0 0 1024 1024">`); }));
  png(s + '</svg>', path.join(OUT, 'family-all.png'));
}
