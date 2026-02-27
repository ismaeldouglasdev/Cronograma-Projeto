// Stores module - pode ser usado para estado global
const Stores = {
  areas: [],
  tasks: [],
  sessoes: [],
  
  setAreas(areas) {
    this.areas = areas;
  },
  
  setTasks(tasks) {
    this.tasks = tasks;
  },
  
  setSessoes(sessoes) {
    this.sessoes = sessoes;
  },
  
  getAreas() {
    return this.areas;
  },
  
  getTasks() {
    return this.tasks;
  },
  
  getSessoes() {
    return this.sessoes;
  }
};

window.Stores = Stores;
