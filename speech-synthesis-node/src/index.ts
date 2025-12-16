// Web SpeechSynthesis API compatible implementation for Node.js/Bun
import { EventEmitter } from 'events';

let nativeBinding: any;

try {
    // Try to load the native binding
    nativeBinding = require('../build/Release/speech_synthesis_native.node');
} catch (err) {
    // Fallback for development or when native module isn't built
    console.warn('Native TTS module not available:', err);
}

export class SpeechSynthesisVoice {
    readonly default: boolean = false;
    readonly lang: string;
    readonly localService: boolean = true;
    readonly name: string;
    readonly voiceURI: string;

    constructor(data: any) {
        this.name = data.name;
        this.lang = data.lang;
        this.localService = data.localService;
        this.default = data.default || false;
        this.voiceURI = data.voiceURI || data.name;
    }
}

export class SpeechSynthesisUtterance extends EventEmitter {
    text: string;
    lang: string = '';
    voice: SpeechSynthesisVoice | null = null;
    volume: number = 1;
    rate: number = 1;
    pitch: number = 1;

    // Event handlers
    onstart: ((event: SpeechSynthesisEvent) => void) | null = null;
    onend: ((event: SpeechSynthesisEvent) => void) | null = null;
    onerror: ((event: SpeechSynthesisErrorEvent) => void) | null = null;
    onpause: ((event: SpeechSynthesisEvent) => void) | null = null;
    onresume: ((event: SpeechSynthesisEvent) => void) | null = null;
    onmark: ((event: SpeechSynthesisEvent) => void) | null = null;
    onboundary: ((event: SpeechSynthesisEvent) => void) | null = null;

    constructor(text?: string) {
        super();
        this.text = text || '';
    }

    // Browser-compatible addEventListener/removeEventListener
    addEventListener(event: string, listener: (...args: any[]) => void): this {
        return this.on(event, listener);
    }

    removeEventListener(event: string, listener: (...args: any[]) => void): this {
        return this.off(event, listener);
    }
}

export interface SpeechSynthesisEvent {
    charIndex: number;
    charLength?: number;
    elapsedTime: number;
    name?: string;
    utterance: SpeechSynthesisUtterance;
    type: string;
}

export interface SpeechSynthesisErrorEvent extends SpeechSynthesisEvent {
    error: string;
}

export class SpeechSynthesis extends EventEmitter {
    private native: any;
    private _pending: boolean = false;
    private _speaking: boolean = false;
    private _paused: boolean = false;
    private utteranceQueue: SpeechSynthesisUtterance[] = [];
    private currentUtterance: SpeechSynthesisUtterance | null = null;
    private voices: SpeechSynthesisVoice[] = [];
    
    // Event handlers
    onvoiceschanged: (() => void) | null = null;

    constructor() {
        super();
        
        if (nativeBinding) {
            this.native = new nativeBinding.SpeechSynthesis();
            this.loadVoices();
        } else {
            console.warn('SpeechSynthesis: Native binding not available. TTS will not work.');
        }
    }

    private loadVoices() {
        if (!this.native) return;
        
        const nativeVoices = this.native.getVoices();
        this.voices = nativeVoices.map((v: any) => new SpeechSynthesisVoice(v));
        
        // Emit voiceschanged event
        if (this.onvoiceschanged) {
            this.onvoiceschanged();
        }
        this.emit('voiceschanged');
    }

    getVoices(): SpeechSynthesisVoice[] {
        return this.voices;
    }

    get speaking(): boolean {
        return this._speaking;
    }

    get pending(): boolean {
        return this.utteranceQueue.length > 0;
    }

    get paused(): boolean {
        return this._paused;
    }

