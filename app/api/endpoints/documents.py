import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Document, DocumentType, UserRole, Role, RoleType
from app.schemas.schemas import DocumentResponse
from app.core.config import settings
from app.core.security import get_current_user_id

router = APIRouter(prefix="/documents", tags=["documents"])

# check user permission
def user_has_permission(user_id: int, perm: str, db: Session) -> bool:
    roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    for r in roles:
        role = db.query(Role).filter(Role.id == r.role_id).first()
        if role and perm in role.permissions.split(","):
            return True
    return False

@router.post("/upload", response_model=DocumentResponse, status_code=201)
def upload_doc(
    title: str = Form(...),
    company_name: str = Form(None),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    if not user_has_permission(user_id, "upload", db):
        raise HTTPException(status_code=403, detail="you dont have permission to upload")

    # only allow pdf and txt files
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".txt"]:
        raise HTTPException(status_code=400, detail="only pdf and txt allowed")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    save_name = f"{user_id}_{file.filename}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_name)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(
        title=title,
        company_name=company_name,
        document_type=document_type,
        file_path=save_path,
        file_name=file.filename,
        uploaded_by=user_id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

@router.get("", response_model=List[DocumentResponse])
def get_all_docs(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # client can only see their company docs
    roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    role_names = []
    for r in roles:
        role = db.query(Role).filter(Role.id == r.role_id).first()
        if role:
            role_names.append(role.name)

    if RoleType.client in role_names and RoleType.admin not in role_names:
        from app.models.models import User
        me = db.query(User).filter(User.id == user_id).first()
        return db.query(Document).filter(Document.company_name == me.company_name).all()

    return db.query(Document).all()

@router.get("/search", response_model=List[DocumentResponse])
def search_docs(
    title: Optional[str] = Query(None),
    company_name: Optional[str] = Query(None),
    document_type: Optional[DocumentType] = Query(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    q = db.query(Document)
    if title:
        q = q.filter(Document.title.ilike(f"%{title}%"))
    if company_name:
        q = q.filter(Document.company_name.ilike(f"%{company_name}%"))
    if document_type:
        q = q.filter(Document.document_type == document_type)
    return q.all()

@router.get("/{document_id}", response_model=DocumentResponse)
def get_doc(document_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    return doc

@router.delete("/{document_id}")
def delete_doc(document_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    if not user_has_permission(user_id, "delete", db):
        raise HTTPException(status_code=403, detail="you dont have permission to delete")
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
    return {"msg": "document deleted"}
