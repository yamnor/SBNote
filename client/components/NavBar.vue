<template>
  <nav class="mb-4 flex justify-between items-center gap-4 relative z-navigation" style="z-index: 40;">
    <!-- Home Button -->
    <RouterLink :to="{ name: 'home' }" class="flex-shrink-0">
      <button class="flex items-center justify-center w-10 h-10 rounded-lg bg-color-button-secondary-bg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg text-color-button-secondary-fg transition-colors">
        <LayoutGrid class="w-6 h-6" />
      </button>
    </RouterLink>
    
    <!-- Search Input -->
    <div class="flex-1 mx-auto relative overflow-visible">
      <SearchInput
        ref="searchInput"
        :incremental="true"
        :searchResults="incrementalSearchResults"
        placeholder="Search notes..."
        @search="onSearch"
        @incrementalSearch="onIncrementalSearch"
        @selectResult="onSelectResult"
        @closeResults="onCloseResults"
        @confirmSelection="onConfirmSelection"
        @clearSearch="onClearSearch"
      />
    </div>
    
    <!-- Menu Dropdown -->
    <DropdownMenu :trigger-icon="Menu" :menu-position="'right'" @close="onMenuClose">
      <template #indicator>
        <!-- Login Status Indicator -->
        <div
          v-show="globalStore.isAuthenticated"
          :class="[
            'absolute -top-1 -right-1 h-2 w-2 rounded-full bg-color-primary'
          ]"
          :title="globalStore.editMode ? 'Logged in (Edit Mode)' : 'Logged in'"
        ></div>
      </template>
      <!-- README Item -->
      <DropdownMenuItem
        :icon="BookOpen"
        @click="showReadme"
      >
        README
      </DropdownMenuItem>
      
      <!-- Divider -->
      <div v-if="globalStore.isAuthenticated && !isReadmePage" class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
      <!-- Mode Toggle Items (hidden for README.md) -->
      <DropdownMenuItem
        v-if="globalStore.isAuthenticated && !isReadmePage"
        :icon="Edit"
        @click="toggleEditMode"
        :class="{ 'bg-gray-100 dark:bg-gray-700': globalStore.editMode }"
      >
        Edit Mode
      </DropdownMenuItem>
      
      <DropdownMenuItem
        v-if="globalStore.isAuthenticated && !isReadmePage"
        :icon="Eye"
        @click="toggleViewMode"
        :class="{ 'bg-gray-100 dark:bg-gray-700': !globalStore.editMode }"
      >
        View Mode
      </DropdownMenuItem>
      
      <!-- Divider -->
      <div v-if="showFileMenu && canModify" class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
      <!-- View Style Section (only for note pages) -->
      <div v-if="showFileMenu && canModify" class="px-4 py-2 text-xs text-gray-500 dark:text-gray-400">
        Edit Style:
      </div>

      <!-- Single View (Edit mode only) -->
      <DropdownMenuItem 
        v-if="showFileMenu && canModify"
        :icon="Square"
        @click="onTogglePreviewStyle"
        :class="{ 'bg-gray-100 dark:bg-gray-700': globalStore.previewStyle === 'tab' }"
      >
        Tab Style
      </DropdownMenuItem>
      
      <!-- Split View (Edit mode only) -->
      <DropdownMenuItem 
        v-if="showFileMenu && canModify"
        :icon="Columns2"
        @click="onTogglePreviewStyle"
        :class="{ 'bg-gray-100 dark:bg-gray-700': globalStore.previewStyle === 'vertical' }"
      >
        Split Style
      </DropdownMenuItem>

      <!-- Divider -->
      <div v-if="showSlideView || showMolView || showRawView" class="border-t border-gray-200 dark:border-gray-600 my-1"></div>

      <!-- Slide View (only for notes with 'slide' tag) -->
      <DropdownMenuItem 
        v-if="showSlideView"
        :icon="Presentation"
        @click="onSlideView"
      >
        Slide View
      </DropdownMenuItem>
      
      <!-- Coordinate View (only for notes with 'coordinate' category) -->
      <DropdownMenuItem 
        v-if="showMolView"
        :icon="Atom"
        @click="onMolView"
      >
        Coordinate View
      </DropdownMenuItem>
      
      <!-- Output View (for all notes) -->
      <DropdownMenuItem 
        v-if="showRawView"
        :icon="Grip"
        @click="onRawView"
      >
        Output View
      </DropdownMenuItem>
      

      
      <!-- Divider -->
      <div class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
      <!-- Tag Configuration (only for authenticated users) -->
      <DropdownMenuItem
        v-if="globalStore.isAuthenticated"
        :icon="Settings"
        @click="showTagConfig"
      >
        Tag Configuration
      </DropdownMenuItem>
      
      <!-- Divider -->
      <div class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
      <!-- Login Item -->
      <RouterLink
        v-if="!globalStore.isAuthenticated && globalStore.config.authType === 'password'"
        :to="{ name: 'login' }"
        @click="onMenuClose"
        class="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      >
        <LogIn class="w-4 h-4 mr-3" />
        Login
      </RouterLink>
      
      <!-- Logout Item -->
      <DropdownMenuItem
        v-if="showLogOutButton"
        :icon="LogOut"
        @click="logOut"
      >
        Logout
      </DropdownMenuItem>
    </DropdownMenu>
    
    <!-- New Note Button with Dropdown -->
    <DropdownMenu 
      v-if="showNewButton"
      :trigger-icon="Plus" 
      :close-on-click-outside="true"
      @close="onNewNoteMenuClose"
    >
      <!-- New Note without tag -->
      <DropdownMenuItem 
        :icon="Plus"
        @click="createNewNote"
      >
        New Note
      </DropdownMenuItem>
      
      <!-- New Note with current tag (if on tag page or home page with selected tag, but not _untagged) -->
      <DropdownMenuItem 
        v-if="((route.name === 'tag' && route.params.tagName && route.params.tagName !== '_untagged') || (route.name === 'home' && selectedTag && selectedTag !== '_untagged'))"
        :icon="Tag"
        @click="() => createNewNoteWithTag()"
      >
        with "{{ route.name === 'tag' ? route.params.tagName : selectedTag }}"
      </DropdownMenuItem>
      
      <!-- Divider -->
      <div v-if="((route.name === 'tag' && route.params.tagName && route.params.tagName !== '_untagged') || (route.name === 'home' && selectedTag && selectedTag !== '_untagged'))" class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
      <!-- Import File -->
      <DropdownMenuItem 
        :icon="Upload"
        @click="showImportModal"
      >
        Import File
      </DropdownMenuItem>
      
      <!-- Divider -->
      <div class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      

      
      <!-- Divider -->
      <div class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
      <!-- Paste Text -->
      <DropdownMenuItem 
        :icon="FileText"
        @click="showPasteModal"
      >
        Paste Text
      </DropdownMenuItem>
    </DropdownMenu>
    
    <!-- Tag Edit Button -->
    <button
      v-if="showTagEditButton"
      @click="showTagConfig"
      class="flex items-center justify-center w-10 h-10 rounded-lg bg-color-button-secondary-bg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg text-color-button-secondary-fg transition-colors"
      :title="selectedTag ? `Configure tag '${selectedTag}'` : 'Configure tags'"
    >
      <Tag class="w-6 h-6" />
    </button>
    
    <!-- File Menu (Note view only) -->
    <DropdownMenu 
      v-if="showFileMenu"
      :trigger-icon="File" 
      :close-on-click-outside="true"
      @close="onFileMenuClose"
    >
      <template #indicator>
        <!-- Auto-saving Indicator (Edit mode only) -->
        <div
          v-show="canModify && autoSaveState.isAutoSaving"
          class="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-green-500 animate-pulse"
          title="Auto-saving..."
        ></div>
        <!-- Unsaved Changes Indicator (Edit mode only) -->
        <div
          v-show="canModify && unsavedChanges && !autoSaveState.isAutoSaving"
          class="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-theme-brand"
          title="Unsaved changes"
        ></div>
      </template>
      
      <!-- Copy Link -->
      <DropdownMenuItem 
        :icon="Link" 
        @click="onCopyLink"
      >
        Copy link
      </DropdownMenuItem>
      
      <!-- History -->
      <DropdownMenuItem 
        :icon="History" 
        @click="showHistory"
      >
        History
      </DropdownMenuItem>
      
 

      
 

      <!-- Visibility Section -->
      <div v-show="canModify" class="px-4 py-2 text-xs text-gray-500 dark:text-gray-400">
        Visibility:
      </div>

      <!-- Private -->
      <DropdownMenuItem 
        v-show="canModify"
        :icon="Lock"
        @click="onChangeVisibility('private')"
        :class="{ 'bg-gray-100 dark:bg-gray-700': currentVisibility === 'private' }"
      >
        Private
      </DropdownMenuItem>
      
      <!-- Limited -->
      <DropdownMenuItem 
        v-show="canModify"
        :icon="Users"
        @click="onChangeVisibility('limited')"
        :class="{ 'bg-gray-100 dark:bg-gray-700': currentVisibility === 'limited' }"
      >
        Limited
      </DropdownMenuItem>
      
      <!-- Public -->
      <DropdownMenuItem 
        v-show="canModify"
        :icon="Globe"
        @click="onChangeVisibility('public')"
        :class="{ 'bg-gray-100 dark:bg-gray-700': currentVisibility === 'public' }"
      >
        Public
      </DropdownMenuItem>
      
      <!-- Divider -->
      <div v-show="canModify" class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
      <!-- Delete Note (Edit mode only) -->
      <DropdownMenuItem 
        v-show="canModify && !isNewNote"
        :icon="Trash2" 
        @click="onDeleteNote"
      >
        Delete
      </DropdownMenuItem>
    </DropdownMenu>
    

    
    <!-- Paste Modal -->
    <PasteModal 
      :is-visible="isPasteModalVisible"
      :selected-tag="selectedTag"
      @close="closePasteModal"
    />
    
    <!-- History Modal -->
    <HistoryModal 
      v-model="isHistoryModalVisible"
      :filename="route.params.filename"
      :note-title="globalStore.currentNoteTitle || 'Unknown'"
    />
    
    <!-- Tag Configuration Modal -->
    <TagConfigModal
      v-model:isVisible="showTagConfigModal"
      :selected-tag-data="selectedTagForConfig"
      @close="closeTagConfig"
      @saved="onTagConfigSaved"
    />
  </nav>
