<template>
  <div class="w-full h-full relative">
    <div
      ref="monacoContainer"
      class="w-full h-full"
      style="min-width: 100px; min-height: 100px; display: block; visibility: visible;"
    ></div>
  </div>
</template>

<style scoped>
/* Ensure the viewer container takes full height */
.w-full.h-full {
  min-height: 0;
}
</style>

<script setup>
import { onMounted, onUnmounted, ref, nextTick, watch } from "vue";

const props = defineProps({
  fileContent: {
    type: String,
    default: ""
  },
  language: {
    type: String,
    default: "plaintext"
  },
  isLoading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['editor-ready', 'editor-error']);

const monacoContainer = ref();
const editor = ref(null);
const isInitialized = ref(false);
const cleanupTimeout = ref(null);

// Simple initialization function
async function initializeEditor() {
  // Don't initialize if already done or no container
  if (isInitialized.value || !monacoContainer.value) {
    return;
  }
  
  // Don't initialize if no content
  if (!props.fileContent) {
    return;
  }
  
  // Check container dimensions
  const rect = monacoContainer.value.getBoundingClientRect();
  
  if (rect.width === 0 || rect.height === 0) {
    // Wait for next frame and try again
    requestAnimationFrame(() => {
      if (!isInitialized.value) {
        initializeEditor();
      }
    });
    return;
  }
  
  try {
    // Import Monaco Editor
    const monaco = await import('monaco-editor');
    
    // Ensure container is visible and has proper dimensions
    monacoContainer.value.style.display = 'block';
    monacoContainer.value.style.visibility = 'visible';
    
    // Create editor with WebGL-safe settings
    const newEditor = monaco.editor.create(monacoContainer.value, {
      value: props.fileContent,
      language: props.language,
      theme: 'vs-dark',
      readOnly: true,
      automaticLayout: true,
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      fontSize: 14,
      lineNumbers: 'on',
      wordWrap: 'on',
      folding: false,
      lineDecorationsWidth: 10,
      lineNumbersMinChars: 3,
      renderLineHighlight: 'none', // Disable line highlighting to reduce WebGL usage
      selectOnLineNumbers: true,
      roundedSelection: false,
      scrollbar: {
        vertical: 'visible',
        horizontal: 'visible',
        verticalScrollbarSize: 17,
        horizontalScrollbarSize: 17,
        useShadows: false
      },
      renderWhitespace: 'none',
      renderControlCharacters: false,
      renderIndentGuides: false,
      guides: { indentation: false },
      // Additional WebGL-safe settings
      renderValidationDecorations: 'off',
      renderOverviewRuler: false,
      overviewRulerBorder: false,
      hideCursorInOverviewRuler: true,
      overviewRulerLanes: 0,
      fixedOverflowWidgets: true,
      // Memory management settings
      largeFileOptimizations: true,
      maxTokenizationLineLength: 20000,
      maxTokenizationLineNumber: 1000
    });
    
    editor.value = newEditor;
    isInitialized.value = true;
    
    // Force layout to ensure proper WebGL context initialization
    cleanupTimeout.value = setTimeout(() => {
      if (newEditor && typeof newEditor.isDisposed === 'function' && !newEditor.isDisposed()) {
        newEditor.layout();
      } else if (newEditor && typeof newEditor.layout === 'function') {
        newEditor.layout();
      }
    }, 100);
    
    emit('editor-ready', newEditor);
    
  } catch (error) {
    emit('editor-error', error);
    
    // Reset state on error
    isInitialized.value = false;
    editor.value = null;
  }
}

// Watch for content changes
watch(() => props.fileContent, (newContent) => {
  if (newContent && !isInitialized.value) {
    // Initialize if we have content but editor is not initialized
    nextTick(() => initializeEditor());
  } else if (newContent && isInitialized.value && editor.value) {
    // Update content if editor is already initialized
    try {
      if (typeof editor.value.isDisposed === 'function' && editor.value.isDisposed()) {
        return;
      }
      editor.value.setValue(newContent);
    } catch (error) {
      // Silent error handling
    }
  }
});

// Watch for language changes
watch(() => props.language, async (newLanguage) => {
  if (isInitialized.value && editor.value) {
    try {
      if (typeof editor.value.isDisposed === 'function' && editor.value.isDisposed()) {
        return;
      }
      const monaco = await import('monaco-editor');
      const model = editor.value.getModel();
      if (model) {
        monaco.editor.setModelLanguage(model, newLanguage);
      }
    } catch (error) {
      // Silent error handling
    }
  }
});

onMounted(async () => {
  await nextTick();
  
  // Initialize if content is already available
  if (props.fileContent) {
    await initializeEditor();
  }
});

onUnmounted(() => {
  // Clear any pending timeouts
  if (cleanupTimeout.value) {
    clearTimeout(cleanupTimeout.value);
    cleanupTimeout.value = null;
  }
  
  // Dispose editor with multiple safety checks
  if (editor.value) {
    try {
      // Check if editor is already disposed
      if (typeof editor.value.isDisposed === 'function' && editor.value.isDisposed()) {
        // Editor already disposed
      } else {
        // Get the model and dispose it first
        const model = editor.value.getModel();
        if (model) {
          try {
            model.dispose();
          } catch (modelError) {
            // Silent error handling
          }
        }
        
        // Dispose the editor
        editor.value.dispose();
      }
    } catch (error) {
      // Silent error handling
    } finally {
      editor.value = null;
    }
  }
  
  // Reset all state
  isInitialized.value = false;
  
  // Force garbage collection hint (optional)
  if (window.gc) {
    try {
      window.gc();
    } catch (e) {
      // Ignore if gc is not available
    }
  }
});
</script> 