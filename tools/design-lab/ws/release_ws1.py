"""Task WS-1 with WS-1b (lane Q): the release's docs. python3 tools/design-lab/ws/release_ws1.py 0.XXX"""
import sys, re, datetime
V = sys.argv[1]
now = datetime.datetime.utcnow().strftime('%H:%M')
def rw(p, f):
    s = open(p, encoding='utf-8').read(); t = f(s); assert t != s, p; open(p, 'w', encoding='utf-8').write(t)
# update notes: one line
rw('desktop/update-notes.txt', lambda s: s.rstrip('\n') + '\n' + f"Start screen (v{V}): AudioLab now opens on a start screen in the splash's drawings: your recent projects (Enter opens the last one, type to search), a new empty project, templates and Open a file. No demo song is loaded any more. Settings › General › Show the start screen at start-up, and Start screen drawings… to choose the pictures.\n")
# device backlog: the WS-1 line
def dev(s):
    L = s.split('\n'); i = [k for k, x in enumerate(L) if x.startswith('- Task WS-1 (start screen build, lane Q):')]
    assert len(i) == 1
    L[i[0]] = (f"- Task WS-1 with WS-1b (start screen build, lane Q, the user's D6 answer): **done**, v{V}. A fresh start opens the start screen "
               "(W1 card over the drawing, every start, no demo songs anywhere, the splash grows into it in 1000 ms): recent projects with tempo, length and "
               "a clip map, New empty project, Beat starter, Audio tracks, My templates, Open a file; Enter opens the last project, arrows, type to search. "
               "Drawings at random: dipole (F1 flow, Jupiter), moons, interference, phase portrait, Lissajous, TRAPPIST-1, Fourier; Settings › General › "
               "'Start screen drawings…' chooses them (WS-1b). Tests taskWS_1.py 38/38, taskWS_1b.py 16/16. Plan: docs/start-screen.md.")
    return '\n'.join(L)
rw('docs/device-backlog-2026-11-25.md', dev)
rw('docs/backlog-log.md', lambda s: s.rstrip('\n') + f"""

## 28 November 2026, task WS-1 with WS-1b (lane Q): the start screen, v{V}
The user's D6 answer: "Empty, no songs. To start up, you have to choose or open your own project ... a splash screen to choose your previous projects, or maybe open a template ... the same scientific style that we have on the actual splash screen." Picks W1 T1 D3 P1, round 2 R4 R5 R6 R7 R8, dipole F1 Jupiter (particles smaller and fewer), motion M1 1000 ms smooth; the drawings setting asked at 01:53 Brussels (WS-1b).
- **Start-up:** the stored tabs come back as they were; no Fractals song, no demo songs added, no "Demo song loaded" toast. With nothing stored, one empty "Untitled" project (one audio and one instrument track, 120 BPM) sits behind the start screen and is dropped when something else opens untouched. Old profiles keep every project and see them as recent, the one open at quit first.
- **The start screen (W1):** a card over the drawing's band: recent projects (name, where it lives, when, tempo, length and track count with amber units, a clip map in track colours), New empty project, Beat starter, Audio tracks, My templates, Open a file, More options (lane F's New project window), the keyboard line, Show at start-up. Enter opens the selection (the last project first), arrows, typing searches, Escape, ⌘N / Ctrl+N, ⌘O / Ctrl+O, a click outside closes.
- **Hand-over (P1, M1):** the splash's card grows into the start screen in 1000 ms (cubic-bezier(.2,.7,.2,1)); Reduce motion, Light mode or Motion Signal only: a 120 ms fade. Enter during the splash opens the last project at once.
- **Drawings:** S1 dipole with the F1 field flow, S2 moons, R4 to R8, never twice in a row; ambient motion only at Motion Ambient, never in Light mode, with Reduce motion or when hidden; nothing per frame when closed.
- **WS-1b:** Settings › General, under "Show the start screen at start-up": "Start screen drawings…" (closed by default), a switch per drawing, Only this one, All on; at least one stays on; `UI.wsDraw`. `WS_HOOKS.settingsRows` for lane B; `audiolab-ws-draw` and `WS_HOOKS.drawings()` for lane G's splash (not changed here).
- **D3:** the + menu has "Start screen…" instead of the Fractals demo; the New project window hides the demo songs. `openDemoFractals()` and `demo()` stay for the release gate and the tests; under navigator.webdriver the start is as before (Fractals) unless localStorage `audiolab-ws-test` is 1.
- **Checks on v{V}:** lint clean; taskWS_1.py 38/38, taskWS_1b.py 16/16; desktop smoke test (real, keyboard) 0 errors, 0 state changes, frames p50 16.7 ms. The audio path is not touched (no worklet, graph or export code changed), so exports and Fractals levels are as in v0.297 (not measured again).
- Released at {now} UTC after the 09:11 freeze; `desktop/app-version.json` untouched.
""")
rw('docs/start-screen.md', lambda s: s.rstrip('\n') + f"\n\n## Released: v{V} (WS-1 with WS-1b)\nstart screen complete. Next for others: lane B may move the two rows (`WS_HOOKS.settingsRows`); lane G may let the splash read `audiolab-ws-draw` and draw F1 and R4 to R8 (`WSR2.FN`).\n")
print('docs written for v' + V)
