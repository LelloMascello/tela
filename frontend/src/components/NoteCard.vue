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

const extensionLabel = computed(() => {
  const ext = props.note.extension;
  return ext ? ext.substring(0, 5).toUpperCase() : 'FILE';
});

const formattedDate = computed(() => {
  if (!props.note.created_at) return null;
  const date = new Date(props.note.created_at);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short', year: 'numeric' });
});
</script>

<template>
  <div
    class="note-card"
    role="button"
    tabindex="0"
    @click="$emit('open-detail', note.id)"
    @keydown.enter="$emit('open-detail', note.id)"
    @keydown.space.prevent="$emit('open-detail', note.id)"
  >
    <div class="card-preview">
      <span class="ext-stamp">{{ extensionLabel }}</span>
    </div>
    <div class="card-info">
      <h4 :title="note.title || note.filename">{{ note.title || note.filename || 'Documento senza nome' }}</h4>
      <div class="status-row">
        <span class="status-dot" :class="statusClass"></span>
        <p>{{ statusText }}</p>
      </div>
      <p v-if="formattedDate" class="meta-date">{{ formattedDate }}</p>
    </div>
  </div>
</template>

<style scoped>
.note-card {
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  display: flex;
  flex-direction: column;
}
.note-card:hover,
.note-card:focus-visible {
  transform: translateY(-3px);
  box-shadow: var(--shadow-card);
  border-color: var(--color-border-strong);
}
.card-preview {
  height: 132px;
  background: var(--color-canvas);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 10px 10px 0;
  border-radius: var(--radius-md);
}
.ext-stamp {
  border: 1.5px solid var(--color-accent);
  color: var(--color-accent);
  background: var(--color-accent-soft);
  padding: 5px 14px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 12px;
  letter-spacing: 0.03em;
  transform: rotate(-3deg);
}
.card-info { padding: 16px 18px 18px; }
.card-info h4 {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.status-row { display: flex; align-items: center; gap: 7px; }
.status-row p { font-size: 13px; color: var(--color-ink-muted); margin: 0; text-transform: capitalize; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--color-ink-muted); flex-shrink: 0; }
.status-dot.done { background: var(--color-status-done); }
.status-dot.pending { background: var(--color-status-pending); }
.status-dot.error { background: var(--color-status-error); }
.meta-date { font-size: 12px; color: var(--color-ink-muted); margin: 6px 0 0; opacity: 0.85; }
</style>