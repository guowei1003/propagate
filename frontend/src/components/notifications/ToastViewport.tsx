import { ToastItem } from "./ToastItem";
import { useToast } from "../../lib/toast";

export function ToastViewport() {
  const { toasts, dismissToast } = useToast();

  if (toasts.length === 0) {
    return null;
  }

  return (
    <section className="toast-viewport" aria-label="全局通知">
      {toasts.map((item) => (
        <ToastItem key={item.id} item={item} onClose={dismissToast} />
      ))}
    </section>
  );
}
