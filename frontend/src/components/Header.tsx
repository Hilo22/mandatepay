"use client";

import React from "react";
import { ShieldCheck, Wifi, WifiOff, Layers, Lock } from "lucide-react";

interface HeaderProps {
  streamConnected: boolean;
  mandateStatus?: string;
}

export default function Header({
  streamConnected,
  mandateStatus,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-[#070d1b]/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-[1600px] items-center justify-between px-6 py-3.5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-blue-700 shadow-lg shadow-sky-600/25">
            <ShieldCheck className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <span className="text-lg font-bold tracking-tight text-white">
                Mandate<span className="text-sky-400">Pay</span>
              </span>
              <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-sky-300">
                Agentic Escrow &amp; Netting Protocol
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Deterministic Financial Guardrails &bull; Contract Assertions &bull; PayPal Batch Settlement
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-1.5 text-xs text-slate-300 md:flex">
            <Lock className="h-3.5 w-3.5 text-emerald-400" />
            <span>Prompt Shield:</span>
            <span className="font-mono font-semibold text-emerald-400">
              &lt;1ms Deterministic
            </span>
          </div>

          <div className="hidden items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-1.5 text-xs text-slate-300 md:flex">
            <Layers className="h-3.5 w-3.5 text-amber-400" />
            <span>PayPal Sandbox:</span>
            <span className="font-mono font-semibold text-amber-300">
              REST v1/v2 Ready
            </span>
          </div>

          {mandateStatus && (
            <div
              className={`rounded-lg border px-3 py-1.5 text-xs font-semibold tracking-wide ${
                mandateStatus === "ACTIVE"
                  ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-300"
                  : mandateStatus === "AWAITING_PAYMENT"
                  ? "border-amber-500/40 bg-amber-500/15 text-amber-300"
                  : "border-red-500/40 bg-red-500/15 text-red-300"
              }`}
            >
              MANDATE: {mandateStatus}
            </div>
          )}

          <div
            className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium ${
              streamConnected
                ? "border-emerald-500/30 bg-emerald-950/50 text-emerald-300"
                : "border-slate-700 bg-slate-900 text-slate-400"
            }`}
          >
            {streamConnected ? (
              <>
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                </span>
                <Wifi className="h-3.5 w-3.5" />
                <span>SSE Live</span>
              </>
            ) : (
              <>
                <WifiOff className="h-3.5 w-3.5 text-slate-500" />
                <span>Reconnecting</span>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

