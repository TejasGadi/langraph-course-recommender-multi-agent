from langchain_core.language_models import BaseChatModel
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from src.config.config import PINECONE_API_KEY
from langchain_openai import ChatOpenAI
from langchain_core.tools.retriever import create_retriever_tool

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)
retriever = PineconeVectorStore.from_existing_index(index_name="course-index", embedding=OpenAIEmbeddings(api_key=PINECONE_API_KEY)).as_retriever()

retriever_tool = create_retriever_tool(
    retriever,
    "pinecone_search",
    "A tool to search the Pinecone vector database for relevant course information.",
)


class TavilySearchInput(BaseModel):
    query: str = Field(..., description="The query to search the web for relevant course information.")

class PineconeSearchInput(BaseModel):
    query: str = Field(..., description="The query to search the Pinecone vector database for relevant course information.")


tools=[
    Tool(
        name="tavily_search",
        func=TavilySearchResults(max_results=5),
        description="A tool to search the web for relevant course information.",
        args_schema=TavilySearchInput
    ),
    retriever_tool
]

class CourseDiscoveryAgent:
    def __init__(self, llm: BaseChatModel=llm, tools: list[Tool]=tools):
        self.agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=(
                "You are a course discovery agent. Recommend relevant courses (school, college, or online) "
                "based on the student's profile. Use tools to switch to other agents if needed."
            )
        )

    def as_runnable(self):
        return self.agent