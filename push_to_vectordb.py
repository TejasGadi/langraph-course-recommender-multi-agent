import os
import json
from typing import List
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from pydantic import Field, BaseModel

# === CONFIG ===
PINECONE_INDEX_NAME = "course-index"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
os.environ["PINECONE_API_KEY"] = os.environ.get("PINECONE_API_KEY")

class CourseSchema(BaseModel):
    """Model for course schema"""
    title: str = Field(..., description="Name of the course")
    description: str = Field(..., description="Description of the course")
    provider_of_course: str = Field(..., description="Provider/Platform or institution of the course")
    daily_commitment_hours: str = Field(..., description="e.g., 2 hours/day")
    start_date: str = Field(..., description="Start date i.e. When it begins")
    duration: str = Field(..., description="Total length of course (e.g., 6 months or 4 years)")
    time_of_the_day: str = Field(..., description="Time of day (e.g., evening)")
    mode: str = Field(..., description="online / offline / hybrid")
    language: str = Field(..., description="Medium of instruction")
    prerequisites: List[str] = Field(default_factory=list, description="Required skills/knowledge List")
    suitable_academic_level_required: str = Field(..., description="Suitable academic level required")
    course_rating: str = Field(..., description="Course rating in range 1 to 5 (float values)")


# === Sample Course Data ===
# You can also load this from a file
file_path = "courses.jsonl"

courses_dataset = []
with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        courses_dataset.append(json.loads(line))

# === Convert course data to LangChain Documents ===
def convert_to_documents(courses: List[dict]) -> List[Document]:
    documents = []
    for course in courses:
        content = f"{course['title']}\n\n{course['description']}"
        metadata = course.get("metadata", {})
        metadata["id"] = course.get("id")
        documents.append(Document(page_content=content, metadata=metadata))
    return documents

def push_to_pinecone(courses: List[dict]):
    if not OPENAI_API_KEY:
        raise ValueError("Missing OPENAI_API_KEY in environment.")

    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=PINECONE_INDEX_NAME,
        embedding=embeddings
    )

    documents = convert_to_documents(courses)
    vectorstore.add_documents(documents)
    print(f"Pushed {len(documents)} courses to Pinecone index '{PINECONE_INDEX_NAME}'.")

# === Main ===
if __name__ == "__main__":
    push_to_pinecone(courses_dataset)