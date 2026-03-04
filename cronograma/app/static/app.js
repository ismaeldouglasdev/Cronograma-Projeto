let API = "";

// Auto-detect API URL based on current location
(function() {
  const loc = window.location;
  if (loc.hostname === "localhost" || loc.hostname === "127.0.0.1") {
    API = `${loc.protocol}//${loc.host}:${loc.port || "80"}`;
  } else {
    API = `${loc.protocol}//${loc.host}`;
  }
})();

let cachedAreas = null;
let allAreas = [];

function getToken() {
  return localStorage.getItem("cronograma_token");
}

function getAuthHeader() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function getSubcategorias() {
  try {
    return JSON.parse(localStorage.getItem("subcategorias") || "[]");
  } catch {
    return [];
  }
}

function saveSubcategoria(sub) {
  if (!sub) return;
  const subs = getSubcategorias();
  if (!subs.includes(sub)) {
    subs.push(sub);
    localStorage.setItem("subcategorias", JSON.stringify(subs));
  }
}

function populateSubcategoriasDatalist() {
  const subs = getSubcategorias();
  const lists = document.querySelectorAll("#subcategoria-list, #subcategoria-list-edit");
  lists.forEach((list) => {
    list.innerHTML = subs.map((s) => `<option value="${escapeHtml(s)}">`).join("");
  });
}

async function get(url) {
  const r = await fetch(API + url, { headers: getAuthHeader() });
  if (!r.ok) throw new Error(r.statusText);
  return r.json();
}

async function post(url, body) {
  const r = await fetch(API + url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(r.statusText);
  return r.json();
}

async function patch(url, body) {
  const r = await fetch(API + url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(r.statusText);
  return r.json();
}

async function delReq(url) {
  const r = await fetch(API + url, { method: "DELETE", headers: getAuthHeader() });
  if (!r.ok) throw new Error(r.statusText);
}

function formatDate(str) {
  if (!str) return "";
  const d = new Date(str + "T12:00:00");
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
}

function formatDuration(minutes) {
  if (!minutes || minutes < 1) return "0min";
  if (minutes < 60) return minutes + "min";
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (mins === 0) return hours + "h";
  return hours + "h" + mins + "min";
}

function areaById(areas, id) {
  return areas.find((a) => a.id === id);
}

function areaNome(areas, id) {
  const a = areaById(areas, id);
  return a ? a.nome : "?";
}

function areaCor(areas, id) {
  const a = areaById(areas, id);
  return (a && a.cor) || "#6366f1";
}

async function loadAreas() {
  const areas = await get("/areas");
  
  const existingSubs = areas.filter((a) => a.subcategoria).map((a) => a.subcategoria);
  existingSubs.forEach((s) => saveSubcategoria(s));
  populateSubcategoriasDatalist();
  
  const categoryFilter = document.getElementById("filter-categoria");
  if (categoryFilter) {
    const subsFromAreas = areas.filter((a) => a.subcategoria).map((a) => a.subcategoria);
    const subsFromStorage = getSubcategorias();
    const allSubs = [...new Set([...subsFromAreas, ...subsFromStorage])];
    categoryFilter.innerHTML = '<option value="">Todas as categorias</option>' + allSubs.map((s) => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`).join("");
  }
  
  const opts = areas
    .map((a) => `<option value="${a.id}" data-color="${a.cor || "#6366f1"}">${escapeHtml(a.nome)}</option>`)
    .join("");
  const selectHtml = '<option value="">Selecione a área</option>' + opts;
  document.querySelectorAll('select[name="area_id"]').forEach((sel) => (sel.innerHTML = selectHtml));
  updateAreaSelected();
  
  renderAreasGrid(areas);
  
  return areas;
}

function renderAreasGrid(areas) {
  if (!areas || !areas.length) return;
  
  allAreas = areas;
  const searchTerm = document.getElementById("search-areas")?.value.toLowerCase() || "";
  const categoryFilter = document.getElementById("filter-categoria")?.value || "";
  
  let filtered = areas;
  if (searchTerm) {
    filtered = filtered.filter((a) => a.nome.toLowerCase().includes(searchTerm));
  }
  if (categoryFilter) {
    filtered = filtered.filter((a) => a.subcategoria === categoryFilter);
  }
  
  const container = document.getElementById("lista-areas");
  if (!container) return;
  
  if (!filtered.length) {
    container.innerHTML = '<p class="resumo-empty">Nenhuma área encontrada.</p>';
    return;
  }
  
  container.innerHTML = filtered
    .map((a) => {
      const meta = [];
      if (a.subcategoria) meta.push(a.subcategoria);
      let tipoLabel = a.tipo === "presencial" ? "Presencial" : "Online";
      let tipoInfo = "";
      if (a.tipo === "presencial") {
        const parts = [a.dia_semana, a.horario, a.sala ? `Sala ${a.sala}` : null, a.bloco ? `Bloco ${a.bloco}` : null].filter(Boolean);
        if (parts.length) tipoInfo = parts.join(" - ");
        if (a.professor) tipoInfo += ` · Prof: ${a.professor}`;
      }
      const bgColor = a.cor || "#6366f1";
      return `
        <div class="area-card" data-id="${a.id}" style="position:relative;">
          <div class="area-icon" style="background:${bgColor}20;color:${bgColor};">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
            </svg>
          </div>
          <div class="area-title">${escapeHtml(a.nome)}</div>
          ${a.subcategoria ? `<div class="area-category">${escapeHtml(a.subcategoria)}</div>` : ""}
          <div class="area-type">${tipoLabel}</div>
          ${tipoInfo ? `<div class="area-info">${tipoInfo}</div>` : ""}
          <button class="btn-del" data-id="${a.id}" data-type="area" title="Excluir">×</button>
        </div>
      `;
    })
    .join("");
  
  container.querySelectorAll(".area-card").forEach((card) => {
    card.addEventListener("click", (e) => {
      if (e.target.closest(".btn-del")) return;
      const area = areas.find((a) => a.id === parseInt(card.dataset.id, 10));
      if (area) openAreaModal(area);
    });
  });
  
  container.querySelectorAll(".btn-del[data-type='area']").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm("Excluir esta área? Tarefas e sessões serão removidas.")) return;
      await delReq(`/areas/${btn.dataset.id}`);
      horariosLoaded = false;
      const areas2 = await loadAreas();
      loadTasks(areas2);
      loadSessoes(areas2);
      loadResumo();
    });
  });
}

