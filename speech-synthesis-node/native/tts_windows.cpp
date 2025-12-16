// Windows Implementation using SAPI (ISpVoice)
#ifdef _WIN32

#include "speech_synthesis.h"
#include <windows.h>
#include <sapi.h>
#include <sphelper.h>
#include <comdef.h>
#include <atlbase.h>
#include <string>
#include <vector>
#include <thread>
#include <mutex>

namespace speech_synthesis {

// Helper to convert UTF-8 to wide string
std::wstring Utf8ToWide(const std::string& str) {
    if (str.empty()) return std::wstring();
    int size = MultiByteToWideChar(CP_UTF8, 0, str.c_str(), -1, nullptr, 0);
    std::wstring result(size, 0);
    MultiByteToWideChar(CP_UTF8, 0, str.c_str(), -1, &result[0], size);
    return result;
}

// Helper to convert wide string to UTF-8
std::string WideToUtf8(const std::wstring& wstr) {
    if (wstr.empty()) return std::string();
    int size = WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), -1, nullptr, 0, nullptr, nullptr);
    std::string result(size, 0);
    WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), -1, &result[0], size, nullptr, nullptr);
    // Remove null terminator
    if (!result.empty() && result.back() == '\0') {
        result.pop_back();
    }
    return result;
}

// SAPI event handler
class SAPIEventSink : public ISpNotifyCallback {
public:
    SAPIEventSink(std::function<void(const SpeechEvent&)> callback) 
        : callback_(callback), refCount_(1) {}

    // IUnknown methods
    STDMETHODIMP QueryInterface(REFIID riid, void** ppv) {
        if (riid == IID_IUnknown || riid == IID_ISpNotifyCallback) {
            *ppv = static_cast<ISpNotifyCallback*>(this);
            AddRef();
            return S_OK;
        }
        *ppv = nullptr;
        return E_NOINTERFACE;
    }

    STDMETHODIMP_(ULONG) AddRef() {
        return InterlockedIncrement(&refCount_);
    }

    STDMETHODIMP_(ULONG) Release() {
        ULONG count = InterlockedDecrement(&refCount_);
        if (count == 0) {
            delete this;
        }
        return count;
    }

    // ISpNotifyCallback method
    STDMETHODIMP NotifyCallback(WPARAM wParam, LPARAM lParam) {
        // Events are processed in ProcessEvents
        return S_OK;
    }

    std::function<void(const SpeechEvent&)> callback_;

private:
    LONG refCount_;
};

class WindowsTTS : public TTSPlatform {
public:
    WindowsTTS() 
        : voice_(nullptr), 
          eventSink_(nullptr),
          speaking_(false),
          paused_(false),
          currentCharIndex_(0) {
        CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    }
    
    ~WindowsTTS() {
        Shutdown();
        CoUninitialize();
    }
    
    bool Initialize() override {
        HRESULT hr = CoCreateInstance(
            CLSID_SpVoice,
            nullptr,
            CLSCTX_ALL,
            IID_ISpVoice,
            (void**)&voice_
        );
        
        if (FAILED(hr) || !voice_) {
            return false;
        }

        // Set event interest
        hr = voice_->SetInterest(
            SPFEI_ALL_TTS_EVENTS,
            SPFEI_ALL_TTS_EVENTS
        );

        return SUCCEEDED(hr);
    }
    
    void Shutdown() override {
        if (voice_) {
            voice_->Speak(nullptr, SPF_PURGEBEFORESPEAK, nullptr);
            voice_->Release();
            voice_ = nullptr;
        }
        if (eventSink_) {
            eventSink_->Release();
            eventSink_ = nullptr;
        }
    }
    
