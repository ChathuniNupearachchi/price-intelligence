import { useEffect, useState } from "react";
import axios from "axios";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
} from "recharts";

type PricePoint = {
  day: string;
  avg_price: string;
};

function App() {
  const [data, setData] = useState<PricePoint[]>([]);
  const [loading, setLoading] = useState(true);

  const productId = "85123A";

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

  if (loading) return <p style={{ padding: 20 }}>Loading price history...</p>;

  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <h1>Price History</h1>
      <h2>Product: {productId}</h2>
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