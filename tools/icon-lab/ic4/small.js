/* AudioLab app icon, task IC4: the small-size master (32 px and below, and the 2x of 16 and 32).
   The W7 composition (the atom zoomed 1.5 times into its top right, tilted 6 degrees, the electron anchored at the
   top right) redrawn for small sizes from its geometry instead of shrinking the 1024 drawing:
     - the three orbits as plain ellipses (rx 540, ry 225 in the 1024 tile, at -36, 24 and 84 degrees) with a stroke
       width given in DEVICE pixels (about 1 px at 16, 1.3 px at 32, 2.2 px at 64), so the rings are thin at every size;
     - the rings at J3's 90 % (each ring on its own, so the crossings show brighter: the transparency the user liked);
     - the nucleus and the electron with whole-pixel diameters, their centres on the pixel grid
       (on a pixel corner for an even diameter, on a pixel centre for an odd one);
     - each ring scaled by a hair so the edge that faces the viewer straight on (the vertical ring's left and right
       sides, the flat rings' tops and bottoms) lands on a pixel centre: those edges are one crisp pixel, not two grey ones;
     - the tile squircle on whole pixels (the Apple grid: a 1, 3 or 6 px margin at 16, 32, 64);
     - one dipole field line pair (J3's field) as a 1 px hairline at 32 and above, centred on the nucleus.
   smallSvg(pid, px, frame, o) -> SVG string with viewBox 0 0 px px. frame 'full' (Windows, favicons) or 'mac'. */
'use strict';
const A = require('../round3/icons3.js');
const SPEC = {
  /* px: ring width, nucleus diameter, electron diameter, electron gap, field line width (0 = none), rim */
  16: { rw: 1.0, nd: 6, ed: 3, eg: 0.9, fw: 0, rim: 0.7, zoom: 1.3 },
  20: { rw: 1.05, nd: 7, ed: 4, eg: 1.0, fw: 0, rim: 0.8, zoom: 1.3 },
  24: { rw: 1.15, nd: 7, ed: 4, eg: 1.0, fw: 0.8, rim: 0.9, zoom: 1.4 },
  32: { rw: 1.3, nd: 9, ed: 5, eg: 1.2, fw: 0.9, rim: 1.0, zoom: 1.4 },
  40: { rw: 1.5, nd: 11, ed: 6, eg: 1.4, fw: 1.0, rim: 1.0, zoom: 1.45 },
  48: { rw: 1.7, nd: 13, ed: 7, eg: 1.6, fw: 1.1, rim: 1.2, zoom: 1.45 },
  64: { rw: 2.3, nd: 18, ed: 10, eg: 2.2, fw: 1.6, rim: 1.4, zoom: 1.4 }
};
function spec(px) { if (SPEC[px]) return SPEC[px]; const ks = Object.keys(SPEC).map(Number); let best = ks[0]; for (const k of ks) if (Math.abs(k - px) < Math.abs(best - px)) best = k; const S = SPEC[best], r = px / best; return { rw: S.rw * Math.sqrt(r), nd: Math.round(S.nd * r), ed: Math.max(2, Math.round(S.ed * r)), eg: S.eg * r, fw: S.fw, rim: S.rim, zoom: S.zoom }; }
const n = (v) => (Math.round(v * 1000) / 1000).toString();
function squircle(x, y, s) { const N = 96, a = s / 2, p = []; for (let i = 0; i < N; i++) { const t = i / N * Math.PI * 2, c = Math.cos(t), si = Math.sin(t); p.push(n(x + a + a * Math.sign(c) * Math.pow(Math.abs(c), 0.4)) + ',' + n(y + a + a * Math.sign(si) * Math.pow(Math.abs(si), 0.4))); } return 'M' + p.join('L') + 'Z'; }
/* the W7 geometry in the 1024 tile: electron anchored at E, nucleus N, orbits rx 540, ry 225 */
const E = [800, 190], ROT = [-36, 24, 84];
/* zoom z: 1.5 is W7 (electron anchored at E); a smaller zoom moves the nucleus toward the tile centre */
function geo(z) { const RX = 360 * z, RY = 150 * z, t = (1.5 - z) / 0.5, W7 = [E[0] - 540 * Math.cos(-36 * Math.PI / 180), E[1] - 540 * Math.sin(-36 * Math.PI / 180)];
  return { RX, RY, N: [W7[0] + (512 - W7[0]) * t, W7[1] + (500 - W7[1]) * t] }; }
