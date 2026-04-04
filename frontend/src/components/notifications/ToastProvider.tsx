import { ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  TOAST_LIMIT,
  ToastContext,
  type ToastEntry,
  type ToastInput,
  buildToastDedupeKey,
  createToastId,
  resolveToastDuration
} from "../../lib/toast";

type Props = {
  children: ReactNode;
};

export function ToastProvider({ children }: Props) {
  const [toasts, setToasts] = useState<ToastEntry[]>([]);
  const timerMapRef = useRef<Map<string, number>>(new Map());

  const dismissToast = useCallback((id: string) => {
    setToasts((current) => current.filter((item) => item.id !== id));
  }, []);

  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  const pushToast = useCallback((input: ToastInput) => {
    const dedupeKey = buildToastDedupeKey(input);
    const nextId = input.id || createToastId();
    const nextTone = input.tone || "info";
    const nextDuration = resolveToastDuration(input);
    const updatedAt = Date.now();

    setToasts((current) => {
      const duplicate = current.find((item) => item.dedupeKey === dedupeKey);
      if (duplicate) {
        const merged: ToastEntry = {
          ...duplicate,
          title: input.title || duplicate.title,
          message: input.message,
          tone: nextTone,
          durationMs: nextDuration,
          action: input.action,
          count: duplicate.count + 1,
          updatedAt
        };
        const withoutDuplicate = current.filter((item) => item.id !== duplicate.id);
        return [merged, ...withoutDuplicate].slice(0, TOAST_LIMIT);
      }

      const created: ToastEntry = {
        id: nextId,
        title: input.title,
        message: input.message,
        tone: nextTone,
        durationMs: nextDuration,
        action: input.action,
        dedupeKey,
        count: 1,
        updatedAt
      };
      return [created, ...current].slice(0, TOAST_LIMIT);
    });

    return nextId;
  }, []);

  useEffect(() => {
    timerMapRef.current.forEach((timerId) => {
      window.clearTimeout(timerId);
    });
    timerMapRef.current.clear();

    toasts.forEach((toast) => {
      const timerId = window.setTimeout(() => {
        dismissToast(toast.id);
      }, toast.durationMs);
      timerMapRef.current.set(toast.id, timerId);
    });

    return () => {
      timerMapRef.current.forEach((timerId) => {
        window.clearTimeout(timerId);
      });
      timerMapRef.current.clear();
    };
  }, [toasts, dismissToast]);

  const value = useMemo(
    () => ({
      toasts,
      pushToast,
      dismissToast,
      clearToasts
    }),
    [toasts, pushToast, dismissToast, clearToasts]
  );

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}
