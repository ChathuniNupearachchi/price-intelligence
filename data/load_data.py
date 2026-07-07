import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# --- 1. Connect to the database (same credentials as docker-compose.yml) ---
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="priceintel",
    user="priceadmin",
    password="devpassword",
)
cur = conn.cursor()

# --- 2. Read the CSV ---
# encoding="latin-1" because this dataset has non-UTF8 characters that would otherwise crash the read.
print("Reading CSV...")
df = pd.read_csv("raw/data.csv", encoding="latin-1")
print(f"Rows read: {len(df)}")

# --- 3. Clean the data ---
# Keep only the columns we care about, and rename them to match our table.
df = df[["StockCode", "Description", "UnitPrice", "InvoiceDate"]].copy()
df.columns = ["product_id", "product_name", "price", "recorded_at"]

# Drop rows missing a product id, price, or date.
df = df.dropna(subset=["product_id", "price", "recorded_at"])

# Keep only rows with a real, positive price (removes zeros and negatives/junk).
df = df[df["price"] > 0]

# Parse the date text into real timestamps; drop any that fail to parse.
df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce")
df = df.dropna(subset=["recorded_at"])

print(f"Rows after cleaning: {len(df)}")

# --- 4. Insert into the database in one efficient batch ---
print("Inserting into database...")
rows = list(df.itertuples(index=False, name=None))
execute_values(
    cur,
    "INSERT INTO price_history (product_id, product_name, price, recorded_at) VALUES %s",
    rows,
    page_size=1000,
)
conn.commit()
print(f"Done. Inserted {len(rows)} rows.")

# --- 5. Clean up ---
cur.close()
conn.close()