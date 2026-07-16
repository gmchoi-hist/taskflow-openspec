const API_BASE = window.location.origin;

function getToken() {
  return localStorage.getItem('token');
}

function setToken(token) {
  localStorage.setItem('token', token);
}

function clearToken() {
  localStorage.removeItem('token');
}

async function apiFetch(path, options = {}) {
  const headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, Object.assign({}, options, { headers }));
  } catch (networkErr) {
    throw Object.assign(new Error('네트워크 오류가 발생했습니다'), { code: 'NETWORK_ERROR' });
  }

  if (res.status === 401) {
    clearToken();
    if (!location.pathname.endsWith('login.html')) {
      location.href = '/login.html';
    }
    throw Object.assign(new Error('인증이 만료되었습니다'), { code: 'TOKEN_EXPIRED' });
  }

  let data = null;
  if (res.status !== 204) {
    data = await res.json().catch(() => null);
  }

  if (!res.ok) {
    const err = (data && data.error) || { code: 'UNKNOWN', message: '알 수 없는 오류가 발생했습니다' };
    throw Object.assign(new Error(err.message), err);
  }

  return data;
}

function requireAuthOrRedirect() {
  if (!getToken()) {
    location.href = '/login.html';
    return false;
  }
  return true;
}
