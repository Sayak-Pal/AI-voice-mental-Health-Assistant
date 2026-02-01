/**
 * Avatar Component - Visual Feedback System
 * Manages avatar animations and state transitions
 */

class AvatarComponent {
    constructor() {
        this.videoElement = document.getElementById('avatar-video');
        this.statusElement = document.getElementById('avatar-status');
        this.currentState = 'IDLE';
        this.transitionInProgress = false;
        this.stateTimeouts = new Map();
        
        // Animation sources (placeholders - will need actual video files)
        this.animations = {
            IDLE: 'assets/animations/idle.mp4',
            LISTENING: 'assets/animations/listening.mp4',
            SPEAKING: 'assets/animations/speaking.mp4',
            THINKING: 'assets/animations/thinking.mp4'
        };
        
        // Status messages for each state
        this.statusMessages = {
            IDLE: 'Ready to listen',
            LISTENING: 'Listening...',
            SPEAKING: 'Speaking...',
            THINKING: 'Processing...'
        };
        
        // State timeout durations (in milliseconds)
        this.stateTimeouts = {
            LISTENING: 30000, // 30 seconds max listening time
            THINKING: 10000,  // 10 seconds max thinking time
            SPEAKING: 60000   // 60 seconds max speaking time
        };
        
        // Transition animation duration
        this.transitionDuration = 300; // 300ms for smooth transitions
        
        this.initialize();
    }
    
    /**
     * Initialize avatar component
     */
    initialize() {
        // Set initial state
        this.setState('IDLE');
        
        // Handle video loading errors gracefully
        this.videoElement.addEventListener('error', (e) => {
            console.warn('Avatar animation failed to load:', e);
            this.showFallbackAvatar();
        });
        
        // Handle video transitions
        this.videoElement.addEventListener('loadstart', () => {
            this.transitionInProgress = true;
        });
        
        this.videoElement.addEventListener('canplay', () => {
            this.transitionInProgress = false;
        });
        
        // Set up smooth transition styles
        this.videoElement.style.transition = `opacity ${this.transitionDuration}ms ease-in-out`;
        this.statusElement.style.transition = `opacity ${this.transitionDuration}ms ease-in-out`;
    }
    
    /**
     * Set avatar state and update animations with smooth transitions
     */
    async setState(newState) {
        if (this.currentState === newState) {
            return; // No change needed
        }
        
        const validStates = ['IDLE', 'LISTENING', 'SPEAKING', 'THINKING'];
        if (!validStates.includes(newState)) {
            console.warn(`Invalid avatar state: ${newState}`);
            return;
        }
        
        // Clear any existing timeout for the current state
        this.clearStateTimeout();
        
        const previousState = this.currentState;
        this.currentState = newState;
        
        // Perform smooth transition
        await this.performSmoothTransition(newState);
        
        // Set timeout for the new state if applicable
        this.setStateTimeout(newState);
        
        console.log(`Avatar state changed: ${previousState} → ${newState}`);
        
        // Notify listeners if callback is set
        this.onStateChange?.(newState, previousState);
    }
    
    /**
     * Perform smooth transition between states
     */
    async performSmoothTransition(newState) {
        // Fade out current state
        this.videoElement.style.opacity = '0.3';
        this.statusElement.style.opacity = '0.3';
        
        // Wait for fade out
        await this.delay(this.transitionDuration / 2);
        
        // Update video source and status
        const animationSrc = this.animations[newState];
        if (this.videoElement.src !== animationSrc) {
            this.videoElement.src = animationSrc;
        }
        
        this.statusElement.textContent = this.statusMessages[newState];
        
        // Update visual feedback classes
        this.updateVisualFeedback(newState);
        
        // Wait for video to be ready
        await this.waitForVideoReady();
        
        // Fade in new state
        this.videoElement.style.opacity = '1';
        this.statusElement.style.opacity = '1';
    }
    
    /**
     * Wait for video to be ready for playback
     */
    async waitForVideoReady() {
        return new Promise((resolve) => {
            if (this.videoElement.readyState >= 2) {
                resolve();
            } else {
                const onCanPlay = () => {
                    this.videoElement.removeEventListener('canplay', onCanPlay);
                    resolve();
                };
                this.videoElement.addEventListener('canplay', onCanPlay);
                
                // Timeout after 2 seconds to prevent hanging
                setTimeout(resolve, 2000);
            }
        });
    }
    
    /**
     * Set timeout for current state
     */
    setStateTimeout(state) {
        const timeoutDuration = this.stateTimeouts[state];
        if (timeoutDuration) {
            this.currentTimeout = setTimeout(() => {
                console.log(`State timeout reached for ${state}, returning to IDLE`);
                this.setState('IDLE');
                this.onStateTimeout?.(state);
            }, timeoutDuration);
        }
    }
    
    /**
     * Clear current state timeout
     */
    clearStateTimeout() {
        if (this.currentTimeout) {
            clearTimeout(this.currentTimeout);
            this.currentTimeout = null;
        }
    }
    
    /**
     * Utility function for delays
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Update visual feedback based on state
     */
    updateVisualFeedback(state) {
        // Remove all state classes
        this.videoElement.classList.remove('listening', 'speaking', 'thinking');
        
        // Add current state class
        switch (state) {
            case 'LISTENING':
                this.videoElement.classList.add('listening');
                break;
            case 'SPEAKING':
                this.videoElement.classList.add('speaking');
                break;
            case 'THINKING':
                this.videoElement.classList.add('thinking');
                break;
        }
    }
    
    /**
     * Show fallback avatar when video fails to load
     */
    showFallbackAvatar() {
        // Create a simple CSS-based avatar as fallback
        const fallbackDiv = document.createElement('div');
        fallbackDiv.className = 'fallback-avatar';
        fallbackDiv.innerHTML = '🤖';
        fallbackDiv.style.cssText = `
            width: 200px;
            height: 200px;
            border-radius: 50%;
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 80px;
            border: 4px solid #74b9ff;
            box-shadow: 0 4px 16px rgba(116, 185, 255, 0.3);
        `;
        
        // Replace video with fallback
        this.videoElement.style.display = 'none';
        this.videoElement.parentNode.insertBefore(fallbackDiv, this.videoElement);
        
        console.log('Using fallback avatar due to video loading issues');
    }
    
    /**
     * Get current avatar state
     */
    getCurrentState() {
        return this.currentState;
    }
    
    /**
     * Check if avatar is currently transitioning
     */
    isTransitioning() {
        return this.transitionInProgress;
    }
    
    /**
     * Force return to idle state (useful for error recovery)
     */
    forceIdle() {
        this.clearStateTimeout();
        this.setState('IDLE');
    }
    
    /**
     * Cleanup method for proper disposal
     */
    destroy() {
        this.clearStateTimeout();
        this.videoElement.removeEventListener('error', this.handleVideoError);
        this.videoElement.removeEventListener('loadstart', this.handleLoadStart);
        this.videoElement.removeEventListener('canplay', this.handleCanPlay);
    }
    
    // Event callbacks (to be set by consumers)
    onStateChange = null;
    onStateTimeout = null;
}