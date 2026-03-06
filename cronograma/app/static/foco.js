const FocoTimer = (function() {
  const CIRCUMFERENCE = 2 * Math.PI * 90;
  
  let state = "idle";
  let isBreak = false;
  let tempoRestante = 25 * 60;
  let duracaoTotal = 25 * 60;
  let startTimestamp = null;
  let animationFrameId = null;
  let currentAreaId = null;
  let currentTaskId = null;
  let cachedAreas = null;
  let cachedTasks = null;
  let originalTitle = document.title;
  
  // Persistent audio - works in background
  let audioContext = null;
  let oscillator = null;
  
  const elements = {
    timerTime: document.getElementById("foco-timer-time"),
    timerLabel: document.getElementById("foco-timer-label"),
    timerProgress: document.querySelector(".foco-timer-progress"),
    startBtn: document.getElementById("foco-start"),
    pauseBtn: document.getElementById("foco-pause"),
    endBtn: document.getElementById("foco-end"),
    resetBtn: document.getElementById("foco-reset"),
    skipBtn: document.getElementById("foco-skip"),
    areaSelect: document.getElementById("foco-area"),
    taskSelect: document.getElementById("foco-task"),
    minutesInput: document.getElementById("foco-minutes"),
    breakMinutesInput: document.getElementById("foco-break-minutes"),
    autoBreakCheckbox: document.getElementById("foco-auto-break"),
    sessionsCount: document.getElementById("foco-sessions-count"),
    totalTime: document.getElementById("foco-total-time"),
    taskProgress: document.getElementById("foco-task-progress"),
    taskPomodoros: document.getElementById("foco-task-pomodoros"),
    taskMeta: document.getElementById("foco-task-meta"),
    progressFill: document.getElementById("foco-progress-fill"),
  };
  
  function init(areas, tasks) {
    cachedAreas = areas;
    cachedTasks = tasks;
    populateAreaSelect();
    loadState();
    updateProgressDisplay();
    loadTodayStats();
    attachEventListeners();
    checkActiveTimer();
  }
  
  function populateAreaSelect() {
    if (!elements.areaSelect) return;
    const opts = cachedAreas.map((a) => `<option value="${a.id}">${escapeHtml(a.nome)}</option>`).join("");
    elements.areaSelect.innerHTML = '<option value="">Selecione a área</option>' + opts;
    
    if (currentAreaId) {
      elements.areaSelect.value = currentAreaId;
      populateTaskSelect();
    }
  }
  
  function populateTaskSelect() {
    if (!elements.taskSelect || !currentAreaId) {
      elements.taskSelect.innerHTML = '<option value="">Selecione uma tarefa</option>';
      elements.taskSelect.disabled = true;
      return;
    }
    
    const areaTasks = cachedTasks.filter(t => t.area_id === currentAreaId && !t.concluida);
    if (areaTasks.length === 0) {
      elements.taskSelect.innerHTML = '<option value="">Nenhuma tarefa pendente</option>';
      elements.taskSelect.disabled = true;
      return;
    }
    
    const opts = areaTasks.map((t) => {
      const pomo = t.pomodoros_concluidos || 0;
      const meta = t.meta_pomodoros || 0;
      const metaText = meta > 0 ? ` (${pomo}/${meta})` : "";
      return `<option value="${t.id}">${escapeHtml(t.titulo)}${metaText}</option>`;
    }).join("");
    
    elements.taskSelect.innerHTML = '<option value="">Nenhuma tarefa específica</option>' + opts;
    elements.taskSelect.disabled = false;
    
    if (currentTaskId) {
      elements.taskSelect.value = currentTaskId;
    }
  }
  
  function loadState() {
    try {
      const saved = JSON.parse(localStorage.getItem("focoState") || "null");
      if (saved) {
        currentAreaId = saved.areaId || null;
        currentTaskId = saved.taskId || null;
        
        if (saved.state === "running" || saved.state === "paused") {
          const elapsed = Math.floor((Date.now() - saved.startTime) / 1000);
          tempoRestante = Math.max(0, saved.tempoRestante - elapsed);
          isBreak = saved.isBreak || false;
          duracaoTotal = saved.duracaoTotal || tempoRestante;
          
          if (saved.state === "paused") {
            startTimestamp = null;
          } else {
            startTimestamp = saved.startTime;
          }
          
          if (tempoRestante <= 0 && saved.state === "running") {
            onTimerComplete();
            clearState();
            return;
          }
          
          if (saved.state === "running" && tempoRestante > 0) {
            state = "running";
            updateButtons();
            elements.minutesInput.disabled = true;
            elements.areaSelect.disabled = true;
            elements.taskSelect.disabled = true;
            tick();
            saveState();
          }
        }
      }
    } catch (e) {
      console.log("Error loading foco state:", e);
    }
  }
  
  function saveState() {
    try {
      const stateToSave = {
        state: state,
        isBreak: isBreak,
        tempoRestante: tempoRestante,
        duracaoTotal: duracaoTotal,
        areaId: currentAreaId,
        taskId: currentTaskId,
        startTime: state === "running" ? (startTimestamp || Date.now()) : null,
      };
      localStorage.setItem("focoState", JSON.stringify(stateToSave));
    } catch (e) {
      console.log("Error saving foco state:", e);
    }
  }
  
  function clearState() {
    localStorage.removeItem("focoState");
  }
  
  function checkActiveTimer() {
    try {
      const saved = JSON.parse(localStorage.getItem("focoState") || "null");
      if (saved && (saved.state === "running" || saved.state === "paused")) {
        if (tempoRestante <= 0) {
          clearState();
          resetTimer();
        }
      }
    } catch (e) {
      console.log("Error checking active timer:", e);
    }
  }
  
  function attachEventListeners() {
    elements.startBtn?.addEventListener("click", handleStart);
    elements.pauseBtn?.addEventListener("click", handlePause);
    elements.endBtn?.addEventListener("click", endManually);
    elements.resetBtn?.addEventListener("click", handleReset);
    elements.skipBtn?.addEventListener("click", handleSkip);
    
    elements.areaSelect?.addEventListener("change", (e) => {
      currentAreaId = e.target.value ? parseInt(e.target.value, 10) : null;
      currentTaskId = null;
      populateTaskSelect();
      updateProgressDisplay();
      saveState();
    });
    
    elements.taskSelect?.addEventListener("change", (e) => {
      currentTaskId = e.target.value ? parseInt(e.target.value, 10) : null;
      updateProgressDisplay();
      saveState();
    });
    
    elements.minutesInput?.addEventListener("change", () => {
      if (state === "idle") {
        tempoRestante = (parseInt(elements.minutesInput.value, 10) || 25) * 60;
        duracaoTotal = tempoRestante;
        updateDisplay();
        saveState();
      }
    });
    
    elements.breakMinutesInput?.addEventListener("change", () => {
      if (isBreak && state === "idle") {
        tempoRestante = (parseInt(elements.breakMinutesInput.value, 10) || 5) * 60;
        duracaoTotal = tempoRestante;
        updateDisplay();
        saveState();
      }
    });
  }
  
  function handleStart() {
    if (state === "idle") {
      if (!currentAreaId) {
        alert("Selecione uma área para iniciar o foco!");
        return;
      }
      tempoRestante = (parseInt(elements.minutesInput.value, 10) || 25) * 60;
      duracaoTotal = tempoRestante;
      startTimestamp = Date.now();
      isBreak = false;
      elements.timerLabel.textContent = "Foco";
    }
    
    if (state !== "running") {
      state = "running";
      updateButtons();
      elements.minutesInput.disabled = true;
      elements.areaSelect.disabled = true;
      elements.taskSelect.disabled = true;
      
      tick();
      saveState();
    }
  }
  
  function handlePause() {
    if (state === "running") {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
      const elapsed = Math.floor((Date.now() - startTimestamp) / 1000);
      duracaoTotal = tempoRestante;
      startTimestamp = null;
      state = "paused";
      elements.pauseBtn.textContent = "▶ Continuar";
      saveState();
    } else if (state === "paused") {
      state = "running";
      startTimestamp = Date.now();
      duracaoTotal = tempoRestante;
      elements.pauseBtn.textContent = "⏸ Pausar";
      tick();
      saveState();
    }
  }
  
  function handleReset() {
    if (state === "running" || state === "paused") {
      if (!confirm("Tem certeza que deseja cancelar a sessão de foco?")) {
        return;
      }
    }
    resetTimer();
  }
  
  function handleSkip() {
    if (isBreak) {
      if (!confirm("Pular o descanso?")) return;
      cancelAnimationFrame(animationFrameId);
      playBeep();
      alert("Descanso finalizado! Ready para mais um pomodoro?");
      resetTimer();
    }
  }
  
  function resetTimer() {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
    startTimestamp = null;
    isBreak = false;
    state = "idle";
    tempoRestante = (parseInt(elements.minutesInput.value, 10) || 25) * 60;
    duracaoTotal = tempoRestante;
    elements.timerLabel.textContent = "Foco";
    updateDisplay();
    updateButtons();
    elements.minutesInput.disabled = false;
    elements.areaSelect.disabled = false;
    if (currentAreaId) elements.taskSelect.disabled = false;
    clearState();
  }
  
  function tick() {
    if (startTimestamp) {
      const elapsed = Math.floor((Date.now() - startTimestamp) / 1000);
      tempoRestante = Math.max(0, duracaoTotal - elapsed);
    }
    updateDisplay();
    updateTabTitle();
    
    if (tempoRestante <= 0) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
      startTimestamp = null;
      document.title = originalTitle;
      onTimerComplete();
    } else {
      animationFrameId = requestAnimationFrame(tick);
      saveState();
    }
  }
  
  function onTimerComplete() {
    playBeep();
    
    if (!isBreak) {
      completarPomodoro();
      
      if (elements.autoBreakCheckbox.checked) {
        startBreak();
      } else {
        state = "idle";
        alert("Pomodoro concluído! +" + (duracaoTotal / 60) + "min registrados.");
        resetTimer();
      }
    } else {
      alert("Tempo de descanso acabou! Ready para mais um pomodoro?");
      resetTimer();
    }
  }
  
  async function completarPomodoro() {
    if (!currentAreaId) return;
    
    const duracao = Math.round(duracaoTotal / 60);
    
    try {
      await post("/pomodoro/completar", {
        area_id: currentAreaId,
        duracao_minutos: duracao,
        task_id: currentTaskId || null,
      });
      
      loadTodayStats();
      updateProgressDisplay();
      
      if (typeof loadSessoes === "function") {
        loadSessoes(cachedAreas);
      }
      if (typeof loadResumo === "function") {
        loadResumo();
      }
    } catch (err) {
      console.error("Erro ao salvar pomodoro:", err);
    }
  }
  
  function startBreak() {
    isBreak = true;
    tempoRestante = (parseInt(elements.breakMinutesInput.value, 10) || 5) * 60;
    duracaoTotal = tempoRestante;
    startTimestamp = Date.now();
    elements.timerLabel.textContent = "Descanso";
    state = "running";
    
    updateDisplay();
    updateButtons();
    elements.taskSelect.disabled = true;
    
    tick();
    saveState();
  }
  
  function updateDisplay() {
    const mins = Math.floor(tempoRestante / 60);
    const secs = tempoRestante % 60;
    elements.timerTime.textContent = `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    
    const progress = ((duracaoTotal - tempoRestante) / duracaoTotal) * CIRCUMFERENCE;
    elements.timerProgress.style.strokeDashoffset = CIRCUMFERENCE - progress;
    
    elements.timerProgress.classList.remove("warning", "danger", "break");
    if (isBreak) {
      elements.timerProgress.classList.add("break");
    } else if (tempoRestante <= 10 && tempoRestante > 0) {
      elements.timerProgress.classList.add("danger");
    } else if (tempoRestante <= 30 && tempoRestante > 0) {
      elements.timerProgress.classList.add("warning");
    }
  }
  
  function updateButtons() {
    if (state === "idle") {
      elements.startBtn.style.display = "inline-block";
      elements.pauseBtn.style.display = "none";
      elements.resetBtn.style.display = "inline-block";
      elements.skipBtn.style.display = "none";
    } else if (state === "running") {
      elements.startBtn.style.display = "none";
      elements.pauseBtn.style.display = "inline-block";
      elements.pauseBtn.textContent = "⏸ Pausar";
      elements.resetBtn.style.display = "inline-block";
      elements.skipBtn.style.display = isBreak ? "inline-block" : "none";
    } else if (state === "paused") {
      elements.startBtn.style.display = "none";
      elements.pauseBtn.style.display = "inline-block";
      elements.pauseBtn.textContent = "▶ Continuar";
      elements.resetBtn.style.display = "inline-block";
      elements.skipBtn.style.display = "none";
    }
  }
  
  function updateProgressDisplay() {
    if (!currentTaskId) {
      elements.taskProgress.style.display = "none";
      return;
    }
    
    const task = cachedTasks?.find(t => t.id === currentTaskId);
    if (!task) {
      elements.taskProgress.style.display = "none";
      return;
    }
    
    const concluidos = task.pomodoros_concluidos || 0;
    const meta = task.meta_pomodoros || 0;
    
    if (meta > 0) {
      elements.taskProgress.style.display = "block";
      elements.taskPomodoros.textContent = concluidos;
      elements.taskMeta.textContent = meta;
      const percent = Math.min(100, (concluidos / meta) * 100);
      elements.progressFill.style.width = percent + "%";
    } else {
      elements.taskProgress.style.display = "none";
    }
  }
  
  async function loadTodayStats() {
    try {
      const sessoes = await get("/sessoes");
      const today = new Date().toISOString().split("T")[0];
      const todaySessions = sessoes.filter(s => s.data === today);
      
      const totalMin = todaySessions.reduce((sum, s) => sum + s.duracao_minutos, 0);
      
      if (elements.sessionsCount) {
        elements.sessionsCount.textContent = todaySessions.length;
      }
      if (elements.totalTime) {
        elements.totalTime.textContent = totalMin;
      }
    } catch (err) {
      console.error("Error loading today stats:", err);
    }
  }
  
  function playBeep() {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();
      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);
      oscillator.frequency.setValueAtTime(880, audioCtx.currentTime);
      gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
      oscillator.start();
      oscillator.stop(audioCtx.currentTime + 0.15);
    } catch (e) {
      console.log("Audio not supported");
    }
  }
  
  function refreshTasks(tasks) {
    cachedTasks = tasks;
    populateTaskSelect();
    updateProgressDisplay();
  }
  
  function refreshAreas(areas) {
    cachedAreas = areas;
    populateAreaSelect();
  }
  
  // Audio using Web Audio API - works in background
  function playBeep() {
    try {
      // Create audio context if not exists
      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      
      // Resume context if suspended (needed for background)
      if (audioContext.state === 'suspended') {
        audioContext.resume();
      }
      
      // Play notification sound
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.value = 800;
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
      
      // Play second beep
      setTimeout(() => {
        const osc2 = audioContext.createOscillator();
        const gain2 = audioContext.createGain();
        osc2.connect(gain2);
        gain2.connect(audioContext.destination);
        osc2.frequency.value = 1000;
        osc2.type = 'sine';
        gain2.gain.setValueAtTime(0.3, audioContext.currentTime);
        gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        osc2.start(audioContext.currentTime);
        osc2.stop(audioContext.currentTime + 0.5);
      }, 200);
      
    } catch (e) {
      console.error('Audio error:', e);
    }
  }
  
  // Update tab title with timer
  function updateTabTitle() {
    if (state === "running" || state === "paused") {
      const mins = Math.floor(tempoRestante / 60);
      const secs = tempoRestante % 60;
      const timeStr = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
      const label = isBreak ? "Descanso" : "Foco";
      document.title = `⏳ ${timeStr} - ${label}`;
    } else {
      document.title = originalTitle;
    }
  }
  
  // Manual end - calculate elapsed time and create session
  function endManually() {
    if (state !== "running" && state !== "paused") return;
    
    const elapsed = Math.floor((duracaoTotal - tempoRestante) / 60);
    if (elapsed < 1) {
      alert("Sessão muito curta para registrar.");
      return;
    }
    
    completarPomodoroManual(elapsed);
    resetTimer();
  }
  
  async function completarPomodoroManual(minutes) {
    if (!currentAreaId) return;
    
    try {
      await post("/pomodoro/completar", {
        area_id: currentAreaId,
        duracao_minutos: minutes,
        task_id: currentTaskId || null,
      });
      
      // Update AppStore with XP
      if (typeof AppStore !== 'undefined') {
        AppStore.addXP('pomodoro', minutes);
      }
      
      loadTodayStats();
      updateProgressDisplay();
      
      if (typeof loadSessoes === "function") loadSessoes(cachedAreas);
      if (typeof loadResumo === "function") loadResumo();
      
    } catch (e) {
      console.error('Erro ao registrar sessão:', e);
    }
  }
  
  function isActive() {
    return state === "running" || state === "paused";
  }
  
  return {
    init,
    refreshTasks,
    refreshAreas,
    isActive,
    loadTodayStats,
    endManually,
  };
})();

window.FocoTimer = FocoTimer;
