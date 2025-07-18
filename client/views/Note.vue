<template>
  <!-- Confirm Deletion Modal -->
  <ConfirmModal
    v-model="state.uiState.isDeleteModalVisible"
    title="Confirm Deletion"
    :message="`Are you sure you want to delete the note '${note.title}'?`"
    confirmButtonText="Delete"
    confirmButtonStyle="danger"
    @confirm="deleteConfirmedHandler"
  />

  <!-- File Size Limit Modal -->
  <ConfirmModal
    v-model="state.uiState.isFileSizeModalVisible"
    title="File Too Large"
    :message="fileSizeModalMessage"
    confirmButtonText="OK"
    confirmButtonStyle="cta"
    @confirm="closeFileSizeModal"
  />

  <div :class="`w-full mx-auto flex flex-col overflow-visible h-full`">
    <Loading ref="loadingIndicator" class="flex-1 overflow-visible">
      <div class="flex flex-col h-full">
        <!-- Content -->
        <div class="flex-1 editor-container">
          <ToastUIEditor
            v-if="canModify"
            ref="toastEditor"
            :key="note.filename || 'new-note'"
            :initialValue="getInitialEditorValue()"
            :initialEditType="loadDefaultEditorMode()"
            :addImageBlobHook="addImageBlobHook"
            :previewStyle="globalStore.previewStyle"

            @change="handleEditorChange"
          />
          <ToastUIEditorViewer
            v-else
            :initialValue="note.content"
          />
        </div>

        <!-- Tags section at bottom -->
        <div class="mt-2 mb-2 note-content-width">
          <TagInput 
            v-model="displayTags"
            :readonly="!canModify"
            @tagConfirmed="onTagConfirmed"
          />
        </div>

        <!-- Note Information Display -->
        <div class="note-content-width">
          <!-- Header with toggle -->
          <div class="flex items-center gap-1 p-1 bg-color-surface border-b border-color-surface cursor-pointer hover:bg-color-surface transition-colors" @click="toggleInfoSection">
            <ChevronDown v-if="state.uiState.isInfoExpanded" class="w-4 h-4 text-color-text-light" />
            <ChevronRight v-else class="w-4 h-4 text-color-text-light" />
            <Info class="w-4 h-4 text-color-text-light" />
            <span class="text-sm text-color-text-light">Info</span>
          </div>
          
          <!-- Collapsible content -->
          <div v-show="state.uiState.isInfoExpanded" class="text-xs text-color-text-light flex flex-col gap-1 p-1 bg-color-surface">
            <div class="flex flex-row justify-between">
              <div class="flex flex-col">
                <span v-if="note.category">Category: {{ note.category }}</span>
                <span v-if="note.visibility">Visibility: {{ note.visibility }}</span>
              </div>
              <div class="flex flex-col items-end">
                <span v-if="note.lastModifiedAsString">Modified: {{ note.lastModifiedAsString }}</span>
                <span v-if="note.createdTimeAsString">Created: {{ note.createdTimeAsString }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Tag Grid section -->
        <div v-if="noteTags.length > 0" class="mt-2 tag-grid-container" :style="noteContainerStyle">
          <div>
            <!-- Sort Controls -->
            <div class="flex items-center justify-end w-full mb-2 space-x-2">
              <SortDropdown
                v-if="selectedNoteTag && displayedTagNotes.length > 0"
                v-model="noteTagSortBy"
                :sort-order="noteTagSortOrder"
                @update:sort-order="updateNoteTagSortOrder"
                :options="noteSortOptions"
                label="Sort Notes by"
              />
              <SortDropdown
                v-model="tagSortBy"
                :sort-order="tagSortOrder"
                @update:sort-order="updateTagSortOrder"
                :options="tagSortOptions"
                label="Sort Tags by"
              />
            </div>

            <!-- Grid Content -->
            <GridLayout
              :items="tagGridItems"
              @tag-click="onNoteTagClick"
              @tag-dblclick="onNoteTagDoubleClick"
            />
          </div>
        </div>

        <!-- Bottom margin for page spacing -->
        <div class="h-20"></div>
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

/* Editor container styling */
.editor-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: visible;
}

