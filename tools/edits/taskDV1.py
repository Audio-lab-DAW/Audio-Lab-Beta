#!/usr/bin/env python3
"""Task DV-1 (display-first devices, the shared frame): python3 tools/edits/taskDV1.py index.html 0.262
New JS before askChoice, new CSS before .dacv; every replacement asserted unique; running it twice changes nothing."""
import sys, os, re
F = sys.argv[1]; VER = sys.argv[2]
D = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if '(task DV-1)' in s:
    print('already applied'); sys.exit(0)
BLOCK = open(os.path.join(D, 'taskDV1_block.js'), encoding='utf-8').read().replace('v0.262', 'v' + VER)
CSS = open(os.path.join(D, 'taskDV1_css.txt'), encoding='utf-8').read().replace('v0.262', 'v' + VER)
old = re.findall(r"VERSION='(\d+\.\d+)'", s); assert len(old) == 1, old
assert tuple(map(int, VER.split('.'))) > tuple(map(int, old[0].split('.'))), (old, VER)
def rep(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
rep('function askChoice(title,text,btns,icon){', BLOCK.rstrip('\n') + '\nfunction askChoice(title,text,btns,icon){')
rep('.dacv{display:flex;', CSS.rstrip('\n') + '\n.dacv{display:flex;')
rep("VERSION='%s'" % old[0], "VERSION='%s'" % VER)
open(F, 'w', encoding='utf-8').write(s); print('task DV-1 applied to', F, 'version', VER)
