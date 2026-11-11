"use client";

import React, { useMemo } from "react";
import { AgGridReact } from "ag-grid-react";
import { ColDef, ICellRendererParams, RowClassParams } from "ag-grid-community";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";
import {
  CheckCircle2,
  ShieldAlert,
  Ban,
  AlertTriangle,
  BadgeCheck,
  Eye,
  Activity,
} from "lucide-react";
import { Transaction } from "@/lib/api-client";
import { formatTime, formatUSD } from "@/lib/utils";

interface AGGridLedgerProps {
  transactions: Transaction[];
  onSelectTransaction: (txn: Transaction) => void;
}

const StatusCellRenderer = (params: ICellRendererParams<Transaction>) => {
  const status = params.value as Transaction["status"];

  switch (status) {
    case "APPROVED":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-bold tracking-wide text-emerald-300">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
          APPROVED
        </span>
      );
    case "BLOCKED_INJECTION":
      return (
        <span className="inline-flex animate-pulse items-center gap-1.5 rounded-full border border-red-500 bg-red-600/35 px-2.5 py-0.5 text-[11px] font-extrabold tracking-wide text-red-200 shadow-sm shadow-red-600/50">
          <ShieldAlert className="h-3.5 w-3.5 text-red-300" />
          BLOCKED_INJECTION
        </span>
      );
    case "BLOCKED_POLICY":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/45 bg-amber-500/20 px-2.5 py-0.5 text-[11px] font-bold tracking-wide text-amber-300">
          <Ban className="h-3.5 w-3.5 text-amber-400" />
          BLOCKED_POLICY
        </span>
      );
    case "BLOCKED_ASSERTION_FAILED":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full border border-yellow-500/45 bg-yellow-500/20 px-2.5 py-0.5 text-[11px] font-bold tracking-wide text-yellow-200">
          <AlertTriangle className="h-3.5 w-3.5 text-yellow-400" />
          BLOCKED_ASSERTION_FAILED
        </span>
      );
    case "SETTLED":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full border border-sky-500/45 bg-sky-500/20 px-2.5 py-0.5 text-[11px] font-bold tracking-wide text-sky-300">
          <BadgeCheck className="h-3.5 w-3.5 text-sky-400" />
          SETTLED
        </span>
      );
    default:
      return <span className="text-xs text-slate-400">{status}</span>;
  }
};

