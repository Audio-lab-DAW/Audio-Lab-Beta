# Lane E: instruments (task IN)

Edit scripts for `index.html`, one per step of `docs/design-round-4-instruments.md` (implementation order). Each asserts unique anchors, so after a rebase it is re-run on the fresh file instead of merging by hand.

- `in_a.py` + `in_a_block.js`: IN-A, the shared instrument base (`INS`). Release notes: `release_a.py <version> <entry.md>`. Meter cost check: `meter_cost.py a.html [b.html]`.

- `in_m.py` + `in_m_block.js`: IN-M, the level meters (M2: RMS core, read-outs, the taper scale). Release notes: `release_m.py <version> <entry.md>`.
- `in_l.py` + `in_l_block.js`: IN-L, loudness (L2: the history drawer `INS.lhist` in five places). Release notes: `release_l.py <version> <entry.md>`.

Tests: `tools/ui-tests/taskIN_<step>.py`.
- `in_g.py` + `in_g_block.js`: IN-G, dynamics (G1 history `INS.grh`, G3 the compressor's curve `ingCK`, G4 bars `ingBar`). Release notes: `release_g.py <version> tools/design-lab/in/entry_g.md`. Draw cost: `draw_cost_g.py a.html [b.html]`.
