"""Course Suitability Agent for validating courses against student preferences."""

from typing import List, Dict
from src.agents.base_agent import BaseAgent
from src.models.base_models import AgentResponse, ConversationContext, CourseMetadata

class CourseSuitabilityAgent(BaseAgent):
    """Agent responsible for validating course suitability."""
    
    def __init__(self):
        """Initialize the Course Suitability Agent."""
        super().__init__("CourseSuitabilityAgent")
        
    def _validate_course(self, course: CourseMetadata, profile: Dict) -> Dict[str, any]:
        """Validate a course against student preferences.
        
        Args:
            course (CourseMetadata): Course to validate
            profile (Dict): Student profile
            
        Returns:
            Dict[str, any]: Validation results
        """
        validation = {
            "score": 0,
            "matches": [],
            "mismatches": [],
            "questions": []
        }
        
        # Check education level compatibility
        if profile['education_level'].lower() in course.level.lower():
            validation["score"] += 1
            validation["matches"].append(f"Education level ({course.level}) matches your current level")
        else:
            validation["mismatches"].append(f"Course level ({course.level}) might not match your education level")
            validation["questions"].append(f"Are you comfortable with a course at {course.level} level?")
        
        # Check mode preference
        if course.mode.lower() == profile['preferred_mode'].lower():
            validation["score"] += 1
            validation["matches"].append(f"Delivery mode ({course.mode}) matches your preference")
        else:
            validation["mismatches"].append(f"Course mode ({course.mode}) differs from your preferred mode")
            validation["questions"].append(f"Would you consider a {course.mode} course?")
        
        # Check time commitment
        if "availability" in profile:
            # Extract time from daily_commitment (e.g., "2 hours/day" -> 2)
            try:
                hours = int(''.join(filter(str.isdigit, course.daily_commitment)))
                if hours <= int(profile['availability'].get('hours_per_day', 24)):
                    validation["score"] += 1
                    validation["matches"].append(f"Time commitment fits your availability")
                else:
                    validation["mismatches"].append(f"Required time ({course.daily_commitment}) might exceed your availability")
                    validation["questions"].append("Can you accommodate this time commitment?")
            except:
                validation["questions"].append(f"Can you commit {course.daily_commitment}?")
        
        # Check prerequisites
        if course.prerequisites:
            validation["questions"].append("Do you meet these prerequisites: " + ", ".join(course.prerequisites))
        
        # Check career alignment
        if any(goal.lower() in [outcome.lower() for outcome in course.career_outcomes] 
               for goal in profile['career_goals']):
            validation["score"] += 1
            validation["matches"].append("Course aligns with your career goals")
        
        return validation
    
    def _format_validation_message(self, course: CourseMetadata, validation: Dict) -> str:
        """Format validation results into a user-friendly message.
        
        Args:
            course (CourseMetadata): Validated course
            validation (Dict): Validation results
            
        Returns:
            str: Formatted message
        """
        message = [f"\nRegarding {course.title} by {course.provider}:"]
        
        if validation["matches"]:
            message.append("\nPositive matches:")
            message.extend([f"✓ {match}" for match in validation["matches"]])
        
        if validation["mismatches"]:
            message.append("\nPotential concerns:")
            message.extend([f"! {mismatch}" for mismatch in validation["mismatches"]])
        
        if validation["questions"]:
            message.append("\nQuestions to consider:")
            message.extend([f"? {question}" for question in validation["questions"]])
        
        return "\n".join(message)
    
    async def process(self, context: ConversationContext) -> AgentResponse:
        """Process the current context and validate discovered courses.
        
        Args:
            context (ConversationContext): Current conversation context
            
        Returns:
            AgentResponse: Agent's response with validation results
        """
        if not context.discovered_courses:
            return self._format_response(
                success=False,
                message="No courses to validate. Please discover courses first.",
                next_action="find_courses"
            )
        
        if not context.student_profile:
            return self._format_response(
                success=False,
                message="Student profile is not complete. Cannot validate courses.",
                next_action="complete_profile"
            )
        
        validated_courses = []
        validation_messages = []
        profile_dict = context.student_profile.dict()
        
        for course in context.discovered_courses:
            validation = self._validate_course(course, profile_dict)
            if validation["score"] >= 2:  # At least 2 positive matches
                validated_courses.append(course)
                validation_messages.append(self._format_validation_message(course, validation))
        
        if not validated_courses:
            return self._format_response(
                success=False,
                message="None of the discovered courses seem to be a good fit. Let me search for alternatives.",
                next_action="find_courses"
            )
        
        # Update context with validated courses
        context = self.update_context(
            context,
            validated_courses=validated_courses,
            current_phase="courses_validated"
        )
        
        response_message = (
            f"I've analyzed {len(context.discovered_courses)} courses and found {len(validated_courses)} "
            f"that match your profile well.\n{''.join(validation_messages)}\n\n"
            f"Would you like to know more about the career paths these courses can lead to?"
        )
        
        return self._format_response(
            success=True,
            message=response_message,
            data={
                "validated_courses": [course.dict() for course in validated_courses],
                "validation_details": validation_messages
            },
            next_action="explore_careers"
        ) 