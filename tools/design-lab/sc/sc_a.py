#!/usr/bin/env python3
"""Task SC-A: the science look's shared drawing module (SCI), its one timer and the Science drawings setting. python3 tools/design-lab/sc/sc_a.py index.html
Every anchor is asserted unique. Re-run on a fresh file after a rebase."""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
D = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
assert 'task SC-A, lane G' not in s, 'already applied'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:140])
    s = s.replace(old, new)

rep('function askChoice(title,text,btns,icon){', open(os.path.join(D, 'sc_a_block.js'), encoding='utf-8').read() + 'function askChoice(title,text,btns,icon){')
rep('.dacv{display:flex;', open(os.path.join(D, 'sc_a_css.txt'), encoding='utf-8').read() + '.dacv{display:flex;')
open(F, 'w', encoding='utf-8').write(s)
print('task SC-A applied')
