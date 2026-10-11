"use strict";

// The lanes come from the manager, not from here: a board that invents its own
// column list drifts from the state machine the moment one changes.
let LANES = [];
let REPO = null;
let BOARD = null;
let RUNNING = {};
let SELECTED = null;
let STREAM = null;
const NEED_KINDS_FALLBACK = ["report.create", "report.update", "entity.create"];

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g,
  (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function toast(text, bad) {
  const el = $("toast");
  el.textContent = text;
  el.classList.remove("hidden");
  el.style.borderColor = bad ? "var(--bad)" : "var(--accent)";
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.add("hidden"), 6000);
}

async function api(path, options) {
  const res = await fetch(path, Object.assign({
    headers: { "Content-Type": "application/json" },
  }, options || {}));
  const text = await res.text();
  let doc = null;
  try { doc = text ? JSON.parse(text) : null; } catch (e) { doc = { raw: text }; }
  if (!res.ok) throw new Error((doc && doc.error) || res.statusText);
  return doc;
}

// -- loading ---------------------------------------------------------------

async function boot() {
  const repos = await api("/api/repos");
  REPO = repos[0];
  $("repo").textContent = REPO.path;
  const m = REPO.manager || {};
  $("contract").textContent = `${m.contract} v${m.contractVersion} · manager ${m.managerVersion}`;
  const sel = $("c-kind");
  (m.needKinds || NEED_KINDS_FALLBACK).forEach((k) => {
    const o = document.createElement("option");
    o.value = o.textContent = k;
    sel.appendChild(o);
  });
  await refresh();
  await health();
  setInterval(refresh, 3000);
  setInterval(health, 30000);
}

async function health() {
  try {
    const h = await api(`/api/repos/${REPO.id}/health`);
    const el = $("health");
    el.textContent = h.ok ? "پروتکل سالم" : "پروتکل نیاز به بررسی دارد";
    el.className = "pill " + (h.ok ? "ok" : "bad");
  } catch (e) {
    $("health").textContent = "بررسی انجام نشد";
    $("health").className = "pill";
  }
}

async function refresh() {
  try {
    BOARD = await api(`/api/repos/${REPO.id}/board`);
    RUNNING = await api(`/api/repos/${REPO.id}/running`);
    LANES = BOARD.lanes || LANES;
    drawBoard();
    drawWaiting();
    if (SELECTED) {
      const fresh = (BOARD.tasks || []).find((t) => t.id === SELECTED.id);
      if (fresh) { SELECTED = fresh; drawDrawer(); }
    }
  } catch (e) {
    toast("خواندن برد ناموفق: " + e.message, true);
  }
}

// -- board -----------------------------------------------------------------

function drawBoard() {
  const tasks = BOARD.tasks || [];
  $("board").innerHTML = LANES.map((lane) => {
    const rows = tasks.filter((t) => lane.states.includes(t.state));
    return `<div class="lane"><h2><span>${esc(lane.title)}</span>
      <span>${rows.length}</span></h2>
      ${rows.map(card).join("") || '<div class="dim" style="font-size:12px">—</div>'}
    </div>`;
  }).join("");
  document.querySelectorAll(".card").forEach((el) => {
    el.onclick = () => select(el.dataset.id);
  });
}

function card(t) {
  const gate = t.awaitingHuman || null;
  const run = RUNNING[t.id];
  const badges = [];
  if (gate && String(gate.kind).startsWith("role:")) {
    badges.push(`<span class="badge role">نقش ${esc(gate.kind.split(":")[1])}</span>`);
  } else if (gate) {
    badges.push(`<span class="badge gate">${esc(gate.kind)}</span>`);
  }
  if (run && run.running) badges.push('<span class="badge run">در اجرا</span>');
  else if (run && run.queued) badges.push('<span class="badge">در صف</span>');
  if (t.health && t.health.stuck) badges.push('<span class="badge stuck">گیرکرده</span>');
  if (t.blocker) badges.push(`<span class="badge stuck">${esc(t.blocker.kind)}</span>`);
  if (t.verify && t.verify.passed === false) badges.push('<span class="badge stuck">verification رد</span>');
  const need = (t.need && t.need.kind) || "";
  return `<div class="card" data-id="${esc(t.id)}">
    <div class="id">#${esc(t.id)} · ${esc(need)}</div>
    <div class="title">${esc(t.slug || t.title || "")}</div>
    <div class="badges">${badges.join("")}</div>
  </div>`;
}

