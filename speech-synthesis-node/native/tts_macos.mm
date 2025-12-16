// macOS Implementation using AVSpeechSynthesizer
#ifdef __APPLE__

#include "speech_synthesis.h"
#import <AVFoundation/AVFoundation.h>
#import <Foundation/Foundation.h>
#include <dispatch/dispatch.h>

namespace speech_synthesis {

@interface SpeechDelegate : NSObject<AVSpeechSynthesizerDelegate>
@property (nonatomic, copy) void(^eventCallback)(const SpeechEvent&);
@property (nonatomic, assign) std::string* currentText;
@end

@implementation SpeechDelegate

- (void)speechSynthesizer:(AVSpeechSynthesizer *)synthesizer 
        didStartSpeechUtterance:(AVSpeechUtterance *)utterance {
    if (self.eventCallback) {
        SpeechEvent event;
        event.type = EVENT_START;
        event.charIndex = 0;
        event.charLength = 0;
        event.elapsedTime = 0.0f;
        self.eventCallback(event);
    }
}

- (void)speechSynthesizer:(AVSpeechSynthesizer *)synthesizer 
        didFinishSpeechUtterance:(AVSpeechUtterance *)utterance {
    if (self.eventCallback) {
        SpeechEvent event;
        event.type = EVENT_END;
        event.charIndex = self.currentText ? (int)self.currentText->length() : 0;
        event.charLength = 0;
        event.elapsedTime = 0.0f;
        self.eventCallback(event);
    }
}

- (void)speechSynthesizer:(AVSpeechSynthesizer *)synthesizer 
        willSpeakRangeOfSpeechString:(NSRange)characterRange 
        utterance:(AVSpeechUtterance *)utterance {
    if (self.eventCallback) {
        SpeechEvent event;
        event.type = EVENT_WORD;
        event.charIndex = (int)characterRange.location;
        event.charLength = (int)characterRange.length;
        event.elapsedTime = 0.0f;
        self.eventCallback(event);
    }
}

- (void)speechSynthesizer:(AVSpeechSynthesizer *)synthesizer 
        didPauseSpeechUtterance:(AVSpeechUtterance *)utterance {
    if (self.eventCallback) {
        SpeechEvent event;
        event.type = EVENT_PAUSE;
        event.charIndex = 0;
        event.charLength = 0;
        event.elapsedTime = 0.0f;
        self.eventCallback(event);
    }
}

- (void)speechSynthesizer:(AVSpeechSynthesizer *)synthesizer 
        didContinueSpeechUtterance:(AVSpeechUtterance *)utterance {
    if (self.eventCallback) {
        SpeechEvent event;
        event.type = EVENT_RESUME;
        event.charIndex = 0;
        event.charLength = 0;
        event.elapsedTime = 0.0f;
        self.eventCallback(event);
    }
}

@end

class MacOSTTS : public TTSPlatform {
public:
    MacOSTTS() : synthesizer_(nil), delegate_(nil), isPaused_(false) {}
    
    ~MacOSTTS() {
        Shutdown();
    }
    
    bool Initialize() override {
        @autoreleasepool {
            synthesizer_ = [[AVSpeechSynthesizer alloc] init];
            delegate_ = [[SpeechDelegate alloc] init];
            synthesizer_.delegate = delegate_;
            return synthesizer_ != nil;
        }
    }
    
    void Shutdown() override {
        @autoreleasepool {
            if (synthesizer_) {
                [synthesizer_ stopSpeakingAtBoundary:AVSpeechBoundaryImmediate];
                synthesizer_.delegate = nil;
                [synthesizer_ release];
                synthesizer_ = nil;
            }
            if (delegate_) {
                [delegate_ release];
                delegate_ = nil;
            }
        }
    }
    
