import { useState, useEffect, type RefObject } from "react";

const COLUMN_BREAKPOINTS = [
  { maxWidth: 639, columns: 2 },
  { maxWidth: 767, columns: 3 },
  { maxWidth: 1023, columns: 4 },
  { maxWidth: 1279, columns: 5 },
  { maxWidth: Infinity, columns: 6 },
];

export function useColumns(
  containerRef: RefObject<HTMLDivElement | null>
): number {
  const [columns, setColumns] = useState(6);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const updateColumns = () => {
      const width = el.clientWidth;
      const bp = COLUMN_BREAKPOINTS.find((b) => width <= b.maxWidth);
      setColumns(bp?.columns ?? 6);
    };

    updateColumns();
    const observer = new ResizeObserver(updateColumns);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return columns;
}
