import os
import json
import shutil
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

from pypdf import PdfReader
from docx import Document

# RAG imports
import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

app = FastAPI(title="AI Future Process Designer")


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# GROQ / LLM CLIENT
# ============================================================

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)


# ============================================================
# STORAGE
# ============================================================

UPLOAD_DIR = Path("knowledge_base")
UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================
# RAG / CHROMADB
# ============================================================

CHROMA_DIR = Path("chroma_db")
CHROMA_DIR.mkdir(exist_ok=True)

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name="process_documents"
)


# Local embedding model
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ============================================================
# REQUEST MODEL
# ============================================================

class ProcessRequest(BaseModel):
    process: str


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "AI Future Process Designer API is running!"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# TEXT EXTRACTION
# ============================================================

def extract_text(file_path: Path):

    extension = file_path.suffix.lower()

    # TXT
    if extension == ".txt":
        return file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    # PDF
    if extension == ".pdf":

        reader = PdfReader(str(file_path))

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text

    # DOCX
    if extension == ".docx":

        document = Document(str(file_path))

        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

        return text

    raise ValueError(
        "Unsupported file type. Please upload PDF, DOCX or TXT."
    )


# ============================================================
# TEXT CHUNKING
# ============================================================

def chunk_text(text, chunk_size=1000, overlap=200):

    text = text.strip()

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start += chunk_size - overlap

    return chunks


# ============================================================
# ADD DOCUMENT TO RAG KNOWLEDGE BASE
# ============================================================

def add_document_to_knowledge_base(
    text,
    filename
):

    chunks = chunk_text(text)

    if not chunks:
        return 0

    # Create embeddings
    embeddings = embedding_model.encode(
        chunks
    ).tolist()

    ids = [
        f"{filename}_{i}"
        for i in range(len(chunks))
    ]

    metadatas = [
        {
            "filename": filename,
            "chunk": i
        }
        for i in range(len(chunks))
    ]

    # Remove old chunks for the same document
    try:

        collection.delete(
            where={
                "filename": filename
            }
        )

    except Exception:
        pass

    # Store in ChromaDB
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return len(chunks)


# ============================================================
# RETRIEVE RELEVANT DOCUMENT INFORMATION
# ============================================================

def retrieve_context(query, top_k=5):

    try:

        query_embedding = embedding_model.encode(
            [query]
        ).tolist()[0]

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        documents = results.get("documents", [[]])[0]

        if not documents:
            return ""

        return "\n\n--- DOCUMENT CONTEXT ---\n\n".join(
            documents
        )

    except Exception as e:

        print("RAG retrieval error:", e)

        return ""


# ============================================================
# PROCESS ANALYSIS
# ============================================================

@app.post("/analyse")
def analyse_process(request: ProcessRequest):

    # --------------------------------------------------------
    # Retrieve relevant information from uploaded documents
    # --------------------------------------------------------

    context = retrieve_context(
        request.process
    )

    # --------------------------------------------------------
    # Build prompt
    # --------------------------------------------------------

    prompt = f"""
You are an Enterprise AI Process Designer.

Analyse the following business process:

CURRENT BUSINESS PROCESS:
{request.process}

Relevant information retrieved from uploaded enterprise
documents is provided below.

DOCUMENT CONTEXT:
{context if context else "No relevant uploaded document context was found."}

Your goal is to identify realistic opportunities to improve
the process using:

- AI
- automation
- better data flows
- human decision-making

Provide your response using these sections:

1. Current Process
2. Key Problems and Bottlenecks
3. AI Opportunities
4. Tasks That Should Remain Human
5. Proposed Future Process
6. Expected Benefits
7. Risks and Considerations
8. AI Recommendations

Important rules:

- Do not invent facts.
- Use the uploaded document context when it is relevant.
- Do not assume AI should replace humans.
- Clearly distinguish AI opportunities from normal software automation.
- Keep important decisions and accountability with humans.
- Recommendations should be practical for an enterprise environment.
- Keep the answer concise and specific.

Return ONLY valid JSON in exactly this structure:

{{
    "current_process": "Brief description",
    "bottlenecks": [
        "problem 1",
        "problem 2"
    ],
    "ai_opportunities": [
        "opportunity 1",
        "opportunity 2"
    ],
    "human_tasks": [
        "human task 1",
        "human task 2"
    ],
    "future_process": [
        "step 1",
        "step 2",
        "step 3"
    ],
    "benefits": [
        "benefit 1",
        "benefit 2"
    ],
    "risks": [
        "risk 1",
        "risk 2"
    ],
    "recommendations": [
        "recommendation 1",
        "recommendation 2"
    ]
}}

Do not include Markdown, code fences, or any text outside the JSON.
"""

    # --------------------------------------------------------
    # Call Groq
    # --------------------------------------------------------

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
        )

        content = response.choices[0].message.content

        # Remove accidental markdown fences if model adds them
        content = content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

        analysis = json.loads(content)

        analysis["rag_used"] = bool(context)
        analysis["rag_chunks"] = collection.count()

        return analysis

    except Exception as e:

        return {
            "error": str(e)
        }


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@app.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...)
):

    allowed_extensions = {
        ".pdf",
        ".docx",
        ".txt"
    }

    extension = Path(file.filename).suffix.lower()

    if extension not in allowed_extensions:

        return {
            "error": "Only PDF, DOCX and TXT files are supported."
        }

    safe_filename = Path(file.filename).name

    file_path = UPLOAD_DIR / safe_filename

    # Save uploaded file
    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    # Extract text
    try:

        extracted_text = extract_text(
            file_path
        )

    except Exception as e:

        file_path.unlink(
            missing_ok=True
        )

        return {
            "error": f"Could not read document: {str(e)}"
        }

    # Save extracted text
    text_path = (
        UPLOAD_DIR /
        f"{file_path.stem}.txt"
    )

    text_path.write_text(
        extracted_text,
        encoding="utf-8"
    )

    # Add to RAG knowledge base
    try:

        chunks_added = add_document_to_knowledge_base(
            extracted_text,
            safe_filename
        )

    except Exception as e:

        return {
            "error": f"Document extracted but RAG indexing failed: {str(e)}"
        }

    return {
        "message": "Document processed successfully.",
        "filename": safe_filename,
        "characters_extracted": len(extracted_text),
        "chunks_added": chunks_added,
        "text_preview": extracted_text[:1000]
    }


# ============================================================
# LIST KNOWLEDGE BASE DOCUMENTS
# ============================================================

@app.get("/documents")
def list_documents():

    documents = []

    for file in UPLOAD_DIR.iterdir():

        if file.is_file():

            documents.append({
                "filename": file.name,
                "size": file.stat().st_size
            })

    return {
        "documents": documents
    }


# ============================================================
# RAG STATUS
# ============================================================

@app.get("/rag-status")
def rag_status():

    try:

        count = collection.count()

        return {
            "status": "ready",
            "documents_chunks": count
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }