from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse

from . import env
from .routes import kdcapital

app = FastAPI()


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.password != env.api_token:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": env.api_token, "token_type": "bearer"}


app.include_router(
    kdcapital.router,
    prefix="/api/kdcapital",
    tags=["api"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)
