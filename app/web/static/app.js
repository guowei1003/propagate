function initReveal() {
  const nodes = Array.from(document.querySelectorAll("[data-reveal]"));
  if (!nodes.length) {
    return;
  }
  if (!("IntersectionObserver" in window)) {
    nodes.forEach((node) => node.classList.add("is-visible"));
    return;
  }
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.14 }
  );
  nodes.forEach((node) => observer.observe(node));
}

function initScrollProgress() {
  const bar = document.getElementById("scroll-progress");
  if (!bar) {
    return;
  }
  const update = () => {
    const scrollTop = window.scrollY || 0;
    const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    const progress = Math.min(1, scrollTop / max);
    bar.style.transform = `scaleX(${progress})`;
  };
  update();
  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
}

function initAmbientParallax() {
  const ambients = Array.from(document.querySelectorAll(".ambient"));
  if (!ambients.length) {
    return;
  }
  window.addEventListener(
    "pointermove",
    (event) => {
      const x = event.clientX / window.innerWidth - 0.5;
      const y = event.clientY / window.innerHeight - 0.5;
      ambients.forEach((item, index) => {
        const depth = (index + 1) * 10;
        item.style.transform = `translate3d(${x * depth}px, ${y * depth}px, 0)`;
      });
    },
    { passive: true }
  );
}

function initTaskStream() {
  const streamTarget = document.querySelector("[data-task-stream]");
  if (!streamTarget || typeof EventSource === "undefined") {
    return;
  }
  const taskId = streamTarget.getAttribute("data-task-stream");
  if (!taskId) {
    return;
  }
  const source = new EventSource(`/api/tasks/${taskId}/stream`);
  source.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    const line = document.createElement("div");
    line.className = `log-line level-${payload.level} is-new`;
    line.innerHTML = `
      <span>#${payload.id}</span>
      <span>${payload.created_at}</span>
      <strong>${payload.event_type}</strong>
      <span>${payload.message}</span>
    `;
    streamTarget.appendChild(line);
    streamTarget.scrollTop = streamTarget.scrollHeight;
    window.setTimeout(() => line.classList.remove("is-new"), 1100);
  };
}

document.addEventListener("DOMContentLoaded", () => {
  initReveal();
  initScrollProgress();
  initAmbientParallax();
  initTaskStream();
});
