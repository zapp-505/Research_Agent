import uuid
from src.db.mongo_client import MongoDB
from src.logging.logger import logger

COLLECTION = "users"

async def get_user_by_email(email: str) -> dict | None:
    col = MongoDB.db[COLLECTION]
    return await col.find_one({"email": email})

async def create_user(email: str, hashed_password: str) -> dict:
    col = MongoDB.db[COLLECTION]
    user_id = str(uuid.uuid4())
    user_doc = {
        "_id": user_id,
        "uid": user_id,
        "email": email,
        "hashed_password": hashed_password
    }
    await col.insert_one(user_doc)
    logger.info(f"Created new user: {email}")
    return user_doc
