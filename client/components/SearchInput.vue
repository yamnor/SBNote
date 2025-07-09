<template>
  <div class="relative w-full search-input overflow-visible">
    <!-- Input -->
    <div
      class="flex items-center w-full rounded-md bg-theme-background-surface"
      :class="{ 'px-3 py-2': !large, 'px-5 py-4': large }"
    >
      <Search class="w-5 h-5 mr-2 text-theme-text-muted flex-shrink-0" />
      <input
        type="text"
        ref="input"
        v-model="searchTerm"
        v-focus
        class="w-full bg-transparent focus:outline-none"
        :placeholder="placeholder"
        @keydown="keydownHandler"
        @keyup="stateChangeHandler"
        @click="stateChangeHandler"
        @blur="tagMenuVisible = false; searchResultsMenuVisible = false"
      />
      <!-- Note: Default behaviour for up and down keys is prevented to stop cursor moving when tag menu is navigated. -->
    </div>

    <!-- Tag Menu -->
    <div
      v-if="tagMenuVisible"
      class="absolute z-50 left-0 mt-2 max-h-64 w-full overflow-scroll rounded-md border border-theme-border bg-theme-background-surface p-1 shadow-lg"
    >
      <p
        v-for="(tag, index) in tagMatches"
        ref="tagMenuItems"
        class="cursor-pointer rounded px-2 py-1 hover:bg-theme-background-subtle"
        :class="{ 'bg-[var(--theme-brand)] text-white': index === tagMenuIndex, 'text-theme-text': index !== tagMenuIndex }"
        @click="tagChosen(tag)"
        @mousedown.prevent
      >
        <!-- Note: Default behaviour for mouse down is prevented to stop focus moving to menu on click. -->
        {{ tag }}
      </p>
    </div>

    <!-- Search Results Menu -->
    <div
      v-if="searchResultsMenuVisible && searchResults.length > 0"
      class="absolute z-50 left-0 mt-2 max-h-64 w-full overflow-scroll rounded-md border border-theme-border bg-theme-background-surface p-1 shadow-lg"
    >
      <div
        v-for="(result, index) in searchResults"
        ref="searchResultMenuItems"
        class="cursor-pointer rounded px-2 py-1 hover:bg-theme-background-subtle"
        :class="{ 'bg-[var(--theme-brand)]': index === searchResultMenuIndex }"
        @click="searchResultChosen(result)"
        @mousedown.prevent
      >
        <div class="flex items-center">
          <div class="flex-1 min-w-0">
            <div class="font-medium truncate" :class="{ 'text-white': index === searchResultMenuIndex, 'text-theme-text': index !== searchResultMenuIndex }">{{ result.title }}</div>
            <div v-if="result.content" class="text-sm truncate" :class="{ 'text-white/80': index === searchResultMenuIndex, 'text-theme-text-muted': index !== searchResultMenuIndex }">
              {{ result.content.substring(0, 100) }}{{ result.content.length > 100 ? '...' : '' }}
            </div>
          </div>
          <SquareArrowOutUpRight class="w-4 h-4 flex-shrink-0 ml-2" :class="{ 'text-white/60': index === searchResultMenuIndex, 'text-theme-text-muted': index !== searchResultMenuIndex }" />
        </div>
      </div>
    </div>

    <!-- New Note Menu (when no search results or empty search term) -->
    <div
      v-if="searchResultsMenuVisible && searchResults.length === 0"
      class="absolute z-50 left-0 mt-2 w-full rounded-md border border-theme-border bg-theme-background-surface p-1 shadow-lg"
    >
      <div
        ref="newNoteMenuItem"
        class="cursor-pointer rounded px-2 py-1 hover:bg-theme-background-subtle"
        :class="{ 'bg-[var(--theme-brand)]': searchResultMenuIndex === 0 }"
        @click="newNoteChosen"
        @mousedown.prevent
      >
        <div class="flex items-center">
          <div class="flex-1 min-w-0">
            <div class="font-medium" :class="{ 'text-white': searchResultMenuIndex === 0, 'text-theme-text': searchResultMenuIndex !== 0 }">New</div>
            <div class="text-sm" :class="{ 'text-white/80': searchResultMenuIndex === 0, 'text-theme-text-muted': searchResultMenuIndex !== 0 }">
              {{ searchTerm.trim() ? `Create new note with "${searchTerm}"` : 'Create new note' }}
            </div>
          </div>
          <Plus class="w-4 h-4 flex-shrink-0 ml-2" :class="{ 'text-white/60': searchResultMenuIndex === 0, 'text-theme-text-muted': searchResultMenuIndex !== 0 }" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Search, SquareArrowOutUpRight, Plus } from "lucide-vue-next";

import { ref, watch } from "vue";
import { useRouter } from "vue-router";

