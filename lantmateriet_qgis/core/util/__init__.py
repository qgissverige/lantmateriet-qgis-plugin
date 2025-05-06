import re
from typing import Iterable

from lantmateriet_qgis.core.util.municipalities import municipalities


def omit(data: dict, keys: Iterable[str]) -> dict:
    return {k: v for k, v in data.items() if k not in keys}


def flatten(data: dict, parent: str = "") -> dict:
    items = {}
    for k, v in data.items():
        new_key = f"{parent}.{k}" if parent else k
        if isinstance(v, dict):
            items.update(flatten(v, new_key))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.update(flatten(item, f"{new_key}.{i}"))
                else:
                    items[f"{new_key}.{i}"] = item
        else:
            items[new_key] = v
    return items


UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


__all__ = ["municipalities", "omit", "flatten", "UUID_RE"]
