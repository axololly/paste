from asqlite import create_pool
from paste.create import create_new_paste
from paste.delete import delete_paste_by_link
from paste.download import download_paste_by_id
from paste.get import get_paste_by_id, get_raw_paste_by_id
from paste._types import CreateSuccess, GetSuccess, Reply
from paste.update import update_existing_paste
from utils import BackgroundLoops, MyAPI

from sanic_limiter import Limiter, get_remote_address # type: ignore
from sanic.response import HTTPResponse
from sanic.request import Request

app = MyAPI("pastolotl-backend")
limiter = Limiter(app, key_func = get_remote_address)

@app.before_server_start
async def before_start(app: MyAPI) -> None:
    app.ctx.pool = await create_pool("../entries/index.sql")
    
    app.ctx.loops = BackgroundLoops(app)
    app.ctx.loops.start()

@app.after_server_stop
async def after_end(app: MyAPI) -> None:
    await app.ctx.pool.close()
    
    app.ctx.loops.end()

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
async def app_download_paste_by_id(request: Request, paste_id: str) -> HTTPResponse | Reply:
    return await download_paste_by_id(app, request, paste_id)

@app.get("/download/{paste_id}/{filepos}")
@limiter.limit("2/minute") # type: ignore
async def app_download_single_paste_by_id(request: Request, paste_id: str, filepos: int) -> HTTPResponse | Reply:
    return await download_paste_by_id(app, request, paste_id, filepos)


if __name__ == '__main__':
    from os import chdir as run_from
    from subprocess import run

    run_from("./backend")
    run("sanic main:app --debug".split(' '))