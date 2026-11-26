# AudioLab glass engine: the module (task G2, 26 November 2026)

The engine from `docs/glass-engine-plan.md` (section 2.4) now exists as a stand-alone file. **Nothing in `index.html` or `desktop/` was changed, VERSION was not bumped.** Glass step 1 (task G3, docked surfaces) can start from here.

| File | What it is |
|---|---|
| `tools/glass-lab/glass-engine.js` | The engine. Plain JS, one file, no build step, no dependencies, about 34 KB with comments. Defines `window.AudioLabGlass`. Paste it into `index.html` or load it with a script tag. |
| `tools/glass-lab/engine-test.html` | Test page: AudioLab-sized panels over the scrolling arrangement from the Glass Bench, frame-time readout, counters, "Measure" and "Compare presets". Needs `glass-engine.js` beside it. |
| `tools/glass-lab/engine_test.py` | 86 headless checks (Python Playwright). `python3 tools/glass-lab/engine_test.py` |

Test page as an artifact (one file, engine inlined): https://claude.ai/artifact/HCdnmA3jbVsRyz4ifo7yvY

## 1. How it works

1. **One WebGL2 canvas** per layer. Everything the engine draws is glass faces; where there is no glass the canvas is transparent.
2. **One backdrop picture** (the arrangement canvas). It is uploaded to a texture **only after `markDirty()`**.
3. **One dual-Kawase blur pyramid** is built from that texture, **only when the picture changed** (or a preset, the quality or the size changed; then from the texture already there, without a new upload).
4. **Every glass surface is one quad in one shader**: rounded-rectangle distance field, rim refraction, face colour, tint, rim light, shadow. The shader reads only the blurred backdrop, never the canvas it draws to, so **glass never samples glass**: a window over a docked panel shows the arrangement, not the panel.
5. **Moving, resizing, fading, adding or removing a panel redraws the quads only.** With nothing changed, `render()` returns at once and makes no GL call.

The shader starts from the one in `glass-bench.html`: the lens has its own distance field with a corner radius of at least the lens width and the bending direction is computed directly (the corner-seam fix), and the lens and blur presets are the same.

### Numbers used (from plan 2.2; numbers only, no code from the reverse-engineering repos)

- **Lens band** = min(short side / 4, preset maximum): Off, Fine 12 px, **Apple 20 px**, Wide 40 px (Wide uses short side / 3). Quarter-circle profile. A 48 px transport gets 12 px, a 32 px pill 8 px, track headers 20 px. The middle of a large panel is flat.
- **Face**: saturation 1.3, then the panel tint. Kinds differ in how much tint: docked and window 0.5, menu and sheet 0.6 (text-heavy glass gets more frost), pill 0.45.
- **Rim light**: two-sided at +45° and −135° (the macOS 26 placement), 1.6 px wide, as in the bench.
- **Shadow** (floating kinds only): offset (0, 8), radius 4 + 20t, opacity 0.04 + 0.56t, t = clamp((short side − 64) / 96, 0, 1). So a window gets a real shadow, a pill a faint one, docked panels none.
- **Blur**: Light, **Regular**, Heavy = the pyramid goes down to 1/4, 1/8, 1/16 of the size.

Two things are **not** Apple's numbers by default, on purpose:
- The plan lists a face colour matrix "0.125 / 1.125" for dark mode without saying which term is which. I read it as "add 0.125, multiply by 1.125". It makes the face clearly brighter than the look the user approved in the Glass Bench, so the default stays the bench look and the matrix is an option (`face:{sat:1.3, mul:1.125, add:0.125}`, or `setFace`). The test page has a "Face" choice to compare the two.
- Rim light strength stays at the bench values rather than Apple's "amount 0.5".

## 2. API

```js
const g = AudioLabGlass.create(canvas, opts);     // canvas: an empty <canvas>, positioned by the app
g.setBackdrop(arrCanvas);                         // or setBackdrop(source, {rect:[x,y,w,h]}) when the picture covers only part of the engine canvas
g.addPanel({id:'tr', rect:[0, 952, 1600, 48], radius:0, kind:'docked'});
g.markDirty();                                    // the backdrop picture was repainted
g.render(now);                                    // call once per frame; draws only what changed; returns true when it drew
```

All rectangles are in **CSS pixels relative to the engine canvas**, as `[x,y,w,h]`, `{x,y,w,h}` or a DOMRect.

