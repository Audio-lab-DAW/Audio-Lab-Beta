/* AudioLab app icon, round 2 (task IC2): science-style designs and colour palettes.
   One drawing module used by the pick page (browser) and by render.js (Node).
   Everything is drawn in code as SVG. The atom (three tapered rings, nucleus,
   satellite electron) is the shipped geometry from desktop/icon-assets, read into
   geom.json by extract_geom.py, so every design carries the exact AudioLab mark.

   svg(designId, paletteId, size, opts) -> SVG string, viewBox 0 0 1024 1024.
     size  : the pixel size it will be shown at; picks the ring tier and how much
             fine detail is drawn (>=128 full, 48..64 bold only, <=32 the small master).
     opts.frame : 'mac' (macOS 26 grid: 824 px squircle tile, 100 px margin, shadow)
                  'full' (the tile fills the canvas: Windows, in-app picker, favicons)
     opts.style : 'default' | 'dark' | 'tinted' | 'clear'  (macOS 26 icon styles;
                  tinted and clear are approximations of what the system does) */
(function (root) {
  'use strict';
  var GEOM = root.AL2_GEOM || (typeof require === 'function' ? require('./geom.json') : null);

  /* ---------- palettes ---------- */
  var PALETTES = [
    { id: 'P0', name: 'Ocean Yellow', from: "Today's logo (reference)", bg: ['#1450A8', '#1450A8'], ring: '#FFFFFF', nuc: '#FFD23A', el: '#FFD23A', det: '#BFD6FF', glow: null, rim: null },
    { id: 'P1', name: 'Ocean chart', from: "Today's blue, deepened, with the splash's cyan", bg: ['#1C62C8', '#0B2F6E'], ring: '#FFFFFF', nuc: '#FFD23A', el: '#FFD23A', det: '#9FC8FF', glow: '#4CC9F0', rim: null },
    { id: 'P2', name: 'Orbit night', from: 'Splash S2, moons in resonance', bg: ['#132044', '#070910'], ring: '#EAF1FF', nuc: '#FFC43C', el: '#4CC9F0', det: '#6096FF', glow: '#6096FF', rim: '#6096FF' },
    { id: 'P3', name: 'Dipole cyan', from: 'Splash S1, dipole field (line and particle colours)', bg: ['#0A3049', '#03111C'], ring: '#E6F7FF', nuc: '#FFC43C', el: '#4CC9F0', det: '#4CC9F0', glow: '#4CC9F0', rim: '#4CC9F0' },
    { id: 'P4', name: 'Harmonograph lilac', from: 'Splash S5, harmonograph (periwinkle to lilac)', bg: ['#1A1E48', '#07080F'], ring: '#EEF0FF', nuc: '#A99BFF', el: '#78AAFF', det: '#A99BFF', glow: '#A99BFF', rim: '#A99BFF' },
    { id: 'P5', name: 'Chart amber', from: 'Splash S7, orbit chart', bg: ['#1C2036', '#07080D'], ring: '#F5F1E8', nuc: '#FFB627', el: '#FFD27A', det: '#FFB627', glow: '#FFB627', rim: '#FFB627' },
    { id: 'P6', name: 'Spectrogram', from: 'Splash S6, spectrogram heat scale', bg: ['#173A82', '#05070D'], ring: '#EAF6FF', nuc: '#FFD23A', el: '#3FB8E8', det: '#3FB8E8', glow: '#3FB8E8', rim: '#3FB8E8' },
    { id: 'P7', name: 'Van Allen', from: 'About window: Earth and the radiation belts', bg: ['#0F1A30', '#05080E'], ring: '#E8EEF9', nuc: '#F0A878', el: '#6ED0EE', det: '#7AAAFF', glow: '#6ED0EE', rim: '#7AAAFF' },
    { id: 'P8', name: 'Chart paper', from: "The orbit chart's ink colour as the ground, drawn like a printed plate", bg: ['#F7F3EA', '#E4DCCA'], ring: '#1B2340', nuc: '#C8610A', el: '#2F6BFF', det: '#1B2340', glow: null, rim: '#1B2340' }
  ];
  var PAL = {}; PALETTES.forEach(function (p) { PAL[p.id] = p; });

  /* ---------- colour helpers ---------- */
  function hex2rgb(h) { h = h.replace('#', ''); return [parseInt(h.substr(0, 2), 16), parseInt(h.substr(2, 2), 16), parseInt(h.substr(4, 2), 16)]; }
  function rgb2hex(c) { return '#' + c.map(function (v) { v = Math.max(0, Math.min(255, Math.round(v))); return (v < 16 ? '0' : '') + v.toString(16); }).join('').toUpperCase(); }
  function mix(a, b, t) { var x = hex2rgb(a), y = hex2rgb(b); return rgb2hex([0, 1, 2].map(function (i) { return x[i] + (y[i] - x[i]) * t; })); }
  function lum(h) { return hex2rgb(h).map(function (v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }).reduce(function (s, v, i) { return s + v * [0.2126, 0.7152, 0.0722][i]; }, 0); }
  function contrast(a, b) { var x = lum(a), y = lum(b); if (x < y) { var t = x; x = y; y = t; } return (x + 0.05) / (y + 0.05); }

  /* palette as macOS 26 would show it in the Tinted and Clear styles (approximation:
     the system removes the colours; brightness of each part is kept). */
  var TINT = '#5EA8FF';
  function styled(P, style) {
    if (style === 'tinted') {
      var tc = function (c) { var l = Math.sqrt(lum(c)); return mix('#0E0F12', mix(TINT, '#FFFFFF', Math.max(0, l - 0.55)), 0.35 + 0.65 * l); };
      return { id: P.id, name: P.name, bg: ['#1A1B1F', '#0C0C0E'], ring: tc(P.ring), nuc: tc(P.nuc), el: tc(P.el), det: tc(P.det), glow: null, rim: '#FFFFFF', tinted: true };
    }
    if (style === 'clear') {
      var cc = function (c) { var l = Math.sqrt(lum(c)); return mix('#7A7D86', '#FFFFFF', l); };
      return { id: P.id, name: P.name, bg: ['#DADDE4', '#9EA3AE'], ring: cc(P.ring), nuc: cc(P.nuc), el: cc(P.el), det: cc(P.det), glow: null, rim: '#FFFFFF', clear: true };
    }
    return P; /* default; dark = default because IC1 keeps the tile colour under Dark */
  }

  function checks(P) {
    var bgMid = mix(P.bg[0], P.bg[1], 0.5);
    var light = '#E6E8EE', dark = '#1C1D22';
    var edgeL = Math.max(contrast(P.bg[0], light), contrast(P.bg[1], light));
    var edgeD = Math.max(contrast(P.bg[0], dark), contrast(P.bg[1], dark));
    return {
      ring: Math.min(contrast(P.ring, P.bg[0]), contrast(P.ring, P.bg[1])),
      nuc: Math.min(contrast(P.nuc, P.bg[0]), contrast(P.nuc, P.bg[1])),
      el: Math.min(contrast(P.el, P.bg[0]), contrast(P.el, P.bg[1])),
      nucRing: contrast(P.nuc, P.ring),
      onLight: edgeL, onDark: edgeD, rim: !!P.rim, mid: bgMid
    };
  }

  /* ---------- geometry helpers ---------- */
  function f(n) { return (Math.round(n * 10) / 10).toString(); }
  function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function squircle(x, y, s, n) {
    n = n || 5; var pts = [], N = 144, a = s / 2;
    for (var i = 0; i < N; i++) {
      var t = i / N * Math.PI * 2, c = Math.cos(t), si = Math.sin(t);
      pts.push(f(x + a + a * Math.sign(c) * Math.pow(Math.abs(c), 2 / n)) + ',' + f(y + a + a * Math.sign(si) * Math.pow(Math.abs(si), 2 / n)));
    }
    return 'M' + pts.join('L') + 'Z';
  }
  var TILE = squircle(0, 0, 1024, 5);
  function line(x1, y1, x2, y2) { return 'M' + f(x1) + ',' + f(y1) + 'L' + f(x2) + ',' + f(y2); }
  function poly(pts) { return 'M' + pts.map(function (p) { return f(p[0]) + ',' + f(p[1]); }).join('L'); }
  function circ(cx, cy, r) { return 'M' + f(cx - r) + ',' + f(cy) + 'a' + f(r) + ',' + f(r) + ' 0 1,0 ' + f(2 * r) + ',0a' + f(r) + ',' + f(r) + ' 0 1,0 ' + f(-2 * r) + ',0Z'; }
  var curL = 3;
  function P_(d, stroke, sw, op, extra) { if (curL === 3 && sw < 8) { sw *= 1.45; if (op != null) op = Math.min(0.9, op * 1.25 + 0.04); } return '<path d="' + d + '" fill="none" stroke="' + stroke + '" stroke-width="' + f(sw) + '"' + (op != null ? ' stroke-opacity="' + (Math.round(op * 100) / 100) + '"' : '') + (extra || '') + '/>'; }
  function dotC(cx, cy, r, fill, op) { return '<circle cx="' + f(cx) + '" cy="' + f(cy) + '" r="' + f(r) + '" fill="' + fill + '"' + (op != null ? ' fill-opacity="' + op + '"' : '') + '/>'; }
  function ticks(cx, cy, r, n, len, every, longLen, sw) { var d = ''; for (var i = 0; i < n; i++) { var a = i / n * Math.PI * 2, L = (every && i % every === 0) ? longLen : len; d += line(cx + Math.cos(a) * r, cy + Math.sin(a) * r, cx + Math.cos(a) * (r - L), cy + Math.sin(a) * (r - L)); } return d; }

  /* ring tier for a pixel size (the shipped icons' four tiers; 'thin' = the W7 rings) */
  function tierFor(sz, thin) { if (sz >= 128) return thin ? 'W7L' : 'L'; if (sz >= 48) return thin ? 'W7M' : 'M'; if (sz >= 24) return thin ? 'W7S' : 'S'; return 'XS'; }
  function lvlFor(sz) { return sz >= 128 ? 3 : sz >= 48 ? 2 : 1; }

  /* transform that puts the mark (its own 1024 frame) at a place in the tile */
  function atomTF(g, pl) {
    if (pl.tf) return pl.tf + ' translate(' + f(g.off[0]) + ' ' + f(g.off[1]) + ')';
    return 'translate(' + f(pl.cx) + ' ' + f(pl.cy) + ') rotate(' + f(pl.rot || 0) + ') scale(' + (pl.s || 1) + ') translate(' + f(-512 + g.off[0]) + ' ' + f(-512 + g.off[1]) + ')';
  }
  /* where a point of the mark frame lands in the tile (for details that follow the atom) */
  function mapPt(pl, x, y) {
    if (pl.tf) return null;
    var s = pl.s || 1, a = (pl.rot || 0) * Math.PI / 180, dx = (x - 512) * s, dy = (y - 512) * s;
    return [pl.cx + dx * Math.cos(a) - dy * Math.sin(a), pl.cy + dx * Math.sin(a) + dy * Math.cos(a)];
  }

  function atom(U, tier, pl, P, o) {
    o = o || {}; var g = GEOM[tier], id = U.id + tier;
    if (!U.defs[id]) {
      U.defs[id] = g.rings.map(function (d, i) { return '<path id="' + id + 'r' + i + '" d="' + d + '" fill-rule="evenodd"/>'; }).join('') +
        '<mask id="' + id + 'h" maskUnits="userSpaceOnUse" x="-3000" y="-3000" width="7000" height="7000"><rect x="-3000" y="-3000" width="7000" height="7000" fill="#fff"/><circle cx="' + g.e[0] + '" cy="' + g.e[1] + '" r="' + g.halo + '" fill="#000"/></mask>';
    }
    var tf = atomTF(g, pl);
    var rings = [0, 1, 2].map(function (i) { return '<use href="#' + id + 'r' + i + '" xlink:href="#' + id + 'r' + i + '"/>'; }).join('');
    var s = '<g transform="' + tf + '">';
    if (o.knock) s += '<g mask="url(#' + id + 'h)" fill="none" stroke="' + o.knock + '" stroke-width="' + o.knockW + '" stroke-linejoin="round">' + rings + '</g>';
    s += '<g mask="url(#' + id + 'h)" fill="' + P.ring + '"' + (o.ringOp ? ' fill-opacity="' + o.ringOp + '"' : '') + '>' + rings + '</g>';
    s += dotC(512, 512, g.nr * (o.nucScale || 1), P.nuc);
    if (!o.noEl) s += dotC(g.e[0], g.e[1], g.er, P.el);
    return s + '</g>';
  }
  /* the atom's rings as a black knock-out for masks (the frame line breaking around the rings) */
  function atomKnock(U, tier, pl, w) {
    var g = GEOM[tier], id = U.id + tier; atom(U, tier, pl, { ring: '#000', nuc: '#000', el: '#000' }); /* makes sure defs exist */
    var rings = [0, 1, 2].map(function (i) { return '<use href="#' + id + 'r' + i + '" xlink:href="#' + id + 'r' + i + '"/>'; }).join('');
    return '<g transform="' + atomTF(g, pl) + '"><g fill="#000" stroke="#000" stroke-width="' + w + '" stroke-linejoin="round">' + rings + '</g>' + dotC(g.e[0], g.e[1], g.halo, '#000') + '</g>';
  }
  /* the three orbit ellipses of the mark (rx 360, ry 150 at -30, 30 and 90 degrees) */
  var ORB = [-30, 30, 90];
  function orbitPt(pl, k, t, rr) { var a = ORB[k] * Math.PI / 180, x = 360 * rr * Math.cos(t), y = 150 * rr * Math.sin(t); return mapPt(pl, 512 + x * Math.cos(a) - y * Math.sin(a), 512 + x * Math.sin(a) + y * Math.cos(a)); }

  /* dipole field line r = L sin^2(theta), both halves, around an axis tilted by tilt degrees */
  function dipole(cx, cy, L, k, tilt, rmin, win) {
    var a = tilt * Math.PI / 180, out = '', t0 = 4;
    if (rmin) t0 = Math.max(t0, Math.asin(Math.min(1, Math.sqrt(rmin / (L * k)))) * 180 / Math.PI);
    if (win) t0 = Math.max(t0, win);
    [1, -1].forEach(function (side) {
      var pts = [];
      for (var i = t0; i <= 180 - t0 + 0.01; i += 2) { var th = i * Math.PI / 180, r = L * k * Math.pow(Math.sin(th), 2); var x = side * r * Math.sin(th), y = -r * Math.cos(th); pts.push([cx + x * Math.cos(a) - y * Math.sin(a), cy + x * Math.sin(a) + y * Math.cos(a)]); }
      out += poly(pts);
    });
    return out;
  }
  function harmono(cx, cy, A, ratio, tEnd, n) {
    var pts = [], fx = ratio[0], fy = ratio[1];
    for (var i = 0; i <= n; i++) {
      var t = i / n * tEnd, d1 = Math.exp(-0.045 * t), d2 = Math.exp(-0.06 * t);
      var x = A * (0.62 * d1 * Math.sin(fx * t + 0.6) + 0.38 * d2 * Math.sin((fx * 1.004) * t + 2.1));
      var y = A * (0.62 * d1 * Math.sin(fy * t) + 0.38 * d2 * Math.sin((fy * 0.997) * t + 1.2));
      pts.push([cx + x, cy + y]);
    }
    return poly(pts);
  }
  var SPC = [[5, 7, 13], [20, 48, 110], [63, 184, 232], [255, 210, 58]];
  function heat(v, P) {
    var stops = P.id === 'P6' || P.id === 'P0' || P.id === 'P1' ? SPC : [hex2rgb(P.bg[1]), hex2rgb(mix(P.bg[0], P.det, 0.25)), hex2rgb(P.det), hex2rgb(P.nuc)];
    v = Math.max(0, Math.min(0.999, v)) * 3; var i = Math.floor(v), t = v - i, a = stops[i], b = stops[i + 1];
    return rgb2hex([0, 1, 2].map(function (j) { return a[j] + (b[j] - a[j]) * t; }));
  }

  /* ---------- the designs ----------
     each returns {under, over, atom:{tier,pl,o}} for the tile at size sz */
  var C = 512;
  var DESIGNS = [
    { id: 'I0', name: 'W7 today', note: "Today's shortcut icon (zoomed 1.5 times into the top right, tilted 6 degrees) with nothing added. The reference for each palette.", shape: 'Zoom and tilt', best: 'P0',
      draw: function (P, L, sz) { return { atom: sz >= 24 ? { tier: tierFor(sz, true), pl: W7PL } : { tier: 'XS', pl: { cx: C, cy: C } } }; } },
    { id: 'I1', name: 'Graticule', note: 'The centred atom on a faint coordinate grid with heavier axes through the nucleus, as on a plotted chart.', shape: 'Centred', best: 'P2',
      draw: function (P, L, sz) {
        var pl = { cx: C, cy: C + 4, s: 0.92 }, u = '';
        if (L === 3) { var d = ''; for (var x = 0; x <= 1024; x += 64) { d += line(x, 0, x, 1024) + line(0, x, 1024, x); } u += P_(d, P.det, 1.6, 0.16); u += P_(line(C, 0, C, 1024) + line(0, C + 4, 1024, C + 4), P.det, 3, 0.38); var t = ''; for (var k = -8; k <= 8; k++) { if (!k) continue; t += line(C + k * 64, C + 4 - 10, C + k * 64, C + 4 + 10) + line(C - 10, C + 4 + k * 64, C + 10, C + 4 + k * 64); } u += P_(t, P.det, 3, 0.45); }
        else if (L === 2) { u += P_(line(C, 0, C, 1024) + line(0, C + 4, 1024, C + 4), P.det, 10, 0.3); }
        return { under: u, atom: { tier: tierFor(sz), pl: L === 1 ? { cx: C, cy: C } : pl } };
      } },
    { id: 'I2', name: 'Orbit ticks', note: 'A tick ring around the atom like the orbit chart on the splash: 120 marks, every tenth long.', shape: 'Centred', best: 'P5',
      draw: function (P, L, sz) {
        var u = '', pl = { cx: C, cy: C, s: 0.84 };
        if (L === 3) { u += P_(ticks(C, C, 452, 120, 14, 10, 34, 0), P.det, 3.2, 0.6); u += P_(circ(C, C, 466), P.det, 1.6, 0.3); }
        else if (L === 2) { u += P_(ticks(C, C, 456, 24, 34, 0, 34), P.det, 12, 0.6); }
        return { under: u, atom: { tier: tierFor(sz), pl: L === 1 ? { cx: C, cy: C } : pl } };
      } },
    { id: 'I3', name: 'Instrument dial', note: 'A round instrument dial inside the tile: a bezel with degree graduations and the atom on the dial face. Reads as a circle even at 16 px.', shape: 'Dial inside the tile', best: 'P5',
      draw: function (P, L, sz) {
        var u = '', o = '', face = mix(P.bg[0], P.det, 0.07), R = L === 1 ? 470 : 452;
        u += dotC(C, C, R, face);
        if (L === 3) {
          u += P_(ticks(C, C, R - 18, 180, 14, 5, 28, 0), P.det, 2.4, 0.55) + P_(ticks(C, C, R - 18, 24, 46, 0, 46), P.det, 4.2, 0.75);
          u += P_(circ(C, C, R - 92), P.det, 1.6, 0.25) + P_(line(C - R + 70, C, C + R - 70, C) + line(C, C - R + 70, C, C + R - 70), P.det, 1.6, 0.18);
          o += P_(circ(C, C, R - 6), P.ring, 16, 0.92);
        } else if (L === 2) { u += P_(ticks(C, C, R - 16, 12, 40, 0, 40), P.det, 14, 0.7); o += P_(circ(C, C, R - 8), P.ring, 26, 0.92); }
        else { o += P_(circ(C, C, R - 20), P.ring, 54, 0.95); }
        return { under: u, over: o, atom: { tier: tierFor(sz), pl: { cx: C, cy: C, s: L === 1 ? 0.7 : 0.76 } } };
      } },
    { id: 'I4', name: 'Porthole', note: "A round lens in the tile; inside it the atom is zoomed in like W7, cut by the lens's edge. Outside the lens a faint grid.", shape: 'Lens inside the tile', best: 'P2',
      draw: function (P, L, sz, U) {
        var cx = 512, cy = 512, R = L === 1 ? 430 : 400, u = '', o = '';
        var cid = U.id + 'lens'; U.defs[cid] = '<clipPath id="' + cid + '"><circle cx="' + cx + '" cy="' + cy + '" r="' + R + '"/></clipPath><radialGradient id="' + cid + 'g" cx="0.42" cy="0.38" r="0.75"><stop offset="0" stop-color="' + mix(P.bg[0], P.det, 0.16) + '"/><stop offset="1" stop-color="' + P.bg[1] + '"/></radialGradient>';
        if (L === 3) { var d = ''; for (var x = 0; x <= 1024; x += 48) { d += line(x, 0, x, 1024) + line(0, x, 1024, x); } u += P_(d, P.det, 1.4, 0.14); }
        u += '<circle cx="' + cx + '" cy="' + cy + '" r="' + R + '" fill="url(#' + cid + 'g)"/>';
        var pl = L === 1 ? { cx: cx, cy: cy, s: 0.74 } : { cx: 440, cy: 592, s: 1.2, rot: -4 };
        var inner = '<g clip-path="url(#' + cid + ')">' + (L === 3 ? P_(circ(cx, cy, R - 40), P.det, 1.6, 0.25) : '') + atom(U, tierFor(sz), pl, P) + '</g>';
        var rw = L === 3 ? 30 : L === 2 ? 44 : 60;
        o += P_(circ(cx, cy, R), P.ring, rw, 0.95);
        if (L === 3) { for (var i = 0; i < 8; i++) { var a = (i + 0.5) / 8 * Math.PI * 2; o += dotC(cx + Math.cos(a) * R, cy + Math.sin(a) * R, 7, P.bg[1], 0.85); } o += P_(circ(cx, cy, R + 24), P.det, 1.6, 0.35); }
        return { under: u + inner, over: o, atom: null };
      } },
    { id: 'I5', name: 'W7 with measurements', note: 'Today\'s W7 crop and tilt, with ruler marks along the left and bottom edges and a faint grid behind, like a plate in a lab notebook.', shape: 'Zoom and tilt', best: 'P1',
      draw: function (P, L, sz) {
        var u = '';
        if (L === 3) {
          var d = ''; for (var x = 0; x <= 1024; x += 64) { d += line(x, 0, x, 1024) + line(0, x, 1024, x); } u += P_(d, P.det, 1.4, 0.13);
          var t = ''; for (var k = 4; k < 64; k++) { var y = k * 16, len = k % 8 === 0 ? 46 : k % 4 === 0 ? 30 : 16; if (y > 120 && y < 904) t += line(64, y, 64 + len, y); var xx = k * 16; if (xx > 120 && xx < 904) t += line(xx, 960, xx, 960 - len); }
          u += P_(t, P.det, 3, 0.6) + P_(line(64, 120, 64, 904) + line(120, 960, 904, 960), P.det, 3, 0.45);
        } else if (L === 2) { var t2 = ''; for (var k2 = 1; k2 < 8; k2++) { t2 += line(70, k2 * 128, 130, k2 * 128) + line(k2 * 128, 954, k2 * 128, 894); } u += P_(t2, P.det, 12, 0.5); }
        return { under: u, atom: sz >= 24 ? { tier: tierFor(sz, true), pl: W7PL } : { tier: 'XS', pl: { cx: C, cy: C } } };
      } },
    { id: 'I6', name: 'Breaking the frame', note: 'A plot frame with axis ticks inside the tile; the atom is larger than the frame and its rings cut through the frame line.', shape: 'Atom breaks the frame line', best: 'P7',
      draw: function (P, L, sz, U) {
        var pl = { cx: C, cy: C, s: 1.02 }, tier = tierFor(sz), u = '';
        if (L === 1) return { atom: { tier: tier, pl: { cx: C, cy: C } } };
        var m = U.id + 'fm', sw = L === 3 ? 7 : 18, x0 = 168, x1 = 856;
        U.defs[m] = '<mask id="' + m + '" maskUnits="userSpaceOnUse" x="0" y="0" width="1024" height="1024"><rect width="1024" height="1024" fill="#fff"/>' + atomKnock(U, tier, pl, L === 3 ? 44 : 70) + '</mask>';
        var fr = '<rect x="' + x0 + '" y="' + x0 + '" width="' + (x1 - x0) + '" height="' + (x1 - x0) + '" rx="' + (L === 3 ? 26 : 40) + '" fill="none" stroke="' + P.det + '" stroke-width="' + sw + '" stroke-opacity="0.8"/>';
        if (L === 3) { var t = '', g = ''; for (var k = 1; k < 16; k++) { var v = x0 + k * (x1 - x0) / 16, len = k % 4 === 0 ? 30 : 16; t += line(v, x1, v, x1 + len) + line(x0, v, x0 - len, v); if (k % 4 === 0) g += line(v, x0, v, x1) + line(x0, v, x1, v); } fr += P_(t, P.det, 3.2, 0.75) + P_(g, P.det, 1.6, 0.2); }
        u += '<g mask="url(#' + m + ')">' + fr + '</g>';
        return { under: u, atom: { tier: tier, pl: pl } };
      } },
    { id: 'I7', name: 'Dipole field', note: 'Field lines of a dipole (r = L sin²θ), tilted 10 degrees through the nucleus, with trapped particles on them, as on the splash.', shape: 'Centred', best: 'P3',
      draw: function (P, L, sz) {
        var u = '', k = 64, Ls = L === 3 ? [1.5, 2.2, 3.1, 4.3, 5.8, 7.8, 10.5] : [3.1, 5.8, 10.5];
        if (L >= 2) { var d = ''; Ls.forEach(function (l) { d += dipole(C, C, l, k, 10, 100); }); u += P_(d, P.det, L === 3 ? 3 : 10, L === 3 ? 0.42 : 0.38); }
        if (L === 3) { var R = rng(7); Ls.slice(1).forEach(function (l, i) { for (var j = 0; j < 2; j++) { var th = (52 + R() * 76) * Math.PI / 180, side = j ? 1 : -1, r = l * k * Math.pow(Math.sin(th), 2), x = side * r * Math.sin(th), y = -r * Math.cos(th), a = 10 * Math.PI / 180; u += dotC(C + x * Math.cos(a) - y * Math.sin(a), C + x * Math.sin(a) + y * Math.cos(a), 7, i % 2 ? P.el : P.nuc, 0.9); } }); }
        return { under: u, atom: { tier: tierFor(sz), pl: L === 1 ? { cx: C, cy: C } : { cx: C, cy: C, s: 0.9 } } };
      } },
    { id: 'I8', name: 'Harmonograph', note: 'A harmonograph trace (two slowing pendulums at 3 : 2) drawn faintly inside the tile, behind the atom.', shape: 'Centred', best: 'P4',
      draw: function (P, L, sz) {
        var u = '';
        if (L === 3) u += P_(harmono(C, C, 500, [3, 2], 70, 5200), P.det, 2.2, 0.45);
        else if (L === 2) u += P_(harmono(C, C, 440, [3, 2], 7, 500), P.det, 11, 0.42);
        return { under: u, atom: { tier: tierFor(sz), pl: L === 1 ? { cx: C, cy: C } : { cx: C, cy: C, s: 0.84 } } };
      } },
    { id: 'I9', name: 'Moons in resonance', note: 'The nucleus as the planet with three moons on orbits at 4 : 2 : 1 (radii by Kepler, 1 : 1.59 : 2.52), as on the splash.', shape: 'Centred', best: 'P2',
      draw: function (P, L, sz) {
        var u = '', o = '', r3 = 486, rs = [r3 / 2.52, r3 / 1.587, r3], ang = [200, 128, 228];
        if (L === 3) { rs.forEach(function (r, i) { u += P_(circ(C, C, r), P.det, i === 2 ? 3 : 2.2, i === 2 ? 0.5 : 0.3); }); u += P_(ticks(C, C, r3 + 18, 72, 12, 6, 24, 0), P.det, 2.4, 0.4);
          [1, 2].forEach(function (i) { var a = ang[i] * Math.PI / 180; o += dotC(C + Math.cos(a) * rs[i], C + Math.sin(a) * rs[i], i === 2 ? 30 : 22, P.el); }); }
        else if (L === 2) { u += P_(circ(C, C, r3), P.det, 12, 0.5); var a2 = ang[2] * Math.PI / 180; o += dotC(C + Math.cos(a2) * r3, C + Math.sin(a2) * r3, 44, P.el); }
        return { under: u, over: o, atom: { tier: tierFor(sz), pl: L === 1 ? { cx: C, cy: C } : { cx: C, cy: C, s: 0.82 } } };
      } },
    { id: 'I10', name: 'Spectrogram band', note: 'A band of spectrogram (the splash\'s 145 BPM pattern, kick, hats and a line) rising from the bottom of the tile; the atom above it.', shape: 'Centred, raised', best: 'P6',
      draw: function (P, L, sz, U) {
        var u = '', cols = L === 3 ? 48 : 12, rows = L === 3 ? 22 : 6, y0 = L === 3 ? 640 : 700, h = 1024 - y0, cw = 1024 / cols, rh = h / rows, R = rng(3);
        if (L === 1) return { atom: { tier: tierFor(sz), pl: { cx: C, cy: C } } };
        var gid = U.id + 'sf'; U.defs[gid] = '<linearGradient id="' + gid + '" x1="0" y1="' + y0 + '" x2="0" y2="1024" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.45" stop-color="#fff" stop-opacity="1"/></linearGradient><mask id="' + gid + 'm" maskUnits="userSpaceOnUse" x="0" y="0" width="1024" height="1024"><rect width="1024" height="1024" fill="url(#' + gid + ')"/></mask>';
        var cells = '';
        var notes = [0.30, 0.30, 0.38, 0.34, 0.30, 0.42, 0.38, 0.34], per = cols / 8;
        for (var c = 0; c < cols; c++) {
          var ph = c % per, kick = Math.exp(-ph / (per * 0.22)), hat = (ph === Math.floor(per / 2)) ? 1 : 0, note = notes[Math.floor(c / per) % 8];
          for (var r = 0; r < rows; r++) {
            var fr = (r + 0.5) / rows, v = 0.06 + R() * 0.1;
            v += kick * Math.exp(-fr / (0.16 + 0.12 * (1 - kick))) * 1.0;            /* kick: low, falling in pitch */
            if (fr > 0.55) v += (hat ? 1.3 : 0.15) * (0.6 + R() * 0.5) * (fr - 0.4);   /* hats: noisy, high */
            [1, 2, 3].forEach(function (hm, j) { var dd = Math.abs(fr - note * 0.55 * hm); if (dd < 0.6 / rows) v += (0.62 - j * 0.16) * (0.8 + 0.2 * Math.cos(ph / per * 6.28)); }); /* a line and its partials */
            cells += '<rect x="' + f(c * cw) + '" y="' + f(1024 - (r + 1) * rh) + '" width="' + f(cw + 0.6) + '" height="' + f(rh + 0.6) + '" fill="' + heat(v, P) + '"/>';
          }
        }
        u += '<g mask="url(#' + gid + 'm)" opacity="' + (P.id === 'P8' ? 0.75 : 0.9) + '">' + cells + '</g>';
        return { under: u, atom: { tier: tierFor(sz), pl: { cx: C, cy: L === 3 ? 452 : 470, s: L === 3 ? 0.8 : 0.84 } } };
      } },
    { id: 'I11', name: 'Van Allen belts', note: 'Two soft radiation belts (warm inner, cool outer) and their field lines around the atom, tilted 9.2 degrees as in the About window.', shape: 'Centred', best: 'P7',
      draw: function (P, L, sz, U) {
        var u = '', k = 60, t = -9.2;
        if (L === 1) return { atom: { tier: tierFor(sz), pl: { cx: C, cy: C } } };
        var bid = U.id + 'bb'; U.defs[bid] = '<filter id="' + bid + '" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="' + (L === 3 ? 16 : 24) + '"/></filter>';
        var inner = '', outer = '';
        [2.5, 2.8, 3.1].forEach(function (l) { inner += dipole(C, C, l, k, t, 0, 58); });
        [5.0, 5.6, 6.2, 6.8].forEach(function (l) { outer += dipole(C, C, l, k, t, 0, 50); });
        u += '<g filter="url(#' + bid + ')">' + P_(inner, P.nuc, L === 3 ? 34 : 60, 0.42) + P_(outer, P.el, L === 3 ? 44 : 80, 0.36) + '</g>';
        if (L === 3) { var d = ''; [1.9, 2.8, 4.0, 5.6, 7.6, 10.5].forEach(function (l) { d += dipole(C, C, l, k, t, 92); }); u += P_(d, P.det, 2.2, 0.35); }
        return { under: u, atom: { tier: tierFor(sz), pl: { cx: C, cy: C, s: 0.88 } } };
      } },
    { id: 'I12', name: 'Fine particles', note: 'The atom of the About window in the tile: the thin W7 rings plus fine particles running on the three orbits. At small sizes the particles drop out.', shape: 'Centred', best: 'P7',
      draw: function (P, L, sz) {
        var pl = { cx: C, cy: C + 4, s: 0.95 }, o = '', R = rng(11);
        if (L === 3) {
          for (var k = 0; k < 3; k++) for (var i = 0; i < 84; i++) { var t = R() * Math.PI * 2, rr = 1.12 + R() * 0.12, p = orbitPt(pl, k, t, rr), far = Math.sin(t) < 0; o += dotC(p[0], p[1], far ? 3.4 + R() * 1.6 : 4.4 + R() * 3, R() < 0.2 ? P.el : P.ring, far ? 0.45 : 0.85); }
          for (var j = 0; j < 46; j++) { var a = R() * Math.PI * 2, r = 96 + R() * 36; o += dotC(C + Math.cos(a) * r * 0.95, C + 4 + Math.sin(a) * r * 0.95, 2.4 + R() * 2, R() < 0.5 ? P.nuc : P.ring, 0.55); }
        }
        return { over: o, atom: { tier: tierFor(sz, L >= 2), pl: L === 1 ? { cx: C, cy: C } : pl } };
      } },
    { id: 'I13', name: 'Specimen', note: 'The atom zoomed 1.2 times and set low left like a specimen under a reticle: cross-hair through the nucleus, a measuring circle, rulers along the top and right edges.', shape: 'Zoom and crop', best: 'P8',
      draw: function (P, L, sz) {
        var pl = { cx: 460, cy: 560, s: 1.2, rot: -4 }, u = '', o = '';
        if (L === 1) return { atom: { tier: tierFor(sz), pl: { cx: C, cy: C } } };
        if (L === 3) {
          u += P_(line(460, 0, 460, 1024) + line(0, 560, 1024, 560), P.det, 2.4, 0.4);
          o += P_(circ(460, 560, 160), P.det, 3, 0.7) + P_(ticks(460, 560, 180, 36, 10, 3, 22, 0), P.det, 2.4, 0.6);
          var t = ''; for (var k = 3; k < 61; k++) { var v = k * 16, len = k % 8 === 0 ? 42 : k % 4 === 0 ? 28 : 14; if (v < 900) t += line(v, 60, v, 60 + len); if (v > 124) t += line(964, v, 964 - len, v); }
          u += P_(t, P.det, 3, 0.55);
        } else { u += P_(line(460, 0, 460, 1024) + line(0, 560, 1024, 560), P.det, 9, 0.4); o += P_(circ(460, 560, 170), P.det, 12, 0.7); }
        return { under: u, over: o, atom: { tier: tierFor(sz), pl: pl } };
      } },
    { id: 'I14', name: 'Polar chart', note: 'A polar grid (rings every 120, spokes every 15 degrees) centred on the nucleus; the atom tilted 12 degrees on it, like a star chart.', shape: 'Tilt', best: 'P4',
      draw: function (P, L, sz) {
        var u = '';
        if (L === 3) { var d = ''; [120, 240, 360, 480, 600].forEach(function (r) { d += circ(C, C, r); }); for (var a = 0; a < 180; a += 15) { var q = a * Math.PI / 180; d += line(C - Math.cos(q) * 740, C - Math.sin(q) * 740, C + Math.cos(q) * 740, C + Math.sin(q) * 740); } u += P_(d, P.det, 2, 0.28); u += P_(ticks(C, C, 480, 72, 12, 6, 24, 0), P.det, 2.4, 0.5); }
        else if (L === 2) { var d2 = circ(C, C, 240) + circ(C, C, 480); for (var b = 0; b < 180; b += 45) { var q2 = b * Math.PI / 180; d2 += line(C - Math.cos(q2) * 740, C - Math.sin(q2) * 740, C + Math.cos(q2) * 740, C + Math.sin(q2) * 740); } u += P_(d2, P.det, 9, 0.3); }
        return { under: u, atom: { tier: tierFor(sz), pl: L === 1 ? { cx: C, cy: C } : { cx: C, cy: C, s: 0.9, rot: 12 } } };
      } }
  ];
  var W7PL = { tf: 'rotate(-6 800 190) translate(-419.2 -274.1) scale(1.5)' };
  var DES = {}; DESIGNS.forEach(function (d) { DES[d.id] = d; });

  var uid = 0;
  function svg(did, pid, size, opts) {
    opts = opts || {}; size = size || 1024;
    var D = DES[did], P = styled(PAL[pid], opts.style), L = lvlFor(size);
    var U = { id: 'a' + (++uid).toString(36) + '_', defs: {} };
    curL = L; var r = D.draw(P, L, size, U);
    var body = (r.under || '') + (r.atom ? atom(U, r.atom.tier, r.atom.pl, P, r.atom.o) : '') + (r.over || '');
    var id = U.id;
    var defs = '<linearGradient id="' + id + 'bg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="' + P.bg[0] + '"/><stop offset="1" stop-color="' + P.bg[1] + '"/></linearGradient>' +
      '<clipPath id="' + id + 'clip"><path d="' + TILE + '"/></clipPath>' +
      (P.glow ? '<radialGradient id="' + id + 'gl" cx="0.5" cy="0.46" r="0.55"><stop offset="0" stop-color="' + P.glow + '" stop-opacity="0.22"/><stop offset="1" stop-color="' + P.glow + '" stop-opacity="0"/></radialGradient>' : '') +
      '<filter id="' + id + 'sh" x="-10%" y="-10%" width="120%" height="125%"><feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000" flood-opacity="0.32"/></filter>' +
      Object.keys(U.defs).map(function (k) { return U.defs[k]; }).join('');
    var tile = '<path d="' + TILE + '" fill="url(#' + id + 'bg)"/>' + (P.glow ? '<rect width="1024" height="1024" fill="url(#' + id + 'gl)" clip-path="url(#' + id + 'clip)"/>' : '') +
      '<g clip-path="url(#' + id + 'clip)">' + body + '</g>' +
      (P.clear ? '<path d="' + TILE + '" fill="none" stroke="#fff" stroke-opacity="0.75" stroke-width="10"/>' : P.rim ? '<path d="' + TILE + '" fill="none" stroke="' + P.rim + '" stroke-opacity="' + (P.tinted ? 0.18 : 0.32) + '" stroke-width="' + (L === 3 ? 6 : L === 2 ? 14 : 26) + '" clip-path="url(#' + id + 'clip)"/>' : '');
    if (P.clear) tile = '<g opacity="0.92">' + tile + '</g>';
    var inner = opts.frame === 'mac' ? '<g filter="url(#' + id + 'sh)"><g transform="translate(100 100) scale(0.8046875)">' + tile + '</g></g>' : tile;
    return '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="' + size + '" height="' + size + '" viewBox="0 0 1024 1024"><defs>' + defs + '</defs>' + inner + '</svg>';
  }


  /* ---------- mock-ups ---------- */
  function inner(svgStr, x, y, w) { return svgStr.replace(/^<svg[^>]*>/, '<svg x="' + f(x) + '" y="' + f(y) + '" width="' + f(w) + '" height="' + f(w) + '" viewBox="0 0 1024 1024">'); }
  /* generic stand-in app icons (invented, not real apps), drawn in 1024 space on the macOS grid */
  var STAND = [
    function () { return '<path d="' + squircle(100, 100, 824) + '" fill="#3D8BF2"/><path d="M250 340h200l40 50h284v330H250z" fill="#E8F2FF"/><path d="M250 430h524v290H250z" fill="#BFDBFF"/>'; },
    function () { return '<path d="' + squircle(100, 100, 824) + '" fill="#F4F6F9"/><circle cx="512" cy="512" r="300" fill="#2F7BF5"/><path d="' + 'M212,512h600M512,212v600M300,330c140,60,284,60,424,0M300,694c140,-60,284,-60,424,0' + '" stroke="#fff" stroke-width="18" fill="none"/><ellipse cx="512" cy="512" rx="130" ry="300" stroke="#fff" stroke-width="18" fill="none"/>'; },
    function () { return '<path d="' + squircle(100, 100, 824) + '" fill="#FFFDF5"/><rect x="100" y="100" width="824" height="200" fill="#F6C944" clip-path="none"/><path d="M230 420h564M230 520h564M230 620h564M230 720h400" stroke="#C9C2AE" stroke-width="16"/>'; },
    function () { return '<path d="' + squircle(100, 100, 824) + '" fill="#202124"/><path d="M260 380l130 110-130 110" stroke="#E9E9E9" stroke-width="44" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M440 640h200" stroke="#E9E9E9" stroke-width="44" stroke-linecap="round"/>'; },
    function () { return '<path d="' + squircle(100, 100, 824) + '" fill="#F0435F"/><circle cx="420" cy="660" r="90" fill="#fff"/><path d="M490 660V300l230-60v300" stroke="#fff" stroke-width="44" fill="none"/><circle cx="650" cy="560" r="80" fill="#fff"/>'; },
    function () { var d = ''; for (var i = 0; i < 12; i++) { var a = i / 12 * Math.PI * 2; d += line(512 + Math.cos(a) * 200, 512 + Math.sin(a) * 200, 512 + Math.cos(a) * 290, 512 + Math.sin(a) * 290); } return '<path d="' + squircle(100, 100, 824) + '" fill="#8E929B"/><path d="' + d + '" stroke="#E7E8EA" stroke-width="70"/><circle cx="512" cy="512" r="220" fill="#E7E8EA"/><circle cx="512" cy="512" r="100" fill="#8E929B"/>'; },
    function () { return '<path d="' + squircle(100, 100, 824) + '" fill="#2A9BF6"/><rect x="230" y="330" width="564" height="380" rx="30" fill="#fff"/><path d="M240 345l272 210 272-210" stroke="#2A9BF6" stroke-width="26" fill="none"/>'; }
  ];
  function standSvg(i, x, y, w) { var c = 'st' + (++uid); return '<svg x="' + f(x) + '" y="' + f(y) + '" width="' + f(w) + '" height="' + f(w) + '" viewBox="0 0 1024 1024"><defs><clipPath id="' + c + '"><path d="' + squircle(100, 100, 824) + '"/></clipPath></defs><g clip-path="url(#' + c + ')">' + STAND[i]() + '</g></svg>'; }
  function wallpaper(theme, W, H, id) {
    return theme === 'light'
      ? '<defs><linearGradient id="' + id + '" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#EEF1F6"/><stop offset="0.6" stop-color="#D9E1EC"/><stop offset="1" stop-color="#C9D4E4"/></linearGradient></defs><rect width="' + W + '" height="' + H + '" fill="url(#' + id + ')"/>'
      : '<defs><linearGradient id="' + id + '" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1A1C26"/><stop offset="0.6" stop-color="#12131A"/><stop offset="1" stop-color="#0A0B10"/></linearGradient></defs><rect width="' + W + '" height="' + H + '" fill="url(#' + id + ')"/>';
  }
  /* macOS Dock: icons 64 pt (drawn here at 2x, 128 px); ours fourth, with the running dot */
  function dock(did, pid, theme, style) {
    var W = 1160, H = 260, n = 8, sz = 128, gap = 10, dw = n * sz + (n + 1) * gap + 40, x0 = (W - dw) / 2, id = 'dk' + (++uid);
    var s = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '">' + wallpaper(theme, W, H, id);
    s += '<rect x="' + f(x0) + '" y="70" width="' + f(dw) + '" height="168" rx="44" fill="' + (theme === 'light' ? '#FFFFFF' : '#2A2C36') + '" fill-opacity="' + (theme === 'light' ? 0.55 : 0.55) + '" stroke="' + (theme === 'light' ? '#FFFFFF' : '#FFFFFF') + '" stroke-opacity="' + (theme === 'light' ? 0.8 : 0.16) + '" stroke-width="2"/>';
    var k = 0;
    for (var i = 0; i < n; i++) {
      var x = x0 + 20 + gap + i * (sz + gap), y = 78;
      if (i === 3) { s += inner(svg(did, pid, 128, { frame: 'mac', style: style }), x, y, sz); s += '<circle cx="' + f(x + sz / 2) + '" cy="' + (y + sz + 14) + '" r="4.5" fill="' + (theme === 'light' ? '#222' : '#EEE') + '"/>'; }
      else s += standSvg(k++ % STAND.length, x, y, sz);
    }
    return s + '</svg>';
  }
  /* Windows 11 taskbar: 48 px high, icons 24 px at 100 % (also shown at 150 %, 36 px) */
  function taskbar(did, pid, theme, scale) {
    scale = scale || 1; var H = 48 * scale, ic = 24 * scale, cell = 44 * scale, n = 6, W = 560 * scale, id = 'tb' + (++uid);
    var dark = theme !== 'light', s = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="' + W + '" height="' + (H + 40 * scale) + '" viewBox="0 0 ' + W + ' ' + (H + 40 * scale) + '">' + wallpaper(theme, W, H + 40 * scale, id);
    var y0 = 40 * scale; s += '<rect x="0" y="' + y0 + '" width="' + W + '" height="' + H + '" fill="' + (dark ? '#202020' : '#F3F3F3') + '" fill-opacity="0.94"/><rect x="0" y="' + y0 + '" width="' + W + '" height="1" fill="' + (dark ? '#3A3A3A' : '#D8D8D8') + '"/>';
    var x0 = (W - n * cell) / 2;
    for (var i = 0; i < n; i++) {
      var cx = x0 + i * cell + cell / 2, y = y0 + (H - ic) / 2;
      if (i === 0) { s += '<circle cx="' + f(cx - 2 * scale) + '" cy="' + f(y + ic / 2 - 2 * scale) + '" r="' + f(7 * scale) + '" fill="none" stroke="' + (dark ? '#DDD' : '#333') + '" stroke-width="' + f(2 * scale) + '"/><path d="' + line(cx + 3 * scale, y + ic / 2 + 3 * scale, cx + 8 * scale, y + ic / 2 + 8 * scale) + '" stroke="' + (dark ? '#DDD' : '#333') + '" stroke-width="' + f(2.2 * scale) + '" stroke-linecap="round"/>'; continue; }
      if (i === 3) { s += '<rect x="' + f(cx - cell / 2 + 2 * scale) + '" y="' + f(y0 + 4 * scale) + '" width="' + f(cell - 4 * scale) + '" height="' + f(H - 8 * scale) + '" rx="' + f(4 * scale) + '" fill="' + (dark ? '#FFFFFF' : '#000000') + '" fill-opacity="0.07"/>'; s += inner(svg(did, pid, Math.round(ic), { frame: 'full' }), cx - ic / 2, y, ic); s += '<rect x="' + f(cx - 8 * scale) + '" y="' + f(y0 + H - 5 * scale) + '" width="' + f(16 * scale) + '" height="' + f(3 * scale) + '" rx="' + f(1.5 * scale) + '" fill="#4CC2FF"/>'; }
      else { var j = [0, 1, 3, 6, 4][i - 1] || 0; s += standSvg(j, cx - ic * 0.62, y - ic * 0.12, ic * 1.24); }
    }
    return s + '</svg>';
  }
  /* the four macOS 26 icon styles side by side */
  function styles(did, pid) {
    var W = 4 * 300, H = 320, s = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '">';
    var bgs = ['#DDE3EC', '#15161C', '#15161C', '#6E7C93'];
    ['default', 'dark', 'tinted', 'clear'].forEach(function (st, i) {
      s += '<rect x="' + i * 300 + '" y="0" width="300" height="' + H + '" fill="' + bgs[i] + '"/>';
      if (st === 'clear') s += '<circle cx="' + (i * 300 + 90) + '" cy="90" r="120" fill="#9BB2D6" fill-opacity="0.7"/><circle cx="' + (i * 300 + 230) + '" cy="250" r="110" fill="#5B6680" fill-opacity="0.7"/>';
      s += inner(svg(did, pid, 256, { frame: 'mac', style: st }), i * 300 + 22, 20, 256);
      s += '<text x="' + (i * 300 + 150) + '" y="302" text-anchor="middle" font-family="Inter,Helvetica,Arial,sans-serif" font-size="17" fill="' + (i === 0 ? '#333' : '#DDD') + '">' + ['Default', 'Dark (kept, IC1)', 'Tinted (system)', 'Clear (system)'][i] + '</text>';
    });
    return s + '</svg>';
  }

  var RECS = [
    { d: 'I5', p: 'P1', why: 'Closest to today: the W7 you already ship, in a deeper ocean blue, with ruler marks. Lowest-risk change.' },
    { d: 'I3', p: 'P5', why: 'The strongest new silhouette: a dial is a circle inside the squircle and still reads at 16 px.' },
    { d: 'I9', p: 'P2', why: 'Matches the splash you picked first (S2): moons on orbits at 4 : 2 : 1 behind the atom.' },
    { d: 'I11', p: 'P7', why: 'The About window in an icon: warm and cool belts, the most "scientific" glow of the set.' },
    { d: 'I4', p: 'P2', why: 'Shape change inside Apple\'s rules: a porthole that zooms into the atom.' }
  ];

  var API = { dock: dock, taskbar: taskbar, styles: styles, PALETTES: PALETTES, DESIGNS: DESIGNS, RECS: RECS, svg: svg, checks: checks, contrast: contrast, mix: mix, TILE: TILE, squircle: squircle, styled: styled, lvlFor: lvlFor, tierFor: tierFor };
  root.AL2 = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
