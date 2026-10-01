"""
Main FastAPI Application for Data Matching Engine.
"""
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.web.routes import router as api_router
from app.utils.sample_generator import generate_sample_files

# Ensure sample files exist
generate_sample_files()

app = FastAPI(
    title="Data Matching Engine & Entity Resolution",
    description="Intelligent Data Matching Engine with Multi-algorithm scoring and explainability.",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "web", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = os.path.join(os.path.dirname(__file__), "web", "templates")
templates = Jinja2Templates(directory=templates_dir)

# Include API Router
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Serve main interactive dashboard."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
