/* magnified sheet of the small masters: node sheet_small5.js out.png P2|P8 */
'use strict';
const S = require('./small5.js'), S6 = require('../ic6/small6.js'), fs = require('fs'), { execFileSync } = require('child_process');
const { PNG } = (() => { try { return require('pngjs'); } catch (e) { return {}; } })();
const out = process.argv[2], P = process.argv[3] || 'P2', T = require('os').tmpdir() + '/al5c-';
const rows = [['S1', (px, o) => S6.ringSmall(P, px, 'full', o)], ['IC6 M5', (px, o) => S6.orbitSmall('M5', P, px, 'full', o)]].concat(S.IDS.map((id) => [id, (px, o) => S.smallSvg(id, P, px, 'full', o)]));
const cells = [[16, null], [32, { pt: 16 }], [32, null], [64, { pt: 32 }]];
let i = 0; const files = [];
for (const [nm, fn] of rows) { const r = []; for (const [px, o] of cells) { const f = T + 'c' + (i++) + '.png'; fs.writeFileSync(T + 'c.svg', fn(px, o)); execFileSync('rsvg-convert', [T + 'c.svg', '-o', f]); r.push(f); } files.push([nm, r]); }
fs.writeFileSync(T + 'cells.json', JSON.stringify(files));
execFileSync('python3', ['-c', `
import json
from PIL import Image, ImageDraw
rows=json.load(open('${T}cells.json'));W=4*(192+16)+120;H=len(rows)*(192+16)+16
im=Image.new('RGB',(W,H),(40,42,50));d=ImageDraw.Draw(im)
for r,(nm,fs) in enumerate(rows):
  y=16+r*208;d.text((8,y+90),nm,fill=(220,220,230))
  for c,f in enumerate(fs):
    t=Image.open(f).convert('RGBA');t=t.resize((192,192),Image.NEAREST);im.paste(t,(120+c*208,y),t)
im.save('${out}')`]);
