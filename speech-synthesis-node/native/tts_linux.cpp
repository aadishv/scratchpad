// Linux Implementation using speech-dispatcher (libspeechd)
#ifdef __linux__

#include "speech_synthesis.h"
#include <libspeechd.h>
#include <string>
#include <vector>
#include <map>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <cstring>

namespace speech_synthesis {

class LinuxTTS : public TTSPlatform {
public:
    LinuxTTS() 
        : connection_(nullptr),
          speaking_(false),
          paused_(false),
          currentMsgId_(-1),
          currentCharIndex_(0) {}
    
    ~LinuxTTS() {
        Shutdown();
    }
    
    bool Initialize() override {
        // Connect to speech-dispatcher
        connection_ = spd_open("speech-synthesis-node", nullptr, nullptr, SPD_MODE_THREADED);
        
        if (!connection_) {
            return false;
        }

        // Set up callbacks
        connection_->callback_begin = OnSpeechStarted;
        connection_->callback_end = OnSpeechFinished;
        connection_->callback_cancel = OnSpeechCancelled;
        connection_->callback_pause = OnSpeechPaused;
        connection_->callback_resume = OnSpeechResumed;

        // Enable callbacks
        spd_set_notification_on(connection_, SPD_BEGIN);
        spd_set_notification_on(connection_, SPD_END);
        spd_set_notification_on(connection_, SPD_CANCEL);
        spd_set_notification_on(connection_, SPD_PAUSE);
        spd_set_notification_on(connection_, SPD_RESUME);

        return true;
    }
    
    void Shutdown() override {
        if (connection_) {
            spd_close(connection_);
            connection_ = nullptr;
        }
    }
    
    std::vector<Voice> GetVoices() override {
        std::vector<Voice> voices;
        
        if (!connection_) {
            return voices;
        }

        // Get available voices
        char** modules = nullptr;
        SPDVoice** voiceList = spd_list_synthesis_voices(connection_);
        
        if (voiceList) {
            for (int i = 0; voiceList[i] != nullptr; i++) {
                Voice voice;
                
                if (voiceList[i]->name) {
                    voice.name = voiceList[i]->name;
                }
                
                if (voiceList[i]->language) {
                    voice.lang = voiceList[i]->language;
                    
                    // Append variant if present
                    if (voiceList[i]->variant) {
                        voice.lang += "-";
                        voice.lang += voiceList[i]->variant;
                    }
                }
                
                voice.localService = true;
                voice.isDefault = (i == 0); // First voice is default
                
                voices.push_back(voice);
            }
            
            free_spd_voices(voiceList);
        }

        // If no voices found, add a default one
        if (voices.empty()) {
            Voice voice;
            voice.name = "Default";
            voice.lang = "en-US";
            voice.localService = true;
            voice.isDefault = true;
            voices.push_back(voice);
        }

        return voices;
    }
    
    bool Speak(const UtteranceParams& params, 
              std::function<void(const SpeechEvent&)> callback) override {
        if (!connection_) {
            return false;
        }

        std::lock_guard<std::mutex> lock(mutex_);

        // Set voice if specified
        if (!params.voiceName.empty()) {
            // Try to set voice by name
            // speech-dispatcher uses separate module/voice/language settings
            // This is a simplified version - might need refinement
            spd_set_voice_type(connection_, SPD_MALE1); // Default fallback
            
            // Parse voice name to extract module and language if formatted
            // For now, just use the name as-is
        }

        // Set language
        if (!params.lang.empty()) {
            std::string langCode = params.lang;
            // Convert from BCP-47 format (en-US) to speech-dispatcher format
            size_t dashPos = langCode.find('-');
            if (dashPos != std::string::npos) {
                std::string lang = langCode.substr(0, dashPos);
                std::string variant = langCode.substr(dashPos + 1);
                spd_set_language(connection_, lang.c_str());
            } else {
                spd_set_language(connection_, langCode.c_str());
            }
        }

        // Set rate (-100 to 100 in speech-dispatcher, we have 0.1 to 10)
        // Map: 0.1->-100, 1.0->0, 10.0->100
        int spdRate = 0;
        if (params.rate < 1.0f) {
            spdRate = static_cast<int>((params.rate - 1.0f) * 100.0f);
        } else {
            spdRate = static_cast<int>((params.rate - 1.0f) * 100.0f / 9.0f);
        }
        spdRate = std::max(-100, std::min(100, spdRate));
        spd_set_voice_rate(connection_, spdRate);

        // Set pitch (-100 to 100 in speech-dispatcher, we have 0.0 to 2.0)
        // Map: 0.0->-100, 1.0->0, 2.0->100
        int spdPitch = static_cast<int>((params.pitch - 1.0f) * 100.0f);
        spdPitch = std::max(-100, std::min(100, spdPitch));
        spd_set_voice_pitch(connection_, spdPitch);

        // Set volume (-100 to 100 in speech-dispatcher, we have 0.0 to 1.0)
        // Map: 0.0->-100, 1.0->100
        int spdVolume = static_cast<int>(params.volume * 200.0f - 100.0f);
        spdVolume = std::max(-100, std::min(100, spdVolume));
        spd_set_volume(connection_, spdVolume);

        // Store callback and text for event handling
        currentCallback_ = callback;
        currentText_ = params.text;
        currentCharIndex_ = 0;
        speaking_ = true;
        paused_ = false;

        // Store instance pointer for callbacks
        instanceMap_[connection_] = this;

        // Speak the text
        currentMsgId_ = spd_say(connection_, SPD_TEXT, params.text.c_str());

        if (currentMsgId_ < 0) {
            speaking_ = false;
            return false;
        }

        // Fire start event immediately
        if (callback) {
            SpeechEvent event;
            event.type = EVENT_START;
            event.charIndex = 0;
            event.charLength = 0;
            event.elapsedTime = 0.0f;
            callback(event);
        }

        // Start monitoring thread for word boundaries (if supported)
        // Note: speech-dispatcher doesn't provide word boundary events by default
        // This is a limitation compared to SAPI and AVSpeechSynthesizer
        std::thread([this, callback, text = params.text]() {
            MonitorSpeech(text, callback);
        }).detach();

        return true;
    }
    