export default function AGGridLedger({
  transactions,
  onSelectTransaction,
}: AGGridLedgerProps) {
  const columnDefs = useMemo<ColDef<Transaction>[]>(
    () => [
      {
        headerName: "Time",
        field: "createdAt",
        width: 105,
        valueFormatter: (p) => formatTime(p.value),
        cellClass: "font-mono text-xs text-slate-400",
      },
      {
        headerName: "Status Guardrail",
        field: "status",
        width: 225,
        cellRenderer: StatusCellRenderer,
        enableCellChangeFlash: true,
      },
      {
        headerName: "Buyer Agent",
        field: "buyerAgentId",
        width: 145,
        cellClass: "font-mono text-xs font-semibold text-slate-200",
      },
      {
        headerName: "Seller Agent / PayPal",
        field: "sellerAgentId",
        width: 220,
        cellRenderer: (p: ICellRendererParams<Transaction>) => (
          <div className="flex flex-col leading-tight py-1">
            <span className="font-mono text-xs font-semibold text-sky-300">
              {p.data?.sellerAgentId}
            </span>
            <span className="font-mono text-[10.5px] text-slate-400">
              {p.data?.sellerPaypalEmail}
            </span>
          </div>
        ),
      },
      {
        headerName: "Category",
        field: "category",
        width: 140,
        cellRenderer: (p: ICellRendererParams<Transaction>) => (
          <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 font-mono text-[11px] text-slate-300">
            {p.value}
          </span>
        ),
      },
      {
        headerName: "Amount",
        field: "amount",
        width: 110,
        enableCellChangeFlash: true,
        valueFormatter: (p) => formatUSD(p.value || 0),
        cellClass: (p) =>
          p.data?.status.startsWith("BLOCKED_")
            ? "font-mono text-xs font-bold text-red-400 line-through"
            : "font-mono text-xs font-bold text-emerald-300",
      },
      {
        headerName: "Ledger Fee",
        width: 105,
        valueGetter: () => "$0.00",
        cellClass: "font-mono text-xs text-emerald-400/80",
      },
      {
        headerName: "Prompt / Deliverable / Rejection Diagnostic",
        field: "promptPayload",
        flex: 1,
        minWidth: 280,
        cellRenderer: (p: ICellRendererParams<Transaction>) => {
          const txn = p.data;
          if (!txn) return null;
          return (
            <div className="flex flex-col justify-center py-1 leading-tight">
              <span className="truncate text-xs text-slate-200">
                {txn.promptPayload}
              </span>
              {txn.rejectionReason ? (
                <span className="truncate font-mono text-[11px] text-red-400">
                  {txn.rejectionReason}
                </span>
              ) : txn.payoutBatchId ? (
                <span className="truncate font-mono text-[11px] text-sky-400">
                  PayPal Batch ID: {txn.payoutBatchId}
                </span>
              ) : (
                <span className="truncate font-mono text-[11px] text-slate-400">
                  Deliverable:{" "}
                  {txn.deliverablePayload
                    ? JSON.stringify(txn.deliverablePayload)
                    : "Verified"}
                </span>
              )}
            </div>
          );
        },
      },
      {
        headerName: "Audit",
        width: 95,
         pinned: "right",
        cellRenderer: (p: ICellRendererParams<Transaction>) => (
          <button
            type="button"
            onClick={() => p.data && onSelectTransaction(p.data)}
            className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-800/90 px-2 py-1 text-[11px] font-medium text-sky-300 transition hover:border-sky-500 hover:bg-sky-500/20"
          >
            <Eye className="h-3 w-3" />
            Inspect
          </button>
        ),
      },
    ],
    [onSelectTransaction]
  );

  const defaultColDef = useMemo<ColDef>(
    () => ({
      sortable: true,
      resizable: true,
      filter: true,
    }),
    []
  );

  const getRowClass = (params: RowClassParams<Transaction>) => {
    if (params.data?.status === "BLOCKED_INJECTION") {
      return "row-blocked-injection";
    }
    return "";
  };

  return (
    <div className="rounded-2xl border border-slate-800/90 bg-[#0b1222] p-5 shadow-2xl">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <Activity className="h-4 w-4 text-sky-400" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
            3. AG Grid Real-Time Agentic Transaction &amp; Guardrail Ledger
          </h2>
          <span className="rounded-full bg-slate-800 px-2.5 py-0.5 font-mono text-xs text-slate-300">
            {transactions.length} Events
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-emerald-400" /> APPROVED
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-red-500" /> BLOCKED_INJECTION
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-amber-400" /> BLOCKED_POLICY
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-yellow-400" />{" "}
            BLOCKED_ASSERTION_FAILED
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-sky-400" /> SETTLED
          </span>
          <span className="text-slate-500">
            (Click any row to open Diagnostic Audit Drawer)
          </span>
        </div>
      </div>

      <div className="ag-theme-quartz-dark h-[440px] w-full overflow-hidden rounded-xl border border-slate-800">
        <AgGridReact<Transaction>
          rowData={transactions}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          getRowId={(params) => params.data.id}
          enableCellChangeFlash={true}
          animateRows={true}
          rowHeight={46}
          headerHeight={38}
          getRowClass={getRowClass}
          onRowClicked={(e) => e.data && onSelectTransaction(e.data)}
          overlayNoRowsTemplate="<span class='text-xs text-slate-400'>No agent transactions recorded yet. Compile a Mandate and click 'Stream Verified Micro-Tasks' or run simulate_agents.py.</span>"
        />
      </div>
    </div>
  );
}

