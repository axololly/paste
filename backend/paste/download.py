from io import BytesIO
from sanic.exceptions import BadRequest, NotFound
from sanic.response import HTTPResponse
from sanic.response.convenience import raw
from sanic.request import Request
from typing import overload
from utils import MyAPI
from zipfile import ZipFile, ZIP_DEFLATED
from zlib import decompress

@overload
async def download_paste_by_id(app: MyAPI, request: Request, paste_id: str) -> HTTPResponse:
    "Download all files under the given `paste_id`."

@overload
async def download_paste_by_id(app: MyAPI, request: Request, paste_id: str, filepos: int) -> HTTPResponse:
    "Download a single file at position `filepos` under the given `paste_id`."

async def download_paste_by_id(app: MyAPI, request: Request, paste_id: str, filepos: int = 0) -> HTTPResponse:
    if filepos < 0:
        raise BadRequest("'filepos' cannot be less than zero.")
    
    # User wants to download a single file
    if filepos:
        async with app.ctx.pool.acquire() as conn:
            req = await conn.execute(
                """
                SELECT filename, content FROM files
                WHERE id = ? AND position = ?
                """,
                paste_id, filepos
            )
            
            row = await req.fetchone()
        
        if not row:
            raise NotFound(f"No file at index {filepos} for paste {paste_id} found.")

        return raw(
            decompress(row["content"]).decode(),
            content_type = 'file/txt'
        )

    # ================================================================================================

    # User wants to download all files
    async with app.ctx.pool.acquire() as conn:
        req = await conn.execute("SELECT filename, content, position FROM files WHERE id = ?", paste_id)
        rows = await req.fetchall()
    
    if not rows:
        raise NotFound(f"No files were found with the paste ID '{paste_id}'.")

    buffer = BytesIO()
    
    with ZipFile(buffer, "w", ZIP_DEFLATED, False) as myzip: # type: ignore
        for row in rows:
            filename = row["filename"] or f"{paste_id}-{row["position"]}"

            with myzip.open(filename, "w") as file:
                file.write(decompress(row["content"]))
    
    return raw(
        buffer.getvalue(),
        content_type = "file/zip"
    )