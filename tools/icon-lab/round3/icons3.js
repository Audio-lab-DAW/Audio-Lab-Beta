/* AudioLab app icon, round 3 (task IC3): the dipole field centred on the nucleus.
   One drawing module for the pick page (browser) and render3.js (Node). Everything is drawn in code as SVG.
   Reuses round 2 (tools/icon-lab/round2): the shipped atom geometry (geom.json, from extract_geom.py), the
   squircle tile, the palettes P2 and P8, the stroke rules and the Dock, taskbar and style mock-ups.

   What changed against round 2's I7: there the field was centred on the tile (512, 512), but the shipped atom
   carries an optical offset, so the nucleus sat at about (502, 492) and the field ran past it off-centre; the
   lines were also cut at a fixed radius. Here every design first decides where the NUCLEUS goes, places the
   atom so its nucleus lands exactly there at every size (placeAt, per ring tier), and draws the field lines
   r = L sin^2(theta) around that same point. Each line starts and ends on a circle a clean gap outside the
   nucleus (the planet's surface), as on the splash (task SP1, S1), so the yellow nucleus plays the Earth.

   svg(designId, paletteId, size, opts) -> SVG string, viewBox 0 0 1024 1024.
     size        : pixel size shown at; picks the level of detail
                   (>=128 everything, 48..64 bold structure, 24..32 small master, 16 the XS master)
     opts.frame  : 'mac' (macOS 26 grid: 824 px squircle, 100 px margin, shadow) or 'full' (tile fills the canvas)
     opts.style  : 'default' | 'dark' | 'darkauto' | 'tinted' | 'clear'
     opts.still  : true leaves out the trapped particles (the animated preview draws its own)
   anim(designId) -> geometry for the animated preview (nucleus, field lines, orbits) in the 1024 frame. */
