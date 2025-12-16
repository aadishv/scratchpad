{
  "targets": [
    {
      "target_name": "speech_synthesis_native",
      "sources": [
        "native/speech_synthesis.cpp"
      ],
      "include_dirs": [
        "<!@(node -p \"require('node-addon-api').include\")"
      ],
      "dependencies": [
        "<!(node -p \"require('node-addon-api').gyp\")"
      ],
      "cflags!": [ "-fno-exceptions" ],
      "cflags_cc!": [ "-fno-exceptions" ],
      "defines": [ "NAPI_DISABLE_CPP_EXCEPTIONS" ],
      "conditions": [
        ["OS=='win'", {
          "sources": [ "native/tts_windows.cpp" ],
          "msvs_settings": {
            "VCCLCompilerTool": {
              "ExceptionHandling": 1
            }
          },
          "libraries": [ "-lole32.lib", "-lsapi.lib" ]
        }],
        ["OS=='mac'", {
          "sources": [ "native/tts_macos.mm" ],
          "xcode_settings": {
            "GCC_ENABLE_CPP_EXCEPTIONS": "YES",
            "CLANG_CXX_LIBRARY": "libc++",
            "MACOSX_DEPLOYMENT_TARGET": "10.14"
          },
          "link_settings": {
            "libraries": [
              "-framework AVFoundation",
              "-framework Foundation"
            ]
          }
        }],
        ["OS=='linux'", {
          "sources": [ "native/tts_linux.cpp" ]
        }]
      ]
    }
  ]
}
