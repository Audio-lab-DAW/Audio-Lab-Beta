#!/usr/bin/env python3
"""AudioLab release gate (task HF1). Decides whether the newest build on main may go to installed apps.

  python3 tools/release-gate/gate.py [--ref VERSION] [--promote] [--push] [--quick] [--skip-ui] [--secs 60]

Runs on a fresh checkout of origin/main (a git worktree under tools/release-gate/out/new), never on your working copy:
  a) lint.js: no top-level function name defined twice, no element id written twice
  b) every UI test in tools/ui-tests (each one that fails is run again on the reference build: a test that also fails
     there, with the reference's own copy of the test, is reported as old, not as a regression; a new test must pass)
  c) the start-up smoke test in the real desktop app (smoke_electron.js): 60 s idle with the Fractals song, the mouse moving
     over the whole window, every MIDI scenario: no track or selection change nobody asked for, no synthetic click, no command,
     no console error, no duplicate element id; frame times of the idle app against the reference build
  d) every main window opened and closed without errors; the update window with 40 long lines keeps Update and Later in view
  e) the Fractals song: Kick and Bass levels and checksums unchanged, and every export line of export_same.py bit-identical to
     the reference build, except lines named in audio-changes.json (a release that changed that sound on purpose)
The reference build is the version installed apps get now (desktop/app-version.json on main), or --ref.
All pass and --promote: AL_PROMOTE=1 node desktop/scripts/sync-app.js in the checkout (desktop/app-version.json, the notes
trimmed to the ten newest lines), committed; --push pushes it to main. Anything fails: nothing is promoted.
The result is written to tools/release-gate/out/result.json and printed; exit 0 only when everything passed."""
import sys, os, json, subprocess, shutil, time, re, glob, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'out')
ap = argparse.ArgumentParser()
ap.add_argument('--ref'); ap.add_argument('--promote', action='store_true'); ap.add_argument('--push', action='store_true')
ap.add_argument('--quick', action='store_true', help='smoke scenarios at 20 s, no UI tests (for trying the gate, never promotes)')
ap.add_argument('--skip-ui', action='store_true'); ap.add_argument('--secs', type=int, default=60)
ap.add_argument('--here', action='store_true', help='test the working copy as it is instead of origin/main (never promotes)')
ap.add_argument('--native', help='task MG1: a native block (JSON) to check (every file downloaded: size, sha256, signature) and put into the live manifest with this promotion')
ap.add_argument('--native-only', action='store_true', help='task MG1: only check the --native block and, with --promote, put it into the live manifest; the program version stays')
A = ap.parse_args()
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, 'gate.log'), 'a', encoding='utf-8')
def say(*a):
    m = ' '.join(str(x) for x in a); print(m, flush=True); LOG.write(m + '\n'); LOG.flush()
def sh(cmd, cwd=REPO, timeout=None, env=None, check=False):
    r = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout, env=env)
    if check and r.returncode: raise SystemExit('command failed: %s\n%s%s' % (cmd, r.stdout[-2000:], r.stderr[-2000:]))
    return r
RES = {'started': time.strftime('%Y-%m-%d %H:%M:%S'), 'steps': {}, 'fail': []}
def step(name, ok, detail):
    RES['steps'][name] = {'ok': bool(ok), 'detail': detail}
    say(('PASS ' if ok else 'FAIL ') + name + (': ' + detail if isinstance(detail, str) and detail else ''))
    if not ok: RES['fail'].append(name)

# ---------- the trees: the newest main and the reference (the build installed apps have) ----------
def worktree(path, rev):
    if os.path.isdir(path): sh(['git', 'worktree', 'remove', '--force', path]); shutil.rmtree(path, ignore_errors=True)
    sh(['git', 'worktree', 'prune']); sh(['git', 'worktree', 'add', '--detach', path, rev], check=True)
    return path