(function (root) {
  'use strict';
  var GEOM = root.AL2_GEOM || (typeof require === 'function' ? require('../round2/geom.json') : null);

  /* ---------- palettes (P2 and P8 exactly as round 2; P8N is new: the proposed Dark variant of P8) ---------- */
  var PALETTES = [
    { id: 'P2', name: 'Orbit night', from: 'Splash S2, moons in resonance (round 2)', bg: ['#132044', '#070910'], ring: '#EAF1FF', nuc: '#FFC43C', el: '#4CC9F0', det: '#6096FF', glow: '#6096FF', rim: '#6096FF' },
    { id: 'P8', name: 'Chart paper', from: "The orbit chart's ink as a printed plate (round 2)", bg: ['#F7F3EA', '#E4DCCA'], ring: '#1B2340', nuc: '#C8610A', el: '#2F6BFF', det: '#1B2340', glow: null, rim: '#1B2340' },
    { id: 'P8N', name: 'Chart paper, night', from: 'New: the Dark variant proposed for P8 (paper and ink swapped, same orange and blue, lifted)', bg: ['#1E2742', '#0C1020'], ring: '#F3EEE2', nuc: '#F08A2C', el: '#6E9BFF', det: '#D9CDB4', glow: null, rim: '#D9CDB4', darkOf: 'P8' }
  ];
  var PAL = {}; PALETTES.forEach(function (p) { PAL[p.id] = p; });

  /* ---------- colour helpers (round 2) ---------- */
  function hex2rgb(h) { h = h.replace('#', ''); return [parseInt(h.substr(0, 2), 16), parseInt(h.substr(2, 2), 16), parseInt(h.substr(4, 2), 16)]; }
  function rgb2hex(c) { return '#' + c.map(function (v) { v = Math.max(0, Math.min(255, Math.round(v))); return (v < 16 ? '0' : '') + v.toString(16); }).join('').toUpperCase(); }
  function mix(a, b, t) { var x = hex2rgb(a), y = hex2rgb(b); return rgb2hex([0, 1, 2].map(function (i) { return x[i] + (y[i] - x[i]) * t; })); }
  function lum(h) { return hex2rgb(h).map(function (v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }).reduce(function (s, v, i) { return s + v * [0.2126, 0.7152, 0.0722][i]; }, 0); }
  function contrast(a, b) { var x = lum(a), y = lum(b); if (x < y) { var t = x; x = y; y = t; } return (x + 0.05) / (y + 0.05); }

  /* macOS 26 styles. dark: what IC1's Icon Composer file shows (P2 kept as drawn; P8 as drawn too unless the
     P8N dark entry is used). darkauto: roughly what macOS makes by itself when an icon brings no dark entry
     (the tile colour replaced by its black tile, the parts kept), to show why P8 needs its own. Tinted and
     Clear: the system removes the colours; the brightness of each part is kept (approximation). */
  var TINT = '#5EA8FF';
  function styled(P, style) {
    if (style === 'darkauto') return { id: P.id, name: P.name, bg: ['#26272C', '#141518'], ring: P.ring, nuc: P.nuc, el: P.el, det: P.det, glow: null, rim: '#FFFFFF', auto: true };
    if (style === 'tinted') {
      var tc = function (c) { var l = Math.sqrt(lum(c)); return mix('#0E0F12', mix(TINT, '#FFFFFF', Math.max(0, l - 0.55)), 0.35 + 0.65 * l); };
      var lt = lum(P.bg[0]) > 0.4; /* a light tile: the system keeps the shape, so dark ink turns light */
      var tc2 = lt ? function (c) { return tc(mix('#FFFFFF', c, 0.15)); } : tc;
      return { id: P.id, name: P.name, bg: ['#1A1B1F', '#0C0C0E'], ring: tc2(P.ring), nuc: tc(P.nuc), el: tc(P.el), det: tc2(P.det), glow: null, rim: '#FFFFFF', tinted: true };
    }
    if (style === 'clear') {
      var cc = function (c) { var l = Math.sqrt(lum(c)); return mix('#7A7D86', '#FFFFFF', l); };
      var lc = lum(P.bg[0]) > 0.4;
      var cc2 = lc ? function (c) { return cc(mix('#FFFFFF', c, 0.1)); } : cc;
      return { id: P.id, name: P.name, bg: ['#DADDE4', '#9EA3AE'], ring: cc2(P.ring), nuc: cc(P.nuc), el: cc(P.el), det: cc2(P.det), glow: null, rim: '#FFFFFF', clear: true };
    }
    return P;
  }
  function checks(P) {
    var light = '#E6E8EE', dark = '#1C1D22';
    return {
      ring: Math.min(contrast(P.ring, P.bg[0]), contrast(P.ring, P.bg[1])),
      nuc: Math.min(contrast(P.nuc, P.bg[0]), contrast(P.nuc, P.bg[1])),
      el: Math.min(contrast(P.el, P.bg[0]), contrast(P.el, P.bg[1])),
      det: Math.min(contrast(P.det, P.bg[0]), contrast(P.det, P.bg[1])),
      onLight: Math.max(contrast(P.bg[0], light), contrast(P.bg[1], light)),
      onDark: Math.max(contrast(P.bg[0], dark), contrast(P.bg[1], dark)), rim: !!P.rim
    };
  }

  /* ---------- geometry helpers (round 2) ---------- */
  function f(n) { return (Math.round(n * 10) / 10).toString(); }
  function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function squircle(x, y, s, n) {
    n = n || 5; var pts = [], N = 144, a = s / 2;
    for (var i = 0; i < N; i++) { var t = i / N * Math.PI * 2, c = Math.cos(t), si = Math.sin(t); pts.push(f(x + a + a * Math.sign(c) * Math.pow(Math.abs(c), 2 / n)) + ',' + f(y + a + a * Math.sign(si) * Math.pow(Math.abs(si), 2 / n))); }
    return 'M' + pts.join('L') + 'Z';
  }
  var TILE = squircle(0, 0, 1024, 5);
  function line(x1, y1, x2, y2) { return 'M' + f(x1) + ',' + f(y1) + 'L' + f(x2) + ',' + f(y2); }
  function poly(pts) { return 'M' + pts.map(function (p) { return f(p[0]) + ',' + f(p[1]); }).join('L'); }
  function circ(cx, cy, r) { return 'M' + f(cx - r) + ',' + f(cy) + 'a' + f(r) + ',' + f(r) + ' 0 1,0 ' + f(2 * r) + ',0a' + f(r) + ',' + f(r) + ' 0 1,0 ' + f(-2 * r) + ',0Z'; }
  var curL = 3;
  /* fine strokes are drawn 1.45 times heavier at full detail: the 1024 drawing is seen at 128 to 256 px */
  function P_(d, stroke, sw, op, extra) { if (curL === 3 && sw < 8) { sw *= 1.45; if (op != null) op = Math.min(0.9, op * 1.25 + 0.04); } return '<path d="' + d + '" fill="none" stroke="' + stroke + '" stroke-width="' + f(sw) + '"' + (op != null ? ' stroke-opacity="' + (Math.round(op * 100) / 100) + '"' : '') + ' stroke-linecap="round" stroke-linejoin="round"' + (extra || '') + '/>'; }
  function dotC(cx, cy, r, fill, op) { return '<circle cx="' + f(cx) + '" cy="' + f(cy) + '" r="' + f(r) + '" fill="' + fill + '"' + (op != null ? ' fill-opacity="' + op + '"' : '') + '/>'; }
  function ticks(cx, cy, r, n, len, every, longLen, mid, midLen) { var d = ''; for (var i = 0; i < n; i++) { var a = i / n * Math.PI * 2 - Math.PI / 2, L = (every && i % every === 0) ? longLen : (mid && i % mid === 0) ? midLen : len; d += line(cx + Math.cos(a) * r, cy + Math.sin(a) * r, cx + Math.cos(a) * (r + L), cy + Math.sin(a) * (r + L)); } return d; }

  function tierFor(sz, thin) { if (sz >= 128) return thin ? 'W7L' : 'L'; if (sz >= 48) return thin ? 'W7M' : 'M'; if (sz >= 24) return thin ? 'W7S' : 'S'; return 'XS'; }
  function lvlFor(sz) { return sz >= 128 ? 3 : sz >= 48 ? 2 : sz >= 24 ? 1 : 0; }

  /* ---------- the atom, placed by its nucleus ---------- */
  /* pl = {cx, cy, s, rot}: the mark's own 1024 frame (with its optical offset) put into the tile */
  function atomTF(g, pl) { return 'translate(' + f(pl.cx) + ' ' + f(pl.cy) + ') rotate(' + f(pl.rot || 0) + ') scale(' + (pl.s || 1) + ') translate(' + f(-512 + g.off[0]) + ' ' + f(-512 + g.off[1]) + ')'; }
  /* the placement that puts the nucleus of this tier exactly on (nx, ny) */
  function placeAt(tier, nx, ny, s, rot) {
    var g = GEOM[tier], a = (rot || 0) * Math.PI / 180, ox = g.off[0] * s, oy = g.off[1] * s;
    return { cx: nx - (ox * Math.cos(a) - oy * Math.sin(a)), cy: ny - (ox * Math.sin(a) + oy * Math.cos(a)), s: s, rot: rot || 0, nx: nx, ny: ny };
  }
  /* where a point of the mark's frame lands in the tile */
  function markPt(tier, pl, x, y) {
    var g = GEOM[tier], s = pl.s || 1, a = (pl.rot || 0) * Math.PI / 180, dx = (x - 512 + g.off[0]) * s, dy = (y - 512 + g.off[1]) * s;
    return [pl.cx + dx * Math.cos(a) - dy * Math.sin(a), pl.cy + dx * Math.sin(a) + dy * Math.cos(a)];
  }
  function ringDefs(U, tier) {
    var g = GEOM[tier], id = U.id + tier;
    if (!U.defs[id]) U.defs[id] = g.rings.map(function (d, i) { return '<path id="' + id + 'r' + i + '" d="' + d + '" fill-rule="evenodd"/>'; }).join('') +
      '<mask id="' + id + 'h" maskUnits="userSpaceOnUse" x="-3000" y="-3000" width="7000" height="7000"><rect x="-3000" y="-3000" width="7000" height="7000" fill="#fff"/><circle cx="' + g.e[0] + '" cy="' + g.e[1] + '" r="' + g.halo + '" fill="#000"/></mask>';
    return id;
  }
  function uses(id) { return [0, 1, 2].map(function (i) { return '<use href="#' + id + 'r' + i + '" xlink:href="#' + id + 'r' + i + '"/>'; }).join(''); }
  function atom(U, tier, pl, P, o) {
    o = o || {}; var g = GEOM[tier], id = ringDefs(U, tier);
    var s = '<g transform="' + atomTF(g, pl) + '">';
    if (!o.noRings) s += '<g mask="url(#' + id + 'h)" fill="' + P.ring + '"' + (o.ringOp ? ' fill-opacity="' + o.ringOp + '"' : '') + '>' + uses(id) + '</g>';
    s += dotC(512, 512, g.nr * (o.nucScale || 1), P.nuc);
    if (!o.noEl) s += dotC(g.e[0], g.e[1], g.er, P.el);
    return s + '</g>';
  }
  /* the rings (and the electron's halo) as black, widened by w: cuts the field lines where they pass under a ring */
  function knock(U, tier, pl, w) {
    var g = GEOM[tier], id = ringDefs(U, tier);
    return '<g transform="' + atomTF(g, pl) + '"><g fill="#000" stroke="#000" stroke-width="' + f(w / (pl.s || 1)) + '" stroke-linejoin="round">' + uses(id) + '</g>' + dotC(g.e[0], g.e[1], g.halo + w / 2 / (pl.s || 1), '#000') + '</g>';
  }
  /* the feet of the lines fade toward the surface (from 30 % at the surface to full strength 1.6 gaps out), so
     the lines still reach the planet but do not bunch into a comb around it */
  function footFade(U, c, Rs, w) {
    var m = U.id + 'ff' + Math.round(c[0]) + '_' + Math.round(Rs);
    U.defs[m] = '<radialGradient id="' + m + 'g" gradientUnits="userSpaceOnUse" cx="' + f(c[0]) + '" cy="' + f(c[1]) + '" r="' + f(Rs + w) + '"><stop offset="0" stop-color="#fff" stop-opacity="0.3"/><stop offset="' + (Rs / (Rs + w)).toFixed(3) + '" stop-color="#fff" stop-opacity="0.3"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></radialGradient>' +
      '<mask id="' + m + '" maskUnits="userSpaceOnUse" x="-200" y="-200" width="1424" height="1424"><rect x="-200" y="-200" width="1424" height="1424" fill="url(#' + m + 'g)"/></mask>';
    return 'url(#' + m + ')';
  }
  function maskOf(U, name, inner) { var m = U.id + name; U.defs[m] = '<mask id="' + m + '" maskUnits="userSpaceOnUse" x="-200" y="-200" width="1424" height="1424"><rect x="-200" y="-200" width="1424" height="1424" fill="#fff"/>' + inner + '</mask>'; return 'url(#' + m + ')'; }

  /* ---------- the dipole field ----------
     A line of the field of a magnet: r = Leq sin^2(theta), theta from the magnetic north pole, Leq = how far the
     line crosses the magnetic equator (px). The axis leans by tilt degrees (clockwise). Each line is drawn from
     the surface circle Rs (a gap outside the nucleus) round to the surface again, on both sides. */
  function fpt(c, Leq, tilt, th, side) {
    var a = tilt * Math.PI / 180, r = Leq * Math.pow(Math.sin(th), 2), x = side * r * Math.sin(th), y = -r * Math.cos(th);
    return [c[0] + x * Math.cos(a) - y * Math.sin(a), c[1] + x * Math.sin(a) + y * Math.cos(a)];
  }
  function footTh(Leq, Rs) { return Math.asin(Math.min(1, Math.sqrt(Rs / Leq))); }
  function fline(c, Leq, tilt, Rs, winDeg) {
    var t0 = footTh(Leq, Rs); if (winDeg) t0 = Math.max(t0, winDeg * Math.PI / 180);
    var n = Math.max(24, Math.round(Leq / 5)), out = '';
    [1, -1].forEach(function (side) { var pts = []; for (var i = 0; i <= n; i++) pts.push(fpt(c, Leq, tilt, t0 + (Math.PI - 2 * t0) * i / n, side)); out += poly(pts); });
    return out;
  }
  /* trapped particles for the still picture: two per line, set where a bouncing particle spends the most time
     (near its mirror points), as on the splash */
  function trapped(c, Ls, tilt, Rs, P, R, rad, hide, innerMax) {
    var o = '';
    Ls.forEach(function (Leq, i) {
      if (i === 0) return;
      var t0 = footTh(Leq, Rs), amp = (Math.PI / 2 - t0) * 0.82;
      [1, -1].forEach(function (side, j) {
        for (var k = 0; k < 12; k++) { var u = R() * 2 - 1, th = Math.PI / 2 + amp * Math.sin(u * Math.PI / 2 + (j ? 0.7 : -0.4)), p = fpt(c, Leq, tilt, th, side);
          if (hide && Leq > innerMax && Math.hypot(p[0] - c[0], p[1] - c[1]) < hide + 20) continue;
          o += dotC(p[0], p[1], rad, (i + j) % 2 ? P.el : P.nuc, 0.92); break; }
      });
    });
    return o;
  }
  /* the magnetic axis through the planet: two short stubs at the poles, between the surface gap and the first line */
  function axisStubs(c, tilt, r0, r1) { var a = tilt * Math.PI / 180, s = Math.sin(a), co = Math.cos(a); return line(c[0] + s * r0, c[1] - co * r0, c[0] + s * r1, c[1] - co * r1) + line(c[0] - s * r0, c[1] + co * r0, c[0] - s * r1, c[1] + co * r1); }

  /* level of detail for the field around an atom with rings (L: 3 full, 2 bold, 1 small master, 0 XS master) */
  var FIELD = {
    3: { Ls: [150, 212, 300, 430, 620, 900], sw: 3, op: 0.44, knock: 30 },
    2: { Ls: [256, 420, 690], sw: 11, op: 0.5, knock: 44 },
    1: { Ls: [430], sw: 38, op: 0.62, knock: 60, win: 56 },
    0: { Ls: [452], sw: 54, op: 0.66, knock: 70, win: 58 }
  };
  var ATOMS = { 3: 0.86, 2: 0.86, 1: 0.74, 0: 0.7 };

  /* The core: the atom with its nucleus on c, the field around it. o: tilt, thin (W7 rings), scale (atom),
     fs (field size factor), clip (url), still. Returns {under, atomSvg, over, pl, tier} */
  function fieldAtom(P, L, sz, U, o) {
    var tier = tierFor(sz, o.thin && L >= 1), s = (o.scale || ATOMS[L]), c = o.c || [512, 512];
    var pl = placeAt(tier, c[0], c[1], s, o.rot || 0), g = GEOM[tier], F = FIELD[L];
    var nr = g.nr * s, gap = L === 3 ? 24 : L === 2 ? 30 : 40, Rs = nr + gap;
    var Ls = F.Ls.map(function (v) { return v * (o.fs || 1); });
    /* inside the ring envelope only the innermost loops are drawn in full; the outer lines come out from behind
       the atom (drawing their feet between the rings made a comb around the nucleus) */
    var q = s / 0.86, inner = '', outer = '';
    Ls.forEach(function (Leq) { var d = fline(c, Leq, o.tilt, Rs, F.win); if (L >= 2 && Leq <= 262 * q) inner += d; else outer += d; });
    var u = '';
    if (inner) u += '<g mask="' + footFade(U, c, Rs, 60 * q) + '">' + P_(inner, P.det, F.sw, F.op) + '</g>';
    if (outer) u += L >= 2 ? '<g mask="' + maskOf(U, 'hd' + tier, dotC(c[0], c[1], 300 * q, '#000')) + '">' + P_(outer, P.det, F.sw, F.op) + '</g>' : P_(outer, P.det, F.sw, F.op);
    if (L === 3) u += P_(axisStubs(c, o.tilt, nr + 12, Math.min(Rs + 46, nr + 70)), P.det, 3, 0.55);
    if (L === 3 && !o.still) u += trapped(c, Ls, o.tilt, Rs, P, rng(o.seed || 7), 7.5, 300 * q, 262 * q);
    var mk = maskOf(U, 'fk' + tier, knock(U, tier, pl, F.knock));
    u = '<g mask="' + mk + '">' + u + '</g>';
    return { under: u, atomSvg: atom(U, tier, pl, P, { ringOp: o.thin ? 0.9 : null }), pl: pl, tier: tier, Rs: Rs, Ls: Ls };
  }

  /* The field becomes the orbits: no rings; three field lines in the ring colour carry the mark, the electron
     rides the middle one where the shipped electron sits (60 degrees from the axis, up and right). */
  var FO = {
    3: { bold: [236, 360, 520], bw: [22, 19, 16], fine: [296, 438, 700], nr: 88, er: 46, halo: 64 },
    2: { bold: [236, 380, 540], bw: [30, 27, 24], fine: [], nr: 96, er: 52, halo: 74 },
    1: { bold: [270, 500], bw: [48, 44], fine: [], nr: 112, er: 64, halo: 92 },
    0: { bold: [290, 520], bw: [64, 58], fine: [], nr: 128, er: 74, halo: 104 }
  };
  function fieldOrbits(P, L, sz, U, o) {
    var c = o.c || [512, 512], k = o.k || 0.86, Q = FO[L], nr = Q.nr * k, Rs = nr + (L === 3 ? 26 : L === 2 ? 34 : 44) * k, tilt = o.tilt;
    var bold = Q.bold.map(function (v) { return v * k; }), fine = Q.fine.map(function (v) { return v * k; });
    var mid = bold[1], eth = 60 * Math.PI / 180 - tilt * Math.PI / 180 * 0, ep = fpt(c, mid, tilt, eth, 1);
    var halo = maskOf(U, 'eh', dotC(ep[0], ep[1], Q.halo * k, '#000'));
    var u = '';
    if (fine.length) { var d = ''; fine.forEach(function (Leq) { d += fline(c, Leq, tilt, Rs); }); u += '<g mask="' + footFade(U, c, Rs, 90 * k) + '">' + P_(d, P.det, 3, 0.4) + '</g>'; }
    if (L === 3) u += P_(axisStubs(c, tilt, nr + 12, nr + 60), P.det, 3, 0.55);
    if (L === 3 && !o.still) u += trapped(c, fine, tilt, Rs, P, rng(o.seed || 5), 7.5);
    var b = ''; bold.forEach(function (Leq, i) { b += P_(fline(c, Leq, tilt, Rs), P.ring, Q.bw[i] * k, 0.96); });
    u = '<g mask="' + halo + '">' + u + b + '</g>';
    var at = dotC(c[0], c[1], nr, P.nuc) + dotC(ep[0], ep[1], Q.er * k, P.el);
    return { under: u, atomSvg: at, Rs: Rs, Ls: bold, fine: fine, e: ep };
  }

  /* measurement elements borrowed from I5: a faint grid, rulers along the left and bottom edges */
  function grid(P, step, op) { var d = ''; for (var x = 0; x <= 1024; x += step) d += line(x, 0, x, 1024) + line(0, x, 1024, x); return P_(d, P.det, 1.4, op); }
  function rulers(P, L) {
    if (L === 3) {
      var t = ''; for (var k = 4; k < 64; k++) { var y = k * 16, len = k % 8 === 0 ? 46 : k % 4 === 0 ? 30 : 16; if (y > 120 && y < 904) t += line(64, y, 64 + len, y); var xx = k * 16; if (xx > 120 && xx < 904) t += line(xx, 960, xx, 960 - len); }
      return P_(t, P.det, 3, 0.6) + P_(line(64, 120, 64, 904) + line(120, 960, 904, 960), P.det, 3, 0.45);
    }
    if (L === 2) { var t2 = ''; for (var k2 = 1; k2 < 8; k2++) t2 += line(70, k2 * 128, 130, k2 * 128) + line(k2 * 128, 954, k2 * 128, 894); return P_(t2, P.det, 12, 0.5); }
    return '';
  }
  /* the magnetic equator with a tick where each line crosses it (the L-shells, unlabelled) */
  function equatorTicks(c, tilt, Ls, P, from) {
    var a = tilt * Math.PI / 180, ex = Math.cos(a), ey = Math.sin(a), nx = -ey, ny = ex, d = '';
    d += line(c[0] + ex * from, c[1] + ey * from, c[0] + ex * 980, c[1] + ey * 980) + line(c[0] - ex * from, c[1] - ey * from, c[0] - ex * 980, c[1] - ey * 980);
    var t = ''; Ls.forEach(function (Leq) { [1, -1].forEach(function (sd) { var px = c[0] + sd * ex * Leq, py = c[1] + sd * ey * Leq; t += line(px - nx * 14, py - ny * 14, px + nx * 14, py + ny * 14); }); });
    return P_(d, P.det, 1.6, 0.3, ' stroke-dasharray="6 10"') + P_(t, P.det, 3, 0.6);
  }
  function scaleBar(P) { return P_(line(760, 118, 888, 118) + line(760, 104, 760, 132) + line(888, 104, 888, 132) + line(824, 110, 824, 126), P.det, 3.2, 0.7); }

  /* porthole (I4): a round lens in the tile with a rim and bolts; inside, the picture clipped to the lens */
  function lens(P, L, U, R, c) {
    var cid = U.id + 'lens';
    U.defs[cid] = '<clipPath id="' + cid + '"><circle cx="' + c[0] + '" cy="' + c[1] + '" r="' + R + '"/></clipPath><radialGradient id="' + cid + 'g" cx="0.42" cy="0.38" r="0.75"><stop offset="0" stop-color="' + mix(P.bg[0], P.det, 0.16) + '"/><stop offset="1" stop-color="' + P.bg[1] + '"/></radialGradient>';
    return { clip: 'url(#' + cid + ')', face: '<circle cx="' + c[0] + '" cy="' + c[1] + '" r="' + R + '" fill="url(#' + cid + 'g)"/>' };
  }
  function rim(P, L, R, c, bolts) {
    var rw = L === 3 ? 30 : L === 2 ? 44 : L === 1 ? 58 : 64, o = P_(circ(c[0], c[1], R), P.ring, rw, 0.95);
    if (L === 3 && bolts) { for (var i = 0; i < 8; i++) { var a = (i + 0.5) / 8 * Math.PI * 2; o += dotC(c[0] + Math.cos(a) * R, c[1] + Math.sin(a) * R, 7, P.bg[1], 0.85); } }
    return o;
  }
  function dialTicks(P, L, R, c) {
    if (L === 3) return P_(ticks(c[0], c[1], R + 26, 120, 14, 10, 40, 5, 25), P.det, 3, 0.62) + P_(circ(c[0], c[1], R + 74), P.det, 1.6, 0.3);
    if (L === 2) return P_(ticks(c[0], c[1], R + 30, 24, 30, 6, 46), P.det, 12, 0.66);
    return '';
  }

  /* ---------- the designs ---------- */
  var C = [512, 512];
  /* W7: the shipped shortcut crop (zoomed 1.5 times into the top right, tilted 6 degrees); its nucleus lands at W7N */
  var W7TF = { a: -6, s: 1.5, t: [-419.2, -274.1], p: [800, 190] };
  var W7N = (function () { var g = { off: [-11.0, -22.6] }, x = (512 + g.off[0]) * 1.5 + W7TF.t[0], y = (512 + g.off[1]) * 1.5 + W7TF.t[1], a = W7TF.a * Math.PI / 180, dx = x - W7TF.p[0], dy = y - W7TF.p[1]; return [W7TF.p[0] + dx * Math.cos(a) - dy * Math.sin(a), W7TF.p[1] + dx * Math.sin(a) + dy * Math.cos(a)]; })();

  var DESIGNS = [
    { id: 'J1', name: 'Field, upright', group: 'Field fixed', note: 'I7 fixed: the field lines centred exactly on the yellow nucleus, axis upright. Every line starts and ends on a circle a clean gap outside the nucleus, like field lines on the Earth. Rings and electron as shipped; the lines pass under the rings with a cut.',
      draw: function (P, L, sz, U, o) { var r = fieldAtom(P, L, sz, U, { tilt: 0, still: o.still }); return { under: r.under, atomSvg: r.atomSvg }; },
      anim: { kind: 'field', tilt: 0 } },
    { id: 'J2', name: 'Field, tilted 10°', group: 'Field fixed', note: 'The same, with the magnetic axis leaning 10 degrees like the Earth\'s (9.2 today). The atom itself stays as shipped, so only the field leans.',
      draw: function (P, L, sz, U, o) { var r = fieldAtom(P, L, sz, U, { tilt: 10, still: o.still }); return { under: r.under, atomSvg: r.atomSvg }; },
      anim: { kind: 'field', tilt: 10 } },
    { id: 'J3', name: 'Field, thin rings', group: 'Field fixed', note: 'Tilted field with the thinner W7 rings at 90 % strength, so the field gets more room and the nucleus reads more as a planet. At 16 px the full XS atom comes back.',
      draw: function (P, L, sz, U, o) { var r = fieldAtom(P, L, sz, U, { tilt: 10, thin: true, still: o.still }); return { under: r.under, atomSvg: r.atomSvg }; },
      anim: { kind: 'field', tilt: 10, thin: true } },
    { id: 'J4', name: 'Field as orbits', group: 'Field fixed', note: 'The rings are replaced by the field: three field lines in the ring colour become the orbits, the electron rides the middle one where the shipped electron sits. The boldest new mark; at 16 px it is a nucleus, four lobes and a dot.',
      draw: function (P, L, sz, U, o) { var r = fieldOrbits(P, L, sz, U, { tilt: 10, still: o.still }); return { under: r.under, atomSvg: r.atomSvg }; },
      anim: { kind: 'orbits', tilt: 10 } },
    { id: 'J5', name: 'Porthole, field', group: 'Porthole', note: 'I4 with I7: a round lens in the tile, the atom centred in it and the field running out to the lens, cut by its edge. A faint grid outside the lens.',
      draw: function (P, L, sz, U, o) {
        var R = L >= 2 ? 404 : 432, ln = lens(P, L, U, R, C), r = fieldAtom(P, L, sz, U, { tilt: 10, scale: L >= 2 ? 0.74 : 0.62, fs: L >= 2 ? 0.92 : 0.8, still: o.still });
        return { under: (L === 3 ? grid(P, 48, 0.14) : '') + ln.face + '<g clip-path="' + ln.clip + '">' + r.under + r.atomSvg + '</g>', over: rim(P, L, R, C, true) };
      }, anim: { kind: 'field', tilt: 10, scale: 0.74, fs: 0.92, lens: 404 } },
    { id: 'J6', name: 'Porthole, zoomed', group: 'Porthole', note: 'Closest to I4: inside the lens the atom is zoomed 1.2 times and set low left, cut by the lens edge; the field is centred on the nucleus there and runs out of the lens.',
      draw: function (P, L, sz, U, o) {
        var R = L >= 2 ? 404 : 432, ln = lens(P, L, U, R, C), zc = L >= 1 ? [452, 566] : C;
        var r = L >= 1 ? fieldAtom(P, L, sz, U, { tilt: 10, c: zc, scale: L >= 2 ? 1.16 : 0.95, fs: L >= 2 ? 1.3 : 1.15, rot: -4, still: o.still, seed: 9 }) : fieldAtom(P, L, sz, U, { tilt: 10, scale: 0.62, fs: 0.8 });
        return { under: (L === 3 ? grid(P, 48, 0.14) : '') + ln.face + '<g clip-path="' + ln.clip + '">' + r.under + r.atomSvg + '</g>', over: rim(P, L, R, C, true) };
      }, anim: { kind: 'field', tilt: 10, scale: 1.16, fs: 1.3, rot: -4, c: [452, 566], lens: 404 } },
    { id: 'J7', name: 'Porthole dial', group: 'Porthole', note: 'The porthole with measurement ticks round its rim like a dial (120 marks, every fifth and tenth longer), the field centred inside. Ticks drop out at 32 and 16 px; the ring and the lens stay.',
      draw: function (P, L, sz, U, o) {
        var R = L >= 2 ? 372 : 432, ln = lens(P, L, U, R, C), r = fieldAtom(P, L, sz, U, { tilt: 10, scale: L >= 2 ? 0.7 : 0.62, fs: L >= 2 ? 0.86 : 0.8, still: o.still });
        return { under: ln.face + '<g clip-path="' + ln.clip + '">' + r.under + r.atomSvg + '</g>' + dialTicks(P, L, R, C), over: rim(P, L, R, C, false) };
      }, anim: { kind: 'field', tilt: 10, scale: 0.7, fs: 0.86, lens: 372 } },
    { id: 'J8', name: 'Field with measurements', group: 'Measurements', note: 'J2 with I5\'s elements: a faint grid, ruler marks along the left and bottom edges, the magnetic equator dashed with an unlabelled tick at each field line (the L-shells), a small scale bar. No text anywhere.',
      draw: function (P, L, sz, U, o) {
        var r = fieldAtom(P, L, sz, U, { tilt: 10, still: o.still }), u = '';
        if (L === 3) u += grid(P, 64, 0.12) + '<g mask="' + maskOf(U, 'eqk', knock(U, r.tier, r.pl, 30)) + '">' + equatorTicks(C, 10, r.Ls, P, r.Rs) + '</g>' + scaleBar(P);
        return { under: u + rulers(P, L) + r.under, atomSvg: r.atomSvg };
      }, anim: { kind: 'field', tilt: 10 } },
    { id: 'J9', name: 'W7 field', group: 'Measurements', note: 'I5 with I7: today\'s W7 crop and tilt with rulers and grid, and the field centred on its nucleus, cut by the tile edge. The most familiar silhouette in the Dock; the zoom leans on the small master at 16 px.',
      draw: function (P, L, sz, U, o) {
        if (L === 0) { var r0 = fieldAtom(P, 0, sz, U, { tilt: 10 }); return { under: r0.under, atomSvg: r0.atomSvg }; }
        var r = fieldAtom(P, L, sz, U, { tilt: 4, thin: true, c: W7N, scale: 1.5, rot: -6, fs: 1.45, still: o.still, seed: 3 });
        return { under: (L === 3 ? grid(P, 64, 0.12) : '') + rulers(P, L) + r.under, atomSvg: r.atomSvg };
      }, anim: { kind: 'field', tilt: 4, thin: true, c: W7N, scale: 1.5, rot: -6, fs: 1.45 } },
    { id: 'J10', name: 'Field-orbit dial', group: 'Porthole', note: 'J4\'s new mark in J7\'s dial: the field as orbits inside the lens, dial ticks round the rim. The most "instrument" of the set.',
      draw: function (P, L, sz, U, o) {
        var R = L >= 2 ? 372 : 432, ln = lens(P, L, U, R, C), r = fieldOrbits(P, L, sz, U, { tilt: 10, k: L >= 2 ? 0.66 : 0.68, still: o.still });
        return { under: ln.face + '<g clip-path="' + ln.clip + '">' + r.under + r.atomSvg + '</g>' + dialTicks(P, L, R, C), over: rim(P, L, R, C, false) };
      }, anim: { kind: 'orbits', tilt: 10, k: 0.66, lens: 372 } },
    { id: 'J11', name: 'I5 for comparison', group: 'Reference', note: 'Round 2\'s I5 unchanged (W7 with measurements), now in P2 and P8, to compare against the field designs.',
      draw: function (P, L, sz, U) {
        var thin = L >= 1, tier = tierFor(sz, thin), u = '';
        if (L === 3) u += grid(P, 64, 0.13);
        u += rulers(P, L);
        if (!thin) return { under: u, atomSvg: atom(U, 'XS', { cx: 512, cy: 512, s: 1, rot: 0 }, P) };
        var a = '<g transform="rotate(-6 800 190) translate(-419.2 -274.1) scale(1.5)">' + atom(U, tier, { cx: 512, cy: 512, s: 1, rot: 0 }, P) + '</g>';
        return { under: u, atomSvg: a };
      }, anim: null }
  ];
  var DES = {}; DESIGNS.forEach(function (d) { DES[d.id] = d; });

  var uid = 0;
  function svg(did, pid, size, opts) {
    opts = opts || {}; size = size || 1024;
    var D = DES[did], P = styled(PAL[pid], opts.style), L = lvlFor(size);
    var U = { id: 'b' + (++uid).toString(36) + '_', defs: {} };
    curL = L; var r = D.draw(P, L, size, U, { still: !!opts.still });
    var body = (r.under || '') + (r.atomSvg || '') + (r.over || '');
    var id = U.id;
    var defs = '<linearGradient id="' + id + 'bg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="' + P.bg[0] + '"/><stop offset="1" stop-color="' + P.bg[1] + '"/></linearGradient>' +
      '<clipPath id="' + id + 'clip"><path d="' + TILE + '"/></clipPath>' +
      (P.glow ? '<radialGradient id="' + id + 'gl" cx="0.5" cy="0.5" r="0.55"><stop offset="0" stop-color="' + P.glow + '" stop-opacity="0.2"/><stop offset="1" stop-color="' + P.glow + '" stop-opacity="0"/></radialGradient>' : '') +
      '<filter id="' + id + 'sh" x="-10%" y="-10%" width="120%" height="125%"><feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000" flood-opacity="0.32"/></filter>' +
      Object.keys(U.defs).map(function (k) { return U.defs[k]; }).join('');
    var rw = L === 3 ? 6 : L === 2 ? 14 : L === 1 ? 22 : 30;
    var tile = '<path d="' + TILE + '" fill="url(#' + id + 'bg)"/>' + (P.glow ? '<rect width="1024" height="1024" fill="url(#' + id + 'gl)" clip-path="url(#' + id + 'clip)"/>' : '') +
      '<g clip-path="url(#' + id + 'clip)">' + body + '</g>' +
      (P.clear ? '<path d="' + TILE + '" fill="none" stroke="#fff" stroke-opacity="0.75" stroke-width="10"/>' : P.rim ? '<path d="' + TILE + '" fill="none" stroke="' + P.rim + '" stroke-opacity="' + (P.tinted || P.auto ? 0.18 : 0.32) + '" stroke-width="' + rw + '" clip-path="url(#' + id + 'clip)"/>' : '');
    if (P.clear) tile = '<g opacity="0.92">' + tile + '</g>';
    var inner = opts.frame === 'mac' ? '<g filter="url(#' + id + 'sh)"><g transform="translate(100 100) scale(0.8046875)">' + tile + '</g></g>' : tile;
    return '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="' + size + '" height="' + size + '" viewBox="0 0 1024 1024"><defs>' + defs + '</defs>' + inner + '</svg>';
  }

  /* ---------- geometry for the animated preview (1024 frame of the full tile) ---------- */
  function anim(did) {
    var D = DES[did], A = D && D.anim; if (!A) return null;
    var c = A.c || C;
    if (A.kind === 'orbits') {
      var k = A.k || 0.86, Q = FO[3], nr = Q.nr * k, Rs = nr + 26 * k;
      return { kind: 'orbits', c: c, tilt: A.tilt, Rs: Rs, nr: nr, lines: Q.fine.concat(Q.bold).map(function (v) { return v * k; }).sort(function (a, b) { return a - b; }), lens: A.lens || 0 };
    }
    var tier = A.thin ? 'W7L' : 'L', s = A.scale || ATOMS[3], g = GEOM[tier], pl = placeAt(tier, c[0], c[1], s, A.rot || 0), nr = g.nr * s, Rs = nr + 24;
    /* the three orbit ellipses of the mark (rx 360, ry 150 at -30, 30 and 90 degrees in the mark frame), for particles on the orbits */
    var orbits = [-30, 30, 90].map(function (deg) { return { a: deg + (A.rot || 0), rx: 360 * s, ry: 150 * s }; });
    return { kind: 'field', sc: s / 0.86, c: c, tilt: A.tilt, Rs: Rs, nr: nr, lines: FIELD[3].Ls.map(function (v) { return v * (A.fs || 1); }), orbits: orbits, oc: markPt(tier, pl, 512, 512), lens: A.lens || 0 };
  }

  /* ---------- mock-ups (round 2, adapted) ---------- */
  function inner(svgStr, x, y, w) { return svgStr.replace(/^<svg[^>]*>/, '<svg x="' + f(x) + '" y="' + f(y) + '" width="' + f(w) + '" height="' + f(w) + '" viewBox="0 0 1024 1024">'); }
  /* generic stand-in app icons (invented, not real apps) */
  var STAND = [
    function () { return '<path d="' + squircle(100, 100, 824) + '" fill="#3D8BF2"/><path d="M250 340h200l40 50h284v330H250z" fill="#E8F2FF"/><path d="M250 430h524v290H250z" fill="#BFDBFF"/>'; },
    function () { return '<path d="' + squircle(100, 100, 824) + '" fill="#F4F6F9"/><circle cx="512" cy="512" r="300" fill="#2F7BF5"/><path d="M212,512h600M512,212v600M300,330c140,60,284,60,424,0M300,694c140,-60,284,-60,424,0" stroke="#fff" stroke-width="18" fill="none"/><ellipse cx="512" cy="512" rx="130" ry="300" stroke="#fff" stroke-width="18" fill="none"/>'; },
    function () { return '<path d="' + squircle(100, 100, 824) + '" fill="#FFFDF5"/><rect x="100" y="100" width="824" height="200" fill="#F6C944"/><path d="M230 420h564M230 520h564M230 620h564M230 720h400" stroke="#C9C2AE" stroke-width="16"/>'; },
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
  /* macOS Dock: icons 64 pt (drawn at 2x, 128 px); ours fourth, with the running dot */
  function dock(did, pid, theme, style) {
    var W = 1160, H = 260, n = 8, sz = 128, gap = 10, dw = n * sz + (n + 1) * gap + 40, x0 = (W - dw) / 2, id = 'dk' + (++uid);
    var s = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '">' + wallpaper(theme, W, H, id);
    s += '<rect x="' + f(x0) + '" y="70" width="' + f(dw) + '" height="168" rx="44" fill="' + (theme === 'light' ? '#FFFFFF' : '#2A2C36') + '" fill-opacity="0.55" stroke="#FFFFFF" stroke-opacity="' + (theme === 'light' ? 0.8 : 0.16) + '" stroke-width="2"/>';
    var k = 0;
    for (var i = 0; i < n; i++) {
      var x = x0 + 20 + gap + i * (sz + gap), y = 78;
      if (i === 3) { s += inner(svg(did, pid, 128, { frame: 'mac', style: style }), x, y, sz); s += '<circle cx="' + f(x + sz / 2) + '" cy="' + (y + sz + 14) + '" r="4.5" fill="' + (theme === 'light' ? '#222' : '#EEE') + '"/>'; }
      else s += standSvg(k++ % STAND.length, x, y, sz);
    }
    return s + '</svg>';
  }
  /* Windows 11 taskbar: 48 px high, icons 24 px at 100 % (also 150 %, 36 px) */
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
  /* macOS 26 icon styles. P2: Default, Dark (kept by IC1's dark entry), Tinted, Clear.
     P8: Default, Dark kept as paper, Dark if macOS makes its own, Dark with the proposed P8N entry, Tinted, Clear. */
  function styleSet(pid) {
    if (pid === 'P8') return [['P8', 'default', 'Default', '#DDE3EC'], ['P8', 'dark', 'Dark, kept as paper', '#15161C'], ['P8', 'darkauto', 'Dark, macOS automatic*', '#15161C'], ['P8N', 'default', 'Dark, proposed P8N', '#15161C'], ['P8', 'tinted', 'Tinted (system)', '#15161C'], ['P8', 'clear', 'Clear (system)', '#6E7C93']];
    if (pid === 'P8N') return [['P8', 'default', 'Default (P8)', '#DDE3EC'], ['P8N', 'default', 'Dark (P8N)', '#15161C'], ['P8N', 'tinted', 'Tinted (system)', '#15161C'], ['P8N', 'clear', 'Clear (system)', '#6E7C93']];
    return [[pid, 'default', 'Default', '#DDE3EC'], [pid, 'dark', 'Dark (kept blue, IC1)', '#15161C'], [pid, 'tinted', 'Tinted (system)', '#15161C'], [pid, 'clear', 'Clear (system)', '#6E7C93']];
  }
  function styles(did, pid) {
    var set = styleSet(pid), W = set.length * 300, H = 320, s = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '">';
    set.forEach(function (e, i) {
      s += '<rect x="' + i * 300 + '" y="0" width="300" height="' + H + '" fill="' + e[3] + '"/>';
      if (e[1] === 'clear') s += '<circle cx="' + (i * 300 + 90) + '" cy="90" r="120" fill="#9BB2D6" fill-opacity="0.7"/><circle cx="' + (i * 300 + 230) + '" cy="250" r="110" fill="#5B6680" fill-opacity="0.7"/>';
      s += inner(svg(did, e[0], 256, { frame: 'mac', style: e[1] }), i * 300 + 22, 20, 256);
      s += '<text x="' + (i * 300 + 150) + '" y="302" text-anchor="middle" font-family="Inter,Helvetica,Arial,sans-serif" font-size="17" fill="' + (e[3] === '#DDE3EC' ? '#333' : '#DDD') + '">' + e[2] + '</text>';
    });
    return s + '</svg>';
  }

  var RECS = [
    { d: 'J2', p: 'P2', first: true, anim: true, why: 'Exactly what you asked for: the I7 field centred on the yellow nucleus like the Earth, leaning 10 degrees, the shipped atom on top, in Orbit night. Dark stays this navy.' },
    { d: 'J7', p: 'P2', anim: true, why: 'Porthole and measurements in one: the field seen through the lens, a dial of ticks round the rim. A circle inside the squircle that still reads at 16 px.' },
    { d: 'J8', p: 'P8', why: 'Chart paper as a printed plate: the field with rulers, grid and the L-shell ticks. Needs the P8N Dark entry.' },
    { d: 'J10', p: 'P8', why: 'The field becomes the orbits, inside the dial: the most distinctive mark of the set, and the cleanest at 16 px.' },
    { d: 'J4', p: 'P2', anim: true, why: 'The new field-orbit mark on its own: nucleus, four lobes and the electron. Bold in the Dock; a bigger step away from today\'s atom.' }
  ];
  var API = { TILE: TILE, dock: dock, taskbar: taskbar, styles: styles, styleSet: styleSet, PALETTES: PALETTES, PAL: PAL, DESIGNS: DESIGNS, RECS: RECS, svg: svg, anim: anim, checks: checks, contrast: contrast, mix: mix, lvlFor: lvlFor, W7N: W7N };
  root.AL3 = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
