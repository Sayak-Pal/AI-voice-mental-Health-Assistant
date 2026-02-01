/**
 * Main Application Controller
 * Initializes and coordinates all components of the Mental Health Screening Assistant
 */

class MentalHealthApp {
    constructor() {
        this.voiceEngine = null;
        this.avatar = null;
        this.safetyMonitor = null;
        this.stateMachine = null;
        this.sessionId = null;
        
        // DOM elements
        this.micButton = document.getElementById('mic-button');
        this.textInputToggle = document.getElementById('text-input-toggle');
        this.textInputContainer = document.getElementById('text-input-container');
        this.textInput = document.getElementById('text-input');
        this.sendTextButton = document.getElementById('send-text-button');
        this.compatibilityWarning = document.getElementById('compatibility-warning');
        this.conversationHistory = document.getElementById('conversation-history');
        
        this.initialize();
    }
    
    /**
     * Initialize the application
     */
    async initialize() {
        try {
            // Initialize voice engine
            this.voiceEngine = new VoiceEngine();
            this.setupVoiceEngineHandlers();
            
            // Initialize other components
            this.avatar = new AvatarComponent();
            this.safetyMonitor = new SafetyMonitor();
            this.stateMachine = new StateMachine();
            
            // Check browser compatibility
            this.checkCompatibility();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Request microphone permission and enable controls
            await this.requestMicrophonePermission();
            
            console.log('Mental Health Screening Assistant initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize application:', error);
            this.showCompatibilityWarning();
            this.enableTextFallback();
        }
    }
    
    /**
     * Check browser compatibility and show warnings if needed
     */
    checkCompatibility() {
        const support = this.voiceEngine.isSupported;
        
        if (!support.full) {
            this.showCompatibilityWarning();
            
            if (!support.recognition) {
                console.warn('Speech recognition not supported');
            }
            
            if (!support.synthesis) {
                console.warn('Speech synthesis not supported');
            }
        }
        
        // Always show text input toggle as fallback
        this.textInputToggle.style.display = 'block';
    }
    
    /**
     * Show browser compatibility warning
     */
    showCompatibilityWarning() {
        this.compatibilityWarning.style.display = 'block';
    }
    
    /**
     * Request microphone permission
     */
    async requestMicrophonePermission() {
        try {
            await navigator.mediaDevices.getUserMedia({ audio: true });
            this.enableMicrophoneButton();
        } catch (error) {
            console.error('Microphone permission denied:', error);
            this.micButton.textContent = 'Microphone access denied';
            this.enableTextFallback();
        }
    }
    
    /**
     * Enable microphone button
     */
    enableMicrophoneButton() {
        this.micButton.disabled = false;
        this.micButton.innerHTML = '<span class="mic-icon">🎤</span><span class="mic-text">Click to speak</span>';
    }
    
    /**
     * Enable text input fallback
     */
    enableTextFallback() {
        this.textInputContainer.style.display = 'flex';
        this.textInputToggle.textContent = 'Voice not available - using text';
        this.textInputToggle.disabled = true;
    }
    
    /**
     * Set up voice engine event handlers
     */
    setupVoiceEngineHandlers() {
        this.voiceEngine.onListeningStart = () => {
            this.micButton.classList.add('listening');
            this.micButton.innerHTML = '<span class="mic-icon">🎤</span><span class="mic-text">Listening...</span>';
            this.avatar.setState('LISTENING');
        };
        
        this.voiceEngine.onListeningEnd = () => {
            this.micButton.classList.remove('listening');
            this.micButton.innerHTML = '<span class="mic-icon">🎤</span><span class="mic-text">Click to speak</span>';
            this.avatar.setState('THINKING');
        };
        
        this.voiceEngine.onSpeechResult = (transcript, confidence) => {
            this.handleUserInput(transcript);
        };
        
        this.voiceEngine.onSpeechError = (error, message) => {
            console.error('Speech recognition error:', error, message);
            this.avatar.setState('IDLE');
            this.addMessageToHistory('system', 'Sorry, I had trouble hearing you. Please try again or use text input.');
        };
        
        this.voiceEngine.onSpeechStart = (text) => {
            this.avatar.setState('SPEAKING');
        };
        
        this.voiceEngine.onSpeechEnd = (text) => {
            this.avatar.setState('IDLE');
        };
    }
    
