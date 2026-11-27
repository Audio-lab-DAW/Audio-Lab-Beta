# Extension lab (task EX1)

Prototypes for user themes, user-made devices, a script device and chat-built devices. Nothing here is loaded by the app.

- `extensions-round-1.html`: the pick page "AudioLab extensions, round 1" (https://claude.ai/artifact/Xz4hiGRdHZM67suL4KiWq5). It is page content without a document wrapper, as the artifact publisher expects.
- `node tools/extension-lab/check.js`: 44 headless checks; also writes `open.html` (the page wrapped so a browser can open it) and the files in `examples/`. Serve `open.html` over http (for example `python3 serve_audiolab.py` from the repo root): audio worklets do not load from `file://`.
- `examples/`: theme, device and script files used on the page.

The plan, the research and the file formats are in `docs/extensions-plan.md`.
