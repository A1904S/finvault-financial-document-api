from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Document
from app.schemas.schemas import IndexResponse, SemanticSearchRequest, SemanticSearchResponse, SearchResultChunk, DocumentContextResponse
from app.core.security import get_current_user_id
from app.services import rag_service

router = APIRouter(prefix="/rag", tags=["rag"])

@router.post("/index-document", response_model=IndexResponse)
def index_doc(document_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    if doc.is_indexed == "yes":
        return IndexResponse(document_id=document_id, status="already indexed", chunks_indexed=0)
    try:
        count = rag_service.index_document(document_id=doc.id, file_path=doc.file_path, title=doc.title)
        doc.is_indexed = "yes"
        db.commit()
        return IndexResponse(document_id=document_id, status="success", chunks_indexed=count)
    except Exception as e:
        doc.is_indexed = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/remove-document/{document_id}")
def remove_embeddings(document_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    rag_service.remove_document_embeddings(document_id)
    doc.is_indexed = "no"
    db.commit()
    return {"msg": "embeddings removed"}

@router.post("/search", response_model=SemanticSearchResponse)
def search(request: SemanticSearchRequest, user_id: int = Depends(get_current_user_id)):
    try:
        results = rag_service.semantic_search(query=request.query, top_k=request.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return SemanticSearchResponse(
        query=request.query,
        results=[SearchResultChunk(**r) for r in results]
    )

@router.get("/context/{document_id}", response_model=DocumentContextResponse)
def get_context(document_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    if doc.is_indexed != "yes":
        raise HTTPException(status_code=400, detail="please index this document first")
    chunks = rag_service.get_document_context(document_id)
    return DocumentContextResponse(document_id=document_id, document_title=doc.title, chunks=chunks)