async function loadTasks(areas) {
  const tasks = await get("/tasks");
  const ul = document.getElementById("lista-tasks");
  const sortBy = document.getElementById("sort-tasks")?.value || "prioridade";
  
  let sortedTasks = [...tasks];
  if (sortBy === "prioridade") {
    sortedTasks.sort((a, b) => {
      if (a.concluida !== b.concluida) return a.concluida ? 1 : -1;
      const pa = a.prioridade || 0;
      const pb = b.prioridade || 0;
      if (pa !== pb) return pb - pa;
      return new Date(a.data_entrega) - new Date(b.data_entrega);
    });
  } else {
    sortedTasks.sort((a, b) => {
      if (a.concluida !== b.concluida) return a.concluida ? 1 : -1;
      return new Date(a.data_entrega) - new Date(b.data_entrega);
    });
  }
  
  if (!sortedTasks.length) {
    ul.innerHTML = '<li class="resumo-empty">Nenhuma tarefa. Adicione uma acima.</li>';
    return;
  }
  ul.innerHTML = sortedTasks
    .map(
      (t) => {
        const meta = [
          areaNome(areas, t.area_id),
          formatDate(t.data_entrega),
          t.concluida && t.duracao_minutos ? `${t.duracao_minutos} min` : null,
        ]
          .filter(Boolean)
          .join(" · ");
        
        const prioridadeClass = t.prioridade === 3 ? "prioridade-alta" : t.prioridade === 2 ? "prioridade-media" : t.prioridade === 1 ? "prioridade-baixa" : "";
        const prioridadeDot = t.prioridade ? `<span class="item-prioridade ${t.prioridade === 3 ? "alta" : t.prioridade === 2 ? "media" : "baixa"}"></span>` : "";
        
        return `
    <li class="${t.concluida ? "done" : ""} ${prioridadeClass}">
      <span class="item-dot" style="background:${areaCor(areas, t.area_id)}"></span>
      ${prioridadeDot}
      <div class="item-body">
        <div class="item-title">${escapeHtml(t.titulo)}</div>
        <div class="item-meta">${meta}</div>
      </div>
      <button class="item-check ${t.concluida ? "done" : ""}" data-id="${t.id}" data-done="${t.concluida}"></button>
      <button class="btn-del" data-id="${t.id}" data-type="task" title="Excluir">×</button>
    </li>
  `;
      }
    )
    .join("");
  ul.querySelectorAll(".item-body").forEach((body, i) => {
    body.addEventListener("click", (e) => {
      if (e.target.closest(".item-check") || e.target.closest(".btn-del")) return;
      openTaskModal(tasks[i], areas);
    });
  });
  ul.querySelectorAll(".item-check").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = parseInt(btn.dataset.id, 10);
      const done = btn.dataset.done === "true";
      if (!done) {
        const minutos = prompt("Quantos minutos você dedicou a esta tarefa?");
        if (minutos === null) return;
        const n = parseInt(minutos, 10);
        if (isNaN(n) || n < 1) {
          alert("Informe um número válido de minutos.");
          return;
        }
        await patch(`/tasks/${id}`, { concluida: true, duracao_minutos: n });
        const areas2 = await loadAreas();
        cachedAreas = areas2;
        loadTasks(areas2);
        loadSessoes(areas2);
        loadResumo();
      } else {
        await patch(`/tasks/${id}`, { concluida: false });
        const areas2 = await loadAreas();
        cachedAreas = areas2;
        loadTasks(areas2);
        loadSessoes(areas2);
        loadResumo();
      }
    });
  });
  ul.querySelectorAll(".btn-del[data-type='task']").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm("Excluir esta tarefa?")) return;
      await delReq(`/tasks/${btn.dataset.id}`);
      const freshAreas = await loadAreas();
      cachedAreas = freshAreas;
      loadTasks(freshAreas);
    });
  });
}

