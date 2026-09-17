from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import get_db
from .config import settings

def current_user(authorization: str|None=Header(default=None), db:Session=Depends(get_db)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401,'Authentication required')
    try:
        payload=jwt.decode(authorization[7:], settings.jwt_secret, algorithms=['HS256'])
        uid=int(payload['sub'])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(401,'Invalid or expired token')
    user=db.execute(text('SELECT id,name,email,role,branch_id FROM users WHERE id=:id'),{'id':uid}).mappings().first()
    if not user: raise HTTPException(401,'User not found')
    return dict(user)

def require_roles(*roles):
    def dep(user=Depends(current_user)):
        if user['role'] not in roles: raise HTTPException(403,'Insufficient permissions')
        return user
    return dep
