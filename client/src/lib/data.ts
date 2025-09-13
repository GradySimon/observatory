import { tableFromArrays, type Table } from "apache-arrow";

// Simple Box–Muller for N(0,1)
function randn(): number {
  let u = 0;
  let v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

export function makeFakeArrowTable(N = 200_000, K = 4): Table {
  const umap_x = new Float32Array(N);
  const umap_y = new Float32Array(N);
  const cat_id = new Uint8Array(N);

  const centers: [number, number][] = [
    [-6, -4],
    [6, -4],
    [-6, 5],
    [6, 5],
  ];
  const sigma = 0.9;

  for (let i = 0; i < N; i++) {
    const c = i % K;
    cat_id[i] = c as 0 | 1 | 2 | 3;
    const [cx, cy] = centers[c];
    umap_x[i] = cx + sigma * randn();
    umap_y[i] = cy + sigma * randn();
  }

  return tableFromArrays({ umap_x, umap_y, cat_id });
}
