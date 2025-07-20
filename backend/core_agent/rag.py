from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
import chromadb
import os

# Configuration
PERSIST_DIRECTORY = "./chroma_db_hf"
COLLECTION_NAME = "constitution"  # Fixed typo
PDF_PATH = "D:/Company Projects/NyaySetu2.0/backend/core_agent/data/Constitution.pdf"  # Path to the PDF file

# Initialize embeddings
model_name = "BAAI/bge-small-en-v1.5"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': True}

embeddings = HuggingFaceBgeEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# Create persist directory
os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)

# Check if collection exists
try:
    collection = client.get_collection(COLLECTION_NAME)
    db = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings
    )
    print(f"Loaded existing collection '{COLLECTION_NAME}'")

except:
    print(f"Creating new collection '{COLLECTION_NAME}'")
    
    # Read PDF
    reader = PdfReader(PDF_PATH)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text()

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )
    text_chunks = text_splitter.split_text(full_text)

    # Create vector store
    db = Chroma.from_texts(
        texts=text_chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        client=client
    )
    print("New vector store created")

# Search function
def retrieve_documents(query: str):
    """Retrieve relevant documents based on a query.
    Args:
        query (str): The search query.
    Returns:
        list: List of documents.
    """
    k=2
    docs = db.similarity_search(query, k=k)
    results = []
    
    for doc in docs:
        results.append(doc.page_content)
    
    return results