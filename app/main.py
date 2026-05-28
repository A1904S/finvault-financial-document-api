from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
from app.models import models
from app.api.endpoints import auth, documents, roles, rag

Base.metadata.create_all(bind=engine)

# main app
app = FastAPI(title="Financial Doc API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(roles.router)
app.include_router(rag.router)

@app.get("/")
def root():
    return {"msg": "api is running", "docs": "/docs"}
