from datetime import datetime, timedelta, timezone
import hashlib, hmac, os
from jose import jwt
from .config import settings

ALGORITHM='HS256'

def hash_password(password: str) -> str:
    salt=os.urandom(16)
    digest=hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 210_000)
    return f'pbkdf2$210000${salt.hex()}${digest.hex()}'

def verify_password(password: str, encoded: str) -> bool:
    try:
        _, rounds, salt, digest=encoded.split('$')
        got=hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return hmac.compare_digest(got,digest)
    except Exception:
        return False

def create_token(user_id:int, role:str, expires_minutes:int=480):
    now=datetime.now(timezone.utc)
    return jwt.encode({'sub':str(user_id),'role':role,'iat':now,'exp':now+timedelta(minutes=expires_minutes)}, settings.jwt_secret, algorithm=ALGORITHM)
