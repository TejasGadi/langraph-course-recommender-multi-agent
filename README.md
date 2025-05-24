# Multi-Agent Course Recommendation System

A sophisticated multi-agent system that provides personalized course and career recommendations using LangGraph and LangChain.

## 🌟 Features

- **Intelligent Profile Collection**: Conversational interface to gather student information
- **Smart Course Discovery**: Uses both vector database and web search for comprehensive course finding
- **Course Validation**: Validates courses against student preferences and requirements
- **Career Guidance**: Provides career path insights based on selected courses
- **Self-Improving**: Automatically stores new course information for future recommendations

## 🤖 Agents

1. **Student Profile Agent**
   - Collects educational background
   - Gathers interests and preferences
   - Understands career aspirations

2. **Course Discovery Agent**
   - Searches vector DB for courses
   - Performs web searches when needed
   - Indexes new courses automatically

3. **Course Suitability Agent**
   - Validates course metadata
   - Matches student preferences
   - Filters unsuitable recommendations

4. **Career Path Agent**
   - Suggests career trajectories
   - Provides industry insights
   - Recommends skill development

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/course-recommender-multi-agent.git
   cd course-recommender-multi-agent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API keys:
   ```env
   OPENAI_API_KEY=your_openai_key
   TAVILY_API_KEY=your_tavily_key
   EXA_API_KEY=your_exa_key
   ```

## 🚀 Usage

Run the system:
```bash
python src/main.py
```

Example interaction:
```
🎓 Welcome to the Course Recommendation System!
I'll help you find the perfect courses for your educational journey.
Type 'quit' to exit.

You: Hi, I'm in 11th grade and interested in computer science
Assistant: Hello! It's great to meet you. I'd love to help you explore computer science courses...
```

## 🏗️ Architecture

The system uses LangGraph for workflow management and includes:

- Vector database (ChromaDB) for course storage
- Web search integration (Tavily) for real-time course discovery
- OpenAI's GPT-4 for natural language understanding
- Pydantic models for data validation

## 📝 Data Models

- **Student Profile**: Education level, interests, preferences
- **Course Metadata**: Title, provider, duration, prerequisites, etc.
- **Career Insights**: Job opportunities, progression paths, skills

## 🔄 Workflow

1. Profile Collection → Course Discovery → Course Validation → Career Guidance
2. Each phase can loop back if needed (e.g., broadening search criteria)
3. Continuous improvement through new course indexing

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- LangChain and LangGraph teams
- OpenAI for GPT-4
- Tavily for web search capabilities 