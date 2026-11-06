/**
 * AppStore - Estado Global Centralizado com Persistência Automática
 * Gamificação completa: XP, Streak, Freezes, Coins, Conquistas
 */

const AppStore = (function() {
  // ============================================
  // GAMIFICAÇÃO SSOT (BACKEND)
  // ============================================
  // XP, streak, coins, freezes e conquistas são calculados exclusivamente
  // pelo backend. O frontend apenas exibe os valores via syncFromBackend().
  // Nenhuma constante local de gamificação é mantida para evitar inconsistências.

  // ============================================
  // ESTADO PRIVADO
  // ============================================
  let state = {
    areas: [],
    tasks: [],
    sessions: [],
    
    stats: {
      totalXP: 0,
      level: 1,
      currentStreak: 0,
      longestStreak: 0,
      totalPomodoros: 0,
      completedTasks: 0,
      lastActivityDate: null,
      coins: 0,
      freezes: 0,
      lastFreezeGain: null,
    },
    
    unlockedAchievements: [],
    
    _loaded: false,
    _subscribers: [],
  };

  // ============================================
  // HELPERS DE NÍVEL (fórmula: XP = 100 * level^1.5)
  // ============================================
  function xpForLevel(level) {
    return Math.floor(100 * Math.pow(level, 1.5));
  }

  function calculateLevel(xp) {
    let level = 1;
    while (true) {
      const xpNeeded = xpForLevel(level);
      if (xp < xpNeeded) break;
      xp -= xpNeeded;
      level++;
    }
    return level;
  }

  function getXPForCurrentLevel(xp) {
    const level = calculateLevel(xp);
    let xpAtLevel = xp;
    for (let l = 1; l < level; l++) {
      xpAtLevel -= xpForLevel(l);
    }
    return Math.max(0, xpAtLevel);
  }

  function getXPForNextLevel(level) {
    return xpForLevel(level);
  }

  // ============================================
  // HELPERS DE DATA
  // ============================================
  function getDateString(date = new Date()) {
    return date.toISOString().split('T')[0];
  }

  function getDaysDifference(date1, date2) {
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    const diffTime = Math.abs(d2 - d1);
    return Math.floor(diffTime / (1000 * 60 * 60 * 24));
  }

  // ============================================
  // SISTEMA DE STREAK COM FREEZES (REMOVIDO - USAR BACKEND SSOT)
  // ============================================
  // Streak é calculado exclusivamente pelo backend (streak_service.py).
  // O frontend não deve calcular streak localmente para evitar inconsistências.
  // Use syncFromBackend() para obter valores atualizados.

  // ============================================
  // SISTEMA DE MOEDAS (REMOVIDO - USAR BACKEND)
  // ============================================
  // Coins e freezes são gerenciados pelo backend.
  // buyFreeze() chama API /coins/buy-freeze.
  
  async function buyFreeze() {
    try {
      const token = localStorage.getItem('cronograma_token');
      const response = await fetch('/coins/buy-freeze', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token }
      });
      if (response.ok) {
        await syncFromBackend();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Erro ao comprar freeze:', error);
      return false;
    }
  }

  // ============================================
  // SISTEMA DE CONQUISTAS (REMOVIDO - USAR BACKEND)
  // ============================================
  // Conquistas são buscadas do backend via syncFromBackend().
  // checkAchievements() local removido para evitar inconsistências.

  // ============================================
  // PERSISTÊNCIA
  // ============================================
  const STORAGE_KEY = 'cronograma_app_state';

  function _save() {
    try {
      const dataToSave = {
        stats: state.stats,
        unlockedAchievements: state.unlockedAchievements,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(dataToSave));
    } catch (e) {
      console.error('Erro ao salvar estado:', e);
    }
  }

  function _load() {
    try {
      // Limpar apenas dados de gamificação do localStorage
      // O backend é a fonte de verdade para XP, tasks, streak, etc.
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        // Manter achievements desbloqueados se houver
        if (parsed.unlockedAchievements) {
          state.unlockedAchievements = parsed.unlockedAchievements;
        }
      }
      state._loaded = true;
    } catch (e) {
      console.error('Erro ao carregar estado:', e);
      state._loaded = true;
    }
  }

  // ============================================
  // SUBSCRIBERS
  // ============================================
  function subscribe(callback) {
    state._subscribers.push(callback);
    return () => {
      state._subscribers = state._subscribers.filter(cb => cb !== callback);
    };
  }

  function _notify() {
    state._subscribers.forEach(cb => cb(getState()));
  }

  // ============================================
  // AÇÕES PÚBLICAS
  // ============================================
  
  function setAreas(areas) {
    state.areas = areas;
    _notify();
  }

  function setTasks(tasks) {
    state.tasks = tasks;
    // XP é calculado exclusivamente pelo backend (SSOT).
    // O frontend não calcula XP localmente para evitar inconsistências.
    // Use syncFromBackend() para obter valores atualizados do backend.
    _notify();
  }

  function setSessions(sessions) {
    state.sessions = sessions;
    // Streak é calculado exclusivamente pelo backend (SSOT).
    // Removido updateStreak() local para evitar inconsistências.
    // Use syncFromBackend() para obter valores atualizados.
    _notify();
  }

  // syncStatsFromData removido - usar syncFromBackend() para sincronizar com backend

  // Adicionar XP (gamificação) — NO-OP: backend é fonte de verdade (SSOT).
  // Mantido para compatibilidade de API; syncFromBackend() sobrescreve.
  function addXP(source, minutes = 0) {
    console.debug('addXP called (no-op, using backend SSOT):', source, minutes);
    return {
      xpGained: 0,
      newLevel: state.stats.level,
      leveledUp: false,
    };
  }

  function getState() {
    return {
      areas: state.areas,
      tasks: state.tasks,
      sessions: state.sessions,
      stats: {
        ...state.stats,
        xpForCurrentLevel: getXPForCurrentLevel(state.stats.totalXP),
        xpForNextLevel: getXPForNextLevel(state.stats.level),
      },
      achievements: state.achievements || {}, // Buscado do backend via syncFromBackend()
      unlockedAchievements: state.unlockedAchievements,
    };
  }

  function init() {
    _load();
    state.stats.level = calculateLevel(state.stats.totalXP);
    // updateStreak() removido - usar syncFromBackend() para obter streak do backend
    return getState();
  }

  function resetProgress() {
    state.stats = {
      totalXP: 0,
      level: 1,
      currentStreak: 0,
      longestStreak: 0,
      totalPomodoros: 0,
      completedTasks: 0,
      lastActivityDate: null,
      coins: 0,
      freezes: 0,
      lastFreezeGain: null,
    };
    state.unlockedAchievements = [];
    _save();
    _notify();
  }

  // ============================================
  // SINCRONIZAÇÃO COM BACKEND (SSOT)
  // ============================================
  async function syncFromBackend() {
    try {
      const token = localStorage.getItem('cronograma_token');
      if (!token) return false;
      
      const response = await fetch('/gamification-summary', {
        headers: {
          'Authorization': 'Bearer ' + token
        }
      });
      
      if (!response.ok) {
        console.warn('Falha ao buscar gamificação do backend:', response.status);
        return false;
      }
      
      const data = await response.json();
      
      // Forçar sobrescrita com dados do backend (fonte de verdade)
      state.stats.totalXP = data.xp_total || 0;
      state.stats.level = data.level || 1;
      state.stats.currentStreak = data.current_streak || 0;
      state.stats.longestStreak = data.longest_streak || 0;
      state.stats.freezes = data.streak_freezes || 0;
      state.stats.coins = data.coins || 0;
      state.stats.totalPomodoros = data.total_pomodoros || 0;
      state.stats.completedTasks = data.tarefas_concluidas || 0;
      
      // Limpar localStorage para evitar dados obsoletos
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch (e) {}
      
      // Converter achievements do backend para formato do store
      state.achievements = {};
      for (const [cat, achievements] of Object.entries(data.achievements || {})) {
        state.achievements[cat] = (achievements || []).map(a => ({
          id: a.id?.toString(),
          title: a.nome,
          description: a.descricao,
          requirement: a.requisito,
          icon: a.icone,
          unlocked: a.desbloqueado
        }));
        
        // Marcar como desbloqueados
        (achievements || []).forEach(a => {
          if (a.desbloqueado) {
            const achId = a.id?.toString();
            if (achId && !state.unlockedAchievements.includes(achId)) {
              state.unlockedAchievements.push(achId);
            }
          }
        });
      }
      
      _save();
      _notify();
      return true;
    } catch (error) {
      console.error('Erro ao sincronizar gamificação:', error);
      return false;
    }
  }

  // API PÚBLICA
  return {
    init,
    getState,
    subscribe,
    setAreas,
    setTasks,
    setSessions,
    syncFromBackend,  // Sincroniza todos os dados do backend (SSOT)
    addXP,  // NO-OP - usar syncFromBackend()
    buyFreeze,  // Chama API /coins/buy-freeze
    resetProgress,
  };
})();

// Exportar
if (typeof window !== 'undefined') {
  window.AppStore = AppStore;
}
