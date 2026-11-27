# The project's state and its edit protocol (task NB-R7, review RN5 A10)

Your picks say the engine keeps all the state and the interface is a view on it (U4f), so that a native look at 240 Hz can come later without moving anything. The review (A10) asked for the design before the engine grows further: who owns the project, how an edit travels, how undo works, how a song that is half web and half native stays in step, and who saves. This is that design, with a working prototype on both sides and the proof the review asked for: 1,000 random edits and undos, page and engine equal after every one.

Files: the engine's side `native/engine/doc/doc.h` (and the test tool `aldoc`), the page's side `native/bridge/doc-sync.js`, the proof `tools/native-lab/doc_sync_test.js` with the three built-in songs as the app holds them (`tools/native-lab/ref/doc/`). Nothing here is in the app yet; the hook goes in with N2c (below).

## 1. The document

The document is the app's project object `S` exactly as JSON carries it: tempo, tracks, clips, notes, devices and their settings, sections, the master chain, automation. It is the same thing the app already snapshots for its undo (`JSON.stringify(S)` at every `pushUndo`) and saves in `.audiolab` files, so nothing has to be invented or converted.

Not in it, on purpose:
- the view (`V`: zoom, scroll, open windows): each view keeps its own;
- the audio of recordings and imported files: the document names them by id (`buf`), the samples stay in the app's store until projects move into real files (RL1b), and later in files beside the project;
- the transport position and what is playing: a stream of its own, not an edit.

Plug-in state (VST3 blobs, N4) goes in as a base64 string with a version, class id and plug-in version (A11, NB-R9). When those get large (Kontakt saves megabytes), the document holds a content hash and the bytes live in a side store, so an edit to one knob never carries the blob.

## 2. Who owns it, stage by stage

| When | Owner | What travels |
|---|---|---|
| Now to the end of stage 3 (N2c, N3) | **the page**. The app keeps changing `S` as it does today (327 places call `pushUndo`) | at every `changed()` the page sends the difference as one edit; the engine keeps an exact copy, checks every edit and refuses one that does not fit |
| From N4 (plug-ins live in the engine) | **the engine**. Plug-in windows, automation recording and control surfaces change the project from the engine's side | the same edits from the page, and `doc.change` events from the engine; undo and redo are done by the engine (`doc.undo`) |
| Stage 4 (native screens) | the engine | a native view uses the same messages as the page; the page and a native window can both be open |

The protocol is the same in all three rows; only the side that presses undo moves. That is what keeps the 240 Hz native look possible without a second move: the state never has to be pulled out of the page again.

**Why diffs and not operations at every call site.** Rewriting 327 call sites to send operations would mean touching nearly every feature of `index.html`, while the design chain is still working in it. Comparing `S` with the copy last sent gives the same operations with one hook in `changed()`, `pushUndo` and `restore`, and it is exact by construction: whatever the app did, the edit is the difference. The cost is measured below (section 8); a site that is hot (a knob drag) can later pass a hint of where it changed.

## 3. Edits

An edit is a short list of operations, applied whole or not at all:

| Operation | Meaning |
|---|---|
| `{"o":"set","p":[...],"v":new,"w":old}` | put `v` at the path; `w` is the value it replaces (no `w`: a new key) |
| `{"o":"del","p":[...],"w":old}` | remove an object key |
| `{"o":"ins","p":[...,i],"v":new}` | insert into an array at index `i` |
| `{"o":"rm","p":[...,i],"w":old}` | remove the array element at index `i` |

A path is a list of object keys (strings) and array indices (numbers): `["tracks",3,"clips",12,"start"]`.

**Every operation carries the old value.** So every edit is its own undo (the inverse of `set` swaps `v` and `w`, `ins` and `rm` swap, `del` becomes `set`), and the engine checks the old value before it changes anything: a page and an engine that drifted apart find out at the first edit that touches the difference, not later in the sound.

**The difference of two projects** (`diff` in `doc-sync.js`): objects key by key; arrays keep the elements that match at both ends (equal, or objects with the same `id`: tracks, clips, devices, sections all have one) and compare those inside, then compare a same-sized middle element by element (notes moved in place) or remove and insert it. Any result is correct, the tests prove that; these rules keep the usual edits small: moving a clip is one `set` of 70 bytes, adding a note one `ins`.

