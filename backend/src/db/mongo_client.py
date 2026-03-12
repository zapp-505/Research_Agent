from motor.motor_asyncio import AsyncIOMotorClient
from src.config import MONGODB_URI
from src.logging.logger import logger


class MongoDB:
    """
    Singleton wrapper around the Motor async MongoDB client.

    Usage:
        await MongoDB.connect()   # called once at FastAPI startup
        db = MongoDB.db           # used everywhere else
        await MongoDB.close()     # called at FastAPI shutdown
    """
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect(cls):
        """Create the client and select the application database."""
        cls.client = AsyncIOMotorClient(MONGODB_URI)
        cls.db = cls.client["research_agent"]
        logger.info("MongoDB connected — database: research_agent")

    @classmethod
    async def close(cls):
        """Close the client connection gracefully."""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")


async def get_db():
    """
    FastAPI dependency — returns the shared database object.
    Inject with:  db = Depends(get_db)
    """
    return MongoDB.db