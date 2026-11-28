/* quick look sheet: node sheet5.js out.png [P2|P8] [ids...] -> every design at 320 and 64 (shown at 128) */
'use strict';
const A = require('./icons5.js'), fs = require('fs'), { execFileSync } = require('child_process');
const out = process.argv[2], P = process.argv[3] || 'P2', ids = process.argv.slice(4).length ? process.argv.slice(4) : A.DESIGNS.map((d) => d.id);
const SZ = 320, G = 14, cols = 7, cw = SZ + G, rows = Math.ceil(ids.length / cols);
let s = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${cols * cw + G}" height="${rows * (SZ + 128 + 40) + G}"><rect width="100%" height="100%" fill="#2B2D35"/>`;
ids.forEach((id, i) => { const x = G + (i % cols) * cw, y = G + Math.floor(i / cols) * (SZ + 128 + 40);
  s += A.svg(id, P, 512, { frame: 'full' }).replace(/^<svg[^>]*>/, `<svg x="${x}" y="${y}" width="${SZ}" height="${SZ}" viewBox="0 0 1024 1024">`);
  s += A.svg(id, P, 64, { frame: 'full' }).replace(/^<svg[^>]*>/, `<svg x="${x}" y="${y + SZ + 8}" width="128" height="128" viewBox="0 0 1024 1024">`);
  s += `<text x="${x + 140}" y="${y + SZ + 30}" font-family="Helvetica" font-size="16" fill="#DDE">${id} ${P}</text>`; });
fs.writeFileSync(require('os').tmpdir() + '/al5s.svg', s + '</svg>'); execFileSync('rsvg-convert', [require('os').tmpdir() + '/al5s.svg', '-o', out]);
