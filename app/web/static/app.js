document.addEventListener("DOMContentLoaded", () => {
  const streamTarget = document.querySelector("[data-task-stream]");
  if (!streamTarget) {
    return;
  }
  const taskId = streamTarget.getAttribute("data-task-stream");
  if (!taskId) {
    return;
  }
  const lastLine = streamTarget.querySelector(".log-line:last-child span");
  const source = new EventSource(`/api/tasks/${taskId}/stream`);
  source.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    const line = document.createElement("div");
    line.className = `log-line level-${payload.level}`;
    line.innerHTML = `
      <span>#${payload.id}</span>
      <span>${payload.created_at}</span>
      <strong>${payload.event_type}</strong>
      <span>${payload.message}</span>
    `;
    streamTarget.appendChild(line);
    streamTarget.scrollTop = streamTarget.scrollHeight;
  };
});

