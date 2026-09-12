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
  <div class="app-layout">
    <header class="main-header">
      <div class="header-top">
        <div class="header-titles">
          <h1>TELA</h1>
          <p>Tutto ciò che hai archiviato, indicizzato e reso ricercabile.</p>
        </div>
        <button type="button" class="upload-fab" @click="isUploadModalOpen = true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          <span>Carica</span>
        </button>
      </div>

      <SearchBar @search="handleSearch" />
    </header>

    <nav class="filters" aria-label="Filtra per tipo">
      <button
        v-for="filter in filters"
        :key="filter"
        type="button"
        :class="['filter-tab', { active: activeFilter === filter }]"
        :aria-pressed="activeFilter === filter"
        @click="activeFilter = filter"
      >
        {{ filter }}
      </button>
    </nav>

    <main class="content-area">
      <div v-if="isLoading" class="grid-container" aria-busy="true" aria-label="Caricamento documenti">
        <div v-for="n in 6" :key="n" class="skeleton-card"></div>
      </div>

      <p v-else-if="loadError" class="state-message state-message--error">{{ loadError }}</p>

      <p v-else-if="filteredNotes.length === 0 && currentQuery.length >= 2" class="state-message">
        Nessun risultato per «{{ currentQuery }}». Prova un altro termine.
      </p>

      <p v-else-if="filteredNotes.length === 0" class="state-message">
        Non ci sono ancora documenti qui. Carica il primo per iniziare.
      </p>

      <div v-else class="grid-container">
        <NoteCard
          v-for="note in filteredNotes"
          :key="note.id"
          :note="note"
          @open-detail="selectedNoteId = note.id"
        />
      </div>
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

<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,500;0,8..60,600;0,8..60,700;1,8..60,600&family=Caveat:wght@500;600;700&family=Special+Elite&family=Work+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  /* Paper & ink — a writing desk: parchment, iron-gall ink, and taped-on scraps */
  --color-page: #ece1c9;
  --color-card: #faf5e7;
  --color-card-raised: #fffcf4;
  --color-ink: #2b241d;
  --color-ink-soft: #5c5142;
  --color-line: #d8c8a0;
  --color-line-strong: #c1aa78;
  --color-stamp: #a3452b;
  --color-stamp-hover: #85371f;
  --color-stamp-wash: #f0ddd0;
  --color-tape-1: #d9b65f;
  --color-tape-2: #7f9c8f;
  --color-tape-3: #c88f85;
  --color-status-pending: #a97a2a;
  --color-status-done: #3f6b4c;
  --color-status-error: #ab3a35;

  --font-display: 'Source Serif 4', Georgia, 'Times New Roman', serif;
  --font-hand: 'Caveat', cursive;
  --font-ui: 'Work Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'IBM Plex Mono', 'Menlo', 'Consolas', monospace;
  --font-stamp: 'Special Elite', var(--font-mono);

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-modal: 14px;
  --radius-card: 3px 16px 4px 16px;
  --radius-stamp: 3px;

  --shadow-card: 0 1px 1px rgba(43, 36, 29, 0.09), 0 12px 22px -14px rgba(43, 36, 29, 0.4);
  --shadow-modal: 0 40px 70px -24px rgba(20, 15, 10, 0.5);
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: var(--font-ui);
  color: var(--color-ink);
  background-color: var(--color-page);
  background-image:
    radial-gradient(circle at 1px 1px, rgba(43, 36, 29, 0.05) 1px, transparent 0),
    radial-gradient(circle at 1px 1px, rgba(43, 36, 29, 0.03) 1px, transparent 0);
  background-size: 3px 3px, 7px 7px;
  background-position: 0 0, 2px 3px;
}

button, input { font-family: inherit; }

:focus-visible {
  outline: 2px solid var(--color-stamp);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

.app-layout { margin: 0 auto; padding: 48px clamp(24px, 5vw, 96px) 80px; max-width: 1400px; }

.main-header { margin-bottom: 4px; }

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  margin-bottom: 28px;
}

.header-titles h1 {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 600;
  margin: 0 0 4px 0;
  letter-spacing: -0.3px;
  color: var(--color-stamp);
}

.header-titles p {
  font-family: var(--font-hand);
  font-size: 20px;
  font-weight: 500;
  color: var(--color-ink-soft);
  margin: 0;
}

.upload-fab {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 46px;
  padding: 0 20px;
  border-radius: var(--radius-sm);
  background: var(--color-stamp);
  color: #fbf3ea;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease, background-color 0.15s ease;
}
.upload-fab:hover { background: var(--color-stamp-hover); transform: rotate(-2deg) translateY(-1px); }

.filters {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--color-line);
  margin: 28px 0 28px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.filters::-webkit-scrollbar { display: none; }
.filter-tab {
  padding: 10px 2px;
  margin-right: 20px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--color-ink-soft);
  font-size: 13.5px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  text-decoration: none;
  transition: color 0.15s ease;
}
.filter-tab:hover { color: var(--color-ink); }
.filter-tab.active {
  color: var(--color-stamp);
  text-decoration: underline;
  text-decoration-style: wavy;
  text-decoration-thickness: 1.5px;
  text-underline-offset: 7px;
}

.content-area { min-height: 240px; }

.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 22px 18px;
}

.skeleton-card {
  height: 208px;
  border-radius: var(--radius-card);
  background: linear-gradient(100deg, var(--color-card) 30%, var(--color-page) 50%, var(--color-card) 70%);
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border: 1px solid var(--color-line);
}
@keyframes shimmer { to { background-position: -200% 0; } }

.state-message {
  font-family: var(--font-hand);
  font-size: 21px;
  font-weight: 500;
  color: var(--color-ink-soft);
  text-align: center;
  padding: 64px 24px;
}
.state-message--error {
  font-family: var(--font-ui);
  font-size: 15px;
  font-weight: 400;
  color: var(--color-status-error);
}

@media (max-width: 640px) {
  .app-layout { padding: 32px 16px 56px; }
  .header-top { flex-direction: column; align-items: stretch; }
  .upload-fab { justify-content: center; }
  .header-titles h1 { font-size: 30px; }
  .filters { margin: 22px 0 22px; }
}

@media (min-width: 641px) and (max-width: 1023px) {
  .app-layout { padding: 44px 32px 72px; }
}
</style>