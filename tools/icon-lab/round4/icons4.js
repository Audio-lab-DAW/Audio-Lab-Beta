/* AudioLab app icon, round 4 (task IC5): J3 and J4 refined side by side, and hybrids of the two.
   One drawing module for the pick page (browser) and render4.js (Node). Everything is drawn in code as SVG.

   Round 3 (tools/icon-lab/round3/icons3.js) drew the rings from the shipped outline paths (geom.json), so their
   weight could not change. Here the rings are drawn as stroked ellipses with the same geometry (the shipped
   orbits are rx 360, ry 150 in the mark frame at -30, 30 and 90 degrees round the nucleus; the shipped W7 rings
   are about 37 units wide, 32 px in the tile at J3's atom scale 0.86), so the ring weight, the transparency and
   the electron's place become parameters. The dipole field is round 3's (r = L sin^2(theta), centred on the
   nucleus, starting on a surface circle a gap outside it).

   svg(id, pid, size, opts) -> SVG string, viewBox 0 0 1024 1024.
     id      : K1..K5 (J3 refined), M1..M5 (J4 refined), H1, H2 (hybrids)
     size    : pixel size it is seen at; picks the level of detail (>=128 everything, 48..96 bold, <=32 small)
     opts.frame : 'mac' (macOS 26 grid: 824 px tile, 100 px margin, shadow) or 'full' (tile fills the canvas)
     opts.style : 'default' | 'dark'   (Dark: P2 stays the same navy; P8 takes its proposed dark entry P8N)
   The round 3 references (J3 as shipped in v0.270, J4 of round 3, J6, J8, J9, J10) come from icons3.js. */
