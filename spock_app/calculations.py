def calculate_pnl(trade):
    if trade["type"] == "buy":
        current_value = trade["current_price"] * trade["quantity"]
        cost = trade["price"] * trade["quantity"]
        pnl = current_value - cost
        pnl_percent = (pnl / cost) * 100 if cost != 0 else 0
    elif trade["type"] == "sell":
        cost = trade["price"] * trade["quantity"]
        current_value = trade["current_price"] * trade["quantity"]
        pnl = cost - current_value
        pnl_percent = (pnl / cost) * 100 if cost != 0 else 0
    else:
        pnl, pnl_percent = 0, 0

    return {"pnl": pnl, "pnl_percent": pnl_percent}
