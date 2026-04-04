import { createContext, useContext } from "react";

export type ToastTone = "success" | "error" | "warning" | "info";

export type ToastAction = {
  label: string;
  onClick: () => void;
};

export type ToastInput = {
  id?: string;
  title?: string;
  message: string;
  tone?: ToastTone;
  durationMs?: number;
  action?: ToastAction;
  dedupeKey?: string;
};

export type ToastEntry = {
  id: string;
  title?: string;
  message: string;
  tone: ToastTone;
  durationMs: number;
  action?: ToastAction;
  dedupeKey: string;
  count: number;
  updatedAt: number;
};

export type ToastContextValue = {
  toasts: ToastEntry[];
  pushToast: (input: ToastInput) => string;
  dismissToast: (id: string) => void;
  clearToasts: () => void;
};

export const TOAST_LIMIT = 3;

export const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider.");
  }
  return context;
}

export function buildToastDedupeKey(input: ToastInput): string {
  if (input.dedupeKey) {
    return input.dedupeKey;
  }
  const tone = input.tone || "info";
  return `${tone}:${input.title || ""}:${input.message}`;
}

export function resolveToastDuration(input: ToastInput): number {
  if (typeof input.durationMs === "number" && input.durationMs > 0) {
    return input.durationMs;
  }
  if (input.tone === "error" || input.tone === "warning") {
    return 7000;
  }
  return 4000;
}

export function createToastId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `toast-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
