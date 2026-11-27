/* AudioLab app icon, task IC6: the small masters for 32 px and below (the user's pick of round 4: S1, "Thin field").

   ringSmall(pid, px, frame, o)  S1 of round 4 (tools/icon-lab/round4/small4.js, drawn the same way, pixel for pixel
     for the default case): the W7 crop and tilt, IC4's thin rings at 90 % on the pixel grid, nucleus and electron
     with whole-pixel diameters, and J9's dipole field centred on the nucleus as one hairline pair, cut by the tile
     edge. Options carry the picker variants:
       o.pt     16 pt at 2x (px 32, pt 16) or 32 pt at 2x (px 64, pt 32): a hair heavier, as in small4.js
       o.zoom, o.N, o.spec   another crop (J6 porthole, J8 measurements), from IC4's picker small versions
       o.lens   J6: the atom inside a porthole of this radius (share of the tile), its rim on top
       o.rulers J8: ruler hairlines along the left and bottom edges (24 px and up)
   orbitSmall(id, pid, px, frame, o)  the same treatment for the field-orbit designs of round 4 (M3, M5):
     the orbits are dipole field lines r = L sin^2(theta) round the nucleus, drawn with a width in DEVICE pixels
     (1 px at 16, 1.3 at 32), each scaled by a hair so its outermost point on the magnetic equator lands on a pixel
     centre; nucleus and electron whole pixels on the grid; the electron on the middle orbit 60 degrees from the
     axis as in the big drawing. Two orbits at 32 px and below, as the big drawing's own small level (three merge
     into one blob at the poles at 32 px). M3 adds one hairline field pair running out past the tile edge (its "field to the
     edge"); M5 its orbits alone (its glass edge and lit spheres are a big-size effect only).
   Each returns an SVG string with viewBox 0 0 px px; frame 'full' (Windows, favicons, picker small) or 'mac'. */
'use strict';
const PAL = require('../round4/icons4.js').PAL;

const SPEC = {
  16: { rw: 1.0, nd: 6, ed: 3, eg: 0.9, rim: 0.7, zoom: 1.3 },
  20: { rw: 1.05, nd: 7, ed: 4, eg: 1.0, rim: 0.8, zoom: 1.3 },
  24: { rw: 1.15, nd: 7, ed: 4, eg: 1.0, rim: 0.9, zoom: 1.4 },
  32: { rw: 1.3, nd: 9, ed: 5, eg: 1.2, rim: 1.0, zoom: 1.4 },
  40: { rw: 1.5, nd: 11, ed: 6, eg: 1.4, rim: 1.0, zoom: 1.45 },
  48: { rw: 1.7, nd: 13, ed: 7, eg: 1.6, rim: 1.2, zoom: 1.45 },
  64: { rw: 2.3, nd: 18, ed: 10, eg: 2.2, rim: 1.4, zoom: 1.4 }
};
/* S1's field (round 4): one pair at 32 px and below, crossing at 600 in the 1024 tile; two pairs at 40 and up */
const S1 = { ringOp: 0.9, tilt: 4, field: { small: [{ L: 600, op: 0.75, w: 1 }], mid: [{ L: 600, op: 0.75, w: 'hair' }], big: [{ L: 560, op: 0.65, w: 'hair' }, { L: 860, op: 0.5, w: 'hair' }] } };

function nearest(px) { const ks = Object.keys(SPEC).map(Number); let b = ks[0]; for (const k of ks) if (Math.abs(k - px) < Math.abs(b - px)) b = k; return b; }
function spec(px) { if (SPEC[px]) return Object.assign({}, SPEC[px]); const b = nearest(px), S = SPEC[b], r = px / b; return { rw: S.rw * Math.sqrt(r), nd: Math.round(S.nd * r), ed: Math.max(2, Math.round(S.ed * r)), eg: S.eg * r, rim: S.rim, zoom: S.zoom }; }
const n = (v) => (Math.round(v * 1000) / 1000).toString();
function squircle(x, y, s) { const N = 96, a = s / 2, p = []; for (let i = 0; i < N; i++) { const t = i / N * Math.PI * 2, c = Math.cos(t), si = Math.sin(t); p.push(n(x + a + a * Math.sign(c) * Math.pow(Math.abs(c), 0.4)) + ',' + n(y + a + a * Math.sign(si) * Math.pow(Math.abs(si), 0.4))); } return 'M' + p.join('L') + 'Z'; }
const E = [800, 190], ROT = [-36, 24, 84];
function geo(z) { const t = (1.5 - z) / 0.5, W7 = [E[0] - 540 * Math.cos(-36 * Math.PI / 180), E[1] - 540 * Math.sin(-36 * Math.PI / 180)];
  return { RX: 360 * z, RY: 150 * z, N: [W7[0] + (512 - W7[0]) * t, W7[1] + (500 - W7[1]) * t] }; }
