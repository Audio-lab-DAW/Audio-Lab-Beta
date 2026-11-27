# Lane E: instruments (task IN)

Edit scripts for `index.html`, one per step of `docs/design-round-4-instruments.md` (implementation order). Each asserts unique anchors, so after a rebase it is re-run on the fresh file instead of merging by hand.

- `in_a.py` + `in_a_block.js`: IN-A, the shared instrument base (`INS`). Release notes: `release_a.py <version> <entry.md>`. Meter cost check: `meter_cost.py a.html [b.html]`.

Tests: `tools/ui-tests/taskIN_<step>.py`.
