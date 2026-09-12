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
  <div class="search-field">
    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
    <input
      type="text"
      v-model="searchQuery"
      @input="handleInput"
      placeholder="Cerca per titolo o contenuto del documento…"
      aria-label="Cerca nei documenti"
    />
    <button v-if="searchQuery" type="button" class="clear-btn" @click="clearSearch" aria-label="Cancella ricerca">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
    </button>
  </div>
</template>

<style scoped>
.search-field {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}
.search-icon {
  position: absolute;
  left: 14px;
  width: 17px;
  height: 17px;
  color: var(--ink-faint);
  pointer-events: none;
}
.search-field input {
  width: 100%;
  padding: 12px 40px 12px 42px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--line);
  background-color: var(--surface);
  font-size: 14.5px;
  color: var(--ink);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  outline: none;
}
.search-field input:hover { border-color: var(--line-strong); }
.search-field input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-wash);
}
.search-field input::placeholder { color: var(--ink-faint); }
.clear-btn {
  position: absolute;
  right: 10px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--ink-faint);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.clear-btn svg { width: 13px; height: 13px; }
.clear-btn:hover { background: var(--surface-sunken); color: var(--ink); }
</style>