</template>

<script setup>
import { computed, ref } from "vue";
import { RouterLink, useRouter, useRoute } from "vue-router";
import { 
  LayoutGrid, 
  Plus, 
  LogOut,
  LogIn,
  Menu,
  Edit,
  Eye,
  File,
  Link,
  Trash2,
  Square,
  Columns2,
  Tag,
  BookOpen,
  Presentation,
  Lock,
  Users,
  Globe,
  Upload,
  Atom,
  Grip,
  ExternalLink,
  FileText,
  History,
  Settings
} from "lucide-vue-next";

import SearchInput from "./SearchInput.vue";
import DropdownMenu from "./DropdownMenu.vue";
import DropdownMenuItem from "./DropdownMenuItem.vue";

import PasteModal from "./PasteModal.vue";
import HistoryModal from "./HistoryModal.vue";
import TagConfigModal from "./TagConfigModal.vue";
import { authTypes } from "../lib/constants.js";
import { useGlobalStore } from "../lib/globalStore.js";
import { clearStoredToken } from "../lib/tokenStorage.js";
import { getTagsWithCounts, createTagsBackup, listTagsBackups, restoreTagsBackup } from "../lib/api.js";

const props = defineProps({
  incrementalSearchResults: {
    type: Array,
    default: () => []
  },
  incrementalSearchTerm: {
    type: String,
    default: ""
  },
  // File menu props
  showFileMenu: {
    type: Boolean,
    default: false
  },
  canModify: {
    type: Boolean,
    default: false
  },
  isNewNote: {
    type: Boolean,
    default: false
  },
  autoSaveState: {
    type: Object,
    default: () => ({ isAutoSaving: false })
  },
  unsavedChanges: {
    type: Boolean,
    default: false
  },
  // Tag edit props
  selectedTag: {
    type: String,
    default: null
  },
  // Visibility props
  currentVisibility: {
    type: String,
    default: 'private'
  }
});



