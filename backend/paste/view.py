from fastapi import Request
from json import JSONDecodeError
import shortuuid
from utils import error_400, http_reply, MyAPI, success
from zlib import decompress

async def _get_paste_by_id(app: MyAPI, request: Request):
    try:
        data: dict = await request.json()
    except JSONDecodeError:
        return error_400("No JSON was given.")
    
    if "id" not in data:
        return error_400("'id' key is missing from JSON.")

    if not isinstance(data["id"], str):
        return error_400("'id' key is not a string.")

    async with app.pool.acquire() as conn:
        req = await conn.execute(
            "SELECT filename, content FROM files WHERE id = ?",
            data["id"]
        )
        rows = await req.fetchall()
    
    if not rows:
        return http_reply(404, f"No paste was found with the ID '{ascii(data["id"])}'.")

    return success | {
        "files": [
            [row["filename"], decompress(row["content"]).decode()]
            for row in rows
        ]
    }