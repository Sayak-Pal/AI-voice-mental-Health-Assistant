/**
 * Voice Engine - Web Speech API Integration
 * Handles speech recognition and synthesis with browser compatibility detection
 */

class VoiceEngine {
    constructor() {
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isListening = false;
        this.isSupported = this.checkSupport();
        this.currentUtterance = null;
        this.speechQueue = [];
        this.isProcessingQueue = false;
        
        // Timeout and retry configuration
        this.timeouts = {
            listening: 10000, // 10 seconds
            silence: 5000,    // 5 seconds of silence
            retry: 3          // Maximum retry attempts
        };
        
        this.listeningTimeout = null;
        this.silenceTimeout = null;
        this.retryCount = 0;
        
        // Configuration
        this.config = {
            language: 'en-US',
            continuous: false,
            interimResults: false,
            maxAlternatives: 1
        };
        
        this.initializeRecognition();
    }
    
    /**
     * Check if Web Speech API is supported in current browser
     */
    checkSupport() {
        const hasRecognition = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
        const hasSynthesis = 'speechSynthesis' in window;
        
        // Check for specific browser limitations
        const userAgent = navigator.userAgent.toLowerCase();
        const isFirefox = userAgent.includes('firefox');
        const isSafari = userAgent.includes('safari') && !userAgent.includes('chrome');
        const isEdge = userAgent.includes('edge');
        
        return {
            recognition: hasRecognition,
            synthesis: hasSynthesis,
            full: hasRecognition && hasSynthesis,
            limitations: {
                firefox: isFirefox, // Limited speech recognition support
                safari: isSafari,   // May have synthesis issues
                edge: isEdge        // May have compatibility issues
            }
        };
    }
    
    /**
     * Initialize speech recognition with proper browser prefixes
     */
    initializeRecognition() {
        if (!this.isSupported.recognition) {
            console.warn('Speech recognition not supported in this browser');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure recognition settings
        this.recognition.continuous = this.config.continuous;
        this.recognition.interimResults = this.config.interimResults;
        this.recognition.lang = this.config.language;
        this.recognition.maxAlternatives = this.config.maxAlternatives;
        
        // Set up event handlers
        this.setupRecognitionHandlers();
    }
    
    /**
     * Set up speech recognition event handlers
     */
    setupRecognitionHandlers() {
        if (!this.recognition) return;
        
        this.recognition.onstart = () => {
            this.isListening = true;
            this.retryCount = 0;
            this.startListeningTimeout();
            this.onListeningStart?.();
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            this.clearTimeouts();
            this.onListeningEnd?.();
        };
        
        this.recognition.onresult = (event) => {
            this.clearTimeouts();
            const result = event.results[0];
            if (result.isFinal) {
                const transcript = result[0].transcript.trim();
                this.onSpeechResult?.(transcript, result[0].confidence);
            }
        };
        
        this.recognition.onerror = (event) => {
            this.isListening = false;
            this.clearTimeouts();
            this.handleRecognitionError(event.error, event.message);
        };
        
        this.recognition.onnomatch = () => {
            this.clearTimeouts();
            this.handleNoMatch();
        };
        
        this.recognition.onspeechstart = () => {
            // User started speaking, reset silence timeout
            this.clearSilenceTimeout();
        };
        
        this.recognition.onspeechend = () => {
            // User stopped speaking, start silence timeout
            this.startSilenceTimeout();
        };
    }
    
    /**
     * Start listening for speech input
     */
    async startListening() {
        if (!this.isSupported.recognition) {
            throw new Error('Speech recognition not supported');
        }
        
        if (this.isListening) {
            console.warn('Already listening');
            return;
        }
        
        try {
            // Request microphone permission
            await navigator.mediaDevices.getUserMedia({ audio: true });
            this.recognition.start();
        } catch (error) {
            throw new Error(`Microphone access denied: ${error.message}`);
        }
    }
    
    /**
     * Stop listening for speech input
     */
    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
        this.clearTimeouts();
    }
    
