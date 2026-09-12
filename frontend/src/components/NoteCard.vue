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
  position: relative;
  background: var(--color-card);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-card);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-card);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

/* Each card sits at a slightly different angle, like photos scattered
   across a desk rather than tiles snapped to a grid. */
.note-card:nth-child(6n+1) { transform: rotate(-1.4deg); }
.note-card:nth-child(6n+2) { transform: rotate(1deg); }
.note-card:nth-child(6n+3) { transform: rotate(-0.6deg); }
.note-card:nth-child(6n+4) { transform: rotate(1.6deg); }
.note-card:nth-child(6n+5) { transform: rotate(-1deg); }
.note-card:nth-child(6n) { transform: rotate(0.8deg); }

/* A strip of washi tape holding each note down, alternating colour and
   placement so the board doesn't repeat every card. */
.note-card::before {
  content: '';
  position: absolute;
  top: -10px;
  width: 52px;
  height: 20px;
  opacity: 0.82;
  box-shadow: 0 2px 3px rgba(43, 36, 29, 0.18);
  z-index: 1;
}
.note-card:nth-child(3n+1)::before { left: 22px; background: var(--color-tape-1); transform: rotate(-7deg); }
.note-card:nth-child(3n+2)::before { left: calc(50% - 26px); background: var(--color-tape-2); transform: rotate(5deg); }
.note-card:nth-child(3n)::before { right: 22px; left: auto; background: var(--color-tape-3); transform: rotate(8deg); }

.note-card:hover,
.note-card:focus-visible {
  transform: rotate(0deg) translateY(-4px) scale(1.015);
  box-shadow: 0 4px 4px rgba(43, 36, 29, 0.1), 0 20px 30px -16px rgba(43, 36, 29, 0.45);
  border-color: var(--color-line-strong);
}
.card-preview {
  position: relative;
  height: 132px;
  margin: 10px 10px 0;
  border-radius: var(--radius-md);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-page);
  background-image:
    repeating-linear-gradient(0deg, transparent, transparent 14px, rgba(43, 36, 29, 0.05) 14px, rgba(43, 36, 29, 0.05) 15px),
    repeating-linear-gradient(90deg, transparent, transparent 14px, rgba(43, 36, 29, 0.05) 14px, rgba(43, 36, 29, 0.05) 15px);
}
.ext-stamp {
  border: 1.5px solid var(--color-stamp);
  outline: 1px solid var(--color-stamp);
  outline-offset: 2px;
  color: var(--color-stamp);
  background: var(--color-stamp-wash);
  padding: 5px 14px;
  border-radius: var(--radius-stamp);
  font-family: var(--font-stamp);
  font-size: 11px;
  letter-spacing: 0.04em;
  transform: rotate(-4deg);
}
.card-info { padding: 16px 18px 18px; }
.card-info h4 {
  font-family: var(--font-display);
  margin: 0 0 10px;
  font-size: 15.5px;
  font-weight: 600;
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.status-row { display: flex; align-items: center; gap: 7px; }
.status-row p { font-size: 13px; color: var(--color-ink-soft); margin: 0; text-transform: capitalize; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--color-ink-soft); flex-shrink: 0; }
.status-dot.done { background: var(--color-status-done); }
.status-dot.pending { background: var(--color-status-pending); }
.status-dot.error { background: var(--color-status-error); }
.meta-date {
  font-family: var(--font-hand);
  font-size: 15px;
  font-weight: 500;
  color: var(--color-ink-soft);
  margin: 5px 0 0;
}
</style>