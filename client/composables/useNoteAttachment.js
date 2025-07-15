import { ref } from 'vue';
import { getNote } from '../lib/api.js';

export function useNoteAttachment() {
  const noteData = ref(null);
  const isLoading = ref(false);
  const error = ref(null);

  /**
   * Load note data and get attachment filename
   * @param {string} basename - The basename without extension
   * @returns {Promise<{noteData: Object, attachmentFilename: string}>}
   */
  async function loadNoteDataAndAttachment(basename) {
    try {
      isLoading.value = true;
      error.value = null;

      // Add .md extension to get note data
      const filenameWithExtension = basename + '.md';
      
      // Get note data to extract title and attachment extension
      const note = await getNote(filenameWithExtension);
      noteData.value = note;
      
      // Generate attachment filename with extension from note data
      const attachmentFilename = getAttachmentFilename(basename, note.attachment_extension, note.category);
      
      return { noteData: note, attachmentFilename };
    } catch (err) {
      console.error('Failed to load note data:', err);
      error.value = err.message || 'Failed to load note data';
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Generate attachment filename with extension from note data
   * @param {string} basename - The basename without extension
   * @param {string} attachmentExtension - The attachment extension from note data
   * @param {string} category - The category from note data (optional)
   * @returns {string} The complete attachment filename
   */
  function getAttachmentFilename(basename, attachmentExtension, category = null) {
    // For new directory structure, construct the path based on category
    if (category) {
      let extension = attachmentExtension;
      if (category === 'output') {
        extension = 'txt';
      } else if (!extension) {
        // Fallback for coordinate and image
        extension = category === 'coordinate' ? 'xyz' : 'png';
      }
      return `${basename}/${category}.${extension}`;
    }
    
    // Fallback to old structure
    if (attachmentExtension) {
      return `${basename}.${attachmentExtension}`;
    }
    // Fallback to .xyz if no extension is found
    return `${basename}.xyz`;
  }

  /**
   * Load note data only (without attachment filename generation)
   * @param {string} basename - The basename without extension
   * @returns {Promise<Object>} The note data
   */
  async function loadNoteData(basename) {
    try {
      isLoading.value = true;
      error.value = null;

      // Add .md extension to get note data
      const filenameWithExtension = basename + '.md';
      
      // Get note data to extract title and attachment extension
      const note = await getNote(filenameWithExtension);
      noteData.value = note;
      
      return note;
    } catch (err) {
      console.error('Failed to load note data:', err);
      error.value = err.message || 'Failed to load note data';
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    noteData,
    isLoading,
    error,
    loadNoteDataAndAttachment,
    getAttachmentFilename,
    loadNoteData
  };
} 