    /**
     * Start timeout for listening session
     */
    startListeningTimeout() {
        this.listeningTimeout = setTimeout(() => {
            if (this.isListening) {
                this.stopListening();
                this.onListeningTimeout?.();
            }
        }, this.timeouts.listening);
    }
    
    /**
     * Start timeout for silence detection
     */
    startSilenceTimeout() {
        this.silenceTimeout = setTimeout(() => {
            if (this.isListening) {
                this.stopListening();
                this.onSilenceTimeout?.();
            }
        }, this.timeouts.silence);
    }
    
    /**
     * Clear all active timeouts
     */
    clearTimeouts() {
        if (this.listeningTimeout) {
            clearTimeout(this.listeningTimeout);
            this.listeningTimeout = null;
        }
        this.clearSilenceTimeout();
    }
    
    /**
     * Clear silence timeout
     */
    clearSilenceTimeout() {
        if (this.silenceTimeout) {
            clearTimeout(this.silenceTimeout);
            this.silenceTimeout = null;
        }
    }
    
    /**
     * Handle recognition errors with retry logic
     */
    handleRecognitionError(error, message) {
        const canRetry = this.retryCount < this.timeouts.retry && 
                        (error === 'network' || error === 'audio-capture' || error === 'aborted');
        
        if (canRetry) {
            this.retryCount++;
            setTimeout(() => {
                this.startListening().catch(err => {
                    this.onSpeechError?.(error, `Retry failed: ${err.message}`);
                });
            }, 1000 * this.retryCount); // Exponential backoff
        } else {
            this.onSpeechError?.(error, message);
            
            // Suggest alternative input method for certain errors
            if (error === 'not-allowed' || error === 'service-not-allowed') {
                this.onAlternativeInputNeeded?.('microphone_denied');
            } else if (error === 'network') {
                this.onAlternativeInputNeeded?.('network_error');
            } else if (error === 'no-speech') {
                this.onAlternativeInputNeeded?.('no_speech_detected');
            }
        }
    }
    
    /**
     * Handle no match scenarios
     */
    handleNoMatch() {
        if (this.retryCount < this.timeouts.retry) {
            this.retryCount++;
            this.onSpeechNoMatch?.();
            // Auto-retry for no match
            setTimeout(() => {
                this.startListening().catch(err => {
                    this.onSpeechError?.('retry-failed', err.message);
                });
            }, 500);
        } else {
            this.onAlternativeInputNeeded?.('speech_not_recognized');
        }
    }
    
    /**
     * Get fallback options when speech recognition fails
     */
    getFallbackOptions() {
        const options = [];
        
        if (!this.isSupported.recognition) {
            options.push({
                type: 'text_input',
                message: 'Speech recognition is not supported in your browser. Please use text input instead.',
                action: 'show_text_input'
            });
        }
        
        if (this.isSupported.limitations.firefox) {
            options.push({
                type: 'browser_limitation',
                message: 'Firefox has limited speech recognition support. Consider using Chrome or Edge for better experience.',
                action: 'show_browser_warning'
            });
        }
        
        return options;
    }
    
    /**
     * Convert text to speech with queue management
     */
    speak(text, options = {}) {
        if (!this.isSupported.synthesis) {
            throw new Error('Speech synthesis not supported');
        }
        
        const speechItem = {
            text,
            options: {
                language: options.language || this.config.language,
                rate: options.rate || 0.9,
                pitch: options.pitch || 1.0,
                volume: options.volume || 0.8,
                voice: options.voice || this.preferredVoice
            },
            priority: options.priority || 'normal' // 'high', 'normal', 'low'
        };
        
        if (options.priority === 'high') {
            // High priority items interrupt current speech and go to front of queue
            this.stopSpeaking();
            this.speechQueue.unshift(speechItem);
        } else {
            // Normal and low priority items are added to queue
            this.speechQueue.push(speechItem);
        }
        
        if (!this.isProcessingQueue) {
            this.processQueue();
        }
        
        return new Promise((resolve, reject) => {
            speechItem.resolve = resolve;
            speechItem.reject = reject;
        });
    }
    
