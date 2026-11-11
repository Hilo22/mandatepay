"use client";

import React from "react";
import {
  Wallet,
  ShieldCheck,
  GitMerge,
  Zap,
  ArrowRight,
} from "lucide-react";
import { Mandate, NettingSummary, Transaction } from "@/lib/api-client";
import { formatUSD } from "@/lib/utils";

interface BudgetOverviewProps {
  mandate: Mandate | null;
  transactions: Transaction[];
  nettingSummary: NettingSummary | null;
}

export default function BudgetOverview({
  mandate,
  transactions,
  nettingSummary,
}: BudgetOverviewProps) {
  const totalLimit = mandate?.totalBudgetLimit || 30.0;
  const currentSpent = mandate?.currentSpent || 0.0;
  const pct = Math.min(100, Math.round((currentSpent / totalLimit) * 100));

  const blockedInjections = transactions.filter(
    (t) => t.status === "BLOCKED_INJECTION"
  ).length;
  const blockedPolicyOrAssertions = transactions.filter(
    (t) =>
      t.status === "BLOCKED_POLICY" || t.status === "BLOCKED_ASSERTION_FAILED"
  ).length;
  const totalBlockedAmount = transactions
    .filter((t) => t.status.startsWith("BLOCKED_"))
    .reduce((acc, t) => acc + t.amount, 0);

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {/* Card 1: Real-time Escrow Budget Progress */}
      <div className="rounded-2xl border border-slate-800/90 bg-[#0b1222] p-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <Wallet className="h-4 w-4 text-sky-400" />
            <span>Mandate Operating Credit Line</span>
          </div>
          <span className="font-mono text-xs font-bold text-sky-300">
            {pct}% Utilized
          </span>
        </div>

        <div className="mt-2.5 flex items-baseline justify-between">
          <div className="text-2xl font-bold text-white">
            {formatUSD(currentSpent)}{" "}
            <span className="text-sm font-normal text-slate-400">
              / {formatUSD(totalLimit)}
            </span>
          </div>
          <span className="text-xs text-slate-400">
            Max/Txn:{" "}
            <strong className="text-slate-200">
              {formatUSD(mandate?.maxChargePerTxn || 3.0)}
            </strong>
          </span>
        </div>

        <div className="mt-3 h-2.5 w-full overflow-hidden rounded-full bg-slate-900">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              pct >= 90
                ? "bg-gradient-to-r from-amber-500 to-red-500"
                : "bg-gradient-to-r from-sky-500 to-emerald-400"
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>

        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
          <span>Off-chain Per-Txn Fee: $0.00</span>
          <span>
            Remaining: {formatUSD(Math.max(0, totalLimit - currentSpent))}
          </span>
        </div>
      </div>

      {/* Card 2: Deterministic Guardrail & Injection Shield */}
      <div className="rounded-2xl border border-slate-800/90 bg-[#0b1222] p-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Deterministic Security Shield</span>
          </div>
          <span className="inline-flex items-center gap-1 rounded bg-emerald-500/10 px-2 py-0.5 font-mono text-[11px] text-emerald-400">
            <Zap className="h-3 w-3" /> &lt;1ms Latency
          </span>
        </div>

        <div className="mt-2.5 flex items-baseline justify-between">
          <div>
            <span className="text-2xl font-bold text-red-400">
              {blockedInjections}
            </span>
            <span className="ml-1.5 text-xs text-slate-400">
              Injections Blocked
            </span>
          </div>
          <div>
            <span className="text-lg font-bold text-amber-300">
              {blockedPolicyOrAssertions}
            </span>
            <span className="ml-1.5 text-xs text-slate-400">
              Policy/Schema Drops
            </span>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between rounded-lg border border-slate-800/80 bg-slate-950/70 px-3 py-1.5 text-xs">
          <span className="text-slate-400">Prevented Rogue Drain:</span>
          <span className="font-mono font-bold text-emerald-400">
            {formatUSD(totalBlockedAmount)} Saved ($0.00 Loss)
          </span>
        </div>
      </div>

      {/* Card 3: Off-Chain Netting Ledger & Batch Compression */}
      <div className="rounded-2xl border border-slate-800/90 bg-[#0b1222] p-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <GitMerge className="h-4 w-4 text-amber-400" />
            <span>Off-Chain Bilateral Netting Ledger</span>
          </div>
          <span className="rounded bg-amber-500/15 px-2 py-0.5 font-mono text-[11px] font-semibold text-amber-300">
            {nettingSummary?.fee_savings_pct || 0}% Payout Compression
          </span>
        </div>

        <div className="mt-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div>
              <div className="text-xl font-bold text-white">
                {nettingSummary?.raw_transaction_count || 0}
              </div>
              <div className="text-[11px] text-slate-400">Micro-Txns</div>
            </div>
            <ArrowRight className="h-4 w-4 text-slate-500" />
            <div>
              <div className="text-xl font-bold text-sky-400">
                {nettingSummary?.consolidated_payout_count || 0}
              </div>
              <div className="text-[11px] text-slate-400">Net Payouts</div>
            </div>
          </div>

          <div className="text-right">
            <div className="text-lg font-bold text-emerald-300">
              {formatUSD(nettingSummary?.total_net_payout || 0)}
            </div>
            <div className="text-[11px] text-slate-400">Queued Settlement</div>
          </div>
        </div>

        <div className="mt-2.5 truncate font-mono text-[11px] text-slate-400">
          {nettingSummary && nettingSummary.payout_items.length > 0
            ? nettingSummary.payout_items
                .map((i) => `${i.receiver.split("@")[0]}: $${i.amount.value}`)
                .join(" | ")
            : "No pending unsettled micro-transactions in queue."}
        </div>
      </div>
    </div>
  );
}