function drawWaiting() {
  const rows = (BOARD.tasks || []).filter((t) => t.awaitingHuman &&
    !String(t.awaitingHuman.kind).startsWith("role:"));
  const box = $("waiting");
  if (!rows.length) { box.classList.add("hidden"); return; }
  box.classList.remove("hidden");
  $("waitingList").innerHTML = rows.map((t) =>
    `<button data-id="${esc(t.id)}">#${esc(t.id)} — ${esc(t.awaitingHuman.kind)}</button>`
  ).join("");
  $("waitingList").querySelectorAll("button").forEach((b) => {
    b.onclick = () => select(b.dataset.id);
  });
}

// -- drawer ----------------------------------------------------------------

function select(id) {
  SELECTED = (BOARD.tasks || []).find((t) => t.id === id) || null;
  if (!SELECTED) return;
  $("drawer").classList.remove("hidden");
  drawDrawer();
  openStream(id);
  loadEvents(id);
  if (SELECTED.awaitingHuman &&
      !String(SELECTED.awaitingHuman.kind).startsWith("role:")) tab("gate");
}

function tab(name) {
  document.querySelectorAll(".tabs button").forEach((b) =>
    b.classList.toggle("on", b.dataset.tab === name));
  document.querySelectorAll(".tab").forEach((d) =>
    d.classList.toggle("on", d.id === "tab-" + name));
}

function drawDrawer() {
  const t = SELECTED;
  $("drawerTitle").textContent = `#${t.id} ${t.slug || ""} — ${t.state}`;
  $("tab-overview").innerHTML = overview(t);
  $("tab-gate").innerHTML = gatePanel(t);
  $("tab-artifacts").innerHTML = artifacts(t);
  wireGate(t);
  $("tab-artifacts").querySelectorAll("button[data-path]").forEach((b) => {
    b.onclick = () => showArtifact(t.id, b.dataset.path);
  });
}

function overview(t) {
  const budget = Object.entries(t.budget || {}).map(([k, v]) =>
    `<tr><td>${esc(k)}</td><td>${v.used} / ${v.max}</td></tr>`).join("");
  const scope = ((t.scope || {}).allow || []).map((s) =>
    `<code>${esc(s)}</code>`).join("، ") || "<span class=dim>هنوز قفلی ندارد</span>";
  const v = t.verify || {};
  const gates = Object.entries(v.perGate || {}).map(([g, row]) =>
    `<tr><td>${esc(g)}</td><td class="${row.passed ? "ok" : "bad"}">${row.passed ? "پاس" : "رد"}</td>
     <td>${row.errors || 0}</td><td>${row.warnings || 0}</td></tr>`).join("");
  const findings = (v.findings || []).map((f) =>
    `<li><b>${esc(f.gate)}</b> — ${esc(f.message)} <span class=dim>${esc(f.where || "")}</span></li>`
  ).join("");
  const batch = t.batch || {};
  const rn = t.releaseNote;
  const rev = t.review;
  const evid = rev && rev.evidence ? Object.entries(rev.evidence).map(([k, rows]) =>
    `<h3>evidence.${esc(k)}</h3><table><tr><th>مورد</th><th>حکم</th><th>شاهد</th></tr>` +
    (rows || []).map((r) => `<tr><td>${esc(r.ac || r.case || r.check || "")}</td>
      <td class="${r.verdict === "pass" ? "ok" : r.verdict === "fail" ? "bad" : "warn"}">${esc(r.verdict)}</td>
      <td>${esc(r.basis || "")}</td></tr>`).join("") + "</table>").join("") : "";
  return `
  <table>
    <tr><th>وضعیت</th><td>${esc(t.state)} <span class=dim>(${esc(t.stateLane || "")})</span></td></tr>
    <tr><th>از</th><td class=dim>${esc(t.stateSince || "")}</td></tr>
    <tr><th>نیاز</th><td>${esc((t.need || {}).kind || "")} · سیستم ${esc((t.need || {}).system || "")}</td></tr>
    <tr><th>قفل scope</th><td>${scope}</td></tr>
    <tr><th>batch</th><td>${batch.path ? `${esc(batch.path)} · ${batch.commands} فرمان · <code>${esc(String(batch.sha256 || "").slice(0, 16))}</code>` : "<span class=dim>هنوز ساخته نشده</span>"}</td></tr>
    ${t.blocker ? `<tr><th>blocker</th><td class=bad>${esc(t.blocker.kind)} — ${esc(t.blocker.reason || "")}</td></tr>` : ""}
  </table>
  ${rn ? `<h3>release-note</h3><p>${rn.userVisible === false ? "<span class=dim>برای کاربر دیده نمی‌شود</span>" : esc(rn.headline || "")}
    ${rn.malformed ? `<span class=bad> — ${esc((rn.problems || []).join("، "))}</span>` : ""}</p>` : ""}
  <h3>بودجه</h3><table><tr><th>نقش</th><th>مصرف</th></tr>${budget}</table>
  <h3>verification</h3>
  ${gates ? `<table><tr><th>گیت</th><th>نتیجه</th><th>خطا</th><th>هشدار</th></tr>${gates}</table>` : "<p class=dim>هنوز اجرا نشده.</p>"}
  ${(v.disabled || []).length ? `<p class=warn>گیت غیرفعال: ${v.disabled.map((d) => esc(d.gate)).join("، ")}</p>` : ""}
  ${findings ? `<ul>${findings}</ul>` : ""}
  ${rev ? `<h3>داوری</h3><p>تصمیم: <b>${esc(rev.decision || "")}</b>
    ${rev.evidenceStatus === "malformed" ? '<span class=bad> — جدول شواهد خراب است</span>' :
      rev.evidenceStatus === "missing" ? '<span class=dim> — بدون بلوک شواهد</span>' : ""}</p>${evid}` : ""}
  <h3>تلاش‌ها</h3>
  <table><tr><th>#</th><th>نقش</th><th>outcome</th><th>درخواست</th></tr>
  ${(t.attempts || []).map((a) => `<tr><td>${a.id}</td><td>${esc(a.role || "")}</td>
    <td>${esc(a.outcome || "")}</td><td>${esc(a.requestedTransition || "")}</td></tr>`).join("")}</table>
  <h3>کارهای خطرناک</h3>
  <p class=hint>هر دو دلیل اجباری دارند و متن از فایل UTF-8 می‌رود، نه از خط فرمان.</p>
  <label>دلیل<textarea id="dangerReason" rows="2"></textarea></label>
  <div class="modal-actions">
    <button class="danger" id="btnVoid">برگرداندن آخرین transition</button>
    <button class="danger" id="btnCancel">بستن تسک</button>
    <button class="danger" id="btnUnlock">آزاد کردن قفل</button>
  </div>`;
}

