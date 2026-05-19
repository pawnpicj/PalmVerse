import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "PalmVerse",
  description: "Interactive palmistry scan MVP",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="th">
      <body>{children}</body>
    </html>
  );
}