sh(['git', 'fetch', '-q', 'origin', 'main'], timeout=300)
if A.here: NEW = REPO
else: NEW = worktree(os.path.join(OUT, 'new'), 'origin/main')
# ---------- task MG1: the native block (the native AudioLab offered to Electron apps, docs/native-migration.md) ----------
NB = os.path.join(HERE, 'native_block.py')
def native_check():
    r = sh(['python3', NB, 'check', os.path.abspath(A.native), '--download'], timeout=3600)
    say(r.stdout.strip()); return r.returncode == 0, (r.stdout.strip().splitlines() or [r.stderr[-300:]])[-1]
if A.native_only:
    if not A.native: raise SystemExit('--native-only needs --native BLOCK.json')
    okn, det = native_check(); step('f native build', okn, det)
    if okn and A.promote and not A.here:
        r = sh(['python3', NB, 'write', os.path.abspath(A.native), os.path.join('desktop', 'app-version.json')], cwd=NEW); say(r.stdout.strip())
        if r.returncode: raise SystemExit('could not write the native block')
        nv = json.load(open(A.native))['version']
        sh(['git', 'add', 'desktop/app-version.json'], cwd=NEW)
        sh(['git', '-c', 'user.name=Audio-lab-DAW', '-c', 'user.email=360039460+Audio-lab-DAW@users.noreply.github.com', 'commit', '-q', '-m', 'release gate: offer the native AudioLab %s to Electron apps (native block checked: every file downloaded, size, sha256%s)' % (nv, ', signature' if os.environ.get('AL_NATIVE_PUBKEY') else '')], cwd=NEW, check=True)
        RES['promotedNative'] = nv
        if A.push:
            for i in range(5):
                if sh(['git', 'pull', '-q', '--rebase', 'origin', 'main'], cwd=NEW).returncode == 0 and sh(['git', 'push', '-q', 'origin', 'HEAD:main'], cwd=NEW).returncode == 0: RES['pushed'] = True; break
                time.sleep(5)
        say('NATIVE %s OFFERED to Electron apps%s' % (nv, ' (pushed)' if RES.get('pushed') else ' (committed in %s, not pushed)' % NEW))
    RES['passed'] = okn; json.dump(RES, open(os.path.join(OUT, 'result.json'), 'w'), indent=1); sys.exit(0 if okn else 1)
VER = re.search(r"const VERSION='([\d.]+)'", open(os.path.join(NEW, 'index.html'), encoding='utf-8').read()).group(1)
live = json.load(open(os.path.join(NEW, 'desktop', 'app-version.json')))
REFV = A.ref or live['version']
lg = sh(['git', 'log', '--format=%H %s', 'origin/main']).stdout.splitlines()
refc = next((l.split()[0] for l in lg if l.split(' ', 1)[1].startswith('v%s:' % REFV)), None)
if not refc: raise SystemExit('no release commit for the reference v%s' % REFV)
REF = worktree(os.path.join(OUT, 'ref'), refc)
RES.update(version=VER, ref=REFV, refCommit=refc[:10], commit=sh(['git', 'rev-parse', 'HEAD'], cwd=NEW).stdout.strip()[:10])
say('release gate: v%s (%s) against the installed build v%s (%s)' % (VER, RES['commit'], REFV, refc[:10]))

# the desktop app for the smoke test: Electron from the working copy's desktop/node_modules (or ELECTRON), the app files of each tree
ELECTRON = os.environ.get('ELECTRON') or ''
if not ELECTRON:
    for d in (os.path.join(NEW, 'desktop'), os.path.join(REPO, 'desktop')):
        r = sh(['node', '-e', "process.stdout.write(require(process.argv[1]))", os.path.join(d, 'node_modules', 'electron')])
        if r.returncode == 0 and r.stdout: ELECTRON = r.stdout; break
if not ELECTRON:
    say('installing Electron for the smoke test'); sh('npm install --no-save electron@45', cwd=os.path.join(NEW, 'desktop'), timeout=900)
    ELECTRON = sh(['node', '-e', "process.stdout.write(require(process.argv[1]))", os.path.join(NEW, 'desktop', 'node_modules', 'electron')]).stdout
