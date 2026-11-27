# fdlibm (Chromium's copy), vendored for the native engine (task NB-N3e)

Chromium's Web Audio computes the biquad filter's coefficients with this library (`third_party/fdlibm`,
"V8 fork of fdlibm"), not with the system's `sin`, `cos` and `exp`. The native engine carries the same code so
that a BiquadFilterNode's coefficients, and so the EQ's output, are the same bits on every machine.

- Source: https://github.com/chromium/chromium/tree/158.0.8127.36/third_party/fdlibm (identical on `main`, 27 Nov 2026).
- Licence: SunPro (see `LICENSE`), with the Chromium Authors' BSD notice in the file header.
- Changes: the includes of Chromium's `base/` and `build/` removed; `base::bit_cast` replaced by a `memcpy` cast and `ALWAYS_INLINE` defined
  (same bits). Nothing else.
- Built with `-ffp-contract=off` like the whole native tree.