/* Tag grid container styling for split view */
.tag-grid-container {
  max-width: var(--layout-width-note);
  width: 100%;
  margin-left: auto;
  margin-right: auto;
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
import { FileX, ChevronDown, ChevronRight, Info } from "lucide-vue-next";
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useRoute } from "vue-router";


import {
  apiErrorHandler,
  createAttachment,
  createNote,
  deleteNote,
  getNote,
  updateNote,
  getNotesByTag,
  getTagsWithCounts,
} from "../lib/api.js";
import { Note } from "../lib/classes.js";
import ConfirmModal from "../components/ConfirmModal.vue";

import Loading from "../components/Loading.vue";
import TagInput from "../components/TagInput.vue";
import ToastUIEditor from "../components/ToastUIEditor.vue";
import ToastUIEditorViewer from "../components/ToastUIEditorViewer.vue";
import SortDropdown from "../components/SortDropdown.vue";
import GridLayout from "../components/GridLayout.vue";

import { noteConstants, params } from "../lib/constants.js";
import { useGlobalStore } from "../lib/globalStore.js";
import { useSorting } from "../composables/useSorting.js";
import { useGridData } from "../composables/useGridData.js";
import { useTagInteractions } from "../composables/useTagInteractions.js";
import { useDataFetching } from "../composables/useDataFetching.js";
import { useNote } from "../composables/useNote.js";
import { useScrollControl } from "../composables/useScrollControl.js";

const props = defineProps({
  filename: String,
});

const route = useRoute();

const globalStore = useGlobalStore();
const canModify = computed(() => {
  // README.md is always read-only
  if (props.filename && props.filename.toLowerCase() === 'readme.md') {
    return false;
  }
  return globalStore.isAuthenticated && globalStore.config.authType !== 'read_only' && globalStore.editMode;
});
// Phase 1: 既存機能の統一 - タイムアウト管理をコンポーザブルに移行
// let autoSaveTimeout = null; // 現在はuseNoteコンポーザブルで管理
const loadingIndicator = ref();
const router = useRouter();
const toastEditor = ref();

// Composables
const { noteSortOptions, tagSortOptions, sortItems } = useSorting();
const { createNestedGridItems } = useGridData();
const { handleTagClick, handleTagDoubleClick } = useTagInteractions();
const { fetchNotesByTag } = useDataFetching();

// Phase 1: 既存機能の統一 - 新しいコンポーザブル（isNewNoteの定義後に移動）
const { scrollToTop } = useScrollControl();

// State management - grouped related states
const state = ref({
  noteState: {
    note: {},
    newTitle: "",
    isNewNote: !props.filename
  },
  uiState: {
    isDeleteModalVisible: false,
    isFileSizeModalVisible: false,
    unsavedChanges: false,
    isInfoExpanded: false
  },
  autoSaveState: {
    isAutoSaving: false,
    isAutoSavingInProgress: false
  },
  tagGridState: {
    selectedNoteTag: null,
    displayedTagNotes: [],
    noteTagSortBy: 'lastModified',
    noteTagSortOrder: 'desc',
    tagSortBy: 'name',
    tagSortOrder: 'asc'
  },
  tagCountsState: {
    allTagsWithCounts: []
  }
});

// Computed properties for easier access
const note = computed(() => state.value.noteState.note);
const newTitle = computed(() => state.value.noteState.newTitle);
const isNewNote = computed(() => state.value.noteState.isNewNote);

// Phase 1: 既存機能の統一 - useNoteは関数定義後に移動

