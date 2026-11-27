# AudioLab native lab (task NM1): the first native tests. Not the app.
#   alnative   Core Audio devices and output, and a bit-for-bit port of one of the app's effects (test A)
#   alvst3     a command line VST3 host (test B)
#   AudioLab VST3 test.app   a small window app for the user's Mac (test C, macOS only)
# Configure with -DVST3_SDK_ROOT=/path/to/vst3sdk (Steinberg's VST 3 SDK, MIT licence).
cmake_minimum_required(VERSION 3.25)
if(NOT DEFINED CMAKE_OSX_DEPLOYMENT_TARGET)
  set(CMAKE_OSX_DEPLOYMENT_TARGET "12.0" CACHE STRING "")
endif()
project(audiolab_native_lab LANGUAGES C CXX)
# Everything here must round like JavaScript: no fused multiply-add, no fast-math (review RN5, A6). Targets that
# want the opposite as a control set it themselves (alnative_fused, alrender_fused).
add_compile_options(-ffp-contract=off -fno-fast-math)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# ---- test A: no SDK needed -------------------------------------------------------------------------
add_executable(alnative alnative/main.cpp common/coreaudio.cpp)
# The DSP must round exactly like JavaScript: no fused multiply-add, no fast-math.
target_compile_options(alnative PRIVATE -ffp-contract=off)
if(APPLE)
  target_link_libraries(alnative PRIVATE "-framework CoreAudio" "-framework CoreFoundation")
endif()
# The control: the same program with fusing allowed, to show whether the flag matters on this machine.
add_executable(alnative_fused alnative/main.cpp common/coreaudio.cpp)
target_compile_options(alnative_fused PRIVATE -ffp-contract=fast)
if(APPLE)
  target_link_libraries(alnative_fused PRIVATE "-framework CoreAudio" "-framework CoreFoundation")
endif()

# ---- the engine, first part (task NB-N1): owns the audio output, driven by JSON lines -------------------
add_executable(alengine engine/engine_main.cpp common/coreaudio.cpp common/nulldevice.cpp)
if(APPLE)
  target_link_libraries(alengine PRIVATE "-framework CoreAudio" "-framework CoreFoundation")
else()
  target_link_libraries(alengine PRIVATE pthread)   # the null device stands in for Core Audio (task NB-R2)
endif()
# the ring under two real threads (task NB-R1); CI builds it with -fsanitize=thread as well
add_executable(alringstress tests/ring_stress.cpp)
if(NOT APPLE)
  target_link_libraries(alringstress PRIVATE pthread)
endif()

# ---- the engine core (task NB-N3a): ported devices, chains, offline render; no sound card needed ---------
# The browser's maths functions (LLVM libc, header only), so ported devices give the browser's bits everywhere.
add_library(al_jsmath INTERFACE)
target_include_directories(al_jsmath INTERFACE third_party/llvm-libc third_party/llvm-libc/include)
target_compile_definitions(al_jsmath INTERFACE LIBC_NAMESPACE=__llvm_libc_al)
# Chromium's copy of fdlibm (task NB-N3e): the sin, cos and exp its BiquadFilterNode computes coefficients with.
# Always -ffp-contract=off, also in the 'fused' control (it stands for the browser, not for the device code).
add_library(al_fdlibm STATIC third_party/fdlibm/ieee754.cc)
target_compile_options(al_fdlibm PRIVATE -ffp-contract=off)
if(APPLE)
  # Chromium on the Mac runs a biquad with fixed values through Accelerate's vDSP_deq22D; so does the engine there
  target_link_libraries(al_fdlibm PUBLIC "-framework Accelerate")
endif()
# Chromium's FFT (task NB-N3g): since Chromium 158 FFTFrame is the RustFFT crate behind a small Rust wrapper
# (rustfft_ffi.rs). The engine builds that same wrapper and crate version (Cargo.lock) with cargo and links it, so
# the oscillators' tables (and later the convolver and the analyser) are the browser's bits.
find_program(AL_CARGO cargo HINTS $ENV{HOME}/.cargo/bin)
if(NOT AL_CARGO)
  # configuring still works (the test app's targets do not need it); building a target that links al_rustfft fails
  message(WARNING "cargo not found: alrender, albus and alnodes need it (Chromium's FFT, task NB-N3g)")
  set(AL_CARGO cargo)
