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
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload;
    } catch (e) {
      return null;
    }
  }

  async function apiFetch(url, options = {}) {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(url, { ...options, headers });
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
      const response = await fetch('/auth/check', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
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
  
  async function login(email, password) {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      if (response.status === 403 && error.detail && error.detail.includes("não verificada")) {
        showVerifyScreen();
        throw new Error(error.detail);
      }
      throw new Error(error.detail || "Erro ao fazer login");
    }
    
    const data = await response.json();
    setToken(data.access_token);
    showMainApp();
    
    if (typeof window.initApp === "function") {
      window.initApp().catch(err => console.error("Erro ao iniciar app:", err));
    }
    
    return data;
  }
  
  async function register(email, password) {
    const response = await fetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Erro ao criar conta");
    }
    
    const data = await response.json();
    clearToken();
    showVerifyScreen();
    
    return data;
  }

  async function verifyEmail(token) {
    const response = await fetch("/auth/verify-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Erro ao verificar email");
    }
    
    return await response.json();
  }

  function logout() {
    clearToken();
    showLoginScreen();
    window.location.reload();
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
          alert(err.message);
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
          alert("As senhas não coincidem");
          return;
        }
        
        try {
          await register(fd.get("email"), password);
          e.target.reset();
        } catch (err) {
          alert(err.message);
        }
      });
    }

    if (verifyBtn && verificationTokenInput) {
      verifyBtn.addEventListener("click", async () => {
        const token = verificationTokenInput.value.trim();
        if (!token) {
          alert("Por favor, insira o token de verificação");
          return;
        }
        try {
          const result = await verifyEmail(token);
          if (result.success) {
            alert("Email verificado com sucesso! Agora você pode fazer login.");
            showLoginScreen();
          }
        } catch (err) {
          alert(err.message);
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
    
    checkAuth();
  }

  return {
    getToken,
    setToken,
    clearToken,
    apiFetch,
    checkAuth,
    login,
    register,
    verifyEmail,
    logout,
    init,
  };
})();

window.Auth = Auth;

document.addEventListener("DOMContentLoaded", () => {
  Auth.init();
});