async function loadSessoes(areas) {
  const sessoes = await get("/sessoes");
  const ul = document.getElementById("lista-sessoes");
  if (!sessoes.length) {
    ul.innerHTML = '<li class="resumo-empty">Nenhuma sessão registrada.</li>';
    return;
  }
  ul.innerHTML = sessoes
    .map(
      (s) => `
    <li>
      <span class="item-dot" style="background:${areaCor(areas, s.area_id)}"></span>
      <div class="item-body" data-id="${s.id}">
        <div class="item-title">${areaNome(areas, s.area_id)}</div>
        <div class="item-meta">${s.duracao_minutos} min · ${formatDate(s.data)}</div>
      </div>
      <button class="btn-del" data-id="${s.id}" data-type="sessao" title="Excluir">×</button>
    </li>
  `
    )
    .join("");
  ul.querySelectorAll(".item-body[data-id]").forEach((body) => {
    body.style.cursor = "pointer";
    body.addEventListener("click", () => {
      const sessao = sessoes.find((s) => s.id === parseInt(body.dataset.id, 10));
      if (sessao) openSessaoModal(sessao, areas);
    });
  });
  ul.querySelectorAll(".btn-del[data-type='sessao']").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm("Excluir esta sessão?")) return;
      await delReq(`/sessoes/${btn.dataset.id}`);
      const freshAreas = await loadAreas();
      loadSessoes(freshAreas);
      loadResumo();
    });
  });
}

async function openTaskModal(task, areas) {
  const modal = document.getElementById("modal-task");
  const form = document.getElementById("form-edit-task");
  
  form.id.value = task.id;
  
  const areaSelect = form.querySelector('select[name="area_id"]');
  const opts = areas.map((a) => `<option value="${a.id}">${escapeHtml(a.nome)}</option>`).join("");
  areaSelect.innerHTML = '<option value="">Selecione a área</option>' + opts;
  areaSelect.value = task.area_id;
  
  form.titulo.value = task.titulo;
  form.descricao.value = task.descricao || "";
  form.data_entrega.value = task.data_entrega;
  form.concluida.value = task.concluida ? "true" : "false";
  form.prioridade.value = task.prioridade || "";
  form.meta_pomodoros.value = task.meta_pomodoros || "";
  
  const pomoProgress = document.getElementById("edit-pomo-progress");
  const pomoConcluidos = document.getElementById("edit-pomo-concluidos");
  if (task.meta_pomodoros) {
    pomoProgress.style.display = "block";
    pomoConcluidos.textContent = task.pomodoros_concluidos || 0;
  } else {
    pomoProgress.style.display = "none";
  }
  
  const duracaoContainer = document.getElementById("edit-duracao-container");
  if (task.concluida && task.duracao_minutos) {
    duracaoContainer.style.display = "block";
    form.duracao_minutos.value = task.duracao_minutos;
  } else {
    duracaoContainer.style.display = "none";
    form.duracao_minutos.value = "";
  }
  
  form.concluida.addEventListener("change", () => {
    const isConcluida = form.concluida.value === "true";
    duracaoContainer.style.display = isConcluida ? "block" : "none";
  });
  
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
}

function closeTaskModal() {
  const modal = document.getElementById("modal-task");
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
}

function openAreaModal(area) {
  const modal = document.getElementById("modal-area");
  const form = document.getElementById("form-edit-area");
  form.id.value = area.id;
  form.nome.value = area.nome;
  form.cor.value = area.cor || "#6366f1";
  form.tipo.value = area.tipo || "online";
  form.subcategoria.value = area.subcategoria || "";
  form.dia_semana.value = area.dia_semana || "";
  form.horario.value = area.horario || "";
  form.sala.value = area.sala || "";
  form.bloco.value = area.bloco || "";
  form.professor.value = area.professor || "";

  const editColorPreview = document.getElementById("edit-color-preview");
  if (editColorPreview) editColorPreview.style.background = area.cor || "#6366f1";

  const editTipoAula = document.getElementById("edit-tipo-aula");
  const editCamposPresencial = document.getElementById("edit-campos-presencial");
  if (editTipoAula && editCamposPresencial) {
    editCamposPresencial.style.display = editTipoAula.value === "presencial" ? "flex" : "none";
  }

  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
}

