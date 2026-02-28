def _fmt(label, val):
    if label in ("Revenue",):  return f"€{val:,.0f}"
    if label == "CR":           return f"{val:.2%}"
    if label == "AOV":          return f"€{val:.2f}"
    return f"{val:,.0f}"


def color_neg(val):
    if isinstance(val, (int, float)) and val < 0:
        return "color: red; font-weight: bold"
    return "color: green"
