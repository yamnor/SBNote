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
            <DialogPanel class="w-full transform overflow-visible rounded-lg bg-color-background shadow-2xl transition-all quick-note-modal" style="max-width: var(--layout-width-note);">
              <!-- Header -->
              <div class="flex items-center justify-between p-2 pb-0">
                <!-- Left side - Slide view button -->
                <div class="flex items-center space-x-2">
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-surface p-2 text-color-text-light hover:bg-color-primary hover:text-color-on-primary"
                    @click="openInSlide"
                    title="Open in slide view"
                  >
                    <Presentation class="w-4 h-4" />
                  </button>
                  

                  
                  <!-- 3DmolViewer button (only show for coordinate category) -->
                  <button
                    v-if="note.category === 'coordinate'"
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-surface p-2 text-color-text-light hover:bg-color-primary hover:text-color-on-primary"
                    @click="openInMol"
                    title="Open in molecular viewer"
                  >
                    <Bolt class="w-4 h-4" />
                  </button>
                  
                  <!-- Output button (only show for output category) -->
                  <button
                    v-if="note.category === 'output'"
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-surface p-2 text-color-text-light hover:bg-color-primary hover:text-color-on-primary"
                    @click="openInOutput"
                    title="Open in output view"
                  >
                    <Scroll class="w-4 h-4" />
                  </button>
                </div>
                
                <!-- Right side - Copy Link, Editor and Close buttons -->
                <div class="flex items-center space-x-2">
                  <!-- Auto-save indicator -->
                  <div class="flex items-center space-x-1">
                    <!-- Auto-saving indicator -->
                    <div
                      v-show="autoSaveState.isAutoSaving"
                      class="h-2 w-2 rounded-full bg-green-500 animate-pulse"
                      title="Auto-saving..."
                    ></div>
                    <!-- Unsaved changes indicator -->
                    <div
                      v-show="hasChanges() && !autoSaveState.isAutoSaving"
                      class="h-2 w-2 rounded-full bg-color-primary"
                      title="Unsaved changes"
                    ></div>
                  </div>
                  
                  <!-- Copy Link button -->
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-surface p-2 text-color-text-light hover:bg-color-primary hover:text-color-on-primary"
                    @click="copyLink"
                    title="Copy link"
                  >
                    <Link2 class="w-4 h-4" />
                  </button>
                  
                  <!-- Open in editor button -->
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-surface p-2 text-color-text-light hover:bg-color-primary hover:text-color-on-primary"
                    @click="openInEditor"
                    title="Open in full editor"
                  >
                    <StickyNote class="w-4 h-4" />
                  </button>
                  
                  <!-- Close button -->
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md bg-color-surface p-2 text-color-text-light hover:bg-color-primary hover:text-color-on-primary"
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
import { useNote } from "../composables/useNote.js";
import { useScrollControl } from "../composables/useScrollControl.js";

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

// Auto-save state management (Note.vueと同様の状態管理)
const autoSaveState = ref({ isAutoSaving: false, isAutoSavingInProgress: false });

// Phase 1: 既存機能の統一 - タイムアウト管理はuseNoteコンポーザブルで管理

// Phase 1: 既存機能の統一 - 新しいコンポーザブル
const { scrollToTop } = useScrollControl();
const {
  // 自動保存・タイトル生成
  autoSaveState: autoSaveStateFromComposable,
  startContentChangedTimeout,
  generateTitleFromContent,
  startTitleGeneration,
  resetAutoSaveState,
  updateIsNewNote,
  

  
  // ノート操作
  saveNote: saveNoteComposable,
  changeNoteVisibility: changeNoteVisibilityComposable,
  
  // 統合クリーンアップ
  cleanup: cleanupNote
} = useNote({
  // API関数
  updateNote,
  apiErrorHandler,
  
  // 依存関係
  router,
  apiErrorHandler,
  
  // コールバック関数
  onSaveSuccess: (data) => {
    emit('note-updated', data);
    

    editingContent.value = data.content;
    editingTags.value = [...data.tags];
  },
  onSaveFailure: (error) => {
    console.error('Error saving note:', error);
    apiErrorHandler(error);
  },
  onStateUpdate: (newState) => {
    Object.assign(autoSaveState.value, newState);
  },
  onContentChange: () => {
    return hasChanges();
  },
  onAutoSave: async () => {
    await performSave();
  },
  onTitleGenerated: (title) => {
    if (title && title !== generatedTitle.value) {
      generatedTitle.value = title;
    }
  },
  isNewNote: () => false // QuickNoteModalは既存ノートのみ
});

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
  
  // Phase 1: 既存機能の統一 - スクロール制御をコンポーザブルに移行
  setTimeout(() => {
    scrollToTop({ target: 'modal' });
  }, 100);
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
  const basename = props.note.filename.replace(/\.md$/, '');
  const url = `${window.location.origin}/${basename}`;
  
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
  
  // Phase 1: 既存機能の統一 - autoSaveStateはコンポーザブルで管理
  resetAutoSaveState();
  
  // Phase 1: 既存機能の統一 - スクロール制御をコンポーザブルに移行
  scrollToTop({ target: 'modal' });
}