    /**
     * Process the speech queue
     */
    async processQueue() {
        if (this.isProcessingQueue || this.speechQueue.length === 0) {
            return;
        }
        
        this.isProcessingQueue = true;
        
        while (this.speechQueue.length > 0) {
            const speechItem = this.speechQueue.shift();
            
            try {
                await this.speakImmediate(speechItem);
            } catch (error) {
                speechItem.reject?.(error);
            }
        }
        
        this.isProcessingQueue = false;
    }
    
    /**
     * Speak text immediately without queue management
     */
    speakImmediate(speechItem) {
        return new Promise((resolve, reject) => {
            const { text, options } = speechItem;
            const utterance = new SpeechSynthesisUtterance(text);
            
            // Configure voice settings
            utterance.lang = options.language;
            utterance.rate = options.rate;
            utterance.pitch = options.pitch;
            utterance.volume = options.volume;
            
            // Set voice if specified
            if (options.voice) {
                utterance.voice = options.voice;
            }
            
            // Set up event handlers
            utterance.onstart = () => {
                this.currentUtterance = utterance;
                this.onSpeechStart?.(text);
            };
            
            utterance.onend = () => {
                this.currentUtterance = null;
                this.onSpeechEnd?.(text);
                speechItem.resolve?.();
                resolve();
            };
            
            utterance.onerror = (event) => {
                this.currentUtterance = null;
                this.onSpeechSynthesisError?.(event.error);
                const error = new Error(event.error);
                speechItem.reject?.(error);
                reject(error);
            };
            
            utterance.onpause = () => {
                this.onSpeechPause?.(text);
            };
            
            utterance.onresume = () => {
                this.onSpeechResume?.(text);
            };
            
            this.synthesis.speak(utterance);
        });
    }
    
    /**
     * Stop current speech synthesis and clear queue
     */
    stopSpeaking() {
        if (this.synthesis.speaking) {
            this.synthesis.cancel();
        }
        
        // Clear the queue and reject pending promises
        while (this.speechQueue.length > 0) {
            const item = this.speechQueue.shift();
            item.reject?.(new Error('Speech interrupted'));
        }
        
        this.currentUtterance = null;
        this.isProcessingQueue = false;
    }
    
    /**
     * Pause current speech synthesis
     */
    pauseSpeaking() {
        if (this.synthesis.speaking && !this.synthesis.paused) {
            this.synthesis.pause();
        }
    }
    
    /**
     * Resume paused speech synthesis
     */
    resumeSpeaking() {
        if (this.synthesis.paused) {
            this.synthesis.resume();
        }
    }
    
    /**
     * Check if currently speaking
     */
    isSpeaking() {
        return this.synthesis.speaking;
    }
    
    /**
     * Check if speech is paused
     */
    isPaused() {
        return this.synthesis.paused;
    }
    
    /**
     * Get queue length
     */
    getQueueLength() {
        return this.speechQueue.length;
    }
    
    /**
     * Clear speech queue without stopping current speech
     */
    clearQueue() {
        while (this.speechQueue.length > 0) {
            const item = this.speechQueue.shift();
            item.reject?.(new Error('Queue cleared'));
        }
    }
    
    /**
     * Get available voices for speech synthesis
     */
    getAvailableVoices() {
        return this.synthesis.getVoices();
    }
    
    /**
     * Set preferred voice for speech synthesis
     */
    setVoice(voiceName) {
        const voices = this.getAvailableVoices();
        const voice = voices.find(v => v.name === voiceName);
        if (voice) {
            this.preferredVoice = voice;
        }
    }
    
    // Event handler properties (to be set by consumers)
    onListeningStart = null;
    onListeningEnd = null;
    onSpeechResult = null;
    onSpeechError = null;
    onSpeechNoMatch = null;
    onSpeechStart = null;
    onSpeechEnd = null;
    onSpeechSynthesisError = null;
    onListeningTimeout = null;
    onSilenceTimeout = null;
    onAlternativeInputNeeded = null;
    onSpeechPause = null;
    onSpeechResume = null;
}