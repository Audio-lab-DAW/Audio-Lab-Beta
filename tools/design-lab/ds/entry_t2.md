## 27 November 2026, v{V}: task DS-T2, the transport meter, the CPU line and the top bar status (design round 2, lane A)

Step 5 of the lane order (picks `... TM1 TC1 TS1 ...`): the meter **TM1**, the CPU read-out **TC1** and the top bar **TS1**, as the pick page's `drawT` with `m:1, c:1, s:1`. Edit script `tools/design-lab/ds/ds_t2.py` (asserted anchors in `meters`, `cpuFrame` and `renderTabs`, the block before `askChoice`, CSS before `.dacv`), test `tools/ui-tests/taskDS_T2.py` (23 checks; `--shots DIR`), docs `tools/design-lab/ds/release_t2.py`.

### What changed
- **Meter (TM1)**: the master meter in the transport is a peak meter with a dB scale: tick marks above the two bars (-48, -36, -24, -12, -6, -3, 0; every 12 dB brighter, 0 in red), labels -48, -24, -12, 0 in 7 px under them, the two bars between (lane E's `INS.mbar` with the RMS core of IN-M, unchanged) and a faint red 0 dB line; the white hold marks stay. The read-out says dBFS instead of dB (the max line and the click to reset are unchanged). Tooltip on the meter. Same size, same dB mapping (-60 to +6 dB) and same "draw only when something moved" key as before.
- **CPU (TC1)**: the last 10 seconds as a line: the highest load of every 250 ms (40 points) on a fixed 0 to 100 % scale with a faint base line, green, red while `cpuBad()` has a problem. Fed by the existing sampling in `cpuFrame`; the line is redrawn only when one of its points moves by half a pixel, and at most once a second while stopped (the old graph also redrew once a second). The percentage, the latency and the performance panel are unchanged. Tooltip on the line.
- **Top bar (TS1)**: a quiet status line in the middle of the tab bar: the engine's audio format (sample rate and 32-bit float, the format the mix is computed in) and the project's save state: "saved n min ago" with a green dot, "unsaved changes" amber, "not saved to a file yet" grey. Refreshed every 5 s and when the tabs change; text written only when it changes; hidden when the tabs or the buttons on the right would touch it. The playhead time above the playhead hides behind it as it does behind a tab (its rectangle cache is reset when the line changes). Work time (TS2) not added.
- **X10 slot**: `DS_HOOKS.status`, a function returning extra text, goes between the format and the save state. For task SC-K (lane A) to put the signal path there.
- Only the AudioLab look (`dsAC3`); the other looks keep today's meter with lines through the bars, the dB read-out, the filled CPU graph and no status line. No other lane's function was rewritten: `meters` (lane E's IN-M bars) and `cpuFrame` each got one branch to the new drawer; nothing in either changed in the last two hours on main.

### Tested
- `tools/ui-tests/taskDS_T2.py`, 23 of 23 (2194x1139 at 1.75x, Fractals playing, Dark and Light): ticks above the bars and nothing between them, the 0 tick red, labels under the bars, the read-out in dBFS, the CPU drawn as a line (about 9 % of the canvas lit, not an area), the status line with the format; one CPU point per 250 ms; the playhead time's rectangles include the status line; unsaved changes amber, saved 2 min ago green, never saved grey, `DS_HOOKS.status` text shown and removed; tooltips; while stopped the CPU line is redrawn at most once a second; FL style keeps today's meter, area graph and no status line; back to AudioLab the status line returns; no console errors.
- After the rebase onto v0.288: `taskIN_M.py` 26/26 (lane E's meters), `taskMD1.py` 33/33 (transport labels and units). Release gate parts by hand: lint clean (2,306 top-level functions); start-up smoke test in Electron 45, all 14 scenarios clean at 20 s on v0.277 + DS-T2, and real, none, iac-push, push1-loop-on clean again at 20 s on the rebased v{V}.
- Screenshots Dark and Light at the user's size compared with the pick page's `drawT` (`m:1, c:1, s:1`): ticks, labels, hold marks, dBFS, the CPU line and the centred status line with its dot match the drawing; the app keeps its own read-out wells, max line and latency read-out.
- **Fractals levels unchanged** (`tools/engine-tests/export_same.py`, this build): Kick -19.05560 dB (fb577dd5202b), Bass -35.48685 dB (392ec52590c7) with the master at -10 dB; -9.75669 (0496bb147f6c) and -25.48699 dB (09e0415bec5e) at 0 dB.
- Frame time (`tools/ui-tests/frametime.py --scen idle,play`, 2194x1139 at 1.75x, Fractals, glass on, software renderer; main-thread ms per frame), measured on v0.277 before and after, alternating:

  | Scene | v0.277 run 1 | DS-T2 run 1 | v0.277 run 2 | DS-T2 run 2 |
  |---|---|---|---|---|
  | idle | 10.62 | 13.13 | 12.05 | 9.91 |
  | play | 123.99 | 29.58 | 29.97 | 29.52 |

  v0.277's first play run ran while Electron was being downloaded (machine busy); the second is the fair one. Within this machine's noise; the app's own time per frame while playing 3.88 against 4.11 and 4.24 ms.

- **Re-check (28 Nov, 09:20 to 09:50 UTC, held by the gate's freeze of 09:11:57)**: the edit script re-applied cleanly on v0.294; `taskDS_T2.py` 23/23, `taskMD1.py` 33/33, `taskIN_M.py` 26/26 (one earlier run missed its live 0.75 dB tap check once, a timing check; it also passes on v0.294 itself), lint clean (2,358 top-level functions, no duplicates), start-up smoke in Electron at 20 s clean for real, none, iac-push, push1-loop-on; Fractals levels the same four numbers as above. Frame time on v0.294 against v{V}, alternating (main ms per frame): idle 9.48 / 8.17 and 11.42 / 8.31, play 21.93 / 20.84 and 24.28 / 22.71.

### Notes
- The "32-bit float" is the format the mix is computed in. The native engine (task NB) may send another format to the device; when it reports one, the status line can show it through `DS_HOOKS.status` or a small change here.

### What is left
- Next run: **DS-B1** browser (B3 look, BR2, BP1), then DS-B2 (BM2), DS-A1 with GL1 if the lines picks are in, then DS-A2 and DS-T1 (MD1 is out, v0.271).
