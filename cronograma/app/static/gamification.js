const Gamification = (function() {
  const XP_POR_POMODORO = 25;
  const XP_POR_TAREFA_CONCLUIDA = 50;
  const XP_POR_AREA_CRIADA = 30;
  
  const BADGES = [
    { id: 'primeiro_pomodoro', nome: '🌱 Primeiro Pomodoro', descricao: 'Complete seu primeiro pomodoro', requer: 1, tipo: 'pomodoro' },
    { id: 'pomodoro_10', nome: '🔥 Foco Level 1', descricao: 'Complete 10 pomodoros', requer: 10, tipo: 'pomodoro' },
    { id: 'pomodoro_50', nome: '⚡ Foco Level 2', descricao: 'Complete 50 pomodoros', requer: 50, tipo: 'pomodoro' },
    { id: 'pomodoro_100', nome: '💎 Mestre do Foco', descricao: 'Complete 100 pomodoros', requer: 100, tipo: 'pomodoro' },
    { id: 'tarefa_1', nome: '📝 Começando', descricao: 'Complete sua primeira tarefa', requer: 1, tipo: 'tarefa' },
    { id: 'tarefa_10', nome: '📚 Produtividade', descricao: 'Complete 10 tarefas', requer: 10, tipo: 'tarefa' },
    { id: 'tarefa_50', nome: '🏆 Gestão Total', descricao: 'Complete 50 tarefas', requer: 50, tipo: 'tarefa' },
    { id: 'area_1', nome: '🎯 Organizado', descricao: 'Crie sua primeira área', requer: 1, tipo: 'area' },
    { id: 'streak_3', nome: '🔥 Sequência', descricao: '3 dias seguidos de estudo', requer: 3, tipo: 'streak' },
    { id: 'streak_7', nome: '🔥🔥 Semana', descricao: '7 dias seguidos de estudo', requer: 7, tipo: 'streak' },
  ];

  let userProgress = {
    xp_total: 0,
    level: 1,
    pomodoros_total: 0,
    tarefas_concluidas: 0,
    areas_criadas: 0,
    badges: [],
    streak_dias: 0,
    ultimo_dia: null
  };

  function calcularNivel(xp) {
    return Math.floor(xp / 500) + 1;
  }

  function xpParaProximoNivel(level) {
    return level * 500;
  }

  function xpAtualNivel(xp) {
    return xp % 500;
  }

  function verificarNovoBadge(tipo, quantidade) {
    const badge = BADGES.find(b => b.tipo === tipo && !userProgress.badges.includes(b.id) && quantidade >= b.requer);
    if (badge) {
      userProgress.badges.push(badge.id);
      return badge;
    }
    return null;
  }

  function calcularStreak() {
    const hoje = new Date().toISOString().split('T')[0];
    const ultimo = userProgress.ultimo_dia;
    
    if (!ultimo) {
      userProgress.streak_dias = 1;
    } else if (ultimo === hoje) {
      // Mesmo dia, não faz nada
    } else {
      const diffDias = (new Date(hoje) - new Date(ultimo)) / (1000 * 60 * 60 * 24);
      if (diffDias === 1) {
        userProgress.streak_dias++;
      } else {
        userProgress.streak_dias = 1;
      }
    }
    userProgress.ultimo_dia = hoje;
    
    return verificarNovoBadge('streak', userProgress.streak_dias);
  }

  function adicionarXP(tipo) {
    let xp = 0;
    let badge = null;
    
    switch(tipo) {
      case 'pomodoro':
        xp = XP_POR_POMODORO;
        userProgress.pomodoros_total++;
        badge = verificarNovoBadge('pomodoro', userProgress.pomodoros_total);
        break;
      case 'tarefa':
        xp = XP_POR_TAREFA_CONCLUIDA;
        userProgress.tarefas_concluidas++;
        badge = verificarNovoBadge('tarefa', userProgress.tarefas_concluidas);
        break;
      case 'area':
        xp = XP_POR_AREA_CRIADA;
        userProgress.areas_criadas++;
        badge = verificarNovoBadge('area', userProgress.areas_criadas);
        break;
    }
    
    const streakBadge = calcularStreak();
    if (streakBadge) badge = streakBadge;
    
    const nivelAnterior = userProgress.level;
    userProgress.xp_total += xp;
    userProgress.level = calcularNivel(userProgress.xp_total);
    
    const subioNivel = userProgress.level > nivelAnterior;
    
    salvarProgresso();
    
    return {
      xp,
      nivel: userProgress.level,
      subioNivel,
      badge,
      progress: {
        xp_atual: xpAtualNivel(userProgress.xp_total),
        xp_proximo: xpParaProximoNivel(userProgress.level),
        streak: userProgress.streak_dias
      }
    };
  }

  function salvarProgresso() {
    try {
      localStorage.setItem('gamificacao_progress', JSON.stringify(userProgress));
    } catch(e) {
      console.error('Erro ao salvar progresso:', e);
    }
  }

  function carregarProgresso() {
    try {
      const saved = localStorage.getItem('gamificacao_progress');
      if (saved) {
        userProgress = { ...userProgress, ...JSON.parse(saved) };
      }
    } catch(e) {
      console.error('Erro ao carregar progresso:', e);
    }
    return userProgress;
  }

  function getProgresso() {
    return {
      ...userProgress,
      xp_proximo: xpParaProximoNivel(userProgress.level),
      xp_atual: xpAtualNivel(userProgress.xp_total),
      badges_disponiveis: BADGES
    };
  }

  function getBadgeInfo(badgeId) {
    return BADGES.find(b => b.id === badgeId);
  }

  function resetProgress() {
    userProgress = {
      xp_total: 0,
      level: 1,
      pomodoros_total: 0,
      tarefas_concluidas: 0,
      areas_criadas: 0,
      badges: [],
      streak_dias: 0,
      ultimo_dia: null
    };
    salvarProgresso();
  }

  function init() {
    carregarProgresso();
  }

  return {
    init,
    adicionarXP,
    getProgresso,
    getBadgeInfo,
    resetProgress,
    BADGES
  };
})();

if (typeof window !== 'undefined') {
  window.Gamification = Gamification;
}
