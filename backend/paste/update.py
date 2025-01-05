from sanic.exceptions import NotFound, SanicException
from ._types import UpdateRequest
from utils import format_file_size, MyAPI
from zlib import compress

async def update_existing_paste(app: MyAPI, data: UpdateRequest) -> None:
    """
    Update an existing paste in the database.

    This uses a similar JSON document structure
    to the `/create/` endpoint, providing
    intuitive usage.

    Parameters
    ----------
    app: `MyAPI`
        the app currently running.
    data: `UpdateRequest`
        the data relevant to the operation.
    
    Raises
    ------
    `BadRequest`
        some arguments were invalid.
    `NotFound`
        the given paste ID could not
        be found in the database.
    """
    
    async with app.ctx.pool.acquire() as conn:
        req = await conn.execute("SELECT expiration, removal_id FROM pastes WHERE id = ?", data.id)
        paste_data_row = await req.fetchone()
    
    if not paste_data_row:
        raise NotFound(f"No paste was found with the ID '{data.id}'.")

    args_for_database: list[tuple[str, str | None, bytes, int]] = []
    total_paste_size = 0

    for i, (filename, content) in enumerate(data.files):
        total_paste_size += len(content)

        # If the paste size exceeds what is required, return
        # a 422 (Unprocessable Entity) HTTP status code.
        if total_paste_size > app.ctx.configs.MAX_PASTE_SIZE:
            raise SanicException(
                f"Combined file size after file {i} exceeds maximum limit "
                f"of {format_file_size(app.ctx.configs.MAX_PASTE_SIZE)} by"
                f" {format_file_size(total_paste_size - app.ctx.configs.MAX_PASTE_SIZE)}",
                
                422
            )
        
        args_for_database.append((
            data.id,
            filename,
            compress(content.encode()),
            i + 1
        ))

    async with app.ctx.pool.acquire() as conn:
        # Delete the existing files
        await conn.execute("DELETE FROM files WHERE id = ?", data.id)

        # Add back the new files
        await conn.executemany(
            "INSERT INTO files (id, filename, content, position) VALUES (?, ?, ?, ?)",
            args_for_database
        )