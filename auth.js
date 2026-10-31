async function getCsrfToken() {
  const response = await fetch('/api/csrf-token');
  if (!response.ok) throw new Error('Could not start a secure session.');
  return (await response.json()).csrf_token;
}

document.getElementById('authForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const message = document.getElementById('message');
  const button = form.querySelector('button');
  button.disabled = true;
  message.textContent = '';
  try {
    const csrf = await getCsrfToken();
    const payload = { email: document.getElementById('email').value, password: document.getElementById('password').value };
    const name = document.getElementById('full_name');
    if (name) payload.full_name = name.value;
    const endpoint = name ? '/api/auth/register' : '/api/auth/login';
    const response = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf }, body: JSON.stringify(payload) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Request failed.');
    window.location.href = result.redirect || '/';
  } catch (error) {
    message.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});
