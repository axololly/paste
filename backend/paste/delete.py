from discord.ext import tasks
from fastapi import Request
from utils import http_reply, MyAPI, sleep_until, success

async def _delete_paste_by_link(app: MyAPI, delete_id: str) -> dict[str, int | str]:
    async with app.pool.acquire() as conn:
        req = await conn.execute("SELECT 1 FROM pastes WHERE delete_id = ?", delete_id)
        row = await req.fetchone()

        if not row:
            return http_reply(404, f"No resource was found under the id '{delete_id}'.")

        await conn.execute("DELETE FROM pastes WHERE delete_id = ?", delete_id)
    
    return success