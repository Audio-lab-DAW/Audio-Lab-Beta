/* Renders task IC9's small masters and the references to PNG with rsvg-convert, and writes renders/manifest.json.
     node render5s.js
   renders/small/<id>-<P>-<pt>@<s>x.png (full tile) and -mac.png (Apple grid), pt 16 20 24 32, s 1 2
   renders/ref/   S1 (shipped, ic6/small6.js) and round 5's MS2 at the same sizes; M5c, M5d at 512, 128, 64
   renders/ba/    the before and after: M5c's big drawing simply scaled to 16 and 32, next to MC1 drawn for them
   renders/sheet-<P>.png  every master magnified 8x, for checking */
'use strict';
const S = require('./small5s.js'), A = require('../round5/icons5.js'), S5 = require('../round5/small5.js'), S6 = require('../ic6/small6.js');
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const OUT = path.join(__dirname, 'renders'), TMP = path.join(require('os').tmpdir(), 'al5s.svg');
function png(svg, file, w) { fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(TMP, svg); const a = [TMP, '-o', file]; if (w) a.unshift('-w', String(w), '-h', String(w)); execFileSync('rsvg-convert', a); return path.relative(OUT, file); }
const PS = ['P2', 'P8'], man = { small: {}, ref: {}, big: {}, ba: {}, tpl: {} };
for (const id of S.IDS) for (const P of PS) for (const pt of S.PTS) for (const s of [1, 2]) for (const fr of ['full', 'mac']) {
  man.small[`${id}-${P}-${pt}@${s}x${fr === 'mac' ? '-mac' : ''}`] = png(S.smallSvg(id, P, pt, s, fr), path.join(OUT, 'small', `${id}-${P}-${pt}@${s}x${fr === 'mac' ? '-mac' : ''}.png`));
}
/* references: S1 as shipped and round 5's MS2 (2x as they define it: o.pt) */
for (const P of PS) for (const pt of S.PTS) for (const s of [1, 2]) for (const fr of ['full', 'mac']) {
  const o = s === 2 ? { pt } : undefined, sfx = `${P}-${pt}@${s}x${fr === 'mac' ? '-mac' : ''}`;
  man.ref['S1-' + sfx] = png(S6.ringSmall(P, pt * s, fr, o), path.join(OUT, 'ref', `S1-${sfx}.png`));
  man.ref['MS2-' + sfx] = png(S5.smallSvg('MS2', P, pt * s, fr, o), path.join(OUT, 'ref', `MS2-${sfx}.png`));
}
for (const d of ['M5c', 'M5d']) for (const P of PS) {
  for (const z of [512, 128, 64]) man.big[`${d}-${P}-${z}`] = png(A.svg(d, P, z, { frame: 'full' }), path.join(OUT, 'big', `${d}-${P}-${z}.png`), z);
  man.big[`${d}-${P}-mac-128`] = png(A.svg(d, P, 128, { frame: 'mac' }), path.join(OUT, 'big', `${d}-${P}-mac-128.png`), 128);
}
/* before and after: the full-detail 1024 drawing simply scaled down (what an automatic resize does) */
for (const z of [16, 32]) man.ba[`M5c-scaled-${z}`] = png(A.svg('M5c', 'P2', 1024, { frame: 'full' }), path.join(OUT, 'ba', `M5c-scaled-${z}.png`), z);
for (const s of [1, 2]) man.tpl[`tpl-16@${s}x`] = png(S.templateSvg(16, s), path.join(OUT, 'tpl', `tpl-16@${s}x.png`));
fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(man, null, 1));

/* magnified check sheet per palette: rows = designs, columns = 16 20 24 32 @1x, then 16 20 24 32 @2x */
for (const P of PS) {
  const rows = [['S1', 'ref', 'S1'], ['MS2 r5', 'ref', 'MS2']].concat(S.IDS.map((id) => [id, 'small', id]));
  const cells = rows.map(([nm, kind, id]) => [nm, [1, 2].flatMap((s) => S.PTS.map((pt) => path.join(OUT, kind === 'ref' ? man.ref[`${id}-${P}-${pt}@${s}x`] : man.small[`${id}-${P}-${pt}@${s}x`])))]);
  fs.writeFileSync(TMP + '.json', JSON.stringify(cells));
  execFileSync('python3', ['-c', `
import json
from PIL import Image, ImageDraw
rows=json.load(open('${TMP}.json'));Z=4;W=90+sum(((16,20,24,32,32,40,48,64)[i]*Z if i<4 else (16,20,24,32,32,40,48,64)[i]*Z//2)+12 for i in range(8));H=len(rows)*(32*Z+14)+10
im=Image.new('RGB',(W,H),(40,42,50));d=ImageDraw.Draw(im)
for r,(nm,fs) in enumerate(rows):
  y=10+r*(32*Z+14);d.text((6,y+60),nm,fill=(220,220,230));x=90
  for i,f in enumerate(fs):
    t=Image.open(f).convert('RGBA');z=Z if i<4 else Z//2;t=t.resize((t.width*z,t.height*z),Image.NEAREST);im.paste(t,(x,y),t);x+=t.width+12
im.save('${path.join(OUT, 'sheet-' + P + '.png')}')`]);
}
console.log('ok', Object.keys(man.small).length, 'small masters');
