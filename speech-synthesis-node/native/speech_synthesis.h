#ifndef SPEECH_SYNTHESIS_H
#define SPEECH_SYNTHESIS_H

#include <string>
#include <vector>
#include <functional>

namespace speech_synthesis {

struct Voice {
    std::string name;
    std::string lang;
    bool localService;
    bool isDefault;
};

struct UtteranceParams {
    std::string text;
    std::string lang;
    std::string voiceName;
    float rate;      // 0.1 to 10
    float pitch;     // 0.0 to 2.0
    float volume;    // 0.0 to 1.0
};

enum EventType {
    EVENT_START,
    EVENT_END,
    EVENT_WORD,
    EVENT_SENTENCE,
    EVENT_MARK,
    EVENT_BOUNDARY,
    EVENT_ERROR,
    EVENT_PAUSE,
    EVENT_RESUME
};

struct SpeechEvent {
    EventType type;
    int charIndex;
    int charLength;
    std::string name;
    float elapsedTime;
};

class TTSPlatform {
public:
    virtual ~TTSPlatform() {}
    
    virtual bool Initialize() = 0;
    virtual void Shutdown() = 0;
    
    virtual std::vector<Voice> GetVoices() = 0;
    virtual bool Speak(const UtteranceParams& params, 
                      std::function<void(const SpeechEvent&)> callback) = 0;
    virtual void Cancel() = 0;
    virtual void Pause() = 0;
    virtual void Resume() = 0;
    virtual bool IsSpeaking() = 0;
    virtual bool IsPaused() = 0;
};

// Platform-specific factory
TTSPlatform* CreatePlatformTTS();

} // namespace speech_synthesis

#endif // SPEECH_SYNTHESIS_H
