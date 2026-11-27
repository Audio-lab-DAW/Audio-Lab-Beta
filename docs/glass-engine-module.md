# AudioLab glass engine: the module (tasks G2, G2b and G2c, 27 November 2026)

The engine from `docs/glass-engine-plan.md` as a stand-alone file. **Version 2.1 (task G2c). Since 2.0 (task G2b) the engine draws its own backdrop on the graphics card. No canvas is copied.** This follows the user's Mac tests (plan 3.2 to 3.5). 2.1 follows the Mac run of the 2.0 test page (plan 3.6): two small savings, a canvas that can be only as large as its glass, a backdrop rate, and a test page that finds the cost; see section 7b. **Nothing in `index.html` or `desktop/` was changed, VERSION was not bumped.** Glass step 1 (task G3, docked surfaces) starts from here.

| File | What it is |
|---|---|
| `tools/glass-lab/glass-engine.js` | The engine. Plain JS, one file, no build step, no dependencies, about 51 KB with comments. Defines `window.AudioLabGlass`. Paste it into `index.html` or load it with a script tag. |
| `tools/glass-lab/engine-test.html` | Test page: AudioLab-sized panels over a scrolling arrangement; levels Glass, Light, Solid; background drawn on the GPU or small copy; live frame-share readout and counters; "Run" table like Glass Bench 3 (with Bench 3's own GPU path as a row); "Find the cost" table. Needs `glass-engine.js` beside it. |
| `tools/glass-lab/engine_test.py` | 151 headless checks (Python Playwright). `python3 tools/glass-lab/engine_test.py` |

Test page as an artifact (one file, engine inlined): https://claude.ai/artifact/HCdnmA3jbVsRyz4ifo7yvY

**Please run it on the Mac** (full window, other heavy tabs closed, and if possible inside the AudioLab desktop app): press "Run (about 45 s)", then "Find the cost (about 2 min)", then "Copy tables" and paste both. What must be true there: "Solid (page only)" and "Bench 3 path" reach 240, and the rows "drawn on GPU" deliver 100 % of the frames at 3840x2027 and 240 Hz, like Solid (plan 3.6 says how to read the rest). The cloud machine that built this has no graphics card, so **every frame rate measured here means nothing**; only correctness was checked.

## 1. How it works

1. **One WebGL2 canvas** per layer. Everything the engine draws is glass faces; where there is no glass the canvas is transparent.
2. **The backdrop is a list of rectangles, drawn by the engine itself**: the lane backgrounds, each clip as a flat rectangle in its track colour (body and title band), a selection tint, the playhead line. No waveforms, notes, text or grid: under frost they cannot be seen. The list is sent to the graphics card once (`setScene`) and again only after an edit.
3. The rectangles are drawn **straight into the quarter-size target** in **one instanced draw call**. Each small pixel gets exactly the share of each rectangle that covers it, so the result equals the full-size picture reduced with a box filter: thin lines and slow scrolling do not shimmer.
4. **One dual-Kawase blur pyramid** is built from that target, then **every glass surface is one quad in one shader**: rounded-rectangle distance field, rim refraction, face colour, tint, rim light, shadow. The shader reads only the blurred backdrop, never the canvas it draws to, so **glass never samples glass**.
5. **Only what changed is redone.** Scroll and zoom are one uniform, the playhead is one uniform; both redraw the backdrop and the blur (cheap: Bench 3 held 240 Hz at 7.8 megapixels doing this on every frame) but **send nothing**. Moving, resizing, fading a panel redraws the quads only. With nothing changed, `render()` returns at once and makes no GL call.
6. **Never a full-size upload.** The other route, a canvas as the backdrop (`setBackdrop`), is the fallback and the route for other sources (piano roll, device displays): the canvas is first reduced to a quarter of its size on screen on a small 2D canvas, and only that small copy is uploaded, only after `markDirty()`, at most 60 times per second.

`backdrop-filter` is used nowhere.

### Levels (plan 3.5)

| Level | What | Backdrop target | Backdrop refresh | Lens |
|---|---|---|---|---|
| **Glass** (default) | the full engine | a quarter of the canvas (in CSS pixels) | every change, every frame if needed | preset (default Wide 45) |
| **Light** | the same engine, cheaper | an eighth | at most 30 per second | off |
| **Solid** | no glass: plain panel colour with fine noise | none | none | none |

Solid is also what a machine without WebGL2 gets (drawn with the 2D context), what Reduce Transparency gives, and what shows while the graphics context is lost. Panels move at the screen rate at every level. Light's blur is a little stronger than Glass at the same blur preset (it starts from a smaller picture); that hides the 30 per second refresh.

### Numbers used (from plan 2.2; numbers only, no code from the reverse-engineering repos)

- **Lens band** = min(short side / 4, preset maximum): Off, Fine 12 px, Apple 20 px, **Wide 45 px** (Wide uses short side / 3). Quarter-circle profile. With Wide a 48 px transport gets 16 px, a 32 px pill about 11 px, the mixer 45 px. The middle of a large panel is flat. **Default: Wide** (the user's pick).
- **Blur**: **Light** (default, the user's pick), Regular, Heavy = the pyramid goes down to 1/4, 1/8, 1/16 of the size at level Glass.
- **Face**: saturation 1.3, then the panel tint. Kinds differ in how much tint: docked and window 0.5, menu and sheet 0.6, pill 0.45.
- **Rim light**: two-sided at +45° and −135°, 1.6 px wide, as in the bench.
- **Shadow** (floating kinds only): offset (0, 8), radius 4 + 20t, opacity 0.04 + 0.56t, t = clamp((short side − 64) / 96, 0, 1).

Not Apple's numbers by default, on purpose: the face colour matrix "0.125 / 1.125" is an option (`face:{sat:1.3, mul:1.125, add:0.125}` or `setFace`), and rim light strength stays at the bench values.

## 2. API

```js
const g = AudioLabGlass.create(canvas, opts);     // canvas: an empty <canvas>, positioned by the app
g.setScene({                                      // the backdrop, as rectangles (once, and again after an edit)
  rect: [0, AY, w, h - AY], originX: X0,          // where the arrangement shows on the engine canvas; where scene x = scrollX lands inside it
  lanes: [{y, h, color}],                         // track lane backgrounds
  clips: [{x, y, w, h, color, titleH, selected}], // x and w in beats, y and h in pixels
  scrollX, scrollY, zoom, playheadX, bg });
g.addPanel({id:'tr', rect:[0, 952, 1600, 48], radius:0, kind:'docked'});
// per frame, only what moved:
g.setPlayhead(beat);                              // one rectangle, one uniform
g.setView({scrollX, scrollY, zoom});              // one uniform; the clip list stays on the graphics card
g.render(now);                                    // draws only what changed; returns true when it drew
```

Added in 2.1 (nothing else in the API changed):

```js
g.setOrigin(x, y);          // the canvas does not start at the top left of the space the rectangles are given in (a small canvas, below)
g.setBackdropRate(120);     // draw the backdrop again at most 120 times per second; panels still move on every frame. 0 or null = the level decides
g.info.origin               // [x, y]
g.debug.set({aa:false});    // test page only: rectangles with hard edges
g.debug.set({freeze:true}); // test page only: a backdrop change redraws the faces but not the backdrop
```

`create(canvas, {backdropRate: 120})` sets the rate at the start. `info.sceneRects` is one less than in 2.0: the background colour is no longer a rectangle.

**A canvas only as large as its glass.** By default the engine canvas covers the whole window and every rectangle is relative to it. For floating glass that is wasteful: a 1100x430 mixer window on a 3840x2027 canvas clears, draws and composites 13 times more pixels than it shows. Instead: make the canvas the size of the window plus 34 px on every side (its shadow), in steps of 8 px; put it at the window's place with CSS (`transform: translate(x, y)`); call `g.setOrigin(x, y)` with the same whole-pixel numbers; keep giving panels, the scene `rect`, the backdrop `rect` and flats in window coordinates, exactly as before. When the window is dragged: move the canvas, `updatePanel`, `setOrigin`, `render`. The size stays, so nothing is allocated again. Several floating panels far apart need one canvas over all of them (then little is saved) or the rule "one floating window at a time gets the fitted canvas". The test page does this behind the switch "floating canvas only as large as its glass". Whether it is needed is for the Mac to say (plan 3.6).

Panel rectangles and `rect` are in **CSS pixels relative to the engine canvas** (or, with `setOrigin`, relative to the point the origin is measured from), as `[x,y,w,h]`, `{x,y,w,h}` or a DOMRect. Colours are `[r,g,b]` or `[r,g,b,a]` (0 to 1), `'#rgb'`, `'#rrggbb'`, `'#rrggbbaa'`, `'rgb(...)'` or `'rgba(...)'`.

### The scene

| Field | Meaning | Default |
|---|---|---|
| `lanes: [{y, h, color}]` | lane backgrounds, full width; `y` scrolls with `scrollY` | none |
| `clips: [{x, y, w, h, color, titleH, selected, alpha}]` | `x`, `w` in scene units (beats); `y`, `h` in pixels. Body = colour at `alpha`, title band = full colour, `selected` adds a tint | none |
| `playheadX` | in scene units; `null` = no playhead | null |
| `scrollX` | scene units (the app's `V.x`) | 0 |
| `scrollY` | pixels (`V.y`) | 0 |
| `zoom` | pixels per scene unit (`V.ppb`); `zoomY` scales lane and clip heights | 1 |
| `rect` (or `viewW`, `viewH`) | where the arrangement shows on the engine canvas; outside it the backdrop is `backdropColor` | whole canvas |
| `originX`, `originY` | where scene x = `scrollX`, y = `scrollY` land inside `rect` (the app's `X0`) | 0 |
| `bg`, `titleH` (14), `bodyAlpha` (0.533, the app's `'88'`), `selColor`, `playheadColor`, `playheadW` (1) | look of the proxy | |

Screen position of a clip: x = rect.x + originX + (clip.x − scrollX) · zoom, y = rect.y + originY + clip.y − scrollY.

`setScene` keeps what is left out. **Passing `lanes` or `clips` (or a look value) sends the rectangle list again; everything else is a uniform.** Send all clips of the song, not only the visible ones: scrolling and zooming then never send anything, and rectangles outside the view cost nothing worth counting (the graphics card clips them). 24 bytes per rectangle; a song with 2000 clips is about 100 KB, sent once per edit.

| Call | What it does | What it costs |
|---|---|---|
| `create(canvas, opts)` | Makes the engine. Falls back by itself when WebGL2 is missing. | once |
| `setScene({...})` | The backdrop as rectangles (see above). `setScene(null)` removes it. | list sent only if lanes, clips or look changed |
| `setPlayhead(x)` | Moves the playhead. Same value: nothing. | backdrop + blur, nothing sent |
| `setView({scrollX, scrollY, zoom, zoomY, rect, originX, originY})` | Scroll, zoom, layout. Same values: nothing. | backdrop + blur, nothing sent |
| `addPanel({id, rect, radius, kind, ...})` | Adds a surface (same id again: updates it). | quads |
| `updatePanel(id, {rect, radius, kind, visible, opacity, z, ...})` | Changes a surface. Unchanged values cost nothing, so it can be called every frame. | quads |
| `removePanel(id)`, `hasPanel(id)` | | quads |
| `setLevel('glass'|'light'|'solid')` | See the table above. | backdrop + blur |
| `setLensPreset('off'|'fine'|'apple'|'wide')` | | quads |
| `setBlurPreset('light'|'regular'|'heavy')` | | backdrop + blur |
| `setBackdrop(source, {rect})`, `markDirty()` | **Small-copy route**: a canvas (or OffscreenCanvas, image, video) as the backdrop. Reduced to quarter size before the upload; uploaded only after `markDirty()`, at most `copyRate` (60) times per second at Glass, 30 at Light. `setBackdrop(null)` goes back to the scene. | small upload + blur |
| `setFlat(id, {rect, radius, color or source})`, `markFlatDirty(id)`, `removeFlat(id)` | A flat picture of DOM that floating glass covers (section 4). A fed canvas (a device display) goes the small-copy route too. | flat blur (+ small upload) |
| `setAccessibility({reduceTransparency, increaseContrast})` | `true` / `false` forces it, `null` follows the system. | quads |
| `setFace({sat, mul, add})` | Face colour matrix. | quads |
| `resize(cssW, cssH, dpr)` | Called by a ResizeObserver unless `autoResize:false`. | backdrop + blur |
| `render(now)` | Does the work. `now` = the frame time from requestAnimationFrame. | only what changed |
| `destroy()` | Frees everything and gives the context back. | |

The last of `setScene` and `setBackdrop(source)` decides where the backdrop comes from (`g.info.source`: `'scene'`, `'copy'` or `'none'`; with none the glass is the plain tint). `setQuality` still exists for older callers (3 and 2 = Glass, 1 = Light, 0 = Solid).

Read-only: `g.mode` (`'gl'` or `'fallback'`), `g.reason` (`'no webgl2'`, `'lost'`, `'shader'`, `'forced'`), `g.pending` (a capped backdrop refresh is waiting: keep calling `render()`), `g.info` (sizes, level, source, presets, pyramid levels, rates, number of rectangles, flags), `g.gl`, and **`g.stats`**:

| Counter | Counts | Should be |
|---|---|---|
| `sceneSends` | rectangle lists sent to the graphics card | 1 at start, +1 per edit; **0 while scrolling or playing** |
| `sceneDraws` | backdrop drawn on the graphics card | one per frame in which the playhead or the view moved (30 per second at Light) |
| `uploads` | canvas copies of the backdrop | **0 on the scene path** |
| `uploadPixels` | size of the largest canvas copy so far | a sixteenth of the source's area on screen, never its full size |
| `flatUploads` | small copies of fed display canvases | only while such a display repaints under floating glass |
| `pyramids`, `flatPyramids`, `draws`, `skipped`, `lost`, `restored` | blur builds, face redraws, idle calls, context losses | |

Panel options beyond rect, radius and kind: `visible`, `opacity` (0 to 1, for menu fades), `z` (drawing order), `over:'flats'`, `tint:[r,g,b]`, `tintAmount`, `shadow` (0 = none, 1 = Apple's), `lens:false`.

Main `opts`: `level`, `lens`, `blur`, `tint` and `solid` (panel colours, default rgb 22 28 42), `backdropColor`, `copyRate` (60; 0 = no cap), `copyQuality` (`'low'`, the `imageSmoothingQuality` used when a canvas is reduced; see section 5), `maxDpr` (2), `face`, `rim`, `kinds`, `allowSoftware` (false: refuse a software renderer where the browser reports one), `regionCull` (true), `autoResize` (true), `onFallback(on, why)`, `requestRender()` (the engine asks for a frame after a restore or a system setting change), `fallbackCanvas`, `reduceTransparency`, `increaseContrast`.

### Kinds

| kind | for | shadow | tint | moves? |
|---|---|---|---|---|
| `docked` | track headers, transport, tab band, device panel | none | 0.5 | no |
| `window` | mixer and other floating windows | yes | 0.5 | yes |
| `sheet`, `menu` | sheets, menus | yes | 0.6 | yes |
| `pill` | small floating controls | faint (by size) | 0.45 | yes |

"Moves: no" matters for speed: when every visible panel is docked, the backdrop and the blur are worked out **only for the screen area under those panels** (plus a safety margin). As soon as a floating panel is visible the whole picture is done, so that moving it never needs a rebuild.

Sizes are counted in **CSS pixels**: on a 2x (Retina) screen the backdrop target is an eighth of the device pixels at Glass. The blur looks the same on every screen and a Retina screen pays no more than a normal one.

### Fallbacks and accessibility

- **WebGL2 missing**: the Solid look, drawn on the same canvas with the 2D context: each panel a rounded rectangle in the solid panel colour with fine noise and a thin border. Redrawn only when a panel changes. All scene calls are harmless.
- **Context lost**: the engine puts a 2D canvas in the same place (same class, position, size, z-index), draws the Solid look there, hides the GL canvas and calls `onFallback(true, 'lost')`. When the browser restores the context it rebuilds shaders, buffers and pyramids, **sends the rectangle list again from its own copy** (the app does nothing), removes the extra canvas, calls `onFallback(false)` and `requestRender()`.
- **Reduce Transparency** (`prefers-reduced-transparency: reduce`): the Solid look, no backdrop work at all.
- **Increase Contrast** (`prefers-contrast: more`): tint at least 0.82, no lens, no rim light, a clear light border.
- Both follow the system live and can be forced by the app.

## 3. What makes it cheap

- Nothing is uploaded: the backdrop is drawn where it is needed, at a sixteenth of the pixels.
- No work without a change: no draw, no blur pass.
- A scroll, a zoom or a playhead step is one uniform. The clip list is sent once per edit.
- One backdrop and one pyramid for all glass in a layer, instead of one capture and blur per element as `backdrop-filter` does.
- Docked-only layouts work only on the area under glass; that area is worked out when a panel changes, not per frame (2.1).
- The scene's background colour is the clear, not a rectangle: each small pixel is cleared once (2.1).
- The rectangle shader's edge smoothing is arithmetic on the rectangle's own edges: one result per pixel, no texture lookup, no extra samples.
- A canvas may be only as large as its glass (`setOrigin`, 2.1): all work of that layer shrinks with it.
- The lens is one texture lookup per pixel at any width; the shadow is computed in the same quad.
- A layer with no visible panel does nothing.

## 4. How to integrate (plan 3.1, 3.4)

**Step 1, docked surfaces (task G3).**

1. Put one canvas where `#arrBack` sits (before `#arr`), covering the area the docked glass covers; `pointer-events:none`. It takes the place of `#arrBack` **and** `#arrBlur`; `gbLayout` / `gbCopy` / `gbTick` and `abDraw` are not needed on this path.
2. `g = AudioLabGlass.create(canvas, {requestRender: () => /* ask the app's frame loop for a frame */, onFallback: (on) => /* nothing to do: the engine shows Solid by itself */})`. Level from the app's glass setting: `g.setLevel('glass' | 'light' | 'solid')`.
3. **Feed the scene from the same clip geometry `drawArr` uses**, in one small function (call it `glassScene()`), built from the values `drawArr` and `clipGeom` already compute:

   ```js
   function glassScene(){            // called only when the clips or the layout changed, never per frame
     const lanes = [], clips = [];
     S.tracks.forEach((t, i) => { if (HIDT.has(t)) return;
       lanes.push({y: TRY[i], h: V.th, color: t.id === selT ? TH.laneSel : (i % 2 ? TH.lane1 : TH.lane0)});
       for (const c of t.clips) clips.push({x: c.start, w: c.len, y: TRY[i] + 2, h: V.th - 5,   // clipGeom without scroll and zoom
         color: t.color, titleH: V.th >= 40 ? 14 : 0, selected: /* the app's selection test for c */ false});
     });
     g.setScene({lanes, clips, bg: TH.bg, rect: [0, AY, w, h - AY], originX: X0,
       scrollX: V.x, scrollY: V.y, zoom: V.ppb, playheadX: curDisp(), playheadColor: phCfg().c, playheadW: phCfg().w});
   }
   ```

   Clip `x` and `w` are in **beats** (`c.start`, `c.len`), so horizontal zoom (`V.ppb`) is a uniform and needs no new list. `y` and `h` are pixels in the unscrolled track stack (`TRY[i]`), so vertical scroll (`V.y`) is a uniform too.
4. **When to call what:**
   - `glassScene()`: after an edit that adds, removes, moves, resizes or recolours a clip; selection change; track added, removed, folded, reordered; track height (`V.th`) or lane change; theme change. In practice: where the app already marks the arrangement cache (`ARRC`) stale for a reason other than scroll, zoom or playhead. Preview mapping of clip starts (`PREVMAP`) also counts as an edit.
   - `g.setView({scrollX: V.x, scrollY: V.y, zoom: V.ppb})`: in `drawArr` on every full repaint (it is free when the values did not change), plus `rect` / `originX` when the layout changed (`X0`, `AY`, window size).
   - `g.setPlayhead(curDisp())`: in the playhead-only branch of `drawArr` (`phOnly`) and in the full one. One uniform; the clip list is not touched.
   - **Never** `setBackdrop(arr)` with the arrangement canvas on this path, and no `markDirty()`.
5. For `#hglass`, `#tr`, `#fxband`, `#fxglass`: `g.addPanel({id, rect, radius, kind:'docked'})`, and `updatePanel` from the existing layout code (`gbLayout`). Those elements then carry **no `backdrop-filter`**, only border and content.
6. Call `g.render(t)` once per frame from the existing frame loop. It is free when nothing changed, so it needs no guard. While `g.pending` is true (Light level, a refresh is waiting) keep the loop running.
7. Check on the Mac with `g.stats`: while scrolling and playing, `uploads` stays 0 and `sceneSends` does not grow.

What the proxy leaves out on purpose: waveforms, notes, clip names, grid lines, the ruler, automation lanes, the loop brace, recording overlays. If one of them turns out to be visible under glass on the Mac (for example a long recording overlay), add it as more rectangles in `glassScene()`; do not switch to a canvas copy.

**Glass over other things than the arrangement** (piano roll, a device display, the browser): use the small-copy route for that source: `setBackdrop(pianoCanvas, {rect})` on that layer's engine and `markDirty()` where it repainted, or, for a display under a floating window, `setFlat(id, {rect, source: displayCanvas})` with `markFlatDirty(id)`. The engine reduces it to quarter size before the upload and caps the rate; the app never needs to make a small copy itself.

**Step 2, floating windows, sheets, menus.** The engine canvas of step 1 lies under the DOM of the docked panels, so a floating face drawn there would be covered by knobs. Use a **second engine on a second canvas directly under the floating layer** (above the docked DOM):

1. Same scene: call `setScene` / `setView` / `setPlayhead` on both engines (two small lists, two uniforms). The second engine does nothing while none of its panels is visible.
2. Windows, menus, sheets: `addPanel({kind:'window' | 'menu' | 'sheet', over:'flats', ...})`.
3. Where floating glass can cover DOM, feed the flat picture: `setFlat('fxglass', {rect, color:[r,g,b,1]})` for each docked panel (its average glass colour), and `setFlat('disp1', {rect, radius, source: displayCanvas})` for device displays, with `markFlatDirty` when such a display repainted. Panels with `over:'flats'` see the backdrop plus these flat pictures; all others do not. Moving the window rebuilds nothing.
4. Remove the nested blurs in the mixer (`.fwh`, `.ck`).

The test page is built exactly this way (two engines, docked and floating, both fed the same scene).

**Settings.** The app's three levels map one to one to `setLevel('glass' | 'light' | 'solid')`; automatic stepping-down goes Glass, Light, Solid. Lens and blur presets map to `setLensPreset` and `setBlurPreset` (defaults Wide and Light need no call).

**Step 3** (remove `rfAttach`, `rfBuild`, `rfMap`, `rfStyle`, the `feImage` lens, and every `backdrop-filter`) only after the user confirms on the Mac.

## 5. What was tested (headless, cloud machine)

`python3 tools/glass-lab/engine_test.py`: **151 checks, all pass**, no console errors or warnings (126 before task G2c). `python3 tools/glass-lab/devices_lab.py` (the display-first devices lab, which uses the engine through the small-copy route): 17 of 17. The cloud machine has **no GPU** (a software renderer), so **its frame rates mean nothing**; only correctness and the counters were tested.

- **Uploads == 0 on the scene path**: scrolling and playing for one second at a simulated 240 frames per second with a panel moving: backdrop drawn 240 times, 0 canvas uploads, 0 lists sent, 240 panel redraws. On the test page (1x and 2x): scrolling + mixer moving and playing + mixer moving give 0 uploads and 0 sends on both layers.
- **A playhead-only change does not send the clips again**: 20 playhead steps give 20 backdrop draws and 0 sends; the same for 20 scroll steps and 20 zoom steps; setting a value it already has does nothing; an edit sends once.
- **The GPU-drawn backdrop is the right picture**: title band, body, lane, half-transparent body, background, selection tint and playhead have the right colours and places; scroll, zoom, vertical scroll, view rectangle and origin move them correctly; a scene and a small copy of the same picture give pixel-identical glass (Glass and Light); on the test page the two routes differ by under 2 of 255 on average (the copy also contains note marks and grid, the scene leaves them out).
- **Rim bends, middle flat**: the place each glass pixel is taken from was read back, on both routes. The shift follows the quarter-circle profile on the left, top and right edges for Fine, Apple and Wide 45 (worst error 1 px); nothing bends beyond the band; the middle is the same pixel with every lens preset; band width follows the panel.
- **No corner seam**: the bending direction is continuous across the corner diagonal for Apple and Wide, radius 0, 6 and 16.
- **Middle frosted**: detail under glass (11 px clips every 23 px) drops to 28 % of the picture with blur Light, 13 % Regular, 2 % Heavy at level Glass, 14 % at level Light; the same strength on a 2x screen as on a 1x screen.
- **Levels**: Glass (lens Wide, quarter size, every frame), Light (lens off, an eighth, 30 backdrop draws per second, panels still 240), Solid (no backdrop work); defaults are Glass, Wide 45, blur Light.
- **Small-copy fallback**: a 1600x1000 canvas over an 800x500 engine goes up as 200x125 (never full size), 100x63 at Light; with the picture dirty on every frame at 240 per second: 60 uploads at Glass, 30 at Light; no upload without `markDirty()`; a 640x480 display shown at 120x90 goes up as 30x23; fed displays follow the same cap.
- **No glass on glass**, **dirty logic**, **working only under docked glass** gives identical pixels (both routes, both levels, three blur presets), **flat picture** for glass over DOM, **shadow**, **opacity**, **face colour**.
- **2.1, small canvas (`setOrigin`)**: a 372x272 canvas placed at (264,124) draws the same window, shadow and backdrop as an 800x600 canvas, within 1 of 255 (scene and copy route, over the backdrop and over flats); moved with its window: same picture, no upload, no list sent; an origin off the small-pixel grid differs only within the blur (mean under 1.5 of 255). On the test page at 1x and 2x: the fitted mixer canvas (1168x504 instead of 1600x1000) looks the same within 1 of 255, travels with the window while scrolling with 0 uploads and 0 lists, and switching it off gives the earlier picture exactly.
- **2.1, background as a clear**: right colour inside the view rectangle (also half-transparent), backdrop colour outside; a new background colour is one backdrop draw and no list.
- **2.1, `setBackdropRate`** at a simulated 240 frames per second: 240 backdrop draws by default, 120 and 60 when asked, panels redrawn 240 times in each case; a level with a lower rate keeps it.
- **2.1, area under docked glass** worked out only on change: after moving, resizing and removing docked panels the pixels are identical to working on everything.
- **2.1, test page**: "Solid (page only)" has no engine canvas in the page and does not call the engine; "Bench 3 path" draws frosted headers and mixer with Bench 3's own code and leaves no canvas or context behind; Run has 8 rows; Find the cost has 25 rows and puts every switch back.
- **Reduce Transparency and Increase Contrast** through the emulated system settings and through `setAccessibility`.
- **Context loss and restore** (`WEBGL_lose_context`), scene path and copy path: Solid look appears on a 2D canvas in the same place, panels still move, after restore the glass is pixel-identical to before, the rectangle list was sent again once by the engine itself, four losses in a row, no canvases left behind.
- **WebGL2 missing**: Solid look on the same canvas, every API call harmless.
- **Test page** at 1x and 2x: screenshots show frosted headers and mixer, each track row under the mixer in the colour of the clips really there, an untouched arrangement outside glass, the menu over the device panel showing the flat panel colour, lens on/off differing in the rim only; Light and Solid; the small-copy route (400x250 uploads for a 1600x1000 window, also at 2x); the Run table has 0 uploads and 0 sends on the "drawn on GPU" rows; context-loss buttons; phone width without sideways scroll.

Not tested here, for the user's Mac and for Windows:

- **Frame rate and real GPU cost.** This is the point of the Mac run. Bench 3 says the recipe holds 240 Hz at 7.8 megapixels; the module adds exact edge coverage in the rectangle shader and a second layer. The first Mac run of the engine page (plan 3.6) kept 67 % while scrolling and 93 % while playing; which piece costs is what "Find the cost" on the 2.1 page measures.
- **Whether the fitted canvas or a backdrop rate is needed**, and which. Both are built and draw correctly; neither is a default.
- **The small-copy route on a GPU.** The reduction uses the browser's fast setting (`copyQuality: 'low'`, the one Bench 3 measured). `'medium'` would be smoother for thin lines but may cost more; not measured.
- A real driver context loss (GPU process restart, sleep and wake), Windows drivers.
- `allowSoftware:false`: Chromium here did not report its software renderer as a "major performance caveat", so the refusal could not be seen working on this machine.

Known limits of the proxy: where two rectangles end inside the same small pixel (two clips that touch, two lanes that meet between pixel rows) a trace of the colour underneath shows through, at most a quarter of one small pixel; under frost it is not visible in the screenshots. Lanes are full width; clips cannot have rounded corners.

## 6. Test page

Open `tools/glass-lab/engine-test.html` in Chrome (or the artifact), full window, and if possible inside the AudioLab desktop app.

- **Level**: Glass, Light, Solid. **Background from**: rectangles drawn on the graphics card (default), or a small copy of the canvas (the fallback), to compare look and cost.
- **Live readout**: frames per second and the **share of the screen's frames that were delivered**, median / 95 % / worst frame time, and per second: background drawn on the GPU, **canvas uploads (must be 0)**, clip lists sent (must be 0), face redraws; CPU time in the engine's calls per frame.
- **Run (about 45 s)** gives a table to copy, like Glass Bench 3: Solid as in Bench 3 (page only: no engine canvas, plain panels; it sets the screen rate); Solid drawn by the engine; Light and Glass drawn on the GPU while scrolling; Glass while playing; Light and Glass with the small copy; **Bench 3 path** (Bench 3's own GPU code and five panels, on this page). Columns: fps, frames delivered, median, 95 %, worst, and the three counters.
- **Find the cost (about 2 min)**: Glass while scrolling, 25 rows with one piece switched off at a time: anti-aliasing off; background 120 and 60 per second; background frozen (faces still drawn); engine idle (canvases on screen, nothing drawn); floating layer off; docked layer off; each panel off in turn; scene with 0 clips; page scrolling off (the 2D arrangement stands still, the glass still scrolls its backdrop); mixer not moving; lens off; engine canvases at half size; only the mixer floating, with a full-window and with a fitted canvas; Bench 3 path; Glass playing. The last column is the change in frames delivered against "everything on". Plan 3.6 has the table that says what each jump means.
- **Copy tables** copies both.
- **Time the pieces**: each piece alone with the graphics card made to finish (send the list, draw the background + blur, draw the faces, the small copy).
- Switches: what moves underneath (scrolling, playing, still), move the mixer, floating canvas only as large as its glass, a moving device display (a small copy per refresh, off by default), lens, blur, face, Reduce transparency, Increase contrast, lose and restore the graphics context, each panel on or off.

## 7. What changed from engine 1.0 (task G2) to 2.0 (task G2b)

| 1.0 | 2.0 |
|---|---|
| Backdrop = the arrangement canvas, uploaded full size after `markDirty()` | Backdrop = rectangles drawn on the GPU (`setScene`, `setPlayhead`, `setView`); no upload |
| `setBackdrop` uploaded the canvas as it was | `setBackdrop` reduces to quarter size first; at most 60 uploads per second; fallback and other sources only |
| Quality 3, 2, 1, 0 (half or quarter size, 60 or 30 per second, static) | Levels Glass, Light, Solid; always quarter size or smaller; `setQuality` kept as an alias |
| Defaults lens Apple 20, blur Regular; Wide was 40 px | Defaults lens Wide 45, blur Light |
| Fed display canvases uploaded full size | Fed display canvases reduced to quarter size, same cap |
| Counters `uploads`, `pyramids`, ... | plus `sceneSends`, `sceneDraws`, `uploadPixels` |

## 7b. What changed from engine 2.0 (task G2b) to 2.1 (task G2c)

The reason, the Mac table and the reading are in plan 3.6. API: nothing removed or changed; `setOrigin`, `setBackdropRate`, `info.origin`, `debug.set` and the option `backdropRate` are new.

| 2.0 | 2.1 |
|---|---|
| Scene background colour = a blended rectangle over the whole small target, on top of a clear | The clear itself (one clear per pixel); `info.sceneRects` is one less; a new `bg` is no longer a new list |
| Area under docked glass worked out on every frame (small arrays thrown away 240 times per second) | Only when a panel, the size or the blur changes |
| The canvas had to cover the whole space of the rectangles | `setOrigin(x, y)`: a canvas only as large as its glass, moved with its window |
| Backdrop rate fixed by the level (Glass: every change) | `setBackdropRate(n)` caps it (off by default) |
| Comment said the rectangle shader gives "the same picture as ... a box filter" | Same shader; the comment now says what it costs: arithmetic on the rectangle's edges, one result per pixel, no lookups |
| Test page: Solid kept two engine canvases on screen; 6 rows | Solid as in Bench 3; Bench 3's own GPU path as a row; Find the cost; readout paused during runs |

**For the task that ports this into `index.html`** (GS1 integrated 2.0.0): replace the engine text with `tools/glass-lab/glass-engine.js` 2.1.0 as it is. Nothing the app calls has changed. Do not use `setOrigin` or `setBackdropRate` in the app until the Mac run in plan 3.6 says which one is needed.

## 8. History: first numbers from the user's Mac with engine 1.0 (26 November 2026)

M4, Chrome 157, 3840x2027 at 1x (7.8 MP), 240 Hz screen, worst case (arrangement scrolling, mixer moving, all panels, both layers):

- Measure: 109 fps, median 8.40 ms, 95 % 12.50 ms, worst 24.9 ms; engine calls 0.364 ms of CPU per frame; 220 uploads and 220 blur rebuilds per second (both layers, every frame).
- Compare presets: screen frame 4.20 ms (238 Hz) with the plain tint; every lens, blur and quality preset landed on 8.2 to 8.4 ms, that is every second screen frame.

What this says: the plain tint with the arrangement scrolling holds 238 Hz; any live glass in the worst case costs more than one 4.2 ms frame in total, so the page falls to every second frame. Lens and blur presets make no difference, as designed. That medium and low did not help pointed at work that was not capped: the device display under the floating layer repainted every frame and was uploaded and re-blurred every frame at any quality. That is fixed (the cap now covers fed canvases). Which piece is the expensive one (uploading a 7.8 MP canvas twice, the blur, or the faces) is not known yet; "Find the cost" was added to answer it.

The answer came from Glass Bench 2 and 3 (plan 3.3 and 3.4): the expensive piece was copying the full-size canvas into the graphics card. Engine 2.0 (section 1) no longer does that.
