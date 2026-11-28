# LLVM libc maths, vendored (task NB-N3c)

The browser's `Math.sin`, `Math.cos`, `Math.exp` and `Math.log10` come from LLVM's libc (V8 15.8, `src/base/ieee754.cc`,
`LIBC_NAMESPACE::shared::...`, no `LIBC_MATH` flags, so the correctly rounded versions). The native engine core uses
the same functions so that its devices give the browser's bits on every system.

- Source: https://github.com/llvm/llvm-project, directory `libc/`, commit `19b71e03e3fdc44adc112e84c76a062920e3b506`
  (27 November 2026). Only the header-only files that `shared/math/{sin,cos,exp,log10}.h` include are kept here
  (143 files, found with the compiler's dependency list), with their paths unchanged.
- Chromium 158 pins another commit of the same library; because these functions are correctly rounded, any
  version gives the same results. Checked: 400,000 arguments of the kinds the devices use, 0 differences
  against Chromium 158 for sin, cos and exp (`tools/native-lab/math_probe.py`).
- Not used for `pow`: V8's `Math.pow` calls the system's own `pow` (flag `use_std_math_pow`, `src/numbers/ieee754.cc`),
  so the native engine does the same (`js::pow` in `native/engine/core/jsmath.h`).
- Licence: Apache License 2.0 with LLVM Exceptions (`LICENSE.TXT`). Attribution belongs in the app's notices
  when the native engine ships (see `docs/research-native-qa-legal.md`, the licence audit).

- Apple Silicon and other 64-bit ARM (task NB-R7, 27 November 2026): the first macOS build machine (native-ci run
  46052838752) found that the 143 files were gathered on an Intel machine and missed the ARM branches
  (`aarch64/nearest_integer.h`, the Darwin and Linux floating-point environments, the FMA range reduction and the small
  `memcpy` they use). 13 files added from the same commit, paths unchanged, found by compiling for `aarch64` until
  nothing was missing. The ARM build uses fused multiply-add inside these functions; they are correctly rounded, so the
  results are the same bits (the Mac job's maths probe is the check).

- `log` (task NB-N3j, 28 November 2026): `shared/math/log.h` and `src/__support/math/log.h` added from the same commit
  (everything else they include was already here). V8's `Math.log` is LLVM's (src/base/ieee754.cc); glibc's `log` differs
  from the browser's on 13 of 400,000 arguments, Chromium's fdlibm on about 1 %. The maths probe now covers `log` and
  `tanh` (V8 calls the system's `tanh`, so the engine does too).
