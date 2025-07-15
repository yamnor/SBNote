<template>
  <div class="note-content-width">
    <!-- Header with toggle -->
    <div class="flex items-center justify-between p-1 border-b border-color-bg-base cursor-pointer hover:bg-color-bg-base transition-colors" @click="toggleInfoSection">
      <Info class="w-4 h-4 text-color-text-secondary" />
      <ChevronDown v-if="isInfoExpanded" class="w-4 h-4 text-color-text-secondary" />
      <ChevronRight v-else class="w-4 h-4 text-color-text-secondary" />
    </div>
    
    <!-- Collapsible content -->
    <div v-show="isInfoExpanded" class="text-xs text-color-text-secondary flex flex-col gap-1 p-1">
      <div class="flex flex-row justify-between">
        <div class="flex flex-col">
          <span v-if="note.category">Category: {{ note.category }}</span>
          <span v-if="note.visibility">Visibility: {{ note.visibility }}</span>
        </div>
        <div class="flex flex-col items-end">
          <span v-if="note.lastModifiedAsString">Modified: {{ note.lastModifiedAsString }}</span>
          <span v-if="note.createdTimeAsString">Created: {{ note.createdTimeAsString }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Info, ChevronDown, ChevronRight } from 'lucide-vue-next';

const props = defineProps({
  note: {
    type: Object,
    required: true
  }
});

const isInfoExpanded = ref(false);

// Toggle info section and save to localStorage
function toggleInfoSection() {
  const newExpandedState = !isInfoExpanded.value;
  isInfoExpanded.value = newExpandedState;
  localStorage.setItem('noteInfoExpanded', newExpandedState.toString());
}

// Load info section state from localStorage
function loadInfoSectionState() {
  const savedState = localStorage.getItem('noteInfoExpanded');
  if (savedState !== null) {
    isInfoExpanded.value = savedState === 'true';
  }
}

onMounted(() => {
  loadInfoSectionState();
});
</script>

<style scoped>
.note-content-width {
  max-width: var(--layout-width-note);
  width: 100%;
  margin-left: auto;
  margin-right: auto;
}
</style> 