    speak(utterance: SpeechSynthesisUtterance): void {
        if (!this.native) {
            const error: SpeechSynthesisErrorEvent = {
                charIndex: 0,
                elapsedTime: 0,
                utterance,
                type: 'error',
                error: 'Native TTS not available'
            };
            
            if (utterance.onerror) {
                utterance.onerror(error);
            }
            utterance.emit('error', error);
            return;
        }

        this.utteranceQueue.push(utterance);
        
        if (!this._speaking) {
            this.processQueue();
        }
    }

    private processQueue(): void {
        if (this.utteranceQueue.length === 0) {
            this._speaking = false;
            this._pending = false;
            return;
        }

        const utterance = this.utteranceQueue.shift()!;
        this.currentUtterance = utterance;
        this._speaking = true;
        this._pending = this.utteranceQueue.length > 0;

        const params = {
            text: utterance.text,
            lang: utterance.lang || '',
            voice: utterance.voice?.name || '',
            rate: utterance.rate,
            pitch: utterance.pitch,
            volume: utterance.volume
        };

        this.native.speak(params, (event: any) => {
            const synthEvent: SpeechSynthesisEvent = {
                charIndex: event.charIndex || 0,
                charLength: event.charLength,
                elapsedTime: event.elapsedTime || 0,
                name: event.name,
                utterance,
                type: event.type
            };

            // Call event handlers
            switch (event.type) {
                case 'start':
                    if (utterance.onstart) utterance.onstart(synthEvent);
                    utterance.emit('start', synthEvent);
                    break;
                case 'end':
                    if (utterance.onend) utterance.onend(synthEvent);
                    utterance.emit('end', synthEvent);
                    this._speaking = false;
                    this.currentUtterance = null;
                    // Process next utterance
                    this.processQueue();
                    break;
                case 'error':
                    const errorEvent = synthEvent as SpeechSynthesisErrorEvent;
                    errorEvent.error = event.error || 'Unknown error';
                    if (utterance.onerror) utterance.onerror(errorEvent);
                    utterance.emit('error', errorEvent);
                    this._speaking = false;
                    this.currentUtterance = null;
                    this.processQueue();
                    break;
                case 'pause':
                    this._paused = true;
                    if (utterance.onpause) utterance.onpause(synthEvent);
                    utterance.emit('pause', synthEvent);
                    break;
                case 'resume':
                    this._paused = false;
                    if (utterance.onresume) utterance.onresume(synthEvent);
                    utterance.emit('resume', synthEvent);
                    break;
                case 'word':
                case 'boundary':
                    if (utterance.onboundary) utterance.onboundary(synthEvent);
                    utterance.emit('boundary', synthEvent);
                    break;
                case 'mark':
                    if (utterance.onmark) utterance.onmark(synthEvent);
                    utterance.emit('mark', synthEvent);
                    break;
            }
        });
    }

    cancel(): void {
        if (!this.native) return;
        
        this.native.cancel();
        this.utteranceQueue = [];
        this.currentUtterance = null;
        this._speaking = false;
        this._paused = false;
        this._pending = false;
    }

    pause(): void {
        if (!this.native || !this._speaking) return;
        
        this.native.pause();
        this._paused = true;
    }

    resume(): void {
        if (!this.native || !this._paused) return;
        
        this.native.resume();
        this._paused = false;
    }
}

// Create singleton instance to match browser API
let speechSynthesisInstance: SpeechSynthesis | null = null;

export function getSpeechSynthesis(): SpeechSynthesis {
    if (!speechSynthesisInstance) {
        speechSynthesisInstance = new SpeechSynthesis();
    }
    return speechSynthesisInstance;
}

// Export default instance for convenience
export const speechSynthesis = getSpeechSynthesis();

// For browser-like global access (optional)
if (typeof globalThis !== 'undefined') {
    (globalThis as any).SpeechSynthesis = SpeechSynthesis;
    (globalThis as any).SpeechSynthesisUtterance = SpeechSynthesisUtterance;
    (globalThis as any).SpeechSynthesisVoice = SpeechSynthesisVoice;
    (globalThis as any).speechSynthesis = speechSynthesis;
}
