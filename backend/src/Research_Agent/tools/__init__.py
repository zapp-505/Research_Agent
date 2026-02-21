# Tools module
from tavily import TavilyClient
import os
import dotenv
from chromadb import Client
from semanticscholar import SemanticScholar

dotenv.load_dotenv()
tavily_api_key = os.getenv("TAVILY_API")
print(f"Tavily API Key: {tavily_api_key}")
# Step 1. Instantiating your TavilyClient

tavily_client = TavilyClient(api_key=tavily_api_key)

# Initialize ChromaDB client
chroma_client = Client()

# Initialize Semantic Scholar client
sch = SemanticScholar()

# Step 2. Executing a simple search query
response = tavily_client.search("Who is Leo Messi?")

# Store the response in ChromaDB
document_id = "leo_messi_info"
chroma_client.add(document_id, response)

# Retrieve the response from ChromaDB
retrieved_response = chroma_client.get(document_id)

# Step 3. That's it! You've done a Tavily Search and stored the response in ChromaDB!
print("Retrieved Response:", retrieved_response)

# Fetch details of a paper by its ID
paper_id = "10.1145/3366423.3380276"
paper = sch.get_paper(paper_id)

# Print paper details
print("Paper Title:", paper["title"])
print("Authors:", ", ".join(author["name"] for author in paper["authors"]))