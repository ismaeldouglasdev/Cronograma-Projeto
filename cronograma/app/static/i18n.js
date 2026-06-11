/**
 * i18n - Internationalization System for Cronograma
 * Supports pt-BR (default) and English
 * Auto-detects browser language and falls back to localStorage 'app_lang'
 */

const i18n = {
  'pt-BR': {
    // Landing page
    landing: {
      nav_entrar: 'Entrar',
      nav_acessar: 'Acessar',
      hero_title: 'Seus estudos',
      hero_title_highlight: 'com disciplina',
      hero_desc: 'Organize suas mat\u00e9rias, acompanhe tarefas, foque com Pomodoro e evolua com um sistema de gamifica\u00e7\u00e3o que transforma sua rotina de estudos.',
      hero_cta: 'Acessar Cronograma \u2192',
      hero_ghost: 'J\u00e1 tenho conta',
      feature1_title: 'Mat\u00e9rias & Tarefas',
      feature1_desc: 'Organize suas disciplinas, defina prioridades e acompanhe prazos de entrega.',
      feature2_title: 'Timer Pomodoro',
      feature2_desc: 'Foco total com sess\u00f5es cronometradas, notifica\u00e7\u00f5es e meta de pomodoros por tarefa.',
      feature3_title: 'Gamifica\u00e7\u00e3o',
      feature3_desc: 'Ganhe XP, suba de n\u00edvel, acumule moedas, conquiste achievements e mantenha seu streak.',
      feature4_title: 'Estat\u00edsticas',
      feature4_desc: 'Visualize horas por mat\u00e9ria, n\u00edvel atual e evolu\u00e7\u00e3o di\u00e1ria com gr\u00e1ficos.',
      feature5_title: 'Quadro de Hor\u00e1rios',
      feature5_desc: 'Monte sua grade semanal com aulas presenciais e online, com sala, hor\u00e1rio e professor.',
      feature6_title: 'Streak & Moedas',
      feature6_desc: 'Mantenha a sequ\u00eancia de estudos, ganhe moedas, compre freezes e n\u00e3o perca o ritmo.',
      footer: 'Cronograma de Estudos \u2014 Projeto Open Source',
    },

    // Auth forms
    auth: {
      cronograma_title: 'Cronograma',
      cronograma_subtitle: 'Organize seus estudos',
      login_title: 'Entrar',
      register_title: 'Criar conta',
      verify_title: 'Verificar Email',
      email_placeholder: 'Email',
      password_placeholder: 'Senha',
      confirm_placeholder: 'Confirmar senha',
      login_btn: 'Entrar',
      register_btn: 'Cadastrar',
      verify_btn: 'Verificar',
      verify_info: 'Conta criada! Por favor, verifique seu email.',
      verify_info_small: 'Copie o token que aparece no console do servidor e cole abaixo:',
      token_placeholder: 'Cole o token de verifica\u00e7\u00e3o aqui',
      nao_tem_conta: 'N\u00e3o tem conta? <a href="#" id="show-register">Cadastrar</a>',
      ja_tem_conta: 'J\u00e1 tem conta? <a href="#" id="show-login">Entrar</a>',
      ja_verificado: 'J\u00e1 verificado? <a href="#" id="show-login-verify">Entrar</a>',
      // Validation messages
      passwords_dont_match: 'As senhas n\u00e3o coincidem',
      enter_token: 'Por favor, insira o token de verifica\u00e7\u00e3o',
      email_verified: 'Email verificado com sucesso! Agora voc\u00ea pode fazer login.',
      login_error: 'Erro ao fazer login',
      register_error: 'Erro ao criar conta',
      verify_error: 'Erro ao verificar email',
    },

    // Sidebar
    sidebar: {
      nivel: 'N\u00edvel',
      areas: '\u00c1reas',
      foco: 'Foco',
      gamificacao: 'Gamifica\u00e7\u00e3o',
      horarios: 'Hor\u00e1rios',
      tarefas: 'Tarefas',
      sessoes: 'Sess\u00f5es',
      resumo: 'Resumo',
      sair: 'Sair',
    },

    // Page titles
    pages: {
      areas: '\u00c1reas',
      foco: 'Foco',
      gamificacao: 'Gamifica\u00e7\u00e3o',
      horarios: 'Quadro de Hor\u00e1rios',
      tarefas: 'Tarefas',
      sessoes: 'Sess\u00f5es',
      resumo: 'Resumo',
    },

    // Pomodoro / Foco
    foco: {
      section_desc: 'Execute suas tarefas com concentra\u00e7\u00e3o',
      timer_foco: 'Foco',
      timer_descanso: 'Descanso',
      btn_iniciar: '\u25b6 Iniciar',
      btn_pausar: '\u23f8 Pausar',
      btn_continuar: '\u25b6 Continuar',
      btn_encerrar: '\u23f9 Encerrar',
      btn_reset: '\ud83d\udd04 Reset',
      btn_pular: '\u23ed\ufe0f Pular',
      label_area: '\u00c1rea',
      label_tarefa: 'Tarefa (opcional)',
      label_foco: 'Foco',
      label_descanso: 'Descanso',
      label_min: 'min',
      label_descanso_auto: 'Descanso autom\u00e1tico',
      hoje: 'Hoje',
      sessoes_count: 'sess\u00f5es',
      meta_tarefa: 'Meta da tarefa',
      pomodoros: 'pomodoros',
      select_area: 'Selecione a \u00e1rea',
      select_tarefa: 'Selecione uma tarefa',
      nenhuma_tarefa_pendente: 'Nenhuma tarefa pendente',
      nenhuma_tarefa_especifica: 'Nenhuma tarefa espec\u00edfica',
      alert_select_area: 'Selecione uma \u00e1rea para iniciar o foco!',
      confirm_cancel: 'Tem certeza que deseja cancelar a sess\u00e3o de foco?',
      confirm_pular_descanso: 'Pular o descanso?',
      alert_descanso_fim: 'Descanso finalizado! Pronto para mais um pomodoro?',
      alert_sessao_curta: 'Sess\u00e3o muito curta para registrar.',
      notif_pomodoro_titulo: 'Pomodoro Conclu\u00eddo!',
      notif_pomodoro_corpo: '{minutos} min de foco registrados. \ud83c\udfaf',
      notif_descanso_titulo: 'Descanso Conclu\u00eddo',
      notif_descanso_corpo: 'Hora de voltar ao foco!',
      tab_foco: 'Foco',
      tab_descanso: 'Descanso',
    },

    // Gamification page
    gamificacao: {
      nivel_label: 'N\u00cdVEL',
      experiencia: 'Experi\u00eancia',
      progresso: 'Progresso:',
      dias_seguidos: 'dias seguidos',
      pomodoros: 'Pomodoros',
      tarefas: 'Tarefas',
      areas: '\u00c1reas',
      xp_total: 'XP Total',
      // Achievement categories
      conquistas: 'Conquistas',
      cat_experiencia: 'Experi\u00eancia',
      cat_dias_seguidos: 'Dias Seguidos',
      cat_pomodoros: 'Pomodoros',
      cat_tarefas_concluidas: 'Tarefas Conclu\u00eddas',
      cat_niveis_alcancados: 'N\u00edveis Alcan\u00e7ados',
      cat_coins: 'Coins',
    },

    // Areas panel
    areas: {
      search_placeholder: 'Buscar por nome...',
      filter_label: 'Filtrar por categoria',
      todas_categorias: 'Todas as categorias',
      nome_placeholder: 'Nome (ex: Matem\u00e1tica)',
      categoria_placeholder: 'Categoria (opcional)',
      tipo_aula: 'Tipo de aula',
      online: 'Online',
      presencial: 'Presencial',
      dia_semana: 'Dia da semana',
      hora_placeholder: 'Hor\u00e1rio (ex: 19:00 - 20:40)',
      sala_placeholder: 'Sala (ex: 206)',
      bloco_placeholder: 'Bloco (ex: E)',
      professor_placeholder: 'Professor (ex: Andre)',
      sala_prefix: 'Sala ',
      bloco_prefix: 'Bloco ',
      prof_prefix: 'Prof: ',
      prof_prefix_dot: 'Prof. ',
      btn_adicionar: 'Adicionar',
      empty: 'Nenhuma \u00e1rea encontrada.',
      confirm_delete: 'Excluir esta \u00e1rea? Tarefas e sess\u00f5es ser\u00e3o removidas.',
    },

    // Tasks panel
    tasks: {
      sort_label: 'Ordenar por',
      sort_prioridade: 'Por Prioridade',
      sort_data: 'Por Data',
      area_label: '\u00c1rea',
      titulo_label: 'T\u00edtulo',
      titulo_placeholder: 'T\u00edtulo da tarefa',
      prioridade_label: 'Prioridade',
      sem_prioridade: 'Sem prioridade',
      alta: 'Alta',
      media: 'M\u00e9dia',
      baixa: 'Baixa',
      meta_pomodoros_label: 'Meta de Pomodoros',
      descricao_label: 'Descri\u00e7\u00e3o',
      descricao_placeholder: 'Descri\u00e7\u00e3o (opcional)',
      data_entrega: 'Data de entrega',
      btn_adicionar: 'Adicionar',
      empty: 'Nenhuma tarefa. Adicione uma acima.',
      confirm_delete: 'Excluir esta tarefa?',
      prompt_minutos: 'Quantos minutos voc\u00ea dedicou a esta tarefa?',
      alert_minutos_validos: 'Informe um n\u00famero v\u00e1lido de minutos.',
    },

    // Sessoes panel
    sessoes: {
      section_desc: 'Registre seu tempo de estudo',
      select_area: 'Selecione a \u00e1rea',
      minutos_placeholder: 'Minutos (ex: 30)',
      data_placeholder: 'Opcional (hoje)',
      btn_registrar: 'Registrar',
      empty: 'Nenhuma sess\u00e3o registrada.',
      confirm_delete: 'Excluir esta sess\u00e3o?',
    },

    // Resumo panel
    resumo: {
      horas_estudadas: 'horas estudadas',
      sessoes: 'sess\u00f5es',
      areas: '\u00e1reas',
      chart_title: 'Distribui\u00e7\u00e3o por \u00c1rea',
      detalhamento: 'Detalhamento',
      empty: 'Nenhuma sess\u00e3o registrada ainda.',
      empty_chart: 'Nenhum dado registrado para este per\u00edodo.',
    },

    // Horarios panel
    horarios: {
      section_desc: 'Seus hor\u00e1rios de aulas presenciais por dia da semana',
      empty: 'Nenhuma aula presencial cadastrada. Adicione \u00e1reas presenciais com dia da semana.',
      sem_aulas: 'Sem aulas',
      dias: {
        segunda: 'Segunda-feira',
        terca: 'Ter\u00e7a-feira',
        quarta: 'Quarta-feira',
        quinta: 'Quinta-feira',
        sexta: 'Sexta-feira',
        sabado: 'S\u00e1bado',
        domingo: 'Domingo',
      },
    },

    // Modals
    modal: {
      fechar: 'Fechar',
      salvar: 'Salvar',
      selecione: 'Selecione',
      edit_tarefa: 'Editar Tarefa',
      edit_area: 'Editar \u00c1rea',
      edit_sessao: 'Editar Sess\u00e3o',
      area_label: '\u00c1rea',
      titulo_label: 'T\u00edtulo',
      descricao_label: 'Descri\u00e7\u00e3o',
      data_entrega: 'Data de entrega',
      status_label: 'Status',
      pendente: 'Pendente',
      concluida: 'Conclu\u00edda',
      prioridade_label: 'Prioridade',
      sem_prioridade: 'Sem prioridade',
      alta: 'Alta',
      media: 'M\u00e9dia',
      baixa: 'Baixa',
      meta_pomodoros_label: 'Meta de Pomodoros',
      pomodoros_concluidos: 'Pomodoros conclu\u00eddos: ',
      duracao_label: 'Dura\u00e7\u00e3o (minutos)',
      nome_label: 'Nome',
      subcategoria_label: 'Subcategoria',
      subcategoria_placeholder: 'Categoria (opcional)',
      tipo_label: 'Tipo',
      online: 'Online',
      presencial: 'Presencial',
      dia_semana: 'Dia da semana',
      horario_label: 'Hor\u00e1rio',
      sala_label: 'Sala',
      bloco_label: 'Bloco',
      professor_label: 'Professor',
      duracao_edit_label: 'Dura\u00e7\u00e3o (minutos)',
    },

    // Pomodoro complete modal
    pomo_modal: {
      title: 'Pomodoro Conclu\u00eddo!',
      min_foco: 'min de foco',
      moedas: 'Moedas',
      xp: 'XP',
      novas_conquistas: '\ud83c\udfc6 Novas Conquistas',
      streak: 'Streak:',
      dias: 'dias',
      subiu_nivel: 'Subiu para o',
      nivel: 'N\u00edvel',
      continuar: 'Continuar \ud83d\ude80',
    },

    // General
    geral: {
      erro_salvar: 'Erro ao salvar: ',
      trocar_aba: 'Trocar de aba?',
      select_area: 'Selecione a \u00e1rea',
    },

    // Language switcher
    lang: {
      pt: 'PT',
      en: 'EN',
    },
  },

  'en': {
    landing: {
      nav_entrar: 'Sign In',
      nav_acessar: 'Access',
      hero_title: 'Your studies,',
      hero_title_highlight: 'with discipline',
      hero_desc: 'Organize your subjects, track tasks, focus with Pomodoro, and level up with a gamification system that transforms your study routine.',
      hero_cta: 'Access Cronograma \u2192',
      hero_ghost: 'I already have an account',
      feature1_title: 'Subjects & Tasks',
      feature1_desc: 'Organize your disciplines, set priorities, and track deadlines.',
      feature2_title: 'Pomodoro Timer',
      feature2_desc: 'Full focus with timed sessions, notifications, and pomodoro goals per task.',
      feature3_title: 'Gamification',
      feature3_desc: 'Earn XP, level up, collect coins, unlock achievements, and keep your streak alive.',
      feature4_title: 'Statistics',
      feature4_desc: 'Visualize hours per subject, current level, and daily progress with charts.',
      feature5_title: 'Schedule Board',
      feature5_desc: 'Build your weekly schedule with in-person and online classes, room, time, and professor.',
      feature6_title: 'Streak & Coins',
      feature6_desc: 'Keep your study streak, earn coins, buy freezes, and never lose your rhythm.',
      footer: 'Study Cronograma \u2014 Open Source Project',
    },

    auth: {
      cronograma_title: 'Cronograma',
      cronograma_subtitle: 'Organize your studies',
      login_title: 'Sign In',
      register_title: 'Create Account',
      verify_title: 'Verify Email',
      email_placeholder: 'Email',
      password_placeholder: 'Password',
      confirm_placeholder: 'Confirm password',
      login_btn: 'Sign In',
      register_btn: 'Register',
      verify_btn: 'Verify',
      verify_info: 'Account created! Please verify your email.',
      verify_info_small: 'Copy the token shown in the server console and paste it below:',
      token_placeholder: 'Paste the verification token here',
      nao_tem_conta: 'Don\'t have an account? <a href="#" id="show-register">Register</a>',
      ja_tem_conta: 'Already have an account? <a href="#" id="show-login">Sign In</a>',
      ja_verificado: 'Already verified? <a href="#" id="show-login-verify">Sign In</a>',
      passwords_dont_match: 'Passwords do not match',
      enter_token: 'Please enter the verification token',
      email_verified: 'Email verified successfully! You can now log in.',
      login_error: 'Error logging in',
      register_error: 'Error creating account',
      verify_error: 'Error verifying email',
    },

    sidebar: {
      nivel: 'Level',
      areas: 'Areas',
      foco: 'Focus',
      gamificacao: 'Gamification',
      horarios: 'Schedule',
      tarefas: 'Tasks',
      sessoes: 'Sessions',
      resumo: 'Summary',
      sair: 'Logout',
    },

    pages: {
      areas: 'Areas',
      foco: 'Focus',
      gamificacao: 'Gamification',
      horarios: 'Schedule',
      tarefas: 'Tasks',
      sessoes: 'Sessions',
      resumo: 'Summary',
    },

    foco: {
      section_desc: 'Run your tasks with full concentration',
      timer_foco: 'Focus',
      timer_descanso: 'Break',
      btn_iniciar: '\u25b6 Start',
      btn_pausar: '\u23f8 Pause',
      btn_continuar: '\u25b6 Resume',
      btn_encerrar: '\u23f9 End',
      btn_reset: '\ud83d\udd04 Reset',
      btn_pular: '\u23ed\ufe0f Skip',
      label_area: 'Area',
      label_tarefa: 'Task (optional)',
      label_foco: 'Focus',
      label_descanso: 'Break',
      label_min: 'min',
      label_descanso_auto: 'Auto break',
      hoje: 'Today',
      sessoes_count: 'sessions',
      meta_tarefa: 'Task goal',
      pomodoros: 'pomodoros',
      select_area: 'Select an area',
      select_tarefa: 'Select a task',
      nenhuma_tarefa_pendente: 'No pending tasks',
      nenhuma_tarefa_especifica: 'No specific task',
      alert_select_area: 'Please select an area to start focusing!',
      confirm_cancel: 'Are you sure you want to cancel this focus session?',
      confirm_pular_descanso: 'Skip the break?',
      alert_descanso_fim: 'Break over! Ready for another pomodoro?',
      alert_sessao_curta: 'Session too short to register.',
      notif_pomodoro_titulo: 'Pomodoro Complete!',
      notif_pomodoro_corpo: '{minutos} min of focus recorded. \ud83c\udfaf',
      notif_descanso_titulo: 'Break Complete',
      notif_descanso_corpo: 'Time to get back to focus!',
      tab_foco: 'Focus',
      tab_descanso: 'Break',
    },

    gamificacao: {
      nivel_label: 'LEVEL',
      experiencia: 'Experience',
      progresso: 'Progress:',
      dias_seguidos: 'day streak',
      pomodoros: 'Pomodoros',
      tarefas: 'Tasks',
      areas: 'Areas',
      xp_total: 'Total XP',
      conquistas: 'Achievements',
      cat_experiencia: 'Experience',
      cat_dias_seguidos: 'Day Streak',
      cat_pomodoros: 'Pomodoros',
      cat_tarefas_concluidas: 'Completed Tasks',
      cat_niveis_alcancados: 'Levels Reached',
      cat_coins: 'Coins',
    },

    areas: {
      search_placeholder: 'Search by name...',
      filter_label: 'Filter by category',
      todas_categorias: 'All categories',
      nome_placeholder: 'Name (e.g. Math)',
      categoria_placeholder: 'Category (optional)',
      tipo_aula: 'Class type',
      online: 'Online',
      presencial: 'In-person',
      dia_semana: 'Day of week',
      hora_placeholder: 'Time (e.g. 07:00 PM - 08:40 PM)',
      sala_placeholder: 'Room (e.g. 206)',
      bloco_placeholder: 'Building (e.g. E)',
      professor_placeholder: 'Professor (e.g. John)',
      sala_prefix: 'Room ',
      bloco_prefix: 'Bldg ',
      prof_prefix: 'Prof: ',
      prof_prefix_dot: 'Prof. ',
      btn_adicionar: 'Add',
      empty: 'No areas found.',
      confirm_delete: 'Delete this area? Tasks and sessions will be removed.',
    },

    tasks: {
      sort_label: 'Sort by',
      sort_prioridade: 'By Priority',
      sort_data: 'By Date',
      area_label: 'Area',
      titulo_label: 'Title',
      titulo_placeholder: 'Task title',
      prioridade_label: 'Priority',
      sem_prioridade: 'No priority',
      alta: 'High',
      media: 'Medium',
      baixa: 'Low',
      meta_pomodoros_label: 'Pomodoro Goal',
      descricao_label: 'Description',
      descricao_placeholder: 'Description (optional)',
      data_entrega: 'Due date',
      btn_adicionar: 'Add',
      empty: 'No tasks. Add one above.',
      confirm_delete: 'Delete this task?',
      prompt_minutos: 'How many minutes did you spend on this task?',
      alert_minutos_validos: 'Please enter a valid number of minutes.',
    },

    sessoes: {
      section_desc: 'Log your study time',
      select_area: 'Select an area',
      minutos_placeholder: 'Minutes (e.g. 30)',
      data_placeholder: 'Optional (today)',
      btn_registrar: 'Register',
      empty: 'No sessions recorded.',
      confirm_delete: 'Delete this session?',
    },

    resumo: {
      horas_estudadas: 'hours studied',
      sessoes: 'sessions',
      areas: 'areas',
      chart_title: 'Distribution by Area',
      detalhamento: 'Details',
      empty: 'No sessions recorded yet.',
      empty_chart: 'No data recorded for this period.',
    },

    horarios: {
      section_desc: 'Your in-person class schedule by day of the week',
      empty: 'No in-person classes registered. Add in-person areas with a day of the week.',
      sem_aulas: 'No classes',
      dias: {
        segunda: 'Monday',
        terca: 'Tuesday',
        quarta: 'Wednesday',
        quinta: 'Thursday',
        sexta: 'Friday',
        sabado: 'Saturday',
        domingo: 'Sunday',
      },
    },

    modal: {
      fechar: 'Close',
      salvar: 'Save',
      selecione: 'Select',
      edit_tarefa: 'Edit Task',
      edit_area: 'Edit Area',
      edit_sessao: 'Edit Session',
      area_label: 'Area',
      titulo_label: 'Title',
      descricao_label: 'Description',
      data_entrega: 'Due date',
      status_label: 'Status',
      pendente: 'Pending',
      concluida: 'Completed',
      prioridade_label: 'Priority',
      sem_prioridade: 'No priority',
      alta: 'High',
      media: 'Medium',
      baixa: 'Low',
      meta_pomodoros_label: 'Pomodoro Goal',
      pomodoros_concluidos: 'Pomodoros completed: ',
      duracao_label: 'Duration (minutes)',
      nome_label: 'Name',
      subcategoria_label: 'Subcategory',
      subcategoria_placeholder: 'Category (optional)',
      tipo_label: 'Type',
      online: 'Online',
      presencial: 'In-person',
      dia_semana: 'Day of week',
      horario_label: 'Time',
      sala_label: 'Room',
      bloco_label: 'Building',
      professor_label: 'Professor',
      duracao_edit_label: 'Duration (minutes)',
    },

    pomo_modal: {
      title: 'Pomodoro Complete!',
      min_foco: 'min of focus',
      moedas: 'Coins',
      xp: 'XP',
      novas_conquistas: '\ud83c\udfc6 New Achievements',
      streak: 'Streak:',
      dias: 'days',
      subiu_nivel: 'Reached',
      nivel: 'Level',
      continuar: 'Continue \ud83d\ude80',
    },

    geral: {
      erro_salvar: 'Error saving: ',
      trocar_aba: 'Switch tabs?',
      select_area: 'Select an area',
    },

    lang: {
      pt: 'PT',
      en: 'EN',
    },
  },
};

