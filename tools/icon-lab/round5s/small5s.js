/* AudioLab app icon, task IC9: small masters for 16, 20, 24 and 32 pt, at 1x and 2x.

   The user (28 Nov 2026, 01:20 Brussels): "For the zoomed ones: let's try MS2. I want the lit one, not the flat one.
   And let's try an M5c, the actual one, the non-flat one".

   MS2a..MS2d: round 5's MS2 (tools/icon-lab/round5/small5.js) developed. The zoomed crop: the nucleus low left of
     centre, the field axis tilted, the outer orbit cut by the tile edges. Always a lit nucleus (a sphere lit from the
     top left) with a glow; never the flat disc.
   MC1..MC3: a small M5c (round 5's 'Glowing core'): the whole picture, not a crop. The nucleus in the middle, the
     half orbits left and right round it (r = L sin^2(theta), tilt 10 as the big icon), transparent so they brighten
     where they gather at the poles, the electron on the right, the lit nucleus with a wide glow. The detail steps
     down per size: one orbit pair at 16, two from 20 or 24, three at 32 (MC1).

   Every size is its own master. A table per design gives, for each point size 16, 20, 24, 32, the orbits (their
   reach L in the 1024 frame), the nucleus and electron diameters in whole pixels, and the line width. The 2x
   picture of a point size keeps that size's detail (16 pt at 2x is the 16 drawing with twice the pixels, not the
   32 drawing), with lines a little lighter than doubled. Pixel fitting: nucleus and electron centres on a pixel
   centre (odd diameter) or a pixel corner (even), each orbit scaled a hair so its outermost point on the tilted
   equator lands on the pixel grid for its line width.

   smallSvg(id, pid, pt, scale, frame) -> SVG string, viewBox 0 0 px px with px = pt * scale.
     frame: 'full' (Windows .ico, favicon, Finder list) or 'mac' (the Apple grid margin of the icns small slots) */
