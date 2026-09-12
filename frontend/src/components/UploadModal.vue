<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { api } from '../api/client';

const emit = defineEmits(['close', 'uploaded']);

const fileInputRef = ref(null);
const isDragging = ref(false);
const queue = ref([]);
let nextId = 0;

const acceptTypes = '.png,.jpg,.jpeg,.webp,.pdf,.docx,.txt,.pptx,.xlsx,.mp3,.wav,.mp4,.avi';

const isUploading = computed(() => queue.value.some((item) => item.status === 'uploading'));
const hasFiles = computed(() => queue.value.length > 0);
const doneCount = computed(() => queue.value.filter((item) => item.status === 'done').length);

const statusLabels = { pending: 'In coda', uploading: 'Caricamento…', done: 'Caricato', error: 'Non riuscito' };

function addFiles(fileList) {
  const files = Array.from(fileList);
  for (const file of files) {
    queue.value.push({ id: nextId++, name: file.name, file, status: 'pending', message: '' });
  }
  processQueue();
}

async function processQueue() {
  const pending = queue.value.filter((item) => item.status === 'pending');
  for (const item of pending) {
    item.status = 'uploading';
    const formData = new FormData();
    formData.append('file', item.file);
    try {
      await api.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      item.status = 'done';
      emit('uploaded');
    } catch (error) {
      item.status = 'error';
      // Surface the backend's actual reason (e.g. "Formato non supportato")
      // instead of a generic blocking alert().
      item.message = error?.response?.data?.detail || 'Formato non supportato o errore del server.';
    }
  }
}

function handleDrop(event) {
  isDragging.value = false;
  if (event.dataTransfer?.files?.length) addFiles(event.dataTransfer.files);
}
function handleFileSelect(event) {
  if (event.target.files?.length) addFiles(event.target.files);
  // Bug fix: without resetting the input, re-selecting the same file
  // (e.g. after fixing it and retrying) would not fire another 'change' event.
  event.target.value = '';
}
function openFileDialog() {
  fileInputRef.value?.click();
}
function retry(id) {
  const item = queue.value.find((i) => i.id === id);
  if (item) {
    item.status = 'pending';
    item.message = '';
    processQueue();
  }
}
function dismiss(id) {
  queue.value = queue.value.filter((i) => i.id !== id);
}
function handleKeydown(event) {
  if (event.key === 'Escape' && !isUploading.value) emit('close');
}

onMounted(() => window.addEventListener('keydown', handleKeydown));
onUnmounted(() => window.removeEventListener('keydown', handleKeydown));
</script>

<template>
  <div class="modal-overlay" @click.self="!isUploading && $emit('close')">
    <div class="modal-content" role="dialog" aria-modal="true" aria-label="Carica nuovi documenti">
      <header>
        <h3>Carica nuovi documenti</h3>
        <button type="button" class="close-btn" :disabled="isUploading" @click="$emit('close')" aria-label="Chiudi">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </header>

      <div
        class="drop-area"
        :class="{ 'is-dragging': isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
        @click="openFileDialog"
      >
        <svg class="drop-icon" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v11"/><path d="M8 8l4-4 4 4"/><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/></svg>
        <p>Trascina qui i tuoi file o clicca per sfogliare</p>
        <p class="subtitle">Immagini, PDF, Word, PowerPoint, Excel, audio e video — anche più file insieme</p>
        <input
          ref="fileInputRef"
          type="file"
          :accept="acceptTypes"
          multiple
          class="hidden-input"
          @change="handleFileSelect"
        />
        <span class="upload-btn">Seleziona file</span>
      </div>

      <ul v-if="hasFiles" class="upload-queue">
        <li v-for="item in queue" :key="item.id" class="queue-item">
          <span class="queue-name">{{ item.name }}</span>
          <span class="queue-status" :class="item.status">
            {{ item.status === 'error' ? item.message : statusLabels[item.status] }}
          </span>
          <button v-if="item.status === 'error'" type="button" class="queue-action" @click="retry(item.id)">Riprova</button>
          <button
            v-if="item.status !== 'uploading'"
            type="button"
            class="queue-dismiss"
            @click="dismiss(item.id)"
            aria-label="Rimuovi dalla lista"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </li>
      </ul>
      <p v-if="hasFiles && !isUploading" class="queue-hint">
        {{ doneCount }} di {{ queue.length }} caricati. Puoi chiudere questa finestra quando vuoi.
      </p>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(15, 16, 14, 0.45); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px; }
