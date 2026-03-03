/**
 * AppStore - Estado Global Centralizado com Persistência Automática
 * Resolve: Perda de dados ao atualizar página
 */

const AppStore = (function() {
  // ============================================
  // CONSTANTES DE GAMIFICAÇÃO
  // ============================================
  const XP_POR_POMODORO = 25;
  const XP_POR_TAREFA_CONCLUIDA = 50;
  const XP_POR_AREA_CRIADA = 25;

  // ============================================
  // DEFINIÇÃO DE CONQUISTAS POR CATEGORIA
  // ============================================
  const ACHIEVEMENTS = {
    xp: [
      { id: 'xp_100', title: '🌱 Primeiros Passos', description: 'Ganhe 100 XP', requirement: 100 },
      { id: 'xp_500', title: '🔥 Dedicado', description: 'Ganhe 500 XP', requirement: 500 },
      { id: 'xp_1000', title: '⚡ Estudioso', description: 'Ganhe 1000 XP', requirement: 1000 },
      { id: 'xp_5000', title: '💎 Mestre do Conhecimento', description: 'Ganhe 5000 XP', requirement: 5000 },
      { id: 'xp_10000', title: '👑 Lenda da Disciplina', description: 'Ganhe 10000 XP', requirement: 10000 },
    ],
    streak: [
      { id: 'streak_3', title: '🔥 Início da Jornada', description: '3 dias consecutivos', requirement: 3 },
      { id: 'streak_7', title: '🔥🔥 Consistente', description: '7 dias consecutivos', requirement: 7 },
      { id: 'streak_14', title: '🔥🔥🔥 Focado', description: '14 dias consecutivos', requirement: 14 },
      { id: 'streak_30', title: '🔥🔥🔥🔥 Dedicado', description: '30 dias consecutivos', requirement: 30 },
      { id: 'streak_100', title: '🔥🔥🔥🔥🔥 Invencível', description: '100 dias consecutivos', requirement: 100 },
    ],
    pomodoro: [
      { id: 'pomo_1', title: '🍅 Primeiro Pomodoro', description: 'Complete 1 pomodoro', requirement: 1 },
      { id: 'pomo_10', title: '🍅🍅 Aquecendo', description: 'Complete 10 pomodoros', requirement: 10 },
      { id: 'pomo_50', title: '🍅🍅🍅 Produtivo', description: 'Complete 50 pomodoros', requirement: 50 },
      { id: 'pomo_100', title: '🍅🍅🍅🍅 Workaholic', description: 'Complete 100 pomodoros', requirement: 100 },
      { id: 'pomo_500', title: '🍅🍅🍅🍅🍅 Máquina', description: 'Complete 500 pomodoros', requirement: 500 },
    ],
    tasks: [
      { id: 'task_1', title: '✅ Primeira Tarefa', description: 'Complete 1 tarefa', requirement: 1 },
      { id: 'task_10', title: '✅✅ Começando', description: 'Complete 10 tarefas', requirement: 10 },
      { id: 'task_50', title: '✅✅✅ Organizado', description: 'Complete 50 tarefas', requirement: 50 },
      { id: 'task_100', title: '✅✅✅✅ Profissional', description: 'Complete 100 tarefas', requirement: 100 },
      { id: 'task_500', title: '✅✅✅✅✅ Mestre', description: 'Complete 500 tarefas', requirement: 500 },
    ],
    level: [
      { id: 'level_2', title: '⬆️ Level 2', description: 'Atinga level 2', requirement: 2 },
      { id: 'level_5', title: '⬆️⬆️ Level 5', description: 'Atinga level 5', requirement: 5 },
      { id: 'level_10', title: '⬆️⬆️⬆️ Level 10', description: 'Atinga level 10', requirement: 10 },
      { id: 'level_25', title: '⬆️⬆️⬆️⬆️ Level 25', description: 'Atinga level 25', requirement: 25 },
      { id: 'level_50', title: '⬆️⬆️⬆️⬆️⬆️ Level 50', description: 'Atinga level 50', requirement: 50 },
    ]
  };

  // ============================================
  // ESTADO PRIVADO
  // ============================================
  let state = {
    // Dados principais
    areas: [],
    tasks: [],
    sessions: [],
    
    // Stats de gamificação
    stats: {
      totalXP: 0,
      level: 1,
      currentStreak: 0,
      longestStreak: 0,
      totalPomodoros: 0,
      completedTasks: 0,
      lastActivityDate: null,
    },
    
    // Conquistas desbloqueadas
    unlockedAchievements: [],
    
    // Controle de loaded
    _loaded: false,
    _subscribers: [],
  };

  // ============================================
  // HELPERS DE NÍVEL
  // ============================================
  function calculateLevel(xp) {
    let level = 1;
    let remainingXP = xp;
    // Fórmula: cada nível requer level * 500 XP
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
  // SISTEMA DE CONQUISTAS
  // ============================================
  function checkAchievements() {
    const newUnlocks = [];
    const stats = state.stats;
    const currentUnlocked = state.unlockedAchievements;

    // Verificar cada categoria
    for (const [category, achievements] of Object.entries(ACHIEVEMENTS)) {
      for (const achievement of achievements) {
        // Se já está desbloqueado, pular
        if (currentUnlocked.includes(achievement.id)) continue;

        let currentValue = 0;
        
        switch (category) {
          case 'xp':
            currentValue = stats.totalXP;
            break;
          case 'streak':
            currentValue = stats.currentStreak;
            break;
          case 'pomodoro':
            currentValue = stats.totalPomodoros;
            break;
          case 'tasks':
            currentValue = stats.completedTasks;
            break;
          case 'level':
            currentValue = stats.level;
            break;
        }

        if (currentValue >= achievement.requirement) {
          currentUnlocked.push(achievement.id);
          newUnlocks.push({ ...achievement, category });
        }
      }
    }

    // Se houve novos desbloqueios, salvar e notificar
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
  
  // Setters para dados (chamados após fetch do backend)
  function setAreas(areas) {
    const wasEmpty = state.areas.length === 0;
    state.areas = areas;
    
    // Se criou primeira área, ganha XP
    if (wasEmpty && areas.length > 0) {
      addXP('area');
    }
    
    _notify();
  }

  function setTasks(tasks) {
    const previousCompleted = state.tasks.filter(t => t.concluida).length;
    const newCompleted = tasks.filter(t => t.concluida).length;
    
    state.tasks = tasks;
    
    // Se completou tarefa nova, atualiza stats
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
    _notify();
  }

  // Atualizar stats baseado em dados reais
  function syncStatsFromData() {
    const completedTasks = state.tasks.filter(t => t.concluida).length;
    const totalSessions = state.sessions.length;
    
    // Atualizar sem ganhar XP duplicado
    if (completedTasks > state.stats.completedTasks) {
      state.stats.completedTasks = completedTasks;
    }
    
    // Calcular streak baseado em sessões
    if (totalSessions > 0) {
      const dates = [...new Set(state.sessions.map(s => s.data))].sort().reverse();
      const today = new Date().toISOString().split('T')[0];
      const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
      
      if (dates[0] === today || dates[0] === yesterday) {
        // Contar dias consecutivos
        let streak = 0;
        let checkDate = dates[0] === today ? today : yesterday;
        
        for (const date of dates) {
          if (date === checkDate) {
            streak++;
            checkDate = new Date(new Date(checkDate).getTime() - 86400000).toISOString().split('T')[0];
          } else if (date < checkDate) {
            break;
          }
        }
        
        if (streak > state.stats.currentStreak) {
          state.stats.currentStreak = streak;
        }
        if (streak > state.stats.longestStreak) {
          state.stats.longestStreak = streak;
        }
        
        state.stats.lastActivityDate = dates[0];
      }
    }
    
    // Verificar conquistas
    checkAchievements();
    _save();
    _notify();
  }

  // Adicionar XP (gamificação)
  function addXP(source) {
    let xpGained = 0;
    
    switch (source) {
      case 'pomodoro':
        xpGained = XP_POR_POMODORO;
        state.stats.totalPomodoros++;
        break;
      case 'task':
        xpGained = XP_POR_TAREFA_CONCLUIDA;
        state.stats.completedTasks++;
        break;
      case 'area':
        xpGained = XP_POR_AREA_CRIADA;
        break;
    }
    
    // Atualizar XP total
    const oldLevel = state.stats.level;
    state.stats.totalXP += xpGained;
    state.stats.level = calculateLevel(state.stats.totalXP);
    
    // Atualizar streak
    const today = new Date().toISOString().split('T')[0];
    const lastDate = state.stats.lastActivityDate;
    
    if (lastDate !== today) {
      const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
      if (lastDate === yesterday) {
        state.stats.currentStreak++;
      } else if (lastDate !== today) {
        state.stats.currentStreak = 1;
      }
      
      if (state.stats.currentStreak > state.stats.longestStreak) {
        state.stats.longestStreak = state.stats.currentStreak;
      }
      
      state.stats.lastActivityDate = today;
    }
    
    // Verificar conquistas
    checkAchievements();
    
    // Salvar e notificar
    _save();
    _notify();
    
    return {
      xpGained,
      newLevel: state.stats.level,
      leveledUp: state.stats.level > oldLevel,
    };
  }

  // Obter estado atual
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

  // Inicializar
  function init() {
    _load();
    
    // Recalcular level baseado em XP total
    state.stats.level = calculateLevel(state.stats.totalXP);
    
    return getState();
  }

  // Resetar progresso
  function resetProgress() {
    state.stats = {
      totalXP: 0,
      level: 1,
      currentStreak: 0,
      longestStreak: 0,
      totalPomodoros: 0,
      completedTasks: 0,
      lastActivityDate: null,
    };
    state.unlockedAchievements = [];
    _save();
    _notify();
  }

  // ============================================
  // API PÚBLICA
  // ============================================
  return {
    init,
    getState,
    subscribe,
    setAreas,
    setTasks,
    setSessions,
    syncStatsFromData,
    addXP,
    resetProgress,
    ACHIEVEMENTS,
  };
})();

// Exportar para window
if (typeof window !== 'undefined') {
  window.AppStore = AppStore;
}
