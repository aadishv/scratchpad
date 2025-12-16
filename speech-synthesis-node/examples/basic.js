// Example usage demonstrating Web SpeechSynthesis API compatibility
const { speechSynthesis, SpeechSynthesisUtterance } = require('../dist/index');

console.log('Speech Synthesis Demo\n');

// Get available voices
console.log('Available voices:');
const voices = speechSynthesis.getVoices();
voices.forEach((voice, i) => {
    console.log(`${i + 1}. ${voice.name} (${voice.lang}) ${voice.default ? '[DEFAULT]' : ''}`);
});

// Create an utterance
const utterance = new SpeechSynthesisUtterance('Hello! This is a test of the speech synthesis API ported from browser implementations.');

// Set properties (just like in the browser!)
utterance.rate = 1.0;   // 0.1 to 10
utterance.pitch = 1.0;  // 0 to 2
utterance.volume = 1.0; // 0 to 1
utterance.lang = 'en-US';

// Use event listeners (browser-compatible)
utterance.addEventListener('start', (event) => {
    console.log('\nSpeech started');
    console.log('Character index:', event.charIndex);
});

utterance.addEventListener('end', (event) => {
    console.log('\nSpeech ended');
    console.log('Total time:', event.elapsedTime, 'ms');
});

utterance.addEventListener('boundary', (event) => {
    console.log('Word boundary at character', event.charIndex, '(length:', event.charLength + ')');
});

utterance.addEventListener('error', (event) => {
    console.error('Speech error:', event.error);
});

// Or use direct event handlers (also browser-compatible)
utterance.onpause = () => console.log('Speech paused');
utterance.onresume = () => console.log('Speech resumed');

// Speak!
console.log('\nSpeaking...');
speechSynthesis.speak(utterance);

// Demo: pause and resume after 2 seconds
setTimeout(() => {
    console.log('\n--- Pausing speech ---');
    speechSynthesis.pause();
    
    setTimeout(() => {
        console.log('--- Resuming speech ---\n');
        speechSynthesis.resume();
    }, 2000);
}, 2000);

// Check status
setInterval(() => {
    console.log(`Status - Speaking: ${speechSynthesis.speaking}, Paused: ${speechSynthesis.paused}, Pending: ${speechSynthesis.pending}`);
}, 500);

// Queue multiple utterances
setTimeout(() => {
    console.log('\n--- Queueing additional speech ---');
    
    const utterance2 = new SpeechSynthesisUtterance('This is the second utterance.');
    utterance2.onstart = () => console.log('Second utterance started');
    utterance2.onend = () => console.log('Second utterance ended');
    
    const utterance3 = new SpeechSynthesisUtterance('And this is the third utterance.');
    utterance3.onstart = () => console.log('Third utterance started');
    utterance3.onend = () => {
        console.log('Third utterance ended');
        console.log('\n=== Demo complete ===');
        process.exit(0);
    };
    
    speechSynthesis.speak(utterance2);
    speechSynthesis.speak(utterance3);
}, 1000);
