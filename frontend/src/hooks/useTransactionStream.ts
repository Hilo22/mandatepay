"use client";

import { useEffect, useState, useCallback } from "react";
import {
  API_BASE_URL,
  Mandate,
  Transaction,
  SettlementResponse,
} from "@/lib/api-client";

interface UseTransactionStreamProps {
  onTransactionCreated?: (txn: Transaction) => void;
  onMandateUpdated?: (mandate: Mandate) => void;
  onBatchSettled?: (settlement: SettlementResponse) => void;
}

export function useTransactionStream({
  onTransactionCreated,
  onMandateUpdated,
  onBatchSettled,
}: UseTransactionStreamProps) {
  const [connected, setConnected] = useState(false);

  const handleEvent = useCallback(
    (rawEventData: string) => {
      try {
        const parsed = JSON.parse(rawEventData);
        const eventType = parsed.event;
        const data = parsed.data;

        if (eventType === "connected") {
          setConnected(true);
        } else if (eventType === "transaction_created" && onTransactionCreated) {
          onTransactionCreated(data as Transaction);
        } else if (eventType === "mandate_updated" && onMandateUpdated) {
          onMandateUpdated(data as Mandate);
        } else if (eventType === "batch_settled" && onBatchSettled) {
          onBatchSettled(data as SettlementResponse);
        }
      } catch {
        // Ignore malformed keep-alive frames
      }
    },
    [onTransactionCreated, onMandateUpdated, onBatchSettled]
  );

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      try {
        eventSource = new EventSource(
          `${API_BASE_URL}/api/transactions/stream`
        );

        eventSource.onopen = () => {
          setConnected(true);
        };

        eventSource.onmessage = (e) => {
          handleEvent(e.data);
        };

        eventSource.onerror = () => {
          setConnected(false);
          if (eventSource) {
            eventSource.close();
          }
          reconnectTimer = setTimeout(connect, 3000);
        };
      } catch {
        setConnected(false);
      }
    };

    connect();

    return () => {
      if (eventSource) eventSource.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, [handleEvent]);

  return { connected };
}