function ext(rx, ry, deg) { const a = deg * Math.PI / 180, c = Math.cos(a), s = Math.sin(a); return [Math.sqrt(rx * rx * c * c + ry * ry * s * s), Math.sqrt(rx * rx * s * s + ry * ry * c * c)]; }
/* a dipole field line r = L sin^2(theta) round c, axis tilted, from the surface Rs round to the surface (one side) */
function fieldLine(c, Leq, tilt, Rs, side) {
  const a = tilt * Math.PI / 180, t0 = Math.asin(Math.min(1, Math.sqrt(Rs / Leq))), pts = [];
  for (let i = 0; i <= 64; i++) { const th = t0 + (Math.PI - 2 * t0) * i / 64, r = Leq * Math.sin(th) ** 2, x = side * r * Math.sin(th), y = -r * Math.cos(th); pts.push([c[0] + x * Math.cos(a) - y * Math.sin(a), c[1] + x * Math.sin(a) + y * Math.cos(a)]); }
  return 'M' + pts.map((p) => n(p[0]) + ',' + n(p[1])).join('L');
}
function fieldPt(c, Leq, tilt, th, side) { const a = tilt * Math.PI / 180, r = Leq * Math.sin(th) ** 2, x = side * r * Math.sin(th), y = -r * Math.cos(th); return [c[0] + x * Math.cos(a) - y * Math.sin(a), c[1] + x * Math.sin(a) + y * Math.cos(a)]; }
const odd = (v) => Math.round(v) % 2 === 1, snap = (v, isOdd) => isOdd ? Math.floor(v) + 0.5 : Math.round(v);
/* on the navy tile the field colour is lifted a little: a 1 px line at #6096FF over navy is too dim at 16 px (round 4) */
const fieldCol = (P) => P.glow ? '#7AA8FF' : P.det;
let uid = 0;
function frameOf(px, frame) { const m = frame === 'mac' ? (px <= 16 ? 1 : Math.round(px * 100 / 1024)) : 0; return { m, ts: px - 2 * m, k: (px - 2 * m) / 1024 }; }
function tileDefs(P, id, tile, cx, cy, ts) {
  return `<linearGradient id="${id}bg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="${P.bg[0]}"/><stop offset="1" stop-color="${P.bg[1]}"/></linearGradient>` +
    `<clipPath id="${id}c"><path d="${tile}"/></clipPath>` +
    (P.glow ? `<radialGradient id="${id}gl" gradientUnits="userSpaceOnUse" cx="${n(cx)}" cy="${n(cy)}" r="${n(ts * 0.55)}"><stop offset="0" stop-color="${P.glow}" stop-opacity="0.22"/><stop offset="1" stop-color="${P.glow}" stop-opacity="0"/></radialGradient>` : '');
}
function wrap(P, id, px, tile, defs, g, rim) {
  let body = `<path d="${tile}" fill="url(#${id}bg)"/>` + (P.glow ? `<rect width="${px}" height="${px}" fill="url(#${id}gl)" clip-path="url(#${id}c)"/>` : '');
  body += `<g clip-path="url(#${id}c)">${g}</g>`;
  if (P.rim && rim) body += `<path d="${tile}" fill="none" stroke="${P.rim}" stroke-opacity="0.35" stroke-width="${n(rim * 2)}" clip-path="url(#${id}c)"/>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${px}" height="${px}" viewBox="0 0 ${px} ${px}"><defs>${defs}</defs>${body}</svg>`;
}

