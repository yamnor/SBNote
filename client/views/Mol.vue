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
      
      <div class="flex items-center gap-4">
        <!-- Raw button -->
        <button
          @click="setViewMode('raw')"
          class="flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--theme-button)] hover:bg-[var(--theme-brand)] hover:text-white text-theme-text transition-colors shadow-sm"
          :class="viewMode === 'raw' ? '!bg-[var(--theme-brand)] !text-white' : ''"
          :title="viewMode === 'raw' ? 'Current view' : 'Raw View'"
        >
          <Grip class="w-4 h-4" />
        </button>
        
        <!-- Mol button -->
        <button
          @click="setViewMode('mol')"
          class="flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--theme-button)] hover:bg-[var(--theme-brand)] hover:text-white text-theme-text transition-colors shadow-sm"
          :class="viewMode === 'mol' ? '!bg-[var(--theme-brand)] !text-white' : ''"
          :title="viewMode === 'mol' ? 'Current view' : 'Mol View'"
        >
          <Eye class="w-4 h-4" />
        </button>
        
        <!-- Chem button -->
        <button
          @click="setViewMode('chem')"
          class="flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--theme-button)] hover:bg-[var(--theme-brand)] hover:text-white text-theme-text transition-colors shadow-sm"
          :class="viewMode === 'chem' ? '!bg-[var(--theme-brand)] !text-white' : ''"
          :title="viewMode === 'chem' ? 'Current view' : 'Chem View'"
        >
          <SquareTerminal class="w-4 h-4" />
        </button>
      </div>
    </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="h-screen flex items-center justify-center p-8">
      <div class="text-center">
        <FileX class="w-16 h-16 mx-auto text-theme-text-muted mb-4" />
        <h2 class="text-xl font-semibold text-theme-text mb-2">Failed to load data</h2>
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
        <p class="text-sm text-theme-text-muted">Loading data...</p>
      </div>
    </div>

    <!-- Content -->
    <div v-else class="h-screen">
      <!-- MolViewer component -->
      <div v-if="viewMode === 'mol'" class="h-full pt-14">
        <MolViewer 
          :attachment-filename="attachmentFilename"
          :note-title="noteTitle"
          :file-content="fileContent"
        />
      </div>
      
      <!-- MiewViewer component -->
      <div v-else-if="viewMode === 'chem'" class="h-full pt-14">
        <MiewViewer 
          :attachment-filename="attachmentFilename"
          :note-title="noteTitle"
          :file-content="fileContent"
        />
      </div>
      
      <!-- RawViewer component -->
      <div v-else-if="viewMode === 'raw'" class="h-full pt-14">
        <RawViewer
          :file-content="fileContent"
          :language="language"
          :is-loading="false"
          @editor-ready="onEditorReady"
          @editor-error="onEditorError"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { FileText as FileTextIcon, Eye, Grip, FileX, Loader2, RefreshCw, ScanEye, SquareTerminal } from 'lucide-vue-next';
import { useNoteAttachment } from '../composables/useNoteAttachment.js';
import MolViewer from '../components/MolViewer.vue';
import MiewViewer from '../components/MiewViewer.vue';
import RawViewer from '../components/RawViewer.vue';

const props = defineProps({
  filename: String,
});

const router = useRouter();

// State
const attachmentFilename = ref(null);
const fileContent = ref('');
const viewMode = ref('mol'); // Default to mol view
const isLoading = ref(false);
const error = ref(null);

// Use composable for note data and attachment handling
const { noteData, loadNoteDataAndAttachment } = useNoteAttachment();

// Computed
const noteTitle = computed(() => {
  return noteData.value?.title || 'Molecular Structure';
});

const language = computed(() => {
  if (!attachmentFilename.value) return 'plaintext';
  const ext = attachmentFilename.value.split('.').pop().toLowerCase();
  const languageMap = {
    'xyz': 'plaintext',
    'pdb': 'plaintext',
    'mol': 'plaintext',
    'sdf': 'plaintext'
  };
  return languageMap[ext] || 'plaintext';
});

// Methods
function goToNote() {
  // Navigate to the note view using basename without extension
  const basename = props.filename.replace(/\.md$/, '');
  router.push({ name: 'note', params: { filename: basename } });
}

function setViewMode(mode) {
  viewMode.value = mode;
}

async function loadFileContent() {
  if (!attachmentFilename.value) return;
  
  try {
    const response = await fetch(`/files/${encodeURIComponent(attachmentFilename.value)}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch file: ${response.statusText}`);
    }
    fileContent.value = await response.text();
  } catch (err) {
    console.error('Failed to load file content:', err);
    error.value = `Failed to load file content: ${err.message}`;
  }
}

async function loadNoteData() {
  try {
    isLoading.value = true;
    error.value = null;
    
    // Use composable to load note data and get attachment filename
    const { attachmentFilename: filename } = await loadNoteDataAndAttachment(props.filename);
    attachmentFilename.value = filename;
    
    // Load file content
    await loadFileContent();
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

function onEditorReady(editor) {
  // Editor is ready
}

function onEditorError(error) {
  // Handle editor-specific errors if needed
  console.error('Editor error:', error);
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