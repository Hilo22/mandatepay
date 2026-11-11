import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MandatePay | Programmable Financial Guardrails & Netting Protocol",
  description:
    "Autonomous financial protocol for Agentic Commerce: Natural Language Mandates, Deterministic Prompt Injection Shield, Contract Assertions & PayPal Batch Net Settlement.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#060b16] text-slate-100 antialiased selection:bg-sky-500/30 selection:text-sky-200">
        {children}
      </body>
    </html>
  );
}