const globalStore = useGlobalStore();
const router = useRouter();
const route = useRoute();
const searchInput = ref();

const isPasteModalVisible = ref(false);
const isHistoryModalVisible = ref(false);
const showTagConfigModal = ref(false);
const selectedTagForConfig = ref(null);

const emit = defineEmits([
  "incrementalSearch", 
  "selectSearchResult", 
  "closeResults",
  "clearSearch",
  // File menu events
  "copyLink",
  "deleteNote",
  "togglePreviewStyle",
  "changeVisibility",
  // Tag edit events

  // Import events
  "showImportModal"
]);

const showNewButton = computed(() => {
  return globalStore.isAuthenticated && globalStore.editMode;
});

const showLogOutButton = computed(() => {
  return globalStore.isAuthenticated;
});

const showTagEditButton = computed(() => {
  return globalStore.isAuthenticated && globalStore.editMode && route.name !== 'note';
});

const isReadmePage = computed(() => {
  return route.name === 'note' && route.params.filename && route.params.filename.toLowerCase() === 'readme.md';
});

const showSlideView = computed(() => {
  // Check if we're on a note page
  return route.name === 'note' && route.params.filename;
});

const showMolView = computed(() => {
      // Check if we're on a note page and the note has 'coordinate' category
    return route.name === 'note' && route.params.filename && globalStore.currentNoteCategory === 'coordinate';
});

