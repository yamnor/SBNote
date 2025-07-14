<template>
  <!-- Confirm Deletion Modal -->
  <ConfirmModal
    v-model="uiState.isDeleteModalVisible"
    title="Confirm Deletion"
    :message="`Are you sure you want to delete the note '${note.title}'?`"
    confirmButtonText="Delete"
    confirmButtonStyle="danger"
    @confirm="deleteConfirmedHandler"
  />

  <!-- File Size Limit Modal -->
  <ConfirmModal
    v-model="uiState.isFileSizeModalVisible"
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
          <div class="flex items-center justify-between p-1 border-b border-color-bg-base cursor-pointer hover:bg-color-bg-base transition-colors" @click="toggleInfoSection">
            <Info class="w-4 h-4 text-color-text-secondary" />
            <ChevronDown v-if="uiState.isInfoExpanded" class="w-4 h-4 text-color-text-secondary" />
            <ChevronRight v-else class="w-4 h-4 text-color-text-secondary" />
          </div>
          
          <!-- Collapsible content -->
          <div v-show="uiState.isInfoExpanded" class="text-xs text-color-text-secondary flex flex-col gap-1 p-1">
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
} from "../api.js";
import { Note } from "../classes.js";
import ConfirmModal from "../components/ConfirmModal.vue";

import Loading from "../components/Loading.vue";
import TagInput from "../components/TagInput.vue";
import ToastUIEditor from "../components/ToastUIEditor.vue";
import ToastUIEditorViewer from "../components/ToastUIEditorViewer.vue";
import SortDropdown from "../components/SortDropdown.vue";
import GridLayout from "../components/GridLayout.vue";

import { noteConstants, params } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";
import { useSorting } from "../composables/useSorting.js";
import { useGridData } from "../composables/useGridData.js";
import { useTagInteractions } from "../composables/useTagInteractions.js";
import { useDataFetching } from "../composables/useDataFetching.js";

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
let contentChangedTimeout = null;
let autoSaveTimeout = null;
let titleGenerationTimeout = null;
const loadingIndicator = ref();
const router = useRouter();
const toastEditor = ref();

// Composables
const { noteSortOptions, tagSortOptions, sortItems } = useSorting();
const { createNestedGridItems } = useGridData();
const { handleTagClick, handleTagDoubleClick } = useTagInteractions();
const { fetchNotesByTag } = useDataFetching();

// State management - grouped related states
const noteState = ref({
  note: {},
  newTitle: "",
  isNewNote: !props.filename
});

const uiState = ref({
  isDeleteModalVisible: false,
  isFileSizeModalVisible: false,
  unsavedChanges: false,
  isInfoExpanded: false
});

const autoSaveState = ref({
  isAutoSaving: false,
  isAutoSavingInProgress: false
});

// Tag grid state
const tagGridState = ref({
  selectedNoteTag: null,
  displayedTagNotes: [],
  noteTagSortBy: 'lastModified',
  noteTagSortOrder: 'desc',
  tagSortBy: 'name',
  tagSortOrder: 'asc'
});

// Tag counts state
const tagCountsState = ref({
  allTagsWithCounts: []
});

// Computed properties for easier access
const note = computed(() => noteState.value.note);
const newTitle = computed(() => noteState.value.newTitle);
const isNewNote = computed(() => noteState.value.isNewNote);

// Tag grid computed properties
const selectedNoteTag = computed(() => tagGridState.value.selectedNoteTag);
const displayedTagNotes = computed(() => tagGridState.value.displayedTagNotes);
const noteTagSortBy = computed(() => tagGridState.value.noteTagSortBy);
const noteTagSortOrder = computed(() => tagGridState.value.noteTagSortOrder);
const tagSortBy = computed(() => tagGridState.value.tagSortBy);
const tagSortOrder = computed(() => tagGridState.value.tagSortOrder);

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
  const allTagsWithCounts = tagCountsState.value.allTagsWithCounts;
  
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

// newTags is a ref for v-model compatibility
const newTags = ref([]);

// File size modal message
const fileSizeModalMessage = ref("");

