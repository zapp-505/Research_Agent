from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver

from src.Research_Agent.graph.graph_builder import GraphBuilder
from src.db.mongo_client import MongoDB
from src.config import MONGODB_URI
from src.routers.auth import router as auth_router
from src.routers.chat import router as chat_router
from src.routers.history import router as history_router
from src.routers.index import router as index_router
from src.routers.sessions import router as sessions_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Async motor client for session store
    await MongoDB.connect()
    
    # Sync pymongo client for MongoDBSaver memory
    sync_client = MongoClient(MONGODB_URI)
    memory = MongoDBSaver(sync_client)
    
    builder = GraphBuilder(checkpointer=memory)
    app.state.agent = builder.build()
    app.state.sync_client = sync_client
    
    yield
    
    await MongoDB.close()
    app.state.sync_client.close()

app = FastAPI(lifespan=lifespan)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(index_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(history_router)
app.include_router(sessions_router)
