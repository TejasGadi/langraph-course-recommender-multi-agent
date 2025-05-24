from typing import List
from langgraph.prebuilt import create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import Tool, tool
from pydantic import BaseModel, Field
import re
from langchain_openai import ChatOpenAI

# --- Define Input Schema for the tool ---
class CourseValidationInput(BaseModel):
    course: dict = Field(..., description="Metadata of the course to validate")
    profile: dict = Field(..., description="Student profile dictionary")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)

# --- Tool: Validate course suitability ---
@tool(
    description="Validate course suitability against a student's profile and provide matches, mismatches, and clarifying questions.",
    args_schema=CourseValidationInput
)
def validate_course_tool(course: dict, profile: dict) -> dict:
    validation = {
        "score": 0,
        "matches": [],
        "mismatches": [],
        "questions": []
    }

    # Education level check
    if profile.get("education_level") and profile["education_level"].lower() in course.get("level", "").lower():
        validation["score"] += 1
        validation["matches"].append(f"Education level ({course.get('level')}) matches your current level.")
    else:
        validation["mismatches"].append(f"Course level ({course.get('level')}) might not match your education level.")
        validation["questions"].append(f"Are you comfortable with a course at {course.get('level')} level?")

    # Mode preference check
    if profile.get("preferred_mode") and course.get("mode") and course["mode"].lower() == profile["preferred_mode"].lower():
        validation["score"] += 1
        validation["matches"].append(f"Delivery mode ({course['mode']}) matches your preference.")
    else:
        validation["mismatches"].append(f"Course mode ({course.get('mode')}) differs from your preferred mode.")
        validation["questions"].append(f"Would you consider a {course.get('mode')} course?")

    # Time commitment check
    if "availability" in profile and profile["availability"]:
        try:
            daily_commitment = course.get("daily_commitment", "")
            hours = int(re.search(r"\d+", daily_commitment).group())
            available_hours = int(profile["availability"].get("hours_per_day", 24))
            if hours <= available_hours:
                validation["score"] += 1
                validation["matches"].append("Time commitment fits your availability.")
            else:
                validation["mismatches"].append(f"Required time ({daily_commitment}) might exceed your availability.")
                validation["questions"].append("Can you accommodate this time commitment?")
        except Exception:
            validation["questions"].append(f"Can you commit {course.get('daily_commitment')}?")

    # Prerequisites check
    if course.get("prerequisites"):
        validation["questions"].append("Do you meet these prerequisites: " + ", ".join(course["prerequisites"]))

    # Career goals alignment check
    if profile.get("career_goals") and course.get("career_outcomes"):
        matched_goals = [goal for goal in profile["career_goals"]
                        if any(goal.lower() in outcome.lower() for outcome in course["career_outcomes"])]
        if matched_goals:
            validation["score"] += 1
            validation["matches"].append("Course aligns with your career goals.")

    # Format a readable message summarizing validation
    message_lines = [f"\nRegarding {course.get('title')} by {course.get('provider')}:"]
    if validation["matches"]:
        message_lines.append("\nPositive matches:")
        message_lines.extend([f"✓ {m}" for m in validation["matches"]])
    if validation["mismatches"]:
        message_lines.append("\nPotential concerns:")
        message_lines.extend([f"! {m}" for m in validation["mismatches"]])
    if validation["questions"]:
        message_lines.append("\nQuestions to consider:")
        message_lines.extend([f"? {q}" for q in validation["questions"]])

    message = "\n".join(message_lines)

    return {
        "validation": validation,
        "message": message
    }


# --- Agent class using React agent ---
tools=[
    Tool(
        name="validate_course_tool",
        func=validate_course_tool,
        description="Validate course suitability against a student's profile and provide matches, mismatches, and clarifying questions.",
        args_schema=CourseValidationInput
    )
]


class CourseSuitabilityAgent:
    def __init__(self, llm: BaseChatModel = llm, tools: List[Tool] = tools):
        self.agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=(
                "You are a suitability analysis agent. Evaluate how suitable a given course is for the student, "
                "based on their profile, constraints, and preferences. "
                "Ask clarifying questions if needed. "
                "If the user requires career advice, handoff to the career advisor agent."
            )
        )

    def as_runnable(self):
        return self.agent