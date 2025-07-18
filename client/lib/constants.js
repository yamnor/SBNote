// Params
export const params = {
  searchTerm: "term",
  redirect: "redirect",
  showHighlights: "showHighlights",
  sortBy: "sortBy",
  title: "title",
  content: "content",
};

export const searchSortOptions = {
  score: 0,
  title: 1,
  lastModified: 2,
};

export const authTypes = {
  none: "none",
  readOnly: "read_only",
  password: "password",
  totp: "totp",
};

// Note editing constants
export const noteConstants = {
  // Timeouts (in milliseconds)
  CONTENT_CHANGE_DELAY: 1000,
  TITLE_GENERATION_DELAY: 500,
  AUTO_SAVE_DELAY: 1000,
  NEW_NOTE_AUTO_SAVE_DELAY: 500,
  TAGS_ONLY_CHANGE_DELAY: 5000,
  
  // Title and content limits
  MAX_TITLE_LENGTH: 100,
  TITLE_TRUNCATE_LENGTH: 97,
  
  // Default values
  DEFAULT_TITLE: "Empty Note",
  DEFAULT_TAG: "_untagged",
  
    // File extensions
  MARKDOWN_EXTENSION: ".md",
  
  // Auto-save indicator minimum display time
  AUTO_SAVE_INDICATOR_MIN_DISPLAY: 300,
  
  // Markdown formatting regex patterns
  MARKDOWN_PATTERNS: {
    HEADERS: /^#{1,6}\s+/,
    BOLD: /\*\*(.*?)\*\*/g,
    ITALIC: /\*(.*?)\*/g,
    BOLD_UNDERSCORE: /__(.*?)__/g,
    ITALIC_UNDERSCORE: /_(.*?)_/g,
    CODE: /`(.*?)`/g,
    LINKS: /\[([^\]]+)\]\([^)]+\)/g,
    IMAGES: /!\[([^\]]*)\]\([^)]+\)/g,
    HTML_TAGS: /<[^>]*>/g,
  }
};



// Home constants
export const homeConstants = {
  // Number of note titles to display in tag cards
  TAG_CARD_TITLE_COUNT: 3,
};
