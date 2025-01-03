from typing import overload
from utils import error_400, error_404, MyAPI, success
from zlib import decompress

async def _get_paste_by_id(app: MyAPI, uuid: str):
    "Retrieve a paste in the database from a given `uuid`."

    if len(uuid) < app.config.PASTE_ID_LENGTH:
        return error_400("Invalid UUID.")

    async with app.pool.acquire() as conn:
        req = await conn.execute("SELECT filename, content FROM files WHERE id = ?", uuid)
        rows = await req.fetchall()
    
    if not rows:
        return error_404(f"No paste was found with the ID '{uuid}'.")

    return success | {
        "files": [
            [row["filename"], decompress(row["content"]).decode()]
            for row in rows
        ]
    }

@overload
async def _get_raw_paste_by_id(app: MyAPI, uuid: str) -> str:
    "Get the raw content of a paste by its UUID."

@overload
async def _get_raw_paste_by_id(app: MyAPI, uuid: str, filepos: int) -> str:
    "Get the raw content of a specific file in a paste."

async def _get_raw_paste_by_id(app: MyAPI, uuid: str, filepos: int = 0) -> str:
    r"""
    Works the same as `_get_paste_by_id` but returns content
    as plain text instead of through JSON.

    Each paste is shown with a header containing the filename:
    
    ```
    [test.py]
    print("Hello world!")
    ```

    Unnamed pastes have their name replaced with `???`.

    If multiple pastes are present, they are separated by the following:
    
        `\n\n***\n\n`
    
    Example
    -------
    ```
    [1. test.py]
    print("I am test.py!")

    ***

    [2. ???]
    print("I don't have a name.")
    ```
    """
   
    if len(uuid) < app.config.PASTE_ID_LENGTH:
       return "400: Invalid UUID."
   
    if filepos < 0:
        return "400: Invalid file position."

    if not filepos: # Not specified - get all files
        async with app.pool.acquire() as conn:
            req = await conn.execute("SELECT filename, content FROM files WHERE id = ?", uuid)
            rows = await req.fetchall()
        
        if not rows:
            return "404: Resource not found."

        return '\n\n***\n\n***'.join(
            f"[{i}. {row["filename"] or "???"}]" '\n'
            f"{decompress(row["content"]).decode()}"
            for i, row in enumerate(rows, start = 1)
        )
    
    # Specified - get specified file
    async with app.pool.acquire() as conn:
        req = await conn.execute(
            """
            SELECT filename, content FROM files
            WHERE id = ? AND position = ?
            """,
            uuid, filepos
        )
        row = await req.fetchone()
    
    if not row:
        return "404: Resource not found."
    
    return f"[{row["filename"]}]\n{decompress(row["content"]).decode()}"