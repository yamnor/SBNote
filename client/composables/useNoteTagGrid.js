import { ref, computed } from 'vue';
import { getTagsWithCounts, getNotesByTag } from '../lib/api.js';
import { useSorting } from './useSorting.js';
import { useGridData } from './useGridData.js';
import { useTagInteractions } from './useTagInteractions.js';
import { useDataFetching } from './useDataFetching.js';

export function useNoteTagGrid() {
  // Import existing composables
  const { sortItems } = useSorting();
  const { createNestedGridItems } = useGridData();
  const { handleTagClick, handleTagDoubleClick } = useTagInteractions();
  const { fetchNotesByTag } = useDataFetching();

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
  const selectedNoteTag = computed(() => tagGridState.value.selectedNoteTag);
  const displayedTagNotes = computed(() => tagGridState.value.displayedTagNotes);
  const noteTagSortBy = computed(() => tagGridState.value.noteTagSortBy);
  const noteTagSortOrder = computed(() => tagGridState.value.noteTagSortOrder);
  const tagSortBy = computed(() => tagGridState.value.tagSortBy);
  const tagSortOrder = computed(() => tagGridState.value.tagSortOrder);

  // Computed property for note tags (current note's tags)
  const noteTags = computed(() => {
    return (newTags, canModify, note) => {
      // Use newTags for editing mode, note.tags for view mode
      const tags = canModify ? newTags : (note.tags || []);
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
    };
  });

  // Computed property for sorted tag notes
  const sortedTagNotes = computed(() => {
    return sortItems(displayedTagNotes.value, noteTagSortBy.value, noteTagSortOrder.value, 'notes');
  });

  // Computed property for tag grid items
  const tagGridItems = computed(() => {
    return (noteTags, selectedNoteTag) => {
      const items = createNestedGridItems(noteTags, sortedTagNotes.value, selectedNoteTag, []);
      return items;
    };
  });

  // State update functions
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

  // Reset tag grid state
  function resetTagGridState() {
    updateTagGridState({
      selectedNoteTag: null,
      displayedTagNotes: []
    });
  }

  return {
    // State
    tagGridState,
    tagCountsState,
    selectedNoteTag,
    displayedTagNotes,
    noteTagSortBy,
    noteTagSortOrder,
    tagSortBy,
    tagSortOrder,
    
    // Computed
    noteTags,
    sortedTagNotes,
    tagGridItems,
    
    // Functions
    updateTagGridState,
    updateTagCountsState,
    loadTagCounts,
    onNoteTagClick,
    onNoteTagDoubleClick,
    updateNoteTagSortOrder,
    updateTagSortOrder,
    resetTagGridState
  };
} 