## 4. Numbers, order, and what happens when something goes wrong

- The engine counts every change its document takes: `seq`. Each edit names the `seq` it was made on (`base`). The engine takes it only if that is still the current one; otherwise it answers `stale` and changes nothing.
- **One edit in flight.** The page sends the next edit only after the answer to the last (a reply takes well under a millisecond on the local socket). Edits made meanwhile wait in a queue, one per undo step, so a burst of changes never gets merged across two undo steps.
- **The engine changes the project while the page's edit is on its way** (from N4: its undo, a plug-in window, a control surface). The engine sends `doc.change` with the operations; then the page's edit arrives on an old `base` and is refused as `stale`. The page has already rolled its unanswered edits back from its copy, applied the engine's change, and put its own changes on top again; they go out as a new edit. **If both changed the same place, the engine's change wins** and the page's is dropped (counted; in the tests it happened 7 to 9 times in 200, every time because the undo removed the track the page had just renamed).
- **No answer in time** (a lost line), **an edit whose old values do not match**, **a stale refusal without an engine change before it**, **an engine that restarted** (it starts empty and says `ready`): the page sends the whole project (`doc.load`, 514 KB for Fractals) and both start again from the same state.
- **The check.** Both sides compute the same 64-bit structural hash of the document (key order does not count, numbers by their exact bits, strings by their exact characters, even unpaired surrogates). The tests compare it after every edit. In the app the page asks for it when nothing has changed for 2 seconds and before every save; a mismatch means `doc.load`.

## 5. Undo

- **Steps.** The app's `pushUndo()` opens a step (`beginStep`); every edit until the next one belongs to it (a knob drag sends many edits, one step). The engine undoes and redoes whole steps.
- **Until N4 the app's own undo stays** (80 snapshots, restore on undo): the restore is just another change, sent as a diff. The tests prove both ways: the app's undo (phase A) and the engine's undo sent back to the page (phase B).
- **From N4 the engine's undo** replaces the snapshots: `doc.undo` answers with the operations it applied, the page applies them to `S` (`remote`). In the tests every engine undo gave exactly the state before its step, and undoing all of them gave the song as loaded, bit for bit.
- **Size.** The history keeps operations, not snapshots. After 800 random edits of Fractals (including whole tracks added and deleted) it held 42 MB; the limit is 64 MB, oldest steps dropped first. Snapshots of the same history would be 80 x 514 KB for only 80 steps.

## 6. A song that is half web and half native (stage 3)

Both engines read the same document: the web engine reads `S` as today, the native engine its exact copy. **Where each track sounds is not stored in the document**: the native engine decides it from the document and its port list (a track goes native when every device on it and every device it sends to is ported) and tells the page (`{"ev":"render","tracks":{"id":"native"|"web"}}`). The web engine mutes what the native one renders and the other way round. Because every change reaches both copies from one place (`S`, then the diff), the two engines can never disagree about a setting; the tests show the copies are equal after every edit. Moving a track from one engine to the other is then a decision about rendering, never an edit, so it cannot leave anything behind in the project.

## 7. Saving

The engine saves its document (`doc.save`): written to `name.tmp`, flushed to the disk (on the Mac with `F_FULLFSYNC`; plain `fsync` does not reach the disk there), then renamed over the file, which is atomic on one volume. The copy before it stays as a second name (`name.1`, `name.2`, five kept) until the rename, so a crash at any moment leaves the old file or the new one, whole. The file carries `format`, `formatVersion`, **`minReader`** (an older AudioLab refuses a file it cannot read fully instead of reading half of it; RL1, NB-R9) and the hash, so a damaged file is found when it is opened and the newest older copy that is whole opens instead.

Until the projects move into real files (RL1b) the engine saves the document only, next to the app's own autosave; the app's `.audiolab` files and its backups stay as they are. Autosave in the engine: 2 seconds after the last edit, and every 2 minutes while editing goes on (the app's own setting).

Measured: Fractals 517 KB in 23 ms including the flush to disk, the Psytrance demo 58 KB in 3 ms (Linux, ext4, this build machine).

## 8. Costs, measured

| Fractals (514 KB of JSON, 30 tracks) | |
|---|---|
| `JSON.stringify(S)`, which the app already does at every `pushUndo` | 3.4 ms |
| a commit when nothing changed (copy and compare) | about 10 ms in Node 22 |
| the hash in the page / in the engine | 10 ms / 2.4 ms |
| an edit on the wire, average over 850 random edits | 0.5 KB (moving a clip: 70 bytes) |
| applying an edit in the engine | a few microseconds |
| the whole project (`doc.load`) | 514 KB |

**The commit cost needs care at 240 Hz.** 10 ms per `changed()` is fine for clicks and too much for a knob dragged at the screen's rate. So the hook commits at most once per frame (it coalesces), and the next step for hot paths is a hint from the call site (`changed()` already knows whether the change is structural; a knob knows its device's path), so only that branch is compared. Measured in the real page with N2c.

