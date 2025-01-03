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

class CreateSuccess(Reply):
    paste_id: str
    removal_id: str
    removal_link: str

class GetSuccess(Reply):
    files: list[list[str | None]]