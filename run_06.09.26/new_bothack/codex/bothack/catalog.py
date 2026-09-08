"""Exact, generated BotHack knowledge tables; no JVM is used at runtime."""
from functools import lru_cache
from importlib.resources import files
import json


@lru_cache(maxsize=1)
def data():
    return json.loads(files("bothack").joinpath("data/original.json").read_text())


@lru_cache(maxsize=1)
def items_by_name():
    result = {item["name"]: item for item in data()["items"]}
    result.update({item["fullname"]: item for item in data()["items"] if item.get("fullname")})
    return result


@lru_cache(maxsize=1)
def monsters_by_name():
    return {monster["name"]: monster for monster in data()["monsters"]}
