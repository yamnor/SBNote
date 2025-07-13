<template>
  <TransitionRoot appear :show="isVisible" as="template">
    <Dialog as="div" @close="closeModal" class="relative z-50">
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/40 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
          <TransitionChild
            as="template"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="w-full transform overflow-hidden rounded-lg bg-color-bg-neutral shadow-2xl transition-all note-preview-modal" style="max-width: var(--layout-width-note);">
              <!-- Header -->
              <div class="flex items-center justify-between p-2 pb-0">
                <!-- Left side - Slide view button and Embed button -->
                <div class="flex items-center space-x-2">
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-button-secondary-bg p-2 text-color-button-secondary-fg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg"
                    @click="openInSlide"
                    title="Open in slide view"
                  >
                    <Presentation class="w-4 h-4" />
                  </button>
                  
                  <!-- Embed button (only show for embed category) -->
                  <button
                    v-if="note.category === 'embed'"
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-button-secondary-bg p-2 text-color-button-secondary-fg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg"
                    @click="openInEmbed"
                    title="Open in embed view"
                  >
                    <ExternalLink class="w-4 h-4" />
                  </button>
                  
                  <!-- MolViewer button (only show for coordinate category) -->
                  <button
                    v-if="note.category === 'coordinate'"
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-button-secondary-bg p-2 text-color-button-secondary-fg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg"
                    @click="openInMol"
                    title="Open in molecular viewer"
                  >
                    <Atom class="w-4 h-4" />
                  </button>
                </div>
                
                <!-- Right side - Copy Link, Editor and Close buttons -->
                <div class="flex items-center space-x-2">
                  <!-- Copy Link button -->
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-button-secondary-bg p-2 text-color-button-secondary-fg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg"
                    @click="copyLink"
                    title="Copy link"
                  >
                    <Link2 class="w-4 h-4" />
                  </button>
                  
                  <!-- Open in editor button -->
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-button-secondary-bg p-2 text-color-button-secondary-fg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg"
                    @click="openInEditor"
                    title="Open in full editor"
                  >
                    <Maximize2 class="w-4 h-4" />
                  </button>
                  
                  <!-- Close button -->
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-button-secondary-bg p-2 text-color-button-secondary-fg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg"
                    @click="closeModal"
                    title="Close"
                  >
                    <X class="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              <!-- Content -->
              <div class="max-h-96 overflow-y-auto overflow-x-hidden">
                <Editor
                  ref="toastEditor"
                  :key="`editor-${note.filename}`"
                  :initialValue="editingContent"
                  :initialEditType="'markdown'"
                  :previewStyle="'tab'"
                  @change="handleEditorChange"
                />
              </div>
              
              <!-- Tags section at bottom -->
              <div class="mt-4 mb-4">
                <TagInput 
                  v-model="editingTags"
                  :readonly="false"
                  @tagConfirmed="handleTagConfirmed"
                />
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { Dialog, DialogPanel, TransitionRoot, TransitionChild } from '@headlessui/vue'
import { onMounted, ref, watch, nextTick, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { X, Maximize2, Presentation, ExternalLink, Link2, Atom } from "lucide-vue-next";
import { useGlobalStore } from "../globalStore.js";
import TagInput from "./TagInput.vue";
import Editor from "./Editor.vue";
import { updateNote } from "../api.js";

const props = defineProps({
  note: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(["close"]);
const isVisible = defineModel({ type: Boolean });
const router = useRouter();
const globalStore = useGlobalStore();

// Refs
const toastEditor = ref();

// Edit state
const editingContent = ref('');
const editingTags = ref([]);

// Auto-save state
let autoSaveTimeout = null;
let contentChangedTimeout = null;
const isAutoSaving = ref(false);

// Constants
const AUTO_SAVE_DELAY = 3000; // 3 seconds
const CONTENT_CHANGE_DELAY = 500; // 500ms

function closeModal() {
  isVisible.value = false;
  emit("close");
  cleanup();
}

function openInEditor() {
  closeModal();
  router.push({ 
    name: 'note', 
    params: { filename: props.note.filename.replace(/\.md$/, '') } 
  });
}

function openInSlide() {
  closeModal();
  router.push({ 
    name: 'slide', 
    params: { filename: props.note.filename.replace(/\.md$/, '') } 
  });
}

function openInEmbed() {
  closeModal();
  router.push({ 
    name: 'embed', 
    params: { filename: props.note.filename.replace(/\.md$/, '') } 
  });
}

function openInMol() {
  closeModal();
  router.push({ 
    name: 'mol', 
    params: { filename: props.note.filename.replace(/\.md$/, '') } 
  });
}

function copyLink() {
  const filename = props.note.filename.replace(/\.md$/, '');
  const url = `${window.location.origin}/${filename}`;
  
  navigator.clipboard.writeText(url).then(() => {
    // Could add a toast notification here if needed
    console.log('Link copied to clipboard:', url);
  }).catch(err => {
    console.error('Failed to copy link:', err);
  });
}

function initializeEditing() {
  editingContent.value = props.note.content || '';
  editingTags.value = [...(props.note.tags || [])];
}

function handleEditorChange() {
  startContentChangedTimeout();
}

function handleTagConfirmed() {
  // Force save immediately for tag changes
  if (autoSaveTimeout) {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = null;
  }
  performSave();
}

function startContentChangedTimeout() {
  clearContentChangedTimeout();
  contentChangedTimeout = setTimeout(contentChangedHandler, CONTENT_CHANGE_DELAY);
}

function clearContentChangedTimeout() {
  if (contentChangedTimeout) {
    clearTimeout(contentChangedTimeout);
    contentChangedTimeout = null;
  }
}

function contentChangedHandler() {
  if (hasChanges()) {
    startAutoSaveTimeout();
  }
}

function startAutoSaveTimeout() {
  clearAutoSaveTimeout();
  autoSaveTimeout = setTimeout(autoSaveHandler, AUTO_SAVE_DELAY);
}

function clearAutoSaveTimeout() {
  if (autoSaveTimeout) {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = null;
  }
}

function autoSaveHandler() {
  if (hasChanges()) {
    performSave();
  }
}

function hasChanges() {
  const currentContent = toastEditor.value ? toastEditor.value.getMarkdown() : editingContent.value;
  
  return (
    currentContent !== props.note.content ||
    JSON.stringify(editingTags.value) !== JSON.stringify(props.note.tags || [])
  );
}

async function performSave() {
  if (isAutoSaving.value) return;
  
  isAutoSaving.value = true;
  
  try {
    const currentContent = toastEditor.value ? toastEditor.value.getMarkdown() : editingContent.value;
    const filenameWithExtension = props.note.filename;
    
    const updatedNote = await updateNote(
      filenameWithExtension,
      props.note.title, // Use original title
      currentContent,
      editingTags.value
    );
    
    // Update the note prop (this will trigger parent component updates)
    Object.assign(props.note, updatedNote);
    
    // Update editing content to match saved content
    editingContent.value = updatedNote.content;
    
  } catch (error) {
    console.error('Failed to save note:', error);
    // Could add error handling here if needed
  } finally {
    isAutoSaving.value = false;
  }
}

function cleanup() {
  clearContentChangedTimeout();
  clearAutoSaveTimeout();
}

// Initialize editing when modal becomes visible
watch(isVisible, async (visible) => {
  if (visible && props.note.content) {
    // Wait for Vue DOM update
    await nextTick();
    
    // Initialize editing state
    initializeEditing();
  }
});

// Clean up viewer when modal closes
watch(isVisible, (visible) => {
  if (!visible) {
    cleanup();
  }
});

// Handle keyboard events
function handleKeydown(event) {
  if (event.key === 'Escape') {
    closeModal();
  }
}

// Prevent keyboard events from bubbling to parent components (like NavBar search)
function handleKeydownCapture(event) {
  // Stop propagation for all keyboard events when modal is visible
  // But allow events from input elements within the modal to work normally
  if (isVisible.value) {
    const target = event.target;
    const isInputElement = target.tagName === 'INPUT' || 
                          target.tagName === 'TEXTAREA' || 
                          target.contentEditable === 'true' ||
                          target.closest('.tag-input-container') ||
                          target.closest('.toastui-editor') ||
                          target.closest('.note-preview-modal');
    
    // Always stop propagation when modal is visible to prevent search input capture
    event.stopPropagation();
    
    // Only allow input events to continue for actual input elements
    if (!isInputElement) {
      event.preventDefault();
    }
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
  document.addEventListener('keydown', handleKeydownCapture, true); // Use capture phase
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
  document.removeEventListener('keydown', handleKeydownCapture, true);
  cleanup();
});
</script>

<style>
@import "@toast-ui/editor/dist/toastui-editor-viewer.css";
@import "prismjs/themes/prism.css";
@import "@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight.css";
@import "./EditorStyles.scss";
@import "./EditorStylesCustom.scss";
</style> 