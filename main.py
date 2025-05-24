"""CLI interface for the Course Recommendation System."""

import asyncio
import os
from dotenv import load_dotenv
from src.orchestrator import Orchestrator 

async def main():
    """Run the course recommendation system."""
    # Load environment variables
    load_dotenv()
    
    # Check for required API keys
    required_keys = ["OPENAI_API_KEY", "TAVILY_API_KEY", "EXA_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print("Error: Missing required API keys:", ", ".join(missing_keys))
        print("Please set these environment variables in a .env file")
        return
    
    # Initialize the orchestrator
    orchestrator = Orchestrator()
    
    print("🎓 Welcome to the Course Recommendation System!")
    print("I'll help you find the perfect courses for your educational journey.")
    print("Type 'quit' to exit.\n")
    
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print("\nThank you for using the Course Recommendation System. Good luck with your studies! 👋")
            break
        
        try:
            # Process the message through the agent workflow
            responses = await orchestrator.process_message(user_input)
            
            # Print agent responses
            for response in responses:
                print("\nAssistant:", response)
                
        except Exception as e:
            print(f"\nError: Something went wrong - {str(e)}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    asyncio.run(main()) 