    std::vector<Voice> GetVoices() override {
        std::vector<Voice> voices;
        
        if (!voice_) {
            return voices;
        }

        CComPtr<ISpObjectToken> cpVoiceToken;
        CComPtr<IEnumSpObjectTokens> cpEnum;
        
        HRESULT hr = SpEnumTokens(SPCAT_VOICES, nullptr, nullptr, &cpEnum);
        if (FAILED(hr)) {
            return voices;
        }

        ISpObjectToken* token = nullptr;
        while (cpEnum->Next(1, &token, nullptr) == S_OK) {
            Voice voice;
            
            // Get voice name
            WCHAR* name = nullptr;
            hr = token->GetStringValue(nullptr, &name);
            if (SUCCEEDED(hr) && name) {
                voice.name = WideToUtf8(name);
                CoTaskMemFree(name);
            }

            // Get language
            WCHAR* langId = nullptr;
            hr = token->GetStringValue(L"Language", &langId);
            if (SUCCEEDED(hr) && langId) {
                // Convert language ID to locale string
                LCID lcid = wcstoul(langId, nullptr, 16);
                WCHAR localeName[LOCALE_NAME_MAX_LENGTH];
                if (LCIDToLocaleName(lcid, localeName, LOCALE_NAME_MAX_LENGTH, 0)) {
                    voice.lang = WideToUtf8(localeName);
                } else {
                    voice.lang = "en-US";
                }
                CoTaskMemFree(langId);
            } else {
                voice.lang = "en-US";
            }

            voice.localService = true;
            voice.isDefault = false;

            voices.push_back(voice);
            token->Release();
        }

        // Mark the current voice as default
        CComPtr<ISpObjectToken> currentToken;
        if (SUCCEEDED(voice_->GetVoice(&currentToken)) && currentToken) {
            WCHAR* currentName = nullptr;
            if (SUCCEEDED(currentToken->GetStringValue(nullptr, &currentName)) && currentName) {
                std::string currentNameUtf8 = WideToUtf8(currentName);
                for (auto& v : voices) {
                    if (v.name == currentNameUtf8) {
                        v.isDefault = true;
                        break;
                    }
                }
                CoTaskMemFree(currentName);
            }
        }

        return voices;
    }
    
    bool Speak(const UtteranceParams& params, 
              std::function<void(const SpeechEvent&)> callback) override {
        if (!voice_) {
            return false;
        }

        std::lock_guard<std::mutex> lock(mutex_);

        // Set voice if specified
        if (!params.voiceName.empty()) {
            CComPtr<IEnumSpObjectTokens> cpEnum;
            HRESULT hr = SpEnumTokens(SPCAT_VOICES, nullptr, nullptr, &cpEnum);
            
            if (SUCCEEDED(hr)) {
                ISpObjectToken* token = nullptr;
                std::wstring targetName = Utf8ToWide(params.voiceName);
                
                while (cpEnum->Next(1, &token, nullptr) == S_OK) {
                    WCHAR* name = nullptr;
                    if (SUCCEEDED(token->GetStringValue(nullptr, &name)) && name) {
                        if (targetName == name) {
                            voice_->SetVoice(token);
                            CoTaskMemFree(name);
                            token->Release();
                            break;
                        }
                        CoTaskMemFree(name);
                    }
                    token->Release();
                }
            }
        }

        // Set rate (-10 to 10 in SAPI, we have 0.1 to 10)
        // Map: 0.1->-10, 1.0->0, 10.0->10
        long sapiRate = 0;
        if (params.rate < 1.0f) {
            sapiRate = static_cast<long>((params.rate - 1.0f) * 10.0f);
        } else {
            sapiRate = static_cast<long>((params.rate - 1.0f) * 10.0f / 9.0f);
        }
        sapiRate = max(-10, min(10, sapiRate));
        voice_->SetRate(sapiRate);

        // Set volume (0 to 100 in SAPI, we have 0.0 to 1.0)
        USHORT sapiVolume = static_cast<USHORT>(params.volume * 100.0f);
        voice_->SetVolume(sapiVolume);

        // SAPI doesn't support pitch directly, would need XML markup

        // Create event sink for this utterance
        if (eventSink_) {
            eventSink_->Release();
        }
        eventSink_ = new SAPIEventSink(callback);
        voice_->SetNotifySink(eventSink_);

        // Start event processing thread
        currentCallback_ = callback;
        currentText_ = params.text;
        currentCharIndex_ = 0;
        speaking_ = true;
        paused_ = false;

        // Fire start event
        if (callback) {
            SpeechEvent event;
            event.type = EVENT_START;
            event.charIndex = 0;
            event.charLength = 0;
            event.elapsedTime = 0.0f;
            callback(event);
        }

        // Speak asynchronously
        std::wstring text = Utf8ToWide(params.text);
        
        // Start event monitoring thread
        std::thread([this, callback]() {
            ProcessEvents(callback);
        }).detach();

        HRESULT hr = voice_->Speak(
            text.c_str(),
            SPF_ASYNC | SPF_PURGEBEFORESPEAK,
            nullptr
        );

        return SUCCEEDED(hr);
    }
    