function artifacts(t) {
  const files = (t.artifacts || []).map((f) =>
    `<li><button data-path="${esc(f)}">${esc(f)}</button></li>`).join("");
  const attempts = (t.attempts || []).map((a) =>
    `<li>attempt ${a.id} <span class=dim>${esc(a.role || "")}</span><ul>` +
    (a.artifacts || []).map((f) =>
      `<li><button data-path="attempts/${a.id}/${esc(f)}">${esc(f)}</button></li>`).join("") +
    "</ul></li>").join("");
  return `<ul>${files}</ul><h3>تلاش‌ها</h3><ul>${attempts}</ul>
    <pre id="artifactBox" class="hidden"></pre>`;
}

async function showArtifact(id, path) {
  try {
    const res = await fetch(`/api/repos/${REPO.id}/tasks/${id}/artifact?path=` +
      encodeURIComponent(path));
    const text = await res.text();
    const box = $("artifactBox");
    box.classList.remove("hidden");
    box.textContent = text;
    box.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (e) { toast(e.message, true); }
}

async function loadEvents(id) {
  try {
    const doc = await api(`/api/repos/${REPO.id}/tasks/${id}/events`);
    $("tab-events").innerHTML = `<table><tr><th>زمان</th><th>رویداد</th><th>جزئیات</th></tr>` +
      (doc.events || []).map((e) => {
        const rest = Object.entries(e).filter(([k]) =>
          !["at", "task", "event"].includes(k))
          .map(([k, v]) => `${k}=${esc(JSON.stringify(v))}`).join(" ");
        return `<tr><td class=dim>${esc((e.at || "").slice(11, 19))}</td>
          <td>${esc(e.event || "")}</td><td class=dim>${rest}</td></tr>`;
      }).join("") + "</table>";
  } catch (e) { $("tab-events").textContent = e.message; }
}

function openStream(id) {
  if (STREAM) STREAM.close();
  $("logBox").textContent = "";
  STREAM = new EventSource(`/api/repos/${REPO.id}/tasks/${id}/stream`);
  STREAM.onmessage = (ev) => {
    const box = $("logBox");
    box.textContent += JSON.parse(ev.data).line + "\n";
    box.scrollTop = box.scrollHeight;
  };
}

// -- the human gates -------------------------------------------------------

function gatePanel(t) {
  const gate = t.awaitingHuman;
  if (!gate) return "<p class=dim>این تسک منتظر پاسخی نیست.</p>";
  const kind = String(gate.kind);
  if (kind.startsWith("role:")) {
    const role = kind.split(":")[1];
    return `<div class="gate-box"><h3>منتظر نقش ${esc(role)}</h3>
      <p>این یک گیت انسانی نیست: نقش <b>${esc(role)}</b> باید فایل‌هایش را
      بنویسد و بعد «اجرا» زده شود. دستور کامل نقش:</p>
      <p><button data-path="${esc(gate.artifact || "")}" class="artifactLink">${esc(gate.artifact || "")}</button></p>
      <p class=hint>provider روی manual است، پس Manager هیچ agent صدا نمی‌زند.
      برای خودکار شدن، provider این نقش را در agent-runtime.yaml عوض کن.</p></div>`;
  }
  if (kind === "clarification") {
    return `<div class="gate-box"><h3>ابهام</h3>
      <p>پرسش‌ها در <code>questions.md</code> است (تب فایل‌ها).</p>
      <label>پاسخ تو<textarea id="clarifyText" rows="6"></textarea></label>
      <label class="row"><input type="checkbox" id="respec">
        این پاسخ خودِ spec را عوض می‌کند (respec): گیت spec-approval دوباره باز می‌شود</label>
      <div class="modal-actions"><button id="btnClarify" class="primary">ثبت پاسخ</button></div></div>`;
  }
  if (kind === "spec-approval") {
    return `<div class="gate-box"><h3>تأیید spec</h3>
      <p><code>proposed-task.md</code> را کنار <code>request.md</code> ببین
      (تب فایل‌ها). با تأیید، Manager همان متن را به‌عنوان <code>task.md</code>
      مهر می‌زند و hash می‌گیرد.</p>
      <label>دلیل رد، اگر رد می‌کنی<textarea id="specReason" rows="3"></textarea></label>
      <div class="modal-actions">
        <button id="btnSpecReject" class="danger">رد</button>
        <button id="btnSpecApprove" class="primary">تأیید spec</button>
      </div></div>`;
  }
  if (kind === "apply-approval") {
    const b = t.batch || {};
    const risky = (t.review && t.review.evidence &&
      (t.review.evidence.additionalChecks || []).filter((r) => r.verdict === "partial")) || [];
    const disabled = ((t.verify || {}).disabled || []);
    return `<div class="gate-box"><h3>اعمال روی بارسا</h3>
      <p>Manager هرگز خودش اعمال نمی‌کند — این مخزن به هیچ نصب بارسا وصل
      نمی‌شود. batch تأییدشده را خودت اعمال کن:</p>
      <div class="copy"><code id="batchPath">${esc(b.path || "")}</code>
        <button id="btnCopy">کپی مسیر</button></div>
      <p class=dim>sha256 <code>${esc(String(b.sha256 || "").slice(0, 32))}</code> · ${esc(String(b.commands))} فرمان</p>
      ${disabled.length ? `<p class=warn>هشدار: این گیت‌ها فعال نبودند: ${disabled.map((d) => esc(d.gate)).join("، ")}</p>` : ""}
      ${risky.length ? `<p class=warn>داوری این‌ها را باز گذاشته:<br>${risky.map((r) => esc(r.check) + " — " + esc(r.basis)).join("<br>")}</p>` : ""}
      <label class="row"><input type="checkbox" id="applyAck">
        این batch را روی بارسا اعمال کردم</label>
      <p class=hint>با تأیید، Manager مکانیکی اثبات می‌کند batch همان چیزی است
      که گیت رویش باز شد (مقایسهٔ sha256) و هنوز از همهٔ گیت‌ها رد می‌شود.
      حرف تو بدون این اثبات پذیرفته نمی‌شود.</p>
      <label>دلیل رد، اگر رد می‌کنی<textarea id="applyReason" rows="3"></textarea></label>
      <div class="modal-actions">
        <button id="btnApplyRejectImpl" class="danger">رد → implementer</button>
        <button id="btnApplyRejectArch" class="danger">رد → architect</button>
        <button id="btnApplyApprove" class="primary" disabled>تمام، ببند</button>
      </div></div>`;
  }
  return `<p>گیت ناشناس: ${esc(kind)}</p>`;
}

function wireGate(t) {
  const id = t.id;
  const post = async (path, body, ok) => {
    try {
      await api(`/api/repos/${REPO.id}/tasks/${id}/${path}`,
        { method: "POST", body: JSON.stringify(body) });
      toast(ok);
      await refresh();
    } catch (e) { toast(e.message, true); }
  };
  const on = (elId, fn) => { const el = $(elId); if (el) el.onclick = fn; };

  $("tab-gate").querySelectorAll("button.artifactLink").forEach((b) => {
    b.onclick = () => { tab("artifacts"); showArtifact(id, b.dataset.path); };
  });
  on("btnSpecApprove", () => post("answer", { approve: true }, "spec تأیید شد"));
  on("btnSpecReject", () => {
    const reason = ($("specReason") || {}).value || "";
    if (!reason.trim()) return toast("دلیل رد اجباری است.", true);
    post("answer", { reject: true, reason }, "spec رد شد");
  });
  on("btnClarify", () => {
    const text = ($("clarifyText") || {}).value || "";
    if (!text.trim()) return toast("پاسخ خالی است.", true);
    post("answer", { clarify: text, respec: $("respec").checked },
      "پاسخ ثبت شد");
  });
  const ack = $("applyAck");
  if (ack) ack.onchange = () => { $("btnApplyApprove").disabled = !ack.checked; };
  on("btnCopy", () => {
    navigator.clipboard.writeText($("batchPath").textContent.trim());
    toast("مسیر کپی شد");
  });
  on("btnApplyApprove", () => post("answer", { approve: true },
    "تسک بسته شد"));
  on("btnApplyRejectImpl", () => {
    const reason = ($("applyReason") || {}).value || "";
    if (!reason.trim()) return toast("دلیل رد اجباری است.", true);
    post("answer", { reject: true, reason, route: "implementer" },
      "برگشت به implementer");
  });
  on("btnApplyRejectArch", () => {
    const reason = ($("applyReason") || {}).value || "";
    if (!reason.trim()) return toast("دلیل رد اجباری است.", true);
    post("answer", { reject: true, reason, route: "architect" },
      "برگشت به architect");
  });
  for (const [btn, verb, msg] of [["btnVoid", "void", "برگشت انجام شد"],
                                  ["btnCancel", "cancel", "تسک بسته شد"],
                                  ["btnUnlock", "unlock", "قفل آزاد شد"]]) {
    on(btn, () => {
      const reason = ($("dangerReason") || {}).value || "";
      if (!reason.trim()) return toast("دلیل اجباری است.", true);
      if (!confirm("مطمئنی؟ این کار برگشت‌پذیر نیست.")) return;
      post(verb, { reason, force: verb === "unlock" }, msg);
    });
  }
}

// -- chrome ----------------------------------------------------------------

document.querySelectorAll(".tabs button").forEach((b) => {
  b.onclick = () => tab(b.dataset.tab);
});
$("closeDrawer").onclick = () => {
  $("drawer").classList.add("hidden");
  if (STREAM) { STREAM.close(); STREAM = null; }
  SELECTED = null;
};
$("runTask").onclick = async () => {
  if (!SELECTED) return;
  try {
    await api(`/api/repos/${REPO.id}/tasks/${SELECTED.id}/run`,
      { method: "POST", body: "{}" });
    tab("log");
    toast("اجرا شروع شد");
  } catch (e) { toast(e.message, true); }
};
$("newTask").onclick = () => $("createModal").classList.remove("hidden");
$("c-cancel").onclick = () => $("createModal").classList.add("hidden");
$("c-create").onclick = async () => {
  const draft = {
    slug: $("c-slug").value.trim(),
    kind: $("c-kind").value,
    system: $("c-system").value.trim(),
    requestText: $("c-text").value,
    start: $("c-start").checked,
  };
  if (!draft.slug || !draft.requestText.trim()) {
    return toast("slug و متن درخواست لازم‌اند.", true);
  }
  try {
    const res = await api("/api/tasks/create",
      { method: "POST", body: JSON.stringify({ drafts: [draft] }) });
    const row = res.results[0];
    if (!row.ok) throw new Error(row.message);
    $("createModal").classList.add("hidden");
    $("c-slug").value = ""; $("c-text").value = "";
    toast(`تسک ${row.taskId} ساخته شد`);
    await refresh();
    select(row.taskId);
  } catch (e) { toast(e.message, true); }
};

boot().catch((e) => toast("راه‌اندازی ناموفق: " + e.message, true));
