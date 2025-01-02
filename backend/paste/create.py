from datetime import datetime as dt, timedelta as td
from fastapi import FastAPI, Request
from json import JSONDecodeError
from ..utils import error_400, http_reply, PasteCodes, success
from zlib import compress

async def _create_new_paste(app: FastAPI, request: Request) -> dict[str, int | str]:
    try:
        data: dict = await request.json()
    
    # No JSON was given.
    except JSONDecodeError:
        return error_400("No JSON was given.")

    if "files" not in data:
        return error_400("No 'files' key found in JSON.")
    
    files: list[list[str | None, str]] = data["files"]

    if not files:
        return error_400("'files' key is an empty list.")

    async with app.pool.acquire() as conn:
        req = await conn.execute('SELECT COUNT(*) FROM pastes AS "count"')
        row = await req.fetchone()
        
    database_id = row["count"] + 1

    if database_id == len(PasteCodes.valid_chars) ** PasteCodes.ID_LENGTH:
        return http_reply(
            403,
            "No more pastes can be created at this given time. "
            "Notify the owner to increase this limit."
        )
    
    display_id = PasteCodes.from_int(database_id, length = PasteCodes.ID_LENGTH)

    if not isinstance(files, list):
        return error_400("'files' key is not mapped to a list.")
    
    args_for_database: list[tuple[int, str | None, bytes]] = []

    for pos, file in enumerate(files):
        if not isinstance(file, list):
            return error_400(f"datatype at pos {pos} is not a list.")

        if len(file) != 2:
            return error_400(f"invalid length {len(file)} of inner list at pos {pos}.")
        
        filename, content = file

        if not isinstance(filename, (str, type(None))):
            return error_400(f"type of first element at pos {pos} is not a string or None.")

        if not isinstance(content, str):
            return error_400(f"type of second element at pos {pos} is not a string.")
        
        # Check that the data is within 5MB in size
        # x << 20 is the same as x * 1024 * 1024
        if len(content) > (5 << 20):
            return http_reply(403, f"Cannot store entries of over 5MB: the given file was {len(content) / (1024**2):,.2f} GB in size.")
        
        args_for_database.append((database_id, filename, compress(content)))

    if "keep_for" in data:
        days_before_delete = data["keep_for"]

        if not isinstance(days_before_delete, int):
            return error_400("'keep_for' argument is not an integer.")
        
        if not 1 <= days_before_delete <= 30:
            return error_400("'keep_for' argument is not between 1 and 30 (inclusive).")

        delete_timestamp = int(dt.now() + td(days = days_before_delete))
    
    else:
        # Keep data for 7 days before deleting
        delete_timestamp = int(dt.now() + td(days = 7))

    async with app.pool.acquire() as conn:
        # Insert the compressed data into the database to save space
        await conn.executemany(
            "INSERT INTO pastes (id, filename, content) VALUES (?, ?, ?)",
            args_for_database
        )

        # Insert a row for when to delete the entry
        await conn.execute(
            "INSERT INTO expiries (id, expiry_timestamp) VALUES (?, ?)",
            database_id, delete_timestamp
        )

    return success | {
        "paste_id": display_id
    }