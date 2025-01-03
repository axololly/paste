from asyncio import sleep
from datetime import datetime as dt
from discord.ext import tasks
from typing import Awaitable, overload
from utils import MyAPI

class BackgroundLoops:
    def __init__(self, app: MyAPI) -> None:
        self.app = app
    
    @overload
    def sleep_until(self, timestamp: int, /) -> Awaitable[None]:
        "Returns a coroutine to let you sleep until a given `timestamp` is reached."
    
    @overload
    def sleep_until(self, datetime: dt, /) -> Awaitable[None]:
        "Returns a coroutine to let you sleep until a given `datetime` is reached."

    def sleep_until(self, _dt_or_ts: dt | int, /) -> Awaitable[None]:
        "Returns a coroutine to let you sleep until a given `datetime` or `timestamp` is reached."

        if isinstance(_dt_or_ts, dt):
            time_asleep = _dt_or_ts.timestamp() - dt.now().timestamp()
        elif isinstance(_dt_or_ts, int):
            time_asleep = _dt_or_ts - dt.now().timestamp()
        else:
            raise TypeError("given argument is not an integer or datetime object.")

        if time_asleep <= 0:
            return
        
        return sleep(time_asleep)

    def start(self) -> None:
        "Start all loops attached to this instance."

        for attr_value in self.__dict__.values():
            if isinstance(attr_value, tasks.Loop):
                attr_value.start()
    
    @tasks.loop(seconds = 1)
    async def delete_in_background(self) -> None:
        """
        Repeatedly sleep until an entry needs to
        be deleted and then delete it.
        """

        async with self.app.pool.acquire() as conn:
            req = await conn.execute(
                """
                SELECT id, expiration FROM pastes
                ORDER BY expiration
                LIMIT 1
                """
            )
            row = await req.fetchone()
        
        if not row:
            self.app.deleting_loop.cancel()
        
        await self.sleep_until(row["expiration"])

        async with self.app.pool.acquire() as conn:
            await conn.execute("DELETE FROM pastes WHERE id = ?", row["id"])