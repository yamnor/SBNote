<template>
  <Grid
    ref="gridComponent"
    :items="gridItemsWithProps"
    :show-sort-controls="true"
    @tag-click="onTagClick"
    @tag-dblclick="onTagDoubleClick"
    @tag-longpress="onTagLongPress"
  >
    <template #sort-controls>
      <SortDropdown
        v-if="selectedTag && displayedNotes.length > 0"
        v-model="noteSortBy"
        :sort-order="noteSortOrder"
        @update:sort-order="updateNoteSortOrder"
        :options="noteSortOptions"
        label="Sort Notes by"
      />
      <SortDropdown
        v-model="sortBy"
        :sort-order="sortOrder"
        @update:sort-order="updateSortOrder"
        label="Sort Tags by"
      />
    </template>
  </Grid>
  
  <!-- Tag Rename Modal -->
  <ConfirmModal
    v-model="showRenameModal"
    title="Rename Tag"
    :message="`Enter new name for tag '${tagToRename}':`"
    confirm-button-text="Rename"
    @confirm="confirmRenameTag"
    @cancel="cancelRenameTag"
  >
    <template #default>
      <input
        v-model="newTagName"
        type="text"
        class="w-full px-3 py-2 border border-theme-border rounded-md focus:outline-none focus:ring-2 focus:ring-theme-brand focus:border-transparent bg-theme-background-surface text-theme-text placeholder-theme-text-muted"
        placeholder="Enter new tag name"
        @keyup.esc="cancelRenameTag"
        ref="renameInput"
      />
    </template>
  </ConfirmModal>
  
  <!-- Tag Delete Modal -->
  <ConfirmModal
    v-model="showDeleteModal"
    title="Delete Tag"
    :message="`Are you sure you want to delete the tag '${tagToDelete}'? This action cannot be undone.`"
    confirm-button-text="Delete"
    confirm-button-style="danger"
    @confirm="confirmDeleteTag"
    @cancel="cancelDeleteTag"
  />
</template>

<script setup>
import { onMounted, ref, watch, onUnmounted, computed, nextTick } from "vue";
import { useRouter } from "vue-router";

import { apiErrorHandler, getTagsWithCounts, getNotesByTag, renameTag, deleteTag } from "../api.js";
import SortDropdown from "../components/SortDropdown.vue";
import Grid from "../components/Grid.vue";
import { useGlobalStore } from "../globalStore.js";
import { useLocalStorage } from "../composables/useLocalStorage.js";
import { useSorting } from "../composables/useSorting.js";
import { useGridData } from "../composables/useGridData.js";
import { useTagInteractions } from "../composables/useTagInteractions.js";
import { useDataFetching } from "../composables/useDataFetching.js";
import ConfirmModal from "../components/ConfirmModal.vue";

const globalStore = useGlobalStore();
const router = useRouter();
const gridComponent = ref();

// Composables
const { createPersistentRef, saveValue } = useLocalStorage();
const { noteSortOptions, sortItems } = useSorting();
const { createNestedGridItems, sortTagsWithPinned } = useGridData();
const { handleTagClick, handleTagDoubleClick, handleTagLongPress } = useTagInteractions();
const { fetchTagsWithCounts, fetchNotesByTag, startPeriodicRefresh } = useDataFetching();

// Persistent state
const sortBy = createPersistentRef('sbnote_home_sort_by', 'name');
const sortOrder = createPersistentRef('sbnote_home_sort_order', 'asc');
const noteSortBy = createPersistentRef('sbnote_home_note_sort_by', 'lastModified');
const noteSortOrder = createPersistentRef('sbnote_home_note_sort_order', 'desc');
const selectedTag = createPersistentRef('sbnote_home_selected_tag', null);
const pinnedTags = createPersistentRef('sbnote_home_pinned_tags', []);

// Local state
const tagsWithCounts = ref([]);
const displayedNotes = ref([]);
let stopRefresh = null;

// Tag edit state
const showRenameModal = ref(false);
const showDeleteModal = ref(false);
const tagToRename = ref('');
const tagToDelete = ref('');
const newTagName = ref('');
const renameInput = ref();

// Computed property for sorted tags with pinned tags at the top
const sortedTagsWithCounts = computed(() => {
  return sortTagsWithPinned(tagsWithCounts.value, sortBy.value, sortOrder.value, pinnedTags.value);
});

