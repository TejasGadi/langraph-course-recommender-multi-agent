from setuptools import setup, find_packages

setup(
    name="course-recommender",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langgraph",
        "openai",
        "chromadb",
        "tavily-python",
    ],
    python_requires=">=3.9",
) 