    /**
     * Set up DOM event listeners
     */
    setupEventListeners() {
        // Microphone button
        this.micButton.addEventListener('click', () => {
            if (this.voiceEngine.isListening) {
                this.voiceEngine.stopListening();
            } else {
                this.startListening();
            }
        });
        
        // Text input toggle
        this.textInputToggle.addEventListener('click', () => {
            const isVisible = this.textInputContainer.style.display === 'flex';
            this.textInputContainer.style.display = isVisible ? 'none' : 'flex';
            this.textInputToggle.textContent = isVisible ? 'Use text instead' : 'Hide text input';
            
            if (!isVisible) {
                this.textInput.focus();
            }
        });
        
        // Text input
        this.textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendTextMessage();
            }
        });
        
        this.sendTextButton.addEventListener('click', () => {
            this.sendTextMessage();
        });
    }
    
    /**
     * Start listening for voice input
     */
    async startListening() {
        try {
            await this.voiceEngine.startListening();
        } catch (error) {
            console.error('Failed to start listening:', error);
            this.addMessageToHistory('system', 'Unable to access microphone. Please use text input instead.');
            this.enableTextFallback();
        }
    }
    
    /**
     * Send text message
     */
    sendTextMessage() {
        const text = this.textInput.value.trim();
        if (text) {
            this.handleUserInput(text);
            this.textInput.value = '';
        }
    }
    
    /**
     * Handle user input (voice or text)
     */
    async handleUserInput(userText) {
        // Add user message to conversation
        this.addMessageToHistory('user', userText);
        
        // Check for crisis indicators
        const crisisLevel = this.safetyMonitor.checkForCrisis(userText);
        if (crisisLevel === 'CRITICAL') {
            this.handleCrisisResponse();
            return;
        }
        
        // Set thinking state
        this.avatar.setState('THINKING');
        
        try {
            // Send to backend for processing (placeholder for now)
            const response = await this.processUserMessage(userText);
            
            // Add system response to conversation
            this.addMessageToHistory('system', response);
            
            // Speak the response if synthesis is supported
            if (this.voiceEngine.isSupported.synthesis) {
                await this.voiceEngine.speak(response);
            }
            
        } catch (error) {
            console.error('Error processing user message:', error);
            this.addMessageToHistory('system', 'I apologize, but I encountered an error. Please try again.');
            this.avatar.setState('IDLE');
        }
    }
    
    /**
     * Process user message (placeholder - will integrate with backend)
     */
    async processUserMessage(userText) {
        // Placeholder response - will be replaced with actual API call
        return "Thank you for sharing that with me. I'm here to help you with a mental health screening. This is just a placeholder response while we set up the system.";
    }
    
    /**
     * Handle crisis response
     */
    handleCrisisResponse() {
        const crisisModal = document.getElementById('crisis-modal');
        crisisModal.style.display = 'flex';
        
        const crisisMessage = "I'm concerned about what you've shared. Please reach out for immediate support. You don't have to go through this alone.";
        this.addMessageToHistory('system', crisisMessage);
        
        if (this.voiceEngine.isSupported.synthesis) {
            this.voiceEngine.speak(crisisMessage);
        }
        
        this.avatar.setState('IDLE');
    }
    
    /**
     * Add message to conversation history
     */
    addMessageToHistory(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `${sender}-message`;
        
        const messageContent = document.createElement('p');
        messageContent.textContent = message;
        messageDiv.appendChild(messageContent);
        
        this.conversationHistory.appendChild(messageDiv);
        
        // Scroll to bottom
        this.conversationHistory.scrollTop = this.conversationHistory.scrollHeight;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.mentalHealthApp = new MentalHealthApp();
});