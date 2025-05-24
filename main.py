import asyncio
from src.orchestrator import Orchestrator

def main():
    print("🎓 Welcome to the Course Recommendation System!")
    print("I'll help you find the perfect courses for your educational journey.")
    print("Type 'quit' to exit.\n")

    orchestrator = Orchestrator()

    async def chat_loop():
        while True:
            user_input = input("You: ")
            if user_input.lower() in {"quit", "exit"}:
                break

            try:
                responses = await orchestrator.process(user_input)
                print("\nAssistant:")
                for response in responses:
                    print(response)
                print()
            except Exception as e:
                print(f"\nAssistant:\nError: Something went wrong - {e}\n")

    asyncio.run(chat_loop())

if __name__ == "__main__":
    main()