import { apiErrorHandler, getTags } from "../api.js";
import * as constants from "../constants.js";
import { getToastOptions } from "../helpers.js";

const props = defineProps({
  initialSearchTerm: { type: String, default: "" },
  large: Boolean,
  placeholder: { type: String, default: "Search..." },
  incremental: { type: Boolean, default: false },
  searchResults: { type: Array, default: () => [] },
});
const emit = defineEmits(["search", "incrementalSearch", "selectResult", "closeResults", "confirmSelection", "clearSearch"]);

const input = ref();
const router = useRouter();
const searchTerm = ref(props.initialSearchTerm);

let tags = null;
const tagMatches = ref([]);
const tagMenuItems = ref([]);
const tagMenuIndex = ref(0);
const tagMenuVisible = ref(false);

// Search results menu state
const searchResultMenuItems = ref([]);
const searchResultMenuIndex = ref(0);
const searchResultsMenuVisible = ref(false);
const previousSearchResults = ref([]);
let incrementalSearchTimeout = null;

function keydownHandler(event) {
  // Tag Menu Open
  if (tagMenuVisible.value) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      tagMenuIndex.value = Math.min(
        tagMenuIndex.value + 1,
        tagMatches.value.length - 1,
      );
      tagMenuItems.value[tagMenuIndex.value].scrollIntoView({
        block: "nearest",
      });
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      // If we're at the top item, hide the menu
      if (tagMenuIndex.value === 0) {
        tagMenuVisible.value = false;
      } else {
        tagMenuIndex.value = Math.max(tagMenuIndex.value - 1, 0);
        tagMenuItems.value[tagMenuIndex.value].scrollIntoView({
          block: "nearest",
        });
      }
    } else if (event.key === "Enter") {
      event.preventDefault();
      tagChosen(tagMatches.value[tagMenuIndex.value]);
    } else if (event.key === "Escape") {
      event.preventDefault();
      tagMenuVisible.value = false;
    }
  }
  // Search Results Menu Open
  else if (searchResultsMenuVisible.value && (props.searchResults.length > 0 || props.searchResults.length === 0)) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      event.stopPropagation();
      const maxIndex = props.searchResults.length > 0 ? props.searchResults.length - 1 : 0;
      searchResultMenuIndex.value = Math.min(
        searchResultMenuIndex.value + 1,
        maxIndex,
      );
      if (props.searchResults.length > 0) {
        searchResultMenuItems.value[searchResultMenuIndex.value].scrollIntoView({
          block: "nearest",
        });
      }
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      event.stopPropagation();
      // If we're at the top item, hide the menu
      if (searchResultMenuIndex.value === 0) {
        searchResultsMenuVisible.value = false;
        emit("closeResults");
      } else {
        searchResultMenuIndex.value = Math.max(searchResultMenuIndex.value - 1, 0);
        if (props.searchResults.length > 0) {
          searchResultMenuItems.value[searchResultMenuIndex.value].scrollIntoView({
            block: "nearest",
          });
        }
      }
    } else if (event.key === "Enter") {
      event.preventDefault();
      event.stopPropagation();
      if (props.searchResults.length > 0) {
        searchResultChosen(props.searchResults[searchResultMenuIndex.value]);
      } else {
        newNoteChosen();
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      searchResultsMenuVisible.value = false;
      emit("closeResults");
    }
  }
  // Show search results menu when ArrowDown is pressed and we have results or no results
  else if (event.key === "ArrowDown" && !tagMenuVisible.value && 
           (props.searchResults.length > 0 || props.searchResults.length === 0)) {
    event.preventDefault();
    event.stopPropagation();
    searchResultsMenuVisible.value = true;
    searchResultMenuIndex.value = 0;
  }
  // Tag Menu Closed and No Search Results
  else if (event.key === "Enter") {
    search();
  }
}

function tagChosen(tag) {
  // Extract tag name without # prefix
  const tagName = tag.startsWith('#') ? tag.substring(1) : tag;
  
  // Navigate to tag search immediately
  router.push({
    name: "tag",
    params: { tagName: tagName },
  });
  
  // Clear search term and close tag menu
  searchTerm.value = "";
  tagMenuVisible.value = false;
  
  // Emit search event
  emit("search");
}

function searchResultChosen(result) {
  // Remove .md extension from filename if present
  const filename = result.filename.replace(/\.md$/, '');
  // Clear search term and results
  searchTerm.value = "";
  searchResultsMenuVisible.value = false;
  emit("closeResults");
  emit("clearSearch");
  router.push({ name: 'note', params: { filename: filename } });
}

