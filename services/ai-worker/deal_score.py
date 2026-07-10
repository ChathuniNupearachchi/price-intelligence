import sys
import json
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://priceadmin:devpassword@localhost:5432/priceintel"
)

def score_product(product_id: str) -> dict:
    """Analyze a product's price history and return a deal assessment."""
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

    # If the product has no history, return a clear "not found" result.
    if df.empty:
        return {"product_id": product_id, "found": False}

    df["avg_price"] = df["avg_price"].astype(float)

    lowest  = df["avg_price"].min()
    highest = df["avg_price"].max()
    average = df["avg_price"].mean()
    latest  = df["avg_price"].iloc[-1]

    percentile_cheaper = round((df["avg_price"] > latest).mean() * 100, 1)

    if percentile_cheaper >= 70:
        verdict = "GREAT_DEAL"
    elif percentile_cheaper >= 40:
        verdict = "FAIR"
    else:
        verdict = "EXPENSIVE"

    # Return a structured dictionary (this becomes JSON for the API).
    return {
        "product_id": product_id,
        "found": True,
        "lowest": round(lowest, 2),
        "average": round(average, 2),
        "highest": round(highest, 2),
        "latest": round(latest, 2),
        "percentile_cheaper": percentile_cheaper,
        "verdict": verdict,
        "days_of_history": len(df),
    }


# When run directly, take the product id from the command line and print JSON.
if __name__ == "__main__":
    product = sys.argv[1] if len(sys.argv) > 1 else "85123A"
    result = score_product(product)
    print(json.dumps(result, indent=2))