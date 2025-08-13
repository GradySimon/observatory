"use client";

import { useEffect, useState } from "react";
import { initDuckDB } from "@/lib/duckdb";
import { makeFakeArrowTable } from "@/lib/data";

const EOS = new Uint8Array([255, 255, 255, 255, 0, 0, 0, 0]);

export default function Home() {
  const [result, setResult] = useState<string>("initializing…");

  useEffect(() => {
    (async () => {
      try {
        setResult("starting duckdb…");
        const { conn } = await initDuckDB();
        const tbl = makeFakeArrowTable();
        console.log(`tbl: ${tbl}`);
        await conn.insertArrowTable(tbl, { name: "arrow_table" });
        await conn.insertArrowTable(EOS, { name: "arrow_table" });
        const res = await conn.query("SELECT * FROM arrow_table LIMIT 1");
        const row = res.toArray();
        setResult(JSON.stringify(row));
      } catch (e) {
        setResult(String(e));
      }
    })();
  }, []);

  return (
    <div style={{ padding: 16, fontFamily: "system-ui, sans-serif" }}>
      <h1>DuckDB-WASM minimal test</h1>
      <pre
        style={{
          whiteSpace: "pre-wrap",
          background: "#f6f8fa",
          padding: 12,
          borderRadius: 6,
          border: "1px solid #eaecef",
        }}
      >
        {result}
      </pre>
    </div>
  );
}
