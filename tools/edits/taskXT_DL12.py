"""Task XT-DL12: the script sandbox spike. Inserts tools/edits/taskXT_DL12_block.js before askChoice and bumps VERSION.
  python3 tools/edits/taskXT_DL12.py [index.html]"""
import sys, os, re
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
blk = open(os.path.join(os.path.dirname(__file__), 'taskXT_DL12_block.js'), encoding='utf-8').read()
assert 'task XT-DL12' not in s, 'already applied'
A = 'function askChoice(title,text,btns,icon){'
assert s.count(A) == 1
assert 'task XT-DL2' in s, 'DL2 first'
for n in ('XT_SBX', 'xtSandboxRun', 'xtSandboxStop'):
    assert n not in s, n + ' exists already'
m = re.findall(r"const VERSION='(\d+)\.(\d+)'", s); assert len(m) == 1
v = '%s.%03d' % (m[0][0], int(m[0][1]) + 1)
s = s.replace(A, blk.replace('(v0.000, task XT-DL12)', '(v%s, task XT-DL12)' % v) + A)
s = re.sub(r"const VERSION='\d+\.\d+'", "const VERSION='%s'" % v, s)
open(P, 'w', encoding='utf-8').write(s); print('ok', v)