function closeAreaModal() {
  const modal = document.getElementById("modal-area");
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
}

function openSessaoModal(sessao, areas) {
  const modal = document.getElementById("modal-sessao");
  const form = document.getElementById("form-edit-sessao");

  form.id.value = sessao.id;

  const areaSelect = form.querySelector('select[name="area_id"]');
  const opts = areas.map((a) => `<option value="${a.id}">${escapeHtml(a.nome)}</option>`).join("");
  areaSelect.innerHTML = '<option value="">Selecione a área</option>' + opts;
  areaSelect.value = sessao.area_id;

  form.duracao_minutos.value = sessao.duracao_minutos;
  form.data.value = sessao.data;

  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
}

function closeSessaoModal() {
  const modal = document.getElementById("modal-sessao");
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
}

function updateColorPreview() {
  const input = document.querySelector('#form-area input[name="cor"]');
  const preview = document.getElementById("color-preview");
  if (input && preview) preview.style.background = input.value || "#6366f1";
}

function updateAreaSelected() {
  const sel = document.querySelector("#form-task select[name='area_id']");
  const span = document.getElementById("area-selected");
  if (!sel || !span) return;
  const opt = sel.options[sel.selectedIndex];
  if (opt && opt.value) {
    span.innerHTML = `<span class="dot" style="background:${opt.dataset.color || "#6366f1"}"></span>${escapeHtml(opt.text)}`;
    span.classList.add("has-value");
  } else {
    span.textContent = "";
    span.classList.remove("has-value");
  }
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function initModal() {
  const modal = document.getElementById("modal-task");
  modal.querySelector(".modal-close").addEventListener("click", closeTaskModal);
  modal.querySelector(".modal-backdrop").addEventListener("click", closeTaskModal);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal.classList.contains("open")) closeTaskModal();
  });

  const areaModal = document.getElementById("modal-area");
  areaModal.querySelector(".modal-close").addEventListener("click", closeAreaModal);
  areaModal.querySelector(".modal-backdrop").addEventListener("click", closeAreaModal);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && areaModal.classList.contains("open")) closeAreaModal();
  });

  const editColorInput = document.querySelector('#form-edit-area input[name="cor"]');
  editColorInput?.addEventListener("input", () => {
    const preview = document.getElementById("edit-color-preview");
    if (preview) preview.style.background = editColorInput.value || "#6366f1";
  });

  const editTipoAula = document.getElementById("edit-tipo-aula");
  editTipoAula?.addEventListener("change", () => {
    const camposPresencial = document.getElementById("edit-campos-presencial");
    if (camposPresencial) {
      camposPresencial.style.display = editTipoAula.value === "presencial" ? "flex" : "none";
    }
  });

  const formEditArea = document.getElementById("form-edit-area");
  formEditArea.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const fd = new FormData(e.target);
      const id = fd.get("id");
      const tipo = fd.get("tipo");
      const subcategoria = fd.get("subcategoria")?.trim() || null;
      if (subcategoria) saveSubcategoria(subcategoria);

      const data = {
        nome: fd.get("nome") || null,
        cor: fd.get("cor") || null,
        tipo: tipo || null,
        subcategoria: subcategoria,
      };
      if (tipo === "presencial") {
        data.dia_semana = fd.get("dia_semana") || null;
        data.horario = fd.get("horario") || null;
        data.sala = fd.get("sala") || null;
        data.bloco = fd.get("bloco") || null;
        data.professor = fd.get("professor") || null;
      } else {
        data.dia_semana = null;
        data.horario = null;
        data.sala = null;
        data.bloco = null;
        data.professor = null;
      }
      await patch(`/areas/${id}`, data);
      populateSubcategoriasDatalist();
      closeAreaModal();
      horariosLoaded = false;
      const areasUpdated = await loadAreas();
      cachedAreas = areasUpdated;
      loadTasks(areasUpdated);
    } catch (err) {
      alert("Erro ao salvar: " + err.message);
    }
  });

  const formEditTask = document.getElementById("form-edit-task");
  formEditTask.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const id = fd.get("id");
    const concluida = fd.get("concluida") === "true";
    const duracao = fd.get("duracao_minutos") ? parseInt(fd.get("duracao_minutos"), 10) : null;
    const prioridade = fd.get("prioridade") ? parseInt(fd.get("prioridade"), 10) : null;
    const metaPomodoros = fd.get("meta_pomodoros") ? parseInt(fd.get("meta_pomodoros"), 10) : null;
    const data = {
      area_id: parseInt(fd.get("area_id"), 10),
      titulo: fd.get("titulo"),
      descricao: fd.get("descricao") || null,
      data_entrega: fd.get("data_entrega"),
      concluida: concluida,
      duracao_minutos: duracao,
      prioridade: prioridade,
      meta_pomodoros: metaPomodoros,
    };
    await patch(`/tasks/${id}`, data);
    closeTaskModal();
    const areasUpdated = await loadAreas();
    cachedAreas = areasUpdated;
    const tasks = await get("/tasks");
    loadTasks(areasUpdated);
    if (typeof FocoTimer !== "undefined") {
      FocoTimer.refreshTasks(tasks);
    }
  });

  const sessaoModal = document.getElementById("modal-sessao");
  sessaoModal.querySelector(".modal-close").addEventListener("click", closeSessaoModal);
  sessaoModal.querySelector(".modal-backdrop").addEventListener("click", closeSessaoModal);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && sessaoModal.classList.contains("open")) closeSessaoModal();
  });

  const formEditSessao = document.getElementById("form-edit-sessao");
  formEditSessao.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const id = fd.get("id");
    const data = {
      area_id: parseInt(fd.get("area_id"), 10),
      duracao_minutos: parseInt(fd.get("duracao_minutos"), 10),
      data: fd.get("data"),
    };
    await patch(`/sessoes/${id}`, data);
    closeSessaoModal();
    loadSessoes(await loadAreas());
    loadResumo();
  });
}

