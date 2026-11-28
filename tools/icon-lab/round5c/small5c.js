/* AudioLab app icon, round 5c (task IC8): zoomed-in small versions of the Earth and Moon designs, for 32 px and below.

   As round 5's MS (tools/icon-lab/round5/small5.js): zoomed in, the Earth low left of centre, the field axis tilted,
   the outer line run out past the tile edge, the Moon top right; drawn at its own pixel size, never shrunk. The
   Earth and the Moon have whole-pixel diameters with their centres on the pixel grid; line widths are in device
   pixels. The lines keep a gentle taper (the near half a little wider and brighter), the far halves still pass
   behind the Earth.

   ES1 (E1, E3): the dipole, two lines, the Moon on the outer one.
   ES2 (E7):     ES1 lit by the Sun from the left: day and night halves on both.
   ES3 (E2, E5, E6): the Moon's orbit as the white ribbon round the Earth, one blue field line behind.
   ES4 (E4, E8): the magnetosphere: the day side closed loops, the stretched tail to the right edge, the Moon in it.

   smallSvg(sid, pid, px, frame, o) -> SVG string, viewBox 0 0 px px. o.pt: the point size when px is its 2x picture. */
(function (root) {
  'use strict';
  var A = root.AL5C || require('./icons5c.js');
  var PAL = A.PAL, X = A.X, squircle = (root.AL5 || require('../round5/icons5.js')).squircle;

  /* per point size: Earth and Moon diameters (px at 1x), bold and fine line widths (px) */
  var SPEC = {
    16: { nd: 5, md: 3, w: 1.05, wf: 0.8 }, 20: { nd: 6, md: 3, w: 1.1, wf: 0.8 }, 24: { nd: 7, md: 4, w: 1.2, wf: 0.85 },
    32: { nd: 9, md: 5, w: 1.45, wf: 0.9 }, 48: { nd: 13, md: 7, w: 1.9, wf: 1.0 }, 64: { nd: 17, md: 9, w: 2.4, wf: 1.1 }
  };
  function spec(pt) { var ks = Object.keys(SPEC).map(Number), b = ks[0]; ks.forEach(function (k) { if (Math.abs(k - pt) < Math.abs(b - pt)) b = k; }); var S = SPEC[b], r = pt / b; return b === pt ? S : { nd: Math.round(S.nd * r), md: Math.max(3, Math.round(S.md * r)), w: S.w * Math.sqrt(r), wf: S.wf }; }
  function snap(v, d) { var o = d % 2 ? 0.5 : 0; return Math.round(v - o) + o; }

  var VARIANTS = {
    ES1: { fam: 'E1 E3', name: 'Dipole, zoomed', note: 'E1 zoomed in: the Earth low left, the axis tilted 18°, two field lines in white (the outer runs out past the edges), the Moon on the outer line at the top right. Lit Earth, a soft glow.' },
    ES2: { fam: 'E7', name: 'Day and night', note: 'ES1 lit by the Sun from the left: the Earth and the Moon each half lit, the same phase. At 16 px the night halves still keep a little colour so both discs read.' },
    ES3: { fam: 'E2 E5 E6', name: 'Orbit', note: 'The Moon\'s orbit as the white ribbon round the Earth, tilted, the far half behind the planet, one blue field line pair behind it. The Moon on the orbit at the right.' },
    ES4: { fam: 'E4 E8', name: 'Tail', note: 'The magnetosphere zoomed: the Earth at the left, two closed loops on the day side, the night side stretched into a tail that runs out of the right edge, the Moon in it.' }
  };
  var IDS = ['ES1', 'ES2', 'ES3', 'ES4'];

  function build(sid, P, T, K, sc) {
    /* T: tile size in px; K: spec at 1x; sc: 1 or 2 (the 2x picture of a point size) */
    var nd = K.nd * sc, md = K.md * sc, w = K.w * sc * (sc > 1 ? 0.92 : 1), wf = K.wf * sc * (sc > 1 ? 0.9 : 1), nr = nd / 2;
    var base = { nr: nr, e: 10, phi0: 16, r0: 1.45, Z: T * 0.35, taper: 0.3, fade: 0.3, plain: true, stubs: false, shadow: false, glow: 2.1, glowOp: 0.8, ffGap: Math.max(1, nr * 0.25), ffW: Math.max(2, nr * 0.9) };
    if (sid === 'ES1' || sid === 'ES2') {
      var c = [snap(T * 0.4, nd), snap(T * 0.6, nd)];
      var S = X(base, { c: c, tilt: 18, bold: [{ L: T * 0.3 / nr, w: w }, { L: T * 0.62 / nr, w: w }], fine: T >= 40 ? [{ L: T * 0.95 / nr, w: wf, op: 0.6 }] : [],
        moon: { mode: 'line', li: 1, th: 52, r: md / 2, snap: md % 2 ? 0.5 : 0 }, halo: md / 2 + Math.max(1, 1.2 * sc) });
      if (sid === 'ES2') S = X(S, { sun: { beta: 10, soft: 0.04 }, glow: 1.8, glowOp: 0.6 });
      return S;
    }
    if (sid === 'ES3') {
      var c3 = [snap(T * 0.44, nd), snap(T * 0.54, nd)];
      return X(base, { c: c3, nr: nr * 1.1, earthK: 1 / 1.1 * 1, tilt: 14, bold: [], fine: [{ L: T * 0.5 / (nr * 1.1), w: wf, op: 0.85 }],
        moon: { mode: 'orbit', R: T * 0.42, t: -18, inc: 5, eo: 27, w: w * 1.15, r: md / 2, col: 'ring' }, halo: md / 2 + Math.max(1, 1.2 * sc), taper: 0.45 });
    }
    /* ES4: the tail */
    var c4 = [snap(T * 0.36, nd), snap(T * 0.5, nd)], u = T / 16;
    return X(base, { c: c4, tilt: 10, e: 4, phi0: 0, taper: 0,
      ms: { Lmax: 3.6, sq: 0.1, st: 0.09, thin: 0.35 },
      bold: [{ L: 2.0 * u * 2.5 / nr, w: w }, { L: 3.4 * u * 2.5 / nr, w: w }],
      open: T >= 24 ? [{ th: 22, h: 2.7 * u * 2.5 / nr, x1: 3.2 * u * 2.5 / nr, w: wf, op: 0.8 }] : [{ th: 22, h: 2.8 * u * 2.5 / nr, x1: 3.2 * u * 2.5 / nr, w: wf, op: 0.85 }],
      moon: { mode: 'xy', x: snap(T * 0.8, md), y: snap(T * 0.5, md), r: md / 2 }, halo: md / 2 + Math.max(1, 1.2 * sc), sun: { beta: 10, soft: 0.04 }, glow: 1.6, glowOp: 0.6 });
  }

  var uid = 0;
  function smallSvg(sid, pid, px, frame, o) {
    o = o || {}; var P = PAL[pid], pt = o.pt || px, sc = px / pt, K = spec(pt);
    var m = frame === 'mac' ? Math.round(px * 100 / 1024 * (px <= 32 ? 0.75 : 1)) : 0, T = px - 2 * m;
    var U = { id: 's' + (++uid).toString(36) + '_', defs: {}, n: 0, lx: -0.35, ly: -0.75 };
    var body = A.scene(build(sid, P, T, K, sc), P, U);
    var id = U.id, tile = squircle(m, m, T, 5), rimW = Math.max(1, sc);
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + px + '" height="' + px + '" viewBox="0 0 ' + px + ' ' + px + '"><defs>' +
      '<linearGradient id="' + id + 'bg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="' + P.bg[0] + '"/><stop offset="1" stop-color="' + P.bg[1] + '"/></linearGradient>' +
      '<clipPath id="' + id + 'clip"><path d="' + tile + '"/></clipPath>' + Object.keys(U.defs).map(function (k) { return U.defs[k]; }).join('') + '</defs>' +
      '<path d="' + tile + '" fill="url(#' + id + 'bg)"/><g clip-path="url(#' + id + 'clip)"><g transform="translate(' + m + ' ' + m + ')">' + body + '</g></g>' +
      '<path d="' + tile + '" fill="none" stroke="' + P.rim + '" stroke-opacity="' + (P.glow ? 0.45 : 0.3) + '" stroke-width="' + rimW + '" clip-path="url(#' + id + 'clip)"/></svg>';
  }
  var RECS = [
    { s: 'ES1', why: 'The small version of E1 and E3: two lines and the Moon read from 16 px.' },
    { s: 'ES2', why: 'The small version of E7: the day and night halves still read at 32 px and give the planet away.' }
  ];
  var API = { VARIANTS: VARIANTS, IDS: IDS, RECS: RECS, smallSvg: smallSvg, SPEC: SPEC };
  root.AL5CS = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
