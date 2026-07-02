import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "PliegoCheck-SECOP",
  description:
    "Plataforma multiagente de análisis GO / NO GO para procesos de contratación pública en SECOP II. Fundación técnica: aún sin análisis funcional de procesos.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
