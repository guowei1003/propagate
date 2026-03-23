const ROLE_LABELS = {
  assistant: "AI",
  user: "用户",
  tool: "Tool",
  system: "系统",
};

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderMarkdown(content) {
  if (window.marked && typeof window.marked.parse === "function") {
    return window.marked.parse(content || "", { breaks: true });
  }
  return `<p>${escapeHtml(content || "").replace(/\n/g, "<br />")}</p>`;
}

function initReveal() {
  const nodes = Array.from(document.querySelectorAll("[data-reveal]"));
  if (!nodes.length) return;
  if (!("IntersectionObserver" in window)) {
    nodes.forEach((node) => node.classList.add("is-visible"));
    return;
  }
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.12 }
  );
  nodes.forEach((node) => observer.observe(node));
}

function initScrollProgress() {
  const bar = document.getElementById("scroll-progress");
  if (!bar) return;
  const update = () => {
    const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    const progress = Math.min(1, Math.max(0, window.scrollY / max));
    bar.style.transform = `scaleX(${progress})`;
  };
  update();
  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
}

function initAmbientParallax() {
  const ambients = Array.from(document.querySelectorAll(".ambient"));
  if (!ambients.length) return;
  window.addEventListener(
    "pointermove",
    (event) => {
      const x = event.clientX / window.innerWidth - 0.5;
      const y = event.clientY / window.innerHeight - 0.5;
      ambients.forEach((node, index) => {
        const depth = (index + 1) * 8;
        node.style.transform = `translate3d(${x * depth}px, ${y * depth}px, 0)`;
      });
    },
    { passive: true }
  );
}

function parsePayload(event) {
  if (event && typeof event.payload === "object" && event.payload !== null) {
    return event.payload;
  }
  if (!event || !event.payload_json) {
    return {};
  }
  try {
    return JSON.parse(event.payload_json);
  } catch {
    return {};
  }
}

function createToolPayloadNode(input) {
  if (!input || !Object.keys(input).length) return null;
  const details = document.createElement("details");
  details.className = "tool-payload";
  details.open = true;
  const summary = document.createElement("summary");
  summary.textContent = "参数";
  const pre = document.createElement("pre");
  pre.textContent = JSON.stringify(input, null, 2);
  details.append(summary, pre);
  return details;
}

function createChatItem(message) {
  const article = document.createElement("article");
  article.className = `chat-item role-${message.role || "assistant"} kind-${message.kind || "message"} is-new`;

  const meta = document.createElement("div");
  meta.className = "chat-meta";
  const role = document.createElement("span");
  role.className = "chat-role";
  role.textContent = ROLE_LABELS[message.role] || message.role || "AI";
  const time = document.createElement("time");
  time.textContent = message.created_at || new Date().toISOString();
  meta.append(role, time);

  const title = document.createElement("h3");
  title.className = "chat-title";
  title.textContent = message.title || "消息";

  const content = document.createElement("div");
  content.className = "chat-content md-content";
  content.innerHTML = renderMarkdown(message.content || "");

  article.append(meta, title, content);

  if (message.tool_name) {
    const tool = document.createElement("div");
    tool.className = "tool-tag";
    tool.textContent = message.tool_name;
    article.appendChild(tool);
  }

  const payloadNode = createToolPayloadNode(message.tool_input || {});
  if (payloadNode) {
    article.appendChild(payloadNode);
  }

  window.setTimeout(() => article.classList.remove("is-new"), 1100);
  return article;
}

function eventToChatMessages(event) {
  const payload = parsePayload(event);
  const createdAt = event.created_at;
  const label = event.event_type_label || event.event_type || "事件";

  if (event.event_type === "task.runtime.prepared") {
    const agents = Array.isArray(payload.agents) ? payload.agents : [];
    return agents.map((agent) => ({
      role: "assistant",
      kind: "tool_call",
      title: "callTool",
      content: "创建临时执行 Agent 并绑定技能。",
      created_at: createdAt,
      tool_name: "create_sub_agent",
      tool_input: {
        agent_name: agent.agent_name,
        sandbox_mode: agent.sandbox_mode,
        skills: agent.skills || [],
        subtask_id: agent.subtask_id,
      },
    }));
  }

  if (
    [
      "subtask.started",
      "subtask.completed",
      "subtask.retrying",
      "subtask.review.failed",
      "subtask.test.failed",
      "subtask.dependents.blocked",
      "task.report.generated",
    ].includes(event.event_type)
  ) {
    return [
      {
        role: "tool",
        kind: "tool_result",
        title: label,
        content: event.message || "",
        created_at: createdAt,
        tool_name: event.event_type,
        tool_input: payload,
      },
    ];
  }

  if (["requirement.analysis.completed", "requirement.clarification.requested"].includes(event.event_type)) {
    return [
      {
        role: "assistant",
        kind: "message",
        title: label,
        content: event.message || "",
        created_at: createdAt,
      },
    ];
  }

  return [];
}

function appendLogLine(streamTarget, event) {
  if (!streamTarget) return;
  const line = document.createElement("div");
  line.className = `log-line level-${event.level || "info"} is-new`;
  line.innerHTML = `
    <span>#${escapeHtml(event.id)}</span>
    <span>${escapeHtml(event.created_at || "")}</span>
    <strong>${escapeHtml(event.event_type_label || event.event_type || "")}</strong>
    <span>${escapeHtml(event.message || "")}</span>
  `;
  streamTarget.appendChild(line);
  streamTarget.scrollTop = streamTarget.scrollHeight;
  window.setTimeout(() => line.classList.remove("is-new"), 1100);
}

function appendChatMessages(chatTarget, messages) {
  if (!chatTarget || !messages.length) return;
  messages.forEach((message) => {
    chatTarget.appendChild(createChatItem(message));
  });
  chatTarget.scrollTop = chatTarget.scrollHeight;
}

function initExistingMarkdown() {
  document.querySelectorAll(".md-content").forEach((node) => {
    node.innerHTML = renderMarkdown(node.textContent || "");
  });
}

function initTaskStream() {
  const logTarget = document.querySelector("[data-task-stream]");
  const chatTarget = document.querySelector("[data-chat-stream]");
  const taskId = (logTarget || chatTarget)?.getAttribute("data-task-stream") || chatTarget?.getAttribute("data-chat-stream");
  if (!taskId || typeof EventSource === "undefined") {
    return;
  }
  const lastEventId = Number(
    logTarget?.getAttribute("data-last-event-id") || chatTarget?.getAttribute("data-last-event-id") || "0"
  );
  const source = new EventSource(`/api/tasks/${taskId}/stream?last_event_id=${Math.max(0, lastEventId)}`);
  source.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    appendLogLine(logTarget, payload);
    appendChatMessages(chatTarget, eventToChatMessages(payload));
  };
}

document.addEventListener("DOMContentLoaded", () => {
  initReveal();
  initScrollProgress();
  initAmbientParallax();
  initExistingMarkdown();
  initTaskStream();
});
