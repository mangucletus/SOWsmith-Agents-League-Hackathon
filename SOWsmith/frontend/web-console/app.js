"use strict";
// Bid Package Agent console — vanilla JS, talks to the Python JSON API.
// All server-supplied values are inserted via textContent / DOM nodes (no innerHTML) to avoid XSS.

const $ = (s) => document.querySelector(s);
const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
async function api(path, method = "GET", body) {
  const opt = { method, headers: { "Content-Type": "application/json" } };
  if (body) opt.body = JSON.stringify(body);
  const r = await fetch(path, opt);
  return r.json();
}

let CURRENT_DRAFT = null; // { filename }

// ---------------- mode switching ----------------
function activateMode(mode) {
  const btn = document.querySelector(`.mode[data-mode="${mode}"]`);
  if (!btn) return;
  document.querySelectorAll(".mode").forEach((x) => x.classList.remove("active"));
  btn.classList.add("active");
  document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
  $("#panel-" + mode).classList.add("active");
  if (mode === "audit") loadAudit();
}
document.querySelectorAll(".mode").forEach((b) => b.addEventListener("click", () => activateMode(b.dataset.mode)));
window.addEventListener("hashchange", () => { const m = location.hash.replace("#", ""); if (m) activateMode(m); });

// ---------------- boot ----------------
async function boot() {
  try {
    const h = await api("/api/health");
    if (h.backend === "offline-mock") $("#backend").classList.add("mock");
    $("#backendText").textContent = h.backend === "azure-openai"
      ? "Azure OpenAI (live grounding)" : "Offline mock (plumbing demo)";
  } catch { $("#backendText").textContent = "API offline"; }

  try {
    const kb = await api("/api/kb");
    $("#kbExemplars").textContent = kb.exemplars.length;
    $("#kbReference").textContent = kb.reference_count;
    $("#kbReviewers").textContent = kb.service_types.length;
    const sel = $("#dType"), eSel = $("#eType");
    kb.service_types.forEach((t) => {
      const o = el("option", null, t); o.value = t; sel.appendChild(o);
      const o2 = el("option", null, t); o2.value = t; eSel.appendChild(o2);
    });
    [sel, eSel].forEach((s) => { if ([...s.options].some((o) => o.value === "Pipeline Construction")) s.value = "Pipeline Construction"; });
  } catch { /* ignore */ }

  const suggest = ["What does our standard hydrotesting scope include?",
    "What is excluded from a facility maintenance SOW?",
    "Which clauses require Legal/Contracts review?",
    "How do bidders submit a proposal?"];
  const box = $("#askSuggest");
  suggest.forEach((q) => { const b = el("button", null, q); b.onclick = () => { $("#askInput").value = q; $("#askForm").requestSubmit(); }; box.appendChild(b); });

  greet();
  const initial = location.hash.replace("#", "");
  if (initial) activateMode(initial);
}

function greet() {
  addMsg("agent", "Hi! I can answer questions about SOWsmith's prior bid packages and the clause library — and I'll cite my sources. Try a suggestion below, or ask your own.");
}

// ---------------- ASK (Flow A) ----------------
function addMsg(role, text) {
  const m = el("div", "msg " + role);
  m.appendChild(el("div", "who", role === "user" ? "You" : "Bid Package Agent"));
  m.appendChild(el("div", "bubble", text));
  $("#chat").appendChild(m);
  $("#chat").scrollTop = $("#chat").scrollHeight;
  return m;
}
$("#askForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = $("#askInput").value.trim(); if (!q) return;
  addMsg("user", q); $("#askInput").value = "";
  const pending = addMsg("agent", "…thinking…");
  try {
    const res = await api("/api/ask", "POST", { question: q });
    pending.querySelector(".bubble").textContent = res.answer || "(no answer)";
    if (res.citations && res.citations.length) {
      const c = el("div", "cites");
      res.citations.forEach((ci) => c.appendChild(el("span", "cite", ci.title)));
      pending.appendChild(c);
    }
  } catch { pending.querySelector(".bubble").textContent = "Sorry — the API is unavailable."; }
});

// ---------------- DRAFT (Flow B) ----------------
$("#draftForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("#dGenerate"); btn.disabled = true;
  btn.replaceChildren(el("span", "spinner"), document.createTextNode("Generating…"));
  const payload = {
    service_type: $("#dType").value,
    document_type: $("#dDoc").value,
    project_context: $("#dContext").value.trim(),
    special_requirements: $("#dSpecial").value.trim(),
  };
  try {
    renderDraft(await api("/api/draft", "POST", payload));
  } catch {
    $("#draftOut").replaceChildren(el("div", "outcome bad", "The API is unavailable."));
  } finally { btn.disabled = false; btn.textContent = "Generate draft"; }
});

