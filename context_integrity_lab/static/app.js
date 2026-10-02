const $ = (selector) => document.querySelector(selector);

function decisionClass(value) {
  return `decision ${value}`;
}

function renderRecon(data) {
  const summary = data.summary || {};
  $("#recon-summary").innerHTML = ["created", "matched", "held", "duplicate"].map((key) =>
    `<div class="metric"><span>${key}</span><strong>${summary[key] || 0}</strong></div>`).join("");
  $("#decisions").innerHTML = (data.decisions || []).map((item) =>
    `<tr><td><code>${item.source_record_id || "—"}</code></td><td>${item.name || "—"}</td><td>${item.event_id || "—"}</td><td><span class="${decisionClass(item.decision)}">${item.decision}</span></td><td>${item.reason}</td></tr>`).join("");
}

async function refreshAudit() {
  const response = await fetch("/api/overview");
  const data = await response.json();
  const events = data.audit || [];
  $("#audit").innerHTML = events.length ? events.slice().reverse().map((event) =>
    `<div class="audit-item"><span class="dot"></span><div><strong>${event.event}</strong><small>${event.decision || event.status || "recorded"} · ${event.reason || "supported"}</small></div></div>`).join("") : '<div class="empty">No events yet.</div>';
}

$("#reconcile").addEventListener("click", async () => {
  $("#reconcile").disabled = true;
  const response = await fetch("/api/reconcile", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
  renderRecon(await response.json());
  await refreshAudit();
  $("#reconcile").disabled = false;
});

$("#ask").addEventListener("click", async () => {
  const payload = { question: $("#question").value, person_id: $("#person").value, project_id: $("#project").value, now: "2026-10-01T12:00:00Z" };
  const response = await fetch("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  const data = await response.json();
  $("#answer").textContent = JSON.stringify(data, null, 2);
  $("#answer").className = `result ${data.status || ""}`;
  await refreshAudit();
});

refreshAudit();