/**
 * Get the current language code
 * Priority: localStorage > browser detection > default (pt-BR)
 */
function getCurrentLang() {
  const stored = localStorage.getItem('app_lang');
  if (stored) return stored;
  const browserLang = navigator.language || navigator.userLanguage || '';
  const detected = browserLang.startsWith('pt') ? 'pt-BR' : 'en';
  localStorage.setItem('app_lang', detected);
  return detected;
}

/**
 * Translate a key using the current language
 * Supports nested keys like 'auth.login_title'
 * Falls back to the key itself if not found
 */
function t(key) {
  const lang = getCurrentLang();
  const keys = key.split('.');
  let value = i18n[lang];
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      // Try fallback to pt-BR
      let fallback = i18n['pt-BR'];
      for (const fk of keys) {
        if (fallback && typeof fallback === 'object' && fk in fallback) {
          fallback = fallback[fk];
        } else {
          return key;
        }
      }
      return fallback;
    }
  }
  return value;
}

/**
 * Set language and reload page
 */
function setLang(lang) {
  const valid = lang === 'pt-BR' || lang === 'en';
  localStorage.setItem('app_lang', valid ? lang : 'pt-BR');
  location.reload();
}

/**
 * Toggle between pt-BR and en
 */
function toggleLang() {
  const current = getCurrentLang();
  setLang(current === 'pt-BR' ? 'en' : 'pt-BR');
}

