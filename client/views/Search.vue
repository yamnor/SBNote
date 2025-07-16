<template>
  <Grid
    ref="gridComponent"
    :items="searchGridItems"
    :show-sort-controls="!!actualSearchTerm"
    @tag-dblclick="onTagDoubleClick"
  >
    <template #sort-controls>
      <SortDropdown
        v-model="sortBy"
        :sort-order="sortOrder"
        @update:sort-order="updateSortOrder"
        :options="searchSortOptions"
        label="Sort Results by"
      />
    </template>
  </Grid>
  
  <!-- Related Tags Section -->
  <div v-if="relatedTags.length > 0" class="mt-8">
    <Grid
      ref="relatedTagsGridComponent"
      key="related-tags-grid"
      :items="relatedTagsGridItems"
      :show-sort-controls="true"
      :show-loading="false"
      @tag-click="onRelatedTagClick"
      @tag-dblclick="onRelatedTagDoubleClick"
    >
      <template #sort-controls>
        <SortDropdown
          v-if="selectedRelatedTag && displayedRelatedTagNotes.length > 0"
          v-model="relatedTagNoteSortBy"
          :sort-order="relatedTagNoteSortOrder"
          @update:sort-order="updateRelatedTagNoteSortOrder"
          :options="noteSortOptions"
          label="Sort Notes by"
        />
        <SortDropdown
          v-model="relatedTagsSortBy"
          :sort-order="relatedTagsSortOrder"
          @update:sort-order="updateRelatedTagsSortOrder"
          :options="relatedTagsSortOptions"
          label="Sort Related Tags by"
        />
      </template>
    </Grid>
  </div>
</template>

<script setup>
import { onMounted, ref, watch, computed, nextTick } from "vue";
import { useRouter } from "vue-router";
import { apiErrorHandler, getNotes, getNotesByTag, getTagsWithCounts } from "../lib/api.js";
import SortDropdown from "../components/SortDropdown.vue";
import Grid from "../components/Grid.vue";
import GridLayout from "../components/GridLayout.vue";
import { params } from "../lib/constants.js";
import { useSorting } from "../composables/useSorting.js";
import { useGridData } from "../composables/useGridData.js";
import { useTagInteractions } from "../composables/useTagInteractions.js";
import { useDataFetching } from "../composables/useDataFetching.js";

const props = defineProps({
  searchTerm: String,
  tagName: String,
  sortBy: {
    type: Number,
    default: 0, // Score
  },
});

const gridComponent = ref();
const relatedTagsGridComponent = ref();
const results = ref([]);
const router = useRouter();

// Composables
const { searchSortOptions, noteSortOptions, sortItems } = useSorting();
const { createSearchGridItems, createNestedGridItems } = useGridData();
const { handleTagDoubleClickForHome } = useTagInteractions();
const { fetchNotes, fetchNotesByTag } = useDataFetching();

// Local state
const sortBy = ref('score'); // 'score', 'title', 'lastModified'
const sortOrder = ref('desc'); // 'asc' or 'desc'

// Related tags state
const relatedTags = ref([]);
const selectedRelatedTag = ref(null);
const displayedRelatedTagNotes = ref([]);
const relatedTagsSortBy = ref('count');
const relatedTagsSortOrder = ref('desc');
const relatedTagCounts = ref({}); // Store actual tag counts
const relatedTagNotes = ref({}); // Store pre-fetched notes for each related tag

// Related tags note sort state
const relatedTagNoteSortBy = ref('lastModified');
const relatedTagNoteSortOrder = ref('desc');

// Related tags sort options
const relatedTagsSortOptions = [
  { value: 'name', label: 'Name', icon: 'FileText' },
  { value: 'count', label: 'Count', icon: 'ArrowUp01' },
  { value: 'updated', label: 'Updated', icon: 'Clock' }
];

// Get the actual search term (either from searchTerm or tagName)
const actualSearchTerm = computed(() => {
  if (props.tagName) {
    return `#${props.tagName}`;
  }
  return props.searchTerm;
});

// Computed property for grid items in search results
const searchGridItems = computed(() => {
  return createSearchGridItems(results.value, props.tagName);
});

// Extract related tags from current search results
const extractRelatedTags = computed(() => {
  if (!props.tagName || !results.value.length) {
    return [];
  }
  
  const tagSet = new Set();
  results.value.forEach(note => {
    if (note.tags && Array.isArray(note.tags)) {
      note.tags.forEach(tag => {
        if (tag !== props.tagName) {
          tagSet.add(tag);
        }
      });
    }
  });
  
  return Array.from(tagSet);
});

