/* AudioLab app icon, round 5c (task IC8): M5d as the Earth (the yellow nucleus) and the Moon (the blue electron).

   Built next to round 5 (tools/icon-lab/round5/icons5.js, read only: its palettes, squircle, colour mix and the Dock
   and macOS-style mock-ups are reused through its API; the tile and depth code below is a copy of its svg()).

   What is new here: the field drawn in 3D.
     - Every field line is a dipole line r = L sin^2(theta) (L in Earth radii, theta from magnetic north) in a meridian
       plane at azimuth phi round the magnetic axis. The point goes through: the dipole tilt (north leans right by
       'tilt' degrees), optionally the magnetosphere's deformation (day side squeezed, night side stretched, open
       lobe lines into the tail), then a camera that looks from slightly above (elevation 'e').
     - Lines are TAPERED by depth: each one is a filled ribbon whose width and brightness follow its depth z (toward
       you: wider, full colour; away from you: thinner, mixed toward the tile). Parts behind the Earth are drawn
       before the Earth (so the planet hides them), parts in front after it (so they pass over it).
     - The Moon's orbit is a tapered ribbon too: a circle in its own plane, inclined 5 degrees to the ecliptic
       (a hairline), seen from 13 degrees above, its far half passing behind the Earth.
     - The Sun (E4, E7, E8): light from the left; Earth and Moon get a day half and a night half with a soft
       terminator (both show the same phase, as they must: the Sun is effectively infinitely far).
     - Van Allen belts (E5, E8): the region between two dipole shells, inner L 1.2 to 2 (peak 1.5), outer L 3 to 6
       (peak 4.5), shaded in nested bands so they are densest at the peak.
     - Magnetopause (E4, E8): Shue et al. (1997), r = r0 (2 / (1 + cos theta))^alpha, alpha 0.58.

   svg(id, pid, size, opts) -> SVG string, viewBox 0 0 1024 1024 (opts.frame 'mac' | 'full', opts.style 'default' | 'dark').
   scene(spec, P, U) is the shared drawer; small5c.js calls it with its own specs for 32 px and below. */
(function (root) {
  'use strict';
  var A5 = root.AL5 || require('../round5/icons5.js');
  var PAL = A5.PAL, mix = A5.mix, squircle = A5.squircle;
  var PI = Math.PI, D2R = PI / 180;
  function f(n) { return (Math.round(n * 10) / 10).toString(); }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  var TILE = squircle(0, 0, 1024, 5);

  /* ---------- geometry ---------- */
  function dip3(L, th, phi) { var r = L * Math.pow(Math.sin(th), 2); return [r * Math.sin(th) * Math.cos(phi), r * Math.cos(th), r * Math.sin(th) * Math.sin(phi)]; }
  /* magnetic frame -> world (x right = anti-sunward, y up = north, z toward the viewer): dipole tilt in the x-y plane */
  function tiltV(v, tilt) { var a = tilt * D2R, c = Math.cos(a), s = Math.sin(a); return [v[0] * c + v[1] * s, -v[0] * s + v[1] * c, v[2]]; }
  /* world -> screen: elevation e (look from above: the far side rises), nr px per Earth radius, centre c */
  function cam(v, S) { var e = S.e * D2R, y = v[1] * Math.cos(e) - v[2] * Math.sin(e), z = v[1] * Math.sin(e) + v[2] * Math.cos(e);
    return [S.c[0] + v[0] * S.nr, S.c[1] - y * S.nr, z * S.nr]; }
  /* the magnetosphere's deformation (world frame, units Earth radii). Day side (x < 0): squeezed toward the Earth
     so the outermost closed line stays inside the magnetopause; night side: stretched along x, more for outer lines,
     and thinned toward the plasma sheet. */
  function deform(v, L, M) {
    var x = v[0], y = v[1], z = v[2];
    if (x < 0) { var q = 1 - M.sq * Math.pow(clamp(L / M.Lmax, 0, 1), 2) * clamp(-x / L, 0, 1); return [x * q, y * (1 - M.sq * 0.35 * Math.pow(L / M.Lmax, 2) * clamp(-x / L, 0, 1)), z * q]; }
    var s = 1 + M.st * L * L, u = clamp(x / L, 0, 1), th = 1 - M.thin * Math.pow(clamp((L - 2.5) / (M.Lmax - 2.5), 0, 1), 1.5) * u;
    return [x * (1 + (s - 1) * u), y * th, z * (1 + (s - 1) * u * 0.6)];
  }
  /* one half of a field line (side +1 / -1 = meridian at phi / phi+180) as screen points [x, y, z] */
  function halfLine(S, L, phi, side, r0) {
    var t0 = Math.asin(Math.min(1, Math.sqrt(r0 / L))), n = Math.max(40, Math.round(L * 14)), pts = [];
    for (var i = 0; i <= n; i++) { var th = t0 + (PI - 2 * t0) * i / n, v = tiltV(dip3(L, th, phi + (side < 0 ? PI : 0)), S.tilt); if (S.ms) v = deform(v, L, S.ms); pts.push(cam(v, S)); }
    return pts;
  }

  /* ---------- tapered ribbons ---------- */
  /* pts [[x,y,z]...]; width w0 (px at z = 0), taper k (0 flat .. 0.7 strong), colour col faded toward bgc by depth.
     Returns { back, front }: chunks with z < 0 and z >= 0. Each chunk is a filled polygon of solid colour (no
     opacity, so chunks do not show seams), with a hairline stroke of its own colour to close the joins. */
  function ribbon(pts, w0, col, bgc, k, fade, Z, ends) {
    var n = pts.length, out = { back: '', front: '' };
    if (n < 2) return out;
    var W = pts.map(function (p) { var zn = clamp(p[2] / Z, -1, 1); return Math.max(0.6, w0 * (1 + k * zn)); });
    var N = pts.map(function (p, i) { var a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1; return [-dy / l, dx / l]; });
    if (PLAIN) {
      /* small sizes: one stroke per run of the same side (behind / in front), no chunks, so no seams */
      var run = [], side = null, flush = function () { if (run.length > 1) { var zm = run.reduce(function (t, p) { return t + p[2]; }, 0) / run.length, zn = clamp(zm / Z, -1, 1), cc = mix(col, bgc, fade * (1 - zn) / 2), ww = Math.max(0.6, w0 * (1 + k * zn));
        var d = '<path d="M' + run.map(function (p) { return f2(p[0]) + ',' + f2(p[1]); }).join('L') + '" fill="none" stroke="' + cc + '" stroke-width="' + f2(ww) + '" stroke-linecap="' + (ends ? 'round' : 'butt') + '" stroke-linejoin="round"/>'; if (side) out.front += d; else out.back += d; } };
      pts.forEach(function (p) { var sd = p[2] >= 0; if (side !== null && sd !== side) { run.push(p); flush(); run = [run[run.length - 1]]; } else run.push(p); side = sd; });
      flush(); return out;
    }
    var CH = 4;
    for (var i = 0; i < n - 1; i += CH) {
      var j = Math.min(n - 1, i + CH), L = [], R = [], zs = 0;
      for (var m = i; m <= j; m++) { var p = pts[m], h = W[m] / 2; L.push(f(p[0] + N[m][0] * h) + ',' + f(p[1] + N[m][1] * h)); R.push(f(p[0] - N[m][0] * h) + ',' + f(p[1] - N[m][1] * h)); zs += p[2]; }
      zs /= (j - i + 1);
      var zn = clamp(zs / Z, -1, 1), c = mix(col, bgc, fade * (1 - zn) / 2);
      var d = '<path d="M' + L.join('L') + 'L' + R.reverse().join('L') + 'Z" fill="' + c + '" stroke="' + c + '" stroke-width="' + SEAM + '" stroke-linejoin="round"/>';
      if (zs < 0) out.back += d; else out.front += d;
    }
    if (ends) [0, n - 1].forEach(function (m) { var p = pts[m], zn = clamp(p[2] / Z, -1, 1), c = mix(col, bgc, fade * (1 - zn) / 2), d = '<circle cx="' + f(p[0]) + '" cy="' + f(p[1]) + '" r="' + f(W[m] / 2) + '" fill="' + c + '"/>'; if (p[2] < 0) out.back += d; else out.front += d; });
    return out;
  }
  var SEAM = 0.8, PLAIN = false;
  function f2(n) { return (Math.round(n * 100) / 100).toString(); }
  function add(acc, r) { acc.back += r.back; acc.front += r.front; }

  /* ---------- spheres ---------- */
  function ball(U, cx, cy, r, col, P, lx, ly) {
    var g = U.id + 'sp' + (++U.n);
    U.defs[g] = '<radialGradient id="' + g + '" gradientUnits="userSpaceOnUse" cx="' + f(cx + r * lx * 0.532) + '" cy="' + f(cy + r * ly * 0.532) + '" r="' + f(r * 1.45) + '"><stop offset="0" stop-color="' + mix(col, '#FFFFFF', 0.55) + '"/><stop offset="0.45" stop-color="' + col + '"/><stop offset="1" stop-color="' + mix(col, P.bg[1], 0.3) + '"/></radialGradient>';
    return '<circle cx="' + f(cx) + '" cy="' + f(cy) + '" r="' + f(r) + '" fill="url(#' + g + ')"/>';
  }
  /* a sphere lit by the Sun from the left, the Sun beta degrees toward the viewer (beta > 0: more than half lit).
     The night half keeps a little of its colour so the disc still reads; the terminator is softened. */
  function sunBall(U, cx, cy, r, col, P, beta, soft) {
    var id = U.id + 'sb' + (++U.n), night = P.glow ? mix(col, '#0A0F22', 0.7) : mix(col, '#2A2A3A', 0.55);
    var rx = r * Math.sin(beta * D2R), pts = [];
    for (var i = 0; i <= 36; i++) { var t = -PI / 2 + PI * i / 36; pts.push(f(cx - r * Math.cos(t)) + ',' + f(cy + r * Math.sin(t))); }
    for (i = 0; i <= 36; i++) { t = PI / 2 - PI * i / 36; pts.push(f(cx + rx * Math.cos(t)) + ',' + f(cy + r * Math.sin(t))); }
    U.defs[id + 'c'] = '<clipPath id="' + id + 'c"><circle cx="' + f(cx) + '" cy="' + f(cy) + '" r="' + f(r) + '"/></clipPath>';
    U.defs[id + 'f'] = '<filter id="' + id + 'f" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="' + f(Math.max(0.3, r * (soft || 0.07))) + '"/></filter>';
    U.defs[id + 'g'] = '<radialGradient id="' + id + 'g" gradientUnits="userSpaceOnUse" cx="' + f(cx - r * 0.45) + '" cy="' + f(cy - r * 0.2) + '" r="' + f(r * 1.5) + '"><stop offset="0" stop-color="' + mix(col, '#FFFFFF', 0.5) + '"/><stop offset="0.45" stop-color="' + col + '"/><stop offset="1" stop-color="' + mix(col, night, 0.4) + '"/></radialGradient>';
    return '<circle cx="' + f(cx) + '" cy="' + f(cy) + '" r="' + f(r) + '" fill="' + night + '"/>' +
      '<g clip-path="url(#' + id + 'c)"><path d="M' + pts.join('L') + 'Z" fill="url(#' + id + 'g)" filter="url(#' + id + 'f)"/></g>';
  }
  function glow(U, c, r0, r1, col, op) {
    var g = U.id + 'gw' + (++U.n);
    U.defs[g] = '<radialGradient id="' + g + '" gradientUnits="userSpaceOnUse" cx="' + f(c[0]) + '" cy="' + f(c[1]) + '" r="' + f(r1) + '"><stop offset="' + (r0 / r1).toFixed(3) + '" stop-color="' + col + '" stop-opacity="' + op + '"/><stop offset="' + ((r0 + (r1 - r0) * 0.35) / r1).toFixed(3) + '" stop-color="' + col + '" stop-opacity="' + (op * 0.35).toFixed(3) + '"/><stop offset="1" stop-color="' + col + '" stop-opacity="0"/></radialGradient>';
    return '<circle cx="' + f(c[0]) + '" cy="' + f(c[1]) + '" r="' + f(r1) + '" fill="url(#' + g + ')"/>';
  }
  function maskOut(U, inner) { var m = U.id + 'm' + (++U.n); U.defs[m] = '<mask id="' + m + '" maskUnits="userSpaceOnUse" x="-300" y="-300" width="1624" height="1624"><rect x="-300" y="-300" width="1624" height="1624" fill="#fff"/>' + inner + '</mask>'; return 'url(#' + m + ')'; }
  function footFade(U, c, Rs, w) {
    var m = U.id + 'ff' + (++U.n);
    U.defs[m] = '<radialGradient id="' + m + 'g" gradientUnits="userSpaceOnUse" cx="' + f(c[0]) + '" cy="' + f(c[1]) + '" r="' + f(Rs + w) + '"><stop offset="0" stop-color="#fff" stop-opacity="0.25"/><stop offset="' + (Rs / (Rs + w)).toFixed(3) + '" stop-color="#fff" stop-opacity="0.25"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></radialGradient>' +
      '<mask id="' + m + '" maskUnits="userSpaceOnUse" x="-300" y="-300" width="1624" height="1624"><rect x="-300" y="-300" width="1624" height="1624" fill="url(#' + m + 'g)"/></mask>';
    return 'url(#' + m + ')';
  }

  /* ---------- the scene ----------
     S: c, nr (px per Earth radius), tilt, e, phi0, r0 (where lines start, Earth radii), Z (depth scale, px),
        bold [{L, w}] (white field lines, as M5d's orbits), boldCol ('ring' | 'det'), taper, fade,
        fine [{L, w, op, phi}] (hairline field lines; phi defaults to phi0), open (lobe lines into the tail),
        ms {Lmax, sq, st, thin, r0mp} (magnetosphere), belts true, axes true, ecl true, sun {beta},
        moon {mode 'line' (li, th) | 'orbit' (R, t, inc, eo, w) | 'at' (x, y in Earth radii), r}, glow, halo */
  function scene(S, P, U) {
    var bgc = P.glow ? '#101A38' : P.id === 'P8N' ? '#18203A' : '#EDE7D9', dark = !!P.glow || P.id === 'P8N';
    SEAM = S.seam || 0.8; PLAIN = !!S.plain;
    var c = S.c, nr = S.nr, Z = S.Z || 260, acc = { back: '', front: '' }, fineAcc = { back: '', front: '' }, under = '', over = '';
    var phi0 = (S.phi0 || 0) * D2R, r0 = S.r0 || 1.3;
    /* the Moon first: where it is decides the halo cut in the lines */
    var moon = S.moon, mp = null, mr = moon.r, orbit = null;
    if (moon.mode === 'line') { var Lm = S.bold[moon.li].L, v = tiltV(dip3(Lm, moon.th * D2R, phi0), S.tilt); if (S.ms) v = deform(v, Lm, S.ms); mp = cam(v, S); if (moon.snap) { var od = moon.snap; mp[0] = Math.round(mp[0] - od) + od; mp[1] = Math.round(mp[1] - od) + od; } }
    else if (moon.mode === 'at') { mp = cam([moon.x, moon.y, 0], S); }
    else if (moon.mode === 'xy') { mp = [moon.x, moon.y, 1]; }
    else if (moon.mode === 'orbit') {
      var eo = moon.eo * D2R, inc = moon.inc * D2R, opts = [], N = 160;
      for (var i = 0; i <= N; i++) { var t = 2 * PI * i / N, x = moon.R * Math.cos(t), z = moon.R * Math.sin(t), y = -z * Math.sin(eo), zz = z * Math.cos(eo), X = x * Math.cos(inc) + y * Math.sin(inc), Y = -x * Math.sin(inc) + y * Math.cos(inc); opts.push([c[0] + X, c[1] + Y, zz]); }
      var tm = moon.t * D2R, x0 = moon.R * Math.cos(tm), z0 = moon.R * Math.sin(tm), y0 = -z0 * Math.sin(eo);
      mp = [c[0] + x0 * Math.cos(inc) + y0 * Math.sin(inc), c[1] - x0 * Math.sin(inc) + y0 * Math.cos(inc), z0 * Math.cos(eo)];
      orbit = ribbon(opts, moon.w, moon.col === 'ring' ? P.ring : P.el, bgc, S.taper != null ? S.taper * 0.9 : 0.55, dark ? 0.55 : 0.5, moon.R, false);
    }
    /* the ecliptic: a faint hairline through the Earth (E2, E5, E6) */
    if (S.ecl) under += '<path d="M40,' + f(c[1]) + 'L984,' + f(c[1]) + '" stroke="' + P.det + '" stroke-width="' + f(S.eclW || 3) + '" stroke-opacity="0.42" stroke-dasharray="' + (S.eclDash || '2 14') + '" stroke-linecap="round" fill="none"/>';
    /* Van Allen belts: nested bands in the picture plane, densest at their peak (inner L 1.5, outer L 4.5) */
    if (S.belts) {
      var belt = function (lo, pk, hi, col, op) {
        var o = '', nb = 5;
        for (var j = 0; j < nb; j++) {
          var a = lo + (pk - lo) * j / nb, b = hi - (hi - pk) * j / nb;
          [1, -1].forEach(function (sd) {
            var S0 = Object.assign({}, S, { ms: null }), A = halfLine(S0, b, 0, sd, 1.0), B = halfLine(S0, a, 0, sd, 1.0).reverse();
            o += '<path d="M' + A.concat(B).map(function (p) { return f(p[0]) + ',' + f(p[1]); }).join('L') + 'Z" fill="' + col + '" fill-opacity="' + op + '"/>';
          });
        }
        return o;
      };
      under += belt(1.2, 1.5, 2.0, P.nuc, S.beltOp ? S.beltOp[0] : 0.1) + belt(3.0, 4.5, 6.2, P.glow ? '#7AA8FF' : P.el, S.beltOp ? S.beltOp[1] : 0.085);
    }
    /* the magnetopause and the solar wind round it (Shue et al. 1997) */
    if (S.ms && S.ms.r0mp) {
      var shue = function (R0, al, from, to, sd) { var p = []; for (var k = 0; k <= 60; k++) { var th = (from + (to - from) * k / 60) * D2R, r = R0 * Math.pow(2 / (1 + Math.cos(th)), al); p.push(cam([-r * Math.cos(th), sd * r * Math.sin(th), 0], S)); } return p; };
      var mpth = [].concat(shue(S.ms.r0mp, 0.58, 150, 0, 1), shue(S.ms.r0mp, 0.58, 0, 150, -1));
      under += '<path d="M' + mpth.map(function (p) { return f(p[0]) + ',' + f(p[1]); }).join('L') + '" fill="none" stroke="' + P.det + '" stroke-width="' + f(S.mpW || 5) + '" stroke-opacity="' + (S.mpOp || 0.55) + '" stroke-dasharray="' + (S.mpDash || '18 12') + '"/>';
      (S.wind || []).forEach(function (R0) { var w = [].concat(shue(R0, 0.62, 140, 0, 1), shue(R0, 0.62, 0, 140, -1)); under += '<path d="M' + w.map(function (p) { return f(p[0]) + ',' + f(p[1]); }).join('L') + '" fill="none" stroke="' + P.det + '" stroke-width="' + f(S.windW || 3) + '" stroke-opacity="0.3"/>'; });
    }
    /* fine field lines (each half on its own) */
    (S.fine || []).forEach(function (F) {
      var ph = F.phi != null ? F.phi * D2R : phi0, col = mix(P.det, bgc, 1 - (F.op || 0.6));
      [1, -1].forEach(function (sd) { add(fineAcc, ribbon(halfLine(S, F.L, ph, sd, r0), F.w, col, bgc, S.taper != null ? S.taper : 0.5, S.fade != null ? S.fade : 0.6, Z, false)); });
    });
    /* open lines into the tail lobes (magnetosphere): from the polar cap up, then back along the tail */
    (S.open || []).forEach(function (O) {
      [1, -1].forEach(function (hs) {
        var pts = [], foot = tiltV(dip3(1.0, O.th * D2R, O.day ? PI : 0), S.tilt), h = O.h, ux = O.day ? -0.35 : 0.25;
        if (hs < 0) foot = tiltV(dip3(1.0, PI - O.th * D2R, O.day ? PI : 0), S.tilt);
        var P0 = [foot[0], foot[1]], P1 = [foot[0] + ux * h, foot[1] + hs * h * 0.95], P2 = [O.x1 - 1.5, hs * h], P3 = [O.x1, hs * h];
        for (var k = 0; k <= 40; k++) { var t = k / 40, a = (1 - t) * (1 - t) * (1 - t), b = 3 * (1 - t) * (1 - t) * t, cc = 3 * (1 - t) * t * t, d = t * t * t; pts.push(cam([a * P0[0] + b * P1[0] + cc * P2[0] + d * P3[0], a * P0[1] + b * P1[1] + cc * P2[1] + d * P3[1], 0], S)); }
        for (k = 1; k <= 20; k++) { var xx = O.x1 + (30 - O.x1) * k / 20; pts.push(cam([xx, hs * h * (1 + 0.012 * (xx - O.x1)), 0], S)); }
        var col = O.bold ? P.ring : mix(P.det, bgc, 1 - (O.op || 0.6));
        add(O.bold ? acc : fineAcc, ribbon(pts, O.w, col, bgc, 0, 0, Z, false));
      });
    });
    /* bold field lines: M5d's white orbits */
    var bcol = S.boldCol === 'det' ? mix(P.det, bgc, 0.1) : P.ring;
    (S.bold || []).forEach(function (B) { [1, -1].forEach(function (sd) { add(acc, ribbon(halfLine(S, B.L, B.phi != null ? B.phi * D2R : phi0, sd, r0), B.w, bcol, bgc, S.taper != null ? S.taper : 0.5, S.fade != null ? S.fade : 0.45, Z, true)); }); });

    /* assemble: halo cut round the Moon, the foot fade round the Earth */
    var halo = S.halo || mr + 22, earthR = nr * (S.earthK || 1);
    var hm = mp ? maskOut(U, '<circle cx="' + f(mp[0]) + '" cy="' + f(mp[1]) + '" r="' + f(halo) + '" fill="#000"/>') : null;
    var ff = footFade(U, c, earthR + (S.ffGap || 18), S.ffW || 70);
    var wrap = function (s) { if (!s) return ''; s = '<g mask="' + ff + '">' + s + '</g>'; return hm ? '<g mask="' + hm + '">' + s + '</g>' : s; };
    var out = under;
    if (S.axes) {
      var ax = function (tl, r1, r2) { var a = tl * D2R, s = Math.sin(a), co = Math.cos(a); return 'M' + f(c[0] + s * r1) + ',' + f(c[1] - co * r1) + 'L' + f(c[0] + s * r2) + ',' + f(c[1] - co * r2) + 'M' + f(c[0] - s * r1) + ',' + f(c[1] + co * r1) + 'L' + f(c[0] - s * r2) + ',' + f(c[1] + co * r2); };
      var rot = S.tilt - 9.2;
      out += '<path d="' + ax(rot, earthR + 10, S.axR || 330) + '" stroke="' + P.ring + '" stroke-opacity="0.55" stroke-width="' + f(S.axW || 5) + '" stroke-dasharray="' + (S.axDash || '16 12') + '" fill="none"/>';
      var arcR = S.arcR || 250, a1 = rot * D2R, a2 = S.tilt * D2R;
      out += '<path d="M' + f(c[0] + Math.sin(a1) * arcR) + ',' + f(c[1] - Math.cos(a1) * arcR) + 'A' + arcR + ' ' + arcR + ' 0 0 1 ' + f(c[0] + Math.sin(a2) * arcR) + ',' + f(c[1] - Math.cos(a2) * arcR) + '" stroke="' + P.nuc + '" stroke-width="' + f((S.axW || 5) * 1.1) + '" fill="none" stroke-opacity="0.9"/>';
    }
    out += wrap(fineAcc.back + acc.back);
    if (orbit) out += orbit.back;
    if (S.glow) out += glow(U, c, earthR, earthR * S.glow, P.glow ? mix(P.nuc, '#FFFFFF', 0.1) : P.nuc, (P.glow ? 0.34 : 0.22) * (S.glowOp || 1));
    var lx = U.lx != null ? U.lx : -0.35, ly = U.ly != null ? U.ly : -0.75;
    var earth = S.sun ? sunBall(U, c[0], c[1], earthR, P.nuc, P, S.sun.beta, S.sun.soft) : ball(U, c[0], c[1], earthR, P.nuc, P, lx, ly);
    if (S.shadow) earth = '<g filter="url(#' + U.id + 'ash)">' + earth + '</g>';
    out += earth;
    if (S.axes) {
      var a = S.tilt * D2R, sn = Math.sin(a), cs = Math.cos(a), r1 = earthR + 10, r2 = S.axR2 || 300;
      out += '<path d="M' + f(c[0] + sn * r1) + ',' + f(c[1] - cs * r1) + 'L' + f(c[0] + sn * r2) + ',' + f(c[1] - cs * r2) + 'M' + f(c[0] - sn * r1) + ',' + f(c[1] + cs * r1) + 'L' + f(c[0] - sn * r2) + ',' + f(c[1] + cs * r2) + '" stroke="' + P.nuc + '" stroke-width="' + f((S.axW || 5) * 1.1) + '" stroke-linecap="round" fill="none"/>';
    }
    out += wrap(fineAcc.front + acc.front);
    if (orbit) out += hm ? '<g mask="' + hm + '">' + orbit.front + '</g>' : orbit.front;
    if (S.stubs) { var a3 = S.tilt * D2R; out += '<path d="M' + f(c[0] + Math.sin(a3) * (earthR + 10)) + ',' + f(c[1] - Math.cos(a3) * (earthR + 10)) + 'L' + f(c[0] + Math.sin(a3) * (earthR + 52)) + ',' + f(c[1] - Math.cos(a3) * (earthR + 52)) + 'M' + f(c[0] - Math.sin(a3) * (earthR + 10)) + ',' + f(c[1] + Math.cos(a3) * (earthR + 10)) + 'L' + f(c[0] - Math.sin(a3) * (earthR + 52)) + ',' + f(c[1] + Math.cos(a3) * (earthR + 52)) + '" stroke="' + P.det + '" stroke-width="4.4" stroke-opacity="0.6" fill="none" stroke-linecap="round"/>'; }
    /* the Moon */
    if (mp) {
      var mg = S.moonGlow ? glow(U, mp, mr, mr * 2.6, P.el, (P.glow ? 0.4 : 0.25) * S.moonGlow) : '';
      var mb = S.sun ? sunBall(U, mp[0], mp[1], mr, P.el, P, S.sun.beta, S.sun.soft) : ball(U, mp[0], mp[1], mr, P.el, P, lx, ly);
      over += mg + (S.shadow ? '<g filter="url(#' + U.id + 'ash)">' + mb + '</g>' : mb);
    }
    return out + over;
  }

  /* ---------- the designs ---------- */
  function X(base, over) { var o = {}, k; for (k in base) o[k] = base[k]; for (k in over) o[k] = over[k]; return o; }
  /* M5d in Earth radii: Earth r 75.7 px (88 x 0.86); its orbits at 203, 310, 447 px = L 2.7, 4.1, 5.9 (the outer
     radiation belt's range); its five fine lines L 3.4 to 13.6, out past the tile edge; tilt 12 degrees */
  var NR = 75.7;
  var BOLD = [{ L: 2.7, w: 16 }, { L: 4.1, w: 14 }, { L: 5.9, w: 12 }];
  var FINE = [{ L: 3.4, w: 4.4, op: 0.62 }, { L: 5.06, w: 4.2, op: 0.56 }, { L: 7.3, w: 4, op: 0.5 }, { L: 10, w: 3.8, op: 0.44 }, { L: 13.6, w: 3.6, op: 0.4 }];
  var BASE = { c: [512, 512], nr: NR, tilt: 12, e: 12, phi0: 28, r0: 1.32, Z: 250, taper: 0.66, fade: 0.55, bold: BOLD, fine: FINE, glow: 3.2, shadow: true, stubs: true, moon: { mode: 'line', li: 1, th: 60, r: 36 }, halo: 54 };
  var CAGE = [{ L: 5.06, w: 3.6, op: 0.4, phi: -50 }, { L: 10, w: 3.4, op: 0.34, phi: -50 }];
  var ORB = { mode: 'orbit', R: 430, t: -32, inc: 5, eo: 13, w: 15, r: 34, col: 'ring' };
  var SUN = { beta: 14, soft: 0.06 };
  var DEP = { light: -20, sheen: 1, sheenTo: 0.34, edge: 0.75, edgeW: 10, shadow: 1, shadowD: 14 };
  var DEPSUN = X(DEP, { light: -62, sheenTo: 0.3 });

  /* each design: s3 (128 and up), s2 (48 to 96: bold structure only) */
  function bold2(S, extra) { return X(S, X({ fine: (S.fine || []).slice(1, 2).map(function (F) { return X(F, { w: 11, op: 0.7 }); }), bold: (S.bold || []).map(function (B) { return X(B, { w: B.w * 1.7 }); }), stubs: false, axW: 9, eclW: 6, mpW: 9, windW: 6 }, extra || {})); }

  var E1 = BASE;
  var E2 = X(BASE, { bold: [{ L: 2.7, w: 9 }, { L: 4.1, w: 8 }], boldCol: 'det', fine: FINE.concat(CAGE), moon: ORB, ecl: true, stubs: true, halo: 50 });
  var E3 = X(BASE, { axes: true, stubs: false, moon: { mode: 'line', li: 1, th: 62, r: 36 }, axR: 360, axR2: 300, arcR: 230 });
  var E4 = { c: [548, 512], nr: 46, tilt: 12, e: 8, phi0: 20, r0: 1.25, Z: 200, taper: 0.5, fade: 0.45,
    ms: { Lmax: 8.2, sq: 0.18, st: 0.03, thin: 0.45, r0mp: 10 }, wind: [11.6, 13.2],
    bold: [{ L: 2.4, w: 10 }, { L: 4.0, w: 9.5 }, { L: 5.9, w: 9 }, { L: 8.2, w: 8 }],
    open: [{ th: 13, h: 5.2, x1: 7, w: 4.4, op: 0.6 }, { th: 9, h: 7.4, x1: 7.5, w: 4.2, op: 0.5 }, { th: 7, h: 9.2, x1: 8, w: 4, op: 0.42, day: true }],
    sun: SUN, glow: 2.6, shadow: true, moon: { mode: 'at', x: 8.6, y: -0.25, r: 20 }, halo: 32, earthK: 1, ffGap: 10, ffW: 40 };
  var E5 = X(BASE, { bold: [], belts: true, fine: FINE.concat(CAGE), moon: ORB, ecl: true, glow: 2.6, halo: 50 });
  var E6 = X(BASE, { nr: 92, bold: [{ L: 2.5, w: 15 }, { L: 3.7, w: 13 }, { L: 5.1, w: 11 }], fine: [{ L: 3.1, w: 4.4, op: 0.6 }, { L: 4.4, w: 4.2, op: 0.55 }, { L: 6.3, w: 4, op: 0.5 }, { L: 8.6, w: 3.8, op: 0.44 }, { L: 11.6, w: 3.6, op: 0.4 }],
    moon: X(ORB, { R: 440, t: -26, r: 25, w: 13 }), ecl: true, boldCol: 'det', halo: 40, moonGlow: 0.8 });
  var E7 = X(BASE, { sun: SUN, glow: 2.4, glowOp: 0.8, moon: { mode: 'line', li: 1, th: 60, r: 36 } });
  var E8 = { c: [470, 512], nr: 70, tilt: 12, e: 8, phi0: 20, r0: 1.25, Z: 220, taper: 0.5, fade: 0.45,
    ms: { Lmax: 5.4, sq: 0.12, st: 0.06, thin: 0.45, r0mp: 6 }, belts: true, beltOp: [0.11, 0.075],
    bold: [{ L: 2.4, w: 13 }, { L: 3.8, w: 12 }, { L: 5.4, w: 11 }],
    fine: [{ L: 3.1, w: 4, op: 0.5 }, { L: 4.6, w: 3.8, op: 0.45 }],
    open: [{ th: 18, h: 3.6, x1: 4.6, w: 4.4, op: 0.6 }, { th: 13, h: 4.8, x1: 5, w: 4.2, op: 0.5 }, { th: 10, h: 6, x1: 5.4, w: 4, op: 0.42, day: true }],
    sun: SUN, glow: 2.4, glowOp: 0.8, shadow: true, moon: { mode: 'at', x: 5.4, y: -0.2, r: 19 }, halo: 30, ffGap: 12, ffW: 50 };

  var DESIGNS = [
    { id: 'E1', name: 'The dipole in 3D', short: 'M5d with its lines turned into 3D and tapered',
      note: 'M5d as the Earth and the Moon: the same field, now in 3D. Each line lies in a plane through the magnetic axis turned 28° toward you, seen from 12° above: the right halves come toward you (wider, full white), the left halves go away (thinner, fainter), and where a line passes behind the Earth the planet hides it. The Moon sits where M5d\'s electron was.',
      s3: E1, s2: bold2(E1), depth: DEP },
    { id: 'E2', name: 'The Moon on its orbit', short: 'the Moon on a 5°-inclined orbit, the field in blue',
      note: 'The white ribbon is now the Moon\'s orbit: a circle seen from 13° above, inclined 5° to the ecliptic (the dotted hairline), tapered by depth, its far half passing behind the Earth. The field stays in blue: two inner lines and the fine lines, with two more in a second plane so the field reads as a cage round the planet.',
      s3: E2, s2: bold2(E2, { bold: [{ L: 2.7, w: 15 }, { L: 4.1, w: 13 }], moon: X(ORB, { w: 24, r: 44 }) }), depth: DEP },
    { id: 'E3', name: 'Two axes', short: 'the magnetic axis 9.2° from the rotation axis',
      note: 'E1 with the Earth\'s two axes: the rotation axis dashed, the magnetic axis solid in the Earth\'s colour, 9.2° apart (the dipole tilt of the 2025 field models; often quoted as 11°, its older value) and marked by a small arc. The field is centred on the magnetic axis, as it should be.',
      s3: E3, s2: bold2(E3), depth: DEP },
    { id: 'E4', name: 'The magnetosphere', short: 'day side squeezed by the solar wind, a long tail, the Moon in it',
      note: 'The real shape, with the Sun to the left: the solar wind squeezes the day side to the magnetopause (dashed, at 10 Earth radii, drawn with the Shue model) and stretches the night side into a long tail; the open lines from the polar caps run back into the tail lobes. The Earth is lit from the left. The Moon crosses the tail around full Moon, a few days each month; here it is drawn in the tail at 8.6 Earth radii (really 60) and enlarged.',
      s3: E4, s2: X(E4, { bold: E4.bold.filter(function (b, i) { return i % 2 === 0; }).map(function (B) { return X(B, { w: B.w * 1.9 }); }), open: E4.open.slice(0, 2).map(function (O) { return X(O, { w: 10, op: 0.75 }); }), wind: [], mpW: 10, moon: X(E4.moon, { r: 34, x: 6.6 }), nr: 60 }), depth: DEPSUN },
    { id: 'E5', name: 'Van Allen belts', short: 'the two radiation belts as shaded bands',
      note: 'The two Van Allen belts as shaded bands, densest at their peaks: the inner belt (mostly protons) L 1.2 to 2, peaking near L 1.5, in the Earth\'s colour; the outer belt (mostly electrons) L 3 to 6, peaking near 4.5, in blue, with the slot between them. Drawn in the picture plane, behind the Earth (the belts are drift shells round the planet, so they are not stretched into the tail). The Moon on its inclined orbit as in E2.',
      s3: E5, s2: bold2(E5, { beltOp: [0.16, 0.13], moon: X(ORB, { w: 24, r: 44 }) }), depth: DEP },
    { id: 'E6', name: 'The Moon to scale', short: 'the Moon at its true size against the Earth (0.27)',
      note: 'The Earth larger and the Moon at its true size beside it: 0.273 Earth radii. Its distance is not to scale (60 Earth radii would put it more than 5 tile widths away); the orbit is drawn at 4.8. The field in blue, the orbit in white as in E2; the small Moon gets a faint glow so it still reads in the Dock.',
      s3: E6, s2: bold2(E6, { bold: [{ L: 2.5, w: 15 }, { L: 3.7, w: 13 }], moon: X(E6.moon, { w: 24, r: 30 }) }), depth: DEP },
    { id: 'E7', name: 'Day and night', short: 'E1 lit by the Sun from the left: both show the same phase',
      note: 'E1 with sunlight from the left, a little toward you: the Earth and the Moon each have a day half and a night half with a soft terminator, and both show the same phase, as they must (the Sun is so far away that its light is parallel). The tile\'s sheen and the shadows follow the same light.',
      s3: E7, s2: bold2(E7), depth: DEPSUN },
    { id: 'E8', name: 'The full plate', short: 'magnetosphere, belts, sunlight and the true-size Moon in the tail',
      note: 'Everything in one: the squeezed day side and the tail, the open lobe lines, the two belts, the Sun from the left, and the Moon at its true size (0.27 Earth radii) in the tail. For legibility the magnetopause is drawn at 6 Earth radii (really about 10) so the Earth can stay large; the Moon at 5.4 (really 60).',
      s3: E8, s2: X(E8, { bold: E8.bold.map(function (B) { return X(B, { w: B.w * 1.8 }); }), fine: [], open: E8.open.slice(0, 2).map(function (O) { return X(O, { w: 10, op: 0.75 }); }), mpW: 10, belts: true, beltOp: [0.15, 0.11], moon: X(E8.moon, { r: 30 }) }), depth: DEPSUN }
  ];
  var DES = {}; DESIGNS.forEach(function (d) { DES[d.id] = d; });

  /* ---------- the tile (a copy of round 5's svg(), with the depth block) ---------- */
  function depthDefs(id_, P, dp, U) {
    var dark = P.glow || P.id === 'P8N', lx = U.lx, ly = U.ly;
    var g = 'x1="' + f(0.5 + 0.5 * lx) + '" y1="' + f(0.5 + 0.5 * ly) + '" x2="' + f(0.5 - 0.5 * lx) + '" y2="' + f(0.5 - 0.5 * ly) + '"';
    var sh = (dp.sheen != null ? dp.sheen : 1) * (dark ? 0.13 : 0.35), e = dp.edge != null ? dp.edge : 0.75, D = dp.shadowD != null ? dp.shadowD : 14;
    return '<filter id="' + id_ + 'ash" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="' + f(-lx * D) + '" dy="' + f(-ly * D) + '" stdDeviation="' + f(D * 1.15) + '" flood-color="#000" flood-opacity="' + f((dp.shadow != null ? dp.shadow : 1) * (dark ? 0.55 : 0.22)) + '"/></filter>' +
      '<linearGradient id="' + id_ + 'gs" ' + g + '><stop offset="0" stop-color="#fff" stop-opacity="' + sh.toFixed(3) + '"/><stop offset="' + (dp.sheenTo || 0.42) + '" stop-color="#fff" stop-opacity="0"/></linearGradient>' +
      '<linearGradient id="' + id_ + 'ge" ' + g + '><stop offset="0" stop-color="#fff" stop-opacity="' + e + '"/><stop offset="0.3" stop-color="#fff" stop-opacity="' + (e * 0.13).toFixed(3) + '"/><stop offset="0.7" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity="' + (e * 0.24).toFixed(3) + '"/></linearGradient>';
  }
  var uid = 0;
  function tileSvg(body, P, dp, U, L, size, opts) {
    var id_ = U.id;
    var defs = '<linearGradient id="' + id_ + 'bg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="' + P.bg[0] + '"/><stop offset="1" stop-color="' + P.bg[1] + '"/></linearGradient>' +
      '<clipPath id="' + id_ + 'clip"><path d="' + TILE + '"/></clipPath>' +
      (P.glow ? '<radialGradient id="' + id_ + 'gl" cx="0.5" cy="0.5" r="0.55"><stop offset="0" stop-color="' + P.glow + '" stop-opacity="0.2"/><stop offset="1" stop-color="' + P.glow + '" stop-opacity="0"/></radialGradient>' : '') +
      '<filter id="' + id_ + 'sh" x="-10%" y="-10%" width="120%" height="125%"><feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000" flood-opacity="0.32"/></filter>' +
      depthDefs(id_, P, dp, U) + Object.keys(U.defs).map(function (k) { return U.defs[k]; }).join('');
    var tile = '<path d="' + TILE + '" fill="url(#' + id_ + 'bg)"/>' + (P.glow ? '<rect width="1024" height="1024" fill="url(#' + id_ + 'gl)" clip-path="url(#' + id_ + 'clip)"/>' : '') +
      '<g clip-path="url(#' + id_ + 'clip)">' + body + '</g>' +
      (L >= 2 ? '<path d="' + TILE + '" fill="url(#' + id_ + 'gs)"/><path d="' + TILE + '" fill="none" stroke="url(#' + id_ + 'ge)" stroke-width="' + f((dp.edgeW || 10) * (L === 3 ? 1 : 1.8)) + '" clip-path="url(#' + id_ + 'clip)"/>'
        : '<path d="' + TILE + '" fill="none" stroke="' + P.rim + '" stroke-opacity="0.32" stroke-width="22" clip-path="url(#' + id_ + 'clip)"/>');
    var inner = opts.frame === 'mac' ? '<g filter="url(#' + id_ + 'sh)"><g transform="translate(100 100) scale(0.8046875)">' + tile + '</g></g>' : tile;
    return '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="' + size + '" height="' + size + '" viewBox="0 0 1024 1024"><defs>' + defs + '</defs>' + inner + '</svg>';
  }
  function newU(dp) { var U = { id: 'e' + (++uid).toString(36) + '_', defs: {}, n: 0 }, la = (dp.light || 0) * D2R; U.lx = Math.sin(la); U.ly = -Math.cos(la); return U; }
  function svg(id, pid, size, opts) {
    opts = opts || {}; size = size || 1024;
    var D = DES[id], P = PAL[(opts.style === 'dark' && pid === 'P8') ? 'P8N' : pid], L = A5.lvlFor(size);
    var U = newU(D.depth), S = L === 3 ? D.s3 : D.s2;
    if (L < 3) S = X(S, { shadow: false });
    return tileSvg(scene(S, P, U), P, D.depth, U, L, size, opts);
  }

  var RECS = [
    { d: 'E1', p: 'P2', why: 'Closest to the M5d you picked: the same mark, now a real 3D field with the Earth hiding the far halves of its lines. The safest main icon.' },
    { d: 'E7', p: 'P2', why: 'E1 lit by the Sun: the day and night halves make the yellow read as a planet at once, and the light matches the tile\'s sheen. Strongest "it is the Earth" with no extra lines.' },
    { d: 'E4', p: 'P2', why: 'The real magnetosphere: the squeezed day side, the tail and the Moon in it. The most scientific picture that still reads in the Dock; best as a picker option or for the About window.' },
    { d: 'E2', p: 'P8', why: 'The Moon\'s inclined orbit as the white ribbon reads cleanly on Chart paper, like a plate in an atlas.' }
  ];
  var API = { DESIGNS: DESIGNS, DES: DES, RECS: RECS, PAL: PAL, svg: svg, scene: scene, tileSvg: tileSvg, newU: newU, X: X, BASE: BASE, ORB: ORB, SUN: SUN, DEP: DEP, DEPSUN: DEPSUN, E4: E4, NR: NR,
    dock: A5.dock, styles: A5.styles, standSvg: A5.standSvg, inner: A5.inner, mix: mix };
  root.AL5C = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
