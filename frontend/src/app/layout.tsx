import type { Metadata } from "next";
import { Space_Mono, Orbitron } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";

const spaceMono = Space_Mono({
  weight: ["400", "700"],
  subsets: ["latin"],
  variable: "--font-space-mono",
});

const orbitron = Orbitron({
  subsets: ["latin"],
  variable: "--font-orbitron",
});

export const metadata: Metadata = {
  title: "OmniSearch | Multimodal Product Discovery",
  description: "A Multimodal Retrieval and Ranking System for Cross-Modal E-Commerce Product Discovery. Search products using text, images, or both.",
  keywords: ["product search", "multimodal search", "e-commerce", "image search", "CLIP", "AI"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${spaceMono.variable} ${orbitron.variable} font-space-mono antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <div className="min-h-screen flex flex-col bg-white dark:bg-black text-black dark:text-white">
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
