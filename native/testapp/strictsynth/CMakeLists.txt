# Tasks NL5 and NL7: a test instrument for the VST3 host (not shipped). Its own project() because the SDK's packaging wants a version.
project(al_strict_synth VERSION 0.7.0 LANGUAGES CXX)
set(public_sdk_SOURCE_DIR ${VST3_SDK_ROOT}/public.sdk)
smtg_add_vst3plugin(al-strict-synth strictsynth.cpp)
target_link_libraries(al-strict-synth PRIVATE sdk)
if(SMTG_MAC)
  smtg_target_set_bundle(al-strict-synth BUNDLE_IDENTIFIER "com.audiolab.test.strictsynth" COMPANY_NAME "AudioLab test")
endif()