function renderDraft(res) {
  const out = $("#draftOut"); out.replaceChildren();
  if (res.error) { out.appendChild(el("div", "outcome bad", res.error)); return; }
  if (res.refused) {
    const bar = el("div", "statusbar"); bar.appendChild(el("span", "badge refused", "REFUSED"));
    out.appendChild(bar);
    out.appendChild(el("div", "outcome bad", res.text));
    CURRENT_DRAFT = null; return;
  }
  CURRENT_DRAFT = { filename: res.filename };

  const bar = el("div", "statusbar");
  const legal = res.review_status && res.review_status.toUpperCase().includes("LEGAL");
  bar.appendChild(el("span", "badge " + (legal ? "legal" : "standard"), res.review_status));
  const meta = el("div", "meta");
  meta.appendChild(el("b", null, res.document_type || "SOW"));
  meta.appendChild(document.createTextNode("  ·  Reviewer: "));
  meta.appendChild(el("b", null, res.reviewer + (res.cc ? ` (cc ${res.cc})` : "")));
  meta.appendChild(document.createTextNode("  ·  Sections: "));
  meta.appendChild(el("b", null, `${res.sections_present}/7`));
  if (res.legal_reasons && res.legal_reasons.length) {
    meta.appendChild(document.createTextNode("  ·  Flagged: "));
    meta.appendChild(el("b", null, res.legal_reasons.join(", ")));
  }
  bar.appendChild(meta);
  out.appendChild(bar);

  out.appendChild(el("div", "sop", res.text));

  if (res.open_questions && res.open_questions.length) {
    const oq = el("div", "openq"); oq.appendChild(el("h4", null, "Open questions"));
    const ul = el("ul"); res.open_questions.forEach((q) => ul.appendChild(el("li", null, q)));
    oq.appendChild(ul); out.appendChild(oq);
  }

  const qa = el("div", "openq");
  if (res.validation && res.validation.length) {
    qa.appendChild(el("h4", null, "Automated QA — read these lines carefully"));
    const ul = el("ul");
    res.validation.forEach((f) => ul.appendChild(el("li", null, `[${f.code}] ${f.message}`)));
    qa.appendChild(ul);
  } else {
    qa.appendChild(el("p", null, "Automated QA: no issues found (deterministic, zero-token check — still review every line)."));
  }
  out.appendChild(qa);

  const dec = el("div", "decide");
  dec.appendChild(el("h4", null, "Reviewer decision"));
  dec.appendChild(el("p", null, "In production a reviewer makes this call from an Adaptive Card in Teams. Simulate it here:"));
  const btns = el("div", "btns");
  [["Approve", "btn-approve"], ["Request Changes", "btn-changes"], ["Reject", "btn-reject"]]
    .forEach(([label, cls]) => { const b = el("button", cls, label); b.onclick = () => review(label, dec); btns.appendChild(b); });
  dec.appendChild(btns);
  out.appendChild(dec);
}

async function review(decision, decEl) {
  if (!CURRENT_DRAFT) return;
  const res = await api("/api/review", "POST",
    { filename: CURRENT_DRAFT.filename, decision, comments: "Reviewed via console" });
  const old = decEl.querySelector(".outcome"); if (old) old.remove();
  let cls = "ok", msg;
  if (res.error) { cls = "bad"; msg = res.error; }
  else if (decision === "Approve") msg = `Approved — moved to the “${res.final_library}” library, version incremented, and logged to the audit trail.`;
  else if (decision === "Reject") { cls = "bad"; msg = `Rejected — moved to the “${res.final_library}” library; the author may resubmit. Logged.`; }
  else { cls = "warn"; msg = "Changes requested — the draft stays in Drafts for revision; comments logged."; }
  decEl.appendChild(el("div", "outcome " + cls, msg));
}

// ---------------- AUDIT ----------------
async function loadAudit() {
  const body = $("#auditBody"); body.replaceChildren();
  const res = await api("/api/audit");
  const rows = res.rows || [];
  $("#auditEmpty").style.display = rows.length ? "none" : "block";
  $("#auditTable").style.display = rows.length ? "table" : "none";
  rows.slice().reverse().forEach((r) => {
    const tr = el("tr");
    tr.appendChild(el("td", "tag-mono", (r.Timestamp || "").replace("T", " ").replace("+00:00", "Z")));
    tr.appendChild(el("td", "act", r.Action));
    tr.appendChild(el("td", null, r.ReviewStatus));
    tr.appendChild(el("td", "tag-mono", r.DraftFileName));
    tr.appendChild(el("td", null, r.Reviewer));
    tr.appendChild(el("td", null, r.Comments));
    body.appendChild(tr);
  });
}