// Phase 1: 既存機能の統一 - scrollToTopはuseScrollControlコンポーザブルで管理
// Phase 1: 既存機能の統一 - generateTitleFromContentはuseNoteコンポーザブルで管理

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

  // Phase 1: 既存機能の統一 - タイトル生成をコンポーザブルに移行
  startTitleGeneration(content, (newGeneratedTitle) => {
    if (newGeneratedTitle && newGeneratedTitle !== generatedTitle.value) {
      generatedTitle.value = newGeneratedTitle;
    }
  });
}

function handleTagConfirmed() {
  // Phase 1: 既存機能の統一 - タイムアウト管理はコンポーザブルに移行
  // Force save immediately for tag changes (Note.vueと同様)
  performSave();
}

// Phase 1: 既存機能の統一 - タイムアウト管理はuseNoteコンポーザブルで管理

// ✅ 修正: hasChanges関数をNote.vueと同様に最適化
function hasChanges() {
  if (!toastEditor.value || autoSaveState.value.isAutoSavingInProgress) {
    return false; // 自動保存中は変更チェックをスキップ
  }
  
  const currentContent = toastEditor.value.getMarkdown();
  const currentTags = editingTags.value;
  
  // コンテンツの変更チェック
  if (currentContent !== props.note.content) {
    return true;
  }
  
  // タグの変更チェック（Note.vueと同様の最適化）
  const originalTags = props.note.tags || [];
  if (currentTags.length !== originalTags.length) {
    return true;
  }
  
  // タグの内容チェック（順序を考慮）
  const sortedCurrentTags = [...currentTags].sort();
  const sortedOriginalTags = [...originalTags].sort();
  
  return sortedCurrentTags.some((tag, index) => tag !== sortedOriginalTags[index]);
}

// Phase 1: 既存機能の統一 - resetAutoSaveStateはuseNoteコンポーザブルで管理

async function performSave() {
  if (!toastEditor.value) return; // isAutoSavingInProgressチェックを削除
  
  try {
    const currentContent = toastEditor.value.getMarkdown();
    
    await saveNoteComposable(
      props.note.title,
      currentContent,
      editingTags.value,
      {
        close: false,
        isAuto: true,
        isNewNote: false,
        filename: props.note.filename.replace(noteConstants.MARKDOWN_EXTENSION, '')
      }
    );
  } catch (error) {
    console.error('Error saving note:', error);
    apiErrorHandler(error);
    // resetAutoSaveState()を削除（useNoteコンポーザブルが管理するため）
  }
}

// Phase 1: 既存機能の統一 - updateAutoSaveStateはuseNoteコンポーザブルで管理

function cleanup() {
  // Phase 1: 既存機能の統一 - クリーンアップはコンポーザブルに移行
  cleanupNote();
  
  // Clean up ToastUIEditor IME event listeners（不要な変更 - コメントアウト）
  // if (toastEditor.value && toastEditor.value.cleanup) {
  //   toastEditor.value.cleanup();
  // }
}

// Initialize editing when modal becomes visible
watch(isVisible, async (visible) => {
  if (visible && props.note.content) {
    // Wait for Vue DOM update
    await nextTick();
    
    // Initialize editing state
    initializeEditing();
    
    // Phase 1: 既存機能の統一 - スクロール制御をコンポーザブルに移行
    setTimeout(() => {
      scrollToTop({ target: 'modal' });
    }, 50);
  }
});

// Clean up viewer when modal closes
watch(isVisible, (visible) => {
  if (!visible) {
    cleanup();
  }
});

// ✅ 修正: タグ変更の監視を追加（Note.vueと同様）
watch([editingTags], () => {
  if (isVisible.value) {
    // タグ変更時に自動保存タイムアウトを開始
    startContentChangedTimeout();
  }
}, { deep: true });

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
  
  // Phase 1: 既存機能の統一 - スクロール制御をコンポーザブルに移行
  setTimeout(() => {
    scrollToTop({ target: 'modal' });
  }, 50);
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