// State update functions
function updateNoteState(updates) {
  Object.assign(noteState.value, updates);
}

function updateUIState(updates) {
  Object.assign(uiState.value, updates);
}

function updateAutoSaveState(updates) {
  Object.assign(autoSaveState.value, updates);
}

function updateTagGridState(updates) {
  Object.assign(tagGridState.value, updates);
}

function updateTagCountsState(updates) {
  Object.assign(tagCountsState.value, updates);
}

// Load tag counts
async function loadTagCounts() {
  try {
    const tagsWithCounts = await getTagsWithCounts();
    updateTagCountsState({ allTagsWithCounts: tagsWithCounts });
  } catch (error) {
    console.error('Failed to load tag counts:', error);
  }
}

// Tag grid event handlers
async function onNoteTagClick(tagName) {
  try {
    const previousSelectedTag = selectedNoteTag.value;
    
    handleTagClick(tagName, selectedNoteTag.value, (tag) => updateTagGridState({ selectedNoteTag: tag }), () => updateTagGridState({ displayedTagNotes: [] }));
    
    // Only fetch notes if a new tag was selected (not the same tag)
    if (selectedNoteTag.value === tagName && previousSelectedTag !== tagName) {
      // Get notes for the selected tag
      const notes = await fetchNotesByTag(getNotesByTag, tagName, noteTagSortBy.value, noteTagSortOrder.value, 10);
      updateTagGridState({ displayedTagNotes: notes });
    }
  } catch (error) {
    console.error('Failed to get notes for tag:', error);
  }
}

function onNoteTagDoubleClick(tagName) {
  handleTagDoubleClick(tagName, '/tag/');
}

function updateNoteTagSortOrder(newOrder) {
  updateTagGridState({ noteTagSortOrder: newOrder });
}

function updateTagSortOrder(newOrder) {
  updateTagGridState({ tagSortOrder: newOrder });
}

// Create empty note to get filename immediately
function createEmptyNote() {
  const emptyTitle = newTitle.value || noteConstants.DEFAULT_TITLE;
  const emptyContent = note.value.content || "";
  const defaultTags = newTags.value;
  
  createNote(emptyTitle, emptyContent, defaultTags)
    .then((data) => {
      // Update note with server data
      updateNoteState({
        note: {
          ...note.value,
          title: data.title,
          tags: data.tags,
          content: data.content,
          filename: data.filename
        },
        newTitle: data.title,
        isNewNote: false  // Mark as existing note after creation
      });
      
      // Update newTags with server data (silently to avoid watch trigger)
      const serverTags = data.tags || [];
      if (newTags.value.length !== serverTags.length || 
          newTags.value.some((tag, index) => tag !== serverTags[index])) {
        newTags.value = serverTags;
      }
      
      // Update browser tab title
      document.title = `${data.title} - SBNote`;
      
      // Update URL with filename (without extension)
      const filename = data.filename.replace(noteConstants.MARKDOWN_EXTENSION, '');
      router.replace({ name: "note", params: { filename } });
      
      // Update local state
      updateUIState({ unsavedChanges: false });
      setBeforeUnloadConfirmation(false);
    })
    .catch((error) => {
      console.error('Failed to create empty note:', error);
      apiErrorHandler(error);
    });
}

function handleEditorChange() {
  if (canModify.value) {
    startContentChangedTimeout();

    const content = toastEditor.value.getMarkdown();
    if (generateTitleFromContent(content) !== note.value.title) {
      updateUIState({ unsavedChanges: true });
    }

    // Auto-generate title from first line
    clearTimeout(titleGenerationTimeout);
    titleGenerationTimeout = setTimeout(() => {
      const content = toastEditor.value.getMarkdown();
      const generatedTitle = generateTitleFromContent(content);
      if (generatedTitle && generatedTitle !== newTitle.value) {
        updateNoteState({ newTitle: generatedTitle });
      }
    }, noteConstants.TITLE_GENERATION_DELAY);
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
  }
}

