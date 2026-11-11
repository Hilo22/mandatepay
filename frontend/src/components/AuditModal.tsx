"use client";

import React from "react";
import {
  X,
  ShieldAlert,
  CheckCircle2,
  Clock,
  FileCode,
  Cpu,
  AlertOctagon,
} from "lucide-react";
import { Transaction } from "@/lib/api-client";
import { formatUSD } from "@/lib/utils";

interface AuditModalProps {
  transaction: Transaction | null;
  onClose: () => void;
}

export default function AuditModal({ transaction, onClose }: AuditModalProps) {
  if (!transaction) return null;

  const isInjection = transaction.status === "BLOCKED_INJECTION";
  const isBlocked = transaction.status.startsWith("BLOCKED_");
  const primaryLog = transaction.auditLogs?.[0];
  const detail = primaryLog?.detailJson || {};
  const latencyMs =
    transaction.latencyMs ?? detail.latency_ms ?? 0.12;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/70 backdrop-blur-sm">
      <div className="flex h-full w-full max-w-2xl flex-col justify-between overflow-y-auto border-l border-slate-800 bg-[#080e1d] p-6 shadow-2xl">
        <div className="space-y-5">
          {/* Header */}
          <div className="flex items-start justify-between border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                {isInjection ? (
                  <AlertOctagon className="h-5 w-5 text-red-400" />
                ) : isBlocked ? (
                  <ShieldAlert className="h-5 w-5 text-amber-400" />
                ) : (
                  <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                )}
                <h3 className="text-base font-bold text-white">
                  Deterministic Guardrail &amp; Assertion Audit Trace
                </h3>
              </div>
              <p className="mt-1 font-mono text-xs text-slate-400">
                Transaction ID: {transaction.id}
              </p>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-800 bg-slate-900 p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Decision Banner */}
          <div
            className={`rounded-xl border p-4 ${
              isInjection
                ? "border-red-500/60 bg-red-950/40 text-red-200"
                : isBlocked
                ? "border-amber-500/50 bg-amber-950/30 text-amber-200"
                : "border-emerald-500/40 bg-emerald-950/30 text-emerald-200"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider">
                Decision: {transaction.status}
              </span>
              <span className="inline-flex items-center gap-1 rounded bg-black/40 px-2 py-0.5 font-mono text-xs">
                <Clock className="h-3.5 w-3.5" />
                Engine Latency: {latencyMs} ms
              </span>
            </div>
            <p className="mt-2 font-mono text-xs leading-relaxed">
              {transaction.rejectionReason ||
                "Deterministic Policy Engine & Contract Assertion Runner verified all constraints. Funds queued in Off-Chain Netting Ledger."}
            </p>
          </div>

          {/* Key Metadata Grid */}
          <div className="grid grid-cols-2 gap-3 rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-xs">
            <div>
              <span className="text-slate-400">Buyer Agent:</span>
              <div className="mt-0.5 font-mono font-semibold text-white">
                {transaction.buyerAgentId}
              </div>
            </div>
            <div>
              <span className="text-slate-400">Seller Agent:</span>
              <div className="mt-0.5 font-mono font-semibold text-sky-300">
                {transaction.sellerAgentId} ({transaction.sellerPaypalEmail})
              </div>
            </div>
            <div>
              <span className="text-slate-400">Requested Amount:</span>
              <div className="mt-0.5 font-mono font-bold text-white">
                {formatUSD(transaction.amount)}{" "}
                {isBlocked && (
                  <span className="text-emerald-400">($0.00 Charged)</span>
                )}
              </div>
            </div>
            <div>
              <span className="text-slate-400">Spend Category:</span>
              <div className="mt-0.5 font-mono text-slate-200">
                {transaction.category}
              </div>
            </div>
          </div>

          {/* Prompt Payload Inspection */}
          <div>
            <div className="mb-1.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-300">
              <Cpu className="h-4 w-4 text-sky-400" />
              <span>Agent Prompt / Instruction Payload</span>
            </div>
            <div
              className={`rounded-xl border p-3.5 font-mono text-xs leading-relaxed ${
                isInjection
                  ? "border-red-500/60 bg-red-950/50 text-red-200"
                  : "border-slate-800 bg-slate-950 text-slate-200"
              }`}
            >
              {transaction.promptPayload}
            </div>
          </div>

          {/* Deliverable Payload vs Expected Assertion Schema */}
          <div>
            <div className="mb-1.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-300">
              <FileCode className="h-4 w-4 text-emerald-400" />
              <span>Seller Deliverable Payload &amp; Contract Assertions</span>
            </div>
            <pre className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950 p-3.5 font-mono text-xs text-emerald-300">
              {JSON.stringify(
                {
                  submitted_deliverable: transaction.deliverablePayload,
                  expected_assertion_schema:
                    detail.expected_assertion_schema || {
                      format: "json",
                      required_keys: ["record_id", "sentiment"],
                    },
                },
                null,
                2
              )}
            </pre>
          </div>

          {/* Full Diagnostic Audit Trace JSON */}
          <div>
            <div className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Full Immutable Audit Log Trace
            </div>
            <pre className="max-h-56 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3.5 font-mono text-[11px] text-slate-300">
              {JSON.stringify(
                transaction.auditLogs?.length
                  ? transaction.auditLogs
                  : detail,
                null,
                2
              )}
            </pre>
          </div>
        </div>

        <div className="mt-6 flex justify-end border-t border-slate-800 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl bg-slate-800 px-5 py-2 text-xs font-semibold text-white hover:bg-slate-700"
          >
            Close Audit Inspector
          </button>
        </div>
      </div>
    </div>
  );
}

