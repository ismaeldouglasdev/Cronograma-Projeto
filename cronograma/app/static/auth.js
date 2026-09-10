const Auth = (function() {
  const TOKEN_KEY = 'cronograma_token';

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  function getCurrentUser() {
    const token = getToken();
    if (!token) return null;
    try {
      const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      const padded = b64 + '='.repeat((4 - (b64.length % 4)) % 4);
      return JSON.parse(atob(padded));
    } catch (e) {
      return null;
    }
  }

  function isGuest() {
    const payload = getCurrentUser();
    return payload && payload.guest === true;
  }

  let refreshPromise = null;

  function refreshSession() {
    if (!refreshPromise) {
      refreshPromise = fetch('/auth/refresh', { method: 'POST' })
        .then(async (response) => {
          if (!response.ok) return null;
          const data = await parseJsonSafe(response, 'refresh');
          if (data && data.access_token) {
            setToken(data.access_token);
            return data.access_token;
          }
          return null;
        })
        .catch(() => null)
        .finally(() => { refreshPromise = null; });
    }
    return refreshPromise;
  }

  async function parseJsonSafe(response, fallbackMsg) {
    try {
      return await response.json();
    } catch (e) {
      const status = response ? response.status : 0;
      const suffix = status >= 500 || status === 0 ? ` (HTTP ${status})` : '';
      return { detail: fallbackMsg + suffix, _unparseable: true };
    }
  }

  async function apiFetch(url, options = {}, retried = false) {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401 && !retried && !url.startsWith('/auth/')) {
      const newToken = await refreshSession();
      if (newToken) {
        return apiFetch(url, options, true);
      }
    }
    if (response.status === 401) {
      clearToken();
      showLoginScreen();
    }
    return response;
  }

  async function checkAuth() {
    const token = getToken();
    if (!token) {
      showLoginScreen();
      return;
    }
    try {
      let response = await fetch('/auth/check', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) {
        const newToken = await refreshSession();
        if (newToken) {
          response = await fetch('/auth/check', {
            headers: { 'Authorization': `Bearer ${newToken}` },
          });
        }
      }
      if (response.ok) {
        showMainApp();
        if (typeof window.initApp === 'function') {
          window.initApp();
        }
      } else {
        clearToken();
        showLoginScreen();
      }
    } catch (e) {
      clearToken();
      showLoginScreen();
    }
  }

  function showLoginScreen() {
    document.getElementById("login-screen").style.display = "flex";
    document.getElementById("login-form-container").style.display = "block";
    document.getElementById("register-form-container").style.display = "none";
    document.getElementById("verify-email-container").style.display = "none";
    document.getElementById("main-app").style.display = "none";
  }
  
  function showRegisterScreen() {
    document.getElementById("login-screen").style.display = "flex";
    document.getElementById("login-form-container").style.display = "none";
    document.getElementById("register-form-container").style.display = "block";
    document.getElementById("verify-email-container").style.display = "none";
    document.getElementById("main-app").style.display = "none";
  }

  function showVerifyScreen() {
    document.getElementById("login-screen").style.display = "flex";
    document.getElementById("login-form-container").style.display = "none";
    document.getElementById("register-form-container").style.display = "none";
    document.getElementById("verify-email-container").style.display = "block";
    document.getElementById("main-app").style.display = "none";
  }
  
  function showMainApp() {
    document.getElementById("login-screen").style.display = "none";
    document.getElementById("main-app").style.display = "block";
  }
  
  const RETRY_STATUSES = [500, 502, 503, 504];

  // Render cold-start can take 30-60s during deploys; retry long enough
  // to ride out the boot window instead of showing a hard 500.
  async function fetchWithRetry(url, payload) {
    let response = null;
    const delays = [3000, 4000, 6000, 8000, 12000];
    for (let attempt = 0; attempt <= delays.length; attempt++) {
      response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
      });
      if (!RETRY_STATUSES.includes(response.status)) break;
      if (attempt < delays.length) await new Promise(r => setTimeout(r, delays[attempt]));
    }
    return response;
  }

  async function login(email, password) {
    const payload = JSON.stringify({ email, password });
    const response = await fetchWithRetry("/auth/login", payload);

    if (!response.ok) {
      const error = await parseJsonSafe(response, (typeof t === 'function' ? t('auth.login_error') : 'Erro ao fazer login'));
      if (response.status === 403 && error.detail && error.detail.includes("não verificada")) {
        showVerifyScreen();
        throw new Error(error.detail);
      }
      throw new Error(error.detail || (typeof t === 'function' ? t('auth.login_error') : 'Erro ao fazer login'));
    }

    const data = await parseJsonSafe(response, (typeof t === 'function' ? t('auth.login_error') : 'Erro ao fazer login'));
    if (!data.access_token) throw new Error(data.detail || 'Resposta inválida do servidor');
    setToken(data.access_token);
    showMainApp();
    
    if (typeof window.initApp === "function") {
      window.initApp().catch(err => console.error("Erro ao iniciar app:", err));
    }
    
    return data;
  }
  
  async function register(email, password) {
    const payload = JSON.stringify({ email, password });
    const response = await fetchWithRetry("/auth/register", payload);

    if (!response.ok) {
      const error = await parseJsonSafe(response, (typeof t === 'function' ? t('auth.register_error') : 'Erro ao criar conta'));
      throw new Error(error.detail || (typeof t === 'function' ? t('auth.register_error') : 'Erro ao criar conta'));
    }

    const data = await parseJsonSafe(response, (typeof t === 'function' ? t('auth.register_error') : 'Erro ao criar conta'));
    if (!data.access_token) throw new Error(data.detail || 'Resposta inválida do servidor');
    setToken(data.access_token);
    showMainApp();
    
    if (typeof window.initApp === "function") {
      window.initApp().catch(err => console.error("Erro ao iniciar app:", err));
    }
    
    return data;
  }

  async function verifyEmail(token) {
    const response = await fetch("/auth/verify-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    
     if (!response.ok) {
       const error = await parseJsonSafe(response, (typeof t === 'function' ? t('auth.verify_error') : 'Erro ao verificar email'));
       throw new Error(error.detail || error.message || (typeof t === 'function' ? t('auth.verify_error') : 'Erro ao verificar email'));
     }

     const data = await parseJsonSafe(response, (typeof t === 'function' ? t('auth.verify_error') : 'Erro ao verificar email'));
     if (!data.success) {
       throw new Error(data.message || (typeof t === 'function' ? t('auth.verify_error') : 'Erro ao verificar email'));
     }

     return data;
  }

  async function logout() {
    clearToken();
    showLoginScreen();
    try {
      await fetch('/auth/logout', { method: 'POST' });
    } catch (e) {}
    window.location.reload();
  }

  async function loginAsGuest() {
    const response = await fetch('/auth/guest', { method: 'POST' });
    if (!response.ok) {
      const error = await parseJsonSafe(response, (typeof t === 'function' ? t('auth.guest_error') : 'Erro ao entrar como convidado'));
      throw new Error(error.detail || (typeof t === 'function' ? t('auth.guest_error') : 'Erro ao entrar como convidado'));
    }
    const data = await parseJsonSafe(response, (typeof t === 'function' ? t('auth.guest_error') : 'Erro ao entrar como convidado'));
    if (!data.access_token) throw new Error(data.detail || 'Resposta inválida do servidor');
    setToken(data.access_token);
    showMainApp();
    if (typeof window.initApp === "function") {
      window.initApp().catch(err => console.error("Erro ao iniciar app:", err));
    }
    return data;
  }

  async function upgradeAccount(email, password) {
    const payload = JSON.stringify({ email, password });
    const response = await fetch('/auth/upgrade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
      body: payload,
    });
    if (!response.ok) {
      const error = await parseJsonSafe(response, (typeof t === 'function' ? t('auth.upgrade_error') : 'Erro ao atualizar conta'));
      throw new Error(error.detail || (typeof t === 'function' ? t('auth.upgrade_error') : 'Erro ao atualizar conta'));
    }
    const data = await parseJsonSafe(response, (typeof t === 'function' ? t('auth.upgrade_error') : 'Erro ao atualizar conta'));
    if (!data.access_token) throw new Error(data.detail || 'Resposta inválida do servidor');
    setToken(data.access_token);
    if (typeof window.updateGuestUI === 'function') {
      window.updateGuestUI();
    }
    return data;
  }

  function init() {
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const showRegister = document.getElementById("show-register");
    const showLogin = document.getElementById("show-login");
    const showLoginVerify = document.getElementById("show-login-verify");
    const logoutBtn = document.getElementById("logout-btn");
    const logoutBtnSidebar = document.getElementById("logout-btn-sidebar");
    const verifyBtn = document.getElementById("verify-btn");
    const verificationTokenInput = document.getElementById("verification-token");
    
    if (loginForm) {
      loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        try {
          await login(fd.get("email"), fd.get("password"));
          e.target.reset();
        } catch (err) {
          alert(typeof translateBackendError === 'function' ? translateBackendError(err.message) : err.message);
        }
      });
    }
    
    if (registerForm) {
      registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const password = fd.get("password");
        const confirmPassword = fd.get("confirm_password");
        
        if (password !== confirmPassword) {
          alert(typeof t === 'function' ? t('auth.passwords_dont_match') : 'As senhas n\u00e3o coincidem');
          return;
        }
        
        try {
          await register(fd.get("email"), password);
          e.target.reset();
        } catch (err) {
          alert(typeof translateBackendError === 'function' ? translateBackendError(err.message) : err.message);
        }
      });
    }

    if (verifyBtn && verificationTokenInput) {
      verifyBtn.addEventListener("click", async () => {
        const token = verificationTokenInput.value.trim();
        if (!token) {
          alert(typeof t === 'function' ? t('auth.enter_token') : 'Por favor, insira o token de verifica\u00e7\u00e3o');
          return;
        }
        try {
          const result = await verifyEmail(token);
          if (result.success) {
            alert(typeof t === 'function' ? t('auth.email_verified') : 'Email verificado com sucesso! Agora voc\u00ea pode fazer login.');
            showLoginScreen();
          }
        } catch (err) {
          alert(typeof translateBackendError === 'function' ? translateBackendError(err.message) : err.message);
        }
      });

      verificationTokenInput.addEventListener("keypress", async (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          verifyBtn.click();
        }
      });
    }
    
    if (showRegister) {
      showRegister.addEventListener("click", (e) => {
        e.preventDefault();
        showRegisterScreen();
      });
    }
    
    if (showLogin) {
      showLogin.addEventListener("click", (e) => {
        e.preventDefault();
        showLoginScreen();
      });
    }

    if (showLoginVerify) {
      showLoginVerify.addEventListener("click", (e) => {
        e.preventDefault();
        showLoginScreen();
      });
    }
    
    if (logoutBtn) {
      logoutBtn.addEventListener("click", logout);
    }
    
    if (logoutBtnSidebar) {
      logoutBtnSidebar.addEventListener("click", logout);
    }

    // Guest login button handler
    const guestLoginBtn = document.getElementById("guest-login-btn");
    if (guestLoginBtn) {
      guestLoginBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        try {
          await loginAsGuest();
          alert(typeof t === 'function' ? t('auth.guest_welcome') : 'Bem-vindo como convidado! Você pode criar uma conta permanente agora para salvar seu progresso.');
        } catch (err) {
          alert(typeof translateBackendError === 'function' ? translateBackendError(err.message) : err.message);
        }
      });
    }

    // Upgrade account form handler
    const upgradeForm = document.getElementById("upgrade-form");
    if (upgradeForm) {
      upgradeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = upgradeForm.querySelector('input[name="email"]').value.trim();
        const password = upgradeForm.querySelector('input[name="password"]').value;
        const confirmPassword = upgradeForm.querySelector('input[name="confirm_password"]').value;

        if (password !== confirmPassword) {
          alert(typeof t === 'function' ? t('auth.passwords_dont_match') : 'As senhas não coincidem');
          return;
        }

        try {
          await upgradeAccount(email, password);
          alert(typeof t === 'function' ? t('auth.upgrade_success') : 'Conta atualizada com sucesso!');
          if (typeof window.showUpgradeForm === 'function') {
            window.showUpgradeForm(false);
          }
        } catch (err) {
          alert(typeof translateBackendError === 'function' ? translateBackendError(err.message) : err.message);
        }
      });
    }
    
    checkAuth();
  }

  return {
    getToken,
    setToken,
    clearToken,
    getCurrentUser,
    isGuest,
    refreshSession,
    apiFetch,
    checkAuth,
    login,
    register,
    verifyEmail,
    logout,
    loginAsGuest,
    upgradeAccount,
    init,
  };
})();

window.Auth = Auth;

document.addEventListener("DOMContentLoaded", () => {
  Auth.init();
});
