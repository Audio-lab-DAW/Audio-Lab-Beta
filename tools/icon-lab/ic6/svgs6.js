/* Task IC6: every picture the app icon needs, as SVG, after the user's round 4 picks (27 Nov 2026, 23:04 Brussels).
   node tools/icon-lab/ic6/svgs6.js <out dir>  -> <out>/<name>.svg and <out>/manifest.json   (read by ship6.py)

   Size plan (each size drawn for itself, never a shrunk picture):
     1024 to 96 px   J3 in P2 as shipped in v0.270 (round 3's icons3.js, unchanged; 128 and up everything, 96 its bold level)
     64 px and below S1 "Thin field" (round 4), small6.js ringSmall: the W7 crop with thin rings on the pixel grid and
                     J9's field as one hairline pair (two at 40 to 64). The user's pick is S1 for 32 px and below; 40 to 64
                     stay on the small master as in IC4, because J3's own drawing there has the fat rings the user
                     rejected at 32 (round 3). 16 pt and 32 pt at 2x are drawn at 32 and 64 physical px for their point
                     size (a hair heavier), not reused from the 1x of the next size.
   Picker (group "Dipole field"): J3 (default), J3 Chart paper (new), J4, M3 and M5 in P2 and P8 (new), J6, J8 (P2, P8),
   J10 (P2, P8). Small versions 16, 32 and 48 the S1 way (small6.js; M3 and M5 at 48 their big drawing's bold level, which
   is already thin); J4 and J10 keep round 3's own small masters, as shipped. */
'use strict';
const fs = require('fs'), path = require('path');
const A = require('../round3/icons3.js'), A4 = require('../round4/icons4.js'), S = require('./small6.js');
const OUT = process.argv[2] || path.join(__dirname, 'out', 'svg');
fs.mkdirSync(OUT, { recursive: true });
const man = {};
function put(name, svg, px) { fs.writeFileSync(path.join(OUT, name + '.svg'), svg); man[name] = px; }

/* the default: J3 in P2, unchanged */
for (const z of [1024, 512, 256, 128, 96]) put(`j3-full-${z}`, A.svg('J3', 'P2', z, { frame: 'full' }), z);
for (const z of [1024, 512, 256, 128]) put(`j3-mac-${z}`, A.svg('J3', 'P2', z, { frame: 'mac' }), z);
/* S1 for 64 px and below */
for (const z of [16, 20, 24, 32, 40, 48, 64]) put(`s1-full-${z}`, S.ringSmall('P2', z, 'full'), z);
put('s1-mac-16', S.ringSmall('P2', 16, 'mac'), 16);
put('s1-mac-16x2', S.ringSmall('P2', 32, 'mac', { pt: 16 }), 32);
put('s1-mac-32', S.ringSmall('P2', 32, 'mac'), 32);
put('s1-mac-32x2', S.ringSmall('P2', 64, 'mac', { pt: 32 }), 64);

/* the layer for Icon Composer (macOS 26): J3 full bleed, square, no rim (as IC4) */
const TILEPATH = A.TILE;
let layer = A.svg('J3', 'P2', 1024, { frame: 'full' });
layer = layer.split('d="' + TILEPATH + '"').join('d="M0,0H1024V1024H0Z"');
layer = layer.replace(/<path d="M0,0H1024V1024H0Z" fill="none" stroke="[^"]*" stroke-opacity="[^"]*" stroke-width="[^"]*" clip-path="[^"]*"\/>/, '');
if (/fill="none" stroke="#6096FF" stroke-opacity="0.32"/.test(layer)) throw new Error('rim left in the layer');
put('j3-layer-1024', layer, 1024);

/* picker options. big(z, frame) draws the design; small(z) the 16 and 32 px versions */
const r3 = (d, p) => (z, fr) => A.svg(d, p, z, { frame: fr });
const r4 = (d, p) => (z, fr) => A4.svg(d, p, z, { frame: fr });
const J6O = (z) => ({ lens: 0.43, zoom: 1.0, N: [452, 566], spec: z <= 16 ? { nd: 4, ed: 3, rw: 1 } : z <= 32 ? { nd: 7, ed: 4 } : { nd: 13, ed: 7 } });
const J8O = (z) => ({ rulers: z >= 32, zoom: 1.05, N: [520, 500], spec: z <= 16 ? { nd: 4, ed: 3 } : z <= 32 ? { nd: 7, ed: 4 } : { nd: 13, ed: 7 } });
const OPTS = [
  { id: 'dipole-field', d: 'J3', p: 'P2', name: 'Dipole Field', big: r3('J3', 'P2'), small: (z) => S.ringSmall('P2', z, 'full') },
  { id: 'dipole-field-paper', d: 'J3', p: 'P8', name: 'Dipole Field, Chart Paper', big: r3('J3', 'P8'), small: (z) => S.ringSmall('P8', z, 'full'), isNew: 1 },
  { id: 'field-orbits', d: 'J4', p: 'P2', name: 'Field Orbits', big: r3('J4', 'P2') },
  { id: 'field-edge', d: 'M3', p: 'P2', name: 'Field to the Edge', big: r4('M3', 'P2'), small: (z) => S.orbitSmall('M3', 'P2', z, 'full'), isNew: 1 },
  { id: 'field-edge-paper', d: 'M3', p: 'P8', name: 'Field to the Edge, Chart Paper', big: r4('M3', 'P8'), small: (z) => S.orbitSmall('M3', 'P8', z, 'full'), isNew: 1 },
  { id: 'field-depth', d: 'M5', p: 'P2', name: 'Field Depth', big: r4('M5', 'P2'), small: (z) => S.orbitSmall('M5', 'P2', z, 'full'), isNew: 1 },
  { id: 'field-depth-paper', d: 'M5', p: 'P8', name: 'Field Depth, Chart Paper', big: r4('M5', 'P8'), small: (z) => S.orbitSmall('M5', 'P8', z, 'full'), isNew: 1 },
  { id: 'porthole-field', d: 'J6', p: 'P2', name: 'Porthole Field', big: r3('J6', 'P2'), small: (z) => S.ringSmall('P2', z, 'full', J6O(z)) },
  { id: 'measured-field', d: 'J8', p: 'P2', name: 'Measured Field', big: r3('J8', 'P2'), small: (z) => S.ringSmall('P2', z, 'full', J8O(z)) },
  { id: 'measured-field-paper', d: 'J8', p: 'P8', name: 'Measured Field, Chart Paper', big: r3('J8', 'P8'), small: (z) => S.ringSmall('P8', z, 'full', J8O(z)) },
  { id: 'field-dial', d: 'J10', p: 'P2', name: 'Field Dial', big: r3('J10', 'P2') },
  { id: 'field-dial-paper', d: 'J10', p: 'P8', name: 'Field Dial, Chart Paper', big: r3('J10', 'P8') }
];
for (const o of OPTS) {
  put(`opt-${o.id}-512`, o.big(512, 'mac'), 512);
  put(`opt-${o.id}-thumb`, o.big(128, 'full'), 128);
  /* J4 and J10 have no small function: round 3's own small masters at every small size, as shipped in IC4 */
  for (const z of [16, 32, 48]) put(`opt-${o.id}-s${z}`, o.small && !(z === 48 && o.d[0] === 'M') ? o.small(z) : o.big(z, 'full'), z);
}
man.__options = OPTS.map((o) => ({ id: o.id, design: o.d, palette: o.p, name: o.name, isNew: !!o.isNew }));
fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(man, null, 1));
console.log(Object.keys(man).length - 1, 'pictures in', OUT);
