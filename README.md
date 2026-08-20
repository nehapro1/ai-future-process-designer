AI Future Process Designer

An enterprise AI application that analyzes existing business processes and recommends future workflows using AI, automation, human oversight, and Retrieval-Augmented Generation (RAG).

Overview

The AI Future Process Designer helps organizations understand how an existing business process can be improved.

Users can either:

Describe a business process directly in the application, or

Upload a PDF, DOCX, or TXT process document.

The application then analyzes the process and identifies:

Current Process

Bottlenecks

AI Opportunities

Human Responsibilities

Expected Benefits

Proposed Future Process

Risks & Considerations

AI Recommendations

Uploaded documents are processed into text chunks, converted into embeddings, stored in ChromaDB, and retrieved when relevant during analysis.

Architecture

                    ┌──────────────────────┐
                    │   React Frontend     │
                    │      Vite App        │
                    └──────────┬───────────┘
                               │
                    HTTP REST API / JSON
                               │
                               ▼
                    ┌──────────────────────┐
                    │   FastAPI Backend    │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       Document Parser    RAG Pipeline       Groq LLM
       PDF / DOCX / TXT   ChromaDB +         Llama 3.3
                           Embeddings

Key Features

1. Business Process Analysis

Users can enter a process such as:

Employees submit leave requests by email.
Managers review them.
HR manually updates Excel and sends the information to payroll.

The AI identifies bottlenecks, automation opportunities, human responsibilities, risks, and a future-state workflow.

2. Document Upload

Supported formats:

PDF

DOCX

TXT

The backend extracts the document text using:

pypdf for PDF

python-docx for DOCX

Python text handling for TXT

3. RAG Knowledge Base

Uploaded documents are:

Document
   ↓
Text Extraction
   ↓
Chunking
   ↓
Sentence Transformer Embeddings
   ↓
ChromaDB
   ↓
Semantic Retrieval
   ↓
Relevant Context
   ↓
LLM Analysis

This allows the model to use relevant information from uploaded enterprise documents instead of relying only on the text entered in the process field.

4. Human-Centred AI

The application does not simply recommend replacing people with AI.

It separates:

Tasks suitable for AI

Tasks suitable for automation

Tasks that should remain human-controlled

Final decisions and accountability

Technology Stack

Frontend

React

Vite

JavaScript

CSS

Backend

Python

FastAPI

Pydantic

Uvicorn

AI / LLM

Groq API

Llama 3.3 70B Versatile

OpenAI-compatible API client

RAG

ChromaDB

Sentence Transformers

all-MiniLM-L6-v2

Document Processing

pypdf

python-docx

Project Structure

ai-future-process-designer/
│
├── backend/
│   ├── main.py
│   ├── .env
│   ├── knowledge_base/
│   └── chroma_db/
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   ├── package.json
│   └── ...
│
├── .gitignore
└── README.md

Setup

Prerequisites

Make sure you have installed:

Python 3.11+

Node.js

npm

A Groq API key

Backend Setup

Open a terminal:

cd backend

Create a virtual environment:

python -m venv venv

Activate it on Windows:

.\venv\Scripts\Activate.ps1

Install dependencies:

pip install fastapi uvicorn python-dotenv openai pypdf python-docx chromadb sentence-transformers python-multipart

Create a .env file inside backend/:

GROQ_API_KEY=your_groq_api_key_here

Start the backend:

uvicorn main:app --reload

The API will run at:

http://127.0.0.1:8000

Health check:

http://127.0.0.1:8000/health

Frontend Setup

Open another terminal:

cd frontend

Install dependencies:

npm install

Start the frontend:

npm run dev

The frontend will normally run at:

http://localhost:5173

How to Use

Option 1 — Enter a Process

Open the application.

Enter the current business process in the text area.

Click Analyse Process.

Review the generated analysis.

Option 2 — Upload a Process Document

Select a PDF, DOCX, or TXT file.

Click Upload Document.

The backend extracts the document text.

The text is divided into chunks.

Embeddings are generated.

Chunks are stored in ChromaDB.

The application displays the number of indexed chunks.

Click Analyse Process.

Relevant document context is retrieved and supplied to the LLM.

API Endpoints

GET /

Checks that the API is running.

GET /health

Returns backend health status.

POST /upload-document

Uploads and processes a PDF, DOCX, or TXT document.

Example response:

{
  "message": "Document processed successfully.",
  "filename": "data_annotation_process.pdf",
  "characters_extracted": 493,
  "chunks_added": 1,
  "text_preview": "..."
}

POST /analyse

Analyzes the supplied business process using the LLM and relevant RAG context.

GET /documents

Returns uploaded files stored in the knowledge base directory.

GET /rag-status

Returns the current RAG knowledge-base status and indexed chunk count.

Example Use Case

A data annotation quality-control process can be entered as:

1. Annotators receive video datasets.
2. Annotators manually label human actions and object interactions.
3. Annotators perform temporal and spatial annotations.
4. Quality reviewers check annotations for errors.
5. Errors are documented.
6. Corrected annotations are submitted for model training.
7. The final dataset is validated.

The application can identify:

Manual annotation as a bottleneck

AI-assisted annotation opportunities

Automated quality-control checks

Human review and final validation responsibilities

A future human-AI workflow

Risks and implementation considerations

RAG Design

The RAG pipeline uses local embeddings generated by:

sentence-transformers/all-MiniLM-L6-v2

Documents are split into chunks using overlapping text windows.

The chunks are stored in a persistent ChromaDB collection:

process_documents

When analysis is requested:

User Process
     ↓
Embedding
     ↓
ChromaDB Similarity Search
     ↓
Top Relevant Chunks
     ↓
Prompt Context
     ↓
Groq / Llama 3.3
     ↓
Structured JSON Analysis

Important Notes

The chroma_db/ directory contains the persistent vector database.

The knowledge_base/ directory contains uploaded documents and extracted text.

Do not commit API keys to Git.

Add .env, virtual environments, node_modules, and generated databases to .gitignore if they should remain local.

Future Improvements

Potential future enhancements include:

Process workflow visualization

Confidence scores for AI recommendations

Side-by-side current vs future process comparison

More advanced document retrieval and reranking

Document deletion and knowledge-base management

Authentication and enterprise access control

Audit logs for AI recommendations

Evaluation datasets for measuring analysis quality

Human feedback loops for improving recommendations

Exporting redesigned processes as PDF or DOCX

Purpose

The project demonstrates how generative AI, RAG, document processing, and human-in-the-loop design can be combined to transform existing enterprise workflows into practical future-state processes.