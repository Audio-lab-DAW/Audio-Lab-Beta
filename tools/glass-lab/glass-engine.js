/* AudioLab glass engine (task G2). Plain JS, no build step, no dependencies.
   One WebGL2 canvas; one shared backdrop picture; one dual-Kawase pyramid built only when the picture changed;
   every glass surface is one quad in one shader. Glass never samples glass.
   Use: const g = AudioLabGlass.create(canvas, opts); g.setBackdrop(arrCanvas); g.addPanel({id, rect, radius, kind}); g.render();
   Docs: docs/glass-engine-module.md */
(function (root) {
  'use strict';
  var VERSION = '1.0.0';
  /* lens presets: [divisor of the short side, maximum band in px]. Apple's rule: band = min(short side / 4, 20). */
  var LENS = { off: [0, 0], fine: [4, 12], apple: [4, 20], wide: [3, 40] };
  /* blur presets: how deep the pyramid goes, counted from a half-size first level (deepest level 1/4, 1/8, 1/16) */
  var BLUR = { light: 2, regular: 3, heavy: 4 };
  /* quality steps: base = size of the first pyramid level (2 = half, 4 = quarter); rate = backdrop refreshes per second (0 = every change) */
  var QNAME = { high: 3, medium: 2, low: 1, 'static': 0 };
  var QSET = [{ base: 4, rate: 30, st: true }, { base: 4, rate: 30 }, { base: 4, rate: 60 }, { base: 2, rate: 0 }];
  /* kinds: shadow = strength (0 none), tint = how much panel colour is mixed in, fixed = does not move (lets the blur skip the area not under glass) */
  var KINDS = {
    docked: { shadow: 0, tint: 0.5, fixed: true },
    window: { shadow: 1, tint: 0.5 },
    sheet: { shadow: 1, tint: 0.6 },
    menu: { shadow: 1, tint: 0.6 },
    pill: { shadow: 1, tint: 0.45 }
  };

  var VS_FULL = '#version 300 es\nout vec2 v;void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);v=p;gl_Position=vec4(p*2.-1.,0.,1.);}';
  /* one quad per surface: rc = x,y,w,h in canvas pixels (y down), mg = margin for the shadow */
  var VS_QUAD = '#version 300 es\nuniform vec2 res;uniform vec4 rc;uniform float mg;out vec2 p;' +
    'void main(){vec2 c=vec2(gl_VertexID&1,gl_VertexID>>1);p=rc.xy-mg+c*(rc.zw+2.*mg);gl_Position=vec4(p.x/res.x*2.-1.,1.-p.y/res.y*2.,0.,1.);}';
  /* down pass: cw 4 = dual-Kawase step to half size; cw 0 with a quarter-texel offset = exact 4x4 box straight to quarter size */
  var FS_DOWN = '#version 300 es\nprecision highp float;in vec2 v;uniform sampler2D t;uniform vec2 px;uniform float flip,cw;out vec4 o;' +
    'void main(){vec2 u=vec2(v.x,mix(v.y,1.-v.y,flip));o=texture(t,u)*cw;o+=texture(t,u-px);o+=texture(t,u+px);o+=texture(t,u+vec2(px.x,-px.y));o+=texture(t,u-vec2(px.x,-px.y));o/=cw+4.;}';
  var FS_UP = '#version 300 es\nprecision highp float;in vec2 v;uniform sampler2D t;uniform vec2 px;out vec4 o;' +
    'void main(){o=texture(t,v+vec2(-px.x*2.,0.));o+=texture(t,v+vec2(-px.x,px.y))*2.;o+=texture(t,v+vec2(0.,px.y*2.));o+=texture(t,v+px)*2.;o+=texture(t,v+vec2(px.x*2.,0.));o+=texture(t,v+vec2(px.x,-px.y))*2.;o+=texture(t,v+vec2(0.,-px.y*2.));o+=texture(t,v-px)*2.;o/=12.;}';
  var SDF = 'float sd(vec2 p,vec2 b,float r){vec2 q=abs(p)-b+r;return length(max(q,0.))+min(max(q.x,q.y),0.)-r;}';
  /* the glass face. tint = rgb + amount; face = saturation, multiply, add; rimp = width, base, lit, contrast border;
     shd = offset y, radius, opacity; md = static (1 = no backdrop), opacity */
  var FS_GLASS = '#version 300 es\nprecision highp float;uniform sampler2D t;uniform vec2 res;uniform vec4 rc,tint,rimp;uniform vec3 face,shd;uniform vec2 md;uniform float rad,band,amt,dpr;in vec2 p;out vec4 o;' + SDF +
    'void main(){vec2 hb=rc.zw*.5,l=p-rc.xy-hb;float d=sd(l,hb,rad),a=clamp(.5-d,0.,1.),sh=0.;' +
    'if(shd.z>0.){float ds=sd(l-vec2(0.,shd.x),hb,rad);sh=shd.z*(1.-smoothstep(-shd.y,shd.y,ds));}' +
    'if(a<=0.){if(sh<.003)discard;o=vec4(0.,0.,0.,sh*md.y);return;}' +
    /* lens field: own corner radius of at least the band, so the bending direction never flips along a corner diagonal */
    'float R=min(max(rad,band),min(hb.x,hb.y));vec2 q=abs(l)-hb+R,sg=vec2(l.x<0.?-1.:1.,l.y<0.?-1.:1.),n;float dl;' +
    'if(q.x>0.&&q.y>0.){float L=length(q);dl=L-R;n=q/L*sg;}else if(q.x>q.y){dl=q.x-R;n=vec2(sg.x,0.);}else{dl=q.y-R;n=vec2(0.,sg.y);}' +
    'vec3 c;if(md.x>.5){c=tint.rgb+(fract(sin(dot(floor(p),vec2(12.9898,78.233)))*43758.5453)-.5)*.022;}else{' +
    'float x=clamp(-dl/band,0.,1.),k=1.-sqrt(max(0.,1.-(1.-x)*(1.-x)));vec2 sp=p-n*k*amt;c=texture(t,vec2(sp.x/res.x,1.-sp.y/res.y)).rgb;' +
    'float L=dot(c,vec3(.2126,.7152,.0722));c=mix(vec3(L),c,face.x)*face.y+face.z;c=mix(c,tint.rgb,tint.a);}' +
    'float rim=1.-smoothstep(0.,rimp.x,-d),lit=abs(dot(n,vec2(-.7071,-.7071)));c+=rim*(rimp.y+rimp.z*lit);' +
    'c=mix(c,vec3(1.),rimp.w*(1.-smoothstep(dpr-.5,dpr+.5,-d)));' +
    'float al=a*md.y;o=vec4(c*al,al+sh*md.y*(1.-a));}';
  /* a flat picture (a colour or a canvas) put on top of the backdrop before blurring: what a floating glass sees where it covers DOM */
  var FS_FLAT = '#version 300 es\nprecision highp float;uniform sampler2D t;uniform vec4 rc,col;uniform float rad,aa,useT;in vec2 p;out vec4 o;' + SDF +
    'void main(){vec2 hb=rc.zw*.5,l=p-rc.xy-hb;float a=clamp(.5-sd(l,hb,rad)/aa,0.,1.);vec4 c=useT>.5?vec4(texture(t,(p-rc.xy)/rc.zw).rgb,col.a):col;o=vec4(c.rgb*c.a*a,c.a*a);}';

  function rectOf(r) {
    if (!r) return { x: 0, y: 0, w: 0, h: 0 };
    if (r.length === 4) return { x: +r[0], y: +r[1], w: +r[2], h: +r[3] };
    return { x: +(r.x != null ? r.x : r.left) || 0, y: +(r.y != null ? r.y : r.top) || 0, w: +(r.w != null ? r.w : r.width) || 0, h: +(r.h != null ? r.h : r.height) || 0 };
  }
  function mq(q) { try { return root.matchMedia ? root.matchMedia(q) : null; } catch (e) { return null; } }

  function create(canvas, o) {
    o = o || {};
    var opt = {
      lens: o.lens in LENS ? o.lens : 'apple',
      blur: o.blur in BLUR ? o.blur : 'regular',
      maxDpr: o.maxDpr || 2,
      dpr: o.dpr || 0,                                         /* 0 = follow the screen */
      tint: o.tint || [0.086, 0.11, 0.165],                    /* panel colour mixed into the face (rgb 22 28 42) */
      solid: o.solid || [0.086, 0.11, 0.165],                  /* the plain tint used by Static, Reduce Transparency and the fallback */
      backdropColor: o.backdropColor || [0.039, 0.039, 0.047], /* where the backdrop picture does not reach */
      face: { sat: 1.3, mul: 1, add: 0 },
      rim: { width: 1.6, base: 0.06, lit: 0.3 },
      regionCull: o.regionCull !== false,
      allowSoftware: !!o.allowSoftware,
      autoResize: o.autoResize !== false,
      onFallback: o.onFallback || null,
      requestRender: o.requestRender || null
    }, k;
    if (o.face) for (k in o.face) opt.face[k] = o.face[k];
    if (o.rim) for (k in o.rim) opt.rim[k] = o.rim[k];
    var kinds = {};
    for (k in KINDS) kinds[k] = KINDS[k];
    if (o.kinds) for (k in o.kinds) kinds[k] = o.kinds[k];

    var gl = null, prog = null, vao = null, mode = 'none', reason = '', destroyed = false;
    var W = 0, H = 0, D = 1, quality = 3;
    var panels = new Map(), order = [], seq = 0, flats = new Map();
    var src = null, srcRect = null, srcTex = null, srcReady = false, lastUp = -1e9;
    var srcDirty = false, pyrDirty = true, bDirty = true, panelsDirty = true, lastFlat = -1e9, flatWait = false;
    var pyrA = null, pyrB = null, regs = null, regKey = '';
    var acc = { rt: o.reduceTransparency, ic: o.increaseContrast };
    var mRT = mq('(prefers-reduced-transparency: reduce)'), mIC = mq('(prefers-contrast: more)');
    var fb = null;   /* fallback: {c, x, own, vis} */
    var stats = { renders: 0, skipped: 0, draws: 0, uploads: 0, pyramids: 0, flatPyramids: 0, flatUploads: 0, lost: 0, restored: 0 };

    function ask() { if (opt.requestRender) try { opt.requestRender(); } catch (e) { } }
    function reduceT() { return acc.rt != null ? !!acc.rt : !!(mRT && mRT.matches); }
    function moreC() { return acc.ic != null ? !!acc.ic : !!(mIC && mIC.matches); }
    function isStatic() { return !!QSET[quality].st || reduceT() || !src; }
    function onMq() { panelsDirty = true; ask(); }

    /* ---------- GL set-up ---------- */
    function mk(vs, fs) {
      var p = gl.createProgram(), i, n, a, u = {};
      [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]].forEach(function (x) {
        var sh = gl.createShader(x[0]); gl.shaderSource(sh, x[1]); gl.compileShader(sh);
        if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS) && !gl.isContextLost()) throw new Error(gl.getShaderInfoLog(sh));
        gl.attachShader(p, sh);
      });
      gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS) && !gl.isContextLost()) throw new Error(gl.getProgramInfoLog(p));
      n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS) || 0;
      for (i = 0; i < n; i++) { a = gl.getActiveUniform(p, i); u[a.name] = gl.getUniformLocation(p, a.name); }
      return { p: p, u: u };
    }
    function tex(w, h) {
      var t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      if (w) gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      return t;
    }
    function target(w, h) {
      var t = tex(w, h), f = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, f); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
      return { t: t, f: f };
    }
    function glInit() {
      prog = { d: mk(VS_FULL, FS_DOWN), u: mk(VS_FULL, FS_UP), g: mk(VS_QUAD, FS_GLASS), f: mk(VS_QUAD, FS_FLAT) };
      vao = gl.createVertexArray(); gl.bindVertexArray(vao);
      gl.disable(gl.DEPTH_TEST); gl.disable(gl.CULL_FACE); gl.activeTexture(gl.TEXTURE0);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
      srcTex = tex(0, 0); srcReady = false; pyrA = pyrB = null;
      flats.forEach(function (f) { f.tex = null; f.dirty = true; });
      srcDirty = !!src; pyrDirty = bDirty = panelsDirty = true; regKey = '';
    }
    /* level plan: sizes as divisors of the canvas in CSS pixels, so the blur looks the same on a 1x and a 2x screen (and a 2x screen pays no more).
       Half base: 2,4,(8),(16). Quarter base: 4,(8),(16); "light" is one level plus a same-size pass. */
    function plan() {
      var base = QSET[quality].base, n = BLUR[opt.blur], m = base === 2 ? n : Math.max(1, n - 1), a = [], i;
      for (i = 0; i < m; i++) a.push(base << i);
      return a;
    }
    function freePyr(P) {
      if (!P || !gl) return;
      P.lev.forEach(function (L) { gl.deleteTexture(L.t); gl.deleteFramebuffer(L.f); if (L.t2) { gl.deleteTexture(L.t2); gl.deleteFramebuffer(L.f2); } });
      if (P.pre) { gl.deleteTexture(P.pre.t); gl.deleteFramebuffer(P.pre.f); }
    }
    function makePyr() {
      var pl = plan(), lev = [], i, L, a, b;
      for (i = 0; i < pl.length; i++) {
        L = { div: pl[i] * D, w: Math.max(2, Math.round(W / (pl[i] * D))), h: Math.max(2, Math.round(H / (pl[i] * D))) };
        a = target(L.w, L.h); L.t = a.t; L.f = a.f;
        if (i < pl.length - 1 || pl.length === 1) { b = target(L.w, L.h); L.t2 = b.t; L.f2 = b.f; }
        lev.push(L);
      }
      /* the first level is more than 4 times smaller than the picture (2x screen, quarter base): go there in two steps so thin lines are not skipped */
      var pre = null;
      if (lev[0].div > 4.001) { pre = target(Math.max(2, Math.round(W * 2 / lev[0].div)), Math.max(2, Math.round(H * 2 / lev[0].div))); pre.div = lev[0].div / 2; pre.w = Math.max(2, Math.round(W * 2 / lev[0].div)); pre.h = Math.max(2, Math.round(H * 2 / lev[0].div)); }
      return { lev: lev, pre: pre, ready: false };
    }
    function dropPyr() { freePyr(pyrA); freePyr(pyrB); pyrA = pyrB = null; pyrDirty = bDirty = panelsDirty = true; regKey = ''; }

    /* ---------- which part of the screen is under glass (only when nothing can move) ---------- */
    function regions() {
      if (!opt.regionCull) return null;
      var pl = plan(), M = 8 * pl[pl.length - 1] * D, out = [], area = 0, i, p, x0, y0, x1, y1;
      for (i = 0; i < order.length; i++) {
        p = order[i]; if (!p.visible) continue;
        if (!p.K.fixed) return null;
        x0 = Math.max(0, p.x * D - M); y0 = Math.max(0, p.y * D - M); x1 = Math.min(W, (p.x + p.w) * D + M); y1 = Math.min(H, (p.y + p.h) * D + M);
        if (x1 <= x0 || y1 <= y0) continue;
        out.push([Math.floor(x0), Math.floor(y0), Math.ceil(x1), Math.ceil(y1)]);
      }
      /* cut into rectangles that do not overlap: one row per band between two horizontal edges, joined intervals inside it */
      var ys = [], res = [], j, a, b, iv, cur, last;
      for (i = 0; i < out.length; i++) { ys.push(out[i][1], out[i][3]); }
      ys.sort(function (m, n) { return m - n; });
      for (j = 0; j < ys.length - 1; j++) {
        a = ys[j]; b = ys[j + 1]; if (b <= a) continue;
        iv = []; for (i = 0; i < out.length; i++) if (out[i][1] <= a && out[i][3] >= b) iv.push([out[i][0], out[i][2]]);
        iv.sort(function (m, n) { return m[0] - n[0]; }); cur = null;
        for (i = 0; i < iv.length; i++) {
          if (cur && iv[i][0] <= cur[2]) { cur[2] = Math.max(cur[2], iv[i][1]); continue; }
          cur = [iv[i][0], a, iv[i][1], b]; res.push(cur);
        }
      }
      /* join a rectangle to the one right above it when both span the same columns */
      out = [];
      for (i = 0; i < res.length; i++) {
        a = res[i]; last = null;
        for (j = 0; j < out.length; j++) if (out[j][3] === a[1] && out[j][0] === a[0] && out[j][2] === a[2]) last = out[j];
        if (last) last[3] = a[3]; else out.push(a);
      }
      for (i = 0; i < out.length; i++) { a = out[i]; area += (a[2] - a[0]) * (a[3] - a[1]); out[i] = [a[0], a[1], a[2] - a[0], a[3] - a[1]]; }
      return area > 0.8 * W * H ? null : out;
    }
    function each(rs, L, fn) {
      if (!rs) { gl.disable(gl.SCISSOR_TEST); fn(); return; }
      gl.enable(gl.SCISSOR_TEST);
      var sx = L.w / W, sy = L.h / H, i, r, x, y, x1, y1;
      for (i = 0; i < rs.length; i++) {
        r = rs[i]; x = Math.floor(r[0] * sx); x1 = Math.ceil((r[0] + r[2]) * sx); y = Math.floor((H - r[1] - r[3]) * sy); y1 = Math.ceil((H - r[1]) * sy);
        gl.scissor(x, y, x1 - x, y1 - y); fn();
      }
      gl.disable(gl.SCISSOR_TEST);
    }
    function tri() { gl.drawArrays(gl.TRIANGLES, 0, 3); }

    /* ---------- the blur pyramid ---------- */
    function build(P, withFlats) {
      var L = P.lev, m = L.length, rs = withFlats ? null : regs, i, t, l0 = L[0], f0 = P.pre || l0;
      gl.disable(gl.BLEND);
      /* 1: the backdrop picture into the first level (its rectangle on the canvas becomes the viewport).
         Exactly half size: one dual-Kawase step, as in the Glass Bench. Smaller: a box filter (4 taps = 4x4 pixels at quarter size). */
      var sr = srcRect || { x: 0, y: 0, w: W / D, h: H / D }, sx = f0.w / W, sy = f0.h / H;
      var vx = Math.round(sr.x * D * sx), vw = Math.max(1, Math.round(sr.w * D * sx)), vh = Math.max(1, Math.round(sr.h * D * sy)), vy = f0.h - Math.round(sr.y * D * sy) - vh;
      gl.bindFramebuffer(gl.FRAMEBUFFER, f0.f);
      if (vx > 0 || vy > 0 || vx + vw < f0.w || vy + vh < f0.h) {
        gl.viewport(0, 0, f0.w, f0.h); gl.clearColor(opt.backdropColor[0], opt.backdropColor[1], opt.backdropColor[2], 1);
        each(rs, f0, function () { gl.clear(gl.COLOR_BUFFER_BIT); });
      }
      gl.viewport(vx, vy, vw, vh); gl.useProgram(prog.d.p); gl.bindTexture(gl.TEXTURE_2D, srcTex);
      var kaw = f0.div <= 2.001, f = kaw ? 1 : 0.25;
      gl.uniform2f(prog.d.u.px, f / vw, f / vh); gl.uniform1f(prog.d.u.flip, 1); gl.uniform1f(prog.d.u.cw, kaw ? 4 : 0);
      each(rs, f0, tri);
      if (P.pre) {
        gl.bindFramebuffer(gl.FRAMEBUFFER, l0.f); gl.viewport(0, 0, l0.w, l0.h); gl.bindTexture(gl.TEXTURE_2D, P.pre.t);
        gl.uniform2f(prog.d.u.px, 1 / l0.w, 1 / l0.h); gl.uniform1f(prog.d.u.flip, 0); gl.uniform1f(prog.d.u.cw, 4); each(rs, l0, tri);
      }
      if (withFlats) drawFlats(l0);
      /* 2: down */
      gl.useProgram(prog.d.p); gl.uniform1f(prog.d.u.flip, 0); gl.uniform1f(prog.d.u.cw, 4);
      for (i = 1; i < m; i++) {
        gl.bindFramebuffer(gl.FRAMEBUFFER, L[i].f); gl.viewport(0, 0, L[i].w, L[i].h); gl.bindTexture(gl.TEXTURE_2D, L[i - 1].t);
        gl.uniform2f(prog.d.u.px, 1 / L[i].w, 1 / L[i].h); each(rs, L[i], tri);
      }
      /* 3: up (with one level: a single pass at the same size) */
      gl.useProgram(prog.u.p); t = L[m - 1].t;
      for (i = m === 1 ? 0 : m - 2; i >= 0; i--) {
        gl.bindFramebuffer(gl.FRAMEBUFFER, L[i].f2); gl.viewport(0, 0, L[i].w, L[i].h); gl.bindTexture(gl.TEXTURE_2D, t);
        gl.uniform2f(prog.u.u.px, 1 / L[i].w, 1 / L[i].h); each(rs, L[i], tri); t = L[i].t2;
      }
      P.out = L[0].t2; P.ready = true;
      if (withFlats) stats.flatPyramids++; else stats.pyramids++;
    }
    function drawFlats(l0) {
      var u = prog.f.u;
      gl.viewport(0, 0, l0.w, l0.h); gl.useProgram(prog.f.p); gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      gl.uniform2f(u.res, W, H); gl.uniform1f(u.mg, 0); gl.uniform1f(u.aa, l0.div);
      flats.forEach(function (fl) {
        if (fl.hidden) return;
        var c = fl.color || [0, 0, 0, 1];
        gl.uniform4f(u.rc, fl.x * D, fl.y * D, fl.w * D, fl.h * D); gl.uniform1f(u.rad, fl.radius * D);
        gl.uniform4f(u.col, c[0], c[1], c[2], c[3] == null ? 1 : c[3]); gl.uniform1f(u.useT, fl.tex && fl.ok ? 1 : 0);
        if (fl.tex && fl.ok) gl.bindTexture(gl.TEXTURE_2D, fl.tex);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      });
      gl.disable(gl.BLEND);
    }
    function upload(t, s) {
      try {
        if (!(s.width || s.videoWidth)) return false;
        gl.bindTexture(gl.TEXTURE_2D, t); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, s); return true;
      } catch (e) { return false; }
    }

    /* ---------- the glass faces ---------- */
    function drawPanels() {
      var u = prog.g.u, hc = moreC(), st = isStatic(), ln = LENS[opt.lens], i, p, K, sh, band, amt, tA, bound = null, t, tt, tin, mg, sm, useB;
      gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, W, H); gl.disable(gl.SCISSOR_TEST);
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
      stats.draws++;
      if (!order.length) return;
      gl.useProgram(prog.g.p); gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      gl.uniform2f(u.res, W, H); gl.uniform1f(u.dpr, D); gl.uniform3f(u.face, opt.face.sat, opt.face.mul, opt.face.add);
      for (i = 0; i < order.length; i++) {
        p = order[i]; if (!p.visible || p.opacity <= 0 || p.w <= 0 || p.h <= 0) continue;
        K = p.K; sh = Math.min(p.w, p.h);
        useB = p.over === 'flats' && flats.size && pyrB && pyrB.ready;
        t = st ? null : useB ? pyrB.out : pyrA && pyrA.ready ? pyrA.out : null;
        if (t && t !== bound) { gl.bindTexture(gl.TEXTURE_2D, t); bound = t; }
        /* lens: band follows the panel's size; no lens with Increase Contrast or when the panel asks for none */
        if (ln[0] && !hc && p.lens !== false) { band = Math.max(0.5, Math.min(ln[1], sh / ln[0])); amt = Math.min(sh / 2, Math.max(24, band * 1.2)); } else { band = 0.5; amt = 0; }
        tin = t ? (p.tint || opt.tint) : (p.solid || opt.solid);
        tA = p.tintAmount != null ? p.tintAmount : K.tint; if (hc) tA = Math.max(tA, 0.82);
        /* shadow (Apple's numbers): offset 8, radius 4 + 20t, opacity 0.04 + 0.56t, t from the short side between 64 and 160 */
        sm = p.shadow != null ? +p.shadow : K.shadow; tt = Math.max(0, Math.min(1, (sh - 64) / 96)); mg = sm > 0 ? (4 + 20 * tt + 8) * D + 1 : 1;
        gl.uniform4f(u.rc, p.x * D, p.y * D, p.w * D, p.h * D); gl.uniform1f(u.mg, mg);
        gl.uniform1f(u.rad, Math.min(p.radius, sh / 2) * D); gl.uniform1f(u.band, band * D); gl.uniform1f(u.amt, amt * D);
        gl.uniform4f(u.tint, tin[0], tin[1], tin[2], tA);
        gl.uniform4f(u.rimp, opt.rim.width * D, hc ? 0 : opt.rim.base, hc ? 0 : opt.rim.lit, hc ? 0.6 : 0);
        gl.uniform3f(u.shd, 8 * D, (4 + 20 * tt) * D, sm > 0 ? sm * (0.04 + 0.56 * tt) : 0);
        gl.uniform2f(u.md, t ? 0 : 1, p.opacity);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      }
      gl.disable(gl.BLEND);
    }

    /* ---------- fallback: plain tint with noise on a 2D canvas (WebGL2 missing or lost) ---------- */
    var noise = null;
    function noiseTile() {
      if (noise) return noise;
      var c = document.createElement('canvas'), x, d, i, v; c.width = c.height = 64; x = c.getContext('2d'); d = x.createImageData(64, 64);
      for (i = 0; i < d.data.length; i += 4) { v = Math.random() * 255 | 0; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; }
      x.putImageData(d, 0, 0); return (noise = c);
    }
    function fallbackOn(why) {
      mode = 'fallback'; reason = why; panelsDirty = true;
      var c = null, x = null, own = false, cs;
      if (!gl) { try { x = canvas.getContext('2d'); if (x) c = canvas; } catch (e) { } }
      if (!x) {
        c = o.fallbackCanvas || document.createElement('canvas'); own = !o.fallbackCanvas;
        if (own) {
          cs = root.getComputedStyle ? getComputedStyle(canvas) : {};
          c.className = canvas.className; c.setAttribute('aria-hidden', 'true');
          c.style.cssText = 'position:' + (cs.position === 'fixed' ? 'fixed' : 'absolute') + ';left:' + canvas.offsetLeft + 'px;top:' + canvas.offsetTop + 'px;width:' + canvas.clientWidth + 'px;height:' + canvas.clientHeight + 'px;pointer-events:none;z-index:' + (cs.zIndex || 'auto');
          if (canvas.parentNode) canvas.parentNode.insertBefore(c, canvas.nextSibling);
        }
        x = c.getContext('2d');
        fb = { c: c, x: x, own: own, vis: canvas.style.visibility }; canvas.style.visibility = 'hidden';
      } else fb = { c: c, x: x, own: false, vis: null };
      if (opt.onFallback) try { opt.onFallback(true, why); } catch (e) { }
    }
    function fallbackOff() {
      if (!fb) return;
      if (fb.own && fb.c.parentNode) fb.c.parentNode.removeChild(fb.c);
      else if (fb.c !== canvas) fb.x.clearRect(0, 0, fb.c.width, fb.c.height);
      if (fb.vis != null) canvas.style.visibility = fb.vis;
      fb = null;
      if (opt.onFallback) try { opt.onFallback(false, ''); } catch (e) { }
    }
    function rgb(c, a) { return 'rgba(' + Math.round(c[0] * 255) + ',' + Math.round(c[1] * 255) + ',' + Math.round(c[2] * 255) + ',' + a + ')'; }
    function draw2d() {
      var c = fb.c, x = fb.x, hc = moreC(), i, p, r, pat;
      if (c.width !== W || c.height !== H) { c.width = W; c.height = H; if (fb.own) { c.style.width = W / D + 'px'; c.style.height = H / D + 'px'; } }
      x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, W, H);
      pat = x.createPattern(noiseTile(), 'repeat'); x.setTransform(D, 0, 0, D, 0, 0);
      for (i = 0; i < order.length; i++) {
        p = order[i]; if (!p.visible || p.opacity <= 0) continue;
        r = Math.min(p.radius, Math.min(p.w, p.h) / 2);
        x.beginPath(); x.moveTo(p.x + r, p.y); x.arcTo(p.x + p.w, p.y, p.x + p.w, p.y + p.h, r); x.arcTo(p.x + p.w, p.y + p.h, p.x, p.y + p.h, r); x.arcTo(p.x, p.y + p.h, p.x, p.y, r); x.arcTo(p.x, p.y, p.x + p.w, p.y, r); x.closePath();
        x.globalAlpha = p.opacity; x.fillStyle = rgb(p.solid || opt.solid, 1); x.fill();
        x.globalAlpha = p.opacity * 0.035; x.fillStyle = pat; x.fill();
        x.globalAlpha = p.opacity; x.lineWidth = 1; x.strokeStyle = hc ? 'rgba(255,255,255,.6)' : 'rgba(255,255,255,.12)'; x.stroke();
      }
      x.globalAlpha = 1; stats.draws++;
    }

    /* ---------- context ---------- */
    function onLost(e) {
      e.preventDefault(); stats.lost++;
      srcReady = false; pyrA = pyrB = null; prog = null;
      fallbackOn('lost'); ask();
    }
    function onRestored() {
      stats.restored++;
      try { glInit(); } catch (err) { reason = 'restore failed'; return; }
      fallbackOff(); mode = 'gl'; reason = '';
      if (W && (canvas.width !== W || canvas.height !== H)) { canvas.width = W; canvas.height = H; }
      ask();
    }
    function start() {
      if (!o.forceFallback) {
        var at = { alpha: true, premultipliedAlpha: true, antialias: false, depth: false, stencil: false, preserveDrawingBuffer: false, powerPreference: 'high-performance', failIfMajorPerformanceCaveat: !opt.allowSoftware };
        try { gl = canvas.getContext('webgl2', at); } catch (e) { gl = null; }
      }
      if (gl) {
        canvas.addEventListener('webglcontextlost', onLost, false); canvas.addEventListener('webglcontextrestored', onRestored, false);
        try { glInit(); mode = 'gl'; } catch (e) { if (root.console) console.warn('AudioLabGlass: ' + e.message); fallbackOn('shader'); }
      } else fallbackOn(o.forceFallback ? 'forced' : 'no webgl2');
    }

    /* ---------- public ---------- */
    function sortOrder() {
      order = Array.from(panels.values()).sort(function (a, b) { return a.z - b.z || a.seq - b.seq; });
    }
    function setP(p, d) {
      var ch = false, r, k;
      if (d.rect) { r = rectOf(d.rect); if (r.x !== p.x || r.y !== p.y || r.w !== p.w || r.h !== p.h) { p.x = r.x; p.y = r.y; p.w = r.w; p.h = r.h; ch = true; } }
      if (d.kind != null && d.kind !== p.kind) { p.kind = d.kind; p.K = kinds[d.kind] || kinds.window; ch = true; }
      if (d.z != null && d.z !== p.z) { p.z = +d.z; ch = true; sortOrder(); }
      ['radius', 'opacity', 'visible', 'over', 'tint', 'solid', 'tintAmount', 'shadow', 'lens'].forEach(function (k) {
        if (k in d && d[k] !== p[k]) { p[k] = d[k]; ch = true; if (k === 'over') bDirty = true; }
      });
      return ch;
    }
    var api = {
      version: VERSION, canvas: canvas, stats: stats,
      get gl() { return gl; },
      get mode() { return mode; },            /* 'gl' or 'fallback' */
      get reason() { return reason; },        /* why the fallback is on */
      get pending() { return mode === 'gl' && (srcDirty || flatWait) && !isStatic(); },   /* a capped backdrop refresh is waiting: call render() again next frame */
      get info() { return { mode: mode, reason: reason, width: W, height: H, dpr: D, quality: quality, lens: opt.lens, blur: opt.blur, levels: plan(), rate: QSET[quality].rate, isStatic: isStatic(), reduceTransparency: reduceT(), increaseContrast: moreC(), regions: regs ? regs.length : 0, panels: panels.size, flats: flats.size }; },

      addPanel: function (d) {
        var p = panels.get(d.id);
        if (!p) { p = { id: d.id, x: 0, y: 0, w: 0, h: 0, radius: 0, kind: 'window', K: kinds.window, z: 0, seq: seq++, visible: true, opacity: 1, over: 'backdrop' }; panels.set(d.id, p); }
        setP(p, d); sortOrder(); panelsDirty = true; return api;
      },
      updatePanel: function (id, d) {
        if (id && typeof id === 'object') { d = id; id = d.id; }
        var p = panels.get(id); if (!p) return false;
        if (setP(p, d || {})) panelsDirty = true; return true;
      },
      removePanel: function (id) { if (panels.delete(id)) { sortOrder(); panelsDirty = true; return true; } return false; },
      hasPanel: function (id) { return panels.has(id); },

      /* the picture behind all glass. rect = where it sits on the engine canvas in CSS px (default: it covers the canvas) */
      setBackdrop: function (source, d) { src = source || null; srcRect = d && d.rect ? rectOf(d.rect) : null; srcDirty = !!src; lastUp = -1e9; panelsDirty = true; return api; },
      markDirty: function () { if (src) srcDirty = true; },

      /* flat pictures over the backdrop, seen only by panels with over:'flats' (glass that floats over DOM). color = [r,g,b,a] 0..1, or source = a canvas */
      setFlat: function (id, d) {
        var f = flats.get(id), r; if (!f) { f = { id: id, x: 0, y: 0, w: 0, h: 0, radius: 0, color: null, source: null, tex: null, ok: false, dirty: false, hidden: false }; flats.set(id, f); }
        if (d.rect) { r = rectOf(d.rect); f.x = r.x; f.y = r.y; f.w = r.w; f.h = r.h; }
        if (d.radius != null) f.radius = +d.radius; if (d.color) f.color = d.color; if ('hidden' in d) f.hidden = !!d.hidden;
        if ('source' in d) { f.source = d.source || null; f.dirty = !!f.source; if (!f.source) f.ok = false; }
        bDirty = true; return api;
      },
      markFlatDirty: function (id) { var f = flats.get(id); if (f && f.source) f.dirty = true; },
      removeFlat: function (id) { var f = flats.get(id); if (!f) return false; if (f.tex && gl) gl.deleteTexture(f.tex); flats.delete(id); bDirty = panelsDirty = true; return true; },

      setLensPreset: function (n) { if (!(n in LENS) || n === opt.lens) return; opt.lens = n; panelsDirty = true; },
      setBlurPreset: function (n) { if (!(n in BLUR) || n === opt.blur) return; opt.blur = n; if (mode === 'gl') dropPyr(); },
      /* 3 or 'high': half-size blur, every change. 2 'medium': quarter-size, backdrop 60 per second. 1 'low': quarter-size, 30 per second. 0 'static': plain tint with noise. */
      setQuality: function (q) { if (q in QNAME) q = QNAME[q]; q = Math.max(0, Math.min(3, q | 0)); if (q === quality) return; quality = q; if (mode === 'gl') dropPyr(); panelsDirty = true; },
      /* true / false to force, null to follow the system setting */
      setAccessibility: function (d) { if ('reduceTransparency' in d) acc.rt = d.reduceTransparency; if ('increaseContrast' in d) acc.ic = d.increaseContrast; panelsDirty = true; },
      setFace: function (d) { for (var k in d) opt.face[k] = d[k]; panelsDirty = true; },

      /* call when the canvas changed size (done automatically with a ResizeObserver unless autoResize:false) */
      resize: function (cw, ch, dpr) {
        var d = dpr || opt.dpr || Math.min(opt.maxDpr, root.devicePixelRatio || 1), w, h;
        cw = cw || canvas.clientWidth; ch = ch || canvas.clientHeight; if (!cw || !ch) return false;
        w = Math.round(cw * d); h = Math.round(ch * d);
        if (w === W && h === H && d === D) return false;
        W = w; H = h; D = d;
        if (mode === 'gl') { canvas.width = W; canvas.height = H; dropPyr(); }
        panelsDirty = true; return true;
      },

      /* draws only what changed. Returns true when the canvas was redrawn. now = the frame time (performance.now() if left out). */
      render: function (now) {
        if (destroyed) return false;
        stats.renders++;
        if (!W) api.resize();
        if (mode !== 'gl') { if (mode === 'fallback' && panelsDirty && W) { draw2d(); panelsDirty = false; return true; } stats.skipped++; return false; }
        if (gl.isContextLost()) { stats.skipped++; return false; }
        var rebuilt = false, any = false, needA = false, needB = false, i, p, rate, rk;
        for (i = 0; i < order.length; i++) { p = order[i]; if (p.visible && p.opacity > 0) { any = true; if (p.over === 'flats' && flats.size) needB = true; else needA = true; } }
        if (any && !isStatic()) {
          rate = QSET[quality].rate; if (now == null) now = performance.now();
          if (srcDirty && (!srcReady || !rate || now - lastUp >= 1000 / rate - 2)) {
            if (upload(srcTex, src)) { srcReady = true; stats.uploads++; pyrDirty = bDirty = true; lastUp = now; }
            srcDirty = false;
          }
          if (srcReady) {
            regs = regions(); rk = regs ? regs.join(';') : 'all';
            if (rk !== regKey) { regKey = rk; pyrDirty = true; }
            if (needA && (pyrDirty || !pyrA)) { if (!pyrA) pyrA = makePyr(); build(pyrA, false); pyrDirty = false; rebuilt = true; }
            if (needB) {
              /* fed canvases follow the same refresh cap as the backdrop */
              var fdue = !rate || now - lastFlat >= 1000 / rate - 2, fup = false; flatWait = false;
              flats.forEach(function (f) { if (f.source && f.dirty) { if (fdue || !f.tex) { if (!f.tex) f.tex = tex(0, 0); f.ok = upload(f.tex, f.source); f.dirty = false; stats.flatUploads++; bDirty = fup = true; } else flatWait = true; } });
              if (fup) lastFlat = now;
              if (bDirty || !pyrB) { if (!pyrB) pyrB = makePyr(); build(pyrB, true); bDirty = false; rebuilt = true; }
            }
          }
        }
        if (!panelsDirty && !rebuilt) { stats.skipped++; return false; }
        drawPanels(); panelsDirty = false; return true;
      },

      /* for tests and the bench page */
      debug: {
        upload: function () { if (mode === 'gl' && src) upload(srcTex, src); },
        rebuild: function () { if (mode === 'gl' && srcReady) { if (pyrA) build(pyrA, false); if (pyrB) build(pyrB, true); } },
        draw: function () { if (mode === 'gl') drawPanels(); },
        lose: function () { loseExt = gl && !gl.isContextLost() && gl.getExtension('WEBGL_lose_context'); if (loseExt) loseExt.loseContext(); return !!loseExt; },
        restore: function () { if (loseExt && gl.isContextLost()) loseExt.restoreContext(); return !!loseExt; }
      },

      destroy: function () {
        if (destroyed) return; destroyed = true;
        canvas.removeEventListener('webglcontextlost', onLost, false); canvas.removeEventListener('webglcontextrestored', onRestored, false);
        if (mRT && mRT.removeEventListener) mRT.removeEventListener('change', onMq); if (mIC && mIC.removeEventListener) mIC.removeEventListener('change', onMq);
        if (ro) ro.disconnect();
        if (fb) { opt.onFallback = null; fallbackOff(); }
        if (gl && !gl.isContextLost()) { freePyr(pyrA); freePyr(pyrB); if (srcTex) gl.deleteTexture(srcTex); flats.forEach(function (f) { if (f.tex) gl.deleteTexture(f.tex); });
          /* give the context back at once (browsers allow only a handful per page) */
          var le = gl.getExtension('WEBGL_lose_context'); if (le) le.loseContext(); }
        panels.clear(); flats.clear(); order = []; src = null;
      }
    };

    start();
    if (mRT && mRT.addEventListener) mRT.addEventListener('change', onMq);
    if (mIC && mIC.addEventListener) mIC.addEventListener('change', onMq);
    var ro = null, loseExt = null;
    if (opt.autoResize && root.ResizeObserver) { ro = new ResizeObserver(function () { if (api.resize()) ask(); }); ro.observe(canvas); }
    api.resize();
    if (o.quality != null) api.setQuality(o.quality);
    return api;
  }

  root.AudioLabGlass = { create: create, version: VERSION, LENS: LENS, BLUR: BLUR, KINDS: KINDS };
})(typeof window !== 'undefined' ? window : this);