**Never on the audio thread.** The document is changed on the engine's command thread. The audio graph is built from it on another thread and swapped in with one atomic pointer; a change of one device setting goes to the running device as a parameter message through a lock-free queue, without a rebuild. That is N3d's first job.

## 9. The messages

From the page: `doc.load {doc}`, `doc.edit {base, step, label, ops}`, `doc.undo`, `doc.redo`, `doc.hash`, `doc.snapshot`, `doc.save {path, keep}`, `doc.open {path}`, `doc.stats`. Every message carries `rq` (the request number from NB-R4a) and is answered once with the same `rq`.

From the engine: the answers (`{rq, seq}`, `{rq, error, seq}`), `doc.change {seq, label, ops}` for a change that started in the engine, `render` (section 6), `ready` after a start (the page then sends `doc.load`).

## 10. The hook in the app (N2c, waits for the design chain)

Four small places in `index.html`, behind the "Native output" switch:
- `pushUndo()`: `alDoc.beginStep(n)`;
- `changed()`: `alDoc.commit(S)`, at most once per frame;
- `restore()` (the app's undo) and `switchProject()`: a commit, and `doc.load` on a project switch;
- the engine's `doc.change`: `S = alDoc.remote(ev, S)`, then the app's own redraw (`renderHeaders`, `renderFx`, `syncGraph`), as after its own undo.

## 11. What is proven, and what is not

Proven on Linux (this machine; CI on every push from now on, and on the Mac job when it gets a machine): `aldoc selftest` (21 checks, also under AddressSanitizer and UndefinedBehaviorSanitizer) and `doc_sync_test.js` on Fractals, the Psytrance demo and Shrine Legion, 1,000 steps each:
- **A**, the page owns: about 850 random edits of 34 kinds (clips moved, dragged, resized, duplicated, deleted, reordered; notes added, removed, moved and sorted; velocities; volume drags; pans; mutes; device settings, devices added, removed and reordered; instruments; tracks added, deleted, moved; names with quotes, line breaks, control characters, accents, Japanese, emoji and unpaired surrogates; tempo; sections; automation points; keyed automation; keys that look like numbers and `__proto__`; keys added and removed; values changing type; awkward numbers: 5e-324, 1e21, -0, 2^53+2, NaN and Infinity, which JSON turns into null; fields set to undefined or a function; a change and its change back) and about 100 undos and redos by the app's own snapshot restore: **the engine's hash equal to the page's after every step**, the whole JSON equal every 100 steps, the page's own diff and apply agree.
- **B**, the engine owns undo: about 210 engine undos and 15 redos among the edits: every undo gives exactly the state before its step; undoing everything gives the song as loaded.
- **C**, 200 times the engine's change overtook the page's edit: refused as stale, rebased, equal every time.
- **D**, a lost line, a stale base, a wrong old value, an engine killed and restarted: found, the whole project sent, equal again.
- **E**, saving: atomic, five older copies, a crash between the write and the rename, a file cut in half, one number changed in a file, a file for a newer AudioLab.

Not proven yet: the page side inside the real app (N2c), the cost in Chromium and Electron rather than Node, the Mac build (D9: no macOS machine has run since NB-R1).

## 12. Assumptions (change any of them)

- The engine's change wins when both changed the same place. The alternative (the page's wins) would let a stale screen undo a plug-in's own change; the engine's side is the one that will own the state.
- The app's undo stays until N4 rather than moving to the engine with N2c: N2c is about sound, and moving undo then would change how undo feels before anything else is native.
- 64 MB of undo history in the engine, oldest dropped first; five older copies of a save.
- Plug-in blobs move into a side store by content hash when they pass 64 KB.