for T in (NEW, REF):
    os.makedirs(os.path.join(T, 'desktop', 'app'), exist_ok=True); shutil.copy(os.path.join(T, 'index.html'), os.path.join(T, 'desktop', 'app', 'index.html'))
ENV = dict(os.environ, ELECTRON=ELECTRON)
XV = ['xvfb-run', '-a', '-s', '-screen 0 4000x2200x24']

# ---------- a) lint ----------
r = sh(['node', os.path.join(HERE, 'lint.js'), os.path.join(NEW, 'index.html')])
step('a lint', r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:])
if r.returncode: say(r.stdout)

# ---------- c, d) the start-up smoke test and the windows ----------
SCEN = 'real,none,keyboard,push1,push1-loop,push1-loop-on,iac-push,iac-push-short,loopback,loopback-maps,macnames,mackie-loop,mackie-loop-on,noise'   # every scenario of smoke_electron.js
secs = 20 if A.quick else A.secs
def smoke(tree, scen, secs, extra=(), tag=''):
    js = os.path.join(OUT, 'smoke-%s%s.json' % (os.path.basename(tree), tag))
    r = sh(XV + ['node', os.path.join(HERE, 'smoke_electron.js'), '--desktop', os.path.join(tree, 'desktop'), '--secs', str(secs), '--scen', scen, '--json', js] + list(extra), env=ENV, timeout=3600)
    try: data = json.load(open(js))
    except Exception: data = []
    return r, data
r, data = smoke(NEW, SCEN, secs)
say(r.stdout.strip())
bad = [d['scen'] for d in data if not d.get('clean')]
step('c start-up smoke test (%d scenarios, %d s idle, mouse over the window)' % (len(SCEN.split(',')), secs), len(data) == len(SCEN.split(',')) and not bad,
     'every scenario clean' if not bad and data else 'not clean: ' + ', '.join(bad or ['harness failed: ' + r.stderr[-300:]]))
# frame times: the idle app, new against reference, twice each (the noise of a shared machine)
def frames(tree):
    out = []
    for i in range(2):
        _, d = smoke(tree, 'none', 20, ['--wander', '0'], '-ft%d' % i)
        if d and d[0].get('frames') and d[0]['frames'].get('n'): out.append(d[0]['frames'])
    return out
fn, fr = frames(NEW), frames(REF)
if fn and fr:
    p50n, p50r = min(f['p50'] for f in fn), min(f['p50'] for f in fr); p95n, p95r = min(f['p95'] for f in fn), min(f['p95'] for f in fr)
    ok = p50n <= p50r * 1.25 + 2 and p95n <= p95r * 1.5 + 10
    step('c frame times (idle, Fractals open)', ok, 'p50 %.1f ms (reference %.1f), p95 %.1f ms (reference %.1f)' % (p50n, p50r, p95n, p95r))
else: step('c frame times (idle, Fractals open)', False, 'no frame times measured')
r, data = smoke(NEW, 'none', 10, ['--wander', '0', '--windows', '1'], '-win')
w = data[0].get('wins') if data else None
step('d windows open and close, the update window with long notes', bool(w) and not w['fail'] and data[0].get('clean'),
     (('%d checks ok' % len(w['ok'])) + ('; ' + ' | '.join(w['fail'])[:600] if w['fail'] else '')) if w else 'harness failed: ' + (data[0].get('crash', '') if data else r.stderr[-300:]))

# ---------- e) the Fractals levels and the exports ----------
def export(tree):
    r = sh(['python3', os.path.join(tree, 'tools', 'engine-tests', 'export_same.py'), os.path.join(tree, 'index.html')], cwd=tree, timeout=1800)
    return [l for l in r.stdout.splitlines() if re.match(r'^(Fractals|\S.{0,14}\s+-?[\d.]+ dB)', l)], r