    void Cancel() override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (voice_) {
            voice_->Speak(nullptr, SPF_PURGEBEFORESPEAK, nullptr);
            speaking_ = false;
            paused_ = false;
        }
    }
    
    void Pause() override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (voice_ && speaking_ && !paused_) {
            voice_->Pause();
            paused_ = true;
            
            if (currentCallback_) {
                SpeechEvent event;
                event.type = EVENT_PAUSE;
                event.charIndex = currentCharIndex_;
                event.charLength = 0;
                event.elapsedTime = 0.0f;
                currentCallback_(event);
            }
        }
    }
    
    void Resume() override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (voice_ && paused_) {
            voice_->Resume();
            paused_ = false;
            
            if (currentCallback_) {
                SpeechEvent event;
                event.type = EVENT_RESUME;
                event.charIndex = currentCharIndex_;
                event.charLength = 0;
                event.elapsedTime = 0.0f;
                currentCallback_(event);
            }
        }
    }
    
    bool IsSpeaking() override {
        if (!voice_) return false;
        
        SPVOICESTATUS status;
        HRESULT hr = voice_->GetStatus(&status, nullptr);
        if (SUCCEEDED(hr)) {
            return status.dwRunningState == SPRS_IS_SPEAKING;
        }
        return false;
    }
    
    bool IsPaused() override {
        return paused_;
    }

private:
    void ProcessEvents(std::function<void(const SpeechEvent&)> callback) {
        if (!voice_ || !callback) return;

        while (speaking_) {
            CSpEvent event;
            HRESULT hr = event.GetFrom(voice_);
            
            if (hr == S_FALSE) {
                // No more events, check if still speaking
                if (!IsSpeaking()) {
                    speaking_ = false;
                    
                    // Fire end event
                    SpeechEvent endEvent;
                    endEvent.type = EVENT_END;
                    endEvent.charIndex = static_cast<int>(currentText_.length());
                    endEvent.charLength = 0;
                    endEvent.elapsedTime = 0.0f;
                    callback(endEvent);
                    break;
                }
                Sleep(10);
                continue;
            }

            if (FAILED(hr)) break;

            switch (event.eEventId) {
                case SPEI_START_INPUT_STREAM:
                    // Already fired in Speak()
                    break;

                case SPEI_WORD_BOUNDARY: {
                    SPVOICESTATUS status;
                    voice_->GetStatus(&status, nullptr);
                    
                    SpeechEvent wordEvent;
                    wordEvent.type = EVENT_WORD;
                    wordEvent.charIndex = static_cast<int>(event.lParam);
                    wordEvent.charLength = static_cast<int>(event.wParam);
                    wordEvent.elapsedTime = 0.0f;
                    
                    currentCharIndex_ = wordEvent.charIndex;
                    callback(wordEvent);
                    break;
                }

                case SPEI_SENTENCE_BOUNDARY: {
                    SpeechEvent sentenceEvent;
                    sentenceEvent.type = EVENT_SENTENCE;
                    sentenceEvent.charIndex = static_cast<int>(event.lParam);
                    sentenceEvent.charLength = static_cast<int>(event.wParam);
                    sentenceEvent.elapsedTime = 0.0f;
                    callback(sentenceEvent);
                    break;
                }

                case SPEI_END_INPUT_STREAM:
                    speaking_ = false;
                    // End event fired above
                    break;

                default:
                    break;
            }
        }
    }

    ISpVoice* voice_;
    SAPIEventSink* eventSink_;
    std::mutex mutex_;
    bool speaking_;
    bool paused_;
    std::string currentText_;
    int currentCharIndex_;
    std::function<void(const SpeechEvent&)> currentCallback_;
};

TTSPlatform* CreatePlatformTTS() {
    return new WindowsTTS();
}

} // namespace speech_synthesis

#endif // _WIN32