// Tag grid computed properties
const selectedNoteTag = computed(() => state.value.tagGridState.selectedNoteTag);
const displayedTagNotes = computed(() => state.value.tagGridState.displayedTagNotes);
const noteTagSortBy = computed(() => state.value.tagGridState.noteTagSortBy);
const noteTagSortOrder = computed(() => state.value.tagGridState.noteTagSortOrder);
const tagSortBy = computed(() => state.value.tagGridState.tagSortBy);
const tagSortOrder = computed(() => state.value.tagGridState.tagSortOrder);

// Phase 1: 既存機能の統一 - autoSaveStateはuseNoteから取得

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
  // Use newTags for editing mode, note.value.tags for view mode
  const tags = canModify.value ? newTags.value : (note.value.tags || []);
  const allTagsWithCounts = state.value.tagCountsState.allTagsWithCounts;
  
  const tagData = tags.map(tag => {
    // Find the actual count for this tag
    const tagData = allTagsWithCounts.find(t => t.tag === tag);
    return {
      tag: tag,
      count: tagData ? tagData.count : 1
    };
  });
  
  // Sort the tags
  return sortItems(tagData, tagSortBy.value, tagSortOrder.value, 'tags');
});

// Computed property for sorted tag notes
const sortedTagNotes = computed(() => {
  return sortItems(displayedTagNotes.value, noteTagSortBy.value, noteTagSortOrder.value, 'notes');
});

// Computed property for tag grid items
const tagGridItems = computed(() => {
  const items = createNestedGridItems(noteTags.value, sortedTagNotes.value, selectedNoteTag.value, []);
  return items;
});

// ✅ 修正: noteContainerStyleを定義
const noteContainerStyle = computed(() => ({}));

// newTags is a ref for v-model compatibility
const newTags = ref([]);

// File size modal message
const fileSizeModalMessage = ref("");

// ✅ 修正: 更新関数を1個に統合
function updateState(path, updates) {
  const target = path.split('.').reduce((obj, key) => obj[key], state.value);
  Object.assign(target, updates);
}

// State update functions (後方互換性のため残す)
function updateNoteState(updates) {
  updateState('noteState', updates);
}

function updateUIState(updates) {
  updateState('uiState', updates);
}

// Phase 1: 既存機能の統一 - updateAutoSaveStateはuseNoteコンポーザブルで管理

function updateTagGridState(updates) {
  updateState('tagGridState', updates);
}

function updateTagCountsState(updates) {
  updateState('tagCountsState', updates);
}

// Load tag counts
async function loadTagCounts() {
  await loadTagCountsComposable();
  // 状態を更新
  updateTagCountsState({ allTagsWithCounts: tagCountsStateComposable.value.allTagsWithCounts });
}

// Tag grid event handlers
async function onNoteTagClick(tagName) {
  await onNoteTagClickComposable(tagName);
  // 状態を更新
  updateTagGridState({
    selectedNoteTag: tagGridStateComposable.value.selectedNoteTag,
    displayedTagNotes: tagGridStateComposable.value.displayedTagNotes
  });
}

function onNoteTagDoubleClick(tagName) {
  onNoteTagDoubleClickComposable(tagName);
}

function updateNoteTagSortOrder(newOrder) {
  updateNoteTagSortOrderComposable(newOrder);
  updateTagGridState({ noteTagSortOrder: newOrder });
}

function updateTagSortOrder(newOrder) {
  updateTagSortOrderComposable(newOrder);
  updateTagGridState({ tagSortOrder: newOrder });
}

// Create empty note to get filename immediately
async function createEmptyNote() {
  const emptyTitle = newTitle.value || noteConstants.DEFAULT_TITLE;
  const emptyContent = note.value.content || "";
  const defaultTags = newTags.value;
  
  try {
    const data = await createEmptyNoteComposable({
      title: emptyTitle,
      content: emptyContent,
      tags: defaultTags,
      onStateUpdate: (updates) => {
        updateNoteState(updates);
      }
    });
    
    // Update newTags with server data (silently to avoid watch trigger)
    const serverTags = data.tags || [];
    if (newTags.value.length !== serverTags.length || 
        newTags.value.some((tag, index) => tag !== serverTags[index])) {
      newTags.value = serverTags;
    }
    
    // Update local state
    updateUIState({ unsavedChanges: false });
    
    // Phase 1: 既存機能の統一 - スクロール制御をコンポーザブルに移行
    setTimeout(() => {
      scrollToTop();
    }, 50);
  } catch (error) {
    console.error('Failed to create empty note:', error);
    apiErrorHandler(error);
  }
}

