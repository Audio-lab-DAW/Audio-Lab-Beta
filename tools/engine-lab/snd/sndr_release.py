"""Task SND-R (lane L): the release, for this run or the next one after a release freeze (CLAUDE.md).
  python3 tools/engine-lab/snd/sndr_release.py "<gate summary>"
Pulls main, stops if desktop/release-freeze.json is there, takes VERSION = the highest on main + 0.001, runs the edit script on the fresh
index.html, node desktop/scripts/sync-app.js (never app-version.json), the docs script, the lint, and commits (push is done by hand after
the UI test ran on the fresh file)."""
import sys, os, re, subprocess, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
sh = lambda *a: subprocess.run(a, cwd=ROOT, check=True, capture_output=True, text=True).stdout
sh('git', 'checkout', '--', 'index.html'); sh('git', 'pull', '-q', '--rebase')
if os.path.exists(os.path.join(ROOT, 'desktop/release-freeze.json')): sys.exit('release freeze on main: wait')
s = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
prev = re.search(r"const VERSION='([0-9.]+)'", s).group(1)
assert '/* ==SNDR-js==' not in s, 'already released'
V = '%.3f' % (float(prev) + 0.001)
sh('python3', 'tools/engine-lab/snd/sndr_edit.py', 'index.html', V)
print(sh('node', 'desktop/scripts/sync-app.js'))
sh('python3', 'tools/engine-lab/snd/sndr_docs.py', V, prev, sys.argv[1] if len(sys.argv) > 1 else 'see the gate log')
print(sh('node', 'tools/release-gate/lint.js', 'index.html'))
st = sh('git', 'status', '--short'); assert 'app-version.json' not in st.replace('app-version-dev.json', ''), st
print('ready', prev, '->', V); print(st)
