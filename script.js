"use strict";

let csrfTokenPromise;

async function getCsrfToken() {
  if (!csrfTokenPromise) {
    csrfTokenPromise = fetch("/api/csrf-token", { credentials: "same-origin" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Could not start a secure session.");
        return (await response.json()).csrf_token;
      })
      .catch((error) => {
        csrfTokenPromise = null;
        throw error;
      });
  }
  return csrfTokenPromise;
}

async function apiFetch(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    headers.set("X-CSRFToken", await getCsrfToken());
  }
  const response = await fetch(path, { ...options, method, headers, credentials: "same-origin" });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status}).`);
  return payload;
}
window.apiFetch = apiFetch;

function showMessage(element, message, isError = false) {
  if (!element) return;
  element.textContent = message;
  element.classList.toggle("is-error", isError);
  element.classList.toggle("is-success", !isError && Boolean(message));
}
function closePopup() { document.getElementById("popup")?.classList.remove("is-visible"); }
function closeMobile() { document.getElementById("mobileMenu")?.classList.remove("open"); }
window.closePopup = closePopup;
window.closeMobile = closeMobile;

async function loadDashboardStats() {
  const stats = await apiFetch("/api/stats");
  const values = { statReported: stats.total_reported, statPending: stats.pending, statProgress: stats.in_progress, statResolved: stats.resolved, heroReportCount: stats.total_reported };
  for (const [id, value] of Object.entries(values)) {
    const node = document.getElementById(id);
    if (node) node.textContent = String(value ?? 0);
  }
  const activity = document.getElementById("activityList");
  if (!activity) return;
  activity.replaceChildren();
  if (!stats.recent_reports?.length) {
    activity.textContent = "No reports have been submitted yet.";
    return;
  }
  stats.recent_reports.forEach((report) => {
    const item = document.createElement("div"); item.className = "activity-item";
    const dot = document.createElement("span"); dot.className = "act-dot"; dot.setAttribute("aria-hidden", "true");
    const text = document.createElement("span"); text.className = "act-text";
    text.textContent = `Report #${report.id} · ${report.issue_type} · ${report.status}`;
    const time = document.createElement("span"); time.className = "act-time"; time.textContent = new Date(report.created_at).toLocaleString();
    item.append(dot, text, time); activity.appendChild(item);
  });
}

async function loadPersonalData() {
  const reportList = document.getElementById("myReports");
  const collectionList = document.getElementById("myCollections");
  if (!reportList || !collectionList) return;
  try {
    const me = await apiFetch("/api/auth/me");
    if (!me.authenticated) {
      reportList.textContent = "Sign in to view your reports.";
      collectionList.textContent = "Sign in to request collection.";
      return;
    }
    const [reportData, collectionData] = await Promise.all([apiFetch("/api/reports"), apiFetch("/api/collections")]);
    reportList.replaceChildren(); collectionList.replaceChildren();
    const reportHeading = document.createElement("h3"); reportHeading.textContent = "Your reports"; reportList.appendChild(reportHeading);
    reportData.reports.forEach((report) => {
      const item = document.createElement("div"); item.className = "activity-item";
      item.textContent = `#${report.id} · ${report.issue_type} · ${report.status} · ${new Date(report.created_at).toLocaleDateString()}`;
      reportList.appendChild(item);
    });
    if (!reportData.reports.length) reportList.append("No reports submitted yet.");
    const collectionHeading = document.createElement("h3"); collectionHeading.textContent = "Your collection requests"; collectionList.appendChild(collectionHeading);
    collectionData.collection_requests.forEach((item) => {
      const row = document.createElement("div"); row.className = "activity-item";
      row.textContent = `${item.category} · ${item.collection_status} · ${item.preferred_date}`; collectionList.appendChild(row);
    });
    if (!collectionData.collection_requests.length) collectionList.append("No collection requests yet.");
  } catch (error) {
    reportList.textContent = error.message; collectionList.textContent = error.message;
  }
}

const reportForm = document.getElementById("reportForm");
reportForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!reportForm.reportValidity()) return;
  const message = document.getElementById("formMessage");
  const button = document.getElementById("submitBtn");
  const buttonText = button?.querySelector(".btn-text");
  const loader = button?.querySelector(".btn-loader");
  if (button) button.disabled = true;
  buttonText?.classList.add("hidden"); loader?.classList.remove("hidden");
  showMessage(message, "Submitting your report…");
  try {
    const result = await apiFetch("/api/reports", { method: "POST", body: new FormData(reportForm) });
    reportForm.reset(); showMessage(message, "");
    const popupId = document.getElementById("popupId");
    if (popupId) popupId.textContent = `Report ID: ${result.issue_id}`;
    document.getElementById("popup")?.classList.add("is-visible");
    await loadDashboardStats();
  } catch (error) {
    showMessage(message, error.message, true);
  } finally {
    if (button) button.disabled = false;
    buttonText?.classList.remove("hidden"); loader?.classList.add("hidden");
  }
});

