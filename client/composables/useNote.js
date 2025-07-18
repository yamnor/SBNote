import { ref, readonly, onUnmounted } from 'vue';
import { noteConstants } from '../lib/constants.js';

/**
 * ノート機能の統合コンポーザブル
 * Note.vueとQuickNoteModal.vueで共通のノート関連機能を提供します
 * 
 * 統合機能:
 * - 自動保存管理
 * - タイトル生成
 * - タイムアウト管理
 * - ノート操作（保存、新規作成、削除、可視性変更）
 * - ファイル操作
 * - ページ離脱保護
 * - UI状態管理（エディターモード、タググリッド、ノート情報）
 */
export function useNote(options = {}) {
  const {
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
    
    // 自動保存設定
    autoSaveDelay = noteConstants.AUTO_SAVE_DELAY,
    contentChangedDelay = noteConstants.CONTENT_CHANGE_DELAY,
    newNoteAutoSaveDelay = noteConstants.NEW_NOTE_AUTO_SAVE_DELAY,
    tagsOnlyChangeDelay = noteConstants.TAGS_ONLY_CHANGE_DELAY,
    
    // タイトル生成設定
    titleGenerationDelay = noteConstants.TITLE_GENERATION_DELAY,
    maxTitleLength = noteConstants.MAX_TITLE_LENGTH,
    titleTruncateLength = noteConstants.TITLE_TRUNCATE_LENGTH,
    defaultTitle = noteConstants.DEFAULT_TITLE,
    
    // コールバック関数
    onSaveSuccess,
    onSaveFailure,
    onDeleteSuccess,
    onDeleteFailure,
    onGlobalStateUpdate,
    onFileSizeError,
    onFileExistsError,
    onNetworkError,
    onTagClick,
    onTagDoubleClick,
    onStateUpdate,
    onContentChange,
    onAutoSave,
    onTitleGenerated,
    isNewNote = () => false
  } = options;

  // 内部状態管理
  const autoSaveState = ref({ isAutoSaving: false, isAutoSavingInProgress: false });
  const editorMode = ref('markdown');
  const isInfoExpanded = ref(false);
  

  const tagGridState = ref({
    selectedNoteTag: null,
    displayedTagNotes: [],
    noteTagSortBy: 'lastModified',
    noteTagSortOrder: 'desc',
    tagSortBy: 'name',
    tagSortOrder: 'asc'
  });
  const tagCountsState = ref({
    allTagsWithCounts: []
  });
  const timeouts = new Map();
  const isUnloadProtected = ref(false);
  let currentIsNewNote = isNewNote();

  // タイムアウト管理機能
  const setTimeout = (name, callback, delay) => {
    clearTimeout(name);
    timeouts.set(name, window.setTimeout(callback, delay));
  };

  const clearTimeout = (name) => {
    const timeoutId = timeouts.get(name);
    if (timeoutId) {
      window.clearTimeout(timeoutId);
      timeouts.delete(name);
    }
  };

  // 自動保存・タイトル生成機能
  const startContentChangedTimeout = () => {
    setTimeout('contentChanged', contentChangedHandler, contentChangedDelay);
  };

  const contentChangedHandler = () => {
    if (autoSaveState.value.isAutoSavingInProgress) return;
    
    if (onContentChange) {
      const hasChanges = onContentChange();
      if (hasChanges) {
        const delay = currentIsNewNote ? newNoteAutoSaveDelay : autoSaveDelay;
        startAutoSaveTimeout(delay);
      }
    }
  };

  const startAutoSaveTimeout = (delay) => {
    setTimeout('autoSave', autoSaveHandler, delay);
  };

  const autoSaveHandler = async () => {
    if (onAutoSave) {
      const startTime = Date.now();
      updateAutoSaveState({ isAutoSaving: true, isAutoSavingInProgress: true });
      
      try {
        await onAutoSave();
      } finally {
        const elapsedTime = Date.now() - startTime;
        const minDisplayTime = noteConstants.AUTO_SAVE_INDICATOR_MIN_DISPLAY;
        
        if (elapsedTime < minDisplayTime) {
          // Ensure indicator shows for minimum time
          setTimeout('autoSaveIndicator', () => {
            updateAutoSaveState({ isAutoSaving: false, isAutoSavingInProgress: false });
          }, minDisplayTime - elapsedTime);
        } else {
          updateAutoSaveState({ isAutoSaving: false, isAutoSavingInProgress: false });
        }
      }
    }
  };

  const updateAutoSaveState = (updates) => {
    Object.assign(autoSaveState.value, updates);
    if (onStateUpdate) {
      onStateUpdate(autoSaveState.value);
    }
  };

  const resetAutoSaveState = () => {
    updateAutoSaveState({ isAutoSaving: false, isAutoSavingInProgress: false });
  };

  const updateIsNewNote = (value) => {
    currentIsNewNote = value;
  };
  


  const generateTitleFromContent = (content) => {
    if (!content) return "";
    
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
    
    // マークダウン除去
    let title = firstLine
      .replace(noteConstants.MARKDOWN_PATTERNS.HEADERS, '')
      .replace(noteConstants.MARKDOWN_PATTERNS.BOLD, '$1')
      .replace(noteConstants.MARKDOWN_PATTERNS.ITALIC, '$1')
      .replace(noteConstants.MARKDOWN_PATTERNS.BOLD_UNDERSCORE, '$1')
      .replace(noteConstants.MARKDOWN_PATTERNS.ITALIC_UNDERSCORE, '$1')
      .replace(noteConstants.MARKDOWN_PATTERNS.CODE, '$1')
      .replace(noteConstants.MARKDOWN_PATTERNS.LINKS, '$1')
      .replace(noteConstants.MARKDOWN_PATTERNS.IMAGES, '$1')
      .replace(noteConstants.MARKDOWN_PATTERNS.HTML_TAGS, '')
      .trim();
    
    if (title.length > maxTitleLength) {
      title = title.substring(0, titleTruncateLength) + '...';
    }
    
    return title || defaultTitle;
  };

  const startTitleGeneration = (content, callback) => {
    setTimeout('titleGeneration', () => {
      const generatedTitle = generateTitleFromContent(content);
      callback(generatedTitle);
    }, titleGenerationDelay);
  };

  // ノート操作機能
  const saveNote = async (title, content, tags, options = {}) => {
    const { close = false, isAuto = false, isNewNote = false, filename = null } = options;
    
    try {
      let data;
      if (isNewNote) {
        data = await createNote(title, content, tags);
      } else {
        const filenameWithExtension = filename + noteConstants.MARKDOWN_EXTENSION;
        data = await updateNote(filenameWithExtension, title, content, tags);
      }
      
      if (onSaveSuccess) await onSaveSuccess(data, { close, isAuto, isNewNote });
      if (onGlobalStateUpdate) {
        onGlobalStateUpdate({
          currentNoteTitle: data.title,
          currentNoteTags: data.tags
        });
      }
      
      return data;
    } catch (error) {
      console.error('Failed to save note:', error);
      if (onSaveFailure) onSaveFailure(error);
      else if (apiErrorHandler) apiErrorHandler(error);
      throw error;
    }
  };

  const createEmptyNote = async (options = {}) => {
    const { title = noteConstants.DEFAULT_TITLE, content = "", tags = [], onStateUpdate } = options;
    
    try {
      const data = await createNote(title, content, tags);
      
      if (onSaveSuccess) await onSaveSuccess(data);
      if (onStateUpdate) {
        onStateUpdate({ note: data, newTitle: data.title, isNewNote: false });
      }
      if (router && data.filename) {
        const filename = data.filename.replace(noteConstants.MARKDOWN_EXTENSION, '');
        router.replace({ name: "note", params: { filename } });
      }
      if (onGlobalStateUpdate) {
        onGlobalStateUpdate({
          currentNoteTitle: data.title,
          currentNoteTags: data.tags
        });
      }
      
      return data;
    } catch (error) {
      console.error('Failed to create empty note:', error);
      if (onSaveFailure) onSaveFailure(error);
      else if (apiErrorHandler) apiErrorHandler(error);
      throw error;
    }
  };

  const deleteConfirmedHandler = async (filename) => {
    try {
      const filenameWithExtension = filename + noteConstants.MARKDOWN_EXTENSION;
      await deleteNote(filenameWithExtension);
      
      if (onDeleteSuccess) onDeleteSuccess();
      if (router) router.push({ name: "home" });
    } catch (error) {
      console.error('Failed to delete note:', error);
      if (onDeleteFailure) onDeleteFailure(error);
      else if (apiErrorHandler) apiErrorHandler(error);
    }
  };

  const changeNoteVisibility = async (options = {}) => {
    const { visibility, filename, title, content, tags, canModify = true, isNewNote = false } = options;
    
    if (!canModify || isNewNote) return;
    
    try {
      const filenameWithExtension = filename + noteConstants.MARKDOWN_EXTENSION;
      const data = await updateNote(filenameWithExtension, title, content, tags, visibility);
      
      if (onSaveSuccess) onSaveSuccess(data, visibility);
      if (onGlobalStateUpdate) {
        onGlobalStateUpdate({ currentNoteTags: data.tags });
      }
      
      return data;
    } catch (error) {
      console.error('Failed to change note visibility:', error);
      if (onSaveFailure) onSaveFailure(error);
      else if (apiErrorHandler) apiErrorHandler(error);
      throw error;
    }
  };

  const addImageBlobHook = (file, callback) => {
    postAttachment(file)
      .then((data) => {
        if (data) {
          const altText = data.originalFilename || data.filename;
          callback(data.url, altText);
        }
      })
      .catch((error) => {
        console.warn('Image upload failed, using local URL:', error);
        const url = URL.createObjectURL(file);
        callback(url, file.name);
      });
  };

  const postAttachment = (file) => {
    if (!file.name || file.name.trim() === "") {
      throw new Error("Invalid filename");
    }

    return createAttachment(file)
      .catch((error) => {
        if (error.response?.status === 409 && onFileExistsError) {
          onFileExistsError(error);
        } else if (error.response?.status === 413 && onFileSizeError) {
          onFileSizeError(error);
        } else if (onNetworkError) {
          onNetworkError(error);
        } else if (apiErrorHandler) {
          apiErrorHandler(error);
        }
        throw error;
      });
  };

  const setBeforeUnloadConfirmation = (enable = true) => {
    if (typeof window !== 'undefined') {
      if (enable) {
        window.onbeforeunload = () => true;
      } else {
        window.onbeforeunload = null;
      }
    }
  };

  const updateUnloadProtection = (unsavedChanges) => {
    setBeforeUnloadConfirmation(unsavedChanges);
  };

  // UI状態管理機能
  const saveDefaultEditorMode = (toastEditor) => {
    if (toastEditor && typeof localStorage !== 'undefined') {
      const isWysiwygMode = toastEditor.isWysiwygMode();
      localStorage.setItem(
        "defaultEditorMode",
        isWysiwygMode ? "wysiwyg" : "markdown"
      );
    }
  };

  const loadDefaultEditorMode = () => {
    if (typeof localStorage !== 'undefined') {
      const defaultWysiwygMode = localStorage.getItem("defaultEditorMode");
      return defaultWysiwygMode || "markdown";
    }
    return "markdown";
  };

  const loadTagCounts = async () => {
    try {
      const tagsWithCounts = await getTagsWithCounts();
      tagCountsState.value.allTagsWithCounts = tagsWithCounts;
    } catch (error) {
      console.error('Failed to load tag counts:', error);
    }
  };

  const onNoteTagClick = async (tagName) => {
    try {
      const previousSelectedTag = tagGridState.value.selectedNoteTag;
      
      if (onTagClick) {
        onTagClick(tagName, previousSelectedTag);
      }
      
      if (tagGridState.value.selectedNoteTag === tagName && previousSelectedTag !== tagName) {
        const notes = await getNotesByTag(tagName, tagGridState.value.noteTagSortBy, tagGridState.value.noteTagSortOrder, 10);
        tagGridState.value.displayedTagNotes = notes;
      }
    } catch (error) {
      console.error('Failed to get notes for tag:', error);
    }
  };

  const onNoteTagDoubleClick = (tagName) => {
    if (onTagDoubleClick) {
      onTagDoubleClick(tagName);
    }
  };

  const updateNoteTagSortOrder = (newOrder) => {
    tagGridState.value.noteTagSortOrder = newOrder;
  };

  const updateTagSortOrder = (newOrder) => {
    tagGridState.value.tagSortOrder = newOrder;
  };

  const toggleInfoSection = () => {
    const newExpandedState = !isInfoExpanded.value;
    isInfoExpanded.value = newExpandedState;
    
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('noteInfoExpanded', newExpandedState.toString());
    }
  };

  const loadInfoSectionState = () => {
    if (typeof localStorage !== 'undefined') {
      const savedState = localStorage.getItem('noteInfoExpanded');
      if (savedState !== null) {
        isInfoExpanded.value = savedState === 'true';
      }
    }
  };

  // 統合クリーンアップ
  const cleanup = () => {
    timeouts.forEach((timeoutId) => window.clearTimeout(timeoutId));
    timeouts.clear();
    setBeforeUnloadConfirmation(false);
  };

  // コンポーネントがアンマウントされた時に自動的にクリーンアップ
  onUnmounted(() => {
    cleanup();
  });

  return {
    // 自動保存・タイトル生成
    autoSaveState: readonly(autoSaveState),
    startContentChangedTimeout,
    generateTitleFromContent,
    startTitleGeneration,
    resetAutoSaveState,
    updateIsNewNote,
    

    
    // ノート操作
    saveNote,
    createEmptyNote,
    deleteConfirmedHandler,
    changeNoteVisibility,
    addImageBlobHook,
    postAttachment,
    setBeforeUnloadConfirmation,
    updateUnloadProtection,
    
    // UI状態管理
    editorMode: readonly(editorMode),
    tagGridState: readonly(tagGridState),
    tagCountsState: readonly(tagCountsState),
    isInfoExpanded: readonly(isInfoExpanded),
    saveDefaultEditorMode,
    loadDefaultEditorMode,
    loadTagCounts,
    onNoteTagClick,
    onNoteTagDoubleClick,
    updateNoteTagSortOrder,
    updateTagSortOrder,
    toggleInfoSection,
    loadInfoSectionState,
    
    // 統合クリーンアップ
    cleanup
  };
} 