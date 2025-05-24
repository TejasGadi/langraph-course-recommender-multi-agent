"""Persistence utility for conversation context."""

import json
import os
from datetime import datetime
from typing import Optional
from src.models.base_models import ConversationContext, StudentProfile, CourseMetadata
from src.utils.logging_utils import agent_logger

class ContextPersistence:
    """Handles persistence of conversation context."""
    
    def __init__(self, storage_dir: str = "data/conversations"):
        """Initialize the persistence handler.
        
        Args:
            storage_dir (str): Directory for storing conversation data
        """
        self.storage_dir = storage_dir
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
    
    def _context_to_dict(self, context: ConversationContext) -> dict:
        """Convert context to a dictionary for storage.
        
        Args:
            context (ConversationContext): Context to convert
            
        Returns:
            dict: Dictionary representation of the context
        """
        return {
            "student_profile": context.student_profile.dict() if context.student_profile else None,
            "discovered_courses": [course.dict() for course in context.discovered_courses],
            "validated_courses": [course.dict() for course in context.validated_courses],
            "current_phase": context.current_phase,
            "chat_history": context.chat_history,
            "last_agent": context.last_agent
        }
    
    def _dict_to_context(self, data: dict) -> ConversationContext:
        """Convert dictionary to ConversationContext.
        
        Args:
            data (dict): Dictionary to convert
            
        Returns:
            ConversationContext: Reconstructed context
        """
        # Convert nested dictionaries back to objects
        if data.get("student_profile"):
            data["student_profile"] = StudentProfile(**data["student_profile"])
        
        data["discovered_courses"] = [CourseMetadata(**course) 
                                    for course in data.get("discovered_courses", [])]
        data["validated_courses"] = [CourseMetadata(**course) 
                                   for course in data.get("validated_courses", [])]
        
        return ConversationContext(**data)
    
    def save_context(self, context: ConversationContext, session_id: Optional[str] = None) -> str:
        """Save conversation context to file.
        
        Args:
            context (ConversationContext): Context to save
            session_id (Optional[str]): Session identifier
            
        Returns:
            str: Session ID used for storage
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Convert context to dictionary
        context_dict = self._context_to_dict(context)
        
        # Save to file
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        with open(file_path, 'w') as f:
            json.dump(context_dict, f, indent=2)
        
        agent_logger.debug(f"Saved context to {file_path}")
        return session_id
    
    def load_context(self, session_id: str) -> Optional[ConversationContext]:
        """Load conversation context from file.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            Optional[ConversationContext]: Loaded context or None if not found
        """
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            context = self._dict_to_context(data)
            agent_logger.debug(f"Loaded context from {file_path}")
            return context
            
        except FileNotFoundError:
            agent_logger.warning(f"No context found for session {session_id}")
            return None
        except Exception as e:
            agent_logger.error(f"Error loading context: {str(e)}")
            return None
    
    def list_sessions(self) -> list:
        """List all available session IDs.
        
        Returns:
            list: List of session IDs
        """
        sessions = []
        for file in os.listdir(self.storage_dir):
            if file.endswith('.json'):
                sessions.append(file[:-5])  # Remove .json extension
        return sorted(sessions) 