// Fetch actual counts for related tags
async function fetchRelatedTagCounts() {
  if (!props.tagName || !extractRelatedTags.value.length) {
    relatedTagCounts.value = {};
    return;
  }
  
  try {
    // Get all tags with counts
    const allTagsWithCounts = await getTagsWithCounts();
    
    // Filter for related tags only
    const counts = {};
    extractRelatedTags.value.forEach(tagName => {
      const tagData = allTagsWithCounts.find(tag => tag.tag === tagName);
      counts[tagName] = tagData ? tagData.count : 0;
    });
    
    relatedTagCounts.value = counts;
  } catch (error) {
    console.error('Failed to fetch related tag counts:', error);
    // Fallback to search result counts if API fails
    const fallbackCounts = {};
    extractRelatedTags.value.forEach(tagName => {
      // 検索結果のノートも含めてカウント
      fallbackCounts[tagName] = results.value.filter(note => 
        note.tags && Array.isArray(note.tags) && note.tags.includes(tagName)
      ).length;
    });
    relatedTagCounts.value = fallbackCounts;
  }
}

// Sort related tags
const sortedRelatedTags = computed(() => {
  const tags = [...relatedTags.value];
  
  switch (relatedTagsSortBy.value) {
    case 'name':
      return tags.sort((a, b) => {
        const result = a.localeCompare(b);
        return relatedTagsSortOrder.value === 'asc' ? result : -result;
      });
    case 'count':
      return tags.sort((a, b) => {
        const countA = relatedTagCounts.value[a] || 0;
        const countB = relatedTagCounts.value[b] || 0;
        const result = countA - countB;
        return relatedTagsSortOrder.value === 'asc' ? result : -result;
      });
    case 'updated':
      return tags.sort((a, b) => {
        // For updated sorting, we'll use a placeholder since we don't pre-fetch all notes
        // This could be enhanced later if needed
        const result = 0;
        return relatedTagsSortOrder.value === 'asc' ? result : -result;
      });
    default:
      return tags;
  }
});

// Sort related tag notes for display
const sortedDisplayedRelatedTagNotes = computed(() => {
  if (!selectedRelatedTag.value || !displayedRelatedTagNotes.value.length) {
    return [];
  }
  
  return sortItems(displayedRelatedTagNotes.value, relatedTagNoteSortBy.value, relatedTagNoteSortOrder.value, 'notes');
});

// Computed property for related tags grid items
const relatedTagsGridItems = computed(() => {
  const items = [];
  
  sortedRelatedTags.value.forEach(tagName => {
    const notes = relatedTagNotes.value[tagName] || [];
    const searchResultCount = notes.filter(note => note.isSearchResult).length;
    const otherCount = notes.filter(note => !note.isSearchResult).length;
    const totalCount = searchResultCount + otherCount;
    
    // Add tag card
    items.push({
      type: 'tag',
      data: { 
        tag: tagName, 
        count: totalCount,
        searchResultCount: searchResultCount,
        otherCount: otherCount
      },
      key: `related-tag-${tagName}`,
      isSelected: selectedRelatedTag.value === tagName,
      hasAnySelection: selectedRelatedTag.value !== null,
      isPinned: false
    });
    
    // Add notes if tag is selected
    if (selectedRelatedTag.value === tagName) {
      const notes = sortedDisplayedRelatedTagNotes.value;
      notes.forEach(note => {
        items.push({
          type: 'note',
          data: note,
          key: `related-note-${note.filename}`,
          isSearchResult: note.isSearchResult || false
        });
      });
    }
  });
  
  return items;
});

// Convert sortBy to server parameter
const serverSortBy = computed(() => {
  switch (sortBy.value) {
    case 'title': return 'title';
    case 'lastModified': return 'lastModified';
    default: return 'score';
  }
});

// Update sort order and trigger search
function updateSortOrder(newOrder) {
  sortOrder.value = newOrder;
  init(false); // Don't show loading for sort operations
}

// Update related tags sort order
function updateRelatedTagsSortOrder(newOrder) {
  relatedTagsSortOrder.value = newOrder;
}

// Update related tag note sort order
function updateRelatedTagNoteSortOrder(newOrder) {
  relatedTagNoteSortOrder.value = newOrder;
}

// Handle tag double click - navigate to home with tag selected
function onTagDoubleClick(tagName) {
  handleTagDoubleClickForHome(tagName);
}

