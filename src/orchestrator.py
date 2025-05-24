import uuid
from typing import List, Dict, Optional, Callable
from langgraph.func import entrypoint, task
from langchain.schema import AIMessage, HumanMessage
from src.agents.student_profile_agent import StudentProfileAgent
from src.agents.course_discovery_agent import CourseDiscoveryAgent
from src.agents.course_suitability_agent import CourseSuitabilityAgent
from src.agents.career_path_agent import CareerPathAgent
from langgraph.graph import add_messages
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver

def generate_uuid_from_text(text: str) -> str:
    """Generate a consistent UUID from a string input."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, text))

# Initialize agents once
AGENTS = {
    "profile": StudentProfileAgent().as_runnable(),
    "discovery": CourseDiscoveryAgent().as_runnable(),
    "suitability": CourseSuitabilityAgent().as_runnable(),
    "career": CareerPathAgent().as_runnable(),
}

@task
async def invoke_agent(agent_key: str, messages: List[Dict]) -> List[Dict]:
    agent = AGENTS.get(agent_key)
    if not agent:
        raise ValueError(f"Unknown agent key: {agent_key}")
    response = await agent.ainvoke({"messages": messages})  # <- this is the fix
    return response.get("messages", [])

checkpointer = MemorySaver()

@entrypoint(checkpointer=checkpointer)
async def orchestrate_conversation(
    new_message: Dict,
    history: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    Orchestrates the multi-turn conversation by delegating to agents based on tool calls.
    
    Args:
        new_message: Incoming user or system message dict
        history: Previous messages in the conversation
    
    Returns:
        List of messages from the last invoked agent or conversation end.
    """
    history = history or []
    conversation = add_messages(history, new_message)

    # Start conversation with the profile agent
    current_agent_key = "profile"

    while True:
        agent_messages = invoke_agent(current_agent_key, conversation)
        conversation = add_messages(conversation, agent_messages)

        # Find the last AIMessage in agent responses
        ai_messages = [m for m in reversed(agent_messages) if isinstance(m, AIMessage)]
        if not ai_messages:
            # No AI response means end conversation or error
            return agent_messages

        last_ai_msg = ai_messages[0]

        # If no tool calls, await user input
        if not last_ai_msg.tool_calls:
            user_ready_signal = interrupt(value="Ready for user input.")
            user_msg = {
                "role": "user",
                "content": user_ready_signal,
                "id": generate_uuid_from_text(user_ready_signal),
            }
            conversation = add_messages(conversation, [user_msg])
            continue

        # Determine next agent based on last tool call name
        last_tool_call = last_ai_msg.tool_calls[-1]
        tool_name = last_tool_call.get("name", "").lower()

        if "profile" in tool_name:
            current_agent_key = "profile"
        elif "discovery" in tool_name:
            current_agent_key = "discovery"
        elif "suitability" in tool_name:
            current_agent_key = "suitability"
        elif "career" in tool_name:
            current_agent_key = "career"
        else:
            # If tool call does not match known agents, end conversation
            return agent_messages


class Orchestrator:
    """Wrapper class for managing the conversation lifecycle."""

    def __init__(self):
        self.thread_id = str(uuid.uuid4())
        self.workflow = orchestrate_conversation

    async def process(self, user_text: str) -> List[str]:
        """
        Processes incoming user text, running it through the orchestrator workflow.
        
        Args:
            user_text: Raw input from user.
        
        Returns:
            List of responses from agents.
        """
        input_message = {
            "role": "user",
            "content": user_text,
            "id": generate_uuid_from_text(user_text),
        }

        thread_config = {"configurable": {"thread_id": self.thread_id}}
        collected_responses = []

        async for update in self.workflow.astream(
            input_message,
            config=thread_config,
            stream_mode="updates",
        ):
            for _, messages in update.items():
                if isinstance(messages, list) and messages:
                    last_msg = messages[-1]
                    # Support both dict and object message types
                    content = (
                        last_msg.get("content")
                        if isinstance(last_msg, dict)
                        else getattr(last_msg, "content", None)
                    )
                    if content:
                        collected_responses.append(content)

        return collected_responses

graph = orchestrate_conversation