from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.schemas import UserCreate, UserLogin, UserOut
from app.db.models import hash_password, verify_password
from app.db.database import db
from bson import ObjectId

auth_router = APIRouter()
security = HTTPBearer()


# ───────────────────────────────
# 🔐 JWT Token Creation
# ───────────────────────────────
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ───────────────────────────────
# 👤 Signup Endpoint
# ───────────────────────────────
@auth_router.post("/signup", response_model=UserOut)
async def signup(user: UserCreate):
    user_exists = await db.users.find_one({"email": user.email})
    if user_exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = {
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "passwordHash": hash_password(user.password),
        "role": "client",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }

    result = await db.users.insert_one(new_user)
    user_out = {
        "id": str(result.inserted_id),
        "name": user.name,
        "email": user.email,
        "role": "client"
    }
    return user_out


# ───────────────────────────────
# 🔑 Login Endpoint
# ───────────────────────────────
@auth_router.post("/login")
async def login(user: UserLogin):
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["passwordHash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {
        "id": str(db_user["_id"]),
        "name": db_user["name"],
        "email": db_user["email"],
        "role": db_user["role"]
    }

    token = create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}


# ───────────────────────────────
# 🔒 Auth Middleware (get current user)
# ───────────────────────────────
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload  # Contains: id, name, email, role
    except JWTError:
        raise HTTPException(status_code=403, detail="Token is invalid or expired")

