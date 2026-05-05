import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Vital Conversations",
  description: "Interface conversationnelle pour l'orchestrateur Vital"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
