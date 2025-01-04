"A helper module to provide helper functions."

from asqlite import Pool
from asyncio import sleep
from datetime import datetime as dt
from discord.ext import tasks
from paste._types import Reply, Success
from sanic import Sanic
from typing import overload

# =================================================================================================

def http_reply(status_code: int, message: str) -> Reply:
    return Reply(
        status = status_code,
        message = message or "No message given."
    )

success: Success = Success()

def error_400(message: str) -> Reply: return http_reply(400, message)
def error_404(message: str) -> Reply: return http_reply(404, message)

# =================================================================================================

class Config:
    MAX_ENTRIES = 100_000
    "A constant for the maximum number of entries the database should be able to take."

    MAX_PASTE_SIZE = 100_000 # 100 KB
    "A constant for the maximum number of bytes each paste should have in total."

    DEFAULT_EXPIRATION_IN_DAYS = 1
    "A constant for the number of days to keep a paste, by default."

    PASTE_ID_LENGTH = 10
    "A constant for how long paste IDs in the database should be."

    REMOVAL_ID_LENGTH = 22
    "A constant for how long removal IDs in the database should be."

class APIContext:
    pool: Pool
    configs: Config = Config()
    loops: 'BackgroundLoops'

class MyAPI(Sanic):
    ctx: APIContext

# =================================================================================================

class BackgroundLoops:
    def __init__(self, app: MyAPI) -> None:
        self.app = app
    
    @overload
    async def sleep_until(self, timestamp: int | float, /) -> None:
        "Returns a coroutine to let you sleep until a given `timestamp` is reached."
    
    @overload
    async def sleep_until(self, datetime: dt, /) -> None:
        "Returns a coroutine to let you sleep until a given `datetime` is reached."

    async def sleep_until(self, _dt_or_ts: dt | int | float, /) -> None:
        "Returns a coroutine to let you sleep until a given `datetime` or `timestamp` is reached."

        if isinstance(_dt_or_ts, dt):
            time_asleep = _dt_or_ts.timestamp() - dt.now().timestamp()
        elif isinstance(_dt_or_ts, (int, float)): # type: ignore
            time_asleep = _dt_or_ts - dt.now().timestamp()
        else:
            raise TypeError("given argument is not an integer or datetime object.")
        
        await sleep(time_asleep)

    def start(self) -> None:
        "Start all loops attached to this instance."

        for attr_value in self.__dict__.values():
            if isinstance(attr_value, tasks.Loop):
                attr_value.start()
    
    def end(self) -> None:
        "Cancel all loops attached to this instance."

        for attr_value in self.__dict__.values():
            if isinstance(attr_value, tasks.Loop):
                attr_value.cancel()
    
    @tasks.loop(seconds = 1)
    async def delete_in_background(self) -> None:
        """
        Repeatedly sleep until an entry needs to
        be deleted and then delete it.
        """

        async with self.app.ctx.pool.acquire() as conn:
            req = await conn.execute(
                """
                SELECT id, expiration FROM pastes
                ORDER BY expiration
                LIMIT 1
                """
            )
            row = await req.fetchone()
        
        if not row:
            self.app.ctx.loops.delete_in_background.cancel()
            return
        
        await self.sleep_until(row["expiration"])

        async with self.app.ctx.pool.acquire() as conn:
            await conn.execute("DELETE FROM pastes WHERE id = ?", row["id"])

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
    
    raise ValueError("no units dictionary is present.")