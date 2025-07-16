<template>
  <TransitionRoot appear :show="isVisible" as="template">
    <Dialog as="div" @close="closeModal" class="relative z-modal">
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
            <DialogPanel class="transform overflow-visible rounded-lg bg-color-bg-neutral shadow-2xl transition-all preview-coordinate-modal" style="max-width: 90vw; max-height: 90vh;">
              <!-- Header -->
              <div class="flex items-center justify-between p-2">
                <!-- Left side - Maximize button -->
                <button
                  type="button"
                  class="inline-flex justify-center rounded-md bg-color-button-secondary-bg p-2 text-color-button-secondary-fg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg"
                  @click="openInFullView"
                  :title="note.category === 'output' ? 'Open in output view' : 'Open in coordinate view'"
                >
                  <Maximize2 class="w-4 h-4" />
                </button>
                
                <!-- Right side - Copy Link, Sticky, and Close buttons -->
                <div class="flex items-center gap-2">
                  <!-- Copy Link button -->
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-button-secondary-bg p-2 text-color-button-secondary-fg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg"
                    @click="copyLink"
                    title="Copy link"
                  >
                    <Link2 class="w-4 h-4" />
                  </button>
                  
                  <!-- Sticky button -->
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-button-secondary-bg p-2 text-color-button-secondary-fg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg"
                    @click="openInNote"
                    title="Open in note view"
                  >
                    <StickyNote class="w-4 h-4" />
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
              <div class="p-0">
                <!-- Loading state -->
                <div v-if="isLoading" class="flex items-center justify-center py-16">
                  <div class="text-center">
                    <Loader2 class="w-8 h-8 mx-auto text-color-primary animate-spin mb-2" />
                    <p class="text-sm text-color-text-secondary">
                      {{ note.category === 'output' ? 'Loading output structure...' : 'Loading molecular structure...' }}
                    </p>
                  </div>
                </div>
                
                <!-- Error state -->
                <div v-else-if="error" class="flex items-center justify-center py-16">
                  <div class="text-center">
                    <FileX class="w-16 h-16 mx-auto text-color-text-secondary mb-4" />
                    <h2 class="text-xl font-semibold text-color-text-primary mb-2">
                      {{ note.category === 'output' ? 'Failed to load output structure' : 'Failed to load molecular structure' }}
                    </h2>
                    <p class="text-color-text-secondary mb-4">{{ error }}</p>
                    <button
                      @click="retryLoad"
                      class="inline-flex items-center px-4 py-2 bg-color-button-primary-bg text-color-button-primary-fg rounded-lg hover:bg-color-button-primary-hover-bg transition-colors"
                    >
                      <RefreshCw class="w-4 h-4 mr-2" />
                      Retry
                    </button>
                  </div>
                </div>
                
                <!-- 3DmolViewer display -->
                <div v-else-if="fileContent && attachmentFilename" class="flex justify-center" style="height: 70vh; width: 70vw;">
                  <div class="w-full h-full">
                    <ThreeDmolViewer
                      :attachment-filename="attachmentFilename"
                      :note-title="note.title"
                      :file-content="fileContent"
                      @error="onViewerError"
                      @loading="onViewerLoading"
                      @loaded="onViewerLoaded"
                    />
                  </div>
                </div>
              </div>
              
              <!-- Tags section at bottom -->
              <div class="mt-4 mb-4 overflow-visible">
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
import { ref, watch, onMounted, onUnmounted, nextTick } from "vue";
import { useRouter } from "vue-router";
import { X, Loader2, FileX, RefreshCw, Link2, StickyNote, Maximize2 } from "lucide-vue-next";
import { useNoteAttachment } from "../composables/useNoteAttachment.js";
import { useGlobalStore } from "../lib/globalStore.js";
import TagInput from "./TagInput.vue";
import ThreeDmolViewer from "./3DmolViewer.vue";
import { updateNote, apiErrorHandler } from "../lib/api.js";

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

// State
const attachmentFilename = ref(null);
const fileContent = ref('');
const isLoading = ref(false);
const error = ref(null);
const editingTags = ref([]);

// Auto-save state (QuickNoteModalと同様の状態管理)
let autoSaveTimeout = null;
let contentChangedTimeout = null;
let titleGenerationTimeout = null;

const autoSaveState = ref({
  isAutoSaving: false,
  isAutoSavingInProgress: false
});

// Constants (QuickNoteModalと統一)
const AUTO_SAVE_DELAY = 1000; // 1000ms
const CONTENT_CHANGE_DELAY = 1000; // 1000ms
const TITLE_GENERATION_DELAY = 2000; // 2000ms

// Use composable for note data and attachment handling
const { loadNoteDataAndAttachment } = useNoteAttachment();

// Methods
function closeModal() {
  isVisible.value = false;
  emit("close");
}

