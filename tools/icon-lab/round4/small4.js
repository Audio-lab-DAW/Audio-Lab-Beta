/* AudioLab app icon, round 4 (task IC5): J9 (the W7 field) redrawn as the master for 32 px and below
   (16 and 32 at 1x and 2x, the Windows small sizes 16 to 48, the favicons, a menu-bar template).

   Built on IC4's small master (tools/icon-lab/ic4/small.js), whose geometry it keeps: the W7 crop (the atom zoomed
   1.5 times into its top right, tilted 6 degrees, the electron anchored at the top right), the three orbits as
   ellipses with a stroke width in DEVICE pixels, each ring nudged so its straight-on edges land on the pixel grid,
   nucleus and electron with whole-pixel diameters centred on the grid. What J9 adds: the dipole field centred on
   the nucleus and running out past the tile edge, cut by it, reduced to what reads at the size (one or two line
   pairs, a hairline), and optionally I5's ruler.

   smallSvg(sid, pid, px, frame, o) -> SVG string, viewBox 0 0 px px.
     sid   : 'S1'..'S4', or 'IC4' (IC4's shipped small master, reproduced for comparison)
     px    : physical pixels (16 at 2x is drawn at 32 physical px with o.pt = 16, a touch heavier)
     frame : 'full' (Windows, favicons) or 'mac' (Apple grid margin)
   template(sid, px, ink) -> a one-colour version (the mark only, no tile) for a menu bar or tray icon. */
