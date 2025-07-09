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
</template>

<script setup>
import { onMounted, ref, watch, computed } from "vue";
import { useRouter } from "vue-router";
import { apiErrorHandler, getNotes } from "../api.js";
import SortDropdown from "../components/SortDropdown.vue";
import Grid from "../components/Grid.vue";
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
const results = ref([]);
const router = useRouter();

// Composables
const { searchSortOptions } = useSorting();
const { createSearchGridItems } = useGridData();
const { handleTagDoubleClickForHome } = useTagInteractions();
const { fetchNotes } = useDataFetching();

// Local state
const sortBy = ref('score'); // 'score', 'title', 'lastModified'
const sortOrder = ref('desc'); // 'asc' or 'desc'

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

// Handle tag double click - navigate to home with tag selected
function onTagDoubleClick(tagName) {
  handleTagDoubleClickForHome(tagName);
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
    .then((data) => {
      results.value = data;
      if (showLoading) {
        gridComponent.value.setLoaded();
      }
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
