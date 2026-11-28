/* AudioLab app icon, round 5 (task IC7): zoomed-in small versions of K5 and M5 for 32 px and below.

   Like W7 and J9 (and S1, the small icon shipped by IC6): zoomed into the atom, tilted, the dipole field centred on
   the nucleus and cut by the tile edge, thin lines in DEVICE pixels snapped to the pixel grid, nucleus and electron
   with whole-pixel diameters on the grid. Each size is drawn at its own pixel size, never shrunk.

   KS1..KS3: the K5 family (rings). Built on S1's geometry (round4/small4.js and ic6/small6.js: the W7 crop, the
     electron anchored top right, the rings nudged so their straight-on edges land on the grid), with K5's lighter
     rings and its lit nucleus.
   MS1..MS3: the M5 family (field orbits). New: the nucleus sits low left of centre, the field axis tilted, the
     orbits r = L sin^2(theta) centred on it and run out past the tile edge on the right and left; each orbit scaled
     a hair so its outermost point on the tilted equator lands on a pixel centre; each half orbit ends a quarter of
     its reach from the nucleus, so the ends stay apart at the poles; the electron on the inner orbit, top right.

   smallSvg(sid, pid, px, frame, o) -> SVG string, viewBox 0 0 px px.
     px    : physical pixels; o.pt = 16 with px 32 (or 32 with px 64) is the 2x picture, drawn a hair heavier
     frame : 'full' (Windows, favicons, picker small) or 'mac' (Apple grid margin) */
