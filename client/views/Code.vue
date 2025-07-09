<template>
  <div class="w-full mx-auto flex flex-col overflow-visible h-full">
    <Loading ref="loadingIndicator" class="flex-1 overflow-visible">
      <div class="flex flex-col h-full">
        <!-- Monaco Editor Container -->
        <div class="flex-1 editor-container">
          <div ref="monacoContainer" class="w-full h-screen"></div>
        </div>

        <!-- File Information Display -->
        <div class="text-xs text-gray-500 flex flex-col gap-1 p-1 file-info">
          <div class="flex flex-row justify-between">
            <div class="flex flex-col">
              <span>File: {{ filename }}</span>
              <span v-if="fileSize">Size: {{ formatFileSize(fileSize) }}</span>
            </div>
            <div class="flex flex-col items-end">
              <span v-if="lastModified">Modified: {{ formatDate(lastModified) }}</span>
            </div>
          </div>
        </div>
      </div>
    </Loading>
  </div>
</template>

<style>
/* Main container styling */
.w-full.mx-auto.flex.h-full.flex-col {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 100%;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
}

/* Editor container styling */
.editor-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: visible;
}

/* File info styling */
.file-info {
  max-width: var(--layout-width-note);
  width: 100%;
  margin-left: auto;
  margin-right: auto;
}
</style>

<script setup>
import { FileX, AlertTriangle } from "lucide-vue-next";
import { computed, onMounted, onUnmounted, ref, nextTick } from "vue";
import { useRouter } from "vue-router";
import { useRoute } from "vue-router";

import { apiErrorHandler } from "../api.js";
import Loading from "../components/Loading.vue";

const props = defineProps({
  filename: String,
});

const route = useRoute();
const router = useRouter();
const loadingIndicator = ref();
const monacoContainer = ref();

// State management
const editorState = ref({
  editor: null,
  fileContent: "",
  fileSize: 0,
  lastModified: null,
  isBinary: false,
  language: "plaintext"
});

// Computed properties
const filename = computed(() => props.filename);
const fileContent = computed(() => editorState.value.fileContent);
const fileSize = computed(() => editorState.value.fileSize);
const lastModified = computed(() => editorState.value.lastModified);
const isBinary = computed(() => editorState.value.isBinary);
const language = computed(() => editorState.value.language);

// Utility functions
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(timestamp) {
  return new Date(timestamp).toLocaleString();
}

function detectLanguage(filename) {
  const ext = filename.split('.').pop().toLowerCase();
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
    'c': 'c',
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
}

function isTextFile(content) {
  // Check if content contains null bytes or other binary indicators
  if (content.includes('\0')) {
    return false;
  }
  
  // Check if content is mostly printable ASCII/UTF-8 characters
  const printableChars = content.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '').length;
  const totalChars = content.length;
  const printableRatio = printableChars / totalChars;
  
  return printableRatio > 0.95;
}

async function loadFile() {
  if (!filename.value) {
    loadingIndicator.value.setFailed("No filename provided");
    return;
  }

  loadingIndicator.value.setLoading();

  try {
    // Fetch file content
    const response = await fetch(`/files/${encodeURIComponent(filename.value)}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        loadingIndicator.value.setFailed("File not found", FileX);
      } else {
        loadingIndicator.value.setFailed(`Failed to load file: ${response.statusText}`);
      }
      return;
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
    if (!isTextFile(textContent)) {
      updateEditorState({
        isBinary: true,
        fileSize: uint8Array.length,
        lastModified: lastModifiedHeader ? new Date(lastModifiedHeader).getTime() : null
      });
      loadingIndicator.value.setFailed("Binary file - cannot display as text", AlertTriangle);
      return;
    }

    // Update state
    updateEditorState({
      fileContent: textContent,
      fileSize: uint8Array.length,
      lastModified: lastModifiedHeader ? new Date(lastModifiedHeader).getTime() : null,
      isBinary: false,
      language: detectLanguage(filename.value)
    });

    // Set loaded first to ensure DOM is available
    loadingIndicator.value.setLoaded();
    
    // Wait for DOM update and initialize Monaco Editor
    await nextTick();
    await initializeMonacoEditor();

  } catch (error) {
    console.error('Failed to load file:', error);
    loadingIndicator.value.setFailed("Failed to load file");
    apiErrorHandler(error);
  }
}

async function initializeMonacoEditor() {
  console.log('Initializing Monaco Editor...');
  console.log('monacoContainer.value:', monacoContainer.value);
  
  if (!monacoContainer.value) {
    console.error('Monaco container not found');
    return;
  }

  try {
    // Import Monaco Editor dynamically
    const monaco = await import('monaco-editor');
    
    // Dispose existing editor if any
    if (editorState.value.editor) {
      editorState.value.editor.dispose();
    }

    // Create new editor
    const editor = monaco.editor.create(monacoContainer.value, {
      value: fileContent.value,
      language: language.value,
      theme: 'vs-dark',
      readOnly: true,
      automaticLayout: true,
      minimap: {
        enabled: true
      },
      scrollBeyondLastLine: false,
      fontSize: 14,
      lineNumbers: 'on',
      wordWrap: 'on',
      folding: true,
      lineDecorationsWidth: 10,
      lineNumbersMinChars: 3,
      renderLineHighlight: 'all',
      selectOnLineNumbers: true,
      roundedSelection: false,
      scrollbar: {
        vertical: 'visible',
        horizontal: 'visible',
        verticalScrollbarSize: 17,
        horizontalScrollbarSize: 17,
        useShadows: false
      }
    });

    // Store editor reference
    updateEditorState({ editor });
    
    console.log('Monaco Editor initialized successfully');

    // Handle window resize
    const handleResize = () => {
      editor.layout();
    };
    window.addEventListener('resize', handleResize);

    // Cleanup function
    const cleanup = () => {
      window.removeEventListener('resize', handleResize);
      if (editor) {
        editor.dispose();
      }
    };

    // Store cleanup function
    editorState.value.cleanup = cleanup;

  } catch (error) {
    console.error('Failed to initialize Monaco Editor:', error);
    loadingIndicator.value.setFailed("Failed to initialize editor");
  }
}

function updateEditorState(updates) {
  Object.assign(editorState.value, updates);
}

onMounted(async () => {
  await loadFile();
});

onUnmounted(() => {
  // Cleanup Monaco Editor
  if (editorState.value.cleanup) {
    editorState.value.cleanup();
  }
});
</script> 