import { useCallback, useEffect, useRef, useState } from "react";
import type { HealthResponse } from "@/lib/api";
import { api } from "@/lib/api";

export type ConnectionStatus = "connecting" | "connected" | "error";

interface UseBackendHealthResult {
  status: ConnectionStatus;
  health?: HealthResponse;
  error?: string;
  retry: () => void;
}

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 1000;

export function useBackendHealth(): UseBackendHealthResult {
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("connecting");
  const [health, setHealth] = useState<HealthResponse | undefined>();
  const [error, setError] = useState<string | undefined>();
  const retryCountRef = useRef(0);
  const mountedRef = useRef(true);

  const fetchHealth = useCallback(async () => {
    setConnectionStatus("connecting");
    setError(undefined);

    try {
      const data = await api.health();
      if (!mountedRef.current) return;

      setHealth(data);
      setConnectionStatus("connected");
      retryCountRef.current = 0;
    } catch (err) {
      if (!mountedRef.current) return;

      const message =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null && "message" in err
            ? (err as { message: string }).message
            : "Failed to connect to backend";

      setError(message);

      if (retryCountRef.current < MAX_RETRIES) {
        retryCountRef.current += 1;
        const delay = BASE_DELAY_MS * Math.pow(2, retryCountRef.current - 1);
        setTimeout(() => {
          if (mountedRef.current) {
            fetchHealth();
          }
        }, delay);
      } else {
        setConnectionStatus("error");
      }
    }
  }, []);

  const retry = useCallback(() => {
    retryCountRef.current = 0;
    fetchHealth();
  }, [fetchHealth]);

  useEffect(() => {
    mountedRef.current = true;
    fetchHealth();

    return () => {
      mountedRef.current = false;
    };
  }, [fetchHealth]);

  return { status: connectionStatus, health, error, retry };
}