endif()
find_package(Threads REQUIRED)
set(AL_RUSTFFT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/third_party/rustfft_ffi)
set(AL_RUSTFFT_LIB ${CMAKE_BINARY_DIR}/cargo/release/${CMAKE_STATIC_LIBRARY_PREFIX}rustfft_ffi${CMAKE_STATIC_LIBRARY_SUFFIX})
add_custom_command(OUTPUT ${AL_RUSTFFT_LIB}
  COMMAND ${CMAKE_COMMAND} -E env MACOSX_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET}
          ${AL_CARGO} build --release --locked --quiet --manifest-path ${AL_RUSTFFT_DIR}/Cargo.toml --target-dir ${CMAKE_BINARY_DIR}/cargo
  DEPENDS ${AL_RUSTFFT_DIR}/src/lib.rs ${AL_RUSTFFT_DIR}/Cargo.toml ${AL_RUSTFFT_DIR}/Cargo.lock
  COMMENT "cargo: Chromium's RustFFT wrapper" VERBATIM)
add_custom_target(al_rustfft_build DEPENDS ${AL_RUSTFFT_LIB})
add_library(al_rustfft STATIC IMPORTED GLOBAL)
set_target_properties(al_rustfft PROPERTIES IMPORTED_LOCATION ${AL_RUSTFFT_LIB})
add_dependencies(al_rustfft al_rustfft_build)
set_property(TARGET al_rustfft APPEND PROPERTY INTERFACE_LINK_LIBRARIES Threads::Threads ${CMAKE_DL_LIBS})
if(NOT APPLE)
  set_property(TARGET al_rustfft APPEND PROPERTY INTERFACE_LINK_LIBRARIES m)
endif()
add_executable(alnodes engine/alnodes.cpp)
target_link_libraries(alnodes PRIVATE al_jsmath al_rustfft)
add_executable(alrender engine/alrender.cpp engine/core/devices.cpp)
target_compile_options(alrender PRIVATE -ffp-contract=off)
target_link_libraries(alrender PRIVATE al_jsmath al_fdlibm al_rustfft)
add_executable(almathprobe engine/math_probe.cpp)
target_compile_options(almathprobe PRIVATE -ffp-contract=off)
target_link_libraries(almathprobe PRIVATE al_jsmath)
# the control: the system's own maths library instead (shows what the vendored functions change)
add_executable(alrender_sysmath engine/alrender.cpp engine/core/devices.cpp)
target_compile_options(alrender_sysmath PRIVATE -ffp-contract=off)
target_compile_definitions(alrender_sysmath PRIVATE AL_MATH_SYSTEM)
target_link_libraries(alrender_sysmath PRIVATE al_fdlibm al_rustfft)
# the control: fusing allowed, to show on each machine whether the rule matters for these devices
add_executable(alrender_fused engine/alrender.cpp engine/core/devices.cpp)
target_compile_options(alrender_fused PRIVATE -ffp-contract=fast)
target_link_libraries(alrender_fused PRIVATE al_jsmath al_fdlibm al_rustfft)
# ---- the mixer (task NB-N3b): tracks, volume, pan and the master as Chromium computes them, whole quanta, offline --
# the mixer's buses with the core's devices: groups, sends, returns, delay compensation, the master's chain (task NB-N3d)
add_executable(albus engine/mix/albus.cpp engine/core/devices.cpp)
target_compile_options(albus PRIVATE -ffp-contract=off)
target_link_libraries(albus PRIVATE al_jsmath al_fdlibm al_rustfft)

# the project document and its edit protocol (task NB-R7): the state the engine will own
add_executable(aldoc engine/doc/aldoc.cpp)