// ---------------- EVALUATE (WS-4) ----------------
const SAMPLE_BIDS = [
  { bidder: "Permian Pipeline LLC", total_price: 1250000, schedule_days: 45, exclusions: ["permits"], terms: "Standard SOWsmith terms accepted." },
  { bidder: "Lone Star Pipeliners", total_price: 1180000, schedule_days: 50, exclusions: ["permits", "site restoration"], terms: "Requests net-90 payment terms and a liquidated damages cap." },
  { bidder: "West Texas Welding & Construction", total_price: 1420000, schedule_days: 40, exclusions: ["permits"], terms: "Standard SOWsmith terms accepted." },
];
$("#eSample").addEventListener("click", () => { $("#eBids").value = JSON.stringify(SAMPLE_BIDS, null, 2); });
$("#evalForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  let bids;
  try { bids = JSON.parse($("#eBids").value || "[]"); }
  catch { $("#evalOut").replaceChildren(el("div", "outcome bad", "Bidder responses must be valid JSON (an array of objects). Try “Load sample bids”.")); return; }
  const btn = $("#eEvaluate"); btn.disabled = true;
  btn.replaceChildren(el("span", "spinner"), document.createTextNode("Evaluating…"));
  try {
    renderEvaluation(await api("/api/evaluate", "POST",
      { service_type: $("#eType").value, document_type: $("#eDoc").value, bids }));
  } catch {
    $("#evalOut").replaceChildren(el("div", "outcome bad", "The API is unavailable."));
  } finally { btn.disabled = false; btn.textContent = "Evaluate"; }
});

function renderEvaluation(res) {
  const out = $("#evalOut"); out.replaceChildren();
  if (res.error) { out.appendChild(el("div", "outcome bad", res.error)); return; }

  const bar = el("div", "statusbar");
  const legal = res.review_status && res.review_status.toUpperCase().includes("LEGAL");
  bar.appendChild(el("span", "badge " + (legal ? "legal" : "standard"), res.review_status));
  const meta = el("div", "meta");
  meta.appendChild(el("b", null, "Recommended: " + (res.recommended || "none")));
  meta.appendChild(document.createTextNode("  ·  Approver: "));
  meta.appendChild(el("b", null, res.approver + (res.cc ? ` (cc ${res.cc})` : "")));
  if (res.legal_reasons && res.legal_reasons.length) {
    meta.appendChild(document.createTextNode("  ·  Flagged: "));
    meta.appendChild(el("b", null, res.legal_reasons.join(", ")));
  }
  bar.appendChild(meta); out.appendChild(bar);

  const tbl = el("table", "audit");
  const thead = el("thead"), htr = el("tr");
  ["Bidder", "Total (USD)", "Schedule", "Exclusions", "Non-standard terms", "Status"].forEach((h) => htr.appendChild(el("th", null, h)));
  thead.appendChild(htr); tbl.appendChild(thead);
  const tb = el("tbody");
  (res.rows || []).forEach((r) => {
    const tr = el("tr");
    tr.appendChild(el("td", null, r.bidder));
    tr.appendChild(el("td", null, r.total_price != null ? "$" + Number(r.total_price).toLocaleString() : "— (no bid)"));
    tr.appendChild(el("td", null, r.schedule_days ? `${r.schedule_days} days` : "—"));
    tr.appendChild(el("td", null, String(r.n_exclusions)));
    tr.appendChild(el("td", null, (r.legal_flags && r.legal_flags.length) ? r.legal_flags.join(", ") : "—"));
    tr.appendChild(el("td", null, r.compliant ? "compliant" : "INCOMPLETE"));
    tb.appendChild(tr);
  });
  tbl.appendChild(tb); out.appendChild(tbl);

  if (res.reasons && res.reasons.length) {
    out.appendChild(el("h4", null, "Why")); const ul = el("ul");
    res.reasons.forEach((r) => ul.appendChild(el("li", null, r))); out.appendChild(ul);
  }
  if (res.risks && res.risks.length) {
    out.appendChild(el("h4", null, "Risks & flags")); const ul = el("ul");
    res.risks.forEach((r) => ul.appendChild(el("li", null, r))); out.appendChild(ul);
  }
  out.appendChild(el("p", null, "Approvals: Supply Chain manager · PM"
    + (legal ? " · Legal/Contracts" : "") + (res.finance_signoff ? " · Finance" : "")
    + " — a human awards (never auto-awarded)."));
}

boot();
