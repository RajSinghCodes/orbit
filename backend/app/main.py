import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine, SessionLocal
from app.data.seed_data import seed_database

# Import routers
from app.api.dashboard import router as dashboard_router
from app.api.supply_chain import router as supply_chain_router
from app.api.incidents import router as incidents_router
from app.api.scenarios import router as scenarios_router
from app.api.workflows import router as workflows_router
from app.api.improvement import router as improvement_router
from app.api.observability import router as observability_router

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("orbit")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema
    logger.info("Initializing ORBIT database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Seed synthetic business dataset
    db = SessionLocal()
    try:
        logger.info("Verifying synthetic supply chain seed data...")
        seed_database(db)
    finally:
        db.close()
    
    yield
    logger.info("Shutting down ORBIT operations intelligence platform...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Autonomous Multi-Agent Business Operations Intelligence Platform for Supply Chain Resiliency",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api
app.include_router(dashboard_router, prefix="/api")
app.include_router(supply_chain_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")
app.include_router(scenarios_router, prefix="/api")
app.include_router(workflows_router, prefix="/api")
app.include_router(improvement_router, prefix="/api")
app.include_router(observability_router, prefix="/api")

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "platform": "ORBIT Autonomous Business Operations Intelligence",
        "version": "1.0.0",
        "llm_mode": settings.LLM_PROVIDER,
        "database": settings.DATABASE_URL.split("://")[0]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
