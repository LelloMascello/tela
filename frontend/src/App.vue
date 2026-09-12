<script setup>
import { ref, computed, onMounted } from 'vue';
import { api } from './api/client';
import SearchBar from './components/SearchBar.vue';
import NoteCard from './components/NoteCard.vue';
import UploadModal from './components/UploadModal.vue';
import DetailModal from './components/DetailModal.vue';

const notes = ref([]);
const isLoading = ref(true);
const loadError = ref(null);
const isUploadModalOpen = ref(false);
const selectedNoteId = ref(null);
const activeFilter = ref('Tutti');
const currentQuery = ref('');

const filters = ['Tutti', 'PDF', 'Documenti', 'Immagini', 'Fogli', 'Presentazioni', 'Audio', 'Video'];
const filterExtensions = {
  PDF: ['pdf'],
  Documenti: ['docx', 'txt'],
  Immagini: ['jpg', 'jpeg', 'png', 'webp'],
  Fogli: ['xlsx'],
  Presentazioni: ['pptx'],
  Audio: ['mp3', 'wav'],
  Video: ['mp4', 'avi'],
};

// Bug fix: filter chips previously updated `activeFilter` but nothing
// ever read it, so clicking them had no visible effect.
const filteredNotes = computed(() => {
  if (activeFilter.value === 'Tutti') return notes.value;
  const exts = filterExtensions[activeFilter.value] ?? [];
  return notes.value.filter((note) => exts.includes((note.extension || '').toLowerCase()));
});

// Conteggi per etichetta filtro, calcolati sul set di note attualmente
// caricato (l'intero archivio, o i risultati di ricerca se si sta cercando).
const filterCounts = computed(() => {
  const counts = { Tutti: notes.value.length };
  for (const key of Object.keys(filterExtensions)) {
    const exts = filterExtensions[key];
    counts[key] = notes.value.filter((note) => exts.includes((note.extension || '').toLowerCase())).length;
  }
  return counts;
});

const fetchNotes = async () => {
  isLoading.value = true;
  loadError.value = null;
  try {
    const response = await api.get('/notes');
    notes.value = response.data.items;
  } catch (error) {
    console.error('Errore fetch notes', error);
    loadError.value = "Non riesco a raggiungere l'archivio. Controlla che il backend sia attivo.";
  } finally {
    isLoading.value = false;
  }
};

const handleSearch = async (query) => {
  currentQuery.value = query;
  if (query.length < 2) {
    fetchNotes();
    return;
  }
  isLoading.value = true;
  loadError.value = null;
  try {
    // Bug fix: the query was interpolated into the URL unencoded, so
    // spaces or symbols could break the request or drop characters.
    const response = await api.get(`/search?q=${encodeURIComponent(query)}`);
    notes.value = response.data.results;
  } catch (error) {
    console.error('Errore ricerca', error);
    loadError.value = 'La ricerca non è riuscita. Riprova tra poco.';
  } finally {
    isLoading.value = false;
  }
};

const handleNoteDeleted = () => {
  window.location.reload();
};

onMounted(fetchNotes);
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <h1>TELA</h1>
        <p>Tutto ciò che hai archiviato, indicizzato e reso ricercabile.</p>
      </div>
      <button type="button" class="btn-primary" @click="isUploadModalOpen = true">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v11"/><path d="M8 8l4-4 4 4"/><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/></svg>
        <span>Carica</span>
      </button>
    </header>

    <SearchBar @search="handleSearch" />

    <nav class="filter-row" aria-label="Filtra per tipo">
      <button
        v-for="filter in filters"
        :key="filter"
        type="button"
        :class="['filter-chip', { active: activeFilter === filter }]"
        :aria-pressed="activeFilter === filter"
        @click="activeFilter = filter"
      >
        {{ filter }}
        <span class="count">{{ filterCounts[filter] ?? 0 }}</span>
      </button>
    </nav>

    <main class="archive">
      <div v-if="isLoading" class="list-header" aria-hidden="true">
        <span></span><span>Documento</span><span>Stato</span><span>Data</span>
      </div>

      <ul v-if="isLoading" class="note-list" aria-busy="true" aria-label="Caricamento documenti">
        <li v-for="n in 6" :key="n" class="skeleton-row">
          <span class="sk sk-icon"></span>
          <span class="sk sk-title"></span>
          <span class="sk sk-status"></span>
          <span class="sk sk-date"></span>
        </li>
      </ul>

      <div v-else-if="loadError" class="state">
        <p class="state-title">L'archivio non risponde</p>
        <p class="state-body">{{ loadError }}</p>
      </div>

      <div v-else-if="filteredNotes.length === 0 && currentQuery.length >= 2" class="state">
        <p class="state-title">Nessun risultato per «{{ currentQuery }}»</p>
        <p class="state-body">Prova un altro termine o controlla i filtri attivi.</p>
      </div>

      <div v-else-if="filteredNotes.length === 0" class="state">
        <p class="state-title">L'archivio è vuoto</p>
        <p class="state-body">Carica il primo documento per iniziare a costruirlo.</p>
        <button type="button" class="btn-primary" @click="isUploadModalOpen = true">Carica un documento</button>
      </div>

      <template v-else>
        <div class="list-header">
          <span></span><span>Documento</span><span>Stato</span><span>Data</span>
        </div>
        <ul class="note-list">
          <NoteCard
            v-for="note in filteredNotes"
            :key="note.id"
            :note="note"
            @open-detail="selectedNoteId = note.id"
          />
        </ul>
      </template>
    </main>

    <UploadModal v-if="isUploadModalOpen" @close="isUploadModalOpen = false" @uploaded="fetchNotes" />
    <DetailModal
      v-if="selectedNoteId"
      :note-id="selectedNoteId"
      @close="selectedNoteId = null"
      @deleted="handleNoteDeleted"
      @updated="fetchNotes"
    />
  </div>
