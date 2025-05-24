"""Career Path Agent for providing career guidance based on selected courses."""

from typing import List, Dict
from langchain_community.tools import TavilySearchResults
from src.agents.base_agent import BaseAgent
from src.models.base_models import AgentResponse, ConversationContext, CourseMetadata
from src.config.config import TAVILY_API_KEY

class CareerPathAgent(BaseAgent):
    """Agent responsible for providing career guidance."""
    
    def __init__(self):
        """Initialize the Career Path Agent."""
        super().__init__("CareerPathAgent")
        self.web_search = TavilySearchResults(api_key=TAVILY_API_KEY)
    
    async def _get_career_insights(self, courses: List[CourseMetadata], career_goals: List[str]) -> Dict:
        """Get career insights for the given courses and goals.
        
        Args:
            courses (List[CourseMetadata]): Validated courses
            career_goals (List[str]): Student's career goals
            
        Returns:
            Dict: Career insights and recommendations
        """
        # Collect all career outcomes from courses
        all_outcomes = []
        for course in courses:
            all_outcomes.extend(course.career_outcomes)
        
        # Create a search query for career insights
        search_query = f"career paths and job opportunities for {', '.join(all_outcomes)} roles"
        search_results = self.web_search.invoke(search_query)
        
        # Create a prompt to analyze career paths
        analysis_prompt = """Analyze the following career information and provide insights:
        
        Career Goals: {goals}
        Course Outcomes: {outcomes}
        Market Research: {research}
        
        Provide a structured analysis with:
        1. Immediate job opportunities
        2. Long-term career progression
        3. Additional skills or certifications recommended
        4. Industry trends and outlook
        5. Salary ranges and growth potential
        
        Format the response as a JSON object.
        """
        
        messages = self._create_prompt(
            analysis_prompt,
            {
                "goals": career_goals,
                "outcomes": all_outcomes,
                "research": str(search_results)
            }
        )
        
        response = self.llm.invoke(messages)
        
        try:
            career_insights = eval(response.content)
            return career_insights
        except:
            return {
                "immediate_opportunities": [],
                "career_progression": [],
                "recommended_skills": [],
                "industry_trends": [],
                "salary_info": {}
            }
    
    def _format_career_advice(self, insights: Dict) -> str:
        """Format career insights into a user-friendly message.
        
        Args:
            insights (Dict): Career insights
            
        Returns:
            str: Formatted career advice
        """
        message = ["Here's what I found about your potential career paths:\n"]
        
        if insights.get("immediate_opportunities"):
            message.append("\n🎯 Immediate Job Opportunities:")
            message.extend([f"• {job}" for job in insights["immediate_opportunities"]])
        
        if insights.get("career_progression"):
            message.append("\n📈 Career Progression Path:")
            message.extend([f"• {step}" for step in insights["career_progression"]])
        
        if insights.get("recommended_skills"):
            message.append("\n🔧 Recommended Additional Skills:")
            message.extend([f"• {skill}" for skill in insights["recommended_skills"]])
        
        if insights.get("industry_trends"):
            message.append("\n📊 Industry Trends:")
            message.extend([f"• {trend}" for trend in insights["industry_trends"]])
        
        if insights.get("salary_info"):
            message.append("\n💰 Salary Information:")
            for role, salary in insights["salary_info"].items():
                message.append(f"• {role}: {salary}")
        
        message.append("\nWould you like more specific information about any of these areas?")
        
        return "\n".join(message)
    
    async def process(self, context: ConversationContext) -> AgentResponse:
        """Process the current context and provide career guidance.
        
        Args:
            context (ConversationContext): Current conversation context
            
        Returns:
            AgentResponse: Agent's response with career guidance
        """
        if not context.validated_courses:
            return self._format_response(
                success=False,
                message="No validated courses to analyze. Please validate courses first.",
                next_action="validate_courses"
            )
        
        if not context.student_profile:
            return self._format_response(
                success=False,
                message="Student profile is not complete. Cannot provide career guidance.",
                next_action="complete_profile"
            )
        
        # Get career insights
        career_insights = await self._get_career_insights(
            context.validated_courses,
            context.student_profile.career_goals
        )
        
        # Format career advice
        advice_message = self._format_career_advice(career_insights)
        
        # Update context
        context = self.update_context(
            context,
            current_phase="career_advice_given"
        )
        
        return self._format_response(
            success=True,
            message=advice_message,
            data={
                "career_insights": career_insights,
                "courses": [course.dict() for course in context.validated_courses]
            },
            next_action="complete"
        ) 