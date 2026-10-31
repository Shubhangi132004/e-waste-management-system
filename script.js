
async function loadPersonalData() {
  const reportList = document.getElementById('myReports');
  const collectionList = document.getElementById('myCollections');
  if (!reportList || !collectionList) return;
  try {
    const me = await apiFetch('/api/auth/me');
    if (!me.authenticated) { reportList.textContent = 'Sign in to view your reports.'; collectionList.textContent = 'Sign in to request collection.'; return; }
    const [reportData, collectionData] = await Promise.all([apiFetch('/api/reports'), apiFetch('/api/collections')]);
    reportList.replaceChildren(); collectionList.replaceChildren();
    const reportHeading = document.createElement('h3'); reportHeading.textContent = 'Your reports'; reportList.appendChild(reportHeading);
    reportData.reports.forEach((report) => { const item = document.createElement('div'); item.className = 'activity-item'; item.textContent = `#${report.id} · ${report.issue_type} · ${report.status} · ${new Date(report.created_at).toLocaleDateString()}`; reportList.appendChild(item); });
    if (!reportData.reports.length) reportList.append('No reports submitted yet.');
    const collectionHeading = document.createElement('h3'); collectionHeading.textContent = 'Your collection requests'; collectionList.appendChild(collectionHeading);
    collectionData.collection_requests.forEach((item) => { const row = document.createElement('div'); row.className = 'activity-item'; row.textContent = `${item.category} · ${item.collection_status} · ${item.preferred_date}`; collectionList.appendChild(row); });
    if (!collectionData.collection_requests.length) collectionList.append('No collection requests yet.');
  } catch (error) { reportList.textContent = error.message; collectionList.textContent = error.message; }
}
const collectionForm = document.getElementById('collectionForm');
collectionForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = document.getElementById('collectionMessage');
  const button = collectionForm.querySelector('button'); button.disabled = true; message.textContent = '';
  try { await apiFetch('/api/collections', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category: document.getElementById('collectionCategory').value, collection_address: document.getElementById('collectionAddress').value, preferred_date: document.getElementById('preferredDate').value, notes: document.getElementById('collectionNotes').value }) }); collectionForm.reset(); message.textContent = 'Collection request submitted.'; loadPersonalData(); }
  catch (error) { message.textContent = error.message; }
  finally { button.disabled = false; }
});
loadPersonalData();
