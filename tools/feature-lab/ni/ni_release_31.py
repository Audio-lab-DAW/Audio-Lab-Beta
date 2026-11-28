"""Lane D release of NI-31 (X18 high-pass hints). Run on a fresh origin/main checkout once desktop/release-freeze.json is gone:
  python3 tools/feature-lab/ni/ni_release_31.py
Applies ni_31.py, sets VERSION to the highest on main + 0.001, syncs the desktop copy (never app-version.json), writes the docs
(backlog entry, update note, Where it stands, commands list, the plan row). Then: lint, taskNI_31, taskXT_DL1/DL2, smoke test, commit, push."""
import subprocess, re, os
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')); os.chdir(R)
def sh(*a): print('$', ' '.join(a)); subprocess.run(a, check=True)
sh('python3', 'tools/feature-lab/ni/ni_31.py', 'index.html')
s = open('index.html', encoding='utf-8').read()
m = re.search(r"const VERSION='(\d+\.\d+)',BUILD='[^']*'", s); V = '%.3f' % (float(m.group(1)) + 0.001)
s = s.replace(m.group(0), "const VERSION='%s',BUILD='%s'" % (V, m.group(0).split("BUILD='")[1].rstrip("'")), 1); open('index.html', 'w', encoding='utf-8').write(s)
sh('node', 'desktop/scripts/sync-app.js')
sh('python3', 'tools/feature-lab/ni/ni_31_docs.py', V)
print('ready: v' + V)
