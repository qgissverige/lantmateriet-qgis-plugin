import re
from typing import Iterable

from lantmateriet.core.util.municipalities import municipalities


def omit(data: dict, keys: Iterable[str]) -> dict:
    return {k: v for k, v in data.items() if k not in keys}


UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


__all__ = ["municipalities", "omit", "UUID_RE"]
