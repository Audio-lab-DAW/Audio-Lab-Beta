#!/usr/bin/env python3
"""Task MG1: puts the native-app window (tools/migrate-tests/mg1_page.js) into index.html, at the end of the app's main script block
(the code needs the block's const/let: UI, PJ, S, BUFS, packProject), and sets VERSION.
  python3 tools/migrate-tests/mg1_page_edit.py 0.262
Anchors are asserted unique; refuses a second run."""
import sys, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
p = os.path.join(ROOT, 'index.html'); s = open(p, encoding='utf-8').read()
if 'task MG1 (the path to the native app' in s: sys.exit('index.html: already has task MG1')
code = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mg1_page.js'), encoding='utf-8').read().rstrip('\n')
# the main block ends just before the small block that moves the undo buttons
A = "\n}\n\n{const u=document.querySelector('#bUndo')"
assert s.count(A) == 1, ('anchor', s.count(A))
s = s.replace(A, '\n' + code + '\n' + A)
if len(sys.argv) > 1:
    v = sys.argv[1]; assert re.fullmatch(r'\d+\.\d{3}', v)
    B = re.search(r"const VERSION='([\d.]+)'", s); assert B and s.count("const VERSION='") == 1
    assert tuple(map(int, v.split('.'))) > tuple(map(int, B.group(1).split('.'))), ('version must grow', B.group(1), v)
    s = s.replace("const VERSION='%s'" % B.group(1), "const VERSION='%s'" % v)
open(p, 'w', encoding='utf-8').write(s); print('index.html: task MG1 window added' + (', VERSION ' + sys.argv[1] if len(sys.argv) > 1 else ''))
