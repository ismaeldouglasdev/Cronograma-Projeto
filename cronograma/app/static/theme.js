const ThemeManager = (function() {
  const STORAGE_KEY = 'app_theme';
  const THEMES = ['dark', 'light', 'ocean', 'purple', 'forest', 'midnight', 'pastel', 'contrast'];
  let currentTheme = 'dark';
  let initialized = false;

  // Dummy log function (disabled for production)
  function log() {}

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
  }

  function themeDisplayName(key) {
    if (typeof t === 'function') {
      const label = t('temas.' + key);
      if (label && label !== 'temas.' + key) return label;
    }
    return key;
  }

  function updateUISelector(theme) {
    const select = document.getElementById('theme-select');
    const selectSidebar = document.getElementById('theme-select-sidebar');
    
    if (select) {
      if (select.options.length < THEMES.length) {
        select.innerHTML = THEMES.map(th => 
          `<option value="${th}">${themeDisplayName(th)}</option>`
        ).join('');
      }
      if (select.value !== theme) {
        select.value = theme;
      }
    }
    
    if (selectSidebar) {
      if (selectSidebar.options.length < THEMES.length) {
        selectSidebar.innerHTML = THEMES.map(th => 
          `<option value="${th}">${themeDisplayName(th)}</option>`
        ).join('');
      }
      if (selectSidebar.value !== theme) {
        selectSidebar.value = theme;
      }
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
    const selectSidebar = document.getElementById('theme-select-sidebar');
    
    if (!select && !selectSidebar) {
      setTimeout(setupSelector, 100);
      return;
    }
    
    if (select && select.dataset.listener !== 'true') {
      select.dataset.listener = 'true';
      if (select.options.length < THEMES.length) {
        select.innerHTML = THEMES.map(th => 
          `<option value="${th}">${themeDisplayName(th)}</option>`
        ).join('');
      }
      select.addEventListener('change', function() {
        setTheme(this.value);
        if (selectSidebar) selectSidebar.value = this.value;
      });
    }
    
    if (selectSidebar && selectSidebar.dataset.listener !== 'true') {
      selectSidebar.dataset.listener = 'true';
      if (selectSidebar.options.length < THEMES.length) {
        selectSidebar.innerHTML = THEMES.map(th => 
          `<option value="${th}">${themeDisplayName(th)}</option>`
        ).join('');
      }
      selectSidebar.addEventListener('change', function() {
        setTheme(this.value);
        if (select) select.value = this.value;
      });
    }
    
    if (select && selectSidebar) {
      const currentTheme = getTheme();
      select.value = currentTheme;
      selectSidebar.value = currentTheme;
    }
    
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
