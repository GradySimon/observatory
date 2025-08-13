import { create } from "zustand";
import { initDuckDB } from "@/lib/duckdb";
import { makeFakeArrowTable } from "@/lib/data";
import { AsyncDuckDBConnection } from "@duckdb/duckdb-wasm";

interface DuckDBState {
  status: "idle" | "starting" | "ready" | "error";
  error: string | null;
  conn: AsyncDuckDBConnection | null;
  start: () => Promise<void>;
  stop: () => Promise<void>;
  lastResult: unknown | null;
  loadData: () => Promise<void>;
}

export const useDuckDBStore = create<DuckDBState>((set, get) => ({
  status: "idle",
  error: null,
  conn: null,
  lastResult: null,
  start: async () => {
    if (get().status === "starting" || get().conn) return;
    set({ status: "starting", error: null });
    try {
      const { conn } = await initDuckDB();
      set({ conn, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
  stop: async () => {
    const { conn } = get();
    try {
      await conn?.close?.();
    } catch {}
    set({ conn: null, status: "idle", error: null });
  },
  loadData: async () => {
    const { conn } = get();
    if (!conn) return;
    // EOS sentinel required by DuckDB-WASM for Arrow batch streams
    const EOS = new Uint8Array([255, 255, 255, 255, 0, 0, 0, 0]);
    try {
      // Fresh name each run
      await conn.query("DROP TABLE IF EXISTS arrow_table;");
      const tbl = makeFakeArrowTable();
      await conn.insertArrowTable(tbl, { name: "arrow_table" });
      await conn.insertArrowTable(EOS, { name: "arrow_table" });
      const res = await conn.query(
        "SELECT COUNT(*) AS n, MIN(umap_x) AS mnx, MAX(umap_x) AS mxx FROM arrow_table;"
      );
      set({ lastResult: res.toArray() });
    } catch (e) {
      set({ error: String(e) });
    }
  },
}));
