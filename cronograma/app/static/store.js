/**
 * AppStore - Estado Global Centralizado com Persistência Automática
 * Gamificação completa: XP, Streak, Freezes, Coins, Conquistas
 */

const AppStore = (function() {
  // ============================================
  // CONSTANTES DE GAMIFICAÇÃO
  // ============================================
  const XP_POR_MINUTO = 0.5; // 30 min = 15 XP, 60 min = 30 XP
  const XP_POR_TAREFA = 5;
  const XP_POR_AREA = 25;
  
  // Coins
  const COINS_POR_TAREFA = 2;
  const COINS_POR_POMODORO = 3;
  const COINS_POR_STREAK_DIA = 1;
  const FREEZE_COST = 50; // Custo para comprar freeze
  
  // Freezes
  const MAX_FREEZES = 4;
  const FREEZE_GAIN_INTERVAL = 7; // Ganha 1 freeze por semana
  
  // ============================================
  // DEFINIÇÃO DE CONQUISTAS (sem emojis)
  // ============================================
  const ACHIEVEMENTS = {
    xp: [
      { id: 'xp_100', title: 'Primeiros Passos', description: 'Ganhe 100 XP', requirement: 100, icon: 'seedling' },
      { id: 'xp_500', title: 'Dedicado', description: 'Ganhe 500 XP', requirement: 500, icon: 'flame' },
      { id: 'xp_1000', title: 'Estudioso', description: 'Ganhe 1000 XP', requirement: 1000, icon: 'bolt' },
      { id: 'xp_5000', title: 'Mestre', description: 'Ganhe 5000 XP', requirement: 5000, icon: 'brain' },
      { id: 'xp_10000', title: 'Lenda', description: 'Ganhe 10000 XP', requirement: 10000, icon: 'crown' },
    ],
    streak: [
      { id: 'streak_3', title: 'Início', description: '3 dias consecutivos', requirement: 3, icon: 'flame' },
      { id: 'streak_7', title: 'Consistente', description: '7 dias consecutivos', requirement: 7, icon: 'flame' },
      { id: 'streak_14', title: 'Focado', description: '14 dias consecutivos', requirement: 14, icon: 'target' },
      { id: 'streak_30', title: 'Dedicado', description: '30 dias consecutivos', requirement: 30, icon: 'medal' },
      { id: 'streak_100', title: 'Lenda', description: '100 dias consecutivos', requirement: 100, icon: 'crown' },
    ],
    pomodoro: [
      { id: 'pomo_1', title: 'Primeiro', description: 'Complete 1 pomodoro', requirement: 1, icon: 'clock' },
      { id: 'pomo_10', title: 'Aquecido', description: 'Complete 10 pomodoros', requirement: 10, icon: 'flame' },
      { id: 'pomo_50', title: 'Fogo', description: 'Complete 50 pomodoros', requirement: 50, icon: 'bolt' },
      { id: 'pomo_100', title: 'Mestre', description: 'Complete 100 pomodoros', requirement: 100, icon: 'medal' },
      { id: 'pomo_500', title: 'Lendário', description: 'Complete 500 pomodoros', requirement: 500, icon: 'crown' },
    ],
    tasks: [
      { id: 'task_1', title: 'Início', description: 'Complete 1 tarefa', requirement: 1, icon: 'done' },
      { id: 'task_10', title: 'Mover', description: 'Complete 10 tarefas', requirement: 10, icon: 'flame' },
      { id: 'task_50', title: 'Produtivo', description: 'Complete 50 tarefas', requirement: 50, icon: 'bolt' },
      { id: 'task_100', title: 'Expert', description: 'Complete 100 tarefas', requirement: 100, icon: 'medal' },
      { id: 'task_500', title: 'Lenda', description: 'Complete 500 tarefas', requirement: 500, icon: 'crown' },
    ],
    level: [
      { id: 'level_2', title: 'Level 2', description: 'Atinga level 2', requirement: 2, icon: 'arrow-up' },
      { id: 'level_5', title: 'Level 5', description: 'Atinga level 5', requirement: 5, icon: 'arrow-up' },
      { id: 'level_10', title: 'Level 10', description: 'Atinga level 10', requirement: 10, icon: 'growing-arrow' },
      { id: 'level_25', title: 'Level 25', description: 'Atinga level 25', requirement: 25, icon: 'medal' },
      { id: 'level_50', title: 'Level 50', description: 'Atinga level 50', requirement: 50, icon: 'crown' },
    ],
    coins: [
      { id: 'coin_50', title: 'Iniciante', description: 'Acumule 50 coins', requirement: 50, icon: 'gift' },
      { id: 'coin_200', title: 'Economizador', description: 'Acumule 200 coins', requirement: 200, icon: 'blue-diamond' },
      { id: 'coin_500', title: 'Rico', description: 'Acumule 500 coins', requirement: 500, icon: 'purple-gem' },
      { id: 'coin_1000', title: 'Milionário', description: 'Acumule 1000 coins', requirement: 1000, icon: 'crown' },
    ]
  };

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
  // HELPERS DE NÍVEL
  // ============================================
  function calculateLevel(xp) {
    let level = 1;
    let remainingXP = xp;
    while (remainingXP >= level * 500) {
      remainingXP -= level * 500;
      level++;
    }
    return level;
  }

  function getXPForCurrentLevel(xp) {
    let level = 1;
    let remaining = xp;
    while (remaining >= level * 500 && level < 100) {
      remaining -= level * 500;
      level++;
    }
    return remaining;
  }

  function getXPForNextLevel(level) {
    return level * 500;
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
  // SISTEMA DE STREAK COM FREEZES
  // ============================================
  function updateStreak() {
    const today = getDateString();
    const lastDate = state.stats.lastActivityDate;
    
    if (!lastDate) {
      // Primeiro dia de atividade
      state.stats.currentStreak = 1;
    } else if (lastDate === today) {
      // Mesmo dia, não altera streak
      return;
    } else {
      const diff = getDaysDifference(lastDate, today);
      
      if (diff === 1) {
        // Dia consecutivo - mantém streak
        state.stats.currentStreak++;
      } else if (diff > 1) {
        // Pulou dias - usar freeze se disponível
        if (state.stats.freezes > 0) {
          state.stats.freezes--;
          console.log('🔒 Freeze usado! Restam: ' + state.stats.freezes);
        } else {
          // Perdeu streak
          state.stats.currentStreak = 1;
        }
      }
    }
    
    // Atualizar longest streak
    if (state.stats.currentStreak > state.stats.longestStreak) {
      state.stats.longestStreak = state.stats.currentStreak;
    }
    
    // Atualizar última data de atividade
    state.stats.lastActivityDate = today;
    
    // Verificar ganha de freeze semanal
    checkWeeklyFreeze();
  }

  function checkWeeklyFreeze() {
    const today = getDateString();
    const lastGain = state.stats.lastFreezeGain;
    
    if (!lastGain || getDaysDifference(lastGain, today) >= FREEZE_GAIN_INTERVAL) {
      if (state.stats.freezes < MAX_FREEZES) {
        state.stats.freezes++;
        state.stats.lastFreezeGain = today;
        console.log('🔒 Novo freeze ganho! Total: ' + state.stats.freezes);
      }
    }
  }

  // ============================================
  // SISTEMA DE MOEDAS
  // ============================================
  function addCoins(amount) {
    state.stats.coins += amount;
    checkAchievements();
  }

  function buyFreeze() {
    if (state.stats.coins >= FREEZE_COST && state.stats.freezes < MAX_FREEZES) {
      state.stats.coins -= FREEZE_COST;
      state.stats.freezes++;
      _save();
      _notify();
      return true;
    }
    return false;
  }

  // ============================================
  // SISTEMA DE CONQUISTAS
  // ============================================
  function checkAchievements() {
    const newUnlocks = [];
    const stats = state.stats;
    const currentUnlocked = state.unlockedAchievements;

    for (const [category, achievements] of Object.entries(ACHIEVEMENTS)) {
      for (const achievement of achievements) {
        if (currentUnlocked.includes(achievement.id)) continue;

        let currentValue = 0;
        
        switch (category) {
          case 'xp': currentValue = stats.totalXP; break;
          case 'streak': currentValue = stats.currentStreak; break;
          case 'pomodoro': currentValue = stats.totalPomodoros; break;
          case 'tasks': currentValue = stats.completedTasks; break;
          case 'level': currentValue = stats.level; break;
          case 'coins': currentValue = stats.coins; break;
        }

        if (currentValue >= achievement.requirement) {
          currentUnlocked.push(achievement.id);
          newUnlocks.push({ ...achievement, category });
        }
      }
    }

    if (newUnlocks.length > 0) {
      _save();
      _notify();
    }

    return newUnlocks;
  }

  function getAchievementsWithStatus() {
    const result = {};
    for (const [category, achievements] of Object.entries(ACHIEVEMENTS)) {
      result[category] = achievements.map(a => ({
        ...a,
        category,
        unlocked: state.unlockedAchievements.includes(a.id)
      }));
    }
    return result;
  }

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
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        state.stats = { ...state.stats, ...parsed.stats };
        state.unlockedAchievements = parsed.unlockedAchievements || [];
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
    const wasEmpty = state.areas.length === 0;
    state.areas = areas;
    
    if (wasEmpty && areas.length > 0) {
      addXP('area');
    }
    
    _notify();
  }

  function setTasks(tasks) {
    const previousCompleted = state.tasks.filter(t => t.concluida).length;
    const newCompleted = tasks.filter(t => t.concluida).length;
    
    state.tasks = tasks;
    
    if (newCompleted > previousCompleted) {
      const diff = newCompleted - previousCompleted;
      for (let i = 0; i < diff; i++) {
        addXP('task');
      }
    }
    
    _notify();
  }

  function setSessions(sessions) {
    state.sessions = sessions;
    updateStreak();
    _notify();
  }

  function syncStatsFromData() {
    const completedTasks = state.tasks.filter(t => t.concluida).length;
    const totalSessions = state.sessions.length;
    
    if (completedTasks > state.stats.completedTasks) {
      state.stats.completedTasks = completedTasks;
    }
    
    // Recalcular streak baseado em datas das sessões
    if (totalSessions > 0) {
      const dates = [...new Set(state.sessions.map(s => s.data))].sort().reverse();
      if (dates.length > 0) {
        const today = getDateString();
        const lastSessionDate = dates[0];
        const daysDiff = getDaysDifference(lastSessionDate, today);
        
        if (daysDiff <= 1) {
          let streak = 0;
          let checkDate = new Date(lastSessionDate);
          
          for (let i = 0; i < dates.length; i++) {
            const expectedDate = getDateString(new Date(checkDate.getTime() - i * 86400000));
            if (dates.includes(expectedDate)) {
              streak++;
            } else {
              break;
            }
          }
          
          if (streak > state.stats.currentStreak) {
            state.stats.currentStreak = streak;
          }
        }
      }
    }
    
    checkAchievements();
    _save();
    _notify();
  }

  // Adicionar XP (gamificação)
  function addXP(source, minutes = 0) {
    let xpGained = 0;
    
    switch (source) {
      case 'pomodoro':
        // XP baseado no tempo real
        xpGained = Math.round(minutes * XP_POR_MINUTO) || XP_POR_MINUTO * 25;
        state.stats.totalPomodoros++;
        addCoins(COINS_POR_POMODORO);
        break;
      case 'task':
        xpGained = XP_POR_TAREFA;
        state.stats.completedTasks++;
        addCoins(COINS_POR_TAREFA);
        break;
      case 'area':
        xpGained = XP_POR_AREA;
        break;
      case 'session':
        // Para sessões manuais
        xpGained = Math.round(minutes * XP_POR_MINUTO);
        break;
    }
    
    const oldLevel = state.stats.level;
    state.stats.totalXP += xpGained;
    state.stats.level = calculateLevel(state.stats.totalXP);
    
    // Atualizar streak
    updateStreak();
    
    // Verificar conquistas
    checkAchievements();
    
    _save();
    _notify();
    
    return {
      xpGained,
      newLevel: state.stats.level,
      leveledUp: state.stats.level > oldLevel,
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
      achievements: getAchievementsWithStatus(),
      unlockedAchievements: state.unlockedAchievements,
    };
  }

  function init() {
    _load();
    state.stats.level = calculateLevel(state.stats.totalXP);
    updateStreak(); // Verificar streak ao iniciar
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
      const token = localStorage.getItem('token');
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
      
      // Atualizar estado com dados do backend
      state.stats.totalXP = data.xp_total || 0;
      state.stats.level = data.level || 1;
      state.stats.currentStreak = data.current_streak || 0;
      state.stats.longestStreak = data.longest_streak || 0;
      state.stats.freezes = data.streak_freezes || 0;
      state.stats.coins = data.coins || 0;
      state.stats.totalPomodoros = data.total_pomodoros || 0;
      state.stats.completedTasks = data.tarefas_concluidas || 0;
      
      // Converter achievements do backend para formato do store
      state.achievements = {};
      for (const [cat, achievements] of Object.entries(data.achievements || {})) {
        state.achievements[cat] = (achievements || []).map(a => ({
          id: a.id?.toString(),
          title: a.nome,
          description: a.descricao,
          requirement: a.requisito,
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
      console.log('✅ Gamificação sincronizada com backend');
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
    syncStatsFromData,
    syncFromBackend,  // Nova função para sincronizar com backend
    addXP,
    addCoins,
    buyFreeze,
    resetProgress,
    ACHIEVEMENTS,
  };
})();

// Exportar
if (typeof window !== 'undefined') {
  window.AppStore = AppStore;
}
