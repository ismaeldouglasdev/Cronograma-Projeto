(function() {
  var themes = ['dark', 'light', 'ocean'];
  var theme = 'dark';
  try {
    theme = localStorage.getItem('app_theme') || 'dark';
  } catch(e) {}
  if (themes.indexOf(theme) === -1) theme = 'dark';
  document.documentElement.setAttribute('data-theme', theme);
  window.__initialTheme = theme;

  var fontLink = document.querySelector('link[media="print"]');
  if (fontLink) {
    if (fontLink.sheet) {
      fontLink.media = 'all';
    } else {
      fontLink.addEventListener('load', function() { fontLink.media = 'all'; });
    }
  }
})();
