<template>
  <Loading
    ref="loadingIndicator"
    class="mx-auto flex h-full flex-col px-2 pt-2 pb-0 print:max-w-full"
  >
    <div class="mx-auto w-full overflow-visible" :style="navBarContainerStyle">
      <NavBar
        v-if="showNavBar"
        ref="navBar"
        :class="{ 'print:hidden': route.name == 'note' }"
        :hide-logo="!showNavBarLogo"
        :incrementalSearchResults="incrementalSearchResults"
        :incrementalSearchTerm="incrementalSearchTerm"
        @incrementalSearch="onIncrementalSearch"
        @selectResult="selectSearchResult"
        @closeResults="closeIncrementalSearch"
        @confirmSelection="confirmSearchResult"
        @clearSearch="clearIncrementalSearch"
        :showFileMenu="route.name === 'note'"
        :canModify="noteFileMenuState.canModify"
        :isNewNote="noteFileMenuState.isNewNote"
        :autoSaveState="noteFileMenuState.autoSaveState"
        :unsavedChanges="noteFileMenuState.unsavedChanges"
        :currentVisibility="noteFileMenuState.currentVisibility"
        @closeNote="onCloseNote"
        @copyLink="onCopyLink"
        @deleteNote="onDeleteNote"
        @togglePreviewStyle="onTogglePreviewStyle"
        @changeVisibility="onChangeVisibility"
        :selectedTag="homeSelectedTag"
        @renameTag="onRenameTag"
        @deleteTag="onDeleteTag"
      />
    </div>
    <RouterView />
    <Toast ref="toast" />
  </Loading>
</template>

<script setup>

import { computed, ref, watch, nextTick, onMounted, onUnmounted } from "vue";
import { RouterView, useRoute } from "vue-router";

import { apiErrorHandler, getConfig, getNotes, getAuthStatus } from "./api.js";
import { useGlobalStore } from "./globalStore.js";
import NavBar from "./components/NavBar.vue";
import { loadStoredToken, getStoredToken, clearStoredToken } from "./tokenStorage.js";
import Loading from "./components/Loading.vue";
import Toast from "./components/Toast.vue";
import router from "./router.js";

const globalStore = useGlobalStore();
const loadingIndicator = ref();
const navBar = ref();
const toast = ref();
const route = useRoute();

// Set toast in global store
watch(toast, (newToast) => {
  if (newToast) {
    globalStore.toast = newToast;
  }
});

// Incremental search state
const incrementalSearchTerm = ref("");
const incrementalSearchResults = ref([]);
let incrementalSearchTimeout = null;

// File menu state for Note view
const noteFileMenuState = ref({
  canModify: false,
  isNewNote: false,
  autoSaveState: { isAutoSaving: false },
  unsavedChanges: false,
  currentVisibility: 'private'
});

// Home view state
const homeSelectedTag = ref(null);

// Global keyboard shortcuts
let globalKeydownHandler = null;

function setupKeyboardShortcuts() {
  // Focus search input when any character key is pressed (except when editing)
  globalKeydownHandler = (event) => {
    // Don't trigger search focus on login page
    if (route.name === 'login') {
      return;
    }
    
    // Check if we're on a note page and if the editor is focused
    if (route.name === 'note') {
      // Check if any input or textarea is focused
      const activeElement = document.activeElement;
      const isEditing = activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.contentEditable === 'true' ||
        activeElement.closest('.toastui-editor-contents') ||
        activeElement.closest('.toastui-editor-md-container')
      );
      
      if (isEditing) {
        return; // Don't trigger search focus when editing
      }
    }
    
    // Check if search input is already focused
    const activeElement = document.activeElement;
    const isSearchInputFocused = activeElement && (
      activeElement.closest('.search-input') ||
      activeElement.tagName === 'INPUT' && activeElement.type === 'text'
    );
    
    if (isSearchInputFocused) {
      return; // Don't trigger search focus when search input is already focused
    }
    
    // Check if the pressed key is a printable character
    const key = event.key;
    const isPrintableChar = key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey;
    
    if (isPrintableChar) {
      // Prevent default behavior to avoid double input
      event.preventDefault();
      // Focus search input and set the character
      if (navBar.value && navBar.value.focusSearchInput) {
        navBar.value.focusSearchInput(key);
      }
    }
  };
  
  document.addEventListener('keydown', globalKeydownHandler);
}

function cleanupKeyboardShortcuts() {
  // Remove the event listener when component is unmounted
  if (globalKeydownHandler) {
    document.removeEventListener('keydown', globalKeydownHandler);
    globalKeydownHandler = null;
  }
}

// Load stored token first before checking authentication
loadStoredToken();