.modal-content {
  background: var(--surface);
  padding: 28px;
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 500px;
  max-height: calc(100vh - 40px);
  max-height: calc(100dvh - 40px);
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--line);
}
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px; }
h3 { margin: 0; font-family: var(--font-mono); font-size: 17px; font-weight: 600; color: var(--ink); }
.close-btn { background: transparent; border: none; width: 30px; height: 30px; border-radius: 50%; cursor: pointer; color: var(--ink-faint); transition: background-color 0.15s ease, color 0.15s ease; display: flex; align-items: center; justify-content: center; }
.close-btn svg { width: 15px; height: 15px; }
.close-btn:hover:not(:disabled) { background: var(--surface-sunken); color: var(--ink); }
.close-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.drop-area {
  border: 1.5px dashed var(--line-strong);
  border-radius: var(--radius-md);
  padding: 40px 24px;
  text-align: center;
  transition: border-color 0.15s ease, background-color 0.15s ease;
  background: var(--canvas);
  cursor: pointer;
}
.drop-icon { color: var(--ink-faint); margin-bottom: 12px; transition: color 0.15s ease; }
.drop-area:hover, .drop-area.is-dragging { border-color: var(--accent); background: var(--accent-wash); }
.drop-area:hover .drop-icon, .drop-area.is-dragging .drop-icon { color: var(--accent); }
.drop-area p { margin: 0; color: var(--ink); font-size: 14.5px; }
.hidden-input { display: none; }
.upload-btn {
  display: inline-block;
  background: var(--accent);
  color: #fff;
  font-weight: 600;
  font-size: 13.5px;
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  margin-top: 16px;
  cursor: pointer;
  transition: background-color 0.15s ease;
}
.drop-area:hover .upload-btn, .drop-area.is-dragging .upload-btn { background: var(--accent-strong); }
.subtitle { font-size: 13px; color: var(--ink-soft); margin-top: 8px !important; }

.upload-queue { list-style: none; margin: 18px 0 0; padding: 0; display: flex; flex-direction: column; gap: 8px; max-height: 220px; overflow-y: auto; }
.queue-item { display: flex; align-items: center; gap: 10px; padding: 9px 10px; border: 1px solid var(--line); border-radius: var(--radius-sm); background: var(--canvas); }
.queue-name { flex: 1; min-width: 0; font-family: var(--font-mono); font-size: 12.5px; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.queue-status { font-size: 12px; font-weight: 500; flex-shrink: 0; max-width: 170px; text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.queue-status.pending, .queue-status.uploading { color: var(--status-pending); }
.queue-status.done { color: var(--status-done); }
.queue-status.error { color: var(--status-error); }
.queue-action { border: none; background: none; color: var(--accent); font-size: 12px; font-weight: 600; cursor: pointer; padding: 0; flex-shrink: 0; }
.queue-dismiss { border: none; background: none; color: var(--ink-faint); cursor: pointer; padding: 2px; flex-shrink: 0; display: flex; }
.queue-dismiss svg { width: 12px; height: 12px; }
.queue-dismiss:hover { color: var(--ink); }
.queue-hint { font-size: 13.5px; color: var(--ink-soft); text-align: center; margin: 14px 0 0; }

@media (max-width: 480px) {
  .modal-content { padding: 20px; }
  .drop-area { padding: 30px 16px; }
  .queue-item { flex-wrap: wrap; }
  .queue-name { flex-basis: 100%; }
  .queue-status { max-width: none; text-align: left; }
}

/* Telefoni in orizzontale: meno spazio verticale nella zona di trascinamento */
@media (max-height: 480px) {
  .modal-overlay { padding: 12px; align-items: flex-start; }
  .modal-content { margin-top: 12px; padding: 18px 20px; }
  .drop-area { padding: 18px 16px; }
  .drop-icon { width: 22px; height: 22px; margin-bottom: 6px; }
  .drop-area p { font-size: 13.5px; }
  .upload-queue { max-height: 140px; }
}
</style>