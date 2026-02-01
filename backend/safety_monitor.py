"""
Crisis Detection and Safety Layer - Backend Module
Real-time monitoring for crisis indicators and emergency response
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class CrisisLevel(Enum):
    """Crisis severity levels"""
    NONE = "NONE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class CrisisResponse:
    """Crisis detection response data"""
    level: CrisisLevel
    triggered_words: List[str]
    message: str
    timestamp: datetime
    requires_override: bool


class SafetyMonitor:
    """Backend crisis detection and safety monitoring system"""
    
    def __init__(self, config_trigger_words: Optional[List[str]] = None):
        """
        Initialize safety monitor with configurable trigger words
        
        Args:
            config_trigger_words: Optional list of custom trigger words
        """
        # Default critical trigger words
        self.critical_triggers = [
            'suicide', 'suicidal', 'kill myself', 'end my life',
            'self-harm', 'hurt myself', 'cut myself', 'harm myself',
            'want to die', 'better off dead', 'no point living',
            'hurt others', 'kill someone', 'harm others', 'end it all',
            'take my own life', 'not worth living', 'kill them'
        ]
        
        # Warning indicators (concerning but not immediately critical)
        self.warning_indicators = [
            'hopeless', 'worthless', 'trapped', 'burden',
            'desperate', 'overwhelmed', 'can\'t cope', 'give up',
            'no way out', 'pointless', 'useless', 'hate myself'
        ]
        
        # Add custom trigger words if provided
        if config_trigger_words:
            self.critical_triggers.extend(config_trigger_words)
        
        # PHQ-9 Question 9 specific patterns
        self.phq9_q9_positive_patterns = [
            r'\b(yes|sometimes|often|nearly every day|several days)\b',
            r'\b(more than half|have thought|been thinking)\b',
            r'\b(crossed my mind|considered|considering|thinking about)\b',
            r'\b(thoughts? of|idea of|wanting to)\b.*\b(die|death|harm)\b'
        ]
        
        self.phq9_q9_negative_patterns = [
            r'\b(no|never|not at all|haven\'t|don\'t)\b',
            r'\b(absolutely not|definitely not|of course not)\b'
        ]
    
    def check_for_crisis(self, text: str) -> CrisisResponse:
        """
        Analyze text for crisis indicators
        
        Args:
            text: User input text to analyze
            
        Returns:
            CrisisResponse with detection results
        """
        if not text or not isinstance(text, str):
            return CrisisResponse(
                level=CrisisLevel.NONE,
                triggered_words=[],
                message="",
                timestamp=datetime.now(),
                requires_override=False
            )
        
        normalized_text = text.lower().strip()
        triggered_words = []
        
        # Check for critical triggers
        for trigger in self.critical_triggers:
            if trigger.lower() in normalized_text:
                triggered_words.append(trigger)
        
        if triggered_words:
            return CrisisResponse(
                level=CrisisLevel.CRITICAL,
                triggered_words=triggered_words,
                message=self._get_crisis_message(),
                timestamp=datetime.now(),
                requires_override=True
            )
        
        # Check for warning indicators
        warning_words = []
        for warning in self.warning_indicators:
            if warning.lower() in normalized_text:
                warning_words.append(warning)
        
        if warning_words:
            return CrisisResponse(
                level=CrisisLevel.WARNING,
                triggered_words=warning_words,
                message=self._get_warning_message(),
                timestamp=datetime.now(),
                requires_override=False
            )
        
        return CrisisResponse(
            level=CrisisLevel.NONE,
            triggered_words=[],
            message="",
            timestamp=datetime.now(),
            requires_override=False
        )
    
    def check_phq9_question9(self, response: str) -> bool:
        """
        Check PHQ-9 Question 9 (suicidal ideation) for positive response
        
        Args:
            response: User response to PHQ-9 Question 9
            
        Returns:
            True if positive response detected, False otherwise
        """
        if not response or not isinstance(response, str):
            return False
        
        normalized_response = response.lower().strip()
        
        # Check for clear negative responses first
        for pattern in self.phq9_q9_negative_patterns:
            if re.search(pattern, normalized_response, re.IGNORECASE):
                # If response is short and clearly negative, return False
                if len(normalized_response) < 20:
                    return False
        
        # Check for positive indicators
        for pattern in self.phq9_q9_positive_patterns:
            if re.search(pattern, normalized_response, re.IGNORECASE):
                return True
        
        return False
    
    def add_trigger_words(self, words: List[str]) -> None:
        """
        Add custom trigger words to the critical triggers list
        
        Args:
            words: List of trigger words to add
        """
        if isinstance(words, list):
            self.critical_triggers.extend(words)
    
    def add_warning_words(self, words: List[str]) -> None:
        """
        Add custom warning words to the warning indicators list
        
        Args:
            words: List of warning words to add
        """
        if isinstance(words, list):
            self.warning_indicators.extend(words)
    
    def _get_crisis_message(self) -> str:
        """Get the crisis response message"""
        # This will be overridden by emergency resource manager
        return """I'm very concerned about what you've shared with me. Your safety is the most important thing right now.

Please reach out for immediate support:
• Crisis Helpline: 988 (available 24/7)
• Emergency Services: 911
• Crisis Text Line: Text HOME to 741741

You don't have to go through this alone. There are people who want to help you, and things can get better. Please reach out to one of these resources right away."""
    
    def _get_warning_message(self) -> str:
        """Get the warning response message"""
        return """I hear that you're going through a difficult time. While I can help with this screening, please remember that professional support is available if you need someone to talk to.

If you're feeling overwhelmed, consider reaching out to:
• Crisis Helpline: 988
• Your healthcare provider
• A trusted friend or family member

Would you like to continue with the screening, or would you prefer information about mental health resources?"""


class CrisisOverrideHandler:
    """Handles crisis response overrides and emergency protocols"""
    
    def __init__(self, safety_monitor: SafetyMonitor):
        self.safety_monitor = safety_monitor
        self.crisis_detected = False
        self.crisis_timestamp = None
    
    def process_user_input(self, text: str, is_phq9_q9: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Process user input and determine if crisis override is needed
        
        Args:
            text: User input text
            is_phq9_q9: Whether this is PHQ-9 Question 9
            
        Returns:
            Tuple of (should_override, override_message)
        """
        # Check for general crisis indicators
        crisis_response = self.safety_monitor.check_for_crisis(text)
        
        # Check PHQ-9 Question 9 specifically
        if is_phq9_q9 and self.safety_monitor.check_phq9_question9(text):
            self.crisis_detected = True
            self.crisis_timestamp = datetime.now()
            return True, self.safety_monitor._get_crisis_message()
        
        # Handle critical crisis detection
        if crisis_response.level == CrisisLevel.CRITICAL:
            self.crisis_detected = True
            self.crisis_timestamp = datetime.now()
            return True, crisis_response.message
        
        # Handle warning level (no override, but log)
        if crisis_response.level == CrisisLevel.WARNING:
            return False, crisis_response.message
        
        return False, None
    
    def is_crisis_active(self) -> bool:
        """Check if crisis state is currently active"""
        return self.crisis_detected
    
    def reset_crisis_state(self) -> None:
        """Reset crisis detection state"""
        self.crisis_detected = False
        self.crisis_timestamp = None