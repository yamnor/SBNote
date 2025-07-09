<template>
  <div class="fixed inset-0 z-50 bg-white dark:bg-gray-900">
    <!-- Header -->
    <div class="absolute top-0 left-0 right-0 z-10 flex items-center justify-between p-4 bg-theme-background backdrop-blur-sm">
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
          <span class="text-sm">Loading file...</span>
        </div>
        
        <!-- Raw button (current view) -->
        <button
          class="flex items-center justify-center w-8 h-8 text-theme-brand text-theme-text transition-colors"
          title="Current view"
        >
          <Grip class="w-8 h-8" />
        </button>
        
        <!-- Mol button -->
        <button
          @click="goToMolView"
          class="flex items-center justify-center w-8 h-8 text-theme-muted hover:text-theme-text text-theme-text-muted transition-colors"
          title="Mol View"
        >
          <Eye class="w-8 h-8" />
        </button>
        

      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="h-screen flex items-center justify-center p-8">
      <div class="text-center">
        <FileX class="w-16 h-16 mx-auto text-theme-text-muted mb-4" />
        <h2 class="text-xl font-semibold text-theme-text mb-2">Failed to load file</h2>
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

    <!-- CodeMirror Editor container -->
    <div v-else class="h-screen relative pt-16" style="min-height: 400px;">
      <RawViewer
        ref="rawViewerRef"
        :file-content="fileContent"
        :language="language"
        :is-loading="isLoading"
        @editor-ready="onEditorReady"
        @editor-error="onEditorError"
      />
      
      <!-- Loading overlay -->
      <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-gray-900/50">
        <div class="text-center">
          <Loader2 class="w-8 h-8 mx-auto text-theme-brand animate-spin mb-2" />
          <p class="text-sm text-theme-text-muted">Loading file content...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Ensure the viewer container takes full height */
.w-full.h-full {
  min-height: 0;
}

/* Ensure full screen coverage */
.fixed.inset-0 {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
</style>

<script setup>
import { FileX, AlertTriangle, Loader2, RefreshCw, FileText, Eye, Info, Grip, FileText as FileTextIcon } from "lucide-vue-next";
import { computed, onMounted, onUnmounted, ref, nextTick, watch } from "vue";
import { useRouter } from "vue-router";
import { useRoute } from "vue-router";

import { apiErrorHandler } from "../api.js";
import { useNoteAttachment } from "../composables/useNoteAttachment.js";
import RawViewer from "../components/RawViewer.vue";

const props = defineProps({
  filename: String,
});

const route = useRoute();
const router = useRouter();

// State management
const editorState = ref({
  fileContent: "",
  fileSize: 0,
  lastModified: null,
  isBinary: false,
  language: "plaintext"
});

// Use composable for note data and attachment handling
const { noteData, isLoading, error, loadNoteDataAndAttachment } = useNoteAttachment();

// Computed properties
const filename = computed(() => props.filename);
const fileContent = computed(() => editorState.value.fileContent);
const fileSize = computed(() => editorState.value.fileSize);
const lastModified = computed(() => editorState.value.lastModified);
const isBinary = computed(() => editorState.value.isBinary);
const language = computed(() => editorState.value.language);

// Computed title
const noteTitle = computed(() => {
  return noteData.value?.title || filename.value;
});

// Reference to RawViewer component for utility functions
const rawViewerRef = ref();

async function loadFile() {
  if (!filename.value) {
    error.value = "No filename provided";
    isLoading.value = false;
    return;
  }

  try {
    // Use composable to load note data and get attachment filename
    const { attachmentFilename } = await loadNoteDataAndAttachment(filename.value);

    // Fetch file content
    const response = await fetch(`/files/${encodeURIComponent(attachmentFilename)}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("File not found");
      } else {
        throw new Error(`Failed to load file: ${response.statusText}`);
      }
    }

    // Get file metadata
    const contentLength = response.headers.get('content-length');
    const lastModifiedHeader = response.headers.get('last-modified');
    
    // Read file content
    const arrayBuffer = await response.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);
    
    // Try to decode as text
    let textContent;
    try {
      textContent = new TextDecoder('utf-8').decode(uint8Array);
    } catch (error) {
      // If UTF-8 fails, try other encodings
      try {
        textContent = new TextDecoder('latin1').decode(uint8Array);
      } catch (error2) {
        textContent = new TextDecoder('utf-8', { fatal: false }).decode(uint8Array);
      }
    }

    // Check if it's a binary file
    if (!rawViewerRef.value?.isTextFile(textContent)) {
      updateEditorState({
        isBinary: true,
        fileSize: uint8Array.length,
        lastModified: lastModifiedHeader ? new Date(lastModifiedHeader).getTime() : null
      });
      throw new Error("Binary file - cannot display as text");
    }

    // Update state
    updateEditorState({
      fileContent: textContent,
      fileSize: uint8Array.length,
      lastModified: lastModifiedHeader ? new Date(lastModifiedHeader).getTime() : null,
      isBinary: false,
      language: rawViewerRef.value?.detectLanguage(attachmentFilename) || 'plaintext'
    });

    // Wait for DOM update
    await nextTick();

  } catch (err) {
    console.error('Failed to load file:', err);
    error.value = err.message || "Failed to load file";
    apiErrorHandler(err);
  } finally {
    isLoading.value = false;
  }
}



function retryLoad() {
  loadFile();
}

function onEditorReady(editor) {
  // Editor is ready
}

function onEditorError(error) {
  // Handle editor-specific errors if needed
}



function goToMolView() {
  // Navigate to the mol view using basename
  router.push({ name: 'mol', params: { filename: props.filename } });
}

function goToNote() {
  // Navigate to the note view using basename
  router.push({ name: 'note', params: { filename: props.filename } });
}



function updateEditorState(updates) {
  Object.assign(editorState.value, updates);
}

onMounted(async () => {
  await loadFile();
});

// Watch for note data changes to update browser title
watch(noteData, (newNoteData) => {
  if (newNoteData?.title) {
    document.title = `${newNoteData.title} - SBNote`;
  } else {
    document.title = "Raw - SBNote";
  }
}, { immediate: true });

onUnmounted(() => {
  // Clear any pending operations
  if (editorState.value) {
    // Reset editor state
    editorState.value = {
      fileContent: "",
      fileSize: 0,
      lastModified: null,
      isBinary: false,
      language: "plaintext"
    };
  }
});
</script> 