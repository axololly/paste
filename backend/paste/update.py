from json import JSONDecodeError
from fastapi import Request
from ._types import UpdateRequest, Reply
from utils import error_400, error_404, format_file_size, http_reply, MyAPI, success
from zlib import compress

async def update_existing_paste(app: MyAPI, request: Request) -> Reply:
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
        data: UpdateRequest = await request.json()
    
    # No JSON was given.
    except JSONDecodeError:
        return error_400("No JSON was given.")

    if set(data.keys()) != {"id", "files"}:
        return error_400("Invalid keys found in JSON.")


    if not isinstance(data["id"], str): # type: ignore
        return error_400("'id' value is not a string.")
    
    async with app.pool.acquire() as conn:
        req = await conn.execute("SELECT expiration, removal_id FROM pastes WHERE id = ?", data["id"])
        paste_data_row = await req.fetchone()
    
    if not paste_data_row:
        return error_404(f"No paste was found with the ID '{data["id"]}'.")


    if not isinstance(data["files"], list): # type: ignore
        return error_400("'files' value is not a list.")

    total_paste_size = 0

    args_for_database: list[tuple[str, str, bytes, int]] = []

    for i, file in enumerate(data["files"]):
        if not isinstance(file, list): # type: ignore
            return error_400(f"item at index {i} is not a list.")
        
        if len(file) != 2:
            return error_400(f"item at index {i} does not contain two items.")

        filename, content = file

        if not isinstance(filename, str):
            return error_400(f"item 0 at index {i} is not a string.")
        
        if not isinstance(content, str): # type: ignore
            return error_400(f"item 1 at index {i} is not a string.")
        
        total_paste_size += len(content)

        if total_paste_size > app.config.MAX_PASTE_SIZE:
            return http_reply(422, f"Combined file size after file {i} exceeds maximum limit of {format_file_size(app.config.MAX_PASTE_SIZE)} by {format_file_size(total_paste_size - app.config.MAX_PASTE_SIZE)}")
        
        args_for_database.append((
            data["id"],
            filename,
            compress(content.encode()),
            i + 1
        ))


    async with app.pool.acquire() as conn:
        # Delete the existing files
        await conn.execute("DELETE FROM files WHERE id = ?", data["id"])

        # Add back the new files
        await conn.executemany(
            "INSERT INTO files (id, filename, content, position) VALUES (?, ?, ?, ?)",
            args_for_database
        )
    
    return success