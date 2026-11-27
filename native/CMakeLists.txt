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
add_executable(alengine engine/engine_main.cpp common/coreaudio.cpp)
if(APPLE)
  target_link_libraries(alengine PRIVATE "-framework CoreAudio" "-framework CoreFoundation")
else()
  target_link_libraries(alengine PRIVATE pthread)
endif()

# ---- the engine core (task NB-N3a): ported devices, chains, offline render; no sound card needed ---------
# The browser's maths functions (LLVM libc, header only), so ported devices give the browser's bits everywhere.
add_library(al_jsmath INTERFACE)
target_include_directories(al_jsmath INTERFACE third_party/llvm-libc third_party/llvm-libc/include)
target_compile_definitions(al_jsmath INTERFACE LIBC_NAMESPACE=__llvm_libc_al)
add_executable(alrender engine/alrender.cpp engine/core/devices.cpp)
target_compile_options(alrender PRIVATE -ffp-contract=off)
target_link_libraries(alrender PRIVATE al_jsmath)
add_executable(almathprobe engine/math_probe.cpp)
target_compile_options(almathprobe PRIVATE -ffp-contract=off)
target_link_libraries(almathprobe PRIVATE al_jsmath)
# the control: the system's own maths library instead (shows what the vendored functions change)
add_executable(alrender_sysmath engine/alrender.cpp engine/core/devices.cpp)
target_compile_options(alrender_sysmath PRIVATE -ffp-contract=off)
target_compile_definitions(alrender_sysmath PRIVATE AL_MATH_SYSTEM)
# the control: fusing allowed, to show on each machine whether the rule matters for these devices
add_executable(alrender_fused engine/alrender.cpp engine/core/devices.cpp)
target_compile_options(alrender_fused PRIVATE -ffp-contract=fast)
target_link_libraries(alrender_fused PRIVATE al_jsmath)
# ---- the mixer (task NB-N3b): tracks, volume, pan and the master as Chromium computes them, whole quanta, offline --
add_executable(almix engine/mix/almix.cpp)
target_compile_options(almix PRIVATE -ffp-contract=off)   # the same bits as JavaScript and Chromium: no fused multiply-add

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
    ${VST3_SDK_ROOT}/public.sdk/source/vst/hosting/plugprovider.cpp
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
