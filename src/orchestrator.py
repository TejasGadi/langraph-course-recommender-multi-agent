"""Main orchestrator for the Course Recommendation System."""

from typing import Dict, List, Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage, AIMessage
from src.agents.student_profile_agent import StudentProfileAgent
from src.agents.course_discovery_agent import CourseDiscoveryAgent
from src.agents.course_suitability_agent import CourseSuitabilityAgent
from src.agents.career_path_agent import CareerPathAgent
from src.models.base_models import ConversationContext

class GraphState(TypedDict):
    """State maintained between nodes in the graph."""
    context: ConversationContext
    messages: List[Dict]
    next_action: str
    error: str | None

def create_agent_graph() -> StateGraph:
    """Create the agent workflow graph.
    
    Returns:
        StateGraph: Configured workflow graph
    """
    # Initialize agents
    profile_agent = StudentProfileAgent()
    discovery_agent = CourseDiscoveryAgent()
    suitability_agent = CourseSuitabilityAgent()
    career_agent = CareerPathAgent()
    
    # Create the graph
    workflow = StateGraph(GraphState)
    
    # Define agent nodes
    async def profile_node(state: GraphState) -> GraphState:
        """Process student profile collection."""
        try:
            context = state["context"]
            response = await profile_agent.process(context)
            state["next_action"] = response.next_action
            state["messages"].append({"role": "assistant", "content": response.message})
            state["error"] = None
        except Exception as e:
            state["error"] = f"Error in profile collection: {str(e)}"
            state["next_action"] = "retry_profile"
        return state
    
    async def discovery_node(state: GraphState) -> GraphState:
        """Process course discovery."""
        try:
            context = state["context"]
            response = await discovery_agent.process(context)
            state["next_action"] = response.next_action
            state["messages"].append({"role": "assistant", "content": response.message})
            state["error"] = None
        except Exception as e:
            state["error"] = f"Error in course discovery: {str(e)}"
            state["next_action"] = "retry_discovery"
        return state
    
    async def suitability_node(state: GraphState) -> GraphState:
        """Process course suitability validation."""
        try:
            context = state["context"]
            response = await suitability_agent.process(context)
            state["next_action"] = response.next_action
            state["messages"].append({"role": "assistant", "content": response.message})
            state["error"] = None
        except Exception as e:
            state["error"] = f"Error in suitability check: {str(e)}"
            state["next_action"] = "retry_suitability"
        return state
    
    async def career_node(state: GraphState) -> GraphState:
        """Process career guidance."""
        try:
            context = state["context"]
            response = await career_agent.process(context)
            state["next_action"] = response.next_action
            state["messages"].append({"role": "assistant", "content": response.message})
            state["error"] = None
        except Exception as e:
            state["error"] = f"Error in career guidance: {str(e)}"
            state["next_action"] = "retry_career"
        return state
    
    async def end_node(state: GraphState) -> GraphState:
        """End the conversation."""
        state["messages"].append({
            "role": "assistant", 
            "content": "Thank you for using the Course Recommendation System. Is there anything else you'd like to know?"
        })
        return state
    
    # Add nodes to the graph
    workflow.add_node("profile", profile_node)
    workflow.add_node("discovery", discovery_node)
    workflow.add_node("suitability", suitability_node)
    workflow.add_node("career", career_node)
    workflow.add_node("end", end_node)
    
    # Define conditional edges
    def should_continue_profile(state: GraphState) -> str:
        """Determine if profile collection should continue."""
        if state["error"]:
            return "profile"
        if state["next_action"] == "continue_profile":
            return "profile"
        if state["next_action"] == "retry_profile":
            return "profile"
        if state["next_action"] == "complete_profile":
            return "profile"
        return "discovery"
    
    def should_retry_discovery(state: GraphState) -> str:
        """Determine if course discovery should be retried."""
        if state["error"]:
            return "discovery"
        if state["next_action"] == "broaden_search":
            return "discovery"
        if state["next_action"] == "find_courses":
            return "discovery"
        if state["next_action"] == "retry_discovery":
            return "discovery"
        if state["next_action"] == "suitability":
            return "suitability"
        return "suitability"
    
    def should_validate_more(state: GraphState) -> str:
        """Determine if more course validation is needed."""
        if state["error"]:
            return "suitability"
        if state["next_action"] == "find_courses":
            return "discovery"
        if state["next_action"] == "validate_courses":
            return "suitability"
        if state["next_action"] == "retry_suitability":
            return "suitability"
        if state["next_action"] == "explore_careers":
            return "career"
        return "career"
    
    def should_end(state: GraphState) -> str:
        """Determine if the workflow should end."""
        if state["error"]:
            return "career"
        if state["next_action"] == "complete":
            return "end"
        if state["next_action"] == "explore_more_courses":
            return "discovery"
        if state["next_action"] == "validate_more_courses":
            return "suitability"
        if state["next_action"] == "update_profile":
            return "profile"
        return "career"
    
    # Add edges to the graph
    workflow.add_edge("profile", should_continue_profile)
    workflow.add_edge("discovery", should_retry_discovery)
    workflow.add_edge("suitability", should_validate_more)
    workflow.add_edge("career", should_end)
    workflow.add_edge("end", lambda _: END)
    
    # Set entry point
    workflow.set_entry_point("profile")
    
    # Compile the graph
    app = workflow.compile()
    
    return app

class Orchestrator:
    """Main orchestrator for the course recommendation system."""
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.workflow = create_agent_graph()
        self.context = ConversationContext()
    
    async def process_message(self, message: str) -> List[str]:
        """Process a user message through the agent workflow.
        
        Args:
            message (str): User's message
            
        Returns:
            List[str]: List of agent responses
        """
        # Update chat history
        self.context.chat_history.append({"role": "user", "content": message})
        
        # Prepare initial state
        state = {
            "context": self.context,
            "messages": [],
            "next_action": "start",
            "error": None
        }
        
        # Run the workflow
        final_state = await self.workflow.arun(state)
        
        # Update context with final state
        self.context = final_state["context"]
        
        # Return agent messages
        return [msg["content"] for msg in final_state["messages"]] 