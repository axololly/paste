"A helper module to provide helper functions."

from __future__ import annotations
from asqlite import Pool
from asyncio import sleep
from datetime import datetime as dt
from discord.ext import tasks
from fastapi import FastAPI
from typing import overload

# =================================================================================================

def http_reply(status_code: int, message: str) -> dict[str, int | str]:
    return {
        "status": status_code,
        "message": message or "No message given."
    }

success = http_reply(200, "Success!")
error_400 = lambda message: http_reply(400, message)

# =================================================================================================

@overload
async def sleep_until(datetime: dt, /) -> None:
    "Sleep until a given `datetime`."

@overload
async def sleep_until(timestamp: int, /) -> None:
    "Sleep until a given timestamp."

async def sleep_until(_dt_or_ts: dt | int, /) -> None:
    if isinstance(_dt_or_ts, dt):
        time_asleep = _dt_or_ts.timestamp() - dt.now().timestamp()
    elif isinstance(_dt_or_ts, int):
        time_asleep = _dt_or_ts - dt.now().timestamp()
    else:
        raise TypeError("given argument is not an integer or datetime object.")

    if time_asleep <= 0:
        return
    
    await sleep(time_asleep)

# =================================================================================================

class Config:
    MAX_ENTRIES: int = 100_000
    "A constant for the maximum number of entries the database should be able to take."

    MAX_FILE_SIZE: int = 100_000
    "A constant for the maximum number of bytes each paste should have in total."

    DEFAULT_EXPIRATION_IN_DAYS: int = 1
    "A constant for the number of days to keep a paste, by default."

class BackgroundLoops:
    app: MyAPI
    delete_in_background: tasks.Loop

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