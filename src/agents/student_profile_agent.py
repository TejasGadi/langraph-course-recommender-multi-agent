from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import json
from typing import List, Dict, Optional
from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import Tool
from pydantic import BaseModel, Field

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)


# Input schema for extract_student_profile tool
class ExtractProfileInput(BaseModel):
    chat_history: List[Dict[str, str]] = Field(
        ..., description="List of message dictionaries with roles and content representing the conversation history."
    )

def extract_student_profile(chat_history: List[Dict[str, str]]) -> dict:
    """Extract structured student profile data from conversation history."""
    prompt = (
        "Extract the student's profile information from the chat history below.\n\n"
        "Return a JSON object with the following fields:\n"
        "- education_level\n"
        "- academic_background\n"
        "- interests\n"
        "- preferred_mode\n"
        "- availability\n"
        "- career_goals\n\n"
        "Only include what is explicitly mentioned. Use null for missing fields.\n\n"
        "Chat History:\n"
        f"{json.dumps(chat_history, indent=2)}"
    )
    response = llm.invoke([{"role": "user", "content": prompt}])
    try:
        return json.loads(response.content)
    except Exception:
        return {}

# Tool: Determine which field is missing
# Input schema for determine_missing_field tool
class DetermineMissingFieldInput(BaseModel):
    profile: Dict[str, Optional[str]] = Field(
        ..., description="Partial or full student profile dictionary to determine missing fields."
    )


def determine_missing_field(profile: Dict[str, Optional[str]]) -> str:
    """Determine which profile section to ask next based on missing fields."""
    if not profile.get("education_level"):
        return "initial"
    elif not profile.get("interests"):
        return "interests"
    elif not profile.get("preferred_mode") or not profile.get("availability"):
        return "preferences"
    elif not profile.get("career_goals"):
        return "career_goals"
    return "complete"


tools=[
    Tool(
        name="extract_student_profile",
        func=extract_student_profile,
        description="Extract structured student profile data from a conversation chat history.",
        args_schema=ExtractProfileInput
    ),
    Tool(
        name="determine_missing_field",
        func=determine_missing_field,
        description="Determine which profile section is missing and should be asked next.",
        args_schema=DetermineMissingFieldInput
    )
]

# StudentProfileAgent
class StudentProfileAgent:
    def __init__(self, llm: BaseChatModel = llm, tools: List[Tool] = tools):
        self.agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=(
                "You are a student profiling agent. Your job is to interact with students "
                "to gather their academic and career profile. Ask questions to extract:\n"
                "- education level\n"
                "- academic background\n"
                "- interests\n"
                "- preferred learning mode (online/offline)\n"
                "- availability (schedule/frequency)\n"
                "- career goals\n\n"
                "Use tools like `extract_student_profile` to extract info from chat history, "
                "and `determine_missing_field` to guide what to ask next. Once the profile is complete, "
                "you must indicate that the handoff to the recommendation agent can happen."
            )
        )

    def as_runnable(self):
        return self.agent