function newNoteChosen() {
  const trimmedTerm = searchTerm.value.trim();
  // Clear search term and results
  searchTerm.value = "";
  searchResultsMenuVisible.value = false;
  emit("closeResults");
  emit("clearSearch");
  router.push({
    name: "new",
    query: trimmedTerm ? { 
      [constants.params.content]: trimmedTerm
    } : {},
  });
}

function search() {
  if (searchTerm.value && searchTerm.value.trim()) {
    const trimmedTerm = searchTerm.value.trim();
    
    // Check if the search term is a tag (starts with #)
    if (trimmedTerm.startsWith('#')) {
      const tagName = trimmedTerm.substring(1); // Remove the # prefix
      if (tagName) {
        router.push({
          name: "tag",
          params: { tagName: tagName },
        });
        emit("search");
        return;
      }
    }
    
    // Regular search
    router.push({
      name: "search",
      query: { [constants.params.searchTerm]: trimmedTerm },
    });
    emit("search");
  } else {
    // Navigate to home when search term is empty
    router.push({ name: "home" });
  }
}

function stateChangeHandler() {
  const wordOnCursor = getWordOnCursor();
  if (wordOnCursor.charAt(0) !== "#") {
    tagMenuVisible.value = false;
    tagMatches.value = [];
  } else {
    // All tags are stored in lowercase, so we can do a case-insensitive search.
    filterTagMatches(wordOnCursor.toLowerCase());
  }
  
  // Don't automatically show search results menu - only show when arrow key is pressed
  // Reset index if search results have changed
  if (JSON.stringify(props.searchResults) !== JSON.stringify(previousSearchResults.value)) {
    searchResultMenuIndex.value = 0;
    previousSearchResults.value = [...props.searchResults];
  }
  
  // Don't automatically hide search results menu for empty search term
  // Only hide if there are no search results and no search term
  if (props.searchResults.length === 0 && !searchTerm.value.trim()) {
    // Keep menu visible for "New" option
  }
  
  // Emit incremental search if enabled with minimal debouncing
  if (props.incremental && searchTerm.value) {
    if (incrementalSearchTimeout) {
      clearTimeout(incrementalSearchTimeout);
    }
    incrementalSearchTimeout = setTimeout(() => {
      emit("incrementalSearch", searchTerm.value);
    }, 100);
  }
}

async function filterTagMatches(input) {
  if (tags === null) {
    try {
      tags = await getTags();
    } catch (error) {
      tags = [];
      apiErrorHandler(error, toast);
    }
    // Map tags to display format, showing "_untagged" as "Untagged"
    tags = tags.map((tag) => {
      if (tag === "_untagged") {
        return "Untagged";
      }
      return `#${tag}`;
    });
  }
  const currentTagMatchCount = tagMatches.value.length;
  tagMatches.value = tags.filter(
    (tag) => tag.startsWith(input) && tag !== input,
  );
  if (
    currentTagMatchCount !== tagMatches.value.length &&
    tagMatches.value.length > 0
  ) {
    tagMenuIndex.value = 0;
    tagMenuVisible.value = true;
  } else if (tagMatches.value.length === 0) {
    tagMenuVisible.value = false;
  }
}

// Helpers

/**
 * Returns the word that the cursor is currently on.
 * @returns {Object} An object containing the start and end indices of the word.
 */
function getWordOnCursorPosition() {
  const cursorPosition = input.value.selectionStart;
  const wordStart = Math.max(
    searchTerm.value.lastIndexOf(" ", cursorPosition - 1) + 1,
    0,
  );
  let wordEnd = searchTerm.value.indexOf(" ", cursorPosition);
  if (wordEnd === -1) {
    // If there is no space after the cursor, then the word ends at the end of the input.
    wordEnd = searchTerm.value.length;
  }
  return { start: wordStart, end: wordEnd };
}

/**
 * Retrieves the word at the current cursor position in the search term.
 * @returns {string} The word at the cursor position.
 */
function getWordOnCursor() {
  const { start, end } = getWordOnCursorPosition();
  return searchTerm.value.substring(start, end);
}

/**
 * Replaces the word at the cursor position with the given replacement.
 * @param {string} replacement The word to replace the current word with.
 */
function replaceWordOnCursor(replacement) {
  const { start, end } = getWordOnCursorPosition();
  searchTerm.value =
    searchTerm.value.substring(0, start) +
    replacement +
    searchTerm.value.substring(end);
}

watch(
  () => props.initialSearchTerm,
  () => {
    searchTerm.value = props.initialSearchTerm;
  },
);

// Method to focus the input
function focus(character = null) {
  if (input.value) {
    input.value.focus();
    // If a character is provided, set it as the search term
    if (character) {
      searchTerm.value = character;
      // Trigger search state change
      stateChangeHandler();
    }
  }
}

// Expose the focus method
defineExpose({ focus });
</script>
