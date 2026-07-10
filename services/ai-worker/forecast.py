import sys
import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://priceadmin:devpassword@localhost:5432/priceintel"
)

def forecast_product(product_id: str, days_ahead: int = 7) -> dict:
    """Predict a product's price for the next `days_ahead` days."""

    # --- 1. Pull daily average prices (same aggregation as before) ---
    query = """
        SELECT
            time_bucket('1 day', recorded_at) AS day,
            AVG(price)::NUMERIC(10,2) AS avg_price
        FROM price_history
        WHERE product_id = %(product_id)s
        GROUP BY day
        ORDER BY day ASC
    """
    df = pd.read_sql(query, engine, params={"product_id": product_id})
    if df.empty:
        return {"product_id": product_id, "found": False}

    df["avg_price"] = df["avg_price"].astype(float)

    # --- 2. Fix the gaps: make one row per day, forward-fill missing days ---
    # Set the date as the index, then resample to daily ('D'), filling gaps
    # with the last known price (ffill) — because a price persists until it changes.
    df = df.set_index("day")
    df = df.resample("D").ffill()      # now every calendar day has a price
    df = df.reset_index()

    # --- 3. Prepare data for the model ---
    # ML models work with numbers, not dates. So we turn each date into a simple
    # "day number": 0, 1, 2, 3... counting from the first day.
    df["day_number"] = range(len(df))

    # X = the input (day number), y = the output we want to predict (price).
    # scikit-learn expects X as a 2D shape, hence the [[...]] / reshape.
    X = df[["day_number"]]        # input feature
    y = df["avg_price"]           # target

    # --- 4. Train the model ---
    # LinearRegression learns the best straight line through the price history:
    # essentially "on average, is the price trending up or down over time?"
    model = LinearRegression()
    model.fit(X, y)               # <-- this is the "learning" step

    # --- 5. Predict future days ---
    last_day = df["day_number"].iloc[-1]
    future_day_numbers = pd.DataFrame(
    {"day_number": [last_day + i for i in range(1, days_ahead + 1)]}
    )
    predictions = model.predict(future_day_numbers)

    latest_price = round(df["avg_price"].iloc[-1], 2)
    predicted_price = round(float(predictions[-1]), 2)  # price `days_ahead` from now

    # The slope tells us the direction: positive = rising, negative = falling.
    trend = "rising" if model.coef_[0] > 0 else "falling"

    # A simple recommendation from the forecast.
    if predicted_price < latest_price:
        advice = "WAIT - price likely to drop"
    else:
        advice = "BUY - price likely to rise"

    return {
        "product_id": product_id,
        "found": True,
        "latest_price": latest_price,
        "predicted_price_in_days": predicted_price,
        "days_ahead": days_ahead,
        "trend": trend,
        "advice": advice,
    }


if __name__ == "__main__":
    product = sys.argv[1] if len(sys.argv) > 1 else "85123A"
    result = forecast_product(product)
    print(json.dumps(result, indent=2))