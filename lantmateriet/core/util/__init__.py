from typing import Iterable


def omit(data: dict, keys: Iterable[str]) -> dict:
    return {k: v for k, v in data.items() if k not in keys}


__all__ = ["omit"]
