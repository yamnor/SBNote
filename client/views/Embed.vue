<template>
  <div class="fixed inset-0 z-50 bg-[var(--theme-background)]">
    <!-- Header -->
    <div class="absolute top-0 left-0 right-0 z-10 flex items-center justify-center">
      <div class="flex items-center justify-between gap-4 py-4 h-14 bg-[var(--theme-background)] backdrop-blur-sm w-full max-w-[var(--layout-width-note)]">
        <button
          @click="goToNote" 
          class="flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--theme-button)] hover:bg-[var(--theme-brand)] hover:text-white text-theme-text transition-colors cursor-pointer flex-shrink-0 shadow-sm"
          title="Go to note"
        >
          <FileTextIcon class="w-4 h-4" />
        </button>
        
        <h1 class="text-sm text-theme-text-muted truncate min-w-0 flex-1">
          {{ noteTitle }}
        </h1>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="h-screen flex items-center justify-center p-8">
      <div class="text-center">
        <FileX class="w-16 h-16 mx-auto text-theme-text-muted mb-4" />
        <h2 class="text-xl font-semibold text-theme-text mb-2">Failed to load embedded content</h2>
        <p class="text-theme-text-muted mb-4">{{ error }}</p>
        <button
          @click="retryLoad"
          class="inline-flex items-center px-4 py-2 bg-theme-brand text-white rounded-lg hover:bg-theme-brand-dark transition-colors"
        >
          <RefreshCw class="w-4 h-4 mr-2" />
          Retry
        </button>
      </div>
    </div>

    <!-- Loading overlay -->
    <div v-else-if="isLoading" class="h-screen flex items-center justify-center bg-white/50 dark:bg-gray-900/50">
      <div class="text-center">
        <Loader2 class="w-8 h-8 mx-auto text-theme-brand animate-spin mb-2" />
        <p class="text-sm text-theme-text-muted">Loading embedded content...</p>
      </div>
    </div>

    <!-- Content -->
    <div v-else class="h-screen">
      <!-- EmbedViewer component -->
      <div class="h-full pt-14">
        <EmbedViewer
          :note-content="noteContent"
          @error="onEmbedError"
          @loading="onEmbedLoading"
          @loaded="onEmbedLoaded"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { FileText as FileTextIcon, FileX, Loader2, RefreshCw } from 'lucide-vue-next';
import { getNote } from '../api.js';
import EmbedViewer from '../components/EmbedViewer.vue';

const props = defineProps({
  filename: String,
});

const router = useRouter();

// State
const noteContent = ref('');
const isLoading = ref(false);
const error = ref(null);
const noteData = ref(null);

// Computed
const noteTitle = computed(() => {
  return noteData.value?.title || 'Embedded Content';
});

// Methods
function goToNote() {
  // Navigate to the note view using basename without extension
  const basename = props.filename.replace(/\.md$/, '');
  router.push({ name: 'note', params: { filename: basename } });
}

async function loadNoteData() {
  try {
    isLoading.value = true;
    error.value = null;
    
    // Get note data
    const data = await getNote(props.filename);
    noteData.value = data;
    noteContent.value = data.content || '';
    
  } catch (err) {
    console.error('Failed to load note data:', err);
    error.value = err.message || 'Failed to load note data';
  } finally {
    isLoading.value = false;
  }
}

function retryLoad() {
  loadNoteData();
}

function onEmbedError(errorMessage) {
  error.value = errorMessage;
}

function onEmbedLoading(loading) {
  // Handle loading state from EmbedViewer if needed
}

function onEmbedLoaded() {
  // Handle loaded state from EmbedViewer if needed
}

// Lifecycle
onMounted(async () => {
  await loadNoteData();
});
</script>

<style scoped>
/* Ensure full screen coverage */
.fixed.inset-0 {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
</style> 