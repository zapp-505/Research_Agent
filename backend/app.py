from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.Research_Agent.graph.graph_builder import GraphBuilder
from src.db.mongo_client import MongoDB
from src.routers.auth import router as auth_router
from src.routers.chat import router as chat_router
from src.routers.history import router as history_router
from src.routers.index import router as index_router

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
async def startup():
    await MongoDB.connect()
    builder = GraphBuilder()
    app.state.agent = builder.build()

@app.on_event("shutdown")
async def shutdown():
    await MongoDB.close()


app.include_router(index_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(history_router)
