import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist" });

export const metadata: Metadata = {
  title: "Unstructured Alpha — Macro Signals for Active Investors",
  description:
    "Institutional-grade macro signals — insider flows, credit spreads, energy positioning, Fed indicators — in one dashboard. Built for investors who want to see what the macro is doing before the move.",
  openGraph: {
    title: "Unstructured Alpha",
    description: "Macro signals. Before the move.",
    siteName: "Unstructured Alpha",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={geist.variable}>
      <body>{children}</body>
    </html>
  );
}