(function (root) {
  'use strict';
  var PAL = (root.AL5 || (typeof require === 'function' ? require('./icons5.js') : null)).PAL;

  var SPEC = {
    16: { rw: 1.0, nd: 6, ed: 3, eg: 0.9, rim: 0.7, zoom: 1.3 },
    20: { rw: 1.05, nd: 7, ed: 4, eg: 1.0, rim: 0.8, zoom: 1.3 },
    24: { rw: 1.15, nd: 7, ed: 4, eg: 1.0, rim: 0.9, zoom: 1.4 },
    32: { rw: 1.3, nd: 9, ed: 5, eg: 1.2, rim: 1.0, zoom: 1.4 },
    40: { rw: 1.5, nd: 11, ed: 6, eg: 1.4, rim: 1.0, zoom: 1.45 },
    48: { rw: 1.7, nd: 13, ed: 7, eg: 1.6, rim: 1.2, zoom: 1.45 },
    64: { rw: 2.3, nd: 18, ed: 10, eg: 2.2, rim: 1.4, zoom: 1.4 }
  };
  function nearest(px) { var ks = Object.keys(SPEC).map(Number), b = ks[0]; ks.forEach(function (k) { if (Math.abs(k - px) < Math.abs(b - px)) b = k; }); return b; }
  function spec(px) { var b = nearest(px), S = SPEC[b], o = {}, k; for (k in S) o[k] = S[k]; if (b !== px) { var r = px / b; o.rw = S.rw * Math.sqrt(r); o.nd = Math.round(S.nd * r); o.ed = Math.max(2, Math.round(S.ed * r)); o.eg = S.eg * r; } return o; }
  function band(px) { return px <= 20 ? 'small' : px <= 32 ? 'mid' : 'big'; }

  /* the variants. ring family: ringOp, zoom (by size), field pairs per band, lit, glow (strength), edge.
     orbit family: N (nucleus in the 1024 tile), tilt, bold (orbit reach per band), hair (field pairs past the edge) */
  var VARIANTS = {
    KS1: { fam: 'K5', kind: 'ring', name: 'S1, lit', note: 'S1 as shipped, with K5 in it: the rings lighter (82 % instead of 90 %), the nucleus lit from the top left with a soft glow of a pixel or two. One hairline field pair, cut by the tile edge. The closest step from what ships today.',
      ringOp: 0.82, lit: true, glow: 0.3, tilt: 4, field: { small: [{ L: 600, op: 0.75, w: 1 }], mid: [{ L: 600, op: 0.75, w: 'hair' }], big: [{ L: 560, op: 0.65, w: 'hair' }, { L: 860, op: 0.5, w: 'hair' }] } },
    KS2: { fam: 'K5', kind: 'ring', name: 'Closer, tilted field', note: 'Zoomed further in (1.5 to 1.6 times instead of 1.3 to 1.4): the rings run out of the tile on the left and bottom, the field tilted 10° with two pairs at 24 px and up (one at 16). Lit nucleus and glow. The most "inside the atom".',
      ringOp: 0.82, lit: true, glow: 0.35, tilt: 10, zoom: { 16: 1.5, 20: 1.5, 24: 1.55, 32: 1.6, 40: 1.6, 48: 1.6, 64: 1.6 }, field: { small: [{ L: 640, op: 0.8, w: 1 }], mid: [{ L: 560, op: 0.8, w: 'hair' }, { L: 860, op: 0.6, w: 'hair' }], big: [{ L: 520, op: 0.7, w: 'hair' }, { L: 760, op: 0.6, w: 'hair' }, { L: 1040, op: 0.45, w: 'hair' }] } },
    KS3: { fam: 'K5', kind: 'ring', name: 'Glowing core, light edge', note: 'KS1 with K5c\'s glowing core: a stronger nucleus glow and a lit electron, and at 24 px and up a one-pixel light edge along the top of the tile (K5\'s glass edge, reduced). At 16 px it is KS1 with the stronger glow.',
      ringOp: 0.78, lit: true, glow: 0.5, elLit: true, edge: true, tilt: 4, field: { small: [{ L: 600, op: 0.75, w: 1 }], mid: [{ L: 600, op: 0.75, w: 'hair' }], big: [{ L: 560, op: 0.65, w: 'hair' }, { L: 860, op: 0.5, w: 'hair' }] } },
    MS1: { fam: 'M5', kind: 'orbit', name: 'Two orbits, zoomed', note: 'M5 zoomed in: the nucleus low left of centre, the field axis tilted 20°, two orbits in the ring colour whose outer one runs out past the right and left edges, the electron on the outer orbit at the top right, where S1 has it; at 40 px and up a third orbit and a hairline field pair. Flat nucleus, as S1.',
      N: [400, 600], tilt: 20, bold: { small: [420, 820], mid: [400, 780], big: [360, 600, 900] }, hair: { small: [], mid: [], big: [1150] }, el: [1, 42], op: 0.92 },
    MS2: { fam: 'M5', kind: 'orbit', name: 'Closer, lit', note: 'Further in: the nucleus a pixel bigger and lower left, the inner orbit already big, the outer one mostly cut by the edges so only its arcs show. Lit nucleus with a glow, as K5 and M5. The boldest at 16.',
      N: [360, 640], tilt: 24, bold: { small: [520, 1000], mid: [500, 960], big: [460, 820, 1200] }, hair: { small: [], mid: [], big: [] }, el: [0, 50], op: 0.92, lit: true, glow: 0.3, ndPlus: 1 },
    MS3: { fam: 'M5', kind: 'orbit', name: 'Three orbits at 32', note: 'Three orbits at 24 px and up (two at 16 and 20), the layered look of the big M5; the orbits a little more see-through (80 %) so they brighten where they gather at the poles. Lit nucleus, light top edge at 24 px and up.',
      N: [410, 600], tilt: 18, bold: { small: [400, 800], mid: [330, 560, 860], big: [300, 500, 740, 1020] }, hair: { small: [], mid: [], big: [] }, el: [1, 45], op: 0.8, lit: true, glow: 0.3, edge: true }
  };
  var IDS = ['KS1', 'KS2', 'KS3', 'MS1', 'MS2', 'MS3'];

  var n = function (v) { return (Math.round(v * 1000) / 1000).toString(); };
  function squircle(x, y, s) { var N = 96, a = s / 2, p = []; for (var i = 0; i < N; i++) { var t = i / N * Math.PI * 2, c = Math.cos(t), si = Math.sin(t); p.push(n(x + a + a * Math.sign(c) * Math.pow(Math.abs(c), 0.4)) + ',' + n(y + a + a * Math.sign(si) * Math.pow(Math.abs(si), 0.4))); } return 'M' + p.join('L') + 'Z'; }
  var E = [800, 190], ROT = [-36, 24, 84];
  function geo(z) { var t = (1.5 - z) / 0.5, W7 = [E[0] - 540 * Math.cos(-36 * Math.PI / 180), E[1] - 540 * Math.sin(-36 * Math.PI / 180)];
    return { RX: 360 * z, RY: 150 * z, N: [W7[0] + (512 - W7[0]) * t, W7[1] + (500 - W7[1]) * t] }; }
  function ext(rx, ry, deg) { var a = deg * Math.PI / 180, c = Math.cos(a), s = Math.sin(a); return [Math.sqrt(rx * rx * c * c + ry * ry * s * s), Math.sqrt(rx * rx * s * s + ry * ry * c * c)]; }
  function fieldPt(c, Leq, tilt, th, side) { var a = tilt * Math.PI / 180, r = Leq * Math.pow(Math.sin(th), 2), x = side * r * Math.sin(th), y = -r * Math.cos(th); return [c[0] + x * Math.cos(a) - y * Math.sin(a), c[1] + x * Math.sin(a) + y * Math.cos(a)]; }
  function fieldLine(c, Leq, tilt, Rs, side) {
    var t0 = Math.asin(Math.min(1, Math.sqrt(Rs / Leq))), pts = [];
    for (var i = 0; i <= 64; i++) pts.push(fieldPt(c, Leq, tilt, t0 + (Math.PI - 2 * t0) * i / 64, side));
    return 'M' + pts.map(function (p) { return n(p[0]) + ',' + n(p[1]); }).join('L');
  }
  var odd = function (v) { return Math.round(v) % 2 === 1; }, snap = function (v, isOdd) { return isOdd ? Math.floor(v) + 0.5 : Math.round(v); };
  var fieldCol = function (P) { return P.glow ? '#7AA8FF' : P.det; };
  function mix(a, b, t) { var h = function (x) { x = x.replace('#', ''); return [0, 2, 4].map(function (i) { return parseInt(x.substr(i, 2), 16); }); }, x = h(a), y = h(b); return '#' + [0, 1, 2].map(function (i) { var v = Math.round(x[i] + (y[i] - x[i]) * t); return (v < 16 ? '0' : '') + v.toString(16); }).join(''); }
  var uid = 0;

  /* the lit sphere (highlight top left) and the glow, both as radial gradients in device pixels */
  function litDefs(id, P, col, cx, cy, r, nm) {
    return '<radialGradient id="' + id + nm + '" gradientUnits="userSpaceOnUse" cx="' + n(cx - r * 0.38) + '" cy="' + n(cy - r * 0.42) + '" r="' + n(r * 1.5) + '"><stop offset="0" stop-color="' + mix(col, '#FFFFFF', 0.55) + '"/><stop offset="0.5" stop-color="' + col + '"/><stop offset="1" stop-color="' + mix(col, P.bg[1], 0.28) + '"/></radialGradient>';
  }
  function glowDefs(id, col, cx, cy, r0, r1, op, nm) {
    return '<radialGradient id="' + id + nm + '" gradientUnits="userSpaceOnUse" cx="' + n(cx) + '" cy="' + n(cy) + '" r="' + n(r1) + '"><stop offset="' + n(r0 / r1) + '" stop-color="' + col + '" stop-opacity="' + op + '"/><stop offset="1" stop-color="' + col + '" stop-opacity="0"/></radialGradient>';
  }

  function smallSvg(sid, pid, px, frame, o) {
    o = o || {}; var V = VARIANTS[sid], P = PAL[pid], id = 's5' + (++uid) + '_', S = spec(px), heavy = o.pt && o.pt < px;
    if (heavy) S.rw *= 1.12;
    var m = frame === 'mac' ? (px <= 16 ? 1 : Math.round(px * 100 / 1024)) : 0, ts = px - 2 * m, k = ts / 1024, B = band(nearest(px));
    var tile = frame === 'mac' ? squircle(m, m, ts) : squircle(0, 0, px);
    var nd = S.nd + (V.ndPlus || 0), nx, ny, ex, ey, ed = S.ed, g = '', defs = '';
    var rwOdd = Math.round(S.rw) % 2 === 1;
    if (V.kind === 'ring') {
      var z = (V.zoom && V.zoom[nearest(px)]) || S.zoom, G = geo(z);
      nx = snap(m + G.N[0] * k, odd(nd)); ny = snap(m + G.N[1] * k, odd(nd));
      var rings = ROT.map(function (deg) { var e2 = ext(G.RX * k, G.RY * k, deg), v = Math.abs(deg) > 60, e = v ? e2[0] : e2[1], c = v ? nx : ny, f = (snap(c + e, rwOdd) - c) / e; return { deg: deg, rx: G.RX * k * f, ry: G.RY * k * f }; });
      var r0 = rings[0], a0 = r0.deg * Math.PI / 180;
      ex = snap(nx + r0.rx * Math.cos(a0), odd(ed)); ey = snap(ny + r0.rx * Math.sin(a0), odd(ed));
      var Rs = nd / 2 + Math.max(1.5, px / 16);
      V.field[B].forEach(function (L) {
        var w = L.w === 'hair' ? (px >= 48 ? 1.2 : 1) * (heavy ? 1.1 : 1) : L.w;
        g += '<path d="' + fieldLine([nx, ny], L.L * k, V.tilt, Rs, 1) + fieldLine([nx, ny], L.L * k, V.tilt, Rs, -1) + '" fill="none" stroke="' + fieldCol(P) + '" stroke-opacity="' + L.op + '" stroke-width="' + n(w) + '" stroke-linecap="butt"/>';
      });
      g += '<g mask="url(#' + id + 'h)">' + rings.map(function (r) { return '<ellipse cx="' + n(nx) + '" cy="' + n(ny) + '" rx="' + n(r.rx) + '" ry="' + n(r.ry) + '" transform="rotate(' + r.deg + ' ' + n(nx) + ' ' + n(ny) + ')" fill="none" stroke="' + P.ring + '" stroke-opacity="' + V.ringOp + '" stroke-width="' + n(S.rw) + '"/>'; }).join('') + '</g>';
    } else {
      nx = snap(m + V.N[0] * k, odd(nd)); ny = snap(m + V.N[1] * k, odd(nd));
      var a = V.tilt * Math.PI / 180, Rs2 = nd / 2 + Math.max(1.5, px / 16);
      var fit = function (L) { var e = L * k * Math.cos(a); return L * k * ((snap(nx + e, rwOdd) - nx) / e); };
      var bold = V.bold[B].map(fit);
      var eo = V.el || [0, 58], ep = fieldPt([nx, ny], bold[Math.min(eo[0], bold.length - 1)], V.tilt, eo[1] * Math.PI / 180, 1); ex = snap(ep[0], odd(ed)); ey = snap(ep[1], odd(ed));
      V.hair[B].forEach(function (L) { g += '<path d="' + fieldLine([nx, ny], L * k, V.tilt, Rs2, 1) + fieldLine([nx, ny], L * k, V.tilt, Rs2, -1) + '" fill="none" stroke="' + fieldCol(P) + '" stroke-opacity="0.72" stroke-width="' + n(heavy ? 1.1 : 1) + '" stroke-linecap="butt"/>'; });
      var og = '';
      bold.forEach(function (L) { [1, -1].forEach(function (sd) { og += '<path d="' + fieldLine([nx, ny], L, V.tilt, Math.max(Rs2, 0.24 * L), sd) + '" fill="none" stroke="' + P.ring + '" stroke-opacity="' + V.op + '" stroke-width="' + n(S.rw) + '" stroke-linecap="round"/>'; }); });
      g += '<g mask="url(#' + id + 'h)">' + og + '</g>';
    }
    defs += '<linearGradient id="' + id + 'bg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="' + P.bg[0] + '"/><stop offset="1" stop-color="' + P.bg[1] + '"/></linearGradient>' +
      '<clipPath id="' + id + 'c"><path d="' + tile + '"/></clipPath>' +
      (P.glow ? '<radialGradient id="' + id + 'gl" gradientUnits="userSpaceOnUse" cx="' + n(nx) + '" cy="' + n(ny) + '" r="' + n(ts * 0.55) + '"><stop offset="0" stop-color="' + P.glow + '" stop-opacity="0.22"/><stop offset="1" stop-color="' + P.glow + '" stop-opacity="0"/></radialGradient>' : '') +
      '<mask id="' + id + 'h" maskUnits="userSpaceOnUse" x="0" y="0" width="' + px + '" height="' + px + '"><rect width="' + px + '" height="' + px + '" fill="#fff"/><circle cx="' + n(ex) + '" cy="' + n(ey) + '" r="' + n(ed / 2 + S.eg) + '" fill="#000"/></mask>';
    /* nucleus glow, then nucleus and electron (lit or flat) */
    if (V.glow) { var gr = nd / 2 + (px <= 20 ? 1.5 : Math.max(2, nd * 0.75)); defs += glowDefs(id, P.glow ? mix(P.nuc, '#FFFFFF', 0.1) : P.nuc, nx, ny, nd / 2, gr, V.glow * (P.glow ? 1 : 0.7), 'ng'); g += '<circle cx="' + n(nx) + '" cy="' + n(ny) + '" r="' + n(gr) + '" fill="url(#' + id + 'ng)"/>'; }
    if (V.elLit && px >= 24) { var er = ed / 2 + Math.max(1.5, ed * 0.7); defs += glowDefs(id, P.el, ex, ey, ed / 2, er, 0.4, 'eg'); g += '<circle cx="' + n(ex) + '" cy="' + n(ey) + '" r="' + n(er) + '" fill="url(#' + id + 'eg)"/>'; }
    if (V.lit) defs += litDefs(id, P, P.nuc, nx, ny, nd / 2, 'nl');
    if (V.elLit) defs += litDefs(id, P, P.el, ex, ey, ed / 2, 'el');
    g += '<circle cx="' + n(nx) + '" cy="' + n(ny) + '" r="' + n(nd / 2) + '" fill="' + (V.lit ? 'url(#' + id + 'nl)' : P.nuc) + '"/><circle cx="' + n(ex) + '" cy="' + n(ey) + '" r="' + n(ed / 2) + '" fill="' + (V.elLit ? 'url(#' + id + 'el)' : P.el) + '"/>';
    var body = '<path d="' + tile + '" fill="url(#' + id + 'bg)"/>' + (P.glow ? '<rect width="' + px + '" height="' + px + '" fill="url(#' + id + 'gl)" clip-path="url(#' + id + 'c)"/>' : '');
    body += '<g clip-path="url(#' + id + 'c)">' + g + '</g>';
    if (V.edge && px >= 24) {
      /* K5's glass edge reduced to one pixel: a light line along the top of the tile, fading down the sides */
      defs += '<linearGradient id="' + id + 'ed" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="' + (P.glow ? 0.6 : 0.9) + '"/><stop offset="0.25" stop-color="#fff" stop-opacity="0.08"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>';
      body += '<path d="' + tile + '" fill="none" stroke="url(#' + id + 'ed)" stroke-width="' + n(px >= 48 ? 2.4 : 2) + '" clip-path="url(#' + id + 'c)"/>';
    } else if (P.rim && S.rim) body += '<path d="' + tile + '" fill="none" stroke="' + P.rim + '" stroke-opacity="0.35" stroke-width="' + n(S.rim * 2) + '" clip-path="url(#' + id + 'c)"/>';
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + px + '" height="' + px + '" viewBox="0 0 ' + px + ' ' + px + '"><defs>' + defs + '</defs>' + body + '</svg>';
  }

  var RECS = [
    { s: 'KS3', why: 'S1 with K5\'s glowing core and, from 24 px, its light edge: the family reads as one with K5 and K5c, and at 16 px it is still S1\'s calm atom.' },
    { s: 'MS1', why: 'The clearest zoomed field orbits: two orbits on the pixel grid, the outer one cut by the edges, the electron top right where S1 has it.' }
  ];
  var API = { VARIANTS: VARIANTS, IDS: IDS, smallSvg: smallSvg, SPEC: SPEC, RECS: RECS };
  root.AL5S = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