    void Cancel() override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (connection_ && speaking_) {
            spd_cancel(connection_);
            speaking_ = false;
            paused_ = false;
        }
    }
    
    void Pause() override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (connection_ && speaking_ && !paused_) {
            spd_pause(connection_);
            paused_ = true;
        }
    }
    
    void Resume() override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (connection_ && paused_) {
            spd_resume(connection_);
            paused_ = false;
        }
    }
    
    bool IsSpeaking() override {
        return speaking_ && !paused_;
    }
    
    bool IsPaused() override {
        return paused_;
    }

private:
    // Static callbacks for speech-dispatcher
    static void OnSpeechStarted(size_t msg_id, size_t client_id, SPDNotificationType type) {
        // Already handled in Speak()
    }

    static void OnSpeechFinished(size_t msg_id, size_t client_id, SPDNotificationType type) {
        // Handled in MonitorSpeech()
    }

    static void OnSpeechCancelled(size_t msg_id, size_t client_id, SPDNotificationType type) {
        // Handled by Cancel()
    }

    static void OnSpeechPaused(size_t msg_id, size_t client_id, SPDNotificationType type) {
        // Handled by Pause()
    }

    static void OnSpeechResumed(size_t msg_id, size_t client_id, SPDNotificationType type) {
        // Handled by Resume()
    }

    void MonitorSpeech(const std::string& text, std::function<void(const SpeechEvent&)> callback) {
        if (!callback) return;

        // Simulate word boundaries by splitting text
        // This is a workaround since speech-dispatcher doesn't provide word events
        std::vector<std::string> words;
        std::string word;
        int charPos = 0;
        
        for (size_t i = 0; i <= text.length(); i++) {
            if (i == text.length() || text[i] == ' ' || text[i] == '\n' || text[i] == '\t') {
                if (!word.empty()) {
                    words.push_back(word);
                    word.clear();
                }
                if (i < text.length()) {
                    charPos = i + 1;
                }
            } else {
                if (word.empty()) {
                    charPos = i;
                }
                word += text[i];
            }
        }

        // Estimate timing based on rate
        // Approximate words per minute at normal rate
        int wordsPerMinute = 150; // Average speaking rate
        double secondsPerWord = 60.0 / wordsPerMinute;

        // Wait a bit for speech to actually start
        std::this_thread::sleep_for(std::chrono::milliseconds(100));

        for (size_t i = 0; i < words.size() && speaking_; i++) {
            // Find word position in original text
            size_t pos = text.find(words[i], currentCharIndex_);
            if (pos != std::string::npos) {
                currentCharIndex_ = static_cast<int>(pos);
                
                SpeechEvent event;
                event.type = EVENT_WORD;
                event.charIndex = currentCharIndex_;
                event.charLength = static_cast<int>(words[i].length());
                event.elapsedTime = static_cast<float>(i * secondsPerWord);
                callback(event);

                currentCharIndex_ += words[i].length();
            }

            // Wait for approximate word duration
            std::this_thread::sleep_for(
                std::chrono::milliseconds(static_cast<int>(secondsPerWord * 1000))
            );

            // Check if still speaking
            if (!speaking_) break;
        }

        // Wait for speech to finish
        while (speaking_) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }

        // Fire end event
        if (callback && speaking_) {
            speaking_ = false;
            
            SpeechEvent event;
            event.type = EVENT_END;
            event.charIndex = static_cast<int>(text.length());
            event.charLength = 0;
            event.elapsedTime = 0.0f;
            callback(event);
        }
    }

    SPDConnection* connection_;
    std::mutex mutex_;
    bool speaking_;
    bool paused_;
    int currentMsgId_;
    int currentCharIndex_;
    std::string currentText_;
    std::function<void(const SpeechEvent&)> currentCallback_;
    
    // Map to find instance from connection pointer (for callbacks)
    static std::map<SPDConnection*, LinuxTTS*> instanceMap_;
};

// Initialize static member
std::map<SPDConnection*, LinuxTTS*> LinuxTTS::instanceMap_;

TTSPlatform* CreatePlatformTTS() {
    return new LinuxTTS();
}

} // namespace speech_synthesis

#endif // __linux__
