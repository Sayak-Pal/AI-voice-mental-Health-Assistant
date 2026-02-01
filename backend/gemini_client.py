"""
Gemini API client for conversational intelligence in mental health screening.
Provides safe, ethical AI responses for mental health screening conversations.
"""

import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import logging
from enum import Enum

from config import config
from session_manager import ConversationPhase, ScreeningTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationContext(Enum):
    """Context types for conversation management."""
    GREETING = "greeting"
    BACKGROUND_CHECK = "background_check"
    TRIAGE = "triage"
    PHQ9_SCREENING = "phq9_screening"
    GAD7_SCREENING = "gad7_screening"
    GHQ12_SCREENING = "ghq12_screening"
    RESULTS_EXPLANATION = "results_explanation"
    CRISIS_RESPONSE = "crisis_response"

class GeminiClient:
    """
    Gemini API client for mental health screening conversations.
    Handles all AI interactions with strict safety and ethical guidelines.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize Gemini client with API key and safety settings."""
        self.api_key = api_key or config.GEMINI_API_KEY
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError("Valid Gemini API key is required")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        
        # Initialize model with safety settings
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=self._get_generation_config(),
            safety_settings=self._get_safety_settings()
        )
        
        # System instructions for different conversation contexts
        self.system_instructions = self._build_system_instructions()
        
        logger.info("Gemini client initialized successfully")
    
    def _get_generation_config(self) -> genai.GenerationConfig:
        """Configure generation parameters for consistent, safe responses."""
        return genai.GenerationConfig(
            temperature=0.3,  # Lower temperature for more consistent responses
            top_p=0.8,
            top_k=40,
            max_output_tokens=500,  # Limit response length
            stop_sequences=["DIAGNOSIS:", "PRESCRIBE:", "MEDICAL_ADVICE:"]
        )
    
    def _get_safety_settings(self) -> List[Dict]:
        """Configure safety filters for mental health content."""
        return [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    
    def _build_system_instructions(self) -> Dict[ConversationContext, str]:
        """Build comprehensive system instructions for each conversation context."""
        
        base_instructions = """
        You are a compassionate AI assistant helping with mental health screening. You are NOT a therapist, doctor, or mental health professional.
        
        CRITICAL SAFETY RULES - NEVER VIOLATE THESE:
        1. NEVER provide medical diagnoses or diagnostic labels
        2. NEVER prescribe medications or specific treatments  
        3. NEVER claim to replace professional mental healthcare
        4. NEVER encourage dependency on this screening tool
        5. NEVER give medical advice or therapeutic interventions
        6. ALWAYS maintain that this is a screening tool, not diagnostic
        7. ALWAYS encourage professional help when appropriate
        8. NEVER analyze or interpret psychological patterns beyond basic screening
        
        COMMUNICATION STYLE:
        - Warm, empathetic, and non-judgmental
        - Use simple, clear language
        - Keep responses concise (under 100 words typically)
        - Validate user feelings without diagnosing
        - Maintain professional boundaries
        
        ETHICAL GUIDELINES:
        - Respect user autonomy and dignity
        - Maintain confidentiality within session
        - Avoid stigmatizing language
        - Promote hope and recovery orientation
        - Acknowledge limitations of screening tools
        """
        
        return {
            ConversationContext.GREETING: base_instructions + """
            CONTEXT: Initial greeting and name collection
            
            TASKS:
            1. Warmly welcome the user to the mental health screening
            2. Ask for their preferred name in a friendly way
            3. Explain this is a brief screening tool, not a diagnosis
            4. Set expectations about the conversation flow
            5. Ensure they understand this is confidential and non-judgmental
            
            EXAMPLE RESPONSE STYLE:
            "Hello! Welcome to our mental health screening assistant. I'm here to help you through a brief screening that might give you some insights into how you're feeling. This isn't a diagnosis - just a way to understand your current mental health better. What would you like me to call you?"
            """,
            
            ConversationContext.BACKGROUND_CHECK: base_instructions + """
            CONTEXT: Asking about past mental health diagnoses
            
            TASKS:
            1. Gently ask about any past mental health diagnoses
            2. Normalize having or not having past diagnoses
            3. Explain why this information helps with screening selection
            4. Reassure about confidentiality
            5. Prepare to move to triage questions
            
            EXAMPLE RESPONSE STYLE:
            "Thanks, [Name]. Before we begin, I'd like to ask - have you ever been diagnosed with a mental health condition by a healthcare professional? This helps me understand your background, but there's no right or wrong answer. Everything we discuss stays private."
            """,
            
            ConversationContext.TRIAGE: base_instructions + """
            CONTEXT: Determining primary concern for screening tool selection
            
            TASKS:
            1. Ask about their main concern: sadness/depression, anxiety, or general stress
            2. Explain that this helps select the most relevant screening questions
            3. Validate their concern without minimizing it
            4. Prepare them for the screening questions ahead
            5. Maintain that all concerns are valid and worth exploring
            
            EXAMPLE RESPONSE STYLE:
            "I understand. Now, thinking about what's been bothering you lately, would you say your main concern is more about feelings of sadness or depression, anxiety and worry, or general stress and life challenges? This helps me choose the most helpful screening questions for you."
            """,
            
            ConversationContext.PHQ9_SCREENING: base_instructions + """
            CONTEXT: Administering PHQ-9 depression screening questions
            
            TASKS:
            1. Present ONE question at a time in conversational format
            2. Use the exact PHQ-9 question content but make it conversational
            3. Explain the timeframe (past 2 weeks) clearly
            4. Accept natural language responses - DO NOT ask for numbers
            5. Validate their experience without interpreting symptoms
            6. For Question 9 (self-harm thoughts), be extra gentle and supportive
            
            PHQ-9 QUESTIONS (present conversationally):
            1. Little interest or pleasure in doing things
            2. Feeling down, depressed, or hopeless  
            3. Trouble falling/staying asleep or sleeping too much
            4. Feeling tired or having little energy
            5. Poor appetite or overeating
            6. Feeling bad about yourself, feeling like a failure, or letting others down
            7. Trouble concentrating on things like reading or watching TV
            8. Moving/speaking slowly or being fidgety/restless
            9. Thoughts of being better off dead or hurting yourself
            
            EXAMPLE RESPONSE STYLE:
            "Over the past two weeks, how often have you had little interest or pleasure in doing things you usually enjoy? You can describe it however feels natural to you."
            """,
            
            ConversationContext.GAD7_SCREENING: base_instructions + """
            CONTEXT: Administering GAD-7 anxiety screening questions
            
            TASKS:
            1. Present ONE question at a time in conversational format
            2. Use the exact GAD-7 question content but make it conversational
            3. Explain the timeframe (past 2 weeks) clearly
            4. Accept natural language responses - DO NOT ask for numbers
            5. Validate their anxiety experiences without pathologizing
            
            GAD-7 QUESTIONS (present conversationally):
            1. Feeling nervous, anxious, or on edge
            2. Not being able to stop or control worrying
            3. Worrying too much about different things
            4. Trouble relaxing
            5. Being so restless that it's hard to sit still
            6. Becoming easily annoyed or irritable
            7. Feeling afraid as if something awful might happen
            
            EXAMPLE RESPONSE STYLE:
            "In the past two weeks, how often have you been feeling nervous, anxious, or on edge? Just describe it in your own words."
            """,
            
            ConversationContext.GHQ12_SCREENING: base_instructions + """
            CONTEXT: Administering GHQ-12 general mental health screening questions
            
            TASKS:
            1. Present ONE question at a time in conversational format
            2. Use the exact GHQ-12 question content but make it conversational
            3. Explain the timeframe (past few weeks) clearly
            4. Accept natural language responses - DO NOT ask for numbers
            5. Validate their experiences with general mental health
            
            GHQ-12 QUESTIONS (present conversationally):
            1. Been able to concentrate on what you're doing
            2. Lost much sleep over worry
            3. Felt you were playing a useful part in things
            4. Felt capable of making decisions about things
            5. Felt constantly under strain
            6. Felt you couldn't overcome your difficulties
            7. Been able to enjoy your normal day-to-day activities
            8. Been able to face up to your problems
            9. Been feeling unhappy and depressed
            10. Been losing confidence in yourself
            11. Been thinking of yourself as a worthless person
            12. Been feeling reasonably happy, all things considered
            
            EXAMPLE RESPONSE STYLE:
            "Over the past few weeks, have you been able to concentrate on what you're doing? Tell me about your experience with focus and concentration lately."
            """,
            
            ConversationContext.RESULTS_EXPLANATION: base_instructions + """
            CONTEXT: Explaining screening results in non-diagnostic terms
            
            TASKS:
            1. Explain results in plain, non-diagnostic language
            2. Normalize their experience and validate their feelings
            3. Provide appropriate next steps based on severity
            4. Emphasize that screening is not diagnosis
            5. Encourage professional help when appropriate
            6. Offer hope and support resources
            
            SEVERITY LEVEL GUIDANCE:
            - Minimal: Validate experience, provide general wellness tips
            - Mild: Acknowledge concerns, suggest monitoring and self-care
            - Moderate: Recommend considering professional support
            - Severe: Strongly encourage professional help, provide resources
            
            EXAMPLE RESPONSE STYLE:
            "Based on your responses, it seems like you've been experiencing some challenges with [area]. This screening suggests [level] concerns. Remember, this isn't a diagnosis - it's just information to help you understand how you're feeling. I'd recommend [appropriate next steps]."
            """
        }
    
    def generate_response(
        self, 
        user_message: str, 
        context: ConversationContext,
        session_data: Optional[Dict] = None,
        question_number: Optional[int] = None
    ) -> str:
        """
        Generate AI response based on user message and conversation context.
        
        Args:
            user_message: User's input message
            context: Current conversation context
            session_data: Optional session information for personalization
            question_number: For screening contexts, which question number
            
        Returns:
            AI-generated response following safety guidelines
        """
        try:
            # Build context-specific prompt
            system_instruction = self.system_instructions.get(context, self.system_instructions[ConversationContext.GREETING])
            
            # Add session context if available
            context_info = ""
            if session_data:
                user_name = session_data.get('user_name', 'there')
                context_info = f"User's name: {user_name}\n"
                
                if session_data.get('has_past_diagnosis'):
                    context_info += "User has past mental health diagnosis\n"
                
                if question_number:
                    context_info += f"Current question number: {question_number}\n"
            
            # Build full prompt
            full_prompt = f"""
            {system_instruction}
            
            {context_info}
            
            User's message: "{user_message}"
            
            Respond according to the context guidelines above. Keep response under 100 words and maintain the warm, professional tone.
            """
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            if response.text:
                logger.info(f"Generated response for context: {context.value}")
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini API")
                return self._get_fallback_response(context)
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._get_fallback_response(context)
    
    def map_response_to_score(
        self, 
        user_response: str, 
        question_context: str,
        screening_tool: ScreeningTool
    ) -> Tuple[int, str]:
        """
        Map natural language response to numeric score for screening questions.
        
        Args:
            user_response: User's natural language response
            question_context: The screening question being answered
            screening_tool: Which screening tool is being used
            
        Returns:
            Tuple of (numeric_score, explanation)
        """
        try:
            # Build scoring prompt
            scoring_prompt = f"""
            You are helping map a user's natural language response to a standardized screening score.
            
            SCREENING TOOL: {screening_tool.value}
            QUESTION CONTEXT: {question_context}
            USER RESPONSE: "{user_response}"
            
            SCORING SCALE (0-3):
            0 = Not at all / Never
            1 = Several days / Sometimes  
            2 = More than half the days / Often
            3 = Nearly every day / Almost always
            
            INSTRUCTIONS:
            1. Analyze the user's response for frequency/intensity indicators
            2. Map to the 0-3 scale based on their description
            3. Provide a brief explanation of your scoring reasoning
            4. Be conservative - when in doubt, score lower
            5. Look for specific time/frequency words in their response
            
            Respond in this exact format:
            SCORE: [0-3]
            EXPLANATION: [Brief explanation of scoring reasoning]
            """
            
            response = self.model.generate_content(scoring_prompt)
            
            if response.text:
                # Parse response
                lines = response.text.strip().split('\n')
                score_line = next((line for line in lines if line.startswith('SCORE:')), None)
                explanation_line = next((line for line in lines if line.startswith('EXPLANATION:')), None)
                
                if score_line and explanation_line:
                    score = int(score_line.split(':')[1].strip())
                    explanation = explanation_line.split(':', 1)[1].strip()
                    
                    # Validate score range
                    if 0 <= score <= 3:
                        logger.info(f"Mapped response to score: {score}")
                        return score, explanation
            
            # Fallback scoring
            logger.warning("Could not parse AI scoring response, using fallback")
            return self._fallback_scoring(user_response)
            
        except Exception as e:
            logger.error(f"Error in response mapping: {str(e)}")
            return self._fallback_scoring(user_response)
    
    def _fallback_scoring(self, user_response: str) -> Tuple[int, str]:
        """Fallback scoring based on keyword analysis."""
        response_lower = user_response.lower()
        
        # High frequency indicators
        if any(word in response_lower for word in ['always', 'constantly', 'every day', 'all the time', 'never stops']):
            return 3, "Fallback scoring based on high frequency indicators"
        
        # Medium-high frequency indicators  
        elif any(word in response_lower for word in ['often', 'frequently', 'most days', 'usually']):
            return 2, "Fallback scoring based on medium-high frequency indicators"
        
        # Low frequency indicators
        elif any(word in response_lower for word in ['sometimes', 'occasionally', 'few times', 'now and then']):
            return 1, "Fallback scoring based on low frequency indicators"
        
        # Minimal/none indicators
        elif any(word in response_lower for word in ['never', 'not at all', 'rarely', 'hardly ever']):
            return 0, "Fallback scoring based on minimal frequency indicators"
        
        # Default to conservative scoring
        return 1, "Fallback scoring - conservative default"
    
    def _get_fallback_response(self, context: ConversationContext) -> str:
        """Provide fallback responses when AI generation fails."""
        fallback_responses = {
            ConversationContext.GREETING: "Hello! I'm here to help you with a mental health screening. This is a safe, confidential space. What would you like me to call you?",
            ConversationContext.BACKGROUND_CHECK: "Thank you for sharing. Have you ever been diagnosed with a mental health condition by a healthcare professional? This helps me provide the most relevant screening.",
            ConversationContext.TRIAGE: "I'd like to understand what's been concerning you most lately. Would you say it's more about feelings of sadness, anxiety, or general stress?",
            ConversationContext.PHQ9_SCREENING: "Thank you for sharing. Let me ask about the next area - how has this been affecting you over the past two weeks?",
            ConversationContext.GAD7_SCREENING: "I appreciate you being open with me. Let's continue with the next question about your recent experiences.",
            ConversationContext.GHQ12_SCREENING: "Thank you for your honesty. Let me ask about another aspect of how you've been feeling recently.",
            ConversationContext.RESULTS_EXPLANATION: "Based on your responses, this screening provides some insights into how you've been feeling. Remember, this isn't a diagnosis, but it can help guide next steps."
        }
        
        return fallback_responses.get(context, "I'm here to help you through this screening. Please let me know how you're feeling.")
    
    def validate_api_connection(self) -> bool:
        """Test API connection and return success status."""
        try:
            test_response = self.model.generate_content("Hello, this is a connection test.")
            return bool(test_response.text)
        except Exception as e:
            logger.error(f"API connection validation failed: {str(e)}")
            return False