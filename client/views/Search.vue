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
          v-if="expandedRelatedTags.size > 0"
          v-model="relatedTagsNoteSortBy"
          :sort-order="relatedTagsNoteSortOrder"
          @update:sort-order="updateRelatedTagsNoteSortOrder"
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
import { onMounted, ref, watch, computed } from "vue";
import { useRouter } from "vue-router";
import { apiErrorHandler, getNotes, getNotesByTag } from "../api.js";
import SortDropdown from "../components/SortDropdown.vue";
import Grid from "../components/Grid.vue";
import GridLayout from "../components/GridLayout.vue";
import { params } from "../constants.js";
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
const relatedTagNotes = ref({});
const expandedRelatedTags = ref(new Set());
const relatedTagsSortBy = ref('count');
const relatedTagsSortOrder = ref('desc');

// Related tags note sort state
const relatedTagsNoteSortBy = ref('lastModified');
const relatedTagsNoteSortOrder = ref('desc');

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
        const countA = relatedTagNotes.value[a]?.length || 0;
        const countB = relatedTagNotes.value[b]?.length || 0;
        const result = countA - countB;
        return relatedTagsSortOrder.value === 'asc' ? result : -result;
      });
    case 'updated':
      return tags.sort((a, b) => {
        const notesA = relatedTagNotes.value[a] || [];
        const notesB = relatedTagNotes.value[b] || [];
        const latestA = notesA.length > 0 ? Math.max(...notesA.map(n => n.lastModified || 0)) : 0;
        const latestB = notesB.length > 0 ? Math.max(...notesB.map(n => n.lastModified || 0)) : 0;
        const result = latestA - latestB;
        return relatedTagsSortOrder.value === 'asc' ? result : -result;
      });
    default:
      return tags;
  }
});

// Sort related tag notes
const sortedRelatedTagNotes = computed(() => {
  const sortedNotes = {};
  
  Object.keys(relatedTagNotes.value).forEach(tagName => {
    const notes = relatedTagNotes.value[tagName] || [];
    sortedNotes[tagName] = sortItems(notes, relatedTagsNoteSortBy.value, relatedTagsNoteSortOrder.value, 'notes');
  });
  
  return sortedNotes;
});

// Computed property for related tags grid items
const relatedTagsGridItems = computed(() => {
  const items = [];
  
  sortedRelatedTags.value.forEach(tagName => {
    const noteCount = relatedTagNotes.value[tagName]?.length || 0;
    
    // Add tag card
    items.push({
      type: 'tag',
      data: { tag: tagName, count: noteCount },
      key: `related-tag-${tagName}`,
      isSelected: expandedRelatedTags.value.has(tagName),
      hasAnySelection: expandedRelatedTags.value.size > 0,
      isPinned: false
    });
    
    // Add notes if tag is expanded
    if (expandedRelatedTags.value.has(tagName)) {
      const notes = sortedRelatedTagNotes.value[tagName] || [];
      notes.forEach(note => {
        items.push({
          type: 'note',
          data: note,
          key: `related-note-${note.filename}`
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

// Update related tags note sort order
function updateRelatedTagsNoteSortOrder(newOrder) {
  relatedTagsNoteSortOrder.value = newOrder;
}

// Handle tag double click - navigate to home with tag selected
function onTagDoubleClick(tagName) {
  handleTagDoubleClickForHome(tagName);
}

// Handle related tag click - expand/collapse notes
function onRelatedTagClick(tagName) {
  if (expandedRelatedTags.value.has(tagName)) {
    expandedRelatedTags.value.delete(tagName);
  } else {
    expandedRelatedTags.value.add(tagName);
  }
}

// Handle related tag double click - navigate to tag page
function onRelatedTagDoubleClick(tagName) {
  router.push(`/tag/${tagName}`);
}

// Fetch notes for a related tag
async function fetchRelatedTagNotes(tagName) {
  try {
    const notes = await fetchNotesByTag(getNotesByTag, tagName, "lastModified", "desc", null, false);
    return notes;
  } catch (error) {
    console.error('Failed to fetch related tag notes:', error);
    return [];
  }
}

// Process related tags and fetch their notes
async function processRelatedTags() {
  if (!props.tagName || !results.value.length) {
    relatedTags.value = [];
    relatedTagNotes.value = {};
    expandedRelatedTags.value.clear();
    return;
  }
  
  const extractedTags = extractRelatedTags.value;
  relatedTags.value = extractedTags;
  
  if (extractedTags.length === 0) {
    return;
  }
  
  // Fetch notes for all related tags in parallel
  const tagNotesPromises = extractedTags.map(async (tagName) => {
    const notes = await fetchRelatedTagNotes(tagName);
    return { tagName, notes };
  });
  
  const tagNotesResults = await Promise.all(tagNotesPromises);
  
  // Update relatedTagNotes
  tagNotesResults.forEach(({ tagName, notes }) => {
    relatedTagNotes.value[tagName] = notes;
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
