import { useEffect, useRef } from "react";

export function usePolling(callback: () => void | Promise<void>, intervalMs: number) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    void savedCallback.current();

    const id = window.setInterval(() => {
      void savedCallback.current();
    }, intervalMs);

    return () => window.clearInterval(id);
  }, [intervalMs]);
}
