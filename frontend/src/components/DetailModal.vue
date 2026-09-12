<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { api } from '../api/client';

const props = defineProps({ noteId: { type: String, required: true } });
const emit = defineEmits(['close', 'deleted', 'updated']);

const note = ref(null);
const isLoading = ref(true);
const loadError = ref(null);
const activeView = ref('document');
const isDeleting = ref(false);
const deleteError = ref(null);
const mediaError = ref(false);

// Il testo estratto è editabile direttamente nella vista "Testo": niente più
// pulsante "Modifica" separato. Le modifiche si salvano da sole poco dopo che
// si smette di scrivere (o subito, se se ne sono inserite/tolte molte), e in
// ogni caso quando la finestra viene chiusa.
const editedText = ref('');
const lastSavedText = ref('');
const isSavingText = ref(false);
const saveTextError = ref(null);
const AUTOSAVE_DELAY_MS = 2000;
const AUTOSAVE_RETRY_MS = 5000;
const AUTOSAVE_CHAR_THRESHOLD = 400;
let autosaveTimer = null;
let inFlightSave = null;

const imageExtensions = ['jpg', 'jpeg', 'png', 'webp'];
const audioExtensions = ['mp3', 'wav'];
const videoExtensions = ['mp4', 'avi'];

// Bug fix: the download link was hardcoded to http://localhost:8000, which
// only works when the frontend and backend are opened on the same machine.
// Reusing the api client's own base URL means it also works over the LAN
// (e.g. from a phone hitting the Raspberry Pi's address).
const fileUrl = computed(() => `${api.defaults?.baseURL ?? ''}/notes/${props.noteId}/file`);
// Il titolo è generato automaticamente dal backend dal testo estratto; finché
// non è disponibile (o per note più vecchie) ripieghiamo sul filename.
const displayTitle = computed(() => note.value?.title || note.value?.filename || '');
const extension = computed(() => (note.value?.extension || '').toLowerCase());
const isImage = computed(() => imageExtensions.includes(extension.value));
const isPdf = computed(() => extension.value === 'pdf');
const isAudio = computed(() => audioExtensions.includes(extension.value));
const isVideo = computed(() => videoExtensions.includes(extension.value));
const isAvMedia = computed(() => isAudio.value || isVideo.value);

// pptx, xlsx (and anything else without a native browser preview) fall back
// to the "no-preview" state further down; audio/video get a real player but
// can still fail (codec support varies, e.g. some .avi files), hence mediaError.
const documentTabLabel = computed(() => (isAvMedia.value ? 'Player' : 'Documento'));
const textTabLabel = computed(() => (isAvMedia.value ? 'Trascrizione' : 'Testo'));

const noPreviewMessage = computed(() => {
  if (mediaError.value) {
    return isAudio.value
      ? 'Il browser non riesce a riprodurre questo file audio. Scaricalo per ascoltarlo.'
      : 'Il browser non riesce a riprodurre questo video. Scaricalo per guardarlo.';
  }
  return "L'anteprima non è disponibile per questo formato.";
});

const textPlaceholder = computed(() => (
  isAvMedia.value
    ? 'Nessuna trascrizione disponibile. Scrivi qui per aggiungerne una…'
    : 'Nessun testo estratto. Scrivi o correggi qui il testo del documento…'
));

const hasUnsavedTextEdits = computed(() => editedText.value !== lastSavedText.value);

