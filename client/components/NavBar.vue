<template>
  <nav class="mb-4 flex justify-between items-center gap-4 relative z-40">
    <!-- Menu Dropdown -->
    <DropdownMenu :trigger-icon="Menu" :menu-position="'left'" @close="onMenuClose">
      <template #indicator>
        <!-- Login Status Indicator -->
        <div
          v-show="globalStore.isAuthenticated"
          :class="[
            'absolute -top-1 -right-1 h-2 w-2 rounded-full',
            globalStore.editMode ? 'bg-[var(--theme-brand-accent)]' : 'bg-[var(--theme-brand)]'
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
      <div class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
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
      <div v-if="globalStore.isAuthenticated && !isReadmePage" class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
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
    
    <!-- Home Button -->
    <RouterLink :to="{ name: 'home' }" class="flex-shrink-0">
      <button class="flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--theme-button)] hover:bg-[var(--theme-brand)] hover:text-white text-theme-text transition-colors shadow-sm">
        <LayoutGrid class="w-4 h-4" />
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
      
      <!-- Divider -->
      <div v-if="((route.name === 'tag' && route.params.tagName && route.params.tagName !== '_untagged') || (route.name === 'home' && selectedTag && selectedTag !== '_untagged'))" class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
      <!-- New Note with current tag (if on tag page or home page with selected tag, but not _untagged) -->
      <DropdownMenuItem 
        v-if="((route.name === 'tag' && route.params.tagName && route.params.tagName !== '_untagged') || (route.name === 'home' && selectedTag && selectedTag !== '_untagged'))"
        :icon="Tag"
        @click="() => createNewNoteWithTag()"
      >
        with "{{ route.name === 'tag' ? route.params.tagName : selectedTag }}"
      </DropdownMenuItem>
      
      <!-- Popular tags section -->
      <div v-if="availableTags.length > 0" class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
      <!-- Popular tags -->
      <div v-if="availableTags.length > 0" class="px-4 py-2 text-xs text-gray-500 dark:text-gray-400">
        Popular tags:
      </div>
      
      <DropdownMenuItem 
        v-for="tag in availableTags.slice(0, 5)"
        :key="tag"
        :icon="Tag"
        @click="() => createNewNoteWithTag(tag)"
      >
        with "{{ tag }}"
      </DropdownMenuItem>
    </DropdownMenu>
    
    <!-- Tag Edit Button with Dropdown -->
    <DropdownMenu 
      v-if="showTagEditButton"
      :trigger-icon="Tag" 
      :close-on-click-outside="true"
      @close="onTagEditMenuClose"
    >
      <!-- No tag selected -->
      <DropdownMenuItem 
        v-if="!selectedTag"
        :icon="Tag"
        :disabled="true"
        class="text-gray-400 cursor-not-allowed"
      >
        No tag selected
      </DropdownMenuItem>
      
      <!-- _untagged tag selected - cannot edit -->
      <DropdownMenuItem 
        v-else-if="selectedTag === '_untagged'"
        :icon="Tag"
        :disabled="true"
        class="text-gray-400 cursor-not-allowed"
      >
        Cannot edit
      </DropdownMenuItem>
      
      <!-- Tag edit options when tag is selected -->
      <template v-else>
        <DropdownMenuItem 
          :icon="Edit"
          @click="onRenameTag"
        >
          Rename "{{ selectedTag }}"
        </DropdownMenuItem>
        
        <!-- Divider -->
        <div class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
        
        <DropdownMenuItem 
          :icon="Trash2"
          @click="onDeleteTag"
          class="text-[var(--theme-brand-accent)] hover:text-[var(--theme-brand-accent)]/80"
        >
          Delete "{{ selectedTag }}"
        </DropdownMenuItem>
      </template>
    </DropdownMenu>
    
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
      
      <!-- Divider -->
      <div v-if="hasSlideTag" class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
      <!-- Slide View (only for notes with 'slide' tag) -->
      <DropdownMenuItem 
        v-if="hasSlideTag"
        :icon="Presentation"
        @click="onSlideView"
      >
        Slide View
      </DropdownMenuItem>
      
      <!-- Divider -->
      <div v-show="canModify" class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
      <!-- Single View (Edit mode only) -->
      <DropdownMenuItem 
        v-show="canModify"
        :icon="Square"
        @click="onTogglePreviewStyle"
        :class="{ 'bg-gray-100 dark:bg-gray-700': globalStore.previewStyle === 'tab' }"
      >
        Single View
      </DropdownMenuItem>
      
      <!-- Split View (Edit mode only) -->
      <DropdownMenuItem 
        v-show="canModify"
        :icon="Columns2"
        @click="onTogglePreviewStyle"
        :class="{ 'bg-gray-100 dark:bg-gray-700': globalStore.previewStyle === 'vertical' }"
      >
        Split View
      </DropdownMenuItem>
      
      <!-- Divider -->
      <div v-show="canModify" class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
      
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
  Globe
} from "lucide-vue-next";

import SearchInput from "../components/SearchInput.vue";
import DropdownMenu from "../components/DropdownMenu.vue";
import DropdownMenuItem from "../components/DropdownMenuItem.vue";
import { authTypes } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";
import { clearStoredToken } from "../tokenStorage.js";
import { getTags } from "../api.js";

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

// Available tags for new note dropdown
const availableTags = ref([]);

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
  "renameTag",
  "deleteTag"
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

const hasSlideTag = computed(() => {
  // Check if we're on a note page and the note has a 'slide' tag
  return route.name === 'note' && route.params.filename && window.currentNoteTags && window.currentNoteTags.includes('slide');
});

// Load available tags for new note dropdown
async function loadAvailableTags() {
  try {
    const tags = await getTags();
    // Filter out "_untagged" tag since it's automatically applied
    availableTags.value = tags.filter(tag => tag !== "_untagged");
  } catch (error) {
    console.error('Failed to load tags:', error);
    availableTags.value = [];
  }
}

// Load tags when component mounts
loadAvailableTags();

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

function onTagEditMenuClose() {
  // Tag edit menu close handler if needed
}

function onRenameTag() {
  emit("renameTag", props.selectedTag);
}

function onDeleteTag() {
  emit("deleteTag", props.selectedTag);
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

function showReadme() {
  // Switch to view mode for README.md
  globalStore.setEditMode(false);
  router.push({ name: 'note', params: { filename: 'README.md' } });
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
