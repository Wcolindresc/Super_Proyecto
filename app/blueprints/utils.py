def to_int(x):
    try:
        return int(x) if x is not None else None
    except Exception:
        return None