| Call | What it does | What it costs |
|---|---|---|
| `create(canvas, opts)` | Makes the engine. Falls back by itself when WebGL2 is missing. | once |
| `addPanel({id, rect, radius, kind, ...})` | Adds a surface (same id again: updates it). | quads |
| `updatePanel(id, {rect, radius, kind, visible, opacity, z, ...})` | Changes a surface. Unchanged values cost nothing, so it can be called every frame. | quads |
| `removePanel(id)`, `hasPanel(id)` | | quads |
| `setBackdrop(source, {rect})` | The picture behind all glass: a canvas, OffscreenCanvas, ImageBitmap, image or video. | upload + blur |
| `markDirty()` | The picture changed. The upload happens in the next `render()`, at most at the quality's rate. | upload + blur |
| `setLensPreset('off'|'fine'|'apple'|'wide')` | | quads |
| `setBlurPreset('light'|'regular'|'heavy')` | | blur (no upload) |
| `setQuality(3|2|1|0)` or `'high'|'medium'|'low'|'static'` | See the table below. | blur (no upload) |
| `setFlat(id, {rect, radius, color:[r,g,b,a] or source})`, `markFlatDirty(id)`, `removeFlat(id)` | A flat picture of DOM that floating glass covers (plan 2.4, option a). See section 4. | flat blur |
| `setAccessibility({reduceTransparency, increaseContrast})` | `true` / `false` forces it, `null` follows the system. | quads |
| `setFace({sat, mul, add})` | Face colour matrix. | quads |
| `resize(cssW, cssH, dpr)` | Called by a ResizeObserver unless `autoResize:false`. | blur (no upload) |
| `render(now)` | Does the work. `now` = the frame time from requestAnimationFrame. | only what changed |
| `destroy()` | Frees everything and gives the context back. | |

Read-only: `g.mode` (`'gl'` or `'fallback'`), `g.reason` (`'no webgl2'`, `'lost'`, `'shader'`, `'forced'`), `g.pending` (a capped backdrop refresh is waiting: keep calling `render()`), `g.info` (sizes, presets, levels, flags), `g.stats` (counters: `uploads`, `pyramids`, `flatPyramids`, `draws`, `skipped`, `lost`, `restored`), `g.gl`.