async function loadNote() {
  isLoading.value = true;
  loadError.value = null;
  mediaError.value = false;
  try {
    const response = await api.get(`/notes/${props.noteId}`);
    note.value = response.data;
    editedText.value = note.value?.extracted_text || '';
    lastSavedText.value = editedText.value;
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
    `Eliminare definitivamente "${displayTitle.value}"? L'operazione non è reversibile.`
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

// Chiamata a ogni tocco di tasto: rimanda il salvataggio finché l'utente sta
// ancora scrivendo, ma lo anticipa se ha già cambiato molti caratteri, così
// non si rischia di perdere una modifica lunga in caso di problemi.
function queueAutosave() {
  saveTextError.value = null;
  clearTimeout(autosaveTimer);
  const changedChars = Math.abs(editedText.value.length - lastSavedText.value.length);
  autosaveTimer = setTimeout(saveText, changedChars >= AUTOSAVE_CHAR_THRESHOLD ? 0 : AUTOSAVE_DELAY_MS);
}

function saveText() {
  clearTimeout(autosaveTimer);
  if (inFlightSave) return inFlightSave;
  if (!hasUnsavedTextEdits.value) return Promise.resolve();

  const textToSave = editedText.value;
  isSavingText.value = true;
  saveTextError.value = null;

  inFlightSave = (async () => {
    try {
      const response = await api.patch(`/notes/${props.noteId}`, { extracted_text: textToSave });
      // Il backend ritorna la nota aggiornata, titolo ricalcolato incluso.
      note.value = response.data;
      lastSavedText.value = textToSave;
      emit('updated', note.value);
    } catch (error) {
      console.error('Errore nel salvataggio della trascrizione', error);
      saveTextError.value = 'Non riesco a salvare le modifiche. Riprova tra poco.';
    } finally {
      isSavingText.value = false;
      inFlightSave = null;
      // Se nel frattempo sono arrivate altre modifiche (o il salvataggio è
      // fallito), ne pianifichiamo un altro invece di lasciarle in sospeso.
      if (editedText.value !== lastSavedText.value) {
        autosaveTimer = setTimeout(saveText, saveTextError.value ? AUTOSAVE_RETRY_MS : AUTOSAVE_DELAY_MS);
      }
    }
  })();

  return inFlightSave;
}

// Se si lascia la scheda "Testo" senza chiudere la finestra, salviamo
// comunque subito quello che è stato scritto.
watch(activeView, (_next, previous) => {
  if (previous === 'text') saveText();
});

async function requestClose() {
  clearTimeout(autosaveTimer);
  await saveText();
  if (hasUnsavedTextEdits.value) await saveText();
  emit('close');
}

function handleKeydown(event) {
  if (event.key === 'Escape') requestClose();
}

onMounted(() => {
  loadNote();
  window.addEventListener('keydown', handleKeydown);
});
onUnmounted(() => {
  clearTimeout(autosaveTimer);
  window.removeEventListener('keydown', handleKeydown);
});
</script>

<template>
  <div class="modal-overlay" @click.self="requestClose">
    <div class="modal-content detail-modal" role="dialog" aria-modal="true" :aria-label="displayTitle || 'Dettaglio documento'">
      <div v-if="isLoading" class="modal-state">
        <div class="spinner"></div>
      </div>

      <div v-else-if="loadError" class="modal-state">
        <p>{{ loadError }}</p>
        <button type="button" class="btn-secondary" @click="requestClose">Chiudi</button>
      </div>

      <template v-else-if="note">
        <header>
          <h3>{{ displayTitle }}</h3>
          <div class="actions">
            <div class="view-toggle">
              <button type="button" :class="{ active: activeView === 'document' }" @click="activeView = 'document'">{{ documentTabLabel }}</button>
              <button type="button" :class="{ active: activeView === 'text' }" @click="activeView = 'text'">{{ textTabLabel }}</button>
            </div>
            <a :href="fileUrl" :download="note.filename" class="btn-secondary">Scarica</a>
            <button type="button" class="btn-danger" :disabled="isDeleting" @click="handleDelete">
              {{ isDeleting ? 'Eliminazione…' : 'Elimina' }}
            </button>
            <button type="button" class="close-btn" @click="requestClose" aria-label="Chiudi">✕</button>
          </div>
        </header>

        <p v-if="deleteError" class="delete-error">{{ deleteError }}</p>

        <div class="content-split">
          <div v-if="activeView === 'text'" class="extracted-text">
            <textarea
              v-model="editedText"
              class="edit-textarea"
              :placeholder="textPlaceholder"
              @input="queueAutosave"
            ></textarea>
            <span
              v-if="isSavingText || hasUnsavedTextEdits || saveTextError"
              class="save-status"
              :class="{ 'is-error': saveTextError }"
            >
              {{ saveTextError || (isSavingText ? 'Salvataggio…' : 'Modifiche in sospeso…') }}
            </span>
          </div>

          <div v-else class="preview-area">
            <img v-if="isImage" :src="fileUrl" :alt="note.filename" class="preview-image" />
            <iframe v-else-if="isPdf" :src="fileUrl" class="preview-pdf" title="Anteprima documento"></iframe>
            <audio
              v-else-if="isAudio && !mediaError"
              :src="fileUrl"
              controls
              class="preview-audio"
              @error="mediaError = true"
            ></audio>
            <video
              v-else-if="isVideo && !mediaError"
              :src="fileUrl"
              controls
              class="preview-video"
              @error="mediaError = true"
            ></video>
            <div v-else class="no-preview">
              <span class="no-preview-badge">{{ extension.toUpperCase() || 'FILE' }}</span>
              <p>{{ noPreviewMessage }}</p>
              <a :href="fileUrl" :download="note.filename" class="btn-secondary">Scarica per visualizzarlo</a>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(30, 24, 18, 0.5); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 24px; }
.detail-modal {
  width: 100%;
  max-width: 1080px;
  height: 85vh;
  display: flex;
  flex-direction: column;
  background: var(--color-card-raised);
  padding: 26px 30px;
  border-radius: var(--radius-modal);
  box-shadow: var(--shadow-modal);
  border: 1px solid var(--color-line);
}
.modal-state { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; color: var(--color-ink-soft); }
.spinner { width: 28px; height: 28px; border-radius: 50%; border: 3px solid var(--color-line); border-top-color: var(--color-stamp); animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
header { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding-bottom: 18px; flex-wrap: wrap; border-bottom: 1px dashed var(--color-line); }
h3 { margin: 0; font-family: var(--font-display); font-size: 22px; color: var(--color-ink); font-weight: 600; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; flex-shrink: 0; }
.view-toggle { display: flex; background: var(--color-page); border-radius: var(--radius-sm); padding: 3px; }
.view-toggle button { font-family: var(--font-stamp); border: none; background: transparent; padding: 7px 14px; font-size: 12px; color: var(--color-ink-soft); border-radius: 4px; cursor: pointer; transition: background-color 0.15s ease, color 0.15s ease; }
.view-toggle button.active { background: var(--color-card-raised); color: var(--color-stamp); box-shadow: 0 1px 2px rgba(43, 36, 29, 0.12); }
.btn-secondary { background: var(--color-card-raised); color: var(--color-ink); font-weight: 500; font-size: 13.5px; padding: 9px 18px; border: 1px solid var(--color-line); border-radius: var(--radius-sm); cursor: pointer; text-decoration: none; transition: border-color 0.15s ease, background-color 0.15s ease; display: inline-flex; align-items: center; }
.btn-secondary:hover { background: var(--color-page); border-color: var(--color-line-strong); }
.btn-secondary:disabled { opacity: 0.6; cursor: not-allowed; }
.close-btn { background: var(--color-page); border: none; width: 34px; height: 34px; border-radius: 50%; font-size: 14px; cursor: pointer; color: var(--color-ink-soft); transition: background-color 0.15s ease; display: flex; align-items: center; justify-content: center; }
.close-btn:hover { background: var(--color-line); color: var(--color-ink); }
.btn-danger { background: var(--color-card-raised); color: #a33a2f; font-weight: 500; font-size: 13.5px; padding: 9px 18px; border: 1px solid #d9b3a8; border-radius: var(--radius-sm); cursor: pointer; transition: border-color 0.15s ease, background-color 0.15s ease; }
.btn-danger:hover:not(:disabled) { background: #f7e6e1; border-color: #a33a2f; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }
.delete-error { margin: 0 0 14px; padding: 10px 14px; background: #f7e6e1; color: #a33a2f; border-radius: var(--radius-sm); font-size: 13px; }
.content-split { flex: 1; display: flex; margin-top: 4px; background: var(--color-page); border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--color-line); }
.preview-area { width: 100%; display: flex; align-items: center; justify-content: center; overflow: auto; }
.preview-image { max-width: 100%; max-height: 100%; object-fit: contain; }
.preview-pdf { width: 100%; height: 100%; border: none; }
.preview-audio { width: 88%; max-width: 460px; }
.preview-video { max-width: 100%; max-height: 100%; background: #000; border-radius: var(--radius-sm); }
.no-preview { display: flex; flex-direction: column; align-items: center; gap: 10px; color: var(--color-ink-soft); padding: 40px; text-align: center; }
.no-preview-badge { font-family: var(--font-stamp); font-size: 12px; color: var(--color-stamp); border: 1.5px solid var(--color-stamp); outline: 1px solid var(--color-stamp); outline-offset: 2px; background: var(--color-stamp-wash); padding: 5px 14px; border-radius: var(--radius-stamp); transform: rotate(-3deg); }
.extracted-text {
  position: relative;
  width: 100%;
  display: flex;
}
.edit-textarea {
  width: 100%;
  height: 100%;
  min-height: 240px;
  resize: none;
  border: none;
  background-color: var(--color-card-raised);
  color: var(--color-ink);
  font-family: var(--font-mono);
  font-size: 13.5px;
  line-height: 1.7;
  padding: 28px 32px;
}
.edit-textarea::placeholder { color: var(--color-ink-soft); font-family: var(--font-hand); font-size: 17px; }
.edit-textarea:focus-visible { outline: 2px solid var(--color-stamp); outline-offset: -2px; }
.save-status {
  position: absolute;
  right: 16px;
  bottom: 16px;
  font-family: var(--font-hand);
  font-size: 16px;
  font-weight: 500;
  color: var(--color-ink-soft);
  background: var(--color-stamp-wash);
  padding: 3px 14px;
  border-radius: var(--radius-stamp);
  pointer-events: none;
}
.save-status.is-error { font-family: var(--font-ui); font-size: 12.5px; font-weight: 500; color: var(--color-status-error); background: #f7e6e1; }

@media (max-width: 640px) {
  .detail-modal { height: 92vh; padding: 20px; }
  h3 { font-size: 18px; }
  .actions { width: 100%; justify-content: space-between; }
}

@media (max-width: 400px) {
  .view-toggle button { padding: 7px 10px; font-size: 11.5px; }
  .btn-secondary { padding: 9px 14px; font-size: 12.5px; }
}
</style>