function handleEditorChange() {
  if (canModify.value && toastEditor.value) {
    // 自動保存タイムアウトを開始
    startContentChangedTimeout();

    const content = toastEditor.value.getMarkdown();
    if (generateTitleFromContent(content) !== note.value.title) {
      updateUIState({ unsavedChanges: true });
    }

    // Phase 1: 既存機能の統一 - タイトル生成をコンポーザブルに移行
    startTitleGeneration(content, (generatedTitle) => {
      if (generatedTitle && generatedTitle !== newTitle.value) {
        updateNoteState({ newTitle: generatedTitle });
      }
    });
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
    // Add .md extension for API call
    const filenameWithExtension = props.filename + noteConstants.MARKDOWN_EXTENSION;
    getNote(filenameWithExtension)
      .then((data) => {
        const isExistingNote = note.value.filename;
        updateNoteState({
          note: data,
          newTitle: data.title
        });
        // Initialize newTags separately
        newTags.value = data.tags || [];
        if (data.title && data.title.trim()) {
          document.title = `${data.title} - SBNote`;
          // Set current note title globally for NavBar component
          globalStore.currentNoteTitle = data.title;
        }
        if (!isExistingNote) {
          note.value.content = data.content;
        }
        loadingIndicator.value.setLoaded();
        updateFileMenuState();
        
        // Reset tag grid state when note changes
        updateTagGridState({
          selectedNoteTag: null,
          displayedTagNotes: []
        });
        
        // Phase 1: 既存機能の統一 - スクロール制御をコンポーザブルに移行
        scrollToTop();
      })
      .catch((error) => {
        console.error('Failed to load note:', error);
        if (error.response?.status === 404) {
          if (!globalStore.isAuthenticated) {
            // If not authenticated and getting 404, redirect to login
            router.push({
              name: "login",
              query: { [params.redirect]: route.fullPath },
            });
          } else {
            // If authenticated and getting 404, note doesn't exist
            loadingIndicator.value.setFailed("Note not found", FileX);
          }
        } else {
          loadingIndicator.value.setFailed();
          apiErrorHandler(error);
        }
      });
  } else {
    // Check if tag parameter is provided for new note
    const tagFromQuery = route.query.tag;
    const contentFromQuery = route.query[params.content];
    const initialTags = tagFromQuery ? [tagFromQuery] : [];
    
    updateNoteState({
      newTitle: "",
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
    updateTagGridState({
      selectedNoteTag: null,
      displayedTagNotes: []
    });
    
    // Immediately create empty note to get filename
    createEmptyNote();
    
    // Phase 1: 既存機能の統一 - スクロール制御をコンポーザブルに移行
    setTimeout(() => {
      scrollToTop();
    }, 100);
  }
}

function getInitialEditorValue() {
  // If this is a new note and we have content from query params, use it
  if (isNewNote.value && note.value.content) {
    return note.value.content;
  }
  
  // 編集中はエディターの現在の内容を優先（カーソル位置を保持するため）
  if (toastEditor.value && !isNewNote.value) {
    const currentContent = toastEditor.value.getMarkdown();
    // console.log('🔍 getInitialEditorValue: using editor content:', currentContent);
    return currentContent;
  }
  
  // console.log('🔍 getInitialEditorValue: using note content:', note.value.content);
  return note.value.content;
}

// Phase 1: 既存機能の統一 - generateTitleFromContentはuseNoteコンポーザブルで管理





// Note Deletion (for NavBar event)
function deleteHandler() {
  updateUIState({ isDeleteModalVisible: true });
}

// Copy Link (for NavBar event)
function copyLinkHandler() {
  // Get basename from filename
  const basename = props.filename.replace(/\.md$/, '');
  const url = `${window.location.origin}/${basename}`;
  
  // Copy to clipboard
  navigator.clipboard.writeText(url).then(() => {
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

async function deleteConfirmedHandler() {
  await deleteConfirmedHandlerComposable(props.filename);
}

async function changeNoteVisibility(visibility) {
  if (!canModify.value || isNewNote.value) {
    return;
  }
  
  try {
    await changeNoteVisibilityComposable({
      visibility,
      filename: props.filename,
      title: newTitle.value,
      content: note.value.content,
      tags: newTags.value,
      canModify: canModify.value,
      isNewNote: isNewNote.value
    });
    
    // Update file menu state to reflect new visibility
    updateFileMenuState();
    
    // Show success toast
    globalStore.toast?.addToast(
      `Note visibility changed to ${visibility}`,
      'Visibility Updated',
      'success'
    );
    
    // Reload tag counts to reflect changes
    await loadTagCountsComposable();
  } catch (error) {
    console.error('Failed to change note visibility:', error);
    apiErrorHandler(error);
  }
}





function handleSaveFailure(error) {
  if (error.response?.status === 413) {
    showFileSizeModal("note");
  } else {
    apiErrorHandler(error);
  }
}



function closeNote() {
  // Phase 1: 既存機能の統一 - クリーンアップはコンポーザブルに移行
  cleanupNote();
  if (isNewNote.value) {
    router.push({ name: "home" });
  }
}

// Image Upload
function addImageBlobHook(file, callback) {
  addImageBlobHookComposable(file, callback);
}

function postAttachment(file) {
  return postAttachmentComposable(file);
}

// Phase 1: 既存機能の統一 - タイムアウト管理はuseNoteコンポーザブルで管理

function onTagConfirmed() {
  // Only proceed if we can modify the note
  if (!canModify.value) {
    return
  }
  
  // Phase 1: 既存機能の統一 - タイムアウト管理はコンポーザブルに移行
  // Force save immediately for tag changes
  if (!autoSaveState.value.isAutoSaving) {
    performSave(false, true);
  }
}

// ✅ 修正: 保存処理を統合
async function saveNote(title, content, tags, close = false, isAuto = false) {
  try {
    const data = await saveNoteComposable(title, content, tags, {
      close,
      isAuto,
      isNewNote: isNewNote.value,
      filename: props.filename
    });
    
    // 共通の成功処理
    handleSaveSuccess(data, close, isAuto);
    
    return data;
  } catch (error) {
    console.error('Failed to save note:', error);
    handleSaveFailure(error);
    throw error;
  }
}

// ✅ 修正: 保存成功処理を共通化
async function handleSaveSuccess(data, close = false, isAuto = false) {

  
  // 編集中は note.content を更新しない（カーソル位置を保持するため）
  if (!isAuto) {
    // console.log('🔍 Manual save: updating note content');
    updateState('noteState', {
      note: data,
      isNewNote: false
    });
  } else {
    // console.log('🔍 Auto save: only updating isNewNote flag');
    // Only update isNewNote flag for auto-save
    updateState('noteState', {
      isNewNote: false
    });
  }
  
  // Update newTags with server data (silently to avoid watch trigger)
  const serverTags = data.tags || [];
  if (newTags.value.length !== serverTags.length || 
      newTags.value.some((tag, index) => tag !== serverTags[index])) {
    newTags.value = serverTags;
  }
  
  if (data.title && data.title.trim()) {
    document.title = `${data.title} - SBNote`;
    globalStore.currentNoteTitle = data.title;
  }
  
  // Update URL with filename (without extension) for new notes
  if (isNewNote.value && !isAuto) {
    const filename = data.filename.replace(noteConstants.MARKDOWN_EXTENSION, '');
    router.replace({ name: "note", params: { filename } });
  }
  
  updateState('uiState', { unsavedChanges: false });
  setBeforeUnloadConfirmation(false);
  
  // Reload tag counts to reflect changes
  await loadTagCounts();
  
  // if (isAuto) resetAutoSaveState(); // 現在はuseNoteコンポーザブルで管理
  if (close) closeNote();
}

// Unified save function
function performSave(close = false, isAuto = false) {
  saveDefaultEditorMode();
  ensureTitle();
  
  // ✅ 削除: 状態設定を削除（useNoteコンポーザブルで一元管理）
  // updateState('autoSaveState', { 
  //   isAutoSaving: true, 
  //   isAutoSavingInProgress: true 
  // });
  
  const newContent = toastEditor.value ? toastEditor.value.getMarkdown() : '';
  
  // ✅ 修正: 正しいsaveNoteComposableを使用
  return saveNoteComposable(newTitle.value, newContent, newTags.value, {
    close,
    isAuto,
    isNewNote: isNewNote.value,
    filename: props.filename
  });
}

// Phase 1: 既存機能の統一 - autoSaveHandlerはuseNoteコンポーザブルで管理

function ensureTitle() {
  if (!newTitle.value || newTitle.value.trim() === "") {
    const content = toastEditor.value ? toastEditor.value.getMarkdown() : '';
    newTitle.value = generateTitleFromContent(content);
    if (!newTitle.value || newTitle.value.trim() === "") {
      newTitle.value = noteConstants.DEFAULT_TITLE;
    }
  }
}





// Phase 1: 既存機能の統一 - resetAutoSaveStateはuseNoteコンポーザブルで管理

// ✅ 削除: 重複する保存関数はuseNoteコンポーザブルで統合済み

function showFileSizeModal(entityName) {
  fileSizeModalMessage.value = `The ${entityName} you're trying to upload is too large. Please choose a smaller file.`;
  updateUIState({ isFileSizeModalVisible: true });
}

function closeFileSizeModal() {
  updateUIState({ isFileSizeModalVisible: false });
}

// Toggle info section and save to localStorage
function toggleInfoSection() {
  toggleInfoSectionComposable();
  // 状態を更新
  updateUIState({ isInfoExpanded: isInfoExpandedComposable.value });
}

// Load info section state from localStorage
function loadInfoSectionState() {
  loadInfoSectionStateComposable();
  // 状態を更新
  updateUIState({ isInfoExpanded: isInfoExpandedComposable.value });
}

// setBeforeUnloadConfirmationはuseNoteコンポーザブルから取得済み

// Update file menu state in App.vue
function updateFileMenuState() {
  if (window.updateNoteFileMenuState) {
    const menuState = {
      canModify: canModify.value,
      isNewNote: isNewNote.value,
      autoSaveState: state.value.autoSaveState,
      unsavedChanges: state.value.uiState.unsavedChanges,
      currentVisibility: note.value.visibility || 'private'
    };
    window.updateNoteFileMenuState(menuState);
  }
  
  // Update current note tags globally for NavBar component
  const currentTags = canModify.value ? newTags.value : (note.value.tags || []);
  globalStore.currentNoteTags = currentTags;
  
  // Update current note category globally for NavBar component
  globalStore.currentNoteCategory = note.value.category || 'note';
}

function saveDefaultEditorMode() {
  saveDefaultEditorModeComposable(toastEditor.value);
}

function loadDefaultEditorMode() {
  return loadDefaultEditorModeComposable();
}

// Phase 1: 既存機能の統一 - scrollToTopはuseScrollControlコンポーザブルで管理

function isContentChanged() {
  if (autoSaveState.value.isAutoSavingInProgress) {
    return false;
  }
  
  // Optimize tag comparison by checking length first
  const currentTags = note.value.tags || [];
  const tagsChanged = newTags.value.length !== currentTags.length || 
    newTags.value.some((tag, index) => tag !== currentTags[index]);
  
  return (
    newTitle.value != note.value.title ||
    (toastEditor.value && toastEditor.value.getMarkdown() != note.value.content) ||
    tagsChanged
  );
}

// Phase 1: 既存機能の統一 - useNoteコンポーザブルを導入
const {
  // 自動保存・タイトル生成
  autoSaveState,
  startContentChangedTimeout,
  generateTitleFromContent,
  startTitleGeneration,
  resetAutoSaveState,
  updateIsNewNote,
  

  
  // ノート操作
  saveNote: saveNoteComposable,
  createEmptyNote: createEmptyNoteComposable,
  deleteConfirmedHandler: deleteConfirmedHandlerComposable,
  changeNoteVisibility: changeNoteVisibilityComposable,
  addImageBlobHook: addImageBlobHookComposable,
  postAttachment: postAttachmentComposable,
  setBeforeUnloadConfirmation,
  updateUnloadProtection,
  
  // UI状態管理
  editorMode,
  tagGridState: tagGridStateComposable,
  tagCountsState: tagCountsStateComposable,
  isInfoExpanded: isInfoExpandedComposable,
  saveDefaultEditorMode: saveDefaultEditorModeComposable,
  loadDefaultEditorMode: loadDefaultEditorModeComposable,
  loadTagCounts: loadTagCountsComposable,
  onNoteTagClick: onNoteTagClickComposable,
  onNoteTagDoubleClick: onNoteTagDoubleClickComposable,
  updateNoteTagSortOrder: updateNoteTagSortOrderComposable,
  updateTagSortOrder: updateTagSortOrderComposable,
  toggleInfoSection: toggleInfoSectionComposable,
  loadInfoSectionState: loadInfoSectionStateComposable,
  
  // 統合クリーンアップ
  cleanup: cleanupNote
} = useNote({
  // API関数
  createNote,
  updateNote,
  deleteNote,
  createAttachment,
  getNotesByTag,
  getTagsWithCounts,
  
  // 依存関係
  router,
  apiErrorHandler,
  
  // コールバック関数
  onSaveSuccess: handleSaveSuccess,
  onSaveFailure: handleSaveFailure,
  onDeleteSuccess: () => {
    // 削除成功時の処理は既存のdeleteConfirmedHandlerで処理
  },
  onDeleteFailure: (error) => {
    apiErrorHandler(error);
  },
  onGlobalStateUpdate: (updates) => {
    if (updates.currentNoteTitle) {
      globalStore.currentNoteTitle = updates.currentNoteTitle;
    }
    if (updates.currentNoteTags) {
      globalStore.currentNoteTags = updates.currentNoteTags;
    }
  },
  onFileSizeError: (error) => {
    showFileSizeModal("attachment");
  },
  onFileExistsError: (error) => {
    // ファイル重複エラーはサーバー側で処理
  },
  onNetworkError: (error) => {
    apiErrorHandler(error);
  },
  onTagClick: (tagName, previousSelectedTag) => {
    handleTagClick(tagName, selectedNoteTag.value, (tag) => updateTagGridState({ selectedNoteTag: tag }), () => updateTagGridState({ displayedTagNotes: [] }));
  },
  onTagDoubleClick: (tagName) => {
    handleTagDoubleClick(tagName, '/tag/');
  },
  onStateUpdate: (newState) => {
    updateState('autoSaveState', newState);
  },
  onContentChange: () => {
    return isContentChanged();
  },
  onAutoSave: async () => {
    await performSave(false, true);
  },
  onTitleGenerated: (title) => {
    if (title && title !== newTitle.value) {
      updateNoteState({ newTitle: title });
    }
  },
  isNewNote: () => isNewNote.value
});

// Unified watch for content changes
function handleContentChange(isTagsOnlyChange = false) {
  if (autoSaveState.value.isAutoSavingInProgress) {
    return;
  }
  
  if (isContentChanged()) {
    updateState('uiState', { unsavedChanges: true });
    setBeforeUnloadConfirmation(true);
    
    // 自動保存タイムアウトを開始
    startContentChangedTimeout();
  } else {
    updateState('uiState', { unsavedChanges: false });
    setBeforeUnloadConfirmation(false);
  }
}

watch([newTitle], () => {
  if (newTitle.value && newTitle.value.trim()) {
    document.title = `${newTitle.value} - SBNote`;
    globalStore.currentNoteTitle = newTitle.value;
  }
  handleContentChange();
}, { deep: true, immediate: true });

watch([newTags], async () => {
  // Check if this is a tags-only change
  const isTagsOnlyChange = (
    newTitle.value === note.value.title &&
    (toastEditor.value && toastEditor.value.getMarkdown() === note.value.content) &&
    newTags.value.length !== (note.value.tags || []).length
  );
  handleContentChange(isTagsOnlyChange);
  
  // Reset tag grid state when tags change
  if (selectedNoteTag.value) {
    updateTagGridState({
      selectedNoteTag: null,
      displayedTagNotes: []
    });
  }
  
  // Update tag counts when tags change (for immediate UI feedback)
  if (canModify.value) {
    await loadTagCounts();
  }
}, { deep: true });

watch(() => props.filename, async () => {
  if (toastEditor.value && toastEditor.value.getMarkdown() !== note.value.content) {
    updateUIState({ unsavedChanges: true });
  }
  await init();
});

// Watch for changes that affect file menu state
watch([canModify, isNewNote, () => state.value.autoSaveState, () => state.value.uiState.unsavedChanges], () => {
  updateFileMenuState();
}, { deep: true });

// Phase 1: 既存機能の統一 - isNewNoteの変更をコンポーザブルに通知
watch(isNewNote, (newValue) => {
  updateIsNewNote(newValue);
});

// Watch for edit mode changes to set preview style for view mode
watch(canModify, (newCanModify) => {
  // In view mode (canModify = false), always use single view (tab)
  if (!newCanModify) {
    globalStore.setPreviewStyle('tab');
  }
}, { immediate: true });

// Phase 1: 既存機能の統一 - スクロール制御をコンポーザブルに移行
// Watch for route changes to reset scroll position
watch(() => route.path, () => {
  // Reset scroll position when route changes
  setTimeout(() => {
    scrollToTop();
  }, 100);
}, { immediate: true });

onMounted(async () => {
  await init();
  
  // Load info section state from localStorage
  loadInfoSectionState();
  
  // Listen for file menu events from NavBar
  window.addEventListener('note-close', closeHandler);
  window.addEventListener('note-copy-link', copyLinkHandler);
  window.addEventListener('note-delete', deleteHandler);
  window.addEventListener('note-toggle-preview-style', togglePreviewStyleHandler);
  window.addEventListener('note-change-visibility', changeVisibilityHandler);
  
  // Update file menu state in App.vue
  updateFileMenuState();
  
  // Phase 1: 既存機能の統一 - スクロール制御をコンポーザブルに移行
  // Use setTimeout to ensure DOM is fully rendered
  setTimeout(() => {
    scrollToTop();
  }, 50);
});

onUnmounted(() => {
  // Clean up event listeners
  window.removeEventListener('note-close', closeHandler);
  window.removeEventListener('note-copy-link', copyLinkHandler);
  window.removeEventListener('note-delete', deleteHandler);
  window.removeEventListener('note-toggle-preview-style', togglePreviewStyleHandler);
  window.removeEventListener('note-change-visibility', changeVisibilityHandler);
  
  // Clean up ToastUIEditor IME event listeners（不要な変更 - コメントアウト）
  // if (toastEditor.value && toastEditor.value.cleanup) {
  //   toastEditor.value.cleanup();
  // }
});
</script>
