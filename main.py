"""
Certificate OCR System - Application Entry Point
Teerop Pvt. Limited - AI & ML Internship Program

This is the main entry point of the application. It creates the FastAPI
app, mounts static files, wires up templates, and includes all API routes.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.api.routes import router as api_router
from app.models.database import init_db

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Certificate OCR System",
    description="Tesseract OCR-Based Document Processing System that "
                 "automatically extracts and structures information from "
                 "certificates and official documents.",
    version="1.0.0",
)

# Allow the frontend (served from the same app) to call the API freely.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (CSS / JS / images) and HTML templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# All /api endpoints live in app/api/routes.py
app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    """Create the SQLite database & tables the first time the app runs."""
    init_db()


# @app.get("/", response_class=HTMLResponse, tags=["Frontend"])
# async def home(request: Request):
#     """Serves the main upload page (Single Page Application)."""
#     return templates.TemplateResponse("index.html", {"request": request})

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def home(request: Request):
    """Serves the main upload page (Single Page Application)."""
    return templates.TemplateResponse(request, "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
