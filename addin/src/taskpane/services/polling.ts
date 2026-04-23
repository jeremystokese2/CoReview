import { useEffect, useRef, useState } from "react";
import type { ReviewDetail } from "../types";
import { getReview } from "./api";

const POLL_INTERVAL_MS = 2000;

export interface PollState {
  review: ReviewDetail | null;
  error: string | null;
  isPolling: boolean;
}

/**
 * Poll GET /reviews/{id} every 2s until status is complete or failed.
 * Cancels in-flight requests on unmount or when reviewId changes.
 */
export function usePollReview(reviewId: string | null): PollState {
  const [review, setReview] = useState<ReviewDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!reviewId) {
      setReview(null);
      setError(null);
      setIsPolling(false);
      return undefined;
    }

    let cancelled = false;
    const ctrl = new AbortController();
    setIsPolling(true);
    setError(null);

    const tick = async () => {
      try {
        const detail = await getReview(reviewId, ctrl.signal);
        if (cancelled) return;
        setReview(detail);
        if (detail.status === "complete" || detail.status === "failed") {
          setIsPolling(false);
          return;
        }
        timerRef.current = window.setTimeout(tick, POLL_INTERVAL_MS);
      } catch (e: any) {
        if (cancelled || e?.name === "AbortError") return;
        setError(e?.message ?? String(e));
        setIsPolling(false);
      }
    };

    tick();

    return () => {
      cancelled = true;
      ctrl.abort();
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [reviewId]);

  return { review, error, isPolling };
}