    std::vector<Voice> GetVoices() override {
        std::vector<Voice> voices;
        
        @autoreleasepool {
            NSArray<AVSpeechSynthesisVoice*>* avVoices = [AVSpeechSynthesisVoice speechVoices];
            
            for (AVSpeechSynthesisVoice* avVoice in avVoices) {
                Voice voice;
                voice.name = [avVoice.name UTF8String];
                voice.lang = [avVoice.language UTF8String];
                voice.localService = true;
                voice.isDefault = false;
                voices.push_back(voice);
            }
            
            // Mark default voice
            NSString* defaultLang = [[NSLocale preferredLanguages] firstObject];
            AVSpeechSynthesisVoice* defaultVoice = 
                [AVSpeechSynthesisVoice voiceWithLanguage:defaultLang];
            
            for (auto& voice : voices) {
                if (voice.name == [defaultVoice.name UTF8String]) {
                    voice.isDefault = true;
                    break;
                }
            }
        }
        
        return voices;
    }
    
    bool Speak(const UtteranceParams& params, 
              std::function<void(const SpeechEvent&)> callback) override {
        @autoreleasepool {
            if (!synthesizer_) return false;
            
            NSString* text = [NSString stringWithUTF8String:params.text.c_str()];
            AVSpeechUtterance* utterance = [AVSpeechUtterance speechUtteranceWithString:text];
            
            // Set voice
            if (!params.voiceName.empty()) {
                NSString* voiceName = [NSString stringWithUTF8String:params.voiceName.c_str()];
                AVSpeechSynthesisVoice* voice = nil;
                
                NSArray<AVSpeechSynthesisVoice*>* voices = [AVSpeechSynthesisVoice speechVoices];
                for (AVSpeechSynthesisVoice* v in voices) {
                    if ([v.name isEqualToString:voiceName]) {
                        voice = v;
                        break;
                    }
                }
                
                if (voice) {
                    utterance.voice = voice;
                }
            } else if (!params.lang.empty()) {
                NSString* lang = [NSString stringWithUTF8String:params.lang.c_str()];
                utterance.voice = [AVSpeechSynthesisVoice voiceWithLanguage:lang];
            }
            
            // Set parameters
            // AVSpeechUtterance rate is 0.0 to 1.0, we need to map from 0.1 to 10
            utterance.rate = AVSpeechUtteranceDefaultSpeechRate * params.rate;
            utterance.pitchMultiplier = params.pitch;
            utterance.volume = params.volume;
            
            // Store callback
            currentText_ = params.text;
            delegate_.currentText = &currentText_;
            delegate_.eventCallback = ^(const SpeechEvent& event) {
                callback(event);
            };
            
            [synthesizer_ speakUtterance:utterance];
            isPaused_ = false;
            
            return true;
        }
    }
    
    void Cancel() override {
        @autoreleasepool {
            if (synthesizer_) {
                [synthesizer_ stopSpeakingAtBoundary:AVSpeechBoundaryImmediate];
                isPaused_ = false;
            }
        }
    }
    
    void Pause() override {
        @autoreleasepool {
            if (synthesizer_ && [synthesizer_ isSpeaking]) {
                [synthesizer_ pauseSpeakingAtBoundary:AVSpeechBoundaryImmediate];
                isPaused_ = true;
            }
        }
    }
    
    void Resume() override {
        @autoreleasepool {
            if (synthesizer_ && isPaused_) {
                [synthesizer_ continueSpeaking];
                isPaused_ = false;
            }
        }
    }
    
    bool IsSpeaking() override {
        @autoreleasepool {
            return synthesizer_ && [synthesizer_ isSpeaking];
        }
    }
    
    bool IsPaused() override {
        return isPaused_;
    }
    
private:
    AVSpeechSynthesizer* synthesizer_;
    SpeechDelegate* delegate_;
    bool isPaused_;
    std::string currentText_;
};

TTSPlatform* CreatePlatformTTS() {
    return new MacOSTTS();
}

} // namespace speech_synthesis

#endif // __APPLE__
