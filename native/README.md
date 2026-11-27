# native/ : the native lab (task NM1)

First native code for AudioLab. These are tests that prove the risky parts of a native Mac app, not the app.
The plan is in `docs/native-mac-plan.md`.

- `dsp/al_crush.h`: the Bitcrusher, ported from the worklet `al-crush` so that it gives the same bits.
- `common/coreaudio.*`: Core Audio (HAL) device list and a plain output stream.
- `alnative/`: test A, the command line program (`devices`, `play`, `crush`, `compare`).
- `host/plugin_api.h`: the plug-in interface of the future engine, with no format named in it.
- `host/vst3_format.cpp`, `host/scan.cpp`: VST3 behind that interface, and scanning in a child process.
- `host/cli.cpp`: test B, `alvst3 scan` and `alvst3 run`.
- `testapp/`: test C, the small window app "AudioLab VST3 test".

Build (macOS or Linux; the Core Audio parts and the app are macOS only):

    git clone --depth 1 --branch v3.8.1_build_84 --recursive --shallow-submodules https://github.com/steinbergmedia/vst3sdk.git
    cmake -S native -B build -DVST3_SDK_ROOT=$PWD/vst3sdk
    cmake --build build --target alnative alvst3

The workflow `.github/workflows/native-lab.yml` (started by hand) builds and runs all of it on an Apple Silicon
runner; results go to the branch `native-lab-results`. The web engine's reference files and the scripts are in
`tools/native-lab/`.
