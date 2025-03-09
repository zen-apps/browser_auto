from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import sys
import os
import logging

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/var/log/app.log"),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting up FastAPI application...")
        yield
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down FastAPI application...")


app = FastAPI(
    title="Browser Automation API",
    description="API for browser automation tasks using Playwright and LangChain",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"message": "Browser Automation API is running"}


# Import routes after app creation to avoid circular imports
from app.api.browser import browser

app.include_router(
    browser,
    prefix="/v1/browser",
    tags=["browser"],
)
