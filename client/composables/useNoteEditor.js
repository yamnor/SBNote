import { ref, computed } from 'vue';
import { noteConstants } from '../lib/constants.js';

export function useNoteEditor() {
  const toastEditor = ref();
  const newTitle = ref('');
  const newTags = ref([]);

  // Generate title from content
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

  // Ensure title exists
  function ensureTitle() {
    if (!newTitle.value || newTitle.value.trim() === "") {
      const content = toastEditor.value.getMarkdown();
      newTitle.value = generateTitleFromContent(content);
      if (!newTitle.value || newTitle.value.trim() === "") {
        newTitle.value = noteConstants.DEFAULT_TITLE;
      }
    }
  }

  // Save default editor mode
  function saveDefaultEditorMode() {
    if (toastEditor.value) {
      const isWysiwygMode = toastEditor.value.isWysiwygMode();
      localStorage.setItem(
        "defaultEditorMode",
        isWysiwygMode ? "wysiwyg" : "markdown",
      );
    }
  }

  // Load default editor mode
  function loadDefaultEditorMode() {
    const defaultWysiwygMode = localStorage.getItem("defaultEditorMode");
    return defaultWysiwygMode || "markdown";
  }

  // Get initial editor value
  function getInitialEditorValue(note, isNewNote) {
    // If this is a new note and we have content from query params, use it
    if (isNewNote && note.content) {
      return note.content;
    }
    return note.content;
  }

  return {
    toastEditor,
    newTitle,
    newTags,
    generateTitleFromContent,
    ensureTitle,
    saveDefaultEditorMode,
    loadDefaultEditorMode,
    getInitialEditorValue
  };
} 