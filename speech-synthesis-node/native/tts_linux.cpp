// Linux Implementation - Stub for demonstration
// In production, this would use speech-dispatcher (libspeechd)
#ifdef __linux__

#include "speech_synthesis.h"
#include <iostream>

namespace speech_synthesis {

class LinuxTTS : public TTSPlatform {
public:
    LinuxTTS() : speaking_(false), paused_(false) {}
    
    ~LinuxTTS() {
        Shutdown();
    }
    
    bool Initialize() override {
        // In a real implementation, this would connect to speech-dispatcher:
        // connection_ = spd_open("speech-synthesis-node", NULL, NULL, SPD_MODE_THREADED);
        std::cerr << "Linux TTS: speech-dispatcher not available in this environment." << std::endl;
        std::cerr << "Install libspeechd-dev to enable real TTS on Linux." << std::endl;
        return true;  // Return true to allow API demonstration
    }
    
    void Shutdown() override {
        // In real implementation: spd_close(connection_);
    }
    
    std::vector<Voice> GetVoices() override {
        std::vector<Voice> voices;
        
        // Stub: Return a fake voice for demonstration
        Voice voice;
        voice.name = "Linux Default (stub)";
        voice.lang = "en-US";
        voice.localService = true;
        voice.isDefault = true;
        voices.push_back(voice);
        
        return voices;
    }
    
    bool Speak(const UtteranceParams& params, 
              std::function<void(const SpeechEvent&)> callback) override {
        
        std::cout << "\n[Linux TTS Stub] Would speak: \"" << params.text << "\"" << std::endl;
        std::cout << "  Rate: " << params.rate << ", Pitch: " << params.pitch 
                  << ", Volume: " << params.volume << std::endl;
        
        if (!params.lang.empty()) {
            std::cout << "  Language: " << params.lang << std::endl;
        }
        if (!params.voiceName.empty()) {
            std::cout << "  Voice: " << params.voiceName << std::endl;
        }
        
        speaking_ = true;
        paused_ = false;
        
        // Simulate events
        if (callback) {
            SpeechEvent startEvent;
            startEvent.type = EVENT_START;
            startEvent.charIndex = 0;
            startEvent.charLength = 0;
            startEvent.elapsedTime = 0.0f;
            callback(startEvent);
            
            // Simulate end event
            SpeechEvent endEvent;
            endEvent.type = EVENT_END;
            endEvent.charIndex = static_cast<int>(params.text.length());
            endEvent.charLength = 0;
            endEvent.elapsedTime = 100.0f;
            callback(endEvent);
        }
        
        speaking_ = false;
        return true;
    }
    
    void Cancel() override {
        speaking_ = false;
        paused_ = false;
        std::cout << "[Linux TTS Stub] Speech cancelled" << std::endl;
    }
    
    void Pause() override {
        if (speaking_) {
            paused_ = true;
            std::cout << "[Linux TTS Stub] Speech paused" << std::endl;
        }
    }
    
    void Resume() override {
        if (paused_) {
            paused_ = false;
            std::cout << "[Linux TTS Stub] Speech resumed" << std::endl;
        }
    }
    
    bool IsSpeaking() override {
        return speaking_;
    }
    
    bool IsPaused() override {
        return paused_;
    }
    
private:
    bool speaking_;
    bool paused_;
};

TTSPlatform* CreatePlatformTTS() {
    return new LinuxTTS();
}

} // namespace speech_synthesis

#endif // __linux__
