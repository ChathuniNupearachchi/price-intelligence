import express from "express";
import cors from "cors";
import { Pool } from "pg";
import { exec } from "child_process";
import path from "path";


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

// Daily average price history for one product (clean, aggregated).
// Example: GET /api/products/85123A/daily
app.get("/api/products/:productId/daily", async (req, res) => {
  const { productId } = req.params;
  try {
    const result = await pool.query(
      `SELECT
         time_bucket('1 day', recorded_at) AS day,
         AVG(price)::NUMERIC(10,2) AS avg_price
       FROM price_history
       WHERE product_id = $1
       GROUP BY day
       ORDER BY day ASC`,
      [productId]
    );
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Database query failed" });
  }
});

// AI forecast for one product — runs the Python Prophet script.
// Example: GET /api/products/85123A/forecast
app.get("/api/products/:productId/forecast", (req, res) => {
  const { productId } = req.params;

  // Basic safety: only allow simple alphanumeric product IDs,
  // so nothing dangerous can be passed into the command.
  if (!/^[A-Za-z0-9]+$/.test(productId)) {
    return res.status(400).json({ error: "Invalid product ID" });
  }

  // Build the path to the Python script and its venv Python executable.
  const aiWorkerDir = path.join(__dirname, "..", "..", "ai-worker");
  const pythonExe = path.join(aiWorkerDir, "venv", "Scripts", "python.exe");
  const script = path.join(aiWorkerDir, "forecast_prophet.py");

  // Run: python forecast_prophet.py <productId>
  exec(`"${pythonExe}" "${script}" ${productId}`, (error, stdout, stderr) => {
    if (error) {
      console.error("Forecast script error:", stderr);
      return res.status(500).json({ error: "Forecast failed" });
    }
    try {
      // The script prints JSON; parse it and send it on.
      const result = JSON.parse(stdout);
      res.json(result);
    } catch (e) {
      console.error("Could not parse forecast output:", stdout);
      res.status(500).json({ error: "Invalid forecast output" });
    }
  });
});

const PORT = 4000;
app.listen(PORT, () => {
  console.log(`API running on http://localhost:${PORT}`);
});