# every build renders twice: a line that differs between two renders of the same build is not repeatable (instruments with
# free-running randomness: Plant, Sampler, Sampler grains, Drum kit move by up to 1 dB from run to run on one build, measured
# 27 Nov 2026), so it cannot be compared; it is listed, not judged. Every repeatable line must be bit-identical to the reference.
en, en2, rn, rn2 = export(NEW), export(NEW), export(REF), export(REF)
allow = {}
try: allow = json.load(open(os.path.join(NEW, 'tools', 'release-gate', 'audio-changes.json')))
except Exception: pass
key = lambda l: re.sub(r'\s+-?[\d.]+ dB.*$', '', l).strip() + ('' if 'master' not in l else ' ' + re.sub(r'^.*\((.*)\)\s*$', r'\1', l))
km = lambda L: {key(l): l for l in L}
n1, n2, r1, r2 = km(en[0]), km(en2[0]), km(rn[0]), km(rn2[0])
unstable = sorted(k for k in set(n1) | set(r1) if n1.get(k) != n2.get(k) or r1.get(k) != r2.get(k))
diff = ['%s: %s -> %s' % (k, r1[k].split(None, 1)[-1].strip(), l.split(None, 1)[-1].strip()) for k, l in n1.items() if k in r1 and r1[k] != l and k not in allow and k not in unstable]
same = [k for k in n1 if k in r1 and k not in unstable]
fx = [l for l in en[0] if l.startswith('Fractals') and 'master put back' not in l]
fixed = any('-19.05560 dB  fb577dd5202b' in l for l in fx) and any('-35.48685 dB  392ec52590c7' in l for l in fx) and not any(k.startswith('Fractals') for k in unstable)
RES['exportUnstable'] = unstable
step('e Fractals levels and exports', bool(en[0]) and fixed and not diff,
     ('Kick -19.05560 dB, Bass -35.48685 dB, same checksums; %d repeatable export lines bit-identical to v%s%s' % (len(same), REFV, '; not repeatable from run to run on either build, so not compared: ' + ', '.join(unstable) if unstable else '')) if bool(en[0]) and fixed and not diff
     else 'changed: ' + ('; '.join(diff) if diff else ' | '.join(fx) or en[1].stderr[-300:]))
if [x for x in en[0] if 'errors' in x]: pass

# ---------- f) task MG1: a native block that goes along with this promotion ----------
if A.native: okn, det = native_check(); step('f native build', okn, det)

# ---------- b) every UI test ----------
HELPERS = {'taskAH_fake.js', 'aivoice_server.js', 'taskAL_synth.js', 'taskD3_census.js', 'taskD3_probe.js'}
try: SKIP = json.load(open(os.path.join(HERE, 'ui-skip.json')))
except Exception: SKIP = {}
def run_test(tree, name, out):
    f = os.path.join(tree, 'tools', 'ui-tests', name); os.makedirs(out, exist_ok=True)
    head = open(f, encoding='utf-8', errors='replace').read(3000)
    first = tree if re.search(r'\[repo dir\]|repo dir', head) else os.path.join(tree, 'index.html')
    if name.endswith('.js'): cmd = XV + ['node', f, os.path.join(tree, 'desktop')]
    else: cmd = ['python3', f, first, out]
    t0 = time.time()
    try: r = sh(cmd, cwd=out, timeout=900, env=ENV); rc, txt = r.returncode, (r.stdout + r.stderr)
    except subprocess.TimeoutExpired: rc, txt = 124, 'timed out after 900 s'
    fl = [l for l in txt.splitlines() if re.search(r'\bFAIL', l)]
    return rc, round(time.time() - t0), fl[:5], txt[-1500:]
