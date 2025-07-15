import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { 
  createNote, 
  updateNote, 
  deleteNote, 
  getNote, 
  createAttachment,
  apiErrorHandler 
} from '../lib/api.js';
import { noteConstants } from '../lib/constants.js';
import { useGlobalStore } from '../lib/globalStore.js';

export function useNoteFileOperations() {
  const router = useRouter();
  const globalStore = useGlobalStore();
  
  const fileSizeModalMessage = ref("");
  const uiState = ref({
    isDeleteModalVisible: false,
    isFileSizeModalVisible: false
  });

  // Create empty note
  function createEmptyNote(newTitle, note, newTags, updateNoteState, updateUIState) {
    const emptyTitle = newTitle || noteConstants.DEFAULT_TITLE;
    const emptyContent = note.content || "";
    const defaultTags = newTags;
    
    return createNote(emptyTitle, emptyContent, defaultTags)
      .then((data) => {
        // Update note with server data
        updateNoteState({
          note: {
            ...note,
            title: data.title,
            tags: data.tags,
            content: data.content,
            filename: data.filename
          },
          newTitle: data.title,
          isNewNote: false  // Mark as existing note after creation
        });
        
        // Update browser tab title
        document.title = `${data.title} - SBNote`;
        
        // Update URL with filename (without extension)
        const filename = data.filename.replace(noteConstants.MARKDOWN_EXTENSION, '');
        router.replace({ name: "note", params: { filename } });
        
        // Update local state
        updateUIState({ unsavedChanges: false });
        
        return data;
      })
      .catch((error) => {
        console.error('Failed to create empty note:', error);
        apiErrorHandler(error);
        throw error;
      });
  }

  // Save new note
  function saveNewNote(title, content, tags, close = false, isAuto = false, updateNoteState, updateUIState, resetAutoSaveState, closeNote) {
    return createNote(title, content, tags)
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
        
        if (data.title && data.title.trim()) {
          document.title = `${data.title} - SBNote`;
          globalStore.currentNoteTitle = data.title;
        }
        
        // Update URL with filename (without extension)
        const filename = data.filename.replace(noteConstants.MARKDOWN_EXTENSION, '');
        router.replace({ name: "note", params: { filename } });
        updateUIState({ unsavedChanges: false });
        
        if (isAuto) resetAutoSaveState();
        if (close) closeNote();
        
        return data;
      })
      .catch((error) => {
        console.error('Failed to save new note:', error);
        if (isAuto) resetAutoSaveState();
        handleSaveFailure(error);
        throw error;
      });
  }

  // Save existing note
  function saveExistingNote(filename, title, content, tags, close = false, isAuto = false, updateNoteState, updateUIState, resetAutoSaveState, closeNote) {
    // Add .md extension for API call
    const filenameWithExtension = filename + noteConstants.MARKDOWN_EXTENSION;
    
    return updateNote(filenameWithExtension, title, content, tags)
      .then(async (data) => {
        // For auto-save, don't update note object to preserve cursor position
        if (!isAuto) {
          updateNoteState({
            note: data
          });
        }
        
        if (data.title && data.title.trim()) {
          document.title = `${data.title} - SBNote`;
          globalStore.currentNoteTitle = data.title;
        }
        updateUIState({ unsavedChanges: false });
        
        if (isAuto) resetAutoSaveState();
        if (close) closeNote();
        
        return data;
      })
      .catch((error) => {
        console.error('Failed to save existing note:', error);
        if (isAuto) resetAutoSaveState();
        handleSaveFailure(error);
        throw error;
      });
  }

  // Delete note
  function deleteNoteHandler(filename, updateUIState) {
    // Add .md extension for API call
    const filenameWithExtension = filename + noteConstants.MARKDOWN_EXTENSION;
    
    return deleteNote(filenameWithExtension)
      .then(() => {
        router.push({ name: "home" });
      })
      .catch((error) => {
        apiErrorHandler(error);
        throw error;
      });
  }

  // Load note
  function loadNote(filename, updateNoteState, updateUIState, updateTagGridState, loadingIndicator) {
    // Add .md extension for API call
    const filenameWithExtension = filename + noteConstants.MARKDOWN_EXTENSION;
    
    return getNote(filenameWithExtension)
      .then((data) => {
        const isExistingNote = false; // This should be passed as parameter
        updateNoteState({
          note: data,
          newTitle: data.title
        });
        
        if (data.title && data.title.trim()) {
          document.title = `${data.title} - SBNote`;
          // Set current note title globally for NavBar component
          globalStore.currentNoteTitle = data.title;
        }
        
        if (!isExistingNote) {
          data.content = data.content;
        }
        
        loadingIndicator.setLoaded();
        
        // Reset tag grid state when note changes
        updateTagGridState({
          selectedNoteTag: null,
          displayedTagNotes: []
        });
        
        return data;
      })
      .catch((error) => {
        console.error('Failed to load note:', error);
        if (error.response?.status === 404) {
          if (!globalStore.isAuthenticated) {
            // If not authenticated and getting 404, redirect to login
            router.push({
              name: "login",
              query: { redirect: router.currentRoute.value.fullPath },
            });
          } else {
            // If authenticated and getting 404, note doesn't exist
            loadingIndicator.setFailed("Note not found");
          }
        } else {
          loadingIndicator.setFailed();
          apiErrorHandler(error);
        }
        throw error;
      });
  }

  // Change note visibility
  function changeNoteVisibility(visibility, filename, newTitle, note, newTags, updateNoteState, updateFileMenuState) {
    if (!filename) {
      return Promise.reject(new Error('No filename provided'));
    }
    
    // Add .md extension for API call
    const filenameWithExtension = filename + noteConstants.MARKDOWN_EXTENSION;
    
    // Update note with new visibility
    return updateNote(filenameWithExtension, newTitle, note.content, newTags, visibility)
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
        
        return data;
      })
      .catch((error) => {
        console.error('Failed to change note visibility:', error);
        apiErrorHandler(error);
        throw error;
      });
  }

  // Image upload
  function addImageBlobHook(file, callback) {
    return postAttachment(file)
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

  // Post attachment
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

  // Handle save failure
  function handleSaveFailure(error) {
    if (error.response?.status === 413) {
      showFileSizeModal("note");
    } else {
      apiErrorHandler(error);
    }
  }

  // Show file size modal
  function showFileSizeModal(entityName) {
    fileSizeModalMessage.value = `The ${entityName} you're trying to upload is too large. Please choose a smaller file.`;
    uiState.value.isFileSizeModalVisible = true;
  }

  // Close file size modal
  function closeFileSizeModal() {
    uiState.value.isFileSizeModalVisible = false;
  }

  return {
    fileSizeModalMessage,
    uiState,
    createEmptyNote,
    saveNewNote,
    saveExistingNote,
    deleteNoteHandler,
    loadNote,
    changeNoteVisibility,
    addImageBlobHook,
    postAttachment,
    handleSaveFailure,
    showFileSizeModal,
    closeFileSizeModal
  };
} 