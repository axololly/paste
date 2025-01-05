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
url_regex = re.compile(r"(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}(?:\:\d{4})?)\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)")

async def create_new_paste(
    app: MyAPI,
    request: Request
) -> JSONResponse:
    """
    ...
    """
    
    # Get the JSON data from the request
    try:
        data: CreateRequest = request.json
    except JSONDecodeError:
        raise BadRequest("No JSON was given.")
    
    # Optional JSON key
    if "keep_for" in data:
        # Not an integer - return 400
        if not isinstance(data["keep_for"], (int, float)):
            raise BadRequest("'keep_for' value is not an integer or decimal.")
        
        # Not in range 1-30 inclusive - return 400
        if not 1 <= data["keep_for"] <= 30:
            raise BadRequest("'keep_for' is not in range 1-30 inclusive.")
    
    # Get how many days the paste should be kept for.
    # If not specified, it defaults to the corresponding
    # attribute on the `Config` class.
    days_before_expiration: int = data.pop("keep_for", app.ctx.configs.DEFAULT_EXPIRATION_IN_DAYS) # type: ignore

    # Does not match scheme - return 400
    if "files" not in data:
        raise SanicException("'files' key missing in JSON.", 400)

    files: list[tuple[str | None, str]] = data["files"]

    total_paste_size = 0
    
    for i, file in enumerate(files):
        # `file` is not a list
        if not isinstance(file, list): # type: ignore
            raise BadRequest(f"element at index {i} in 'files' list is not a list.")
        
        # `file` does not have two items in it
        if len(file) != 2:
            raise BadRequest(f"element at index {i} in 'files' has more or less than 2 items inside.")

        # Deconstruct for easier management
        filename, content = file

        # `filename` is not a string or `NoneType`
        if not isinstance(filename, (str, type(None))): # type: ignore
            raise BadRequest(f"first element at index {i} in 'files' is not a string or NoneType equivalent.")

        # `content` is not a string
        if not isinstance(content, str): # type: ignore
            raise BadRequest(f"second element at index {i} in 'files' is not a string.")
        
        if not content:
            raise BadRequest(f"second element at index {i} in 'files' is an empty string.")

        total_paste_size += len(content)

        # If the file size exceeds what is required, return
        # a 422 (Unprocessable Entity) HTTP status code.
        if total_paste_size > app.ctx.configs.MAX_PASTE_SIZE:
            raise SanicException(
                f"Combined file size after file {i} exceeds maximum limit " +
                f"of {format_file_size(app.ctx.configs.MAX_PASTE_SIZE)} by" +
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

    expiration = int((dt.now() + td(days = days_before_expiration)).timestamp())

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
                (paste_id, filename, compress(content.encode()), position) # type: ignore (content is always 'str')
                for position, (filename, content) in enumerate(files, start = 1)
            ]
        )
    
    base_url = re.sub(url_regex, r'\1', request.url)
    
    return to_json({
        "paste_id": paste_id,
        "removal_id": removal_id,
        "removal_link": f"{base_url}/delete/{removal_id}"
    })