// Initialize authentication
async function initializeAuth() {
  try {
    const data = await getConfig();
    globalStore.config = data;
    
    // Check authentication status if auth is enabled
    if (data.authType !== 'none' && data.authType !== 'read_only') {
      const authData = await getAuthStatus();
      globalStore.isAuthenticated = authData.authenticated;
      
      // If authentication failed but we have a stored token, clear it
      if (!authData.authenticated) {
        if (getStoredToken()) {
          clearStoredToken();
        }
      }
    } else {
      // For 'none' and 'read_only' modes, set authenticated based on auth type
      // In 'read_only' mode, we want to show the editor but in read-only mode
      globalStore.isAuthenticated = data.authType === 'none' || data.authType === 'read_only';
    }
    
    // Layout width initialization is now handled in globalStore
    
    loadingIndicator.value.setLoaded();
  } catch (error) {
    apiErrorHandler(error);
    loadingIndicator.value.setFailed();
  }
}

initializeAuth();

const showNavBar = computed(() => {
  return route.name !== "login";
});

const showNavBarLogo = computed(() => {
  return route.name !== "home";
});

// NavBar container style - always use note width for consistency
const navBarContainerStyle = computed(() => {
  return {
    maxWidth: 'var(--layout-width-note)'
  };
});

// Incremental search functions
function onIncrementalSearch(searchTerm) {
  incrementalSearchTerm.value = searchTerm;
  
  // Clear previous timeout
  if (incrementalSearchTimeout) {
    clearTimeout(incrementalSearchTimeout);
  }
  
  // Minimal debounce for search requests
  incrementalSearchTimeout = setTimeout(() => {
    if (searchTerm && searchTerm.length >= 1) {
      performIncrementalSearch(searchTerm);
    } else {
      incrementalSearchResults.value = [];
    }
  }, 100);
}

function performIncrementalSearch(searchTerm) {
  getNotes(searchTerm)
    .then((data) => {
      incrementalSearchResults.value = data.slice(0, 10); // Limit to 10 results
    })
    .catch((error) => {
      console.error('Incremental search failed:', error);
      incrementalSearchResults.value = [];
    });
}

function selectSearchResult(index) {
  // This function is no longer needed as selection is handled in SearchInput component
}

function confirmSearchResult(result) {
  // This function is no longer needed as selection is handled in SearchInput component
}

function closeIncrementalSearch() {
  incrementalSearchTerm.value = "";
  incrementalSearchResults.value = [];
  if (incrementalSearchTimeout) {
    clearTimeout(incrementalSearchTimeout);
    incrementalSearchTimeout = null;
  }
}

function clearIncrementalSearch() {
  incrementalSearchTerm.value = "";
  incrementalSearchResults.value = [];
  if (incrementalSearchTimeout) {
    clearTimeout(incrementalSearchTimeout);
    incrementalSearchTimeout = null;
  }
}

// File menu event handlers for Note view
function onCloseNote() {
  // Emit event to Note view
  window.dispatchEvent(new CustomEvent('note-close'));
}

function onCopyLink() {
  // Emit event to Note view
  window.dispatchEvent(new CustomEvent('note-copy-link'));
}

function onDeleteNote() {
  // Emit event to Note view
  window.dispatchEvent(new CustomEvent('note-delete'));
}

function onTogglePreviewStyle(newStyle) {
  // Emit event to Note view
  window.dispatchEvent(new CustomEvent('note-toggle-preview-style', { detail: newStyle }));
}

function onChangeVisibility(visibility) {
  // Emit event to Note view
  window.dispatchEvent(new CustomEvent('note-change-visibility', { detail: visibility }));
}

// Tag edit event handlers
function onRenameTag(tagName) {
  // Emit event to Home view
  window.dispatchEvent(new CustomEvent('tag-rename', { detail: tagName }));
}

function onDeleteTag(tagName) {
  // Emit event to Home view
  window.dispatchEvent(new CustomEvent('tag-delete', { detail: tagName }));
}

// Function to update file menu state from Note view
function updateNoteFileMenuState(state) {
  Object.assign(noteFileMenuState.value, state);
}

// Function to update home selected tag from Home view
function updateHomeSelectedTag(tagName) {
  homeSelectedTag.value = tagName;
}

// Expose the update functions globally
window.updateNoteFileMenuState = updateNoteFileMenuState;
window.updateHomeSelectedTag = updateHomeSelectedTag;

// Setup keyboard shortcuts when component is mounted
onMounted(() => {
  setupKeyboardShortcuts();
});

// Cleanup keyboard shortcuts when component is unmounted
onUnmounted(() => {
  cleanupKeyboardShortcuts();
});
</script>
