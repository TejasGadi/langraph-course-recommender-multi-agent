"""Base agent class for the Course Recommendation System."""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from src.models.base_models import AgentResponse, ConversationContext
from src.config.config import OPENAI_API_KEY, LLM_MODEL, TEMPERATURE

class BaseAgent:
    """Base class for all agents in the system."""
    
    def __init__(self, name: str):
        """Initialize the base agent.
        
        Args:
            name (str): Name of the agent
        """
        self.name = name
        self.llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=LLM_MODEL,
            temperature=TEMPERATURE
        )
        
    def _create_prompt(self, template: str, input_variables: Dict[str, Any]) -> str:
        """Create a prompt from template and variables.
        
        Args:
            template (str): Prompt template
            input_variables (Dict[str, Any]): Variables for the template
            
        Returns:
            str: Formatted prompt
        """
        prompt = ChatPromptTemplate.from_template(template)
        return prompt.format_messages(**input_variables)
    
    def _format_response(self, 
                        success: bool, 
                        message: str, 
                        data: Optional[Dict] = None, 
                        next_action: Optional[str] = None) -> AgentResponse:
        """Format the agent's response.
        
        Args:
            success (bool): Whether the operation was successful
            message (str): Response message
            data (Optional[Dict]): Additional data
            next_action (Optional[str]): Next action to take
            
        Returns:
            AgentResponse: Formatted response
        """
        return AgentResponse(
            success=success,
            message=message,
            data=data,
            next_action=next_action
        )
    
    def update_context(self, context: ConversationContext, **updates) -> ConversationContext:
        """Update the conversation context.
        
        Args:
            context (ConversationContext): Current context
            **updates: Updates to apply
            
        Returns:
            ConversationContext: Updated context
        """
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
        context.last_agent = self.name
        return context
    
    async def process(self, context: ConversationContext) -> AgentResponse:
        """Process the current context and return a response.
        
        Args:
            context (ConversationContext): Current conversation context
            
        Returns:
            AgentResponse: Agent's response
        """
        raise NotImplementedError("Subclasses must implement process method") 