// Computed property for sorted notes
const sortedNotes = computed(() => {
  return sortItems(displayedNotes.value, noteSortBy.value, noteSortOrder.value, 'notes');
});

// Computed property for grid items with props for GridLayout component
const gridItemsWithProps = computed(() => {
  return createNestedGridItems(sortedTagsWithCounts.value, sortedNotes.value, selectedTag.value, pinnedTags.value);
});

// Update sort order
function updateSortOrder(newOrder) {
  sortOrder.value = newOrder;
}

// Update note sort order
function updateNoteSortOrder(newOrder) {
  noteSortOrder.value = newOrder;
}

// Handle tag click
async function onTagClick(tagName) {
  try {
    const previousSelectedTag = selectedTag.value;
    
    handleTagClick(tagName, selectedTag.value, (tag) => selectedTag.value = tag, () => displayedNotes.value = []);
    
    // Only fetch notes if a new tag was selected (not the same tag)
    if (selectedTag.value === tagName && previousSelectedTag !== tagName) {
      // Get notes for the selected tag using config limit
      const limit = globalStore.config.quickAccessLimit || 12;
      const notes = await fetchNotesByTag(getNotesByTag, tagName, "lastModified", "desc", limit);
      displayedNotes.value = notes;
    }
  } catch (error) {
    console.error('Failed to get notes for tag:', error);
  }
}

// Handle tag double click - navigate to search page
function onTagDoubleClick(tagName) {
  handleTagDoubleClick(tagName, '/tag/');
}

// Handle tag long press for pinning/unpinning
function onTagLongPress(tagName) {
  handleTagLongPress(tagName, pinnedTags.value, (tags) => pinnedTags.value = tags, saveValue, 'sbnote_home_pinned_tags');
}

// Tag edit handlers
function handleRenameTag(tagName) {
  tagToRename.value = tagName;
  newTagName.value = tagName;
  showRenameModal.value = true;
  nextTick(() => {
    if (renameInput.value) {
      renameInput.value.focus();
      renameInput.value.select();
    }
  });
}

function handleDeleteTag(tagName) {
  tagToDelete.value = tagName;
  showDeleteModal.value = true;
}

async function confirmRenameTag() {
  if (!newTagName.value.trim() || newTagName.value.trim() === tagToRename.value) {
    showRenameModal.value = false;
    return;
  }
  
  try {
    await renameTag(tagToRename.value, newTagName.value.trim());
    
    // Update selected tag if it was the renamed tag
    if (selectedTag.value === tagToRename.value) {
      selectedTag.value = newTagName.value.trim();
    }
    
    // Update pinned tags if the renamed tag was pinned
    const pinnedIndex = pinnedTags.value.indexOf(tagToRename.value);
    if (pinnedIndex !== -1) {
      pinnedTags.value[pinnedIndex] = newTagName.value.trim();
      saveValue('sbnote_home_pinned_tags', pinnedTags.value);
    }
    
    // Refresh tags list
    const tagsData = await fetchTagsWithCounts(getTagsWithCounts);
    tagsWithCounts.value = tagsData;
    
    // Clear displayed notes if the selected tag was renamed
    if (selectedTag.value === newTagName.value.trim()) {
      displayedNotes.value = [];
    }
    
    showRenameModal.value = false;
    globalStore.toast?.addToast('Tag renamed successfully', '', 'success');
  } catch (error) {
    console.error('Failed to rename tag:', error);
    globalStore.toast?.addToast('Failed to rename tag', '', 'error');
  }
}

function cancelRenameTag() {
  showRenameModal.value = false;
  newTagName.value = '';
}

async function confirmDeleteTag() {
  try {
    await deleteTag(tagToDelete.value);
    
    // Clear selected tag if it was the deleted tag
    if (selectedTag.value === tagToDelete.value) {
      selectedTag.value = null;
    }
    
    // Remove from pinned tags if the deleted tag was pinned
    const pinnedIndex = pinnedTags.value.indexOf(tagToDelete.value);
    if (pinnedIndex !== -1) {
      pinnedTags.value.splice(pinnedIndex, 1);
      saveValue('sbnote_home_pinned_tags', pinnedTags.value);
    }
    
    // Refresh tags list
    const tagsData = await fetchTagsWithCounts(getTagsWithCounts);
    tagsWithCounts.value = tagsData;
    
    // Clear displayed notes if the selected tag was deleted
    if (selectedTag.value === null) {
      displayedNotes.value = [];
    }
    
    showDeleteModal.value = false;
    globalStore.toast?.addToast('Tag deleted successfully', '', 'success');
  } catch (error) {
    console.error('Failed to delete tag:', error);
    globalStore.toast?.addToast('Failed to delete tag', '', 'error');
  }
}

