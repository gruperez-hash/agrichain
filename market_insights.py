from collections import defaultdict


def _to_float(value, default=0):
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _to_int(value, default=0):
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _product_key(product):
    name = (product.name or "").strip().lower()
    unit = (getattr(product, "unit", None) or "unit").strip().lower()
    return f"{name or f'product-{product.id}'}::{unit}"


def _demand_trend(order_count, units_sold):
    if order_count >= 5 or units_sold >= 5:
        return "High Demand"
    if order_count > 0:
        return "Active Demand"
    return "Low Demand"


def _market_action(demand_trend, total_stock):
    if demand_trend == "High Demand" and total_stock <= 10:
        return "Increase supply"
    if demand_trend == "High Demand":
        return "Maintain supply"
    if demand_trend == "Active Demand":
        return "Monitor pricing"
    if total_stock >= 20:
        return "Promote product"
    return "Collect more data"


def _market_reading(demand_trend, total_stock, listing_count, farmer_count):
    if demand_trend == "High Demand" and total_stock <= 10:
        return (
            "Demand is strong but available stock is tight. Farmers can benefit "
            "from adding supply while buyers should order early."
        )
    if demand_trend == "High Demand":
        return (
            "Demand is strong and supply is still present. This product is a good "
            "candidate for steady harvesting and close price monitoring."
        )
    if demand_trend == "Active Demand":
        return (
            "Orders are starting to move. Watch whether new listings increase "
            "competition or confirm stronger demand."
        )
    if listing_count <= 1 or farmer_count <= 1:
        return (
            "Market signal is still thin because there are few comparable listings."
        )
    if total_stock >= 20:
        return (
            "Supply is available but buyer demand is still low. Promotion or price "
            "review may help move stock."
        )
    return "More product and order records are needed for a stronger market signal."


def _market_next_step(demand_trend, total_stock):
    if demand_trend == "High Demand" and total_stock <= 10:
        return "Farmers: increase supply. Buyers: reserve stock before it runs out."
    if demand_trend == "High Demand":
        return "Maintain supply and review price only after new orders come in."
    if demand_trend == "Active Demand":
        return "Monitor price changes and watch the next few orders."
    if total_stock >= 20:
        return "Improve product visibility or consider a competitive price."
    return "Collect more listings and transaction data."


def build_market_rows(products, orders):
    orders_by_product = defaultdict(list)
    for order in orders:
        orders_by_product[order.product_id].append(order)

    groups = {}
    for product in products:
        key = _product_key(product)
        if key not in groups:
            groups[key] = {
                "key": key,
                "name": product.name or "Unnamed Product",
                "unit": product.unit or "unit",
                "prices": [],
                "total_stock": 0,
                "listing_count": 0,
                "farmer_count": set(),
                "order_count": 0,
                "units_sold": 0,
                "approved_revenue": 0
            }

        group = groups[key]
        group["prices"].append(_to_float(product.price))
        group["total_stock"] += _to_int(product.quantity)
        group["listing_count"] += 1

        if product.farmer:
            group["farmer_count"].add(product.farmer_id)

        for order in orders_by_product.get(product.id, []):
            status = (order.status or "").lower()
            if status in {"cancelled", "rejected"}:
                continue

            group["order_count"] += 1
            if status == "approved":
                group["units_sold"] += _to_int(order.quantity)
                group["approved_revenue"] += _to_float(order.total_price)

    market_rows = []
    for group in groups.values():
        prices = group["prices"]
        avg_price = sum(prices) / len(prices) if prices else 0
        demand_trend = _demand_trend(group["order_count"], group["units_sold"])
        farmer_count = len(group["farmer_count"])
        market_action = _market_action(demand_trend, group["total_stock"])

        market_rows.append({
            "key": group["key"],
            "name": group["name"],
            "unit": group["unit"],
            "avg_price": avg_price,
            "min_price": min(prices) if prices else 0,
            "max_price": max(prices) if prices else 0,
            "total_stock": group["total_stock"],
            "listing_count": group["listing_count"],
            "farmer_count": farmer_count,
            "order_count": group["order_count"],
            "units_sold": group["units_sold"],
            "approved_revenue": group["approved_revenue"],
            "demand_trend": demand_trend,
            "market_action": market_action,
            "ai_reading": _market_reading(
                demand_trend,
                group["total_stock"],
                group["listing_count"],
                farmer_count
            ),
            "next_step": _market_next_step(demand_trend, group["total_stock"])
        })

    return sorted(
        market_rows,
        key=lambda row: (-row["units_sold"], -row["order_count"], row["name"].lower())
    )


def build_market_summary(market_rows):
    if not market_rows:
        return {
            "product_types": 0,
            "total_stock": 0,
            "total_orders": 0,
            "total_units_sold": 0,
            "average_market_price": 0,
            "high_demand_count": 0
        }

    return {
        "product_types": len(market_rows),
        "total_stock": sum(row["total_stock"] for row in market_rows),
        "total_orders": sum(row["order_count"] for row in market_rows),
        "total_units_sold": sum(row["units_sold"] for row in market_rows),
        "average_market_price": (
            sum(row["avg_price"] for row in market_rows) / len(market_rows)
        ),
        "high_demand_count": sum(
            1 for row in market_rows if row["demand_trend"] == "High Demand"
        )
    }


def build_price_insights(products, market_rows):
    rows_by_key = {row["key"]: row for row in market_rows}
    insights = {}

    for product in products:
        row = rows_by_key.get(_product_key(product))
        current_price = _to_float(product.price)

        if not row or row["listing_count"] < 2 or row["avg_price"] <= 0:
            insights[product.id] = {
                "status": "No comparison yet",
                "avg_price": row["avg_price"] if row else 0,
                "difference": 0,
                "suggestion": "Collect more market data",
                "detail": "Price guidance will improve after more similar listings appear.",
                "next_step": "Keep product details updated so future comparisons are accurate."
            }
            continue

        avg_price = row["avg_price"]
        difference = ((current_price - avg_price) / avg_price) * 100

        if current_price > avg_price * 1.15:
            status = "Above Market"
            suggestion = "Review price"
            detail = f"Your price is {abs(difference):.1f}% above the market average."
            next_step = "Consider a modest reduction or add value through quality and delivery notes."
        elif current_price < avg_price * 0.85:
            status = "Below Market"
            suggestion = "Possible price increase"
            detail = f"Your price is {abs(difference):.1f}% below the market average."
            next_step = "If orders stay active, test a small price increase."
        else:
            status = "Fair Price"
            suggestion = "Keep current price"
            detail = "Your price is close to the current market average."
            next_step = "Maintain price and monitor demand before changing it."

        insights[product.id] = {
            "status": status,
            "avg_price": avg_price,
            "difference": difference,
            "suggestion": suggestion,
            "detail": detail,
            "next_step": next_step
        }

    return insights
