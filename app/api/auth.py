from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from app.config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.schemas import LoginResponse, UserCreate, UserLogin, UserOut,AdminCreate, PromoteRequest
from app.exceptions import AuthenticationException, exception_to_http
from app.services.service_layer import AuthService
from app.logger import logger_auth

auth_router = APIRouter()
security = HTTPBearer(auto_error=False)
auth_service = AuthService()


# ───────────────────────────────
# 🔐 JWT Token Creation
# ───────────────────────────────
def create_access_token(data: dict):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({
        "sub": data["id"],        # JWT Standard
        "type": "access",         # Future refresh token support
        "exp": expire,
        "iat": now
    })
    return jwt.encode(
        to_encode,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

# ───────────────────────────────
# 👤 Signup Endpoint (Clients Only)
# ───────────────────────────────
@auth_router.post("/signup", response_model=UserOut)
async def signup(user: UserCreate):
    try:
        return await auth_service.register_client(
            name=user.name,
            email=user.email,
            phone=user.phone,
            password=user.password
        )
    except Exception as exc:
        raise exception_to_http(exc)


# ───────────────────────────────
# 🔑 Login Endpoint
# ───────────────────────────────
@auth_router.post("/login", response_model=LoginResponse)
async def login(user: UserLogin):
    try:
        token_data = await auth_service.verify_credentials(user.email, user.password)
        token = create_access_token(token_data)
        logger_auth.info(
            f"Successful login for role {token_data['role']}"
        )
        return {"access_token": token, "token_type": "bearer", "user": token_data}
    except Exception as exc:
        raise exception_to_http(exc)


# ───────────────────────────────
# 🔒 Auth Middleware (get current user)
# ───────────────────────────────
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None:
        raise exception_to_http(
            AuthenticationException(
                "Authentication credentials were not provided."
            )
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")

        if not user_id:
            raise AuthenticationException("Invalid token")

        if payload.get("type") != "access":
            raise AuthenticationException(
                "Invalid token type."
            )
        
        return {
            "id": user_id,
            "email": payload["email"],
            "name": payload["name"],
            "role": payload["role"]
        } # Contains: id, name, email, role
    
    except JWTError as e:
        logger_auth.error(f"JWT validation failed: {str(e)}")
        raise exception_to_http(AuthenticationException("Token is invalid or expired"))
    
# ───────────────────────────────
# 👤 Current Logged In User
# ───────────────────────────────
@auth_router.get("/me", response_model=UserOut)
async def get_me(
    current_user: dict = Depends(get_current_user)
):
    try:
        return await auth_service.get_current_user_profile(
            current_user["id"]
        )

    except Exception as exc:
        raise exception_to_http(exc)

# ───────────────────────────────
# 👨‍💼 Create Sub-Admin (Super Admin Only)
# ───────────────────────────────

@auth_router.post("/create-sub-admin", response_model=UserOut)
async def create_sub_admin(
    admin_data: AdminCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        if current_user.get("role") != "super_admin":
            raise AuthenticationException("Only Super Admin can create Sub-Admins")
        
        return await auth_service.create_sub_admin(admin_data.email, admin_data.name)
    except Exception as exc:
        raise exception_to_http(exc)

# ───────────────────────────────
# 🔄 Promote Client to Sub-Admin (Super Admin Only)
# ───────────────────────────────

@auth_router.post("/promote-to-sub-admin", response_model=UserOut)
async def promote_to_sub_admin(
    request: PromoteRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        if current_user.get("role") != "super_admin":
            raise AuthenticationException("Only Super Admin can promote users")
        
        return await auth_service.promote_to_sub_admin(request.user_id)
    except Exception as exc:
        raise exception_to_http(exc)

