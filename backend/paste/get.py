from sanic.exceptions import BadRequest, NotFound
from sanic.response import HTTPResponse
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
async def get_raw_paste_by_id(app: MyAPI, uuid: str) -> HTTPResponse:
    "Get the raw content of a paste by its UUID."

@overload
async def get_raw_paste_by_id(app: MyAPI, uuid: str, filepos: int) -> HTTPResponse:
    "Get the raw content of a specific file in a paste."

async def get_raw_paste_by_id(app: MyAPI, uuid: str, filepos: int = 0) -> HTTPResponse:
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
    
    For an example, see below:

    ```
    [1. test.py]
    print("I am test.py!")

    ***

    [2. ???]
    print("I don't have a name.")
    ```

    Parameters
    ----------
    app: `MyAPI`
        the app currently running.
    uuid: `str`
        the UUID of the paste to get.
    filepos: `int`
        which file to select. By default, this selects
        all the files related to the paste.
    
    Returns
    -------
    `HTTPResponse`
        the raw text retrieved from the database.
    
    Raises
    ------
    `BadRequest`
        some arguments given were invalid.
    `NotFound`
        the requested paste (or file) was not
        present in the database.
    """
   
    if len(uuid) < app.ctx.configs.PASTE_ID_LENGTH:
       raise BadRequest("Invalid UUID.")
   
    if filepos < 0:
        raise BadRequest("Invalid file position.")

    # Specified - get specified file
    if filepos:
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

        text = f"[{row["filename"]}]\n{decompress(row["content"]).decode()}"
    
    # Not specified - get all files
    else:
        async with app.ctx.pool.acquire() as conn:
            req = await conn.execute("SELECT filename, content FROM files WHERE id = ?", uuid)
            rows = await req.fetchall()
        
        if not rows:
            raise NotFound("Resource not found.")

        text = '\n\n***\n\n***'.join(                   # Separator
            f"[{i}. {row["filename"] or "???"}]" '\n'   # Header
            f"{decompress(row["content"]).decode()}"    # Text
            for i, row in enumerate(rows, start = 1)
        )

    return HTTPResponse(text)