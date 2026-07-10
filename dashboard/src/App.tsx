import { useEffect, useState } from "react";
import axios from "axios";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
} from "recharts";

type PricePoint = {
  day: string;
  avg_price: string;
};

// The shape of the forecast the API returns.
type Forecast = {
  found: boolean;
  latest_price: number;
  predicted_price_in_days: number;
  predicted_range: [number, number];
  days_ahead: number;
  advice: string;
};

function App() {
  const [data, setData] = useState<PricePoint[]>([]);
  const [loading, setLoading] = useState(true);

  // New: forecast state, and a separate loading flag for it (it's slow).
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [forecastLoading, setForecastLoading] = useState(true);

  const productId = "85123A";

  // Fetch the price history (fast).
  useEffect(() => {
    axios
      .get(`http://localhost:4000/api/products/${productId}/daily`)
      .then((res) => {
        const cleaned = res.data.map((point: PricePoint) => ({
          date: new Date(point.day).toLocaleDateString(),
          price: parseFloat(point.avg_price),
        }));
        setData(cleaned);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load data:", err);
        setLoading(false);
      });
  }, []);

  // Fetch the AI forecast (slow — separate call so the chart isn't blocked).
  useEffect(() => {
    axios
      .get(`http://localhost:4000/api/products/${productId}/forecast`)
      .then((res) => {
        setForecast(res.data);
        setForecastLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load forecast:", err);
        setForecastLoading(false);
      });
  }, []);

  if (loading) return <p style={{ padding: 20 }}>Loading price history...</p>;

  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <h1>Price History</h1>
      <h2>Product: {productId}</h2>

      {/* AI Forecast panel */}
      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 16,
          marginBottom: 20,
          background: "#f9f9f9",
          maxWidth: 500,
        }}
      >
        <h3 style={{ marginTop: 0 }}>AI Price Forecast</h3>
        {forecastLoading ? (
          <p>Analyzing price patterns...</p>
        ) : forecast && forecast.found ? (
          <div>
            <p>Current price: <strong>{forecast.latest_price}</strong></p>
            <p>
              Predicted in {forecast.days_ahead} days:{" "}
              <strong>{forecast.predicted_price_in_days}</strong>{" "}
              (range {forecast.predicted_range[0]}–{forecast.predicted_range[1]})
            </p>
            <p style={{
              fontWeight: "bold",
              color: forecast.advice.startsWith("WAIT") ? "#c0392b" : "#27ae60",
            }}>
              {forecast.advice}
            </p>
          </div>
        ) : (
          <p>No forecast available.</p>
        )}
      </div>

      {/* Price history chart */}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="price" stroke="#8884d8" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default App;