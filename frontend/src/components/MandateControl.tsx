"use client";

import React, { useState } from "react";
import {
  Sparkles,
  CheckCircle2,
  CreditCard,
  Terminal,
  ShieldAlert,
  Play,
  FileWarning,
  Send,
  Loader2,
} from "lucide-react";
import { Mandate } from "@/lib/api-client";
import { formatUSD } from "@/lib/utils";

interface MandateControlProps {
  mandate: Mandate | null;
  onCompileMandate: (prompt: string, email: string) => Promise<void>;
  onApproveTopUp: (mandateId: string) => Promise<void>;
  onRunNormalStream: () => Promise<void>;
  onInjectRogueAgent: () => Promise<void>;
  onTriggerAssertionFail: () => Promise<void>;
  onExecuteSettlement: () => Promise<void>;
  isBusy: boolean;
  unsettledCount: number;
}

const DEFAULT_PROMPT =
  "Allocate $30 for NLP data labeling tasks. Max $3 per task. Require deliverable JSON keys 'record_id' and 'sentiment'.";

export default function MandateControl({
  mandate,
  onCompileMandate,
  onApproveTopUp,
  onRunNormalStream,
  onInjectRogueAgent,
  onTriggerAssertionFail,
  onExecuteSettlement,
  isBusy,
  unsettledCount,
}: MandateControlProps) {
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [ownerEmail, setOwnerEmail] = useState("buyer_owner@sandbox.paypal.com");
  const [error, setError] = useState<string | null>(null);

  const handleCompile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await onCompileMandate(prompt, ownerEmail);
    } catch (err: any) {
      setError(err.message || "Failed to compile mandate");
    }
  };

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
      {/* Left: Natural Language Mandate Compiler */}
      <div className="rounded-2xl border border-slate-800/90 bg-[#0b1222] p-5 shadow-xl lg:col-span-7">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-sky-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
              1. Natural Language Mandate Authorization
            </h2>
          </div>
          <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-slate-400">
            Tool: compile_mandate_policy
          </span>
        </div>

        <form onSubmit={handleCompile} className="space-y-3">
          <div>
            <textarea
              rows={2}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe spending limits, allowed categories, and required deliverable JSON keys..."
              className="w-full rounded-xl border border-slate-700/80 bg-slate-950/90 px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <label className="text-xs text-slate-400">Owner PayPal:</label>
              <input
                type="email"
                value={ownerEmail}
                onChange={(e) => setOwnerEmail(e.target.value)}
                className="rounded-lg border border-slate-800 bg-slate-900 px-2.5 py-1 font-mono text-xs text-slate-200 focus:border-sky-500 focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-2.5">
              <button
                type="submit"
                disabled={isBusy}
                className="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-sky-600/25 transition hover:bg-sky-500 disabled:opacity-50"
              >
                {isBusy ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Terminal className="h-3.5 w-3.5" />
                )}
                Compile Policy &amp; Create PayPal Top-Up
              </button>

              {mandate && mandate.status === "AWAITING_PAYMENT" && (
                <button
                  type="button"
                  disabled={isBusy}
                  onClick={() => onApproveTopUp(mandate.id)}
                  className="inline-flex animate-pulse items-center gap-2 rounded-xl bg-[#ffc439] px-4 py-2 text-xs font-bold text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-[#f4b92b]"
                >
                  <CreditCard className="h-4 w-4" />
                  Approve {formatUSD(mandate.totalBudgetLimit)} PayPal Sandbox Top-Up
                </button>
              )}
            </div>
          </div>

          {error && (
            <div className="rounded-lg border border-red-500/40 bg-red-950/40 px-3 py-2 text-xs text-red-300">
              {error}
            </div>
          )}
        </form>

        {/* Live Action Simulation Bar for Hackathon Demo */}
        <div className="mt-4 border-t border-slate-800/80 pt-3.5">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Autonomous Agent Simulation &amp; Security Test Controls
            </span>
            <span className="text-[11px] text-slate-500">
              Instant SSE Stream to AG Grid
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={isBusy || !mandate || mandate.status !== "ACTIVE"}
              onClick={onRunNormalStream}
              className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-500/15 px-3 py-1.5 text-xs font-semibold text-emerald-300 transition hover:bg-emerald-500/25 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Play className="h-3.5 w-3.5" />
              Stream Verified Micro-Tasks
            </button>

            <button
              type="button"
              disabled={isBusy || !mandate || mandate.status !== "ACTIVE"}
              onClick={onInjectRogueAgent}
              className="inline-flex items-center gap-1.5 rounded-lg border border-red-500/50 bg-red-600/20 px-3 py-1.5 text-xs font-bold text-red-200 shadow-sm shadow-red-600/20 transition hover:bg-red-600/35 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ShieldAlert className="h-3.5 w-3.5 text-red-400" />
              Inject Malicious Rogue Agent
            </button>

            <button
              type="button"
              disabled={isBusy || !mandate || mandate.status !== "ACTIVE"}
              onClick={onTriggerAssertionFail}
              className="inline-flex items-center gap-1.5 rounded-lg border border-yellow-500/40 bg-yellow-500/15 px-3 py-1.5 text-xs font-semibold text-yellow-200 transition hover:bg-yellow-500/25 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <FileWarning className="h-3.5 w-3.5 text-yellow-400" />
              Test Missing Deliverable Key
            </button>

            <button
              type="button"
              disabled={isBusy || unsettledCount === 0}
              onClick={onExecuteSettlement}
              className="ml-auto inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-[#0070ba] to-[#003087] px-3.5 py-1.5 text-xs font-bold text-white shadow-md shadow-sky-700/30 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Send className="h-3.5 w-3.5" />
              Execute Batch Net Settlement ({unsettledCount})
            </button>
          </div>
        </div>
      </div>

      {/* Right: Synthesized Deterministic Policy JSON Inspector */}
      <div className="flex flex-col justify-between rounded-2xl border border-slate-800/90 bg-[#0b1222] p-5 shadow-xl lg:col-span-5">
        <div>
          <div className="mb-2.5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
                2. Synthesized Deterministic Policy JSON
              </h3>
            </div>
            {mandate?.paypalOrderId && (
              <span className="rounded bg-blue-950/80 px-2 py-0.5 font-mono text-[11px] text-sky-300">
                Order: {mandate.paypalOrderId}
              </span>
            )}
          </div>

          {mandate ? (
            <pre className="max-h-[195px] overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-[11.5px] leading-relaxed text-sky-300">
              {JSON.stringify(
                {
                  mandate_id: mandate.id,
                  status: mandate.status,
                  total_budget_limit: mandate.totalBudgetLimit,
                  max_charge_per_txn: mandate.maxChargePerTxn,
                  allowed_categories: mandate.allowedCategories,
                  assertion_schema: mandate.assertionSchema,
                },
                null,
                2
              )}
            </pre>
          ) : (
            <div className="flex h-[180px] items-center justify-center rounded-xl border border-dashed border-slate-800 bg-slate-950/50 p-4 text-center text-xs text-slate-500">
              Compile a natural language mandate on the left to synthesize immutable guardrails and fund the PayPal escrow credit line.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

