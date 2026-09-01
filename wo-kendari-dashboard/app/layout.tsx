import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Sidebar from "@/components/Sidebar";
import { PresenceProvider } from "@/context/PresenceContext";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Ops Center — WO Kendari",
  description: "Dashboard kendali insiden operator",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="id" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="flex h-screen overflow-hidden bg-[var(--background)] font-sans">
        <PresenceProvider>
          <Sidebar />
          <div className="h-full flex-1 overflow-hidden">{children}</div>
        </PresenceProvider>
      </body>
    </html>
  );
}