const aiSuggestButton = document.getElementById("aiSuggestBtn");
aiSuggestButton?.addEventListener("click", async () => {
  const description = document.getElementById("description")?.value.trim() || "";
  const message = document.getElementById("aiSuggestion");
  const categorySelect = document.getElementById("issueType");
  if (!description) { showMessage(message, "Describe the electronic item or problem first.", true); return; }
  aiSuggestButton.disabled = true; aiSuggestButton.textContent = "Analysing locally…";
  try {
    const result = await apiFetch("/api/ai/suggest-category", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: description }),
    });
    message.replaceChildren();
    const explanation = document.createElement("span");
    const rankedScores = result.alternatives.map((item) => `${item.category} (${(item.model_score * 100).toFixed(1)}%)`).join(" · ");
    explanation.textContent = `Local AI suggestion: ${result.suggested_category}. Top model scores (not calibrated): ${rankedScores}. Please check the category; this is not a guarantee.`;
    const choose = document.createElement("button"); choose.type = "button"; choose.className = "btn-ghost ai-use-button"; choose.textContent = "Use this suggestion";
    choose.addEventListener("click", () => {
      categorySelect.value = result.suggested_category; categorySelect.focus();
      showMessage(message, `${result.suggested_category} selected. Review it before submitting.`);
    });
    message.append(explanation, choose);
  } catch (error) { showMessage(message, error.message, true); }
  finally { aiSuggestButton.disabled = false; aiSuggestButton.textContent = "Suggest a category with local AI"; }
});

const collectionForm = document.getElementById("collectionForm");
collectionForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!collectionForm.reportValidity()) return;
  const message = document.getElementById("collectionMessage");
  const button = collectionForm.querySelector('button[type="submit"]');
  if (button) button.disabled = true;
  showMessage(message, "");
  try {
    await apiFetch("/api/collections", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category: document.getElementById("collectionCategory").value, collection_address: document.getElementById("collectionAddress").value, preferred_date: document.getElementById("preferredDate").value, notes: document.getElementById("collectionNotes").value }),
    });
    collectionForm.reset(); showMessage(message, "Demo collection request saved."); await loadPersonalData();
  } catch (error) { showMessage(message, error.message, true); }
  finally { if (button) button.disabled = false; }
});

const gpsButton = document.getElementById("gpsBtn");
gpsButton?.addEventListener("click", () => {
  const message = document.getElementById("formMessage");
  if (!navigator.geolocation) { showMessage(message, "Location is not available in this browser.", true); return; }
  gpsButton.disabled = true; showMessage(message, "Requesting location permission…");
  navigator.geolocation.getCurrentPosition(
    (position) => {
      document.getElementById("latitude").value = position.coords.latitude;
      document.getElementById("longitude").value = position.coords.longitude;
      showMessage(message, "Location added. Remove it if you do not want to share it."); gpsButton.disabled = false;
    },
    () => { showMessage(message, "Location was not added. Check browser permission or enter the area manually.", true); gpsButton.disabled = false; },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 },
  );
});

const hamburger = document.getElementById("hamburger");
hamburger?.addEventListener("click", () => document.getElementById("mobileMenu")?.classList.toggle("open"));
const darkToggle = document.getElementById("darkToggle");
const savedTheme = localStorage.getItem("ecosmart-theme");
if (savedTheme === "dark" || savedTheme === "light") document.documentElement.dataset.theme = savedTheme;
const initialThemeIcon = darkToggle?.querySelector(".toggle-icon");
if (initialThemeIcon && savedTheme === "dark") initialThemeIcon.textContent = "☀️";
darkToggle?.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next; localStorage.setItem("ecosmart-theme", next);
  const icon = darkToggle.querySelector(".toggle-icon"); if (icon) icon.textContent = next === "dark" ? "☀️" : "🌙";
});
document.getElementById("popup")?.addEventListener("click", (event) => { if (event.target.id === "popup") closePopup(); });
document.addEventListener("keydown", (event) => { if (event.key === "Escape") closePopup(); });
const preferredDate = document.getElementById("preferredDate");
if (preferredDate) {
  const localToday = new Date();
  localToday.setMinutes(localToday.getMinutes() - localToday.getTimezoneOffset());
  preferredDate.min = localToday.toISOString().slice(0, 10);
}
const copyright = document.getElementById("copyright");
if (copyright) copyright.textContent = `© ${new Date().getFullYear()} EcoSmart Academic Project. Demo only.`;
loadDashboardStats().catch(() => {
  const activity = document.getElementById("activityList");
  if (activity) activity.textContent = "Dashboard data is temporarily unavailable.";
});
loadPersonalData();
