from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import Role, UserRole, User, RoleType
from app.schemas.schemas import RoleCreate, RoleResponse, AssignRoleRequest
from app.core.security import get_current_user_id

router = APIRouter(tags=["roles"])

# default permissions for each role
DEFAULT_PERMISSIONS = {
    RoleType.admin:   "upload,edit,delete,view,review,manage_roles",
    RoleType.analyst: "upload,edit,view",
    RoleType.auditor: "review,view",
    RoleType.client:  "view",
}

def check_if_admin(user_id: int, db: Session):
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    for ur in user_roles:
        role = db.query(Role).filter(Role.id == ur.role_id).first()
        if role and role.name == RoleType.admin:
            return True
    raise HTTPException(status_code=403, detail="only admin can do this")

@router.post("/roles/create", response_model=RoleResponse, status_code=201)
def create_role(data: RoleCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    check_if_admin(user_id, db)
    existing = db.query(Role).filter(Role.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="role already exists")
    perms = data.permissions or DEFAULT_PERMISSIONS.get(data.name, "view")
    role = Role(name=data.name, description=data.description, permissions=perms)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@router.post("/users/assign-role")
def assign_role(data: AssignRoleRequest, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    check_if_admin(user_id, db)
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    role = db.query(Role).filter(Role.name == data.role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail="role not found, create it first")
    already = db.query(UserRole).filter(UserRole.user_id == data.user_id, UserRole.role_id == role.id).first()
    if already:
        return {"msg": "role already assigned"}
    db.add(UserRole(user_id=data.user_id, role_id=role.id))
    db.commit()
    return {"msg": "role assigned successfully"}

@router.get("/users/{user_id}/roles", response_model=List[RoleResponse])
def get_roles(user_id: int, db: Session = Depends(get_db), current_user: int = Depends(get_current_user_id)):
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    result = []
    for ur in user_roles:
        role = db.query(Role).filter(Role.id == ur.role_id).first()
        if role:
            result.append(role)
    return result

@router.get("/users/{user_id}/permissions")
def get_permissions(user_id: int, db: Session = Depends(get_db), current_user: int = Depends(get_current_user_id)):
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    all_perms = set()
    for ur in user_roles:
        role = db.query(Role).filter(Role.id == ur.role_id).first()
        if role and role.permissions:
            for p in role.permissions.split(","):
                all_perms.add(p.strip())
    return {"user_id": user_id, "permissions": list(all_perms)}
