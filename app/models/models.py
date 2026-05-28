from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum
from app.db.database import Base

class DocumentType(str, enum.Enum):
    invoice = "invoice"
    report = "report"
    contract = "contract"

class RoleType(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    auditor = "auditor"
    client = "client"

# users table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    company_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="uploader")
    user_roles = relationship("UserRole", back_populates="user")

# roles table
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(RoleType), unique=True)
    description = Column(String, nullable=True)
    permissions = Column(Text, default="")

    user_roles = relationship("UserRole", back_populates="role")

# this table connects users and roles
class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))
    assigned_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

# documents table
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    company_name = Column(String, nullable=True)
    document_type = Column(Enum(DocumentType))
    file_path = Column(String)
    file_name = Column(String)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_indexed = Column(String, default="no")

    uploader = relationship("User", back_populates="documents")
