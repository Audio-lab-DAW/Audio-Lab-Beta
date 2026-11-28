# Lane Q, task WS: the start screen

- `start.src.html`: the pick page (WS-0). `python3 build.py` inlines `splbg.js` (a plain copy of `SPLBG` from index.html, lines of the SP1 block) and writes `start.html`, which is what is published as the artifact "AudioLab start screen".
- `shot.py <abs path to start.html> <out dir>`: screenshots of the four mocks plus a Light, a keyboard and a replay shot, and the console errors.
- WS-1's edit scripts go here too.
- Round 2 (WS-0b): `start2.src.html` plus `r2draw.js` (the eight new drawings R1 to R8 and the dipole flows F1 to F3, in SPLBG's function shape), `python3 build2.py` writes `start2.html` (published as "Start screen round 2"); `shot2.py <abs path to start2.html> <out dir>` screenshots the sections, the hand-over M1 to M4 at five moments and Light, and lists console errors.
