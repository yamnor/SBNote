import { useRouter } from 'vue-router';

export function useTagInteractions() {
  const router = useRouter();

  // Handle tag click for selection/deselection
  const handleTagClick = (tagName, selectedTag, setSelectedTag, clearNotes, startAnimation, stopAnimation) => {
    // If the same tag is clicked again, clear the notes with animation delay
    if (selectedTag === tagName) {
      setSelectedTag(null);
      // Start animation first
      if (startAnimation) startAnimation();
      // Clear notes after animation delay (0.5 second)
      setTimeout(() => {
        clearNotes();
        if (stopAnimation) stopAnimation();
      }, 500);
      return;
    }
    
    // If clicking a different tag and there are currently displayed notes, animate them out first
    if (selectedTag && startAnimation) {
      // Start animation first
      startAnimation();
      // Clear notes after animation delay
      setTimeout(() => {
        clearNotes();
        setSelectedTag(tagName);
        if (stopAnimation) stopAnimation();
      }, 500);
      return;
    }
    
    // If no animation function or no current selection, switch immediately
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