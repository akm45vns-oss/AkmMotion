import type { Metadata } from "next";
import "./globals.css";
import AuthSessionWatcher from "@/components/auth/AuthSessionWatcher";

export const metadata: Metadata = {
  title: "AkmMotion — AI Script-to-Video Platform",
  description: "Transform your scripts into stunning 1080x1920 YouTube Shorts, TikToks, and Reels powered by AI.",
  icons: {
    icon: "/logo-icon.png",
    apple: "/logo-icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0D0E0E] text-[#F5F1E8] antialiased">
        <AuthSessionWatcher />
        {children}
      </body>
    </html>
  );
}