(function (root) {
  'use strict';
  var PAL = (root.AL5 || (typeof require === 'function' ? require('../round5/icons5.js') : null)).PAL;

  /* base per point size (1x): nucleus and electron diameters, line width, the electron's cut-out, the rim */
  var BASE = {
    16: { nd: 6, ed: 3, rw: 1.0, eg: 0.9, rim: 0.7 },
    20: { nd: 7, ed: 4, rw: 1.1, eg: 1.0, rim: 0.8 },
    24: { nd: 8, ed: 4, rw: 1.2, eg: 1.0, rim: 0.9 },
    32: { nd: 10, ed: 5, rw: 1.4, eg: 1.2, rim: 1.0 }
  };
  var PTS = [16, 20, 24, 32];

  /* designs. N: nucleus in the 1024 frame; tilt; orb[pt]: orbit reaches in the 1024 frame; op: orbit opacity;
     end: where each half orbit stops near the nucleus (share of its reach; smaller = gathers closer, brighter poles);
     nd/ed: extra pixels on the nucleus / electron; rwK: line weight factor; glow: nucleus glow strength, glowR:
     its reach in nucleus radii; elOrb/elTh: the electron's orbit and angle from the axis (moved out until it clears
     the nucleus by a pixel); elGlow; edge: a one-pixel light edge along the top from 24 pt; hair[pt]: hairline field
     lines in the field colour */
  var D = {
    MS2a: { fam: 'MS2', name: 'Lit, electron clear', N: [360, 640], tilt: 24,
      orb: { 16: [520, 1000], 20: [520, 980], 24: [500, 960], 32: [500, 960] }, op: 0.92, end: 0.24, nd: 1, glow: 0.32, glowR: 1.9,
      elOrb: 0, elTh: 50,
      note: 'Round 5\'s MS2 with one fix: at 16 and 20 px its electron touched the nucleus, so here it slides out along the inner orbit until a pixel of navy shows between them. Nucleus a pixel bigger than MS1, lit from the top left, a soft glow. The closest to MS2 as you saw it.' },
    MS2b: { fam: 'MS2', name: 'Lit, stronger', N: [350, 650], tilt: 24, star: true,
      orb: { 16: [540, 1020], 20: [530, 1000], 24: [510, 980], 32: [500, 960] }, op: 0.97, end: 0.24, nd: 2, rwK: 1.15, glow: 0.38, glowR: 2.0,
      elOrb: 0, elTh: 55, elGlow: true, edge: true,
      note: 'What the research says to do as an icon shrinks: heavier lines and more contrast. The orbits a step heavier and nearly opaque, the nucleus two pixels bigger than MS1 with a stronger glow, the electron lit with a small glow from 24 px, and from 24 px the one-pixel light edge along the top (the glass edge of K5a and M5d, reduced). Reads best on a light desktop and in the Finder list.' },
    MS2c: { fam: 'MS2', name: 'Glowing poles', N: [360, 640], tilt: 24,
      orb: { 16: [520, 1000], 20: [520, 980], 24: [500, 960], 32: [490, 940] }, op: 0.74, end: 0.12, nd: 1, glow: 0.55, glowR: 2.4,
      elOrb: 0, elTh: 52, elGlow: true,
      note: 'M5c\'s idea inside the zoom: the orbits see-through (74 %) and running in closer to the nucleus, so where they gather at the poles they brighten, and the strongest glow of the four. The softest; the glow carries it at 32 and up, at 16 it is a little dimmer than MS2b.' },
    MS2d: { fam: 'MS2', name: 'Three arcs at 32', N: [370, 630], tilt: 22,
      orb: { 16: [520, 1000], 20: [520, 980], 24: [440, 720, 1060], 32: [400, 650, 950] }, op: 0.9, end: 0.24, nd: 1, glow: 0.38, glowR: 2,
      elOrb: 0, elTh: 52, hair: { 32: [1300] }, edge: true,
      note: 'Two orbits at 16 and 20 px as MS2a; at 24 a third arc comes in, at 32 a hairline field line past the edge as well, so the step up to the 64 px icon (M5d\'s fine lines to the edge) is smaller. Light top edge from 24 px.' },

    MC1: { fam: 'MC', name: 'Whole, simplified', N: [476, 530], tilt: 10, star: true,
      orb: { 16: [470], 20: [330, 480], 24: [320, 470], 32: [280, 390, 490] }, op: 0.8, end: 0.2, nd: 0, glow: 0.36, glowR: 2.4,
      elOrb: -1, elTh: 40, elGlow: true, edge: true,
      note: 'The actual M5c, whole: the nucleus near the middle (a hair left, to leave the electron room inside the tile), the half orbits left and right, tilt 10°, the electron on the right. Only the amount of detail changes with the size: one pair of orbits at 16 px, two at 20 and 24, three at 32 as in the big icon. Orbits at 80 % so they brighten at the poles, the lit nucleus with M5c\'s wide glow, the light top edge from 24 px.' },
    MC2: { fam: 'MC', name: 'Big glowing core', N: [470, 534], tilt: 10,
      orb: { 16: [500], 20: [500], 24: [380, 510], 32: [350, 500] }, op: 0.76, end: 0.16, nd: 2, glow: 0.46, glowR: 2.4, rwK: 1.1,
      elOrb: -1, elTh: 40, elGlow: true,
      note: 'The glowing core first: a nucleus two pixels bigger with the strongest glow, one pair of orbits up to 20 px and two from 24, gathering close to the nucleus so the poles shine. At 16 px it is a bright sun with one orbit, the clearest silhouette of the three.' },
    MC3: { fam: 'MC', name: 'Closer whole', N: [486, 534], tilt: 10,
      orb: { 16: [560, 900], 20: [540, 880], 24: [500, 800], 32: [420, 640, 930] }, op: 0.82, end: 0.2, nd: 1, glow: 0.45, glowR: 2.4,
      elOrb: 0, elTh: 50, elGlow: true, edge: true,
      note: 'M5c a quarter closer: still whole round a nucleus near the middle, but the outer orbit runs out past the left and right edges, the way M5d\'s fine lines run to the edge. Two orbits at every size, three at 32. Between MC1 and the MS2 zoom.' }
  };
  var MS = ['MS2a', 'MS2b', 'MS2c', 'MS2d'], MC = ['MC1', 'MC2', 'MC3'], IDS = MS.concat(MC);

  var n = function (v) { return (Math.round(v * 1000) / 1000).toString(); };
  function squircle(x, y, s) { var N = 96, a = s / 2, p = []; for (var i = 0; i < N; i++) { var t = i / N * Math.PI * 2, c = Math.cos(t), si = Math.sin(t); p.push(n(x + a + a * Math.sign(c) * Math.pow(Math.abs(c), 0.4)) + ',' + n(y + a + a * Math.sign(si) * Math.pow(Math.abs(si), 0.4))); } return 'M' + p.join('L') + 'Z'; }
  function fpt(c, L, tilt, th, side) { var a = tilt * Math.PI / 180, r = L * Math.pow(Math.sin(th), 2), x = side * r * Math.sin(th), y = -r * Math.cos(th); return [c[0] + x * Math.cos(a) - y * Math.sin(a), c[1] + x * Math.sin(a) + y * Math.cos(a)]; }
  function half(c, L, tilt, Rs, side) { var t0 = Math.asin(Math.min(1, Math.sqrt(Rs / L))), pts = []; for (var i = 0; i <= 72; i++) pts.push(fpt(c, L, tilt, t0 + (Math.PI - 2 * t0) * i / 72, side)); return 'M' + pts.map(function (p) { return n(p[0]) + ',' + n(p[1]); }).join('L'); }
  var odd = function (v) { return Math.round(v) % 2 === 1; }, snap = function (v, isOdd) { return isOdd ? Math.floor(v) + 0.5 : Math.round(v); };
  function mix(a, b, t) { var h = function (x) { x = x.replace('#', ''); return [0, 2, 4].map(function (i) { return parseInt(x.substr(i, 2), 16); }); }, x = h(a), y = h(b); return '#' + [0, 1, 2].map(function (i) { var v = Math.round(x[i] + (y[i] - x[i]) * t); return (v < 16 ? '0' : '') + v.toString(16); }).join(''); }
  function lit(id, P, col, cx, cy, r) { return '<radialGradient id="' + id + '" gradientUnits="userSpaceOnUse" cx="' + n(cx - r * 0.38) + '" cy="' + n(cy - r * 0.42) + '" r="' + n(r * 1.5) + '"><stop offset="0" stop-color="' + mix(col, '#FFFFFF', 0.6) + '"/><stop offset="0.5" stop-color="' + col + '"/><stop offset="1" stop-color="' + mix(col, P.bg[1], 0.3) + '"/></radialGradient>'; }
  function glow(id, col, cx, cy, r0, r1, op) { return '<radialGradient id="' + id + '" gradientUnits="userSpaceOnUse" cx="' + n(cx) + '" cy="' + n(cy) + '" r="' + n(r1) + '"><stop offset="' + n(r0 / r1) + '" stop-color="' + col + '" stop-opacity="' + op + '"/><stop offset="1" stop-color="' + col + '" stop-opacity="0"/></radialGradient>'; }
  var uid = 0;

  function smallSvg(sid, pid, pt, scale, frame) {
    var V = D[sid], P = PAL[pid], B = BASE[pt], s = scale || 1, px = pt * s, id = 'q' + (++uid) + '_';
    var m = frame === 'mac' ? (pt <= 16 ? 1 : Math.round(pt * 100 / 1024)) * s : 0, ts = px - 2 * m, k = ts / 1024;
    var tile = frame === 'mac' ? squircle(m, m, ts) : squircle(0, 0, px);
    var nd = (B.nd + (V.nd || 0)) * s, ed = B.ed * s, rw = B.rw * (V.rwK || 1) * (s === 2 ? 1.75 : 1), eg = B.eg * s;
    var rwOdd = Math.round(rw) % 2 === 1;
    var nx = snap(m + V.N[0] * k, odd(nd)), ny = snap(m + V.N[1] * k, odd(nd)), c = [nx, ny];
    var a = V.tilt * Math.PI / 180, Rs = nd / 2 + Math.max(1, 1.2 * s);
    var fit = function (L) { var e = L * k * Math.cos(a); return L * k * ((snap(nx + e, rwOdd) - nx) / e); };
    var orbs = V.orb[pt].map(fit);
    /* the electron: on its orbit at elTh, moved toward the equator until a pixel (2 at 2x) clears the nucleus */
    var eo = orbs[V.elOrb < 0 ? orbs.length + V.elOrb : V.elOrb], th = V.elTh, ep, need = nd / 2 + ed / 2 + 1.2 * s;
    /* first angle from elTh toward the equator that clears the nucleus and keeps the electron inside the tile by a
       pixel; if none does both, the angle inside the tile that clears the nucleus most */
    var lo = m + ed / 2 + 1.5 * s, hi = px - m - ed / 2 - 1.5 * s, best = null, bd = -1;
    for (; th <= 96; th += 2) { var q = fpt(c, eo, V.tilt, th * Math.PI / 180, 1), dq = Math.hypot(q[0] - nx, q[1] - ny), inside = q[0] >= lo && q[0] <= hi && q[1] >= lo && q[1] <= hi;
      if (inside && dq >= need) { best = q; break; } if (inside && dq > bd) { bd = dq; best = q; } }
    ep = best || fpt(c, eo, V.tilt, V.elTh * Math.PI / 180, 1);
    var ex = snap(ep[0], odd(ed)), ey = snap(ep[1], odd(ed));
    var defs = '', g = '';
    ((V.hair && V.hair[pt]) || []).forEach(function (L) { var Lf = fit(L); g += '<path d="' + half(c, Lf, V.tilt, Rs, 1) + half(c, Lf, V.tilt, Rs, -1) + '" fill="none" stroke="' + (P.glow ? '#7AA8FF' : P.det) + '" stroke-opacity="0.6" stroke-width="' + n(s === 2 ? 1.6 : 1) + '"/>'; });
    /* at 16 and 20 pt a one-pixel line at 75 % turns grey: the see-through orbits go nearly opaque there */
    var op = pt <= 20 ? Math.min(0.97, V.op + 0.16) : V.op, og = '';
    orbs.forEach(function (L) { [1, -1].forEach(function (sd) { og += '<path d="' + half(c, L, V.tilt, Math.max(Rs, (V.end || 0.24) * L), sd) + '" fill="none" stroke="' + P.ring + '" stroke-opacity="' + op + '" stroke-width="' + n(rw) + '" stroke-linecap="round"/>'; }); });
    g += '<g mask="url(#' + id + 'h)">' + og + '</g>';
    defs += '<linearGradient id="' + id + 'bg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="' + P.bg[0] + '"/><stop offset="1" stop-color="' + P.bg[1] + '"/></linearGradient>' +
      '<clipPath id="' + id + 'c"><path d="' + tile + '"/></clipPath>' +
      (P.glow ? '<radialGradient id="' + id + 'gl" gradientUnits="userSpaceOnUse" cx="' + n(nx) + '" cy="' + n(ny) + '" r="' + n(ts * 0.6) + '"><stop offset="0" stop-color="' + P.glow + '" stop-opacity="0.24"/><stop offset="1" stop-color="' + P.glow + '" stop-opacity="0"/></radialGradient>' : '') +
      '<mask id="' + id + 'h" maskUnits="userSpaceOnUse" x="0" y="0" width="' + px + '" height="' + px + '"><rect width="' + px + '" height="' + px + '" fill="#fff"/><circle cx="' + n(ex) + '" cy="' + n(ey) + '" r="' + n(ed / 2 + eg) + '" fill="#000"/></mask>';
    /* glow, lit nucleus (always lit: the user asked for the lit one, never flat), electron */
    var gr = nd / 2 * (V.glowR || 2); defs += glow(id + 'ng', P.glow ? mix(P.nuc, '#FFFFFF', 0.1) : P.nuc, nx, ny, nd / 2, gr, V.glow * (P.glow ? 1 : 0.6));
    g += '<circle cx="' + n(nx) + '" cy="' + n(ny) + '" r="' + n(gr) + '" fill="url(#' + id + 'ng)"/>';
    if (V.elGlow && pt * s >= 24) { var er = ed / 2 + Math.max(1.5, ed * 0.7); defs += glow(id + 'eg', P.el, ex, ey, ed / 2, er, 0.42); g += '<circle cx="' + n(ex) + '" cy="' + n(ey) + '" r="' + n(er) + '" fill="url(#' + id + 'eg)"/>'; }
    defs += lit(id + 'nl', P, P.nuc, nx, ny, nd / 2);
    var elLit = pt * s >= 20; if (elLit) defs += lit(id + 'el', P, P.el, ex, ey, ed / 2);
    g += '<circle cx="' + n(nx) + '" cy="' + n(ny) + '" r="' + n(nd / 2) + '" fill="url(#' + id + 'nl)"/><circle cx="' + n(ex) + '" cy="' + n(ey) + '" r="' + n(ed / 2) + '" fill="' + (elLit ? 'url(#' + id + 'el)' : P.el) + '"/>';
    var body = '<path d="' + tile + '" fill="url(#' + id + 'bg)"/>' + (P.glow ? '<rect width="' + px + '" height="' + px + '" fill="url(#' + id + 'gl)" clip-path="url(#' + id + 'c)"/>' : '');
    body += '<g clip-path="url(#' + id + 'c)">' + g + '</g>';
    if (V.edge && pt >= 24) {
      defs += '<linearGradient id="' + id + 'ed" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="' + (P.glow ? 0.6 : 0.9) + '"/><stop offset="0.25" stop-color="#fff" stop-opacity="0.08"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>';
      body += '<path d="' + tile + '" fill="none" stroke="url(#' + id + 'ed)" stroke-width="' + n(2 * s) + '" clip-path="url(#' + id + 'c)"/>';
    } else if (P.rim) body += '<path d="' + tile + '" fill="none" stroke="' + P.rim + '" stroke-opacity="0.35" stroke-width="' + n(B.rim * 2 * s) + '" clip-path="url(#' + id + 'c)"/>';
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + px + '" height="' + px + '" viewBox="0 0 ' + px + ' ' + px + '"><defs>' + defs + '</defs>' + body + '</svg>';
  }

  /* a menu bar template glyph (black on transparent, macOS tints it): only if AudioLab ever adds a menu bar item */
  function templateSvg(pt, s) {
    var px = pt * s, c = px / 2, r = 2.5 * s, w = 1.2 * s, L = 7.2 * s, o = '';
    [1, -1].forEach(function (sd) { o += '<path d="' + half([c, c], L, 10, Math.max(r + 1.3 * s, 0.24 * L), sd) + '" fill="none" stroke="#000" stroke-width="' + n(w) + '" stroke-linecap="round"/>'; });
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + px + '" height="' + px + '" viewBox="0 0 ' + px + ' ' + px + '">' + o + '<circle cx="' + n(c) + '" cy="' + n(c) + '" r="' + n(r) + '" fill="#000"/></svg>';
  }

  var API = { D: D, MS: MS, MC: MC, IDS: IDS, PTS: PTS, BASE: BASE, smallSvg: smallSvg, templateSvg: templateSvg };
  root.AL5SS = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
