# Financial Document Management API

This is my assignment project for Nimap Infotech. I built a REST API using FastAPI that lets users upload and search financial documents using AI.

## What I built

- User registration and login using JWT tokens
- Upload financial documents (PDF, TXT)
- Role based access control (admin, analyst, auditor, client)
- AI powered search using vector embeddings (RAG)

## Tech Stack

- **FastAPI** - for building the API
- **PostgreSQL** - to store users and document info
- **Qdrant** - vector database for storing embeddings
- **sentence-transformers** - for generating text embeddings
- **Docker** - to run postgres and qdrant locally

## How to run

First start the databases using docker:
```
docker-compose up -d
```

Then install python packages:
```
pip install -r requirements.txt
```

Run the server:
```
uvicorn app.main:app --reload
```

Open browser and go to http://localhost:8000/docs to test all APIs.

## API Endpoints

**Auth**
- POST /auth/register - create new account
- POST /auth/login - login and get token

**Documents**
- POST /documents/upload - upload a pdf
- GET /documents - get all documents
- GET /documents/{id} - get one document
- DELETE /documents/{id} - delete document
- GET /documents/search - search by title or company

**Roles**
- POST /roles/create - create a role
- POST /users/assign-role - give role to user
- GET /users/{id}/roles - see user roles
- GET /users/{id}/permissions - see user permissions

**RAG Search**
- POST /rag/index-document - process document for AI search
- POST /rag/search - search using natural language
- GET /rag/context/{id} - get all chunks of a document
- DELETE /rag/remove-document/{id} - remove from vector db

## How AI search works

When a document is uploaded and indexed:
1. Text is extracted from the PDF
2. Text is split into small chunks (500 chars each)
3. Each chunk is converted to a vector using sentence-transformers model
4. Vectors are stored in Qdrant

When user searches:
1. Query is converted to vector
2. Qdrant finds 20 most similar chunks
3. A reranker model picks the best 5 results

## Problems I faced

- bcrypt was giving version error so I switched to hashlib for password hashing
- Had merge conflict on github, fixed it using force push
- Qdrant collection needs to be created before searching, added auto-create logic

## Note

All APIs are tested using Swagger UI at /docs
