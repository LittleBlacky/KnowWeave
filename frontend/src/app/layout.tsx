import type { Metadata } from "next";
import { MockProvider } from "./MockProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "KnowWeave",
  description: "Evidence-governed knowledge workbench",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>
        <MockProvider>{children}</MockProvider>
      </body>
    </html>
  );
}
