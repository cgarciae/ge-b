from fastapi import Depends, FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from . import params
from .routes import scraper

app = FastAPI()


@app.middleware("http")
async def get_authorization(request: Request, call_next):

    if not (
        request.url.path.startswith("/docs")
        or request.url.path.startswith("/openapi.json")
        or request.url.path == "/api/pipeline"
    ):
        authorization = request.headers.get("authorization", "")
        token = authorization.replace("Bearer", "").strip()

        if token != params.api_token:
            return JSONResponse(status_code=401, content=dict(message="Unauthorized"))

    return await call_next(request)


@app.middleware("http")
async def add_download_headers(request: Request, call_next):

    resp = await call_next(request)

    if request.url.path.startswith("/static/xmps"):
        filename = request.url.path.split("/")[-1]
        resp.headers["Content-Disposition"] = f"attachment; filename={filename}"

    return resp


app.include_router(
    scraper.router,
    prefix="/api",
    tags=["api"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)
