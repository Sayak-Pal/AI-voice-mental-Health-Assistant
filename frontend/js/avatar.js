/**
 * Avatar Component - Cartoon SVG Version
 * Handles Lip-Sync via CSS Class Toggling
 */

class AvatarComponent {
    constructor() {
        this.statusElement = document.getElementById('avatar-status');
        this.svgContainer = document.querySelector('.human-svg');
        this.currentState = 'IDLE';
        this.initialize();
    }
    
    initialize() {
        this.setState('IDLE');
    }

    setState(newState) {
        if (this.currentState === newState) return;
        this.currentState = newState;
        
        // 1. Update Status Text
        const statusMap = {
            'IDLE': 'Ready to listen',
            'LISTENING': 'Listening...',
            'THINKING': 'Thinking...',
            'SPEAKING': 'Speaking...'
        };
        
        if (this.statusElement) {
            this.statusElement.textContent = statusMap[newState] || 'Active';
            
            // Update dot color based on state
            const dot = document.querySelector('.status-dot');
            if(dot) dot.style.background = (newState === 'SPEAKING' || newState === 'LISTENING') 
                ? '#10B981' : '#cbd5e1'; 
        }

        // 2. Trigger Animations
        this.updateVisuals(newState);
    }

    updateVisuals(state) {
        if (!this.svgContainer) return;
        
        const stage = document.querySelector('.avatar-stage');

        // Reset all animation classes
        this.svgContainer.classList.remove('talking');
        if (stage) stage.classList.remove('speaking');

        // Apply new state
        switch (state) {
            case 'SPEAKING':
                // Adds CSS animation for mouth moving (lip-sync)
                this.svgContainer.classList.add('talking');
                // Adds CSS animation for rings rippling
                if (stage) stage.classList.add('speaking');
                break;
                
            case 'LISTENING':
                // Optional: You could add a 'leaning' class here if defined in CSS
                break;
        }
    }
}
