<template>
  <div v-if="noteTags.length > 0" class="mt-2 tag-grid-container" :style="noteContainerStyle">
    <div>
      <!-- Sort Controls -->
      <div class="flex items-center justify-end w-full mb-2 space-x-2">
        <SortDropdown
          v-if="selectedNoteTag && displayedTagNotes.length > 0"
          v-model="noteTagSortBy"
          :sort-order="noteTagSortOrder"
          @update:sort-order="updateNoteTagSortOrder"
          :options="noteSortOptions"
          label="Sort Notes by"
        />
        <SortDropdown
          v-model="tagSortBy"
          :sort-order="tagSortOrder"
          @update:sort-order="updateTagSortOrder"
          :options="tagSortOptions"
          label="Sort Tags by"
        />
      </div>

      <!-- Grid Content -->
      <GridLayout
        :items="tagGridItems"
        @tag-click="onNoteTagClick"
        @tag-dblclick="onNoteTagDoubleClick"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import SortDropdown from '../sort/SortDropdown.vue';
import GridLayout from '../layout/GridLayout.vue';
import { useSorting } from '../../composables/useSorting.js';
import { useNoteTagGrid } from '../../composables/useNoteTagGrid.js';

const props = defineProps({
  noteTags: {
    type: Array,
    required: true
  },
  noteContainerStyle: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits(['tag-click', 'tag-dblclick']);

const { noteSortOptions, tagSortOptions } = useSorting();
const {
  selectedNoteTag,
  displayedTagNotes,
  noteTagSortBy,
  noteTagSortOrder,
  tagSortBy,
  tagSortOrder,
  sortedTagNotes,
  tagGridItems,
  updateNoteTagSortOrder,
  updateTagSortOrder,
  onNoteTagClick,
  onNoteTagDoubleClick
} = useNoteTagGrid();

// Computed properties
const computedTagGridItems = computed(() => {
  return tagGridItems.value(props.noteTags, selectedNoteTag.value);
});

function handleTagClick(tagName) {
  onNoteTagClick(tagName);
  emit('tag-click', tagName);
}

function handleTagDoubleClick(tagName) {
  onNoteTagDoubleClick(tagName);
  emit('tag-dblclick', tagName);
}
</script>

<style scoped>
.tag-grid-container {
  max-width: var(--layout-width-note);
  width: 100%;
  margin-left: auto;
  margin-right: auto;
}
</style> 