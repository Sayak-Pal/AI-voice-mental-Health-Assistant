"""
Conversation flow management for mental health screening.
Handles conversation state transitions and integrates with Gemini API.
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging
from datetime import datetime

from gemini_client import GeminiClient, ConversationContext
from session_manager import SessionManager, SessionData, ConversationPhase, ScreeningTool
from safety_monitor import SafetyMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationFlowManager:
    """
    Manages conversation flow and state transitions for mental health screening.
    Integrates Gemini API responses with session management and safety monitoring.
    """
    
    def __init__(self, session_manager: SessionManager, safety_monitor: SafetyMonitor):
        """Initialize conversation flow manager."""
        self.session_manager = session_manager
        self.safety_monitor = safety_monitor
        self.gemini_client = GeminiClient()
        
        # Screening tool question definitions
        self.screening_questions = self._initialize_screening_questions()
        
        logger.info("Conversation flow manager initialized")
    
    def _initialize_screening_questions(self) -> Dict[ScreeningTool, List[Dict]]:
        """Initialize screening questionnaire definitions."""
        return {
            ScreeningTool.PHQ9: [
                {"id": "phq9_1", "text": "Little interest or pleasure in doing things"},
                {"id": "phq9_2", "text": "Feeling down, depressed, or hopeless"},
                {"id": "phq9_3", "text": "Trouble falling or staying asleep, or sleeping too much"},
                {"id": "phq9_4", "text": "Feeling tired or having little energy"},
                {"id": "phq9_5", "text": "Poor appetite or overeating"},
                {"id": "phq9_6", "text": "Feeling bad about yourself — or that you are a failure or have let yourself or your family down"},
                {"id": "phq9_7", "text": "Trouble concentrating on things, such as reading the newspaper or watching television"},
                {"id": "phq9_8", "text": "Moving or speaking so slowly that other people could have noticed. Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual"},
                {"id": "phq9_9", "text": "Thoughts that you would be better off dead, or of hurting yourself"}
            ],
            ScreeningTool.GAD7: [
                {"id": "gad7_1", "text": "Feeling nervous, anxious, or on edge"},
                {"id": "gad7_2", "text": "Not being able to stop or control worrying"},
                {"id": "gad7_3", "text": "Worrying too much about different things"},
                {"id": "gad7_4", "text": "Trouble relaxing"},
                {"id": "gad7_5", "text": "Being so restless that it is hard to sit still"},
                {"id": "gad7_6", "text": "Becoming easily annoyed or irritable"},
                {"id": "gad7_7", "text": "Feeling afraid, as if something awful might happen"}
            ],
            ScreeningTool.GHQ12: [
                {"id": "ghq12_1", "text": "Been able to concentrate on whatever you're doing"},
                {"id": "ghq12_2", "text": "Lost much sleep over worry"},
                {"id": "ghq12_3", "text": "Felt that you are playing a useful part in things"},
                {"id": "ghq12_4", "text": "Felt capable of making decisions about things"},
                {"id": "ghq12_5", "text": "Felt constantly under strain"},
                {"id": "ghq12_6", "text": "Felt you couldn't overcome your difficulties"},
                {"id": "ghq12_7", "text": "Been able to enjoy your normal day-to-day activities"},
                {"id": "ghq12_8", "text": "Been able to face up to your problems"},
                {"id": "ghq12_9", "text": "Been feeling unhappy and depressed"},
                {"id": "ghq12_10", "text": "Been losing confidence in yourself"},
                {"id": "ghq12_11", "text": "Been thinking of yourself as a worthless person"},
                {"id": "ghq12_12", "text": "Been feeling reasonably happy, all things considered"}
            ]
        }
    
    def process_user_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process user message and generate appropriate AI response based on conversation state.
        
        Args:
            session_id: Session identifier
            user_message: User's input message
            
        Returns:
            Dictionary containing AI response and updated session state
        """
        try:
            # Get session data
            session = self.session_manager.get_session(session_id)
            if not session:
                return {
                    "error": "Session not found or expired",
                    "ai_response": None,
                    "current_phase": None,
                    "crisis_detected": False
                }
            
            # Check for crisis indicators first
            crisis_response = self.safety_monitor.check_for_crisis(user_message)
            if crisis_response.should_override:
                # Handle crisis situation
                return self._handle_crisis_response(session_id, user_message, crisis_response)
            
            # Process based on current conversation phase
            current_phase = session.current_phase
            
            if current_phase == ConversationPhase.GREETING:
                return self._handle_greeting_phase(session_id, user_message, session)
            elif current_phase == ConversationPhase.TRIAGE:
                return self._handle_triage_phase(session_id, user_message, session)
            elif current_phase == ConversationPhase.SCREENING:
                return self._handle_screening_phase(session_id, user_message, session)
            elif current_phase == ConversationPhase.RESULTS:
                return self._handle_results_phase(session_id, user_message, session)
            else:
                return self._handle_unknown_phase(session_id, user_message, session)
                
        except Exception as e:
            logger.error(f"Error processing user message: {str(e)}")
            return {
                "error": f"Failed to process message: {str(e)}",
                "ai_response": "I'm sorry, I encountered an error. Let's try again.",
                "current_phase": session.current_phase.value if session else None,
                "crisis_detected": False
            }
    
    def _handle_greeting_phase(self, session_id: str, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Handle greeting phase - collect name and move to background check."""
        try:
            # Check if this is the initial greeting or user providing their name
            if not session.user_name and user_message.strip():
                # Extract name from user message (simple approach)
                potential_name = user_message.strip().split()[0] if user_message.strip() else "there"
                
                # Update session with user name
                self.session_manager.update_session(session_id, user_name=potential_name)
                
                # Generate response asking about past diagnoses
                ai_response = self.gemini_client.generate_response(
                    user_message,
                    ConversationContext.BACKGROUND_CHECK,
                    {"user_name": potential_name}
                )
                
                # Move to triage phase (skipping detailed background for now)
                self.session_manager.update_session(session_id, current_phase=ConversationPhase.TRIAGE.value)
                
                # Add to conversation history
                self.session_manager.add_conversation(session_id, user_message, ai_response, ConversationPhase.TRIAGE.value)
                
                return {
                    "ai_response": ai_response,
                    "current_phase": ConversationPhase.TRIAGE.value,
                    "crisis_detected": False,
                    "next_action": "triage_question"
                }
            else:
                # Initial greeting
                ai_response = self.gemini_client.generate_response(
                    user_message,
                    ConversationContext.GREETING
                )
                
                # Add to conversation history
                self.session_manager.add_conversation(session_id, user_message, ai_response, ConversationPhase.GREETING.value)
                
                return {
                    "ai_response": ai_response,
                    "current_phase": ConversationPhase.GREETING.value,
                    "crisis_detected": False,
                    "next_action": "collect_name"
                }
                
        except Exception as e:
            logger.error(f"Error in greeting phase: {str(e)}")
            return self._get_error_response(session, str(e))
    
    def _handle_triage_phase(self, session_id: str, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Handle triage phase - determine screening tool based on primary concern."""
        try:
            # Analyze user response to determine screening tool
            screening_tool = self._determine_screening_tool(user_message)
            
            # Update session with selected tool and move to screening phase
            self.session_manager.update_session(
                session_id, 
                selected_tool=screening_tool.value,
                current_phase=ConversationPhase.SCREENING.value
            )
            
            # Generate first screening question
            first_question = self.screening_questions[screening_tool][0]
            
            # Get appropriate conversation context
            if screening_tool == ScreeningTool.PHQ9:
                context = ConversationContext.PHQ9_SCREENING
            elif screening_tool == ScreeningTool.GAD7:
                context = ConversationContext.GAD7_SCREENING
            else:
                context = ConversationContext.GHQ12_SCREENING
            
            ai_response = self.gemini_client.generate_response(
                first_question["text"],
                context,
                {"user_name": session.user_name, "question_number": 1}
            )
            
            # Add to conversation history
            self.session_manager.add_conversation(session_id, user_message, ai_response, ConversationPhase.SCREENING.value)
            
            return {
                "ai_response": ai_response,
                "current_phase": ConversationPhase.SCREENING.value,
                "crisis_detected": False,
                "selected_tool": screening_tool.value,
                "question_number": 1,
                "next_action": "screening_question"
            }
            
        except Exception as e:
            logger.error(f"Error in triage phase: {str(e)}")
            return self._get_error_response(session, str(e))
    
    def _handle_screening_phase(self, session_id: str, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Handle screening phase - process responses and ask next questions."""
        try:
            if not session.selected_tool:
                return self._get_error_response(session, "No screening tool selected")
            
            screening_tool = session.selected_tool
            questions = self.screening_questions[screening_tool]
            current_question_index = len(session.responses)
            
            if current_question_index >= len(questions):
                # All questions answered, move to results
                return self._transition_to_results(session_id, user_message, session)
            
            # Process current response
            current_question = questions[current_question_index - 1] if current_question_index > 0 else questions[0]
            
            if current_question_index > 0:
                # Map user response to score
                score, explanation = self.gemini_client.map_response_to_score(
                    user_message,
                    current_question["text"],
                    screening_tool
                )
                
                # Check for PHQ-9 Question 9 (suicidal ideation)
                if screening_tool == ScreeningTool.PHQ9 and current_question["id"] == "phq9_9" and score > 0:
                    # Trigger crisis response for positive PHQ-9 Q9
                    return self._handle_phq9_q9_crisis(session_id, user_message, session, score)
                
                # Add response to session
                self.session_manager.add_response(
                    session_id,
                    current_question["id"],
                    user_message,
                    score
                )
            
            # Check if there are more questions
            if current_question_index < len(questions):
                next_question = questions[current_question_index]
                
                # Get appropriate conversation context
                if screening_tool == ScreeningTool.PHQ9:
                    context = ConversationContext.PHQ9_SCREENING
                elif screening_tool == ScreeningTool.GAD7:
                    context = ConversationContext.GAD7_SCREENING
                else:
                    context = ConversationContext.GHQ12_SCREENING
                
                ai_response = self.gemini_client.generate_response(
                    next_question["text"],
                    context,
                    {
                        "user_name": session.user_name,
                        "question_number": current_question_index + 1
                    }
                )
                
                # Add to conversation history
                self.session_manager.add_conversation(session_id, user_message, ai_response, ConversationPhase.SCREENING.value)
                
                return {
                    "ai_response": ai_response,
                    "current_phase": ConversationPhase.SCREENING.value,
                    "crisis_detected": False,
                    "selected_tool": screening_tool.value,
                    "question_number": current_question_index + 1,
                    "next_action": "screening_question"
                }
            else:
                # All questions completed, transition to results
                return self._transition_to_results(session_id, user_message, session)
                
        except Exception as e:
            logger.error(f"Error in screening phase: {str(e)}")
            return self._get_error_response(session, str(e))
    
    def _handle_results_phase(self, session_id: str, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Handle results phase - provide screening results and recommendations."""
        try:
            # Calculate total score
            total_score = session.get_total_score()
            
            # Determine severity level
            severity_level = self._calculate_severity_level(session.selected_tool, total_score)
            
            # Generate results explanation
            ai_response = self.gemini_client.generate_response(
                f"Total score: {total_score}, Severity: {severity_level}",
                ConversationContext.RESULTS_EXPLANATION,
                {
                    "user_name": session.user_name,
                    "screening_tool": session.selected_tool.value,
                    "total_score": total_score,
                    "severity_level": severity_level
                }
            )
            
            # Mark session as completed
            self.session_manager.update_session(session_id, completed=True)
            
            # Add to conversation history
            self.session_manager.add_conversation(session_id, user_message, ai_response, ConversationPhase.RESULTS.value)
            
            return {
                "ai_response": ai_response,
                "current_phase": ConversationPhase.RESULTS.value,
                "crisis_detected": False,
                "total_score": total_score,
                "severity_level": severity_level,
                "screening_tool": session.selected_tool.value,
                "completed": True,
                "next_action": "screening_complete"
            }
            
        except Exception as e:
            logger.error(f"Error in results phase: {str(e)}")
            return self._get_error_response(session, str(e))
    
    def _handle_unknown_phase(self, session_id: str, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Handle unknown or invalid conversation phase."""
        logger.warning(f"Unknown conversation phase: {session.current_phase}")
        
        # Reset to greeting phase
        self.session_manager.update_session(session_id, current_phase=ConversationPhase.GREETING.value)
        
        ai_response = "I'm sorry, something went wrong. Let's start over. What would you like me to call you?"
        
        return {
            "ai_response": ai_response,
            "current_phase": ConversationPhase.GREETING.value,
            "crisis_detected": False,
            "next_action": "restart"
        }
    
    def _handle_crisis_response(self, session_id: str, user_message: str, crisis_response) -> Dict[str, Any]:
        """Handle crisis situation with immediate intervention."""
        try:
            # Update session with crisis detection
            self.session_manager.update_session(
                session_id,
                crisis_detected=True,
                current_phase=ConversationPhase.CRISIS_RESPONSE.value
            )
            
            # Generate crisis response message
            crisis_message = crisis_response.message or "I'm concerned about what you've shared. Please reach out for immediate support."
            
            # Add to conversation history
            self.session_manager.add_conversation(session_id, user_message, crisis_message, ConversationPhase.CRISIS_RESPONSE.value)
            
            return {
                "ai_response": crisis_message,
                "current_phase": ConversationPhase.CRISIS_RESPONSE.value,
                "crisis_detected": True,
                "crisis_level": crisis_response.level.value,
                "next_action": "crisis_intervention"
            }
            
        except Exception as e:
            logger.error(f"Error handling crisis response: {str(e)}")
            return {
                "ai_response": "I'm concerned about your safety. Please contact emergency services or a crisis helpline immediately.",
                "current_phase": ConversationPhase.CRISIS_RESPONSE.value,
                "crisis_detected": True,
                "error": str(e)
            }
    
    def _handle_phq9_q9_crisis(self, session_id: str, user_message: str, session: SessionData, score: int) -> Dict[str, Any]:
        """Handle PHQ-9 Question 9 positive response (suicidal ideation)."""
        try:
            # Update session with crisis detection
            self.session_manager.update_session(
                session_id,
                crisis_detected=True,
                current_phase=ConversationPhase.CRISIS_RESPONSE.value
            )
            
            # Add the response first
            self.session_manager.add_response(
                session_id,
                "phq9_9",
                user_message,
                score
            )
            
            crisis_message = ("I'm very concerned about what you've shared regarding thoughts of hurting yourself. "
                            "Your safety is the most important thing right now. Please reach out for immediate support. "
                            "If you're in the US, you can call 988 for the Suicide & Crisis Lifeline, "
                            "or contact emergency services at 911 if you're in immediate danger.")
            
            # Add to conversation history
            self.session_manager.add_conversation(session_id, user_message, crisis_message, ConversationPhase.CRISIS_RESPONSE.value)
            
            return {
                "ai_response": crisis_message,
                "current_phase": ConversationPhase.CRISIS_RESPONSE.value,
                "crisis_detected": True,
                "crisis_trigger": "PHQ9_Q9",
                "next_action": "crisis_intervention"
            }
            
        except Exception as e:
            logger.error(f"Error handling PHQ-9 Q9 crisis: {str(e)}")
            return {
                "ai_response": "I'm very concerned about your safety. Please contact emergency services immediately.",
                "current_phase": ConversationPhase.CRISIS_RESPONSE.value,
                "crisis_detected": True,
                "error": str(e)
            }
    
    def _determine_screening_tool(self, user_message: str) -> ScreeningTool:
        """Determine appropriate screening tool based on user's primary concern."""
        message_lower = user_message.lower()
        
        # Keywords for different screening tools
        depression_keywords = ['sad', 'depressed', 'depression', 'down', 'hopeless', 'empty', 'worthless']
        anxiety_keywords = ['anxious', 'anxiety', 'worried', 'worry', 'nervous', 'panic', 'fear']
        
        # Count keyword matches
        depression_score = sum(1 for keyword in depression_keywords if keyword in message_lower)
        anxiety_score = sum(1 for keyword in anxiety_keywords if keyword in message_lower)
        
        # Determine screening tool
        if depression_score > anxiety_score:
            return ScreeningTool.PHQ9
        elif anxiety_score > depression_score:
            return ScreeningTool.GAD7
        else:
            # Default to general mental health screening
            return ScreeningTool.GHQ12
    
    def _calculate_severity_level(self, screening_tool: ScreeningTool, total_score: int) -> str:
        """Calculate severity level based on screening tool and total score."""
        if screening_tool == ScreeningTool.PHQ9:
            if total_score <= 4:
                return "minimal"
            elif total_score <= 9:
                return "mild"
            elif total_score <= 14:
                return "moderate"
            elif total_score <= 19:
                return "moderately_severe"
            else:
                return "severe"
        elif screening_tool == ScreeningTool.GAD7:
            if total_score <= 4:
                return "minimal"
            elif total_score <= 9:
                return "mild"
            elif total_score <= 14:
                return "moderate"
            else:
                return "severe"
        else:  # GHQ12
            if total_score <= 11:
                return "minimal"
            elif total_score <= 15:
                return "mild"
            elif total_score <= 20:
                return "moderate"
            else:
                return "severe"
    
    def _transition_to_results(self, session_id: str, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Transition from screening to results phase."""
        try:
            # Process the final response if there is one
            if user_message.strip():
                questions = self.screening_questions[session.selected_tool]
                current_question_index = len(session.responses)
                
                if current_question_index < len(questions):
                    current_question = questions[current_question_index]
                    
                    # Map final response to score
                    score, explanation = self.gemini_client.map_response_to_score(
                        user_message,
                        current_question["text"],
                        session.selected_tool
                    )
                    
                    # Add final response to session
                    self.session_manager.add_response(
                        session_id,
                        current_question["id"],
                        user_message,
                        score
                    )
            
            # Update session phase to results
            self.session_manager.update_session(session_id, current_phase=ConversationPhase.RESULTS.value)
            
            # Calculate results
            total_score = session.get_total_score()
            severity_level = self._calculate_severity_level(session.selected_tool, total_score)
            
            # Generate results explanation
            ai_response = self.gemini_client.generate_response(
                f"Screening completed. Total score: {total_score}, Severity: {severity_level}",
                ConversationContext.RESULTS_EXPLANATION,
                {
                    "user_name": session.user_name,
                    "screening_tool": session.selected_tool.value,
                    "total_score": total_score,
                    "severity_level": severity_level
                }
            )
            
            # Mark session as completed
            self.session_manager.update_session(session_id, completed=True)
            
            # Add to conversation history
            self.session_manager.add_conversation(session_id, user_message, ai_response, ConversationPhase.RESULTS.value)
            
            return {
                "ai_response": ai_response,
                "current_phase": ConversationPhase.RESULTS.value,
                "crisis_detected": False,
                "total_score": total_score,
                "severity_level": severity_level,
                "screening_tool": session.selected_tool.value,
                "completed": True,
                "next_action": "screening_complete"
            }
            
        except Exception as e:
            logger.error(f"Error transitioning to results: {str(e)}")
            return self._get_error_response(session, str(e))
    
    def _get_error_response(self, session: SessionData, error_message: str) -> Dict[str, Any]:
        """Generate error response."""
        return {
            "error": error_message,
            "ai_response": "I'm sorry, I encountered an error. Let's try again or start over.",
            "current_phase": session.current_phase.value if session else None,
            "crisis_detected": False
        }
    
    def get_conversation_history(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get conversation history for a session."""
        session = self.session_manager.get_session(session_id)
        if session:
            return session.conversation_history
        return None
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of session progress and state."""
        session = self.session_manager.get_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "user_name": session.user_name,
            "current_phase": session.current_phase.value,
            "selected_tool": session.selected_tool.value if session.selected_tool else None,
            "questions_answered": len(session.responses),
            "total_score": session.get_total_score(),
            "crisis_detected": session.crisis_detected,
            "completed": session.completed,
            "start_time": session.start_time.isoformat(),
            "last_activity": session.last_activity.isoformat()
        }