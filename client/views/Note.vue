<template>
  <!-- Confirm Deletion Modal -->
  <ConfirmModal
    v-model="fileOperations.uiState.isDeleteModalVisible"
    title="Confirm Deletion"
    :message="`Are you sure you want to delete the note '${note.title}'?`"
    confirmButtonText="Delete"
    confirmButtonStyle="danger"
    @confirm="deleteConfirmedHandler"
  />

  <!-- File Size Limit Modal -->
  <ConfirmModal
    v-model="fileOperations.uiState.isFileSizeModalVisible"
    title="File Too Large"
    :message="fileOperations.fileSizeModalMessage"
    confirmButtonText="OK"
    confirmButtonStyle="cta"
    @confirm="fileOperations.closeFileSizeModal"
  />

  <div :class="`w-full mx-auto flex flex-col overflow-visible h-full`">
    <Loading ref="loadingIndicator" class="flex-1 overflow-visible">
      <div class="flex flex-col h-full">
        <!-- Content -->
        <NoteEditor
          :note="note"
          :can-modify="canModify"
          :is-new-note="isNewNote"
          :add-image-blob-hook="fileOperations.addImageBlobHook"
          @editor-change="handleEditorChange"
        />

        <!-- Tags section at bottom -->
        <div class="mt-2 mb-2 note-content-width">
          <TagInput 
            v-model="displayTags"
            :readonly="!canModify"
            @tagConfirmed="onTagConfirmed"
          />
        </div>

        <!-- Note Information Display -->
        <NoteInfoPanel :note="note" />

        <!-- Tag Grid section -->
        <NoteTagGrid
          :note-tags="noteTags"
          :note-container-style="noteContainerStyle"
          @tag-click="onNoteTagClick"
          @tag-dblclick="onNoteTagDoubleClick"
        />
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

/* Toast Editor container styling */
.flex-1 {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: visible;
}

/* Note content width styling */
.note-content-width {
  max-width: var(--layout-width-note);
  width: 100%;
  margin-left: auto;
  margin-right: auto;
}
</style>

<script setup>
import { FileX } from "lucide-vue-next";
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useRoute } from "vue-router";

import { Note } from "../lib/classes.js";
import ConfirmModal from "../components/modal/ConfirmModal.vue";
import Loading from "../components/ui/Loading.vue";
import TagInput from "../components/input/TagInput.vue";
import { NoteEditor, NoteTagGrid, NoteInfoPanel } from "../components/note/index.js";

import { noteConstants, params } from "../lib/constants.js";
import { useGlobalStore } from "../lib/globalStore.js";
import { useNoteEditor } from "../composables/useNoteEditor.js";
import { useNoteAutoSave } from "../composables/useNoteAutoSave.js";
import { useNoteFileOperations } from "../composables/useNoteFileOperations.js";
import { useNoteTagGrid } from "../composables/useNoteTagGrid.js";

const props = defineProps({
  filename: String,
});

const route = useRoute();
const router = useRouter();
const globalStore = useGlobalStore();
const loadingIndicator = ref();

// Composables
const {
  toastEditor,
  newTitle,
  newTags,
  generateTitleFromContent,
  ensureTitle,
  saveDefaultEditorMode,
  loadDefaultEditorMode,
  getInitialEditorValue
} = useNoteEditor();

const {
  autoSaveState,
  uiState: autoSaveUIState,
  setBeforeUnloadConfirmation,
  startContentChangedTimeout,
  clearContentChangedTimeout,
  startAutoSaveTimeout,
  clearAutoSaveTimeout,
  clearTitleGenerationTimeout,
  resetAutoSaveState,
  contentChangedHandler,
  autoSaveHandler: autoSaveHandlerFromComposable,
  handleContentChange,
  handleEditorChange: handleAutoSaveEditorChange,
  isContentChanged,
  cleanup: cleanupAutoSave
} = useNoteAutoSave();

const {
  fileSizeModalMessage,
  uiState: fileOperationsUIState,
  createEmptyNote: createEmptyNoteFromComposable,
  saveNewNote,
  saveExistingNote,
  deleteNoteHandler,
  loadNote,
  changeNoteVisibility: changeNoteVisibilityFromComposable,
  addImageBlobHook,
  postAttachment,
  handleSaveFailure,
  showFileSizeModal,
  closeFileSizeModal
} = useNoteFileOperations();

