"A helper module to provide helper functions."

from __future__ import annotations
from asqlite import Pool
from discord.ext import tasks
from fastapi import FastAPI

# =================================================================================================

def http_reply(status_code: int, message: str) -> dict[str, int | str]:
    return {
        "status": status_code,
        "message": message or "No message given."
    }

success = http_reply(200, "Success!")
error_400 = lambda message: http_reply(400, message)
error_404 = lambda message: http_reply(404, message)

# =================================================================================================

class Config:
    MAX_ENTRIES = 100_000
    "A constant for the maximum number of entries the database should be able to take."

    MAX_PASTE_SIZE = 100_000
    "A constant for the maximum number of bytes each paste should have in total."

    DEFAULT_EXPIRATION_IN_DAYS = 1
    "A constant for the number of days to keep a paste, by default."

    PASTE_ID_LENGTH = 10
    "A constant for how long paste IDs in the database should be."

    REMOVAL_ID_LENGTH = 22
    "A constant for how long removal IDs in the database should be."

class BackgroundLoops:
    app: MyAPI
    delete_in_background: tasks.Loop
    
    def start(self) -> None: ...

class MyAPI(FastAPI):
    pool: Pool
    config: Config = Config
    loops: BackgroundLoops

# =================================================================================================

def format_file_size(count: int) -> str:
    if count < 0:
        raise ValueError("'count' argument cannot be negative.")
    
    if count == 0:
        return '0 B'

    units = {
        1 << 40: "TB",
        1 << 30: "GB",
        1 << 20: "MB",
        1 << 10: "KB",
        1 <<  0:  "B"
    }

    for capacity, unit in units.items():
        if count > capacity:
            return f"{count / capacity:.2f} {unit}"