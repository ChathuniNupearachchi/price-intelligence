import express from "express";
import cors from "cors";
import { Pool } from "pg";

const app = express();
app.use(cors());          // allow the browser frontend to call us
app.use(express.json());  // parse JSON request bodies

// Connection pool to Postgres (same credentials as docker-compose.yml).
// A "pool" reuses a set of connections instead of opening one per request — efficient and standard.
const pool = new Pool({
  host: "localhost",
  port: 5432,
  database: "priceintel",
  user: "priceadmin",
  password: "devpassword",
});

// A simple health-check endpoint — visiting this confirms the API is alive.
app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

// The real endpoint: price history for one product.
// Example: GET /api/products/85123A/history
app.get("/api/products/:productId/history", async (req, res) => {
  const { productId } = req.params;
  try {
    const result = await pool.query(
      `SELECT recorded_at, price
       FROM price_history
       WHERE product_id = $1
       ORDER BY recorded_at ASC`,
      [productId]   // $1 is safely replaced with productId — prevents SQL injection
    );
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Database query failed" });
  }
});

const PORT = 4000;
app.listen(PORT, () => {
  console.log(`API running on http://localhost:${PORT}`);
});