add_executable(almix engine/mix/almix.cpp)
target_compile_options(almix PRIVATE -ffp-contract=off)   # the same bits as JavaScript and Chromium: no fused multiply-add
target_link_libraries(almix PRIVATE al_fdlibm)   # the pan gains: fdlibm, as stereo_panner.cc

# ---- tests B and C: need the VST 3 SDK ---------------------------------------------------------------
if(VST3_SDK_ROOT)
  if(APPLE)
    enable_language(OBJC OBJCXX)
  endif()
  set(SMTG_ENABLE_VST3_HOSTING_EXAMPLES OFF CACHE BOOL "" FORCE)
  set(SMTG_RUN_VST_VALIDATOR OFF CACHE BOOL "" FORCE)
  if(NOT DEFINED AL_SDK_EXAMPLES)
    set(AL_SDK_EXAMPLES ON)
  endif()
  set(SMTG_ENABLE_VST3_PLUGIN_EXAMPLES ${AL_SDK_EXAMPLES} CACHE BOOL "" FORCE)
  if(NOT APPLE)
    set(SMTG_ENABLE_VSTGUI_SUPPORT OFF CACHE BOOL "" FORCE)
  endif()
  set(SMTG_CREATE_PLUGIN_LINK OFF CACHE BOOL "" FORCE)
  add_subdirectory(${VST3_SDK_ROOT} vst3sdk EXCLUDE_FROM_ALL)

  set(AL_HOST_SOURCES
    host/vst3_format.cpp
    host/scan.cpp
    host/diag.cpp
    ${VST3_SDK_ROOT}/public.sdk/source/vst/hosting/plugprovider.cpp
    ${VST3_SDK_ROOT}/public.sdk/source/vst/vstpresetfile.cpp
  ${VST3_SDK_ROOT}/public.sdk/source/common/memorystream.cpp
  )
  if(APPLE)
    list(APPEND AL_HOST_SOURCES ${VST3_SDK_ROOT}/public.sdk/source/vst/hosting/module_mac.mm)
    set_source_files_properties(${VST3_SDK_ROOT}/public.sdk/source/vst/hosting/module_mac.mm PROPERTIES COMPILE_FLAGS "-fobjc-arc")
  else()
    list(APPEND AL_HOST_SOURCES ${VST3_SDK_ROOT}/public.sdk/source/vst/hosting/module_linux.cpp)
  endif()
  add_library(alhost STATIC ${AL_HOST_SOURCES})
  target_include_directories(alhost PUBLIC ${VST3_SDK_ROOT})
  target_link_libraries(alhost PUBLIC sdk_hosting)
  if(APPLE)
    target_link_libraries(alhost PUBLIC "-framework CoreFoundation" "-framework Foundation")
  else()
    target_link_libraries(alhost PUBLIC dl pthread)
  endif()

  # task NL5: a test instrument that only sounds when the host gives its controller the processor's state and delivers
  # the controller's messages from a loader thread (as we suspect Phase Plant and Pigments need). Built only for the tests.
  if(AL_SDK_EXAMPLES)
    add_subdirectory(testapp/strictsynth)
  endif()

  add_executable(alvst3 host/cli.cpp)
  target_link_libraries(alvst3 PRIVATE alhost)

  if(APPLE)
    set(APPNAME "AudioLab VST3 test")
    add_executable(alvst3app MACOSX_BUNDLE testapp/main.mm common/coreaudio.cpp)
    set_source_files_properties(testapp/main.mm PROPERTIES COMPILE_FLAGS "-fobjc-arc")
    set_target_properties(alvst3app PROPERTIES
      OUTPUT_NAME "${APPNAME}"
      MACOSX_BUNDLE_INFO_PLIST ${CMAKE_CURRENT_SOURCE_DIR}/testapp/Info.plist)
    target_link_libraries(alvst3app PRIVATE alhost "-framework Cocoa" "-framework CoreAudio" "-framework CoreFoundation")
  endif()
endif()
