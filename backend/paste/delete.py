from sanic.exceptions import NotFound
from utils import MyAPI

async def delete_paste_by_link(app: MyAPI, removal_id: str) -> None:
    async with app.ctx.pool.acquire() as conn:
        req = await conn.execute("SELECT 1 FROM pastes WHERE removal_id = ?", removal_id)
        row = await req.fetchone()

        if not row:
            raise NotFound(f"No resource was found under the id '{removal_id}'.")

        await conn.execute("DELETE FROM pastes WHERE removal_id = ?", removal_id)