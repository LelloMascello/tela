<script setup>
import { ref, onBeforeUnmount } from 'vue';

const searchQuery = ref('');
const emit = defineEmits(['search']);
let debounceTimer = null;

// Bug fix: previously every keystroke fired a request once the query hit
// 2 characters, which sends far more traffic than needed while typing.
const handleInput = () => {
  clearTimeout(debounceTimer);
  const value = searchQuery.value;
  if (value.length === 0) {
    emit('search', '');
    return;
  }
  if (value.length < 2) return;
  debounceTimer = setTimeout(() => emit('search', value), 300);
};

const clearSearch = () => {
  searchQuery.value = '';
  clearTimeout(debounceTimer);
  emit('search', '');
};

onBeforeUnmount(() => clearTimeout(debounceTimer));
</script>

<template>
  <div class="search-container">
    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
    <input
      type="text"
      v-model="searchQuery"
      @input="handleInput"
      placeholder="Cerca tra testo, documenti e testo estratto..."
      aria-label="Cerca nei documenti"
    />
    <button v-if="searchQuery" type="button" class="clear-btn" @click="clearSearch" aria-label="Cancella ricerca">✕</button>
  </div>
</template>

<style scoped>
.search-container { position: relative; display: flex; align-items: center; width: 100%; }
.search-icon {
  position: absolute;
  left: 16px;
  width: 18px;
  height: 18px;
  color: var(--color-ink-muted);
  pointer-events: none;
}
.search-container input {
  width: 100%;
  padding: 14px 40px 14px 46px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface-raised);
  font-size: 14.5px;
  color: var(--color-ink);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  outline: none;
}
.search-container input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-soft);
}
.search-container input::placeholder { color: var(--color-ink-muted); }
.clear-btn {
  position: absolute;
  right: 12px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: none;
  background: var(--color-canvas);
  color: var(--color-ink-muted);
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.clear-btn:hover { background: var(--color-border); color: var(--color-ink); }
</style>