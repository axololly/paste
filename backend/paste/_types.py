"""
from typing import TypedDict

class Reply(TypedDict):
    status: int
    message: str

class CountRow(TypedDict):
    count: int

class CreateRequest(TypedDict):
    id: str
    files: list[list[str | None]]
    keep_for: int | None

class CreateSuccess(Reply, TypedDict):
    paste_id: str
    removal_id: str
    removal_link: str

class GetSuccess(Reply):
    files: list[list[str | None]]
"""

# ======================================================

from typing import TypedDict

type Files = list[tuple[str | None, str]]

class CreateRequest(TypedDict):
    files: Files
    keep_for: int | None

class UpdateRequest(TypedDict):
    id: str
    files: Files

class CountRow(TypedDict):
    count: int

# ======================================================

from pydantic import BaseModel

class Reply(BaseModel):
    status: int
    message: str

class Success(Reply):
    status: int = 200
    message: str = "Success!"

class GetSuccess(Success):
    files: list[tuple[str | None, str]]

class CreateSuccess(Success):
    paste_id: str
    removal_id: str
    removal_link: str