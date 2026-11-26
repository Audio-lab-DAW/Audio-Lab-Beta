# Voice device research (AudioLab Pro)

Research date: 2026-11-26. Every claim has a source link. Where a source was missing, contradictory or blocked, this is stated. "Guess" marks my own inference. Ratios and semitone values marked "calc" are my arithmetic on sourced numbers.

Blocked during research (the permission request timed out, so these pages were not read directly): github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI (main page; the English README was read instead), github.com/Plachtaa/seed-vc (raw README read instead), github.com/voicepaw/so-vits-svc-fork (PyPI page read instead), github.com/yxlllc/DDSP-SVC (a mirror read instead).

---

## 1. Voice conversion / singing voice conversion models

### RVC (Retrieval-based-Voice-Conversion-WebUI)
- **What it does:** any-to-one voice conversion. A content encoder (HuBERT/ContentVec features), a pitch track (RMVPE etc.) and a per-voice VITS-style synthesizer. Each target voice needs its own trained model ("net_g"). Source: https://huggingface.co/TigreGotico/voiceclonnx-rvc
- **Training data needed:** ">=10min low noise speech recommended". Source: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/docs/en/README.en.md
- **Code licence:** MIT. The official model repo on Hugging Face is tagged MIT: https://huggingface.co/lj1995/VoiceConversionWebUI . Third-party ONNX packagers also state upstream RVC is MIT: https://huggingface.co/ohnoitsaninja/rvc-base-onnx
- **Pretrained base models:** trained on "nearly 50 hours of high quality audio from the VCTK open source dataset" (README above). Repo tag is MIT (lj1995 page above). VCTK itself is CC BY 4.0, 110 English speakers, about 44 hours: https://huggingface.co/datasets/vctk/blob/main/README.md . So redistribution should carry a VCTK attribution (guess, based on CC BY terms).
- **Content encoder:** RVC's `hubert_base.pt` (190 MB) "was generated from checkpoint_best_legacy_500.pt", the ContentVec checkpoint, which is MIT: https://huggingface.co/wok000/vcclient_modules/blob/main/contentvec/Readme.md . ContentVec was trained on the 960 h of LibriSpeech and derived from HuBERT-Base: https://ar5iv.labs.arxiv.org/html/2204.09224 . LibriSpeech is CC BY 4.0: https://www.openslr.org/12
- **RMVPE pitch model:** original code Apache-2.0 (https://github.com/Dream-High/RMVPE); RVC's `rmvpe.pt` weights are MIT per an ONNX repackager that ships both licences: https://huggingface.co/Scicom-intl/rmvpe-onnx
- **File sizes:** `hubert_base.pt` 190 MB, `rmvpe.pt` 181 MB, `rmvpe.onnx` 362 MB: https://huggingface.co/lj1995/VoiceConversionWebUI/tree/main . ONNX ContentVec 360 MB fp32 / 91 MB int8, RMVPE 345 MB fp32 / 94 MB int8: https://huggingface.co/TigreGotico/voiceclonnx-rvc . RMVPE fp16-stored ONNX 185.8 MB: https://huggingface.co/Scicom-intl/rmvpe-onnx . Per-voice synthesizer size: not confirmed in this session (guess: tens of MB for a v2 model).
- **Real-time:** README reports end-to-end latency of 170 ms, 90 ms with ASIO (README above). The realtime GUI defaults: block time 0.25 s (range 0.02 to 1.5 s), crossfade 0.05 s, extra inference time 2.5 s, F0 method FCPE or RMVPE; displayed delay = device output latency + block + crossfade + 0.01 s: https://huggingface.co/NeoPy/RVC/blob/main/gui/v1.py . An independent paper measured No-F0 RVC at 189.8 ms end-to-end on an Intel i9-10850K CPU, RTF 1.114 (barely real-time): https://arxiv.org/pdf/2311.00873v1.pdf
- **Platform:** Windows DirectML path and an `rmvpe.onnx` for AMD/Intel; README does not mention Apple (README above). ONNX export scripts exist in forks: https://huggingface.co/NeoPy/RVC/blob/main/tools/onnx/export_onnx.py
- **Singing quality:** widely used for singing covers (not formally measured here). RMVPE is described as better than Crepe_full for vocals (README above).

### Applio
- RVC-based tool. README: "source code and model weights" are MIT; commercial use allowed with lawful use; separate Terms of Use for the official build. Windows/Linux/macOS scripts. Source: https://raw.githubusercontent.com/IAHispano/Applio/main/README.md . Real-time and ONNX support not mentioned in the README.

### w-okada voice-changer (VCClient)
- Real-time client that runs RVC, Beatrice v1/v2, MMVC, so-vits-svc, DDSP-SVC. Has an "onnx (mac M1)" edition supporting RVC: https://github.com/w-okada/voice-changer
- **Licence:** GitHub lists "other"; Beatrice models are proprietary; character voices have their own terms: https://awesome.ecosyste.ms/projects/github.com%2Fw-okada%2Fvoice-changer . Not suitable to embed without legal review.
- **Latency:** no millisecond figures found. A community guide recommends chunk 112 on NVIDIA, 448 on CPU, 448 (M2 Max and lower) or 256 (higher) on Mac, with RMVPE_ONNX or CREPE_TINY on Mac: https://Huggingface.co/blog/Lenylvt/w-okada

### so-vits-svc (svc-develop-team) and so-vits-svc-fork
- so-vits-svc 4.1: AGPL-3.0, "for academic learning and communication, not production"; supports ContentVec, HuBERT-soft, Whisper-PPG encoders and crepe, dio, pm, harvest, rmvpe, fcpe pitch; optional shallow diffusion; no models bundled, per-voice training required: https://raw.githubusercontent.com/svc-develop-team/so-vits-svc/4.1-Stable/README.md
- so-vits-svc-fork: MIT, realtime mic conversion (`svc vc`), CPU inference "fast enough", MPS "probably supported", marked "No Longer Maintained", points to Applio: https://pypi.org/project/so-vits-svc-fork . No latency numbers.

### DDSP-SVC
- MIT, "Real-time end-to-end singing voice conversion system based on DDSP", last push Aug 2024 (metadata): https://awesome.ecosyste.ms/projects/github.com%2Fyxlllc%2FDDSP-SVC
- Needs per-voice training (about 1000 clips, none under 2 s); RMVPE recommended; real-time resource use "significantly lower" than so-vits-svc and "probably slightly higher" than RVC; newer versions add a rectified-flow shallow diffusion stage: https://gh.hhj520.top/yxlllc/DDSP-SVC (mirror). No latency or size numbers found.

### Diff-SVC
- AGPL-3.0, diffusion SVC, "not intended for production", last push July 2023: https://awesome.ecosyste.ms/projects/github.com%2Fprophesier%2Fdiff-svc . Diffusion is offline-oriented (not real-time; no figures found).

### Seed-VC
- Zero-shot (1 to 30 s reference, no training), also singing; optional fine-tuning: https://raw.githubusercontent.com/Plachtaa/seed-vc/main/README.md
- **Licence:** GPL-3.0 per PyPI: https://pypi.org/project/seed-vc/ . The Hugging Face weights repo shows conflicting "mit" metadata and "gpl-3.0" header: https://huggingface.co/Plachta/Seed-VC/blob/00edd3ad7e8397150c27e7c25f95047721b050d0/README.md?code=true
- **Sizes:** real-time tiny 25M params (XLSR-large encoder, HIFT vocoder, 22 kHz); offline 98M; singing 200M at 44.1 kHz (Whisper-small + BigVGAN); v2 67M + 90M (README above). Note the external encoders (XLSR-large, Whisper) add their own size (not measured here).
- **Real-time:** 430 ms latency on RTX 3060 Laptop (block 0.18 s, 150 ms inference per chunk); GPU "strongly recommended"; Apple Silicon supported via requirements-mac (README and PyPI above).

### OpenVoice V2
- MIT for V1 and V2 since April 2024, commercial use allowed; tone-colour cloning for speech in six languages; singing not mentioned: https://raw.githubusercontent.com/myshell-ai/OpenVoice/HEAD/README.md
- ONNX repack: converter 64.3 MB fp16 / 32.7 MB int8, plus ref encoder 1.6 MB; RTF 0.04 to 0.06 on RTX 3080 Laptop; 22.05 kHz output: https://huggingface.co/moonbox-dev/OpenVoiceV2-ONNX . Zero-shot (reference clip), no per-voice training.

### FreeVC
- MIT, one-shot text-free VC using WavLM + VITS, pretrained checkpoints, last push March 2024: https://awesome.ecosyste.ms/projects/github.com%2FOlaWod%2FFreeVC . Speech-oriented; no singing or latency data found.

### kNN-VC
- Any-to-any: WavLM-Large features, each source frame replaced by the mean of k nearest reference frames, HiFi-GAN vocoder; quality gains diminish beyond 5 minutes of reference: https://github.com/bshall/knn-vc/ . Paper used about 8 minutes per speaker and says inference is "faster than real-time" on an 8 GB GPU: https://arxiv.org/pdf/2305.18975
- **Licence:** GitHub metadata says "other": https://awesome.ecosyste.ms/projects/github.com%2Fbshall%2Fknn-vc . Terms not confirmed.

### Comparison table

| Model | Code licence | Weights licence | Per-voice training | Real-time (reported) | Apple / ONNX | Singing |
|---|---|---|---|---|---|---|
| RVC v2 | MIT | MIT (base on VCTK CC BY 4.0) | Yes, ~10 min | 170 ms (90 ms ASIO); 190 ms CPU (No-F0) | ONNX exports exist; w-okada ONNX M1 build | Good, widely used |
| Applio | MIT | MIT | Yes | Not stated | macOS scripts | Same as RVC |
| w-okada | "other" | Mixed, Beatrice proprietary | Depends | No ms figure | ONNX M1 build | Runs RVC |
| so-vits-svc 4.1 | AGPL-3.0 | None bundled | Yes | Via w-okada | Not stated | Good |
| so-vits-svc-fork | MIT | None bundled | Yes | Yes, no figure | MPS "probably" | Good; unmaintained |
| DDSP-SVC | MIT | Not stated | Yes, ~1000 clips | Yes, no figure | Not stated | Designed for singing |
| Diff-SVC | AGPL-3.0 | Not stated | Yes | No | Not stated | Singing, offline |
| Seed-VC | GPL-3.0 | Conflicting MIT/GPL | No (zero-shot) | 430 ms on GPU | Mac supported | Dedicated 200M model |
| OpenVoice V2 | MIT | MIT | No (zero-shot) | RTF 0.04 to 0.06 GPU | ONNX 34 to 66 MB | Not claimed |
| FreeVC | MIT | MIT (repo) | No (one-shot) | No figure | Not stated | Not claimed |
| kNN-VC | "other" | Not confirmed | No (reference set) | Faster than real time on GPU | Not stated | Not claimed |

---

## 2. Running inference in Electron or the browser

- **onnxruntime-node:** prebuilt EPs: CPU on Windows/Linux/macOS x64 and arm64; CoreML on macOS x64 and arm64; DirectML on Windows x64 and arm64; WebGPU on Windows, Linux x64, macOS; CUDA Linux x64 only: https://socket.dev/npm/package/onnxruntime-node/overview/1.24.3 . MIT, unpacked size 218 MB (npm page showing v1.21.1): https://npmjs.com/package/onnxruntime-node . Guess: most of that size is per-platform binaries, so an Electron build that prunes other platforms ships much less (not measured).
- **CoreML EP details:** macOS 10.15+; MLProgram format needs macOS 12+ and supports more ops (LayerNorm, GELU, ConvTranspose etc.); compute units ALL / CPUAndNeuralEngine / CPUAndGPU / CPUOnly; Conv only 1D/2D, MatMul needs constant weights; dynamic shapes allowed but can hurt performance (`RequireStaticInputShapes`): https://onnxruntime.ai/docs/execution-providers/CoreML-ExecutionProvider.html . Practical note (guess): fixed block sizes for the realtime path suit CoreML best.
- **onnxruntime-web:** WASM build (`ort-wasm-simd-threaded.wasm`) and JSEP build (`ort-wasm-simd-threaded.jsep.wasm`) for WebGPU and WebNN; use `onnxruntime-web/wasm` import to shrink the bundle; cache large models in IndexedDB; WebGPU needs a secure context: https://onnxruntime.ai/docs/tutorials/web/deploy.html . One JSEP wasm file measured 23.9 MB: https://huggingface.co/spaces/dwb2023/transformers-js-demos/blob/main/assets/ort-wasm-simd-threaded.jsep-BAR87mbD.wasm
- **Known RVC ONNX pipelines:**
  - voiceclonnx-rvc: ContentVec-768 ONNX (360 MB fp32 / 91 MB int8) + RMVPE ONNX (345 MB / 94 MB) + per-voice net_g; MIT: https://huggingface.co/TigreGotico/voiceclonnx-rvc
  - rvc-base-onnx: HuBERT base layer-12 ONNX variants + rmvpe.onnx, MIT, "for local RVC-compatible ONNX Runtime inference": https://huggingface.co/ohnoitsaninja/rvc-base-onnx
  - Official/fork ONNX exporters for the synthesizer: https://huggingface.co/NeoPy/RVC/blob/main/tools/onnx/export_onnx.py and an ONNX inference script: https://huggingface.co/spaces/kevinwang676/rvc-talktalkai-gpu/raw/main/lib/infer_pack/onnx_inference.py
- **Pitch models as ONNX:** RMVPE 185.8 MB, CPU RTF 0.056 single thread; FCPE 47.8 MB, CPU RTF 0.022 single thread / 0.0068 four threads, mel front end inside the graph: https://huggingface.co/Scicom-intl/rmvpe-onnx , https://huggingface.co/Scicom-intl/fcpe-onnx
- **CoreML conversion of RVC:** no maintained public CoreML RVC pipeline found in this session (not confirmed either way).

---

## 3. Pitch trackers for the note view

| Tracker | Size | Accuracy (from papers) | Cost | Licence |
|---|---|---|---|---|
| CREPE full | ~22.2M params; 42.4 MB f16 | RWC-synth RPA 0.999; MDB-stem-synth RPA 0.967 / RCA 0.970 | ~282 GFLOP per s audio; RTF 0.48 on RTX 4090 | MIT |
| CREPE tiny | 0.93 MB f16 | Slightly lower than full (no figure) | ~7.3 GFLOP per s | MIT |
| SwiftF0 | 95,842 params (paper) / 14,386 (PyPI, newer) | Avg RPA 90.07 clean vs CREPE 70.87 and pYIN 84.50 on its benchmark | 132.6 ms for 5 s on CPU; claims 180x real time per core | MIT |
| PESTO | 0.13M params | Close to CREPE on MIR-1K, MDB (no number on README); MIR-1K RPA 98.47 in FCPE paper | ONNX ~0.7 ms per frame; streaming mode | LGPL-3.0 |
| FCPE | 10.64M params; ONNX 47.8 MB | MIR-1K RPA 96.79; TONAS 96.03 | RTF 0.0062 on RTX 4090; CPU RTF 0.022 | MIT |
| RMVPE | 90.42M params; ONNX 185.8 MB | MIR-1K vocals RPA 97.27 / RCA 97.28; polyphonic MIR-1K 95.42 | RTF 0.033 on RTX 4090; CPU RTF 0.056 | Code Apache-2.0, RVC weights MIT |
| pYIN | DSP, no weights | Recall ~0.98 vs YIN below 0.951 (synth singing); RWC-synth RPA 0.990 | Cheap | librosa ISC |
| YIN | DSP | Lower than pYIN (above) | Cheapest | Public algorithm |

Sources: CREPE table and pYIN/SWIPE comparison: https://arxiv.org/pdf/1802.06182 ; CREPE MIT: https://github.com/marl/crepe ; CREPE sizes and FLOPs: https://huggingface.co/cstr/crepe-GGUF ; FCPE paper (params, RPA, RTF for FCPE, RMVPE, CREPE, PESTO): https://arxiv.org/html/2509.15140v1 ; FCPE MIT: https://pypi.org/project/torchfcpe ; RMVPE paper: https://arxiv.org/html/2306.15412v1 ; SwiftF0 paper: https://arxiv.org/html/2508.18440v1 ; SwiftF0 package (MIT, 14,386 params, ONNX Runtime dependency, 46.875 to 2093.75 Hz, streaming needs 176 ms lookahead): https://pypi.org/project/swift-f0/ ; PESTO (LGPL-3.0, ONNX export, streaming): https://github.com/SonyCSLParis/pesto ; pYIN paper: https://core.ac.uk/download/30696897.pdf ; librosa ISC: https://pypi.org/project/librosa/

Caveat: accuracy depends heavily on dataset; the FCPE paper notes RMVPE, CREPE and PESTO were trained on MIR-1K, so their MIR-1K scores are favoured (FCPE paper above). SwiftF0's benchmark scores for CREPE are much lower than CREPE's own paper, so cross-paper numbers are not directly comparable.

---

## 4. Non-AI pitch and formant editing, and how pro tools present notes

### DSP methods
- **TD-PSOLA:** pitch marks per period on voiced sections, Hann windows of 2 to 4 periods, overlap-add at the new period. Two-period windows preserve the spectral envelope (formants) but broaden formant bandwidths; longer windows cause reverberant artefacts; unvoiced stretching above 2x gives tonal noise; very cheap computationally: https://courses.grainger.illinois.edu/ece420/5_PSOLA.pdf
- **WORLD vocoder:** modified-BSD licence, "no patent in all algorithms"; DIO and Harvest (F0), CheapTrick (envelope), D4C (aperiodicity), synthesis; has a real-time synthesis function: https://github.com/mmorise/World . Good fit for offline pitch and formant edits on a note basis (my suggestion).
- **Phase vocoder with formant preservation:** Röbel and Rodet use a cepstrum-based iterative "true envelope" estimator to preserve the spectral envelope while pitch shifting in a phase vocoder: https://dafx.de/paper-archive/details/EDSTSaO17Gd_0LV03iwDfw

### Melodyne
- Notes are "blobs" whose vertical position is pitch; Main Tool drags pitch in semitones (Alt for cents), time, and duration; double-click above a blob splits notes: https://helpcenter.celemony.com/M5/doc/melodyneEditor5/en/M5tour_QuickStart_editor
- **Correct Pitch macro:** moves notes toward the nearest semitone by a set amount, plus a second slider for pitch drift (source above). Sliders named Pitch Center and Pitch Drift, percentages; avoid 100% unless needed: https://acoustica.com/mixcraft-10-manual/appendix-1-using-melodyne-for-basic-vocal-tuning . Sound On Sound suggests starting both at 100% after splits: https://www.soundonsound.com/techniques/pitch-correcting-vocals-melodyne . Melodyne 5 uses a "musically weighted" pitch centre: https://www.soundonsound.com/reviews/celemony-melodyne-5
- **Pitch Modulation and Pitch Drift tools:** modulation = fast variation (vibrato); drift = slow wander; 100% original, 0% flat, -100% inverted; double-click toggles original/none: https://helpcenter.celemony.com/M5/doc/melodyneStudio5/en/M5tour_ToolModulationDrift_2
- **Formant tool:** formants shown as thick lines over blobs, drag per note, also edits transitions (SOS Melodyne article above). Units not found.
- **Amplitude tool:** drag per note, Alt for fine, double-click mutes; Note Separation and Separation Type tools (soft vs hard separations): https://helpcenter.celemony.com/M5/doc/melodyneStudio5/en/M5tour_ToolAmplitude . Melodyne 5 auto-detects sibilants and has a Sibilant Balance tool, Fade tool and Leveling macro (SOS review above).

### Auto-Tune (Antares)
- Retune Speed in ms: 0 = instant (the "Cher effect"), 10 to 50 ms natural starting range, default 20: https://www.sweetwater.com/sweetcare/articles/auto-tune-retune-speed-setting-work/
- Humanize: slows correction only on sustained notes, start 0, 10 to 20 for sustained notes. Flex Tune: 15 to 30 starting point, 0 pulls every note, higher lets natural variation through (Modern mode): https://help.antarestech.com/hc/en-us/articles/42855736822932

### Waves Tune
- Display: Detection graph, Correction graph, Note Segments. Speed 0.1 to 800 ms (default 15), Note Transition 0.1 to 800 ms (default 120), Ratio 0 to 100%, Formant Correction switch, Natural Vibrato 0 to 200%, Synthetic vibrato rate 1 to 20 Hz, depth up to 400 cents: https://josephnilo.com/blog/waves-tune-explained/

### Synchro Arts Revoice Pro
- APT transfers timing, pitch and loudness from a guide to a dub; includes a Realistic Doubler: https://www.synchroarts.com/manuals/legacy/RevoiceProV2.6/Manual/2_Introduction.htm . Notes appear as blocks with a pitch trace; blocks can be stretched, inverted, tilted; pencil draws pitch; Correct Pitch 0 to 100%: https://www.soundonsound.com/techniques/revoice-pro-32-masterclass-part-2

### Logic Pro Flex Pitch
- Hotspots per note: Fine Pitch (top middle, cents), Pitch Drift (top left and top right corners, start and end), Vibrato (bottom middle), Formant Shift (bottom right), Gain (bottom left); note edges change length: https://www.makeuseof.com/logic-pro-how-to-use-flex-pitch/ (secondary source; Apple's own page did not render in this session). That is six hotspots counting drift in and out separately.
- Track parameters: Formant Track, Formant Shift, and "Keep Unvoiced Formants": https://support.apple.com/ro-md/guide/logicpro/flex-pitch-algorithm-and-parameters-lgcpba8e3301/10.7.8/mac/12.3

---

## 5. Choir and doubler effects

- **Waves Doubler:** 2-voice and 4-voice versions; delay 0 to 100 ms (default 8 ms); detune -100 to +100 cents, "2 to 12 cents sound fairly in tune", example 4 cents; pan -45 to +45 degrees (defaults V1 +22.5, V2 -22.5, V3 +45, V4 -45); mod depth up to 200 cents, mod rate 0.1 to 200 Hz (default 1 Hz); gain default -12 dB: https://manualmachine.com/waves/doubler/1343926-user-manual
- **Waves double-tracking article:** delay one duplicate 10 ms and the other 20 ms, pan hard left and right, keep the original centred; original Abbey Road ADT used around 100 ms: https://www.waves.com/double-tracking-vocals-different-approaches-for-a-richer-mix
- **Sound On Sound ADT:** detune double by about 0.20 semitones (about 20 cents, calc), mix 5 to 6 dB below the lead, LFO 1 Hz or lower for modulated delay: https://www.soundonsound.com/techniques/easy-d-t
- **Soundtoys Little AlterBoy:** pitch plus or minus one octave, separate formant control, modes Transpose, Quantize, Robot, plus Drive and Mix: https://producelikeapro.com/blog/little-alterboy-review/ . Single voice, not a choir.
- **iZotope VocalSynth Polyvox:** Formant, Character, Humanize (varies time and pitch offsets, adds detune), Pan, Filter; number-of-voices control not documented on that page: https://s3.amazonaws.com/izotopedownloads/docs/vocalsynth201/polyvox/index.html
- **Antares Harmony Engine:** 4 harmony voices; Choir adds up to 16 extra voices per channel (up to 80 total; the page headline says "32-piece", which conflicts); Humanize adds vibrato and timing variation; Throat Length sets per-voice formants: https://www.antarestech.com/blog/harmony-engine-blog . Choir spread in ms or cents not published there.
- **Melda MHarmonizer and Eventide:** not researched in detail; no numbers confirmed.

**Summary of typical natural doubling numbers (from the sources above):** delays of 8 to 20 ms per double, detune 2 to 12 cents (up to about 20 cents), slow modulation at or below 1 Hz, doubles 5 to 12 dB under the lead, panned wide. The "10 to 40 ms" range in the brief is plausible but only 8 to 20 ms was confirmed. For a choir, a guess consistent with the above: 8 to 16 voices, each with random 5 to 35 ms offset, plus or minus 5 to 15 cents detune with slow random drift, formant varied by plus or minus 1 to 2 semitones, spread across the stereo field.

---

## 6. Male, female and child voices

**Mean speaking F0**
- Adults: men 115 Hz (SD 21), women 199 Hz (SD 28); children aged 4 to 12: 243 to 277 Hz: https://www.sydney.edu.au/content/dam/corporate/documents/faculty-of-medicine-and-health/research/research-centres/sydney-voice-lab/acoustic-analysis-normative-data-reference-sheet-20250416_v4.0-sydney-voice-lab.pdf.coredownload.pdf
- NCVS: men about 125 Hz, women about 200 Hz, children 250 to 400 Hz; male vocal folds about 60% longer: https://ncvs.org/?p=8521
- Peterson and Barney 1952 had 33 men, 28 women, 15 children: https://www.fon.hum.uva.nl/praat/manual/Create_formant_table__Peterson___Barney_1952_.html . Hillenbrand 1995 had 139 talkers (45 men, 48 women, 46 children): https://voxbooster.com/blog/vowel-formant-frequency-norms-statistics-2026/ (secondary).
- Per-vowel P&B averages (MIT course notes, partly garbled scan): /i/ male F0 136, F1 270, F2 2290, F3 3010; female F0 235, F1 310, F2 2790, F3 3310: https://ocw.mit.edu/courses/6-541j-speech-communication-spring-2004/764792e5deae0aeabf7ca55d1257e919_6541j_02_19_04.pdf

**Formant ratios**
- From the P&B /i/ values: women vs men F1 1.15, F2 1.22, F3 1.10 (calc).
- From Chung et al. 2012 /i/: women vs men F1 1.06, F2 1.20, F3 1.10; 5-year-olds vs men about 1.19 to 1.38 (blog calc): https://voxbooster.com/blog/vowel-formant-frequency-norms-statistics-2026/
- Adult male formants are about 32% lower than at age 4, adult female about 20% lower (Huber et al. 1999, cited); male vocal tract about 15.5 cm: https://www.pdn.cam.ac.uk/system/files/documents/SPjasa05.pdf . So age-4 child vs man is about 1/0.68 = 1.47 (calc).
- At equal F0, much of the F1 difference disappears, so part of the formant difference follows F0: https://core.ac.uk/download/85221943.pdf

**Suggested character presets (calc from the numbers above, starting from a male source; reverse signs for a female source):**

| Character | Pitch shift | Formant shift |
|---|---|---|
| Man to woman | about +8 to +9.5 semitones (200/125 to 199/115) | about x1.15 to x1.20 (about +2.4 to +3.2 semitones) |
| Man to child | about +12 to +14 semitones (250 to 270 Hz) | about x1.3 to x1.47 (about +4.5 to +6.7 semitones) |
| Woman to man | about -8 to -9.5 semitones | about x0.83 to x0.87 |

For singing, keep the melody's octave (shift by 0 or 12 semitones) and use mostly formant shift plus a small pitch move, otherwise the song changes key (my suggestion).

---

## 7. Pop vocal chain numbers

| Stage | Values | Source |
|---|---|---|
| High-pass | 80 to 100 Hz (Antares); 100 to 250 Hz (iZotope); 40 to 85 Hz (LANDR); 80 to 300 Hz swept (AudioTechnology) | Antares: https://www.antarestech.com/blog/the-5-tips-you-need-to-mix-vocals ; iZotope: https://www.izotope.com/en/learn/vocal-cheet-sheet.html ; LANDR: https://blog.landr.com/vocal-chain-8-essential-mix-elements-for-vocal-tracks ; AT: https://www.audiotechnology.com/tutorials/mixing-synth-pop-vocals |
| Cuts | mud 200 to 500 Hz; nasal 500 Hz to 1.2 kHz; harsh 2 to 5 kHz or 5 to 8 kHz | Antares, iZotope, AudioTechnology above |
| Presence / air | presence 2 to 5 kHz; air 10 to 12 kHz (Antares), 10 kHz+ shelf (iZotope), 8 to 14 kHz (AT) | Above |
| Compression | 2:1 to 4:1 delicate, 4:1 to 8:1 powerful; attack 0.1 to 1 ms fast or 10 to 30 ms slow; release 50 to 100 ms fast or 200 ms to 1 s slow (Antares). 1176 at 4:1, attack 3, release 7, 3 to 7 dB GR typical (AT). 3 to 7 dB GR on lead (iZotope chain) | Above; https://www.izotope.com/en/learn/crafting-a-basic-vocal-chain.html |
| De-esser | 5 to 8 kHz, up to 10 kHz for female voices (Antares); two-stage 6 to 20 kHz plus 2 to 5 kHz (male) or 3 to 6 kHz (female), 5 to 10 dB GR (AT) | Above |
| Plate reverb | decay about 2 s, pre-delay 30 to 80 ms (AT); decay 2.5 s, pre-delay 87 ms (range 70 to 180), low cut 180 Hz (UA Mokran preset); decay 0.3 to 0.8 s intimate or 1.5 to 3 s epic, pre-delay 10 to 30 ms (Antares) | AT and Antares above; https://www.uaudio.com/blogs/ua/peter-mokran-vocal-preset-uad-pure-plate |
| Delay | slapback 80 to 130 ms with L/R offset 10 to 15 ms; 1/4 or 1/8 note echo with moderate feedback (AT); tempo sync via 60000/BPM | AT above; https://www.sageaudio.com/articles/how-to-mix-vocals-start-to-finish |

---

## 8. Recommendation

**Constraints:** ship only code and weights that allow redistribution; never ship a voice that imitates a real person; users bring or train their own voices.

**Voice conversion: adopt the RVC v2 architecture via ONNX Runtime.**
- Why: MIT code (lj1995 repo tag, https://huggingface.co/lj1995/VoiceConversionWebUI); content encoder is MIT ContentVec trained on CC BY 4.0 LibriSpeech; pitch weights MIT with Apache-2.0 original code (https://huggingface.co/Scicom-intl/rmvpe-onnx); base models MIT trained on CC BY 4.0 VCTK. It is the dominant user ecosystem for trained singing voices (Applio is MIT too) and has working ONNX pipelines.
- It is any-to-one: every voice needs a trained model (about 10 min of audio), which fits "users bring or train their own" and is harder to misuse than zero-shot cloning. Ship no net_g voice models. Guess: offer a "train from my own recordings" flow later, and show a consent notice on import.
- Runtime: onnxruntime-node with CoreML (Mac) and DirectML (Windows), CPU fallback (https://socket.dev/npm/package/onnxruntime-node/overview/1.24.3). Run offline render first (note-based edits), real-time later; expect roughly 170 to 250 ms latency in real time (RVC README and GUI defaults above), so treat it as a render or monitoring effect, not low-latency tracking.
- Download sizes: ContentVec ONNX 91 MB int8 or 360 MB fp32; pitch either FCPE ONNX 47.8 MB or RMVPE ONNX 185.8 MB (or 94 MB int8); onnxruntime-node up to 218 MB unpacked before pruning. A realistic first install: about 140 MB of models (ContentVec int8 + FCPE) plus the runtime (calc).
- Attribution to include in the app's licences screen: RVC (MIT), ContentVec (MIT), RMVPE (Apache-2.0 / MIT weights), FCPE (MIT), VCTK (CC BY 4.0), LibriSpeech (CC BY 4.0).
- Keep as later options: DDSP-SVC (MIT, lighter, singing-focused, https://awesome.ecosyste.ms/projects/github.com%2Fyxlllc%2FDDSP-SVC) if a training pipeline is built in-house. OpenVoice V2 is MIT and small (34 to 66 MB ONNX), but it is speech-oriented and zero-shot cloning from any clip makes imitating real people trivial, so not recommended for this product goal.
- Avoid: Seed-VC (GPL-3.0), so-vits-svc and Diff-SVC (AGPL-3.0), w-okada (mixed or proprietary components), kNN-VC (licence "other", unconfirmed).

**Pitch tracker for the note view: SwiftF0 for display, FCPE for conversion.**
- SwiftF0: MIT, about 14k to 96k parameters, ONNX-native, 180x real time per CPU core, range 46.9 to 2093.8 Hz, so it can run in the browser build via onnxruntime-web WASM with negligible download (package 116 kB): https://pypi.org/project/swift-f0/
- FCPE: MIT, 47.8 MB ONNX, strong on singing datasets, already the default F0 in RVC's realtime GUI: https://huggingface.co/Scicom-intl/fcpe-onnx , https://huggingface.co/NeoPy/RVC/blob/main/gui/v1.py
- Keep a pure-JS pYIN or YIN as a zero-download fallback (pYIN recall about 0.98 on synthetic singing, https://core.ac.uk/download/30696897.pdf). Skip PESTO unless LGPL-3.0 obligations are acceptable (https://github.com/SonyCSLParis/pesto).

**Pitch and formant editing without AI:** use WORLD (modified BSD, https://github.com/mmorise/World) or a TD-PSOLA path for per-note pitch, drift and vibrato edits, with a true-envelope phase vocoder for the "man / woman / child" formant presets. This gives the Melodyne-style editor and the character presets with no model download at all; AI conversion becomes an optional add-on.