function getInitialEditorValue() {
  // If this is a new note and we have content from query params, use it
  if (isNewNote.value && note.value.content) {
    return note.value.content;
  }
  return note.value.content;
}

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
    // Remove headers (# ## ### etc.)
    .replace(noteConstants.MARKDOWN_PATTERNS.HEADERS, '')
    // Remove bold/italic markers
    .replace(noteConstants.MARKDOWN_PATTERNS.BOLD, '$1')
    .replace(noteConstants.MARKDOWN_PATTERNS.ITALIC, '$1')
    .replace(noteConstants.MARKDOWN_PATTERNS.BOLD_UNDERSCORE, '$1')
    .replace(noteConstants.MARKDOWN_PATTERNS.ITALIC_UNDERSCORE, '$1')
    // Remove code markers
    .replace(noteConstants.MARKDOWN_PATTERNS.CODE, '$1')
    // Remove links [text](url) -> text
    .replace(noteConstants.MARKDOWN_PATTERNS.LINKS, '$1')
    // Remove images ![alt](url) -> alt
    .replace(noteConstants.MARKDOWN_PATTERNS.IMAGES, '$1')
    // Remove HTML tags
    .replace(noteConstants.MARKDOWN_PATTERNS.HTML_TAGS, '')
    // Trim whitespace
    .trim();
  
  // Limit title length to reasonable size
  if (title.length > noteConstants.MAX_TITLE_LENGTH) {
    title = title.substring(0, noteConstants.TITLE_TRUNCATE_LENGTH) + '...';
  }
  
  return title;
}





// Note Deletion (for NavBar event)
function deleteHandler() {
  updateUIState({ isDeleteModalVisible: true });
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
  // Add .md extension for API call
  const filenameWithExtension = props.filename + noteConstants.MARKDOWN_EXTENSION;
  deleteNote(filenameWithExtension)
    .then(() => {
      router.push({ name: "home" });
    })
    .catch((error) => {
      apiErrorHandler(error);
    });
}

