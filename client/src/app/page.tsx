"use client";

import { useEffect, useState } from "react";
import { useDuckDBStore } from "./store";

const EOS = new Uint8Array([255, 255, 255, 255, 0, 0, 0, 0]);

export default function Home() {
  const [result, setResult] = useState<string>("initializing…");

  const { status, conn, start, error, lastResult, loadData } = useDuckDBStore();

  useEffect(() => {
    start();
  }, [start]);

  useEffect(() => {
    (async () => {
      if (!conn || status !== "ready") return;
      setResult("duckdb ready; inserting Arrow…");
      await loadData();
    })();
  }, [conn, status, loadData]);

  return (
    <div style={{ padding: 16, fontFamily: "system-ui, sans-serif" }}>
      <h1>DuckDB-WASM minimal test</h1>
      <div>Status: {status}</div>
      {error && <div style={{ color: "red" }}>{error}</div>}
      <pre
        style={{
          whiteSpace: "pre-wrap",
          background: "#f6f8fa",
          padding: 12,
          borderRadius: 6,
          border: "1px solid #eaecef",
        }}
      >
        {lastResult
          ? JSON.stringify(lastResult, (_, v) =>
              typeof v === "bigint" ? v.toString() : v
            )
          : result}
      </pre>
    </div>
  );
}
