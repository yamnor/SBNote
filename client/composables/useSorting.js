import { computed } from 'vue';

export function useSorting() {
  // Common sort options
  const commonSortOptions = [
    {
      value: 'title',
      label: 'Title',
      icon: 'FileText'
    },
    {
      value: 'lastModified',
      label: 'Modified',
      icon: 'Clock'
    }
  ];

  // Note sort options
  const noteSortOptions = [
    {
      value: 'lastModified',
      label: 'Modified',
      icon: 'Clock'
    },
    {
      value: 'title',
      label: 'Title',
      icon: 'FileText'
    }
  ];

  // Search sort options
  const searchSortOptions = [
    {
      value: 'score',
      label: 'Relevance',
      icon: 'Score'
    },
    {
      value: 'title',
      label: 'Title',
      icon: 'FileText'
    },
    {
      value: 'lastModified',
      label: 'Modified',
      icon: 'Calendar'
    }
  ];

  // Tag sort options
  const tagSortOptions = [
    {
      value: 'name',
      label: 'Name',
      icon: 'FileText'
    },
    {
      value: 'count',
      label: 'Count',
      icon: 'Clock'
    },
    {
      value: 'updated',
      label: 'Updated',
      icon: 'Clock'
    }
  ];

  // Sort items by title
  const sortByTitle = (items, order = 'asc') => {
    const sorted = [...items];
    sorted.sort((a, b) => {
      const comparison = a.title.localeCompare(b.title);
      return order === 'asc' ? comparison : -comparison;
    });
    return sorted;
  };

  // Sort items by lastModified
  const sortByLastModified = (items, order = 'asc') => {
    const sorted = [...items];
    sorted.sort((a, b) => {
      const comparison = new Date(a.lastModified) - new Date(b.lastModified);
      return order === 'asc' ? comparison : -comparison;
    });
    return sorted;
  };

  // Sort tags by name
  const sortTagsByName = (tags, order = 'asc') => {
    const sorted = [...tags];
    sorted.sort((a, b) => {
      const comparison = a.tag.localeCompare(b.tag);
      return order === 'asc' ? comparison : -comparison;
    });
    return sorted;
  };

  // Sort tags by count
  const sortTagsByCount = (tags, order = 'asc') => {
    const sorted = [...tags];
    sorted.sort((a, b) => {
      const comparison = a.count - b.count;
      return order === 'asc' ? comparison : -comparison;
    });
    return sorted;
  };

  // Sort tags by recent modified time
  const sortTagsByUpdated = (tags, order = 'asc') => {
    const sorted = [...tags];
    sorted.sort((a, b) => {
      const aTime = a.recentModified || 0;
      const bTime = b.recentModified || 0;
      const comparison = aTime - bTime;
      return order === 'asc' ? comparison : -comparison;
    });
    return sorted;
  };

  // Generic sort function
  const sortItems = (items, sortBy, sortOrder, itemType = 'notes') => {
    if (itemType === 'tags') {
      if (sortBy === 'name') {
        return sortTagsByName(items, sortOrder);
      } else if (sortBy === 'count') {
        return sortTagsByCount(items, sortOrder);
      } else if (sortBy === 'updated') {
        return sortTagsByUpdated(items, sortOrder);
      }
    } else {
      if (sortBy === 'title') {
        return sortByTitle(items, sortOrder);
      } else if (sortBy === 'lastModified') {
        return sortByLastModified(items, sortOrder);
      }
    }
    return items;
  };

  return {
    commonSortOptions,
    noteSortOptions,
    searchSortOptions,
    tagSortOptions,
    sortByTitle,
    sortByLastModified,
    sortTagsByName,
    sortTagsByCount,
    sortTagsByUpdated,
    sortItems
  };
} 