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
            <DialogPanel class="w-full transform overflow-visible rounded-lg bg-color-bg-neutral shadow-2xl transition-all quick-note-modal" style="max-width: var(--layout-width-note);">
              <!-- Header -->
              <div class="flex items-center justify-between p-2 pb-0">
                <!-- Left side - Slide view button -->
                <div class="flex items-center space-x-2">
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-button-secondary-bg p-2 text-color-button-secondary-fg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg"
                    @click="openInSlide"
                    title="Open in slide view"
                  >
                    <Presentation class="w-4 h-4" />
                  </button>
                  

                  
                  <!-- 3DmolViewer button (only show for coordinate category) -->
                  <button
                    v-if="note.category === 'coordinate'"
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-button-secondary-bg p-2 text-color-button-secondary-fg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg"
                    @click="openInMol"
                    title="Open in molecular viewer"
                  >
                    <Bolt class="w-4 h-4" />
                  </button>
                  
                  <!-- Output button (only show for output category) -->
                  <button
                    v-if="note.category === 'output'"
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-button-secondary-bg p-2 text-color-button-secondary-fg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg"
                    @click="openInOutput"
                    title="Open in output view"
                  >
                    <Scroll class="w-4 h-4" />
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
              <div class="max-h-96 overflow-y-auto overflow-x-hidden">
                <ToastUIEditor
                  ref="toastEditor"
                  :key="`editor-${note.filename}`"
                  :initialValue="editingContent"
                  :initialEditType="'markdown'"
                  :previewStyle="'tab'"
                  @change="handleEditorChange"
                />
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
import { onMounted, ref, watch, nextTick, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { X, Maximize2, Presentation, Link2, Bolt, Scroll, StickyNote } from "lucide-vue-next";
import { useGlobalStore } from "../lib/globalStore.js";
import TagInput from "./TagInput.vue";
import ToastUIEditor from "./ToastUIEditor.vue";
import { updateNote, apiErrorHandler } from "../lib/api.js";
import { noteConstants } from "../lib/constants.js";

const props = defineProps({
  note: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(["close", "note-updated"]);
const isVisible = defineModel({ type: Boolean });
const router = useRouter();
const globalStore = useGlobalStore();

// Refs
const toastEditor = ref();

// Edit state
const editingContent = ref('');
const editingTags = ref([]);

// Auto-save state (Note.vueと同様の状態管理)
let autoSaveTimeout = null;
let contentChangedTimeout = null;
let titleGenerationTimeout = null;

// ✅ 修正: autoSaveStateをrefとして定義
const autoSaveState = ref({
  isAutoSaving: false,
  isAutoSavingInProgress: false
});

// ✅ 修正: 定数を正しく使用
const AUTO_SAVE_DELAY = noteConstants.AUTO_SAVE_DELAY; // 1000ms
const CONTENT_CHANGE_DELAY = noteConstants.CONTENT_CHANGE_DELAY; // 1000ms
const TITLE_GENERATION_DELAY = noteConstants.TITLE_GENERATION_DELAY; // 500ms

// Title generation state
const generatedTitle = ref('');

// Constants (Note.vueと統一)
// noteConstants.AUTO_SAVE_DELAY = 1000ms
// noteConstants.CONTENT_CHANGE_DELAY = 1000ms
// noteConstants.TITLE_GENERATION_DELAY = 2000ms

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



function openInMol() {
  closeModal();
  router.push({ 
    name: 'coordinate', 
    params: { filename: props.note.filename.replace(/\.md$/, '') } 
  });
}

function openInOutput() {
  closeModal();
  router.push({ 
    name: 'output', 
    params: { filename: props.note.filename.replace(/\.md$/, '') } 
  });
}

function copyLink() {
  const filename = props.note.filename.replace(/\.md$/, '');
  const url = `${window.location.origin}/note/${filename}`;
  
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

function initializeEditing() {
  editingContent.value = props.note.content || '';
  editingTags.value = [...(props.note.tags || [])];
  generatedTitle.value = '';
  
  // ✅ 修正: autoSaveStateを初期化
  updateAutoSaveState({
    isAutoSaving: false,
    isAutoSavingInProgress: false
  });
}

// Title generation function (Note.vueと同様)
function generateTitleFromContent(content) {
  if (!content) return "";
  
  // Split content into lines and get the first non-empty line
  const lines = content.split('\n');
  let firstLine = "";
  
  for (const line of lines) {
    const trimmedLine = line.trim();
    if (trimmedLine) {
      firstLine = trimmedLine;
      break;
    }
  }
  
  if (!firstLine) return "";
  
  // Remove markdown formatting
  let title = firstLine
    .replace(/^#+\s*/, '') // Remove heading markers
    .replace(/^\*\s*/, '') // Remove list markers
    .replace(/^-\s*/, '') // Remove list markers
    .replace(/^>\s*/, '') // Remove blockquote markers
    .replace(/^`+/, '') // Remove code markers at start
    .replace(/`+$/, '') // Remove code markers at end
    .replace(/^\|/, '') // Remove table markers
    .replace(/\|$/, '') // Remove table markers
    .trim();
  
  // Limit title length
  if (title.length > 100) {
    title = title.substring(0, 100) + '...';
  }
  
  return title;
}

function handleEditorChange() {
  // ✅ 修正: ToastUIEditorの初期化チェックを追加
  if (!toastEditor.value || autoSaveState.value.isAutoSavingInProgress) {
    return;
  }
  
  startContentChangedTimeout();

  const content = toastEditor.value.getMarkdown();
  if (generateTitleFromContent(content) !== props.note.title) {
    // Title has changed, update generated title
    const newGeneratedTitle = generateTitleFromContent(content);
    if (newGeneratedTitle && newGeneratedTitle !== generatedTitle.value) {
      generatedTitle.value = newGeneratedTitle;
    }
  }

  // Auto-generate title from first line (Note.vueと同様)
  clearTimeout(titleGenerationTimeout);
  titleGenerationTimeout = setTimeout(() => {
    if (toastEditor.value) {
      const content = toastEditor.value.getMarkdown();
      const newGeneratedTitle = generateTitleFromContent(content);
      if (newGeneratedTitle && newGeneratedTitle !== generatedTitle.value) {
        generatedTitle.value = newGeneratedTitle;
      }
    }
  }, TITLE_GENERATION_DELAY);
}

function handleTagConfirmed() {
  // Force save immediately for tag changes (Note.vueと同様)
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

// ✅ 修正: contentChangedHandlerをNote.vueと同様に改善
function contentChangedHandler() {
  if (!toastEditor.value || autoSaveState.value.isAutoSavingInProgress) {
    return; // 重要な: 保存中は処理をスキップ
  }
  
  if (hasChanges()) {
    startAutoSaveTimeout();
  }
  
  // Auto-generate title from first line
  clearTimeout(titleGenerationTimeout);
  titleGenerationTimeout = setTimeout(() => {
    if (toastEditor.value) {
      const content = toastEditor.value.getMarkdown();
      const generatedTitle = generateTitleFromContent(content);
      if (generatedTitle && generatedTitle !== props.note.title) {
        // タイトルが変更された場合のみ更新
        props.note.title = generatedTitle;
      }
    }
  }, TITLE_GENERATION_DELAY);
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

// ✅ 修正: hasChanges関数をNote.vueと同様に最適化
function hasChanges() {
  if (!toastEditor.value) return false;
  
  const currentContent = toastEditor.value.getMarkdown();
  const currentTags = editingTags.value;
  
  // コンテンツの変更チェック
  if (currentContent !== props.note.content) {
    return true;
  }
  
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

// ✅ 修正: resetAutoSaveState関数を追加
function resetAutoSaveState() {
  updateAutoSaveState({ 
    isAutoSaving: false, 
    isAutoSavingInProgress: false 
  });
}

async function performSave() {
  if (!toastEditor.value || autoSaveState.value.isAutoSaving) return;
  
  updateAutoSaveState({ 
    isAutoSaving: true, 
    isAutoSavingInProgress: true 
  });
  
  try {
    const currentContent = toastEditor.value.getMarkdown();
    const filenameWithExtension = props.note.filename;
    
    const updatedNote = await updateNote(
      filenameWithExtension,
      props.note.title,
      currentContent,
      editingTags.value
    );
    
    // ✅ 修正: Props直接変更を避けてemitを使用
    emit('note-updated', updatedNote);
    
    // Update local state
    editingContent.value = currentContent;
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
    resetAutoSaveState(); // ✅ 修正: 新しい関数を使用
  }
}

function updateAutoSaveState(updates) {
  Object.assign(autoSaveState.value, updates);
}

function cleanup() {
  clearContentChangedTimeout();
  clearAutoSaveTimeout();
  clearTitleGenerationTimeout();
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
                          target.closest('.toastui-editor') ||
                          target.closest('.quick-note-modal');
    
    // Check if the target is within tag input container
    const isTagInput = target.closest('.tag-input-container');
    
    // For tag input elements, don't stop propagation to allow Enter key handling
    if (isTagInput) {
      return; // Allow event to continue to TagInput component
    }
    
    // Stop propagation for other elements when modal is visible to prevent search input capture
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
@import "./ToastUIEditor.scss";
@import "./ToastUIEditorCustom.scss";
</style> 