const DIAS_SEMANA = [
  { key: "segunda", label: "Segunda-feira" },
  { key: "terca", label: "Terça-feira" },
  { key: "quarta", label: "Quarta-feira" },
  { key: "quinta", label: "Quinta-feira" },
  { key: "sexta", label: "Sexta-feira" },
  { key: "sabado", label: "Sábado" },
  { key: "domingo", label: "Domingo" },
];

let horariosLoaded = false;

async function loadHorarios() {
  if (horariosLoaded) return;
  
  const areas = await get("/areas");
  const presencialAreas = areas.filter((a) => a.tipo === "presencial" && a.dia_semana);
  
  const container = document.getElementById("quadro-horarios");
  
  if (!presencialAreas.length) {
    container.innerHTML = '<p class="aula-empty">Nenhuma aula presencial cadastrada. Adicione áreas presenciais com dia da semana.</p>';
    horariosLoaded = true;
    return;
  }
  
  container.innerHTML = DIAS_SEMANA.map((dia) => {
    const aulas = presencialAreas.filter((a) => a.dia_semana === dia.key);
    const aulasHtml = aulas.length
      ? aulas
          .map(
            (a) => `
          <div class="aula-item" style="background:${a.cor || "#6366f1"}22;">
            <span class="item-dot" style="background:${a.cor || "#6366f1"}"></span>
            <div class="aula-info">
              <div class="aula-nome">${escapeHtml(a.nome)}</div>
              <div class="aula-detalhes">
                ${a.horario || ""} ${a.sala ? `· Sala ${a.sala}` : ""} ${a.bloco ? `(${a.bloco})` : ""}
                ${a.professor ? `· Prof. ${a.professor}` : ""}
              </div>
            </div>
          </div>
        `
          )
          .join("")
      : '<p class="aula-empty">Sem aulas</p>';
    
    return `
      <div class="dia-card">
        <div class="dia-header">${dia.label}</div>
        <div class="dia-aulas">${aulasHtml}</div>
      </div>
    `;
  }).join("");
  
  horariosLoaded = true;
}

let resumoLoaded = false;

