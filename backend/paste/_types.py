from pydantic import BaseModel
from typing import TypedDict

class CountRow(TypedDict):
    count: int

type Files = list[tuple[str | None, str]]

class CreateRequest(TypedDict):
    files: Files
    keep_for: int | None

class UpdateRequest(TypedDict):
    id: str
    files: Files

class GetResponse(BaseModel):
    files: list[tuple[str | None, str]]

class CreateResponse(BaseModel):
    paste_id: str
    removal_id: str
    removal_link: str