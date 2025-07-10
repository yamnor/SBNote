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
      <!-- RawViewer component -->
      <div class="h-full pt-14">
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
import { FileText as FileTextIcon, FileX, Loader2, RefreshCw } from 'lucide-vue-next';
import { useNoteAttachment } from '../composables/useNoteAttachment.js';
import RawViewer from '../components/RawViewer.vue';

const props = defineProps({
  filename: String,
});

const router = useRouter();

// State
const attachmentFilename = ref(null);
const fileContent = ref('');
const isLoading = ref(false);
const error = ref(null);

// Use composable for note data and attachment handling
const { noteData, loadNoteDataAndAttachment } = useNoteAttachment();

// Computed
const noteTitle = computed(() => {
  return noteData.value?.title || 'Raw File';
});

const language = computed(() => {
  if (!attachmentFilename.value) return 'plaintext';
  const ext = attachmentFilename.value.split('.').pop().toLowerCase();
  const languageMap = {
    'js': 'javascript',
    'ts': 'typescript',
    'jsx': 'javascript',
    'tsx': 'typescript',
    'html': 'html',
    'htm': 'html',
    'css': 'css',
    'scss': 'scss',
    'sass': 'sass',
    'less': 'less',
    'json': 'json',
    'xml': 'xml',
    'yaml': 'yaml',
    'yml': 'yaml',
    'py': 'python',
    'rb': 'ruby',
    'php': 'php',
    'java': 'java',
    'c': 'cpp',
    'cpp': 'cpp',
    'cc': 'cpp',
    'cxx': 'cpp',
    'h': 'cpp',
    'hpp': 'cpp',
    'cs': 'csharp',
    'go': 'go',
    'rs': 'rust',
    'swift': 'swift',
    'kt': 'kotlin',
    'scala': 'scala',
    'sql': 'sql',
    'sh': 'shell',
    'bash': 'shell',
    'zsh': 'shell',
    'fish': 'shell',
    'ps1': 'powershell',
    'md': 'markdown',
    'txt': 'plaintext',
    'log': 'plaintext',
    'ini': 'ini',
    'conf': 'ini',
    'toml': 'toml',
    'lock': 'json'
  };
  return languageMap[ext] || 'plaintext';
});

// Methods
function goToNote() {
  // Navigate to the note view using basename without extension
  const basename = props.filename.replace(/\.md$/, '');
  router.push({ name: 'note', params: { filename: basename } });
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