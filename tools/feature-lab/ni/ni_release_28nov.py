"""Lane D release of 28 Nov: the Fractals export flake fix (ni_sideb0.py), NI-5c (ni_5c.py) and NI-9 (ni_9.py), one version.
Run on a fresh origin/main checkout once desktop/release-freeze.json is gone:
  python3 tools/feature-lab/ni/ni_release_28nov.py
Applies both edit scripts, sets VERSION to the highest on main + 0.001, syncs the desktop copy (never app-version.json), writes the docs.
Then run the tests, the lint and the smoke test, commit and push (see the end of docs/ideas-build.md's NI-5c row)."""
import subprocess, re, os, sys
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')); os.chdir(R)
def sh(*a): print('$', ' '.join(a)); subprocess.run(a, check=True)
sh('python3', 'tools/feature-lab/ni/ni_sideb0.py', 'index.html')
sh('python3', 'tools/feature-lab/ni/ni_5c.py', 'index.html')
sh('python3', 'tools/feature-lab/ni/ni_9.py', 'index.html')
s = open('index.html', encoding='utf-8').read()
m = re.search(r"const VERSION='(\d+)\.(\d+)',BUILD='[^']*'", s); old = m.group(1) + '.' + m.group(2)
V = '%.3f' % (float(old) + 0.001)
s = s.replace(m.group(0), "const VERSION='%s',BUILD='28 November 2026'" % V, 1); open('index.html', 'w', encoding='utf-8').write(s)
print('VERSION', old, '->', V)
sh('node', 'desktop/scripts/sync-app.js')
sh('python3', 'tools/feature-lab/ni/ni_5c_docs.py', V)
sh('python3', 'tools/feature-lab/ni/ni_9_docs.py', V)
b = open('docs/backlog-log.md', encoding='utf-8').read()
if 'the Fractals export flake found and fixed' not in b:
    lg = open('tools/feature-lab/ni/ni_sideb0_log.md', encoding='utf-8').read().replace('{V}', V)
    open('docs/backlog-log.md', 'w', encoding='utf-8').write(b.rstrip('\n') + '\n\n' + lg.rstrip('\n') + '\n')
# update notes: one line for this release (CLAUDE.md), replacing the line ni_5c_docs.py wrote
u = open('desktop/update-notes.txt', encoding='utf-8').read().rstrip('\n').split('\n')
u = [l for l in u if not l.startswith('Clashes that take turns (v') and not l.startswith('Export fix (v') and not l.startswith('Harmonic ruler (v')]
u.append('Harmonic ruler (v%s): every spectrum view names its five strongest notes with cents (amber outside the key, red when a pitch keeps ringing); clashes that take turns in the beat get a thin dashed cable; long exports with the Sidechain effect pump on the right beat.' % V)
open('desktop/update-notes.txt', 'w', encoding='utf-8').write('\n'.join(u) + '\n')
p = open('docs/ideas-build.md', encoding='utf-8').read()
A = '| NI-6 | **I6 energy arc.**'
row = '| NI-fx1 | **The Fractals export flake** (asked by the scheduling chat for task RG, 28 Nov): `SIDE_B0` set again after `renderMix`\'s await, so a render running alongside cannot move the Sidechain pump\'s beat. | lane K\'s `renderMix` (one statement) | `taskNI_sideb0.py` (the race forced three ways); `export_same.py` 20 of 20 identical | **done v%s** |\n' % V
if '| NI-fx1 |' not in p:
    assert p.count(A) == 1; p = p.replace(A, row + A); open('docs/ideas-build.md', 'w', encoding='utf-8').write(p)
print('ready: v' + V)
