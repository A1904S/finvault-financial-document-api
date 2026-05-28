from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.models.models import DocumentType, RoleType

# auth
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    company_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    company_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# roles
class RoleCreate(BaseModel):
    name: RoleType
    description: Optional[str] = None
    permissions: Optional[str] = ""

class RoleResponse(BaseModel):
    id: int
    name: RoleType
    description: Optional[str]
    permissions: str

    class Config:
        from_attributes = True

class AssignRoleRequest(BaseModel):
    user_id: int
    role_name: RoleType

# documents
class DocumentResponse(BaseModel):
    id: int
    title: str
    company_name: Optional[str]
    document_type: DocumentType
    file_name: str
    uploaded_by: int
    created_at: datetime
    is_indexed: str

    class Config:
        from_attributes = True

# rag search
class IndexResponse(BaseModel):
    document_id: int
    status: str
    chunks_indexed: int

class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResultChunk(BaseModel):
    document_id: int
    document_title: str
    chunk_text: str
    score: float

class SemanticSearchResponse(BaseModel):
    query: str
    results: List[SearchResultChunk]

class DocumentContextResponse(BaseModel):
    document_id: int
    document_title: str
    chunks: List[str]
