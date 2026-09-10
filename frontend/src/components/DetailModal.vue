<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { api } from '../api/client';

const props = defineProps({ noteId: { type: String, required: true } });
const emit = defineEmits(['close', 'deleted']);

const note = ref(null);
const isLoading = ref(true);
const loadError = ref(null);
const activeView = ref('document');
const isDeleting = ref(false);
const deleteError = ref(null);

const imageExtensions = ['jpg', 'jpeg', 'png', 'webp'];

// Bug fix: the download link was hardcoded to http://localhost:8000, which
// only works when the frontend and backend are opened on the same machine.
// Reusing the api client's own base URL means it also works over the LAN
// (e.g. from a phone hitting the Raspberry Pi's address).
const fileUrl = computed(() => `${api.defaults?.baseURL ?? ''}/notes/${props.noteId}/file`);
const extension = computed(() => (note.value?.extension || '').toLowerCase());
const isImage = computed(() => imageExtensions.includes(extension.value));
const isPdf = computed(() => extension.value === 'pdf');

async function loadNote() {
  isLoading.value = true;
  loadError.value = null;
  try {
    const response = await api.get(`/notes/${props.noteId}`);
    note.value = response.data;
  } catch (error) {
    console.error('Errore nel recupero della nota', error);
    loadError.value = 'Non riesco a trovare questo documento.';
  } finally {
    isLoading.value = false;
  }
}

async function handleDelete() {
  if (isDeleting.value) return;

  const confirmed = window.confirm(
    `Eliminare definitivamente "${note.value?.filename}"? L'operazione non è reversibile.`
  );
  if (!confirmed) return;

  isDeleting.value = true;
  deleteError.value = null;
  try {
    await api.delete(`/notes/${props.noteId}`);
    emit('deleted', props.noteId);
    emit('close');
  } catch (error) {
    console.error('Errore durante l\'eliminazione della nota', error);
    deleteError.value = 'Non riesco a eliminare questo documento. Riprova.';
  } finally {
    isDeleting.value = false;
  }
}

function handleKeydown(event) {
  if (event.key === 'Escape') emit('close');
}

onMounted(() => {
  loadNote();
  window.addEventListener('keydown', handleKeydown);
});
onUnmounted(() => window.removeEventListener('keydown', handleKeydown));
</script>

<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content detail-modal" role="dialog" aria-modal="true" :aria-label="note?.filename || 'Dettaglio documento'">
      <div v-if="isLoading" class="modal-state">
        <div class="spinner"></div>
      </div>

      <div v-else-if="loadError" class="modal-state">
        <p>{{ loadError }}</p>
        <button type="button" class="btn-secondary" @click="$emit('close')">Chiudi</button>
      </div>

      <template v-else-if="note">
        <header>
          <h3>{{ note.filename }}</h3>
          <div class="actions">
            <div class="view-toggle">
              <button type="button" :class="{ active: activeView === 'document' }" @click="activeView = 'document'">Documento</button>
              <button type="button" :class="{ active: activeView === 'text' }" @click="activeView = 'text'">Testo</button>
            </div>
            <a :href="fileUrl" :download="note.filename" class="btn-secondary">Scarica</a>
            <button type="button" class="btn-danger" :disabled="isDeleting" @click="handleDelete">
              {{ isDeleting ? 'Eliminazione…' : 'Elimina' }}
            </button>
            <button type="button" class="close-btn" @click="$emit('close')" aria-label="Chiudi">✕</button>
          </div>
        </header>

        <p v-if="deleteError" class="delete-error">{{ deleteError }}</p>

        <div class="content-split">
          <div v-if="activeView === 'text'" class="extracted-text">
            <p v-if="note.extracted_text">{{ note.extracted_text }}</p>
            <p v-else class="empty-note">Nessun testo estratto per questo documento.</p>
          </div>

          <div v-else class="preview-area">
            <img v-if="isImage" :src="fileUrl" :alt="note.filename" class="preview-image" />
            <iframe v-else-if="isPdf" :src="fileUrl" class="preview-pdf" title="Anteprima documento"></iframe>
            <div v-else class="no-preview">
              <span class="no-preview-badge">{{ extension.toUpperCase() || 'FILE' }}</span>
              <p>L'anteprima non è disponibile per questo formato.</p>
              <a :href="fileUrl" :download="note.filename" class="btn-secondary">Scarica per visualizzarlo</a>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(20, 26, 22, 0.45); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 24px; }
