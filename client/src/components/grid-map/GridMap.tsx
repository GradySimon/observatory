"use client";

import { useEffect, useMemo, useState } from "react";
import { useDuckDBStore } from "@/app/store";

type RGB = [number, number, number];

const PALETTE: RGB[] = [
  [230, 57, 70],
  [29, 53, 87],
  [69, 123, 157],
  [241, 196, 15],
];

function mixSRGB(counts: number[], total: number): RGB {
  if (!total) return [255, 255, 255];
  let r = 0,
    g = 0,
    b = 0;
  for (let k = 0; k < Math.min(counts.length, PALETTE.length); k++) {
    const w = counts[k] / total;
    r += PALETTE[k][0] * w;
    g += PALETTE[k][1] * w;
    b += PALETTE[k][2] * w;
  }
  return [Math.round(r), Math.round(g), Math.round(b)];
}

function rgbToCss([r, g, b]: RGB) {
  return `rgb(${r}, ${g}, ${b})`;
}

export default function GridMap() {
  const { status, conn, lastResult } = useDuckDBStore();
  const [phase, setPhase] = useState("waiting for data…");
  const [cells, setCells] = useState<string[] | null>(null);

  // modest grid for React-div rendering
  const W = 32,
    H = 32;

  useEffect(() => {
    (async () => {
      if (!conn || status !== "ready") return;
      if (!lastResult) {
        setPhase("waiting for data…");
        return;
      }

      setPhase("computing extents…");
      const t = await conn.query(`
        SELECT
          MIN(umap_x) AS xmin, MAX(umap_x) AS xmax,
          MIN(umap_y) AS ymin, MAX(umap_y) AS ymax
        FROM arrow_table;
      `);
      const b = t.toArray()[0] as {
        xmin: number;
        xmax: number;
        ymin: number;
        ymax: number;
      };
      const { xmin, xmax, ymin, ymax } = b;

      setPhase("binning…");
      const sql = `
        WITH binned AS (
          SELECT
            CAST(FLOOR((umap_x - ${xmin}) / NULLIF(${xmax} - ${xmin}, 0) * ${W}) AS INTEGER) AS ix,
            CAST(FLOOR((umap_y - ${ymin}) / NULLIF(${ymax} - ${ymin}, 0) * ${H}) AS INTEGER) AS iy,
            cat_id
          FROM arrow_table
          WHERE ${xmax} > ${xmin} AND ${ymax} > ${ymin}
            AND umap_x BETWEEN ${xmin} AND ${xmax}
            AND umap_y BETWEEN ${ymin} AND ${ymax}
        ),
        agg AS (
          SELECT ix, iy, cat_id, COUNT(*) AS n
          FROM binned
          WHERE ix BETWEEN 0 AND ${W - 1} AND iy BETWEEN 0 AND ${H - 1}
          GROUP BY 1,2,3
        )
        SELECT ix, iy, cat_id, n,
               SUM(n) OVER (PARTITION BY ix, iy) AS n_total
        FROM agg
        ORDER BY iy, ix, cat_id;
      `;
      const result = await conn.query(sql);

      // accumulate into per-cell counts and totals
      const rows = result.toArray() as Array<{
        ix: number;
        iy: number;
        cat_id: number;
        n: any;
        n_total: any;
      }>;
      const totals = new Uint32Array(W * H);
      const counts = new Uint32Array(W * H * 4);
      let maxTot = 0;
      for (const r of rows) {
        const ix = r.ix;
        const iy = r.iy;
        const cat = r.cat_id;
        const n = Number(r.n);
        const nTot = Number(r.n_total);
        const idx = iy * W + ix;
        totals[idx] = nTot;
        counts[idx * 4 + cat] += n;
        if (nTot > maxTot) maxTot = nTot;
      }

      const out: string[] = new Array(W * H).fill("rgba(0,0,0,0)");
      for (let i = 0; i < W * H; i++) {
        const tot = totals[i];
        if (tot === 0) {
          out[i] = "transparent";
          continue;
        }
        const mix = mixSRGB(
          [
            counts[i * 4],
            counts[i * 4 + 1],
            counts[i * 4 + 2],
            counts[i * 4 + 3],
          ],
          tot
        );
        const shade = 0.15 + 0.85 * Math.sqrt(tot / (maxTot || 1));
        const col = rgbToCss([
          Math.min(255, Math.round(mix[0] * shade)),
          Math.min(255, Math.round(mix[1] * shade)),
          Math.min(255, Math.round(mix[2] * shade)),
        ]);
        out[i] = col;
      }

      setCells(out);
      setPhase("done");
    })();
  }, [conn, status, lastResult]);

  const gridStyle = useMemo<React.CSSProperties>(
    () => ({
      display: "grid",
      gridTemplateColumns: `repeat(${W}, 1fr)`,
      gridTemplateRows: `repeat(${H}, 1fr)`,
      width: 640,
      height: 640,
      imageRendering: "pixelated",
      border: "1px solid #ddd",
      background: "#fff",
    }),
    []
  );

  return (
    <div style={{ padding: 16, fontFamily: "system-ui, sans-serif" }}>
      <div style={{ marginBottom: 8 }}>{phase}</div>
      <div style={gridStyle}>
        {cells?.map((bg, i) => (
          <div key={i} style={{ backgroundColor: bg }} />
        ))}
      </div>
      <div style={{ marginTop: 8, display: "flex", gap: 12 }}>
        {[0, 1, 2, 3].map((k) => (
          <div
            key={k}
            style={{ display: "flex", alignItems: "center", gap: 6 }}
          >
            <div
              style={{
                width: 14,
                height: 14,
                backgroundColor: rgbToCss(PALETTE[k]),
              }}
            />
            <span style={{ fontSize: 12 }}>cat {k}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
