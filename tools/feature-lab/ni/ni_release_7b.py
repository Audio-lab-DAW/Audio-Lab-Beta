"""Lane D release of NI-31 (X18 high-pass hints) and NI-7b (X23 gain staging check), one version.
Run on a fresh origin/main checkout once desktop/release-freeze.json is gone (CLAUDE.md, release channel):
  python3 tools/feature-lab/ni/ni_release_7b.py
Applies ni_31.py then ni_7b.py, sets VERSION to the highest on main + 0.001, syncs the desktop copy (never app-version.json), writes the
docs of both steps with one update-notes line. Then: lint, taskNI_31, taskNI_7b, taskXT_DL1/DL2, the smoke test, commit, push."""
import subprocess, re, os
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')); os.chdir(R)
def sh(*a): print('$', ' '.join(a)); subprocess.run(a, check=True)
sh('python3', 'tools/feature-lab/ni/ni_31.py', 'index.html')
sh('python3', 'tools/feature-lab/ni/ni_7b.py', 'index.html')
s = open('index.html', encoding='utf-8').read()
m = re.search(r"const VERSION='(\d+\.\d+)',BUILD='([^']*)'", s); V = '%.3f' % (float(m.group(1)) + 0.001)
s = s.replace(m.group(0), "const VERSION='%s',BUILD='%s'" % (V, m.group(2)), 1); open('index.html', 'w', encoding='utf-8').write(s)
sh('node', 'desktop/scripts/sync-app.js')
sh('python3', 'tools/feature-lab/ni/ni_31_docs.py', V)
sh('python3', 'tools/feature-lab/ni/ni_7b_docs.py', V)
u = open('desktop/update-notes.txt', encoding='utf-8').read().rstrip('\n').split('\n')
u = [l for l in u if not l.startswith('High-pass hints (v') and not l.startswith('Gain staging (v')]
u.append('High-pass hints and gain staging (v%s): right-click the logo for High-pass hints… (low end a track does not need, with a one-click gentle cut) and Gain staging… (tracks too hot into their devices or too quiet, and the master\'s headroom).' % V)
open('desktop/update-notes.txt', 'w', encoding='utf-8').write('\n'.join(u) + '\n')
print('ready: v' + V)
