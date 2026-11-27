# Extension lab (task EX1)

Prototypes for user themes, user-made devices, a script device and chat-built devices. Nothing here is loaded by the app.

- `extensions-round-1.html`: the pick page "AudioLab extensions, round 1" (https://claude.ai/artifact/Xz4hiGRdHZM67suL4KiWq5). It is page content without a document wrapper, as the artifact publisher expects.
- `node tools/extension-lab/check.js`: 44 headless checks; also writes `open.html` (the page wrapped so a browser can open it) and the files in `examples/`. Serve `open.html` over http (for example `python3 serve_audiolab.py` from the repo root): audio worklets do not load from `file://`.
- `examples/`: theme, device and script files used on the page.

The plan, the research and the file formats are in `docs/extensions-plan.md`.

## The deep layer (task EX2)

Prototypes for the layer below Settings: an everything list, hide / rename / move any control, commands and macros, CSS snippets, user scripts in a worker, safe mode. Nothing here is loaded by the app.

- `extensions-with-deep-layer.html`: **the file that is published to the pick page** (same link as above): EX1's page plus the part "The deep layer" before the questions. `extensions-round-1.html` itself is not modified.
- `deep-layer.html`: the deep layer alone, for testing.
- `python3 tools/extension-lab/build_deep.py`: builds both from `deep-src/` (and from `extensions-round-1.html`). Run it again after any change to EX1's page, then publish `extensions-with-deep-layer.html`.
- `node tools/extension-lab/deep_check.js`: 73 headless checks over both pages.

Design, research and file formats: `docs/extensions-plan.md`, section 9.
