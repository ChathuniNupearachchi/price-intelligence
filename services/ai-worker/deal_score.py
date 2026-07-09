import pandas as pd
from sqlalchemy import create_engine

# --- 1. Connect to the database ---
# SQLAlchemy uses a connection "URL" in this format:
# postgresql://user:password@host:port/database
engine = create_engine(
    "postgresql://priceadmin:devpassword@localhost:5432/priceintel"
)

# The product we're analyzing (hard-coded for now, like the chart).
product_id = "85123A"

# --- 2. Pull this product's DAILY average prices into a pandas DataFrame ---
# We reuse the same time_bucket aggregation from Part A.
# A "DataFrame" is pandas' core object: a table with rows and columns, like a spreadsheet in code.
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

# Convert avg_price to a plain float number (it comes back as a Decimal/string type).
df["avg_price"] = df["avg_price"].astype(float)

print(f"Loaded {len(df)} days of price history for {product_id}")

# --- 3. Compute the core statistics ---
# These pandas methods each summarize the whole 'avg_price' column into one number.
lowest  = df["avg_price"].min()     # cheapest day ever
highest = df["avg_price"].max()     # most expensive day ever
average = df["avg_price"].mean()    # typical price
latest  = df["avg_price"].iloc[-1]  # the most recent day's price (.iloc[-1] = last row)

# --- 4. Compute the percentile of the latest price ---
# "What fraction of historical prices are ABOVE the latest price?"
# If most history is more expensive, the latest price is a good deal.
cheaper_share = (df["avg_price"] > latest).mean()  # mean() of True/False = fraction that are True
percentile_cheaper = round(cheaper_share * 100, 1)

# --- 5. Turn the numbers into a plain-English verdict ---
if percentile_cheaper >= 70:
    verdict = "GREAT DEAL - buy now"
elif percentile_cheaper >= 40:
    verdict = "FAIR PRICE"
else:
    verdict = "EXPENSIVE - consider waiting"

# --- 6. Show the result ---
print("-" * 40)
print(f"Product:            {product_id}")
print(f"Lowest ever:        {lowest:.2f}")
print(f"Average:            {average:.2f}")
print(f"Highest ever:       {highest:.2f}")
print(f"Latest price:       {latest:.2f}")
print(f"Cheaper than {percentile_cheaper}% of history")
print(f"VERDICT:            {verdict}")
print("-" * 40)