async function loadResumo() {
  if (resumoLoaded) return;
  
  try {
    const resumo = await get("/sessoes/resumo");
    
    const container = document.getElementById("resumo-horas");
    const chartCanvas = document.getElementById("chart-resumo");
    
    if (!resumo.length) {
      container.innerHTML = '<p class="resumo-empty">Nenhuma sessão registrada ainda.</p>';
      
      // Zeros quando não há dados
      document.getElementById("resumo-horas-total").textContent = "0";
      document.getElementById("resumo-sessoes-total").textContent = "0";
      document.getElementById("resumo-areas-total").textContent = "0";
      
      resumoLoaded = true;
      return;
    }
    
    // Calcular totais
    const totalMinutos = resumo.reduce((sum, r) => sum + r.total_minutos, 0);
    const totalHoras = (totalMinutos / 60).toFixed(1);
    const totalSessoes = resumo.length;
    const totalAreas = resumo.length;
    
    // Atualizar métricas principais
    document.getElementById("resumo-horas-total").textContent = totalHoras;
    document.getElementById("resumo-sessoes-total").textContent = totalSessoes;
    document.getElementById("resumo-areas-total").textContent = totalAreas;
    
    // Encontrar o máximo para as barras
    const maxMinutos = Math.max(...resumo.map(r => r.total_minutos));
    
    // Renderizar lista com barras de progresso
    container.innerHTML = resumo
      .map((r) => {
        const percent = maxMinutos > 0 ? (r.total_minutos / maxMinutos) * 100 : 0;
        return `
          <div class="resumo-item">
            <span class="resumo-dot" style="background:${r.area_cor || '#6366f1'}"></span>
            <div class="resumo-item-info">
              <div class="resumo-item-header">
                <span class="resumo-nome">${escapeHtml(r.area_nome)}</span>
                <span class="resumo-tempo">${r.total_horas}h</span>
              </div>
              <div class="resumo-progress-bar">
                <div class="resumo-progress-fill" style="width: ${percent}%; background: ${r.area_cor || '#6366f1'}"></div>
              </div>
            </div>
          </div>
        `;
      }).join("");
    
    // Destruir gráfico anterior se existir
    if (chartResumo) {
      chartResumo.destroy();
      chartResumo = null;
    }
    
    // Renderizar gráfico de barras se Chart.js estiver disponível
    if (typeof Chart !== "undefined" && chartCanvas) {
      chartResumo = new Chart(chartCanvas, {
        type: "bar",
        data: {
          labels: resumo.map((r) => r.area_nome),
          datasets: [{
            label: "Minutos",
            data: resumo.map((r) => r.total_minutos),
            backgroundColor: resumo.map((r) => r.area_cor || "#6366f1"),
            borderRadius: 6,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          indexAxis: 'y', // Gráfico de barras horizontal
          plugins: {
            legend: { display: false },
          },
          scales: {
            x: {
              beginAtZero: true,
              grid: { color: "rgba(255,255,255,0.06)" },
              ticks: { color: "#9b9a97" },
            },
            y: {
              grid: { display: false },
              ticks: { color: "#9b9a97" },
            },
          },
        },
      });
    }
    
    resumoLoaded = true;
  } catch (e) {
    console.error("Erro ao carregar resumo:", e);
  }
}

// Page titles for each tab
const PAGE_TITLES = {
  'areas': 'Áreas',
  'foco': 'Foco',
  'gamificacao': 'Gamificação',
  'horarios': 'Quadro de Horários',
  'tasks': 'Tarefas',
  'sessoes': 'Sessões',
  'resumo': 'Resumo'
};

function switchToTab(tabName) {
  // Update all tab/sidebar-link elements
  document.querySelectorAll('.tab, .sidebar-link').forEach((t) => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach((p) => p.classList.remove('active'));
  
  // Activate the selected tab/sidebar-link
  const tabButton = document.querySelector(`.tab[data-tab="${tabName}"]`) || 
                    document.querySelector(`.sidebar-link[data-tab="${tabName}"]`);
  if (tabButton) {
    tabButton.classList.add('active');
  }
  
  // Show the panel
  const panel = document.getElementById(tabName);
  if (panel) {
    panel.classList.add('active');
  }
  
  // Update page title
  const pageTitle = document.getElementById('page-title');
  if (pageTitle && PAGE_TITLES[tabName]) {
    pageTitle.textContent = PAGE_TITLES[tabName];
  }
  
  // Load data if needed
  if (tabName === 'horarios') {
    loadHorarios();
  }
  if (tabName === 'resumo') {
    loadResumo();
  }
}

function initTabs() {
  let alertShownThisSession = false;
  
  // Handle original tabs
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      if (typeof FocoTimer !== "undefined" && FocoTimer.isActive()) {
        if (!alertShownThisSession && !confirm("Trocar de aba?")) {
          return;
        }
        alertShownThisSession = true;
      }
      
      switchToTab(tab.dataset.tab);
    });
  });
  
  // Handle sidebar links
  document.querySelectorAll(".sidebar-link").forEach((link) => {
    link.addEventListener("click", () => {
      if (typeof FocoTimer !== "undefined" && FocoTimer.isActive()) {
        if (!alertShownThisSession && !confirm("Trocar de aba?")) {
          return;
        }
        alertShownThisSession = true;
      }
      
      switchToTab(link.dataset.tab);
    });
  });
}

