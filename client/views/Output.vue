<template>
  <div class="fixed inset-0 z-modal bg-color-background">
    <!-- Header -->
    <div class="absolute top-0 left-0 right-0 z-navigation flex items-center justify-center">
      <div class="flex items-center justify-between gap-4 py-4 h-14 bg-color-background backdrop-blur-sm w-full max-w-[var(--layout-width-note)]">
      <button
        @click="goBack" 
        class="flex items-center justify-center w-10 h-10 rounded-lg bg-color-surface hover:bg-color-primary hover:text-color-on-primary text-color-text-light transition-colors cursor-pointer flex-shrink-0"
        title="Go back"
      >
        <ArrowLeft class="w-6 h-6" />
      </button>
      
      <h1 class="text-sm text-color-text-light truncate min-w-0 flex-1">
        {{ noteTitle }}
      </h1>
      
      <div class="flex items-center gap-4">
        <!-- Output button -->
        <button
          @click="setViewMode('output')"
          class="flex items-center justify-center w-9 h-9 rounded-lg bg-color-surface hover:bg-color-primary hover:text-color-on-primary text-color-text-light transition-colors shadow-sm"
          :class="viewMode === 'output' ? '!bg-color-primary !text-color-on-primary' : ''"
          :title="viewMode === 'output' ? 'Current view' : 'Output View'"
        >
          <Scroll class="w-6 h-6" />
        </button>
        
        <!-- 3Dmol button -->
        <button
          @click="setViewMode('3dmol')"
          class="flex items-center justify-center w-9 h-9 rounded-lg bg-color-surface hover:bg-color-primary hover:text-color-on-primary text-color-text-light transition-colors shadow-sm"
          :class="viewMode === '3dmol' ? '!bg-color-primary !text-color-on-primary' : ''"
          :title="viewMode === '3dmol' ? 'Current view' : '3Dmol View'"
        >
          <Eye class="w-6 h-6" />
        </button>
        
        <!-- Miew button -->
        <button
          @click="setViewMode('miew')"
          class="flex items-center justify-center w-9 h-9 rounded-lg bg-color-surface hover:bg-color-primary hover:text-color-on-primary text-color-text-light transition-colors shadow-sm"
          :class="viewMode === 'miew' ? '!bg-color-primary !text-color-on-primary' : ''"
          :title="viewMode === 'miew' ? 'Current view' : 'Miew View'"
        >
          <Terminal class="w-6 h-6" />
        </button>
      </div>
    </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="h-screen flex items-center justify-center p-8">
      <div class="text-center">
        <FileX class="w-16 h-16 mx-auto text-color-text-light mb-4" />
        <h2 class="text-xl font-semibold text-color-text-base mb-2">Failed to load data</h2>
        <p class="text-color-text-light mb-4">{{ error }}</p>
        <button
          @click="retryLoad"
          class="inline-flex items-center px-4 py-2 bg-color-primary text-color-on-primary rounded-lg hover:bg-color-primary-dark transition-colors"
        >
          <RefreshCw class="w-4 h-4 mr-2" />
          Retry
        </button>
      </div>
    </div>

    <!-- Loading overlay -->
    <div v-else-if="isLoading" class="h-screen flex items-center justify-center bg-white/50 dark:bg-gray-900/50">
      <div class="text-center">
        <Loader2 class="w-8 h-8 mx-auto text-color-primary animate-spin mb-2" />
        <p class="text-sm text-color-text-light">Loading data...</p>
      </div>
    </div>

    <!-- Content -->
    <div v-else class="h-screen">
      <!-- 3DmolViewer component -->
      <div v-if="viewMode === '3dmol'" class="h-full pt-14">
        <ThreeDmolViewer 
          :attachment-filename="attachmentFilename"
          :note-title="noteTitle"
          :file-content="fileContent"
        />
      </div>
      
      <!-- MiewViewer component -->
      <div v-else-if="viewMode === 'miew'" class="h-full pt-14">
        <MiewViewer 
          :attachment-filename="attachmentFilename"
          :note-title="noteTitle"
          :file-content="fileContent"
        />
      </div>
      
      <!-- CodeMirrorEditor component -->
      <div v-else-if="viewMode === 'output'" class="h-full pt-14">
        <CodeMirrorEditor
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
import { ArrowLeft, Eye, Scroll, FileX, Loader2, RefreshCw, Terminal } from 'lucide-vue-next';
import { useNoteAttachment } from '../composables/useNoteAttachment.js';
import ThreeDmolViewer from '../components/3DmolViewer.vue';
import MiewViewer from '../components/MiewViewer.vue';
import CodeMirrorEditor from '../components/CodeMirrorEditor.vue';

const props = defineProps({
  filename: String,
});

const router = useRouter();

// State
const attachmentFilename = ref(null);
const fileContent = ref('');
const viewMode = ref('3dmol'); // Default to 3Dmol view
const isLoading = ref(false);
const error = ref(null);



// Use composable for note data and attachment handling
const { noteData, loadNoteDataAndAttachment } = useNoteAttachment();

// Computed
const noteTitle = computed(() => {
  return noteData.value?.title || 'Output File';
});

const language = computed(() => {
  if (!attachmentFilename.value) return 'output';
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
    'txt': 'output',
    'log': 'output',
    'ini': 'ini',
    'conf': 'ini',
    'toml': 'toml',
    'lock': 'json',
    'xyz': 'output'
  };
  return languageMap[ext] || 'output';
});

// Methods
function goBack() {
  // Check if there's a previous page in browser history
  if (window.history.length > 1) {
    // Check if the previous page is within the same app
    const currentOrigin = window.location.origin;
    const referrer = document.referrer;
    
    // If referrer is from the same origin, go back
    if (referrer && referrer.startsWith(currentOrigin)) {
      router.back();
    } else {
      // If referrer is from outside the app or empty, go to home
      router.push({ name: "home" });
    }
  } else {
    // If no history, go to home
    router.push({ name: "home" });
  }
}

function setViewMode(mode) {
  viewMode.value = mode;
  // Load appropriate file content when view mode changes
  loadFileContentForMode(mode);
}

// Get appropriate filename based on view mode
function getFilenameForMode(mode) {
  const basename = props.filename.replace(/\.md$/, '');
  switch (mode) {
    case '3dmol':
    case 'miew':
      return `${basename}/output.pkl`;
    case 'output':
    default:
      return `${basename}/output.txt`;
  }
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

async function loadFileContentForMode(mode) {
  const filename = getFilenameForMode(mode);
  attachmentFilename.value = filename;
  await loadFileContent();
}

async function loadNoteData() {
  try {
    isLoading.value = true;
    error.value = null;
    
    // Load note data for title
    const { noteData: note } = await loadNoteDataAndAttachment(props.filename);
    
    // Load file content for current view mode
    await loadFileContentForMode(viewMode.value);
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