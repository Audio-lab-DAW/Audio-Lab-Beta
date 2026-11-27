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