async function init() {
  initTabs();
  initModal();
  updateColorPreview();
  populateSubcategoriasDatalist();

  const searchAreas = document.getElementById("search-areas");
  const filterCategoria = document.getElementById("filter-categoria");
  const sortTasks = document.getElementById("sort-tasks");
  
  searchAreas?.addEventListener("input", () => renderAreasGrid(allAreas));
  filterCategoria?.addEventListener("change", () => renderAreasGrid(allAreas));
  
  sortTasks?.addEventListener("change", async () => {
    if (!cachedAreas) cachedAreas = await loadAreas();
    loadTasks(cachedAreas);
  });

  const formArea = document.getElementById("form-area");
  formArea.querySelector('input[name="cor"]')?.addEventListener("input", updateColorPreview);

  const tipoAula = document.getElementById("tipo-aula");
  const camposPresencial = document.getElementById("campos-presencial");
  tipoAula?.addEventListener("change", () => {
    camposPresencial.style.display = tipoAula.value === "presencial" ? "flex" : "none";
  });

  let areas = await loadAreas();
  cachedAreas = areas;

  formArea.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const tipo = fd.get("tipo") || "online";
    const subcategoria = fd.get("subcategoria")?.trim() || null;
    if (subcategoria) saveSubcategoria(subcategoria);

    const data = {
      nome: fd.get("nome"),
      cor: fd.get("cor") || null,
      tipo: tipo,
      subcategoria: subcategoria,
    };
    if (tipo === "presencial") {
      data.dia_semana = fd.get("dia_semana") || null;
      data.horario = fd.get("horario") || null;
      data.sala = fd.get("sala") || null;
      data.bloco = fd.get("bloco") || null;
      data.professor = fd.get("professor") || null;
    }
    await post("/areas", data);
    e.target.reset();
    populateSubcategoriasDatalist();
    formArea.querySelector('input[name="cor"]').value = "#6366f1";
    updateColorPreview();
    camposPresencial.style.display = "none";
    horariosLoaded = false;
    const newAreas = await loadAreas();
    cachedAreas = newAreas;
    loadTasks(newAreas);
    populateSubcategoriasDatalist();
  });

  const formTask = document.getElementById("form-task");
  formTask.querySelector('select[name="area_id"]')?.addEventListener("change", updateAreaSelected);

  formTask.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const data = fd.get("data_entrega");
    const prioridade = fd.get("prioridade") ? parseInt(fd.get("prioridade"), 10) : null;
    const metaPomodoros = fd.get("meta_pomodoros") ? parseInt(fd.get("meta_pomodoros"), 10) : null;
    await post("/tasks", {
      area_id: parseInt(fd.get("area_id"), 10),
      titulo: fd.get("titulo"),
      descricao: fd.get("descricao")?.trim() || null,
      data_entrega: data,
      prioridade: prioridade,
      meta_pomodoros: metaPomodoros,
    });
    e.target.reset();
    cachedAreas = await loadAreas();
    const tasks = await get("/tasks");
    loadTasks(cachedAreas);
    if (typeof FocoTimer !== "undefined") {
      FocoTimer.refreshTasks(tasks);
    }
  });

  const formSessao = document.getElementById("form-sessao");
  formSessao.querySelector('input[name="data"]').placeholder = "Opcional (hoje)";

  formSessao.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const dataVal = fd.get("data");
    await post("/sessoes", {
      area_id: parseInt(fd.get("area_id"), 10),
      duracao_minutos: parseInt(fd.get("duracao_minutos"), 10),
      data: dataVal || null,
    });
    e.target.reset();
    const newAreas = await loadAreas();
    cachedAreas = newAreas;
    loadSessoes(newAreas);
    loadResumo();
  });

  await loadTasks(areas);
  await loadSessoes(areas);
  await loadResumo();
  
  // Sincronizar com AppStore para persistência de gamificação
  if (typeof AppStore !== 'undefined') {
    AppStore.init();
    AppStore.setAreas(areas);
    const allTasks = await get('/tasks');
    AppStore.setTasks(allTasks);
    
    // Sincronizar com backend (SSOT - Fonte Única de Verdade)
    await AppStore.syncFromBackend();
    
    // Renderizar gamificação com dados do store
    if (typeof renderGamification === 'function') {
      renderGamification();
    }
  }
  
  if (typeof FocoTimer !== "undefined") {
    const tasks = await get("/tasks");
    FocoTimer.init(areas, tasks);
  }
  
  // Inicializar gamificação
  if (typeof Gamification !== "undefined") {
    Gamification.init();
    renderGamification();
  }
}

async function initApp() {
  return init();
}

window.initApp = initApp;

document.addEventListener("DOMContentLoaded", () => {
  // A inicialização será feita pelo Auth após login
});

