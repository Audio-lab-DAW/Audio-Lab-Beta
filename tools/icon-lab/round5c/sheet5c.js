/* quick look sheet: node sheet5c.js out.png [P2|P8] [ids...] -> each design at 320 and its 64 px level (shown at 128) */
'use strict';
const A = require('./icons5c.js'), fs = require('fs'), os = require('os'), path = require('path'), { execFileSync } = require('child_process');
const out = process.argv[2], P = process.argv[3] || 'P2', ids = process.argv.slice(4).length ? process.argv.slice(4) : A.DESIGNS.map((d) => d.id);
const SZ = 320, G = 14, cols = 4, cw = SZ + G;
const rows = Math.ceil(ids.length / cols);
let s = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${cols * cw + G}" height="${rows * (SZ + 128 + 40) + G}"><rect width="100%" height="100%" fill="#2B2D35"/>`;
ids.forEach((id, i) => { const x = G + (i % cols) * cw, y = G + Math.floor(i / cols) * (SZ + 128 + 40);
  s += A.svg(id, P, 512, { frame: 'full' }).replace(/^<svg[^>]*>/, `<svg x="${x}" y="${y}" width="${SZ}" height="${SZ}" viewBox="0 0 1024 1024">`);
  s += A.svg(id, P, 64, { frame: 'full' }).replace(/^<svg[^>]*>/, `<svg x="${x}" y="${y + SZ + 8}" width="128" height="128" viewBox="0 0 1024 1024">`);
  s += `<text x="${x + 140}" y="${y + SZ + 30}" font-family="Helvetica" font-size="16" fill="#DDE">${id} ${P}</text>`; });
const tmp = path.join(os.tmpdir(), 'al5c-sheet.svg'); fs.writeFileSync(tmp, s + '</svg>'); execFileSync('rsvg-convert', [tmp, '-o', out]);
