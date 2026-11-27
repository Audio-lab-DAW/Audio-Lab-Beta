#!/usr/bin/env python3
"""Task GS4 (glass step 4): floating device panel and transport, lens on the transport, the bottom-left corner on engine glass.
   python3 tools/edits/taskGS4.py index.html 0.231   (the version: the highest on main + 0.001)
Engine 2.4.0 (lensY) comes from tools/edits/taskGS4_engine.py, run first. Every replacement is asserted unique; running it twice changes nothing."""
import sys, os
F = sys.argv[1]; VER = sys.argv[2]
D = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if '(task GS4, glass step 4)' in s:
    print('already applied'); sys.exit(0)
assert 'uniform vec2 lk;' in s, 'run taskGS4_engine.py first'
BLOCK = open(os.path.join(D, 'taskGS4_block.js'), encoding='utf-8').read().replace('@VER@', VER)
CSS = open(os.path.join(D, 'taskGS4_css.txt'), encoding='utf-8').read().replace('@VER@', VER)
import re
old = re.findall(r"VERSION='(\d+\.\d+)'", s); assert len(old) == 1, old
assert tuple(map(int, VER.split('.'))) > tuple(map(int, old[0].split('.'))), (old, VER)
def rep(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
rep('function askChoice(title,text,btns,icon){', BLOCK.rstrip('\n') + '\nfunction askChoice(title,text,btns,icon){')
rep('.dacv{display:flex;', CSS.rstrip('\n') + '\n.dacv{display:flex;')
# windows and menus over the floating panels see them with their rounded corners
rep('glfFlat(L,f.k,{rect:f.R,radius:0,color:f.c},f.s,seen);', "glfFlat(L,f.k,{rect:f.R,radius:(f.k==='d:tr'||f.k==='d:fxglass')?gs4Rad(f.k.slice(2)):0,color:f.c},f.s,seen);")
# the faces are no longer 1 px larger than their elements: that was so no seam showed where the arrangement canvas was cut away; with the engine's canvas
# above the arrangement the extra pixel would show
rep("const R=[r2((x0-m.left)/z)-1,r2((y0-m.top)/z)-1,r2((x1-x0)/z)+2,r2((y1-y0)/z)+2],E=gleEdges(id,R[1]+1,R[3]-2);", "const R=[r2((x0-m.left)/z),r2((y0-m.top)/z),r2((x1-x0)/z),r2((y1-y0)/z)],E=gleEdges(id,R[1],R[3]);")
rep("R=[x-1,HGR.t-1,HDRW+2,HGR.b-HGR.t+2];", "R=[x,HGR.t,HDRW,HGR.b-HGR.t];")
rep("VERSION='%s'" % old[0], "VERSION='%s'" % VER)
open(F, 'w', encoding='utf-8').write(s); print('task GS4 applied to', F, 'version', VER)
