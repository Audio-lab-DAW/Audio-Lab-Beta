// The C side of native/third_party/rustfft_ffi (Chromium's RustFFT wrapper, task NB-N3g).
#pragma once
#include <cstddef>
extern "C" {
struct AlRustFft;
AlRustFft* al_rustfft_new(size_t size);
void al_rustfft_forward(AlRustFft* f, const float* data, float* real_data, float* imag_data);
void al_rustfft_inverse(AlRustFft* f, const float* real_data, const float* imag_data, float* data);
void al_rustfft_free(AlRustFft* f);
}