async function loadCoordinateData() {
  if (!props.note.filename) {
    error.value = 'No note filename provided';
    return;
  }

  try {
    isLoading.value = true;
    error.value = null;

    // Extract basename from filename (remove .md extension)
    const basename = props.note.filename.replace(/\.md$/, '');
    
    // Load note data and get attachment filename
    const { attachmentFilename: filename, noteData } = await loadNoteDataAndAttachment(basename);
    
    // Set attachment filename
    attachmentFilename.value = filename;
    
    // Load file content
    await loadFileContent();
    
  } catch (err) {
    console.error('Failed to load coordinate data:', err);
    error.value = err.message || 'Failed to load coordinate data';
  } finally {
    isLoading.value = false;
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

function retryLoad() {
  loadCoordinateData();
}

function onViewerError(errorMessage) {
  console.error('3DmolViewer error:', errorMessage);
  error.value = errorMessage;
  isLoading.value = false;
}

function onViewerLoading() {
  // Don't set isLoading to true here, as it will interfere with the template conditions
  error.value = null;
}

function onViewerLoaded() {
  // isLoading is already false from loadCoordinateData
  error.value = null;
}

function copyLink() {
  const filename = props.note.filename.replace(/\.md$/, '');
  const url = `${window.location.origin}/${filename}`;
  
  navigator.clipboard.writeText(url).then(() => {
    // Show success toast notification
    globalStore.toast?.addToast(
      'Note URL copied to clipboard',
      'Copy Link',
      'success'
    );
  }).catch(err => {
    console.error('Failed to copy link:', err);
    // Show error toast notification
    globalStore.toast?.addToast(
      'Failed to copy URL to clipboard',
      'Copy Link Error',
      'error'
    );
  });
}

function openInNote() {
  closeModal();
  router.push({ 
    name: 'note', 
    params: { filename: props.note.filename.replace(/\.md$/, '') } 
  });
}

function openInFullView() {
  closeModal();
  if (props.note.category === 'output') {
    router.push({ 
      name: 'output', 
      params: { filename: props.note.filename.replace(/\.md$/, '') } 
    });
  } else {
    router.push({ 
      name: 'coordinate', 
      params: { filename: props.note.filename.replace(/\.md$/, '') } 
    });
  }
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
  if (autoSaveState.value.isAutoSavingInProgress) {
    return;
  }
  
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

function clearTitleGenerationTimeout() {
  if (titleGenerationTimeout) {
    clearTimeout(titleGenerationTimeout);
    titleGenerationTimeout = null;
  }
}

function autoSaveHandler() {
  if (hasChanges()) {
    performSave();
  }
}

function hasChanges() {
  const currentTags = editingTags.value;
  
  // タグの変更チェック（最適化）
  if (currentTags.length !== props.note.tags.length) {
    return true;
  }
  
  // タグの内容チェック（順序を考慮）
  const sortedCurrentTags = [...currentTags].sort();
  const sortedOriginalTags = [...props.note.tags].sort();
  
  for (let i = 0; i < sortedCurrentTags.length; i++) {
    if (sortedCurrentTags[i] !== sortedOriginalTags[i]) {
      return true;
    }
  }
  
  return false;
}

function resetAutoSaveState() {
  updateAutoSaveState({ 
    isAutoSaving: false, 
    isAutoSavingInProgress: false 
  });
}

function updateAutoSaveState(updates) {
  Object.assign(autoSaveState.value, updates);
}

async function performSave() {
  if (autoSaveState.value.isAutoSaving) return;
  
  updateAutoSaveState({ 
    isAutoSaving: true, 
    isAutoSavingInProgress: true 
  });
  
  try {
    const filenameWithExtension = props.note.filename;
    
    const updatedNote = await updateNote(
      filenameWithExtension,
      props.note.title,
      props.note.content,
      editingTags.value
    );
    
    // Update local state
    editingTags.value = [...updatedNote.tags];
    
    // Clear timeouts
    clearTimeout(autoSaveTimeout);
    clearTimeout(contentChangedTimeout);
    autoSaveTimeout = null;
    contentChangedTimeout = null;
    
  } catch (error) {
    console.error('Error saving note:', error);
    apiErrorHandler(error);
  } finally {
    resetAutoSaveState();
  }
}

function cleanup() {
  clearContentChangedTimeout();
  clearAutoSaveTimeout();
  clearTitleGenerationTimeout();
}

// Watch for modal visibility changes
watch(isVisible, (visible) => {
  if (visible && props.note) {
    loadCoordinateData();
    // Initialize editing tags
    editingTags.value = [...(props.note.tags || [])];
  } else {
    // Reset state when modal closes
    attachmentFilename.value = null;
    fileContent.value = '';
    error.value = null;
    isLoading.value = false;
    editingTags.value = [];
    cleanup();
  }
});

// Handle keyboard events
function handleKeydown(event) {
  if (event.key === 'Escape') {
    closeModal();
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

// Watch for tag changes to trigger auto-save
watch(editingTags, () => {
  if (isVisible.value) {
    startContentChangedTimeout();
  }
}, { deep: true });

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
  cleanup();
});
</script>

<style scoped>
.preview-coordinate-modal {
  max-width: 90vw;
  max-height: 90vh;
}
</style> 