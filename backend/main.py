from __future__ import annotations
from asqlite import create_pool
from contextlib import asynccontextmanager
from fastapi import Request
from paste.create import _create_new_paste
from paste.delete import _delete_paste_by_link
from paste.get import _get_paste_by_id, _get_raw_paste_by_id
from paste.update import _update_existing_paste
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from utils import BackgroundLoops, MyAPI

limiter = Limiter(key_func = get_remote_address)

@asynccontextmanager
async def lifespan(app: MyAPI):
    async with create_pool("entries/index.sql") as pool:
        app.pool = pool
        app.loops = BackgroundLoops(app)
        app.loops.start()
        
        yield

app = MyAPI(lifespan = lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.post("/create/")
@limiter.limit("6/minute") # 10s per request
async def create_new_paste(request: Request) -> dict[str, int | str]:
    return await _create_new_paste(app, request)


@app.get("/get/{paste_id}")
@limiter.limit("20/minute") # 3s per request
async def get_paste_by_id(request: Request, paste_id: str): # Return type was too complicated to figure out
    return await _get_paste_by_id(app, paste_id)

@app.get("/get/raw/{paste_id}")
@limiter.limit("20/minute") # 3s per request
async def get_raw_paste_by_id(request: Request, paste_id: str):
    return await _get_raw_paste_by_id(app, paste_id)

@app.get("/get/raw/{paste_id}/{filepos}")
@limiter.limit("20/minute") # 3s per request
async def get_raw_file_by_id(request: Request, paste_id: str, filepos: int):
    return await _get_raw_paste_by_id(app, paste_id, filepos)


@app.delete("/delete/{removal_id}")
@limiter.limit("10/minute") # 6s per request
async def delete_paste_by_link(request: Request, removal_id: str) -> dict[str, int | str]:
    return await _delete_paste_by_link(app, removal_id)


@app.put("/update/")
@limiter.limit("3/minute")
async def update_existing_paste(request: Request) -> dict[str, int | str]:
    return await _update_existing_paste(app, request)


if __name__ == '__main__':
    import uvicorn
    
    uvicorn.run("main:app")