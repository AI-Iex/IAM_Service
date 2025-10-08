from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__type="ID"   # Use Argon2id variant
)

# Function for password hashing
def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty.")
    return pwd_context.hash(password)

# Function for password verification (returns True if the password matches the hash)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        raise ValueError("Passwords cannot be empty.")
    return pwd_context.verify(plain_password, hashed_password)
