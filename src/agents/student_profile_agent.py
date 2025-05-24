"""Student Profile Agent for collecting and managing student information."""

from typing import Dict, List, Optional
from src.agents.base_agent import BaseAgent
from src.models.base_models import AgentResponse, ConversationContext, StudentProfile

class StudentProfileAgent(BaseAgent):
    """Agent responsible for collecting and managing student profiles."""
    
    def __init__(self):
        """Initialize the Student Profile Agent."""
        super().__init__("StudentProfileAgent")
        self.profile_collection_prompts = {
            "initial": """You are a friendly educational advisor. The student has just started the conversation. 
            Greet them warmly and ask about their current educational level and academic interests.
            Current conversation history: {chat_history}""",
            
            "interests": """Based on the student's educational level, ask about their specific subject interests 
            and what they hope to learn. Make sure to acknowledge their previous responses.
            Current conversation history: {chat_history}""",
            
            "preferences": """Now that we know their course preferences, ask about their preferred course format 
            (online/offline/hybrid) and time availability (e.g., evenings, weekends).
            Current conversation history: {chat_history}""",
            
            "career_goals": """Finally, ask about their career aspirations and what they hope to achieve 
            with these courses. Be encouraging and supportive.
            Current conversation history: {chat_history}"""
        }
    
    def _extract_profile_info(self, chat_history: List[Dict[str, str]]) -> Dict:
        """Extract profile information from chat history.
        
        Args:
            chat_history (List[Dict[str, str]]): Conversation history
            
        Returns:
            Dict: Extracted profile information
        """
        # Create a prompt for the LLM to extract information
        extraction_prompt = """Based on the following conversation, extract the student's profile information.
        Format the response as a JSON object with these fields:
        - education_level
        - academic_background
        - interests
        - preferred_mode
        - availability
        - career_goals
        
        Conversation:
        {chat_history}
        
        Only include information that was explicitly mentioned. If a field wasn't discussed, leave it as null.
        """
        
        messages = self._create_prompt(extraction_prompt, {"chat_history": str(chat_history)})
        response = self.llm.invoke(messages)
        
        try:
            # The response should be in JSON format
            profile_data = eval(response.content)
            return profile_data
        except:
            return {}
    
    def _determine_next_prompt(self, profile_data: Dict) -> Optional[str]:
        """Determine which prompt to use next based on missing information.
        
        Args:
            profile_data (Dict): Current profile information
            
        Returns:
            Optional[str]: Next prompt key or None if profile is complete
        """
        if not profile_data.get('education_level'):
            return "initial"
        elif not profile_data.get('interests'):
            return "interests"
        elif not profile_data.get('preferred_mode') or not profile_data.get('availability'):
            return "preferences"
        elif not profile_data.get('career_goals'):
            return "career_goals"
        return None
    
    async def process(self, context: ConversationContext) -> AgentResponse:
        """Process the current context and collect student profile information.
        
        Args:
            context (ConversationContext): Current conversation context
            
        Returns:
            AgentResponse: Agent's response with next steps
        """
        # Extract current profile information
        profile_data = self._extract_profile_info(context.chat_history)
        
        # Determine which information we still need
        next_prompt_key = self._determine_next_prompt(profile_data)
        
        if next_prompt_key is None:
            # Profile is complete, create StudentProfile object
            try:
                student_profile = StudentProfile(**profile_data)
                context = self.update_context(context, 
                                           student_profile=student_profile,
                                           current_phase="profile_complete")
                return self._format_response(
                    success=True,
                    message="Great! I have all the information I need. Let me start looking for courses that match your profile.",
                    data={"profile": profile_data},
                    next_action="find_courses"
                )
            except Exception as e:
                return self._format_response(
                    success=False,
                    message="I had trouble processing your information. Could you please clarify your responses?",
                    data={"error": str(e)},
                    next_action="retry_profile"
                )
        
        # Get the next prompt and generate response
        prompt = self.profile_collection_prompts[next_prompt_key]
        messages = self._create_prompt(prompt, {"chat_history": str(context.chat_history)})
        response = self.llm.invoke(messages)
        
        return self._format_response(
            success=True,
            message=response.content,
            data={"current_profile": profile_data},
            next_action="continue_profile"
        ) 