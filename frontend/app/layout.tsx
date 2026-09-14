import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AkmMotion — AI Script-to-Video Platform",
  description: "Transform your scripts into stunning 1080x1920 YouTube Shorts, TikToks, and Reels powered by AI.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0C0D0E] text-white antialiased">
        {children}
      </body>
    </html>
  );
}