(function (root) {
  'use strict';

  var PALETTES = [
    { id: 'P2', name: 'Orbit night', bg: ['#132044', '#070910'], ring: '#EAF1FF', nuc: '#FFC43C', el: '#4CC9F0', det: '#6096FF', glow: '#6096FF', rim: '#6096FF' },
    { id: 'P8', name: 'Chart paper', bg: ['#F7F3EA', '#E4DCCA'], ring: '#1B2340', nuc: '#C8610A', el: '#2F6BFF', det: '#1B2340', glow: null, rim: '#1B2340' },
    { id: 'P8N', name: 'Chart paper, night', bg: ['#1E2742', '#0C1020'], ring: '#F3EEE2', nuc: '#F08A2C', el: '#6E9BFF', det: '#D9CDB4', glow: null, rim: '#D9CDB4' }
  ];
  var PAL = {}; PALETTES.forEach(function (p) { PAL[p.id] = p; });

  function hex2rgb(h) { h = h.replace('#', ''); return [parseInt(h.substr(0, 2), 16), parseInt(h.substr(2, 2), 16), parseInt(h.substr(4, 2), 16)]; }
  function rgb2hex(c) { return '#' + c.map(function (v) { v = Math.max(0, Math.min(255, Math.round(v))); return (v < 16 ? '0' : '') + v.toString(16); }).join('').toUpperCase(); }
  function mix(a, b, t) { var x = hex2rgb(a), y = hex2rgb(b); return rgb2hex([0, 1, 2].map(function (i) { return x[i] + (y[i] - x[i]) * t; })); }

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
  function stroke(d, col, w, op, extra) { return '<path d="' + d + '" fill="none" stroke="' + col + '" stroke-width="' + f(w) + '"' + (op != null && op < 1 ? ' stroke-opacity="' + (Math.round(op * 100) / 100) + '"' : '') + ' stroke-linecap="round" stroke-linejoin="round"' + (extra || '') + '/>'; }
  function dot(cx, cy, r, fill, op) { return '<circle cx="' + f(cx) + '" cy="' + f(cy) + '" r="' + f(r) + '" fill="' + fill + '"' + (op != null && op < 1 ? ' fill-opacity="' + op + '"' : '') + '/>'; }
  function mask(U, name, inner, base) { var m = U.id + name; U.defs[m] = '<mask id="' + m + '" maskUnits="userSpaceOnUse" x="-300" y="-300" width="1624" height="1624">' + (base == null ? '<rect x="-300" y="-300" width="1624" height="1624" fill="#fff"/>' : base) + inner + '</mask>'; return 'url(#' + m + ')'; }

  /* ---------- the dipole field (round 3) ---------- */
  function fpt(c, Leq, tilt, th, side) {
    var a = tilt * Math.PI / 180, r = Leq * Math.pow(Math.sin(th), 2), x = side * r * Math.sin(th), y = -r * Math.cos(th);
    return [c[0] + x * Math.cos(a) - y * Math.sin(a), c[1] + x * Math.sin(a) + y * Math.cos(a)];
  }
  function footTh(Leq, Rs) { return Math.asin(Math.min(1, Math.sqrt(Rs / Leq))); }
  /* one side of a field line (side +1 right, -1 left), from the surface circle Rs round to the surface again */
  function fside(c, Leq, tilt, Rs, side, win) {
    var t0 = footTh(Leq, Rs); if (win) t0 = Math.max(t0, win * Math.PI / 180);
    var n = Math.max(32, Math.round(Leq / 4)), pts = [];
    for (var i = 0; i <= n; i++) pts.push(fpt(c, Leq, tilt, t0 + (Math.PI - 2 * t0) * i / n, side));
    return poly(pts);
  }
  function fline(c, Leq, tilt, Rs, win) { return fside(c, Leq, tilt, Rs, 1, win) + fside(c, Leq, tilt, Rs, -1, win); }
  function axisStubs(c, tilt, r0, r1) { var a = tilt * Math.PI / 180, s = Math.sin(a), co = Math.cos(a); return line(c[0] + s * r0, c[1] - co * r0, c[0] + s * r1, c[1] - co * r1) + line(c[0] - s * r0, c[1] + co * r0, c[0] - s * r1, c[1] + co * r1); }
  function trapped(c, Ls, tilt, Rs, P, R, rad, hideR) {
    var o = '';
    Ls.forEach(function (Leq, i) {
      if (i === 0) return;
      var t0 = footTh(Leq, Rs), amp = (Math.PI / 2 - t0) * 0.82;
      [1, -1].forEach(function (side, j) {
        for (var k = 0; k < 14; k++) { var u = R() * 2 - 1, th = Math.PI / 2 + amp * Math.sin(u * Math.PI / 2 + (j ? 0.7 : -0.4)), p = fpt(c, Leq, tilt, th, side);
          if (hideR && Math.hypot(p[0] - c[0], p[1] - c[1]) < hideR) continue;
          if (p[0] < 40 || p[0] > 984 || p[1] < 40 || p[1] > 984) continue;
          o += dot(p[0], p[1], rad, (i + j) % 2 ? P.el : P.nuc, 0.92); break; }
      });
    });
    return o;
  }

  /* ---------- level of detail ---------- */
  function lvlFor(sz) { return sz >= 128 ? 3 : sz >= 48 ? 2 : 1; }

  /* ---------- the atom as stroked ellipses ---------- */
  var RING_ANG = [-30, 30, 90];
  function ellPt(c, s, ang, t) { var a = ang * Math.PI / 180, tt = t * Math.PI / 180, x = 360 * s * Math.cos(tt), y = 150 * s * Math.sin(tt); return [c[0] + x * Math.cos(a) - y * Math.sin(a), c[1] + x * Math.sin(a) + y * Math.cos(a)]; }
  function ellipse(c, s, ang, attrs) { return '<ellipse cx="' + f(c[0]) + '" cy="' + f(c[1]) + '" rx="' + f(360 * s) + '" ry="' + f(150 * s) + '" transform="rotate(' + ang + ' ' + f(c[0]) + ' ' + f(c[1]) + ')" fill="none" ' + attrs + '/>'; }
  /* rings: each ring on its own with its own opacity, so where two cross the crossing shows brighter (J3's transparency).
     style 'glass': a translucent band with a bright thin core, like a glass tube lit from inside */
  function rings(c, s, rot, w, op, P, style) {
    return RING_ANG.map(function (a) {
      var ang = a + rot;
      if (style === 'glass') return ellipse(c, s, ang, 'stroke="' + P.ring + '" stroke-opacity="' + op + '" stroke-width="' + f(w) + '"') + ellipse(c, s, ang, 'stroke="' + P.ring + '" stroke-opacity="0.95" stroke-width="' + f(Math.max(2, w * 0.26)) + '"');
      return ellipse(c, s, ang, 'stroke="' + P.ring + '" stroke-opacity="' + op + '" stroke-width="' + f(w) + '"');
    }).join('');
  }
  function ringKnock(c, s, rot, w) { return RING_ANG.map(function (a) { return ellipse(c, s, a + rot, 'stroke="#000" stroke-width="' + f(w) + '"'); }).join(''); }

  /* nucleus and electron: flat, or a sphere (lit from the top left) for the depth variants; an optional glow */
  function ball(U, cx, cy, r, col, sphere, P) {
    if (!sphere) return dot(cx, cy, r, col);
    var g = U.id + 'sp' + (++U.n);
    U.defs[g] = '<radialGradient id="' + g + '" gradientUnits="userSpaceOnUse" cx="' + f(cx - r * 0.35) + '" cy="' + f(cy - r * 0.4) + '" r="' + f(r * 1.45) + '"><stop offset="0" stop-color="' + mix(col, '#FFFFFF', 0.55) + '"/><stop offset="0.45" stop-color="' + col + '"/><stop offset="1" stop-color="' + mix(col, P.bg[1], 0.3) + '"/></radialGradient>';
    return dot(cx, cy, r, 'url(#' + g + ')');
  }
  function glow(U, c, r0, r1, col, op) {
    var g = U.id + 'gw' + (++U.n);
    U.defs[g] = '<radialGradient id="' + g + '" gradientUnits="userSpaceOnUse" cx="' + f(c[0]) + '" cy="' + f(c[1]) + '" r="' + f(r1) + '"><stop offset="' + (r0 / r1).toFixed(3) + '" stop-color="' + col + '" stop-opacity="' + op + '"/><stop offset="' + ((r0 + (r1 - r0) * 0.35) / r1).toFixed(3) + '" stop-color="' + col + '" stop-opacity="' + (op * 0.35).toFixed(3) + '"/><stop offset="1" stop-color="' + col + '" stop-opacity="0"/></radialGradient>';
    return dot(c[0], c[1], r1, 'url(#' + g + ')');
  }
  /* the feet of the lines fade toward the surface so they do not bunch into a comb round the nucleus */
  function footFade(U, c, Rs, w) {
    var m = U.id + 'ff' + (++U.n);
    U.defs[m] = '<radialGradient id="' + m + 'g" gradientUnits="userSpaceOnUse" cx="' + f(c[0]) + '" cy="' + f(c[1]) + '" r="' + f(Rs + w) + '"><stop offset="0" stop-color="#fff" stop-opacity="0.3"/><stop offset="' + (Rs / (Rs + w)).toFixed(3) + '" stop-color="#fff" stop-opacity="0.3"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></radialGradient>' +
      '<mask id="' + m + '" maskUnits="userSpaceOnUse" x="-300" y="-300" width="1624" height="1624"><rect x="-300" y="-300" width="1624" height="1624" fill="url(#' + m + 'g)"/></mask>';
    return 'url(#' + m + ')';
  }
  /* the field fading out before the tile edge (instead of being cut by it) */
  function edgeFade(U, c, r0, r1) {
    var m = U.id + 'ef' + (++U.n);
    U.defs[m] = '<radialGradient id="' + m + 'g" gradientUnits="userSpaceOnUse" cx="' + f(c[0]) + '" cy="' + f(c[1]) + '" r="' + f(r1) + '"><stop offset="' + (r0 / r1).toFixed(3) + '" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>' +
      '<mask id="' + m + '" maskUnits="userSpaceOnUse" x="-300" y="-300" width="1624" height="1624"><rect x="-300" y="-300" width="1624" height="1624" fill="url(#' + m + 'g)"/></mask>';
    return 'url(#' + m + ')';
  }

  /* ---------- J3 family: rings and the field round them ----------
     p: s (atom scale), rot, ringW, ringOp, ringStyle, tilt, Ls, sw, opIn, opOut (field strength, inner to outer line),
        knock (gap cut in the field round each ring; 0 = the field shows through the rings), edge ('cut' | 'fade'),
        el {ring, t, r}, nucR, nucGlow, sphere, particles, fieldCol */
  function ringDesign(P, L, U, p) {
    var c = p.c || [512, 512], s = p.s, rot = p.rot || 0, q = s / 0.86;
    var ringW = L === 3 ? p.ringW : L === 2 ? Math.max(p.ringW * 1.3, 38) : 70;
    var nr = (p.nucR || 80) * s * (L === 3 ? 1 : L === 2 ? 1.12 : 1.38), er = (p.el.r || 46) * s * (L === 3 ? 1 : L === 2 ? 1.15 : 1.4);
    var Ls, sw, opIn, opOut, win = 0;
    if (L === 3) { Ls = p.Ls; sw = p.sw; opIn = p.opIn; opOut = p.opOut; }
    else if (L === 2) { Ls = p.Ls2 || [p.Ls[1] * 1.15, p.Ls[3], p.Ls[4] * 1.1]; sw = Math.max(11, p.sw * 2.4); opIn = Math.min(0.85, p.opIn + 0.05); opOut = Math.min(0.8, p.opOut + 0.08); }
    else { Ls = [430 * q]; sw = 38; opIn = opOut = 0.62; win = 56; }
    var gap = L === 3 ? 24 : L === 2 ? 30 : 40, Rs = nr + gap, fc = p.fieldCol ? p.fieldCol(P) : P.det;
    var hideR = 350 * q, innerMax = 262 * q;
    var inner = '', outer = '';
    Ls.forEach(function (Leq, i) {
      var t = Ls.length > 1 ? i / (Ls.length - 1) : 0, op = opIn + (opOut - opIn) * t, d = stroke(fline(c, Leq, p.tilt, Rs, win), fc, sw, op);
      if (L >= 2 && Leq <= innerMax && !p.noHide) inner += d; else outer += d;
    });
    var u = '';
    if (inner) u += '<g mask="' + footFade(U, c, Rs, 60 * q) + '">' + inner + '</g>';
    if (outer) u += (L >= 2 && !p.noHide) ? '<g mask="' + mask(U, 'hd' + (++U.n), dot(c[0], c[1], hideR, '#000')) + '">' + outer + '</g>' : '<g mask="' + footFade(U, c, Rs, 60 * q) + '">' + outer + '</g>';
    if (L === 3) u += stroke(axisStubs(c, p.tilt, nr + 12, Math.min(Rs + 46, nr + 70)), fc, 4.4, 0.6);
    if (L === 3 && p.particles) u += trapped(c, Ls, p.tilt, Rs, P, rng(p.seed || 7), 7.5, hideR);
    if (p.edge === 'fade') u = '<g mask="' + edgeFade(U, [512, 512], 380, 560) + '">' + u + '</g>';
    if (p.knock !== 0) u = '<g mask="' + mask(U, 'kn' + (++U.n), ringKnock(c, s, rot, ringW + 2 * (L === 3 ? (p.knock || 15) : 20))) + '">' + u + '</g>';
    /* electron on ring p.el.ring at parameter p.el.t (degrees); a halo cut in the rings round it */
    var ep = ellPt(c, s, RING_ANG[p.el.ring || 0] + rot, p.el.t || 0), halo = er + (L === 3 ? 12 : 16) * s;
    var a = '';
    if (p.nucGlow) a += glow(U, c, nr, nr * (L === 3 ? 3.2 : 2.4), P.glow ? mix(P.nuc, '#FFFFFF', 0.1) : P.nuc, P.glow ? 0.34 : 0.22);
    var rg = rings(c, s, rot, ringW, L === 3 ? p.ringOp : Math.min(0.95, p.ringOp + 0.04), P, L === 3 ? p.ringStyle : null);
    a += '<g mask="' + mask(U, 'eh' + (++U.n), dot(ep[0], ep[1], halo, '#000')) + '">' + rg + '</g>';
    a += ball(U, c[0], c[1], nr, P.nuc, p.sphere && L >= 2, P) + ball(U, ep[0], ep[1], er, P.el, p.sphere && L >= 2, P);
    if (p.shadow && L === 3) a = '<g filter="url(#' + U.id + 'ash)">' + a + '</g>';
    return { under: u, atom: a };
  }

  /* ---------- J4 family: the field lines are the orbits ----------
     p: k (scale), tilt, bold [Leq], bw [width], bop (opacity of the bold lines, each side drawn on its own so
        overlaps show brighter), fine [Leq], fw, fop, fineOut (fine lines run on past the tile edge), gap (surface
        gap; small = the lines come out of the poles), el {line, th, r}, nucR, nucGlow, sphere, particles, ringsUnder */
  function orbitDesign(P, L, U, p) {
    var c = p.c || [512, 512], k = p.k || 0.86, tilt = p.tilt;
    var B = L === 3 ? { bold: p.bold, bw: p.bw, fine: p.fine || [] } : L === 2 ? { bold: p.bold2 || [236, 380, 540], bw: p.bw2 || [30, 27, 24], fine: p.fine2 || [] } : { bold: [270, 500], bw: [48, 44], fine: [] };
    var nr = (p.nucR || 88) * k * (L === 3 ? 1 : L === 2 ? 1.09 : 1.27), er = (p.el.r || 46) * k * (L === 3 ? 1 : L === 2 ? 1.13 : 1.39);
    var gap = p.gap != null ? p.gap : (L === 3 ? 26 : L === 2 ? 34 : 44), Rs = nr + gap * k;
    var bold = B.bold.map(function (v) { return v * k; }), fine = B.fine.map(function (v) { return v * k; });
    var mid = bold[Math.min(p.el.line != null ? p.el.line : 1, bold.length - 1)], ep = fpt(c, mid, tilt, (p.el.th || 60) * Math.PI / 180, p.el.side || 1);
    var u = '';
    if (p.ringsUnder) u += p.ringsUnder(P, L, U, c);
    if (fine.length) {
      var d = '';
      fine.forEach(function (Leq, i) { var t = fine.length > 1 ? i / (fine.length - 1) : 0; d += stroke(fline(c, Leq, tilt, Rs), P.det, L === 3 ? (p.fw || 4.4) : 11, (p.fop || 0.54) * (1 - 0.35 * t)); });
      u += '<g mask="' + footFade(U, c, Rs, 90 * k) + '">' + d + '</g>';
    }
    if (L === 3 && p.stubs !== false) u += stroke(axisStubs(c, tilt, nr + 12, nr + 60), P.det, 4.4, 0.6);
    if (L === 3 && p.particles) u += trapped(c, fine.length ? fine : bold, tilt, Rs, P, rng(p.seed || 5), 7.5, nr + 80);
    var b = '', bop = L === 3 ? (p.bop || 0.96) : Math.min(0.96, (p.bop || 0.96) + 0.1);
    bold.forEach(function (Leq, i) { var w = B.bw[i] * k; [1, -1].forEach(function (sd) { b += stroke(fside(c, Leq, tilt, Rs, sd), P.ring, w, bop); }); });
    if (p.edge === 'fade') u = '<g mask="' + edgeFade(U, [512, 512], 380, 560) + '">' + u + '</g>';
    var halo = (p.el.halo || 64) * k * (L === 3 ? 1 : 1.15);
    u = '<g mask="' + mask(U, 'eh' + (++U.n), dot(ep[0], ep[1], halo, '#000')) + '">' + u + b + '</g>';
    var a = '';
    if (p.nucGlow) a += glow(U, c, nr, nr * (L === 3 ? 3.0 : 2.3), P.glow ? mix(P.nuc, '#FFFFFF', 0.1) : P.nuc, P.glow ? 0.34 : 0.22);
    a += ball(U, c[0], c[1], nr, P.nuc, p.sphere && L >= 2, P) + ball(U, ep[0], ep[1], er, P.el, p.sphere && L >= 2, P);
    if (p.shadow && L === 3) a = '<g filter="url(#' + U.id + 'ash)">' + a + '</g>';
    return { under: u, atom: a };
  }

  /* ---------- the designs ---------- */
  /* J3 as shipped, in these terms: atom 0.86, W7 rings about 32 px at 90 %, field six lines 4.4 px at 59 %, tilt 10 */
  var J3B = { s: 0.86, ringW: 32, ringOp: 0.9, tilt: 10, Ls: [150, 212, 300, 430, 620, 900], sw: 4.4, opIn: 0.59, opOut: 0.59, knock: 15, el: { ring: 0, t: 0, r: 46 }, particles: true };
  function X(base, over) { var o = {}, k; for (k in base) o[k] = base[k]; for (k in over) o[k] = over[k]; return o; }
  var J4B = { k: 0.86, tilt: 10, bold: [236, 360, 520], bw: [22, 19, 16], fine: [296, 438, 700], el: { line: 1, th: 60, r: 46, halo: 64 }, nucR: 88, particles: true };

  var DESIGNS = [
    /* ----- J3 refined ----- */
    { id: 'K1', fam: 'J3', name: 'Lighter rings', short: 'J3 with lighter, more see-through rings',
      note: 'J3 with the rings a quarter lighter (24 px instead of 32) and more transparent (78 % instead of 90 %), so the crossings glow and the field shows round the nucleus. The field itself as J3: six lines, tilt 10°.',
      p: X(J3B, { ringW: 24, ringOp: 0.78, knock: 12 }), kind: 'ring' },
    { id: 'K2', fam: 'J3', name: 'Glass rings', short: 'rings as glass tubes: translucent band, bright core',
      note: 'Each ring is a translucent band (42 %) with a thin bright core: the transparency you liked, taken further, like a glass tube lit from inside. A soft glow round the nucleus. The field passes under the rings without a cut, so it is seen through the glass.',
      p: X(J3B, { ringW: 30, ringOp: 0.42, ringStyle: 'glass', knock: 0, nucGlow: true, opIn: 0.62, opOut: 0.5 }), kind: 'ring' },
    { id: 'K3', fam: 'J3', name: 'Wide field', short: 'smaller atom, the field runs out past the tile edge',
      note: 'The atom 10 % smaller, the field bigger: seven lines, the outer ones running out past the tile edge and cut by it, like a magnetosphere bigger than the picture. The inner lines stronger than the outer ones. Tilt 12°.',
      p: X(J3B, { s: 0.77, ringW: 26, ringOp: 0.86, tilt: 12, Ls: [150, 215, 305, 430, 610, 860, 1220], sw: 4.6, opIn: 0.74, opOut: 0.4, knock: 13, nucGlow: true, Ls2: [262, 470, 820] }), kind: 'ring' },
    { id: 'K4', fam: 'J3', name: 'Planet', short: 'bigger lit nucleus, smaller electron at the top',
      note: 'The nucleus grows by a fifth and is lit like a planet (sphere shading and glow); the electron is smaller and rides the top of the upright ring. The field starts on the planet\'s surface. Rings 26 px at 84 %.',
      p: X(J3B, { ringW: 26, ringOp: 0.84, nucR: 96, nucGlow: true, sphere: true, el: { ring: 2, t: 157, r: 38 }, Ls: [176, 240, 330, 460, 650, 920] }), kind: 'ring' },
    { id: 'K5', fam: 'J3', name: 'Depth (macOS 26)', short: 'K1 with a glass edge, lit spheres and a soft shadow',
      note: 'K1 with depth in the macOS 26 manner: a light edge along the top of the tile and a faint sheen, the nucleus and electron lit as spheres, a soft shadow under the atom. On macOS 26 the system can add its own glass edge instead (Icon Composer\'s specular); the drawn one is for the flat files.',
      p: X(J3B, { ringW: 24, ringOp: 0.8, knock: 12, sphere: true, shadow: true, nucGlow: true }), kind: 'ring', glass: true },
    /* ----- J4 refined ----- */
    { id: 'M1', fam: 'J4', name: 'Lighter orbits', short: 'J4 with thinner field orbits, more fine lines',
      note: 'J4 with the three field orbits a quarter thinner (17, 15, 13 px), four fine field lines behind them instead of three. More air between the lobes; the electron a touch smaller.',
      p: X(J4B, { bw: [17, 15, 13], fine: [300, 445, 640, 900], el: { line: 1, th: 60, r: 42, halo: 60 } }), kind: 'orbit' },
    { id: 'M2', fam: 'J4', name: 'Transparent orbits', short: 'J3\'s transparency on J4: orbits at 70 %',
      note: 'J3\'s transparency on J4: each half of each orbit drawn on its own at 70 %, so where they gather at the poles they glow brighter. A soft glow round the nucleus, fine lines a little stronger.',
      p: X(J4B, { bw: [22, 19, 16], bop: 0.7, fop: 0.62, nucGlow: true }), kind: 'orbit' },
    { id: 'M3', fam: 'J4', name: 'Field to the edge', short: 'three orbits plus fine lines out past the tile edge',
      note: 'The three orbits stay, and fine field lines run on past the tile edge, cut by it, so the orbits sit inside a bigger field (as in K3). Tilt 12°, nucleus glow.',
      p: X(J4B, { tilt: 12, bw: [20, 17, 14], fine: [300, 445, 640, 880, 1200], fop: 0.6, nucGlow: true, fine2: [820] }), kind: 'orbit' },
    { id: 'M4', fam: 'J4', name: 'From the poles', short: 'orbits come straight out of the nucleus',
      note: 'No gap at the surface: the orbits come straight out of the nucleus at its poles, like real field lines leaving a planet. Reads as one connected mark; the poles become two bright points.',
      p: X(J4B, { gap: -8, bw: [19, 17, 15], stubs: false, nucR: 92 }), kind: 'orbit' },
    { id: 'M5', fam: 'J4', name: 'Depth (macOS 26)', short: 'M1 with a glass edge, lit spheres and a soft shadow',
      note: 'M1 with the same depth as K5: a light edge along the top of the tile, the nucleus and electron lit as spheres, a soft shadow under the mark.',
      p: X(J4B, { bw: [17, 15, 13], fine: [300, 445, 640, 900], el: { line: 1, th: 60, r: 42, halo: 60 }, sphere: true, shadow: true, nucGlow: true }), kind: 'orbit', glass: true },
    /* ----- hybrids ----- */
    { id: 'H1', fam: 'Hybrid', name: 'Rings behind orbits', short: 'J3\'s rings faint and transparent, J4\'s orbits in front',
      note: 'J3\'s three rings drawn thin and transparent (14 px at 38 %) behind J4\'s field orbits in the ring colour. Up close you see the atom you know inside the field; from far away it reads as J4.',
      p: X(J4B, { bw: [18, 16, 14], fine: [], particles: false, nucGlow: true, ringsUnder: function (P, L, U, c) { return rings(c, 0.86, 0, L === 3 ? 14 : 26, L === 3 ? 0.38 : 0.42, P); } }), kind: 'orbit' },
    { id: 'H2', fam: 'Hybrid', name: 'Field through rings', short: 'J3\'s transparent atom over strong field orbits',
      note: 'J3\'s atom with transparent rings (26 px at 72 %) over a field drawn as strong as J4\'s, in a light blue, without the cut under the rings, so the field shows through them. The electron stays where it is today.',
      p: X(J3B, { ringW: 26, ringOp: 0.72, knock: 0, Ls: [236, 360, 520, 720, 980], sw: 11, opIn: 0.8, opOut: 0.5, noHide: true, particles: false, fieldCol: function (P) { return P.glow ? mix(P.det, P.ring, 0.45) : P.det; }, Ls2: [236, 380, 560] }), kind: 'ring' }
  ];
  var DES = {}; DESIGNS.forEach(function (d) { DES[d.id] = d; });

  var uid = 0;
  function svg(id, pid, size, opts) {
    opts = opts || {}; size = size || 1024;
    var D = DES[id], P = PAL[(opts.style === 'dark' && pid === 'P8') ? 'P8N' : pid], L = lvlFor(size);
    var U = { id: 'r' + (++uid).toString(36) + '_', defs: {}, n: 0 };
    var r = D.kind === 'ring' ? ringDesign(P, L, U, D.p) : orbitDesign(P, L, U, D.p);
    var body = r.under + r.atom;
    var id_ = U.id;
    var defs = '<linearGradient id="' + id_ + 'bg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="' + P.bg[0] + '"/><stop offset="1" stop-color="' + P.bg[1] + '"/></linearGradient>' +
      '<clipPath id="' + id_ + 'clip"><path d="' + TILE + '"/></clipPath>' +
      (P.glow ? '<radialGradient id="' + id_ + 'gl" cx="0.5" cy="0.5" r="0.55"><stop offset="0" stop-color="' + P.glow + '" stop-opacity="0.2"/><stop offset="1" stop-color="' + P.glow + '" stop-opacity="0"/></radialGradient>' : '') +
      '<filter id="' + id_ + 'sh" x="-10%" y="-10%" width="120%" height="125%"><feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000" flood-opacity="0.32"/></filter>' +
      '<filter id="' + id_ + 'ash" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="14" stdDeviation="16" flood-color="#000" flood-opacity="' + (P.glow || P.id === 'P8N' ? 0.55 : 0.22) + '"/></filter>' +
      (D.glass ? '<linearGradient id="' + id_ + 'gs" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="' + (P.glow || P.id === 'P8N' ? 0.13 : 0.35) + '"/><stop offset="0.42" stop-color="#fff" stop-opacity="0"/></linearGradient>' +
        '<linearGradient id="' + id_ + 'ge" x1="0" y1="0" x2="0.25" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.75"/><stop offset="0.3" stop-color="#fff" stop-opacity="0.1"/><stop offset="0.7" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity="0.18"/></linearGradient>' : '') +
      Object.keys(U.defs).map(function (k) { return U.defs[k]; }).join('');
    var rw = L === 3 ? 6 : L === 2 ? 14 : 22;
    var tile = '<path d="' + TILE + '" fill="url(#' + id_ + 'bg)"/>' + (P.glow ? '<rect width="1024" height="1024" fill="url(#' + id_ + 'gl)" clip-path="url(#' + id_ + 'clip)"/>' : '') +
      '<g clip-path="url(#' + id_ + 'clip)">' + body + '</g>' +
      (D.glass && L >= 2 ? '<path d="' + TILE + '" fill="url(#' + id_ + 'gs)"/><path d="' + TILE + '" fill="none" stroke="url(#' + id_ + 'ge)" stroke-width="' + (L === 3 ? 10 : 18) + '" clip-path="url(#' + id_ + 'clip)"/>' :
        P.rim ? '<path d="' + TILE + '" fill="none" stroke="' + P.rim + '" stroke-opacity="0.32" stroke-width="' + rw + '" clip-path="url(#' + id_ + 'clip)"/>' : '');
    var inner = opts.frame === 'mac' ? '<g filter="url(#' + id_ + 'sh)"><g transform="translate(100 100) scale(0.8046875)">' + tile + '</g></g>' : tile;
    return '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="' + size + '" height="' + size + '" viewBox="0 0 1024 1024"><defs>' + defs + '</defs>' + inner + '</svg>';
  }

  /* ---------- mock-ups (round 3's, taking any drawing function) ---------- */
  function inner(svgStr, x, y, w) { return svgStr.replace(/^<svg[^>]*>/, '<svg x="' + f(x) + '" y="' + f(y) + '" width="' + f(w) + '" height="' + f(w) + '" viewBox="' + (svgStr.match(/viewBox="([^"]*)"/) || [0, '0 0 1024 1024'])[1] + '">'); }
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
  function standSvg(i, x, y, w, full) { var c = 'st' + (++uid), sq = full ? squircle(0, 0, 1024) : squircle(100, 100, 824), body = STAND[i]().replace(squircle(100, 100, 824), sq); return '<svg x="' + f(x) + '" y="' + f(y) + '" width="' + f(w) + '" height="' + f(w) + '" viewBox="0 0 1024 1024"><defs><clipPath id="' + c + '"><path d="' + sq + '"/></clipPath></defs><g clip-path="url(#' + c + ')">' + (full ? '<g transform="translate(-124.3 -124.3) scale(1.2427)">' + STAND[i]() + '</g>' : body) + '</g></svg>'; }
  function wallpaper(theme, W, H, id) {
    return theme === 'light'
      ? '<defs><linearGradient id="' + id + '" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#EEF1F6"/><stop offset="0.6" stop-color="#D9E1EC"/><stop offset="1" stop-color="#C9D4E4"/></linearGradient></defs><rect width="' + W + '" height="' + H + '" fill="url(#' + id + ')"/>'
      : '<defs><linearGradient id="' + id + '" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1A1C26"/><stop offset="0.6" stop-color="#12131A"/><stop offset="1" stop-color="#0A0B10"/></linearGradient></defs><rect width="' + W + '" height="' + H + '" fill="url(#' + id + ')"/>';
  }
  /* macOS Dock: icons 64 pt drawn at 2x (128 px); ours fourth, with the running dot. draw(size) -> mac-frame SVG */
  function dock(draw, theme) {
    var W = 1160, H = 260, n = 8, sz = 128, gap = 10, dw = n * sz + (n + 1) * gap + 40, x0 = (W - dw) / 2, id = 'dk' + (++uid);
    var s = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '">' + wallpaper(theme, W, H, id);
    s += '<rect x="' + f(x0) + '" y="70" width="' + f(dw) + '" height="168" rx="44" fill="' + (theme === 'light' ? '#FFFFFF' : '#2A2C36') + '" fill-opacity="0.55" stroke="#FFFFFF" stroke-opacity="' + (theme === 'light' ? 0.8 : 0.16) + '" stroke-width="2"/>';
    var k = 0;
    for (var i = 0; i < n; i++) {
      var x = x0 + 20 + gap + i * (sz + gap), y = 78;
      if (i === 3) { s += inner(draw(128), x, y, sz); s += '<circle cx="' + f(x + sz / 2) + '" cy="' + (y + sz + 14) + '" r="4.5" fill="' + (theme === 'light' ? '#222' : '#EEE') + '"/>'; }
      else s += standSvg(k++ % STAND.length, x, y, sz);
    }
    return s + '</svg>';
  }
  /* macOS 26 Default and Dark side by side. P2: Dark is the same navy (IC1's dark entry). P8: Dark takes P8N. */
  function styles(drawStyled, pid) {
    var set = [['default', 'Default', '#DDE3EC'], ['dark', pid === 'P8' ? 'Dark (P8N entry)' : 'Dark (stays navy)', '#15161C']];
    var W = set.length * 300, H = 320, s = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '">';
    set.forEach(function (e, i) {
      s += '<rect x="' + i * 300 + '" y="0" width="300" height="' + H + '" fill="' + e[2] + '"/>';
      s += inner(drawStyled(256, e[0]), i * 300 + 22, 20, 256);
      s += '<text x="' + (i * 300 + 150) + '" y="302" text-anchor="middle" font-family="Inter,Helvetica,Arial,sans-serif" font-size="17" fill="' + (i ? '#DDD' : '#333') + '">' + e[1] + '</text>';
    });
    return s + '</svg>';
  }

  var RECS = [
    { d: 'K1', p: 'P2', role: 'main', why: 'The safest step from the shipped J3: the same atom, the same field, with lighter and more transparent rings. The crossings glow, the field reads round the nucleus, and it still holds up at 64 px.' },
    { d: 'M2', p: 'P2', role: 'alt', why: 'J4 with J3\'s transparency: the orbits gather and glow at the poles. The boldest silhouette in the Dock and the clearest at small sizes of the big icons.' },
    { d: 'H1', p: 'P2', role: 'alt', why: 'The hybrid that keeps both: the atom you know, faint, inside J4\'s field orbits. A good alternative if you cannot decide between J3 and J4.' },
    { d: 'K3', p: 'P2', role: 'main', why: 'J3 with the bigger field running out of the tile: the most "Earth\'s magnetosphere" of the J3 row.' }
  ];
  var API = { PALETTES: PALETTES, PAL: PAL, DESIGNS: DESIGNS, DES: DES, RECS: RECS, svg: svg, dock: dock, styles: styles, standSvg: standSvg, wallpaper: wallpaper, inner: inner, squircle: squircle, mix: mix, lvlFor: lvlFor, fpt: fpt, footTh: footTh };
  root.AL4 = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
