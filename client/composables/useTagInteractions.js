import { useRouter } from 'vue-router';

export function useTagInteractions() {
  const router = useRouter();

  // Handle tag click for selection/deselection
  const handleTagClick = (tagName, selectedTag, setSelectedTag, clearNotes) => {
    // If the same tag is clicked again, clear the notes
    if (selectedTag === tagName) {
      clearNotes();
      setSelectedTag(null);
      return;
    }
    
    // Clear previous notes and set new selected tag
    clearNotes();
    setSelectedTag(tagName);
  };

  // Handle tag double click - navigate to search page
  const handleTagDoubleClick = (tagName, targetRoute = '/tag/') => {
    router.push(`${targetRoute}${tagName}`);
  };

  // Handle tag double click for home navigation with tag selection
  const handleTagDoubleClickForHome = (tagName) => {
    // Navigate to home page with the tag pre-selected
    router.push('/');
    // Store the tag to be selected in localStorage
    localStorage.setItem('home_selected_tag', tagName);
  };

  // Handle tag long press for pinning/unpinning
  const handleTagLongPress = (tagName, pinnedTags, setPinnedTags, saveToLocalStorage, localStorageKey) => {
    const currentPinnedTags = [...pinnedTags];
    
    if (currentPinnedTags.includes(tagName)) {
      // Unpin the tag
      const index = currentPinnedTags.indexOf(tagName);
      currentPinnedTags.splice(index, 1);
    } else {
      // Pin the tag
      currentPinnedTags.push(tagName);
    }
    
    setPinnedTags(currentPinnedTags);
    if (saveToLocalStorage && localStorageKey) {
      saveToLocalStorage(localStorageKey, currentPinnedTags);
    }
  };

  return {
    handleTagClick,
    handleTagDoubleClick,
    handleTagDoubleClickForHome,
    handleTagLongPress
  };
} 