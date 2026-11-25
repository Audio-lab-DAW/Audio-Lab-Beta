# AudioLab Pro

A digital audio workstation that runs in Chrome.

**Open it:** https://audio-lab-daw.github.io/Audio-Lab-Beta/

The page is AudioLab Pro running as its own page, not inside a frame, so:
- **Settings → Audio → Choose output device…** can pick your DAC (iFi Gryphon, AMS-24, …) by name.
- The shared-memory engine is available. `coi-serviceworker.js` adds the cross-origin isolation headers that GitHub Pages can't send itself.

The first visit reloads the page once while the service worker starts. That's normal.

## Files
| File | What it is |
|---|---|
| `index.html` | AudioLab Pro (the whole app in one file) |
| `coi-serviceworker.js` | Adds COOP/COEP + speaker-selection headers on GitHub Pages |
| `_headers` | The same headers for Netlify / Cloudflare Pages |
| `serve_audiolab.py` | Run it on your Mac without the internet: `python3 serve_audiolab.py`, then open http://localhost:8765 |
| `engine-test.html` | The earlier shared-memory engine test |

## First-time setup (once)
In the repository on GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: `main`, folder `/ (root)` → Save.** The site is live at the link above about a minute later.

Projects are kept per website. Save a project as a `.audiolab` file in one place and open it in the other.


## Desktop app
Mac and Windows apps live in [`desktop/`](desktop/README.md). Build them from the Actions tab (*Build desktop apps*).

## Install as an app (no download, no Mac security prompts)
Open the site in Chrome, then use the install icon at the right of the address bar (or ⋮ ▸ Cast, save and share ▸ Install page as app). AudioLab Pro then opens in its own window and Dock icon, with direct output-device selection.
