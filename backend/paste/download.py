from fastapi.responses import StreamingResponse
from io import BytesIO
from ._types import Reply
# from typing import overload
from utils import error_400, error_404, MyAPI
from zipfile import ZipFile, ZIP_DEFLATED

async def download_paste_by_id(app: MyAPI, paste_id: str, filepos: int = 0) -> StreamingResponse | Reply:
    if filepos < 0:
        return error_400("'filepos' cannot be less than zero.")
    
    # User wants to download a single file
    if filepos:
        async with app.pool.acquire() as conn:
            req = await conn.execute(
                """
                SELECT filename, content FROM files
                WHERE id = ? AND position = ?
                """,
                paste_id, filepos
            )
            
            row = await req.fetchone()
        
        if not row:
            return error_404(f"No file at index {filepos} for paste {paste_id} found.")
    
        return StreamingResponse(
            content = BytesIO(row["content"].encode()),
            media_type = "text",
            headers = {
                "Content-Disposition": f"inline; filename={row['filename'] or paste_id}"
            }
        )

    # ================================================================================================

    # User wants to download all files
    async with app.pool.acquire() as conn:
        req = await conn.execute("SELECT filename, content, position FROM files WHERE id = ?", paste_id)
        rows = await req.fetchall()
    
    if not rows:
        return error_404(f"No files were found with the paste ID '{paste_id}'.")

    with BytesIO() as buffer:
        with ZipFile(buffer, "a", ZIP_DEFLATED, False) as myzip:
            for row in rows:
                filename = f"{paste_id}-{row["filename"] or row["position"]}"

                with myzip.open(filename, "w") as file:
                    file.write(row["content"])
    
        return StreamingResponse(
            content = buffer,
            media_type = "text",
            headers = {
                "Content-Disposition": f"inline; filename={paste_id}.zip"
            }
        )