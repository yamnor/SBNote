import { ref } from 'vue';
import { apiErrorHandler } from '../api.js';

export function useDataFetching() {
  const isLoading = ref(false);
  const error = ref(null);

  // Generic data fetching with loading state
  const fetchData = async (fetchFunction, showLoading = true) => {
    if (showLoading) {
      isLoading.value = true;
      error.value = null;
    }

    try {
      const data = await fetchFunction();
      return data;
    } catch (err) {
      error.value = err;
      apiErrorHandler(err);
      throw err;
    } finally {
      if (showLoading) {
        isLoading.value = false;
      }
    }
  };

  // Fetch tags with counts
  const fetchTagsWithCounts = async (getTagsWithCounts, showLoading = true) => {
    return await fetchData(() => getTagsWithCounts(), showLoading);
  };

  // Fetch notes by tag
  const fetchNotesByTag = async (getNotesByTag, tagName, sortBy, sortOrder, limit, showLoading = true) => {
    return await fetchData(() => getNotesByTag(tagName, sortBy, sortOrder, limit), showLoading);
  };

  // Fetch notes for search
  const fetchNotes = async (getNotes, searchTerm, sortBy, sortOrder, offset, limit, showLoading = true) => {
    return await fetchData(() => getNotes(searchTerm, sortBy, sortOrder, offset, limit), showLoading);
  };

  // Periodic refresh function
  const startPeriodicRefresh = (fetchFunction, interval = 30000, condition = () => true) => {
    const refreshInterval = setInterval(() => {
      if (condition()) {
        fetchFunction()
          .catch((err) => {
            console.error('Failed to refresh data:', err);
          });
      }
    }, interval);

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  };

  return {
    isLoading,
    error,
    fetchData,
    fetchTagsWithCounts,
    fetchNotesByTag,
    fetchNotes,
    startPeriodicRefresh
  };
} 