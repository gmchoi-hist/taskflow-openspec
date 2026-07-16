const API_BASE = window.location.origin;

function getToken() {
  return localStorage.getItem('token') || sessionStorage.getItem('token');
}

// remember=true(기본값): 브라우저를 닫아도 로그인 유지(localStorage)
// remember=false: 이 탭/창에서만 유지, 브라우저 종료 시 로그아웃(sessionStorage)
function setToken(token, remember = true) {
  if (remember) {
    localStorage.setItem('token', token);
    sessionStorage.removeItem('token');
  } else {
    sessionStorage.setItem('token', token);
    localStorage.removeItem('token');
  }
}

function clearToken() {
  localStorage.removeItem('token');
  sessionStorage.removeItem('token');
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

// 자동 로그인: 유효한 토큰이 있으면 폼을 보여주지 않고 바로 앱으로 이동한다.
// 반환값 true면 리다이렉트를 시작한 것이므로 호출부는 나머지 초기화를 건너뛰어야 한다.
async function autoLoginRedirectIfPossible() {
  if (!getToken()) return false;
  try {
    const me = await apiFetch('/auth/me');
    location.replace(me.team_id ? '/app.html' : '/team-select.html');
    return true;
  } catch (e) {
    return false;
  }
}