/**
 * Apply translations to all elements with data-i18n attributes
 * Called automatically on DOMContentLoaded
 */
function applyTranslations() {
  // Translate text content
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    const translation = t(key);
    if (translation && translation.includes('<') && translation.includes('>')) {
      el.innerHTML = translation;
    } else if (translation) {
      el.textContent = translation;
    }
  });

  // Translate placeholders
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const translation = t(el.dataset.i18nPlaceholder);
    if (translation) el.placeholder = translation;
  });

  // Translate titles/tooltips
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const translation = t(el.dataset.i18nTitle);
    if (translation) el.title = translation;
  });

  // Translate aria-labels
  document.querySelectorAll('[data-i18n-aria]').forEach(el => {
    const translation = t(el.dataset.i18nAria);
    if (translation) el.setAttribute('aria-label', translation);
  });

  // Update language switcher buttons
  document.querySelectorAll('.lang-switch, .lang-switch-auth').forEach(el => {
    const currentLang = getCurrentLang();
    const targetLang = currentLang === 'pt-BR' ? 'en' : 'pt-BR';
    const display = currentLang === 'pt-BR' ? 'PT' : 'EN';
    el.textContent = display;
  });
}

// Auto-detect language on first visit
if (!localStorage.getItem('app_lang')) {
  const browserLang = navigator.language || navigator.userLanguage || '';
  localStorage.setItem('app_lang', browserLang.startsWith('pt') ? 'pt-BR' : 'en');
}

// Apply translations on DOM ready
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyTranslations);
  } else {
    applyTranslations();
  }
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
  window.t = t;
  window.setLang = setLang;
  window.toggleLang = toggleLang;
  window.getCurrentLang = getCurrentLang;
  window.applyTranslations = applyTranslations;
}