const {
  tagGridState,
  tagCountsState,
  selectedNoteTag,
  displayedTagNotes,
  noteTagSortBy,
  noteTagSortOrder,
  tagSortBy,
  tagSortOrder,
  noteTags: computedNoteTags,
  sortedTagNotes,
  tagGridItems,
  updateTagGridState,
  updateTagCountsState,
  loadTagCounts,
  onNoteTagClick,
  onNoteTagDoubleClick,
  updateNoteTagSortOrder,
  updateTagSortOrder,
  resetTagGridState
} = useNoteTagGrid();

const canModify = computed(() => {
  // README.md is always read-only
  if (props.filename && props.filename.toLowerCase() === 'readme.md') {
    return false;
  }
  return globalStore.isAuthenticated && globalStore.config.authType !== 'read_only' && globalStore.editMode;
});

// State management - grouped related states
const noteState = ref({
  note: {},
  isNewNote: !props.filename
});

// Computed properties for easier access
const note = computed(() => noteState.value.note);
const isNewNote = computed(() => noteState.value.isNewNote);

// Computed property for tag display
const displayTags = computed({
  get: () => canModify.value ? newTags.value : (note.value.tags || []),
  set: (value) => {
    if (canModify.value) {
      newTags.value = value;
    }
  }
});

// Computed property for note tags (current note's tags)
const noteTags = computed(() => {
  return computedNoteTags.value(newTags.value, canModify.value, note.value);
});

// Computed property for tag grid items
const computedTagGridItems = computed(() => {
  return tagGridItems.value(noteTags.value, selectedNoteTag.value);
});

// State update functions
function updateNoteState(updates) {
  Object.assign(noteState.value, updates);
}

// Create empty note to get filename immediately
function createEmptyNote() {
  const emptyTitle = newTitle.value || noteConstants.DEFAULT_TITLE;
  const emptyContent = note.value.content || "";
  const defaultTags = newTags.value;
  
  createEmptyNoteFromComposable(emptyTitle, emptyContent, defaultTags, updateNoteState, autoSaveUIState)
    .then((data) => {
      // Update newTags with server data (silently to avoid watch trigger)
      const serverTags = data.tags || [];
      if (newTags.value.length !== serverTags.length || 
          newTags.value.some((tag, index) => tag !== serverTags[index])) {
        newTags.value = serverTags;
      }
      
      setBeforeUnloadConfirmation(false);
    })
    .catch((error) => {
      console.error('Failed to create empty note:', error);
    });
}

function handleEditorChange(event) {
  if (canModify.value) {
    const { content, generatedTitle } = event;
    
    if (generatedTitle && generatedTitle !== newTitle.value) {
      newTitle.value = generatedTitle;
    }
    
    handleAutoSaveEditorChange(generateTitleFromContent, newTitle, note.value);
  }
}

async function init() {
  if (props.filename && props.filename === note.value.filename) {
    return;
  }
  loadingIndicator.value.setLoading();
  
  // Load tag counts first
  await loadTagCounts();
  
  if (props.filename) {
    loadNote(props.filename, updateNoteState, autoSaveUIState, resetTagGridState, loadingIndicator)
      .then((data) => {
        // Initialize newTags separately
        newTags.value = data.tags || [];
        updateFileMenuState();
      })
      .catch((error) => {
        console.error('Failed to load note:', error);
      });
  } else {
    // Check if tag parameter is provided for new note
    const tagFromQuery = route.query.tag;
    const contentFromQuery = route.query[params.content];
    const initialTags = tagFromQuery ? [tagFromQuery] : [];
    
    updateNoteState({
      note: new Note({
        content: contentFromQuery || ""
      })
    });
    
    // Initialize newTags separately
    newTags.value = initialTags;
    
    // Set default title for new note
    document.title = "New Note - SBNote";
    globalStore.currentNoteTitle = "New Note";
    globalStore.currentNoteCategory = "note";
    globalStore.currentNoteTags = initialTags;
    loadingIndicator.value.setLoaded();
    updateFileMenuState();
    
    // Reset tag grid state for new note
    resetTagGridState();
    
    // Immediately create empty note to get filename
    createEmptyNote();
  }
}







