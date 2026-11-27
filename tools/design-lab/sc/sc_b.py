#!/usr/bin/env python3
"""Task SC-B: About as the random set Y1 (Earth 3 in 5, orbit corner 1 in 5, field arcs 1 in 5). python3 tools/design-lab/sc/sc_b.py index.html [version]
Every anchor is asserted unique. Re-run on a fresh file after a rebase."""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
V = sys.argv[2] if len(sys.argv) > 2 else '0.2xx'
D = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
assert 'task SC-B, lane G' not in s, 'already applied'
assert 'task SC-A, lane G' in s, 'needs SC-A'
def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:140])
    s = s.replace(old, new)
rep('function askChoice(title,text,btns,icon){', open(os.path.join(D, 'sc_b_block.js'), encoding='utf-8').read().replace('v0.2xx', 'v' + V) + 'function askChoice(title,text,btns,icon){')
# AB1: the two new kinds (force and counters), the Y1 pick, and scene() hands them to sciAboutDraw
rep("const AB1=(()=>{const TAU=Math.PI*2,D=Math.PI/180,ATOM=116,KINDS=['corner','sheet'];", "const AB1=(()=>{const TAU=Math.PI*2,D=Math.PI/180,ATOM=116,KINDS=['corner','sheet','orbit','arcs'];/* orbit, arcs: task SC-B */")
rep("const n={bg:0,atom:0,open:0,corner:0,sheet:0};let G=null,S=null,force=null;", "const n={bg:0,atom:0,open:0,corner:0,sheet:0,orbit:0,arcs:0};let G=null,S=null,force=null;")
rep("return KINDS.includes(f)?f:KINDS[Math.random()<.5?0:1]}", "return KINDS.includes(f)?f:sciAboutPick()}/* task SC-B: Y1 */")
rep("function scene(c,w,h,t,kind,M){const g=prep(),p=KIND[kind],", "function scene(c,w,h,t,kind,M){if(!KIND[kind]){sciAboutDraw(c,w,h,t,kind,M);return}const g=prep(),p=KIND[kind],")
open(F, 'w', encoding='utf-8').write(s)
print('task SC-B applied')
