import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes_stream import router as stream_router
from .routes_events import router as events_router

app = FastAPI(
    title="BorderVision API",
    version="2.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream_router)
app.include_router(events_router)


@app.get("/api/v2/health")
async def health():
    return {"status": "ok"}
