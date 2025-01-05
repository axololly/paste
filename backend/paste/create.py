import shortuuid, re
from datetime import datetime as dt, timedelta as td
from json import JSONDecodeError
from sanic.exceptions import BadRequest, SanicException
from sanic.request import Request
from sanic.response import JSONResponse, json as to_json
from ._types import CountRow, CreateRequest, CreateResponse
from utils import format_file_size, MyAPI
from zlib import compress

# URL regex that's used to extract the domain name
# from the `url` attribute on `request`.
# Group 1 is the domain and group 2 is the route.
url_regex = re.compile(r"(https?:\/\/[\w.]*?(\:\d{4})?)\/")

async def create_new_paste(
    app: MyAPI,
    data: CreateRequest,
    request_url: str
) -> JSONResponse:
    """
    Create a new paste in the database with the given `data`.

    This takes a list of two-long sublists that start with an
    optional filename and finish with a required code sample
    to upload onto the database.

    Parameters
    ----------
    app: `FastAPI`
        the app currently running.
    data: `CreateRequest`
        the data the user submitted for upload.
    request_url: `str`
        the complete URL the request was made from. This
        is necessary for generating a delete link.
    
    Returns
    -------
    `JSONResponse`
        a JSON document containing the ID of the created
        paste and its removal link.
    
    Raises
    ------
    `BadRequest`
        the request did not match the designated schema.
    `SanicException`
        403: database reached allowed maximum; no space left.
        422: file size exceeded allowed maximum.
    """

    total_paste_size = sum([len(content) for _, content in data.files])

    # If the paste size exceeds what is required, return
    # a 422 (Unprocessable Entity) HTTP status code.
    if total_paste_size > app.ctx.configs.MAX_PASTE_SIZE:
        raise SanicException(
            f"Combined file size exceeds maximum limit of" +
            f" {format_file_size(app.ctx.configs.MAX_PASTE_SIZE)} by" +
            f" {format_file_size(total_paste_size - app.ctx.configs.MAX_PASTE_SIZE)}",
                
            422
        )
    

    async with app.ctx.pool.acquire() as conn:
        req = await conn.execute("SELECT COUNT(*) AS 'count' FROM pastes")
        row: CountRow = await req.fetchone() # type: ignore
        count = row["count"]
    
    # Verify that there's still space available in the database.
    # If there isn't, return a 403 notifying the user.
    if count == app.ctx.configs.MAX_ENTRIES:
        raise SanicException("System is full. Please try again later.", 403)

    async def get_unique_uuid(*, length: int, column: str) -> str:
        "Get a new UUID with length `length` that hasn't appeared in the `column` column of the database."

        async with app.ctx.pool.acquire() as conn:
            while True:
                # Generate a new ID
                next_uuid = shortuuid.random(length)

                # Check it doesn't already exist
                req = await conn.execute(f"SELECT 1 FROM pastes WHERE {column} = ?", next_uuid)
                row = await req.fetchone()

                # Unique ID is found
                if not row:
                    return next_uuid
    

    paste_id = await get_unique_uuid(
        length = app.ctx.configs.PASTE_ID_LENGTH,
        column = "id"
    )
    
    removal_id = await get_unique_uuid(
        length = app.ctx.configs.REMOVAL_ID_LENGTH,
        column = "removal_id"
    )

    expiration = int((dt.now() + td(days = data.keep_for)).timestamp())

    async with app.ctx.pool.acquire() as conn:
        # Add to the `pastes` table
        await conn.execute(
            "INSERT INTO pastes (id, expiration, removal_id) VALUES (?, ?, ?)",
            paste_id, expiration, removal_id
        )

        # Add all the file data to the `files` table
        await conn.executemany(
            "INSERT INTO files (id, filename, content, position) VALUES (?, ?, ?, ?)",
            [
                (paste_id, filename, compress(content.encode()), position)
                for position, (filename, content) in enumerate(data.files, start = 1)
            ]
        )
    
    base_url = re.sub(url_regex, r'\1', request_url)
    
    return to_json({
        "paste_id": paste_id,
        "removal_link": f"{base_url}/delete/{removal_id}"
    })