Panel options beyond rect, radius and kind: `visible`, `opacity` (0 to 1, for menu fades), `z` (drawing order), `over:'flats'`, `tint:[r,g,b]`, `tintAmount`, `shadow` (0 = none, 1 = Apple's), `lens:false`.

Main `opts`: `lens`, `blur`, `quality`, `tint` and `solid` (panel colours, default rgb 22 28 42), `backdropColor`, `maxDpr` (2), `face`, `rim`, `kinds` (override or add kinds), `allowSoftware` (false: refuse a software renderer where the browser reports one), `regionCull` (true), `autoResize` (true), `onFallback(on, why)`, `requestRender()` (the engine asks for a frame after a restore or a system setting change), `fallbackCanvas`, `reduceTransparency`, `increaseContrast`.

### Kinds

| kind | for | shadow | tint | moves? |
|---|---|---|---|---|
| `docked` | track headers, transport, tab band, device panel | none | 0.5 | no |
| `window` | mixer and other floating windows | yes | 0.5 | yes |
| `sheet`, `menu` | sheets, menus | yes | 0.6 | yes |
| `pill` | small floating controls | faint (by size) | 0.45 | yes |

"Moves: no" matters for speed: when every visible panel is docked, the blur is computed **only for the screen area under those panels** (plus a safety margin), not for the whole arrangement. With the usual layout that is about half the screen. As soon as a floating panel is visible the whole picture is blurred, so that moving it never needs a rebuild. A docked panel that changes size (the device panel being dragged taller) rebuilds the blur for those frames, from the texture already there.

### Quality steps

| Level | Blur pyramid starts at | Backdrop refresh | Panels |
|---|---|---|---|
| 3 high (default) | half size | every change | screen rate |
| 2 medium | quarter size | at most 60 per second | screen rate |
| 1 low | quarter size | at most 30 per second | screen rate |
| 0 static | none: plain tint with fine noise | none (nothing is uploaded) | screen rate |

The cap also holds for fed display canvases (`markFlatDirty`): a device display that repaints every frame under a floating window is picked up 60 or 30 times per second at medium and low.

Sizes are counted in **CSS pixels**. On a 2x (Retina) screen the first level is therefore a quarter of the device pixels at "high" and an eighth at "medium": the blur looks the same on every screen and a Retina screen pays no more than a normal one. This differs from the Glass Bench, which counted device pixels (so its blur was half as wide on a 2x screen and cost four times as much there).

### Fallbacks and accessibility

- **WebGL2 missing**: the engine draws on the same canvas with the 2D context: each panel a rounded rectangle in the solid panel colour with fine noise and a thin border. Redrawn only when a panel changes.
- **Context lost**: the engine puts a 2D canvas in the same place (same class, position, size, z-index), draws the same plain tint there, hides the GL canvas and calls `onFallback(true, 'lost')`. When the browser restores the context it rebuilds shaders, textures and pyramids, removes the extra canvas, calls `onFallback(false)` and `requestRender()`.
- **Reduce Transparency** (`prefers-reduced-transparency: reduce`): plain tint with noise, no backdrop work at all.
- **Increase Contrast** (`prefers-contrast: more`): tint at least 0.82, no lens, no rim light, a clear light border.
- Both follow the system live and can be forced by the app.

## 3. What makes it cheap

- No work without a change: no upload, no blur pass, no draw.
- One upload and one pyramid for all glass in a layer, instead of one capture and blur per element as `backdrop-filter` does.
- The pyramid works on a quarter, a sixteenth, ... of the pixels; blur strength is a matter of levels, not of a wide kernel.
- Docked-only layouts blur only the area under glass.
- The lens is one texture lookup per pixel at any width; the shadow is computed in the same quad.
- A layer with no visible panel does nothing, even with a dirty backdrop.

## 4. How to integrate (plan 3.1)

**Step 1, docked surfaces.**

1. Put one canvas where `#arrBack` sits (before `#arr`), covering the area the docked glass covers; `pointer-events:none`. It takes the place of `#arrBack` **and** `#arrBlur`; `gbLayout` / `gbCopy` / `gbTick` and `abDraw` are not needed on this path.
2. `g = AudioLabGlass.create(canvas, {requestRender: () => /* ask the app's frame loop for a frame */, onFallback: (on) => /* switch the old glass path on or off */})`.
3. `g.setBackdrop(arrCanvas, {rect})` with the arrangement canvas and where it sits relative to the engine canvas.
4. For `#hglass`, `#tr`, `#fxband`, `#fxglass`: `g.addPanel({id, rect, radius, kind:'docked'})`, and `updatePanel` from the existing layout code (`gbLayout`). Those elements then carry **no `backdrop-filter`**, only border and content. Keep `gbClip` or drop it: the glass faces are opaque, so the arrangement under them is hidden either way.
5. Call `g.markDirty()` **only where `drawArr` actually repainted**. A playhead-only frame must not call it: draw the playhead as its own thin layer under the engine canvas (it then simply disappears under glass), as the test page does in "playhead only".
6. Call `g.render(t)` once per frame from the existing frame loop. It is free when nothing changed, so it needs no guard.
7. While `g.mode !== 'gl'` the engine shows the plain tint by itself. If the old `backdrop-filter` glass should be the fallback instead (plan 3.1), switch it on in `onFallback(true)` and hide the engine canvas.

**Step 2, floating windows, sheets, menus.** The engine canvas of step 1 lies under the DOM of the docked panels, so a floating face drawn there would be covered by knobs. Use a **second engine on a second canvas directly under the floating layer** (above the docked DOM):

1. Same backdrop (`setBackdrop(arrCanvas, {rect})`, `markDirty()` at the same place). The second engine uploads and blurs only while one of its panels is visible.
2. Windows, menus, sheets: `addPanel({kind:'window' | 'menu' | 'sheet', over:'flats', ...})`.
3. Where floating glass can cover DOM, feed the flat picture: `setFlat('fxglass', {rect, color:[r,g,b,1]})` for each docked panel (its average glass colour), and `setFlat('disp1', {rect, radius, source: displayCanvas})` for device displays, with `markFlatDirty` when such a display repainted. Panels with `over:'flats'` see the backdrop plus these flat pictures; all others do not. Moving the window rebuilds nothing.
4. Remove the nested blurs in the mixer (`.fwh`, `.ck`).

The test page is built exactly this way (two engines, docked and floating), so its numbers are the numbers of this plan.

**Settings.** GL engine = quality 3 (automatic stepping-down can go to 2 and 1 before leaving the engine), Blur and Solid stay outside the engine (Solid can also be quality 0). Lens and blur presets map one to one to `setLensPreset` and `setBlurPreset`.

**Step 3** (remove `rfAttach`, `rfBuild`, `rfMap`, `rfStyle`, the `feImage` lens) only after the user confirms on the Mac.

## 5. What was tested (headless, cloud machine)

`python3 tools/glass-lab/engine_test.py`: **88 checks, all pass**, no console errors or warnings. The cloud machine has **no GPU** (SwiftShader software renderer), so **its frame rates mean nothing**; only correctness was tested.

- **Rim bends, middle flat**: with a picture whose colour is its own coordinate, the place each glass pixel is taken from was read back. The shift follows the quarter-circle profile on the left, top and right edges for Fine, Apple and Wide (worst error 1 px); nothing bends beyond the band; the middle is the same pixel with every lens preset; band width follows the panel (48 px bar about 12 px, 32 px pill about 8 px).
- **No corner seam**: the bending direction is continuous across the corner diagonal for radius 0, 6 and 16.
- **Middle frosted**: detail under glass drops to under 10 % (regular), 3 % (heavy), 25 % (light) of the picture, at half and quarter size; more blur gives less detail; the same strength on a 2x screen as on a 1x screen.
- **Face colour** matches the formula; the Apple matrix option brightens it.
- **No glass on glass**: a window over a red docked panel is pixel-identical to the window alone.
- **Dirty logic** (counted): first frame 1 upload and 1 pyramid; moving a panel 50 times gives 50 quad redraws, **0 uploads, 0 pyramid rebuilds**; 50 idle `render()` calls draw nothing; `updatePanel` with the same rectangle draws nothing; a lens change redraws faces only; a blur change rebuilds one pyramid without an upload; with no visible glass a dirty backdrop is not uploaded.
- **Refresh cap**: at a simulated 240 frames per second, with the backdrop dirty every frame and a panel moving every frame: high 240 uploads, medium 60, low 30, and 240 panel redraws in each case.
- **Blurring only under docked glass** gives pixels identical to blurring everything (all blur presets, half and quarter size); when a floating panel appears the full blur is rebuilt from the kept texture.
- **Flat picture**: floating glass sees the backdrop, the flat colour and the fed display canvas; docked glass does not; moving the floating glass rebuilds nothing; a changed display rebuilds only the flat pyramid.
- **Backdrop rectangle**, **shadow** values, **panel opacity**, **quality static**.
- **Reduce Transparency and Increase Contrast** through the emulated system settings and through `setAccessibility`.
- **Context loss and restore** (`WEBGL_lose_context`): fallback tint appears on a 2D canvas in the same place, panels still move, after restore the glass is pixel-identical to before; four losses in a row; no canvases left behind.
- **WebGL2 missing** (getContext made to return null): fallback on the same canvas, every API call harmless.
- **Test page** at 1x and 2x: both layers draw; scrolling uploads every frame; a still picture with the mixer moving gives 0 uploads, 0 rebuilds and the docked layer is not redrawn at all; playhead on its own layer gives 0 uploads; nothing moving gives 0 draws; screenshots show frosted headers and mixer, an untouched arrangement outside glass, the menu over the device panel showing the flat panel colour, lens on/off differing in the rim only; the page's context-loss buttons, quality and accessibility switches; phone width without sideways scroll.

Not tested here, for the user's Mac and for Windows:

- **Frame rate and real GPU cost.** In software, the whole glass of the test page (both layers, 1600x1000) took about 75 to 90 ms per rebuild at high and about 37 ms at medium and low; lens and blur presets made no difference beyond noise. Only the ratio means anything.
- A real driver context loss (GPU process restart, sleep and wake), Windows drivers.
- `allowSoftware:false`: Chromium here did not report its software renderer as a "major performance caveat", so the refusal could not be seen working on this machine.
- The cost of uploading the real arrangement canvas (on a GPU it is a copy on the graphics card; in software it is a read-back).

## 6. Test page

Open `tools/glass-lab/engine-test.html` in Chrome (or the artifact), full window, and if possible inside the AudioLab desktop app.

- **Live readout**: frames per second, median / 95 % / worst frame time, CPU time spent in the engine's calls per frame, and per second: backdrop uploads, blur rebuilds, face redraws. "Underneath: still" or "playhead only" with the mixer moving must show 0 uploads and 0 rebuilds.
- **Measure (5 s)** gives a table to copy. **Compare presets** counts how many times the whole glass fits into one screen frame for each lens, blur and quality choice (same method as the Glass Bench).
- **Find the cost (about 30 s)** (added after the first Mac run, see section 7): first times each piece alone with the graphics card made to finish (upload, blur, faces, per layer), then runs the page in twelve steps from no glass to all glass and counts the frames that arrived on time.
- Switches: lens, blur, quality, face (bench look or Apple's matrix), Reduce transparency, Increase contrast, lose and restore the graphics context, each panel on or off.

## 7. First numbers from the user's Mac (26 November 2026)

M4, Chrome 157, 3840x2027 at 1x (7.8 MP), 240 Hz screen, worst case (arrangement scrolling, mixer moving, all panels, both layers):

- Measure: 109 fps, median 8.40 ms, 95 % 12.50 ms, worst 24.9 ms; engine calls 0.364 ms of CPU per frame; 220 uploads and 220 blur rebuilds per second (both layers, every frame).
- Compare presets: screen frame 4.20 ms (238 Hz) with the plain tint; every lens, blur and quality preset landed on 8.2 to 8.4 ms, that is every second screen frame.

What this says: the plain tint with the arrangement scrolling holds 238 Hz; any live glass in the worst case costs more than one 4.2 ms frame in total, so the page falls to every second frame. Lens and blur presets make no difference, as designed. That medium and low did not help pointed at work that was not capped: the device display under the floating layer repainted every frame and was uploaded and re-blurred every frame at any quality. That is fixed (the cap now covers fed canvases). Which piece is the expensive one (uploading a 7.8 MP canvas twice, the blur, or the faces) is not known yet; "Find the cost" was added to answer it.
