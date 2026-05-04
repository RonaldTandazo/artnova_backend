import json
from app.config.logger import logger
from fastapi import FastAPI, Depends, Request
from strawberry.fastapi import GraphQLRouter
from app.graphql.GraphSchema import GraphSchema 
from app.db.database import get_db, get_mongo_db
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.db.redis import connect_to_redis, close_redis_connection
from app.config.settings import URL_FRONTEND
import mimetypes

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await connect_to_redis()

@app.on_event("shutdown")
async def shutdown_event():
    await close_redis_connection()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mimetypes.add_type('model/gltf+json', '.gltf')
mimetypes.add_type('model/gltf-binary', '.glb')

app.mount("/avatars", StaticFiles(directory="app/public/users/avatars"))
app.mount("/covers", StaticFiles(directory="app/public/users/covers"))
app.mount("/thumbnails", StaticFiles(directory="app/public/artworks/thumbnails"))
app.mount("/images", StaticFiles(directory="app/public/artworks/multimedia/images"))
app.mount("/videos", StaticFiles(directory="app/public/artworks/multimedia/videos"))
app.mount("/models", StaticFiles(directory="app/public/artworks/models"))

# GRAPHQL
async def get_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    body = None

    if request.method == "POST":
        if "application/json" in request.headers.get("Content-Type", ""):
            try:
                body = await request.json()  
            except json.JSONDecodeError:
                pass
    
    return {"db": db, "mongo_db": mongo_db, "request": request, "body": body}

graphql_app = GraphQLRouter(schema=GraphSchema, context_getter=get_context, subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL], multipart_uploads_enabled=True)
app.include_router(graphql_app, prefix="/graphql", tags=["graphql"])

graphql_ws_router = GraphQLRouter(schema=GraphSchema, subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL])
app.include_router(graphql_ws_router, prefix="/graphql/ws", tags=["graphql_ws"])