// Note Deletion (for NavBar event)
function deleteHandler() {
  fileOperationsUIState.value.isDeleteModalVisible = true;
}

// Copy Link (for NavBar event)
function copyLinkHandler() {
  // Get current note URL
  const currentRoute = router.currentRoute.value;
  const noteUrl = router.resolve(currentRoute).href;
  const fullUrl = window.location.origin + noteUrl;
  
  // Copy to clipboard
  navigator.clipboard.writeText(fullUrl).then(() => {
    // Show success toast notification
    globalStore.toast?.addToast(
      'Note URL copied to clipboard',
      'Copy Link',
      'success'
    );
  }).catch(err => {
    console.error('Failed to copy URL:', err);
    // Show error toast notification
    globalStore.toast?.addToast(
      'Failed to copy URL to clipboard',
      'Copy Link Error',
      'error'
    );
  });
}

// Close Note (for NavBar event)
function closeHandler() {
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

// Toggle Preview Style (for NavBar event)
function togglePreviewStyleHandler(event) {
  // The previewStyle is already updated in globalStore by NavBar
  // No additional logic needed as the computed property will automatically update
}

// Change Visibility (for NavBar event)
function changeVisibilityHandler(event) {
  const visibility = event.detail;
  changeNoteVisibility(visibility);
}

function deleteConfirmedHandler() {
  deleteNoteHandler(props.filename, autoSaveUIState);
}

function changeNoteVisibility(visibility) {
  if (!canModify.value || isNewNote.value) {
    return;
  }
  
  changeNoteVisibilityFromComposable(visibility, props.filename, newTitle.value, note.value, newTags.value, updateNoteState, updateFileMenuState)
    .then(async () => {
      // Reload tag counts to reflect changes
      await loadTagCounts();
    })
    .catch((error) => {
      console.error('Failed to change note visibility:', error);
    });
}





function closeNote() {
  clearAutoSaveTimeout();
  clearTitleGenerationTimeout();
  if (isNewNote.value) {
    router.push({ name: "home" });
  }
}

function onTagConfirmed() {
  // Only proceed if we can modify the note
  if (!canModify.value) {
    return
  }
  
  // Clear any pending auto-save timeout
  clearAutoSaveTimeout();
  
  // Force save immediately for tag changes
  if (!autoSaveState.value.isAutoSaving) {
    performSave(false, true);
  }
}

// Unified save function
function performSave(close = false, isAuto = false) {
  saveDefaultEditorMode();
  ensureTitle();
  
  autoSaveState.value.isAutoSaving = true;
  autoSaveState.value.isAutoSavingInProgress = true;
  
  const newContent = toastEditor.value.getMarkdown();
  if (isNewNote.value) {
    saveNewNote(newTitle.value, newContent, newTags.value, close, isAuto, updateNoteState, autoSaveUIState, resetAutoSaveState, closeNote);
  } else {
    saveExistingNote(props.filename, newTitle.value, newContent, newTags.value, close, isAuto, updateNoteState, autoSaveUIState, resetAutoSaveState, closeNote);
  }
}



// Update file menu state in App.vue
function updateFileMenuState() {
  if (window.updateNoteFileMenuState) {
    window.updateNoteFileMenuState({
      canModify: canModify.value,
      isNewNote: isNewNote.value,
      autoSaveState: autoSaveState.value,
      unsavedChanges: autoSaveUIState.value.unsavedChanges,
      currentVisibility: note.value.visibility || 'private'
    });
  }
  
  // Update current note tags globally for NavBar component
  const currentTags = canModify.value ? newTags.value : (note.value.tags || []);
  globalStore.currentNoteTags = currentTags;
  
  // Update current note category globally for NavBar component
  globalStore.currentNoteCategory = note.value.category || 'note';
}

watch([newTitle], () => {
  if (newTitle.value && newTitle.value.trim()) {
    document.title = `${newTitle.value} - SBNote`;
    globalStore.currentNoteTitle = newTitle.value;
  }
  // Handle content change manually
  if (autoSaveState.value.isAutoSavingInProgress) {
    return;
  }
  
  if (isContentChanged(newTitle.value, note.value, newTags.value, toastEditor.value)) {
    autoSaveUIState.value.unsavedChanges = true;
    setBeforeUnloadConfirmation(true);
    const delay = isNewNote.value ? noteConstants.NEW_NOTE_AUTO_SAVE_DELAY : noteConstants.AUTO_SAVE_DELAY;
    setTimeout(() => {
      if (autoSaveUIState.value.unsavedChanges && !autoSaveState.value.isAutoSaving) {
        if (!isContentChanged(newTitle.value, note.value, newTags.value, toastEditor.value)) {
          resetAutoSaveState();
          return;
        }
        performSave(false, true);
      }
    }, delay);
  } else {
    autoSaveUIState.value.unsavedChanges = false;
    setBeforeUnloadConfirmation(false);
    clearAutoSaveTimeout();
  }
}, { deep: true, immediate: true });

watch([newTags], async () => {
  // Check if this is a tags-only change
  const isTagsOnlyChange = (
    newTitle.value === note.value.title &&
    (toastEditor.value && toastEditor.value.getMarkdown() === note.value.content) &&
    newTags.value.length !== (note.value.tags || []).length
  );
  
  // Handle content change manually
  if (autoSaveState.value.isAutoSavingInProgress) {
    return;
  }
  
  if (isContentChanged(newTitle.value, note.value, newTags.value, toastEditor.value)) {
    autoSaveUIState.value.unsavedChanges = true;
    setBeforeUnloadConfirmation(true);
    
    const delay = isTagsOnlyChange ? noteConstants.TAGS_ONLY_CHANGE_DELAY : noteConstants.AUTO_SAVE_DELAY;
    setTimeout(() => {
      if (autoSaveUIState.value.unsavedChanges && !autoSaveState.value.isAutoSaving) {
        performSave(false, true);
      }
    }, delay);
  } else {
    autoSaveUIState.value.unsavedChanges = false;
    setBeforeUnloadConfirmation(false);
    clearAutoSaveTimeout();
  }
  
  // Reset tag grid state when tags change
  if (selectedNoteTag.value) {
    resetTagGridState();
  }
  
  // Update tag counts when tags change (for immediate UI feedback)
  if (canModify.value) {
    await loadTagCounts();
  }
}, { deep: true });

watch(() => props.filename, async () => {
  if (toastEditor.value && toastEditor.value.getMarkdown() !== note.value.content) {
    autoSaveUIState.value.unsavedChanges = true;
  }
  await init();
});

// Watch for changes that affect file menu state
watch([canModify, isNewNote, autoSaveState, () => autoSaveUIState.value.unsavedChanges], () => {
  updateFileMenuState();
}, { deep: true });

// Watch for edit mode changes to set preview style for view mode
watch(canModify, (newCanModify) => {
  // In view mode (canModify = false), always use single view (tab)
  if (!newCanModify) {
    globalStore.setPreviewStyle('tab');
  }
}, { immediate: true });

onMounted(async () => {
  await init();
  
  // Listen for file menu events from NavBar
  window.addEventListener('note-close', closeHandler);
  window.addEventListener('note-copy-link', copyLinkHandler);
  window.addEventListener('note-delete', deleteHandler);
  window.addEventListener('note-toggle-preview-style', togglePreviewStyleHandler);
  window.addEventListener('note-change-visibility', changeVisibilityHandler);
  
  // Update file menu state in App.vue
  updateFileMenuState();
});

onUnmounted(() => {
  // Clean up event listeners
  window.removeEventListener('note-close', closeHandler);
  window.removeEventListener('note-copy-link', copyLinkHandler);
  window.removeEventListener('note-delete', deleteHandler);
  window.removeEventListener('note-toggle-preview-style', togglePreviewStyleHandler);
  window.removeEventListener('note-change-visibility', changeVisibilityHandler);
  
  // Clean up auto save
  cleanupAutoSave();
});
</script>