// Handle related tag click - expand/collapse notes
async function onRelatedTagClick(tagName) {
  try {
    const previousSelectedTag = selectedRelatedTag.value;
    
    // If clicking the same tag, start animation and clear notes with delay
    if (selectedRelatedTag.value === tagName) {
      // Start animation first
      startNoteAnimation();
      
      // Wait for animation to complete before clearing notes
      setTimeout(() => {
        // Clear notes after animation is done
        displayedRelatedTagNotes.value = [];
        selectedRelatedTag.value = null;
        stopNoteAnimation();
      }, 500); // Wait for animation to complete
      return;
    }
    
    // If clicking a different tag and there are currently displayed notes, animate them out first
    if (selectedRelatedTag.value && displayedRelatedTagNotes.value.length > 0) {
      // Start animation first
      startNoteAnimation();
      
      // Wait for animation to complete before switching to new tag
      setTimeout(async () => {
        try {
          // Clear previous notes and set new selected tag
          displayedRelatedTagNotes.value = [];
          selectedRelatedTag.value = tagName;
          stopNoteAnimation();
          
          // Use pre-fetched notes for the selected tag
          const notes = relatedTagNotes.value[tagName] || [];
          displayedRelatedTagNotes.value = notes;
          
          // Wait for DOM update before starting animation
          await nextTick();
          
          // Start enter animation for new notes
          startNoteEnterAnimation();
        } catch (error) {
          console.error('Failed to display notes for related tag:', error);
          // Clear selection on error
          selectedRelatedTag.value = null;
          displayedRelatedTagNotes.value = [];
        }
      }, 500); // Wait for animation to complete
      return;
    }
    
    // If no current notes are displayed, switch immediately
    displayedRelatedTagNotes.value = [];
    selectedRelatedTag.value = tagName;
    stopNoteAnimation();
    
    // Use pre-fetched notes for the selected tag
    const notes = relatedTagNotes.value[tagName] || [];
    displayedRelatedTagNotes.value = notes;
    
    // Wait for DOM update before starting animation
    await nextTick();
    
    // Start enter animation for new notes
    startNoteEnterAnimation();
  } catch (error) {
    console.error('Failed to display notes for related tag:', error);
    // Clear selection on error
    selectedRelatedTag.value = null;
    displayedRelatedTagNotes.value = [];
  }
}

// Handle related tag double click - navigate to tag page
function onRelatedTagDoubleClick(tagName) {
  router.push(`/tag/${tagName}`);
}

// Fetch notes for a related tag
async function fetchRelatedTagNotes(tagName) {
  try {
    // 全てのノートを取得
    const allNotes = await fetchNotesByTag(getNotesByTag, tagName, "lastModified", "desc", null, false);
    
    // 検索結果のノートにフラグを追加（除外しない）
    const searchResultFilenames = new Set(results.value.map(note => note.filename));
    const processedNotes = allNotes.map(note => ({
      ...note,
      isSearchResult: searchResultFilenames.has(note.filename)
    }));
    
    return processedNotes;
  } catch (error) {
    console.error('Failed to fetch related tag notes:', error);
    return [];
  }
}

// Process related tags and fetch their notes
async function processRelatedTags() {
  if (!props.tagName || !results.value.length) {
    relatedTags.value = [];
    selectedRelatedTag.value = null;
    displayedRelatedTagNotes.value = [];
    relatedTagCounts.value = {};
    relatedTagNotes.value = {};
    return;
  }
  
  const extractedTags = extractRelatedTags.value;
  relatedTags.value = extractedTags;
  
  // Fetch actual counts for related tags
  await fetchRelatedTagCounts();
  
  // Pre-fetch notes for each related tag
  const allRelatedTagNotes = {};
  for (const tagName of extractedTags) {
    try {
      const notes = await fetchRelatedTagNotes(tagName);
      allRelatedTagNotes[tagName] = notes;
    } catch (error) {
      console.error(`Failed to fetch notes for related tag ${tagName}:`, error);
      allRelatedTagNotes[tagName] = [];
    }
  }
  
  // Store pre-fetched notes
  relatedTagNotes.value = allRelatedTagNotes;
  
  // Clear any existing selection when processing new related tags
  // アニメーション付きでクリア
  if (selectedRelatedTag.value && displayedRelatedTagNotes.value.length > 0) {
    startNoteAnimation();
    setTimeout(() => {
      selectedRelatedTag.value = null;
      displayedRelatedTagNotes.value = [];
      stopNoteAnimation();
    }, 500);
  } else {
    selectedRelatedTag.value = null;
    displayedRelatedTagNotes.value = [];
  }
}

// Start note animation by adding classes to DOM elements
function startNoteAnimation() {
  const relatedTagsGrid = relatedTagsGridComponent.value?.$el;
  if (!relatedTagsGrid) {
    setTimeout(startNoteAnimation, 100);
    return;
  }
  
  const selectors = [
    '.note-card-wrapper',
    '.note-card'
  ];
  
  let foundCards = [];
  
  selectors.forEach(selector => {
    // 関連タググリッド内のノートカードのみを取得
    const cards = relatedTagsGrid.querySelectorAll(selector);
    foundCards = foundCards.concat(Array.from(cards));
  });
  
  // Remove duplicates
  foundCards = [...new Set(foundCards)];
  
  if (foundCards.length === 0) {
    setTimeout(startNoteAnimation, 100);
    return;
  }
  
  foundCards.forEach((card, index) => {
    card.classList.add('leaving');
    card.style.setProperty('--animation-index', index);
  });
}