const N = geo(1.5).N;
/* half extents of a rotated ellipse along x and y */
function ext(rx, ry, deg) { const a = deg * Math.PI / 180, c = Math.cos(a), s = Math.sin(a); return [Math.sqrt(rx * rx * c * c + ry * ry * s * s), Math.sqrt(rx * rx * s * s + ry * ry * c * c)]; }
/* a dipole field line r = L sin^2(theta) around c, axis tilted, from the surface Rs round to the surface */
function fieldLine(c, Leq, tilt, Rs, side) {
  const a = tilt * Math.PI / 180, t0 = Math.asin(Math.min(1, Math.sqrt(Rs / Leq))), pts = [];
  for (let i = 0; i <= 64; i++) { const th = t0 + (Math.PI - 2 * t0) * i / 64, r = Leq * Math.sin(th) ** 2, x = side * r * Math.sin(th), y = -r * Math.cos(th); pts.push([c[0] + x * Math.cos(a) - y * Math.sin(a), c[1] + x * Math.sin(a) + y * Math.cos(a)]); }
  return 'M' + pts.map((p) => n(p[0]) + ',' + n(p[1])).join('L');
}
let uid = 0;
function smallSvg(pid, px, frame, o) {
  o = o || {}; const P = A.PAL[pid], S = Object.assign({}, spec(px), o.spec || {}), id = 'sm' + (++uid) + '_';
  const z = o.zoom || S.zoom || 1.5, G = geo(z), RX = G.RX, RY = G.RY, N = o.N || G.N;
  const m = frame === 'mac' ? (px <= 16 ? 1 : Math.round(px * 100 / 1024)) : 0, ts = px - 2 * m, k = ts / 1024;
  /* nucleus centre on the grid: a pixel corner for an even diameter, a pixel centre for an odd one */
  const odd = (v) => Math.round(v) % 2 === 1;
  let nx = m + N[0] * k, ny = m + N[1] * k;
  const snap = (v, isOdd) => isOdd ? Math.floor(v) + 0.5 : Math.round(v);
  const dx = snap(nx, odd(S.nd)) - nx, dy = snap(ny, odd(S.nd)) - ny; nx += dx; ny += dy;
  /* the rings: scale each one a hair so its straight-on edges land on pixel centres (odd width) or corners (even) */
  const rwOdd = Math.round(S.rw) % 2 === 1;
  const rings = ROT.map((deg) => {
    const [ex, ey] = ext(RX * k, RY * k, deg), vertical = Math.abs(deg) > 60, e = vertical ? ex : ey, c = vertical ? nx : ny;
    const target = snap(c + e, rwOdd) - c, f = target / e;
    return { deg, rx: RX * k * f, ry: RY * k * f };
  });
  /* the electron on the -36 degree ring at its parameter 0, then put on the grid */
  const r0 = rings[0], a0 = r0.deg * Math.PI / 180;
  let ex = nx + r0.rx * Math.cos(a0), ey = ny + r0.rx * Math.sin(a0);
  ex = snap(ex, odd(S.ed)); ey = snap(ey, odd(S.ed));
  const tile = frame === 'mac' ? squircle(m, m, ts) : squircle(0, 0, px);
  let defs = `<linearGradient id="${id}bg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="${P.bg[0]}"/><stop offset="1" stop-color="${P.bg[1]}"/></linearGradient>` +
    `<clipPath id="${id}c"><path d="${tile}"/></clipPath>` +
    (P.glow ? `<radialGradient id="${id}gl" gradientUnits="userSpaceOnUse" cx="${n(nx)}" cy="${n(ny)}" r="${n(ts * 0.55)}"><stop offset="0" stop-color="${P.glow}" stop-opacity="0.22"/><stop offset="1" stop-color="${P.glow}" stop-opacity="0"/></radialGradient>` : '') +
    `<mask id="${id}h" maskUnits="userSpaceOnUse" x="0" y="0" width="${px}" height="${px}"><rect width="${px}" height="${px}" fill="#fff"/><circle cx="${n(ex)}" cy="${n(ey)}" r="${n(S.ed / 2 + S.eg)}" fill="#000"/></mask>`;
  let body = `<path d="${tile}" fill="url(#${id}bg)"/>` + (P.glow ? `<rect width="${px}" height="${px}" fill="url(#${id}gl)" clip-path="url(#${id}c)"/>` : '');
  let g = '';
  if (S.fw && !o.noField) {
    /* J3's field: one line pair, axis tilted 10 degrees, crossing the equator just outside the rings' narrow side */
    const Leq = 330 * k, Rs = S.nd / 2 + 2 * k * 40, c = [nx, ny];
    g += `<path d="${fieldLine(c, Leq, 10, Rs, 1)}${fieldLine(c, Leq, 10, Rs, -1)}" fill="none" stroke="${P.det}" stroke-opacity="0.75" stroke-width="${n(S.fw)}" stroke-linecap="round"/>`;
  }
  if (o.rulers) { /* J8: ruler hairlines along the left and bottom edges, a tick every quarter */
    const L0 = m + ts * 0.1, L1 = m + ts * 0.9, x0 = Math.round(m + ts * 0.07) + 0.5, y0 = Math.round(m + ts * 0.93) - 0.5, tl = Math.max(1, Math.round(ts * 0.05));
    let d = `M${n(x0)},${n(L0)}V${n(L1)}M${n(L0)},${n(y0)}H${n(L1)}`; for (let i = 1; i < 4; i++) { const t = Math.round(L0 + (L1 - L0) * i / 4) + 0.5; d += `M${n(x0)},${n(t)}h${tl}M${n(t)},${n(y0)}v${-tl}`; }
    g += `<path d="${d}" fill="none" stroke="${P.det}" stroke-opacity="0.6" stroke-width="1"/>`;
  }
  g += `<g mask="url(#${id}h)">` + rings.map((r) => `<ellipse cx="${n(nx)}" cy="${n(ny)}" rx="${n(r.rx)}" ry="${n(r.ry)}" transform="rotate(${r.deg} ${n(nx)} ${n(ny)})" fill="none" stroke="${P.ring}" stroke-opacity="${o.ringOp || S.op || 0.9}" stroke-width="${n(S.rw)}"/>`).join('') + '</g>';
  g += `<circle cx="${n(nx)}" cy="${n(ny)}" r="${n(S.nd / 2)}" fill="${P.nuc}"/><circle cx="${n(ex)}" cy="${n(ey)}" r="${n(S.ed / 2)}" fill="${P.el}"/>`;
  if (o.lens) { /* J6: the porthole; the atom inside is cut by the lens, the rim on top */
    const lr = Math.round(ts * o.lens * 2) / 2, lc = m + ts / 2, rw = Math.max(1, Math.round(S.rw * 1.6));
    defs += `<clipPath id="${id}l"><circle cx="${n(lc)}" cy="${n(lc)}" r="${n(lr)}"/></clipPath>`;
    g = `<circle cx="${n(lc)}" cy="${n(lc)}" r="${n(lr)}" fill="${P.bg[0]}"/><g clip-path="url(#${id}l)">${g}</g><circle cx="${n(lc)}" cy="${n(lc)}" r="${n(lr - (rw % 2 ? 0.5 : 0))}" fill="none" stroke="${P.ring}" stroke-opacity="0.95" stroke-width="${rw}"/>`;
  }
  body += `<g clip-path="url(#${id}c)">${g}</g>`;
  if (P.rim && S.rim) body += `<path d="${tile}" fill="none" stroke="${P.rim}" stroke-opacity="0.35" stroke-width="${n(S.rim * 2)}" clip-path="url(#${id}c)"/>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${px}" height="${px}" viewBox="0 0 ${px} ${px}"><defs>${defs}</defs>${body}</svg>`;
}
module.exports = { smallSvg, SPEC, N, E };
