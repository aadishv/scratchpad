#include <napi.h>
#include "speech_synthesis.h"
#include <memory>
#include <map>

using namespace speech_synthesis;

class SpeechSynthesisWrapper : public Napi::ObjectWrap<SpeechSynthesisWrapper> {
public:
    static Napi::Object Init(Napi::Env env, Napi::Object exports);
    SpeechSynthesisWrapper(const Napi::CallbackInfo& info);
    ~SpeechSynthesisWrapper();

private:
    static Napi::FunctionReference constructor;
    std::unique_ptr<TTSPlatform> platform_;
    Napi::ThreadSafeFunction tsfn_;
    
    Napi::Value GetVoices(const Napi::CallbackInfo& info);
    Napi::Value Speak(const Napi::CallbackInfo& info);
    Napi::Value Cancel(const Napi::CallbackInfo& info);
    Napi::Value Pause(const Napi::CallbackInfo& info);
    Napi::Value Resume(const Napi::CallbackInfo& info);
    Napi::Value IsSpeaking(const Napi::CallbackInfo& info);
    Napi::Value IsPaused(const Napi::CallbackInfo& info);
};

Napi::FunctionReference SpeechSynthesisWrapper::constructor;

Napi::Object SpeechSynthesisWrapper::Init(Napi::Env env, Napi::Object exports) {
    Napi::HandleScope scope(env);
    
    Napi::Function func = DefineClass(env, "SpeechSynthesis", {
        InstanceMethod("getVoices", &SpeechSynthesisWrapper::GetVoices),
        InstanceMethod("speak", &SpeechSynthesisWrapper::Speak),
        InstanceMethod("cancel", &SpeechSynthesisWrapper::Cancel),
        InstanceMethod("pause", &SpeechSynthesisWrapper::Pause),
        InstanceMethod("resume", &SpeechSynthesisWrapper::Resume),
        InstanceMethod("isSpeaking", &SpeechSynthesisWrapper::IsSpeaking),
        InstanceMethod("isPaused", &SpeechSynthesisWrapper::IsPaused),
    });
    
    constructor = Napi::Persistent(func);
    constructor.SuppressDestruct();
    
    exports.Set("SpeechSynthesis", func);
    return exports;
}

SpeechSynthesisWrapper::SpeechSynthesisWrapper(const Napi::CallbackInfo& info)
    : Napi::ObjectWrap<SpeechSynthesisWrapper>(info) {
    Napi::Env env = info.Env();
    platform_ = std::unique_ptr<TTSPlatform>(CreatePlatformTTS());
    
    if (!platform_->Initialize()) {
        Napi::Error::New(env, "Failed to initialize TTS platform").ThrowAsJavaScriptException();
    }
}

SpeechSynthesisWrapper::~SpeechSynthesisWrapper() {
    if (platform_) {
        platform_->Shutdown();
    }
    if (tsfn_) {
        tsfn_.Release();
    }
}

Napi::Value SpeechSynthesisWrapper::GetVoices(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    
    std::vector<Voice> voices = platform_->GetVoices();
    Napi::Array result = Napi::Array::New(env, voices.size());
    
    for (size_t i = 0; i < voices.size(); i++) {
        Napi::Object voice = Napi::Object::New(env);
        voice.Set("name", voices[i].name);
        voice.Set("lang", voices[i].lang);
        voice.Set("localService", voices[i].localService);
        voice.Set("default", voices[i].isDefault);
        voice.Set("voiceURI", voices[i].name);
        result[i] = voice;
    }
    
    return result;
}

Napi::Value SpeechSynthesisWrapper::Speak(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    
    if (info.Length() < 1 || !info[0].IsObject()) {
        Napi::TypeError::New(env, "Object expected").ThrowAsJavaScriptException();
        return env.Null();
    }
    
    Napi::Object params = info[0].As<Napi::Object>();
    Napi::Function callback = info[1].As<Napi::Function>();
    
    UtteranceParams utterance;
    utterance.text = params.Get("text").As<Napi::String>().Utf8Value();
    
    if (params.Has("lang")) {
        utterance.lang = params.Get("lang").As<Napi::String>().Utf8Value();
    }
    if (params.Has("voice")) {
        utterance.voiceName = params.Get("voice").As<Napi::String>().Utf8Value();
    }
    
    utterance.rate = params.Has("rate") ? params.Get("rate").As<Napi::Number>().FloatValue() : 1.0f;
    utterance.pitch = params.Has("pitch") ? params.Get("pitch").As<Napi::Number>().FloatValue() : 1.0f;
    utterance.volume = params.Has("volume") ? params.Get("volume").As<Napi::Number>().FloatValue() : 1.0f;
    
    // Create thread-safe function for callbacks
    tsfn_ = Napi::ThreadSafeFunction::New(
        env,
        callback,
        "SpeechCallback",
        0,
        1
    );
    
    // Speak with callback
    bool success = platform_->Speak(utterance, [this](const SpeechEvent& event) {
        auto callback = [event](Napi::Env env, Napi::Function jsCallback) {
            Napi::Object eventObj = Napi::Object::New(env);
            
            std::string type;
            switch (event.type) {
                case EVENT_START: type = "start"; break;
                case EVENT_END: type = "end"; break;
                case EVENT_WORD: type = "word"; break;
                case EVENT_SENTENCE: type = "sentence"; break;
                case EVENT_MARK: type = "mark"; break;
                case EVENT_BOUNDARY: type = "boundary"; break;
                case EVENT_ERROR: type = "error"; break;
                case EVENT_PAUSE: type = "pause"; break;
                case EVENT_RESUME: type = "resume"; break;
            }
            
            eventObj.Set("type", type);
            eventObj.Set("charIndex", event.charIndex);
            eventObj.Set("charLength", event.charLength);
            eventObj.Set("name", event.name);
            eventObj.Set("elapsedTime", event.elapsedTime);
            
            jsCallback.Call({eventObj});
        };
        
        tsfn_.NonBlockingCall(callback);
    });
    
    return Napi::Boolean::New(env, success);
}

Napi::Value SpeechSynthesisWrapper::Cancel(const Napi::CallbackInfo& info) {
    platform_->Cancel();
    return info.Env().Undefined();
}

Napi::Value SpeechSynthesisWrapper::Pause(const Napi::CallbackInfo& info) {
    platform_->Pause();
    return info.Env().Undefined();
}

Napi::Value SpeechSynthesisWrapper::Resume(const Napi::CallbackInfo& info) {
    platform_->Resume();
    return info.Env().Undefined();
}

Napi::Value SpeechSynthesisWrapper::IsSpeaking(const Napi::CallbackInfo& info) {
    return Napi::Boolean::New(info.Env(), platform_->IsSpeaking());
}

Napi::Value SpeechSynthesisWrapper::IsPaused(const Napi::CallbackInfo& info) {
    return Napi::Boolean::New(info.Env(), platform_->IsPaused());
}

Napi::Object InitAll(Napi::Env env, Napi::Object exports) {
    return SpeechSynthesisWrapper::Init(env, exports);
}

NODE_API_MODULE(speech_synthesis_native, InitAll)
