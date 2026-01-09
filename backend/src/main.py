from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn

from src.utils.logging import setup_logging
from src.api.routers import health, auth
from src.api.middleware.error_handler import error_handler
from src.config import settings
from src.exceptions import MyFinGPTException
from fastapi.exceptions import RequestValidationError

# Setup logging first
setup_logging()

app = FastAPI(
    title="MyFinGPT-POC-V2",
    version="0.1.0",
    description="Production-grade multi-agent financial analysis system"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# Add exception handlers
app.add_exception_handler(MyFinGPTException, error_handler)
app.add_exception_handler(RequestValidationError, error_handler)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting MyFinGPT-POC-V2 backend")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down MyFinGPT-POC-V2 backend")


if __name__ == "__main__":
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

