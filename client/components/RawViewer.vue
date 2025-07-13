<template>
  <div class="w-full h-full relative">
    <div
      ref="editorContainer"
      class="w-full h-full"
      style="min-width: 100px; min-height: 100px;"
    ></div>
  </div>
</template>

<style scoped>
/* Ensure the viewer container takes full height */
.w-full.h-full {
  min-height: 0;
  height: 100%;
}

/* CodeMirror custom styles */
:deep(.cm-editor) {
  height: 100%;
  font-family: "Noto Sans Mono", "Consolas", "Lucida Console", Monaco, "Andale Mono", monospace;
  font-size: 14px;
  line-height: 1.5;
}

:deep(.cm-editor .cm-scroller) {
  font-family: inherit;
}

:deep(.cm-editor .cm-content) {
  padding: 1rem;
  white-space: pre-wrap;
  word-wrap: break-word;
}

:deep(.cm-editor .cm-line) {
  padding: 0;
}

:deep(.cm-editor .cm-gutters) {
  background-color: var(--color-bg-subtle);
  border-right: 1px solid var(--color-border-primary);
  color: var(--color-text-secondary);
}

:deep(.cm-editor .cm-lineNumbers) {
  color: var(--color-text-secondary);
}

:deep(.cm-editor .cm-activeLineGutter) {
  background-color: var(--color-bg-subtle);
}

:deep(.cm-editor .cm-selectionBackground) {
  background-color: var(--color-primary-light);
}

:deep(.cm-editor .cm-cursor) {
  border-left-color: var(--color-text-primary);
}

:deep(.cm-editor .cm-tooltip) {
  background-color: var(--color-bg-base);
  border: 1px solid var(--color-border-primary);
  color: var(--color-text-primary);
}

:deep(.cm-editor .cm-tooltip.cm-tooltip-autocomplete) {
  background-color: var(--color-bg-base);
  border: 1px solid var(--color-border-primary);
}

:deep(.cm-editor .cm-tooltip.cm-tooltip-autocomplete ul) {
  background-color: var(--color-bg-base);
}

:deep(.cm-editor .cm-tooltip.cm-tooltip-autocomplete li) {
  color: var(--color-text-primary);
}

:deep(.cm-editor .cm-tooltip.cm-tooltip-autocomplete li[aria-selected]) {
  background-color: var(--color-primary-light);
  color: var(--color-text-primary);
}
</style>

<script setup>
import { onMounted, onUnmounted, ref, nextTick, watch } from "vue";
import { EditorView, basicSetup } from "codemirror";
import { EditorState } from "@codemirror/state";
import { javascript } from "@codemirror/lang-javascript";
import { python } from "@codemirror/lang-python";
import { cpp } from "@codemirror/lang-cpp";
import { java } from "@codemirror/lang-java";
import { html } from "@codemirror/lang-html";
import { css } from "@codemirror/lang-css";
import { json } from "@codemirror/lang-json";
import { xml } from "@codemirror/lang-xml";
import { yaml } from "@codemirror/lang-yaml";
import { markdown } from "@codemirror/lang-markdown";

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

const editorContainer = ref();
const editor = ref(null);
const isInitialized = ref(false);

// Utility functions moved from Raw.vue
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

// Language mapping for CodeMirror - representative languages only
const languageMap = {
  'javascript': javascript(),
  'typescript': javascript({ typescript: true }),
  'jsx': javascript({ jsx: true }),
  'tsx': javascript({ typescript: true, jsx: true }),
  'python': python(),
  'cpp': cpp(),
  'c': cpp(),
  'java': java(),
  'html': html(),
  'css': css(),
  'scss': css(),
  'sass': css(),
  'less': css(),
  'json': json(),
  'xml': xml(),
  'yaml': yaml(),
  'yml': yaml(),
  'markdown': markdown(),
  'md': markdown(),
  'plaintext': null
};

// Get language support for CodeMirror
function getLanguageSupport(language) {
  return languageMap[language] || null;
}

