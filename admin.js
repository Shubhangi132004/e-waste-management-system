let csrfToken = null;
async function getCsrfToken() { if (csrfToken) return csrfToken; const response = await fetch('/api/csrf-token'); if (!response.ok) throw new Error('Secure session unavailable.'); csrfToken = (await response.json()).csrf_token; return csrfToken; }
async function apiFetch(path, options = {}) { const headers = new Headers(options.headers || {}); if ((options.method || 'GET') !== 'GET') headers.set('X-CSRFToken', await getCsrfToken()); const response = await fetch(path, { ...options, headers }); const result = await response.json().catch(() => ({})); if (!response.ok) throw new Error(result.error || 'Request failed.'); return result; }

const tableBody = document.getElementById('reportBody');
const emptyState = document.getElementById('emptyState');
let statusChart;
let issueChart;
let reports = [];

function addCell(row, value) { const cell = document.createElement('td'); cell.textContent = value ?? '—'; row.appendChild(cell); return cell; }
function renderReports() {
  tableBody.replaceChildren();
  if (!reports.length) { emptyState.hidden = false; return; }
  emptyState.hidden = true;
  reports.forEach((report) => {
    const row = document.createElement('tr');
    addCell(row, report.id); addCell(row, report.name); addCell(row, report.location); addCell(row, report.issue_type);
    const imageCell = document.createElement('td');
    if (report.image_url) { const link = document.createElement('a'); link.href = report.image_url; link.target = '_blank'; link.rel = 'noopener'; const image = document.createElement('img'); image.src = report.image_url; image.alt = `Report ${report.id} upload`; image.className = 'report-img'; link.appendChild(image); imageCell.appendChild(link); } else imageCell.textContent = 'No image';
    row.appendChild(imageCell);
    const gpsCell = document.createElement('td');
    if (report.latitude !== null && report.longitude !== null) { const link = document.createElement('a'); link.className = 'gps-btn'; link.href = `https://www.google.com/maps?q=${encodeURIComponent(`${report.latitude},${report.longitude}`)}`; link.target = '_blank'; link.rel = 'noopener'; link.textContent = '📍 View'; gpsCell.appendChild(link); } else gpsCell.textContent = 'Not available';
    row.appendChild(gpsCell);
    const statusCell = addCell(row, report.status); statusCell.className = `status-${report.status.toLowerCase().replaceAll(' ', '-')}`;
    const actionCell = document.createElement('td');
    const update = document.createElement('button'); update.className = 'update-btn'; update.textContent = 'Update'; update.addEventListener('click', () => updateStatus(report.id));
    const remove = document.createElement('button'); remove.className = 'delete-btn'; remove.textContent = 'Delete'; remove.addEventListener('click', () => deleteReport(report.id)); actionCell.append(update, remove); row.appendChild(actionCell); tableBody.appendChild(row);
  });
}

async function loadReports() { const search = encodeURIComponent(document.getElementById('searchInput').value.trim()); const status = encodeURIComponent(document.getElementById('statusFilter').value); try { const result = await apiFetch(`/api/admin/reports?search=${search}&status=${status}`); reports = result.reports; renderReports(); } catch (error) { tableBody.replaceChildren(); const row = document.createElement('tr'); const cell = document.createElement('td'); cell.colSpan = 8; cell.textContent = error.message; row.appendChild(cell); tableBody.appendChild(row); } }
async function loadStats() { const data = await apiFetch('/api/stats'); document.getElementById('totalReports').textContent = data.total_reported; document.getElementById('pendingReports').textContent = data.pending; document.getElementById('progressReports').textContent = data.in_progress; document.getElementById('resolvedReports').textContent = data.resolved; return data; }
async function loadCharts() { const data = await apiFetch('/api/stats'); const statuses = ['Pending', 'In Progress', 'Resolved']; const statusValues = statuses.map((status) => data.status.find((item) => item.status === status)?.total || 0); statusChart?.destroy(); statusChart = new Chart(document.getElementById('statusChart'), { type: 'pie', data: { labels: statuses, datasets: [{ data: statusValues, backgroundColor: ['#f59e0b', '#3b82f6', '#22c55e'] }] }, options: { responsive: true, maintainAspectRatio: false } }); issueChart?.destroy(); issueChart = new Chart(document.getElementById('issueChart'), { type: 'bar', data: { labels: data.issues.map((item) => item.issue_type), datasets: [{ label: 'Reports', data: data.issues.map((item) => item.total), backgroundColor: '#16a34a' }] }, options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } } }); }
async function refresh() { await Promise.all([loadReports(), loadStats(), loadCharts()]); }
async function updateStatus(id) { const status = prompt('Enter status: Pending, In Progress, or Resolved'); if (!['Pending', 'In Progress', 'Resolved'].includes(status)) return; try { await apiFetch(`/api/admin/reports/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) }); await refresh(); } catch (error) { alert(error.message); } }
async function deleteReport(id) { if (!confirm('Delete this report and its uploaded image? This cannot be undone.')) return; try { await apiFetch(`/api/admin/reports/${id}`, { method: 'DELETE' }); await refresh(); } catch (error) { alert(error.message); } }

document.getElementById('searchInput').addEventListener('input', loadReports);
document.getElementById('statusFilter').addEventListener('change', loadReports);
document.getElementById('exportBtn').addEventListener('click', () => { const { jsPDF } = window.jspdf; const doc = new jsPDF(); doc.text('EcoSmart Waste Reports', 14, 18); doc.autoTable({ head: [['ID', 'Name', 'Location', 'Category', 'Status']], body: reports.map((report) => [report.id, report.name, report.location, report.issue_type, report.status]), startY: 30, theme: 'grid' }); doc.save('EcoSmart_Reports.pdf'); });
document.getElementById('logoutBtn').addEventListener('click', async () => { try { await apiFetch('/api/auth/logout', { method: 'POST' }); window.location.href = '/login'; } catch (error) { alert(error.message); } });
refresh().catch((error) => { alert(error.message); });
