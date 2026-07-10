import sys
import json
import pandas as pd
from prophet import Prophet
from sqlalchemy import create_engine
import logging

# Prophet is very chatty in the terminal; quiet its logs so our output stays clean.
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

engine = create_engine(
    "postgresql://priceadmin:devpassword@localhost:5432/priceintel"
)

def forecast_with_prophet(product_id: str, days_ahead: int = 7) -> dict:
    """Predict a product's future price using Facebook Prophet."""

    # --- 1. Pull daily average prices (same as before) ---
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

    # --- 2. Fill gaps into a clean daily series (as before) ---
    df = df.set_index("day")
    df = df.resample("D").ffill()
    df = df.reset_index()

    # --- 3. Rename columns to what Prophet REQUIRES ---
    # Prophet demands exactly two columns: 'ds' (the date) and 'y' (the value).
    prophet_df = df.rename(columns={"day": "ds", "avg_price": "y"})

    # Prophet's date column must be timezone-naive; strip any timezone.
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(None)

    # --- 4. Create and train the Prophet model ---
    # weekly_seasonality=True lets it learn day-of-week cycles.
    # yearly_seasonality is left auto (Prophet decides if there's enough data).
    model = Prophet(weekly_seasonality=True, daily_seasonality=False)
    model.fit(prophet_df)          # <-- Prophet learns trend + seasonality here

    # --- 5. Build a future dataframe and predict ---
    # make_future_dataframe extends the dates by `days_ahead` days.
    future = model.make_future_dataframe(periods=days_ahead)
    forecast = model.predict(future)

    # forecast has many columns; 'yhat' is the predicted value.
    latest_price = round(prophet_df["y"].iloc[-1], 2)
    predicted_price = round(float(forecast["yhat"].iloc[-1]), 2)  # last future day

    # Prophet also gives an uncertainty range: yhat_lower / yhat_upper.
    predicted_low = round(float(forecast["yhat_lower"].iloc[-1]), 2)
    predicted_high = round(float(forecast["yhat_upper"].iloc[-1]), 2)

    if predicted_price < latest_price:
        advice = "WAIT - price likely to drop"
    else:
        advice = "BUY - price likely to rise"

    return {
        "product_id": product_id,
        "found": True,
        "model": "prophet",
        "latest_price": latest_price,
        "predicted_price_in_days": predicted_price,
        "predicted_range": [predicted_low, predicted_high],
        "days_ahead": days_ahead,
        "advice": advice,
    }


if __name__ == "__main__":
    product = sys.argv[1] if len(sys.argv) > 1 else "85123A"
    result = forecast_with_prophet(product)
    print(json.dumps(result, indent=2))