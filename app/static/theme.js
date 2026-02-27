const ThemeManager = (function() {
  const STORAGE_KEY = 'app_theme';
  const THEMES = ['dark', 'light', 'ocean'];
  let currentTheme = 'dark';
  let initialized = false;

  function log(msg, data) {
    console.log('[DEBUG THEME] ' + msg, data || '');
  }

  function getStoredTheme() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && THEMES.includes(stored)) {
        return stored;
      }
    } catch (e) {
      log('Error reading from localStorage', e);
    }
    return 'dark';
  }

  function persist(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
      log('persisted', theme);
    } catch (e) {
      log('Error saving to localStorage', e);
    }
  }

  function applyTheme(theme) {
    if (!THEMES.includes(theme)) {
      theme = 'dark';
    }
    
    document.documentElement.setAttribute('data-theme', theme);
    currentTheme = theme;
    persist(theme);
    
    updateUISelector(theme);
    dispatchEvent(theme);
    
    log('theme applied', theme);
  }

  function updateUISelector(theme) {
    const select = document.getElementById('theme-select');
    if (select && select.value !== theme) {
      select.value = theme;
    }
  }

  function dispatchEvent(theme) {
    const event = new CustomEvent('themeChanged', { detail: { theme: theme } });
    window.dispatchEvent(event);
  }

  function setTheme(theme) {
    if (THEMES.includes(theme)) {
      log('theme changed', theme);
      applyTheme(theme);
    }
  }

  function getTheme() {
    return currentTheme;
  }

  function init() {
    if (initialized) {
      log('already initialized, skipping');
      return;
    }
    initialized = true;
    
    const theme = getStoredTheme();
    applyTheme(theme);
    
    log('theme loaded', theme);
    
    setupSelector();
  }

  function setupSelector() {
    const select = document.getElementById('theme-select');
    if (!select) {
      setTimeout(setupSelector, 100);
      return;
    }
    
    if (select.dataset.listener === 'true') {
      return;
    }
    select.dataset.listener = 'true';
    
    select.addEventListener('change', function() {
      setTheme(this.value);
    });
    
    log('selector setup complete');
  }

  if (typeof window !== 'undefined') {
    window.ThemeManager = {
      init: init,
      setTheme: setTheme,
      getTheme: getTheme,
      applyTheme: applyTheme,
    };
  }

  return {
    init: init,
    setTheme: setTheme,
    getTheme: getTheme,
    applyTheme: applyTheme,
  };
})();

window.ThemeManager = ThemeManager;
