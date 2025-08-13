import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DuckDB-WASM minimal",
  description: "Single expression query test",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