// Initialize CodeMirror editor
async function initializeEditor() {
  // Don't initialize if already done or no container
  if (isInitialized.value || !editorContainer.value) {
    return;
  }
  
  // Don't initialize if no content
  if (!props.fileContent) {
    return;
  }
  
  // Check container dimensions
  const rect = editorContainer.value.getBoundingClientRect();
  
  if (rect.width === 0 || rect.height === 0) {
    // Wait for next frame and try again
    requestAnimationFrame(() => {
      if (!isInitialized.value) {
        initializeEditor();
      }
    });
    return;
  }
  
  // Add a small delay to ensure all CodeMirror modules are properly initialized
  await new Promise(resolve => setTimeout(resolve, 50));
  
  try {
    // Get language support
    const languageSupport = getLanguageSupport(props.language);
    // Create extensions array, filter out null
    const extensions = [
      basicSetup,
      EditorView.theme({
        "&": {
          height: "100%"
        },
        ".cm-scroller": {
          fontFamily: "Noto Sans Mono, Consolas, Lucida Console, Monaco, Andale Mono, monospace"
        },
        ".cm-content": {
          padding: "0.5rem !important",
          whiteSpace: "pre-wrap",
          wordWrap: "break-word",
          backgroundColor: "var(--color-bg-base)"
        },
        ".cm-line": {
          padding: "0"
        },
        ".cm-gutters": {
          backgroundColor: "var(--color-bg-neutral) !important",
          borderRight: "1px solid var(--color-bg-base) !important",
          color: "var(--color-text-muted) !important"
        },
        ".cm-activeLine": {
          backgroundColor: "var(--color-primary-light) !important"
        },
        ".cm-activeLineGutter": {
          backgroundColor: "var(--color-primary) !important",
          color: "var(--color-text-inverse) !important"
        },
        ".cm-cursor": {
          borderLeftColor: "var(--color-text-primary)"
        }
      }),
      EditorView.updateListener.of((update) => {
        // Handle content changes if needed
      })
    ];
    if (languageSupport) {
      extensions.push(languageSupport);
    }
    // Create editor state
    const state = EditorState.create({
      doc: props.fileContent,
      extensions
    });
    
    // Create editor view
    const newEditor = new EditorView({
      state,
      parent: editorContainer.value
    });
    
    editor.value = newEditor;
    isInitialized.value = true;
    
    emit('editor-ready', newEditor);
    
  } catch (error) {
    console.error('Failed to initialize CodeMirror editor:', error);
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
      const transaction = editor.value.state.update({
        changes: {
          from: 0,
          to: editor.value.state.doc.length,
          insert: newContent
        }
      });
      editor.value.dispatch(transaction);
    } catch (error) {
      console.error('Failed to update editor content:', error);
    }
  }
});

// Watch for language changes
watch(() => props.language, async (newLanguage) => {
  if (isInitialized.value && editor.value) {
    try {
      const languageSupport = getLanguageSupport(newLanguage);
      const extensions = [
        basicSetup,
        EditorView.theme({
          "&": {
            height: "100%"
          },
          ".cm-scroller": {
            fontFamily: "Noto Sans Mono, Consolas, Lucida Console, Monaco, Andale Mono, monospace"
          },
          ".cm-content": {
            padding: "1rem",
            whiteSpace: "pre-wrap",
            wordWrap: "break-word"
          },
          ".cm-line": {
            padding: "0"
          },
          ".cm-gutters": {
            backgroundColor: "var(--color-bg-subtle)",
            borderRight: "1px solid var(--color-border-primary)",
            color: "var(--color-text-secondary)"
          },
          ".cm-lineNumbers": {
            color: "var(--color-text-secondary)"
          },
          ".cm-activeLineGutter": {
            backgroundColor: "var(--color-bg-subtle)"
          },
          ".cm-selectionBackground": {
            backgroundColor: "var(--color-primary-light)"
          },
          ".cm-cursor": {
            borderLeftColor: "var(--color-text-primary)"
          }
        }),
        EditorView.updateListener.of((update) => {
          // Handle content changes if needed
        })
      ];
      if (languageSupport) {
        extensions.push(languageSupport);
      }
      // Recreate editor with new language support
      const newState = EditorState.create({
        doc: editor.value.state.doc,
        extensions
      });
      editor.value.setState(newState);
    } catch (error) {
      console.error('Failed to update editor language:', error);
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
  // Destroy editor
  if (editor.value) {
    try {
      editor.value.destroy();
    } catch (error) {
      console.error('Failed to destroy editor:', error);
    } finally {
      editor.value = null;
    }
  }
  
  // Reset state
  isInitialized.value = false;
});

// Expose utility functions for parent component
defineExpose({
  formatFileSize,
  formatDate,
  detectLanguage,
  isTextFile
});
</script> 