function changeNoteVisibility(visibility) {
  if (!canModify.value || isNewNote.value) {
    return;
  }
  
  // Add .md extension for API call
  const filenameWithExtension = props.filename + noteConstants.MARKDOWN_EXTENSION;
  
  // Update note with new visibility
  updateNote(filenameWithExtension, newTitle.value, note.value.content, newTags.value, visibility)
    .then(async (data) => {
      // Update note state
      updateNoteState({
        note: data
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
      await loadTagCounts();
    })
    .catch((error) => {
      console.error('Failed to change note visibility:', error);
      apiErrorHandler(error);
    });
}





function handleSaveFailure(error) {
  if (error.response?.status === 413) {
    showFileSizeModal("note");
  } else {
    apiErrorHandler(error);
  }
}



function closeNote() {
  clearAutoSaveTimeout();
  clearTitleGenerationTimeout();
  if (isNewNote.value) {
    router.push({ name: "home" });
  }
}

// Image Upload
function addImageBlobHook(file, callback) {
  postAttachment(file)
    .then((data) => {
      if (data) {
        // Use original filename as alt text for better accessibility
        const altText = data.originalFilename || data.filename;
        callback(data.url, altText);
      }
    })
    .catch((error) => {
      console.warn('Image upload failed, using local URL:', error);
      // Fallback to local URL if upload fails
      const url = URL.createObjectURL(file);
      callback(url, file.name);
    });
}

function postAttachment(file) {
  if (!file.name || file.name.trim() === "") {
    globalStore.toast?.addToast(
      "Invalid filename",
      "Invalid Attachment",
      "error"
    );
    return Promise.reject(new Error("Invalid filename"));
  }

  return createAttachment(file)
    .then((data) => {
      return data;
    })
    .catch((error) => {
      if (error.response?.status === 409) {
        // File already exists, will be handled by server
        return Promise.reject(error);
      } else if (error.response?.status === 413) {
        showFileSizeModal("attachment");
        return Promise.reject(error);
      } else {
        apiErrorHandler(error);
        return Promise.reject(error);
      }
    });
}

function startContentChangedTimeout() {
  clearContentChangedTimeout();
  contentChangedTimeout = setTimeout(contentChangedHandler, noteConstants.CONTENT_CHANGE_DELAY);
}

function clearContentChangedTimeout() {
  if (contentChangedTimeout != null) {
    clearTimeout(contentChangedTimeout);
  }
}

function contentChangedHandler() {
  if (autoSaveState.value.isAutoSavingInProgress) {
    return;
  }
  
  if (isContentChanged()) {
    updateUIState({ unsavedChanges: true });
    setBeforeUnloadConfirmation(true);
    const delay = isNewNote.value ? noteConstants.NEW_NOTE_AUTO_SAVE_DELAY : noteConstants.AUTO_SAVE_DELAY;
    startAutoSaveTimeout(delay);
  } else {
    updateUIState({ unsavedChanges: false });
    setBeforeUnloadConfirmation(false);
    clearAutoSaveTimeout();
  }
}

function startAutoSaveTimeout(delay = noteConstants.AUTO_SAVE_DELAY) {
  clearAutoSaveTimeout();
  autoSaveTimeout = setTimeout(autoSaveHandler, delay);
}

function clearAutoSaveTimeout() {
  if (autoSaveTimeout != null) {
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

function onTagConfirmed() {
  // Only proceed if we can modify the note
  if (!canModify.value) {
    return
  }
  
  // Clear any pending auto-save timeout
  if (autoSaveTimeout) {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = null;
  }
  
  // Force save immediately for tag changes
  if (!autoSaveState.value.isAutoSaving) {
    performSave(false, true);
  }
}

// Unified save function
function performSave(close = false, isAuto = false) {
  saveDefaultEditorMode();
  ensureTitle();
  
  updateAutoSaveState({ 
    isAutoSaving: true, 
    isAutoSavingInProgress: true 
  });
  
  const newContent = toastEditor.value.getMarkdown();
  if (isNewNote.value) {
    saveNewNote(newTitle.value, newContent, newTags.value, close, isAuto);
  } else {
    saveExistingNote(props.filename, newTitle.value, newContent, newTags.value, close, isAuto);
  }
}

function autoSaveHandler() {
  if (!isContentChanged()) {
    resetAutoSaveState();
    return;
  }
  performSave(false, true);
}

function ensureTitle() {
  if (!newTitle.value || newTitle.value.trim() === "") {
    const content = toastEditor.value.getMarkdown();
    newTitle.value = generateTitleFromContent(content);
    if (!newTitle.value || newTitle.value.trim() === "") {
      newTitle.value = noteConstants.DEFAULT_TITLE;
    }
  }
}





function resetAutoSaveState() {
  updateAutoSaveState({ 
    isAutoSaving: false, 
    isAutoSavingInProgress: false 
  });
}

function saveNewNote(title, content, tags, close = false, isAuto = false) {
  createNote(title, content, tags)
    .then(async (data) => {
      // For auto-save, don't update note object to preserve cursor position
      if (!isAuto) {
        updateNoteState({
          note: data,
          isNewNote: false  // Mark as existing note after creation
        });
      } else {
        // Only update isNewNote flag for auto-save
        updateNoteState({
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
      // Update URL with filename (without extension)
      const filename = data.filename.replace(noteConstants.MARKDOWN_EXTENSION, '');
      router.replace({ name: "note", params: { filename } });
      updateUIState({ unsavedChanges: false });
      setBeforeUnloadConfirmation(false);
      
      // Reload tag counts to reflect changes
      await loadTagCounts();
      
      if (isAuto) resetAutoSaveState();
      if (close) closeNote();
    })
    .catch((error) => {
      console.error('Failed to save new note:', error);
      if (isAuto) resetAutoSaveState();
      handleSaveFailure(error);
    });
}

function saveExistingNote(filename, title, content, tags, close = false, isAuto = false) {
  // Add .md extension for API call
  const filenameWithExtension = filename + noteConstants.MARKDOWN_EXTENSION;
  updateNote(filenameWithExtension, title, content, tags)
    .then(async (data) => {
      // For auto-save, don't update note object to preserve cursor position
      if (!isAuto) {
        updateNoteState({
          note: data
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
      updateUIState({ unsavedChanges: false });
      setBeforeUnloadConfirmation(false);
      
      // Reload tag counts to reflect changes
      await loadTagCounts();
      
      if (isAuto) resetAutoSaveState();
      if (close) closeNote();
    })
    .catch((error) => {
      console.error('Failed to save existing note:', error);
      if (isAuto) resetAutoSaveState();
      handleSaveFailure(error);
    });
}

function showFileSizeModal(entityName) {
  fileSizeModalMessage.value = `The ${entityName} you're trying to upload is too large. Please choose a smaller file.`;
  updateUIState({ isFileSizeModalVisible: true });
}

function closeFileSizeModal() {
  updateUIState({ isFileSizeModalVisible: false });
}

// Toggle info section and save to localStorage
function toggleInfoSection() {
  const newExpandedState = !uiState.value.isInfoExpanded;
  updateUIState({ isInfoExpanded: newExpandedState });
  localStorage.setItem('noteInfoExpanded', newExpandedState.toString());
}

// Load info section state from localStorage
function loadInfoSectionState() {
  const savedState = localStorage.getItem('noteInfoExpanded');
  if (savedState !== null) {
    updateUIState({ isInfoExpanded: savedState === 'true' });
  }
}

function setBeforeUnloadConfirmation(enable = true) {
  if (enable) {
    window.onbeforeunload = () => {
      return true;
    };
  } else {
    window.onbeforeunload = null;
  }
}

// Update file menu state in App.vue
function updateFileMenuState() {
  if (window.updateNoteFileMenuState) {
    window.updateNoteFileMenuState({
      canModify: canModify.value,
      isNewNote: isNewNote.value,
      autoSaveState: autoSaveState.value,
      unsavedChanges: uiState.value.unsavedChanges,
      currentVisibility: note.value.visibility || 'private'
    });
  }
  
  // Update current note tags globally for NavBar component
  const currentTags = canModify.value ? newTags.value : (note.value.tags || []);
  globalStore.currentNoteTags = currentTags;
  
  // Update current note category globally for NavBar component
  globalStore.currentNoteCategory = note.value.category || 'note';
}

function saveDefaultEditorMode() {
  if (toastEditor.value) {
    const isWysiwygMode = toastEditor.value.isWysiwygMode();
    localStorage.setItem(
      "defaultEditorMode",
      isWysiwygMode ? "wysiwyg" : "markdown",
    );
  }
}

function loadDefaultEditorMode() {
  const defaultWysiwygMode = localStorage.getItem("defaultEditorMode");
  return defaultWysiwygMode || "markdown";
}

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

// Unified watch for content changes
function handleContentChange(isTagsOnlyChange = false) {
  if (autoSaveState.value.isAutoSavingInProgress) {
    return;
  }
  
  if (isContentChanged()) {
    updateUIState({ unsavedChanges: true });
    setBeforeUnloadConfirmation(true);
    
    const delay = isTagsOnlyChange ? noteConstants.TAGS_ONLY_CHANGE_DELAY : noteConstants.AUTO_SAVE_DELAY;
    
    if (autoSaveTimeout) {
      clearTimeout(autoSaveTimeout);
    }
    autoSaveTimeout = setTimeout(() => {
      if (uiState.value.unsavedChanges && !autoSaveState.value.isAutoSaving) {
        autoSaveHandler();
      }
    }, delay);
  } else {
    updateUIState({ unsavedChanges: false });
    setBeforeUnloadConfirmation(false);
    clearAutoSaveTimeout();
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
watch([canModify, isNewNote, autoSaveState, () => uiState.value.unsavedChanges], () => {
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
});

onUnmounted(() => {
  // Clean up event listeners
  window.removeEventListener('note-close', closeHandler);
  window.removeEventListener('note-copy-link', copyLinkHandler);
  window.removeEventListener('note-delete', deleteHandler);
  window.removeEventListener('note-toggle-preview-style', togglePreviewStyleHandler);
  window.removeEventListener('note-change-visibility', changeVisibilityHandler);
});
</script>
