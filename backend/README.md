# Backend - FastAPI with Python

The backend of this pastebin application was written using [`sanic`](https://sanic.dev/en/), which was incredibly simple and easy to use.

> :wrench::memo: **Note:** The background tasks that delete pastes after they've expired uses [`discord.py`](https://github.com/Rapptz/discord.py)'s [`tasks.loop`](https://github.com/Rapptz/discord.py/blob/master/discord/ext/tasks/__init__.py#L768) decorator, wrapped in my own [`BackgroundLoops`](https://github.com/axololly/paste/tree/main/backend/paste/loops.py#L7-L52) class.

For documentation, click [here](https://github.com/axololly/paste/tree/main/backend/docs/api.md) to read.