// Função para renderizar gamificação
function renderGamification() {
  // Preferir AppStore (novo sistema centralizado)
  if (typeof AppStore !== 'undefined') {
    const state = AppStore.getState();
    const stats = state.stats;
    
    // Atualizar elementos do hero
    document.getElementById("gami-level").textContent = stats.level;
    document.getElementById("gami-xp-current").textContent = stats.xpForCurrentLevel;
    document.getElementById("gami-xp-next").textContent = stats.xpForNextLevel;
    document.getElementById("gami-xp-total").textContent = stats.totalXP;
    document.getElementById("gami-streak").textContent = stats.currentStreak;
    document.getElementById("gami-pomodoros").textContent = stats.totalPomodoros;
    document.getElementById("gami-tarefas").textContent = stats.completedTasks;
    document.getElementById("gami-areas").textContent = state.areas.length;
    
    // Atualizar sidebar stats
    const sidebarLevel = document.getElementById("sidebar-level");
    const sidebarXp = document.getElementById("sidebar-xp");
    const sidebarStreak = document.getElementById("sidebar-streak");
    if (sidebarLevel) sidebarLevel.textContent = stats.level;
    if (sidebarXp) sidebarXp.textContent = stats.totalXP;
    if (sidebarStreak) sidebarStreak.textContent = stats.currentStreak;
    
    // Barra de XP com percentual
    const xpPercent = stats.xpForNextLevel > 0 
      ? Math.min((stats.xpForCurrentLevel / stats.xpForNextLevel) * 100, 100) 
      : 0;
    document.getElementById("gami-xp-fill").style.width = xpPercent + "%";
    document.getElementById("gami-xp-percent").textContent = Math.round(xpPercent) + "%";
    
    // Renderizar conquistas por categoria
    const achievements = state.achievements;
    const categorias = ['xp', 'streak', 'pomodoro', 'tasks', 'level', 'coins'];
    
    categorias.forEach(catId => {
      const container = document.getElementById(`gami-badges-${catId}`);
      if (!container || !achievements[catId]) return;
      
      container.innerHTML = achievements[catId].map(ach => `
        <div class="gami-badge ${ach.unlocked ? 'unlocked' : 'locked'}" title="${ach.description}">
          <span class="gami-badge-icon">${ach.title.split(' ')[0]}</span>
          <span class="gami-badge-name">${ach.title.split(' ').slice(1).join(' ')}</span>
        </div>
      `).join('');
    });
    
    return;
  }
  
  // Fallback para Gamification antigo
  if (typeof Gamification === "undefined") return;
  
  const progress = Gamification.getProgresso();
  
  // Atualizar elementos do hero
  document.getElementById("gami-level").textContent = progress.level;
  document.getElementById("gami-xp-current").textContent = progress.xp_atual;
  document.getElementById("gami-xp-next").textContent = progress.xp_proximo;
  document.getElementById("gami-xp-total").textContent = progress.xp_total;
  document.getElementById("gami-streak").textContent = progress.streak_dias;
  document.getElementById("gami-pomodoros").textContent = progress.pomodoros_total;
  document.getElementById("gami-tarefas").textContent = progress.tarefas_concluidas;
  document.getElementById("gami-areas").textContent = progress.areas_criadas;
  
  // Atualizar sidebar stats (fallback)
  const sidebarLevel = document.getElementById("sidebar-level");
  const sidebarXp = document.getElementById("sidebar-xp");
  const sidebarStreak = document.getElementById("sidebar-streak");
  if (sidebarLevel) sidebarLevel.textContent = progress.level;
  if (sidebarXp) sidebarXp.textContent = progress.xp_total;
  if (sidebarStreak) sidebarStreak.textContent = progress.streak_dias;
  
  // Barra de XP com percentual
  const xpPercent = Math.min((progress.xp_atual / progress.xp_proximo) * 100, 100);
  document.getElementById("gami-xp-fill").style.width = xpPercent + "%";
  document.getElementById("gami-xp-percent").textContent = Math.round(xpPercent) + "%";
  
  // Categorias de badges: xp, streak, pomodoro, tasks, level
  const categorias = [
    { id: 'xp', key: 'xp' },
    { id: 'streak', key: 'streak' },
    { id: 'pomodoro', key: 'pomodoro' },
    { id: 'tasks', key: 'tarefa' },
    { id: 'level', key: 'level' }
  ];
  
  categorias.forEach(cat => {
    const container = document.getElementById(`gami-badges-${cat.id}`);
    if (!container) return;
    
    // Filtrar badges desta categoria
    const badgesDaCategoria = Gamification.BADGES.filter(b => b.tipo === cat.key || (cat.id === 'level' && b.tipo === 'level'));
    
    if (badgesDaCategoria.length === 0) {
      // Se não há badges locais, tentar usar dados do backend
      container.innerHTML = '<p class="gami-empty">Carregando conquistas...</p>';
      return;
    }
    
    container.innerHTML = badgesDaCategoria.map(badge => {
      const unlocked = progress.badges.includes(badge.id);
      return `
        <div class="gami-badge ${unlocked ? 'unlocked' : 'locked'}" title="${badge.descricao}">
          <span class="gami-badge-icon">${badge.nome.split(' ')[0]}</span>
          <span class="gami-badge-name">${badge.nome.split(' ').slice(1).join(' ')}</span>
        </div>
      `;
    }).join("");
  });
}
