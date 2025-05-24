from langchain_core.language_models import BaseChatModel
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)

class CareerPathAnalysisInput(BaseModel):
    query: str = Field(..., description="The query to analyze the career path.")

def ask_llm(query: str) -> str:
    return llm.invoke(query)

tools=[
    Tool(
        name="career_path_analysis",
        func=ask_llm,
        description="A tool to give insights into the career path as per selected courses or user's ask in the query",
        args_schema=CareerPathAnalysisInput
    )
]

class CareerPathAgent:
    def __init__(self, llm: BaseChatModel=llm, tools: list[Tool]=tools):
        self.agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=(
                "You are a career advisor. Provide insights into potential career paths aligned with the student's "
                "profile and selected courses. Offer guidance on next steps, degrees, and skill-building."
            )
        )

    def as_runnable(self):
        return self.agent