if A.quick or A.skip_ui: step('b UI tests', not A.promote, 'not run (--quick or --skip-ui)')
else:
    tests = sorted(n for n in os.listdir(os.path.join(NEW, 'tools', 'ui-tests')) if (n.endswith('.py') or n.endswith('_electron.js')) and n not in HELPERS)
    res, regress, old = {}, [], []
    for n in tests:
        if n in SKIP: res[n] = {'skip': SKIP[n]}; say('     skip %s: %s' % (n, SKIP[n])); continue
        rc, secs_, fl, tail = run_test(NEW, n, os.path.join(OUT, 'ui', n))
        res[n] = {'rc': rc, 's': secs_, 'fail': fl}
        if rc == 0 and not fl: say('     ok   %s (%d s)' % (n, secs_)); continue
        if os.path.exists(os.path.join(REF, 'tools', 'ui-tests', n)):
            rc2, s2, fl2, _ = run_test(REF, n, os.path.join(OUT, 'ui-ref', n)); res[n]['ref'] = {'rc': rc2, 'fail': fl2}
            if rc2 != 0 or fl2: old.append(n); say('     old  %s: fails on v%s too (%s)' % (n, REFV, (fl or [tail.strip().splitlines()[-1] if tail.strip() else 'exit %d' % rc])[0][:160])); continue
        regress.append(n); res[n]['tail'] = tail; say('     FAIL %s (exit %d): %s' % (n, rc, ' | '.join(fl)[:400] or tail[-400:]))
    RES['ui'] = res
    step('b UI tests (%d run, %d skipped)' % (len([x for x in res.values() if 'rc' in x]), len([x for x in res.values() if 'skip' in x])), not regress,
         ('no regression' + ('; %d also fail on v%s: %s' % (len(old), REFV, ', '.join(old)) if old else '')) if not regress else 'regressions: ' + ', '.join(regress))

# ---------- the decision ----------
RES['passed'] = not RES['fail']; RES['finished'] = time.strftime('%Y-%m-%d %H:%M:%S')
say('')
if RES['passed'] and A.promote and not A.quick and not A.skip_ui and not A.here:
    notes = os.path.join(NEW, 'desktop', 'update-notes.txt')
    L = [l for l in open(notes, encoding='utf-8').read().splitlines() if l.strip()][:10]   # the newest line is on top
    open(notes, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    r = sh(['node', os.path.join('desktop', 'scripts', 'sync-app.js')], cwd=NEW, env=dict(os.environ, AL_PROMOTE='1', **({'AL_NATIVE_BLOCK': os.path.abspath(A.native)} if A.native else {})))   # task MG1: the native block is kept, or replaced by --native
    say(r.stdout.strip()); m = json.load(open(os.path.join(NEW, 'desktop', 'app-version.json')))
    assert m['version'] == VER, m['version']
    sh(['git', 'add', 'desktop/app-version.json', 'desktop/update-notes.txt', 'desktop/package.json'], cwd=NEW)
    msg = 'release gate: promote v%s to installed apps (passed: lint, %s, start-up smoke test, windows, Fractals levels and exports against v%s)' % (VER, 'UI tests', REFV)
    sh(['git', '-c', 'user.name=Audio-lab-DAW', '-c', 'user.email=360039460+Audio-lab-DAW@users.noreply.github.com', 'commit', '-q', '-m', msg], cwd=NEW, check=True)
    RES['promoted'] = VER
    if A.push:
        for i in range(5):
            if sh(['git', 'pull', '-q', '--rebase', 'origin', 'main'], cwd=NEW).returncode == 0 and sh(['git', 'push', '-q', 'origin', 'HEAD:main'], cwd=NEW).returncode == 0: RES['pushed'] = True; break
            time.sleep(5)
    say('PROMOTED v%s: installed apps are offered it%s' % (VER, ' (pushed)' if RES.get('pushed') else ' (committed in %s, not pushed)' % NEW))
elif RES['passed']: say('ALL PASSED (v%s). Not promoted: %s.' % (VER, 'run with --promote' if not A.promote else 'a --quick, --skip-ui or --here run never promotes'))
else: say('NOT PROMOTED: failed: ' + ', '.join(RES['fail']))
json.dump(RES, open(os.path.join(OUT, 'result.json'), 'w'), indent=1)
sys.exit(0 if RES['passed'] else 1)
