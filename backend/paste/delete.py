from utils import error_404, MyAPI, success
from ._types import Reply

async def delete_paste_by_link(app: MyAPI, removal_id: str) -> Reply:
    async with app.pool.acquire() as conn:
        req = await conn.execute("SELECT 1 FROM pastes WHERE removal_id = ?", removal_id)
        row = await req.fetchone()

        if not row:
            return error_404(f"No resource was found under the id '{removal_id}'.")

        await conn.execute("DELETE FROM pastes WHERE removal_id = ?", removal_id)
    
    return success