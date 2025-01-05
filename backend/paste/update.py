from json import JSONDecodeError
from sanic.exceptions import BadRequest, NotFound, SanicException
from sanic.request import Request
from ._types import UpdateRequest
from utils import format_file_size, MyAPI
from zlib import compress

async def update_existing_paste(app: MyAPI, request: Request) -> None:
    """
    Update an existing paste through the JSON of a `request`.

    This does not refresh the time before deletion.

    Format
    ------
    ```json
    {
        "id": // The UUID required
        "files": // The new content to add - list[list[int, str]]
    }
    ```
    """
    
    try:
        data: UpdateRequest = request.json
    
    # No JSON was given.
    except JSONDecodeError:
        raise BadRequest("No JSON was given.")

    if set(data.keys()) != {"id", "files"}:
        raise BadRequest("Invalid keys found in JSON.")


    if not isinstance(data["id"], str): # type: ignore
        raise BadRequest("'id' value is not a string.")
    
    async with app.ctx.pool.acquire() as conn:
        req = await conn.execute("SELECT expiration, removal_id FROM pastes WHERE id = ?", data["id"])
        paste_data_row = await req.fetchone()
    
    if not paste_data_row:
        raise NotFound(f"No paste was found with the ID '{data["id"]}'.")


    if not isinstance(data["files"], list): # type: ignore
        raise BadRequest("'files' value is not a list.")

    total_paste_size = 0

    args_for_database: list[tuple[str, str, bytes, int]] = []

    for i, file in enumerate(data["files"]):
        if not isinstance(file, list): # type: ignore
            raise BadRequest(f"item at index {i} is not a list.")
        
        if len(file) != 2:
            raise BadRequest(f"item at index {i} does not contain two items.")

        filename, content = file

        if not isinstance(filename, str):
            raise BadRequest(f"item 0 at index {i} is not a string.")
        
        if not isinstance(content, str): # type: ignore
            raise BadRequest(f"item 1 at index {i} is not a string.")
        
        total_paste_size += len(content)

        if total_paste_size > app.ctx.configs.MAX_PASTE_SIZE:
            raise SanicException(
                f"Combined file size after file {i} exceeds maximum limit "
                f"of {format_file_size(app.ctx.configs.MAX_PASTE_SIZE)} by"
                f" {format_file_size(total_paste_size - app.ctx.configs.MAX_PASTE_SIZE)}",
                
                422
            )
        
        args_for_database.append((
            data["id"],
            filename,
            compress(content.encode()),
            i + 1
        ))


    async with app.ctx.pool.acquire() as conn:
        # Delete the existing files
        await conn.execute("DELETE FROM files WHERE id = ?", data["id"])

        # Add back the new files
        await conn.executemany(
            "INSERT INTO files (id, filename, content, position) VALUES (?, ?, ?, ?)",
            args_for_database
        )