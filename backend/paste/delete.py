from sanic.exceptions import NotFound
from sanic.response import HTTPResponse
from utils import MyAPI

async def delete_paste_by_link(app: MyAPI, removal_id: str) -> HTTPResponse:
    """
    Delete a paste from its removal ID.

    This isn't anything more than a simple
    `DELETE FROM` statement on the database.

    Parameters
    ----------
    app: `MyAPI`
        the app currently running.
    removal_id: `str`
        the removal ID of the paste. Note that
        this is **NOT** the main ID of the paste;
        these are two different values.
    
    Returns
    -------
    `HTTPResponse`
        a simple text response displaying the operation
        was successful.
    
    Raises
    ------
    `NotFound`
        there was no paste with the given removal ID.
    """
    
    async with app.ctx.pool.acquire() as conn:
        req = await conn.execute("SELECT 1 FROM pastes WHERE removal_id = ?", removal_id)
        row = await req.fetchone()

        if not row:
            raise NotFound(f"No resource was found under the id '{removal_id}'.")

        await conn.execute("DELETE FROM pastes WHERE removal_id = ?", removal_id)
    
    return HTTPResponse("Success.")