// Start note enter animation by adding classes to DOM elements
function startNoteEnterAnimation() {
  // Use nextTick to ensure DOM is updated
  nextTick(() => {
    const relatedTagsGrid = relatedTagsGridComponent.value?.$el;
    if (!relatedTagsGrid) {
      setTimeout(startNoteEnterAnimation, 50);
      return;
    }
    
    const selectors = [
      '.note-card-wrapper',
      '.note-card'
    ];
    
    let foundCards = [];
    
    selectors.forEach(selector => {
      // 関連タググリッド内のノートカードのみを取得
      const cards = relatedTagsGrid.querySelectorAll(selector);
      foundCards = foundCards.concat(Array.from(cards));
    });
    
    // Remove duplicates
    foundCards = [...new Set(foundCards)];
    
    if (foundCards.length === 0) {
      // If no cards found, try again after a short delay
      setTimeout(startNoteEnterAnimation, 50);
      return;
    }
    
    // Set initial state for all cards
    foundCards.forEach((card, index) => {
      // Set initial position (left side, invisible)
      card.style.transform = 'translateX(-100px)';
      card.style.opacity = '0';
      card.style.transition = 'all 0.5s ease-in-out';
      card.style.zIndex = '1';
    });
    
    // Force browser reflow to ensure initial state is applied
    foundCards[0]?.offsetHeight;
    
    // Animate to final position
    requestAnimationFrame(() => {
      foundCards.forEach((card) => {
        card.style.transform = 'translateX(0)';
        // 検索結果のノートは半透明、それ以外は完全に不透明
        const isSearchResult = card.classList.contains('opacity-50');
        card.style.opacity = isSearchResult ? '0.5' : '1';
      });
    });
    
    // Clean up after animation
    setTimeout(() => {
      foundCards.forEach(card => {
        card.style.transform = '';
        card.style.transition = '';
        card.style.zIndex = '';
        // opacityはNoteCardコンポーネントのCSSクラスで制御するため、ここではクリアしない
      });
    }, 500);
  });
}

// Stop note animation by removing classes
function stopNoteAnimation() {
  const relatedTagsGrid = relatedTagsGridComponent.value?.$el;
  if (!relatedTagsGrid) return;
  
  const noteCards = relatedTagsGrid.querySelectorAll('.note-card-wrapper');
  const noteCardElements = relatedTagsGrid.querySelectorAll('.note-card');
  
  noteCards.forEach(card => {
    card.classList.remove('leaving');
  });
  
  noteCardElements.forEach(card => {
    card.classList.remove('leaving');
  });
}

// Highlight search terms in content
function highlightSearchTerms(content) {
  if (!content || !actualSearchTerm.value || props.tagName) {
    return content;
  }
  
  // Extract search terms (remove # if present)
  const searchTerm = actualSearchTerm.value.replace('#', '').trim();
  if (!searchTerm) {
    return content;
  }
  
  // Split search terms by spaces and filter out empty strings
  const terms = searchTerm.split(/\s+/).filter(term => term.length > 0);
  
  let highlightedContent = content;
  
  // Highlight each search term
  terms.forEach(term => {
    const regex = new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    highlightedContent = highlightedContent.replace(regex, '<mark class="highlight">$1</mark>');
  });
  
  return highlightedContent;
}

function init(showLoading = true) {
  if (showLoading) {
    gridComponent.value.setLoading();
  }
  
  fetchNotes(getNotes, actualSearchTerm.value, serverSortBy.value, sortOrder.value, null, null, showLoading)
    .then(async (data) => {
      results.value = data;
      if (showLoading) {
        gridComponent.value.setLoaded();
      }
      
      // Process related tags after results are loaded
      await processRelatedTags();
    })
    .catch((error) => {
      if (showLoading) {
        gridComponent.value.setFailed();
      }
    });
}

watch(() => actualSearchTerm.value, init);
watch(() => sortBy.value, () => init(false)); // Don't show loading for sort operations
onMounted(init);
</script>

<style>
/* Highlight display styles */
.highlight {
  @apply text-theme-brand font-semibold bg-yellow-100 px-0.5 rounded;
}

/* Search highlight styles */
.search-highlights .match,
.search-highlights .highlight {
  @apply text-theme-brand font-semibold bg-yellow-100 px-0.5 rounded;
}

/* Styles for highlight tags returned from server */
.search-highlights mark,
.search-highlights .highlight,
.search-highlights .match,
.search-highlights b {
  @apply text-theme-brand font-semibold bg-yellow-100 px-0.5 rounded;
}
</style>
