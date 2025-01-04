from asqlite import create_pool
from contextlib import asynccontextmanager
from fastapi import Request
from fastapi.responses import StreamingResponse
from paste.create import create_new_paste
from paste.delete import delete_paste_by_link
from paste.download import download_paste_by_id
from paste.get import get_paste_by_id, get_raw_paste_by_id
from paste._types import CreateSuccess, GetSuccess, Reply
from paste.update import update_existing_paste
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
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore


@app.post("/create/")
@limiter.limit("6/minute") # type: ignore # 10s per request
async def app_create_new_paste(request: Request) -> CreateSuccess | Reply:
    return await create_new_paste(app, request)


@app.get("/get/{paste_id}")
@limiter.limit("20/minute") # type: ignore # 3s per request
async def app_get_paste_by_id(request: Request, paste_id: str) -> GetSuccess | Reply:
    return await get_paste_by_id(app, paste_id)

@app.get("/get/raw/{paste_id}")
@limiter.limit("20/minute") # type: ignore # 3s per request
async def app_get_raw_paste_by_id(request: Request, paste_id: str) -> str:
    return await get_raw_paste_by_id(app, paste_id)

@app.get("/get/raw/{paste_id}/{filepos}")
@limiter.limit("20/minute") # type: ignore # 3s per request
async def app_get_raw_file_by_id(request: Request, paste_id: str, filepos: int) -> str:
    return await get_raw_paste_by_id(app, paste_id, filepos)


@app.delete("/delete/{removal_id}")
@limiter.limit("10/minute")  # type: ignore # 6s per request
async def app_delete_paste_by_link(request: Request, removal_id: str) -> Reply:
    return await delete_paste_by_link(app, removal_id)


@app.put("/update/")
@limiter.limit("3/minute") # type: ignore
async def app_update_existing_paste(request: Request) -> Reply:
    return await update_existing_paste(app, request)


@app.get("/download/{paste_id}")
@limiter.limit("2/minute") # type: ignore
async def app_download_paste_by_id(request: Request, paste_id: str) -> StreamingResponse | Reply:
    return await download_paste_by_id(app, paste_id)

@app.get("/download/{paste_id}/{filepos}")
@limiter.limit("2/minute") # type: ignore
async def app_download_single_paste_by_id(request: Request, paste_id: str, filepos: int) -> StreamingResponse | Reply:
    return await download_paste_by_id(app, paste_id, filepos)

if __name__ == '__main__':
    import uvicorn
    
    uvicorn.run("main:app")