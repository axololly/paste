from pydantic import BaseModel, field_validator
from sanic.exceptions import BadRequest
from typing import TypedDict
from utils import Config

class CountRow(TypedDict):
    """
    Represents the resulting row of the SQL:
    
    ```sql
    SELECT COUNT(...) AS 'count' FROM ...
    ```
    """

    count: int

type Files = list[tuple[str | None, str]]
"A type alias for how files in the pastebin are meant to be submitted."

class CreateRequest(BaseModel):
    """
    A type class that models how a JSON request
    to the `/create/` endpoint should be formatted.

    `keep_for` cannot be less than 1 or greater than
    30, as that's the number of days to store a paste
    for. By default, this number is 1.
    """
    
    files: Files
    keep_for: int | float = Config.DEFAULT_EXPIRATION_IN_DAYS

    @field_validator('keep_for')
    def validate_fields(cls, val: int, _) -> int:
        if not 1 <= val <= 30:
            raise BadRequest("'keep_for' is not in range 1-30 inclusive.")
        
        return val

class CreateResponse(BaseModel):
    """
    A type class that models how a JSON response
    from the `/create/` endpoint should be formatted.
    """

    paste_id: str
    removal_id: str
    removal_link: str


class UpdateRequest(BaseModel):
    """
    A type class that models how a JSON request
    to the `/update/` endpoint should be formatted.
    """

    id: str
    files: Files


class GetResponse(BaseModel):
    """
    A type class that models how a JSON response
    from the `/get/` endpoint should be formatted.
    """

    files: Files