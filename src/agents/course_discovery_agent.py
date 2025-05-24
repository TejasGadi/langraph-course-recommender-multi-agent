"""Course Discovery Agent for finding relevant courses using vector DB and web search."""

from typing import List, Dict
import json
from langchain.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import load_prompt
from src.agents.base_agent import BaseAgent
from src.models.base_models import AgentResponse, ConversationContext, CourseMetadata
from src.config.config import OPENAI_API_KEY, TAVILY_API_KEY, VECTOR_DB_PATH, EMBEDDING_MODEL
from langchain_tavily import TavilySearch
from langchain import hub

class CourseDiscoveryAgent(BaseAgent):
    """Agent responsible for discovering relevant courses."""
    
    def __init__(self):
        """Initialize the Course Discovery Agent."""
        super().__init__("CourseDiscoveryAgent")
        self.embeddings = OpenAIEmbeddings(
            api_key=OPENAI_API_KEY,
            model=EMBEDDING_MODEL
        )
        self.vector_store = Chroma(
            collection_name="courses",
            embedding_function=self.embeddings
        )
        
        # Initialize Tavily search tool
        self.tavily_search = TavilySearch(
            api_key=TAVILY_API_KEY,
            max_results=5,
            search_depth="advanced"
        )
        
        # Initialize tools
        self.tools = [
            Tool(
                name="search_courses",
                description="Search for courses in the vector database",
                func=self._search_courses
            ),
            Tool(
                name="web_search",
                description="Search for courses on the web",
                func=self.tavily_search.invoke
            )
        ]
        
        # Initialize LLM and agent
        self.llm = ChatOpenAI(temperature=0)
        
        # Load the default prompt template from LangChain Hub
        self.prompt = hub.pull("hwchase17/openai-tools-agent")
        
        # Create the agent with the default prompt
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools)
        
    def _create_search_query(self, profile: Dict) -> str:
        """Create a search query based on student profile.
        
        Args:
            profile (Dict): Student profile information
            
        Returns:
            str: Formatted search query
        """
        template = """Find {education_level} level courses in {interests} with {mode} delivery format"""
        query = template.format(
            education_level=profile.get('education_level', ''),
            interests=', '.join(profile.get('interests', [])),
            mode=profile.get('preferred_mode', 'any')
        )
        return query
    
    async def _search_courses(self, query: str) -> List[dict]:
        """Search for courses in the vector store.
        
        Args:
            query (str): Search query
            
        Returns:
            List[dict]: List of relevant courses
        """
        results = self.vector_store.similarity_search(query)
        return [doc.metadata for doc in results]
    
    async def _search_web(self, query: str) -> List[CourseMetadata]:
        """Search for courses on the web.
        
        Args:
            query (str): Search query
            
        Returns:
            List[CourseMetadata]: List of found courses
        """
        # Add "online course" or "degree program" to the query
        web_query = f"{query} online course degree program syllabus"
        search_results = self.tavily_search.invoke(web_query)
        
        # Create a prompt to extract course information from search results
        extraction_prompt = """Extract course information from the following search results.
        Format each course as a JSON object matching this schema:
        {
            "title": "course title",
            "provider": "institution/platform",
            "duration": "course duration",
            "daily_commitment": "time commitment",
            "start_date": "start date",
            "schedule": "course schedule",
            "mode": "delivery mode",
            "language": "language",
            "prerequisites": ["prerequisite1", "prerequisite2"],
            "level": "academic level",
            "cost": "course cost",
            "certification": true/false,
            "career_outcomes": ["outcome1", "outcome2"]
        }
        
        Search Results:
        {search_results}
        
        Only include information that is explicitly mentioned. Skip any fields where information is not available.
        """
        
        messages = self._create_prompt(extraction_prompt, {"search_results": str(search_results)})
        response = self.llm.invoke(messages)
        
        try:
            # Parse the extracted courses
            courses_data = json.loads(response.content)
            courses = [CourseMetadata(**course) for course in courses_data]
            
            # Store new courses in vector DB
            for course in courses:
                self.vector_store.add_texts(
                    texts=[json.dumps(course.dict())],
                    metadatas=[{"source": "web_search"}]
                )
            
            return courses
        except:
            return []
    
    async def process(self, context: ConversationContext) -> AgentResponse:
        """Process the current conversation context.
        
        Args:
            context (ConversationContext): Current conversation context
            
        Returns:
            AgentResponse: Agent's response and next action
        """
        if not context.student_profile:
            return self._format_response(
                success=False,
                message="Student profile is not complete. Please complete the profile first.",
                next_action="complete_profile"
            )
        
        # Prepare search query
        query = f"Find courses matching: Education level - {context.student_profile.education_level}, "
        query += f"Interests - {', '.join(context.student_profile.interests)}, "
        query += f"Career goals - {', '.join(context.student_profile.career_aspirations)}"
        
        try:
            # Execute agent to find courses
            result = await self.agent_executor.ainvoke({"input": query})
            
            # Update context with discovered courses
            context.courses.extend(result.get("courses", []))
            
            return AgentResponse(
                message=result["output"],
                next_action="suitability" if context.courses else "broaden_search"
            )
            
        except Exception as e:
            return AgentResponse(
                message=f"I encountered an error while searching for courses: {str(e)}",
                next_action="broaden_search"
            ) 