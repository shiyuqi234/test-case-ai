"""FastAPI web UI for test-case-ai."""

from __future__ import annotations

import pathlib

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .generator import generate, generate_from_openapi

TEMPLATE_DIR = pathlib.Path(__file__).parent / "templates"

app = FastAPI(
    title="Test Case AI",
    description="AI-powered test case generator web UI",
    version="0.1.0",
)


class GenerateRequest(BaseModel):
    """Request body for /api/generate."""

    input_type: str = "desc"  # "desc" or "openapi"
    description: str = ""
    openapi_url: str = ""
    provider: str = "anthropic"
    api_key: str = ""
    model: str = ""
    base_url: str = ""


@app.get("/")
async def index():
    """Serve the web UI."""
    html_path = TEMPLATE_DIR / "index.html"
    if not html_path.exists():
        return JSONResponse({"error": "UI template not found"}, status_code=404)
    return FileResponse(html_path)


@app.post("/api/generate")
async def api_generate(req: GenerateRequest):
    """Generate test cases from a description or OpenAPI spec.

    Returns:
        JSON with success flag and either yaml content or error message.
    """
    try:
        if req.input_type == "openapi":
            from .openapi_parser import fetch_spec, get_base_url, parse_endpoints

            spec = fetch_spec(req.openapi_url)
            resolved_base = req.base_url or get_base_url(spec)
            endpoints = parse_endpoints(spec)
            yaml_result = generate_from_openapi(
                endpoints,
                base_url=resolved_base,
                api_key=req.api_key,
                model=req.model,
                provider=req.provider,
            )
        else:
            yaml_result = generate(
                req.description,
                base_url=req.base_url,
                api_key=req.api_key,
                model=req.model,
                provider=req.provider,
            )

        return JSONResponse({
            "success": True,
            "yaml": yaml_result,
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
        })
