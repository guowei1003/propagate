import { type ToastEntry } from "../../lib/toast";

type Props = {
  item: ToastEntry;
  onClose: (id: string) => void;
};

export function ToastItem({ item, onClose }: Props) {
  const liveMode = item.tone === "error" || item.tone === "warning" ? "assertive" : "polite";
  const role = liveMode === "assertive" ? "alert" : "status";

  return (
    <article
      className={`toast-item toast-item--${item.tone}`}
      role={role}
      aria-live={liveMode}
      aria-atomic="true"
    >
      <div className="toast-item__body">
        <div className="toast-item__header">
          <strong>{item.title || "系统提示"}</strong>
          <div className="toast-item__header-actions">
            {item.count > 1 ? <span className="toast-item__count">x{item.count}</span> : null}
            <button
              className="toast-item__close"
              type="button"
              aria-label="关闭通知"
              onClick={() => onClose(item.id)}
            >
              ×
            </button>
          </div>
        </div>
        <p>{item.message}</p>
      </div>
      {item.action ? (
        <button
          className="toast-item__action"
          type="button"
          onClick={() => {
            item.action?.onClick();
            onClose(item.id);
          }}
        >
          {item.action.label}
        </button>
      ) : null}
    </article>
  );
}
