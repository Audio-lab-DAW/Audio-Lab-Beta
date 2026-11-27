/* AudioLab glass engine (tasks G2, G2b and G2c). Plain JS, no build step, no dependencies.
   One WebGL2 canvas. The engine draws its own backdrop on the GPU: lane backgrounds, clips as flat rectangles, the playhead,
   straight into a quarter-size target (one instanced draw call), then one dual-Kawase pyramid, then every glass surface as one quad in one shader.
   No canvas is uploaded on this path. A small (quarter-size) copy of a canvas is the fallback and the route for other sources (piano roll, device displays).
   Glass never samples glass.
   Use: const g = AudioLabGlass.create(canvas, opts); g.setScene({lanes, clips, playheadX, scrollX, zoom, rect}); g.addPanel({id, rect, radius, kind}); g.render();
        per frame: g.setPlayhead(x) / g.setView({scrollX, zoom}) / g.updatePanel(id, {rect}); g.render(t);
        small canvas: g.setOrigin(x, y) when the canvas does not start at the top left of the space the rectangles are given in (2.1)
   Docs: docs/glass-engine-module.md */
(function (root) {
  'use strict';
  var VERSION = '2.1.0';
  /* lens presets: [divisor of the short side, maximum band in px]. Apple's rule: band = min(short side / 4, 20). The user's default is wide (up to 45 px). */
  var LENS = { off: [0, 0], fine: [4, 12], apple: [4, 20], wide: [3, 45] };
  /* blur presets: how deep the pyramid goes (deepest level 1/4, 1/8, 1/16 of the size at level Glass) */
  var BLUR = { light: 2, regular: 3, heavy: 4 };
  /* levels. base = size of the backdrop target (4 = quarter, 8 = an eighth of the canvas in CSS px); cut = pyramid levels left out;
     rate = backdrop refreshes per second (0 = every change; canvas copies have their own cap, copyRate) */
  var LEVELS = { glass: { base: 4, cut: 1, lens: true, rate: 0 }, light: { base: 8, cut: 2, lens: false, rate: 30 }, solid: { base: 4, cut: 1, lens: false, rate: 0, st: true } };
  var QCOMPAT = { 3: 'glass', 2: 'glass', 1: 'light', 0: 'solid', high: 'glass', medium: 'glass', low: 'light', 'static': 'solid' };
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

  /* the backdrop drawn on the GPU: one instance per rectangle. r = x,y,w,h; c = colour; m = how the rectangle follows the view:
     0 clip (x and w in scene units, scrolled and zoomed; y scrolled), 1 lane (x, w in view px; y scrolled), 2 playhead (x from the uniform ph),
     3 fixed (view px), 4 clip title band (as 0, height in px). view = scrollX, scrollY, zoomX, zoomY; org = view rectangle x,y and the scene origin x,y (CSS px);
     sc = CSS px to target px. The quad is grown by half a target pixel (gr) and the fragment shader computes how much of each pixel the rectangle covers:
     arithmetic on the rectangle's own edges, ONE result per pixel, no texture lookup and no extra samples. A small target so gets the same picture as a
     full-size one reduced with a box filter (thin lines and slow scrolling do not shimmer) at the price of a few multiplications.
     FS_SCENE0 is the same without coverage (hard edges), only for the test page's "anti-aliasing off" row.
     The background colour is not a rectangle: it is the clear of the view rectangle (2.1). */
  var VS_SCENE = '#version 300 es\nlayout(location=0) in vec4 r;layout(location=1) in vec4 c;layout(location=2) in float m;uniform vec4 view,org;uniform vec2 sc,tsz;uniform float ph,gr;flat out vec4 col;flat out vec4 box;' +
    'void main(){bool cl=m<.5||m>3.5,pl=m>1.5&&m<2.5,ys=m<1.5||m>3.5;float X=cl?org.z+(r.x-view.x)*view.z:pl?org.z+(ph-view.x)*view.z+r.x:org.x+r.x,Wd=cl?r.z*view.z:r.z,' +
    'Y=ys?org.w+(r.y-view.y)*view.w:org.y+r.y,Ht=m<1.5?r.w*view.w:r.w;box=vec4(X,Y,X+Wd,Y+Ht)*sc.xyxy;vec2 k=vec2(gl_VertexID&1,gl_VertexID>>1),p=mix(box.xy-gr,box.zw+gr,k);' +
    'col=c;gl_Position=vec4(p.x/tsz.x*2.-1.,1.-p.y/tsz.y*2.,0.,1.);}';
  var FS_SCENE = '#version 300 es\nprecision highp float;flat in vec4 col;flat in vec4 box;uniform vec2 tsz;out vec4 o;' +
    'void main(){vec2 f=vec2(gl_FragCoord.x,tsz.y-gl_FragCoord.y);float a=clamp(min(f.x+.5,box.z)-max(f.x-.5,box.x),0.,1.)*clamp(min(f.y+.5,box.w)-max(f.y-.5,box.y),0.,1.)*col.a;o=vec4(col.rgb*a,a);}';

  var FS_SCENE0 = '#version 300 es\nprecision highp float;flat in vec4 col;flat in vec4 box;out vec4 o;void main(){o=vec4(col.rgb*col.a,col.a);}';

  var HEX = {};
  /* colour as [r,g,b] or [r,g,b,a] (0..1), or '#rgb', '#rrggbb', '#rrggbbaa', 'rgb(r,g,b)', 'rgba(r,g,b,a)' */
  function colOf(c) {
    if (!c) return [0, 0, 0, 1];
    if (typeof c !== 'string') return c;
    var v = HEX[c], h, n;
    if (v) return v;
    if (c.indexOf('rgb') === 0) { h = c.slice(c.indexOf('(') + 1).split(/[,\s\/]+/).map(parseFloat); return (HEX[c] = [(h[0] || 0) / 255, (h[1] || 0) / 255, (h[2] || 0) / 255, h[3] >= 0 ? h[3] : 1]); }
    h = c.charAt(0) === '#' ? c.slice(1) : c;
    if (h.length === 3 || h.length === 4) h = h.replace(/./g, '$&$&');
    n = parseInt(h.slice(0, 6), 16); if (isNaN(n)) n = 0;
    v = [(n >> 16 & 255) / 255, (n >> 8 & 255) / 255, (n & 255) / 255, h.length >= 8 ? parseInt(h.slice(6, 8), 16) / 255 : 1];
    return (HEX[c] = v);
  }
  function rectOf(r) {
    if (!r) return { x: 0, y: 0, w: 0, h: 0 };
    if (r.length === 4) return { x: +r[0], y: +r[1], w: +r[2], h: +r[3] };
    return { x: +(r.x != null ? r.x : r.left) || 0, y: +(r.y != null ? r.y : r.top) || 0, w: +(r.w != null ? r.w : r.width) || 0, h: +(r.h != null ? r.h : r.height) || 0 };
  }
  function mq(q) { try { return root.matchMedia ? root.matchMedia(q) : null; } catch (e) { return null; } }

  function create(canvas, o) {
    o = o || {};
    var opt = {
      lens: o.lens in LENS ? o.lens : 'wide',
      blur: o.blur in BLUR ? o.blur : 'light',
      copyRate: o.copyRate != null ? +o.copyRate : 60,          /* canvas copies per second at level Glass, at most (0 = every markDirty) */
      copyQuality: o.copyQuality || 'low',                     /* imageSmoothingQuality used when a canvas is reduced before the upload */
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
    var W = 0, H = 0, D = 1, OX = 0, OY = 0, level = 'glass', LV = LEVELS.glass;
    var userRate = o.backdropRate != null ? +o.backdropRate : null, dbg = { aa: true, freeze: false };
    var panels = new Map(), order = [], seq = 0, flats = new Map();
    var kind = 'none';   /* where the backdrop comes from: 'scene' (drawn on the GPU), 'copy' (a small copy of a canvas), 'none' */
    var scene = null, sVao = null, sBuf = null, geomDirty = false, sceneDirty = false, lastScene = -1e9;
    var src = null, srcRect = null, srcH = { tex: null, q: null, qx: null }, srcReady = false, lastUp = -1e9;
    var srcDirty = false, pyrDirty = true, bDirty = true, panelsDirty = true, lastFlat = -1e9, flatWait = false;
    var pyrA = null, pyrB = null, regs = null, regKey = '', regDirty = true, blank = null;
    var acc = { rt: o.reduceTransparency, ic: o.increaseContrast };
    var mRT = mq('(prefers-reduced-transparency: reduce)'), mIC = mq('(prefers-contrast: more)');
    var fb = null;   /* fallback: {c, x, own, vis} */
    /* sceneSends = rectangle lists sent to the GPU, sceneDraws = backdrop drawn on the GPU, uploads = canvas copies of the backdrop (stays 0 on the scene path),
       uploadPixels = size of the largest copy so far */
    var stats = { renders: 0, skipped: 0, draws: 0, sceneSends: 0, sceneDraws: 0, uploads: 0, uploadPixels: 0, pyramids: 0, flatPyramids: 0, flatUploads: 0, lost: 0, restored: 0 };

    function ask() { if (opt.requestRender) try { opt.requestRender(); } catch (e) { } }
    function reduceT() { return acc.rt != null ? !!acc.rt : !!(mRT && mRT.matches); }
    function moreC() { return acc.ic != null ? !!acc.ic : !!(mIC && mIC.matches); }
    function isStatic() { return !!LV.st || reduceT() || kind === 'none'; }
    /* refreshes per second: the app's own cap (setBackdropRate) wins, never faster than the level's */
    function capOf(copy) { var r = LV.rate || (copy ? opt.copyRate : 0); return userRate > 0 ? (r ? Math.min(r, userRate) : userRate) : r; }
    function onMq() { panelsDirty = regDirty = true; ask(); }

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
      prog = { d: mk(VS_FULL, FS_DOWN), u: mk(VS_FULL, FS_UP), g: mk(VS_QUAD, FS_GLASS), f: mk(VS_QUAD, FS_FLAT), s: mk(VS_SCENE, FS_SCENE), s0: null };
      /* the rectangles of the scene: 24 bytes each (x,y,w,h floats, colour 4 bytes, mode float), one instance per rectangle */
      sVao = gl.createVertexArray(); sBuf = gl.createBuffer(); gl.bindVertexArray(sVao); gl.bindBuffer(gl.ARRAY_BUFFER, sBuf);
      gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 4, gl.FLOAT, false, 24, 0); gl.vertexAttribDivisor(0, 1);
      gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 4, gl.UNSIGNED_BYTE, true, 24, 16); gl.vertexAttribDivisor(1, 1);
      gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 1, gl.FLOAT, false, 24, 20); gl.vertexAttribDivisor(2, 1);
      vao = gl.createVertexArray(); gl.bindVertexArray(vao);
      gl.disable(gl.DEPTH_TEST); gl.disable(gl.CULL_FACE); gl.activeTexture(gl.TEXTURE0);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
      srcH.tex = tex(0, 0); blank = tex(1, 1); srcReady = false; pyrA = pyrB = null;
      flats.forEach(function (f) { f.tex = null; f.dirty = !!f.source; });
      srcDirty = !!src; geomDirty = sceneDirty = !!scene; lastScene = lastUp = -1e9; pyrDirty = bDirty = panelsDirty = regDirty = true; regKey = '';
    }
    /* level plan: sizes as divisors of the canvas in CSS pixels, so the blur looks the same on a 1x and a 2x screen (and a 2x screen pays no more).
       Glass: 4,(8),(16); "light" is one level plus a same-size pass. Light: 8,(16). The first level is the target the backdrop is drawn into. */
    function plan() {
      var m = Math.max(1, BLUR[opt.blur] - LV.cut), a = [], i;
      for (i = 0; i < m; i++) a.push(LV.base << i);
      return a;
    }
    function freePyr(P) {
      if (!P || !gl) return;
      P.lev.forEach(function (L) { gl.deleteTexture(L.t); gl.deleteFramebuffer(L.f); if (L.t2) { gl.deleteTexture(L.t2); gl.deleteFramebuffer(L.f2); } });
    }
    function makePyr() {
      var pl = plan(), lev = [], i, L, a, b;
      for (i = 0; i < pl.length; i++) {
        L = { div: pl[i] * D, w: Math.max(2, Math.round(W / (pl[i] * D))), h: Math.max(2, Math.round(H / (pl[i] * D))) };
        a = target(L.w, L.h); L.t = a.t; L.f = a.f;
        if (i < pl.length - 1 || pl.length === 1) { b = target(L.w, L.h); L.t2 = b.t; L.f2 = b.f; }
        lev.push(L);
      }
      return { lev: lev, ready: false };
    }
    function dropPyr() { freePyr(pyrA); freePyr(pyrB); pyrA = pyrB = null; pyrDirty = bDirty = panelsDirty = regDirty = true; regKey = ''; }

    /* ---------- which part of the screen is under glass (only when nothing can move) ---------- */
    function regions() {
      if (!opt.regionCull) return null;
      var pl = plan(), M = 8 * pl[pl.length - 1] * D, out = [], area = 0, i, p, x0, y0, x1, y1;
      for (i = 0; i < order.length; i++) {
        p = order[i]; if (!p.visible) continue;
        if (!p.K.fixed) return null;
        x0 = Math.max(0, (p.x - OX) * D - M); y0 = Math.max(0, (p.y - OY) * D - M); x1 = Math.min(W, (p.x - OX + p.w) * D + M); y1 = Math.min(H, (p.y - OY + p.h) * D + M);
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

    /* ---------- the backdrop drawn on the GPU ---------- */
    function grow(sc, n) {
      if (sc.buf && sc.buf.byteLength >= n * 24) return;
      var nb = new ArrayBuffer(Math.max(n * 24, sc.buf ? sc.buf.byteLength * 2 : 24 * 256)), u = new Uint8Array(nb);
      if (sc.buf) u.set(sc.u8);
      sc.buf = nb; sc.f32 = new Float32Array(nb); sc.u8 = u;
    }
    function put(sc, x, y, w, h, c, a, m) {
      grow(sc, sc.n + 1);
      var o = sc.n * 6, f = sc.f32, u = sc.u8, k = sc.n * 24 + 16;
      f[o] = x; f[o + 1] = y; f[o + 2] = w; f[o + 3] = h; f[o + 5] = m;
      u[k] = c[0] * 255 + 0.5; u[k + 1] = c[1] * 255 + 0.5; u[k + 2] = c[2] * 255 + 0.5; u[k + 3] = (c[3] == null ? 1 : c[3]) * a * 255 + 0.5;
      sc.n++;
    }
    /* the rectangle list: lanes, clips (body, title band, selection tint), then the playhead as the last one. The background is the clear in drawScene. */
    function listScene() {
      var sc = scene, BIG = 1e6, i, c, col, th, L = sc.lanes || [], C = sc.clips || [], sel = colOf(sc.selColor);
      sc.n = 0;
      for (i = 0; i < L.length; i++) { c = L[i]; put(sc, c.x || 0, c.y, c.w != null ? c.w : BIG, c.h, colOf(c.color), 1, 1); }
      for (i = 0; i < C.length; i++) {
        c = C[i]; col = colOf(c.color);
        put(sc, c.x, c.y, c.w, c.h, col, c.alpha != null ? c.alpha : sc.bodyAlpha, 0);
        th = c.titleH != null ? c.titleH : sc.titleH; if (th > 0) put(sc, c.x, c.y, c.w, Math.min(th, c.h), col, 1, 4);
        if (c.selected) put(sc, c.x, c.y, c.w, c.h, sel, 1, 0);
      }
      put(sc, -sc.playheadW / 2, 0, sc.playheadW, BIG, colOf(sc.playheadColor), 1, 2);
      geomDirty = sceneDirty = true;
    }
    function sendScene() {
      gl.bindBuffer(gl.ARRAY_BUFFER, sBuf); gl.bufferData(gl.ARRAY_BUFFER, new Uint8Array(scene.buf, 0, scene.n * 24), gl.DYNAMIC_DRAW);
      geomDirty = false; stats.sceneSends++;
    }
    function drawScene(l0, rs) {
      var sc = scene, P = dbg.aa ? prog.s : (prog.s0 || (prog.s0 = mk(VS_SCENE, FS_SCENE0))), u = P.u, cw = W / D, ch = H / D, R = sc.rect, v = R ? { x: R.x - OX, y: R.y - OY, w: R.w, h: R.h } : { x: 0, y: 0, w: cw, h: ch }, sx = l0.w / cw, sy = l0.h / ch;
      var bg = colOf(sc.bg || opt.backdropColor), ba = bg[3] == null ? 1 : bg[3], b0 = opt.backdropColor;
      var n = sc.n - (sc.playheadX == null ? 1 : 0), i, r, x0, y0, x1, y1;
      /* the view rectangle in target pixels (y up for the scissor) */
      var vx0 = Math.max(0, Math.floor(v.x * sx)), vx1 = Math.min(l0.w, Math.ceil((v.x + v.w) * sx)), vy0 = Math.max(0, l0.h - Math.ceil((v.y + v.h) * sy)), vy1 = Math.min(l0.h, l0.h - Math.floor(v.y * sy));
      /* one clear per pixel: where the view rectangle covers the whole target, the clear with the scene's background is the only one */
      if (vx0 > 0 || vy0 > 0 || vx1 < l0.w || vy1 < l0.h) each(rs, l0, function () { gl.clear(gl.COLOR_BUFFER_BIT); });
      if (vx1 <= vx0 || vy1 <= vy0) return;
      gl.viewport(0, 0, l0.w, l0.h); gl.useProgram(P.p); gl.bindVertexArray(sVao);
      gl.clearColor(bg[0] * ba + b0[0] * (1 - ba), bg[1] * ba + b0[1] * (1 - ba), bg[2] * ba + b0[2] * (1 - ba), 1);
      gl.uniform4f(u.view, sc.scrollX, sc.scrollY, sc.zoom, sc.zoomY); gl.uniform4f(u.org, v.x, v.y, v.x + sc.originX, v.y + sc.originY);
      gl.uniform2f(u.sc, sx, sy); gl.uniform2f(u.tsz, l0.w, l0.h); gl.uniform1f(u.ph, sc.playheadX == null ? 0 : sc.playheadX); gl.uniform1f(u.gr, dbg.aa ? 0.5 : 0);
      gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA); gl.enable(gl.SCISSOR_TEST);
      if (!rs) { gl.scissor(vx0, vy0, vx1 - vx0, vy1 - vy0); gl.clear(gl.COLOR_BUFFER_BIT); if (n > 0) gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, 4, n); }
      else for (i = 0; i < rs.length; i++) {
        r = rs[i]; x0 = Math.max(vx0, Math.floor(r[0] * l0.w / W)); x1 = Math.min(vx1, Math.ceil((r[0] + r[2]) * l0.w / W)); y0 = Math.max(vy0, Math.floor((H - r[1] - r[3]) * l0.h / H)); y1 = Math.min(vy1, Math.ceil((H - r[1]) * l0.h / H));
        if (x1 > x0 && y1 > y0) { gl.scissor(x0, y0, x1 - x0, y1 - y0); gl.clear(gl.COLOR_BUFFER_BIT); if (n > 0) gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, 4, n); }
      }
      gl.disable(gl.SCISSOR_TEST); gl.disable(gl.BLEND); gl.bindVertexArray(vao);
      stats.sceneDraws++;
    }

    /* ---------- the blur pyramid ---------- */
    function build(P, withFlats) {
      var L = P.lev, m = L.length, rs = withFlats ? null : regs, i, t, l0 = L[0], bc = opt.backdropColor;
      gl.disable(gl.BLEND);
      /* 1: the backdrop into the first level, which is already the small target: the scene is drawn there directly, a canvas copy arrives at that size */
      gl.bindFramebuffer(gl.FRAMEBUFFER, l0.f); gl.viewport(0, 0, l0.w, l0.h); gl.clearColor(bc[0], bc[1], bc[2], 1);
      if (kind === 'scene') drawScene(l0, rs);
      else {
        each(rs, l0, function () { gl.clear(gl.COLOR_BUFFER_BIT); });
        var sr = srcRect ? { x: srcRect.x - OX, y: srcRect.y - OY, w: srcRect.w, h: srcRect.h } : { x: 0, y: 0, w: W / D, h: H / D }, sx = l0.w * D / W, sy = l0.h * D / H;
        var vx = Math.round(sr.x * sx), vw = Math.max(1, Math.round(sr.w * sx)), vh = Math.max(1, Math.round(sr.h * sy)), vy = l0.h - Math.round(sr.y * sy) - vh;
        gl.viewport(vx, vy, vw, vh); gl.useProgram(prog.d.p); gl.bindTexture(gl.TEXTURE_2D, srcH.tex);
        gl.uniform2f(prog.d.u.px, 0, 0); gl.uniform1f(prog.d.u.flip, 1); gl.uniform1f(prog.d.u.cw, 4);
        each(rs, l0, tri);
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
        gl.uniform4f(u.rc, (fl.x - OX) * D, (fl.y - OY) * D, fl.w * D, fl.h * D); gl.uniform1f(u.rad, fl.radius * D);
        gl.uniform4f(u.col, c[0], c[1], c[2], c[3] == null ? 1 : c[3]); gl.uniform1f(u.useT, fl.tex && fl.ok ? 1 : 0);
        /* a plain colour still needs some texture bound that is not the target being drawn into */
        gl.bindTexture(gl.TEXTURE_2D, fl.tex && fl.ok ? fl.tex : blank);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      });
      gl.disable(gl.BLEND);
    }
    /* a canvas goes to the GPU as a small copy: reduced on a 2D canvas to the size of the first pyramid level (a quarter, at Light an eighth, of its size on screen)
       and only that is uploaded. A source that is already that small is uploaded as it is. Never a full-size upload. */
    function upload(h, s, cssW, cssH) {
      try {
        var sw = s.width || s.videoWidth, sh = s.height || s.videoHeight, tw, th;
        if (!sw || !sh) return 0;
        tw = Math.max(2, Math.round(cssW / LV.base)); th = Math.max(2, Math.round(cssH / LV.base));
        if (!h.tex) h.tex = tex(0, 0);
        gl.bindTexture(gl.TEXTURE_2D, h.tex);
        if (sw * sh <= tw * th * 1.5) { gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, s); tw = sw; th = sh; }
        else {
          if (!h.q) { h.q = document.createElement('canvas'); h.qx = h.q.getContext('2d', { alpha: false }); }
          if (h.q.width !== tw || h.q.height !== th) { h.q.width = tw; h.q.height = th; }
          h.qx.imageSmoothingEnabled = true; h.qx.imageSmoothingQuality = opt.copyQuality; h.qx.drawImage(s, 0, 0, tw, th);
          gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, h.q);
        }
        if (tw * th > stats.uploadPixels) stats.uploadPixels = tw * th;
        return tw * th;
      } catch (e) { return 0; }
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
        if (ln[0] && LV.lens && !hc && p.lens !== false) { band = Math.max(0.5, Math.min(ln[1], sh / ln[0])); amt = Math.min(sh / 2, Math.max(24, band * 1.2)); } else { band = 0.5; amt = 0; }
        tin = t ? (p.tint || opt.tint) : (p.solid || opt.solid);
        tA = p.tintAmount != null ? p.tintAmount : K.tint; if (hc) tA = Math.max(tA, 0.82);
        /* shadow (Apple's numbers): offset 8, radius 4 + 20t, opacity 0.04 + 0.56t, t from the short side between 64 and 160 */
        sm = p.shadow != null ? +p.shadow : K.shadow; tt = Math.max(0, Math.min(1, (sh - 64) / 96)); mg = sm > 0 ? (4 + 20 * tt + 8) * D + 1 : 1;
        gl.uniform4f(u.rc, (p.x - OX) * D, (p.y - OY) * D, p.w * D, p.h * D); gl.uniform1f(u.mg, mg);
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
      pat = x.createPattern(noiseTile(), 'repeat'); x.setTransform(D, 0, 0, D, -OX * D, -OY * D);
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
      srcReady = false; pyrA = pyrB = null; prog = null; srcH.tex = null;
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
      get pending() { return mode === 'gl' && ((kind === 'scene' ? sceneDirty : srcDirty) || flatWait) && !isStatic(); },   /* a capped backdrop refresh is waiting: call render() again next frame */
      get info() { return { mode: mode, reason: reason, width: W, height: H, dpr: D, origin: [OX, OY], level: level, source: kind, lens: LV.lens ? opt.lens : 'off', blur: opt.blur, levels: plan(), rate: capOf(kind === 'copy'), copyRate: capOf(true), sceneRects: scene ? scene.n : 0, isStatic: isStatic(), reduceTransparency: reduceT(), increaseContrast: moreC(), regions: regs ? regs.length : 0, panels: panels.size, flats: flats.size }; },

      addPanel: function (d) {
        var p = panels.get(d.id);
        if (!p) { p = { id: d.id, x: 0, y: 0, w: 0, h: 0, radius: 0, kind: 'window', K: kinds.window, z: 0, seq: seq++, visible: true, opacity: 1, over: 'backdrop' }; panels.set(d.id, p); }
        setP(p, d); sortOrder(); panelsDirty = regDirty = true; return api;
      },
      updatePanel: function (id, d) {
        if (id && typeof id === 'object') { d = id; id = d.id; }
        var p = panels.get(id); if (!p) return false;
        if (setP(p, d || {})) panelsDirty = regDirty = true; return true;
      },
      removePanel: function (id) { if (panels.delete(id)) { sortOrder(); panelsDirty = regDirty = true; return true; } return false; },
      hasPanel: function (id) { return panels.has(id); },

      /* THE BACKDROP, DRAWN ON THE GPU. Everything is optional; what is left out keeps its value.
         lanes: [{y, h, color}]                       track lane backgrounds (y in scene px, scrolls with scrollY; full width)
         clips: [{x, y, w, h, color, titleH, selected}]  x and w in scene units (for example beats), y and h in px; body = colour at bodyAlpha, title band = full colour
         playheadX (scene units, null = none), scrollX (scene units), scrollY (px), zoom (px per scene unit), zoomY (1),
         rect [x,y,w,h] = where the arrangement shows on the engine canvas in CSS px (or viewW, viewH; default the whole canvas),
         originX, originY = where scene x = scrollX and y = scrollY land inside rect (0, 0), bg, titleH (14), bodyAlpha (0.533), selColor, playheadColor, playheadW (1).
         Passing lanes or clips sends the rectangle list to the GPU again; everything else is a uniform (bg is the clear colour). */
      setScene: function (d) {
        if (!d) { scene = null; kind = src ? 'copy' : 'none'; geomDirty = sceneDirty = false; pyrDirty = bDirty = panelsDirty = true; return api; }
        var first = !scene, k;
        if (first) scene = { n: 0, buf: null, f32: null, u8: null, lanes: [], clips: [], rect: null, originX: 0, originY: 0, scrollX: 0, scrollY: 0, zoom: 1, zoomY: 1, playheadX: null, playheadW: 1, playheadColor: [0.243, 0.812, 0.557], bg: null, titleH: 14, bodyAlpha: 0.533, selColor: [1, 1, 1, 0.25] };
        var geo = first || 'lanes' in d || 'clips' in d;
        for (k in { titleH: 1, bodyAlpha: 1, selColor: 1, playheadColor: 1, playheadW: 1 }) if (k in d && d[k] !== scene[k]) { scene[k] = d[k]; geo = true; }
        if ('bg' in d && d.bg !== scene.bg) { scene.bg = d.bg; sceneDirty = true; }
        if ('lanes' in d) scene.lanes = d.lanes || []; if ('clips' in d) scene.clips = d.clips || [];
        if (geo) listScene();
        api.setView(d); if ('playheadX' in d) api.setPlayhead(d.playheadX);
        if (kind !== 'scene') { kind = 'scene'; sceneDirty = panelsDirty = true; lastScene = -1e9; }
        return api;
      },
      /* scroll and zoom: uniforms only, the rectangles stay on the GPU */
      setView: function (d) {
        if (!scene || !d) return api;
        var ch = false, r, o, k;
        for (k in { scrollX: 1, scrollY: 1, zoom: 1, zoomY: 1, originX: 1, originY: 1 }) if (d[k] != null && +d[k] !== scene[k]) { scene[k] = +d[k]; ch = true; }
        if ('rect' in d || d.viewW != null) {
          r = d.rect ? rectOf(d.rect) : d.viewW != null ? { x: 0, y: 0, w: +d.viewW, h: +d.viewH } : null; o = scene.rect;
          if (!r !== !o || (r && (r.x !== o.x || r.y !== o.y || r.w !== o.w || r.h !== o.h))) { scene.rect = r; ch = true; }
        }
        if (ch) sceneDirty = true;
        return api;
      },
      /* the playhead: one rectangle, placed by one uniform. x in scene units, null hides it */
      setPlayhead: function (x) {
        if (!scene) return api;
        x = x == null ? null : +x;
        if (x !== scene.playheadX) { scene.playheadX = x; sceneDirty = true; }
        return api;
      },

      /* THE SMALL-COPY ROUTE: a canvas as the backdrop (fallback, and for glass over a piano roll or a display). It is reduced to a quarter of its size on screen
         before it is uploaded, only after markDirty(), at most copyRate times per second. rect = where it sits on the engine canvas in CSS px (default: it covers the canvas).
         The last of setScene and setBackdrop decides the source; setBackdrop(null) goes back to the scene. */
      setBackdrop: function (source, d) {
        src = source || null; srcRect = d && d.rect ? rectOf(d.rect) : null; srcDirty = !!src; srcReady = false; lastUp = -1e9;
        kind = src ? 'copy' : scene ? 'scene' : 'none'; if (kind === 'scene') { sceneDirty = true; lastScene = -1e9; }
        pyrDirty = bDirty = panelsDirty = true; return api;
      },
      markDirty: function () { if (src) srcDirty = true; },

      /* flat pictures over the backdrop, seen only by panels with over:'flats' (glass that floats over DOM). color = [r,g,b,a] 0..1, or source = a canvas */
      setFlat: function (id, d) {
        var f = flats.get(id), r; if (!f) { f = { id: id, x: 0, y: 0, w: 0, h: 0, radius: 0, color: null, source: null, tex: null, q: null, qx: null, ok: false, dirty: false, hidden: false }; flats.set(id, f); }
        if (d.rect) { r = rectOf(d.rect); f.x = r.x; f.y = r.y; f.w = r.w; f.h = r.h; }
        if (d.radius != null) f.radius = +d.radius; if (d.color) f.color = d.color; if ('hidden' in d) f.hidden = !!d.hidden;
        if ('source' in d) { f.source = d.source || null; f.dirty = !!f.source; if (!f.source) f.ok = false; }
        bDirty = true; return api;
      },
      markFlatDirty: function (id) { var f = flats.get(id); if (f && f.source) f.dirty = true; },
      removeFlat: function (id) { var f = flats.get(id); if (!f) return false; if (f.tex && gl) gl.deleteTexture(f.tex); flats.delete(id); bDirty = panelsDirty = true; return true; },

      setLensPreset: function (n) { if (!(n in LENS) || n === opt.lens) return; opt.lens = n; panelsDirty = true; },
      setBlurPreset: function (n) { if (!(n in BLUR) || n === opt.blur) return; opt.blur = n; if (mode === 'gl') dropPyr(); },
      /* 'glass': lens, quarter-size backdrop, refreshed on every change. 'light': the same engine with the lens off, a backdrop half that size, refreshed 30 times per second.
         'solid': no glass, plain tint with noise (also what Reduce Transparency and a missing WebGL2 give). */
      setLevel: function (n) { if (!(n in LEVELS) || n === level) return api; level = n; LV = LEVELS[n]; if (mode === 'gl') dropPyr(); srcDirty = !!src; sceneDirty = !!scene; lastScene = lastUp = -1e9; panelsDirty = true; return api; },
      /* older name: 3 and 2 = glass, 1 = light, 0 = solid */
      setQuality: function (q) { if (q in QCOMPAT) api.setLevel(QCOMPAT[q]); },
      /* true / false to force, null to follow the system setting */
      setAccessibility: function (d) { if ('reduceTransparency' in d) acc.rt = d.reduceTransparency; if ('increaseContrast' in d) acc.ic = d.increaseContrast; panelsDirty = regDirty = true; },
      setFace: function (d) { for (var k in d) opt.face[k] = d[k]; panelsDirty = true; },
      /* A SMALL CANVAS (2.1). By default the canvas starts at the top left of the space all rectangles are given in (panels, scene rect, backdrop rect, flats).
         A canvas that is only as large as the glass it draws (a floating window plus 34 px for its shadow) sits somewhere inside that space: say where its
         top left corner is, in CSS px (whole device pixels), and keep giving every rectangle in the same space as before. Moving the canvas with its window is
         then: move it with CSS, call setOrigin(x, y), render(). The size stays, so nothing is allocated again. All work shrinks with the canvas. */
      setOrigin: function (x, y) { x = +x || 0; y = +y || 0; if (x === OX && y === OY) return api; OX = x; OY = y; pyrDirty = bDirty = panelsDirty = regDirty = true; return api; },
      /* the backdrop is drawn again at most n times per second (panels still move on every frame). 0 or null = the level decides (Glass: on every change). */
      setBackdropRate: function (n) { userRate = n > 0 ? +n : null; return api; },

      /* call when the canvas changed size (done automatically with a ResizeObserver unless autoResize:false) */
      resize: function (cw, ch, dpr) {
        var d = dpr || opt.dpr || Math.min(opt.maxDpr, root.devicePixelRatio || 1), w, h;
        cw = cw || canvas.clientWidth; ch = ch || canvas.clientHeight; if (!cw || !ch) return false;
        w = Math.round(cw * d); h = Math.round(ch * d);
        if (w === W && h === H && d === D) return false;
        W = w; H = h; D = d;
        if (mode === 'gl') { canvas.width = W; canvas.height = H; dropPyr(); }
        panelsDirty = regDirty = true; return true;
      },

      /* draws only what changed. Returns true when the canvas was redrawn. now = the frame time (performance.now() if left out). */
      render: function (now) {
        if (destroyed) return false;
        stats.renders++;
        if (!W) api.resize();
        if (mode !== 'gl') { if (mode === 'fallback' && panelsDirty && W) { draw2d(); panelsDirty = false; return true; } stats.skipped++; return false; }
        if (gl.isContextLost()) { stats.skipped++; return false; }
        var rebuilt = false, any = false, needA = false, needB = false, ready = false, i, p, rate, rk;
        for (i = 0; i < order.length; i++) { p = order[i]; if (p.visible && p.opacity > 0) { any = true; if (p.over === 'flats' && flats.size) needB = true; else needA = true; } }
        if (any && !isStatic()) {
          if (now == null) now = performance.now();
          if (kind === 'scene') {
            /* the rectangles go to the GPU only when the app passed new ones; the backdrop is drawn again only when something in it changed */
            if (geomDirty) sendScene();
            rate = capOf(false);
            if (sceneDirty && (!rate || now - lastScene >= 1000 / rate - 2)) { if (dbg.freeze && (pyrA || pyrB)) panelsDirty = true; else pyrDirty = bDirty = true; sceneDirty = false; lastScene = now; }
            ready = true;
          } else {
            rate = capOf(true);
            if (srcDirty && (!srcReady || !rate || now - lastUp >= 1000 / rate - 2)) {
              if (upload(srcH, src, srcRect ? srcRect.w : W / D, srcRect ? srcRect.h : H / D)) { srcReady = true; stats.uploads++; pyrDirty = bDirty = true; lastUp = now; }
              srcDirty = false;
            }
            ready = srcReady;
          }
          if (ready) {
            /* the area under glass is worked out again only after a panel, the size or the blur changed, not on every frame */
            if (regDirty) { regs = regions(); rk = regs ? regs.join(';') : 'all'; regDirty = false; if (rk !== regKey) { regKey = rk; pyrDirty = true; } }
            if (needA && (pyrDirty || !pyrA)) { if (!pyrA) pyrA = makePyr(); build(pyrA, false); pyrDirty = false; rebuilt = true; }
            if (needB) {
              /* fed canvases (device displays) go the small-copy route with the same cap */
              rate = capOf(true);
              var fdue = !rate || now - lastFlat >= 1000 / rate - 2, fup = false; flatWait = false;
              flats.forEach(function (f) { if (f.source && f.dirty) { if (fdue || !f.tex) { f.ok = !!upload(f, f.source, f.w, f.h); f.dirty = false; stats.flatUploads++; bDirty = fup = true; } else flatWait = true; } });
              if (fup) lastFlat = now;
              if (bDirty || !pyrB) { if (!pyrB) pyrB = makePyr(); build(pyrB, true); bDirty = false; rebuilt = true; }
            }
          }
        }
        if (!panelsDirty && !rebuilt) { stats.skipped++; return false; }
        drawPanels(); panelsDirty = false; return true;
      },

      /* for tests and the bench page. set({aa:false}) = rectangles with hard edges; set({freeze:true}) = a change of the backdrop redraws the faces but not the backdrop */
      debug: {
        set: function (d) { for (var k in d) if (k in dbg) dbg[k] = !!d[k]; if (scene) sceneDirty = true; return dbg; },
        upload: function () { if (mode === 'gl' && src) upload(srcH, src, srcRect ? srcRect.w : W / D, srcRect ? srcRect.h : H / D); },
        send: function () { if (mode === 'gl' && scene) sendScene(); },
        rebuild: function () { if (mode === 'gl' && (kind === 'scene' || srcReady)) { if (pyrA) build(pyrA, false); if (pyrB) build(pyrB, true); } },
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
        if (gl && !gl.isContextLost()) { freePyr(pyrA); freePyr(pyrB); if (srcH.tex) gl.deleteTexture(srcH.tex); if (sBuf) gl.deleteBuffer(sBuf); flats.forEach(function (f) { if (f.tex) gl.deleteTexture(f.tex); });
          /* give the context back at once (browsers allow only a handful per page) */
          var le = gl.getExtension('WEBGL_lose_context'); if (le) le.loseContext(); }
        panels.clear(); flats.clear(); order = []; src = null; scene = null; kind = 'none';
      }
    };

    start();
    if (mRT && mRT.addEventListener) mRT.addEventListener('change', onMq);
    if (mIC && mIC.addEventListener) mIC.addEventListener('change', onMq);
    var ro = null, loseExt = null;
    if (opt.autoResize && root.ResizeObserver) { ro = new ResizeObserver(function () { if (api.resize()) ask(); }); ro.observe(canvas); }
    api.resize();
    if (o.level != null) api.setLevel(o.level); else if (o.quality != null) api.setQuality(o.quality);
    return api;
  }

  root.AudioLabGlass = { create: create, version: VERSION, LENS: LENS, BLUR: BLUR, KINDS: KINDS, LEVELS: LEVELS };
})(typeof window !== 'undefined' ? window : this);