/* ---------- S1: the ring designs (J3, and the J6 / J8 crops) ---------- */
function ringSmall(pid, px, frame, o) {
  o = o || {}; const P = PAL[pid], id = 'i6r' + (++uid) + '_', S = Object.assign(spec(px), o.spec || {});
  if (o.pt && o.pt < px) S.rw *= 1.12; /* 16 pt at 2x: seen at half size, so a hair heavier */
  const b = nearest(px), band = b <= 20 ? 'small' : b <= 32 ? 'mid' : 'big';
  const G = geo(o.zoom || S.zoom), N = o.N || G.N, F = frameOf(px, frame), m = F.m, ts = F.ts, k = F.k;
  const nx = snap(m + N[0] * k, odd(S.nd)), ny = snap(m + N[1] * k, odd(S.nd));
  const rwOdd = Math.round(S.rw) % 2 === 1;
  const rings = ROT.map((deg) => { const e2 = ext(G.RX * k, G.RY * k, deg), v = Math.abs(deg) > 60, e = v ? e2[0] : e2[1], c = v ? nx : ny, f = (snap(c + e, rwOdd) - c) / e; return { deg, rx: G.RX * k * f, ry: G.RY * k * f }; });
  const r0 = rings[0], a0 = r0.deg * Math.PI / 180, ex = snap(nx + r0.rx * Math.cos(a0), odd(S.ed)), ey = snap(ny + r0.rx * Math.sin(a0), odd(S.ed));
  const tile = frame === 'mac' ? squircle(m, m, ts) : squircle(0, 0, px);
  let defs = tileDefs(P, id, tile, nx, ny, ts) +
    `<mask id="${id}h" maskUnits="userSpaceOnUse" x="0" y="0" width="${px}" height="${px}"><rect width="${px}" height="${px}" fill="#fff"/><circle cx="${n(ex)}" cy="${n(ey)}" r="${n(S.ed / 2 + S.eg)}" fill="#000"/></mask>`;
  let g = '';
  const Rs = S.nd / 2 + Math.max(1.5, px / 16), c = [nx, ny];
  for (const L of S1.field[band]) {
    const w = L.w === 'hair' ? (px >= 48 ? 1.2 : 1) * (o.pt && o.pt < px ? 1.1 : 1) : L.w;
    g += `<path d="${fieldLine(c, L.L * k, S1.tilt, Rs, 1)}${fieldLine(c, L.L * k, S1.tilt, Rs, -1)}" fill="none" stroke="${fieldCol(P)}" stroke-opacity="${L.op}" stroke-width="${n(w)}" stroke-linecap="butt"/>`;
  }
  if (o.rulers && px >= 24) {
    const L0 = m + ts * 0.1, L1 = m + ts * 0.9, x0 = Math.round(m + ts * 0.07) + 0.5, y0 = Math.round(m + ts * 0.93) - 0.5, tl = Math.max(1, Math.round(ts * 0.05));
    let d = `M${n(x0)},${n(L0)}V${n(L1)}M${n(L0)},${n(y0)}H${n(L1)}`; for (let i = 1; i < 4; i++) { const t = Math.round(L0 + (L1 - L0) * i / 4) + 0.5; d += `M${n(x0)},${n(t)}h${tl}M${n(t)},${n(y0)}v${-tl}`; }
    g += `<path d="${d}" fill="none" stroke="${P.det}" stroke-opacity="0.6" stroke-width="1"/>`;
  }
  g += `<g mask="url(#${id}h)">` + rings.map((r) => `<ellipse cx="${n(nx)}" cy="${n(ny)}" rx="${n(r.rx)}" ry="${n(r.ry)}" transform="rotate(${r.deg} ${n(nx)} ${n(ny)})" fill="none" stroke="${P.ring}" stroke-opacity="${S1.ringOp}" stroke-width="${n(S.rw)}"/>`).join('') + '</g>';
  g += `<circle cx="${n(nx)}" cy="${n(ny)}" r="${n(S.nd / 2)}" fill="${P.nuc}"/><circle cx="${n(ex)}" cy="${n(ey)}" r="${n(S.ed / 2)}" fill="${P.el}"/>`;
  if (o.lens) {
    const lr = Math.round(ts * o.lens * 2) / 2, lc = m + ts / 2, lw = Math.max(1, Math.round(S.rw * 1.6));
    defs += `<clipPath id="${id}l"><circle cx="${n(lc)}" cy="${n(lc)}" r="${n(lr)}"/></clipPath>`;
    g = `<circle cx="${n(lc)}" cy="${n(lc)}" r="${n(lr)}" fill="${P.bg[0]}"/><g clip-path="url(#${id}l)">${g}</g><circle cx="${n(lc)}" cy="${n(lc)}" r="${n(lr - (lw % 2 ? 0.5 : 0))}" fill="none" stroke="${P.ring}" stroke-opacity="0.95" stroke-width="${lw}"/>`;
  }
  return wrap(P, id, px, tile, defs, g, S.rim);
}

