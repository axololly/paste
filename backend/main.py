from __future__ import annotations
import asyncio
from asqlite import create_pool
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from .paste.create import _create_new_paste
from .paste.delete import delete_in_background
from .paste.view import _get_paste_by_id
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func = get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_pool("entries/index.sql") as pool:
        yield {"pool": pool}

app = FastAPI(lifespan = lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ID_LENGTH = 4

@app.post("/create/")
@limiter.limit("6/minute") # 10s per request
async def create_new_paste(request: Request) -> dict[str, int | str]:
    return await _create_new_paste(app, request)

@app.get("/get/")
@limiter.limit("20/minute") # 3s per request
async def get_paste_by_id(request: Request): # Return type was too complicated to figure out
    return await _get_paste_by_id(app, request)

if __name__ == '__main__':
    import uvicorn
    
    uvicorn.run("backend.main:app")