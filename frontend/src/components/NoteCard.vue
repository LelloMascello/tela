<script setup>
import { computed } from 'vue';

const props = defineProps({ note: { type: Object, required: true } });
defineEmits(['open-detail']);

const statusLabels = {
  completato: 'Indicizzato',
  in_elaborazione: 'In elaborazione',
  errore: 'Errore',
};

const statusText = computed(() => {
  const raw = props.note.status;
  if (!raw) return 'Indicizzato';
  return statusLabels[raw] || raw.replace(/_/g, ' ');
});

const statusClass = computed(() => {
  const raw = props.note.status || 'completato';
  if (raw === 'in_elaborazione') return 'pending';
  if (raw === 'errore') return 'error';
  return 'done';
});

// Ogni estensione viene ricondotta a una delle categorie usate anche dai
// filtri in App.vue: colore e forma dell'icona bastano a riconoscere il
// tipo di file a colpo d'occhio, senza doverci scrivere sopra l'estensione.
const typeLabels = {
  pdf: 'PDF',
  doc: 'Documento',
  image: 'Immagine',
  sheet: 'Foglio di calcolo',
  slide: 'Presentazione',
  audio: 'Audio',
  video: 'Video',
  generic: 'File',
};
const extensionTypeMap = {
  pdf: 'pdf',
  docx: 'doc', txt: 'doc',
  jpg: 'image', jpeg: 'image', png: 'image', webp: 'image',
  xlsx: 'sheet',
  pptx: 'slide',
  mp3: 'audio', wav: 'audio',
  mp4: 'video', avi: 'video',
};
const typeKey = computed(() => extensionTypeMap[(props.note.extension || '').toLowerCase()] || 'generic');
const typeLabel = computed(() => typeLabels[typeKey.value]);

const formattedDate = computed(() => {
  if (!props.note.created_at) return null;
  const date = new Date(props.note.created_at);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short', year: 'numeric' });
});
</script>

<template>
  <li
    class="note-row"
    role="button"
    tabindex="0"
    @click="$emit('open-detail', note.id)"
    @keydown.enter="$emit('open-detail', note.id)"
    @keydown.space.prevent="$emit('open-detail', note.id)"
  >
    <span class="type-badge" :class="'type-' + typeKey" role="img" :aria-label="typeLabel">
      <svg v-if="typeKey === 'doc'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <rect x="5" y="3" width="14" height="18" rx="2" />
        <line x1="8" y1="8" x2="16" y2="8" />
        <line x1="8" y1="12" x2="16" y2="12" />
        <line x1="8" y1="16" x2="13" y2="16" />
      </svg>
      <svg v-else-if="typeKey === 'pdf'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 3h8l4 4v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
        <path d="M14 3v4h4" />
        <line x1="8" y1="14" x2="15" y2="14" />
        <line x1="8" y1="17" x2="13" y2="17" />
      </svg>
      <svg v-else-if="typeKey === 'image'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="16" height="16" rx="2.5" />
        <circle cx="9" cy="9.5" r="1.6" />
        <path d="M4.5 16.5l4.5-5 3.5 4 4-5 4.5 5.5" />
      </svg>
      <svg v-else-if="typeKey === 'sheet'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="16" height="16" rx="2" />
        <line x1="4" y1="9.3" x2="20" y2="9.3" />
        <line x1="4" y1="14.6" x2="20" y2="14.6" />
        <line x1="9.3" y1="4" x2="9.3" y2="20" />
        <line x1="14.6" y1="4" x2="14.6" y2="20" />
      </svg>
      <svg v-else-if="typeKey === 'slide'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="5" width="18" height="12" rx="2" />
        <polygon points="10,9 10,13.5 14.5,11.25" />
        <line x1="8" y1="20" x2="16" y2="20" />
      </svg>
      <svg v-else-if="typeKey === 'audio'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="6" y1="9" x2="6" y2="15" />
        <line x1="10" y1="5" x2="10" y2="19" />
        <line x1="14" y1="7" x2="14" y2="17" />
        <line x1="18" y1="10" x2="18" y2="14" />
      </svg>
      <svg v-else-if="typeKey === 'video'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <polygon points="10,9 10,15 15.5,12" />
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 3h8l4 4v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
        <path d="M14 3v4h4" />
      </svg>
    </span>

    <h4 class="row-title" :title="note.title || note.filename">{{ note.title || note.filename || 'Documento senza nome' }}</h4>

    <span class="status-pill" :class="statusClass"><i class="dot"></i>{{ statusText }}</span>
    <span class="row-date">{{ formattedDate || '—' }}</span>
  </li>
</template>

<style scoped>
/* Le colonne qui sotto devono restare identiche a .list-header in App.vue,
   così l'intestazione si allinea con ogni riga. */
.note-row {
  display: grid;
  grid-template-columns: 36px 1fr 150px 100px;
  grid-template-areas: "icon title status date";
  align-items: center;
  gap: 16px;
  padding: 13px 6px;
  border-bottom: 1px solid var(--line);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background-color 0.12s ease;
}
.note-row:hover,
.note-row:focus-visible {
  background: var(--surface);
}

.type-badge {
  grid-area: icon;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.type-badge svg { width: 16px; height: 16px; }
.type-badge.type-doc { background: var(--type-doc); color: #fff; }
.type-badge.type-pdf { background: var(--type-pdf); color: #fff; }
.type-badge.type-image { background: var(--type-image); color: #fff; }
.type-badge.type-sheet { background: var(--type-sheet); color: #fff; }
.type-badge.type-slide { background: var(--type-slide); color: #fff; }
.type-badge.type-audio { background: var(--type-audio); color: #fff; }
.type-badge.type-video { background: var(--type-video); color: #fff; }
.type-badge.type-generic { background: var(--type-generic); color: #fff; }

.row-title {
  grid-area: title;
  margin: 0;
  min-width: 0;
  font-size: 14.5px;
  font-weight: 500;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-pill {
  grid-area: status;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  justify-self: start;
  padding: 4px 10px 4px 8px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 500;
  white-space: nowrap;
}
.status-pill .dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.status-pill.done { background: var(--status-done-wash); color: var(--status-done); }
.status-pill.done .dot { background: var(--status-done); }
.status-pill.pending { background: var(--status-pending-wash); color: var(--status-pending); }
.status-pill.pending .dot { background: var(--status-pending); }
.status-pill.error { background: var(--status-error-wash); color: var(--status-error); }
.status-pill.error .dot { background: var(--status-error); }

.row-date {
  grid-area: date;
  font-family: var(--font-mono);
  font-size: 12.5px;
  color: var(--ink-faint);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 720px) {
  .note-row {
    grid-template-columns: 32px 1fr auto;
    grid-template-areas:
      "icon title title"
      "icon status date";
    row-gap: 6px;
    column-gap: 10px;
    padding: 14px 6px;
  }
  .row-date { justify-self: start; }
}
</style>