/* ---------- the field-orbit designs (M3, M5) ---------- */
const ORB = {
  /* bold: the orbits' equator crossings in the 1024 tile (whole mark centred, as the big drawing at scale 0.86);
     edge: the hairline field pairs that run past the tile edge; tilt as the big drawing */
  M3: { tilt: 12, bold: { small: [232, 430], mid: [250, 450] }, edge: { small: [], mid: [705] }, op: 0.95 },
  M5: { tilt: 10, bold: { small: [232, 430], mid: [250, 450] }, edge: { small: [], mid: [] }, op: 0.95 }
};
function orbitSmall(did, pid, px, frame, o) {
  o = o || {}; const D = ORB[did], P = PAL[pid], id = 'i6o' + (++uid) + '_', S = Object.assign(spec(px), o.spec || {});
  if (o.pt && o.pt < px) S.rw *= 1.12;
  const band = px <= 20 ? 'small' : 'mid', F = frameOf(px, frame), m = F.m, ts = F.ts, k = F.k;
  /* whole-pixel nucleus and electron in the big drawing's proportion at its small level (nucleus 96, electron 55 units
     in the 1024 tile as radii), never below 4 and 3 px */
  const nd = Math.max(4, Math.round(192 * k)), ed = Math.max(3, Math.round(110 * k));
  const nx = snap(m + 512 * k, odd(nd)), ny = snap(m + 512 * k, odd(nd)), c = [nx, ny];
  const a = D.tilt * Math.PI / 180, Rs = nd / 2 + Math.max(1.5, px / 16), rwOdd = Math.round(S.rw) % 2 === 1;
  /* scale each orbit so its outermost x (on the tilted equator) lands on a pixel centre (odd width) or edge (even) */
  const fit = (L) => { const e = L * k * Math.cos(a); return L * k * ((snap(nx + e, rwOdd) - nx) / e); };
  const bold = D.bold[band].map(fit), edge = D.edge[band].map((L) => L * k);
  const tile = frame === 'mac' ? squircle(m, m, ts) : squircle(0, 0, px);
  const mid = bold[Math.min(1, bold.length - 1)], ep0 = fieldPt(c, mid, D.tilt, 60 * Math.PI / 180, 1), ex = snap(ep0[0], odd(ed)), ey = snap(ep0[1], odd(ed));
  let defs = tileDefs(P, id, tile, nx, ny, ts) +
    `<mask id="${id}h" maskUnits="userSpaceOnUse" x="0" y="0" width="${px}" height="${px}"><rect width="${px}" height="${px}" fill="#fff"/><circle cx="${n(ex)}" cy="${n(ey)}" r="${n(ed / 2 + S.eg)}" fill="#000"/></mask>`;
  let g = '';
  for (const L of edge) g += `<path d="${fieldLine(c, L, D.tilt, Rs, 1)}${fieldLine(c, L, D.tilt, Rs, -1)}" fill="none" stroke="${fieldCol(P)}" stroke-opacity="0.75" stroke-width="${n(o.pt && o.pt < px ? 1.1 : 1)}" stroke-linecap="butt"/>`;
  /* each half orbit on its own, so they gather brighter at the poles (the transparency of the big drawing) */
  /* each orbit ends at its own distance from the nucleus (two fifths of its reach, at least the surface gap), so the
     ends stay apart at the poles instead of merging into one blob at these sizes */
  g += bold.map((L) => [1, -1].map((sd) => `<path d="${fieldLine(c, L, D.tilt, Math.max(Rs, 0.4 * L), sd)}" fill="none" stroke="${P.ring}" stroke-opacity="${D.op}" stroke-width="${n(S.rw)}" stroke-linecap="round"/>`).join('')).join('');
  g = `<g mask="url(#${id}h)">${g}</g>`;
  g += `<circle cx="${n(nx)}" cy="${n(ny)}" r="${n(nd / 2)}" fill="${P.nuc}"/><circle cx="${n(ex)}" cy="${n(ey)}" r="${n(ed / 2)}" fill="${P.el}"/>`;
  return wrap(P, id, px, tile, defs, g, S.rim);
}

module.exports = { ringSmall, orbitSmall, SPEC, S1, ORB };
