<template>
  <div class="fixed inset-0 z-50 bg-white dark:bg-gray-900">
    <!-- Header -->
    <div class="absolute top-0 left-0 right-0 z-10 flex items-center justify-between p-4 bg-white/90 backdrop-blur-sm">
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <FileTextIcon 
            @click="goToNote" 
            class="w-8 h-8 text-theme-muted hover:text-theme-text text-theme-text-muted transition-colors cursor-pointer"
            title="Go to note"
          />
          <h1 class="text-lg font-semibold text-theme-text-muted">
            {{ noteTitle }}
          </h1>
        </div>
      </div>
      
      <div class="flex items-center space-x-8">
        <!-- Loading indicator -->
        <div v-if="isLoading" class="flex items-center space-x-2 text-theme-text-muted">
          <Loader2 class="w-4 h-4 animate-spin" />
          <span class="text-sm">Loading molecule...</span>
        </div>
        
        <!-- Raw button -->
        <button
          @click="goToRawView"
          class="flex items-center justify-center w-8 h-8 text-theme-muted hover:text-theme-text text-theme-text-muted transition-colors"
          title="Raw View"
        >
          <Grip class="w-8 h-8" />
        </button>
        
        <!-- Mol button (current view) -->
        <button
          class="flex items-center justify-center w-8 h-8 text-theme-brand text-theme-text transition-colors"
          title="Current view"
        >
          <Eye class="w-8 h-8" />
        </button>
        

      </div>
    </div>

    <!-- MolViewer component -->
    <div class="h-screen">
      <MolViewer 
        :attachment-filename="attachmentFilename"
        @error="handleViewerError"
        @loading="handleViewerLoading"
        @loaded="handleViewerLoaded"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ArrowLeft, FileX, Loader2, RefreshCw, Info, FileText, Eye, Grip, FileText as FileTextIcon } from 'lucide-vue-next';
import { useNoteAttachment } from '../composables/useNoteAttachment.js';
import MolViewer from '../components/MolViewer.vue';

const props = defineProps({
  filename: String,
});

const router = useRouter();
const route = useRoute();

// State
const attachmentFilename = ref(null);
const isLoading = ref(false);
const error = ref(null);

// Use composable for note data and attachment handling
const { noteData, loadNoteDataAndAttachment } = useNoteAttachment();

// Computed
const noteTitle = computed(() => {
  return noteData.value?.title || 'Molecular Structure';
});

// Methods
function goBack() {
  if (window.history.length > 1) {
    router.back();
  } else {
    router.push({ name: 'home' });
  }
}

function goToNote() {
  // Navigate to the note view using basename without extension
  const basename = props.filename.replace(/\.md$/, '');
  router.push({ name: 'note', params: { filename: basename } });
}

function goToRawView() {
  // Navigate to the raw view using basename
  router.push({ name: 'raw', params: { filename: props.filename } });
}

async function loadNoteData() {
  try {
    // Use composable to load note data and get attachment filename
    const { attachmentFilename: filename } = await loadNoteDataAndAttachment(props.filename);
    attachmentFilename.value = filename;
  } catch (err) {
    console.error('Failed to load note data:', err);
    error.value = err.message || 'Failed to load molecule data';
  }
}

// MolViewer event handlers
function handleViewerError(errorMessage) {
  error.value = errorMessage;
}

function handleViewerLoading(loading) {
  isLoading.value = loading;
}

function handleViewerLoaded() {
  // Molecule loaded successfully
  console.log('Molecule loaded successfully');
}

// Lifecycle
onMounted(async () => {
  await loadNoteData();
});

// Watch for note data changes to update browser title
watch(noteData, (newNoteData) => {
  if (newNoteData?.title) {
    document.title = `${newNoteData.title} - SBNote`;
  } else {
    document.title = "Molecule - SBNote";
  }
}, { immediate: true });
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