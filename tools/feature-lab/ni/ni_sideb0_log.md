## 28 November 2026, v{V}: the Fractals export flake found and fixed (lane D, for task RG; one line in lane K's `renderMix`)

The scheduling chat asked lane D to fix this first (task RG's entries of 28 November): in about 1 render in 8, "Fractals Bass, master put back to 0 dB" of `tools/engine-tests/export_same.py` gave -26.74483 dB (a6774faed0a9) instead of -25.48699 dB (09e0415bec5e). NI-6 (v0.269) was the first suspect. It was not NI-6: the log shows the same value on v0.215 (task AI's entry), before any lane D code.

### The cause
- The Bass of Fractals goes through the **Sidechain** effect (`side`: a pump locked to the beat). In an offline render it is built in sync with the global `SIDE_B0`, the beat the render starts at.
- `renderMix` set `SIDE_B0=b0` and then awaited `wlLoad(oc)` (loading the worklets into the new offline context). The pump is built after that await.
- Any other `renderMix` that starts during the await overwrites `SIDE_B0`. The overview map's background render (`renderMix(..., fast)` in pieces after the song loads) does that for a few seconds after start-up, and the pieces of `renderMixChunked` run two or three at a time.
- The pump was then built on another render's start beat: the Bass ducked on the wrong phase. A shift by a whole number of beats does not show (the pump repeats every beat), so it only flaked when the other start beat was off the beat grid.
- Shown on the old file: within one page, the 4th of 4 identical Bass renders gave -26.74483 dB (12 pages, 1 bad); the two renders are the same up to sample 5023, then differ on every beat. Setting `SIDE_B0` to 64.5 or 7.37 while a render waits gives -27.43 and -26.12 dB.

### The fix
- `renderMix` sets `SIDE_B0=b0` again right after the await; from there to `startRendering()` the build is synchronous, so nothing can come in between. One statement, in lane K's `renderMix` (the scheduling chat asked lane D to fix it; lane K: please keep it if you rebuild `renderMix`).
- NI-7's own render (`NI_jourRender`, lane D) now also sets `SIDE_B0` before it makes its context, so the Volume Shaper's offline origin (`VMOF`, read when the context is made) is its own.
- Edit script `tools/feature-lab/ni/ni_sideb0.py`, test `tools/ui-tests/taskNI_sideb0.py`.

### Proof
- **`export_same.py` 20 of 20 runs identical** on the 9 repeatable lines (Fractals Kick and Bass at -10 dB and at 0 dB, Saw, Pad, Acid, Wavetable, Venom): Bass at 0 dB -25.48699 dB (09e0415bec5e) in all 20. Plant, Sampler, Sampler grains and Drum kit move from run to run as before (free-running randomness, listed as not repeatable in `gate.py`).
- The stress repro (4 Bass renders straight after start-up, 14 pages): 56 of 56 renders the reference (the old file: 1 bad in 48).
- `taskNI_sideb0.py` forces the race three ways (`SIDE_B0` changed right after the call, changed while the worklets load, a real second render off the beat grid started in the same task): **the old file fails all three** (-27.43, -26.12, -26.12 dB), the fixed file passes 6 of 6.

### What changes for the user
- **Exports of songs with the Sidechain effect that are longer than 32 beats can change**, toward the right sound: a long export is rendered in pieces two or three at a time, and a piece could get its neighbour's start beat. Fractals' Bass from beat 0 to 160, compared piece by piece with one unbroken render: before, the piece at beats 120 to 144 differed by up to 0.1 (the pump on the wrong phase); now every piece is within 0.01 like the others (the usual seam of the pieces, from compressors starting fresh). The release gate's export lines (32 beats in one render) are unchanged.
- Nothing else in the sound changes; the live playback never used this path.
