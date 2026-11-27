/* Task IC4: every picture the shipped app icon needs, as SVG, from the round 3 drawing code and the IC4 small master.
   node tools/icon-lab/ic4/svgs.js <out dir>  -> <out>/<name>.svg and <out>/manifest.json
   Read by ship.py, which renders them and writes the app's files.

   Size plan (each size drawn for itself, never a shrunk picture):
     1024 to 128 px   J3 (round 3: the tilted dipole field round the yellow nucleus, the thinner W7 rings at 90 %)
     96 px            J3 at its bold level (three field lines, W7M rings)
     64 px and below  the IC4 small master (small.js): the zoomed, tilted W7 crop with thin rings on the pixel grid
   Picker options: J4, J6, J8, J10 in P2 (Orbit night), J8 and J10 also in P8 (Chart paper), each with small versions. */
'use strict';
const fs = require('fs'), path = require('path');
const A = require('../round3/icons3.js'), S = require('./small.js');
const OUT = process.argv[2] || path.join(__dirname, 'out', 'svg');
fs.mkdirSync(OUT, { recursive: true });
const man = {};
function put(name, svg, px) { fs.writeFileSync(path.join(OUT, name + '.svg'), svg); man[name] = px; }

/* the default: J3 in P2 */
for (const z of [1024, 512, 256, 128, 96]) put(`j3-full-${z}`, A.svg('J3', 'P2', z, { frame: 'full' }), z);
for (const z of [1024, 512, 256, 128]) put(`j3-mac-${z}`, A.svg('J3', 'P2', z, { frame: 'mac' }), z);
for (const z of [16, 20, 24, 32, 40, 48, 64]) put(`j3s-full-${z}`, S.smallSvg('P2', z, 'full'), z);
for (const z of [16, 32, 64]) put(`j3s-mac-${z}`, S.smallSvg('P2', z, 'mac'), z);

/* the layer for Icon Composer (macOS 26): J3 full bleed, square (macOS cuts its own squircle and draws its own edge),
   no rim. make_icon.py takes the fill colour out of it. */
const TILEPATH = A.TILE;
let layer = A.svg('J3', 'P2', 1024, { frame: 'full' });
layer = layer.split('d="' + TILEPATH + '"').join('d="M0,0H1024V1024H0Z"');
layer = layer.replace(/<path d="M0,0H1024V1024H0Z" fill="none" stroke="[^"]*" stroke-opacity="[^"]*" stroke-width="[^"]*" clip-path="[^"]*"\/>/, '');
if (/fill="none" stroke="#6096FF" stroke-opacity="0.32"/.test(layer)) throw new Error('rim left in the layer');
put('j3-layer-1024', layer, 1024);

/* picker options */
const OPTS = [
  { id: 'dipole-field', d: 'J3', p: 'P2', name: 'Dipole Field', small: (z, fr) => S.smallSvg('P2', z, fr) },
  { id: 'field-orbits', d: 'J4', p: 'P2', name: 'Field Orbits' },
  { id: 'porthole-field', d: 'J6', p: 'P2', name: 'Porthole Field', small: (z, fr) => S.smallSvg('P2', z, fr, { lens: 0.43, zoom: 1.0, N: [452, 566], spec: z <= 16 ? { nd: 4, ed: 3, rw: 1 } : z <= 32 ? { nd: 7, ed: 4, fw: 0 } : { nd: 13, ed: 7 } }) },
  { id: 'measured-field', d: 'J8', p: 'P2', name: 'Measured Field', small: (z, fr) => S.smallSvg('P2', z, fr, { rulers: z >= 32, zoom: 1.05, N: [520, 500], spec: z <= 16 ? { nd: 4, ed: 3 } : z <= 32 ? { nd: 7, ed: 4 } : { nd: 13, ed: 7 } }) },
  { id: 'measured-field-paper', d: 'J8', p: 'P8', name: 'Measured Field, Chart Paper', small: (z, fr) => S.smallSvg('P8', z, fr, { rulers: z >= 32, zoom: 1.05, N: [520, 500], spec: z <= 16 ? { nd: 4, ed: 3 } : z <= 32 ? { nd: 7, ed: 4 } : { nd: 13, ed: 7 } }) },
  { id: 'field-dial', d: 'J10', p: 'P2', name: 'Field Dial' },
  { id: 'field-dial-paper', d: 'J10', p: 'P8', name: 'Field Dial, Chart Paper' }
];
for (const o of OPTS) {
  put(`opt-${o.id}-512`, A.svg(o.d, o.p, 512, { frame: 'mac' }), 512);
  put(`opt-${o.id}-thumb`, A.svg(o.d, o.p, 128, { frame: 'full' }), 128);
  /* small versions, edge to edge (Windows window, taskbar and shortcut icons): J4 and J10 keep round 3's own small masters
     (nucleus, lobes and dot read cleanly), the ring designs get the thin-ring treatment of the IC4 small master */
  for (const z of [16, 32, 48]) put(`opt-${o.id}-s${z}`, o.small ? o.small(z, 'full') : A.svg(o.d, o.p, z, { frame: 'full' }), z);
}
man.__options = OPTS.map((o) => ({ id: o.id, design: o.d, palette: o.p, name: o.name }));
fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(man, null, 1));
console.log(Object.keys(man).length - 1, 'pictures in', OUT);
