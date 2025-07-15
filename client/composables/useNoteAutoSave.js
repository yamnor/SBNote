import { ref, watch } from 'vue';
import { noteConstants } from '../lib/constants.js';

export function useNoteAutoSave() {
  let contentChangedTimeout = null;
  let autoSaveTimeout = null;
  let titleGenerationTimeout = null;

  const autoSaveState = ref({
    isAutoSaving: false,
    isAutoSavingInProgress: false
  });

  const uiState = ref({
    unsavedChanges: false
  });

  // Set beforeunload confirmation
  function setBeforeUnloadConfirmation(enable = true) {
    if (enable) {
      window.onbeforeunload = () => {
        return true;
      };
    } else {
      window.onbeforeunload = null;
    }
  }

  // Start content changed timeout
  function startContentChangedTimeout() {
    clearContentChangedTimeout();
    contentChangedTimeout = setTimeout(contentChangedHandler, noteConstants.CONTENT_CHANGE_DELAY);
  }

  // Clear content changed timeout
  function clearContentChangedTimeout() {
    if (contentChangedTimeout != null) {
      clearTimeout(contentChangedTimeout);
    }
  }

  // Start auto save timeout
  function startAutoSaveTimeout(delay = noteConstants.AUTO_SAVE_DELAY) {
    clearAutoSaveTimeout();
    autoSaveTimeout = setTimeout(() => {
      // This will be handled by the main component
    }, delay);
  }

  // Clear auto save timeout
  function clearAutoSaveTimeout() {
    if (autoSaveTimeout != null) {
      clearTimeout(autoSaveTimeout);
      autoSaveTimeout = null;
    }
  }

  // Clear title generation timeout
  function clearTitleGenerationTimeout() {
    if (titleGenerationTimeout) {
      clearTimeout(titleGenerationTimeout);
      titleGenerationTimeout = null;
    }
  }

  // Reset auto save state
  function resetAutoSaveState() {
    autoSaveState.value = { 
      isAutoSaving: false, 
      isAutoSavingInProgress: false 
    };
  }

  // Content changed handler
  function contentChangedHandler() {
    if (autoSaveState.value.isAutoSavingInProgress) {
      return;
    }
    
    // This function will be called from the main component
    // The actual logic is handled in the main component
  }

  // Auto save handler
  function autoSaveHandler() {
    // This function will be called from the main component
    // The actual logic is handled in the main component
  }

  // Handle content change
  function handleContentChange(isTagsOnlyChange = false) {
    if (autoSaveState.value.isAutoSavingInProgress) {
      return;
    }
    
    if (isContentChanged()) {
      uiState.value.unsavedChanges = true;
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
      uiState.value.unsavedChanges = false;
      setBeforeUnloadConfirmation(false);
      clearAutoSaveTimeout();
    }
  }

  // Handle editor change
  function handleEditorChange(generateTitleFromContent, newTitle, note) {
    startContentChangedTimeout();

    // Auto-generate title from first line
    clearTimeout(titleGenerationTimeout);
    titleGenerationTimeout = setTimeout(() => {
      // This will be handled in the main component
    }, noteConstants.TITLE_GENERATION_DELAY);
  }

  // Check if content is changed
  function isContentChanged(newTitle, note, newTags, toastEditor) {
    if (autoSaveState.value.isAutoSavingInProgress) {
      return false;
    }
    
    // Optimize tag comparison by checking length first
    const currentTags = note.tags || [];
    const tagsChanged = newTags.length !== currentTags.length || 
      newTags.some((tag, index) => tag !== currentTags[index]);
    
    return (
      newTitle != note.title ||
      (toastEditor && toastEditor.getMarkdown() != note.content) ||
      tagsChanged
    );
  }

  // Clean up timeouts
  function cleanup() {
    clearContentChangedTimeout();
    clearAutoSaveTimeout();
    clearTitleGenerationTimeout();
    setBeforeUnloadConfirmation(false);
  }

  return {
    autoSaveState,
    uiState,
    setBeforeUnloadConfirmation,
    startContentChangedTimeout,
    clearContentChangedTimeout,
    startAutoSaveTimeout,
    clearAutoSaveTimeout,
    clearTitleGenerationTimeout,
    resetAutoSaveState,
    contentChangedHandler,
    autoSaveHandler,
    handleContentChange,
    handleEditorChange,
    isContentChanged,
    cleanup
  };
} 