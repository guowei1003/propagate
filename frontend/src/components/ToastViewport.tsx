import type { ToastEntry } from "../lib/toast";

type Props = {
  toasts: ToastEntry[];
  onDismiss: (id: string) => void;
};

function ToastItem({ toast, onDismiss }: { toast: ToastEntry; onDismiss: (id: string) => void }) {
  return (
    <div className={`toast-item toast-item--${toast.tone}`} role="alert">
      <div className="toast-item__header">
        {toast.title && <strong>{toast.title}</strong>}
        {toast.count > 1 && <span className="toast-item__count">{toast.count}</span>}
        <button className="toast-item__close" onClick={() => onDismiss(toast.id)} aria-label="Dismiss">
          ×
        </button>
      </div>
      <p>{toast.message}</p>
      {toast.action && (
        <button className="toast-item__action" onClick={toast.action.onClick}>
          {toast.action.label}
        </button>
      )}
    </div>
  );
}

export function ToastViewport({ toasts, onDismiss }: Props) {
  if (toasts.length === 0) return null;
  return (
    <div className="toast-viewport" aria-live="polite" aria-label="Notifications">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}
