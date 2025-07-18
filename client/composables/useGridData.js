import { computed } from 'vue';
import { useSorting } from './useSorting.js';

export function useGridData() {
  const { sortItems } = useSorting();

  // Create grid items from tags and notes
  const createGridItems = (tags = [], notes = [], selectedTag = null, pinnedTags = []) => {
    const items = [];
    
    // Add tag items
    for (const tagData of tags) {
      items.push({
        type: 'tag',
        data: tagData,
        key: `tag-${tagData.tag}`,
        isSelected: selectedTag === tagData.tag,
        hasAnySelection: selectedTag !== null,
        isPinned: tagData.is_pinned || pinnedTags.includes(tagData.tag)
      });
    }
    
    // Add note items
    for (const note of notes) {
      items.push({
        type: 'note',
        data: note,
        key: `note-${note.filename}`
      });
    }
    
    return items;
  };

  // Create grid items with notes nested under selected tag (Home.vue style)
  const createNestedGridItems = (tags = [], notes = [], selectedTag = null, pinnedTags = []) => {
    const items = [];
    
    for (const tagData of tags) {
      // Add tag card
      items.push({
        type: 'tag',
        data: tagData,
        key: `tag-${tagData.tag}`,
        isSelected: selectedTag === tagData.tag,
        hasAnySelection: selectedTag !== null,
        isPinned: tagData.is_pinned || pinnedTags.includes(tagData.tag)
      });
      
      // If this tag is selected, add its notes right after
      if (selectedTag === tagData.tag && notes.length > 0) {
        for (const note of notes) {
          items.push({
            type: 'note',
            data: note,
            key: `note-${note.filename}`
          });
        }
      }
    }
    
    return items;
  };

  // Create search grid items (Search.vue style)
  const createSearchGridItems = (results = [], tagName = null, completeTagData = null) => {
    const items = [];
    
    // For tag search: show tag card first, then notes
    if (tagName) {
      // Use complete tag data if provided, otherwise create basic data
      const tagData = completeTagData ? {
        ...completeTagData,
        count: results.length
      } : {
        tag: tagName,
        count: results.length
      };
      
      items.push({
        type: 'tag',
        data: tagData,
        key: `tag-${tagName}`,
        isSelected: false,  // 検索タグは常に表示状態（選択状態ではない）
        hasAnySelection: false,
        isPinned: completeTagData ? completeTagData.is_pinned || false : false
      });
    }
    
    // Add note cards
    for (const result of results) {
      items.push({
        type: 'note',
        data: result,
        key: `note-${result.filename}`
      });
    }
    
    return items;
  };

  // Sort tags with pinned tags at the top and _untagged at the bottom
  const sortTagsWithPinned = (tags, sortBy, sortOrder, pinnedTags) => {
    const sorted = sortItems(tags, sortBy, sortOrder, 'tags');
    
    // Move pinned tags to the top (using server-side is_pinned flag)
    const pinned = [];
    const unpinned = [];
    const untagged = [];
    
    for (const tag of sorted) {
      if (tag.is_pinned || pinnedTags.includes(tag.tag)) {
        pinned.push(tag);
      } else if (tag.tag === '_untagged') {
        untagged.push(tag);
      } else {
        unpinned.push(tag);
      }
    }
    
    return [...pinned, ...unpinned, ...untagged];
  };

  // Get note count for a tag
  const getTagNoteCount = (tag, tagsWithCounts) => {
    const tagData = tagsWithCounts.find(t => t.tag === tag);
    return tagData ? tagData.count : 0;
  };

  return {
    createGridItems,
    createNestedGridItems,
    createSearchGridItems,
    sortTagsWithPinned,
    getTagNoteCount
  };
} 