const showRawView = computed(() => {
  // Check if we're on a note page and the note has 'output' category
  return route.name === 'note' && route.params.filename && globalStore.currentNoteCategory === 'output';
});






function toggleEditMode() {
  globalStore.setEditMode(true);
}

function toggleViewMode() {
  globalStore.setEditMode(false);
}

function logOut() {
  clearStoredToken();
  globalStore.isAuthenticated = false;
  router.push({ name: "home" });
}

function onMenuClose() {
  // Menu close handler if needed
}

function onSearch() {
  // Search is handled by SearchInput component
  // This function can be used for additional search-related actions if needed
}

function onIncrementalSearch(searchTerm) {
  // Emit incremental search to parent component
  emit("incrementalSearch", searchTerm);
}

function onSelectResult(result) {
  emit("selectSearchResult", result);
}

function onCloseResults() {
  // Handle closing results
  emit("closeResults");
}

function onConfirmSelection(result) {
  // Handle confirming selection
  emit("selectSearchResult", result);
}

function onClearSearch() {
  // Handle clearing search
  emit("clearSearch");
}

function onFileMenuClose() {
  // File menu close handler if needed
}

function onNewNoteMenuClose() {
  // New note menu close handler if needed
}





function createNewNote() {
  router.push({ name: 'new' });
}

function createNewNoteWithTag(tagName = null) {
  let tag = tagName;
  
  // If no tagName provided, get tag from route params or selected tag
  if (!tag) {
    if (route.name === 'tag') {
      tag = route.params.tagName;
    } else if (route.name === 'home' && props.selectedTag) {
      tag = props.selectedTag;
    }
  }
  
  // Don't include _untagged tag
  if (tag && tag !== '_untagged') {
    router.push({ name: 'new', query: { tag } });
  } else {
    router.push({ name: 'new' });
  }
}

function onCopyLink() {
  emit("copyLink");
}

function onDeleteNote() {
  emit("deleteNote");
}

function onTogglePreviewStyle() {
  const newStyle = globalStore.previewStyle === 'vertical' ? 'tab' : 'vertical';
  globalStore.setPreviewStyle(newStyle);
  emit("togglePreviewStyle", newStyle);
}

function onChangeVisibility(visibility) {
  emit("changeVisibility", visibility);
}

function onSlideView() {
  // Navigate to slide view
  router.push({ name: 'slide', params: { filename: route.params.filename } });
}

function onMolView() {
  // Navigate to coordinate view
  router.push({ name: 'coordinate', params: { filename: route.params.filename } });
}

function onRawView() {
  // Navigate to output view
  router.push({ name: 'output', params: { filename: route.params.filename } });
}



function showReadme() {
  // Switch to view mode for README.md
  globalStore.setEditMode(false);
  router.push({ name: 'note', params: { filename: 'README.md' } });
}

function showImportModal() {
  emit("showImportModal");
}



function showPasteModal() {
  // Remove focus from search input to prevent input capture
  if (searchInput.value) {
    searchInput.value.blur();
  }
  
  // Small delay to ensure focus is properly removed before showing modal
  setTimeout(() => {
    isPasteModalVisible.value = true;
  }, 10);
}

function closePasteModal() {
  isPasteModalVisible.value = false;
}

function showHistory() {
  isHistoryModalVisible.value = true;
}

function closeHistoryModal() {
  isHistoryModalVisible.value = false;
}

// Tag configuration functions
async function showTagConfig() {
  try {
    // If we have a selected tag, use it for configuration
    if (props.selectedTag && props.selectedTag !== '_untagged') {
      const tagsData = await getTagsWithCounts();
      const selectedTagData = tagsData.find(tag => tag.tag === props.selectedTag);
      if (selectedTagData) {
        selectedTagForConfig.value = selectedTagData;
        showTagConfigModal.value = true;
        return;
      }
    }
    
    // If no selected tag or selected tag not found, show modal with tag selection
    showTagConfigModal.value = true;
  } catch (error) {
    console.error('Failed to load tags for configuration:', error);
  }
}

function closeTagConfig() {
  showTagConfigModal.value = false;
  selectedTagForConfig.value = null;
}

async function onTagConfigSaved() {
  // Refresh the page or reload tag data to reflect changes
  // For now, we'll just show a success message
  globalStore.toast?.addToast('Tag configuration saved successfully', '', 'success');
  
  // If we're on a tag page, we might want to refresh the tag data
  // This could be implemented by emitting an event to the parent component
}

// Method to focus the search input
function focusSearchInput(character = null) {
  if (searchInput.value) {
    searchInput.value.focus(character);
  }
}

// Expose the focus method for parent components
defineExpose({ focusSearchInput });
</script>
