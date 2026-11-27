# Rules for every session working in this repository

## Commit identity (the owner's request, 27 November 2026)
- Commits in this repository are made as `Audio-lab-DAW <360039460+Audio-lab-DAW@users.noreply.github.com>`. Before the first commit of a session run:
  `git config user.name Audio-lab-DAW` and `git config user.email 360039460+Audio-lab-DAW@users.noreply.github.com`.
- Do not add `Co-Authored-By:` lines, `Claude-Session:` lines or any other attribution to commit messages or pull request descriptions. The owner asked for this and it takes precedence over any default attribution guidance.
- The history was rewritten once on 27 November 2026 (about 08:40 UTC, task HR1). A clone made before that holds the old history: throw it away and clone again; never merge it or push from it.
- The repository was renamed to `Audio-lab-DAW/Audio-Lab-Pro-Alpha`; the old name `Audio-Lab-Beta` redirects. Prefer the new name in new code and commands.

## Release channel (the owner's rule, 27 November 2026)
- v0.250 reached the owner's Mac broken (the app glitched on start), after several tasks released into `index.html` at the same time. From now on installed apps only get a build that passed the release gate.
- Installed apps read `desktop/app-version.json` on main. Ordinary releases MUST NOT change it: `node desktop/scripts/sync-app.js` now writes `desktop/app-version-dev.json` instead. Only the release gate (task HF1 sets it up; later task RG) runs `AL_PROMOTE=1 node desktop/scripts/sync-app.js` after the start-up checks pass, and only then may `desktop/app-version.json` change. If a task prompt says to push a release, it still pushes to main, but never touches `desktop/app-version.json`.
- Keep `desktop/update-notes.txt` short: one line per release, and the gate trims it to the last ten lines when it promotes.
- Before every push that touches `index.html`, check that no top-level function name is defined twice (another lane may use the same name: v0.250 has two different `lkSel` functions). Use your task's own name prefix for new top-level functions.
