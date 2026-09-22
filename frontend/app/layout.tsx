import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "簡易POSアプリ",
  description: "簡易POSアプリ（Lv1+Lv2）",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
