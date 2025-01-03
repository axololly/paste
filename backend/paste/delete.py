from utils import error_404, MyAPI, success

"""
async def _delete_paste_by_id(app: MyAPI, paste_id: str) -> dict[str, int | str]:
    async with app.pool.acquire() as conn:
        req = await conn.execute("SELECT 1 FROM pastes WHERE id = ?", paste_id)
        row = await req.fetchone()

        if not row:
            return error_404(f"No resource was found under the id '{paste_id}'.")

        await conn.execute("DELETE FROM pastes WHERE delete_id = ?", paste_id)
    
    return success
"""

async def _delete_paste_by_link(app: MyAPI, removal_id: str) -> dict[str, int | str]:
    async with app.pool.acquire() as conn:
        req = await conn.execute("SELECT 1 FROM pastes WHERE removal_id = ?", removal_id)
        row = await req.fetchone()

        if not row:
            return error_404(f"No resource was found under the id '{removal_id}'.")

        await conn.execute("DELETE FROM pastes WHERE removal_id = ?", removal_id)
    
    return success