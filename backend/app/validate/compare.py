from decimal import Decimal


def same_money(a, b):
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except Exception:
        return False


def items_match(a, b):
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x["description"] != y["description"]:
            return False
        for k in ("quantity", "unit_price", "total"):
            if not same_money(x[k], y[k]):
                return False
    return True