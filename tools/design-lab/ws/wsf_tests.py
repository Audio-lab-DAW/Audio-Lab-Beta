"""Task WS-F (lane Q): point every browser test at tools/test-songs/. For each Python file under tools/ that routes
https://app.test/**, the handler argument is wrapped in alsong(...) (tools/test-songs/alsong.py), and an import line that finds
tools/test-songs from the file's own place is added after the file's first top-level import. Idempotent (a file that already
says alsong is left alone). Prints what it changed.   python3 tools/design-lab/ws/wsf_tests.py"""
import os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
PAT = re.compile(r"\.route\((['\"])https://app\.test/\*\*\1\s*,\s*")
SKIP = {os.path.join('tools', 'test-songs', 'alsong.py'), os.path.join('tools', 'design-lab', 'ws', 'wsf_tests.py')}

def close_of(s, i):
    """index of the ')' that closes the call whose arguments start at i (depth 1), skipping strings"""
    d, q, k = 1, None, i
    while k < len(s):
        c = s[k]
        if q:
            if c == '\\': k += 2; continue
            if s.startswith(q, k): k += len(q); q = None; continue
        elif c in '\'"':
            q = s[k:k + 3] if s[k:k + 3] in ('"""', "'''") else c; k += len(q); continue
        elif c == '#':
            k = s.find('\n', k); k = len(s) if k < 0 else k; continue
        elif c in '([{': d += 1
        elif c in ')]}':
            d -= 1
            if d == 0: return k
        k += 1
    raise ValueError('no closing paren')

changed = []
for dp, dn, fn in os.walk(os.path.join(ROOT, 'tools')):
    dn[:] = [d for d in dn if d not in ('node_modules', '__pycache__')]
    for f in fn:
        if not f.endswith('.py'): continue
        p = os.path.join(dp, f); rel = os.path.relpath(p, ROOT)
        if rel in SKIP: continue
        s = open(p, encoding='utf-8').read()
        if 'https://app.test/**' not in s or 'alsong' in s: continue
        out, pos, n = [], 0, 0
        for m in PAT.finditer(s):
            if m.start() < pos: continue
            a = m.end(); b = close_of(s, a)
            arg = s[a:b].rstrip()
            out.append(s[pos:a] + 'alsong(' + arg + ')' + s[a + len(arg):b]); pos = b; n += 1
        if not n: continue
        s2 = ''.join(out) + s[pos:]
        up = os.path.relpath(os.path.join(ROOT, 'tools', 'test-songs'), dp).replace(os.sep, '/')
        imp = "import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), %r)); from alsong import alsong  # task WS-F: the test songs\n" % up
        L = s2.split('\n'); at = None
        for i, l in enumerate(L):
            if re.match(r'(import |from (?!__future__)\S+ import )', l) and not l.rstrip().endswith(('(', '\\', ',')):
                at = i + 1; break
        assert at is not None, rel
        L.insert(at, imp.rstrip('\n'))
        s2 = '\n'.join(L)
        compile(s2, p, 'exec')
        open(p, 'w', encoding='utf-8').write(s2); changed.append((rel, n))
for r, n in sorted(changed): print('%3d  %s' % (n, r))
print(len(changed), 'files')
