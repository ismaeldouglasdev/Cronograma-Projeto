/**
 * AppLogger - Sistema de Logging Frontend
 *
 * Recursos:
 * - Níveis: DEBUG, INFO, WARN, ERROR
 * - Console output estruturado com timestamp
 * - Buffer de logs para envio em lote ao backend
 * - Preserva window.onerror para erros não capturados
 *
 * Uso:
 *   AppLogger.info('Mensagem', { usuario: 1, acao: 'login' });
 *   AppLogger.error('Falha na API', { status: 500 }, err);
 */
const AppLogger = (function () {
  // ─── Constantes ──────────────────────────────────────────────────────────
  const LEVELS = {
    DEBUG: { priority: 0, label: 'D', color: '#6b7280' },
    INFO: { priority: 1, label: 'I', color: '#22c55e' },
    WARN: { priority: 2, label: 'W', color: '#f59e0b' },
    ERROR: { priority: 3, label: 'E', color: '#ef4444' },
  };

  const DEFAULT_LEVEL = 'INFO';
  const BUFFER_MAX = 20; // Envia ao backend a cada 20 logs
  const FLUSH_INTERVAL_MS = 30000; // Ou a cada 30s

  // ─── Estado ──────────────────────────────────────────────────────────────
  let currentLevel = DEFAULT_LEVEL;
  const logBuffer = [];
  let flushTimer = null;

  // ─── Helpers ─────────────────────────────────────────────────────────────
  function getTimestamp() {
    return new Date().toISOString();
  }

  function getLevelFromStorage() {
    try {
      const stored = localStorage.getItem('cronograma_log_level');
      if (stored && LEVELS[stored]) {
        return stored;
      }
    } catch (e) { /* ignore */ }
    return DEFAULT_LEVEL;
  }

  function persistLevel(level) {
    try {
      localStorage.setItem('cronograma_log_level', level);
    } catch (e) { /* ignore */ }
  }

  // ─── Core Log ────────────────────────────────────────────────────────────
  function log(level, message, context, error) {
    const levelConfig = LEVELS[level] || LEVELS.INFO;
    const currentConfig = LEVELS[currentLevel] || LEVELS.INFO;

    // Filtro por nível
    if (levelConfig.priority < currentConfig.priority) return;

    const entry = {
      timestamp: getTimestamp(),
      level: level,
      message: message,
      context: context || {},
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    if (error) {
      entry.error = {
        name: error.name || 'Error',
        message: error.message || String(error),
        stack: error.stack ? error.stack.split('\n').slice(0, 5).join('\n') : null,
      };
    }

    // Console output
    const prefix = '%c' + levelConfig.label + '%c ' + getTimestamp().slice(11, 19) + ' ';
    const style1 = 'color:#fff;background:' + levelConfig.color + ';padding:1px 4px;border-radius:2px;font-weight:bold';
    const style2 = 'color:#9b9a97';

    switch (level) {
      case 'ERROR':
        console.error(prefix, style1, style2, message, context, error || '');
        break;
      case 'WARN':
        console.warn(prefix, style1, style2, message, context);
        break;
      case 'DEBUG':
        console.debug(prefix, style1, style2, message, context);
        break;
      default:
        console.log(prefix, style1, style2, message, context);
    }

    // Buffer para envio ao backend
    logBuffer.push(entry);
    if (logBuffer.length >= BUFFER_MAX) {
      flushLogs();
    }
  }

  // ─── Envio ao Backend ────────────────────────────────────────────────────
  async function flushLogs() {
    if (logBuffer.length === 0) return;

    const batch = logBuffer.splice(0, BUFFER_MAX);
    const token = (typeof getToken === 'function') ? getToken() : localStorage.getItem('cronograma_token');

    try {
      await fetch('/logs/client', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: 'Bearer ' + token } : {}),
        },
        body: JSON.stringify({ logs: batch }),
      });
    } catch (e) {
      // Silently fail - don't create infinite log loop
      console.debug('[AppLogger] Falha ao enviar logs ao backend');
    }
  }

  function startFlushTimer() {
    if (flushTimer) clearInterval(flushTimer);
    flushTimer = setInterval(flushLogs, FLUSH_INTERVAL_MS);
  }

  // ─── Global Error Handler ────────────────────────────────────────────────
  function setupGlobalErrorHandler() {
    const originalOnerror = window.onerror;

    window.onerror = function (message, source, lineno, colno, error) {
      log('ERROR', 'Uncaught: ' + message, {
        source: source,
        line: lineno,
        column: colno,
      }, error);

      if (typeof originalOnerror === 'function') {
        return originalOnerror(message, source, lineno, colno, error);
      }
      return false;
    };

    // Promise rejection handler
    window.addEventListener('unhandledrejection', function (event) {
      const reason = event.reason;
      log('ERROR', 'Unhandled Rejection', {}, reason instanceof Error ? reason : new Error(String(reason)));
    });
  }

  // ─── Public API ──────────────────────────────────────────────────────────
  function setLevel(level) {
    if (LEVELS[level]) {
      currentLevel = level;
      persistLevel(level);
      log('INFO', 'Log level set to ' + level);
    }
  }

  function getLevel() {
    return currentLevel;
  }

  function debug(message, context) { log('DEBUG', message, context); }
  function info(message, context) { log('INFO', message, context); }
  function warn(message, context) { log('WARN', message, context); }
  function error(message, context, err) { log('ERROR', message, context, err); }

  // ─── Init ────────────────────────────────────────────────────────────────
  function init() {
    currentLevel = getLevelFromStorage();
    setupGlobalErrorHandler();
    startFlushTimer();

    log('INFO', 'AppLogger initialized', { level: currentLevel });

    // Flush on beforeunload
    window.addEventListener('beforeunload', function () {
      if (flushTimer) clearInterval(flushTimer);
      flushLogs();
    });
  }

  return {
    init: init,
    setLevel: setLevel,
    getLevel: getLevel,
    debug: debug,
    info: info,
    warn: warn,
    error: error,
    flush: flushLogs,
    LEVELS: Object.keys(LEVELS),
  };
})();

// Auto-init on DOM ready
document.addEventListener('DOMContentLoaded', function () {
  AppLogger.init();
});
