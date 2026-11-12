import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GetWay — vos vidéos, simplement",
  description: "Récupérez vos vidéos et contenus audio autorisés avec GetWay.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