</template>

<style scoped>
.app-shell {
  margin: 0 auto;
  padding: 56px clamp(24px, 5vw, 96px) 96px;
  max-width: 1080px;
  width: 100%;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  margin-bottom: 32px;
}

.brand h1 {
  font-family: var(--font-mono);
  font-size: 26px;
  font-weight: 600;
  letter-spacing: 0.01em;
  margin: 0 0 6px;
  color: var(--ink);
}
.brand p {
  font-size: 15px;
  color: var(--ink-soft);
  margin: 0;
  max-width: 46ch;
}

.btn-primary {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 42px;
  padding: 0 18px;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #fff;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease, transform 0.1s ease;
}
.btn-primary:hover { background: var(--accent-strong); }
.btn-primary:active { transform: translateY(1px); }

.filter-row {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--line);
  margin: 28px 0 8px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.filter-row::-webkit-scrollbar { display: none; }
.filter-chip {
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
  padding: 11px 2px;
  margin-right: 22px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--ink-soft);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: color 0.15s ease, border-color 0.15s ease;
}
.filter-chip .count {
  font-size: 12.5px;
  color: var(--ink-faint);
  font-variant-numeric: tabular-nums;
}
.filter-chip:hover { color: var(--ink); }
.filter-chip.active { color: var(--ink); border-bottom-color: var(--accent); }
.filter-chip.active .count { color: var(--ink-soft); }

.archive { min-height: 240px; padding-top: 12px; }

/* Le colonne qui sotto devono restare identiche a quelle di .note-row in
   NoteCard.vue, così l'intestazione si allinea con le righe della lista. */
.list-header, .skeleton-row {
  display: grid;
  grid-template-columns: 36px 1fr 150px 100px;
  align-items: center;
  gap: 16px;
}
.list-header {
  padding: 0 4px 10px;
  font-family: var(--font-mono);
  font-size: 12.5px;
  color: var(--ink-faint);
}
.list-header span:nth-child(3),
.list-header span:nth-child(4) {
  text-align: left;
}

.note-list { list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--line); }

.skeleton-row { padding: 14px 4px; border-bottom: 1px solid var(--line); }
.sk {
  height: 14px;
  border-radius: 4px;
  background: linear-gradient(100deg, var(--surface-sunken) 30%, var(--line) 50%, var(--surface-sunken) 70%);
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}
.sk-icon { width: 28px; height: 28px; border-radius: var(--radius-sm); }
.sk-title { width: 70%; }
.sk-status { width: 80px; }
.sk-date { width: 60px; }
@keyframes shimmer { to { background-position: -200% 0; } }

.state {
  padding: 72px 24px;
  text-align: center;
  border: 1px dashed var(--line);
  border-radius: var(--radius-lg);
}
.state-title { font-size: 16px; font-weight: 600; color: var(--ink); margin: 0 0 6px; }
.state-body { font-size: 14px; color: var(--ink-soft); margin: 0 0 18px; }
.state .btn-primary { margin: 0 auto; }

@media (max-width: 720px) {
  .list-header { display: none; }
  .list-header, .skeleton-row { grid-template-columns: 32px 1fr; }
  .skeleton-row { display: flex; align-items: center; gap: 12px; }
  .sk-status, .sk-date { display: none; }
}

@media (max-width: 640px) {
  .app-shell { padding: 40px 20px 64px; }
  .topbar { flex-direction: column; align-items: stretch; }
  .btn-primary { justify-content: center; }
  .brand h1 { font-size: 23px; }
  .filter-row { margin: 22px 0 6px; }
  .filter-chip { padding: 12px 2px; }
}

@media (max-width: 380px) {
  .app-shell { padding: 32px 14px 48px; }
  .brand p { font-size: 14px; }
  .filter-chip { font-size: 13px; margin-right: 16px; }
}

@media (min-width: 641px) and (max-width: 1023px) {
  .app-shell { padding: 48px 32px 80px; }
}
</style>