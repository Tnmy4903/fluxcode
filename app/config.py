import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET = os.getenv("JWT_SECRET")

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
SUPPORTED_JWT_ALGORITHMS = {"HS256"}

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440)
    )
except ValueError:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES must be an integer."
    )

DB_NAME = os.getenv("DB_NAME", "company_db")

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")

# Validate required environment variables
if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI environment variable is missing."
    )

if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET environment variable is missing."
    )

# Validate JWT algorithm
if JWT_ALGORITHM not in SUPPORTED_JWT_ALGORITHMS:
    raise RuntimeError(
        f"Unsupported JWT algorithm: {JWT_ALGORITHM}"
    )