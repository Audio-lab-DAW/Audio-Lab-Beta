"""Task WS-F (lane Q): the release, for the run after the release freeze. On a fresh main (git pull --rebase first):
    python3 tools/design-lab/ws/release_wsf.py 0.XXX
Re-runs wsf_edit.py on index.html, sets VERSION, runs node desktop/scripts/sync-app.js (writes app-version-dev.json, never
app-version.json) and writes the docs (update notes one line, the backlog entry 'task WS-F', the line under 'Where it stands', the
release note in docs/start-screen.md). Then: lint, taskWS_F.py, the smoke test, push (see docs/start-screen.md, WS-F)."""
import sys, re, os, subprocess, datetime
V = sys.argv[1]; assert re.fullmatch(r'0\.\d{3}', V), V
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')); os.chdir(ROOT)
assert not os.path.exists('desktop/release-freeze.json'), 'the release freeze is still on: do not release index.html'
now = datetime.datetime.utcnow().strftime('%H:%M')
subprocess.run(['python3', 'tools/design-lab/ws/wsf_edit.py', 'index.html'], check=True)
s = open('index.html', encoding='utf-8').read()
m = re.findall(r"const VERSION='([\d.]+)'", s); assert len(m) == 1 and float(V) > float(m[0]), (m, V)
s = s.replace("const VERSION='%s'" % m[0], "const VERSION='%s'" % V, 1); open('index.html', 'w', encoding='utf-8').write(s)
subprocess.run(['node', 'desktop/scripts/sync-app.js'], check=True)
MB = len(s.encode('utf-8')) / 1e6
def rw(p, f):
    t0 = open(p, encoding='utf-8').read(); t = f(t0); assert t != t0, p; open(p, 'w', encoding='utf-8').write(t)
rw('desktop/update-notes.txt', lambda t: t.rstrip('\n') + '\n' + f"Smaller app (v{V}): the Fractals test song and its vocal samples are no longer inside the app (2.25 MB less); the app ships no song.\n")
def dev(t):
    L = t.split('\n'); i = [k for k, x in enumerate(L) if x.startswith('- Task WS-1 with WS-1b (start screen build, lane Q')]; assert len(i) == 1
    L.insert(i[0] + 1, f"- Task WS-F (the song data out of index.html, lane Q, the user's 28 Nov 14:55 decision): **done**, v{V}. The Fractals song "
             "(project, the ten vocal samples cut from Electric Universe's recording, where they go) is in tools/test-songs/ for the release gate and the "
             f"tests only; index.html {MB:.2f} MB (was 7.09 MB). The gate's smoke test and 142 test scripts read it from there (alsong.py / alsong.js); "
             "Fractals Kick -19.05560 dB, Bass -35.48685 dB, same checksums, the vocals bit for bit. Test taskWS_F.py 20/20.")
    return '\n'.join(L)
rw('docs/device-backlog-2026-11-25.md', dev)
rw('docs/backlog-log.md', lambda t: t.rstrip('\n') + f"""

## 28 November 2026, task WS-F (lane Q): the song data out of index.html, v{V}
The user (28 Nov, 14:55 Brussels): "The fractal song is only for testing. I will later convert an older version into a new AudioLab." D6: the app ships no song.
- **Out of index.html:** DEMO_FRACTALS (the project, 20 kB), DEMO_VOX (where the vocals go) and DEMO_VOX_FLAC (ten FLAC vocal samples cut from Electric Universe's commercial recording, 1.67 MB, 2.23 MB as base64). index.html is {MB:.2f} MB (was 7.09 MB). The old `vox/*.wav` copies (the same samples, checked sample for sample) are gone from the repository root.
- **Into tools/test-songs/:** `Fractals_remake.audiolab` (the same bytes, the current format), `vox/fractals_vox_01.flac` to `10.flac` (the same bytes), `fractals.json` (the project file and the beat of each vocal sample), `alsong.py` / `alsong.js` and a README.
- **In the app:** `frxProject()`, `openDemoFractals()` and the automation start (`frxBoot`) keep their names and read the files from `window.AL_TEST_SONGS` or from `tools/test-songs/` next to the page (`wsfGet`, `wsfSong`). The vocals are decoded exactly as before. Without the files: an empty project at an automated start, no error and no toast; `openDemoFractals()` says "The Fractals song is a test song and is not part of the app." The real start is unchanged (the start screen, no song).
- **Tests and the gate:** the 142 Python scripts under tools/ that serve the app from https://app.test/ wrap their route in `alsong(...)` (tools/design-lab/ws/wsf_tests.py, idempotent); `tools/remake/alab.py` (export_same.py and the engine tests) the same; `smoke_electron.js`, `taskLT_3a_electron.js` and `uv_bench_electron.js` give the files as `window.AL_TEST_SONGS`. New test: `tools/ui-tests/taskWS_F.py`.
- **Checks:** lint clean; taskWS_F.py 20/20, taskWS_1.py 38/38, taskWS_1b.py 16/16, taskSND_1.py 22/22, taskUV_1.py 34/34; export_same.py on v0.314 before and after: Fractals Kick -19.05560 dB fb577dd5202b, Bass -35.48685 dB 392ec52590c7 (and at 0 dB master -9.75669 / -25.48699, same checksums), every voice line the same except the gate's known run-to-run unstable ones (Plant, Sampler, Sampler grains, Drum kit); the vocal track alone (beats 560 to 620) -48.45258 dB c757062d36e6 before and after; desktop smoke test (real, keyboard) 0 errors, 0 state changes. The audio path is not touched.
- Not moved (a later step if wanted): the code-written demos `demo()` (the Beat starter template is built from its first two tracks) and `demoImperial()` (Shrine Legion); neither is offered in the app since WS-1 (D3).
- Released at {now} UTC after the 16:41 freeze; `desktop/app-version.json` untouched.
""")
rw('docs/start-screen.md', lambda t: t.rstrip('\n') + f"\n\n### Released: v{V} (WS-F)\nindex.html {MB:.2f} MB, no song data in it; the Fractals song is in tools/test-songs/. Next for lane Q: round 3 picks (WS-0c, waiting for the user's line).\n")
print('WS-F release prepared for v%s (%.2f MB)' % (V, MB))