.detail-modal { width: 100%; max-width: 1080px; height: 85vh; display: flex; flex-direction: column; background: var(--color-surface-raised); padding: 26px 30px; border-radius: var(--radius-lg); box-shadow: var(--shadow-modal); }
.modal-state { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; color: var(--color-ink-muted); }
.spinner { width: 28px; height: 28px; border-radius: 50%; border: 3px solid var(--color-border); border-top-color: var(--color-accent); animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
header { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding-bottom: 18px; flex-wrap: wrap; }
h3 { margin: 0; font-family: var(--font-display); font-size: 22px; color: var(--color-ink); font-weight: 600; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; flex-shrink: 0; }
.view-toggle { display: flex; background: var(--color-canvas); border-radius: var(--radius-sm); padding: 3px; }
.view-toggle button { border: none; background: transparent; padding: 7px 14px; font-size: 13px; font-weight: 500; color: var(--color-ink-muted); border-radius: 6px; cursor: pointer; transition: background-color 0.15s ease, color 0.15s ease; }
.view-toggle button.active { background: var(--color-surface-raised); color: var(--color-ink); box-shadow: 0 1px 2px rgba(30, 39, 35, 0.08); }
.btn-secondary { background: var(--color-surface-raised); color: var(--color-ink); font-weight: 500; font-size: 13.5px; padding: 9px 18px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); cursor: pointer; text-decoration: none; transition: border-color 0.15s ease, background-color 0.15s ease; display: inline-flex; align-items: center; }
.btn-secondary:hover { background: var(--color-canvas); border-color: var(--color-border-strong); }
.close-btn { background: var(--color-canvas); border: none; width: 34px; height: 34px; border-radius: 50%; font-size: 14px; cursor: pointer; color: var(--color-ink-muted); transition: background-color 0.15s ease; display: flex; align-items: center; justify-content: center; }
.close-btn:hover { background: var(--color-border); color: var(--color-ink); }
.btn-danger { background: var(--color-surface-raised); color: #c0392b; font-weight: 500; font-size: 13.5px; padding: 9px 18px; border: 1px solid #e3b0aa; border-radius: var(--radius-sm); cursor: pointer; transition: border-color 0.15s ease, background-color 0.15s ease; }
.btn-danger:hover:not(:disabled) { background: #fdecea; border-color: #c0392b; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }
.delete-error { margin: 0 0 14px; padding: 10px 14px; background: #fdecea; color: #c0392b; border-radius: var(--radius-sm); font-size: 13px; }
.content-split { flex: 1; display: flex; margin-top: 4px; background: var(--color-canvas); border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--color-border); }
.preview-area { width: 100%; display: flex; align-items: center; justify-content: center; overflow: auto; }
.preview-image { max-width: 100%; max-height: 100%; object-fit: contain; }
.preview-pdf { width: 100%; height: 100%; border: none; }
.no-preview { display: flex; flex-direction: column; align-items: center; gap: 10px; color: var(--color-ink-muted); padding: 40px; text-align: center; }
.no-preview-badge { font-family: var(--font-mono); font-size: 12px; font-weight: 600; color: var(--color-accent); border: 1.5px solid var(--color-accent); background: var(--color-accent-soft); padding: 5px 14px; border-radius: 4px; }
.extracted-text { width: 100%; padding: 28px 32px; overflow-y: auto; }
.extracted-text p { text-align: left; font-family: var(--font-mono); font-size: 13.5px; line-height: 1.7; color: var(--color-ink); white-space: pre-wrap; margin: 0; }
.empty-note { font-family: var(--font-ui) !important; color: var(--color-ink-muted) !important; }

@media (max-width: 640px) {
  .detail-modal { height: 92vh; padding: 20px; }
  h3 { font-size: 18px; }
  .actions { width: 100%; justify-content: space-between; }
}

@media (max-width: 400px) {
  .view-toggle button { padding: 7px 10px; font-size: 12.5px; }
  .btn-secondary { padding: 9px 14px; font-size: 12.5px; }
}
</style>