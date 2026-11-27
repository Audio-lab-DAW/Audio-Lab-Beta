#!/usr/bin/env python3
"""Task GS4: glass engine 2.4.0, a per-panel lens strength along each axis (lensX, lensY; 1 = as before).
Applied to tools/glass-lab/glass-engine.js and to the same engine text inside index.html. Every replacement is asserted unique.
   python3 tools/edits/taskGS4_engine.py [index.html] [tools/glass-lab/glass-engine.js]"""
import sys
FILES = sys.argv[1:] or ['index.html', 'tools/glass-lab/glass-engine.js']
REPL = [
  ("  var VERSION = '2.3.0';", "  var VERSION = '2.4.0';"),
  ("uniform float rad,band,amt,dpr,sq,lr;in vec2 p;out vec4 o;", "uniform float rad,band,amt,dpr,sq,lr;uniform vec2 lk;in vec2 p;out vec4 o;"),
  ("'vec2 sp=p-dv*amt;c=texture(", "'vec2 sp=p-dv*amt*lk;c=texture("),
  ("        if (u.lr) gl.uniform1f(u.lr, lensR(p, band) * D);\n",
   "        if (u.lr) gl.uniform1f(u.lr, lensR(p, band) * D);\n"
   "        /* 2.4: the lens strength of this panel along each axis (lensX bends at the left and right edges, lensY at the top and bottom); 1 = as before */\n"
   "        if (u.lk) gl.uniform2f(u.lk, p.lensX != null ? +p.lensX : 1, p.lensY != null ? +p.lensY : 1);\n"),
  ("['radius', 'opacity', 'visible', 'over', 'tint', 'solid', 'tintAmount', 'shadow', 'lens', 'edges', 'corners'].forEach",
   "['radius', 'opacity', 'visible', 'over', 'tint', 'solid', 'tintAmount', 'shadow', 'lens', 'edges', 'corners', 'lensX', 'lensY'].forEach"),
  ("        return { edges: (m & 1 ? 't' : '') + (m & 2 ? 'r' : '') + (m & 4 ? 'b' : '') + (m & 8 ? 'l' : ''), square: !!p.sq, band: bd,\n          lensRadius: opt.corners === 'outline' ? lensR(p, bd) : p.sq ? 0 : Math.min(Math.max(Math.min(p.radius, h), bd), h) };",
   "        var info = { edges: (m & 1 ? 't' : '') + (m & 2 ? 'r' : '') + (m & 4 ? 'b' : '') + (m & 8 ? 'l' : ''), square: !!p.sq, band: bd,\n          lensRadius: opt.corners === 'outline' ? lensR(p, bd) : p.sq ? 0 : Math.min(Math.max(Math.min(p.radius, h), bd), h) };\n"
   "        /* 2.4: lensX and lensY only when the panel was given its own (otherwise 1) */\n"
   "        if (p.lensX != null) info.lensX = +p.lensX; if (p.lensY != null) info.lensY = +p.lensY; return info;"),
]
for f in FILES:
    s = open(f, encoding='utf-8').read()
    if "uniform vec2 lk;" in s:
        print(f, 'already has engine 2.4.0'); continue
    for a, b in REPL:
        n = s.count(a); assert n == 1, (f, a[:60], n); s = s.replace(a, b)
    open(f, 'w', encoding='utf-8').write(s); print(f, 'engine 2.4.0')
