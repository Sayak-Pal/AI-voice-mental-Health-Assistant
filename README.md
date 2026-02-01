# Voice-Based AI Mental Health Screening Assistant

A web application that provides accessible mental health screening through conversational AI, featuring voice interaction with an animated avatar and standardized screening questionnaires (PHQ-9, GAD-7, GHQ-12).

## Features

- **Voice Interaction**: Web Speech API integration for natural conversation
- **Visual Feedback**: Animated avatar with state-based animations
- **Safety First**: Real-time crisis detection and emergency resource display
- **Standardized Screening**: PHQ-9, GAD-7, and GHQ-12 questionnaires
- **Privacy Focused**: Session-only data storage, no persistent logging
- **Browser Compatible**: Graceful fallbacks for unsupported features

## Project Structure

```
├── backend/                 # Python FastAPI backend
│   ├── app.py              # Main FastAPI application
│   ├── config.py           # Configuration management
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variables template
├── frontend/               # Frontend web application
│   ├── index.html          # Main HTML structure
│   ├── styles.css          # CSS styling
│   ├── js/                 # JavaScript modules
│   │   ├── app.js          # Main application controller
│   │   ├── voice-engine.js # Web Speech API integration
│   │   ├── avatar.js       # Avatar component
│   │   ├── safety-monitor.js # Crisis detection
│   │   └── state-machine.js # State management
│   └── assets/             # Static assets
│       └── animations/     # Avatar animation videos
└── README.md               # This file
```

## Setup Instructions

### Backend Setup

1. **Create Python Virtual Environment**
   ```bash
   cd backend
   python -m venv venv
   
   # Windows
   venv\\Scripts\\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration:
   # - Add your Gemini API key
   # - Configure crisis helpline numbers for your region
   # - Adjust other settings as needed
   ```

4. **Run Backend Server**
   ```bash
   python app.py
   ```
   Server will start at `http://localhost:8000`

### Frontend Setup

1. **Serve Frontend Files**
   The frontend is a static web application. You can serve it using:
   
   **Option 1: Python HTTP Server**
   ```bash
   cd frontend
   python -m http.server 3000
   ```
   
   **Option 2: Node.js HTTP Server**
   ```bash
   cd frontend
   npx http-server -p 3000
   ```
   
   **Option 3: Any web server of your choice**

2. **Access Application**
   Open `http://localhost:3000` in your web browser

### Avatar Animations (Optional)

To enable avatar animations, add video files to `frontend/assets/animations/`:
- `idle.mp4` - Default idle animation
- `listening.mp4` - Animation when listening to user
- `speaking.mp4` - Animation when system is speaking
- `thinking.mp4` - Animation when processing user input

If animation files are not available, the system will use a CSS-based fallback avatar.

## Environment Configuration

### Required Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key for conversational AI
- `CRISIS_HELPLINE_US`: Crisis helpline number (default: 988)
- `EMERGENCY_SERVICES`: Emergency services number (default: 911)

### Optional Environment Variables

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Enable debug mode (default: True)
- `SESSION_TIMEOUT_MINUTES`: Session timeout (default: 30)
- `ENABLE_CRISIS_DETECTION`: Enable crisis detection (default: True)
- `CRISIS_TRIGGER_WORDS`: Comma-separated crisis trigger words

## Browser Compatibility

### Supported Features
- **Chrome/Edge**: Full voice and synthesis support
- **Firefox**: Full voice and synthesis support
- **Safari**: Limited voice support, full synthesis
- **Mobile browsers**: Varies by platform

### Fallback Options
- Text input when voice recognition fails
- CSS-based avatar when video animations unavailable
- Graceful degradation for unsupported browsers

## Safety and Ethics

### Crisis Detection
- Real-time monitoring for suicide/self-harm indicators
- Immediate intervention with emergency resources
- PHQ-9 Question 9 special handling for suicidal ideation

### Privacy Protection
- No persistent data storage
- Session-only conversation memory
- No third-party tracking by default
- Automatic data cleanup on session end

### Non-Diagnostic Nature
- Clear disclaimers throughout interface
- No medical diagnoses provided
- Professional referral recommendations
- Emphasis on screening vs. diagnosis

## Development Notes

This is the initial project structure setup. The system includes:

✅ **Completed:**
- Project directory structure
- Basic HTML interface with Web Speech API detection
- Python FastAPI backend foundation
- Environment configuration system
- JavaScript component architecture
- CSS styling with calming design
- Browser compatibility detection
- Crisis detection framework

🚧 **Next Steps:**
- Implement crisis detection and safety layer
- Build voice engine and Web Speech API integration
- Create avatar component and state management
- Develop backend API endpoints
- Integrate Gemini API for conversational intelligence

## License

This project is designed for educational and research purposes in mental health technology. Please ensure compliance with healthcare regulations and ethical guidelines in your jurisdiction before deployment.

## Support

For technical issues or questions about the mental health screening assistant, please refer to the project documentation or contact the development team.

**Important:** This is not a diagnostic tool. For professional mental health support, please consult a qualified healthcare provider.