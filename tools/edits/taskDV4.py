#!/usr/bin/env python3
"""Task DV-4 (display-first devices, step 4: the bottom dock, the values line clear of the handles, On the picture for the Compressor, Sidechain, Echo delay, Space reverb): python3 tools/edits/taskDV4.py index.html 0.296
Needs DV-3 applied first (on main once DV-3 is released). New JS before askChoice, new CSS before .dacv; one small asserted change inside lane I's own
DV-1 block (the values line leaves out what the picture already writes). Every replacement asserted unique; running it twice changes nothing."""
import sys, os, re
F = sys.argv[1]; VER = sys.argv[2]
D = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if '(task DV-4)' in s:
    print('already applied'); sys.exit(0)
assert '(task DV-3)' in s, 'DV-3 first'
BLOCK = open(os.path.join(D, 'taskDV4_block.js'), encoding='utf-8').read().replace('v0.296', 'v' + VER)
CSS = open(os.path.join(D, 'taskDV4_css.txt'), encoding='utf-8').read().replace('v0.296', 'v' + VER)
old = re.findall(r"VERSION='(\d+\.\d+)'", s); assert len(old) == 1, old
assert tuple(map(int, VER.split('.'))) > tuple(map(int, old[0].split('.'))), (old, VER)
def rep(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
# DV-1's values line leaves out what the picture already writes in words (DVTXT skip; the four DV-4 devices)
rep("if(!C||!C.label||!C.spec||typeof C.spec.f!=='function')continue;let v;", "if(!C||!C.label||!C.spec||typeof C.spec.f!=='function')continue;if(dvSkip(B,String(C.label)))continue;let v;")
rep('function askChoice(title,text,btns,icon){', BLOCK.rstrip('\n') + '\nfunction askChoice(title,text,btns,icon){')
rep('.dacv{display:flex;', CSS.rstrip('\n') + '\n.dacv{display:flex;')
rep("VERSION='%s'" % old[0], "VERSION='%s'" % VER)
open(F, 'w', encoding='utf-8').write(s); print('task DV-4 applied to', F, 'version', VER)
