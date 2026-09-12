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
        <button type="button" class="close-btn" :disabled="isUploading" @click="$emit('close')" aria-label="Chiudi">✕</button>
      </header>

      <div
        class="drop-area"
        :class="{ 'is-dragging': isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
        @click="openFileDialog"
      >
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
          >✕</button>
        </li>
      </ul>
      <p v-if="hasFiles && !isUploading" class="queue-hint">
        {{ doneCount }} di {{ queue.length }} caricati. Puoi chiudere questa finestra quando vuoi.
      </p>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(30, 24, 18, 0.5); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px; }
.modal-content {
  background: var(--color-card-raised);
  padding: 30px;
  border-radius: var(--radius-modal);
  width: 100%;
  max-width: 520px;
  max-height: calc(100vh - 40px);
  max-height: calc(100dvh - 40px);
  overflow-y: auto;
  box-shadow: var(--shadow-modal);
  border: 1px solid var(--color-line);
}
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px; }
h3 { margin: 0; font-family: var(--font-display); font-size: 21px; font-weight: 600; color: var(--color-ink); }
.close-btn { background: var(--color-page); border: none; width: 32px; height: 32px; border-radius: 50%; font-size: 13px; cursor: pointer; color: var(--color-ink-soft); transition: background-color 0.15s ease; }
.close-btn:hover:not(:disabled) { background: var(--color-line); color: var(--color-ink); }
.close-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.drop-area {
  position: relative;
  border: 2px dashed var(--color-line-strong);
  border-radius: var(--radius-md);
  padding: 44px 24px;
  text-align: center;
  transition: border-color 0.15s ease, background-color 0.15s ease;
  background: var(--color-page);
  cursor: pointer;
}
.drop-area::before {
  content: '✂';
  position: absolute;
  top: -13px;
  left: 22px;
  background: var(--color-card-raised);
  color: var(--color-ink-soft);
  padding: 0 6px;
  font-size: 14px;
  transform: rotate(-8deg);
}
.drop-area:hover, .drop-area.is-dragging { border-color: var(--color-stamp); background: var(--color-stamp-wash); }
.drop-area p { margin: 0; color: var(--color-ink); font-size: 14.5px; }
.hidden-input { display: none; }
.upload-btn {
  display: inline-block;
  background: var(--color-stamp);
  color: #fbf3ea;
  font-weight: 500;
  font-size: 14px;
  padding: 11px 22px;
  border-radius: var(--radius-sm);
  margin-top: 16px;
  cursor: pointer;
  transition: background-color 0.15s ease, transform 0.15s ease;
}
.upload-btn:hover { background: var(--color-stamp-hover); transform: rotate(-1.5deg); }
.subtitle { font-size: 13px; color: var(--color-ink-soft); margin-top: 8px !important; }
.upload-queue { list-style: none; margin: 18px 0 0; padding: 0; display: flex; flex-direction: column; gap: 8px; max-height: 220px; overflow-y: auto; }
.queue-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border: 1px solid var(--color-line); border-radius: var(--radius-sm); background: var(--color-page); }
.queue-name { flex: 1; min-width: 0; font-family: var(--font-mono); font-size: 12.5px; color: var(--color-ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.queue-status { font-family: var(--font-stamp); font-size: 12px; font-weight: 400; flex-shrink: 0; max-width: 180px; text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.queue-status.pending, .queue-status.uploading { color: var(--color-status-pending); }
.queue-status.done { color: var(--color-status-done); }
.queue-status.error { color: var(--color-status-error); }
.queue-action { border: none; background: none; color: var(--color-stamp); font-size: 12px; font-weight: 600; cursor: pointer; padding: 0; flex-shrink: 0; }
.queue-dismiss { border: none; background: none; color: var(--color-ink-soft); font-size: 11px; cursor: pointer; padding: 2px; flex-shrink: 0; }
.queue-dismiss:hover { color: var(--color-ink); }
.queue-hint { font-family: var(--font-hand); font-size: 16px; color: var(--color-ink-soft); text-align: center; margin: 14px 0 0; }

@media (max-width: 480px) {
  .modal-content { padding: 22px; }
  .drop-area { padding: 32px 16px; }
  .queue-item { flex-wrap: wrap; }
  .queue-name { flex-basis: 100%; }
  .queue-status { max-width: none; text-align: left; }
}

/* Telefoni in orizzontale: meno spazio verticale nella zona di trascinamento */
@media (max-height: 480px) {
  .modal-overlay { padding: 12px; align-items: flex-start; }
  .modal-content { margin-top: 12px; padding: 18px 22px; }
  .drop-area { padding: 20px 16px; }
  .drop-area p { font-size: 13.5px; }
  .upload-queue { max-height: 140px; }
}
</style>