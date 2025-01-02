from fastapi import FastAPI, Request
from json import JSONDecodeError
from ..utils import error_400, http_reply, PasteCodes, success
from zlib import decompress

async def _get_paste_by_id(app: FastAPI, request: Request):
    try:
        data: dict = await request.json()
    except JSONDecodeError:
        return error_400("No JSON was given.")
    
    if "id" not in data:
        return error_400("'id' key is missing from JSON.")

    if not isinstance(data["id"], str):
        return error_400("'id' key is not a string.")
    
    id = PasteCodes.from_str(data["id"])

    if not id:
        return error_400(
            "'id' contains invalid characters. "
           f"Valid character set is: {ascii(PasteCodes.valid_chars)}"
        )

    async with app.pool.acquire() as conn:
        req = await conn.execute("SELECT filename, content FROM pastes WHERE id = ?", id)
        rows = await req.fetchall()
    
    if not rows:
        return http_reply(404, f"No entry was found by the ID '{id}'.")

    return success | {
        "files": [
            [row["filename"], decompress(row["content"]).decode()]
            for row in rows
        ]
    }