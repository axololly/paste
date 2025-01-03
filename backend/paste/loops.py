from discord.ext import tasks
from utils import MyAPI, sleep_until

class BackgroundLoops:
    def __init__(self, app: MyAPI) -> None:
        self.app = app
    
    @tasks.loop(seconds = 1)
    async def delete_in_background(self) -> None:
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
        
        await sleep_until(row["expiration"])

        async with self.app.pool.acquire() as conn:
            await conn.execute("DELETE FROM pastes WHERE id = ?", row["id"])