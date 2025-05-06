"""These are helpers to help create CQL2 queries."""


def property(name: str) -> dict:
    return dict(property=name)


def like(a: str | dict, b: str | dict) -> dict:
    return dict(op="like", args=[a, b])


def startswith(a: str | dict, b: str) -> dict:
    return dict(op="like", args=[a, b + "%"])


def equals(a: str | dict, b: str | int | dict) -> dict:
    return dict(op="=", args=[a, b])


def between(value: int | dict, lower: int | dict, upper: int | dict) -> dict:
    return dict(op="between", args=[value, lower, upper])


def in_(a: str | dict, b: list[str | int | dict]) -> dict:
    if len(b) == 1:
        return equals(a, b[0])
    return dict(op="in", args=[a, b])


def is_null(a: str | dict) -> dict:
    return dict(op="isNull", args=[a])


def plus(a: str | int | dict, b: str | dict) -> dict:
    return dict(op="+", args=[a, b])


def and_(items: list[dict]) -> dict:
    if len(items) == 1:
        return items[0]
    return dict(op="and", args=items)


def or_(items: list[dict]) -> dict:
    if len(items) == 1:
        return items[0]
    return dict(op="or", args=items)