function cancelDeleteTag() {
  showDeleteModal.value = false;
}

// Refresh home data (tags and selected tag notes)
async function refreshHomeData() {
  try {
    // Refresh tags list
    const tagsData = await fetchTagsWithCounts(getTagsWithCounts);
    tagsWithCounts.value = tagsData;
    
    // If there's a selected tag, refresh its notes
    if (selectedTag.value) {
      try {
        const limit = globalStore.config.quickAccessLimit || 12;
        const notes = await fetchNotesByTag(getNotesByTag, selectedTag.value, "lastModified", "desc", limit);
        displayedNotes.value = notes;
      } catch (error) {
        console.error('Failed to refresh selected tag notes:', error);
        // If the selected tag no longer exists, clear the selection
        selectedTag.value = null;
        displayedNotes.value = [];
      }
    }
  } catch (error) {
    console.error('Failed to refresh home data:', error);
  }
}


async function init() {
  if (globalStore.config.quickAccessHide) {
    return;
  }
  
  try {
    // Load tags with counts efficiently
    const tagsData = await fetchTagsWithCounts(getTagsWithCounts);
    tagsWithCounts.value = tagsData;
    gridComponent.value.setLoaded();
    
    // Check if there's a tag to be selected from localStorage (from search page)
    const tagToSelect = localStorage.getItem('home_selected_tag');
    if (tagToSelect) {
      localStorage.removeItem('home_selected_tag'); // Clear it after reading
      selectedTag.value = tagToSelect;
      
      // Load notes for the selected tag
      try {
        const limit = globalStore.config.quickAccessLimit || 12;
        const notes = await fetchNotesByTag(getNotesByTag, tagToSelect, "lastModified", "desc", limit);
        displayedNotes.value = notes;
      } catch (error) {
        console.error('Failed to load tag notes:', error);
        selectedTag.value = null;
      }
      return;
    }
    
    // If there's a saved selected tag, load its notes
    if (selectedTag.value) {
      try {
        const limit = globalStore.config.quickAccessLimit || 12;
        const notes = await fetchNotesByTag(getNotesByTag, selectedTag.value, "lastModified", "desc", limit);
        displayedNotes.value = notes;
      } catch (error) {
        console.error('Failed to load saved tag notes:', error);
        // If the saved tag no longer exists or has issues, clear the selection
        selectedTag.value = null;
      }
    }
  } catch (error) {
    gridComponent.value.setFailed();
  }
}

// Start periodic refresh of tags
function startPeriodicRefreshInterval() {
  stopRefresh = startPeriodicRefresh(
    () => getTagsWithCounts().then(tagsData => tagsWithCounts.value = tagsData),
    30000,
    () => !globalStore.config.quickAccessHide
  );
}

// Watch to allow for delayed config load.
watch(() => globalStore.config.hideRecentlyModified, init);

// Watch selectedTag changes and notify App.vue
watch(selectedTag, (newTag) => {
  if (window.updateHomeSelectedTag) {
    window.updateHomeSelectedTag(newTag);
  }
});

onMounted(() => {
  init();
  startPeriodicRefreshInterval();
  
  // Listen for tag edit events from NavBar
  window.addEventListener('tag-rename', (event) => {
    handleRenameTag(event.detail);
  });
  
  window.addEventListener('tag-delete', (event) => {
    handleDeleteTag(event.detail);
  });
  
  // Listen for file import events to refresh data
  window.addEventListener('file-imported', () => {
    refreshHomeData();
  });
});

onUnmounted(() => {
  if (stopRefresh) {
    stopRefresh();
  }
  
  // Clean up event listeners
  window.removeEventListener('tag-rename', handleRenameTag);
  window.removeEventListener('tag-delete', handleDeleteTag);
  window.removeEventListener('file-imported', refreshHomeData);
});
</script>