(function (root) {
  'use strict';
  var PAL = (root.AL4 || (typeof require === 'function' ? require('./icons4.js') : null)).PAL;

  /* per physical px: ring width, nucleus and electron diameters, electron gap, rim, zoom (IC4's table) */
  var SPEC = {
    16: { rw: 1.0, nd: 6, ed: 3, eg: 0.9, rim: 0.7, zoom: 1.3 },
    20: { rw: 1.05, nd: 7, ed: 4, eg: 1.0, rim: 0.8, zoom: 1.3 },
    24: { rw: 1.15, nd: 7, ed: 4, eg: 1.0, rim: 0.9, zoom: 1.4 },
    32: { rw: 1.3, nd: 9, ed: 5, eg: 1.2, rim: 1.0, zoom: 1.4 },
    40: { rw: 1.5, nd: 11, ed: 6, eg: 1.4, rim: 1.0, zoom: 1.45 },
    48: { rw: 1.7, nd: 13, ed: 7, eg: 1.6, rim: 1.2, zoom: 1.45 },
    64: { rw: 2.3, nd: 18, ed: 10, eg: 2.2, rim: 1.4, zoom: 1.4 }
  };
  var IC4FW = { 16: 0, 20: 0, 24: 0.8, 32: 0.9, 40: 1.0, 48: 1.1, 64: 1.6 };
  function nearest(px) { var ks = Object.keys(SPEC).map(Number), b = ks[0]; ks.forEach(function (k) { if (Math.abs(k - px) < Math.abs(b - px)) b = k; }); return b; }
  function spec(px) { if (SPEC[px]) return SPEC[px]; var b = nearest(px), S = SPEC[b], r = px / b; return { rw: S.rw * Math.sqrt(r), nd: Math.round(S.nd * r), ed: Math.max(2, Math.round(S.ed * r)), eg: S.eg * r, rim: S.rim, zoom: S.zoom }; }

  /* The four J9 variants. field: line pairs [{L: crossing distance in the 1024 tile, op, w: px or 'hair'}] by size band
     (small = up to 20 px, mid = 24 to 32, big = 40 and up); tilt of the field axis (J9: 4 degrees); ringOp. */
  var VARIANTS = {
    S1: { name: 'Thin field', note: 'IC4\'s thin rings at 90 % with J9\'s field: one line pair centred on the nucleus, a hairline, running out past the tile edge. At 16 px it is a single 1 px arc.',
      ringOp: 0.9, tilt: 4, field: { small: [{ L: 600, op: 0.75, w: 1 }], mid: [{ L: 600, op: 0.75, w: 'hair' }], big: [{ L: 560, op: 0.65, w: 'hair' }, { L: 860, op: 0.5, w: 'hair' }] } },
    S2: { name: 'Field first', note: 'The field takes the lead: two line pairs at 32 px (one at 16) a little stronger, the rings lighter (75 %), the nucleus one pixel bigger. Closest to J9\'s big drawing.',
      ringOp: 0.75, tilt: 4, nd: 1, field: { small: [{ L: 600, op: 0.9, w: 1 }], mid: [{ L: 540, op: 0.85, w: 'hair' }, { L: 780, op: 0.7, w: 'hair' }], big: [{ L: 500, op: 0.8, w: 'hair' }, { L: 700, op: 0.65, w: 'hair' }, { L: 940, op: 0.5, w: 'hair' }] } },
    S3: { name: 'Field and ruler', note: 'S1 with I5\'s measurements: a hairline ruler along the left and bottom edges with three ticks at 24 px and up (J9\'s rulers, reduced). At 16 px it is S1.',
      ringOp: 0.9, tilt: 4, ruler: true, field: { small: [{ L: 600, op: 0.75, w: 1 }], mid: [{ L: 600, op: 0.75, w: 'hair' }], big: [{ L: 560, op: 0.65, w: 'hair' }, { L: 860, op: 0.5, w: 'hair' }] } },
    S4: { name: 'Less zoom', note: 'The crop opened up (zoom 1.15 to 1.25 instead of 1.3 to 1.4) so more of the atom and of the field fit, the field\'s left lobe comes into the tile. Reads as an atom first.',
      ringOp: 0.9, tilt: 4, zoom: { 16: 1.15, 20: 1.15, 24: 1.2, 32: 1.25, 40: 1.25, 48: 1.3, 64: 1.3 }, field: { small: [{ L: 560, op: 0.75, w: 1 }], mid: [{ L: 540, op: 0.75, w: 'hair' }, { L: 800, op: 0.6, w: 'hair' }], big: [{ L: 520, op: 0.65, w: 'hair' }, { L: 780, op: 0.55, w: 'hair' }] } },
    IC4: { name: 'IC4 small master (shipped in v0.270)', note: 'For comparison: what ships today at 64 px and below.', ringOp: 0.9, ic4: true }
  };

  var n = function (v) { return (Math.round(v * 1000) / 1000).toString(); };
  function squircle(x, y, s) { var N = 96, a = s / 2, p = []; for (var i = 0; i < N; i++) { var t = i / N * Math.PI * 2, c = Math.cos(t), si = Math.sin(t); p.push(n(x + a + a * Math.sign(c) * Math.pow(Math.abs(c), 0.4)) + ',' + n(y + a + a * Math.sign(si) * Math.pow(Math.abs(si), 0.4))); } return 'M' + p.join('L') + 'Z'; }
  var E = [800, 190], ROT = [-36, 24, 84];
  function geo(z) { var t = (1.5 - z) / 0.5, W7 = [E[0] - 540 * Math.cos(-36 * Math.PI / 180), E[1] - 540 * Math.sin(-36 * Math.PI / 180)];
    return { RX: 360 * z, RY: 150 * z, N: [W7[0] + (512 - W7[0]) * t, W7[1] + (500 - W7[1]) * t] }; }
  function ext(rx, ry, deg) { var a = deg * Math.PI / 180, c = Math.cos(a), s = Math.sin(a); return [Math.sqrt(rx * rx * c * c + ry * ry * s * s), Math.sqrt(rx * rx * s * s + ry * ry * c * c)]; }
  function fieldLine(c, Leq, tilt, Rs, side) {
    var a = tilt * Math.PI / 180, t0 = Math.asin(Math.min(1, Math.sqrt(Rs / Leq))), pts = [];
    for (var i = 0; i <= 64; i++) { var th = t0 + (Math.PI - 2 * t0) * i / 64, r = Leq * Math.pow(Math.sin(th), 2), x = side * r * Math.sin(th), y = -r * Math.cos(th); pts.push([c[0] + x * Math.cos(a) - y * Math.sin(a), c[1] + x * Math.sin(a) + y * Math.cos(a)]); }
    return 'M' + pts.map(function (p) { return n(p[0]) + ',' + n(p[1]); }).join('L');
  }
  var uid = 0;

  /* the geometry for a size: nucleus, rings and electron on the pixel grid */
  function layout(V, px, frame, o) {
    var S = {}, k0 = spec(px); for (var kk in k0) S[kk] = k0[kk];
    if (o.pt && o.pt < px) { S.rw *= 1.12; } /* 16 pt at 2x: seen at half size, so a hair heavier */
    if (V.nd) S.nd += V.nd;
    var b = nearest(px), z = (V.zoom && V.zoom[b]) || S.zoom, G = geo(z);
    var m = frame === 'mac' ? (px <= 16 ? 1 : Math.round(px * 100 / 1024)) : 0, ts = px - 2 * m, k = ts / 1024;
    var odd = function (v) { return Math.round(v) % 2 === 1; }, snap = function (v, isOdd) { return isOdd ? Math.floor(v) + 0.5 : Math.round(v); };
    var nx = snap(m + G.N[0] * k, odd(S.nd)), ny = snap(m + G.N[1] * k, odd(S.nd));
    var rwOdd = Math.round(S.rw) % 2 === 1;
    var rings = ROT.map(function (deg) {
      var e2 = ext(G.RX * k, G.RY * k, deg), vertical = Math.abs(deg) > 60, e = vertical ? e2[0] : e2[1], c = vertical ? nx : ny;
      var f = (snap(c + e, rwOdd) - c) / e; return { deg: deg, rx: G.RX * k * f, ry: G.RY * k * f };
    });
    var r0 = rings[0], a0 = r0.deg * Math.PI / 180;
    var ex = snap(nx + r0.rx * Math.cos(a0), odd(S.ed)), ey = snap(ny + r0.rx * Math.sin(a0), odd(S.ed));
    return { S: S, m: m, ts: ts, k: k, nx: nx, ny: ny, ex: ex, ey: ey, rings: rings, band: b <= 20 ? 'small' : b <= 32 ? 'mid' : 'big' };
  }

  function smallSvg(sid, pid, px, frame, o) {
    o = o || {}; var V = VARIANTS[sid], P = PAL[pid], id = 'sm' + (++uid) + '_', Y = layout(V, px, frame, o), S = Y.S, k = Y.k, nx = Y.nx, ny = Y.ny;
    var tile = frame === 'mac' ? squircle(Y.m, Y.m, Y.ts) : squircle(0, 0, px);
    var defs = '<linearGradient id="' + id + 'bg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="' + P.bg[0] + '"/><stop offset="1" stop-color="' + P.bg[1] + '"/></linearGradient>' +
      '<clipPath id="' + id + 'c"><path d="' + tile + '"/></clipPath>' +
      (P.glow ? '<radialGradient id="' + id + 'gl" gradientUnits="userSpaceOnUse" cx="' + n(nx) + '" cy="' + n(ny) + '" r="' + n(Y.ts * 0.55) + '"><stop offset="0" stop-color="' + P.glow + '" stop-opacity="0.22"/><stop offset="1" stop-color="' + P.glow + '" stop-opacity="0"/></radialGradient>' : '') +
      '<mask id="' + id + 'h" maskUnits="userSpaceOnUse" x="0" y="0" width="' + px + '" height="' + px + '"><rect width="' + px + '" height="' + px + '" fill="#fff"/><circle cx="' + n(Y.ex) + '" cy="' + n(Y.ey) + '" r="' + n(S.ed / 2 + S.eg) + '" fill="#000"/></mask>';
    var body = '<path d="' + tile + '" fill="url(#' + id + 'bg)"/>' + (P.glow ? '<rect width="' + px + '" height="' + px + '" fill="url(#' + id + 'gl)" clip-path="url(#' + id + 'c)"/>' : '');
    var g = '', c = [nx, ny];
    if (V.ic4) {
      var fw = IC4FW[nearest(px)];
      if (fw) { var Rs0 = S.nd / 2 + 2 * k * 40; g += '<path d="' + fieldLine(c, 330 * k, 10, Rs0, 1) + fieldLine(c, 330 * k, 10, Rs0, -1) + '" fill="none" stroke="' + P.det + '" stroke-opacity="0.75" stroke-width="' + n(fw) + '" stroke-linecap="round"/>'; }
    } else {
      /* J9's field: centred on the nucleus, starting one pixel and a half outside it, cut by the tile edge */
      var Rs = S.nd / 2 + Math.max(1.5, px / 16);
      V.field[Y.band].forEach(function (L) {
        var w = L.w === 'hair' ? (px >= 48 ? 1.2 : 1) * (o.pt && o.pt < px ? 1.1 : 1) : L.w;
        g += '<path d="' + fieldLine(c, L.L * k, V.tilt, Rs, 1) + fieldLine(c, L.L * k, V.tilt, Rs, -1) + '" fill="none" stroke="' + mixDet(P) + '" stroke-opacity="' + L.op + '" stroke-width="' + n(w) + '" stroke-linecap="butt"/>';
      });
    }
    if (V.ruler && px >= 24) {
      var L0 = Y.m + Y.ts * 0.12, L1 = Y.m + Y.ts * 0.88, x0 = Math.round(Y.m + Y.ts * 0.07) + 0.5, y0 = Math.round(Y.m + Y.ts * 0.93) - 0.5, tl = Math.max(1, Math.round(Y.ts * 0.05));
      var d = 'M' + n(x0) + ',' + n(L0) + 'V' + n(L1) + 'M' + n(L0) + ',' + n(y0) + 'H' + n(L1);
      for (var i = 1; i < 4; i++) { var t = Math.round(L0 + (L1 - L0) * i / 4) + 0.5; d += 'M' + n(x0) + ',' + n(t) + 'h' + tl + 'M' + n(t) + ',' + n(y0) + 'v' + (-tl); }
      g += '<path d="' + d + '" fill="none" stroke="' + P.det + '" stroke-opacity="0.6" stroke-width="1"/>';
    }
    g += '<g mask="url(#' + id + 'h)">' + Y.rings.map(function (r) { return '<ellipse cx="' + n(nx) + '" cy="' + n(ny) + '" rx="' + n(r.rx) + '" ry="' + n(r.ry) + '" transform="rotate(' + r.deg + ' ' + n(nx) + ' ' + n(ny) + ')" fill="none" stroke="' + P.ring + '" stroke-opacity="' + V.ringOp + '" stroke-width="' + n(S.rw) + '"/>'; }).join('') + '</g>';
    g += '<circle cx="' + n(nx) + '" cy="' + n(ny) + '" r="' + n(S.nd / 2) + '" fill="' + P.nuc + '"/><circle cx="' + n(Y.ex) + '" cy="' + n(Y.ey) + '" r="' + n(S.ed / 2) + '" fill="' + P.el + '"/>';
    body += '<g clip-path="url(#' + id + 'c)">' + g + '</g>';
    if (P.rim && S.rim) body += '<path d="' + tile + '" fill="none" stroke="' + P.rim + '" stroke-opacity="0.35" stroke-width="' + n(S.rim * 2) + '" clip-path="url(#' + id + 'c)"/>';
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + px + '" height="' + px + '" viewBox="0 0 ' + px + ' ' + px + '"><defs>' + defs + '</defs>' + body + '</svg>';
  }
  /* on the navy tile the field colour is lifted a little: a 1 px line at #6096FF over navy is too dim at 16 px */
  function mixDet(P) { return P.glow ? '#7AA8FF' : P.det; }

  /* one-colour mark for a menu bar or tray (no tile): rings, nucleus as a filled dot, electron, the outer field arc */
  function template(sid, px, ink) {
    var V = VARIANTS[sid], Y = layout(V, px, 'full', {}), S = Y.S, k = Y.k, nx = Y.nx, ny = Y.ny, id = 'tp' + (++uid) + '_';
    var g = '<mask id="' + id + 'h" maskUnits="userSpaceOnUse" x="0" y="0" width="' + px + '" height="' + px + '"><rect width="' + px + '" height="' + px + '" fill="#fff"/><circle cx="' + n(Y.ex) + '" cy="' + n(Y.ey) + '" r="' + n(S.ed / 2 + S.eg) + '" fill="#000"/><circle cx="' + n(nx) + '" cy="' + n(ny) + '" r="' + n(S.nd / 2 + S.eg) + '" fill="#000"/></mask>';
    var body = '';
    if (!V.ic4) { var L = V.field[Y.band][0], Rs = S.nd / 2 + Math.max(1.5, px / 16); body += '<path d="' + fieldLine([nx, ny], L.L * k, V.tilt, Rs, 1) + fieldLine([nx, ny], L.L * k, V.tilt, Rs, -1) + '" fill="none" stroke="' + ink + '" stroke-opacity="0.55" stroke-width="1"/>'; }
    body += Y.rings.map(function (r) { return '<ellipse cx="' + n(nx) + '" cy="' + n(ny) + '" rx="' + n(r.rx) + '" ry="' + n(r.ry) + '" transform="rotate(' + r.deg + ' ' + n(nx) + ' ' + n(ny) + ')" fill="none" stroke="' + ink + '" stroke-width="' + n(S.rw) + '"/>'; }).join('');
    body = '<g mask="url(#' + id + 'h)">' + body + '</g><circle cx="' + n(nx) + '" cy="' + n(ny) + '" r="' + n(S.nd / 2) + '" fill="' + ink + '"/><circle cx="' + n(Y.ex) + '" cy="' + n(Y.ey) + '" r="' + n(S.ed / 2) + '" fill="' + ink + '"/>';
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + px + '" height="' + px + '" viewBox="0 0 ' + px + ' ' + px + '"><defs>' + g + '</defs><clipPath id="' + id + 'c"><rect width="' + px + '" height="' + px + '"/></clipPath><g clip-path="url(#' + id + 'c)">' + body + '</g></svg>';
  }

  var RECS = [{ s: 'S1', why: 'Thin rings, one clean field arc: keeps IC4\'s crisp atom and adds J9\'s field where it reads. At 16 px it is the calmest of the four.' }];
  var API = { VARIANTS: VARIANTS, IDS: ['S1', 'S2', 'S3', 'S4'], smallSvg: smallSvg, template: template, SPEC: SPEC, RECS: RECS };
  root.AL4S = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
