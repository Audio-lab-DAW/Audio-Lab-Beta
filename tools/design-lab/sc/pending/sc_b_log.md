
## 27 November 2026, vVV: task SC-B, About as the random set Y1 (lane G)
Step SC-B of `docs/science-look-round-2.md` (section Y, the user's pick **Y1**: "Earth most often: Earth 3 times in 5, orbit corner 1 in 5, field arcs 1 in 5, chosen each time About opens"). Claimed in "Where it stands" before the work. Built on task AB1's About window and SC-A's drawing module. Edit script `tools/design-lab/sc/sc_b.py` with `sc_b_block.js` (five anchors, asserted unique: the block before `askChoice`, and four small lines in `AB1`: its kinds, its counters, its pick, and the first line of its `scene`), test `tools/ui-tests/taskSC_B.py` (19 checks).

### Built
- **The odds**: `sciAboutPick()` (weights in `SCI_ABOUT`): the Earth 3 in 5, split evenly between AB1's two Earth pictures (E2 "corner" and E7 "sheet", 3 in 10 each), the orbit corner 1 in 5, the field arcs 1 in 5. Chosen at every opening, no restart needed; the same one can come twice, as before.
- **Orbit corner (B2)**: `SCI.D.corner`, five tick rings centred just outside the lower right corner and reaching across the window, a tick ring with longer marks every fifth, one slow amber body per ring. **Field arcs (B3)**: `SCI.D.field`, dipole field lines rising from below the lower edge, a charge riding each line. Both on AB1's dark ground and under AB1's veil, so the text column, the name and the atom keep the same backing and contrast as with the Earth; drawn a little stronger than the faint places so they read like the Earth's lines (no labels).
- **Unchanged**: the window, its content, the atom, the timing (at most 30 pictures a second, only while About is open, a still picture at the Light level, with reduce motion and when Motion is not Ambient, nothing when closed), and the two Earth pictures.
- **Light mode and the setting**: no new science drawings in Light mode (the user's W14 off) and none with Science drawings off: About then shows the Earth only (corner and sheet evenly), as before.
- Test hook as AB1's: `AB1.force('orbit' | 'arcs')`; counters `AB1.n.orbit`, `AB1.n.arcs`; `AB1.bench('orbit'|'arcs', w, h, n)`.

### Tested
- `tools/ui-tests/taskSC_B.py`, 19 of 19: 20,000 picks (Earth 59.96 %, corner 30.0 %, sheet 29.9 %, orbit 20.4 %, arcs 19.6 %); 30 real openings gave all four; each new picture in the same window (atom, 8 values), drawn beside the text, 21 pictures a second while open, still with Motion not Ambient, nothing drawn when closed; Light mode and the setting off: Earth only; the Earth pictures as before; drawing time 0.03 ms (orbit) and 0.09 ms (arcs) a picture against about 1 ms for the Earth. No console errors.
- Screenshots looked at: orbit, arcs and the corner Earth at 1400 x 900 at 2x. The first build drew the new pictures at the faint strength and they looked empty next to the Earth; raised so their lines are about as bright as the Earth's field lines.
- GATE

### Left
- SC-C: W1 as the user changed it (a tempo orbit switched on by the user, pinnable as a borderless pin, no ring of amber numbers), W2, W11. Then SC-D, SC-E, SC-F (W4 only), SC-G (W10 as changed), SC-H to SC-L.
