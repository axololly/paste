from sanic.exceptions import BadRequest, NotFound
from ._types import GetResponse
from typing import overload
from utils import MyAPI
from zlib import decompress

async def get_paste_by_id(app: MyAPI, uuid: str) -> GetResponse:
    """
    Retrieve a paste in the database from a given `uuid`.

    Parameters
    ----------
    app: `MyAPI`
        the instance of the app currently running right now.
    uuid: `str`
        the UUID of the paste to retrieve.

    Returns
    -------
    `GetResponse`
        the resulting response.
    """

    if len(uuid) < app.ctx.configs.PASTE_ID_LENGTH:
        raise BadRequest("Invalid UUID.")

    async with app.ctx.pool.acquire() as conn:
        req = await conn.execute("SELECT filename, content FROM files WHERE id = ?", uuid)
        rows = await req.fetchall()
    
    if not rows:
        raise NotFound(f"No paste was found with the ID '{uuid}'.")

    return GetResponse(
        files = [
            (row["filename"], decompress(row["content"]).decode())
            for row in rows
        ]
    )

@overload
async def get_raw_paste_by_id(app: MyAPI, uuid: str) -> str:
    "Get the raw content of a paste by its UUID."

@overload
async def get_raw_paste_by_id(app: MyAPI, uuid: str, filepos: int) -> str:
    "Get the raw content of a specific file in a paste."

async def get_raw_paste_by_id(app: MyAPI, uuid: str, filepos: int = 0) -> str:
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
   
    if len(uuid) < app.ctx.configs.PASTE_ID_LENGTH:
       raise BadRequest("Invalid UUID.")
   
    if filepos < 0:
        raise BadRequest("Invalid file position.")

    # Not specified - get all files
    if not filepos:
        async with app.ctx.pool.acquire() as conn:
            req = await conn.execute("SELECT filename, content FROM files WHERE id = ?", uuid)
            rows = await req.fetchall()
        
        if not rows:
            raise NotFound("Resource not found.")

        return '\n\n***\n\n***'.join(                   # Separator
            f"[{i}. {row["filename"] or "???"}]" '\n'   # Header
            f"{decompress(row["content"]).decode()}"    # Text
            for i, row in enumerate(rows, start = 1)
        )
    
    # Specified - get specified file
    async with app.ctx.pool.acquire() as conn:
        req = await conn.execute(
            """
            SELECT filename, content FROM files
            WHERE id = ? AND position = ?
            """,
            uuid, filepos
        )
        row = await req.fetchone()
    
    if not row:
        raise NotFound("Resource not found.")
    
    return f"[{row["filename"]}]\n{decompress(row["content"]).decode()}"